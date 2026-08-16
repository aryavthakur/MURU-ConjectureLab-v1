"""INDEPENDENT re-derivation of a sample of E3 worlds.

This is the deepest check in the audit: for a stratified sample of worlds
covering every family/coefficient/noise/grid combination, regenerate the raw
world (covariates + g_hat) using the E3 branch's own generation code
(v2c_generator.py + the frozen rc5_estimate -- these are DATA GENERATION
code, not "the primary aggregation/analyzer" that the audit brief says not
to trust; aggregate_e3.py is the thing we do not import anywhere in this
audit), then INDEPENDENTLY REFIT all five candidate models with fresh code
written for this audit: a different scipy entry point (least_squares with
the Trust Region Reflective method and explicit bounds, rather than
oracle_models.py's bounds-free curve_fit/Levenberg-Marquardt), a
independently-typed BIC formula, and independently-typed R2. Compare the
selected model and BIC values against what run_e3.py / oracle_models.py
persisted for the same world_id.

This tests whether the *reported per-world fits themselves* (not just the
aggregation arithmetic already checked in independent_recompute.py) are
robust to a different, reasonable optimizer/parameterization choice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b/scripts/e3_identifiability")
sys.path.insert(0, "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/heldout-analysis-restoration/src")

import _bootstrap  # noqa: F401  (puts frozen src + e3 scripts dir on path; reused deliberately -- pure path plumbing, no science)
from v2c_generator import build_world  # E3's data-generation code, not the aggregator
from muru.paper_benchmark.rc5_estimate import fit_case_scalars  # the frozen estimator itself

WORLDS_PATH = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b/results/e3_identifiability/e3_worlds.jsonl")
OUT_DIR = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/results/audit_e3")

FAMILIES = ("mass_power", "mass_affine_descriptor", "mass_saturating_descriptor", "mass_interaction", "mass_exponential_descriptor")


# --- independently-written model functions (design doc section 3.3's closed forms, typed fresh) ---
def resid_mass(p, mass, y):
    a, b = p
    return a * mass ** b - y

def resid_affine(p, mass, d, y):
    a, b, c = p
    return a * mass ** b * (1 + c * d) - y

def resid_sat(p, mass, d, y):
    a, b, c = p
    return a * mass ** b * (1 + c * d / (1 + d)) - y

def resid_exp(p, mass, d, y):
    a, b, c = p
    return a * mass ** b * np.exp(c * d) - y

def resid_inter(p, mass, d, d2, y):
    a, b, c = p
    return a * mass ** b * (1 + c * d * d2) - y


def r2(y, pred):
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return float("nan") if ss_tot <= 0 else 1 - ss_res / ss_tot


def bic(n, rss, k):
    return n * np.log(max(rss / n, 1e-300)) + k * np.log(n)


def fit_independent(model_id, train, val, test):
    mass_t, d_t, d2_t, y_t = train["mass"], train["descriptor"], train["descriptor2"], train["g"]
    # Independent init: crude method-of-moments rather than oracle_models.py's log-log OLS.
    a0 = float(np.median(y_t) / np.median(mass_t) ** 0.5)
    b0 = 0.5
    c0 = 0.5  # deliberately different starting value from oracle_models.py's 0.3
    if model_id == "M_mass":
        p0 = [a0, b0]
        lb, ub = [1e-6, -5], [1e6, 5]
        res = least_squares(resid_mass, p0, args=(mass_t, y_t), method="trf", bounds=(lb, ub), max_nfev=20000)
        k = 2
        def predict(p, mass, d, d2): return p[0] * mass ** p[1]
    elif model_id == "M_affine":
        p0 = [a0, b0, c0]
        lb, ub = [1e-6, -5, -50], [1e6, 5, 50]
        res = least_squares(resid_affine, p0, args=(mass_t, d_t, y_t), method="trf", bounds=(lb, ub), max_nfev=20000)
        k = 3
        def predict(p, mass, d, d2): return p[0] * mass ** p[1] * (1 + p[2] * d)
    elif model_id == "M_sat":
        p0 = [a0, b0, c0]
        lb, ub = [1e-6, -5, -50], [1e6, 5, 50]
        res = least_squares(resid_sat, p0, args=(mass_t, d_t, y_t), method="trf", bounds=(lb, ub), max_nfev=20000)
        k = 3
        def predict(p, mass, d, d2): return p[0] * mass ** p[1] * (1 + p[2] * d / (1 + d))
    elif model_id == "M_exp":
        p0 = [a0, b0, c0]
        lb, ub = [1e-6, -5, -50], [1e6, 5, 50]
        res = least_squares(resid_exp, p0, args=(mass_t, d_t, y_t), method="trf", bounds=(lb, ub), max_nfev=20000)
        k = 3
        def predict(p, mass, d, d2): return p[0] * mass ** p[1] * np.exp(p[2] * d)
    elif model_id == "M_inter":
        p0 = [a0, b0, c0]
        lb, ub = [1e-6, -5, -50], [1e6, 5, 50]
        res = least_squares(resid_inter, p0, args=(mass_t, d_t, d2_t, y_t), method="trf", bounds=(lb, ub), max_nfev=20000)
        k = 3
        def predict(p, mass, d, d2): return p[0] * mass ** p[1] * (1 + p[2] * d * d2)
    else:
        raise ValueError(model_id)

    popt = res.x
    pred_train = predict(popt, mass_t, d_t, d2_t)
    rss_train = float(np.sum((y_t - pred_train) ** 2))
    n_train = len(y_t)
    b_ic = bic(n_train, rss_train, k)
    pred_val = predict(popt, val["mass"], val["descriptor"], val["descriptor2"])
    r2_val = r2(val["g"], pred_val)
    return {"converged": res.success, "bic": b_ic, "r2_val": r2_val, "params": popt.tolist(), "k": k}


def split_dict(compounds_with_g, split):
    sub = compounds_with_g[compounds_with_g["split"] == split]
    return {col: sub[col].to_numpy(dtype=float) for col in ("mass", "descriptor", "descriptor2", "g")}


def main():
    # Load originals for a stratified sample: every family x every c x noise=0.02,default x grid=6, a handful of replicates
    originals = {}
    sample_ids = []
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            originals[r["world_id"]] = r

    import itertools
    coeffs = (0.25, 0.40, 0.55, 1.1, 2.2)
    for fam in FAMILIES:
        for c in coeffs:
            for rep in (0, 13, 27):  # 3 replicates spread across the 50
                wid = f"V2C|E3|{fam}|c{c:g}|noise0.02|grid6|r{rep:03d}"
                if wid in originals:
                    sample_ids.append(wid)
    print(f"Sample size: {len(sample_ids)} worlds")

    model_ids = ("M_mass", "M_affine", "M_sat", "M_exp", "M_inter")
    n_match_selection = 0
    n_total = 0
    bic_diffs = []
    mismatches = []

    for wid in sample_ids:
        orig = originals[wid]
        fam, c, noise, grid, rep = orig["family"], orig["c"], orig["noise_sd"], orig["grid_points"], orig["replicate"]
        world = build_world(fam, c, noise, grid, rep)
        scalars = fit_case_scalars(world.compounds, world.trajectories)
        compounds_with_g = world.compounds.assign(g=scalars.g)
        train = split_dict(compounds_with_g, "train")
        val = split_dict(compounds_with_g, "validation")
        test = split_dict(compounds_with_g, "test")

        my_bics = {}
        for mid in model_ids:
            fit = fit_independent(mid, train, val, test)
            my_bics[mid] = fit["bic"]
            orig_bic = orig["models"][mid]["bic"]
            if orig_bic is not None:
                bic_diffs.append(abs(fit["bic"] - orig_bic))

        my_selected = min(my_bics, key=my_bics.get)
        orig_selected = orig["bic_selected_model"]
        n_total += 1
        if my_selected == orig_selected:
            n_match_selection += 1
        else:
            mismatches.append({
                "world_id": wid, "family": fam, "c": c,
                "orig_selected": orig_selected, "my_selected": my_selected,
                "orig_bics": {m: orig["models"][m]["bic"] for m in model_ids},
                "my_bics": my_bics,
            })

    print(f"\nSelection agreement (independent fit vs oracle_models.py): {n_match_selection}/{n_total} ({100*n_match_selection/n_total:.1f}%)")
    print(f"BIC value differences: mean={np.mean(bic_diffs):.6f}, max={np.max(bic_diffs):.6f}, median={np.median(bic_diffs):.6f}")
    print(f"Number of mismatched selections: {len(mismatches)}")
    for m in mismatches[:15]:
        print(f"  MISMATCH {m['world_id']}: orig={m['orig_selected']} mine={m['my_selected']}")
        print(f"    orig_bics={ {k: round(v,4) if v is not None else None for k,v in m['orig_bics'].items()} }")
        print(f"    my_bics  ={ {k: round(v,4) for k,v in m['my_bics'].items()} }")

    result = {
        "sample_size": n_total,
        "selection_agreement": n_match_selection,
        "selection_agreement_pct": 100 * n_match_selection / n_total,
        "bic_diff_mean": float(np.mean(bic_diffs)),
        "bic_diff_max": float(np.max(bic_diffs)),
        "bic_diff_median": float(np.median(bic_diffs)),
        "n_mismatches": len(mismatches),
        "mismatches": mismatches,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "independent_refit_sample.json"
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
