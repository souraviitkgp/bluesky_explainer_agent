"""Bluesky Post Explainer API. Run: python main.py [--port 8000]"""
import argparse
from contextlib import asynccontextmanager

from fastapi import FastAPI

import config  
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Bluesky Post Explainer API",
    description="Fetches a Bluesky post by URL, searches the web for context, and returns an explanation in bullet points.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bluesky Post Explainer API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable reload")
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
