"""Truth-based recovery scoring, run ONLY after candidates are frozen.

Blind-truth discipline (`TYPE2_VALIDATION_PREREGISTRATION.md` §8): the symbolic
search and the Type 2 selection rule never see any of this. Selection completes,
its output is written to the checkpoint store, and only then does this module
open the planted law to score what was selected.

Four distinct things are measured and reported separately, so that a Type 2
success can never be mistaken for a Type 3 one:

| Quantity | Class | What it means |
|---|---|---|
| variable support recovery | Type 2 | the reported structure uses the right variables and only those |
| scaling-exponent recovery | Type 2 | the reported exponents match the planted ones within the master plan's ±0.15 |
| family recovery | Type 2 | the reported representative and the planted law are the same Type 2 family |
| exact-form recovery | **Type 3 diagnostic** | the reported representative is functionally equivalent to the complete planted law |

`search_found_the_law` is reported alongside the last of these, because Phase 3
showed that "the search cannot find it" and "the rule does not report it" are
different failures and must not be conflated.

This module imports `truth2`. It must never be imported by the discovery side.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from muru.objval import equiv, signature
from muru.objval.truth2 import PlantedLaw2, phi, planted2

RECOVERY_VERSION = "ov-recovery-1.0.0"

# Master plan §18.3. The same number is the family-merge tolerance in
# `objval.equiv`; it is the plan's declared resolution for an exponent claim.
EXPONENT_TOL = 0.15

# Shape-family recovery: the fitted shared `Phi` against the planted one, after
# the single positive rescaling of the energy axis that the collapse model
# leaves free. 0.05 relative RMSE over the observed u-range is roughly twice the
# moderate-regime noise SD expressed as a fraction of Phi's range, so a fit
# inside it is indistinguishable from the planted shape at the noise present.
SHAPE_REL_RMSE_TOL = 0.05
_LOG_A_GRID = np.linspace(-2.0, 2.0, 401)


def planted_evaluator(family: str, params: dict, variables: list[str],
                      latent_name: str | None = None):
    """An evaluator for the planted `g` on a dimensionless descriptor matrix.

    Returns `None` when the planted law depends on a variable the search is
    never given (`G5`'s latent driver, `GRT`'s lipophilicity) or when no
    descriptor law exists at all (`G4`, `GC`, `NULL`). In those worlds there is
    nothing to recover and the recovery fields are recorded as not applicable.
    """
    law: PlantedLaw2 = planted2(family)
    support = law.support_of(params)
    if not support or any(s.startswith("__") for s in support):
        return None, tuple(support)
    if family == "G2":
        return None, tuple(support)   # no compact universal law exists

    idx = {v: i for i, v in enumerate(variables)}
    if family == "G1A":
        def ev(Z):
            z = {"v0": Z[:, idx["precursor_mz"]],
                 "v1": Z[:, idx["heteroatom_fraction"]]}
            g = law.g_of(z, params)
            return g, np.isfinite(g)
        return ev, ("precursor_mz", "heteroatom_fraction")

    def ev(Z):
        z = {v: Z[:, i] for v, i in idx.items()}
        with np.errstate(all="ignore"):
            g = np.asarray(law.g_of(z, params), float)
        return g, np.isfinite(g)
    return ev, tuple(support)


def planted_signature(family: str, params: dict, variables: list[str],
                      Z: np.ndarray) -> dict | None:
    ev, support = planted_evaluator(family, params, variables)
    if ev is None:
        return None
    return signature.signature_from(ev, variables, Z, support)


def shape_recovery(phi_u: np.ndarray, phi_v: np.ndarray, params: dict) -> dict:
    """Does the fitted shared `Phi` reproduce the planted shape family?

    The collapse model identifies `(g, Phi)` only up to `(a*g, Phi(u/a))`, so a
    single positive `a` is fitted before comparing. Nothing else is free.
    """
    u = np.exp(np.asarray(phi_u, float))
    v = np.asarray(phi_v, float)
    ok = np.isfinite(u) & np.isfinite(v) & (u > 0)
    if ok.sum() < 10:
        return {"applicable": False, "reason": "fitted shape has too few knots"}
    u, v = u[ok], v[ok]
    scale = max(float(v.max() - v.min()), 1e-9)

    best = (np.inf, np.nan)
    for la in _LOG_A_GRID:
        pv = phi(u / np.exp(la), params["mu_inf"], params["phi_p"])
        rel = float(np.sqrt(np.mean((v - pv) ** 2)) / scale)
        if rel < best[0]:
            best = (rel, float(np.exp(la)))
    monotone = bool(np.all(np.diff(v) <= 1e-9))
    return {"applicable": True, "rel_rmse": best[0], "best_scale": best[1],
            "tolerance": SHAPE_REL_RMSE_TOL, "fitted_monotone_decreasing": monotone,
            "shape_family_recovered": bool(best[0] <= SHAPE_REL_RMSE_TOL and monotone),
            "planted_mu_inf": params["mu_inf"], "planted_p": params["phi_p"]}


def score_world(family: str, params: dict, variables: list[str], Z: np.ndarray,
                reported: dict | None, rep_expr: sp.Expr | None,
                band_exprs: list[sp.Expr], phi_u=None, phi_v=None) -> dict:
    """Everything truth-based, for one world, after selection is frozen."""
    out: dict = {"family": family, "recovery_version": RECOVERY_VERSION}

    if phi_u is not None and phi_v is not None and family not in ("G4", "GC", "NULL"):
        out["shape"] = shape_recovery(phi_u, phi_v, params)
    else:
        out["shape"] = {"applicable": False,
                        "reason": "no planted collapse shape in this family"}

    psig = planted_signature(family, params, variables, Z)
    if psig is None:
        out["planted_signature"] = None
        out["support_recovery"] = {"applicable": False}
        out["exponent_recovery"] = {"applicable": False}
        out["family_recovery"] = {"applicable": False}
        out["exact_form"] = {"applicable": False}
        return out

    ev, _ = planted_evaluator(family, params, variables)
    pv, pok = ev(Z)
    out["planted_signature"] = {k: psig[k] for k in
                                ("effective_support", "exponents", "signs",
                                 "monotone", "usable", "effective_support_blocks",
                                 "block_exponents", "block_signs")}

    # ---- Type 3 diagnostic: did the SEARCH find the exact law anywhere? -----
    found, best_rel = False, np.inf
    for e in band_exprs:
        v, ok = signature._eval(e, variables, Z)
        fc = equiv.functional_class(pv, v, pok & ok)
        best_rel = min(best_rel, fc["numeric"]["rel_rmse"])
        if fc["functionally_equivalent"]:
            found = True
    out["exact_form"] = {"applicable": True,
                         "search_found_the_law": bool(found),
                         "best_rel_rmse_on_band": float(best_rel)}

    if reported is None or rep_expr is None:
        out["support_recovery"] = {"applicable": True, "recovered": False,
                                   "reason": "no reported family"}
        out["exponent_recovery"] = {"applicable": True, "recovered": False}
        out["family_recovery"] = {"applicable": True, "recovered": False}
        out["exact_form"]["system_reported_the_law"] = False
        return out

    rsig = signature.signature(rep_expr, variables, Z)
    rv, rok = signature._eval(rep_expr, variables, Z)
    ok = pok & rok

    # Support recovery is adjudicated at BLOCK level, and the variable-level
    # comparison is reported beside it so that proxy substitution inside the
    # mass block is visible and is never quietly counted as a recovery failure
    # or as a recovery success.
    pb, rb = set(psig["effective_support_blocks"]), set(rsig["effective_support_blocks"])
    ps, rs = set(psig["effective_support"]), set(rsig["effective_support"])
    out["support_recovery"] = {
        "applicable": True,
        "planted_blocks": sorted(pb), "reported_blocks": sorted(rb),
        "recovered": bool(pb == rb),
        "missing_blocks": sorted(pb - rb), "extra_blocks": sorted(rb - pb),
        "correct_blocks_present": bool(pb <= rb),
        "no_unsupported_blocks": bool(not (rb - pb)),
        "planted_variables": sorted(ps), "reported_variables": sorted(rs),
        "variable_level_exact_match": bool(ps == rs),
    }

    per_block, all_ok = {}, True
    for v in sorted(pb):
        pe = psig["block_exponents"].get(v)
        re_ = rsig["block_exponents"].get(v)
        d = (abs(pe - re_) if (pe is not None and re_ is not None
                               and np.isfinite(pe) and np.isfinite(re_))
             else float("nan"))
        within = bool(np.isfinite(d) and d <= EXPONENT_TOL)
        per_block[v] = {"planted": pe, "reported": re_, "abs_diff": d,
                        "within_tolerance": within}
        all_ok = all_ok and within
    out["exponent_recovery"] = {
        "applicable": True, "tolerance": EXPONENT_TOL, "per_block": per_block,
        "recovered": bool(all_ok and per_block),
        "mass_exponent_planted": signature.mass_exponent(psig),
        "mass_exponent_reported": signature.mass_exponent(rsig),
        "mass_exponent_within_tolerance": bool(
            np.isfinite(signature.mass_exponent(psig))
            and np.isfinite(signature.mass_exponent(rsig))
            and abs(signature.mass_exponent(psig)
                    - signature.mass_exponent(rsig)) <= EXPONENT_TOL),
    }

    fam = equiv.same_family(rsig, psig, rv, pv, ok)
    out["family_recovery"] = {"applicable": True, "recovered": fam["same_family"],
                              "reasons": fam["reasons"],
                              "numeric": fam["numeric"]}

    fc = equiv.functional_class(pv, rv, ok)
    out["exact_form"].update({
        "system_reported_the_law": bool(fc["functionally_equivalent"]),
        "symbolically_equivalent": bool(fc["exact_equivalent"]),
        "rel_rmse_reported_vs_planted": float(fc["numeric"]["rel_rmse"]),
        "n_distinct_algebraic_forms_in_family":
            reported["n_distinct_algebraic_forms"],
        "algebraic_form_identified": reported["algebraic_form_identified"],
    })
    return out
