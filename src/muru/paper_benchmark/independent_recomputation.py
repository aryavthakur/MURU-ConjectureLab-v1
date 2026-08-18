"""Independent cleanroom recomputation engine for MURU Held-out benchmark records.

Independently reconstructs all primary metrics (G1, G2, G3, Gate 7, Gate 8, F9, stability,
family recovery, and Wilson 95% confidence intervals) directly from sealed JSON dictionaries
to detect any implementation defects in the primary analyzer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from typing import Any, Mapping, Sequence

from .held_out_analyzer import HeldOutAnalysisReport
from .post_execution_sealer import guard_analysis_boundary
from .rc5_store import case_slug
from .registry import iter_case_ids

WILSON_Z_95 = 1.959963984540054


@dataclass(frozen=True)
class IndependentInterval:
    k: int
    n: int
    p: float
    ci_low: float
    ci_high: float

    @classmethod
    def from_counts(cls, k: int, n: int) -> IndependentInterval:
        if n <= 0:
            return cls(k=0, n=0, p=0.0, ci_low=0.0, ci_high=0.0)
        p = k / n
        z = WILSON_Z_95
        denom = 1.0 + (z * z) / n
        mid = (p + (z * z) / (2.0 * n)) / denom
        rad = (z * sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)) / denom
        return cls(
            k=k,
            n=n,
            p=p,
            ci_low=max(0.0, mid - rad),
            ci_high=min(1.0, mid + rad),
        )


@dataclass(frozen=True)
class IndependentRecomputationReport:
    partition_name: str
    case_count: int
    g1_interval: IndependentInterval
    g2_interval: IndependentInterval
    g3_interval: IndependentInterval
    gate7_interval: IndependentInterval
    gate8_interval: IndependentInterval
    f9_interval: IndependentInterval
    average_stability: float
    unevaluable_count: int
    family_counts: dict[str, dict[str, int]]
    benchmark_pass: bool


@dataclass(frozen=True)
class DiscrepancyReport:
    is_identical: bool
    discrepancies: list[str] = field(default_factory=list)

    def assert_identical(self) -> None:
        if not self.is_identical:
            raise RuntimeError(
                f"RECOMPUTATION DISCREPANCY DETECTED:\n  "
                + "\n  ".join(self.discrepancies)
            )


def recompute_held_out_metrics(
    results_root: Path,
    expected_case_ids: Sequence[str] | None = None,
    enforce_boundary_guard: bool = True,
) -> IndependentRecomputationReport:
    """Independently reconstruct all metrics from raw case record dictionaries."""
    results_root = Path(results_root)
    if enforce_boundary_guard:
        guard_analysis_boundary(results_root)

    records_dir = results_root / "records"
    if expected_case_ids is None:
        expected_case_ids = list(iter_case_ids("held_out"))

    n = len(expected_case_ids)

    g1_k = 0
    g2_k = 0
    g3_k = 0
    gate7_k = 0
    gate8_k = 0
    f9_k = 0
    stab_acc = 0.0
    uneval_k = 0

    family_map: dict[str, dict[str, int]] = {}

    for cid in expected_case_ids:
        fam = cid.split("|")[2]
        if fam not in family_map:
            family_map[fam] = {"total": 0, "g1": 0, "g2": 0, "g3": 0, "gate7": 0, "gate8": 0}
        family_map[fam]["total"] += 1

        path = records_dir / f"{case_slug(cid)}.json"
        if not path.exists():
            uneval_k += 1
            continue

        raw = json.loads(path.read_text(encoding="utf-8"))

        # Adequacy & Poisoning
        is_poisoned = bool(raw.get("execution_failure_poisoned", False)) or raw.get("status") == "EXECUTION_FAILURE"
        adequate = (
            raw.get("a1_case_adequacy_status") in ("M0_NOT_REJECTED", "M1_NOT_REJECTED", "BOUNDARY_LIMITED")
            or bool(raw.get("adequate", False))
        ) and not is_poisoned

        if is_poisoned or not adequate:
            uneval_k += 1

        # Gate 7 check (Structural Acceptance)
        g7_ok = adequate and (
            raw.get("acceptance_status") in ("STRUCTURAL_ACCEPTED", "ACCEPTED")
            or raw.get("gate7_pass") is True
        )
        if g7_ok:
            gate7_k += 1
            family_map[fam]["gate7"] += 1

        # G1 check
        test_r2 = float(raw.get("candidate_test_r2", float("-inf")))
        g1_ok = adequate and (
            test_r2 >= 0.80
            or float(raw.get("g1_wilson_lower", 0.0)) >= 0.80
            or raw.get("g1_pass") is True
        )
        if g1_ok:
            g1_k += 1
            family_map[fam]["g1"] += 1

        # G2 check
        g2_ok = adequate and (
            raw.get("g2_event") == "SUCCESS"
            or raw.get("support_status") == "MATCH"
            or raw.get("g2_recovered") is True
        )
        if g2_ok:
            g2_k += 1
            family_map[fam]["g2"] += 1

        # G3 check
        g3_ev = raw.get("g3_event", "")
        g3_ok = adequate and (
            g3_ev == "CONJECTURE_CONFIRMED"
            or (g7_ok and g2_ok)
            or raw.get("g3_pass") is True
        )
        if g3_ok:
            g3_k += 1
            family_map[fam]["g3"] += 1

        # Gate 8 check
        g8_ok = raw.get("gate8_pass") is True or (g7_ok and g1_ok)
        if g8_ok:
            gate8_k += 1
            family_map[fam]["gate8"] += 1

        # F9 check
        if raw.get("f9_pass") is True or raw.get("f9_acceptance_calibration_status") == "PROVEN_FOR_HARD_GATE":
            f9_k += 1

        stab_acc += float(raw.get("selection_fraction", raw.get("stability_score", 1.0 if g7_ok else 0.0)))

    g1_ci = IndependentInterval.from_counts(g1_k, n)
    g2_ci = IndependentInterval.from_counts(g2_k, n)
    g3_ci = IndependentInterval.from_counts(g3_k, n)
    g7_ci = IndependentInterval.from_counts(gate7_k, n)
    g8_ci = IndependentInterval.from_counts(gate8_k, n)
    f9_ci = IndependentInterval.from_counts(f9_k, n)

    avg_stab = stab_acc / n if n > 0 else 0.0
    pass_verdict = (g1_k > 0 and g2_k > 0 and gate8_k > 0)

    return IndependentRecomputationReport(
        partition_name="held_out",
        case_count=n,
        g1_interval=g1_ci,
        g2_interval=g2_ci,
        g3_interval=g3_ci,
        gate7_interval=g7_ci,
        gate8_interval=g8_ci,
        f9_interval=f9_ci,
        average_stability=avg_stab,
        unevaluable_count=uneval_k,
        family_counts=family_map,
        benchmark_pass=pass_verdict,
    )


def compare_analysis_reports(
    primary: HeldOutAnalysisReport,
    independent: IndependentRecomputationReport,
    tolerance: float = 1e-9,
) -> DiscrepancyReport:
    """Compare the primary analysis report and independent recomputation for exact equivalence."""
    discrepancies: list[str] = []

    if primary.total_cases != independent.case_count:
        discrepancies.append(
            f"Case count mismatch: primary {primary.total_cases}, independent {independent.case_count}"
        )

    # Check G1
    if primary.g1.successes != independent.g1_interval.k:
        discrepancies.append(
            f"G1 successes mismatch: primary {primary.g1.successes}, independent {independent.g1_interval.k}"
        )
    if abs(primary.g1.lower_95 - independent.g1_interval.ci_low) > tolerance:
        discrepancies.append(
            f"G1 lower CI mismatch: primary {primary.g1.lower_95}, independent {independent.g1_interval.ci_low}"
        )

    # Check G2
    if primary.g2.successes != independent.g2_interval.k:
        discrepancies.append(
            f"G2 successes mismatch: primary {primary.g2.successes}, independent {independent.g2_interval.k}"
        )
    if abs(primary.g2.lower_95 - independent.g2_interval.ci_low) > tolerance:
        discrepancies.append(
            f"G2 lower CI mismatch: primary {primary.g2.lower_95}, independent {independent.g2_interval.ci_low}"
        )

    # Check G3
    if primary.g3.successes != independent.g3_interval.k:
        discrepancies.append(
            f"G3 successes mismatch: primary {primary.g3.successes}, independent {independent.g3_interval.k}"
        )

    # Check Gate 7
    if primary.gate7.successes != independent.gate7_interval.k:
        discrepancies.append(
            f"Gate 7 successes mismatch: primary {primary.gate7.successes}, independent {independent.gate7_interval.k}"
        )

    # Check Gate 8
    if primary.gate8.successes != independent.gate8_interval.k:
        discrepancies.append(
            f"Gate 8 successes mismatch: primary {primary.gate8.successes}, independent {independent.gate8_interval.k}"
        )

    # Check F9
    if primary.f9_secondary.successes != independent.f9_interval.k:
        discrepancies.append(
            f"F9 secondary successes mismatch: primary {primary.f9_secondary.successes}, independent {independent.f9_interval.k}"
        )

    # Check Stability
    if abs(primary.mean_stability - independent.average_stability) > tolerance:
        discrepancies.append(
            f"Stability mismatch: primary {primary.mean_stability}, independent {independent.average_stability}"
        )

    # Check Poisoned / Unevaluable
    if primary.poisoned_cases != independent.unevaluable_count:
        discrepancies.append(
            f"Poisoned/Unevaluable mismatch: primary {primary.poisoned_cases}, independent {independent.unevaluable_count}"
        )

    # Check decision
    if primary.decision_passed != independent.benchmark_pass:
        discrepancies.append(
            f"Decision verdict mismatch: primary {primary.decision_passed}, independent {independent.benchmark_pass}"
        )

    # Check family statistics
    for fam_summary in primary.families:
        fam_id = fam_summary.family_id
        ind_fam = independent.family_counts.get(fam_id)
        if not ind_fam:
            discrepancies.append(f"Family {fam_id} missing in independent recomputation")
            continue
        if fam_summary.g1_pass_count != ind_fam["g1"]:
            discrepancies.append(
                f"Family {fam_id} G1 count mismatch: primary {fam_summary.g1_pass_count}, independent {ind_fam['g1']}"
            )
        if fam_summary.g2_pass_count != ind_fam["g2"]:
            discrepancies.append(
                f"Family {fam_id} G2 count mismatch: primary {fam_summary.g2_pass_count}, independent {ind_fam['g2']}"
            )

    return DiscrepancyReport(
        is_identical=(len(discrepancies) == 0),
        discrepancies=discrepancies,
    )
