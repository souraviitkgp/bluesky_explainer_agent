# Eval harness – Bluesky Post Explainer

Structured spec for evaluating the explainer agent. Two evaluation modes: **with golden dataset** and **without golden dataset** (LLM-as-judge, optionally with groundedness via web search).

---

## 1. Two evaluation modes

| Mode | When to use | Primary signals |
|------|-------------|------------------|
| **Golden dataset** | Human-written expected explanations exist | Semantic similarity, optional LLM judge |
| **No golden** | No human references | LLM-as-judge (relevance); optional groundedness using logged web search |

---

## 2. Golden-dataset evaluation

### 2.1 Fixture format

- One record per post. Fields:
  - `post_url` (or `post_id`)
  - `expected_explanation`: human-written ideal explanation (full text or bullet list)

### 2.2 Metrics

| Metric | Description |
|--------|-------------|
| **Semantic similarity** | Embedding similarity (e.g. cosine) between model output and `expected_explanation`. Use a single embedding model for both; report per-item and mean. |
| **LLM-as-judge** | Judge prompt: given post + expected + model output, score (e.g. 1–5) or binary (acceptable/not). Criteria: correctness, coverage, no hallucination. |
| **Aggregate** | Per run: mean similarity, mean judge score across items. |

### 2.3 What to log per item

- `post_url` / `post_id`
- Model output (explanation)
- Token usage / cost (from existing pipeline)
- Embedding similarity score
- Judge score (if used)

---

## 3. No-golden evaluation (LLM-as-judge)

### 3.1 Fixture format

- One record per post:
  - `post_url` or `post_id`
  - No `expected_explanation`.

### 3.2 Relevance judge

- **Input to judge:** Post text (or snapshot) + model-generated explanation.
- **Prompt:** Ask whether the explanation is relevant, accurate, and adequately covers what the post is about (and any key entities/context). Output: score (e.g. 1–5) or binary.
- **Log:** For each item, log post, explanation, and judge score/reasoning (if returned).

### 3.3 Groundedness (include web search)

- **Idea:** Ensure the explanation is grounded in the agent’s own web search, not hallucinated.
- **Mechanics:**
  - **Log web search:** During agent run, capture all web-search tool inputs and outputs (queries + snippets/pages used).
  - **Judge input:** For each item, give the judge: (1) post text, (2) model explanation, (3) **logged web search results** (queries + retrieved text).
  - **Groundedness prompt:** “Given the post, the explanation, and the web search results that were available to the model: (a) Is the explanation relevant to the post? (b) Are the key claims in the explanation supported by the web search results?” Score or binary; optional short justification.
- **Log:** Per item: post, explanation, web search log, relevance score, groundedness score.

### 3.4 What to log per item

- Post identifier and text (or snapshot)
- Model explanation
- **Web search log:** list of `{query, results_or_snippets}` (or equivalent)
- Token usage / cost
- Relevance score (and optional reasoning)
- Groundedness score (and optional reasoning)

---

## 4. Data structures (reference)

### 4.1 Golden-dataset fixture (e.g. JSON)

```json
{
  "items": [
    {
      "id": "unique_id",
      "post_url": "https://bsky.app/profile/.../post/...",
      "expected_explanation": "• Fact one\n• Fact two\n..."
    }
  ]
}
```

### 4.2 No-golden fixture

```json
{
  "items": [
    {
      "id": "unique_id",
      "post_url": "https://..."
    }
  ]
}
```

### 4.3 Per-item result (both modes)

- `id`, `post_url` (or `post_id`)
- `explanation`: model output
- `token_usage`, `cost` (if available)
- **Golden:** `similarity`, `judge_score`
- **No-golden:** `relevance_score`

### 4.4 Web search log (for groundedness)

- Structure: list of tool calls with inputs and outputs, e.g. `[{ "query": "...", "snippets": ["...", "..."] }, ...]`
- Stored per eval item so the judge can use it without re-running search.

---

## 5. File layout and implementation

```
eval/
  EVAL_HARNESS.md          # this doc (methodology)
  __init__.py
  run_harness.py           # runner: auto-detects golden vs no_golden from fixture
  metrics.py               # semantic_similarity, LLM judges
  prompts.py               # judge prompt templates (placeholders)
  fixtures/
    golden.json            # sample items with expected_explanation
    no_golden.json         # sample items with post_url only
  results/                 # optional: --output eval/results/out.json
```

**What’s implemented**
- One runner: `python eval/run_harness.py --fixture eval/fixtures/golden.json` (or `no_golden.json`). Mode is inferred from the fixture (presence of `expected_explanation`).
- **Golden:** fetches post, runs explainer, computes semantic similarity (OpenAI embeddings), optional LLM judge (post + expected + agent explanation → score 1–5).
- **No-golden:** fetches post, runs explainer, LLM relevance judge (post + agent explanation → score 1–5). Judge is required (no --skip-judge).
- **Not implemented:** web search logging and groundedness judge (as per design doc, can be added later).

**Run (from project root)**
```bash
python eval/run_harness.py --fixture eval/fixtures/golden.json
python eval/run_harness.py --fixture eval/fixtures/no_golden.json --output eval/results/out.json
python eval/run_harness.py --fixture eval/fixtures/golden.json --skip-judge   # no LLM judge, only similarity
```

---

## 6. Summary

| Aspect | Golden | No-golden |
|--------|--------|-----------|
| **Input** | `expected_explanation` | Post only |
| **Metrics** | Similarity, optional judge | Relevance judge (required); groundedness judge |
| **Groundedness** | Optional (same web-search log + judge) | Yes: log web search, pass to judge |
| **Log** | Explanation, similarity, judge | Explanation, relevance (and optional groundedness) |
