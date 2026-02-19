# Bluesky Post Explainer Agent

An AI agent that **fetches a Bluesky post by URL**, **searches the web for context**, and **explains the post** in short bullet points (meaning, origin, derivatives).

**Design focus**
- Although the use case is simple, the **code structure** is aimed at solid design that scales: clear separation of API routes, tools, agent, and config so we can add more tools, endpoints, or agents without a rewrite.
- The emphasis is on **end-to-end implementation** (working pipeline, async API, env-based config) rather than on refining explanation quality (e.g. prompt tuning, tool-call strategies, or model choices). Those can be improved on top of this base.

## Setup

1. **Virtualenv** (recommended): create and activate a venv, then install deps:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Credentials**  
   Create a `.env` file in the **project root** with:
   - `BLUESKY_EMAIL` – your Bluesky login email
   - `BLUESKY_PASSWORD` – your Bluesky app password
   - `OPENAI_API_KEY` – your OpenAI API key (for the explainer agent)

   The OpenAI model used by the agent is set in `config.py` (`OPENAI_MODEL`); change it there if needed.

## Usage

**REST API (FastAPI, async)**

From the project root (the directory that contains `main.py`):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# or
python main.py --reload --port 8000
```

Then call the explain endpoint (POST only):

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"post_url": "https://bsky.app/profile/trumpstaxes.com/post/3mbrz32dais2i"}'
```

Response: `{"post_url": "...", "explanation": "• ..."}`. Interactive docs: http://localhost:8000/docs

**Python (agent only)**  
Run from the project root (or ensure it’s on `PYTHONPATH`) so imports resolve:

```python
from agent import agent, explain_with_stats

# One-shot with stats (e.g. for scripts)
result = explain_with_stats("https://bsky.app/profile/HANDLE/post/RKEY")
print(result["explanation"])

# Or stream to stdout
agent.print_response("Explain this post: https://bsky.app/profile/...", stream=True)
```

## Project layout

All app code lives in the **project root**:

- `main.py` – FastAPI app and uvicorn entrypoint (run with `python main.py` or `uvicorn main:app`)
- `config.py` – env loading from `.env`, `OPENAI_MODEL`, and `OPENAI_MODEL_COSTS` (USD per 1M tokens; GPT-4/5 family)
- `helpers/cost.py` – cost calculation using `OPENAI_MODEL_COSTS` (estimate_openai_cost)
- `schemas.py` – request/response models
- `agent.py` – Agno agent and `explain_with_stats` / `explain_with_stats_async`
- `api/routes.py` – async `/health` and `/explain` routes
- `tools/bluesky_fetch.py` – fetch post by URL
- `.env`, `requirements.txt`, `README.md`

**Eval**  
- `eval/EVAL_HARNESS.md` – Methodology (fixture formats, metrics, groundedness design).  
- **Implementation:** `eval/run_harness.py` runs on a fixture and auto-detects golden vs no-golden. Sample fixtures: `eval/fixtures/golden.json` (human `expected_explanation`), `eval/fixtures/no_golden.json` (post_url only). Metrics: semantic similarity, LLM-as-judge (relevance or golden comparison). In no-golden mode the judge is required (do not use `--skip-judge`). Web search logging / groundedness judge not implemented.  
  From project root: `python eval/run_harness.py --fixture eval/fixtures/golden.json` or `--fixture eval/fixtures/no_golden.json`; optional `--output eval/results/out.json`; `--skip-judge` only for golden (skips judge, keeps similarity).

## What it does

1. **`fetch_bluesky_post(post_url)`** – Fetches the post from Bluesky using the atproto client.
2. **Web search** – Uses Agno’s `WebSearchTools` to find context (people, terms, events).
3. **Explanation** – The agent writes bullet points: what the post means, origin/background, and any notable derivatives or related things.
