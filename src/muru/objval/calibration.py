"""Null threshold table arithmetic.

Separated from the runner so the arithmetic is testable without a calibration
run on disk.

Statistic, unchanged from `PHASE3_PREREGISTRATION.md` §15: the maximum over the
30 seeds of the best validation R^2 attainable at complexity <= c. It prices in
search multiplicity, and within a world it upper-bounds whatever any selection
rule can report at complexity c — so the threshold stays conservative under the
Type 2 rule as well as the old one. What changed is the calibration SIZE, 100
worlds instead of 40 (`BACKLOG.md` I8).
"""
from __future__ import annotations

import numpy as np

CALIBRATION_VERSION = "ov-calibration-1.0.0"

NULL_QUANTILE = 0.95
N_BOOT_THRESHOLD = 2000
BOOT_SEED = 20260812
NEG_INF_FILL = -1e9


def threshold_table(curves: np.ndarray, quantile: float = NULL_QUANTILE,
                    n_boot: int = N_BOOT_THRESHOLD,
                    seed: int = BOOT_SEED) -> dict:
    """Per-complexity thresholds with a bootstrap interval on the quantile.

    `curves` is (n_worlds, max_complexity + 1). Non-finite entries mean the
    search produced nothing usable at that complexity in that world and are
    floored rather than dropped, so a world never silently leaves the sample.

    Thresholds are made non-decreasing in complexity: a larger hypothesis space
    cannot make chance fitting harder, and a dip would be sampling noise
    presented as a real gate.
    """
    M = np.where(np.isfinite(curves), curves, NEG_INF_FILL)
    if M.ndim != 2 or M.shape[0] < 2:
        raise ValueError("need at least two calibration worlds")

    thr = np.maximum.accumulate(np.quantile(M, quantile, axis=0))
    med = np.median(M, axis=0)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, M.shape[0], (n_boot, M.shape[0]))
    boots = np.quantile(M[idx], quantile, axis=1)      # (n_boot, n_complexity)
    lo = np.percentile(boots, 2.5, axis=0)
    hi = np.percentile(boots, 97.5, axis=0)

    return {"calibration_version": CALIBRATION_VERSION,
            "n_calibration_worlds": int(M.shape[0]),
            "quantile": quantile, "n_bootstrap": n_boot,
            "threshold": [float(x) for x in thr],
            "threshold_ci_lo": [float(x) for x in lo],
            "threshold_ci_hi": [float(x) for x in hi],
            "median": [float(x) for x in med],
            "interval_width": [float(h - l) for l, h in zip(lo, hi)]}
