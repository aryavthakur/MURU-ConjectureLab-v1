"""The v2 development population: every exposed positive-mode compound.

Union of LCSB-DEV (439), WUR-DEV-ANALYSIS (476), WUR-DEV-HOLD (130) and
WUR-SEALED (404) = 1,325 connectivity keys. A key measured on both
instruments keeps its LCSB trajectory as the primary copy (the v1 pooling
convention); both copies stay in the native table for the acquisition
experiments. Excluded: the LCSB confirmation set (110 keys; its 41 keys
that are also WUR-SEALED enter through their WUR copy only), WUR negative
mode, and the D6-excluded negative trajectories.

Energy coordinate: LCSB nominal NCE, pooled rungs 30-90; WUR is read at
T(E) = a + bE by PCHIP on its own ladder (frozen Stage 1 map, never refit).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from muru.discovery.protocol import FEATURES
from muru.io.wur_provenance import canonical_key_hash
from muru.molecules import scaffold_group, tier_a_descriptors
from muru.wur_bridge import apply_energy_map
from muru.wur_v2 import identity as ID
from muru.wur_v2.exposure import lcsb_confirmation_keys

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"
DATA = ART / "wur_v2" / "data"
POOLED_ENERGIES = (30.0, 45.0, 60.0, 75.0, 90.0)
NATIVE_ENERGIES = (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)


def bridge() -> tuple[float, float]:
    g = json.loads((ART / "wur_bridge_gate.json").read_text())["alignment"]
    return float(g["a"]), float(g["b"])


def historical_class(key: str, lcsb_dev: set, hold: set, sealed: set, analysis: set) -> str:
    tags = []
    if key in lcsb_dev:
        tags.append("LCSB-DEV")
    if key in analysis:
        tags.append("WUR-DEV-ANALYSIS")
    if key in hold:
        tags.append("WUR-DEV-HOLD")
    if key in sealed:
        tags.append("WUR-SEALED")
    return "+".join(tags)


def build() -> dict[str, pd.DataFrame]:
    conf = lcsb_confirmation_keys()
    hold_d = json.loads((ART / "wur_dev_internal_holdout.json").read_text())
    hold, analysis = set(hold_d["hold"]["connectivity_keys"]), set(hold_d["analysis"]["connectivity_keys"])
    sealed = set(json.loads((ART / "wur_sealed_partition.json").read_text())["connectivity_keys"])

    comp = pd.read_parquet(ART / "p2_compounds.parquet")
    lcsb = comp[~comp["in_confirmation"]].rename(columns={"inchikey_first_block": "connectivity_key"})
    lcsb_dev = set(lcsb["connectivity_key"])
    assert not lcsb_dev & conf
    corpus = pd.read_parquet(ART / "p2_dev_corpus.parquet")
    corpus = corpus[corpus["inchikey_first_block"].isin(lcsb_dev)]           # confirmation rows dropped by key
    lspec = pd.read_parquet(DATA / "lcsb_pos_spectra.parquet")
    pmr = lspec.groupby(["connectivity_key", "ce_numeric"])["precursor_mass_ratio"].mean()

    wid = pd.read_csv(DATA / "wur_pos_identity.csv")
    wcells = pd.read_csv(DATA / "wur_pos_cells.csv")
    wur_keys = set(wid["connectivity_key"])
    assert wur_keys == hold | analysis | sealed

    # ---------- native cells, every copy ----------
    ln = corpus.rename(columns={"inchikey_first_block": "connectivity_key"})[
        ["connectivity_key", "ce_numeric", "mu", "survival_yield", "fragment_depth"]].copy()
    ln["precursor_mass_ratio"] = [pmr.get((k, e), np.nan) for k, e in zip(ln["connectivity_key"], ln["ce_numeric"])]
    ln["source"] = "LCSB"
    wn = wcells[["connectivity_key", "ce_numeric", "mu", "survival_yield", "fragment_depth",
                 "precursor_mass_ratio", "n_acquisitions", "n_accepted_rows"]].copy()
    wn["source"] = "WUR"
    native = pd.concat([ln, wn], ignore_index=True)

    # ---------- aligned WUR (frozen map) ----------
    a, b = bridge()
    mapped, _ = apply_energy_map(wcells[["connectivity_key", "ce_numeric", "mu"]], a, b)
    walign = mapped[mapped["ce_numeric"].isin(POOLED_ENERGIES)].copy()
    walign["source"] = "WUR"

    # ---------- compounds ----------
    rows = []
    wsmi = wid.set_index("connectivity_key")
    wprec = pd.read_parquet(DATA / "wur_pos_spectra.parquet").groupby("connectivity_key")["precursor_mass"].median()
    for key in sorted(lcsb_dev | wur_keys):
        in_l, in_w = key in lcsb_dev, key in wur_keys
        if in_l:
            r = lcsb[lcsb["connectivity_key"] == key].iloc[0]
            smiles, prec, adduct = r["smiles"], float(r["precursor_mz"]), "[M+H]+"
        else:
            smiles, prec, adduct = wsmi.loc[key, "smiles"], float(wprec.loc[key]), wsmi.loc[key, "adduct"]
        d = tier_a_descriptors(smiles)
        if not d:
            raise ValueError(f"descriptor failure {key}")
        d["precursor_mz"] = prec
        pk = ID.parent_connectivity_key(smiles)
        rows.append({"group_key": key, "smiles": smiles, "parent_key": pk,
                     "primary_source": "LCSB" if in_l else "WUR", "measured_lcsb": in_l, "measured_wur": in_w,
                     "historical_class": historical_class(key, lcsb_dev, hold, sealed, analysis),
                     "adduct": adduct, "wur_adduct": wsmi.loc[key, "adduct"] if in_w else "",
                     "scaffold_v1": scaffold_group(smiles, key), "scaffold_group": ID.scaffold_group_v2(smiles, key),
                     "stereo_in_smiles": any(c in smiles for c in "@/\\"),
                     **{f: float(d[f]) for f in FEATURES}})
    cov = pd.DataFrame(rows)
    cov["strict_cluster"] = ID.strict_clusters(cov["smiles"], cov["scaffold_group"]).to_numpy()

    # ---------- primary aligned long table ----------
    la = corpus.rename(columns={"inchikey_first_block": "connectivity_key"})
    la = la[la["ce_numeric"].isin(POOLED_ENERGIES)][["connectivity_key", "ce_numeric", "mu"]].copy()
    la["source"] = "LCSB"
    long = pd.concat([la, walign[~walign["connectivity_key"].isin(lcsb_dev)]], ignore_index=True)
    long = long.rename(columns={"connectivity_key": "group_key"})
    if long.groupby(["group_key", "ce_numeric"]).size().max() != 1:
        raise ValueError("duplicated aligned cell")
    walign_all = walign.rename(columns={"connectivity_key": "group_key"})
    manifest = {"n_compounds": int(len(cov)), "keys_sha256": canonical_key_hash(cov["group_key"]),
                "n_lcsb_primary": int((cov.primary_source == "LCSB").sum()),
                "n_wur_primary": int((cov.primary_source == "WUR").sum()),
                "n_both_instruments": int((cov.measured_lcsb & cov.measured_wur).sum()),
                "historical_class_counts": cov["historical_class"].value_counts().to_dict(),
                "n_scaffold_groups": int(cov["scaffold_group"].nunique()),
                "n_scaffold_v1_groups": int(cov["scaffold_v1"].nunique()),
                "n_strict_clusters": int(cov["strict_cluster"].nunique()),
                "adduct_counts": cov["adduct"].value_counts().to_dict(),
                "n_aligned_cells": int(len(long)), "bridge": {"a": a, "b": b},
                "parent_key_mismatches": int((cov["parent_key"] != cov["group_key"]).sum()),
                "confirmation_keys_present": int(cov["group_key"].isin(conf & lcsb_dev).sum())}
    return {"compounds": cov, "long_aligned": long, "wur_aligned_all": walign_all, "native": native,
            "manifest": manifest}
