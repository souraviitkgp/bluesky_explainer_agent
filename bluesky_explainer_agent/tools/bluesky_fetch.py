"""
Bluesky fetch tool for the explainer agent.
Fetches post content from a bsky.app URL and returns a plain-text summary.
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from atproto import Client

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv(Path.cwd() / ".env")


def _load_credentials():
    """Load Bluesky credentials from project root .env or env vars."""
    email = os.getenv("BLUESKY_EMAIL")
    password = os.getenv("BLUESKY_PASSWORD")
    if not email or not password:
        raise ValueError(
            "Set BLUESKY_EMAIL and BLUESKY_PASSWORD in .env (project root) or environment"
        )
    return email, password


def _bsky_url_to_at_uri(client: Client, url: str) -> str:
    """Convert bsky.app profile/post URL to AT URI."""
    m = re.match(
        r"https?://(?:www\.)?bsky\.app/profile/([^/]+)/post/([^/?#]+)",
        url.strip(),
    )
    if not m:
        raise ValueError(f"Not a bsky.app post URL: {url}")
    handle, rkey = m.group(1), m.group(2)
    resolved = client.resolve_handle(handle)
    return f"at://{resolved.did}/app.bsky.feed.post/{rkey}"


def fetch_bluesky_post(post_url: str) -> str:
    """Fetch a Bluesky post by its bsky.app URL."""
    email, password = _load_credentials()
    client = Client()
    client.login(email, password)

    post_uri = _bsky_url_to_at_uri(client, post_url)
    res = client.get_post_thread(uri=post_uri, depth=0, parent_height=0)
    thread = res.thread

    thread_type = getattr(thread, "py_type", "")
    if "notFoundPost" in thread_type:
        return f"[Post not found] URI: {getattr(thread, 'uri', post_uri)}"
    if "blockedPost" in thread_type:
        return f"[Blocked post] URI: {getattr(thread, 'uri', post_uri)}"
    if "threadViewPost" not in thread_type:
        return f"[Unknown thread type] {thread}"

    post = thread.post
    record = getattr(post, "record", None)
    text = getattr(record, "text", "") if record else ""
    return text
