"""Design B step 60: the single preregistered analysis.

Reduction (frozen, plan f7825e2 section 7): for compound i and metric M,
  d_i = mean over the 5 NCE cells and the 2 models of [M(K1) - M(K2)]  (equal weights, 10 terms).
A compound enters only if all 20 K1/K2 cells (5 NCE x 2 models x 2 mappings) carry a value.
Primary: D_div = (mean d over L + mean d over H) / 2. Stratified compound-level percentile bootstrap, B = 10,000,
seed 20260919, compounds resampled with replacement within stratum, one shared set of draws for every statistic.
Two-sided 95% interval. Identifying test (fixed sequence, only if the primary rejects):
  I = D_div - D_null (D_null = mean d over N), two-sided 95% interval from the same draws; significant if it
  excludes zero; identification also requires sign(I) = sign(D_div) and sign(mean_L) = sign(mean_H) = sign(D_div).
Verdicts: SUPPORTED AND IDENTIFIED, FAVOURED NOT IDENTIFIED, INTERFACE UNRESOLVED (K1 or K2 by the sign of D_div).
Descriptive only: K3 contrasts, JS, per model, per NCE, per stratum, q95 support sensitivity, reproducibility QC.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

ROOT = HERE.parents[2]
STUDY_DIR = ROOT / "artifacts/ce_interface_adjudication/design_b"
ONE_LOOK_ENV = "MURU_CE_DESIGN_B_ONE_LOOK"


def compound_contrasts(scores: pd.DataFrame, a: str, b: str, metric: str, cell_mask=None) -> pd.DataFrame:
    s = scores[scores["mapping"].isin([a, b])].copy()
    if cell_mask is not None:
        s = s[cell_mask.reindex(s.index).fillna(False).astype(bool)]
    w = s.pivot_table(index=["compound_id", "stratum", "nce", "model"], columns="mapping", values=metric, aggfunc="first")
    w = w.dropna(subset=[a, b])
    w["diff"] = w[a] - w[b]
    g = w.reset_index().groupby(["compound_id", "stratum"])
    d = g["diff"].mean().rename("d").reset_index()
    d["n_terms"] = g.size().values
    return d


def complete_compounds(scores: pd.DataFrame, metric: str) -> set:
    s = scores[scores["mapping"].isin(C.PRIMARY_PAIR)]
    ok = s.groupby("compound_id")[metric].apply(lambda v: v.notna().sum())
    need = len(C.NCE_GRID) * len(C.MODELS) * len(C.PRIMARY_PAIR)
    return set(ok[ok == need].index)


def bootstrap_draws(d: pd.DataFrame, B: int = C.BOOT_B, seed: int = C.BOOT_SEED) -> dict:
    """Per-stratum bootstrap means, shape (B,), one generator, strata drawn in the fixed order L, N, H."""
    rng = np.random.default_rng(seed)
    out = {}
    for s in ("L", "N", "H"):
        v = d.loc[d["stratum"] == s].sort_values("compound_id")["d"].to_numpy()
        idx = rng.integers(0, len(v), size=(B, len(v))) if len(v) else np.zeros((B, 0), int)
        out[s] = v[idx].mean(axis=1) if len(v) else np.full(B, np.nan)
    return out


def ci(x: np.ndarray) -> list:
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def decide(point: dict, ci_div: list, ci_I: list) -> dict:
    lead = "K1" if point["D_div"] > 0 else "K2"
    primary = ci_div[0] > 0 or ci_div[1] < 0
    if not primary:
        return {"verdict": "INTERFACE UNRESOLVED", "primary_rejects": False, "identifying_test_run": False}
    sgn = np.sign(point["D_div"])
    I_sig = ci_I[0] > 0 or ci_I[1] < 0
    ident = bool(I_sig and np.sign(point["I"]) == sgn and np.sign(point["mean_L"]) == sgn and np.sign(point["mean_H"]) == sgn)
    return {"verdict": f"{lead} SUPPORTED AND IDENTIFIED" if ident else f"{lead} FAVOURED, NOT IDENTIFIED",
            "primary_rejects": True, "identifying_test_run": True, "I_significant": bool(I_sig),
            "I_sign_agrees": bool(np.sign(point["I"]) == sgn),
            "L_H_signs_agree": bool(np.sign(point["mean_L"]) == sgn and np.sign(point["mean_H"]) == sgn)}


def contrast_block(scores, a, b, metric, B=C.BOOT_B, seed=C.BOOT_SEED, cell_mask=None) -> dict:
    d = compound_contrasts(scores, a, b, metric, cell_mask)
    draws = bootstrap_draws(d, B, seed)
    m = {s: float(d.loc[d["stratum"] == s, "d"].mean()) if (d["stratum"] == s).any() else float("nan") for s in ("L", "N", "H")}
    pt = {"mean_L": m["L"], "mean_N": m["N"], "mean_H": m["H"], "D_div": (m["L"] + m["H"]) / 2}
    pt["I"] = pt["D_div"] - m["N"]
    div = (draws["L"] + draws["H"]) / 2
    return {"point": pt, "ci_D_div": ci(div), "ci_I": ci(div - draws["N"]),
            "ci_per_stratum": {s: ci(draws[s]) for s in ("L", "N", "H")},
            "n": d.groupby("stratum").size().to_dict()}


def analyse(scores: pd.DataFrame, B: int = C.BOOT_B, seed: int = C.BOOT_SEED) -> dict:
    keep = complete_compounds(scores, C.PRIMARY_METRIC)
    sc = scores[scores["compound_id"].isin(keep)]
    prim = contrast_block(sc, "K1", "K2", C.PRIMARY_METRIC, B, seed)
    res = {"primary": prim, "decision": decide(prim["point"], prim["ci_D_div"], prim["ci_I"])}
    n = prim["n"]
    res["underpowered_disclosure"] = {s: int(n.get(s, 0)) < C.UNDERPOWERED_FLOOR for s in ("L", "N", "H")}
    desc = {"JS_K1_K2": contrast_block(sc, "K1", "K2", C.ROBUSTNESS_METRIC, B, seed),
            "cos_K1_K3": contrast_block(sc, "K1", "K3", C.PRIMARY_METRIC, B, seed),
            "cos_K2_K3": contrast_block(sc, "K2", "K3", C.PRIMARY_METRIC, B, seed)}
    for mdl in C.MODELS:
        desc[f"cos_K1_K2_{mdl}"] = contrast_block(sc[sc["model"] == mdl], "K1", "K2", C.PRIMARY_METRIC, B, seed)
    k2 = sc["nce"].astype(float) * sc["theoretical_mh"].astype(float) / 500.0
    in_support = (sc["nce"].astype(float) <= C.TRAINING_CE_Q95) & (k2 <= C.TRAINING_CE_Q95)
    desc["q95_support_sensitivity"] = contrast_block(sc, "K1", "K2", C.PRIMARY_METRIC, B, seed, cell_mask=in_support)
    per_nce = sc[sc["mapping"].isin(C.MAPPINGS)].groupby(["stratum", "nce", "mapping"])[C.PRIMARY_METRIC].mean()
    desc["mean_cosine_by_stratum_nce_mapping"] = {"|".join(map(str, k)): float(v) for k, v in per_nce.items()}
    res["descriptive"] = desc
    res["excluded_incomplete_prediction"] = sorted(set(scores["compound_id"]) - keep)
    return res


def main() -> int:
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    if os.environ.get(ONE_LOOK_ENV) != "1":
        raise SystemExit(f"refusing: {ONE_LOOK_ENV}=1 required; the analysis runs exactly once")
    for ref in (C.FREEZE_REF, C.PROCUREMENT_REF, C.SPECTRA_REF, C.PREDICTIONS_REF):
        if not subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", ref], capture_output=True, text=True).stdout.strip():
            raise SystemExit(f"refusing: {ref} does not resolve")
    out = STUDY_DIR / "result/analysis.json"
    if out.exists():
        raise SystemExit("refusing: a result already exists; the one look has been taken")
    p = STUDY_DIR / "scores/cell_scores.csv"
    res = analyse(pd.read_csv(p))
    res["inputs"] = {"cell_scores_sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    qc = STUDY_DIR / "scores/reproducibility_qc.csv"
    if qc.exists():
        q = pd.read_csv(qc)
        res["descriptive"]["reproducibility_qc_median_obs_obs_cosine"] = float(q["obs_obs_cosine"].median()) if len(q) else None
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({"verdict": res["decision"]["verdict"], "point": res["primary"]["point"],
                      "ci_D_div": res["primary"]["ci_D_div"], "ci_I": res["primary"]["ci_I"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
