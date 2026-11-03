"""Exact v2 estimands and the cluster bootstrap (protocol sections 6 and 7).

Inputs are matrices over (compound, rung) with NaN for unobserved cells.
P1 pools cells; MRMSE averages per-compound RMSE; they are different
estimands and every comparison reports both. The bootstrap resamples whole
clusters and recomputes P1 of candidate and reference inside each replicate,
so an interval labelled P1_diff or P1_ratio is an interval for exactly that.
"""
from __future__ import annotations

import numpy as np

AF_RMSE = 0.20
AF_MAX = 0.30
S4_FACTOR = 2.0
BOOT_N = 2000
BOOT_SEED = 20260925


def errors(pred: np.ndarray, Y: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(Y), pred - Y, np.nan)


def p1(E: np.ndarray) -> float:
    return float(np.sqrt(np.nanmean(E ** 2)))


def compound_rmse(E: np.ndarray) -> np.ndarray:
    return np.sqrt(np.nanmean(E ** 2, axis=1))


def summary(pred: np.ndarray, Y: np.ndarray, pred_b0: np.ndarray | None = None) -> dict:
    E = errors(pred, Y)
    r = compound_rmse(E)
    k = max(1, int(np.ceil(0.05 * len(r))))
    out = {"P1": p1(E), "MRMSE": float(np.mean(r)), "MED": float(np.median(r)),
           "Q90": float(np.quantile(r, 0.90)), "Q95": float(np.quantile(r, 0.95)),
           "CVaR95": float(np.mean(np.sort(r)[-k:])),
           "AF": float(np.mean(r > AF_RMSE)), "AF_max": float(np.mean(np.nanmax(np.abs(E), axis=1) > AF_MAX)),
           "AF_union": float(np.mean((r > AF_RMSE) | (np.nanmax(np.abs(E), axis=1) > AF_MAX))),
           "P1_cw": float(np.sqrt(np.mean(np.nanmean(E ** 2, axis=1)))),
           "n_compounds": int(len(r)), "n_cells": int(np.isfinite(Y).sum())}
    if pred_b0 is not None:
        rb = compound_rmse(errors(pred_b0, Y))
        out["S4"] = float(np.mean(r > S4_FACTOR * rb))
    return out


def per_rung(pred: np.ndarray, Y: np.ndarray, energies) -> dict:
    E = errors(pred, Y)
    return {str(float(e)): float(np.sqrt(np.nanmean(E[:, j] ** 2))) for j, e in enumerate(energies)}


def cluster_bootstrap(pred_c: np.ndarray, pred_r: np.ndarray, Y: np.ndarray, clusters,
                      n: int = BOOT_N, seed: int = BOOT_SEED, level: float = 0.95) -> dict:
    """Whole-cluster resampling; P1 of both arms recomputed inside every replicate."""
    Ec, Er = errors(pred_c, Y), errors(pred_r, Y)
    sc, sr = np.nansum(Ec ** 2, axis=1), np.nansum(Er ** 2, axis=1)
    nc = np.isfinite(Y).sum(axis=1)
    rc, rr = compound_rmse(Ec), compound_rmse(Er)
    afc, afr = (rc > AF_RMSE).astype(float), (rr > AF_RMSE).astype(float)
    codes, uniq = _codes(clusters)
    G = len(uniq)
    # per-cluster sums make each replicate O(G)
    S_c, S_r, N = (np.bincount(codes, w, G) for w in (sc, sr, nc.astype(float)))
    R_c, R_r, M = np.bincount(codes, rc, G), np.bincount(codes, rr, G), np.bincount(codes, minlength=G).astype(float)
    A_c, A_r = np.bincount(codes, afc, G), np.bincount(codes, afr, G)
    rng = np.random.default_rng(seed)
    W = rng.multinomial(G, np.full(G, 1.0 / G), size=n).astype(float)   # cluster multiplicities
    p1c = np.sqrt(W @ S_c / (W @ N))
    p1r = np.sqrt(W @ S_r / (W @ N))
    mr = (W @ R_c - W @ R_r) / (W @ M)
    af = (W @ A_c - W @ A_r) / (W @ M)
    a = (1 - level) / 2 * 100

    def ci(x):
        return [float(v) for v in np.percentile(x, [a, 100 - a])]

    P1c, P1r = p1(Ec), p1(Er)
    return {"P1_cand": P1c, "P1_ref": P1r, "P1_diff": P1c - P1r, "P1_ratio": P1c / P1r,
            "P1_diff_ci": ci(p1c - p1r), "P1_ratio_ci": ci(p1c / p1r),
            "MRMSE_diff": float(rc.mean() - rr.mean()), "MRMSE_diff_ci": ci(mr),
            "AF_diff": float(afc.mean() - afr.mean()), "AF_diff_ci": ci(af),
            "wins_fraction": float(np.mean(rc < rr)), "n_clusters": int(G), "n_boot": n, "seed": seed,
            "unit": "whole clusters resampled with replacement; P1 recomputed per replicate"}


def compound_mean_rmse_bootstrap(dc: np.ndarray, clusters=None, n: int = BOOT_N, seed: int = BOOT_SEED,
                                 level: float = 0.95) -> list[float]:
    """The v1 procedure: bootstrap of the mean paired per-compound RMSE difference."""
    rng = np.random.default_rng(seed)
    a = (1 - level) / 2 * 100
    if clusters is None:
        idx = rng.integers(0, len(dc), size=(n, len(dc)))
        return [float(v) for v in np.percentile(dc[idx].mean(1), [a, 100 - a])]
    codes, uniq = _codes(clusters)
    G = len(uniq)
    D, M = np.bincount(codes, dc, G), np.bincount(codes, minlength=G).astype(float)
    W = rng.multinomial(G, np.full(G, 1.0 / G), size=n).astype(float)
    return [float(v) for v in np.percentile((W @ D) / (W @ M), [a, 100 - a])]


def _codes(clusters):
    uniq, codes = np.unique(np.asarray(clusters).astype(str), return_inverse=True)
    return codes, uniq
