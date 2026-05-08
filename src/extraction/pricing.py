"""Static pricing table for extraction models.

Not accounting truth. Prices are sourced from provider pricing pages at time of
writing and may change. PRICING_TABLE_VERSION and PRICING_TABLE_SOURCE track
provenance so every extraction attempt records which pricing snapshot was used.
"""

from typing import Optional

PRICING_TABLE_VERSION = "2026-05-07"
PRICING_TABLE_SOURCE = "manual_static_provider_pricing_2026_05_07"

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash":       {"input_per_1m": 0.30, "output_per_1m": 2.50},
    "gemini-2.5-flash-lite":  {"input_per_1m": 0.10, "output_per_1m": 0.40},
    "gemini-3-flash-preview": {"input_per_1m": 0.50, "output_per_1m": 3.00},
    "gpt-5.4-nano":           {"input_per_1m": 0.20, "output_per_1m": 1.25},
    "gpt-5.4-mini":           {"input_per_1m": 0.75, "output_per_1m": 4.50},
}


def get_model_pricing(model: str) -> Optional[dict[str, float]]:
    """Get pricing for a model. Returns None if unknown (cost_estimate_usd will be null)."""
    return MODEL_PRICING.get(model)


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    """Calculate estimated cost in USD. Returns None if model unknown."""
    pricing = get_model_pricing(model)
    if pricing is None:
        return None
    return (prompt_tokens * pricing["input_per_1m"] + completion_tokens * pricing["output_per_1m"]) / 1_000_000
