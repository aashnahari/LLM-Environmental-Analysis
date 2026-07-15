from dataclasses import dataclass
from typing import Dict
 
from assumptions import CACHE_DISCOUNT
from schema import UsageRecord


@dataclass(frozen=True)
class ModelCoefficients:
    fixed_wh: float     # per-query overhead, independent of tokens
    rate_in_wh: float   # Wh per input token
    rate_out_wh: float  # Wh per output token

COEFFICIENTS: Dict[str, ModelCoefficients] = {
    "gpt-4o":            ModelCoefficients(0.12098, 130.94e-6,  963.08e-6),
    "claude-3.7-sonnet": ModelCoefficients(0.11804, 146.65e-6, 2724.31e-6),
}


class UnknownModelError(KeyError):
    """Raised when a model has no coefficients."""


def resolve_coefficients(model: str) -> ModelCoefficients:
    if model in COEFFICIENTS:
        return COEFFICIENTS[model]
    raise UnknownModelError(
        f"No coefficients for '{model}'. Add it to COEFFICIENTS."
    )

def energy_wh(record: UsageRecord) -> float:
    """Estimate energy (Wh) from token fields."""
    coeffs = resolve_coefficients(record.model)
    fresh_input = record.input_tokens - record.cached_tokens
    return (
        coeffs.fixed_wh
        + coeffs.rate_in_wh * (fresh_input + CACHE_DISCOUNT * record.cached_tokens)
        + coeffs.rate_out_wh * record.output_tokens
    )