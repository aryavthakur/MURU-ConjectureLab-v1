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
