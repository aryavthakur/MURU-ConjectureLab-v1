"""Identity-only internal holdout inside WUR-DEV, reserved before Stage 2A.

The reservation is drawn only from "free" WUR-DEV positive-mode scaffold
groups: groups that contain no compound of the LCSB development corpus. A
group that touches LCSB development is already exposed through its LCSB
trajectory, so it cannot serve as a blind check. Groups move whole, so no
scaffold group is split across the boundary.

The draw uses identity information only (connectivity key, scaffold group,
the in_lcsb_dev flag) and a frozen seed. No mu, no peak, no descriptor is
read here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from muru.io.wur_provenance import canonical_key_hash

HOLDOUT_SEED = 20260912
HOLDOUT_FRACTION = 0.40          # of the free-group compound count
HOLDOUT_NAME = "WUR-DEV-HOLD"
ANALYSIS_NAME = "WUR-DEV-ANALYSIS"


def free_groups(dev_pos: pd.DataFrame) -> list[str]:
    """Scaffold groups of WUR-DEV positive mode that touch no LCSB-dev key."""
    touch = dev_pos.groupby("scaffold_group")["in_lcsb_dev"].any()
    return sorted(touch[~touch].index)


def reserve_internal_holdout(dev_pos: pd.DataFrame,
                             seed: int = HOLDOUT_SEED,
                             fraction: float = HOLDOUT_FRACTION) -> dict:
    """Assign every WUR-DEV positive-mode key to HOLD or ANALYSIS.

    Free groups are visited in a seeded random order and added to HOLD until
    the HOLD key count first reaches `fraction` of the free-group key count.
    Every non-free group and every remaining free group is ANALYSIS.
    """
    required = {"connectivity_key", "scaffold_group", "in_lcsb_dev", "side"}
    missing = required - set(dev_pos.columns)
    if missing:
        raise ValueError(f"dev_pos lacks columns {sorted(missing)}")
    if not (dev_pos["side"] == "WUR-DEV").all():
        raise ValueError("reserve_internal_holdout accepts WUR-DEV rows only")
    if dev_pos["connectivity_key"].duplicated().any():
        raise ValueError("one row per connectivity key is required")

    free = free_groups(dev_pos)
    sizes = dev_pos.groupby("scaffold_group")["connectivity_key"].nunique()
    n_free_keys = int(sizes.loc[free].sum()) if free else 0
    target = fraction * n_free_keys

    rng = np.random.default_rng(seed)
    order = [free[i] for i in rng.permutation(len(free))]
    hold_groups: list[str] = []
    n_hold = 0
    for g in order:
        if n_hold >= target:
            break
        hold_groups.append(g)
        n_hold += int(sizes.loc[g])

    hold_set = set(hold_groups)
    hold_keys = sorted(dev_pos.loc[dev_pos["scaffold_group"].isin(hold_set),
                                   "connectivity_key"])
    analysis_keys = sorted(dev_pos.loc[~dev_pos["scaffold_group"].isin(hold_set),
                                       "connectivity_key"])
    assert not (set(hold_keys) & set(analysis_keys))
    assert len(hold_keys) + len(analysis_keys) == len(dev_pos)
    # No held-out group may touch LCSB development.
    assert not dev_pos.loc[dev_pos["scaffold_group"].isin(hold_set),
                           "in_lcsb_dev"].any()

    return {
        "name": HOLDOUT_NAME,
        "seed": int(seed),
        "fraction_of_free_keys": float(fraction),
        "rule": ("free WUR-DEV positive-mode scaffold groups (no LCSB-dev "
                 "compound) visited in seeded random order, added to HOLD "
                 "until HOLD keys >= fraction * free keys; groups move whole"),
        "n_free_groups": len(free),
        "n_free_keys": n_free_keys,
        "hold": {
            "n_keys": len(hold_keys),
            "n_scaffold_groups": len(hold_groups),
            "connectivity_keys": hold_keys,
            "scaffold_groups": sorted(hold_groups),
            "connectivity_keys_sha256": canonical_key_hash(hold_keys),
        },
        "analysis": {
            "name": ANALYSIS_NAME,
            "n_keys": len(analysis_keys),
            "n_scaffold_groups": int(dev_pos.loc[
                ~dev_pos["scaffold_group"].isin(hold_set), "scaffold_group"].nunique()),
            "connectivity_keys": analysis_keys,
            "connectivity_keys_sha256": canonical_key_hash(analysis_keys),
        },
    }
