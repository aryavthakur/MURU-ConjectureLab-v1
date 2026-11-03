"""Phase 1 fragmentation functionals.

Every functional T maps a spectrum S = {(mz_k, I_k)} to a scalar. Each carries
its mathematical definition, its valid-input requirements, its behaviour on
degenerate input, and its preprocessing dependencies.

Convention for degenerate input: return float('nan'), never a silent 0.0 and
never an exception. A NaN propagates visibly into the census and gets counted;
a 0.0 would be indistinguishable from a real measurement of zero. The one thing
this module must never do is manufacture a number.

--------------------------------------------------------------------------
THE DECOMPOSITION, AND A CORRECTION TO THE MASTER PLAN
--------------------------------------------------------------------------
Master plan section 7.1 states the identity

    mu_i(E) = SY_i(E) * 1 + (1 - SY_i(E)) * phi_i(E)                    (PLAN)

and section 11 of the session brief calls a failure of it a BLOCKER.

The identity as written is FALSE IN GENERAL, and it is false for this corpus,
for a reason that has nothing to do with implementation error. Writing p for
the index of the precursor peak:

    mu  = (sum_k I_k mz_k) / (sum_k I_k) / mz_prec
        = [I_p mz_p + sum_{k!=p} I_k mz_k] / (sum_k I_k) / mz_prec
        = SY * (mz_p / mz_prec) + (1 - SY) * phi                        (EXACT)

so (PLAN) requires mz_p == mz_prec exactly: the OBSERVED precursor peak m/z
must equal the DECLARED MS$FOCUSED_ION: PRECURSOR_M/Z. In these records it does
not. RMassBank recalibrates fragment and precursor masses, so e.g. record
MSBNK-LCSB-LU003301 declares PRECURSOR_M/Z 207.1492 while its peak list carries
the precursor at 207.1491. The ratio mz_p/mz_prec differs from 1 at the ppm
level, so (PLAN) fails by roughly

    SY * |mz_p - mz_prec| / mz_prec  ~  1e-6 * SY

which is far above floating-point tolerance (~1e-16) and far below anything of
scientific consequence.

MURU therefore:
  * implements mu directly from its definition (first moment of the normalized
    mass distribution) -- it does NOT compute mu from the decomposition;
  * implements (EXACT) as the identity under test;
  * reports max |mu - [SY + (1-SY) phi]| across the corpus as the
    PLAN-form residual, so the ppm-scale gap is measured and stated rather
    than hidden by a loose tolerance.

The BLOCKER condition is treated as: (EXACT) must hold to floating point. It
does. (PLAN) holds to ppm. Both numbers appear in ENDPOINT_SCREEN.md.
"""

from __future__ import annotations

import numpy as np

from .spectra import DEFAULT_PRECURSOR_PPM, Spectrum

NAN = float("nan")


def _valid(s: Spectrum) -> bool:
    """A spectrum supports intensity-weighted functionals iff it has >=1 peak
    and strictly positive total intensity."""
    return s.n_peaks > 0 and s.intensity.sum() > 0


# ---------------------------------------------------------------------------
# Primary functionals
# ---------------------------------------------------------------------------
def mu(s: Spectrum) -> float:
    """Intensity-weighted normalized spectrum mass.

        mu = [ sum_k I_k * mz_k / sum_k I_k ] / mz_precursor

    The first moment of the normalized mass distribution, expressed as a
    fraction of the precursor m/z. Dimensionless, cross-molecule comparable.
    mu = 1 means all intensity sits at the precursor; mu -> 0 means intensity
    has migrated to low-mass fragments.

    Valid input: >=1 peak, sum I > 0, declared precursor m/z > 0.
    Degenerate: NaN if any of those fail.
    Preprocessing dependence: LOW. Intensity-weighted, so dropping low-intensity
    peaks barely moves it. Sensitive to precursor inclusion by construction.
    """
    if not _valid(s) or not s.precursor_mz or s.precursor_mz <= 0:
        return NAN
    return float((s.intensity * s.mz).sum() / s.intensity.sum() / s.precursor_mz)


def survival_yield(s: Spectrum, ppm: float = DEFAULT_PRECURSOR_PPM) -> float:
    """Fraction of total intensity remaining in the precursor ion.

        SY = I_precursor / sum_k I_k

    Valid input: >=1 peak, sum I > 0, declared precursor m/z.
    Degenerate: NaN if those fail. Returns exactly 0.0 when the precursor is
    absent from the peak list -- a real measurement of complete depletion,
    subject to the detection floor (see the censoring census, T1.10).
    Preprocessing dependence: MODERATE, entirely through precursor matching.
    """
    if not _valid(s) or s.precursor_mz is None:
        return NAN
    i = s.precursor_index(ppm)
    if i is None:
        return 0.0
    return float(s.intensity[i] / s.intensity.sum())


def fragment_depth(s: Spectrum, ppm: float = DEFAULT_PRECURSOR_PPM) -> float:
    """Intensity-weighted mean fragment mass, normalized by precursor m/z.

        phi = [ sum_{k != p} I_k mz_k / sum_{k != p} I_k ] / mz_precursor

    Measures how far fragmentation has progressed among the fragments, ignoring
    how much precursor survives. Low phi means deep secondary fragmentation.

    Valid input: >=1 NON-precursor peak with positive intensity.
    Degenerate: NaN when the spectrum is precursor-only (no fragments) -- phi is
    genuinely undefined there, and returning 0 would fabricate deep
    fragmentation from a spectrum showing none.
    Preprocessing dependence: LOW.
    """
    if not _valid(s) or not s.precursor_mz or s.precursor_mz <= 0:
        return NAN
    i = s.precursor_index(ppm)
    if i is None:
        mzf, inf = s.mz, s.intensity
    else:
        keep = np.ones(s.n_peaks, dtype=bool)
        keep[i] = False
        mzf, inf = s.mz[keep], s.intensity[keep]
    if mzf.size == 0 or inf.sum() <= 0:
        return NAN
    return float((inf * mzf).sum() / inf.sum() / s.precursor_mz)


def precursor_mass_ratio(s: Spectrum, ppm: float = DEFAULT_PRECURSOR_PPM) -> float:
    """mz_p / mz_precursor -- the factor by which the PLAN identity misses 1.

    Exactly 1.0 by convention when the precursor peak is absent (SY = 0, so the
    term it multiplies vanishes and any value would do).
    """
    if s.precursor_mz is None or s.precursor_mz <= 0:
        return NAN
    i = s.precursor_index(ppm)
    if i is None:
        return 1.0
    return float(s.mz[i] / s.precursor_mz)


def decomposition_residual_exact(s: Spectrum, ppm: float = DEFAULT_PRECURSOR_PPM) -> float:
    """|mu - [SY*(mz_p/mz_prec) + (1-SY)*phi]|. Must be ~1e-16. BLOCKER if not."""
    m, sy, ph, r = (mu(s), survival_yield(s, ppm),
                    fragment_depth(s, ppm), precursor_mass_ratio(s, ppm))
    if np.isnan(m) or np.isnan(sy) or np.isnan(r):
        return NAN
    if np.isnan(ph):
        # Precursor-only spectrum: the (1-SY) term is empty, SY == 1.
        return abs(m - sy * r)
    return abs(m - (sy * r + (1.0 - sy) * ph))


def decomposition_residual_plan(s: Spectrum, ppm: float = DEFAULT_PRECURSOR_PPM) -> float:
    """|mu - [SY + (1-SY)*phi]| -- the master plan's stated form.

    Expected to be ppm-scale, not floating point. Measured, not assumed.
    """
    m, sy, ph = mu(s), survival_yield(s, ppm), fragment_depth(s, ppm)
    if np.isnan(m) or np.isnan(sy):
        return NAN
    if np.isnan(ph):
        return abs(m - sy)
    return abs(m - (sy + (1.0 - sy) * ph))


# ---------------------------------------------------------------------------
# Secondary / diagnostic functionals
# ---------------------------------------------------------------------------
def spectral_entropy(s: Spectrum) -> float:
    """Shannon entropy of the normalized intensity distribution.

        S = - sum_k p_k ln p_k,   p_k = I_k / sum_j I_j

    Natural log, per Li et al. 2021 eq. 1. Zero-intensity peaks contribute
    0 (limit p ln p -> 0 as p -> 0).

    Valid input: >=1 peak, sum I > 0.
    Degenerate: NaN if invalid. Exactly 0.0 for a single peak, which is correct
    (no uncertainty), not a failure.
    Preprocessing dependence: HIGH. Bounded above by ln(n), and n here is set by
    RMassBank's formula-annotation success rather than by the detector.
    """
    if not _valid(s):
        return NAN
    p = s.intensity / s.intensity.sum()
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def normalized_entropy(s: Spectrum) -> float:
    """S / ln(n) -- entropy as a fraction of its maximum at that peak count.

    Strips the peak-count dependence, leaving distribution shape only.
    Degenerate: NaN for n < 2 (ln(1) = 0; the ratio is undefined, and 0/0 is
    not "perfectly uniform").
    DIAGNOSTIC ONLY per master plan section 7.1.
    """
    if not _valid(s) or s.n_peaks < 2:
        return NAN
    e = spectral_entropy(s)
    return float(e / np.log(s.n_peaks)) if not np.isnan(e) else NAN


def peak_count(s: Spectrum) -> int:
    """Number of peaks. COVARIATE ONLY -- mass-confounded, preprocessing-driven."""
    return s.n_peaks


def total_ion_current(s: Spectrum) -> float:
    """Sum of intensities. Confounder variable for the T1.9 screen."""
    return s.tic if s.n_peaks else NAN


def base_peak_fraction(s: Spectrum) -> float:
    """I_max / sum I. Concentration of intensity in the single largest peak."""
    if not _valid(s):
        return NAN
    return float(s.intensity.max() / s.intensity.sum())


# ---------------------------------------------------------------------------
# Registry consumed by the endpoint screen (T1.9)
# ---------------------------------------------------------------------------
ENDPOINTS = {
    "mu": mu,
    "survival_yield": survival_yield,
    "fragment_depth": fragment_depth,
    "spectral_entropy": spectral_entropy,
    "normalized_entropy": normalized_entropy,
    "base_peak_fraction": base_peak_fraction,
}

COVARIATES = {
    "peak_count": peak_count,
    "tic": total_ion_current,
}
