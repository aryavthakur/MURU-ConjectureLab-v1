"""Amendment A3.1: structural acceptance predicate with typed states,
as amended by Amendment A3.5 section 6.9.

Acceptance is TRUTH-BLIND.  Family correctness is NOT part of acceptance.
Planted truth is NEVER read by this predicate.

The ordered predicate:
  1. A1 adequacy prerequisite (only M0_NOT_REJECTED proceeds)
  2. valid_r2 > null_threshold[min(complexity, 20)]
  3. selection_fraction >= 20/30
  4. complexity <= 20
  5. invalid_fraction <= 0.005
  6. effective support non-empty
  7. ceiling_fraction >= 0.80
       OR (ceiling_r2 < 0.05 AND candidate_test_r2 > null_threshold[min(c, 20)])
  8. the four hard Gate-8 rungs all PASS, fail-closed

Amendment A3.5 section 6.9 (RC5 obligations 13, 14, 17, 18, 19)
----------------------------------------------------------------
Two coordinated corrections, neither of which introduces a threshold,
constant, or calibration object:

**Gate 7 (section 6.9.3, obligation 17).**  The waiver branch previously
admitted **any** ``candidate_test_r2`` with no floor at all.  It now also
requires ``candidate_test_r2 > null_threshold[min(complexity, 20)]`` -- the
identical, already-frozen, already-computed table Gates 2, F7, F9 and F10 all
read, and the identical ``candidate_test_r2`` quantity section 6.3(i) already
bound and required to be computed **once**.  This is F5's one genuine
non-redundant contribution, folded into the branch where the frozen text
identified the gap, rather than restated as a sixth rung.  ``ceiling_pass``'s
own rule is unchanged, and ``CEILING_FRACTION_GATE`` / ``CEILING_WAIVER_THRESHOLD``
keep their frozen values.

**Gate 8 (section 6.9.4, obligations 14 and 18).**
``F5_SCAFFOLD_HOLDOUT`` is superseded and removed: it is never again
independently evaluated as a Gate-8 rung.  ``F9_ENERGY_SUBSET`` remains a
member of :class:`FalsificationRung` because it is still computed and
reported, but it is routed to reporting only and is **never** a member of
:data:`REQUIRED_HARD_GATES`; its acceptance calibration status is
``NOT_PROVEN_FOR_HARD_GATE``.  :func:`check_gate8` is **fail-closed**: its
predicate is ``result != PASS``, not ``result == FAIL``, so a missing rung, a
``FAIL``, and a stray ``NOT_APPLICABLE`` all reject identically.

That last point repairs a real, previously-disclosed-but-uncorrected
code/docstring ambiguity.  The superseded :func:`check_falsification_harness`
claimed in its docstring that ``NOT_APPLICABLE`` is "never counted as PASS"
while its code returned ``False`` only on a missing rung or an explicit
``FAIL`` -- so a ``NOT_APPLICABLE`` silently fell through to harness-passing.
Section 6.0 made non-emission a hard binding on the *emitting* side; the
*checking* side is now closed here.

This module is the REFERENCE CONTRACT.  Production integration is RC3/RC5.
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
    """The falsification rungs this contract knows about.

    ``F5_SCAFFOLD_HOLDOUT`` is **absent**: A3.5 section 6.9.2 supersedes it and
    obligation 14 requires it dropped from this enum.  Its quantity survives as
    ``candidate_test_r2``, consumed by Gate 7's waiver branch.

    ``F9_ENERGY_SUBSET`` is **present but never gating**: it is computed and
    reported for every case reaching Gate 8 (``f9_stress_test_result`` /
    ``f9_stress_test_metric``), and is deliberately not a member of
    :data:`REQUIRED_HARD_GATES`.
    """
    F1_REPRODUCIBILITY = "F1_REPRODUCIBILITY"
    F4_COMPOUND_HOLDOUT = "F4_COMPOUND_HOLDOUT"
    F7_INFLUENCE_DROP = "F7_INFLUENCE_DROP"
    F9_ENERGY_SUBSET = "F9_ENERGY_SUBSET"
    F10_NEGATIVE_CONTROL = "F10_NEGATIVE_CONTROL"


class FalsificationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    #: Retained for type compatibility with the frozen enum only.  A3.5
    #: section 6.0 forbids every rung from ever emitting it; if one does by
    #: defect, :func:`check_gate8` treats it as non-passing.
    NOT_APPLICABLE = "NOT_APPLICABLE"


#: A3.5 section 6.9.4, verbatim.  Renamed from ``REQUIRED_FALSIFICATION_RUNGS``
#: because its membership and its meaning both changed: these are the hard
#: gates, and nothing else gates.
REQUIRED_HARD_GATES: frozenset[FalsificationRung] = frozenset({
    FalsificationRung.F1_REPRODUCIBILITY,
    FalsificationRung.F4_COMPOUND_HOLDOUT,
    FalsificationRung.F7_INFLUENCE_DROP,
    FalsificationRung.F10_NEGATIVE_CONTROL,
})

#: A3.5 section 6.9.4: F9 is computed, reported, and never acceptance-determining.
SECONDARY_REPORTED_RUNGS: frozenset[FalsificationRung] = frozenset({
    FalsificationRung.F9_ENERGY_SUBSET,
})

#: Section 6.9.4's own words, recorded here so no report can cite F9's
#: PASS/FAIL as evidence of validated robustness.
F9_ACCEPTANCE_CALIBRATION_STATUS = "NOT_PROVEN_FOR_HARD_GATE"

if REQUIRED_HARD_GATES & SECONDARY_REPORTED_RUNGS:  # pragma: no cover - static
    raise ImportError(
        "a secondary reported rung is also a hard gate; A3.5 section 6.9.4 "
        "forbids F9 from ever entering REQUIRED_HARD_GATES"
    )


def check_gate8(
    results: Mapping[FalsificationRung, FalsificationResult],
) -> bool:
    """A3.5 section 6.9.4's amended acceptance check, **fail-closed**.

    Only an explicit ``PASS`` passes.  A missing required rung fails; ``FAIL``
    fails; a ``NOT_APPLICABLE`` that should never occur fails identically, by
    construction rather than by a separate branch.

    The predicate is deliberately ``result != PASS`` and not
    ``result == FAIL``: that difference *is* the repair.
    """
    for rung in REQUIRED_HARD_GATES:
        result = results.get(rung)
        if result is None:
            return False                      # missing required rung: fail closed
        if result != FalsificationResult.PASS:
            return False                      # FAIL and stray NOT_APPLICABLE alike
    return True


# -----------------------------------------------------------------------
# Candidate input
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class StructuralCandidate:
    """Input to the structural acceptance predicate.

    Carries no truth field of any kind, so planted truth cannot reach the
    predicate even by accident.
    """
    valid_r2: float
    complexity: int
    selection_fraction: float  # fraction of 30 seeds that selected this
    invalid_fraction: float
    effective_support: frozenset[str] | None
    ceiling_fraction: float
    ceiling_r2: float
    falsification_results: Mapping[FalsificationRung, FalsificationResult]
    #: A3.5 section 6.3(i) / 6.9.3: the representative candidate's ``test``
    #: R2 under the frozen affine-refit convention, computed **once** by the
    #: caller and shared with ``rc3_ceiling.estimate_ceiling``.  Gate 7's
    #: waiver branch reads it; nothing else in this predicate does.
    candidate_test_r2: float = float("-inf")


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

    # Gate 7: ceiling, as amended by A3.5 section 6.9.3.  `threshold` is the
    # value already looked up at Gate 2 -- the same table, the same index --
    # so the waiver floor cannot read a different bar than Gate 2 did.
    ceiling_pass = candidate.ceiling_fraction >= CEILING_FRACTION_GATE
    floor_pass = candidate.candidate_test_r2 > threshold
    ceiling_waiver = (candidate.ceiling_r2 < CEILING_WAIVER_THRESHOLD) and floor_pass
    if not (ceiling_pass or ceiling_waiver):
        return AcceptanceResult(
            status=AcceptanceStatus.REJECTED_CEILING,
            gate_reached="ceiling",
        )

    # Gate 8: the four hard rungs, fail-closed (A3.5 section 6.9.4).
    if not check_gate8(candidate.falsification_results):
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
