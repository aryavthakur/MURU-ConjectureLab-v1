"""Constructed contract tests for structural acceptance (Amendment A3.1).

All fixtures are hand-built.  No Development case outcomes, no Held-out
data, no calibration world execution.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.adequacy import CaseAdequacyStatus
from muru.paper_benchmark.structural_acceptance import (
    CEILING_FRACTION_GATE,
    CEILING_WAIVER_THRESHOLD,
    MAX_COMPLEXITY,
    MAX_INVALID_FRACTION,
    STABILITY_DENOMINATOR,
    STABILITY_GATE,
    AcceptanceResult,
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
    REQUIRED_HARD_GATES,
    SECONDARY_REPORTED_RUNGS,
    StructuralCandidate,
    check_gate8,
    evaluate_structural_acceptance,
)


def _all_pass_falsification() -> dict[FalsificationRung, FalsificationResult]:
    """Every HARD gate passing.

    A3.5 section 6.9.4 narrowed the gating set to four rungs; F9 is computed
    and reported but never enters this mapping, and F5 no longer exists.
    """
    return {rung: FalsificationResult.PASS for rung in REQUIRED_HARD_GATES}


def _standard_threshold() -> dict[int, float]:
    return {c: 0.3 for c in range(1, 21)}


def _passing_candidate(**overrides) -> StructuralCandidate:
    defaults = dict(
        valid_r2=0.8,
        complexity=10,
        selection_fraction=25 / 30,
        invalid_fraction=0.001,
        effective_support=frozenset({"mass", "descriptor"}),
        ceiling_fraction=0.9,
        ceiling_r2=0.5,
        falsification_results=_all_pass_falsification(),
        # A3.5 section 6.9.3: the waiver branch's floor.  Comfortably above
        # _standard_threshold()'s 0.3 so it is never the binding constraint in
        # a test that is measuring something else.
        candidate_test_r2=0.75,
    )
    defaults.update(overrides)
    return StructuralCandidate(**defaults)


# -----------------------------------------------------------------------
# A1 prerequisite
# -----------------------------------------------------------------------

class TestA1Prerequisite:

    def test_m0_not_rejected_proceeds(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_m0_rejected_m1(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_REJECTED_M1,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_A1_INADEQUATE

    def test_m0_rejected_m2(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_REJECTED_M2,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_A1_INADEQUATE

    def test_m0_rejected_m3(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_REJECTED_M3,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_A1_INADEQUATE

    def test_m0_rejected_multiple(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_REJECTED_MULTIPLE,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_A1_INADEQUATE

    def test_insufficient_data_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.INSUFFICIENT_DATA,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE

    def test_boundary_limited_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.BOUNDARY_LIMITED,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE

    def test_numerical_failure_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.NUMERICAL_FAILURE,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE

    def test_model_fit_failure_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.MODEL_FIT_FAILURE,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE

    def test_timeout_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.TIMEOUT,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE

    def test_contract_failure_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.CONTRACT_FAILURE,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE


# -----------------------------------------------------------------------
# Null threshold gate
# -----------------------------------------------------------------------

class TestNullThreshold:

    def test_above_threshold(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(valid_r2=0.5),
            {c: 0.3 for c in range(1, 21)},
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_below_threshold(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(valid_r2=0.2),
            {c: 0.3 for c in range(1, 21)},
        )
        assert result.status == AcceptanceStatus.REJECTED_BELOW_NULL

    def test_equal_threshold_rejected(self):
        """Equal to threshold is NOT above - strict >."""
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(valid_r2=0.3),
            {c: 0.3 for c in range(1, 21)},
        )
        assert result.status == AcceptanceStatus.REJECTED_BELOW_NULL

    def test_complexity_capping(self):
        """Candidate with complexity > 20 uses threshold at key 20."""
        threshold = {c: 0.3 for c in range(1, 21)}
        threshold[20] = 0.1  # make key 20 easy to pass
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(valid_r2=0.5, complexity=20),
            threshold,
        )
        # complexity=20, threshold[20]=0.1, valid_r2=0.5 > 0.1: should pass null
        # but then hit complexity gate (20 <= 20 passes)
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED


# -----------------------------------------------------------------------
# Stability gate
# -----------------------------------------------------------------------

class TestStability:

    def test_stable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(selection_fraction=25 / 30),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_exactly_at_gate(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(selection_fraction=20 / 30),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_unstable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(selection_fraction=19 / 30),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_UNSTABLE


# -----------------------------------------------------------------------
# Complexity gate
# -----------------------------------------------------------------------

class TestComplexity:

    def test_at_max(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(complexity=20),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_overcomplex(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(complexity=21),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_OVERCOMPLEX


# -----------------------------------------------------------------------
# Invalid fraction gate
# -----------------------------------------------------------------------

class TestInvalidFraction:

    def test_within_tolerance(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(invalid_fraction=0.004),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_at_limit(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(invalid_fraction=0.005),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_exceeds(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(invalid_fraction=0.006),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_INVALID_FRACTION


# -----------------------------------------------------------------------
# Empty support gate
# -----------------------------------------------------------------------

class TestEmptySupport:

    def test_non_empty(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(effective_support=frozenset({"mass"})),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_empty_support(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(effective_support=frozenset()),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_EMPTY_SUPPORT

    def test_none_support(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(effective_support=None),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_EMPTY_SUPPORT


# -----------------------------------------------------------------------
# Ceiling gate
# -----------------------------------------------------------------------

class TestCeiling:

    def test_ceiling_pass(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(ceiling_fraction=0.85, ceiling_r2=0.6),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_ceiling_fail_no_waiver(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(ceiling_fraction=0.70, ceiling_r2=0.6),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_CEILING

    def test_ceiling_waiver_with_candidate_floor_pass(self):
        """A3.5 section 6.9.3: low ceiling_r2 AND the candidate floor cleared.

        Under A3.1 the waiver fired on low ``ceiling_r2`` alone, with no floor
        at all.  It now additionally requires
        ``candidate_test_r2 > null_threshold[min(complexity, 20)]``.
        """
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                ceiling_fraction=0.50, ceiling_r2=0.03, candidate_test_r2=0.55
            ),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_ceiling_waiver_with_candidate_floor_fail(self):
        """Low ceiling_r2 but the floor not cleared: still REJECTED_CEILING.

        This is the exact, sole, disclosed gap the fold closes.  Under the
        superseded rule this case was accepted.
        """
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                ceiling_fraction=0.50, ceiling_r2=0.03, candidate_test_r2=0.25
            ),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_CEILING

    def test_the_waiver_floor_is_strict_at_the_threshold(self):
        """`>` not `>=`: equality does not clear the floor."""
        threshold = _standard_threshold()
        exactly = threshold[10]
        assert evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                ceiling_fraction=0.50, ceiling_r2=0.03, candidate_test_r2=exactly
            ),
            threshold,
        ).status == AcceptanceStatus.REJECTED_CEILING

    def test_the_waiver_floor_reads_the_capped_complexity_index(self):
        # min(complexity, MAX_COMPLEXITY): a complexity above the cap must not
        # index past the table.
        # Strictly increasing, so an off-by-one index is visible, and small
        # enough at the cap that Gate 2 is not what this measures.
        threshold = {c: 0.01 * c for c in range(1, 21)}
        assert threshold[MAX_COMPLEXITY] == pytest.approx(0.20)

        just_above = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                complexity=MAX_COMPLEXITY,
                valid_r2=0.99,
                ceiling_fraction=0.50,
                ceiling_r2=0.03,
                candidate_test_r2=threshold[MAX_COMPLEXITY] + 0.01,
            ),
            threshold,
        )
        assert just_above.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

        just_below = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                complexity=MAX_COMPLEXITY,
                valid_r2=0.99,
                ceiling_fraction=0.50,
                ceiling_r2=0.03,
                candidate_test_r2=threshold[MAX_COMPLEXITY] - 0.01,
            ),
            threshold,
        )
        assert just_below.status == AcceptanceStatus.REJECTED_CEILING

    def test_a_high_ceiling_fraction_needs_no_floor(self):
        """Outside the waiver regime no floor is added.

        Section 6.9.3: F7's own unconditional hard-gate floor already covers
        that region, so the amended rule deliberately does not reproduce old
        F5's every branch.  This is the disclosed residual gap, pinned.
        """
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                ceiling_fraction=0.95, ceiling_r2=0.6, candidate_test_r2=-1.0
            ),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_ceiling_exactly_at_gate(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(ceiling_fraction=0.80, ceiling_r2=0.6),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_ceiling_waiver_boundary_not_triggered(self):
        """ceiling_r2 == 0.05 does NOT trigger the waiver (strict <).

        Unchanged in spirit by A3.5; the fixture now supplies the floor field
        so the boundary, not the floor, is what this measures.
        """
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(
                ceiling_fraction=0.50, ceiling_r2=0.05, candidate_test_r2=0.99
            ),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_CEILING
        assert CEILING_WAIVER_THRESHOLD == 0.05


# -----------------------------------------------------------------------
# Falsification harness
# -----------------------------------------------------------------------

class TestFalsification:

    def test_all_pass(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_one_fail(self):
        fals = _all_pass_falsification()
        fals[FalsificationRung.F1_REPRODUCIBILITY] = FalsificationResult.FAIL
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(falsification_results=fals),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_FALSIFICATION

    def test_not_applicable_on_a_hard_rung_blocks(self):
        """A3.5 section 6.9.4's fail-closed repair.

        Under the superseded ``check_falsification_harness`` a stray
        ``NOT_APPLICABLE`` fell through and the harness returned True.  The
        amended predicate is ``result != PASS``, so it now rejects identically
        to a FAIL.
        """
        for rung in sorted(REQUIRED_HARD_GATES, key=lambda r: r.value):
            fals = _all_pass_falsification()
            fals[rung] = FalsificationResult.NOT_APPLICABLE
            result = evaluate_structural_acceptance(
                CaseAdequacyStatus.M0_NOT_REJECTED,
                _passing_candidate(falsification_results=fals),
                _standard_threshold(),
            )
            assert result.status == AcceptanceStatus.REJECTED_FALSIFICATION, (
                f"NOT_APPLICABLE on {rung.value} must fail closed"
            )
            assert not check_gate8(fals)

    def test_each_hard_rung_fail_blocks(self):
        for rung in sorted(REQUIRED_HARD_GATES, key=lambda r: r.value):
            fals = _all_pass_falsification()
            fals[rung] = FalsificationResult.FAIL
            result = evaluate_structural_acceptance(
                CaseAdequacyStatus.M0_NOT_REJECTED,
                _passing_candidate(falsification_results=fals),
                _standard_threshold(),
            )
            assert result.status == AcceptanceStatus.REJECTED_FALSIFICATION, (
                f"rung {rung} should reject"
            )

    def test_missing_hard_rung_blocks(self):
        for rung in sorted(REQUIRED_HARD_GATES, key=lambda r: r.value):
            fals = _all_pass_falsification()
            del fals[rung]
            assert not check_gate8(fals)
            result = evaluate_structural_acceptance(
                CaseAdequacyStatus.M0_NOT_REJECTED,
                _passing_candidate(falsification_results=fals),
                _standard_threshold(),
            )
            assert result.status == AcceptanceStatus.REJECTED_FALSIFICATION

    def test_the_hard_set_is_exactly_f1_f4_f7_f10(self):
        assert {r.value for r in REQUIRED_HARD_GATES} == {
            "F1_REPRODUCIBILITY",
            "F4_COMPOUND_HOLDOUT",
            "F7_INFLUENCE_DROP",
            "F10_NEGATIVE_CONTROL",
        }

    def test_f5_is_not_independently_gate8_gating(self):
        """F5 is superseded: it is not even a member of the rung enum."""
        assert not hasattr(FalsificationRung, "F5_SCAFFOLD_HOLDOUT")
        assert "F5_SCAFFOLD_HOLDOUT" not in {r.value for r in FalsificationRung}
        assert "F5_SCAFFOLD_HOLDOUT" not in {r.value for r in REQUIRED_HARD_GATES}

    def test_f9_failure_alone_does_not_block(self):
        """F9 is reported, never gating.

        It cannot be placed in the Gate-8 mapping at all, and its absence from
        REQUIRED_HARD_GATES means a failing F9 leaves an otherwise-passing case
        accepted.
        """
        assert FalsificationRung.F9_ENERGY_SUBSET in SECONDARY_REPORTED_RUNGS
        assert FalsificationRung.F9_ENERGY_SUBSET not in REQUIRED_HARD_GATES

        fals = _all_pass_falsification()
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(falsification_results=fals),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

        # Even if an F9 result were smuggled into the mapping, check_gate8
        # never reads it.
        smuggled = dict(fals)
        smuggled[FalsificationRung.F9_ENERGY_SUBSET] = FalsificationResult.FAIL
        assert check_gate8(smuggled) is True


# -----------------------------------------------------------------------
# No candidate
# -----------------------------------------------------------------------

class TestNoCandidate:

    def test_no_candidate_unevaluable(self):
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            None,
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.UNEVALUABLE


# -----------------------------------------------------------------------
# Frozen constants
# -----------------------------------------------------------------------

class TestFrozenConstants:

    def test_stability_gate(self):
        assert STABILITY_GATE == 20
        assert STABILITY_DENOMINATOR == 30

    def test_max_complexity(self):
        assert MAX_COMPLEXITY == 20

    def test_invalid_fraction(self):
        assert MAX_INVALID_FRACTION == 0.005

    def test_ceiling_fraction_gate(self):
        assert CEILING_FRACTION_GATE == 0.80

    def test_ceiling_waiver(self):
        assert CEILING_WAIVER_THRESHOLD == 0.05
