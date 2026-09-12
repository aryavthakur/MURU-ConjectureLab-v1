import numpy as np
import pandas as pd
import pytest

from muru.wur_stage2.holdout import (
    free_groups, reserve_internal_holdout,
)


def _dev(n_groups=40, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_groups):
        size = int(rng.integers(1, 5))
        touches = g % 4 == 0
        for k in range(size):
            rows.append({"connectivity_key": f"K{g:03d}{k}",
                         "scaffold_group": f"G{g:03d}",
                         "in_lcsb_dev": touches and k == 0,
                         "side": "WUR-DEV"})
    return pd.DataFrame(rows)


def test_free_groups_exclude_any_group_touching_lcsb_dev():
    dev = _dev()
    free = set(free_groups(dev))
    touching = set(dev.loc[dev.in_lcsb_dev, "scaffold_group"])
    assert not (free & touching)
    assert free | touching == set(dev.scaffold_group)


def test_holdout_is_group_disjoint_free_only_and_deterministic():
    dev = _dev()
    a = reserve_internal_holdout(dev, seed=7, fraction=0.4)
    b = reserve_internal_holdout(dev, seed=7, fraction=0.4)
    assert a == b
    hold = set(a["hold"]["connectivity_keys"])
    ana = set(a["analysis"]["connectivity_keys"])
    assert not (hold & ana)
    assert hold | ana == set(dev.connectivity_key)
    grp = dev.set_index("connectivity_key").scaffold_group
    assert not (set(grp.loc[list(hold)]) & set(grp.loc[list(ana)]))
    assert not dev.set_index("connectivity_key").loc[list(hold), "in_lcsb_dev"].any()
    assert a["hold"]["n_keys"] >= 0.4 * a["n_free_keys"]
    c = reserve_internal_holdout(dev, seed=8, fraction=0.4)
    assert c["hold"]["connectivity_keys"] != a["hold"]["connectivity_keys"]


def test_holdout_rejects_non_dev_rows_and_duplicate_keys():
    dev = _dev()
    bad = dev.copy(); bad.loc[0, "side"] = "WUR-SEALED"
    with pytest.raises(ValueError):
        reserve_internal_holdout(bad)
    dup = pd.concat([dev, dev.iloc[[0]]])
    with pytest.raises(ValueError):
        reserve_internal_holdout(dup)


def test_holdout_stops_at_first_crossing_of_target():
    dev = _dev(seed=3)
    r = reserve_internal_holdout(dev, seed=11, fraction=0.5)
    sizes = dev.groupby("scaffold_group").connectivity_key.nunique()
    # removing the last-added group would drop HOLD below target: mutation guard
    hold_groups = r["hold"]["scaffold_groups"]
    total = sum(int(sizes[g]) for g in hold_groups)
    smallest_drop = min(int(sizes[g]) for g in hold_groups)
    assert total >= 0.5 * r["n_free_keys"]
    # at least one group is load-bearing (fewer keys than target + max group)
    assert total - smallest_drop < 0.5 * r["n_free_keys"] + max(sizes)
