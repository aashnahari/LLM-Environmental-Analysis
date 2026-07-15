from datetime import date
from typing import Optional
from schema import make_record, Host, Source, Confidence, UsageRecord


AZURE_MODEL_NAME_MAP = {
    "gpt-4o-deployment":       "gpt-4o", #need to know what to call this
}


def _resolve_model_name(raw_model: str) -> str:
    if raw_model in AZURE_MODEL_NAME_MAP:
        return AZURE_MODEL_NAME_MAP[raw_model]
    raise KeyError(
        f"Azure model '{raw_model}' has no entry in AZURE_MODEL_NAME_MAP. "
        f"Add a mapping from this deployment name to a canonical model name."
    )

def normalize_azure_row(
    raw_model: str, #guess
    input_tokens: float, #guess
    output_tokens: float, #guess
    cached_tokens: float = 0.0, #guess
    n_requests: float = 1.0, #guess
    period_start: Optional[date] = None, #guess
    period_end: Optional[date] = None, #guess
) -> UsageRecord:
    model = _resolve_model_name(raw_model)
    period = (period_start, period_end) if period_start and period_end else None
 
    return make_record(
        model=model,
        raw_model=raw_model, 
        host=Host.AZURE,      
        source=Source.AZURE,   
        input_tokens=input_tokens, 
        output_tokens=output_tokens, 
        cached_tokens=cached_tokens, 
        n_requests=n_requests,
        period=period,
        confidence=Confidence.MEASURED,  
    )

def normalize_azure_export(rows: list) -> list:
    """Apply normalize_azure_row across a full export. PLACEHOLDER -- once
    you know the real export shape (e.g. a list of dicts from a CSV reader),
    this becomes a simple comprehension unpacking each row's fields into
    normalize_azure_row(**row) or similar."""
    return [normalize_azure_row(**row) for row in rows]
 