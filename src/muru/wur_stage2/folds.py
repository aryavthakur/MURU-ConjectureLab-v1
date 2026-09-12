"""Frozen Stage 2B folds: repeated scaffold-group K-fold on DEV2B."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from muru.io.wur_provenance import canonical_key_hash
from muru.splits import assert_group_disjoint, grouped_folds

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"
K = 5
REPEAT_SEEDS = (20260913, 20260914, 20260915)
INNER_K = 4
INNER_SEED_BASE = 20260916


def build_folds(frame: pd.DataFrame) -> dict:
    """`frame` has group_key and scaffold_group, one row per compound."""
    if frame["group_key"].duplicated().any():
        raise ValueError("one row per compound required")
    keys_sha = canonical_key_hash(sorted(frame["group_key"]))
    repeats = []
    for r, seed in enumerate(REPEAT_SEEDS):
        f = grouped_folds(frame["scaffold_group"], n_folds=K, seed=seed)
        chk = frame.assign(fold=f.to_numpy(), inchikey_first_block=frame["group_key"])
        assert_group_disjoint(chk, "fold", key_col="scaffold_group")
        assert_group_disjoint(chk, "fold", key_col="inchikey_first_block")
        assignment = dict(zip(frame["group_key"], (int(x) for x in f.to_numpy())))
        repeats.append({"repeat": r, "seed": seed, "assignment": assignment,
                        "fold_sizes": [int((f == k).sum()) for k in range(K)],
                        "fold_groups": [int(frame.loc[(f == k).to_numpy(), "scaffold_group"].nunique())
                                        for k in range(K)]})
    payload = {"k": K, "repeat_seeds": list(REPEAT_SEEDS), "inner_k": INNER_K,
               "inner_seed_base": INNER_SEED_BASE, "n_compounds": int(len(frame)),
               "n_scaffold_groups": int(frame["scaffold_group"].nunique()),
               "population_keys_sha256": keys_sha, "repeats": repeats}
    payload["folds_sha256"] = hashlib.sha256(json.dumps(
        [r["assignment"] for r in repeats], sort_keys=True).encode()).hexdigest()
    return payload


def load_folds() -> dict:
    d = json.loads((ART / "wur_stage2b" / "folds.json").read_text())
    recomputed = hashlib.sha256(json.dumps(
        [r["assignment"] for r in d["repeats"]], sort_keys=True).encode()).hexdigest()
    if recomputed != d["folds_sha256"]:
        raise ValueError("folds.json does not match its own hash")
    return d


def inner_folds(train_frame: pd.DataFrame, outer_fold: int) -> pd.Series:
    """Nested scaffold-group folds inside one training fold."""
    return grouped_folds(train_frame["scaffold_group"], n_folds=INNER_K,
                         seed=INNER_SEED_BASE + outer_fold)
