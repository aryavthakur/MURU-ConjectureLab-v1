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
    StructuralCandidate,
    check_falsification_harness,
    evaluate_structural_acceptance,
)


def _all_pass_falsification() -> dict[FalsificationRung, FalsificationResult]:
    return {rung: FalsificationResult.PASS for rung in FalsificationRung}


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

    def test_ceiling_waiver(self):
        """Low ceiling_r2 triggers waiver even when ceiling_fraction is low."""
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(ceiling_fraction=0.50, ceiling_r2=0.03),
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
        """ceiling_r2 == 0.05 does NOT trigger waiver (strict <)."""
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(ceiling_fraction=0.50, ceiling_r2=0.05),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.REJECTED_CEILING


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

    def test_not_applicable_allowed(self):
        fals = _all_pass_falsification()
        fals[FalsificationRung.F7_INFLUENCE_DROP] = FalsificationResult.NOT_APPLICABLE
        result = evaluate_structural_acceptance(
            CaseAdequacyStatus.M0_NOT_REJECTED,
            _passing_candidate(falsification_results=fals),
            _standard_threshold(),
        )
        assert result.status == AcceptanceStatus.STRUCTURAL_ACCEPTED

    def test_each_rung_fail(self):
        for rung in FalsificationRung:
            fals = _all_pass_falsification()
            fals[rung] = FalsificationResult.FAIL
            result = evaluate_structural_acceptance(
                CaseAdequacyStatus.M0_NOT_REJECTED,
                _passing_candidate(falsification_results=fals),
                _standard_threshold(),
            )
            assert result.status == AcceptanceStatus.REJECTED_FALSIFICATION, f"rung {rung} should reject"

    def test_missing_rung_fails(self):
        fals = _all_pass_falsification()
        del fals[FalsificationRung.F10_NEGATIVE_CONTROL]
        assert not check_falsification_harness(fals)


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
