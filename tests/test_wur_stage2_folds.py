import pandas as pd
import pytest

from muru.wur_stage2 import folds as FO


def _frame(n=200):
    return pd.DataFrame({"group_key": [f"K{i}" for i in range(n)],
                         "scaffold_group": [f"S{i % 37}" if i % 5 else "BIG" for i in range(n)]})


def test_folds_are_group_disjoint_deterministic_and_hashed():
    a = FO.build_folds(_frame()); b = FO.build_folds(_frame())
    assert a["folds_sha256"] == b["folds_sha256"] and len(a["repeats"]) == 3
    fr = _frame().set_index("group_key")
    for rep in a["repeats"]:
        s = pd.Series(rep["assignment"])
        assert s.groupby(fr.loc[s.index, "scaffold_group"].to_numpy()).nunique().max() == 1
        assert sum(rep["fold_sizes"]) == 200 and set(s.unique()) == set(range(5))
    assert a["repeats"][0]["assignment"] != a["repeats"][1]["assignment"]


def test_duplicate_compound_rejected():
    f = pd.concat([_frame(), _frame().iloc[[0]]])
    with pytest.raises(ValueError):
        FO.build_folds(f)


def test_largest_first_balancing_pins_a_dominant_group_to_fold0_in_every_repeat():
    # Documents the property the reviews found on DEV2B: a single scaffold group
    # larger than n/K is placed first and alone in fold 0 at every seed, so the
    # 15 (repeat, fold) held-out sets are not all distinct.
    n = 200
    frame = pd.DataFrame({"group_key": [f"K{i}" for i in range(n)],
                          "scaffold_group": ["BIG" if i < 60 else f"S{i}" for i in range(n)]})
    d = FO.build_folds(frame)
    for rep in d["repeats"]:
        a = pd.Series(rep["assignment"])
        assert set(frame.loc[frame.group_key.isin(a.index[a == 0]), "scaffold_group"]) == {"BIG"}
    assert FO.distinct_heldout_sets(d) == 13


def test_committed_dev2b_folds_have_13_distinct_heldout_sets():
    d = FO.load_folds()
    assert FO.distinct_heldout_sets(d) == 13
    with pytest.raises(ValueError):
        FO.load_folds(expected_population_sha256="0" * 64)
