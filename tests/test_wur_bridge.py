import numpy as np
import pandas as pd
import pytest

from muru.wur_bridge import (
    build_population_b, per_energy_statistics, rule_passes,
)

LADDER = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def _mu_frame(keys, offsets=None, energies=LADDER, seed=0):
    """A synthetic mu table: a smooth decreasing ladder per compound, with a
    per-compound level so Spearman has something to correlate."""
    rng = np.random.default_rng(seed)
    levels = {k: 0.3 + 0.6 * rng.random() for k in keys}
    rows = []
    for k in keys:
        for e in energies:
            base = levels[k] * (1.0 - 0.008 * (e - 15.0))
            rows.append({"connectivity_key": k, "ce_numeric": e,
                         "mu": base + (offsets or {}).get(e, 0.0)})
    return pd.DataFrame(rows)


def _keys(n):
    return [f"K{i:04d}" for i in range(n)]


# -- population B ----------------------------------------------------------

def test_population_b_is_the_intersection_of_wur_dev_and_lcsb_development():
    b = build_population_b({"A", "B", "C"}, {"B", "C", "D"}, set(), set())
    assert b == ["B", "C"]


def test_population_b_is_sorted_and_deduplicated():
    b = build_population_b({"C", "A", "A"}, {"A", "C"}, set(), set())
    assert b == ["A", "C"]


def test_population_b_removes_anything_sealed_on_the_wur_side():
    b = build_population_b({"A", "B"}, {"A", "B"}, {"B"}, set())
    assert b == ["A"]


def test_population_b_removes_anything_sealed_on_the_lcsb_side():
    b = build_population_b({"A", "B"}, {"A", "B"}, set(), {"A"})
    assert b == ["B"]


def test_population_b_is_empty_when_the_corpora_do_not_overlap():
    assert build_population_b({"A"}, {"B"}, set(), set()) == []


# -- per-energy statistics -------------------------------------------------

def test_statistics_cover_every_ladder_energy():
    keys = _keys(30)
    stats = per_energy_statistics(_mu_frame(keys), _mu_frame(keys), keys)
    assert [s["ce_numeric"] for s in stats] == LADDER


def test_identical_corpora_give_zero_delta_and_unit_correlation():
    keys = _keys(30)
    frame = _mu_frame(keys)
    for s in per_energy_statistics(frame, frame, keys):
        assert s["median_abs_delta"] == pytest.approx(0.0)
        assert s["median_signed_delta"] == pytest.approx(0.0)
        assert s["spearman_rho"] == pytest.approx(1.0)
        assert s["n"] == 30
        assert s["passes"] is True


def test_a_constant_offset_shows_up_as_a_signed_delta_of_that_size():
    keys = _keys(30)
    lcsb = _mu_frame(keys)
    wur = _mu_frame(keys, offsets={e: 0.09 for e in LADDER})
    for s in per_energy_statistics(wur, lcsb, keys):
        assert s["median_signed_delta"] == pytest.approx(0.09)
        assert s["spearman_rho"] == pytest.approx(1.0)
        assert s["passes"] is False


def test_n_reports_only_compounds_present_on_both_sides_at_that_energy():
    keys = _keys(10)
    lcsb = _mu_frame(keys)
    lcsb = lcsb[~((lcsb["connectivity_key"] == "K0000")
                  & (lcsb["ce_numeric"] == 45.0))]
    stats = {s["ce_numeric"]: s for s in
             per_energy_statistics(_mu_frame(keys), lcsb, keys)}
    assert stats[45.0]["n"] == 9
    assert stats[15.0]["n"] == 10


def test_statistics_ignore_compounds_outside_population_b():
    keys = _keys(10)
    frame = _mu_frame(keys)
    stats = per_energy_statistics(frame, frame, keys[:5])
    assert all(s["n"] == 5 for s in stats)


def test_an_energy_with_fewer_than_three_pairs_cannot_pass():
    keys = _keys(2)
    frame = _mu_frame(keys)
    for s in per_energy_statistics(frame, frame, keys):
        assert s["spearman_rho"] is None
        assert s["passes"] is False


def test_an_energy_passes_only_when_both_conditions_hold():
    keys = _keys(30)
    lcsb = _mu_frame(keys)
    near = _mu_frame(keys, offsets={e: 0.049 for e in LADDER})
    over = _mu_frame(keys, offsets={e: 0.051 for e in LADDER})
    assert all(s["passes"] for s in per_energy_statistics(near, lcsb, keys))
    assert not any(s["passes"] for s in per_energy_statistics(over, lcsb, keys))


def test_uncorrelated_mu_fails_even_with_a_small_median_delta():
    keys = _keys(60)
    lcsb = _mu_frame(keys, seed=1)
    wur = _mu_frame(keys, seed=2)
    stats = per_energy_statistics(wur, lcsb, keys)
    assert any(s["spearman_rho"] < 0.80 for s in stats)


# -- the 5-of-6 rule -------------------------------------------------------

def _stats(passing):
    return [{"ce_numeric": e, "passes": p} for e, p in zip(LADDER, passing)]


def test_rule_passes_on_six_of_six():
    assert rule_passes(_stats([True] * 6)) is True


def test_rule_passes_on_exactly_five_of_six():
    assert rule_passes(_stats([True, True, True, True, True, False])) is True


def test_rule_fails_on_four_of_six():
    assert rule_passes(_stats([True, True, True, True, False, False])) is False


def test_rule_fails_on_none():
    assert rule_passes(_stats([False] * 6)) is False
