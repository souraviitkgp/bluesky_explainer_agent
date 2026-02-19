"""Cost estimation using config model costs."""
import config


def estimate_openai_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    costs: dict[str, tuple[float, float]] | None = None,
) -> float | None:
    """Estimate cost in USD from token counts. Uses config.OPENAI_MODEL_COSTS by default.

    costs: optional dict of model_id -> (input_usd_per_1M, output_usd_per_1M). If None, uses config.OPENAI_MODEL_COSTS.
    Returns None if model_id not in costs.
    """
    if costs is None:
        costs = config.OPENAI_MODEL_COSTS
    if model_id not in costs:
        return None
    inp_per_m, out_per_m = costs[model_id]
    cost = (input_tokens * inp_per_m + output_tokens * out_per_m) / 1_000_000
    return round(cost, 4)
