"""
Eval harness: run explainer on fixture items and compute metrics.
Usage (from project root): python eval/run_harness.py [--fixture eval/fixtures/golden.json] [--output eval/results/out.json] [--skip-judge]

Fixture type is auto-detected: if items have "expected_explanation" we run golden-dataset metrics (similarity, optional judge); otherwise LLM relevance judge only. For no-golden mode, --skip-judge is not allowed (judge is required).
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure project root on path when run as python eval/run_harness.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import config
from agent import explain_with_stats
from tools import fetch_bluesky_post

from eval.metrics import llm_judge_golden, llm_judge_relevance, semantic_similarity


def load_fixture(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_golden(fixture: dict) -> bool:
    items = fixture.get("items") or []
    return bool(items and items[0].get("expected_explanation") is not None)


def run_item(item: dict, golden: bool, skip_judge: bool = False) -> dict:
    post_url = item.get("post_url") or item.get("post_id")
    if not post_url:
        return {"id": item.get("id"), "error": "missing post_url/post_id"}
    out = {"id": item.get("id"), "post_url": post_url}

    # Fetch post text (for judge)
    try:
        post_text = fetch_bluesky_post(post_url)
        if not post_text or post_text.startswith("["):
            post_text = "(post fetch returned no text or error)"
    except Exception as e:
        out["error"] = f"fetch: {e}"
        return out

    # Run explainer
    try:
        result = explain_with_stats(post_url)
        explanation = (result.get("explanation") or "").strip()
        out["explanation"] = explanation
        out["usage"] = result.get("usage")
        out["request_elapsed_seconds"] = result.get("request_elapsed_seconds")
    except Exception as e:
        out["error"] = f"agent: {e}"
        return out

    if golden:
        expected = (item.get("expected_explanation") or "").strip()
        out["expected_explanation"] = expected
        out["similarity"] = semantic_similarity(expected, explanation)
        if not skip_judge:
            try:
                judge = llm_judge_golden(post_text, expected, explanation)
                out["judge_score"] = judge["score"]
                out["judge_reasoning"] = judge.get("reasoning", "")
            except Exception as e:
                out["judge_error"] = str(e)
    else:
        if not skip_judge:
            try:
                judge = llm_judge_relevance(post_text, explanation)
                out["relevance_score"] = judge["score"]
                out["relevance_reasoning"] = judge.get("reasoning", "")
            except Exception as e:
                out["judge_error"] = str(e)

    return out


def main():
    parser = argparse.ArgumentParser(description="Run eval harness on a fixture file")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=_root / "eval" / "fixtures" / "golden.json",
        help="Path to fixture JSON (golden or no_golden)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Write results JSON here (default: {config.EVAL_RESULTS_DIR}/out.json)",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip LLM judge (golden only; in no-golden mode judge is required)",
    )
    args = parser.parse_args()

    fixture_path = args.fixture if args.fixture.is_absolute() else _root / args.fixture
    if not fixture_path.exists():
        print(f"Fixture not found: {fixture_path}", file=sys.stderr)
        sys.exit(1)

    fixture = load_fixture(fixture_path)
    golden = is_golden(fixture)
    mode = "golden" if golden else "no_golden"

    if not golden and args.skip_judge:
        print("Error: In no-golden mode the LLM judge is required; there is no other evaluation. Do not use --skip-judge.", file=sys.stderr)
        sys.exit(1)

    print(f"Mode: {mode} (fixture: {fixture_path})")
    print("-" * 50)

    results = []
    for i, item in enumerate(fixture.get("items") or []):
        print(f"  [{i+1}] {item.get('id', item.get('post_url', '?'))} ... ", end="", flush=True)
        res = run_item(item, golden, skip_judge=args.skip_judge)
        if res.get("error"):
            print(f"ERROR: {res['error']}")
        else:
            print("ok")
        results.append(res)

    # Aggregate
    summary = {"mode": mode, "n": len(results), "errors": sum(1 for r in results if r.get("error"))}
    if golden:
        sims = [r["similarity"] for r in results if r.get("similarity") is not None]
        summary["mean_similarity"] = round(sum(sims) / len(sims), 4) if sims else None
        scores = [r["judge_score"] for r in results if r.get("judge_score") is not None]
        summary["mean_judge_score"] = round(sum(scores) / len(scores), 2) if scores else None
    else:
        scores = [r["relevance_score"] for r in results if r.get("relevance_score") is not None]
        summary["mean_relevance_score"] = round(sum(scores) / len(scores), 2) if scores else None

    print("-" * 50)
    print("Summary:", json.dumps(summary, indent=2))
    report = {"summary": summary, "results": results}

    if args.output is not None:
        out_path = args.output if args.output.is_absolute() else _root / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
