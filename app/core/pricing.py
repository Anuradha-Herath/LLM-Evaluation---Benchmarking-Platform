from typing import Dict, Optional

# Default token pricing lookup per 1,000,000 tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input_per_1m": 0.15, "output_per_1m": 0.60},
    "gpt-4o": {"input_per_1m": 2.50, "output_per_1m": 10.00},
    "gpt-3.5-turbo": {"input_per_1m": 0.50, "output_per_1m": 1.50},
    "claude-3-5-sonnet": {"input_per_1m": 3.00, "output_per_1m": 15.00},
    "llama3": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    "mock-model-v1": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    "mock-model-v2": {"input_per_1m": 0.01, "output_per_1m": 0.02},
}


def calculate_estimated_cost(
    model: str,
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    custom_pricing: Optional[Dict[str, Dict[str, float]]] = None,
) -> float:
    """
    Calculates the estimated cost in USD based on input/output token counts and model pricing.

    :param model: Model identifier string.
    :param input_tokens: Number of prompt/input tokens.
    :param output_tokens: Number of completion/output tokens.
    :param custom_pricing: Optional custom pricing dict override.
    :return: Estimated cost in USD rounded to 6 decimal places.
    """
    if not input_tokens and not output_tokens:
        return 0.0

    pricing_table = custom_pricing or MODEL_PRICING
    model_key = model.lower()

    # Find matching pricing rule or default to 0.0 for local/unknown models
    rates = pricing_table.get(model_key, {"input_per_1m": 0.0, "output_per_1m": 0.0})

    in_cost = ((input_tokens or 0) / 1_000_000.0) * rates.get("input_per_1m", 0.0)
    out_cost = ((output_tokens or 0) / 1_000_000.0) * rates.get("output_per_1m", 0.0)

    return round(in_cost + out_cost, 6)
