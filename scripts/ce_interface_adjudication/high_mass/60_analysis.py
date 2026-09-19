#!/usr/bin/env python3
"""High-mass replication, step 60: the single frozen one-look analysis.

Reuses the Design A analysis module (pinned by sha256) for the mechanical drop rule, the frozen
three-step reduction (replicate records -> NCE cells -> models) and the multinomial bootstrap weights.
Replaces only the decision: ONE primary contrast D = S_K1 - S_K2, two-sided 95% percentile interval.

  HIGH_MASS_SUPPORTS_K1  interval wholly above zero
  HIGH_MASS_SUPPORTS_K2  interval wholly below zero
  HIGH_MASS_UNRESOLVED   otherwise

K3, JS, per-model, per-NCE, per-contributor and per-mass patterns are descriptive only.
Refuses unless MURU_CE_HIGH_MASS_ONE_LOOK=1, the freeze ref resolves, and the score table and the
population match the sha256 values in the frozen input manifest.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hm_constants as C  # noqa: E402

ROOT = HERE.parents[2]
DESIGN_A_ANALYSIS = HERE.parent / "design_a/50_analysis.py"
ONE_LOOK_ENV = "MURU_CE_HIGH_MASS_ONE_LOOK"
STUDY = ROOT / C.STUDY_DIR_REL
SCORES_REL = f"{C.STUDY_DIR_REL}/scores/record_scores.csv"
POPULATION_REL = f"{C.STUDY_DIR_REL}/population/high_mass_compounds.csv"
RECORDS_REL = f"{C.STUDY_DIR_REL}/population/high_mass_records.csv"
INPUT_MANIFEST_REL = f"{C.STUDY_DIR_REL}/freeze/input_manifest.json"
RESULT_DIR = STUDY / "result"


def load_design_a():
    got = hashlib.sha256(DESIGN_A_ANALYSIS.read_bytes()).hexdigest()
    if got != C.DESIGN_A_SHA256["50_analysis.py"]:
        raise SystemExit(f"refusing: Design A analysis sha256 {got} != pinned")
    spec = importlib.util.spec_from_file_location("design_a_analysis", DESIGN_A_ANALYSIS)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    A.PREREG_ID, A.FREEZE_REF, A.ONE_LOOK_ENV = C.STUDY_ID, C.FREEZE_REF, ONE_LOOK_ENV
    A.SCORES_REL, A.POPULATION_REL, A.INPUT_MANIFEST_REL = SCORES_REL, POPULATION_REL, INPUT_MANIFEST_REL
    A.NCE_CELLS = tuple(C.NCE_GRID)
    A.BOOT_SEED = C.BOOT_SEED
    return A


def decide(ci: list[float]) -> str:
    if ci[0] > 0.0:
        return "HIGH_MASS_SUPPORTS_K1"
    if ci[1] < 0.0:
        return "HIGH_MASS_SUPPORTS_K2"
    return "HIGH_MASS_UNRESOLVED"


def contrast(A, S: pd.DataFrame, codes, n_units, W, a="K1", b="K2") -> dict:
    d = S[a].to_numpy(float) - S[b].to_numpy(float)
    counts = np.bincount(codes, minlength=n_units).astype(float)
    rep = (W @ np.bincount(codes, weights=d, minlength=n_units)) / (W @ counts)
    return {"contrast": f"S_{a} - S_{b}", "point_estimate": float(d.mean()),
            "ci95": A._percentile_ci(rep, 0.95), "n_units": int(n_units), "n_boot": int(W.shape[0]),
            "n_compounds_positive": int((d > 0).sum()), "n_compounds_negative": int((d < 0).sum())}


def analyse_metric(A, scores, pop, metric, n_boot=C.BOOT_B, seed=C.BOOT_SEED) -> dict:
    prep = A.prepare_records(scores, pop, metric=metric)
    red = A.reduce_scores(prep["records"], metric=metric)
    S = red["S"]
    codes, uniq = A.unit_codes(list(S.index), prep["population"], "compound")
    W = A.replicate_weights(codes, len(uniq), n=n_boot, seed=seed)
    out = {"metric": metric, "completeness_and_drops": prep["report"], "n_compounds_analysed": int(len(S)),
           "composite_scores": {k: float(S[k].mean()) for k in C.MAPPINGS},
           "primary_contrast_K1_minus_K2": contrast(A, S, codes, len(uniq), W),
           "replicate_weights_sha256": hashlib.sha256(W.tobytes()).hexdigest(),
           "descriptive": {
               "K1_minus_K3": contrast(A, S, codes, len(uniq), W, "K1", "K3"),
               "K2_minus_K3": contrast(A, S, codes, len(uniq), W, "K2", "K3"),
               "per_model": {}, "per_nce": A.per_nce_breakdown(red["cell"]),
               "model_agreement": A.model_agreement(red["per_model"])}}
    for m in C.MODELS:
        Sm = red["per_model"][red["per_model"]["model"] == m].pivot(
            index="compound_id", columns="mapping", values="value").sort_index().reindex(columns=list(C.MAPPINGS))
        out["descriptive"]["per_model"][m] = contrast(A, Sm, codes, len(uniq), W)
    popi = prep["population"].set_index("compound_id")
    d = (S["K1"] - S["K2"]).rename("d").to_frame().join(popi[["contributor_arm", "theoretical_mh"]])
    out["descriptive"]["per_contributor_arm_mean_K1_minus_K2"] = {
        str(k): {"n": int(len(g)), "mean": float(g["d"].mean())} for k, g in d.groupby("contributor_arm")}
    d["mass_band"] = pd.cut(d["theoretical_mh"], [0, 500, 700, 900, 1000], right=False).astype(str)
    out["descriptive"]["per_mass_band_mean_K1_minus_K2"] = {
        str(k): {"n": int(len(g)), "mean": float(g["d"].mean())} for k, g in d.groupby("mass_band")}
    out["per_compound_K1_minus_K2"] = {str(k): float(v) for k, v in (S["K1"] - S["K2"]).items()}
    return out


def analyse(A, scores, population, n_boot=C.BOOT_B, seed=C.BOOT_SEED) -> dict:
    pop = population.drop_duplicates("compound_id").copy()
    pop["compound_id"] = pop["compound_id"].astype(str)
    pop["scaffold_group"] = pop["scaffold_group"].astype(str)
    if pop["scaffold_group"].duplicated().any():
        raise SystemExit("refusing: population must hold one compound per scaffold group")
    pop = pop.sort_values("compound_id").reset_index(drop=True)
    primary = analyse_metric(A, scores, pop, C.PRIMARY_METRIC, n_boot, seed)
    js = analyse_metric(A, scores, pop, C.ROBUSTNESS_METRIC, n_boot, seed)
    ci = primary["primary_contrast_K1_minus_K2"]["ci95"]
    return {"study_id": C.STUDY_ID, "verdict": decide(ci),
            "rule": "95% percentile interval of mean compound-level S_K1 - S_K2: above 0 -> K1, below 0 -> K2, else UNRESOLVED",
            "bootstrap": {"B": n_boot, "seed": seed, "unit": "compound (one compound per scaffold group)"},
            "nce_grid": list(C.NCE_GRID), "primary": primary,
            "robustness_js": {**js, "status": "robustness only; cannot change the verdict",
                              "verdict_if_applied": decide(js["primary_contrast_K1_minus_K2"]["ci95"])}}


def main() -> int:
    A = load_design_a()
    if os.environ.get(ONE_LOOK_ENV) != "1":
        raise SystemExit(f"refusing: {ONE_LOOK_ENV}=1 required; the analysis runs exactly once")
    gov = {"freeze_ref_commit": A.check_freeze_ref(ROOT), **A.check_input_hashes(ROOT)}
    if (RESULT_DIR / "analysis.json").exists():
        raise SystemExit("refusing: a result already exists; the one look has been taken")
    scores = pd.read_csv(ROOT / SCORES_REL)
    population = pd.read_csv(ROOT / POPULATION_REL)
    res = analyse(A, scores, population)
    res["governance"] = gov
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "analysis.json").write_text(json.dumps(res, indent=1) + "\n")
    (RESULT_DIR / "verdict.txt").write_text(res["verdict"] + "\n")
    p = res["primary"]["primary_contrast_K1_minus_K2"]
    print(f"{res['verdict']}  D = {p['point_estimate']:+.6f}  95% [{p['ci95'][0]:+.6f}, {p['ci95'][1]:+.6f}]  "
          f"n = {p['n_units']}  composite {res['primary']['composite_scores']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
