"""Amendment A3.1: structural acceptance predicate with typed states.

Acceptance is TRUTH-BLIND.  Family correctness is NOT part of acceptance.
Planted truth is NEVER read by this predicate.

The ordered predicate:
  1. A1 adequacy prerequisite (only M0_NOT_REJECTED proceeds)
  2. valid_r2 > null_threshold[min(complexity, 20)]
  3. selection_fraction >= 20/30
  4. complexity <= 20
  5. invalid_fraction <= 0.005
  6. effective support non-empty
  7. ceiling_fraction >= 0.80 OR ceiling_r2 < 0.05 (waiver)
  8. reduced falsification harness passes

This module is the REFERENCE CONTRACT.  Production integration is RC3.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .adequacy import CaseAdequacyStatus


# -----------------------------------------------------------------------
# Typed acceptance states
# -----------------------------------------------------------------------

class AcceptanceStatus(str, Enum):
    """Every terminal structural-acceptance state."""
    STRUCTURAL_ACCEPTED = "STRUCTURAL_ACCEPTED"
    REJECTED_A1_INADEQUATE = "REJECTED_A1_INADEQUATE"
    REJECTED_BELOW_NULL = "REJECTED_BELOW_NULL"
    REJECTED_UNSTABLE = "REJECTED_UNSTABLE"
    REJECTED_OVERCOMPLEX = "REJECTED_OVERCOMPLEX"
    REJECTED_INVALID_FRACTION = "REJECTED_INVALID_FRACTION"
    REJECTED_EMPTY_SUPPORT = "REJECTED_EMPTY_SUPPORT"
    REJECTED_CEILING = "REJECTED_CEILING"
    REJECTED_FALSIFICATION = "REJECTED_FALSIFICATION"
    UNEVALUABLE = "UNEVALUABLE"


# A1 states that permit structural inference
_A1_PERMITTED = frozenset({CaseAdequacyStatus.M0_NOT_REJECTED})

# A1 model-rejection states
_A1_REJECTION_STATES = frozenset({
    CaseAdequacyStatus.M0_REJECTED_M1,
    CaseAdequacyStatus.M0_REJECTED_M2,
    CaseAdequacyStatus.M0_REJECTED_M3,
    CaseAdequacyStatus.M0_REJECTED_MULTIPLE,
})

# A1 failure/timeout/contract states
_A1_UNEVALUABLE_STATES = frozenset({
    CaseAdequacyStatus.INSUFFICIENT_DATA,
    CaseAdequacyStatus.BOUNDARY_LIMITED,
    CaseAdequacyStatus.NUMERICAL_FAILURE,
    CaseAdequacyStatus.MODEL_FIT_FAILURE,
    CaseAdequacyStatus.TIMEOUT,
    CaseAdequacyStatus.CONTRACT_FAILURE,
})

# Frozen thresholds
STABILITY_GATE = 20  # out of 30
STABILITY_DENOMINATOR = 30
MAX_COMPLEXITY = 20
MAX_INVALID_FRACTION = 0.005
CEILING_FRACTION_GATE = 0.80
CEILING_WAIVER_THRESHOLD = 0.05


# -----------------------------------------------------------------------
# Reduced falsification harness
# -----------------------------------------------------------------------

class FalsificationRung(str, Enum):
    """The reduced falsification rungs applicable to structural acceptance."""
    F1_REPRODUCIBILITY = "F1_REPRODUCIBILITY"
    F4_COMPOUND_HOLDOUT = "F4_COMPOUND_HOLDOUT"
    F5_SCAFFOLD_HOLDOUT = "F5_SCAFFOLD_HOLDOUT"
    F7_INFLUENCE_DROP = "F7_INFLUENCE_DROP"
    F9_ENERGY_SUBSET = "F9_ENERGY_SUBSET"
    F10_NEGATIVE_CONTROL = "F10_NEGATIVE_CONTROL"


class FalsificationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


REQUIRED_FALSIFICATION_RUNGS: frozenset[FalsificationRung] = frozenset({
    FalsificationRung.F1_REPRODUCIBILITY,
    FalsificationRung.F4_COMPOUND_HOLDOUT,
    FalsificationRung.F5_SCAFFOLD_HOLDOUT,
    FalsificationRung.F7_INFLUENCE_DROP,
    FalsificationRung.F9_ENERGY_SUBSET,
    FalsificationRung.F10_NEGATIVE_CONTROL,
})


def check_falsification_harness(
    results: Mapping[FalsificationRung, FalsificationResult],
) -> bool:
    """Check the reduced falsification harness.

    Required rungs must be present with PASS or NOT_APPLICABLE.
    NOT_APPLICABLE is never counted as PASS.
    Any FAIL in a required rung fails the harness.
    """
    for rung in REQUIRED_FALSIFICATION_RUNGS:
        result = results.get(rung)
        if result is None:
            return False
        if result == FalsificationResult.FAIL:
            return False
    return True


# -----------------------------------------------------------------------
# Candidate input
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class StructuralCandidate:
    """Input to the structural acceptance predicate."""
    valid_r2: float
    complexity: int
    selection_fraction: float  # fraction of 30 seeds that selected this
    invalid_fraction: float
    effective_support: frozenset[str] | None
    ceiling_fraction: float
    ceiling_r2: float
    falsification_results: Mapping[FalsificationRung, FalsificationResult]


# -----------------------------------------------------------------------
# Acceptance evaluation
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptanceResult:
    """The structural acceptance verdict for one case."""
    status: AcceptanceStatus
    gate_reached: str

    @property
    def accepted(self) -> bool:
        return self.status == AcceptanceStatus.STRUCTURAL_ACCEPTED


def evaluate_structural_acceptance(
    a1_status: CaseAdequacyStatus,
    candidate: StructuralCandidate | None,
    null_threshold: Mapping[int, float],
) -> AcceptanceResult:
    """Apply the frozen structural acceptance predicate.

    The predicate is evaluated in the frozen order.  It short-circuits
    at the first failing gate.

    Parameters
    ----------
    a1_status
        The A1 adequacy status for this case.
    candidate
        The best structural candidate.  None if no candidate was produced.
    null_threshold
        Mapping from complexity (1..20) to the calibrated null threshold.
    """
    # Gate 1: A1 adequacy prerequisite
    if a1_status in _A1_REJECTION_STATES:
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_A1_INADEQUATE,
            gate_reached="a1_adequacy",
        )
    if a1_status in _A1_UNEVALUABLE_STATES:
        return AcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            gate_reached="a1_adequacy",
        )
    if a1_status not in _A1_PERMITTED:
        return AcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            gate_reached="a1_adequacy",
        )

    # No candidate produced
    if candidate is None:
        return AcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            gate_reached="no_candidate",
        )

    # Gate 2: null threshold
    effective_complexity = min(candidate.complexity, MAX_COMPLEXITY)
    threshold = null_threshold.get(effective_complexity)
    if threshold is None:
        return AcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            gate_reached="null_threshold_missing",
        )
    if not (candidate.valid_r2 > threshold):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_BELOW_NULL,
            gate_reached="null_threshold",
        )

    # Gate 3: stability
    if not (candidate.selection_fraction >= STABILITY_GATE / STABILITY_DENOMINATOR):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_UNSTABLE,
            gate_reached="stability",
        )

    # Gate 4: complexity
    if not (candidate.complexity <= MAX_COMPLEXITY):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_OVERCOMPLEX,
            gate_reached="complexity",
        )

    # Gate 5: invalid fraction
    if not (candidate.invalid_fraction <= MAX_INVALID_FRACTION):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_INVALID_FRACTION,
            gate_reached="invalid_fraction",
        )

    # Gate 6: effective support non-empty
    if candidate.effective_support is None or len(candidate.effective_support) == 0:
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_EMPTY_SUPPORT,
            gate_reached="effective_support",
        )

    # Gate 7: ceiling
    ceiling_pass = candidate.ceiling_fraction >= CEILING_FRACTION_GATE
    ceiling_waiver = candidate.ceiling_r2 < CEILING_WAIVER_THRESHOLD
    if not (ceiling_pass or ceiling_waiver):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_CEILING,
            gate_reached="ceiling",
        )

    # Gate 8: reduced falsification harness
    if not check_falsification_harness(candidate.falsification_results):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_FALSIFICATION,
            gate_reached="falsification",
        )

    return AcceptanceResult(
        status=AcceptanceStatus.STRUCTURAL_ACCEPTED,
        gate_reached="all_passed",
    )


# -----------------------------------------------------------------------
# Ceiling estimator provenance
# -----------------------------------------------------------------------

CEILING_ESTIMATOR_SPEC = {
    "class": "sklearn.ensemble.HistGradientBoostingRegressor",
    "params": {
        "max_iter": 150,
        "max_depth": 3,
        "min_samples_leaf": 20,
        "random_state": 0,
    },
    "dependency": "scikit-learn==1.9.0",
    "provenance": "requirements.lock.txt at c7c23324d40cd432bdd14bf9d3292b5a2867ef9e",
    "predates_development": True,
    "train_partition": "train",
    "score_partition": "test",
}
