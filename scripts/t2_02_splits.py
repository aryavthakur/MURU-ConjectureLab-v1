"""Phase 2 splits: scaffold audit, similarity clustering, confirmation seal, S0-S3.

Runs before the pre-registration is committed, because the pre-registration must
record the sealed confirmation-set hash and the split definitions. Uses molecular
structure only; no endpoint value is read here.

Writes:
  artifacts/p2_compounds.parquet          per-compound structure keys
  artifacts/confirmation_set_sealed.json  SEALED. Do not open in Phase 2.
  artifacts/p2_splits.parquet             fold assignments on the development set
  artifacts/p2_split_audit.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.molecules import butina_clusters, murcko_scaffold, scaffold_group
from muru.splits import (CONNECTIVITY_KEY, assert_group_disjoint,
                         make_leaked_split, make_split)

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
SEED = 20260811
N_FOLDS = 5
CONFIRMATION_FRACTION = 0.20
SIMILARITY_THRESHOLD = 0.6

A: dict = {}

dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")

cmpd = (dev.groupby("group_key")
        .agg(inchikey_first_block=("inchikey_first_block", "first"),
             smiles=("smiles_raw", "first"),
             mix=("mix", "first"),
             precursor_mz=("precursor_mz", "first"),
             n_energies=("ce_numeric", "nunique"))
        .reset_index())

cmpd["murcko"] = [murcko_scaffold(s) for s in cmpd.smiles]
cmpd["scaffold_group"] = [scaffold_group(s, k) for s, k
                          in zip(cmpd.smiles, cmpd.inchikey_first_block)]
cmpd["is_acyclic"] = cmpd.murcko == ""
cmpd["cluster"] = butina_clusters(cmpd.smiles.tolist(), SIMILARITY_THRESHOLD)
cmpd["cluster_group"] = "C" + cmpd.cluster.astype(str)

# ---------------------------------------------------------------------------
# Scaffold audit (instruction 4) -- reported before S2 is accepted
# ---------------------------------------------------------------------------
sg = cmpd.scaffold_group.value_counts()
murcko_nonempty = cmpd[~cmpd.is_acyclic].murcko.value_counts()
A["n_compounds"] = int(len(cmpd))
A["scaffold"] = {
    "n_unique_murcko_nonempty": int(murcko_nonempty.size),
    "n_acyclic_empty_murcko": int(cmpd.is_acyclic.sum()),
    "frac_acyclic": round(float(cmpd.is_acyclic.mean()), 4),
    "n_scaffold_groups_after_policy": int(sg.size),
    "n_singleton_groups": int((sg == 1).sum()),
    "frac_compounds_in_singletons": round(float((sg == 1).sum() / len(cmpd)), 4),
    "largest_groups": [{"scaffold": s, "n": int(n)} for s, n in sg.head(10).items()],
    "group_size_distribution": {str(k): int(v) for k, v
                                in sg.value_counts().sort_index().items()},
    "max_group_frac_of_corpus": round(float(sg.max() / len(cmpd)), 4),
    "ringless_policy": ("each acyclic compound is its own scaffold group, keyed "
                        "by connectivity block; see MASTER_PLAN_CLARIFICATIONS C5"),
}

cl = cmpd.cluster_group.value_counts()
A["cluster"] = {
    "similarity_threshold": SIMILARITY_THRESHOLD,
    "distance_cutoff_used": 1 - SIMILARITY_THRESHOLD,
    "n_clusters": int(cl.size),
    "n_singleton_clusters": int((cl == 1).sum()),
    "frac_compounds_in_singletons": round(float((cl == 1).sum() / len(cmpd)), 4),
    "largest_clusters": [int(n) for n in cl.head(10)],
    "cluster_size_distribution": {str(k): int(v) for k, v
                                  in cl.value_counts().sort_index().items()},
    "max_cluster_frac_of_corpus": round(float(cl.max() / len(cmpd)), 4),
}

# S2 acceptance judgement, recorded before any performance is seen
A["s2_verdict"] = {
    "pathological": bool(sg.max() / len(cmpd) > 0.35 or sg.size < 30),
    "reason": (f"{int(sg.size)} scaffold groups over {len(cmpd)} compounds; "
               f"largest group holds {sg.max()} ({100*sg.max()/len(cmpd):.1f}%). "
               "Neither degenerate nor dominated, so S2 is meaningful for this "
               "corpus and is pre-registered as the primary split."),
}

# ---------------------------------------------------------------------------
# Confirmation set: sealed by SCAFFOLD GROUP, before any model exists
# ---------------------------------------------------------------------------
rng = np.random.default_rng(SEED)
groups = sg.index.to_numpy()
order = rng.permutation(len(groups))
target = int(round(CONFIRMATION_FRACTION * len(cmpd)))

# Selection rule: walk scaffold groups in seeded random order and take each one
# unless it would push the confirmation set past 115% of the 20% target. The
# tolerance exists because group sizes are very uneven -- the benzene group
# alone is 14.6% of the corpus -- so a plain "add until >= target" loop
# overshoots badly. The rule keeps every group eligible (80 < 1.15 * 110) rather
# than systematically excluding the large ones, which would leave the
# confirmation set unrepresentative of the corpus's commonest chemistry.
CONFIRMATION_TOLERANCE = 1.15
chosen, n_sel = [], 0
for gi in order:
    g = groups[gi]
    if n_sel >= target:
        break
    if n_sel + int(sg[g]) > target * CONFIRMATION_TOLERANCE:
        continue
    chosen.append(g)
    n_sel += int(sg[g])

conf_mask = cmpd.scaffold_group.isin(chosen)
conf = cmpd[conf_mask]
devset = cmpd[~conf_mask]

seal = {
    "purpose": "SEALED Phase 2 confirmation set. Do not open during Phase 2.",
    "constructed_utc": pd.Timestamp.now("UTC").isoformat(),
    "seed": SEED,
    "selection_unit": "bemis_murcko_scaffold_group",
    "target_fraction": CONFIRMATION_FRACTION,
    "n_scaffold_groups": len(chosen),
    "n_compounds": int(len(conf)),
    "frac_compounds": round(float(len(conf) / len(cmpd)), 4),
    "connectivity_keys": sorted(conf[CONNECTIVITY_KEY].tolist()),
    "disclosure": (
        "These compounds were excluded from Phase 2 model fitting, "
        "hyperparameter tuning, candidate selection and threshold adaptation. "
        "They are NOT unseen with respect to all study design: the Phase 1 "
        "audit selected the primary endpoint mu using the full positive-mode "
        "corpus, which included these compounds. See PREREGISTRATION.md."),
}
seal_path = ART / "confirmation_set_sealed.json"
seal_path.write_text(json.dumps(seal, indent=2))
seal_hash = hashlib.sha256(seal_path.read_bytes()).hexdigest()
A["confirmation"] = {
    "n_compounds": int(len(conf)), "n_scaffold_groups": len(chosen),
    "frac": round(float(len(conf) / len(cmpd)), 4),
    "sha256": seal_hash,
    "development_n_compounds": int(len(devset)),
}

# ---------------------------------------------------------------------------
# Splits, on the DEVELOPMENT corpus only
# ---------------------------------------------------------------------------
d = dev.merge(devset[["group_key", "scaffold_group", "cluster_group"]],
              on="group_key", how="inner")

d["fold_S1"] = make_split(d, CONNECTIVITY_KEY, "S1", N_FOLDS, SEED)
d["fold_S2"] = make_split(d, "scaffold_group", "S2", N_FOLDS, SEED)
d["fold_S3"] = make_split(d, "cluster_group", "S3", N_FOLDS, SEED)
d["fold_S0"] = make_leaked_split(d, N_FOLDS, SEED)

for s in ("S1", "S2", "S3"):
    assert_group_disjoint(d, f"fold_{s}")
assert not set(d[CONNECTIVITY_KEY]) & set(conf[CONNECTIVITY_KEY]), \
    "confirmation compounds leaked into the development corpus"

leak_per_cpd = d.groupby(CONNECTIVITY_KEY).fold_S0.nunique()
A["splits"] = {
    "n_folds": N_FOLDS,
    "development_rows": int(len(d)),
    "development_compounds": int(d[CONNECTIVITY_KEY].nunique()),
    "fold_sizes": {s: d.groupby(f"fold_{s}").size().to_dict()
                   for s in ("S1", "S2", "S3", "S0")},
    "fold_compound_counts": {
        s: d.groupby(f"fold_{s}")[CONNECTIVITY_KEY].nunique().to_dict()
        for s in ("S1", "S2", "S3")},
    "S0_frac_compounds_split_across_folds": round(float((leak_per_cpd > 1).mean()), 4),
}

d.to_parquet(ART / "p2_splits.parquet", index=False)
cmpd.assign(in_confirmation=conf_mask).to_parquet(ART / "p2_compounds.parquet",
                                                  index=False)
(ART / "p2_split_audit.json").write_text(json.dumps(A, indent=2, default=str))

print(json.dumps(A, indent=2, default=str)[:4000])
