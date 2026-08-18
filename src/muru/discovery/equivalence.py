"""Candidate equivalence and stability.

Exact string equality is not a recovery criterion: two expressions can be
mathematically identical and syntactically different, and a reparameterization
is the same object. The hierarchy below is frozen by
`PHASE3_PREREGISTRATION.md`:

1. symbolic simplification where it is safe and terminates,
2. algebraic equivalence on the valid domain, **up to a positive multiplicative
   constant** (the collapse model identifies `g` only up to scale),
3. dense noise-free numerical evaluation on an INDEPENDENTLY generated holdout
   domain (Latin hypercube), never on the training points,
4. variable-support comparison,
5. complexity comparison.

A candidate counts as recovery if it is numerically equivalent to the planted
law within tolerance even when simplification cannot prove identity. A
high-complexity interpolant with tiny training error does not.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from muru.discovery import grammar

EQUIV_VERSION = "p3-equiv-1.0.0"

# Frozen tolerances.
EXACT_REL_RMSE = 1e-6      # numerically indistinguishable => symbolic-equivalent
FUNC_REL_RMSE = 0.02       # functionally equivalent
FUNC_MIN_R = 0.999         # master plan 13.5 fingerprint-clustering threshold
N_LHC_ADJUDICATE = 10_000  # master plan 13.5
N_LHC_CLUSTER = 2_000      # within-world dedup, cheaper
SIMPLIFY_TIMEOUT_TERMS = 400


def latin_hypercube(bounds: dict[str, tuple[float, float]], variables: list[str],
                    n: int, seed: int) -> np.ndarray:
    """Independently generated evaluation domain, never the training points."""
    rng = np.random.default_rng(seed)
    out = np.empty((n, len(variables)))
    for k, v in enumerate(variables):
        lo, hi = bounds[v]
        cut = (np.arange(n) + rng.random(n)) / n
        out[:, k] = lo + (hi - lo) * rng.permutation(cut)
    return out


def domain_bounds(X: np.ndarray, variables: list[str]) -> dict[str, tuple[float, float]]:
    return {v: (float(X[:, i].min()), float(X[:, i].max()))
            for i, v in enumerate(variables)}


def fingerprint(expr: sp.Expr, variables: list[str], D: np.ndarray
                ) -> tuple[np.ndarray, np.ndarray]:
    return grammar.evaluate(expr, variables, D)


def numeric_relation(va: np.ndarray, vb: np.ndarray, ok: np.ndarray) -> dict:
    """Compare two candidate evaluations up to a positive multiplicative scale."""
    if ok.sum() < 50:
        return {"r": float("nan"), "scale": float("nan"),
                "rel_rmse": float("inf"), "n": int(ok.sum())}
    a, b = va[ok], vb[ok]
    if np.allclose(a, a[0]) or np.allclose(b, b[0]):
        same = float(np.sqrt(np.mean((a - b) ** 2)) /
                     max(np.sqrt(np.mean(a ** 2)), 1e-15))
        return {"r": 1.0 if same < EXACT_REL_RMSE else 0.0, "scale": 1.0,
                "rel_rmse": same, "n": int(ok.sum())}
    denom = float(np.dot(b, b))
    c = float(np.dot(a, b) / denom) if denom > 1e-30 else float("nan")
    rel = float(np.sqrt(np.mean((a - c * b) ** 2)) /
                max(np.sqrt(np.mean(a ** 2)), 1e-15))
    r = float(np.corrcoef(a, b)[0, 1])
    return {"r": r, "scale": c, "rel_rmse": rel, "n": int(ok.sum())}


def algebraically_equivalent(a: sp.Expr, b: sp.Expr) -> bool | None:
    """True/False if simplification decides it, None if it does not terminate
    usefully. Equivalence is judged up to a positive multiplicative constant."""
    try:
        if sp.count_ops(a) + sp.count_ops(b) > SIMPLIFY_TIMEOUT_TERMS:
            return None
        # Positivity is asserted here only, as a proof aid: every descriptor in
        # the dimensionless frame is non-negative, and it lets powsimp combine
        # radicals. It is not applied at parse time, where it would change the
        # tree the complexity metric counts.
        sub = {s: sp.Symbol(s.name, positive=True)
               for s in (a.free_symbols | b.free_symbols)}
        a, b = a.subs(sub), b.subs(sub)
        ratio = sp.simplify(sp.cancel(sp.powsimp(a / b, force=True)))
        if ratio.is_number:
            return bool(ratio.is_positive is not False and ratio != 0)
        diff = sp.simplify(sp.cancel(a - b))
        if diff == 0:
            return True
        return None
    except Exception:
        return None


def equivalence(a: sp.Expr, b: sp.Expr, variables: list[str], D: np.ndarray
                ) -> dict:
    """Full hierarchy. Returns the verdict and every input to it."""
    va, oka = fingerprint(a, variables, D)
    vb, okb = fingerprint(b, variables, D)
    ok = oka & okb
    num = numeric_relation(va, vb, ok)
    alg = algebraically_equivalent(a, b)

    exact = bool(alg is True or num["rel_rmse"] < EXACT_REL_RMSE)
    functional = bool(exact or (num["r"] > FUNC_MIN_R
                                and num["rel_rmse"] < FUNC_REL_RMSE))
    sa = grammar.variable_support(a, variables)
    sb = grammar.variable_support(b, variables)
    return {
        "algebraic": alg,
        "numeric": num,
        "exact_equivalent": exact,
        "functionally_equivalent": functional,
        "support_a": list(sa), "support_b": list(sb),
        "support_match": set(sa) == set(sb),
        "complexity_a": grammar.complexity(a),
        "complexity_b": grammar.complexity(b),
        "valid_fraction": float(ok.mean()),
    }


# --------------------------------------------------------------------------
# stability across seeds
# --------------------------------------------------------------------------
def cluster_by_fingerprint(cands: list, variables: list[str], D: np.ndarray
                           ) -> list[list[int]]:
    """Group candidates whose predictions agree up to positive scale.

    Stability is judged on expression FAMILIES, not identical strings
    (master plan 13.5).
    """
    vals, oks = [], []
    for c in cands:
        v, o = fingerprint(c.expr, variables, D)
        vals.append(v), oks.append(o)
    clusters: list[list[int]] = []
    reps: list[int] = []
    for i in range(len(cands)):
        placed = False
        for ci, rep in enumerate(reps):
            ok = oks[i] & oks[rep]
            n = numeric_relation(vals[i], vals[rep], ok)
            if n["r"] > FUNC_MIN_R and n["rel_rmse"] < FUNC_REL_RMSE:
                clusters[ci].append(i)
                placed = True
                break
        if not placed:
            clusters.append([i])
            reps.append(i)
    return clusters


def selection_frequency(per_seed_best: list, variables: list[str],
                        D: np.ndarray) -> dict:
    """How many of the seeds selected the same expression family?

    An expression recovered by 24 of 30 seeds is a different object from one
    recovered once (master plan 13.5).
    """
    if not per_seed_best:
        return {"n_seeds": 0, "top_count": 0, "fraction": 0.0,
                "n_families": 0, "top_index": None}
    clusters = cluster_by_fingerprint(per_seed_best, variables, D)
    sizes = [len(c) for c in clusters]
    k = int(np.argmax(sizes))
    return {
        "n_seeds": len(per_seed_best),
        "top_count": int(sizes[k]),
        "fraction": float(sizes[k] / len(per_seed_best)),
        "n_families": len(clusters),
        "top_index": int(clusters[k][0]),
        "cluster_sizes": sorted(sizes, reverse=True),
    }
