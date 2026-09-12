import numpy as np
import pandas as pd
import pytest

from muru.wur_bridge import (
    alignment_branch_applies, apply_energy_map, build_population_b,
    fit_energy_map, interpolate_ladder, per_energy_statistics, rule_passes,
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


def _skewed_frame(keys, energies=LADDER, seed=0):
    """A frame whose per-energy delta distribution is deliberately skewed, so
    that the median and the mean of the deltas differ by a wide margin."""
    rng = np.random.default_rng(seed)
    levels = {k: 0.3 + 0.6 * rng.random() for k in keys}
    rows = []
    for k in keys:
        for e in energies:
            rows.append({"connectivity_key": k, "ce_numeric": e,
                         "mu": levels[k] * (1.0 - 0.008 * (e - 15.0))})
    return pd.DataFrame(rows)


def test_the_delta_statistic_is_a_median_and_not_a_mean():
    """Twenty compounds sit at delta = 0.01 and five at delta = 1.0. The
    median delta is 0.01 and passes; the mean is 0.208 and would fail. The
    preregistration names numpy.median, so a mean would be a protocol
    violation, and this is the test that can see it."""
    keys = _keys(25)
    lcsb = _skewed_frame(keys, seed=3)
    wur = lcsb.copy()
    # Outliers must be the 5 highest-mu compounds in lcsb, not an arbitrary
    # slice of the key list: adding +1.0 to a low-ranked compound would push
    # it above higher-ranked ones and break the Spearman correlation, which
    # is not what this test is exercising.
    outliers = set(
        lcsb[lcsb["ce_numeric"] == LADDER[0]].nlargest(5, "mu")["connectivity_key"]
    )
    wur["mu"] = [
        mu + (1.0 if k in outliers else 0.01)
        for k, mu in zip(wur["connectivity_key"], wur["mu"])
    ]
    stats = per_energy_statistics(wur, lcsb, keys)
    for s in stats:
        assert s["n"] == 25
        assert s["median_abs_delta"] == pytest.approx(0.01)
        assert s["median_signed_delta"] == pytest.approx(0.01)
        # The mean would be 0.2092, far above MEDIAN_ABS_DELTA_MAX.
        assert np.mean([0.01] * 20 + [1.0] * 5) > 0.05
    assert rule_passes(stats) is True


def test_a_constant_mu_vector_gives_a_null_correlation_not_a_number():
    """scipy returns nan when either vector is constant. The preregistration
    requires that recorded as a null correlation, distinct from the
    too-few-pairs case, and requires that energy to fail."""
    keys = _keys(10)
    lcsb = _mu_frame(keys, seed=9)
    wur = lcsb.copy()
    wur["mu"] = 0.5  # constant on the WUR side at every energy
    stats = per_energy_statistics(wur, lcsb, keys)
    for s in stats:
        assert s["n"] == 10, "the pairs are present; only the correlation is undefined"
        assert s["spearman_rho"] is None
        assert s["passes"] is False
        assert s["median_abs_delta"] is not None
    assert rule_passes(stats) is False


def _stat(energy, signed, rho):
    return {"ce_numeric": energy, "n": 30, "median_signed_delta": signed,
            "median_abs_delta": abs(signed), "spearman_rho": rho,
            "passes": abs(signed) <= 0.05 and rho >= 0.80}


def test_branch_applies_to_a_consistent_within_tolerance_offset():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER]
    assert alignment_branch_applies(stats) is True


def test_branch_does_not_apply_when_signs_disagree():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [_stat(90.0, -0.09, 0.95)]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_an_offset_exceeds_the_cap():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [_stat(90.0, 0.16, 0.95)]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_correlation_is_weak_anywhere():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [_stat(90.0, 0.09, 0.79)]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_the_base_rule_already_passed():
    stats = [_stat(e, 0.01, 0.99) for e in LADDER]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_an_energy_has_no_pairs():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [
        {"ce_numeric": 90.0, "n": 0, "median_signed_delta": None,
         "median_abs_delta": None, "spearman_rho": None, "passes": False}]
    assert alignment_branch_applies(stats) is False


# -- interpolation ---------------------------------------------------------

def test_interpolate_ladder_reproduces_the_knots_exactly():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    out = interpolate_ladder(np.array(LADDER), values, np.array(LADDER))
    assert np.allclose(out, values)


def test_interpolate_ladder_is_monotone_between_monotone_knots():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    targets = np.linspace(15.0, 90.0, 200)
    out = interpolate_ladder(np.array(LADDER), values, targets)
    assert np.all(np.diff(out) <= 1e-12)


def test_interpolate_ladder_never_overshoots_its_knots():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    out = interpolate_ladder(np.array(LADDER), values,
                             np.linspace(15.0, 90.0, 200))
    assert out.max() <= values.max() + 1e-12
    assert out.min() >= values.min() - 1e-12


def test_interpolate_ladder_clamps_instead_of_extrapolating():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    out = interpolate_ladder(np.array(LADDER), values, np.array([-5.0, 200.0]))
    assert out[0] == pytest.approx(values[0])
    assert out[1] == pytest.approx(values[-1])


# -- the map ---------------------------------------------------------------

def test_apply_energy_map_counts_cells_clamped_at_the_ladder_ends():
    keys = _keys(5)
    mapped, n_clamped = apply_energy_map(_mu_frame(keys), a=20.0, b=1.0)
    # T(90) = 110 and T(75) = 95 are above the ladder for all 5 compounds.
    assert n_clamped == 10


def test_apply_energy_map_with_the_identity_changes_nothing():
    keys = _keys(5)
    frame = _mu_frame(keys)
    mapped, n_clamped = apply_energy_map(frame, a=0.0, b=1.0)
    assert n_clamped == 0
    merged = frame.merge(mapped, on=["connectivity_key", "ce_numeric"],
                         suffixes=("_in", "_out"))
    assert np.allclose(merged["mu_in"], merged["mu_out"])


def test_fit_energy_map_recovers_the_identity_when_the_corpora_match():
    """With identical corpora the global optimum is T(E) = E exactly, and it
    sits interior to the frozen box, so this pins that the fitter finds a
    known reachable optimum rather than merely improving on its start point.
    mu is strictly decreasing in E here, so J = 0 forces T(E) = E at all six
    rungs, which forces a = 0 and b = 1: the minimiser is unique."""
    keys = _keys(30)
    frame = _mu_frame(keys, seed=13)
    fit = fit_energy_map(frame, frame, keys)
    assert fit["objective"] < 1e-6
    assert fit["a"] == pytest.approx(0.0, abs=0.5)
    assert fit["b"] == pytest.approx(1.0, abs=0.02)
    assert fit["converged"] is True


def test_the_fitted_map_is_never_worse_than_doing_nothing():
    """The honest property of any fit: whatever it returns, it must not score
    worse on its own objective than the identity map, which is always
    available to it because a = 0, b = 1 is interior to the frozen box."""
    keys = _keys(30)
    lcsb = _mu_frame(keys, seed=17)
    wur = _mu_frame(keys, seed=17, offsets={e: 0.08 for e in LADDER})
    fit = fit_energy_map(wur, lcsb, keys)
    identity_objective = sum(
        abs(s["median_signed_delta"])
        for s in per_energy_statistics(wur, lcsb, keys)
    )
    assert fit["objective"] <= identity_objective + 1e-9


def test_fit_energy_map_is_deterministic_at_the_frozen_seed():
    keys = _keys(20)
    lcsb = _mu_frame(keys, seed=5)
    wur = _mu_frame(keys, seed=5, offsets={e: 0.08 for e in LADDER})
    first = fit_energy_map(wur, lcsb, keys)
    second = fit_energy_map(wur, lcsb, keys)
    assert first["a"] == second["a"]
    assert first["b"] == second["b"]


def test_fit_energy_map_stays_inside_the_frozen_box():
    from muru.wur_bridge_constants import ALIGNMENT_A_BOUNDS, ALIGNMENT_B_BOUNDS
    keys = _keys(20)
    lcsb = _mu_frame(keys, seed=7)
    wur = _mu_frame(keys, seed=7, offsets={e: 0.12 for e in LADDER})
    fit = fit_energy_map(wur, lcsb, keys)
    assert ALIGNMENT_A_BOUNDS[0] <= fit["a"] <= ALIGNMENT_A_BOUNDS[1]
    assert ALIGNMENT_B_BOUNDS[0] <= fit["b"] <= ALIGNMENT_B_BOUNDS[1]
