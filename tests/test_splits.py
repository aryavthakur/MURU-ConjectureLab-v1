"""Split construction, leakage assertions, and the Butina similarity/distance check.

The Butina tests use synthetic bit vectors with hand-computed Tanimoto
similarities, so they pin the similarity-to-distance conversion independently
of RDKit's fingerprint generator and of any real molecule.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from rdkit import DataStructs
from rdkit.DataStructs.cDataStructs import ExplicitBitVect

from muru.molecules import (butina_clusters_from_fps, murcko_scaffold,
                            scaffold_group)
from muru.splits import (LeakageError, assert_group_disjoint,
                         assert_no_key_overlap, grouped_folds,
                         make_leaked_split, make_split)


# ---------------------------------------------------------------------------
# Synthetic fingerprints with known pairwise Tanimoto
# ---------------------------------------------------------------------------
def bv(nbits: int, on_bits: list[int]) -> ExplicitBitVect:
    v = ExplicitBitVect(nbits)
    for b in on_bits:
        v.SetBit(b)
    return v


def test_synthetic_tanimoto_is_what_we_think():
    """Sanity: the hand-computed similarities used below are correct."""
    a = bv(16, [0, 1, 2, 3, 4, 5, 6, 7])          # 8 bits
    b = bv(16, [0, 1, 2, 3, 4, 5, 6, 8])          # 7 shared, union 9 -> 7/9
    c = bv(16, [0, 1, 2, 3, 8, 9, 10, 11])        # 4 shared, union 12 -> 1/3
    assert DataStructs.TanimotoSimilarity(a, b) == pytest.approx(7 / 9)
    assert DataStructs.TanimotoSimilarity(a, c) == pytest.approx(1 / 3)


def test_butina_groups_pair_above_similarity_threshold():
    """Similarity 7/9 = 0.778 >= 0.6 -> same cluster."""
    a = bv(16, [0, 1, 2, 3, 4, 5, 6, 7])
    b = bv(16, [0, 1, 2, 3, 4, 5, 6, 8])
    labels = butina_clusters_from_fps([a, b], similarity_threshold=0.6)
    assert labels[0] == labels[1]


def test_butina_separates_pair_below_similarity_threshold():
    """Similarity 1/3 = 0.333 < 0.6 -> different clusters."""
    a = bv(16, [0, 1, 2, 3, 4, 5, 6, 7])
    c = bv(16, [0, 1, 2, 3, 8, 9, 10, 11])
    labels = butina_clusters_from_fps([a, c], similarity_threshold=0.6)
    assert labels[0] != labels[1]


def test_butina_threshold_is_similarity_not_distance():
    """The bug this guards against.

    A pair at Tanimoto similarity 0.5 lies BELOW a 0.6 similarity threshold and
    must be separated. If the threshold were passed to RDKit as a distance
    cutoff (0.6) instead of being converted to 1 - 0.6 = 0.4, the pair's
    distance of 0.5 would fall under it and they would be merged.
    """
    a = bv(16, [0, 1, 2, 3, 4, 5])
    b = bv(16, [0, 1, 2, 3, 6, 7, 8, 9])   # 4 shared, union 10 -> 0.4? check
    # exact: |A|=6, |B|=8, shared=4, union=10 -> 0.4 similarity, 0.6 distance
    assert DataStructs.TanimotoSimilarity(a, b) == pytest.approx(0.4)
    labels = butina_clusters_from_fps([a, b], similarity_threshold=0.6)
    assert labels[0] != labels[1], (
        "pair at similarity 0.4 was merged under a 0.6 similarity threshold; "
        "the threshold is being used as a distance cutoff")


def test_butina_similarity_one_only_merges_identical():
    a = bv(16, [0, 1, 2, 3])
    b = bv(16, [0, 1, 2, 3])
    c = bv(16, [0, 1, 2, 4])
    labels = butina_clusters_from_fps([a, b, c], similarity_threshold=1.0)
    assert labels[0] == labels[1]
    assert labels[2] != labels[0]


def test_butina_rejects_out_of_range_threshold():
    a = bv(16, [0, 1])
    with pytest.raises(ValueError):
        butina_clusters_from_fps([a], similarity_threshold=1.5)


# ---------------------------------------------------------------------------
# Scaffold policy
# ---------------------------------------------------------------------------
def test_ringless_molecule_has_empty_murcko_scaffold():
    assert murcko_scaffold("CCCCO") == ""


def test_ringless_molecules_are_not_pooled_into_one_group():
    """MASTER_PLAN_CLARIFICATIONS.md C5: each acyclic compound is its own group."""
    g1 = scaffold_group("CCCCO", "AAAAAAAAAAAAAA")
    g2 = scaffold_group("CCCCCCN", "BBBBBBBBBBBBBB")
    assert g1 != g2
    assert g1.startswith("__ACYCLIC__")


def test_ring_molecules_share_a_scaffold_group():
    a = scaffold_group("c1ccccc1C", "AAAAAAAAAAAAAA")
    b = scaffold_group("c1ccccc1CC", "BBBBBBBBBBBBBB")
    assert a == b == "c1ccccc1"


# ---------------------------------------------------------------------------
# Split disjointness
# ---------------------------------------------------------------------------
def _toy(n_cpd: int = 40, n_energy: int = 6) -> pd.DataFrame:
    return pd.DataFrame({
        "inchikey_first_block": np.repeat([f"K{i:04d}" for i in range(n_cpd)],
                                          n_energy),
        "scaffold_group": np.repeat([f"S{i % 7}" for i in range(n_cpd)], n_energy),
        "ce_numeric": np.tile([15, 30, 45, 60, 75, 90], n_cpd),
    })


def test_make_split_is_connectivity_disjoint():
    df = _toy()
    df["fold"] = make_split(df, "scaffold_group", "S2")
    assert_group_disjoint(df, "fold")
    assert_group_disjoint(df, "fold", key_col="scaffold_group")


def test_all_energies_of_a_molecule_stay_together():
    df = _toy()
    df["fold"] = make_split(df, "scaffold_group", "S2")
    per = df.groupby("inchikey_first_block").fold.nunique()
    assert (per == 1).all()


def test_assert_group_disjoint_detects_a_planted_violation():
    df = _toy()
    df["fold"] = make_split(df, "scaffold_group", "S2")
    victim = df.index[0]
    df.loc[victim, "fold"] = (df.loc[victim, "fold"] + 1) % 5
    with pytest.raises(LeakageError):
        assert_group_disjoint(df, "fold")


def test_assert_no_key_overlap_detects_shared_compound():
    df = _toy()
    train, test = df.iloc[:120], df.iloc[100:]
    with pytest.raises(LeakageError):
        assert_no_key_overlap(train, test)


def test_leaked_split_actually_leaks():
    """S0 must split rows, not molecules -- otherwise the canary tests nothing."""
    df = _toy()
    df["fold"] = make_leaked_split(df)
    per = df.groupby("inchikey_first_block").fold.nunique()
    assert (per > 1).mean() > 0.9, (
        "S0 did not place a molecule's energies on both sides of the wall, so "
        "it cannot expose the leakage mechanism it exists to demonstrate")


def test_grouped_folds_balances_row_load_despite_uneven_groups():
    """One dominant group must not swamp a single fold."""
    groups = pd.Series(["BIG"] * 80 + [f"S{i}" for i in range(200)])
    folds = grouped_folds(groups, n_folds=5)
    load = folds.value_counts()
    assert load.max() / load.min() < 2.0


def test_grouped_folds_is_deterministic():
    groups = pd.Series([f"S{i % 30}" for i in range(300)])
    a = grouped_folds(groups, n_folds=5, seed=7)
    b = grouped_folds(groups, n_folds=5, seed=7)
    assert a.equals(b)
