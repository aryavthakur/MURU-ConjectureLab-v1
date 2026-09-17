"""Tests for the frozen Design A spectrum similarity layer.

Entirely synthetic. No observed spectrum of the adjudication population is read,
opened, parsed or summarized anywhere in this file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "spectrum_similarity.py"
_spec = importlib.util.spec_from_file_location("ce_design_a_spectrum_similarity", MODULE_PATH)
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


# The pinned sha256 of the frozen configuration. Any change to any convention in
# FROZEN_CONFIG changes this value and fails this suite. That is the point.
PINNED_FROZEN_CONFIG_SHA256 = (
    "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def spec(mz, inten):
    return (np.asarray(mz, dtype=float), np.asarray(inten, dtype=float))


def bin_boundary_bracket(start_mz: float):
    """Return (lo, hi) straddling the first bin boundary above start_mz.

    bin_index(lo) == bin_index(start_mz) and bin_index(hi) == bin_index(lo) + 1,
    with hi the next representable double above lo.
    """
    k = S.bin_index(start_mz)
    lo, hi = float(start_mz), float(start_mz) + 1.0
    assert S.bin_index(hi) > k
    while True:
        mid = (lo + hi) / 2.0
        if mid == lo or mid == hi:
            break
        if S.bin_index(mid) == k:
            lo = mid
        else:
            hi = mid
    assert S.bin_index(lo) == k
    assert S.bin_index(hi) == k + 1
    return lo, hi


BW = S.bin_width_da()


# ---------------------------------------------------------------------------
# 1. identical spectra
# ---------------------------------------------------------------------------

def test_identical_spectra_are_exactly_one():
    mz = [100.001, 210.037, 333.502, 401.0]
    linear = [1.0, 0.5, 0.25, 0.125]
    # Prediction arrives on the ms-pred sqrt scale, observation on the linear scale.
    pred = spec(mz, np.sqrt(linear))
    obs = spec(mz, linear)
    assert S.cosine_similarity_untransformed(pred, obs) == 1.0
    assert S.jensen_shannon_similarity(pred, obs) == 1.0


def test_identical_spectra_are_exactly_one_with_parent_mass():
    mz = [100.001, 210.037, 333.502]
    linear = [1.0, 0.5, 0.25]
    pred = spec(mz, np.sqrt(linear))
    obs = spec(mz, linear)
    assert S.cosine_similarity_untransformed(pred, obs, parent_mass=400.0) == 1.0
    assert S.jensen_shannon_similarity(pred, obs, parent_mass=400.0) == 1.0


# ---------------------------------------------------------------------------
# 2. disjoint spectra
# ---------------------------------------------------------------------------

def test_disjoint_spectra_are_exactly_zero():
    pred = spec([100.001, 150.001], np.sqrt([1.0, 0.5]))
    obs = spec([200.001, 250.001], [1.0, 0.5])
    assert S.cosine_similarity_untransformed(pred, obs) == 0.0
    assert S.jensen_shannon_similarity(pred, obs) == 0.0


def test_disjoint_single_peaks_are_exactly_zero():
    pred = spec([120.0], [1.0])
    obs = spec([320.0], [1.0])
    assert S.cosine_similarity_untransformed(pred, obs) == 0.0
    assert S.jensen_shannon_similarity(pred, obs) == 0.0


# ---------------------------------------------------------------------------
# 3. scale invariance
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("factor", [1e-6, 0.5, 3.0, 1000.0, 1e6])
def test_cosine_invariant_to_rescale_of_either_side(factor):
    mz = [100.001, 210.037, 333.502]
    linear = np.array([1.0, 0.37, 0.11])
    pred = spec(mz, np.sqrt(linear))
    obs = spec(mz, [0.9, 0.4, 0.2])

    base = S.cosine_similarity_untransformed(pred, obs)
    # Rescaling the prediction on its own sqrt scale is a sqrt(factor) rescale.
    pred_scaled = spec(mz, np.sqrt(linear) * np.sqrt(factor))
    obs_scaled = spec(mz, np.array([0.9, 0.4, 0.2]) * factor)

    assert S.cosine_similarity_untransformed(pred_scaled, obs) == pytest.approx(base, abs=1e-12)
    assert S.cosine_similarity_untransformed(pred, obs_scaled) == pytest.approx(base, abs=1e-12)
    assert S.cosine_similarity_untransformed(pred_scaled, obs_scaled) == pytest.approx(base, abs=1e-12)


@pytest.mark.parametrize("factor", [1e-6, 0.5, 3.0, 1000.0, 1e6])
def test_js_invariant_to_rescale_of_either_side(factor):
    mz = [100.001, 210.037, 333.502]
    linear = np.array([1.0, 0.37, 0.11])
    pred = spec(mz, np.sqrt(linear))
    obs = spec(mz, [0.9, 0.4, 0.2])

    base = S.jensen_shannon_similarity(pred, obs)
    pred_scaled = spec(mz, np.sqrt(linear) * np.sqrt(factor))
    obs_scaled = spec(mz, np.array([0.9, 0.4, 0.2]) * factor)

    assert S.jensen_shannon_similarity(pred_scaled, obs) == pytest.approx(base, abs=1e-12)
    assert S.jensen_shannon_similarity(pred, obs_scaled) == pytest.approx(base, abs=1e-12)
    assert S.jensen_shannon_similarity(pred_scaled, obs_scaled) == pytest.approx(base, abs=1e-12)


# ---------------------------------------------------------------------------
# 4. the sqrt inverse
# ---------------------------------------------------------------------------

def test_square_recovers_sqrt_input_exactly():
    linear = np.array([1.0, 0.25, 0.0625, 4.0, 2.25e-4])
    recovered = S._apply_inverse_transform(np.sqrt(linear), "square")
    assert np.array_equal(recovered, linear)


def test_prepared_prediction_matches_linear_observation_bit_for_bit():
    mz = [100.001, 210.037, 333.502]
    linear = np.array([1.0, 0.25, 0.0625])
    p_idx, p_val = S.prepare_spectrum(spec(mz, np.sqrt(linear)), inverse_transform="square")
    o_idx, o_val = S.prepare_spectrum(spec(mz, linear), inverse_transform="identity")
    assert np.array_equal(p_idx, o_idx)
    assert np.array_equal(p_val, o_val)


def test_sqrt_inverse_changes_the_value_in_the_expected_direction():
    """The prediction is the exact sqrt encoding of the observation.

    With the frozen inverse transform the two agree exactly, so cosine is 1.0.
    Skipping the inverse leaves the prediction compressed toward its base peak and
    the cosine must fall strictly below 1.0.
    """
    mz = [100.001, 200.001]
    # 0.0625 is exactly representable and its square root, 0.25, is too, so the
    # sqrt encoding and its inverse are exact here and the test is about the
    # transform, not about float rounding.
    linear = np.array([1.0, 0.0625])
    pred = spec(mz, np.sqrt(linear))  # [1.0, 0.25] on the sqrt scale
    obs = spec(mz, linear)

    with_inverse = S.cosine_similarity_untransformed(pred, obs)
    without_inverse = S.cosine_similarity_untransformed(
        pred, obs, pred_inverse_transform="identity", allow_override=True
    )
    assert with_inverse == 1.0
    assert without_inverse < with_inverse
    sqrt_side = np.array([1.0, 0.25])
    expected_without = float(
        np.dot(sqrt_side, linear)
        / (np.linalg.norm(sqrt_side) * np.linalg.norm(linear))
    )
    assert without_inverse == pytest.approx(expected_without, abs=1e-14)

    js_with = S.jensen_shannon_similarity(pred, obs)
    js_without = S.jensen_shannon_similarity(
        pred, obs, pred_inverse_transform="identity", allow_override=True
    )
    assert js_with == 1.0
    assert js_without < js_with


def test_double_inverse_is_not_applied():
    """The inverse is applied exactly once per side, never twice."""
    mz = [100.001, 200.001]
    linear = np.array([1.0, 0.0625])
    _, once = S.prepare_spectrum(spec(mz, np.sqrt(linear)), inverse_transform="square")
    _, direct = S.prepare_spectrum(spec(mz, linear), inverse_transform="identity")
    assert np.array_equal(once, direct)
    # A second square would give [1.0, 0.00390625], which it must not.
    assert not np.allclose(once, np.square(linear) / np.square(linear).max())


# ---------------------------------------------------------------------------
# 5. tolerance and the bin boundary
# ---------------------------------------------------------------------------

def test_bin_index_rule_matches_ms_pred():
    scale = (S.FROZEN_CONFIG["num_bins"] - 1) / S.FROZEN_CONFIG["mass_upper_limit_da"]
    for mz in [0.0, 1.0, 100.0, 250.12345, 999.9, 1499.0]:
        assert S.bin_index(mz) == int(np.floor(mz * scale)) + 1


def test_bin_width_is_the_frozen_tolerance():
    assert S.FROZEN_CONFIG["tolerance_unit"] == "Da"
    assert S.FROZEN_CONFIG["tolerance_value"] == pytest.approx(BW, abs=0.0)
    assert BW == pytest.approx(0.10000666711114074, abs=1e-15)


def test_peaks_inside_the_tolerance_match_and_outside_do_not():
    lo, hi = bin_boundary_bracket(100.0)
    # hi is one ulp above lo yet lands in the next bin: matching is bin coincidence.
    assert S.cosine_similarity_untransformed(spec([lo], [1.0]), spec([lo], [1.0])) == 1.0
    assert S.cosine_similarity_untransformed(spec([lo], [1.0]), spec([hi], [1.0])) == 0.0
    assert S.jensen_shannon_similarity(spec([lo], [1.0]), spec([hi], [1.0])) == 0.0

    # Two peaks half a bin width apart but inside the same bin do match.
    inside = lo - 0.5 * BW
    assert S.bin_index(inside) == S.bin_index(lo)
    assert S.cosine_similarity_untransformed(spec([inside], [1.0]), spec([lo], [1.0])) == 1.0

    # Two peaks more than one bin width apart can never share a bin.
    outside = hi + 1.1 * BW
    assert S.bin_index(outside) > S.bin_index(hi)
    assert S.cosine_similarity_untransformed(spec([lo], [1.0]), spec([outside], [1.0])) == 0.0


def test_peaks_in_the_same_bin_are_pooled_by_addition():
    idx, vals = S.prepare_spectrum(
        spec([100.001, 100.002, 100.003], [1.0, 1.0, 1.0]), inverse_transform="identity"
    )
    assert idx.shape == (1,)
    # max normalization first (all become 1.0), then addition pooling.
    assert vals[0] == pytest.approx(3.0, abs=1e-15)


def test_peaks_above_the_mass_upper_limit_are_dropped():
    above = S.FROZEN_CONFIG["mass_upper_limit_da"] + 10.0
    idx, vals = S.prepare_spectrum(
        spec([100.001, above], [1.0, 1.0]), inverse_transform="identity"
    )
    assert idx.shape == (1,)


# ---------------------------------------------------------------------------
# 6. precursor treatment and mass cutoff
# ---------------------------------------------------------------------------

def test_mass_cutoff_keeps_parent_plus_one_and_drops_above():
    parent = 300.0
    kept = parent + 0.5   # inside parent_mass + 1.0
    dropped = parent + 1.5  # outside
    idx, _ = S.prepare_spectrum(
        spec([100.001, kept, dropped], [1.0, 0.5, 0.5]),
        inverse_transform="identity",
        parent_mass=parent,
    )
    assert idx.shape == (2,)
    assert S.bin_index(dropped) not in set(idx.tolist())
    assert S.bin_index(kept) in set(idx.tolist())


def test_mass_cutoff_changes_the_endpoint():
    parent = 300.0
    mz_shared = [100.001, 200.001]
    pred = spec(mz_shared + [parent + 1.5], np.sqrt([1.0, 0.25, 0.5625]))
    obs = spec(mz_shared, [1.0, 0.25])
    # With the cutoff the extra prediction peak is removed and the two agree.
    assert S.cosine_similarity_untransformed(pred, obs, parent_mass=parent) == 1.0
    # Without a parent mass there is no cutoff and the extra peak costs similarity.
    assert S.cosine_similarity_untransformed(pred, obs, parent_mass=None) < 1.0


def test_frozen_default_keeps_the_precursor_peak():
    assert S.FROZEN_CONFIG["precursor_treatment"] == "keep"
    parent = 300.0
    idx, _ = S.prepare_spectrum(
        spec([100.001, parent], [1.0, 1.0]),
        inverse_transform="identity",
        parent_mass=parent,
    )
    assert S.bin_index(parent) in set(idx.tolist())


def test_precursor_removal_option_drops_at_the_documented_index():
    parent = 300.0
    num_bins = S.FROZEN_CONFIG["num_bins"]
    upper = S.FROZEN_CONFIG["mass_upper_limit_da"]
    cut = int((parent - 1.0) * num_bins / upper)

    # A peak whose bin index is just below the cut survives, just at or above dies.
    mzs = [100.001, 250.0, parent - 0.4, parent]
    idx, _ = S.prepare_spectrum(
        spec(mzs, [1.0, 1.0, 1.0, 1.0]),
        inverse_transform="identity",
        parent_mass=parent,
        precursor_treatment="remove_above_parent_minus_1",
    )
    assert all(int(i) < cut for i in idx.tolist())
    assert S.bin_index(parent) >= cut
    assert S.bin_index(100.001) in set(idx.tolist())


def test_precursor_removal_requires_a_parent_mass():
    with pytest.raises(ValueError):
        S.prepare_spectrum(
            spec([100.0], [1.0]),
            inverse_transform="identity",
            parent_mass=None,
            precursor_treatment="remove_above_parent_minus_1",
        )


def test_precursor_removal_is_refused_without_an_override():
    pred = spec([100.001], [1.0])
    obs = spec([100.001], [1.0])
    with pytest.raises(S.ConfigOverrideError):
        S.cosine_similarity_untransformed(
            pred, obs, parent_mass=300.0,
            precursor_treatment="remove_above_parent_minus_1",
        )
    value = S.cosine_similarity_untransformed(
        pred, obs, parent_mass=300.0,
        precursor_treatment="remove_above_parent_minus_1",
        allow_override=True,
    )
    assert value == 1.0


# ---------------------------------------------------------------------------
# 7. degenerate cases
# ---------------------------------------------------------------------------

def _good():
    return spec([100.001, 200.001], [1.0, 0.5])


DEGENERATE_SPECTRA = {
    "empty": spec([], []),
    "all_zero_intensity": spec([100.001, 200.001], [0.0, 0.0]),
    "all_negative_intensity": spec([100.001, 200.001], [-1.0, -0.5]),
    "all_nan_intensity": spec([100.001, 200.001], [np.nan, np.nan]),
    "all_nan_mz": spec([np.nan, np.nan], [1.0, 0.5]),
    "all_inf_intensity": spec([100.001, 200.001], [np.inf, np.inf]),
    "all_above_upper_limit": spec([2000.0, 3000.0], [1.0, 0.5]),
}


@pytest.mark.parametrize("name", sorted(DEGENERATE_SPECTRA))
def test_degenerate_prediction_returns_the_documented_value(name):
    bad = DEGENERATE_SPECTRA[name]
    for fn in (S.cosine_similarity_untransformed, S.jensen_shannon_similarity):
        value = fn(bad, _good())
        assert value == float(S.FROZEN_CONFIG["empty_spectrum_value"])
        assert not np.isnan(value)


@pytest.mark.parametrize("name", sorted(DEGENERATE_SPECTRA))
def test_degenerate_observation_returns_the_documented_value(name):
    bad = DEGENERATE_SPECTRA[name]
    for fn in (S.cosine_similarity_untransformed, S.jensen_shannon_similarity):
        value = fn(_good(), bad)
        assert value == float(S.FROZEN_CONFIG["empty_spectrum_value"])
        assert not np.isnan(value)


def test_both_sides_degenerate():
    empty = spec([], [])
    assert S.cosine_similarity_untransformed(empty, empty) == 0.0
    assert S.jensen_shannon_similarity(empty, empty) == 0.0


def test_non_finite_peaks_are_dropped_and_the_rest_survives():
    clean = spec([100.001, 200.001], [1.0, 0.5])
    dirty = spec([100.001, np.nan, 200.001, 300.001], [1.0, 0.7, 0.5, np.inf])
    obs = spec([100.001, 200.001], [1.0, 0.5])

    a = S.cosine_similarity_untransformed(spec(*clean), obs, pred_inverse_transform="identity", allow_override=True)
    b = S.cosine_similarity_untransformed(dirty, obs, pred_inverse_transform="identity", allow_override=True)
    assert a == b == 1.0

    ja = S.jensen_shannon_similarity(clean, obs, pred_inverse_transform="identity", allow_override=True)
    jb = S.jensen_shannon_similarity(dirty, obs, pred_inverse_transform="identity", allow_override=True)
    assert ja == jb == 1.0


def test_negative_peaks_are_dropped_not_squared_into_positives():
    idx, vals = S.prepare_spectrum(
        spec([100.001, 200.001], [1.0, -0.5]), inverse_transform="square"
    )
    assert idx.shape == (1,)
    assert vals[0] > 0.0


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        S.cosine_similarity_untransformed(spec([100.0, 200.0], [1.0]), _good())
    with pytest.raises(ValueError):
        S.jensen_shannon_similarity(_good(), (np.array([100.0]), np.array([1.0, 2.0])))


def test_no_endpoint_ever_returns_nan_or_leaves_the_unit_interval():
    rng = np.random.default_rng(20260916)
    for _ in range(200):
        n_p = int(rng.integers(0, 8))
        n_o = int(rng.integers(0, 8))
        p = spec(rng.uniform(50.0, 1400.0, n_p), rng.uniform(0.0, 1.0, n_p))
        o = spec(rng.uniform(50.0, 1400.0, n_o), rng.uniform(0.0, 1.0, n_o))
        for fn in (S.cosine_similarity_untransformed, S.jensen_shannon_similarity):
            v = fn(p, o)
            assert isinstance(v, float)
            assert not np.isnan(v)
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# 8. determinism
# ---------------------------------------------------------------------------

def _messy_pair(rng):
    mz = np.concatenate([
        rng.uniform(50.0, 1400.0, 40),
        # deliberate within bin collisions so that pooling order could matter
        np.array([100.001, 100.002, 100.003, 100.0015, 700.001, 700.002]),
    ])
    inten = np.concatenate([
        rng.uniform(1e-12, 1.0, 40),
        np.array([1.0, 1e-16, 1e-16, 1e-15, 1.0, 1e-16]),
    ])
    return mz, inten


def test_repeated_calls_are_bit_identical():
    rng = np.random.default_rng(11)
    p_mz, p_int = _messy_pair(rng)
    o_mz, o_int = _messy_pair(rng)
    pred, obs = spec(p_mz, p_int), spec(o_mz, o_int)

    c = [S.cosine_similarity_untransformed(pred, obs) for _ in range(25)]
    j = [S.jensen_shannon_similarity(pred, obs) for _ in range(25)]
    assert len(set(x.hex() for x in c)) == 1
    assert len(set(x.hex() for x in j)) == 1


def test_input_order_permutations_are_bit_identical():
    rng = np.random.default_rng(12)
    p_mz, p_int = _messy_pair(rng)
    o_mz, o_int = _messy_pair(rng)

    base_c = S.cosine_similarity_untransformed(spec(p_mz, p_int), spec(o_mz, o_int))
    base_j = S.jensen_shannon_similarity(spec(p_mz, p_int), spec(o_mz, o_int))

    perm_rng = np.random.default_rng(13)
    for _ in range(25):
        pp = perm_rng.permutation(p_mz.shape[0])
        oo = perm_rng.permutation(o_mz.shape[0])
        c = S.cosine_similarity_untransformed(
            spec(p_mz[pp], p_int[pp]), spec(o_mz[oo], o_int[oo])
        )
        j = S.jensen_shannon_similarity(
            spec(p_mz[pp], p_int[pp]), spec(o_mz[oo], o_int[oo])
        )
        assert c.hex() == base_c.hex()
        assert j.hex() == base_j.hex()


def test_prepared_vectors_are_permutation_invariant_bit_for_bit():
    rng = np.random.default_rng(14)
    mz, inten = _messy_pair(rng)
    idx0, val0 = S.prepare_spectrum(spec(mz, inten), inverse_transform="square")
    perm_rng = np.random.default_rng(15)
    for _ in range(25):
        pp = perm_rng.permutation(mz.shape[0])
        idx1, val1 = S.prepare_spectrum(spec(mz[pp], inten[pp]), inverse_transform="square")
        assert np.array_equal(idx0, idx1)
        assert np.array_equal(val0, val1)


# ---------------------------------------------------------------------------
# 9. the frozen configuration itself
# ---------------------------------------------------------------------------

def test_frozen_config_sha256_is_pinned():
    """Regression guard. Changing ANY convention changes this hash and fails here.

    If this test fails, do not edit the pin. Either revert the convention change or
    run a documented re-freeze and update the preregistration and the freeze
    manifest at the same time.
    """
    assert S.frozen_config_sha256() == PINNED_FROZEN_CONFIG_SHA256
    assert S.FROZEN_CONFIG_SHA256 == PINNED_FROZEN_CONFIG_SHA256


def test_frozen_config_sha256_is_the_hash_of_the_canonical_json():
    expected = hashlib.sha256(
        json.dumps(dict(S.FROZEN_CONFIG), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert S.frozen_config_sha256() == expected


def test_frozen_config_records_every_required_convention():
    required = {
        "num_bins",
        "mass_upper_limit_da",
        "tolerance_value",
        "tolerance_unit",
        "tolerance_application",
        "pool_fn",
        "pred_inverse_transform",
        "obs_inverse_transform",
        "normalization_method",
        "normalization_order",
        "precursor_treatment",
        "mass_cutoff_rule",
        "mass_cutoff_offset_da",
        "empty_spectrum_value",
        "zero_norm_value",
        "nonfinite_handling",
        "dtype",
        "js_log_base",
    }
    assert required.issubset(set(S.FROZEN_CONFIG.keys()))
    assert S.FROZEN_CONFIG["dtype"] == "float64"
    assert S.FROZEN_CONFIG["num_bins"] == 15000
    assert S.FROZEN_CONFIG["mass_upper_limit_da"] == 1500.0
    assert S.FROZEN_CONFIG["pool_fn"] == "add"
    assert S.FROZEN_CONFIG["pred_inverse_transform"] == "square"
    assert S.FROZEN_CONFIG["obs_inverse_transform"] == "identity"
    assert S.FROZEN_CONFIG["normalization_method"] == "max"
    assert S.FROZEN_CONFIG["precursor_treatment"] == "keep"


def test_frozen_config_is_not_mutable_in_place():
    with pytest.raises(TypeError):
        S.FROZEN_CONFIG["num_bins"] = 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"num_bins": 1000},
        {"mass_upper_limit": 1005.0},
        {"pool_fn": "max"},
        {"pred_inverse_transform": "identity"},
        {"obs_inverse_transform": "square"},
        {"normalization_method": "sum"},
        {"mass_cutoff_offset_da": 0.0},
        {"dtype": "float32"},
    ],
)
def test_modified_convention_is_refused_without_an_override(kwargs):
    pred, obs = spec([100.001], [1.0]), spec([100.001], [1.0])
    with pytest.raises(S.ConfigOverrideError):
        S.cosine_similarity_untransformed(pred, obs, **kwargs)
    with pytest.raises(S.ConfigOverrideError):
        S.jensen_shannon_similarity(pred, obs, **kwargs)
    # An explicit override runs and returns a number.
    assert isinstance(
        S.cosine_similarity_untransformed(pred, obs, allow_override=True, **kwargs), float
    )


def test_frozen_defaults_run_without_an_override():
    pred, obs = spec([100.001, 200.001], np.sqrt([1.0, 0.25])), spec([100.001, 200.001], [1.0, 0.25])
    assert S.cosine_similarity_untransformed(pred, obs) == 1.0
    assert S.jensen_shannon_similarity(pred, obs) == 1.0


# ---------------------------------------------------------------------------
# 10. metric definitions, checked against closed forms
# ---------------------------------------------------------------------------

def test_cosine_matches_the_closed_form_on_a_two_peak_example():
    mz = [100.001, 200.001]
    pred_linear = np.array([1.0, 0.25])
    obs_linear = np.array([1.0, 0.75])
    value = S.cosine_similarity_untransformed(
        spec(mz, np.sqrt(pred_linear)), spec(mz, obs_linear)
    )
    expected = float(
        np.dot(pred_linear, obs_linear)
        / (np.linalg.norm(pred_linear) * np.linalg.norm(obs_linear))
    )
    assert value == pytest.approx(expected, abs=1e-14)


def test_js_matches_the_closed_form_on_a_two_peak_example():
    mz = [100.001, 200.001]
    pred_linear = np.array([1.0, 0.25])
    obs_linear = np.array([1.0, 0.75])
    value = S.jensen_shannon_similarity(
        spec(mz, np.sqrt(pred_linear)), spec(mz, obs_linear)
    )
    p = pred_linear / pred_linear.sum()
    q = obs_linear / obs_linear.sum()
    m = 0.5 * (p + q)
    jsd = 0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m))
    expected = float(1.0 - jsd / np.log(2.0))
    assert value == pytest.approx(expected, abs=1e-14)


def test_js_half_overlap_is_the_known_value():
    """p = (1, 0), q = (0.5, 0.5) gives JSD = 0.5*ln2 - ... checked numerically."""
    pred = spec([100.001], [1.0])
    obs = spec([100.001, 200.001], [1.0, 1.0])
    p = np.array([1.0, 0.0])
    q = np.array([0.5, 0.5])
    m = 0.5 * (p + q)
    jsd = 0.5 * np.sum(p[p > 0] * np.log(p[p > 0] / m[p > 0])) + 0.5 * np.sum(
        q[q > 0] * np.log(q[q > 0] / m[q > 0])
    )
    expected = float(1.0 - jsd / np.log(2.0))
    assert S.jensen_shannon_similarity(pred, obs) == pytest.approx(expected, abs=1e-14)


def test_js_is_symmetric_under_swapping_the_two_sides():
    mz = [100.001, 200.001, 300.001]
    linear_a = np.array([1.0, 0.25, 0.5])
    linear_b = np.array([0.3, 1.0, 0.2])
    forward = S.jensen_shannon_similarity(spec(mz, np.sqrt(linear_a)), spec(mz, linear_b))
    backward = S.jensen_shannon_similarity(spec(mz, np.sqrt(linear_b)), spec(mz, linear_a))
    assert forward == pytest.approx(backward, abs=1e-14)
