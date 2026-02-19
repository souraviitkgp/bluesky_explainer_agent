"""Eval metrics: semantic similarity, LLM judge. Run from project root."""
import config
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

from eval.prompts import JUDGE_GOLDEN, JUDGE_RELEVANCE
from helpers.openai_client import chat_completion_json, get_openai_client

JUDGE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "description": "1-5"},
        "reasoning": {"type": "string"},
    },
    "required": ["score", "reasoning"],
    "additionalProperties": False,
}


def _embed(text: str) -> list[float]:
    """Always call embedding API (no special case for blank text)."""
    client = get_openai_client()
    r = client.embeddings.create(input=[text], model=config.EVAL_EMBEDDING_MODEL)
    return r.data[0].embedding


def semantic_similarity(expected: str, actual: str) -> float:
    """Cosine similarity between embeddings of expected and actual (sklearn pairwise). In [-1, 1]."""
    e = _embed(expected)
    a = _embed(actual)
    sim = sklearn_cosine_similarity([e], [a])[0, 0]
    return round(float(sim), 4)


def llm_judge_golden(post_text: str, expected: str, agent_explanation: str) -> dict:
    """LLM judge: given post, expected, and agent explanation, score 1-5. Returns {score, reasoning}."""
    prompt = JUDGE_GOLDEN.format(
        post_text=post_text,
        expected=expected,
        agent_explanation=agent_explanation,
    )
    out = chat_completion_json(
        config.EVAL_JUDGE_MODEL,
        [{"role": "user", "content": prompt}],
        JUDGE_RESPONSE_SCHEMA,
    )
    score = int(out.get("score", 0))
    return {"score": score, "reasoning": out.get("reasoning", "")}


def llm_judge_relevance(post_text: str, agent_explanation: str) -> dict:
    """LLM judge: is the explanation relevant and accurate for the post? Score 1-5. Returns {score, reasoning}."""
    prompt = JUDGE_RELEVANCE.format(
        post_text=post_text,
        agent_explanation=agent_explanation,
    )
    out = chat_completion_json(
        config.EVAL_JUDGE_MODEL,
        [{"role": "user", "content": prompt}],
        JUDGE_RESPONSE_SCHEMA,
    )
    score = int(out.get("score", 0))
    return {"score": score, "reasoning": out.get("reasoning", "")}
