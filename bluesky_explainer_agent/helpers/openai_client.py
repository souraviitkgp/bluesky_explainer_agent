"""Shared OpenAI client and chat completion with structured JSON output."""
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Lazy singleton: one client per process.
_openai_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _env_path = Path(__file__).resolve().parent.parent / ".env"
        if _env_path.exists():
            load_dotenv(_env_path)
        else:
            load_dotenv(Path.cwd() / ".env")
        _openai_client = OpenAI()
    return _openai_client


def chat_completion_json(
    model: str,
    messages: list[dict],
    schema: dict,
    max_tokens: int = 512,
) -> dict:
    """Call chat completion with response_format=json_schema. Returns parsed dict."""
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": schema,
            },
        },
    )
    content = (resp.choices[0].message.content or "{}").strip()
    return json.loads(content)
