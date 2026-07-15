from datetime import date
from typing import Optional

from assumptions import CHATGPT_TIER_PROFILE
from schema import make_record, Host, Source, Confidence, UsageRecord


# tier -> the model it actually runs (OpenAI Help Center, "ChatGPT Rate Card",
# fetched 2026-07-15). Map "instant"/"thinking"/"pro" to your real export's tier names.
CHATGPT_TIER_RAW_MODEL = {
    "instant": "gpt-5.5-instant",
    "thinking": "gpt-5.6-sol",
    "pro": "gpt-5.6-sol-pro",
}

# proxy to the closest benchmarked stand-in, same as adapters/codex.py
CHATGPT_MODEL_PROXY_MAP = {
    "gpt-5.5-instant": "gpt-4o",
    "gpt-5.6-sol": "gpt-4o",
    "gpt-5.6-sol-pro": "gpt-4o",
}


def _resolve_model_name(tier: str) -> str:
    if tier not in CHATGPT_TIER_RAW_MODEL:
        raise KeyError(
            f"ChatGPT tier '{tier}' has no entry in CHATGPT_TIER_RAW_MODEL. "
            f"Known tiers: {sorted(CHATGPT_TIER_RAW_MODEL)}."
        )
    raw_model = CHATGPT_TIER_RAW_MODEL[tier]
    return raw_model, CHATGPT_MODEL_PROXY_MAP[raw_model]


def normalize_chatgpt(
    tier: str,
    n_messages: float,
    n_requests: Optional[float] = None,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> UsageRecord:
    if tier not in CHATGPT_TIER_PROFILE:
        raise KeyError(
            f"ChatGPT tier '{tier}' has no entry in CHATGPT_TIER_PROFILE. "
            f"Known tiers: {sorted(CHATGPT_TIER_PROFILE)}."
        )
    raw_model, model = _resolve_model_name(tier)
    in_per_msg, out_per_msg = CHATGPT_TIER_PROFILE[tier]
    period = (period_start, period_end) if period_start and period_end else None

    return make_record(
        model=model,
        raw_model=raw_model,
        host=Host.AZURE,  # ChatGPT runs on OpenAI-direct infra, same as Azure OpenAI
        source=Source.CHATGPT,
        input_tokens=n_messages * in_per_msg,
        output_tokens=n_messages * out_per_msg,
        cached_tokens=0.0,  # no per-message cache breakdown available
        n_requests=n_requests if n_requests is not None else n_messages,
        period=period,
        confidence=Confidence.ESTIMATED,
    )


def normalize_chatgpt_export(rows: list) -> list:
    return [normalize_chatgpt(**row) for row in rows]
