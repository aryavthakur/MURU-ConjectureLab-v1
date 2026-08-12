"""Null-calibration arithmetic, finite-simulation p-values, false-positive
counting and K6 adjudication.

The arithmetic here decides the phase, so it is pinned by hand-computed cases.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery import nulls  # noqa: E402


def curves(n=40, seed=0):
    rng = np.random.default_rng(seed)
    return [np.maximum.accumulate(np.sort(rng.uniform(-0.2, 0.6, 21)))
            for _ in range(n)]


def test_threshold_is_the_95th_percentile_at_each_complexity():
    cs = curves()
    t = nulls.threshold_table(cs)
    M = np.vstack(cs)
    for c in (3, 10, 20):
        assert abs(t["threshold_by_complexity"][c]
                   - np.percentile(M[:, c], 95)) < 1e-9


def test_threshold_never_falls_as_complexity_rises():
    t = nulls.threshold_table(curves())
    thr = t["threshold_by_complexity"]
    assert all(thr[i] <= thr[i + 1] + 1e-12 for i in range(len(thr) - 1)), (
        "a larger hypothesis space cannot make chance fitting harder")


def test_threshold_table_records_how_many_worlds_built_it():
    t = nulls.threshold_table(curves(n=37))
    assert t["n_worlds"] == 37 and t["quantile"] == 95.0


def test_all_four_master_plan_null_constructions_are_declared():
    assert len(nulls.NULL_CONSTRUCTIONS) == 4
    assert "descriptors_permuted_across_compounds" in nulls.NULL_CONSTRUCTIONS


def test_false_positive_rate_reports_exact_numerator_and_denominator():
    fp = nulls.false_positive_rate(3, 100)
    assert fp["n_accepted"] == 3 and fp["n_valid_replicates"] == 100
    assert abs(fp["rate"] - 0.03) < 1e-12


def test_zero_accepted_does_not_produce_a_zero_probability_claim():
    """A 0/100 point estimate must still carry a non-degenerate upper bound."""
    fp = nulls.false_positive_rate(0, 100)
    assert fp["rate"] == 0.0
    assert fp["ci"][0] == 0.0
    assert fp["ci"][1] > 0.02, "the interval, not the point estimate, is the claim"
    assert "zero" in fp["note"]


def test_clopper_pearson_interval_brackets_the_estimate():
    for k in (0, 1, 5, 17, 100):
        fp = nulls.false_positive_rate(k, 100)
        assert fp["ci"][0] <= fp["rate"] <= fp["ci"][1]


def test_k6_does_not_fire_at_exactly_five_of_one_hundred():
    """The criterion is <= 5%, so 5/100 passes and 6/100 fails."""
    assert not nulls.adjudicate_k6(nulls.false_positive_rate(5, 100))["fires"]
    assert nulls.adjudicate_k6(nulls.false_positive_rate(6, 100))["fires"]


def test_k6_verdict_string_matches_the_flag():
    for k in (0, 5, 6, 40):
        a = nulls.adjudicate_k6(nulls.false_positive_rate(k, 100))
        assert a["fires"] == (a["verdict"] == "K6 FIRES")


def test_k6_reports_the_interval_alongside_the_point_criterion():
    a = nulls.adjudicate_k6(nulls.false_positive_rate(4, 100))
    assert a["ci"][1] > a["observed_rate"]
    assert a["n_valid_replicates"] == 100


def test_empty_calibration_is_an_error_not_a_silent_default():
    with pytest.raises(ValueError):
        nulls.threshold_table([])
    with pytest.raises(ValueError):
        nulls.false_positive_rate(0, 0)
