"""E1: criteria (C0-C4) x practical-win rules (P0-P3), as pure functions of
the persisted per-compound record. MURU_V2_E1_PROTOCOL.md Sec 6-7.

Nothing here fits or refits anything: every criterion/rule is a re-scoring
of fields already produced by ``e1_fit.py`` and persisted to the compound
table by ``e1_run.py``. This is what makes the full C x P grid a "minutes"
operation (design Sec 3.9) regardless of how many worlds were generated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd

MIN_OBSERVED_ENERGIES = 5
N_TEST_COMPOUNDS_EXPECTED = 30
DEFAULT_MIN_EVALUABLE = 24

# --------------------------------------------------------------------------
# Criteria: C0-C4. Each takes the full compound table (one row per
# (world_id, detector, compound_id)) and returns a boolean Series
# ("unresolved" => BOUNDARY_LIMITED regardless of the win test). Vectorised
# (not `.apply(axis=1)`): the compound table is >1M rows and every criterion
# is scored on both CALIBRATE and CONFIRM across up to 15 parameter settings,
# so row-wise Python would dominate wall clock.
# --------------------------------------------------------------------------


def _gt(series: pd.Series, threshold: float) -> pd.Series:
    return series.fillna(-np.inf) > threshold


def c0_unresolved(df: pd.DataFrame) -> pd.Series:
    return df["m0_unresolved_c0_any"].fillna(False) | df["mk_unresolved_c0_any"].fillna(False)


def c1_unresolved(df: pd.DataFrame, delta: float) -> pd.Series:
    return _gt(df["m0_max_probe_gain_rel"], delta) | _gt(df["mk_max_probe_gain_rel"], delta)


def c2_unresolved(df: pd.DataFrame, delta: float) -> pd.Series:
    """threshold is `gain_abs > delta * sigma_hat_sq * n_fold`, pre-divided at
    aggregation time (e1_fit.aggregate_compound) into a ratio compared
    directly against delta."""
    return _gt(df["m0_max_c2_ratio"], delta) | _gt(df["mk_max_c2_ratio"], delta)


def c3_unresolved(df: pd.DataFrame, rho: float) -> pd.Series:
    return _gt(df["m0_max_profile_ratio"], rho) | _gt(df["mk_max_profile_ratio"], rho)


def c4_unresolved(df: pd.DataFrame) -> pd.Series:
    """Verdict invariance: unresolved iff the relaxed-refit verdict differs
    from the primal verdict. Precomputed at compound-aggregation time
    (needs mae_alt/mae_m0 under both fits)."""
    return df["c4_verdict_flip"].fillna(False)


CRITERIA: dict[str, dict] = {
    "C0": {"fn": c0_unresolved, "params": [{}], "n_free_params": 0},
    "C1": {"fn": c1_unresolved, "params": [{"delta": d} for d in (1e-3, 3e-3, 1e-2, 3e-2, 1e-1)], "n_free_params": 1},
    "C2": {"fn": c2_unresolved, "params": [{"delta": d} for d in (0.25, 0.5, 1, 2, 4)], "n_free_params": 1},
    "C3": {"fn": c3_unresolved, "params": [{"rho": r} for r in (0.05, 0.10, 0.25)], "n_free_params": 1},
    "C4": {"fn": c4_unresolved, "params": [{}], "n_free_params": 0},
}


def criterion_instances() -> list[tuple[str, dict]]:
    out = []
    for cid, spec in CRITERIA.items():
        for params in spec["params"]:
            out.append((cid, params))
    return out


def apply_criterion(df: pd.DataFrame, cid: str, params: dict) -> pd.Series:
    return CRITERIA[cid]["fn"](df, **params)


# --------------------------------------------------------------------------
# Practical-win rules: P0-P3. Each takes (mae_m0, mae_alt, evaluable_count,
# wins, median_rel_reduction) case-level aggregates and returns `fired`.
# --------------------------------------------------------------------------


def is_win(mae_m0: float, mae_alt: float, ratio: float) -> bool:
    if mae_m0 is None or mae_alt is None or not (math.isfinite(mae_m0) and math.isfinite(mae_alt)):
        return False
    if mae_m0 == 0.0:
        return False
    return mae_alt <= ratio * mae_m0


def directional_null_tail(wins: int, evaluable: int) -> float:
    if evaluable < 0 or wins < 0:
        raise ValueError("counts must be non-negative")
    if wins > evaluable:
        return 0.0
    from math import comb
    return sum(comb(evaluable, k) for k in range(wins, evaluable + 1)) / float(2 ** evaluable)


@dataclass(frozen=True)
class CaseCompoundStats:
    """Case-level statistics needed by every win rule, at a fixed ratio 0.90
    (P0/P2/P3's own win test) plus the raw (mae_m0, mae_alt) pairs for P1's
    ratio sweep."""

    evaluable: int
    wins_r90: int
    median_rel_reduction: float | None
    pairs: tuple[tuple[float, float], ...]  # (mae_m0, mae_alt) for evaluable compounds


def p0_fired(stats: CaseCompoundStats) -> bool:
    return stats.evaluable >= DEFAULT_MIN_EVALUABLE and stats.wins_r90 >= 20


def p1_fired(stats: CaseCompoundStats, ratio: float, w: int) -> bool:
    if stats.evaluable < DEFAULT_MIN_EVALUABLE:
        return False
    wins = sum(1 for m0, mk in stats.pairs if is_win(m0, mk, ratio))
    return wins >= w


def p2_fired(stats: CaseCompoundStats, q: float) -> bool:
    if stats.evaluable < DEFAULT_MIN_EVALUABLE:
        return False
    return directional_null_tail(stats.wins_r90, stats.evaluable) <= q


def p3_fired(stats: CaseCompoundStats, m: float, f: float) -> bool:
    if stats.evaluable < DEFAULT_MIN_EVALUABLE:
        return False
    if stats.median_rel_reduction is None or stats.median_rel_reduction < m:
        return False
    frac = stats.wins_r90 / stats.evaluable if stats.evaluable else 0.0
    return frac >= f


RULES: dict[str, dict] = {
    "P0": {"fn": p0_fired, "params": [{}], "n_free_params": 3},
    "P1": {
        "fn": p1_fired,
        "params": [{"ratio": r, "w": w} for r, w in product((0.80, 0.90, 0.95, 0.98), (15, 18, 20, 24))],
        "n_free_params": 2,
    },
    "P2": {"fn": p2_fired, "params": [{"q": q} for q in (0.05, 0.01, 0.001)], "n_free_params": 1},
    "P3": {
        "fn": p3_fired,
        "params": [{"m": m, "f": f} for m, f in product((0.05, 0.10), (0.5, 0.6, 0.67))],
        "n_free_params": 2,
    },
}


def rule_instances() -> list[tuple[str, dict]]:
    out = []
    for rid, spec in RULES.items():
        for params in spec["params"]:
            out.append((rid, params))
    return out


def apply_rule(stats: CaseCompoundStats, rid: str, params: dict) -> bool:
    return RULES[rid]["fn"](stats, **params)


def pair_free_params(cid: str, rid: str) -> int:
    return CRITERIA[cid]["n_free_params"] + RULES[rid]["n_free_params"]


def ladder_index(cid: str, params: dict, rid: str, rparams: dict) -> int:
    """Lower index = more conservative parameter choice, per the CRITERIA/RULES
    tables' own declared ordering (MURU_V2_E1_PROTOCOL.md Sec 6, tie-break 4)."""
    c_idx = CRITERIA[cid]["params"].index(params) if params in CRITERIA[cid]["params"] else 0
    r_idx = RULES[rid]["params"].index(rparams) if rparams in RULES[rid]["params"] else 0
    return c_idx + r_idx
