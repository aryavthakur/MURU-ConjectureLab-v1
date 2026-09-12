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
from scipy.interpolate import PchipInterpolator
from scipy.optimize import differential_evolution
from scipy.stats import spearmanr

from muru.wur_bridge_constants import (
    ALIGNMENT_A_BOUNDS, ALIGNMENT_B_BOUNDS, ALIGNMENT_MAXITER,
    ALIGNMENT_POLISH, ALIGNMENT_TOL, LADDER_ENERGIES, MEDIAN_ABS_DELTA_MAX,
    MIN_PAIRS_FOR_CORRELATION, MIN_PASSING_ENERGIES, OFFSET_MAX, SEED,
    SPEARMAN_MIN,
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


def alignment_branch_applies(stats: list[dict]) -> bool:
    """Whether the base rule failed *only* through a consistent offset.

    Every condition is read off the raw pre-alignment statistics, before any
    map is fitted. All four must hold: the base rule failed; the median
    signed delta has the same sign at every energy; its magnitude is within
    OFFSET_MAX everywhere; and the correlation is at or above SPEARMAN_MIN
    everywhere. Anything else is NO_POOL and no map is fitted at all.
    """
    if rule_passes(stats):
        return False
    signed = [s["median_signed_delta"] for s in stats]
    rhos = [s["spearman_rho"] for s in stats]
    if any(v is None for v in signed) or any(r is None for r in rhos):
        return False
    if not (all(v > 0 for v in signed) or all(v < 0 for v in signed)):
        return False
    if any(abs(v) > OFFSET_MAX for v in signed):
        return False
    return all(r >= SPEARMAN_MIN for r in rhos)


def interpolate_ladder(energies: np.ndarray, values: np.ndarray,
                       targets: np.ndarray) -> np.ndarray:
    """Read a measured ladder at arbitrary energies, by PCHIP.

    Shape-preserving piecewise cubic Hermite interpolation, knots at the
    measured energies exactly. There is no knot selection and nothing here
    is fitted: this is a deterministic readout rule for a curve that has
    already been measured, which is why it can sit alongside the fitted
    affine map without the two being the same kind of object.

    Targets outside the measured range are CLAMPED to the end knots. The
    interpolator never extrapolates.
    """
    order = np.argsort(energies)
    x, y = np.asarray(energies)[order], np.asarray(values)[order]
    interpolator = PchipInterpolator(x, y, extrapolate=False)
    clamped = np.clip(np.asarray(targets, dtype=float), x[0], x[-1])
    return interpolator(clamped)


def apply_energy_map(wur_mu: pd.DataFrame, a: float, b: float,
                     population_b: list[str] | None = None
                     ) -> tuple[pd.DataFrame, int]:
    """Re-read every WUR ladder at T(E) = a + b*E, for E on the ladder.

    Returns the re-read table, keyed by the LCSB energy E it is to be
    compared at, and the number of (compound, energy) cells whose mapped
    energy fell outside the ladder and was clamped.

    When `population_b` is given, `wur_mu` is filtered to those connectivity
    keys before the loop, so the returned table and the clamped-cell count
    are both over that restricted population rather than the whole WUR
    table. Existing two-argument callers keep working unchanged.
    """
    if population_b is not None:
        wur_mu = wur_mu[wur_mu["connectivity_key"].isin(set(population_b))]
    targets = a + b * np.asarray(LADDER_ENERGIES, dtype=float)
    n_clamped = 0
    rows = []
    for key, grp in wur_mu.groupby("connectivity_key", sort=True):
        grp = grp.sort_values("ce_numeric")
        energies = grp["ce_numeric"].to_numpy()
        if tuple(energies) != tuple(float(e) for e in LADDER_ENERGIES):
            raise ValueError(
                f"{key}: WUR ladder is {list(energies)}, not the six rungs "
                f"{list(LADDER_ENERGIES)}. Section 5.4 relies on a complete "
                f"ladder; an incomplete one would be silently filled by the "
                f"end clamp.")
        values = interpolate_ladder(energies, grp["mu"].to_numpy(), targets)
        n_clamped += int(np.sum((targets < energies[0]) | (targets > energies[-1])))
        rows += [{"connectivity_key": key, "ce_numeric": float(e), "mu": float(v)}
                 for e, v in zip(LADDER_ENERGIES, values)]
    return pd.DataFrame(rows, columns=["connectivity_key", "ce_numeric", "mu"]), n_clamped


def _alignment_objective(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
                         population_b: list[str], a: float, b: float) -> float:
    """Sum over the six energies of |per-energy median signed delta|.

    This targets exactly the failure the branch exists for, a consistent
    offset, rather than overall scatter, which no energy map can fix.
    """
    mapped, _ = apply_energy_map(wur_mu, a, b, population_b)
    total = 0.0
    for stat in per_energy_statistics(mapped, lcsb_mu, population_b):
        if stat["median_signed_delta"] is None:
            return float("inf")
        total += abs(stat["median_signed_delta"])
    return total


def fit_energy_map(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
                   population_b: list[str]) -> dict:
    """The single monotone affine energy map T(E) = a + b*E, b > 0.

    Fitted on population B alone, which is already exposed on both sides, by
    differential evolution at the frozen seed inside the frozen box. Two
    parameters, one fit, no restarts. Deterministic.
    """
    result = differential_evolution(
        lambda p: _alignment_objective(wur_mu, lcsb_mu, population_b, p[0], p[1]),
        bounds=[ALIGNMENT_A_BOUNDS, ALIGNMENT_B_BOUNDS],
        seed=SEED, tol=ALIGNMENT_TOL, maxiter=ALIGNMENT_MAXITER,
        polish=ALIGNMENT_POLISH,
    )
    a, b = float(result.x[0]), float(result.x[1])
    return {
        "form": "T(E) = a + b*E, applied to the LCSB nominal energy to give "
                "the WUR nominal energy at which WUR is read",
        "a": a,
        "b": b,
        "objective": float(result.fun),
        "objective_definition": "sum over the six ladder energies of the "
                                "absolute per-energy median signed delta",
        "interpolation": "PCHIP on each compound's own six-point WUR ladder, "
                         "knots at the ladder rungs, clamped at the ends, "
                         "never extrapolated",
        "optimizer": "scipy.optimize.differential_evolution",
        "seed": SEED,
        "polish": ALIGNMENT_POLISH,
        "bounds": {"a": list(ALIGNMENT_A_BOUNDS), "b": list(ALIGNMENT_B_BOUNDS)},
        "converged": bool(result.success),
    }
