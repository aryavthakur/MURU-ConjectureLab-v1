"""Type 2 family equivalence.

"Same family" is not allowed to be a vague escape hatch, so it is defined here
as a conjunction of checkable conditions, every one of which is invariant to
multiplying a candidate by a positive constant.

Two candidates belong to the same Type 2 empirical equation family when:

1. both carry a usable positive scale over the evaluation domain,
2. they have the SAME effective variable support — neither may carry an
   additional variable that materially moves the prediction,
3. every shared effect has the same sign,
4. every shared scaling exponent agrees within `EXPONENT_TOL`,
5. they agree on monotonicity in each supported variable,
6. they predict within `FAMILY_REL_RMSE` of each other, up to positive scale,
   on a dense independently generated lattice over the descriptor domain.

Condition 6 is deliberately looser than the Phase 3 FUNCTIONAL-equivalence
tolerance (0.02) and far looser than its SYMBOLIC one (1e-6). That is the whole
point of the Type 2 claim class: two algebraically distinct expressions can make
the same empirical structural claim. Exact form is scored separately and never
folded into this predicate.

This module reads candidates. It never reads a planted law.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from muru.discovery.equivalence import numeric_relation
from muru.objval import signature as sig_mod

EQUIV_VERSION = "ov-equiv-1.0.0"

# The master plan's own §18.3 tolerance on a recovered scaling exponent. It is
# used here as the family-merge tolerance because the plan already declares it
# to be the resolution at which an exponent claim is meaningful. It is not a
# number invented from Phase 3's failure.
EXPONENT_TOL = 0.15

# Predictive agreement required inside one family, on the dense lattice, after
# the optimal positive rescaling.
FAMILY_REL_RMSE = 0.10
FAMILY_MIN_R = 0.99

# Phase 3's frozen tolerances, reused UNCHANGED so that exact-form recovery
# remains measured on the same scale Phase 3 measured it on.
EXACT_REL_RMSE = 1e-6
FUNC_REL_RMSE = 0.02
FUNC_MIN_R = 0.999


def same_family(sa: dict, sb: dict, va: np.ndarray, vb: np.ndarray,
                ok: np.ndarray, exponent_tol: float = EXPONENT_TOL) -> dict:
    """Full Type 2 family predicate between two candidates.

    `sa`/`sb` are signatures from `objval.signature.signature`; `va`/`vb` are
    their evaluations on the shared dense lattice with validity mask `ok`.
    """
    reasons: list[str] = []
    if not (sa["usable"] and sb["usable"]):
        reasons.append("candidate is not a usable positive scale over the domain")

    # Support and scaling are compared at BLOCK level (see
    # `objval.signature.MASS_BLOCK`). Two expressions that put the same scaling
    # on two near-collinear size proxies make one empirical claim, and this
    # corpus cannot say which proxy carries it. Variable-level support is still
    # recorded on both signatures and reported.
    supp_a = set(sa["effective_support_blocks"])
    supp_b = set(sb["effective_support_blocks"])
    if supp_a != supp_b:
        reasons.append(f"effective support differs: {sorted(supp_a)} vs {sorted(supp_b)}")

    for v in sorted(supp_a & supp_b):
        if sa["block_signs"].get(v, 0) != sb["block_signs"].get(v, 0):
            reasons.append(f"sign of {v} differs")
        ea, eb = sa["block_exponents"].get(v), sb["block_exponents"].get(v)
        if ea is not None and eb is not None and np.isfinite(ea) and np.isfinite(eb):
            if abs(ea - eb) > exponent_tol:
                reasons.append(f"exponent in {v} differs by {abs(ea - eb):.3f}")
        if sa["block_monotone"].get(v) != sb["block_monotone"].get(v):
            reasons.append(f"monotonicity in {v} differs")

    num = numeric_relation(va, vb, ok)
    if not (np.isfinite(num["r"]) and num["r"] >= FAMILY_MIN_R
            and num["rel_rmse"] <= FAMILY_REL_RMSE):
        reasons.append(f"predictions disagree: r={num['r']:.4f}, "
                       f"rel_rmse={num['rel_rmse']:.4f}")

    return {"same_family": not reasons, "reasons": reasons, "numeric": num}


def functional_class(va: np.ndarray, vb: np.ndarray, ok: np.ndarray) -> dict:
    """Phase 3's functional/symbolic equivalence, unchanged.

    Used ONLY to report how many distinct algebraic forms sit inside one Type 2
    family — that is, whether the exact form is identified — never to decide
    family membership.
    """
    num = numeric_relation(va, vb, ok)
    exact = bool(np.isfinite(num["rel_rmse"]) and num["rel_rmse"] < EXACT_REL_RMSE)
    functional = bool(exact or (np.isfinite(num["r"]) and num["r"] > FUNC_MIN_R
                                and num["rel_rmse"] < FUNC_REL_RMSE))
    return {"exact_equivalent": exact, "functionally_equivalent": functional,
            "numeric": num}


def cluster_families(sigs: list[dict], vals: list[np.ndarray],
                     oks: list[np.ndarray],
                     exponent_tol: float = EXPONENT_TOL) -> list[list[int]]:
    """Greedy single-representative clustering into Type 2 families.

    Deterministic in the input order, which the caller fixes (seed, then
    complexity, then expression string), so the clustering is reproducible.
    """
    clusters: list[list[int]] = []
    reps: list[int] = []
    for i in range(len(sigs)):
        placed = False
        for ci, rep in enumerate(reps):
            ok = oks[i] & oks[rep]
            if same_family(sigs[i], sigs[rep], vals[i], vals[rep], ok,
                           exponent_tol)["same_family"]:
                clusters[ci].append(i)
                placed = True
                break
        if not placed:
            clusters.append([i])
            reps.append(i)
    return clusters


def cluster_functional(vals: list[np.ndarray], oks: list[np.ndarray]
                       ) -> list[list[int]]:
    """Phase 3 functional-equivalence clustering, used for identifiability."""
    clusters: list[list[int]] = []
    reps: list[int] = []
    for i in range(len(vals)):
        placed = False
        for ci, rep in enumerate(reps):
            ok = oks[i] & oks[rep]
            if functional_class(vals[i], vals[rep], ok)["functionally_equivalent"]:
                clusters[ci].append(i)
                placed = True
                break
        if not placed:
            clusters.append([i])
            reps.append(i)
    return clusters


def signature_of(expr: sp.Expr, variables: list[str], Z: np.ndarray) -> dict:
    return sig_mod.signature(expr, variables, Z)
