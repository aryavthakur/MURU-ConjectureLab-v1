import numpy as np
import pytest

from muru import features as F
from muru.spectra import Spectrum
from muru.wur_stage2 import spectral_features as SF


def _spec(mz, inten, pre):
    return Spectrum(mz=np.array(mz, float), intensity=np.array(inten, float), precursor_mz=pre)


def test_features_reproduce_frozen_mu_and_have_every_name():
    s = _spec([50, 100, 150, 200], [1, 2, 3, 4], 200.0)
    f = SF.spectrum_features(s)
    assert set(f) == set(SF.FEATURE_NAMES)
    assert f["mu"] == pytest.approx(F.mu(s))
    assert f["survival_yield"] == pytest.approx(0.4)
    assert f["peak_count"] == 4 and f["n_peaks_1pct"] == 4
    assert f["frac_x_lt_025"] == 0.0 and f["frac_x_025_050"] == pytest.approx(0.1)
    assert f["frac_x_050_075"] == pytest.approx(0.2) and f["frac_x_ge_075"] == pytest.approx(0.3 + 0.4)
    assert f["x_wq50"] > 0.5 and 0 < f["x_wsd"] < 0.5


def test_bin_fractions_sum_to_one_and_quantiles_monotone():
    rng = np.random.default_rng(0)
    for _ in range(20):
        n = int(rng.integers(2, 40))
        mz = np.sort(rng.uniform(30, 300, n)); inten = rng.uniform(0, 1e5, n)
        f = SF.spectrum_features(_spec(mz, inten, 300.0))
        assert f["frac_x_lt_025"] + f["frac_x_025_050"] + f["frac_x_050_075"] + f["frac_x_ge_075"] == pytest.approx(1.0)
        assert f["x_wq25"] <= f["x_wq50"] <= f["x_wq75"]


def test_degenerate_spectrum_yields_nan_not_crash():
    f = SF.spectrum_features(_spec([100.0], [0.0], 100.0))
    assert np.isnan(f["x_wsd"]) and np.isnan(f["mu"])
