"""RC3 G2 aggregate scorer.

Every event sequence here is constructed.  No test reads a real case, a real
partition, or any real outcome.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.g2_contract import (
    G2_HELD_OUT_DENOMINATOR,
    G2_WILSON_LOWER_GATE,
    G2Event,
    wilson_lower_95,
)
from muru.paper_benchmark.g3_contract import (
    G3_HELD_OUT_DENOMINATOR,
    G3_WILSON_UPPER_GATE,
    G3Event,
)
from muru.paper_benchmark.rc3_scoring import G2Score, score_g2, score_g3


def make_events(successes: int, failures: int, unevaluable: int) -> list[G2Event]:
    return (
        [G2Event.SUCCESS] * successes
        + [G2Event.FAILURE] * failures
        + [G2Event.UNEVALUABLE] * unevaluable
    )


# -----------------------------------------------------------------------
# Denominator enforcement
# -----------------------------------------------------------------------

def test_denominator_is_144():
    assert G2_HELD_OUT_DENOMINATOR == 144


@pytest.mark.parametrize("n", [0, 1, 143, 145, 200])
def test_wrong_event_count_raises(n):
    with pytest.raises(ValueError, match="expected 144"):
        score_g2([G2Event.SUCCESS] * n)


def test_non_g2event_element_raises():
    events = make_events(100, 30, 14)
    events[7] = "SUCCESS"  # a bare string must not sneak through
    with pytest.raises(ValueError, match="expected G2Event"):
        score_g2(events)


def test_denominator_never_shrinks_even_when_all_unevaluable():
    score = score_g2([G2Event.UNEVALUABLE] * 144)
    assert score.denominator == 144
    assert score.successes == 0
    assert score.unevaluable == 144
    assert score.wilson_lower == wilson_lower_95(0, 144)
    assert not score.gate_passed


def test_denominator_never_shrinks_when_all_succeed():
    score = score_g2([G2Event.SUCCESS] * 144)
    assert score.denominator == 144
    assert score.successes == 144
    assert score.gate_passed


# -----------------------------------------------------------------------
# The non-drop property: UNEVALUABLE costs exactly what a failure costs
# -----------------------------------------------------------------------

def test_unevaluable_counts_as_non_success_like_failure():
    with_failures = score_g2(make_events(110, 34, 0))
    with_unevaluable = score_g2(make_events(110, 0, 34))
    assert with_failures.successes == with_unevaluable.successes
    assert with_failures.wilson_lower == with_unevaluable.wilson_lower
    assert with_failures.gate_passed == with_unevaluable.gate_passed


@pytest.mark.parametrize("n_unevaluable", [1, 5, 20, 44])
def test_dropping_unevaluable_would_strictly_inflate_the_bound(n_unevaluable):
    """A run containing UNEVALUABLE cases scores strictly lower than the same
    run with those cases dropped.

    The dropped variant is the arithmetic a shrinking denominator would
    produce.  ``score_g2`` cannot express it, which is the point: the
    comparison is computed directly against ``wilson_lower_95``.
    """
    successes = 100
    failures = 144 - successes - n_unevaluable

    honest = score_g2(make_events(successes, failures, n_unevaluable))

    # What a shrinking denominator would have reported.
    dropped_denominator = 144 - n_unevaluable
    dishonest_bound = wilson_lower_95(successes, dropped_denominator)

    assert honest.denominator == 144
    assert honest.wilson_lower < dishonest_bound


def test_dropping_unevaluable_can_flip_the_gate():
    """The non-drop rule is not cosmetic: it changes the verdict."""
    successes, n_unevaluable = 108, 24
    failures = 144 - successes - n_unevaluable

    honest = score_g2(make_events(successes, failures, n_unevaluable))
    dishonest_bound = wilson_lower_95(successes, 144 - n_unevaluable)

    assert not honest.gate_passed
    assert dishonest_bound >= G2_WILSON_LOWER_GATE


# -----------------------------------------------------------------------
# Gate arithmetic
# -----------------------------------------------------------------------

def test_gate_uses_frozen_threshold_and_frozen_denominator():
    score = score_g2(make_events(120, 20, 4))
    assert score.wilson_lower == wilson_lower_95(120, 144)
    assert score.gate_passed == (score.wilson_lower >= G2_WILSON_LOWER_GATE)


def test_counts_partition_the_denominator():
    score = score_g2(make_events(90, 30, 24))
    assert score.successes + score.failures + score.unevaluable == 144
    assert score.non_successes == 54
    assert score.success_rate == 90 / 144


def test_score_is_frozen():
    score = score_g2(make_events(90, 30, 24))
    assert isinstance(score, G2Score)
    with pytest.raises(Exception):
        score.successes = 1  # type: ignore[misc]


# -----------------------------------------------------------------------
# G3 gets the same element discipline
# -----------------------------------------------------------------------

def test_g3_rejects_bare_strings_that_would_otherwise_score_as_safe():
    """The frozen scorer accepts strings and scores them SAFE.

    A G3 sequence built from typo'd or stringified labels would pass the
    safety gate: permissive drift. RC3 type-checks before delegating.
    """
    from muru.paper_benchmark.g3_contract import score_g3 as frozen_score_g3

    unsafe_looking = ["banana"] * G3_HELD_OUT_DENOMINATOR
    # The frozen scorer waves it through with a clean bill of health.
    assert frozen_score_g3(unsafe_looking).gate_passed

    with pytest.raises(ValueError, match="expected G3Event"):
        score_g3(unsafe_looking)


def test_g3_enforces_its_denominator():
    with pytest.raises(ValueError, match="expected 36"):
        score_g3([G3Event.SAFE] * 35)


def test_g3_delegates_the_arithmetic_unchanged():
    from muru.paper_benchmark.g3_contract import score_g3 as frozen_score_g3

    events = (
        [G3Event.SAFE] * 30 + [G3Event.UNSAFE] * 3 + [G3Event.VIOLATION] * 3
    )
    assert score_g3(events) == frozen_score_g3(events)


def test_g3_unevaluable_violation_counts_against_the_gate():
    events = [G3Event.SAFE] * 30 + [G3Event.VIOLATION] * 6
    score = score_g3(events)
    assert score.violations == 6
    assert score.denominator == G3_HELD_OUT_DENOMINATOR == 36
    assert score.wilson_upper > G3_WILSON_UPPER_GATE
    assert not score.gate_passed
