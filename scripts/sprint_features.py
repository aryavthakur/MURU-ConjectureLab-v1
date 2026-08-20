"""FINAL ACCURACY SPRINT — candidate-side feature cache.

Implements FEATURE GROUPS 1-3 of MURU_FINAL_ACCURACY_SPRINT_FREEZE.md exactly.
No truth field is an input to anything here.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                              # noqa: E402
import sympy as sp                                              # noqa: E402
from scipy.optimize import least_squares                        # noqa: E402
from scipy.stats import spearmanr                               # noqa: E402

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "src"))
sys.path.insert(0, str(WT / "scripts"))
OUT = WT / "artifacts" / "sprint"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = WT / "artifacts" / "accopt" / "candidate_cache.json"

# ---- frozen constants of the refit procedure (see freeze doc 2.1) ----------
MAX_FREE_CONSTANTS = 10
MAX_NFEV_PER_PARAM = 200
LS_TOL = 1e-10
INVALID_PENALTY_SD = 3.0
MIN_STRATUM_N = 15
N_TERTILE = 3

_G = {}


def _init():
    from muru.discovery import protocol
    from muru.synth.generators import load_dev_covariates
    _G["protocol"] = protocol
    _G["cov"] = load_dev_covariates()
    _G["variables"] = list(protocol.FEATURES)


# --------------------------------------------------------------- refit ----
def free_constants(expr: sp.Expr) -> list[sp.Float]:
    """Distinct Float atoms that never appear as a Pow exponent."""
    structural = set()
    for p in expr.atoms(sp.Pow):
        for f in p.exp.atoms(sp.Float):
            structural.add(f)
        if isinstance(p.exp, sp.Float):
            structural.add(p.exp)
    vals = sorted({f for f in expr.atoms(sp.Float) if f not in structural},
                  key=lambda f: (float(f), str(f)))
    return vals


def parameterize(expr: sp.Expr):
    consts = free_constants(expr)
    if not consts:
        return None, [], "no_free_constants"
    if len(consts) > MAX_FREE_CONSTANTS:
        return None, [], "too_many_free_constants"
    syms = [sp.Symbol(f"__p{i}") for i in range(len(consts))]
    pexpr = expr.xreplace({c: s for c, s in zip(consts, syms)})
    return pexpr, [float(c) for c in consts], "ok"


def _make_fn(pexpr, syms, psyms):
    return sp.lambdify(list(syms) + list(psyms), pexpr, modules=["numpy"])


def eval_protected(fn, X, theta):
    from muru.discovery import grammar
    with np.errstate(all="ignore"):
        try:
            out = fn(*[X[:, i] for i in range(X.shape[1])], *theta)
        except Exception:
            return np.zeros(len(X)), np.zeros(len(X), dtype=bool)
    out = np.asarray(out, float)
    if out.ndim == 0:
        out = np.full(len(X), float(out))
    return out, grammar.finite_mask(out)


def weighted_r2(y, pred, w, mask):
    if mask.sum() < 3:
        return float("-inf")
    yy, pp, ww = y[mask], pred[mask], w[mask]
    mean = np.average(yy, weights=ww)
    ssr = float(np.sum(ww * (yy - pp) ** 2))
    sst = float(np.sum(ww * (yy - mean) ** 2))
    if sst <= 0:
        return float("-inf")
    return 1.0 - ssr / sst


def weighted_rmse(y, pred, w, mask):
    if mask.sum() < 1:
        return float("nan")
    yy, pp, ww = y[mask], pred[mask], w[mask]
    return float(np.sqrt(np.sum(ww * (yy - pp) ** 2) / np.sum(ww)))


def refit_candidate(expr, variables, Xtr, ytr, wtr):
    """Deterministic constant refit on TRAIN only. Returns dict."""
    from muru.discovery import grammar
    pexpr, theta0, reason = parameterize(expr)
    if pexpr is None:
        return {"refit_ok": False, "n_params": 0, "reason": reason,
                "status": None, "theta": None}
    syms = [sp.Symbol(v) for v in variables]
    psyms = [sp.Symbol(f"__p{i}") for i in range(len(theta0))]
    try:
        fn = _make_fn(pexpr, syms, psyms)
    except Exception:
        return {"refit_ok": False, "n_params": len(theta0),
                "reason": "lambdify_failed", "status": None, "theta": None}
    sw = np.sqrt(wtr)
    ysd = float(np.std(ytr)) or 1.0
    pen = INVALID_PENALTY_SD * ysd

    def resid(theta):
        pred, ok = eval_protected(fn, Xtr, theta)
        r = np.where(ok, ytr - np.where(ok, pred, 0.0), pen)
        return sw * r

    try:
        sol = least_squares(resid, np.asarray(theta0, float), method="trf",
                            xtol=LS_TOL, ftol=LS_TOL, gtol=LS_TOL,
                            max_nfev=MAX_NFEV_PER_PARAM * len(theta0))
    except Exception:
        return {"refit_ok": False, "n_params": len(theta0),
                "reason": "optimizer_raised", "status": None, "theta": None}
    if not sol.success:
        return {"refit_ok": False, "n_params": len(theta0),
                "reason": "no_convergence", "status": int(sol.status),
                "theta": None}
    return {"refit_ok": True, "n_params": len(theta0), "reason": "ok",
            "status": int(sol.status), "theta": [float(x) for x in sol.x],
            "_fn": fn}


# ------------------------------------------------------- stratum metrics --
def stratum_stats(y, pred, w, ok, Xva, variables, eff_support):
    """Tertile strata on precursor_mz and on each effective-support descriptor."""
    strat_vars = ["precursor_mz"] + [v for v in eff_support
                                     if v != "precursor_mz" and v in variables]
    r2s, rmses, worst_norm = [], [], []
    n_used = 0
    for v in strat_vars:
        j = variables.index(v)
        x = Xva[:, j]
        q = np.percentile(x, [100.0 / N_TERTILE, 200.0 / N_TERTILE])
        lab = np.digitize(x, q)
        for t in range(N_TERTILE):
            m = (lab == t) & ok
            if m.sum() < MIN_STRATUM_N:
                continue
            n_used += 1
            r2s.append(weighted_r2(y, pred, w, m))
            rm = weighted_rmse(y, pred, w, m)
            rmses.append(rm)
            sd = float(np.std(y[m])) or 1.0
            worst_norm.append(rm / sd)
    if n_used < 2:
        return {"n_strata": n_used, "strat_median_r2": None,
                "strat_min_r2": None, "strat_sd_r2": None,
                "strat_median_rmse": None, "strat_worst_norm_rmse": None}
    r2s = [x for x in r2s if np.isfinite(x)]
    if len(r2s) < 2:
        return {"n_strata": n_used, "strat_median_r2": None,
                "strat_min_r2": None, "strat_sd_r2": None,
                "strat_median_rmse": float(np.median(rmses)),
                "strat_worst_norm_rmse": float(np.max(worst_norm))}
    return {"n_strata": n_used,
            "strat_median_r2": float(np.median(r2s)),
            "strat_min_r2": float(np.min(r2s)),
            "strat_sd_r2": float(np.std(r2s, ddof=1)) if len(r2s) > 1 else 0.0,
            "strat_median_rmse": float(np.median(rmses)),
            "strat_worst_norm_rmse": float(np.max(worst_norm))}


def residual_stats(y, pred, w, ok, Xva, variables, eff_support):
    e = (y - pred)[ok]
    if e.size < 10:
        return {"resid_max_abs_spearman": None, "resid_med_abs_spearman": None,
                "resid_interaction_spearman": None}
    rhos = {}
    for j, v in enumerate(variables):
        x = Xva[ok, j]
        if np.all(x == x[0]):
            rhos[v] = 0.0
            continue
        r = spearmanr(e, x).statistic
        rhos[v] = float(abs(r)) if np.isfinite(r) else 0.0
    vals = [rhos[v] for v in variables]
    inter = None
    cand = [v for v in eff_support if v != "precursor_mz" and v in variables]
    if cand:
        dstar = max(cand, key=lambda v: (rhos[v], v))
        z = Xva[ok, variables.index("precursor_mz")] * Xva[ok, variables.index(dstar)]
        if not np.all(z == z[0]):
            r = spearmanr(e, z).statistic
            inter = float(abs(r)) if np.isfinite(r) else 0.0
    return {"resid_max_abs_spearman": float(np.max(vals)),
            "resid_med_abs_spearman": float(np.median(vals)),
            "resid_interaction_spearman": inter}


# -------------------------------------------------------------- per world --
def process(args):
    spec_tuple, world_cache = args
    if not _G:
        _init()
    from muru.discovery import grammar, protocol
    from ov_20_search import build_search_world
    from muru.objval.plan2 import all_worlds2
    variables = _G["variables"]
    spec = _G["specs"][spec_tuple]
    w = build_search_world(spec, None if spec.family == "G1A" else _G["cov"])
    long, covw = w.search_inputs()
    wd = protocol.build_world_data(spec.world_id, long, covw)
    Xtr, ytr, wtr = wd.part("train")
    Xva, yva, wva = wd.part("valid")

    rows = []
    n_fail = 0
    for m in world_cache["members"]:
        row = {"seed": m["seed"], "band_index": m["band_index"]}
        try:
            expr = grammar.parse(m["expr"], variables)
        except Exception:
            row.update({"refit_ok": False, "refit_reason": "parse_failed",
                        "computational_failure": True})
            n_fail += 1
            rows.append(row)
            continue
        # ---- original prediction on VALID -----------------------------
        pred0, ok0 = grammar.evaluate(expr, variables, Xva)
        inv0 = float(1.0 - ok0.mean())
        r20 = weighted_r2(yva, pred0, wva, ok0) if inv0 <= grammar.MAX_INVALID_FRACTION else float("-inf")
        rm0 = weighted_rmse(yva, pred0, wva, ok0)
        # ---- refit ----------------------------------------------------
        rf = refit_candidate(expr, variables, Xtr, ytr, wtr)
        fn = rf.pop("_fn", None)
        r2r, rmr, predr, okr = None, None, None, None
        if rf["refit_ok"] and fn is not None:
            predr, okr = eval_protected(fn, Xva, rf["theta"])
            invr = float(1.0 - okr.mean())
            if invr > grammar.MAX_INVALID_FRACTION:
                rf["refit_ok"] = False
                rf["reason"] = "refit_invalid_fraction"
            else:
                r2r = weighted_r2(yva, predr, wva, okr)
                rmr = weighted_rmse(yva, predr, wva, okr)
                if not np.isfinite(r2r):
                    rf["refit_ok"] = False
                    rf["reason"] = "refit_nonfinite_r2"
                    r2r = None
        use_pred, use_ok = (predr, okr) if (rf["refit_ok"] and predr is not None) else (pred0, ok0)
        st = stratum_stats(yva, use_pred, wva, use_ok, Xva, variables, m["eff_support"])
        rs = residual_stats(yva, use_pred, wva, use_ok, Xva, variables, m["eff_support"])
        rs0 = residual_stats(yva, pred0, wva, ok0, Xva, variables, m["eff_support"])
        row.update({
            "orig_valid_r2": float(r20) if np.isfinite(r20) else None,
            "orig_valid_rmse": float(rm0) if np.isfinite(rm0) else None,
            "refit_valid_r2": r2r, "refit_valid_rmse": rmr,
            "refit_ok": bool(rf["refit_ok"]), "n_params": rf["n_params"],
            "refit_reason": rf["reason"], "optimizer_status": rf["status"],
            "computational_failure": False,
        })
        row.update(st)
        row.update(rs)
        row["orig_resid_max_abs_spearman"] = rs0["resid_max_abs_spearman"]
        rows.append(row)
    return {"world_id": spec.world_id, "block": world_cache["block"],
            "n_members": len(rows), "n_computational_failures": n_fail,
            "features": rows}


def _worker_init():
    _init()
    from muru.objval.plan2 import all_worlds2
    _G["specs"] = {s.world_id: s for s in all_worlds2()}


def main():
    import multiprocessing as mp
    cache = json.loads(CACHE.read_text())
    t0 = time.time()
    ctx = mp.get_context("fork")
    _init()
    from muru.objval.plan2 import all_worlds2
    _G["specs"] = {s.world_id: s for s in all_worlds2()}
    tasks = [(w["world_id"], w) for w in cache]
    out = []
    with ctx.Pool(7, initializer=_worker_init) as pool:
        for n, r in enumerate(pool.imap_unordered(process, tasks, chunksize=2), 1):
            out.append(r)
            if n % 25 == 0 or n == len(tasks):
                print(f"  [{n}/{len(tasks)}] {time.time()-t0:.0f}s", flush=True)
    out.sort(key=lambda r: r["world_id"])
    p = OUT / "candidate_feature_cache.json"
    p.write_text(json.dumps(out))
    nm = sum(r["n_members"] for r in out)
    nok = sum(1 for r in out for f in r["features"] if f.get("refit_ok"))
    nf = sum(r["n_computational_failures"] for r in out)
    print(f"wrote {p} — {len(out)} worlds, {nm} members, refit_ok {nok} "
          f"({100.0*nok/max(1,nm):.1f}%), comp-failures {nf}, "
          f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
