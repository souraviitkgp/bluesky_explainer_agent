"""Load environment from project root .env and app config."""
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv(Path.cwd() / ".env")

# Model for the explainer agent (change here if needed)
OPENAI_MODEL = "gpt-4o"

# OpenAI model costs: USD per 1M tokens (input, output). Source: https://openai.com/api/pricing
OPENAI_MODEL_COSTS: dict[str, tuple[float, float]] = {
    # GPT-5 / flagship (2025)
    "gpt-5.2": (1.75, 14.00),
    "gpt-5.2-pro": (21.00, 168.00),
    "gpt-5-mini": (0.25, 2.00),
    # GPT-4 family
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (3.00, 12.00),
    "gpt-4.1-mini": (0.80, 3.20),
    "gpt-4.1-nano": (0.20, 0.80),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
}

# Eval harness
EVAL_EMBEDDING_MODEL = "text-embedding-3-small"
EVAL_JUDGE_MODEL = "gpt-4o-mini"
EVAL_RESULTS_DIR = "eval/results"
