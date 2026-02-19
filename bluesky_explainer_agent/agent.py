"""
Bluesky Post Explainer Agent.
Fetches post by URL, searches the web, explains in bullet points (origin, background, derivatives).
"""
import time

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.websearch import WebSearchTools

import config
from helpers.cost import estimate_openai_cost
from tools import fetch_bluesky_post

BLUESKY_EXPLAINER_INSTRUCTIONS = """You are an expert at explaining Bluesky posts to readers who may not have context.

When given a Bluesky post URL:
1. Use the fetch_bluesky_post tool to get the full post content (author, text, engagement).
2. Use web_search (and search_news if relevant) to find context: people, terms, events, memes, or trends mentioned or alluded to in the post.
3. Write a short explanation in bullet points. Use this style:
   • Lead with what the post means or refers to (define terms, name origin, summarize the idea).
   • Add bullet(s) on origin, who coined it, when, or how it gained traction.
   • If applicable, add bullet(s) on derivatives, related tokens, memes, or follow-ups.

Keep bullets concise and factual. Base explanations on the post content and your web search results. If the post is straightforward (e.g. general opinion or news), explain what it's about and any key entities or events; you don't need to force a "term + origin + derivatives" structure.
"""

agent = Agent(
    name="Bluesky Explainer",
    model=OpenAIChat(id=config.OPENAI_MODEL),
    tools=[fetch_bluesky_post, WebSearchTools()],
    instructions=BLUESKY_EXPLAINER_INSTRUCTIONS,
    markdown=True,
)


def _make_prompt(post_url: str) -> str:
    return f"""Explain this Bluesky post. Fetch its content and search for relevant context, then write your explanation in bullet points as specified in your instructions.

Post URL: {post_url}"""


def _usage_from_response(response) -> dict | None:
    """Build usage dict from agent run response.metrics. Cost from config.OPENAI_MODEL_COSTS when available."""
    usage = {}
    if response and getattr(response, "metrics", None):
        m = response.metrics
        if getattr(m, "input_tokens", None) is not None:
            usage["input_tokens"] = int(m.input_tokens)
        if getattr(m, "output_tokens", None) is not None:
            usage["output_tokens"] = int(m.output_tokens)
        if getattr(m, "total_tokens", None) is not None:
            usage["total_tokens"] = int(m.total_tokens)
        # Cost: use helper with config.OPENAI_MODEL_COSTS when we have token counts
        if usage.get("input_tokens") is not None and usage.get("output_tokens") is not None:
            estimated = estimate_openai_cost(
                config.OPENAI_MODEL,
                usage["input_tokens"],
                usage["output_tokens"],
            )
            if estimated is not None:
                usage["cost"] = estimated
        if usage.get("cost") is None and getattr(m, "cost", None) is not None:
            usage["cost"] = round(float(m.cost), 4)
        if getattr(m, "time_to_first_token", None) is not None:
            usage["time_to_first_token_seconds"] = round(float(m.time_to_first_token), 2)
        if getattr(m, "duration", None) is not None:
            usage["model_run_duration_seconds"] = round(float(m.duration), 2)
    return usage if usage else None


def explain_with_stats(post_url: str) -> dict:
    """Run the agent (sync) and return explanation plus usage and timing stats."""
    start = time.perf_counter()
    response = agent.run(_make_prompt(post_url), stream=False)
    request_elapsed_seconds = round(time.perf_counter() - start, 2)
    explanation = (response.content or "").strip() if response else ""
    return {
        "explanation": explanation,
        "usage": _usage_from_response(response),
        "request_elapsed_seconds": request_elapsed_seconds,
    }


async def explain_with_stats_async(post_url: str) -> dict:
    """Run the agent (async) and return explanation plus usage and timing stats. Use in API."""
    start = time.perf_counter()
    response = await agent.arun(_make_prompt(post_url), stream=False)
    request_elapsed_seconds = round(time.perf_counter() - start, 2)
    explanation = (response.content or "").strip() if response else ""
    return {
        "explanation": explanation,
        "usage": _usage_from_response(response),
        "request_elapsed_seconds": request_elapsed_seconds,
    }
