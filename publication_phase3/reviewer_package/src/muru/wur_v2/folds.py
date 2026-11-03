"""v2 grouped partitions (protocol section 4). Identity only.

PRIMARY: one 5-fold partition of whole stereo-free scaffold groups, largest
group first into the currently smallest fold (`muru.splits.grouped_folds`),
seed 20260920. Every compound is held out exactly once and the primary
metric is computed on the pooled out-of-fold predictions.

PARTITION_SENSITIVITY: the same rule at seeds 20260921 and 20260922 (tie
order only; the benzene group is whole in every partition).

STRICT: 5 folds of whole strict structural clusters, seed 20260923.

GIANT: leave-benzene-group-out (train on everything else, score the 183
benzene-scaffold compounds).

RANDOM: compound-level 5-fold, seed 20260924, a leakage diagnostic only.

Inner folds: 4 grouped folds of the same grouping column inside a training
set, seed 20260930 + outer fold.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from muru.splits import grouped_folds

K = 5
INNER_K = 4
PRIMARY_SEED = 20260920
SENSITIVITY_SEEDS = (20260921, 20260922)
STRICT_SEED = 20260923
RANDOM_SEED = 20260924
INNER_SEED_BASE = 20260930
GIANT_GROUP = "c1ccccc1"


def assignment_hash(assign: pd.Series) -> str:
    payload = json.dumps(sorted((str(k), int(v)) for k, v in assign.items()))
    return hashlib.sha256(payload.encode()).hexdigest()


def grouped(cov: pd.DataFrame, col: str, seed: int, k: int = K) -> pd.Series:
    f = grouped_folds(cov[col].reset_index(drop=True), n_folds=k, seed=seed)
    out = pd.Series(f.to_numpy(), index=cov["group_key"].to_numpy(), name="fold")
    check_disjoint(cov, out, col)
    return out


def random_folds(cov: pd.DataFrame, seed: int = RANDOM_SEED, k: int = K) -> pd.Series:
    rng = np.random.default_rng(seed)
    f = np.arange(len(cov)) % k
    rng.shuffle(f)
    return pd.Series(f, index=cov["group_key"].to_numpy(), name="fold")


def check_disjoint(cov: pd.DataFrame, assign: pd.Series, col: str) -> None:
    g = cov.set_index("group_key")[col]
    per = pd.DataFrame({"g": g.loc[assign.index].to_numpy(), "f": assign.to_numpy()}).groupby("g")["f"].nunique()
    if (per > 1).any():
        raise ValueError(f"group column {col} straddles folds: {per[per > 1].index[:5].tolist()}")
    if assign.index.duplicated().any():
        raise ValueError("a compound appears twice in the assignment")


def inner_folds(train_cov: pd.DataFrame, col: str, outer_fold: int) -> np.ndarray:
    f = grouped_folds(train_cov[col].reset_index(drop=True), n_folds=INNER_K, seed=INNER_SEED_BASE + outer_fold)
    return f.to_numpy()


def all_partitions(cov: pd.DataFrame) -> dict:
    parts = {"PRIMARY": grouped(cov, "scaffold_group", PRIMARY_SEED)}
    for i, s in enumerate(SENSITIVITY_SEEDS):
        parts[f"PARTITION_S{i + 1}"] = grouped(cov, "scaffold_group", s)
    parts["STRICT"] = grouped(cov, "strict_cluster", STRICT_SEED)
    parts["RANDOM"] = random_folds(cov)
    giant = (cov["scaffold_group"] == GIANT_GROUP).to_numpy()
    parts["GIANT"] = pd.Series(np.where(giant, 0, 1), index=cov["group_key"].to_numpy(), name="fold")
    return parts
