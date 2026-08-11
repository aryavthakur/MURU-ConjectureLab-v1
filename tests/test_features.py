"""BLOCKER-class tests for the fragmentation functionals.

Every expected value here is either hand-calculable or traced to a primary
source. Nothing is asserted against a number produced by this codebase.

Entropy provenance: the three properties tested below are stated verbatim in
Li et al. 2021 (Nat Methods 18:1524-1531), whose text reads: "the minimum
spectral entropy is zero for a single fragment ion", "If all ions have the same
intensity, a maximized spectral entropy is reached at ln (number of ions)", and
"a normalized spectral entropy ... by dividing the spectral entropy by ln
(number of ions)". Text extracted from the PDF in the reference pack.

NOTE ON THE MASTER PLAN'S TEST SPEC: master plan section 20 asks for entropy to
be checked "against the four worked examples in Li et al. Fig. 1 (entropies 0,
1, 2, 3)". Those specific panel values live in a figure image and were NOT
extracted, so they are not asserted here. The three properties above are
stronger tests anyway: S = ln(n) for uniform input pins the base of the
logarithm exactly, which is the only thing an implementation can get wrong.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from muru.features import (
    base_peak_fraction, decomposition_residual_exact, fragment_depth, mu,
    normalized_entropy, peak_count, spectral_entropy, survival_yield,
)
from muru.spectra import Spectrum


def spec(mz, inten, precursor=None):
    return Spectrum(np.array(mz, float), np.array(inten, float), precursor)


# ---------------------------------------------------------------------------
# Entropy -- traced to Li et al. 2021
# ---------------------------------------------------------------------------
def test_entropy_single_peak_is_zero():
    """Li et al.: 'the minimum spectral entropy is zero for a single fragment ion'."""
    assert spectral_entropy(spec([100.0], [12345.0])) == 0.0


@pytest.mark.parametrize("n", [2, 3, 4, 5, 10, 50])
def test_entropy_uniform_is_log_n(n):
    """Li et al.: uniform intensities give entropy ln(number of ions).

    This pins the logarithm base. A log2 implementation fails here.
    """
    s = spec([100.0 + i for i in range(n)], [1.0] * n)
    assert spectral_entropy(s) == pytest.approx(math.log(n), abs=1e-12)


def test_entropy_hand_calculated_nonuniform():
    """p = (0.5, 0.25, 0.25) -> S = -0.5 ln0.5 - 2(0.25 ln0.25).

    = 0.5*ln2 + 0.5*ln4 = 0.34657359 + 0.69314718 = 1.03972077
    """
    s = spec([100.0, 200.0, 300.0], [2.0, 1.0, 1.0])
    assert spectral_entropy(s) == pytest.approx(1.0397207708399179, abs=1e-12)


def test_entropy_invariant_to_intensity_scaling():
    """Entropy depends on the normalized distribution, not absolute scale."""
    a = spec([100.0, 200.0, 300.0], [2.0, 1.0, 1.0])
    b = spec([100.0, 200.0, 300.0], [2e9, 1e9, 1e9])
    assert spectral_entropy(a) == pytest.approx(spectral_entropy(b), abs=1e-12)


def test_normalized_entropy_uniform_is_one():
    """Li et al.: normalized entropy ranges 0-1; uniform input is the maximum."""
    s = spec([100.0, 200.0, 300.0, 400.0], [1.0] * 4)
    assert normalized_entropy(s) == pytest.approx(1.0, abs=1e-12)


def test_normalized_entropy_undefined_for_single_peak():
    """ln(1) = 0; the ratio is undefined. Must be NaN, never 0.0 or 1.0."""
    assert math.isnan(normalized_entropy(spec([100.0], [5.0])))


# ---------------------------------------------------------------------------
# mu / SY / phi -- hand-calculable
# ---------------------------------------------------------------------------
def test_mu_all_intensity_at_precursor_is_one():
    assert mu(spec([200.0], [1000.0], precursor=200.0)) == pytest.approx(1.0)


def test_mu_hand_calculated():
    """I=(1000 @ 100), (3000 @ 200); precursor 200.
    weighted mean mz = (1000*100 + 3000*200)/4000 = 700000/4000 = 175
    mu = 175/200 = 0.875
    """
    s = spec([100.0, 200.0], [1000.0, 3000.0], precursor=200.0)
    assert mu(s) == pytest.approx(0.875, abs=1e-12)


def test_survival_yield_hand_calculated():
    """SY = 3000/4000 = 0.75."""
    s = spec([100.0, 200.0], [1000.0, 3000.0], precursor=200.0)
    assert survival_yield(s) == pytest.approx(0.75, abs=1e-12)


def test_fragment_depth_hand_calculated():
    """Only fragment is 100 @ 1000 -> phi = 100/200 = 0.5."""
    s = spec([100.0, 200.0], [1000.0, 3000.0], precursor=200.0)
    assert fragment_depth(s) == pytest.approx(0.5, abs=1e-12)


def test_survival_yield_zero_when_precursor_absent():
    """Complete depletion is a real measurement, reported as exactly 0."""
    s = spec([50.0, 100.0], [10.0, 20.0], precursor=200.0)
    assert survival_yield(s) == 0.0


def test_fragment_depth_nan_when_no_fragments():
    """Precursor-only spectrum: phi is undefined. Must NOT be 0."""
    s = spec([200.0], [1000.0], precursor=200.0)
    assert math.isnan(fragment_depth(s))


# ---------------------------------------------------------------------------
# THE DECOMPOSITION -- master plan section 7.1. A failure here is a BLOCKER.
# ---------------------------------------------------------------------------
def test_decomposition_exact_identity_hand_case():
    """mu = SY*(mz_p/mz_prec) + (1-SY)*phi, with mz_p == mz_prec here.
    0.75*1 + 0.25*0.5 = 0.875 == mu. Checks out by hand.
    """
    s = spec([100.0, 200.0], [1000.0, 3000.0], precursor=200.0)
    assert decomposition_residual_exact(s) == pytest.approx(0.0, abs=1e-15)


@pytest.mark.parametrize("seed", range(25))
def test_decomposition_exact_identity_random(seed):
    """The identity must hold to floating point on arbitrary spectra."""
    rng = np.random.default_rng(seed)
    n = int(rng.integers(2, 40))
    prec = float(rng.uniform(150.0, 550.0))
    mz = np.sort(rng.uniform(50.0, prec, size=n))
    mz[-1] = prec  # ensure a precursor peak exists
    inten = rng.uniform(1.0, 1e7, size=n)
    assert decomposition_residual_exact(spec(mz, inten, prec)) < 1e-12


@pytest.mark.parametrize("seed", range(10))
def test_decomposition_holds_without_precursor_peak(seed):
    """When the precursor is absent SY=0 and mu must equal phi exactly."""
    rng = np.random.default_rng(1000 + seed)
    prec = float(rng.uniform(150.0, 550.0))
    mz = np.sort(rng.uniform(50.0, prec * 0.9, size=8))
    inten = rng.uniform(1.0, 1e6, size=8)
    s = spec(mz, inten, prec)
    assert survival_yield(s) == 0.0
    assert mu(s) == pytest.approx(fragment_depth(s), abs=1e-12)


# ---------------------------------------------------------------------------
# Degenerate input -- must return NaN, never a fabricated number
# ---------------------------------------------------------------------------
def test_zero_intensity_spectrum_is_nan_not_zero():
    s = spec([100.0, 200.0], [0.0, 0.0], precursor=200.0)
    assert math.isnan(mu(s))
    assert math.isnan(spectral_entropy(s))
    assert math.isnan(survival_yield(s))
    assert math.isnan(base_peak_fraction(s))


def test_empty_spectrum_is_nan_not_zero():
    s = spec([], [], precursor=200.0)
    assert math.isnan(mu(s))
    assert math.isnan(spectral_entropy(s))
    assert peak_count(s) == 0


def test_missing_precursor_mz_is_nan():
    """No declared precursor -> mu is undefined, not 1.0."""
    s = spec([100.0, 200.0], [1.0, 1.0], precursor=None)
    assert math.isnan(mu(s))


def test_negative_intensity_rejected():
    with pytest.raises(ValueError):
        spec([100.0], [-1.0], precursor=100.0)
