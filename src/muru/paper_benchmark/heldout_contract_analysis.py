"""The restored Held-out primary analysis: frozen scorers, invoked.

This module replaces the superseded ``held_out_analyzer``.  Its governing
principle is that it *decides nothing*.  Every endpoint number here is the
return value of a frozen scorer, and every frozen scorer's length assertion is
allowed to fire:

* ``rc5_g1_bridge.score_g1``  raises unless the sequence is exactly 164
* ``rc3_scoring.score_g2``    raises unless the sequence is exactly 144
* ``rc3_scoring.score_g3``    raises unless the sequence is exactly 36

Those three guards exist precisely to catch the denominator drift that
produced the superseded analysis, and they survived unfired only because the
frozen scorers were never invoked.

**Gate 7** is the ceiling comparison at position 7 of the ordered
structural-acceptance predicate, never structural acceptance itself and never a
falsification cascade (A3.5 §6.9.3).  **Gate 8** is ``check_gate8`` over the
four hard rungs ``{F1, F4, F7, F10}``, fail-closed; **G1 is an endpoint, not a
gate, and appears nowhere in it** (A3.5 §6.9.4).  Both reached-sets and both
verdicts are read off the frozen predicate's own ``gate_reached`` output rather
than reconstructed, so the short-circuit order cannot drift.

**G1 note.**  The sealed record schema ``muru-rc5-case-record-2.0.0`` persists
no G1 observable.  Where the exact per-case observables are unavailable, G1 is
scored in ``UPPER_BOUND`` mode: the two unrecoverable conjuncts are set to
their most favourable admissible values and ``score_g1`` is invoked on that
explicitly optimistic sequence.  What it returns is therefore the largest
competent count and the largest Wilson lower bound the evidence admits, never a
point estimate.  Because Wilson lower is monotone in successes, a gate verdict
of FAIL at the bound is a FAIL for every possible value of the missing terms.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .adequacy import adequacy_satisfies_g1
from .g2_contract import G2Event, evaluate_g2_event
from .g3_contract import G3Event, classify_g3_event
from .heldout_endpoint_populations import (
    EndpointPopulation,
    build_all_primary_populations,
    held_out_case_ids,
    variant_code_for_case,
)
from .post_execution_sealer import guard_analysis_boundary
from .rc3_scoring import score_g2, score_g3
from .rc5_g1_bridge import CaseG1, G1Score, score_g1
from .rc5_record_payload import SealedRecord, load_sealed_partition
from .structural_acceptance import (
    CEILING_FRACTION_GATE,
    CEILING_WAIVER_THRESHOLD,
    F9_ACCEPTANCE_CALIBRATION_STATUS,
    REQUIRED_HARD_GATES,
    SECONDARY_REPORTED_RUNGS,
    AcceptanceResult,
    AcceptanceStatus,
    FalsificationResult,
    check_gate8,
    evaluate_structural_acceptance,
)

__all__ = [
    "ContractViolation",
    "GATE7_REACHED_STAGES",
    "GATE7_PASSED_STAGES",
    "GATE8_REACHED_STAGES",
    "GATE8_PASSED_STAGES",
    "F9_CITATION_PROHIBITION",
    "Gate7Report",
    "Gate8Report",
    "F9Report",
    "G1Assessment",
    "FrozenDecision",
    "HeldOutContractAnalysis",
    "analyze_sealed_partition",
]


class ContractViolation(RuntimeError):
    """The sealed evidence contradicts the frozen contract."""


#: A case reaches Gate 7 iff the frozen predicate short-circuited at or after
#: position 7.  These are the predicate's own ``gate_reached`` strings; no gate
#: order is restated here.
GATE7_REACHED_STAGES: frozenset[str] = frozenset({"ceiling", "falsification", "all_passed"})
GATE7_PASSED_STAGES: frozenset[str] = frozenset({"falsification", "all_passed"})
GATE8_REACHED_STAGES: frozenset[str] = frozenset({"falsification", "all_passed"})
GATE8_PASSED_STAGES: frozenset[str] = frozenset({"all_passed"})

#: A3.5 §6.9.4, binding on every downstream report.
F9_CITATION_PROHIBITION = (
    "F9 is a secondary, non-gating stress test with acceptance calibration "
    "status NOT_PROVEN_FOR_HARD_GATE. Its PASS/FAIL may NOT be cited in any "
    "report or paper as evidence of validated robustness."
)


# ---------------------------------------------------------------------------
# Gate 7 — the ceiling comparison at position 7
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Gate7Report:
    """Gate 7 outcomes, plus branch attribution for the F5 folded-in floor."""

    reached: int
    passed: int
    failed: int
    passed_via_ceiling_pass: int
    passed_via_ceiling_waiver_only: int
    failed_case_ids: tuple[str, ...]
    reached_case_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "definition": (
                "ceiling comparison at position 7 of the ordered structural-"
                "acceptance predicate: ceiling_pass OR ceiling_waiver. Never "
                "structural acceptance; never F7_INFLUENCE_DROP."
            ),
            "ceiling_fraction_gate": CEILING_FRACTION_GATE,
            "ceiling_waiver_threshold": CEILING_WAIVER_THRESHOLD,
            "reached": self.reached,
            "passed": self.passed,
            "failed": self.failed,
            "passed_via_ceiling_pass": self.passed_via_ceiling_pass,
            "passed_via_ceiling_waiver_only": self.passed_via_ceiling_waiver_only,
            "failed_case_ids": list(self.failed_case_ids),
        }


@dataclass(frozen=True)
class Gate8Report:
    """Gate 8 outcomes over the four hard rungs, fail-closed."""

    reached: int
    passed: int
    failed: int
    failed_case_ids: tuple[str, ...]
    per_rung_pass: Mapping[str, int]
    per_rung_fail: Mapping[str, int]
    rung_keys_ever_emitted: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "definition": (
                "check_gate8 over REQUIRED_HARD_GATES, fail-closed on missing, "
                "FAIL, and stray NOT_APPLICABLE alike. G1 is an endpoint, not a "
                "gate, and is not a conjunct of Gate 8."
            ),
            "required_hard_gates": sorted(r.value for r in REQUIRED_HARD_GATES),
            "g1_is_a_conjunct": False,
            "reached": self.reached,
            "passed": self.passed,
            "failed": self.failed,
            "failed_case_ids": list(self.failed_case_ids),
            "per_rung_pass": dict(self.per_rung_pass),
            "per_rung_fail": dict(self.per_rung_fail),
            "rung_keys_ever_emitted": list(self.rung_keys_ever_emitted),
        }


@dataclass(frozen=True)
class F9Report:
    """F9 secondary stress test.  Reported, never gating."""

    computed_for: int
    pass_count: int
    fail_count: int
    null_count: int
    pass_among_gate8_reachers: int
    fail_among_gate8_reachers: int
    calibration_status: str
    metric_min: float | None
    metric_max: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": "secondary_reported_non_gating",
            "secondary_reported_rungs": sorted(r.value for r in SECONDARY_REPORTED_RUNGS),
            "gating": False,
            "computed_for": self.computed_for,
            "pass": self.pass_count,
            "fail": self.fail_count,
            "null": self.null_count,
            "pass_among_gate8_reachers": self.pass_among_gate8_reachers,
            "fail_among_gate8_reachers": self.fail_among_gate8_reachers,
            "acceptance_calibration_status": self.calibration_status,
            "f9_stress_test_metric_min": self.metric_min,
            "f9_stress_test_metric_max": self.metric_max,
            "citation_prohibition": F9_CITATION_PROHIBITION,
        }


@dataclass(frozen=True)
class G1Assessment:
    """G1 as scored by ``score_g1``, with its evidential mode declared."""

    mode: str                     # "EXACT" or "UPPER_BOUND"
    score: G1Score
    m0_accepted_count: int
    a1_distribution: Mapping[str, int]
    unrecoverable_conjuncts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "denominator": self.score.denominator,
            "competent": self.score.competent,
            "competent_is_an_upper_bound": self.mode == "UPPER_BOUND",
            "wilson_lower_95": self.score.wilson_lower,
            "gate": "wilson_lower_95 >= 0.70",
            "gate_passed": self.score.gate_passed,
            "m0_accepted_count": self.m0_accepted_count,
            "a1_distribution": dict(self.a1_distribution),
            "unrecoverable_conjuncts": list(self.unrecoverable_conjuncts),
            "success_predicate": (
                "g_spearman >= 0.80 AND trajectory_mae <= 0.80 * "
                "per_energy_mean_mae AND m0_accepted"
            ),
        }


@dataclass(frozen=True)
class FrozenDecision:
    """The frozen decision rule.  Three Wilson gates, conjoined.  No existence tests."""

    g1_gate_passed: bool
    g2_gate_passed: bool
    g3_gate_passed: bool

    @property
    def all_primary_endpoints_pass(self) -> bool:
        return self.g1_gate_passed and self.g2_gate_passed and self.g3_gate_passed

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": (
                "G1 wilson_lower_95 >= 0.70 AND G2 wilson_lower_95 >= 0.70 AND "
                "G3 wilson_upper_95 <= 0.15"
            ),
            "g1_gate_passed": self.g1_gate_passed,
            "g2_gate_passed": self.g2_gate_passed,
            "g3_gate_passed": self.g3_gate_passed,
            "all_primary_endpoints_pass": self.all_primary_endpoints_pass,
        }


@dataclass(frozen=True)
class HeldOutContractAnalysis:
    """The complete restored analysis."""

    partition: str
    case_population: int
    populations: Mapping[str, EndpointPopulation]
    acceptance_recomputation_disagreements: tuple[str, ...]
    failure_stage_distribution: Mapping[str, int]
    structural_accepted_count: int
    structural_accepted_by_family: Mapping[str, int]
    g1: G1Assessment
    g2_score: Any
    g2_success_case_ids: tuple[str, ...]
    g3_score: Any
    g3_event_counts: Mapping[str, int]
    g3_violation_case_ids: tuple[str, ...]
    gate7: Gate7Report
    gate8: Gate8Report
    f9: F9Report
    execution_failure_poisoned: Mapping[str, int]
    decision: FrozenDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "partition": self.partition,
            "case_population": self.case_population,
            "case_population_is_not_a_denominator": True,
            "endpoint_denominators": {
                name: pop.denominator for name, pop in sorted(self.populations.items())
            },
            "acceptance_recomputation_disagreements": list(
                self.acceptance_recomputation_disagreements
            ),
            "failure_stage_distribution": dict(self.failure_stage_distribution),
            "structural_accepted_count": self.structural_accepted_count,
            "structural_accepted_is_an_acceptance_count_not_an_endpoint_rate": True,
            "structural_accepted_by_family": dict(self.structural_accepted_by_family),
            "g1": self.g1.to_dict(),
            "g2": {
                "denominator": self.g2_score.denominator,
                "successes": self.g2_score.successes,
                "failures": self.g2_score.failures,
                "unevaluable": self.g2_score.unevaluable,
                "success_rate": self.g2_score.success_rate,
                "wilson_lower_95": self.g2_score.wilson_lower,
                "gate": "wilson_lower_95 >= 0.70",
                "gate_passed": self.g2_score.gate_passed,
                "success_predicate": "support_status == MATCH AND family_status == MATCH",
                "success_case_ids": list(self.g2_success_case_ids),
            },
            "g3": {
                "denominator": self.g3_score.denominator,
                "violations": self.g3_score.violations,
                "violation_rate": self.g3_score.violation_rate,
                "wilson_upper_95": self.g3_score.wilson_upper,
                "gate": "wilson_upper_95 <= 0.15",
                "gate_passed": self.g3_score.gate_passed,
                "direction": "inverted: low violation rate is good",
                "unevaluable_counts_as_violation": True,
                "event_counts": dict(self.g3_event_counts),
                "violation_case_ids": list(self.g3_violation_case_ids),
            },
            "gate7": self.gate7.to_dict(),
            "gate8": self.gate8.to_dict(),
            "f9": self.f9.to_dict(),
            "execution_failure_poisoned_by_endpoint": dict(self.execution_failure_poisoned),
            "decision": self.decision.to_dict(),
        }


# ---------------------------------------------------------------------------
# the analysis
# ---------------------------------------------------------------------------

def _recompute_acceptance(
    records: Mapping[str, SealedRecord],
    null_threshold: Mapping[int, float],
) -> tuple[dict[str, AcceptanceResult], tuple[str, ...]]:
    """Re-derive every case's verdict through the frozen predicate.

    The stored verdict is compared, never trusted: a record claiming
    ``STRUCTURAL_ACCEPTED`` on inputs that fail Gate 3 would be caught here.
    """
    derived: dict[str, AcceptanceResult] = {}
    disagreements: list[str] = []
    for case_id, record in records.items():
        result = evaluate_structural_acceptance(
            a1_status=record.a1_status,
            candidate=record.structural_candidate,
            null_threshold=null_threshold,
        )
        derived[case_id] = result
        stored = record.stored_acceptance
        if stored.status != result.status or stored.gate_reached != result.gate_reached:
            disagreements.append(
                f"{case_id}: stored {stored.status.value}/{stored.gate_reached} "
                f"vs derived {result.status.value}/{result.gate_reached}"
            )
    return derived, tuple(disagreements)


def evaluate_gate7(
    records: Mapping[str, SealedRecord],
    acceptance: Mapping[str, AcceptanceResult],
    null_threshold: Mapping[int, float],
) -> Gate7Report:
    """Gate 7 over the cases that actually reached position 7.

    The reached-set and the verdict come from the frozen predicate's own
    ``gate_reached``.  The branch attribution re-evaluates the two published
    sub-predicates for reporting only, and is asserted consistent with the
    frozen verdict rather than substituted for it.
    """
    reached: list[str] = []
    failed: list[str] = []
    via_ceiling_pass = 0
    via_waiver_only = 0

    for case_id in sorted(records):
        result = acceptance[case_id]
        if result.gate_reached not in GATE7_REACHED_STAGES:
            continue
        reached.append(case_id)
        frozen_passed = result.gate_reached in GATE7_PASSED_STAGES
        if not frozen_passed:
            failed.append(case_id)

        candidate = records[case_id].structural_candidate
        if candidate is None:  # pragma: no cover - unreachable past gate 1
            raise ContractViolation(
                f"{case_id} reached Gate 7 with no candidate; the frozen "
                f"predicate routes a missing candidate to UNEVALUABLE at "
                f"no_candidate"
            )
        threshold = null_threshold[min(candidate.complexity, 20)]
        ceiling_pass = candidate.ceiling_fraction >= CEILING_FRACTION_GATE
        floor_pass = candidate.candidate_test_r2 > threshold
        ceiling_waiver = (candidate.ceiling_r2 < CEILING_WAIVER_THRESHOLD) and floor_pass

        if (ceiling_pass or ceiling_waiver) != frozen_passed:
            raise ContractViolation(
                f"{case_id}: Gate 7 branch attribution disagrees with the frozen "
                f"predicate (ceiling_pass={ceiling_pass}, "
                f"ceiling_waiver={ceiling_waiver}, frozen={frozen_passed})"
            )
        if frozen_passed:
            if ceiling_pass:
                via_ceiling_pass += 1
            else:
                via_waiver_only += 1

    return Gate7Report(
        reached=len(reached),
        passed=len(reached) - len(failed),
        failed=len(failed),
        passed_via_ceiling_pass=via_ceiling_pass,
        passed_via_ceiling_waiver_only=via_waiver_only,
        failed_case_ids=tuple(failed),
        reached_case_ids=tuple(reached),
    )


def evaluate_gate8(
    records: Mapping[str, SealedRecord],
    acceptance: Mapping[str, AcceptanceResult],
) -> Gate8Report:
    """Gate 8 via ``check_gate8``.  Four rungs.  Fail-closed.  No G1."""
    reached: list[str] = []
    failed: list[str] = []
    per_rung_pass: Counter[str] = Counter()
    per_rung_fail: Counter[str] = Counter()
    rung_keys_emitted: set[str] = set()

    for case_id in sorted(records):
        record = records[case_id]
        rung_keys_emitted.update(r.value for r in record.falsification_results)

        if acceptance[case_id].gate_reached not in GATE8_REACHED_STAGES:
            continue
        reached.append(case_id)

        results = record.falsification_results
        passed = check_gate8(results)
        frozen_passed = acceptance[case_id].gate_reached in GATE8_PASSED_STAGES
        if passed != frozen_passed:
            raise ContractViolation(
                f"{case_id}: check_gate8 says {passed} but the frozen predicate "
                f"reached {acceptance[case_id].gate_reached}"
            )
        if not passed:
            failed.append(case_id)

        for rung in sorted(REQUIRED_HARD_GATES, key=lambda r: r.value):
            outcome = results.get(rung)
            if outcome == FalsificationResult.PASS:
                per_rung_pass[rung.value] += 1
            else:
                per_rung_fail[rung.value] += 1

    return Gate8Report(
        reached=len(reached),
        passed=len(reached) - len(failed),
        failed=len(failed),
        failed_case_ids=tuple(failed),
        per_rung_pass=dict(sorted(per_rung_pass.items())),
        per_rung_fail=dict(sorted(per_rung_fail.items())),
        rung_keys_ever_emitted=tuple(sorted(rung_keys_emitted)),
    )


def report_f9(
    records: Mapping[str, SealedRecord],
    acceptance: Mapping[str, AcceptanceResult],
) -> F9Report:
    """Report the F9 secondary observable.  It gates nothing."""
    counts: Counter[str] = Counter()
    among_reachers: Counter[str] = Counter()
    metrics: list[float] = []

    for case_id in sorted(records):
        record = records[case_id]
        if record.f9_acceptance_calibration_status != F9_ACCEPTANCE_CALIBRATION_STATUS:
            raise ContractViolation(
                f"{case_id}: f9_acceptance_calibration_status is "
                f"{record.f9_acceptance_calibration_status!r}; A3.5 §6.9.4 fixes "
                f"it to {F9_ACCEPTANCE_CALIBRATION_STATUS!r}"
            )
        outcome = record.f9_stress_test_result
        counts["null" if outcome is None else outcome.value] += 1
        metric = record.f9_stress_test_metric
        if metric is not None:
            metrics.append(metric)
        if acceptance[case_id].gate_reached in GATE8_REACHED_STAGES:
            among_reachers["null" if outcome is None else outcome.value] += 1

    return F9Report(
        computed_for=counts["PASS"] + counts["FAIL"],
        pass_count=counts["PASS"],
        fail_count=counts["FAIL"],
        null_count=counts["null"],
        pass_among_gate8_reachers=among_reachers["PASS"],
        fail_among_gate8_reachers=among_reachers["FAIL"],
        calibration_status=F9_ACCEPTANCE_CALIBRATION_STATUS,
        metric_min=min(metrics) if metrics else None,
        metric_max=max(metrics) if metrics else None,
    )


def _bounding_case_g1(case_id: str, m0_accepted: bool) -> CaseG1:
    """The most favourable G1 outcome consistent with a known ``m0_accepted``.

    The two conjuncts the sealed schema does not persist are set to their
    passing extremes, so ``scalar_competent`` reduces exactly to
    ``m0_accepted``.  Scoring this sequence yields the maximum competent count
    the evidence admits — an upper bound, and labelled as one.
    """
    return CaseG1(
        case_id=case_id,
        g_spearman=1.0,
        trajectory_mae=0.0,
        per_energy_mean_mae=1.0,
        m0_accepted=m0_accepted,
        cells=0,
        evaluable_compounds=0,
        contract_failure=False,
    )


def assess_g1(
    records: Mapping[str, SealedRecord],
    population: EndpointPopulation,
    exact_outcomes: Mapping[str, CaseG1] | None = None,
) -> G1Assessment:
    """Score G1 through ``score_g1`` over its registry-built 164-case population.

    With ``exact_outcomes`` supplied the mode is EXACT and the real observables
    are scored.  Without them the mode is UPPER_BOUND and the returned count is
    the largest the evidence admits.
    """
    a1_distribution: Counter[str] = Counter()
    m0_accepted_count = 0
    outcomes: list[CaseG1] = []

    for case_id in population.case_ids:
        record = records[case_id]
        status = record.a1_status
        a1_distribution[status.value] += 1
        m0_accepted = adequacy_satisfies_g1(status)
        if m0_accepted:
            m0_accepted_count += 1
        if exact_outcomes is None:
            outcomes.append(_bounding_case_g1(case_id, m0_accepted))
        else:
            outcome = exact_outcomes[case_id]
            if outcome.m0_accepted != m0_accepted:
                raise ContractViolation(
                    f"{case_id}: supplied G1 outcome claims m0_accepted="
                    f"{outcome.m0_accepted} but the sealed A1 status is "
                    f"{status.value}"
                )
            outcomes.append(outcome)

    # The frozen scorer's own 164-length assertion is the guard here.
    score = score_g1(outcomes)

    return G1Assessment(
        mode="UPPER_BOUND" if exact_outcomes is None else "EXACT",
        score=score,
        m0_accepted_count=m0_accepted_count,
        a1_distribution=dict(sorted(a1_distribution.items())),
        unrecoverable_conjuncts=(
            () if exact_outcomes is not None else ("g_spearman", "trajectory_mae")
        ),
    )


def score_g2_endpoint(
    records: Mapping[str, SealedRecord],
    population: EndpointPopulation,
) -> tuple[Any, tuple[str, ...]]:
    """Score G2 through ``evaluate_g2_event`` and ``score_g2`` over its 144 cases."""
    events: list[G2Event] = []
    successes: list[str] = []
    for case_id in population.case_ids:
        record = records[case_id]
        event = evaluate_g2_event(record.support_status, record.family_status)
        if event != record.stored_g2_event:
            raise ContractViolation(
                f"{case_id}: stored g2_event {record.stored_g2_event.value} but "
                f"evaluate_g2_event yields {event.value}"
            )
        events.append(event)
        if event == G2Event.SUCCESS:
            successes.append(case_id)
    return score_g2(events), tuple(successes)


def score_g3_endpoint(
    records: Mapping[str, SealedRecord],
    population: EndpointPopulation,
    acceptance: Mapping[str, AcceptanceResult],
) -> tuple[Any, Mapping[str, int], tuple[str, ...]]:
    """Score G3 through ``classify_g3_event`` and ``score_g3`` over its 36 cases.

    ``analysis.classify_negative_control`` is deliberately not imported: A3.5
    §8.3 makes ``g3_contract`` the sole G3 authority, and the other classifier
    drifts permissively on 20 of these 36 opportunities.
    """
    events: list[G3Event] = []
    counts: Counter[str] = Counter()
    violations: list[str] = []
    for case_id in population.case_ids:
        record = records[case_id]
        event = classify_g3_event(
            variant=variant_code_for_case(case_id),
            acceptance=acceptance[case_id],
            effective_support=record.effective_support,
        )
        events.append(event)
        counts[event.value] += 1
        if event in (G3Event.UNSAFE, G3Event.VIOLATION):
            violations.append(case_id)
    return score_g3(events), dict(sorted(counts.items())), tuple(violations)


def analyze_sealed_partition(
    results_root: Path,
    null_threshold: Mapping[int, float],
    exact_g1_outcomes: Mapping[str, CaseG1] | None = None,
    enforce_boundary_guard: bool = True,
) -> HeldOutContractAnalysis:
    """Run the restored analysis over sealed Held-out evidence.

    Nothing is written into ``results_root``.
    """
    results_root = Path(results_root)
    if enforce_boundary_guard:
        guard_analysis_boundary(results_root)

    case_ids = held_out_case_ids()
    records = load_sealed_partition(results_root, case_ids)

    digests = {records[c].null_threshold_digest for c in case_ids}
    if len(digests) != 1:
        raise ContractViolation(
            f"sealed records carry {len(digests)} distinct null_threshold_digests"
        )

    acceptance, disagreements = _recompute_acceptance(records, null_threshold)
    if disagreements:
        raise ContractViolation(
            f"{len(disagreements)} sealed records contradict the frozen "
            f"acceptance predicate: {disagreements[:3]}"
        )

    populations = build_all_primary_populations()

    stages: Counter[str] = Counter(r.gate_reached for r in acceptance.values())
    accepted_families: Counter[str] = Counter(
        case_id.split("|")[2]
        for case_id, result in acceptance.items()
        if result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED
    )

    g1 = assess_g1(records, populations["scalar_competence"], exact_g1_outcomes)
    g2_score, g2_successes = score_g2_endpoint(records, populations["family_recovery"])
    g3_score, g3_counts, g3_violations = score_g3_endpoint(
        records, populations["principal_structural_safety"], acceptance
    )

    gate7 = evaluate_gate7(records, acceptance, null_threshold)
    gate8 = evaluate_gate8(records, acceptance)
    f9 = report_f9(records, acceptance)

    poisoned = {
        name: sum(
            1 for case_id in pop.case_ids if records[case_id].execution_failure_poisoned
        )
        for name, pop in sorted(populations.items())
    }

    decision = FrozenDecision(
        g1_gate_passed=g1.score.gate_passed,
        g2_gate_passed=g2_score.gate_passed,
        g3_gate_passed=g3_score.gate_passed,
    )

    return HeldOutContractAnalysis(
        partition="held_out",
        case_population=len(case_ids),
        populations=populations,
        acceptance_recomputation_disagreements=disagreements,
        failure_stage_distribution=dict(sorted(stages.items())),
        structural_accepted_count=sum(accepted_families.values()),
        structural_accepted_by_family=dict(sorted(accepted_families.items())),
        g1=g1,
        g2_score=g2_score,
        g2_success_case_ids=g2_successes,
        g3_score=g3_score,
        g3_event_counts=g3_counts,
        g3_violation_case_ids=g3_violations,
        gate7=gate7,
        gate8=gate8,
        f9=f9,
        execution_failure_poisoned=poisoned,
        decision=decision,
    )
