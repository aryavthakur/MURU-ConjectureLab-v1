"""Preprocessing robustness, mixture confounding (K8), and negative-mode scope.

Three bounded checks, each reported at the evidential weight it actually
carries:

1. Curated vs independently reprocessed raw mzML, on the MATCHED SUBSET ONLY.
   This is subset preprocessing robustness. It is NOT full-corpus independent
   raw replication and is never described as such (instruction 22).
2. Mixture identity after energy and mass are accounted for, plus
   leave-one-mixture-out sensitivity (instruction 21, K8).
3. Negative mode: the K4A/K4B comparison under S2 only, to see whether the
   positive-mode conclusion qualitatively replicates. No claim requiring a
   negative-mode noise estimate is made -- none exists (instruction 24).

Writes artifacts/p2_robustness.json
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.models import (SEED, FlexibleBenchmark, MassFlex, PerEnergyMean, Spec,
                         TierAModel, bootstrap_paired, compound_errors,
                         nested_cv)
from muru.molecules import TIER_A, butina_clusters, scaffold_group, tier_a_descriptors
from muru.splits import make_split

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
MIN_BIT_COUNT = 5
N_BOOT = 2000
RIDGE_GRID = [1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0]

R: dict = {}
base = json.loads((ART / "p2_baselines.json").read_text())

# ===========================================================================
# 1. Preprocessing branches, matched subset
# ===========================================================================
raw = pd.read_parquet(ART / "raw_branch_merged.parquet")
raw = raw[raw.n_scans > 0]
raw_avg = (raw.groupby(["inchikey_first_block", "ce_numeric"], as_index=False)
           .agg(mu=("mu", "mean"), precursor_mz=("precursor_mz", "mean")))

dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")
cur = dev[["inchikey_first_block", "ce_numeric", "mu", "precursor_mz"]]

matched_keys = sorted(set(raw_avg.inchikey_first_block) & set(cur.inchikey_first_block))
P: dict = {
    "scope": ("matched subset only -- mixes 499/503/505, positive mode. This is "
              "subset preprocessing robustness, NOT full-corpus independent raw "
              "replication, and subset agreement is not extrapolated to the "
              "corpus."),
    "n_matched_compounds": len(matched_keys),
    "n_curated_corpus_compounds": int(dev.group_key.nunique()),
    "coverage_pct": round(100 * len(matched_keys) / dev.group_key.nunique(), 2),
}

rho = {}
for label, frame in (("curated", cur), ("raw", raw_avg)):
    sub = frame[frame.inchikey_first_block.isin(matched_keys)]
    rho[label] = {}
    for e, g in sub.groupby("ce_numeric"):
        g = g.dropna(subset=["mu", "precursor_mz"])
        rho[label][int(e)] = (round(float(stats.spearmanr(g.mu, g.precursor_mz)
                                          .statistic), 4) if len(g) >= 10 else None)
P["rho_mu_vs_precursor_mz_by_branch"] = rho
P["rho_agreement"] = {
    "same_sign_at_every_energy": all(
        (rho["curated"][e] is None or rho["raw"][e] is None
         or np.sign(rho["curated"][e]) == np.sign(rho["raw"][e]))
        for e in rho["curated"]),
    "max_abs_difference": round(max(
        abs(rho["curated"][e] - rho["raw"][e])
        for e in rho["curated"]
        if rho["curated"][e] is not None and rho["raw"][e] is not None), 4),
}

# Paired agreement of mu itself on the matched cells
mrg = cur.merge(raw_avg, on=["inchikey_first_block", "ce_numeric"],
                suffixes=("_cur", "_raw")).dropna(subset=["mu_cur", "mu_raw"])
P["mu_agreement"] = {
    "n_paired_cells": int(len(mrg)),
    "median_difference_raw_minus_curated": round(float((mrg.mu_raw - mrg.mu_cur).median()), 5),
    "mean_abs_difference": round(float((mrg.mu_raw - mrg.mu_cur).abs().mean()), 5),
    "spearman": round(float(stats.spearmanr(mrg.mu_cur, mrg.mu_raw).statistic), 4),
    "phase1_intermixture_sd_upper_bound": 0.0295,
    "note": ("the Phase 1 figure is the conservative inter-mixture variability "
             "estimate, an upper bound on technical repeatability -- not an "
             "instrument noise floor"),
}
R["preprocessing_robustness"] = P

# ===========================================================================
# 2. Mixture confounding and K8
# ===========================================================================
d = pd.read_parquet(ART / "p2_splits.parquet")
tA = pd.read_parquet(ART / "p2_tierA.parquet").drop(columns=["precursor_mz"])
df = d.merge(tA, on="group_key")

hp_tierA = ast.literal_eval(base["performance"]["S2"]["TIER_A"]["hp_modal"])


class MassFlexPlusMix(MassFlex):
    """MASS FLEX with mixture identity added as a one-hot block."""

    def _basis(self, frame, fit: bool):
        B = super()._basis(frame, fit)
        if fit:
            self.mixes_ = sorted(frame["mix"].unique())
        M = np.column_stack([(frame["mix"] == m).astype(float)
                             for m in self.mixes_])
        return np.column_stack([B, M])


specs = {
    "MASS_FLEX": Spec("MASS_FLEX", MassFlex, grid=[{"alpha": a} for a in RIDGE_GRID]),
    "MASS_FLEX_plus_mix": Spec("MASS_FLEX_plus_mix", MassFlexPlusMix,
                               grid=[{"alpha": a} for a in RIDGE_GRID]),
    "TIER_A": Spec("TIER_A", TierAModel, feats=list(TIER_A),
                   grid=[{"alpha": a} for a in RIDGE_GRID], needs_feats=True),
}
ce = {}
for name, sp in specs.items():
    p = nested_cv(df, sp, "fold_S2", inner_folds=4, seed=SEED)
    ce[name] = compound_errors(p)

scaf = df.drop_duplicates("inchikey_first_block").set_index(
    "inchikey_first_block").scaffold_group
mix_gain = bootstrap_paired(ce["MASS_FLEX_plus_mix"], ce["MASS_FLEX"], scaf,
                            N_BOOT, SEED)
struct_gain = bootstrap_paired(ce["TIER_A"], ce["MASS_FLEX"], scaf, N_BOOT, SEED)

# Leave-one-mixture-out
lomo = {}
for m in sorted(df["mix"].unique()):
    tr, te = df[df["mix"] != m], df[df["mix"] == m]
    if te.inchikey_first_block.nunique() < 10:
        continue
    row = {}
    for name, sp in (("MASS_FLEX", specs["MASS_FLEX"]), ("TIER_A", specs["TIER_A"])):
        mdl = sp.ctor(**sp.grid[-2])
        mdl.fit(tr, sp.feats) if sp.needs_feats else mdl.fit(tr)
        if sp.needs_feats:
            mdl.feats_ = sp.feats
        row[name] = round(float(np.mean(np.abs(te.mu - mdl.predict(te)))), 5)
    row["n_compounds"] = int(te.inchikey_first_block.nunique())
    row["tier_a_minus_mass_flex"] = round(row["TIER_A"] - row["MASS_FLEX"], 5)
    lomo[int(m)] = row

R["mixture_confounding"] = {
    "question": ("does mixture identity materially improve prediction AFTER "
                 "energy and mass are included"),
    "mass_flex_mae": round(float(ce["MASS_FLEX"].mae.mean()), 5),
    "mass_flex_plus_mix_mae": round(float(ce["MASS_FLEX_plus_mix"].mae.mean()), 5),
    "mix_gain_over_mass_flex": {
        "mae_diff": round(mix_gain["diff"], 5),
        "ci_scaffold": [round(mix_gain["lo"], 5), round(mix_gain["hi"], 5)],
        "improves": bool(mix_gain["diff"] < 0 and mix_gain["hi"] < 0)},
    "structure_gain_over_mass_flex": {
        "mae_diff": round(struct_gain["diff"], 5),
        "ci_scaffold": [round(struct_gain["lo"], 5), round(struct_gain["hi"], 5)]},
    "leave_one_mixture_out": lomo,
}
mix_d = abs(mix_gain["diff"])
str_d = abs(struct_gain["diff"])
R["mixture_confounding"]["K8"] = {
    "comparable_to_descriptor_effect": bool(mix_d >= 0.5 * str_d and mix_gain["diff"] < 0),
    "fires": bool(mix_d >= 0.5 * str_d and mix_gain["diff"] < 0
                  and mix_gain["hi"] < 0),
    "rule": ("K8 fires if mixture identity improves on MASS FLEX with the "
             "scaffold-level interval excluding zero AND its gain is at least "
             "half the descriptor gain"),
}

# ===========================================================================
# 3. Negative mode -- bounded scope
# ===========================================================================
tr_all = pd.read_parquet(ART / "trajectories.parquet")
b = tr_all[tr_all.is_base_cell]
neg = b[b.ion_mode_raw.str.upper() == "NEGATIVE"].copy()
agg = {c: "mean" for c in ("mu", "precursor_mz", "retention_time_min")}
agg["smiles_raw"] = "first"
agg["inchikey_first_block"] = "first"
n = neg.groupby(["group_key", "ce_numeric"], as_index=False).agg(agg)
cov = n.groupby("group_key").ce_numeric.nunique()
n = n[n.group_key.isin(cov[cov >= 5].index)].copy()

ncmp = n.drop_duplicates("group_key")[["group_key", "smiles_raw",
                                       "inchikey_first_block"]].copy()
ncmp["scaffold_group"] = [scaffold_group(s, k) for s, k
                          in zip(ncmp.smiles_raw, ncmp.inchikey_first_block)]
ncmp["cluster_group"] = ["C" + str(c) for c in
                         butina_clusters(ncmp.smiles_raw.tolist(), 0.6)]
desc = pd.DataFrame([{"group_key": r.group_key, **tier_a_descriptors(r.smiles_raw)}
                     for r in ncmp.itertuples()])
n = (n.merge(ncmp[["group_key", "scaffold_group", "cluster_group"]], on="group_key")
     .merge(desc, on="group_key"))
n["fold_S2"] = make_split(n, "scaffold_group", "S2neg", 5, SEED)

nce = {}
for name, sp in (("B1", Spec("B1", PerEnergyMean)),
                 ("MASS_FLEX", specs["MASS_FLEX"]),
                 ("TIER_A", specs["TIER_A"])):
    p = nested_cv(n, sp, "fold_S2", inner_folds=4, seed=SEED)
    nce[name] = compound_errors(p)

nscaf = n.drop_duplicates("inchikey_first_block").set_index(
    "inchikey_first_block").scaffold_group
k4a_neg = bootstrap_paired(nce["TIER_A"], nce["B1"], nscaf, N_BOOT, SEED)
k4b_neg = bootstrap_paired(nce["TIER_A"], nce["MASS_FLEX"], nscaf, N_BOOT, SEED)

R["negative_mode"] = {
    "scope": ("bounded by instruction 24: K4A/K4B under S2 only, as a "
              "qualitative replication check. The primary Phase 2 experiment "
              "remains positive mode."),
    "n_compounds": int(n.group_key.nunique()),
    "n_rows": int(len(n)),
    "repeatability": ("UNKNOWN -- no negative-mode mzML was acquired (Phase 1 "
                      "issue I2). No claim requiring a negative-mode noise "
                      "estimate is made."),
    "mae": {k: round(float(v.mae.mean()), 5) for k, v in nce.items()},
    "K4A_tier_a_vs_B1": {
        "mae_diff": round(k4a_neg["diff"], 5),
        "ci_scaffold": [round(k4a_neg["lo"], 5), round(k4a_neg["hi"], 5)],
        "pass": bool(k4a_neg["diff"] < 0 and k4a_neg["hi"] < 0)},
    "K4B_tier_a_vs_MASS_FLEX": {
        "mae_diff": round(k4b_neg["diff"], 5),
        "ci_scaffold": [round(k4b_neg["lo"], 5), round(k4b_neg["hi"], 5)],
        "rel_reduction_pct": round(
            -100 * k4b_neg["diff"] / float(nce["MASS_FLEX"].mae.mean()), 2),
        "pass": bool(k4b_neg["diff"] < 0 and k4b_neg["hi"] < 0
                     and -100 * k4b_neg["diff"] / float(nce["MASS_FLEX"].mae.mean()) >= 5.0)},
}

(ART / "p2_robustness.json").write_text(json.dumps(R, indent=2, default=str))
print(json.dumps(R, indent=2, default=str))
