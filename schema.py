from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Tuple

class Host(str, Enum):
    """Physical infrastructure the request actually ran on. Determines which
    environmental multipliers (PUE/WUE/CIF) apply."""
    AZURE = "azure"
    AWS = "aws"
 
 
class Source(str, Enum):
    """Where the usage data came from. Used for reporting and not
    calculating."""
    CHATGPT = "chatgpt"
    CODEX = "codex"
    AZURE = "azure"
    BEDROCK = "bedrock"
 
 
class Confidence(str, Enum):
    """How much this record rests on real measurement vs. an assumption
    (tier→token profile, input:output ratio guess, etc.)."""
    MEASURED = "measured"
    ESTIMATED = "estimated"

@dataclass(frozen=True)
class UsageRecord:

    model: str                       
    host: Host                       
    source: Source                   
    raw_model: Optional[str] = None

    input_tokens: float = 0.0
    output_tokens: float = 0.0
    cached_tokens: float = 0.0
    n_requests: float = 1.0

    period: Optional[Tuple[date, date]] = None
    confidence: Confidence = Confidence.ESTIMATED

    def __post_init__(self):
        if self.input_tokens < 0 or self.output_tokens < 0 or self.cached_tokens < 0:
            raise ValueError(f"Token counts must be non-negative: {self}")
        if self.cached_tokens > self.input_tokens:
            raise ValueError(f"cached_tokens cannot exceed input_tokens: {self}")
        if self.n_requests < 0:
            raise ValueError(f"n_requests must be non-negative: {self}")
        if self.period is not None and self.period[0] > self.period[1]:
            raise ValueError(f"period start must be <= period end: {self}")
        if self.raw_model is None:
            object.__setattr__(self, "raw_model", self.model)


def make_record(
    model: str,
    host: Host,
    source: Source,
    input_tokens: float,
    output_tokens: float,
    cached_tokens: float = 0.0,
    n_requests: float = 1.0,
    period: Optional[Tuple[date, date]] = None,
    confidence: Confidence = Confidence.ESTIMATED,
    raw_model: Optional[str] = None,
) -> UsageRecord:
    return UsageRecord(
        model=model,
        raw_model=raw_model,
        host=host,
        source=source,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        n_requests=n_requests,
        period=period,
        confidence=confidence,
    )
