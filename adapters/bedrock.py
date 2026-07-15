from datetime import date
from typing import Optional

from assumptions import BEDROCK_INPUT_OUTPUT_RATIO
from schema import make_record, Host, Source, Confidence, UsageRecord


# Bedrock model ID -> canonical model name. IDs are account-specific
# (e.g. versioned strings); this entry is a plausible example, unconfirmed.
BEDROCK_MODEL_NAME_MAP = {
    "anthropic.claude-3-7-sonnet-20250219-v1:0": "claude-3.7-sonnet",
}

# $ per 1M tokens (input, output). Anthropic prices Claude on Bedrock at
# parity with its direct API -- verify against your account/region.
BEDROCK_RATES_PER_1M = {
    "anthropic.claude-3-7-sonnet-20250219-v1:0": (3.00, 15.00),
}


def _resolve_model_name(raw_model: str) -> str:
    if raw_model in BEDROCK_MODEL_NAME_MAP:
        return BEDROCK_MODEL_NAME_MAP[raw_model]
    raise KeyError(
        f"Bedrock model '{raw_model}' has no entry in BEDROCK_MODEL_NAME_MAP. "
        f"Add a mapping from this model ID to a canonical model name."
    )


def normalize_bedrock_from_tokens(
    raw_model: str,
    input_tokens: float,
    output_tokens: float,
    cached_tokens: float = 0.0,
    n_requests: float = 1.0,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> UsageRecord:
    model = _resolve_model_name(raw_model)
    period = (period_start, period_end) if period_start and period_end else None

    return make_record(
        model=model,
        raw_model=raw_model,
        host=Host.AWS,
        source=Source.BEDROCK,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        n_requests=n_requests,
        period=period,
        confidence=Confidence.MEASURED,
    )


def normalize_bedrock_from_spend(
    raw_model: str,
    total_usd: float,
    n_requests: float = 1.0,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> UsageRecord:
    # spend alone can't tell you the input:output split -- roughest of the four sources
    if raw_model not in BEDROCK_RATES_PER_1M:
        raise KeyError(
            f"Bedrock model '{raw_model}' has no entry in BEDROCK_RATES_PER_1M. "
            f"Add its published per-1M-token price."
        )
    in_rate, out_rate = BEDROCK_RATES_PER_1M[raw_model]
    ratio = BEDROCK_INPUT_OUTPUT_RATIO  # input_tokens = ratio * output_tokens

    output_tokens = total_usd * 1_000_000 / (ratio * in_rate + out_rate)
    input_tokens = ratio * output_tokens

    model = _resolve_model_name(raw_model)
    period = (period_start, period_end) if period_start and period_end else None

    return make_record(
        model=model,
        raw_model=raw_model,
        host=Host.AWS,
        source=Source.BEDROCK,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=0.0,  # spend-only exports don't break out cache reads
        n_requests=n_requests,
        period=period,
        confidence=Confidence.ESTIMATED,
    )


def normalize_bedrock_export(rows: list) -> list:
    return [
        normalize_bedrock_from_tokens(**row) if "input_tokens" in row
        else normalize_bedrock_from_spend(**row)
        for row in rows
    ]
