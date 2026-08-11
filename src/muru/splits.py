"""Evaluation splits S0-S3, with disjointness enforced by assertion.

The connectivity key is the InChIKey first block. Every collision energy of a
molecule, and every internal MassBank ID sharing that connectivity, moves
together across every split except the deliberately leaked S0 diagnostic.

Disjointness is asserted, never inspected (Phase 2 instruction 4).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CONNECTIVITY_KEY = "inchikey_first_block"


class LeakageError(AssertionError):
    """Raised when a molecular connectivity crosses an evaluation boundary."""


def assert_group_disjoint(df: pd.DataFrame, fold_col: str,
                          key_col: str = CONNECTIVITY_KEY) -> None:
    """Every connectivity key must live in exactly one fold."""
    spread = df.groupby(key_col)[fold_col].nunique()
    bad = spread[spread > 1]
    if len(bad):
        raise LeakageError(
            f"{len(bad)} connectivity keys span multiple {fold_col} folds: "
            f"{list(bad.index[:5])}")


def assert_no_key_overlap(train: pd.DataFrame, test: pd.DataFrame,
                          key_col: str = CONNECTIVITY_KEY) -> None:
    """Train and test must share no connectivity key."""
    overlap = set(train[key_col]) & set(test[key_col])
    if overlap:
        raise LeakageError(
            f"{len(overlap)} connectivity keys in both train and test: "
            f"{sorted(overlap)[:5]}")


def grouped_folds(group_ids: pd.Series, n_folds: int = 5,
                  seed: int = 20260811) -> pd.Series:
    """Assign folds to groups, balancing fold SIZE in rows.

    ``GroupKFold`` balances group counts; here group sizes are very uneven (one
    scaffold holds 80 compounds, 290 hold one each), so folds are filled
    greedily largest-group-first into whichever fold is currently smallest.
    That keeps a single large scaffold from dominating one fold's row count.
    Ties are broken by a seeded permutation so the assignment is reproducible
    but not alphabetical.
    """
    counts = group_ids.value_counts()
    rng = np.random.default_rng(seed)
    order = pd.Series(rng.permutation(len(counts)), index=counts.index)
    ordered = (pd.DataFrame({"n": counts, "tie": order})
               .sort_values(["n", "tie"], ascending=[False, True]).index)

    load = np.zeros(n_folds, dtype=int)
    assign: dict[str, int] = {}
    for g in ordered:
        f = int(np.argmin(load))
        assign[g] = f
        load[f] += int(counts[g])
    return group_ids.map(assign)


def make_split(df: pd.DataFrame, group_col: str, name: str,
               n_folds: int = 5, seed: int = 20260811) -> pd.Series:
    """Build a grouped split and assert it is leakage-free."""
    folds = grouped_folds(df[group_col], n_folds=n_folds, seed=seed)
    check = df.assign(**{f"_fold_{name}": folds})
    assert_group_disjoint(check, f"_fold_{name}", key_col=group_col)
    assert_group_disjoint(check, f"_fold_{name}", key_col=CONNECTIVITY_KEY)
    return folds


def make_leaked_split(df: pd.DataFrame, n_folds: int = 5,
                      seed: int = 20260811) -> pd.Series:
    """S0: the deliberately leaked diagnostic.

    Assigns folds per ROW (one compound-energy observation), so the six
    energies of a molecule land on both sides of the wall. This is the trivial
    failure mode the project files warn about. It is a diagnostic that measures
    the size of the leakage gap and is NEVER reported as scientific
    performance.
    """
    rng = np.random.default_rng(seed)
    return pd.Series(rng.integers(0, n_folds, size=len(df)), index=df.index)
