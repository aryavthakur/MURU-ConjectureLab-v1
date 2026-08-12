"""Empirical null calibration and the K6 false-positive arithmetic.

Genetic programming always returns something, so a raw symbolic-regression
score means nothing on its own. The threshold a candidate must clear is built
empirically, at its own complexity, from worlds where no valid structural
conjecture exists.

The statistic is deliberately the one the real protocol reports:
**the maximum over all 30 seeds of the best validation R² attainable at
complexity <= c**. Taking the max over seeds is what makes the threshold
multiplicity-aware — it prices in the fact that the protocol runs the search 30
times and keeps the best.

Calibration worlds and the G4 worlds used to measure the false-positive rate
are disjoint, so the rate is not measured against a threshold fitted to it.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

NULL_VERSION = "p3-nulls-1.0.0"
NULL_QUANTILE = 95.0        # master plan 13.6
MAX_COMPLEXITY = 20

# The four null constructions of master plan 13.6. Calibration worlds cycle
# through them, so every construction contributes to the per-complexity
# distribution rather than each getting its own thin sample.
NULL_CONSTRUCTIONS = (
    "target_permuted_across_compounds",
    "target_permuted_across_energy_within_compound",
    "descriptors_permuted_across_compounds",
    "gaussian_targets_with_observed_variance",
)


def threshold_table(curves: list[np.ndarray],
                    quantile: float = NULL_QUANTILE) -> dict:
    """Per-complexity null thresholds from the calibration worlds.

    `curves[i][c]` is world i's max-over-seeds best validation R² at
    complexity <= c.
    """
    if not curves:
        raise ValueError("no calibration curves supplied")
    M = np.vstack(curves)
    M = np.where(np.isfinite(M), M, -np.inf)
    thr = np.array([
        np.percentile(M[:, c][np.isfinite(M[:, c])], quantile)
        if np.isfinite(M[:, c]).any() else -np.inf
        for c in range(M.shape[1])])
    # A threshold must not fall as complexity rises: a larger hypothesis space
    # cannot make chance fitting harder.
    thr = np.maximum.accumulate(thr)
    return {
        "null_version": NULL_VERSION,
        "quantile": quantile,
        "n_worlds": int(M.shape[0]),
        "max_complexity": int(M.shape[1] - 1),
        "threshold_by_complexity": [float(x) for x in thr],
        "median_by_complexity": [
            float(np.median(M[:, c][np.isfinite(M[:, c])]))
            if np.isfinite(M[:, c]).any() else float("-inf")
            for c in range(M.shape[1])],
        "statistic": ("max over seeds of best validation R^2 at complexity <= c; "
                      "the max over seeds is what prices in search multiplicity"),
        "constructions": list(NULL_CONSTRUCTIONS),
    }


def false_positive_rate(n_accepted: int, n_valid: int, alpha: float = 0.05) -> dict:
    """Exact numerator and denominator with a Clopper-Pearson interval.

    Never `p = 0`: with a finite number of simulations the smallest resolvable
    rate is bounded below by the interval, not by the point estimate.
    """
    if n_valid <= 0:
        raise ValueError("no valid null replicates")
    lo, hi = stats.binomtest(n_accepted, n_valid).proportion_ci(
        confidence_level=1 - alpha, method="exact")
    return {
        "n_accepted": int(n_accepted),
        "n_valid_replicates": int(n_valid),
        "rate": n_accepted / n_valid,
        "ci_method": "Clopper-Pearson exact",
        "ci": [float(lo), float(hi)],
        "confidence_level": 1 - alpha,
        "note": ("a point estimate of 0/N does not license the claim that the "
                 "population rate is zero; the interval is the claim"),
    }


K6_MAX_RATE = 0.05


def adjudicate_k6(fp: dict) -> dict:
    """K6 is a hard Phase 3 gate: false-positive rate <= 5% under G4."""
    fires = fp["rate"] > K6_MAX_RATE
    return {
        "gate": "K6",
        "criterion": (f"G4 null false-positive rate <= {K6_MAX_RATE:.0%} "
                      "(nominal point criterion)"),
        "observed_rate": fp["rate"],
        "n_accepted": fp["n_accepted"],
        "n_valid_replicates": fp["n_valid_replicates"],
        "ci": fp["ci"],
        "fires": bool(fires),
        "verdict": "K6 FIRES" if fires else "K6 does not fire",
        "uncertainty_note": (
            "the point criterion is adjudicated on the observed rate; the "
            "interval is reported so the population rate is not overstated in "
            "either direction"),
    }
