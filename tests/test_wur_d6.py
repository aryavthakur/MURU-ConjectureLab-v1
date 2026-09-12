import pandas as pd

from muru.io.wur_partition import (
    apply_d6, build_dev_neg_keys, partition, sealed_scaffold_groups,
)


def _partitioned():
    """POS: one dev group, one sealed group. NEG: one row in a scaffold group
    that is sealed on the POS side, one row in a group that is not."""
    pos = pd.DataFrame({
        "connectivity_key": ["PDEV", "PSEAL"],
        "scaffold_group": ["gdev", "gseal"],
        "side": ["WUR-DEV", "WUR-SEALED"],
    })
    neg = pd.DataFrame({
        "connectivity_key": ["NOVERLAP", "NFREE"],
        "scaffold_group": ["gseal", "gneg"],
        "side": ["WUR-DEV", "WUR-DEV"],
    })
    return {"POS": pos, "NEG": neg}


def test_sealed_scaffold_groups_reads_the_pos_sealed_side():
    assert sealed_scaffold_groups(_partitioned()["POS"]) == {"gseal"}


def test_d6_excludes_a_neg_dev_row_in_a_sealed_pos_scaffold_group():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    neg = out["NEG"].set_index("connectivity_key")["side"]
    assert neg["NOVERLAP"] == "EXCLUDED"
    assert neg["NFREE"] == "WUR-DEV"


def test_d6_never_relabels_a_sealed_row():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    pos = out["POS"].set_index("connectivity_key")["side"]
    assert pos["PSEAL"] == "WUR-SEALED"
    assert pos["PDEV"] == "WUR-DEV"


def test_d6_leaves_the_pos_sealed_key_list_identical():
    part = _partitioned()
    before = sorted(part["POS"].loc[part["POS"]["side"] == "WUR-SEALED",
                                    "connectivity_key"])
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    after = sorted(out["POS"].loc[out["POS"]["side"] == "WUR-SEALED",
                                   "connectivity_key"])
    assert before == after


def test_d6_is_a_no_op_on_pos():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    pd.testing.assert_series_equal(
        part["POS"].set_index("connectivity_key")["side"].sort_index(),
        out["POS"].set_index("connectivity_key")["side"].sort_index(),
    )


def test_d6_is_idempotent():
    part = _partitioned()
    groups = sealed_scaffold_groups(part["POS"])
    once = apply_d6(part, groups)
    twice = apply_d6(once, sealed_scaffold_groups(once["POS"]))
    for polarity in ("POS", "NEG"):
        pd.testing.assert_frame_equal(
            once[polarity].sort_values("connectivity_key").reset_index(drop=True),
            twice[polarity].sort_values("connectivity_key").reset_index(drop=True),
        )


def test_after_d6_no_dev_row_in_either_polarity_is_in_a_sealed_group():
    part = _partitioned()
    groups = sealed_scaffold_groups(part["POS"])
    out = apply_d6(part, groups)
    for polarity in ("POS", "NEG"):
        dev = out[polarity][out[polarity]["side"] == "WUR-DEV"]
        assert not (set(dev["scaffold_group"]) & groups)


def test_sides_still_account_for_every_row_in_each_polarity():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    for polarity in ("POS", "NEG"):
        df = out[polarity]
        counts = df["side"].value_counts()
        total = (counts.get("WUR-DEV", 0) + counts.get("WUR-SEALED", 0)
                 + counts.get("EXCLUDED", 0))
        assert total == len(part[polarity])


def test_build_dev_neg_keys_lists_only_post_d6_dev_keys():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    listing = build_dev_neg_keys(out["NEG"])
    assert listing["connectivity_keys"] == ["NFREE"]
    assert listing["n_compounds"] == 1


def test_d6_runs_on_a_real_shaped_partition_without_touching_free_groups():
    pos = pd.DataFrame({
        "connectivity_key": [f"K{i}" for i in range(20)],
        "scaffold_group": [f"g{i}" for i in range(20)],
        "in_lcsb_dev": [False] * 20,
        "in_lcsb_sealed": [False] * 20,
    })
    neg = pd.DataFrame({
        "connectivity_key": ["N0"], "scaffold_group": ["ng0"],
        "in_lcsb_dev": [False], "in_lcsb_sealed": [False],
    })
    part = partition({"POS": pos, "NEG": neg})
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    assert (out["NEG"]["side"] == "WUR-DEV").all()
