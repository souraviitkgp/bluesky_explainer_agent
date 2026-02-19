"""Request/response models for the Explainer API."""
from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    """Request body for POST /explain."""

    post_url: str = Field(
        ...,
        description="Bluesky post URL (e.g. https://bsky.app/profile/HANDLE/post/RKEY)",
        examples=["https://bsky.app/profile/trumpstaxes.com/post/3mbrz32dais2i"],
    )


class TokenUsage(BaseModel):
    """Token counts and optional cost from the model run."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = Field(default=None, description="Estimated cost when available (rounded)")


class ExplainResponse(BaseModel):
    """Response for /explain."""

    post_url: str
    explanation: str
    request_elapsed_seconds: float = Field(
        description="Total request wall-clock time in seconds (rounded)"
    )
    token_usage: TokenUsage | None = Field(
        default=None, description="Token counts and cost when available"
    )
    time_to_first_token_seconds: float | None = Field(
        default=None, description="Seconds until first token from model (rounded)"
    )
    model_run_duration_seconds: float | None = Field(
        default=None, description="Agent/model run duration from SDK metrics (rounded)"
    )
