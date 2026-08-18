"""Machine-readable, sealed truth records for paper benchmark cases."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TruthRecord:
    case_id: str
    partition: str
    family: str
    variant: str
    seeds: dict[str, int]
    phi: dict[str, float | str]
    g_definition: str | None
    g_by_compound: dict[str, float]
    descriptor_relationship: str | None
    active_variables: list[str]
    mathematical_family: str | None
    coefficients: dict[str, float]
    exponents: dict[str, float]
    noise: dict[str, float | str]
    missingness: dict[str, float | str]
    scalar_truth_defined: bool
    m0_adequacy_truth: str
    symbolic_truth_kind: str
    applicable_endpoints: list[str]
    expected_behavior: str
    truth_version: str = "paper-benchmark-truth-1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
