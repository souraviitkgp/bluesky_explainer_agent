"""Async API routes for the Bluesky Explainer."""
import re

from fastapi import APIRouter, HTTPException

from agent import explain_with_stats_async
from schemas import ExplainRequest, ExplainResponse, TokenUsage

BSKY_POST_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?bsky\.app/profile/[^/]+/post/[^/?#]+$"
)

router = APIRouter(tags=["explain"])


def _validate_post_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="post_url is required")
    if not BSKY_POST_URL_PATTERN.match(url):
        raise HTTPException(
            status_code=400,
            detail="post_url must be a bsky.app post URL (e.g. https://bsky.app/profile/HANDLE/post/RKEY)",
        )
    return url


@router.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Explain a Bluesky post",
)
async def explain_post(body: ExplainRequest):
    """Explain a Bluesky post. Pass the post URL in the request body. Runs asynchronously."""
    url = _validate_post_url(body.post_url)
    try:
        result = await explain_with_stats_async(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    usage = result.get("usage") or {}
    token_usage = None
    if any(
        usage.get(k) is not None
        for k in ("input_tokens", "output_tokens", "total_tokens", "cost")
    ):
        token_usage = TokenUsage(
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
            cost=usage.get("cost"),
        )
    ttft = usage.get("time_to_first_token_seconds")
    model_dur = usage.get("model_run_duration_seconds")
    return ExplainResponse(
        post_url=url,
        explanation=result["explanation"],
        request_elapsed_seconds=result["request_elapsed_seconds"],
        token_usage=token_usage,
        time_to_first_token_seconds=round(ttft, 2) if ttft is not None else None,
        model_run_duration_seconds=round(model_dur, 2) if model_dur is not None else None,
    )
