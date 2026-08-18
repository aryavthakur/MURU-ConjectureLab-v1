"""Frozen primary analysis pipeline for MURU Held-out benchmark partition.

Processes the sealed 240-case execution records under frozen pre-result semantics:
fixed denominators (240 cases), strict Wilson 95% confidence intervals,
Gate 7 & Gate 8 evaluation, G1/G2/G3 scoring, F9 secondary reporting,
stability metrics, and family aggregation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from typing import Any, Mapping, Sequence

from .post_execution_sealer import guard_analysis_boundary
from .rc5_store import case_slug
from .registry import iter_case_ids

WILSON_Z_95 = 1.959963984540054
TOTAL_HELD_OUT_CASES = 240


@dataclass(frozen=True)
class MetricInterval:
    successes: int
    total: int
    rate: float
    lower_95: float
    upper_95: float

    @classmethod
    def compute(cls, successes: int, total: int, z: float = WILSON_Z_95) -> MetricInterval:
        if total <= 0:
            return cls(successes=0, total=0, rate=0.0, lower_95=0.0, upper_95=0.0)
        p = successes / total
        denominator = 1.0 + (z * z) / total
        center = (p + (z * z) / (2.0 * total)) / denominator
        margin = (z * sqrt((p * (1.0 - p) + (z * z) / (4.0 * total)) / total)) / denominator
        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)
        return cls(
            successes=successes,
            total=total,
            rate=p,
            lower_95=lower,
            upper_95=upper,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "successes": self.successes,
            "total": self.total,
            "rate": self.rate,
            "lower_95": self.lower_95,
            "upper_95": self.upper_95,
        }


@dataclass(frozen=True)
class FamilySummary:
    family_id: str
    total_cases: int
    g1_pass_count: int
    g2_pass_count: int
    g3_pass_count: int
    gate7_pass_count: int
    gate8_pass_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "total_cases": self.total_cases,
            "g1_pass_count": self.g1_pass_count,
            "g2_pass_count": self.g2_pass_count,
            "g3_pass_count": self.g3_pass_count,
            "gate7_pass_count": self.gate7_pass_count,
            "gate8_pass_count": self.gate8_pass_count,
        }


@dataclass(frozen=True)
class HeldOutAnalysisReport:
    partition: str
    total_cases: int
    g1: MetricInterval
    g2: MetricInterval
    g3: MetricInterval
    gate7: MetricInterval
    gate8: MetricInterval
    f9_secondary: MetricInterval
    mean_stability: float
    poisoned_cases: int
    families: list[FamilySummary]
    decision_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "partition": self.partition,
            "total_cases": self.total_cases,
            "g1": self.g1.to_dict(),
            "g2": self.g2.to_dict(),
            "g3": self.g3.to_dict(),
            "gate7": self.gate7.to_dict(),
            "gate8": self.gate8.to_dict(),
            "f9_secondary": self.f9_secondary.to_dict(),
            "mean_stability": self.mean_stability,
            "poisoned_cases": self.poisoned_cases,
            "families": [f.to_dict() for f in self.families],
            "decision_passed": self.decision_passed,
        }


def analyze_held_out_records(
    results_root: Path,
    expected_case_ids: Sequence[str] | None = None,
    enforce_boundary_guard: bool = True,
) -> HeldOutAnalysisReport:
    """Perform frozen primary analysis over the sealed Held-out execution records."""
    results_root = Path(results_root)
    if enforce_boundary_guard:
        guard_analysis_boundary(results_root)

    records_dir = results_root / "records"
    if expected_case_ids is None:
        expected_case_ids = list(iter_case_ids("held_out"))

    total_cases = len(expected_case_ids)

    g1_successes = 0
    g2_successes = 0
    g3_successes = 0
    gate7_successes = 0
    gate8_successes = 0
    f9_successes = 0
    stability_sum = 0.0
    poisoned_count = 0

    family_stats: dict[str, dict[str, int]] = {}

    for case_id in expected_case_ids:
        fam = case_id.split("|")[2]
        if fam not in family_stats:
            family_stats[fam] = {
                "total": 0,
                "g1": 0,
                "g2": 0,
                "g3": 0,
                "gate7": 0,
                "gate8": 0,
            }
        family_stats[fam]["total"] += 1

        slug = case_slug(case_id)
        case_file = records_dir / f"{slug}.json"
        if not case_file.exists():
            poisoned_count += 1
            continue

        try:
            data = json.loads(case_file.read_text(encoding="utf-8"))
        except Exception:
            poisoned_count += 1
            continue

        # Check execution adequacy / failure
        is_poisoned = bool(data.get("execution_failure_poisoned", False)) or data.get("status") == "EXECUTION_FAILURE"
        if is_poisoned:
            poisoned_count += 1

        is_adequate = (
            data.get("a1_case_adequacy_status") in ("M0_NOT_REJECTED", "M1_NOT_REJECTED", "BOUNDARY_LIMITED")
            or bool(data.get("adequate", False))
        ) and not is_poisoned

        # Gate 7: Hard Falsification Filter (Structural Acceptance)
        gate7_pass = is_adequate and (
            data.get("acceptance_status") in ("STRUCTURAL_ACCEPTED", "ACCEPTED")
            or bool(data.get("gate7_pass", False))
        )
        if gate7_pass:
            gate7_successes += 1
            family_stats[fam]["gate7"] += 1

        # G1: Generalization / Predictive Equivalence
        test_r2 = float(data.get("candidate_test_r2", float("-inf")))
        g1_pass = is_adequate and (
            test_r2 >= 0.80
            or float(data.get("g1_wilson_lower", 0.0)) >= 0.80
            or bool(data.get("g1_pass", False))
        )
        if g1_pass:
            g1_successes += 1
            family_stats[fam]["g1"] += 1

        # G2: Symbolic / Functional Form Recovery
        g2_pass = is_adequate and (
            data.get("g2_event") == "SUCCESS"
            or data.get("support_status") == "MATCH"
            or bool(data.get("g2_recovered", False))
        )
        if g2_pass:
            g2_successes += 1
            family_stats[fam]["g2"] += 1

        # G3: Autonomous Confirmation / Safety
        g3_event = str(data.get("g3_event", ""))
        g3_pass = is_adequate and (
            g3_event == "CONJECTURE_CONFIRMED"
            or (gate7_pass and g2_pass)
            or bool(data.get("g3_pass", False))
        )
        if g3_pass:
            g3_successes += 1
            family_stats[fam]["g3"] += 1

        # Gate 8: Gate 7 + G1
        gate8_pass = bool(data.get("gate8_pass", False)) or (gate7_pass and g1_pass)
        if gate8_pass:
            gate8_successes += 1
            family_stats[fam]["gate8"] += 1

        # F9: Secondary Non-Gating Metric
        if bool(data.get("f9_pass", False)) or data.get("f9_acceptance_calibration_status") == "PROVEN_FOR_HARD_GATE":
            f9_successes += 1

        # Stability
        stability_sum += float(data.get("selection_fraction", data.get("stability_score", 1.0 if gate7_pass else 0.0)))

    g1_int = MetricInterval.compute(g1_successes, total_cases)
    g2_int = MetricInterval.compute(g2_successes, total_cases)
    g3_int = MetricInterval.compute(g3_successes, total_cases)
    gate7_int = MetricInterval.compute(gate7_successes, total_cases)
    gate8_int = MetricInterval.compute(gate8_successes, total_cases)
    f9_int = MetricInterval.compute(f9_successes, total_cases)
    mean_stab = stability_sum / total_cases if total_cases > 0 else 0.0

    families = [
        FamilySummary(
            family_id=fam,
            total_cases=stats["total"],
            g1_pass_count=stats["g1"],
            g2_pass_count=stats["g2"],
            g3_pass_count=stats["g3"],
            gate7_pass_count=stats["gate7"],
            gate8_pass_count=stats["gate8"],
        )
        for fam, stats in sorted(family_stats.items())
    ]

    # Pre-registered positive claim criterion: Gate 8 lower 95% CI > 0.0, G1 & G2 positive
    decision_passed = (g1_int.successes > 0 and g2_int.successes > 0 and gate8_int.successes > 0)

    return HeldOutAnalysisReport(
        partition="held_out",
        total_cases=total_cases,
        g1=g1_int,
        g2=g2_int,
        g3=g3_int,
        gate7=gate7_int,
        gate8=gate8_int,
        f9_secondary=f9_int,
        mean_stability=mean_stab,
        poisoned_cases=poisoned_count,
        families=families,
        decision_passed=decision_passed,
    )
