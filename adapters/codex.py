from datetime import date
from typing import Optional

from schema import make_record, Host, Source, Confidence, UsageRecord


# Credits per 1M tokens (input, cached, output). OpenAI Help Center, "Codex
# rate card", fetched 2026-07-15: help.openai.com/en/articles/20001106
CODEX_RATES_PER_1M = {
    "gpt-5.6-sol":         (125.00, 12.50, 750.0),
    "gpt-5.6-terra":       (62.50,   6.25, 375.0),
    "gpt-5.6-luna":        (25.00,   2.50, 150.0),
    "gpt-5.5":             (125.00, 12.50, 750.0),
    "gpt-5.5-cyber":       (500.00, 50.00, 3000.0),
    "gpt-5.4":             (62.50,   6.25, 375.0),
    "gpt-5.4-mini":        (18.75,  1.875, 112.5),
    "gpt-5.3-codex":       (43.75,  4.375, 350.0),
    "gpt-5.2":             (43.75,  4.375, 350.0),
}

# energy_model.COEFFICIENTS only covers gpt-4o/claude-3.7-sonnet, so current
# Codex models proxy to the closest stand-in -- a guess, not a measurement.
CODEX_MODEL_PROXY_MAP = {
    "gpt-5.6-sol":   "gpt-4o",
    "gpt-5.6-terra": "gpt-4o",
    "gpt-5.6-luna":  "gpt-4o",
    "gpt-5.5":       "gpt-4o",
    "gpt-5.5-cyber": "gpt-4o",
    "gpt-5.4":       "gpt-4o",
    "gpt-5.4-mini":  "gpt-4o",
    "gpt-5.3-codex": "gpt-4o",
    "gpt-5.2":       "gpt-4o",
}


def _resolve_model_name(raw_model: str) -> str:
    if raw_model in CODEX_MODEL_PROXY_MAP:
        return CODEX_MODEL_PROXY_MAP[raw_model]
    raise KeyError(
        f"Codex model '{raw_model}' has no entry in CODEX_MODEL_PROXY_MAP. "
        f"Add a mapping from this model name to a benchmarked stand-in."
    )


def normalize_codex_from_tokens(
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
        host=Host.AZURE,  # Codex runs on OpenAI-direct infra, same as Azure OpenAI
        source=Source.CODEX,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        n_requests=n_requests,
        period=period,
        confidence=Confidence.MEASURED,
    )


def normalize_codex_from_credits(
    raw_model: str,
    input_credits: float,
    cached_credits: float,
    output_credits: float,
    n_requests: float = 1.0,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> UsageRecord:
    # invert per token type -- rates differ by type, so no flat credit:token ratio
    if raw_model not in CODEX_RATES_PER_1M:
        raise KeyError(
            f"Codex model '{raw_model}' has no entry in CODEX_RATES_PER_1M. "
            f"Add its published per-1M-token credit rates."
        )
    in_rate, cached_rate, out_rate = CODEX_RATES_PER_1M[raw_model]
    input_tokens = input_credits / in_rate * 1_000_000
    cached_tokens = cached_credits / cached_rate * 1_000_000
    output_tokens = output_credits / out_rate * 1_000_000

    model = _resolve_model_name(raw_model)
    period = (period_start, period_end) if period_start and period_end else None

    return make_record(
        model=model,
        raw_model=raw_model,
        host=Host.AZURE,
        source=Source.CODEX,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        n_requests=n_requests,
        period=period,
        confidence=Confidence.ESTIMATED,
    )


def normalize_codex_export(rows: list) -> list:
    return [
        normalize_codex_from_tokens(**row) if "input_tokens" in row
        else normalize_codex_from_credits(**row)
        for row in rows
    ]
