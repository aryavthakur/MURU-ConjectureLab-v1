"""The F1-F12 falsification ladder (master plan 16.1), automated.

A candidate is fed in and every rung emits a machine-readable pass/fail. A
candidate must survive the complete REQUIRED set to count as accepted. This is
a ladder, not a "validation score": each rung tests a distinct way the
candidate could be an artifact.

Where a master-plan rung is not evaluable on synthetic data, it is recorded
`not_applicable` with the reason, and it is never silently counted as a pass.
Every ambiguity was resolved here, in code, before any candidate performance was
observed.

This module reads data. It never reads a planted law.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import sympy as sp

from muru.discovery import grammar
from muru.discovery.estimate import fit_collapse
from muru.discovery.protocol import MASS_BLOCK, SCALE, WorldData

HARNESS_VERSION = "p3-falsify-1.0.0"

# Rungs that must PASS for acceptance. F3 and F11 are not evaluable on
# mode-agnostic synthetic data; F8 is a labelling test whose gate applies only
# to a claim of structure beyond mass; F12 is supporting evidence and never a
# gate (master plan 16.1).
REQUIRED = ("F1", "F2", "F4", "F5", "F6", "F7", "F9", "F10")
LABELLING = ("F8",)
NOT_APPLICABLE = ("F3", "F11")
SUPPORTING = ("F12",)

N_PERMUTATIONS_F10 = 20
INFLUENCE_DROP_FRACTION = 0.05
MIN_TEST_R2 = 0.0


# --------------------------------------------------------------------------
def affine_refit(expr: sp.Expr, variables: list[str], X: np.ndarray,
                 y: np.ndarray, w: np.ndarray) -> tuple[float, float, bool]:
    """Re-fit the candidate's overall scale and offset by weighted least
    squares on the TRAINING data only (master plan 13.4).

    The collapse target identifies `g` only up to a positive multiplicative
    constant, so an affine refit is exactly the freedom the science allows -- no
    more, and it is fitted on training data, never on the holdout.
    """
    f, ok = grammar.evaluate(expr, variables, X)
    if ok.sum() < 10:
        return 0.0, 0.0, False
    A = np.column_stack([np.ones(ok.sum()), f[ok]])
    sw = np.sqrt(w[ok])
    try:
        coef, *_ = np.linalg.lstsq(A * sw[:, None], y[ok] * sw, rcond=None)
    except np.linalg.LinAlgError:
        return 0.0, 0.0, False
    return float(coef[0]), float(coef[1]), True


def r2_after_refit(expr: sp.Expr, variables: list[str],
                   Xtr, ytr, wtr, Xte, yte, wte) -> float:
    a, b, ok = affine_refit(expr, variables, Xtr, ytr, wtr)
    if not ok:
        return -np.inf
    f, valid = grammar.evaluate(expr, variables, Xte)
    if valid.sum() < 5:
        return -np.inf
    pred = a + b * f
    yy, pp, ww = yte[valid], pred[valid], wte[valid]
    mean = np.average(yy, weights=ww)
    ss_tot = float(np.sum(ww * (yy - mean) ** 2))
    if ss_tot <= 0:
        return -np.inf
    return 1.0 - float(np.sum(ww * (yy - pp) ** 2)) / ss_tot


# --------------------------------------------------------------------------
def run_harness(wd: WorldData, expr: sp.Expr, complexity: int,
                support: tuple[str, ...], null_threshold: np.ndarray,
                stability: dict) -> dict:
    """Feed one candidate through F1-F12."""
    V = wd.variables
    thr = float(null_threshold[min(complexity, len(null_threshold) - 1)])
    Xtr, ytr, wtr = wd.part("train")
    Xva, yva, wva = wd.part("valid")
    Xte, yte, wte = wd.part("test")
    rungs: dict[str, dict] = {}

    # F1 reproducibility -----------------------------------------------------
    # The recorded artifact must reproduce: the stored expression re-evaluates
    # to identical predictions, and the world's data hash is reproducible by
    # construction (generator seed). Engine determinism under a fixed seed is
    # pinned separately by tests/test_p3_engine.py.
    p1, ok1 = grammar.evaluate(expr, V, Xte)
    p2, ok2 = grammar.evaluate(sp.sympify(sp.srepr(expr)), V, Xte)
    same = bool(np.array_equal(ok1, ok2) and
                np.allclose(p1[ok1], p2[ok2], rtol=0, atol=0))
    rungs["F1"] = {"name": "reproducibility", "pass": same,
                   "detail": "stored expression re-evaluates bit-identically"}

    # F2 preprocessing invariance -------------------------------------------
    # No 7.3 preprocessing grid exists for synthetic response, so the analogue
    # is invariance to a defensible change in the ESTIMATION pipeline: the
    # number of knots used for the shared shape Phi.
    # The knot count of the shared shape Phi, and the number of alternations,
    # are choices with no uniquely correct value. A conclusion that flips when
    # they change is a pipeline artifact, exactly as a conclusion that flips
    # when the intensity cutoff moves from 0.1% to 1% would be.
    settings = [(30, 2), (60, 3), (120, 4)]
    r2s = []
    for nk, na in settings:
        fit = fit_collapse(wd.long, n_alternations=na, n_knots=nk,
                           with_hmain=False)
        r2s.append(_refit_against(fit, wd, expr, V))
    f2_ok = all(np.isfinite(r) and r > thr for r in r2s)
    rungs["F2"] = {"name": "preprocessing invariance", "pass": bool(f2_ok),
                   "settings": [{"n_knots": nk, "n_alternations": na}
                                for nk, na in settings],
                   "r2_by_setting": [float(r) for r in r2s], "threshold": thr,
                   "r2_range": float(np.nanmax(r2s) - np.nanmin(r2s))
                   if np.isfinite(r2s).any() else float("nan"),
                   "detail": "estimation-pipeline invariance stands in for the "
                             "7.3 grid, which has no synthetic analogue"}

    # F4 compound holdout ----------------------------------------------------
    r2_test = r2_after_refit(expr, V, Xtr, ytr, wtr, Xte, yte, wte)
    rungs["F4"] = {"name": "compound holdout (S1)",
                   "pass": bool(np.isfinite(r2_test) and r2_test > MIN_TEST_R2),
                   "r2": float(r2_test)}

    # F5 scaffold holdout — the primary claim gate ---------------------------
    rungs["F5"] = {"name": "scaffold holdout (S2) — PRIMARY",
                   "pass": bool(np.isfinite(r2_test) and r2_test > thr),
                   "r2": float(r2_test), "threshold": thr,
                   "detail": "splits are scaffold-group-disjoint by construction"}

    # F6 chemical-dissimilarity holdout --------------------------------------
    r2_clust = _cluster_holdout(wd, expr, V)
    rungs["F6"] = {"name": "similarity-cluster holdout (S3)",
                   "pass": bool(np.isfinite(r2_clust) and r2_clust > thr),
                   "r2": float(r2_clust), "threshold": thr}

    # F7 influence robustness ------------------------------------------------
    r2_infl, r2_mix = _influence(wd, expr, V)
    f7 = bool(np.isfinite(r2_infl) and r2_infl > thr
              and (not np.isfinite(r2_mix) or r2_mix > thr))
    rungs["F7"] = {"name": "influence robustness", "pass": f7,
                   "r2_drop_top5pct": float(r2_infl),
                   "r2_leave_one_mix_out": float(r2_mix), "threshold": thr,
                   "detail": "a relationship carried by a handful of molecules "
                             "is not a relationship"}

    # F8 descriptor ablation — labelling, not rejection -----------------------
    abl = _ablations(wd, expr, V, support)
    rungs["F8"] = {"name": "descriptor ablation", "pass": True,
                   "labelling_only": True, **abl,
                   "detail": "master plan 16.1: if removing mass destroys the "
                             "result, the law IS a mass law and is reported so"}

    # F9 energy-subset stability ---------------------------------------------
    f9 = _energy_subsets(wd, expr, V, thr)
    rungs["F9"] = {"name": "energy-subset stability",
                   "pass": bool(all(v["pass"] for v in f9.values())),
                   "subsets": f9,
                   "detail": "a form that exists only on the full six-point "
                             "grid is describing the grid"}

    # F10 negative controls --------------------------------------------------
    f10 = _negative_controls(wd, expr, V, thr)
    rungs["F10"] = {"name": "negative controls", **f10,
                    "detail": "the candidate MUST fail on permuted data; "
                              "passing under permutation invalidates the pipeline"}

    # F12 extrapolation probe — supporting evidence only ----------------------
    rungs["F12"] = {"name": "extrapolation probe", "pass": None,
                    "supporting_only": True,
                    "r2_valid": float(r2_after_refit(expr, V, Xtr, ytr, wtr,
                                                     Xva, yva, wva)),
                    "detail": "six energy levels cannot support an "
                              "extrapolation gate; reported, never decisive"}

    # not evaluable ----------------------------------------------------------
    rungs["F3"] = {"name": "source-branch invariance", "pass": None,
                   "not_applicable": True,
                   "detail": "no independently reprocessed branch exists for a "
                             "synthetic response; the real raw branch covers 39 "
                             "compounds (7.1%) and licenses no corpus claim"}
    rungs["F11"] = {"name": "mode replication (S4)", "pass": None,
                    "not_applicable": True,
                    "detail": "the generators are mode-agnostic; Phase 2 found "
                              "K4B FAILS in negative mode, which remains binding"}

    required_pass = {k: bool(rungs[k]["pass"]) for k in REQUIRED}
    return {
        "harness_version": HARNESS_VERSION,
        "rungs": rungs,
        "required": list(REQUIRED),
        "required_results": required_pass,
        "passed": all(required_pass.values()),
        "failed_rungs": [k for k, v in required_pass.items() if not v],
        "mass_carried": abl["mass_block_destroys_result"],
        "structural_beyond_mass_supported": bool(
            abl["non_mass_ablation_destroys_result"]
            and not abl["mass_block_alone_reproduces"]),
    }


# --------------------------------------------------------------------------
def _refit_against(fit, wd: WorldData, expr: sp.Expr, V: list[str]) -> float:
    y = fit.g_hat
    order = {k: i for i, k in enumerate(fit.compounds)}
    idx = np.array([order[k] for k in wd.cov.group_key])
    y = y[idx]
    w = fit.weights[idx]
    tr, te = wd.split == "train", wd.split == "test"
    return r2_after_refit(expr, V, wd.X[tr], y[tr], w[tr],
                          wd.X[te], y[te], w[te])


def _cluster_holdout(wd: WorldData, expr: sp.Expr, V: list[str]) -> float:
    """Hold out whole similarity clusters instead of scaffold groups."""
    cl = wd.cov.cluster_group.to_numpy()
    uniq = np.unique(cl)
    rng = np.random.default_rng(11)
    hold = set(rng.permutation(uniq)[:max(1, len(uniq) // 5)])
    te = np.array([c in hold for c in cl])
    tr = ~te
    if te.sum() < 20 or tr.sum() < 50:
        return np.nan
    return r2_after_refit(expr, V, wd.X[tr], wd.y[tr], wd.w[tr],
                          wd.X[te], wd.y[te], wd.w[te])


def _influence(wd: WorldData, expr: sp.Expr, V: list[str]) -> tuple[float, float]:
    tr = wd.split == "train"
    te = wd.split == "test"
    a, b, ok = affine_refit(expr, V, wd.X[tr], wd.y[tr], wd.w[tr])
    if not ok:
        return np.nan, np.nan
    f, valid = grammar.evaluate(expr, V, wd.X)
    resid = np.where(valid, np.abs(wd.y - (a + b * f)), 0.0)
    thresh = np.quantile(resid[tr], 1 - INFLUENCE_DROP_FRACTION)
    keep = tr & (resid <= thresh)
    r_infl = r2_after_refit(expr, V, wd.X[keep], wd.y[keep], wd.w[keep],
                            wd.X[te], wd.y[te], wd.w[te])

    mixes = wd.cov["mix"].to_numpy()
    r_mix = np.nan
    if len(np.unique(mixes)) > 1:
        drop = pd.Series(mixes[tr]).value_counts().idxmax()
        keep2 = tr & (mixes != drop)
        if keep2.sum() > 50:
            r_mix = r2_after_refit(expr, V, wd.X[keep2], wd.y[keep2], wd.w[keep2],
                                   wd.X[te], wd.y[te], wd.w[te])
    return r_infl, r_mix


def _ablations(wd: WorldData, expr: sp.Expr, V: list[str],
               support: tuple[str, ...]) -> dict:
    """Replace a descriptor (or the whole mass block) by its training median and
    re-fit the candidate's affine constants. A large loss means the candidate
    genuinely depends on what was removed."""
    tr, te = wd.split == "train", wd.split == "test"
    base = r2_after_refit(expr, V, wd.X[tr], wd.y[tr], wd.w[tr],
                          wd.X[te], wd.y[te], wd.w[te])

    def ablate(names) -> float:
        Xa = wd.X.copy()
        for nm in names:
            if nm in V:
                j = V.index(nm)
                Xa[:, j] = np.median(wd.X[tr, j])
        return r2_after_refit(expr, V, Xa[tr], wd.y[tr], wd.w[tr],
                              Xa[te], wd.y[te], wd.w[te])

    per = {v: float(ablate([v])) for v in V}
    mass = float(ablate(MASS_BLOCK))
    non_mass = float(ablate([v for v in V if v not in MASS_BLOCK]))

    # a mass-and-energy-only comparator, the synthetic analogue of MASS FLEX
    mass_only_r2 = _mass_only_reference(wd)
    drop = 0.5 * max(base, 1e-9)
    return {
        "base_test_r2": float(base),
        "per_descriptor_r2": per,
        "mass_block_ablated_r2": mass,
        "non_mass_ablated_r2": non_mass,
        "mass_block_destroys_result": bool(mass < base - drop),
        "non_mass_ablation_destroys_result": bool(non_mass < base - drop),
        "mass_only_reference_r2": float(mass_only_r2),
        "mass_block_alone_reproduces": bool(mass_only_r2 >= base - 0.02),
    }


def _mass_only_reference(wd: WorldData) -> float:
    """Flexible predictor using the mass block alone — the Phase 2 MASS FLEX
    analogue. If it matches the candidate, the candidate is a mass law."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    V = wd.variables
    cols = [V.index(m) for m in MASS_BLOCK if m in V]
    tr, te = wd.split == "train", wd.split == "test"
    m = HistGradientBoostingRegressor(max_iter=150, max_depth=3,
                                      min_samples_leaf=20, random_state=0)
    m.fit(wd.X[np.ix_(tr, cols)], wd.y[tr], sample_weight=wd.w[tr])
    pred = m.predict(wd.X[np.ix_(te, cols)])
    yy, ww = wd.y[te], wd.w[te]
    mean = np.average(yy, weights=ww)
    ss_tot = float(np.sum(ww * (yy - mean) ** 2))
    if ss_tot <= 0:
        return -np.inf
    return 1.0 - float(np.sum(ww * (yy - pred) ** 2)) / ss_tot


def _energy_subsets(wd: WorldData, expr: sp.Expr, V: list[str],
                    thr: float) -> dict:
    """Re-estimate the collapse scale from energy subsets and ask whether the
    candidate still predicts it."""
    subsets = {"low_{15,30,45}": [15.0, 30.0, 45.0],
               "high_{45,60,75,90}": [45.0, 60.0, 75.0, 90.0],
               "odd_index_{15,45,75}": [15.0, 45.0, 75.0]}
    out = {}
    for name, keep in subsets.items():
        sub = wd.long[wd.long.ce_numeric.isin(keep)]
        try:
            fit = fit_collapse(sub, n_alternations=3, with_hmain=False)
        except Exception:
            out[name] = {"pass": False, "r2": float("nan"),
                         "note": "collapse fit failed on this subset"}
            continue
        order = {k: i for i, k in enumerate(fit.compounds)}
        idx = np.array([order[k] for k in wd.cov.group_key if k in order])
        mask = np.array([k in order for k in wd.cov.group_key])
        y, w = fit.g_hat[idx], fit.weights[idx]
        tr = mask & (wd.split == "train")
        te = mask & (wd.split == "test")
        ytr = y[(wd.split == "train")[mask]]
        wtr = w[(wd.split == "train")[mask]]
        yte = y[(wd.split == "test")[mask]]
        wte = w[(wd.split == "test")[mask]]
        r = r2_after_refit(expr, V, wd.X[tr], ytr, wtr, wd.X[te], yte, wte)
        out[name] = {"pass": bool(np.isfinite(r) and r > thr), "r2": float(r),
                     "threshold": thr}
    return out


def _negative_controls(wd: WorldData, expr: sp.Expr, V: list[str],
                       thr: float) -> dict:
    """The candidate must FAIL when the descriptor-response link is destroyed.

    Passing under permutation invalidates the pipeline, not the candidate
    (master plan 16.1 F10).
    """
    rng = np.random.default_rng(4242)
    tr, te = wd.split == "train", wd.split == "test"
    hits = 0
    r2s = []
    for _ in range(N_PERMUTATIONS_F10):
        perm = rng.permutation(len(wd.y))
        yp = wd.y[perm]
        r = r2_after_refit(expr, V, wd.X[tr], yp[tr], wd.w[tr],
                           wd.X[te], yp[te], wd.w[te])
        r2s.append(float(r) if np.isfinite(r) else -1e9)
        if np.isfinite(r) and r > thr:
            hits += 1
    frac = hits / N_PERMUTATIONS_F10
    return {"pass": bool(frac <= 0.05), "n_permutations": N_PERMUTATIONS_F10,
            "n_exceeding_threshold": hits, "fraction": frac,
            "threshold": thr, "median_permuted_r2": float(np.median(r2s))}
