"""Endpoint screening and confounder analysis (T1.9, T1.8).

Statistics kept to the simplest valid tools: descriptive distributions, Spearman
rank correlation, and a compound-level (cluster) bootstrap. No modelling.

The cluster bootstrap resamples COMPOUNDS, not records. Resampling records would
understate uncertainty by roughly sqrt(6) because the six energies of one
compound are not independent observations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def monotone_flags(values: np.ndarray) -> tuple[bool, bool]:
    """(strictly monotone, weakly monotone) across an energy-ordered series.

    Both directions count: a decreasing endpoint (mu) and an increasing one
    (entropy) are equally "monotone in energy". NaN anywhere -> (False, False),
    because an incomplete trajectory cannot be assessed.
    """
    v = np.asarray(values, dtype=float)
    if v.size < 3 or np.any(np.isnan(v)):
        return False, False
    d = np.diff(v)
    strict = bool(np.all(d > 0) or np.all(d < 0))
    weak = bool(np.all(d >= 0) or np.all(d <= 0))
    return strict, weak


def trajectory_stats(df: pd.DataFrame, endpoint: str,
                     group_col: str = "group_key",
                     energy_col: str = "ce_numeric") -> pd.DataFrame:
    """Per-trajectory summary: monotonicity, range, endpoint values by energy."""
    out = []
    for key, g in df.groupby(group_col, sort=True):
        g = g.sort_values(energy_col)
        v = g[endpoint].to_numpy(dtype=float)
        strict, weak = monotone_flags(v)
        finite = v[np.isfinite(v)]
        out.append({
            "group_key": key,
            "n_energies": len(g),
            "n_finite": int(finite.size),
            "monotone_strict": strict,
            "monotone_weak": weak,
            "range": float(finite.max() - finite.min()) if finite.size >= 2 else np.nan,
            "first": float(v[0]) if v.size else np.nan,
            "last": float(v[-1]) if v.size else np.nan,
            "direction": (
                "decreasing" if weak and finite.size >= 2 and v[-1] < v[0]
                else "increasing" if weak and finite.size >= 2 and v[-1] > v[0]
                else "flat_or_nonmonotone"
            ),
        })
    return pd.DataFrame(out)


def between_compound_sd(df: pd.DataFrame, endpoint: str,
                        energy_col: str = "ce_numeric") -> float:
    """Pooled SD across compounds at fixed energy.

    Pooling within-energy SDs is the right comparator for a within-compound
    range: it answers "how much do molecules differ from each other at the same
    setting", not "how much does the endpoint move overall".
    """
    parts = [g[endpoint].dropna().to_numpy() for _, g in df.groupby(energy_col)]
    parts = [p for p in parts if p.size > 1]
    if not parts:
        return float("nan")
    num = sum(((p.size - 1) * p.var(ddof=1)) for p in parts)
    den = sum((p.size - 1) for p in parts)
    return float(np.sqrt(num / den)) if den else float("nan")


def spearman_by_energy(df: pd.DataFrame, endpoint: str, covariate: str,
                       energy_col: str = "ce_numeric") -> pd.DataFrame:
    """Spearman rho between an endpoint and a covariate, at each energy.

    Stratifying by energy is essential: pooling across energies would show a
    correlation driven entirely by both variables moving with energy.
    """
    rows = []
    for e, g in df.groupby(energy_col):
        s = g[[endpoint, covariate]].dropna()
        if len(s) < 10:
            rows.append({"energy": e, "n": len(s), "rho": np.nan, "p": np.nan})
            continue
        rho, p = stats.spearmanr(s[endpoint], s[covariate])
        rows.append({"energy": e, "n": len(s), "rho": float(rho), "p": float(p)})
    return pd.DataFrame(rows)


def cluster_bootstrap_ci(values_by_group: dict[str, float], n_boot: int = 2000,
                         statistic=np.median, alpha: float = 0.05,
                         seed: int = 20260811) -> tuple[float, float, float]:
    """Bootstrap CI for a statistic, resampling COMPOUNDS with replacement."""
    keys = list(values_by_group)
    vals = np.array([values_by_group[k] for k in keys], dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    boots = np.array([
        statistic(rng.choice(vals, size=vals.size, replace=True))
        for _ in range(n_boot)
    ])
    return (float(statistic(vals)),
            float(np.percentile(boots, 100 * alpha / 2)),
            float(np.percentile(boots, 100 * (1 - alpha / 2))))
