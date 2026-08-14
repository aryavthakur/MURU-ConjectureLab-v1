"""Constructed contract tests for G3 (Amendment A3.1).

All fixtures are hand-built.  No Development case outcomes, no Held-out
data, no calibration world execution.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.g3_contract import (
    G3_HELD_OUT_DENOMINATOR,
    G3_WILSON_UPPER_GATE,
    G3Event,
    G3Score,
    classify_f19a_event,
    classify_f19b_event,
    classify_f19c_event,
    classify_f20a_event,
    classify_f20b_event,
    classify_f20c_event,
    classify_g3_event,
    score_g3,
)
from muru.paper_benchmark.structural_acceptance import (
    AcceptanceResult,
    AcceptanceStatus,
)
from muru.paper_benchmark.g2_contract import wilson_upper_95


def _accepted() -> AcceptanceResult:
    return AcceptanceResult(status=AcceptanceStatus.STRUCTURAL_ACCEPTED, gate_reached="all_passed")


def _rejected() -> AcceptanceResult:
    return AcceptanceResult(status=AcceptanceStatus.REJECTED_BELOW_NULL, gate_reached="null_threshold")


def _unevaluable() -> AcceptanceResult:
    return AcceptanceResult(status=AcceptanceStatus.UNEVALUABLE, gate_reached="a1_adequacy")


# -----------------------------------------------------------------------
# F19A: descriptor link destroyed
# -----------------------------------------------------------------------

class TestF19A:

    def test_safe_rejection(self):
        assert classify_f19a_event(_rejected(), None) == G3Event.SAFE

    def test_mass_only_safe(self):
        assert classify_f19a_event(_accepted(), frozenset({"mass"})) == G3Event.SAFE

    def test_empty_support_safe(self):
        """Empty support is mass-only subset, so safe."""
        assert classify_f19a_event(_accepted(), frozenset()) == G3Event.SAFE

    def test_non_mass_unsafe(self):
        assert classify_f19a_event(
            _accepted(), frozenset({"mass", "descriptor"})
        ) == G3Event.UNSAFE

    def test_unevaluable_violation(self):
        assert classify_f19a_event(_unevaluable(), None) == G3Event.VIOLATION


# -----------------------------------------------------------------------
# F19B: mass-preserving null
# -----------------------------------------------------------------------

class TestF19B:

    def test_safe_rejection(self):
        assert classify_f19b_event(_rejected(), None) == G3Event.SAFE

    def test_mass_only_safe(self):
        assert classify_f19b_event(_accepted(), frozenset({"mass"})) == G3Event.SAFE

    def test_non_mass_unsafe(self):
        assert classify_f19b_event(
            _accepted(), frozenset({"mass", "descriptor"})
        ) == G3Event.UNSAFE

    def test_unevaluable_violation(self):
        assert classify_f19b_event(_unevaluable(), None) == G3Event.VIOLATION


# -----------------------------------------------------------------------
# F19C: response cell resampling
# -----------------------------------------------------------------------

class TestF19C:

    def test_non_acceptance_safe(self):
        assert classify_f19c_event(_rejected()) == G3Event.SAFE

    def test_acceptance_unsafe(self):
        assert classify_f19c_event(_accepted()) == G3Event.UNSAFE

    def test_unevaluable_violation(self):
        assert classify_f19c_event(_unevaluable()) == G3Event.VIOLATION


# -----------------------------------------------------------------------
# F20A: latent driver
# -----------------------------------------------------------------------

class TestF20A:

    def test_non_acceptance_safe(self):
        assert classify_f20a_event(_rejected()) == G3Event.SAFE

    def test_acceptance_unsafe(self):
        assert classify_f20a_event(_accepted()) == G3Event.UNSAFE

    def test_unevaluable_violation(self):
        assert classify_f20a_event(_unevaluable()) == G3Event.VIOLATION


# -----------------------------------------------------------------------
# F20B: measurement coupling
# -----------------------------------------------------------------------

class TestF20B:

    def test_non_acceptance_safe(self):
        assert classify_f20b_event(_rejected()) == G3Event.SAFE

    def test_acceptance_unsafe(self):
        assert classify_f20b_event(_accepted()) == G3Event.UNSAFE

    def test_unevaluable_violation(self):
        assert classify_f20b_event(_unevaluable()) == G3Event.VIOLATION


# -----------------------------------------------------------------------
# F20C: out-of-grammar trap
# -----------------------------------------------------------------------

class TestF20C:

    def test_non_acceptance_safe(self):
        assert classify_f20c_event(_rejected()) == G3Event.SAFE

    def test_acceptance_unsafe(self):
        assert classify_f20c_event(_accepted()) == G3Event.UNSAFE

    def test_unevaluable_violation(self):
        assert classify_f20c_event(_unevaluable()) == G3Event.VIOLATION


# -----------------------------------------------------------------------
# G3 event dispatch
# -----------------------------------------------------------------------

class TestG3Dispatch:

    def test_all_variants(self):
        for variant in ("F19A", "F19B", "F19C", "F20A", "F20B", "F20C"):
            result = classify_g3_event(variant, _rejected())
            assert result == G3Event.SAFE

    def test_unknown_variant_raises(self):
        with pytest.raises(ValueError):
            classify_g3_event("F99", _rejected())

    def test_each_f20_variant_accepted_unsafe(self):
        for variant in ("F20A", "F20B", "F20C"):
            result = classify_g3_event(variant, _accepted())
            assert result == G3Event.UNSAFE


# -----------------------------------------------------------------------
# G3 aggregate scoring
# -----------------------------------------------------------------------

class TestG3Score:

    def test_all_safe(self):
        events = [G3Event.SAFE] * 36
        score = score_g3(events)
        assert score.violations == 0
        assert score.gate_passed
        assert score.wilson_upper < 0.15

    def test_all_unsafe(self):
        events = [G3Event.UNSAFE] * 36
        score = score_g3(events)
        assert score.violations == 36
        assert not score.gate_passed

    def test_all_violations(self):
        events = [G3Event.VIOLATION] * 36
        score = score_g3(events)
        assert score.violations == 36
        assert not score.gate_passed

    def test_mixed(self):
        events = [G3Event.SAFE] * 34 + [G3Event.UNSAFE, G3Event.VIOLATION]
        score = score_g3(events)
        assert score.violations == 2
        assert score.denominator == 36

    def test_wrong_count_raises(self):
        with pytest.raises(ValueError):
            score_g3([G3Event.SAFE] * 35)
        with pytest.raises(ValueError):
            score_g3([G3Event.SAFE] * 37)

    def test_unevaluable_counts_as_violation(self):
        """UNEVALUABLE (mapped to VIOLATION) stays in denominator and counts."""
        events = [G3Event.SAFE] * 35 + [G3Event.VIOLATION]
        score = score_g3(events)
        assert score.violations == 1
        assert score.denominator == 36


# -----------------------------------------------------------------------
# Frozen parameters
# -----------------------------------------------------------------------

class TestG3FrozenParameters:

    def test_denominator(self):
        assert G3_HELD_OUT_DENOMINATOR == 36

    def test_gate(self):
        assert G3_WILSON_UPPER_GATE == 0.15

    def test_wilson_upper_at_zero(self):
        """Zero violations should pass."""
        upper = wilson_upper_95(0, 36)
        assert upper <= 0.15
