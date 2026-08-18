"""Tier A and Tier B computation on the DEVELOPMENT corpus.

Computed from sanitized SMILES only. No endpoint is read, so the descriptor
freeze is genuinely blind to the response (Phase 2 instructions 6 and 7).
Confirmation-set compounds are excluded entirely: they are not used for
descriptor selection, correlation screening, or anything else in Phase 2.

Writes:
  artifacts/p2_tierA.parquet
  artifacts/p2_tierB.parquet
  artifacts/p2_descriptor_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.molecules import (MASS_BLOCK, MORGAN_NBITS, MORGAN_RADIUS, TIER_A,
                            TIER_B_RDKIT_BLOCK, morgan_bits, rdkit_block,
                            tier_a_descriptors)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"

A: dict = {}

cmpd = pd.read_parquet(ART / "p2_compounds.parquet")
dev = cmpd[~cmpd.in_confirmation].copy()
A["n_development_compounds"] = int(len(dev))
A["n_confirmation_excluded"] = int(cmpd.in_confirmation.sum())

# ---------------------------------------------------------------------------
# Tier A
# ---------------------------------------------------------------------------
rows = []
failures = []
for r in dev.itertuples():
    d = tier_a_descriptors(r.smiles)
    if not d:
        failures.append(r.group_key)
        continue
    d["group_key"] = r.group_key
    d["precursor_mz"] = float(r.precursor_mz)   # from the record, not RDKit
    rows.append(d)
tierA = pd.DataFrame(rows)[["group_key", *TIER_A]]

A["tier_a"] = {
    "frozen_list": list(TIER_A),
    "n_descriptors": len(TIER_A),
    "n_failures": len(failures),
    "failed_group_keys": failures,
    "mass_block_for_ablation": list(MASS_BLOCK),
}
A["tier_a_summary"] = {
    c: {"n_missing": int(tierA[c].isna().sum()),
        "n_distinct": int(tierA[c].nunique()),
        "min": float(tierA[c].min()), "max": float(tierA[c].max()),
        "median": float(tierA[c].median()),
        "sd": float(tierA[c].std(ddof=1))}
    for c in TIER_A}

corr = tierA[list(TIER_A)].corr(method="spearman")
A["tier_a_spearman"] = {a: {b: round(float(corr.loc[a, b]), 3) for b in TIER_A}
                        for a in TIER_A}
pairs = [(a, b, float(corr.loc[a, b])) for i, a in enumerate(TIER_A)
         for b in TIER_A[i + 1:]]
A["tier_a_collinearity"] = {
    "severe_ge_0.90": [{"a": a, "b": b, "rho": round(r, 3)}
                       for a, b, r in pairs if abs(r) >= 0.90],
    "strong_0.70_to_0.90": [{"a": a, "b": b, "rho": round(r, 3)}
                            for a, b, r in pairs if 0.70 <= abs(r) < 0.90],
    "max_abs_offdiagonal": round(max(abs(r) for _, _, r in pairs), 3),
}

# Variance inflation, to state how far coefficient interpretation can be trusted
X = tierA[list(TIER_A)].to_numpy(float)
Xs = (X - X.mean(0)) / X.std(0, ddof=1)
vif = {}
for i, name in enumerate(TIER_A):
    y = Xs[:, i]
    Z = np.delete(Xs, i, axis=1)
    beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
    r2 = 1 - ((y - Z @ beta) ** 2).sum() / (y ** 2).sum()
    vif[name] = round(float(1 / max(1 - r2, 1e-12)), 2)
A["tier_a_vif"] = vif

# ---------------------------------------------------------------------------
# Tier B
# ---------------------------------------------------------------------------
fp = np.vstack([morgan_bits(s) for s in dev.smiles])
blk = pd.DataFrame([rdkit_block(s) for s in dev.smiles])
blk.insert(0, "group_key", dev.group_key.to_numpy())

fp_cols = [f"fp_{i}" for i in range(MORGAN_NBITS)]
fpdf = pd.DataFrame(fp, columns=fp_cols)
fpdf.insert(0, "group_key", dev.group_key.to_numpy())
tierB = blk.merge(fpdf, on="group_key")

on = fp.sum(0)
A["tier_b"] = {
    "morgan_radius": MORGAN_RADIUS,
    "morgan_nbits": MORGAN_NBITS,
    "rdkit_block": list(TIER_B_RDKIT_BLOCK),
    "n_rdkit_descriptors": len(TIER_B_RDKIT_BLOCK),
    "n_fingerprint_bits_ever_set": int((on > 0).sum()),
    "n_fingerprint_bits_always_zero": int((on == 0).sum()),
    "median_bits_set_per_molecule": float(np.median(fp.sum(1))),
    "n_rdkit_nan_cells": int(blk[[c for c in blk.columns
                                  if c != "group_key"]].isna().sum().sum()),
    "total_features": int(len(TIER_B_RDKIT_BLOCK) + (on > 0).sum()),
}

tierA.to_parquet(ART / "p2_tierA.parquet", index=False)
tierB.to_parquet(ART / "p2_tierB.parquet", index=False)
(ART / "p2_descriptor_audit.json").write_text(json.dumps(A, indent=2))

print(json.dumps({k: v for k, v in A.items()
                  if k not in ("tier_a_spearman", "tier_a_summary")}, indent=2))
