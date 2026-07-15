from dataclasses import dataclass
from typing import Callable, Dict, Hashable, Iterable

from energy_model import energy_wh
from infra_factors import footprint
from schema import Confidence, UsageRecord


@dataclass(frozen=True)
class RecordFootprint:
    energy_wh: float
    water_l: float
    carbon_kg: float


def full_footprint(record: UsageRecord) -> RecordFootprint:
    e = energy_wh(record)
    f = footprint(e, record.host)
    return RecordFootprint(energy_wh=e, water_l=f.water_l, carbon_kg=f.carbon_kg)


@dataclass
class Totals:
    energy_wh: float = 0.0
    water_l: float = 0.0
    carbon_kg: float = 0.0
    n_requests: float = 0.0
    n_records: int = 0
    n_estimated: int = 0  # rested on an assumption, not a measurement

    def add(self, record: UsageRecord, fp: RecordFootprint) -> None:
        self.energy_wh += fp.energy_wh
        self.water_l += fp.water_l
        self.carbon_kg += fp.carbon_kg
        self.n_requests += record.n_requests
        self.n_records += 1
        if record.confidence == Confidence.ESTIMATED:
            self.n_estimated += 1


def aggregate_by(
    records: Iterable[UsageRecord], key_fn: Callable[[UsageRecord], Hashable]
) -> Dict[Hashable, Totals]:
    buckets: Dict[Hashable, Totals] = {}
    for record in records:
        key = key_fn(record)
        buckets.setdefault(key, Totals()).add(record, full_footprint(record))
    return buckets


def total(records: Iterable[UsageRecord]) -> Totals:
    return aggregate_by(records, key_fn=lambda r: "total").get("total", Totals())


def by_source(records: Iterable[UsageRecord]) -> Dict[Hashable, Totals]:
    return aggregate_by(records, key_fn=lambda r: r.source)


def by_model(records: Iterable[UsageRecord]) -> Dict[Hashable, Totals]:
    return aggregate_by(records, key_fn=lambda r: r.model)


def by_host(records: Iterable[UsageRecord]) -> Dict[Hashable, Totals]:
    return aggregate_by(records, key_fn=lambda r: r.host)
