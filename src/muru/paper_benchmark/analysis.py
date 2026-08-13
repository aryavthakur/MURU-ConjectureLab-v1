"""Endpoint reconstruction and prospectively frozen G1/G2/G3 decision logic."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Sequence

from .adequacy import CaseAdequacyStatus, adequacy_satisfies_g1
from .registry import endpoint_case_count, resolve_case_id


def endpoint_denominator(endpoint_name: str) -> int:
    return endpoint_case_count(endpoint_name)


def m0_accepted_from_adequacy(status: CaseAdequacyStatus | str) -> bool:
    """Amendment A1: the only admissible source of ``CaseOutcome.m0_accepted``.

    A case may contribute M0 acceptance to G1 only when its Amendment A1
    adequacy status is ``M0_NOT_REJECTED``.  Indeterminate and failure states
    leave the adequacy component of G1 unsatisfied.
    """
    return adequacy_satisfies_g1(status)


def endpoint_applies(endpoint_name: str, case_id: str) -> bool:
    _, variant, _ = resolve_case_id(case_id)
    return endpoint_name in variant.endpoint_names


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    g_spearman: float
    trajectory_mae: float
    per_energy_mean_mae: float
    m0_accepted: bool
    family_recovered: bool
    unsupported_non_mass: bool
    richer_family: bool
    adversarial_flagged: bool
    null_flagged: bool

    @property
    def scalar_competent(self) -> bool:
        return self.g_spearman >= 0.80 and self.trajectory_mae <= 0.80 * self.per_energy_mean_mae and self.m0_accepted


@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float


@dataclass(frozen=True)
class GateResult:
    name: str
    successes: int
    total: int
    interval: Interval
    passed: bool


@dataclass(frozen=True)
class DecisionReport:
    positive_claim: bool
    gates: dict[str, GateResult]
    failed_gates: tuple[str, ...]


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> Interval:
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError("invalid binomial count")
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return Interval(max(0.0, center - margin), min(1.0, center + margin))


def classify_negative_control(outcome: CaseOutcome) -> str | None:
    family, variant, _ = resolve_case_id(outcome.case_id)
    if family.code == "F07":
        return "false_extra_structure" if outcome.unsupported_non_mass or outcome.richer_family else None
    if family.code == "F19":
        if variant.code == "F19C":
            return "false_null_structure" if not outcome.null_flagged else None
        return "false_null_structure" if outcome.unsupported_non_mass or outcome.richer_family else None
    if family.code == "F20":
        return "false_adversarial_structure" if not outcome.adversarial_flagged else None
    return None


def _selected(outcomes: Sequence[CaseOutcome], endpoint: str) -> list[CaseOutcome]:
    return [outcome for outcome in outcomes if endpoint_applies(endpoint, outcome.case_id)]


def _gate_lower(name: str, successes: int, total: int, threshold: float) -> GateResult:
    interval = wilson_interval(successes, total)
    return GateResult(name, successes, total, interval, interval.lower >= threshold)


def _gate_upper(name: str, errors: int, total: int, threshold: float) -> GateResult:
    interval = wilson_interval(errors, total)
    return GateResult(name, total - errors, total, interval, interval.upper <= threshold)


def umbrella_decision(outcomes: Sequence[CaseOutcome]) -> DecisionReport:
    scalar = _selected(outcomes, "scalar_competence")
    family = _selected(outcomes, "family_recovery")
    safety = _selected(outcomes, "principal_structural_safety")
    g1 = _gate_lower("G1", sum(outcome.scalar_competent for outcome in scalar), endpoint_denominator("scalar_competence"), 0.70)
    g2 = _gate_lower("G2", sum(outcome.family_recovered for outcome in family), endpoint_denominator("family_recovery"), 0.70)
    g3 = _gate_upper("G3", sum(classify_negative_control(outcome) is not None for outcome in safety), endpoint_denominator("principal_structural_safety"), 0.15)
    gates = {gate.name: gate for gate in (g1, g2, g3)}
    failed = tuple(name for name, gate in gates.items() if not gate.passed)
    return DecisionReport(positive_claim=not failed, gates=gates, failed_gates=failed)
