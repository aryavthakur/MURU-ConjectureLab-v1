"""Phase 2 pre-registration diagnostics (non-outcome).

Everything here runs BEFORE PREREGISTRATION.md is frozen and BEFORE any
outcome model is fitted. It answers the questions the pre-registration cannot
be written without:

  - Is Bemis-Murcko scaffolding pathological on this corpus? (instruction 4)
  - Are the draft Tier A descriptors computable, non-degenerate, non-redundant?
    (instruction 6)
  - What is the empirical support and variance structure of mu, so the
    likelihood is chosen on evidence rather than prestige? (instruction 13)

It deliberately computes NO model performance and NO endpoint-vs-descriptor
association. Descriptor/endpoint relationships are outcome analysis and belong
after the freeze.

Writes: artifacts/p2_dev_corpus.parquet, artifacts/p2_descriptors_tierA.parquet,
        artifacts/p2_prereg_diagnostics.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
ENERGIES = [15, 30, 45, 60, 75, 90]

D: dict = {}


# --------------------------------------------------------------------------
# Development corpus
# --------------------------------------------------------------------------
def build_corpus() -> pd.DataFrame:
    tr = pd.read_parquet(ART / "trajectories.parquet")
    base = tr[tr.is_base_cell]
    pos = base[base.ion_mode_raw.str.upper() == "POSITIVE"].copy()

    # One row per (compound, energy). The six duplicated compound-by-mode keys
    # documented in DATA_CENSUS.md (M1/D3) map to two internal IDs each; they
    # are averaged here so that a compound contributes one trajectory, not two
    # interleaved ones. Phase 1 left them interleaved, which is why its
    # monotone fractions are slightly conservative.
    dup = pos.groupby("group_key").size()
    D["duplicated_group_keys"] = sorted(dup[dup > len(ENERGIES)].index.tolist())

    num = ["mu", "survival_yield", "fragment_depth", "spectral_entropy",
           "normalized_entropy", "base_peak_fraction", "peak_count", "tic",
           "precursor_mz", "retention_time_min", "exact_mass"]
    agg = {c: "mean" for c in num}
    agg["smiles_raw"] = "first"
    agg["inchikey_recorded"] = "first"
    agg["dataset_raw"] = "first"
    agg["inchikey_first_block"] = "first"
    df = pos.groupby(["group_key", "ce_numeric"], as_index=False).agg(agg)

    cov = df.groupby("group_key").ce_numeric.nunique()
    D["positive_groups_total"] = int(cov.size)
    D["positive_groups_ge5"] = int((cov >= 5).sum())
    D["positive_groups_complete"] = int((cov == 6).sum())

    keep = cov[cov >= 5].index
    df = df[df.group_key.isin(keep)].copy()
    df["mix"] = df.dataset_raw.str.extract(r"(\d{3})$").astype(int)
    return df


dev = build_corpus()
D["modelling_rows"] = int(len(dev))
D["modelling_compounds"] = int(dev.group_key.nunique())

# --------------------------------------------------------------------------
# mu support and variance structure  (instruction 13)
# --------------------------------------------------------------------------
mu = dev.mu.to_numpy(float)
D["mu_support"] = {
    "min": float(np.nanmin(mu)), "max": float(np.nanmax(mu)),
    "n_nan": int(np.isnan(mu).sum()),
    "n_exactly_0": int((mu == 0).sum()), "n_exactly_1": int((mu == 1).sum()),
    "n_le_1e-6": int((mu <= 1e-6).sum()), "n_ge_1_minus_1e-6": int((mu >= 1 - 1e-6).sum()),
    "n_gt_1": int((mu > 1).sum()),
    "frac_in_open_01": float(((mu > 0) & (mu < 1)).mean()),
}
D["mu_by_energy"] = {
    int(e): {
        "n": int(g.mu.notna().sum()),
        "mean": float(g.mu.mean()), "sd": float(g.mu.std(ddof=1)),
        "min": float(g.mu.min()), "max": float(g.mu.max()),
        "q05": float(g.mu.quantile(.05)), "q95": float(g.mu.quantile(.95)),
        "skew": float(g.mu.skew()),
    }
    for e, g in dev.groupby("ce_numeric")
}
# heteroskedasticity: ratio of largest to smallest per-energy SD
sds = [v["sd"] for v in D["mu_by_energy"].values()]
D["mu_sd_ratio_max_over_min"] = float(max(sds) / min(sds))

# within-compound dependence: variance share between vs within compounds
gm = dev.groupby("group_key").mu.mean()
grand = dev.mu.mean()
n_i = dev.groupby("group_key").mu.size()
ss_between = float((n_i * (gm - grand) ** 2).sum())
ss_within = float(dev.groupby("group_key").mu.apply(
    lambda s: ((s - s.mean()) ** 2).sum()).sum())
D["mu_variance_share_between_compound_marginal"] = ss_between / (ss_between + ss_within)

# trajectory shape: is a logit-linear-in-energy form plausible?
eps = 1e-6
dev["mu_clip"] = dev.mu.clip(eps, 1 - eps)
dev["logit_mu"] = np.log(dev.mu_clip / (1 - dev.mu_clip))
shape = []
for k, g in dev[dev.group_key.isin(
        dev.groupby("group_key").ce_numeric.nunique().pipe(lambda s: s[s == 6]).index)
        ].groupby("group_key"):
    g = g.sort_values("ce_numeric")
    y = g.logit_mu.to_numpy()
    x = g.ce_numeric.to_numpy(float)
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    ss_tot = ((y - y.mean()) ** 2).sum()
    shape.append({"lin_r2": 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else np.nan,
                  "slope": b})
sh = pd.DataFrame(shape)
D["logit_linear_in_NCE_fit"] = {
    "n_complete": int(len(sh)),
    "median_r2": float(sh.lin_r2.median()),
    "q10_r2": float(sh.lin_r2.quantile(.10)),
    "frac_r2_below_0.9": float((sh.lin_r2 < 0.9).mean()),
    "median_slope": float(sh.slope.median()),
}
# same on log(NCE)
shape_l = []
for k, g in dev[dev.group_key.isin(
        dev.groupby("group_key").ce_numeric.nunique().pipe(lambda s: s[s == 6]).index)
        ].groupby("group_key"):
    g = g.sort_values("ce_numeric")
    y = g.logit_mu.to_numpy()
    x = np.log(g.ce_numeric.to_numpy(float))
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    ss_tot = ((y - y.mean()) ** 2).sum()
    shape_l.append(1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else np.nan)
D["logit_linear_in_logNCE_fit"] = {
    "median_r2": float(pd.Series(shape_l).median()),
    "frac_r2_below_0.9": float((pd.Series(shape_l) < 0.9).mean()),
}

# --------------------------------------------------------------------------
# Murcko scaffold audit  (instruction 4)
# --------------------------------------------------------------------------
cmpds = dev.groupby("group_key").agg(
    smiles=("smiles_raw", "first"),
    inchikey=("inchikey_first_block", "first"),
    mix=("mix", "first"),
).reset_index()

rows = []
for r in cmpds.itertuples():
    m = Chem.MolFromSmiles(r.smiles)
    if m is None:
        rows.append({"group_key": r.group_key, "mol_ok": False, "scaffold": None,
                     "scaffold_empty": None, "n_rings": None, "generic": None})
        continue
    sc = MurckoScaffold.GetScaffoldForMol(m)
    smi = Chem.MolToSmiles(sc) if sc is not None else ""
    gen = Chem.MolToSmiles(MurckoScaffold.MakeScaffoldGeneric(sc)) if smi else ""
    rows.append({
        "group_key": r.group_key, "mol_ok": True, "scaffold": smi,
        "scaffold_empty": (smi == ""),
        "n_rings": int(rdMolDescriptors.CalcNumRings(m)),
        "generic": gen,
    })
sc = pd.DataFrame(rows).merge(cmpds, on="group_key")

D["scaffold_audit"] = {
    "n_compounds": int(len(sc)),
    "n_mol_parse_failures": int((~sc.mol_ok).sum()),
    "n_unique_scaffolds_incl_empty": int(sc.scaffold.nunique(dropna=True)),
    "n_empty_scaffold": int(sc.scaffold_empty.fillna(False).sum()),
    "frac_empty_scaffold": float(sc.scaffold_empty.fillna(False).mean()),
    "n_ringless_molecules": int((sc.n_rings == 0).sum()),
}
nonempty = sc[~sc.scaffold_empty.fillna(True)]
vc = nonempty.scaffold.value_counts()
D["scaffold_audit"].update({
    "n_unique_scaffolds_nonempty": int(vc.size),
    "n_singleton_scaffolds": int((vc == 1).sum()),
    "frac_compounds_in_singleton_scaffolds": float(
        (vc[vc == 1].sum()) / len(sc)),
    "largest_scaffold_groups": [
        {"scaffold": s, "n": int(n)} for s, n in vc.head(12).items()],
    "scaffold_size_distribution": {str(k): int(v)
                                   for k, v in vc.value_counts().sort_index().items()},
    "max_scaffold_group_frac_of_corpus": float(vc.max() / len(sc)),
})

# --------------------------------------------------------------------------
# Tier A descriptor computability  (instruction 6)
# --------------------------------------------------------------------------
def tier_a(smiles: str) -> dict:
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return {}
    mh = Chem.AddHs(m)
    return {
        "heavy_atom_count": float(m.GetNumHeavyAtoms()),
        "total_atom_count": float(mh.GetNumAtoms()),
        "rotatable_bonds": float(rdMolDescriptors.CalcNumRotatableBonds(m)),
        "ring_count": float(rdMolDescriptors.CalcNumRings(m)),
        "aromatic_ring_count": float(rdMolDescriptors.CalcNumAromaticRings(m)),
        "rdbe": float(rdMolDescriptors.CalcNumRings(m)
                      + sum(b.GetBondTypeAsDouble() - 1 for b in m.GetBonds())),
        "tpsa": float(rdMolDescriptors.CalcTPSA(m)),
        "n_N": float(sum(a.GetSymbol() == "N" for a in m.GetAtoms())),
        "n_O": float(sum(a.GetSymbol() == "O" for a in m.GetAtoms())),
        "n_S": float(sum(a.GetSymbol() == "S" for a in m.GetAtoms())),
        "n_halogen": float(sum(a.GetSymbol() in ("F", "Cl", "Br", "I")
                               for a in m.GetAtoms())),
        "heteroatom_fraction": float(
            sum(a.GetSymbol() not in ("C", "H") for a in m.GetAtoms())
            / max(m.GetNumHeavyAtoms(), 1)),
        "labute_asa": float(Descriptors.LabuteASA(m)),
        "mol_wt": float(Descriptors.MolWt(m)),
    }


desc = pd.DataFrame([{"group_key": r.group_key, **tier_a(r.smiles)}
                     for r in cmpds.itertuples()])
desc = desc.merge(
    dev.groupby("group_key").agg(precursor_mz=("precursor_mz", "first"),
                                 exact_mass=("exact_mass", "first")).reset_index(),
    on="group_key")

cand = [c for c in desc.columns if c != "group_key"]
D["tier_a_candidates"] = {
    c: {
        "n_missing": int(desc[c].isna().sum()),
        "n_distinct": int(desc[c].nunique()),
        "min": float(desc[c].min()), "max": float(desc[c].max()),
        "median": float(desc[c].median()),
        "zero_variance": bool(desc[c].nunique() <= 1),
    } for c in cand
}
corr = desc[cand].corr(method="spearman")
D["tier_a_spearman_corr"] = {a: {b: round(float(corr.loc[a, b]), 3)
                                 for b in cand} for a in cand}
pairs = [(a, b, float(corr.loc[a, b])) for i, a in enumerate(cand)
         for b in cand[i + 1:] if abs(corr.loc[a, b]) >= 0.90]
D["tier_a_severe_collinearity_ge_0.90"] = [
    {"a": a, "b": b, "rho": round(r, 3)} for a, b, r in
    sorted(pairs, key=lambda t: -abs(t[2]))]

# --------------------------------------------------------------------------
# Mixture structure (for NC6 / K8 planning)
# --------------------------------------------------------------------------
D["mixture_distribution"] = {
    str(k): int(v) for k, v in cmpds.mix.value_counts().sort_index().items()}

# --------------------------------------------------------------------------
dev.to_parquet(ART / "p2_dev_corpus.parquet", index=False)
desc.to_parquet(ART / "p2_descriptors_tierA.parquet", index=False)
sc.to_parquet(ART / "p2_scaffolds.parquet", index=False)
(ART / "p2_prereg_diagnostics.json").write_text(json.dumps(D, indent=2))

print(json.dumps({k: v for k, v in D.items()
                  if k not in ("tier_a_spearman_corr", "tier_a_candidates")},
                 indent=2)[:6000])
