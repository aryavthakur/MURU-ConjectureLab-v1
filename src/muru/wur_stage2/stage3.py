"""Stage 3: the single look at WUR-SEALED for the frozen final candidate.

Everything here is fixed by MURU_WUR_FINAL_CANDIDATE_FREEZE.md. The sealed
peaks are decoded exactly once, through `build_mu_table(..., allow_sealed=True)`,
the only call site in the repository that passes that flag. The first
access is stamped with the git HEAD at run time so the freeze-precedes-
access audit can be run against it.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

from muru.discovery import protocol
from muru.io import wur_raw
from muru.io.wur_identity import accepted_rows
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.io.wur_spectra import build_mu_table
from muru.molecules import scaffold_group, tier_a_descriptors
from muru.wur_stage2 import arms_v1, cv as CV, holdcheck as HC, population as POP, world as W
from muru.wur_stage2.descriptors2 import TIER_A2, tier_a2_descriptors

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts" / "wur_stage3"
WUR_SEALED_SHA256 = "6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52"
BOOT_SEED = 20260911


def training_population(data_dir: Path):
    """DEV2B plus HOLD (aligned), as the freeze specifies."""
    long_dev, cov_dev, frame_dev = CV.load_dev2b()
    hold_long, hold_cov, _, _ = HC.hold_tables(data_dir)
    long = pd.concat([long_dev, hold_long], ignore_index=True)
    cov = pd.concat([cov_dev, hold_cov[cov_dev.columns]], ignore_index=True)
    a2 = pd.concat([pd.read_csv(arms_v1.A2_PATH), hold_cov[["group_key", *TIER_A2]]], ignore_index=True)
    return long, cov, a2


def sealed_tables(data_dir: Path):
    sealed = json.loads((ROOT / "artifacts" / "wur_sealed_partition.json").read_text())
    keys = set(sealed["connectivity_keys"])
    if canonical_key_hash(sorted(keys)) != WUR_SEALED_SHA256:
        raise POP.PopulationError("sealed hash mismatch")
    pos = POP.wur_dev_partition.__wrapped__(data_dir) if hasattr(POP.wur_dev_partition, "__wrapped__") else None
    from muru.io.wur_census import load_annotated_trajectories
    from muru.io.wur_partition import apply_d6, partition, sealed_scaffold_groups
    pre = partition(load_annotated_trajectories(data_dir))
    part = apply_d6(pre, sealed_scaffold_groups(pre["POS"]))
    pos = part["POS"]
    ident = pos[pos["side"] == "WUR-SEALED"].reset_index(drop=True)
    if set(ident["connectivity_key"]) != keys:
        raise POP.PopulationError("sealed identity rows do not match the frozen key list")
    acc = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    acc = acc[acc["connectivity_key"].isin(keys)].reset_index(drop=True)
    first_access = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                    "git_tree_dirty": bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip())}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "first_sealed_access.json").write_text(json.dumps(first_access, indent=1) + "\n")
    mu, census = build_mu_table(acc, data_dir, allow_sealed=True)   # THE sealed read
    gate = json.loads((ROOT / "artifacts" / "wur_bridge_gate.json").read_text())["alignment"]
    a, b = float(gate["a"]), float(gate["b"])
    aligned = W.aligned_wur_long(mu, a, b)
    native = W.native_long(mu, "WUR")
    pm = acc.groupby("connectivity_key")["precursor_mass"].median()
    rows, fails = [], []
    for r in ident.itertuples(index=False):
        d = tier_a_descriptors(r.smiles); d2 = tier_a2_descriptors(r.smiles)
        if not d or not d2:
            fails.append(r.connectivity_key); continue
        d["precursor_mz"] = float(pm.loc[r.connectivity_key])
        rows.append({"group_key": r.connectivity_key, "scaffold_group": scaffold_group(r.smiles, r.connectivity_key),
                     "stereo_scaffold": HC.stereo_scaffold(r.smiles),
                     **{f: float(d[f]) for f in protocol.FEATURES}, **{f: float(d2[f]) for f in TIER_A2}, "source": "WUR"})
    cov = pd.DataFrame(rows)
    return aligned, native, cov, {"n_keys": len(keys), "n_spectra": int(len(acc)), "n_cells": int(len(mu)),
                                  "peak_defect_census": census, "descriptor_failures": fails,
                                  "spectra_per_cell": mu["n_spectra"].value_counts().to_dict()}, first_access


def run(data_dir: Path) -> dict:
    long, cov, a2 = training_population(data_dir)
    arms_v1._a2 = lambda: a2
    aligned, native, cov_s, census, first_access = sealed_tables(data_dir)
    keys = sorted(cov_s["group_key"])
    Y = CV.wide(aligned, keys)
    a2_all = pd.concat([a2, cov_s[["group_key", *TIER_A2]]], ignore_index=True)
    arms_v1._a2 = lambda: a2_all
    ctx = {"repeat": 3, "outer_fold": 0}
    arms = {"V1B_RIDGE_TIERA": CV.LinRidge, "S2A_FROZEN_PIPELINE": lambda: CV.S2AFrozen(OUT / "ckpt_s2a_stage3"),
            "B0_NULL_PROFILE": CV.B0NullProfile, "B1_MASS_ONLY_ISOTONIC": CV.B1MassOnly,
            "V1A_STABLE_LAW": arms_v1.StableLaw, "V1C_RICH_RIDGE_24": arms_v1.RichRidge}
    fitted, preds, rmse, diag = {}, {}, {}, {}
    for name, make in arms.items():
        arm = make(); arm.fit(long, cov, ctx); fitted[name] = arm
        preds[name] = arm.predict_mu(cov_s); rmse[name] = CV.per_compound_rmse(preds[name], Y); diag[name] = arm.diagnostics()
    # WUR-only trained secondary
    wur_train = long[long["source"] == "WUR"]
    arm_w = CV.LinRidge(); arm_w.fit(wur_train, cov[cov["group_key"].isin(set(wur_train["group_key"]))], ctx)
    preds["V1B_WUR_ONLY_TRAINED"] = arm_w.predict_mu(cov_s); rmse["V1B_WUR_ONLY_TRAINED"] = CV.per_compound_rmse(preds["V1B_WUR_ONLY_TRAINED"], Y)
    rng = np.random.default_rng(BOOT_SEED)
    clusters = pd.factorize(cov_s["stereo_scaffold"])[0]
    benzene = (cov_s["scaffold_group"] == "c1ccccc1").to_numpy()
    src = np.array(["WUR"] * len(keys))
    res = {"population": {"n_evaluated": len(keys), "keys_sha256": canonical_key_hash(keys), **census},
           "first_sealed_access": first_access, "arms": {}, "comparisons": {}, "strata": {}}
    for name in preds:
        m = CV.fold_metrics(preds[name], Y, preds["B0_NULL_PROFILE"], src)
        m["diagnostics"] = diag.get(name, {})
        res["arms"][name] = m
        res["strata"][name] = {"benzene": float(np.sqrt(np.nanmean((preds[name][benzene] - Y[benzene]) ** 2))) if benzene.any() else None,
                               "non_benzene": float(np.sqrt(np.nanmean((preds[name][~benzene] - Y[~benzene]) ** 2)))}
    pairs = [("V1B_RIDGE_TIERA", "S2A_FROZEN_PIPELINE"), ("V1B_RIDGE_TIERA", "B1_MASS_ONLY_ISOTONIC"),
             ("V1B_RIDGE_TIERA", "B0_NULL_PROFILE"), ("B1_MASS_ONLY_ISOTONIC", "S2A_FROZEN_PIPELINE"),
             ("V1A_STABLE_LAW", "S2A_FROZEN_PIPELINE"), ("V1A_STABLE_LAW", "V1B_RIDGE_TIERA"),
             ("V1C_RICH_RIDGE_24", "V1B_RIDGE_TIERA"), ("V1B_WUR_ONLY_TRAINED", "V1B_RIDGE_TIERA")]
    for c, r in pairs:
        dc = rmse[c] - rmse[r]
        res["comparisons"][f"{c}_vs_{r}"] = {
            "P1_cand": res["arms"][c]["P1"], "P1_ref": res["arms"][r]["P1"],
            "rel_improvement": (res["arms"][r]["P1"] - res["arms"][c]["P1"]) / res["arms"][r]["P1"],
            "mean_paired_rmse_diff": float(dc.mean()),
            "ci90_compound": HC.paired_boot(dc, None, 0.90, rng), "ci95_compound": HC.paired_boot(dc, None, 0.95, rng),
            "ci95_cluster_stereo_scaffold": HC.paired_boot(dc, clusters, 0.95, rng),
            "wins_fraction": float(np.mean(dc < 0))}
    # S2A under its own gate
    s2a = fitted["S2A_FROZEN_PIPELINE"].sel_
    res["s2a_gate"] = {"report": s2a["report"], "expr": s2a.get("expr"), "features": s2a["gate"]["features"],
                       "note": "under its own gate the frozen method abstains when report is false; its P1 above is forced prediction"}
    # native coordinate secondary and E=15 separate
    Yn = CV.wide(native, keys, energies=(30.0, 45.0, 60.0, 75.0, 90.0))
    res["native_secondary"] = {name: float(np.sqrt(np.nanmean((fitted[name].predict_mu(cov_s) - Yn) ** 2)))
                               for name in ("V1B_RIDGE_TIERA", "S2A_FROZEN_PIPELINE", "B0_NULL_PROFILE", "B1_MASS_ONLY_ISOTONIC")}
    e15 = native[native["ce_numeric"] == 15.0]["mu"]
    res["e15_separate"] = {"n": int(len(e15)), "median": float(e15.median()), "q25": float(e15.quantile(.25)), "q75": float(e15.quantile(.75)),
                           "note": "never pooled; erratum E-3"}
    c = res["comparisons"]["V1B_RIDGE_TIERA_vs_S2A_FROZEN_PIPELINE"]; b = res["comparisons"]["V1B_RIDGE_TIERA_vs_B1_MASS_ONLY_ISOTONIC"]
    res["success_conditions"] = {"P1_C_lt_S2A": c["P1_cand"] < c["P1_ref"], "P1_C_lt_B1": b["P1_cand"] < b["P1_ref"],
                                 "rel_vs_S2A_ge_2.5pct": c["rel_improvement"] >= 0.025, "ci90_compound_below_zero": c["ci90_compound"][1] < 0}
    res["principal_claim_survives"] = all(res["success_conditions"].values())
    res["environment"] = environment_provenance(ROOT)
    pd.DataFrame({"group_key": keys, "stereo_scaffold": cov_s["stereo_scaffold"], "benzene": benzene,
                  **{f"rmse_{n}": rmse[n] for n in rmse}}).to_csv(OUT / "stage3_percompound.csv", index=False)
    aligned.to_csv(OUT / "sealed_long_aligned.csv", index=False); native.to_csv(OUT / "sealed_long_native.csv", index=False)
    cov_s.to_csv(OUT / "sealed_covariates.csv", index=False)
    return res
