"""Stage 1: the cross-instrument bridge gate.

Does the same compound produce the same fragmentation trajectory on the
IQ-X as on the Q Exactive at matching NCE labels? If not, pooling the WUR
and LCSB corpora is invalid and every later result must be reported per
corpus.

Pure logic. No file IO, no artifact writing, no data-directory knowledge.
Every threshold comes from `wur_bridge_constants`, which is frozen in
MURU_WUR_REAL_DATA_PREREGISTRATION.md.
"""
from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from muru.wur_bridge_constants import (
    LADDER_ENERGIES, MEDIAN_ABS_DELTA_MAX, MIN_PAIRS_FOR_CORRELATION,
    MIN_PASSING_ENERGIES, SPEARMAN_MIN,
)


def build_population_b(wur_dev_keys: Iterable[str],
                       lcsb_dev_keys: Iterable[str],
                       wur_sealed_keys: Iterable[str],
                       lcsb_sealed_keys: Iterable[str]) -> list[str]:
    """Compounds measured on both instruments and exposed on both sides.

    Constructed operationally as an intersection of realized key sets, never
    as arithmetic on expected counts. Anything sealed on either side is
    removed, even though D3 should already keep the LCSB seal out of
    WUR-DEV: the subtraction is cheap and its being a no-op is worth
    demonstrating rather than assuming.
    """
    b = set(wur_dev_keys) & set(lcsb_dev_keys)
    b -= set(wur_sealed_keys)
    b -= set(lcsb_sealed_keys)
    return sorted(b)


def _paired(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
            population_b: list[str], energy: float) -> pd.DataFrame:
    keys = set(population_b)
    w = wur_mu[(wur_mu["ce_numeric"] == energy)
               & wur_mu["connectivity_key"].isin(keys)]
    l = lcsb_mu[(lcsb_mu["ce_numeric"] == energy)
                & lcsb_mu["connectivity_key"].isin(keys)]
    return w[["connectivity_key", "mu"]].merge(
        l[["connectivity_key", "mu"]], on="connectivity_key",
        suffixes=("_wur", "_lcsb"), how="inner",
    ).sort_values("connectivity_key")


def per_energy_statistics(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
                          population_b: list[str]) -> list[dict]:
    """The gate statistics at each ladder rung.

    delta_i = mu_WUR,i - mu_LCSB,i over population B compounds carrying a
    value on both sides at that energy. An energy passes when the median
    absolute delta is at most MEDIAN_ABS_DELTA_MAX and the Spearman rank
    correlation is at least SPEARMAN_MIN. An energy with fewer than three
    pairs has no defined correlation and cannot pass.
    """
    stats = []
    for energy in LADDER_ENERGIES:
        pairs = _paired(wur_mu, lcsb_mu, population_b, energy)
        n = len(pairs)
        if n == 0:
            stats.append({
                "ce_numeric": float(energy), "n": 0,
                "median_signed_delta": None, "median_abs_delta": None,
                "spearman_rho": None, "passes": False,
            })
            continue
        delta = pairs["mu_wur"].to_numpy() - pairs["mu_lcsb"].to_numpy()
        if n >= MIN_PAIRS_FOR_CORRELATION:
            rho = float(spearmanr(pairs["mu_wur"].to_numpy(),
                                  pairs["mu_lcsb"].to_numpy()).statistic)
            rho = None if np.isnan(rho) else rho
        else:
            rho = None
        median_abs = float(np.median(np.abs(delta)))
        stats.append({
            "ce_numeric": float(energy),
            "n": int(n),
            "median_signed_delta": float(np.median(delta)),
            "median_abs_delta": median_abs,
            "spearman_rho": rho,
            "passes": bool(rho is not None
                           and median_abs <= MEDIAN_ABS_DELTA_MAX
                           and rho >= SPEARMAN_MIN),
        })
    return stats


def rule_passes(stats: list[dict]) -> bool:
    """The frozen rule: both conditions on at least 5 of the 6 energies."""
    return sum(1 for s in stats if s["passes"]) >= MIN_PASSING_ENERGIES
