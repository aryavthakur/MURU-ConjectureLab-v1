import pandas as pd

from muru.io.wur_partition import (
    SEED, assign_side_by_group, check_sealed_floor, partition,
)


def _toy_pos(n_free_groups=40):
    rows = []
    for g in range(2):
        rows.append({"connectivity_key": f"DEV{g}", "scaffold_group": f"devgrp{g}",
                     "in_lcsb_dev": True, "in_lcsb_sealed": False})
    rows.append({"connectivity_key": "BOTH0", "scaffold_group": "bothgrp",
                 "in_lcsb_dev": True, "in_lcsb_sealed": True})
    for g in range(n_free_groups):
        rows.append({"connectivity_key": f"FREE{g}", "scaffold_group": f"free{g}",
                     "in_lcsb_dev": False, "in_lcsb_sealed": False})
    return pd.DataFrame(rows)


def test_group_touching_dev_goes_to_wur_dev():
    df = assign_side_by_group(_toy_pos())
    assert (df.loc[df["scaffold_group"] == "devgrp0", "side"] == "WUR-DEV").all()


def test_group_touching_both_dev_and_sealed_goes_to_sealed_d3_beats_d2():
    df = assign_side_by_group(_toy_pos())
    assert (df.loc[df["scaffold_group"] == "bothgrp", "side"] == "WUR-SEALED").all()


def test_free_groups_split_roughly_in_half():
    df = assign_side_by_group(_toy_pos(n_free_groups=40))
    free = df[df["scaffold_group"].str.startswith("free")]
    counts = free.groupby("side")["scaffold_group"].nunique()
    assert abs(counts.get("WUR-DEV", 0) - counts.get("WUR-SEALED", 0)) <= 1


def test_free_group_split_is_deterministic_at_fixed_seed():
    df1 = assign_side_by_group(_toy_pos(), seed=SEED)
    df2 = assign_side_by_group(_toy_pos(), seed=SEED)
    pd.testing.assert_series_equal(
        df1.set_index("connectivity_key")["side"].sort_index(),
        df2.set_index("connectivity_key")["side"].sort_index(),
    )


def test_a_scaffold_group_never_splits_across_sides():
    df = assign_side_by_group(_toy_pos(n_free_groups=60))
    per_group_sides = df.groupby("scaffold_group")["side"].nunique()
    assert (per_group_sides == 1).all()


def test_check_sealed_floor_reports_pass_and_fail():
    passing = pd.DataFrame({"scaffold_group": [f"g{i}" for i in range(150)] * 2})
    result = check_sealed_floor(passing)
    assert result["n_trajectories"] == 300
    assert result["passes_trajectory_floor"] is True
    assert result["passes_scaffold_group_floor"] is True

    failing = pd.DataFrame({"scaffold_group": ["g0"] * 10})
    assert check_sealed_floor(failing)["passes_trajectory_floor"] is False


def test_negative_mode_is_entirely_wur_dev_even_if_it_touches_sealed():
    annotated = {
        "POS": _toy_pos(),
        "NEG": pd.DataFrame({
            "connectivity_key": ["N0", "N1"], "scaffold_group": ["ng0", "ng1"],
            "in_lcsb_dev": [False, False], "in_lcsb_sealed": [False, True],
        }),
    }
    result = partition(annotated)
    assert (result["NEG"]["side"] == "WUR-DEV").all()
