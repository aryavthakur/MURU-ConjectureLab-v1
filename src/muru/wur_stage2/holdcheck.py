"""The single internal check on WUR-DEV-HOLD (protocol section 8, A-3).

Trains every arm on all of DEV2B, decodes HOLD once, aligns it with the
frozen Stage 1 map, scores P1 and the paired bootstraps. After this runs,
HOLD is EXPOSED and never again blind.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

from muru.discovery import protocol
from muru.io import wur_raw
from muru.io.wur_identity import accepted_rows
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.io.wur_spectra import build_mu_table
from muru.molecules import scaffold_group, tier_a_descriptors
from muru.wur_stage2 import arms_v1, cv as CV, population as POP, world as W
from muru.wur_stage2.descriptors2 import TIER_A2, tier_a2_descriptors

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts" / "wur_stage2b"
REL_FLOOR = 0.025
BOOT_N = 2000
BOOT_SEED = 20260911


def stereo_scaffold(smiles: str) -> str:
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return "__NONE__"
    Chem.RemoveStereochemistry(m)
    sc = MurckoScaffold.GetScaffoldForMol(m)
    s = Chem.MolToSmiles(sc)
    return s if s else "__ACYCLIC__"


def hold_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """HOLD long table (aligned, pooled rungs), covariates, identity, census."""
    hold = POP.load_internal_holdout()
    keys = set(hold["hold"]["connectivity_keys"])
    if canonical_key_hash(sorted(keys)) != hold["hold"]["connectivity_keys_sha256"]:
        raise POP.PopulationError("HOLD manifest hash mismatch")
    dev = POP.wur_dev_partition(data_dir)
    ident = dev[dev["connectivity_key"].isin(keys)].reset_index(drop=True)
    acc = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    acc = acc[acc["connectivity_key"].isin(keys)].reset_index(drop=True)
    if set(acc["connectivity_key"]) != keys:
        raise POP.PopulationError("HOLD accepted rows do not cover HOLD keys")
    sealed = set(json.loads((ROOT / "artifacts" / "wur_sealed_partition.json").read_text())["connectivity_keys"])
    if keys & sealed:
        raise POP.PopulationError("HOLD intersects the seal")
    mu, census = build_mu_table(acc, data_dir)          # seal guard runs; HOLD is not sealed
    if census:
        raise POP.PopulationError(f"HOLD peak defects: {census[:3]}")
    gate = json.loads((ROOT / "artifacts" / "wur_bridge_gate.json").read_text())["alignment"]
    long = W.aligned_wur_long(mu, float(gate["a"]), float(gate["b"]))
    pm = acc.groupby("connectivity_key")["precursor_mass"].median()
    rows = []
    for r in ident.itertuples(index=False):
        d = tier_a_descriptors(r.smiles); d2 = tier_a2_descriptors(r.smiles)
        if not d or not d2:
            raise POP.PopulationError(f"descriptor failure for a HOLD key")
        d["precursor_mz"] = float(pm.loc[r.connectivity_key])
        rows.append({"group_key": r.connectivity_key,
                     "scaffold_group": scaffold_group(r.smiles, r.connectivity_key),
                     "stereo_scaffold": stereo_scaffold(r.smiles),
                     **{f: float(d[f]) for f in protocol.FEATURES},
                     **{f: float(d2[f]) for f in TIER_A2}, "source": "WUR"})
    cov = pd.DataFrame(rows)
    return long, cov, ident, {"n_keys": len(keys), "n_spectra": int(len(acc)), "n_cells": int(len(mu))}


def paired_boot(dc: np.ndarray, clusters: np.ndarray | None, level: float, rng) -> list[float]:
    a = (1 - level) / 2 * 100
    if clusters is None:
        idx = rng.integers(0, len(dc), size=(BOOT_N, len(dc)))
        m = dc[idx].mean(1)
    else:
        uniq = np.unique(clusters)
        groups = [np.where(clusters == u)[0] for u in uniq]
        m = np.empty(BOOT_N)
        for b in range(BOOT_N):
            pick = rng.integers(0, len(groups), size=len(groups))
            sel = np.concatenate([groups[i] for i in pick])
            m[b] = dc[sel].mean()
    return np.percentile(m, [a, 100 - a]).tolist()


def run(data_dir: Path) -> dict:
    if (OUT / "hold_check.json").exists():
        # v2 guard: HOLD was scored once; a second run would overwrite its per-compound record
        raise POP.PopulationError("hold_check.json exists: HOLD was already scored once; holdcheck.run refuses")
    t0 = time.time()
    long_dev, cov_dev, frame_dev = CV.load_dev2b()
    hold_long, hold_cov, ident, census = hold_tables(data_dir)
    keys = sorted(hold_cov["group_key"])
    Y = CV.wide(hold_long, keys)
    # Tier A2 for the candidate that needs it: extend the A2 table in memory
    a2_dev = pd.read_csv(arms_v1.A2_PATH)
    a2_all = pd.concat([a2_dev, hold_cov[["group_key", *TIER_A2]]], ignore_index=True)
    arms_v1._a2 = lambda: a2_all
    # exposure: HOLD stereo scaffolds shared with any DEV2B compound
    dev_sm = pd.read_parquet(ROOT / "artifacts" / "p2_compounds.parquet")
    dev_sm = dev_sm[~dev_sm.in_confirmation]
    dev_stereo = {stereo_scaffold(s) for s in dev_sm["smiles"]}
    exposed = hold_cov["stereo_scaffold"].isin(dev_stereo).to_numpy()
    ctx = {"repeat": 99, "outer_fold": 0}
    arms = {"V1B_RIDGE_TIERA": CV.LinRidge, "B0_NULL_PROFILE": CV.B0NullProfile,
            "B1_MASS_ONLY_ISOTONIC": CV.B1MassOnly, "V1A_STABLE_LAW": arms_v1.StableLaw,
            "V1C_RICH_RIDGE_24": arms_v1.RichRidge,
            "S2A_FROZEN_PIPELINE": lambda: CV.S2AFrozen(OUT / "ckpt_s2a_hold")}
    preds, rmse, diag = {}, {}, {}
    cov_h = hold_cov.copy()
    for name, make in arms.items():
        arm = make()
        arm.fit(long_dev, cov_dev, ctx)
        p = arm.predict_mu(cov_h)
        preds[name] = p; rmse[name] = CV.per_compound_rmse(p, Y); diag[name] = arm.diagnostics()
    rng = np.random.default_rng(BOOT_SEED)
    clusters = pd.factorize(hold_cov["stereo_scaffold"])[0]
    res = {"n_hold": len(keys), "n_exposed_stereo_scaffold": int(exposed.sum()), "census": census,
           "hold_keys_sha256": canonical_key_hash(keys), "arms": {}, "comparisons": {}}
    for name in arms:
        m = CV.fold_metrics(preds[name], Y, preds["B0_NULL_PROFILE"], np.array(["WUR"] * len(keys)))
        m["P1_excluding_exposed"] = float(np.sqrt(np.nanmean(np.where(np.isfinite(Y[~exposed]), preds[name][~exposed] - Y[~exposed], np.nan) ** 2)))
        m["diagnostics"] = diag[name]
        res["arms"][name] = m
    C = "V1B_RIDGE_TIERA"
    for ref in ("S2A_FROZEN_PIPELINE", "B1_MASS_ONLY_ISOTONIC", "B0_NULL_PROFILE", "V1C_RICH_RIDGE_24", "V1A_STABLE_LAW"):
        for cand in (C, "V1A_STABLE_LAW", "V1C_RICH_RIDGE_24"):
            if cand == ref:
                continue
            dc = rmse[cand] - rmse[ref]
            p1c, p1r = res["arms"][cand]["P1"], res["arms"][ref]["P1"]
            res["comparisons"][f"{cand}_vs_{ref}"] = {
                "P1_cand": p1c, "P1_ref": p1r, "rel_improvement": (p1r - p1c) / p1r,
                "mean_paired_rmse_diff": float(dc.mean()),
                "ci90_compound": paired_boot(dc, None, 0.90, rng),
                "ci95_compound": paired_boot(dc, None, 0.95, rng),
                "ci90_cluster_stereo_scaffold": paired_boot(dc, clusters, 0.90, rng),
                "wins_fraction": float(np.mean(dc < 0))}
    c_s2a = res["comparisons"][f"{C}_vs_S2A_FROZEN_PIPELINE"]
    c_b1 = res["comparisons"][f"{C}_vs_B1_MASS_ONLY_ISOTONIC"]
    cond = {"P1_C_lt_S2A": c_s2a["P1_cand"] < c_s2a["P1_ref"],
            "P1_C_lt_B1": c_b1["P1_cand"] < c_b1["P1_ref"],
            "rel_vs_S2A_ge_2.5pct": c_s2a["rel_improvement"] >= REL_FLOOR,
            "ci90_compound_below_zero": c_s2a["ci90_compound"][1] < 0}
    res["conditions"] = cond
    res["passed"] = all(cond.values())
    res["hold_status"] = "EXPOSED"
    res["seconds"] = time.time() - t0
    res["environment"] = environment_provenance(ROOT)
    pd.DataFrame({"group_key": keys, "stereo_scaffold": hold_cov["stereo_scaffold"], "exposed": exposed,
                  **{f"rmse_{n}": rmse[n] for n in arms}}).to_csv(OUT / "hold_check_percompound.csv", index=False)
    return res
