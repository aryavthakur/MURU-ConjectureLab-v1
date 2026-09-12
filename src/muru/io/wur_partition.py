"""Stage 0 partition rules D1-D5. D1 (scaffold group of the
lexicographically-first deposited SMILES) is already applied upstream, in
wur_census.load_annotated_trajectories -- this module applies D2-D5 to the
result."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

SEED = 20260911
SEALED_TRAJECTORY_FLOOR = 250
SEALED_SCAFFOLD_GROUP_FLOOR = 150


def assign_side_by_group(pos_traj: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """D2-D4 on the positive-mode qualifying trajectory table. `pos_traj`
    must already carry scaffold_group/in_lcsb_dev/in_lcsb_sealed. Returns a
    copy with an added `side` column."""
    df = pos_traj.copy()
    by_group_dev = df.groupby("scaffold_group")["in_lcsb_dev"].any()
    by_group_sealed = df.groupby("scaffold_group")["in_lcsb_sealed"].any()
    touches_dev = set(by_group_dev[by_group_dev].index)
    touches_sealed = set(by_group_sealed[by_group_sealed].index)
    free_groups = sorted(set(df["scaffold_group"]) - touches_dev - touches_sealed)

    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(free_groups)
    half = len(shuffled) // 2
    free_sealed = set(shuffled[:half])

    def side_for(group: str) -> str:
        if group in touches_sealed:
            return "WUR-SEALED"                      # D3 beats D2
        if group in touches_dev:
            return "WUR-DEV"                          # D2
        return "WUR-SEALED" if group in free_sealed else "WUR-DEV"  # D4

    df["side"] = df["scaffold_group"].map(side_for)
    return df


def check_sealed_floor(sealed_df: pd.DataFrame) -> dict:
    n_traj = len(sealed_df)
    n_groups = sealed_df["scaffold_group"].nunique() if n_traj else 0
    return {
        "n_trajectories": int(n_traj),
        "n_scaffold_groups": int(n_groups),
        "trajectory_floor": SEALED_TRAJECTORY_FLOOR,
        "scaffold_group_floor": SEALED_SCAFFOLD_GROUP_FLOOR,
        "passes_trajectory_floor": n_traj >= SEALED_TRAJECTORY_FLOOR,
        "passes_scaffold_group_floor": n_groups >= SEALED_SCAFFOLD_GROUP_FLOOR,
    }


def partition(annotated: dict[str, pd.DataFrame],
              seed: int = SEED) -> dict[str, pd.DataFrame]:
    """D1 (upstream) through D5. Returns {"POS": ..., "NEG": ...}, each with
    a `side` column."""
    pos = assign_side_by_group(annotated["POS"], seed=seed)
    neg = annotated["NEG"].copy()
    neg["side"] = "WUR-DEV"                            # D5
    return {"POS": pos, "NEG": neg}


def build_split_manifest(partitioned: dict[str, pd.DataFrame],
                         pre_d6: dict[str, pd.DataFrame] | None = None) -> dict:
    """The split manifest. `partitioned` is the post-D6 assignment; `pre_d6`
    is the D1-D5 assignment, preserved so the D6 record shows what moved."""
    manifest = {"seed": SEED, "created_utc": datetime.now(timezone.utc).isoformat(),
                "polarities": {}}
    for polarity_file, df in partitioned.items():
        entry = {
            "n_trajectories": int(len(df)),
            "n_scaffold_groups": int(df["scaffold_group"].nunique()) if len(df) else 0,
        }
        for side in ("WUR-DEV", "WUR-SEALED", "EXCLUDED"):
            sub = df[df["side"] == side]
            entry[side] = {
                "n_trajectories": int(len(sub)),
                "n_scaffold_groups": int(sub["scaffold_group"].nunique()) if len(sub) else 0,
            }
        entry["sides_account_for_all_rows"] = bool(
            entry["WUR-DEV"]["n_trajectories"]
            + entry["WUR-SEALED"]["n_trajectories"]
            + entry["EXCLUDED"]["n_trajectories"] == entry["n_trajectories"])
        if pre_d6 is not None:
            before = pre_d6[polarity_file]
            before_dev = before[before["side"] == "WUR-DEV"]
            after_dev = df[df["side"] == "WUR-DEV"]
            moved = df[df["side"] == "EXCLUDED"]
            entry["d6"] = {
                "rule": "side == WUR-DEV AND scaffold_group in positive-mode "
                        "WUR-SEALED groups -> EXCLUDED",
                "dev_trajectories_before": int(len(before_dev)),
                "dev_trajectories_after": int(len(after_dev)),
                "excluded_trajectories": int(len(moved)),
                "excluded_scaffold_groups": int(moved["scaffold_group"].nunique())
                    if len(moved) else 0,
            }
        if polarity_file == "POS":
            entry["sealed_floor_check"] = check_sealed_floor(
                df[df["side"] == "WUR-SEALED"])
        manifest["polarities"][polarity_file] = entry
    return manifest


def sealed_scaffold_groups(pos_partitioned: pd.DataFrame) -> set[str]:
    """The positive-mode scaffold groups held by WUR-SEALED. D6's input."""
    return set(pos_partitioned.loc[
        pos_partitioned["side"] == "WUR-SEALED", "scaffold_group"])


def apply_d6(partitioned: dict[str, pd.DataFrame],
             sealed_groups: set[str]) -> dict[str, pd.DataFrame]:
    """D6: a development-exposure exclusion, applied over D1-D5.

    D5 routes every negative-mode trajectory to WUR-DEV without consulting
    the scaffold-group logic that D2-D4 use, so a negative-mode compound can
    sit in development while its scaffold group is sealed on the positive
    side. D6 removes exactly those rows:

        side == "WUR-DEV" AND scaffold_group in sealed_groups -> "EXCLUDED"

    Scope is deliberately narrow. A WUR-SEALED row is never relabelled, so
    the sealed key list is untouched and the sealed-part floor is unmoved.
    The rule is written for both polarities and is a provable no-op on POS,
    because D1-D4 never split a scaffold group across sides. It is applied
    as a filter over the D1-D5 result; it does not re-run the partition.
    """
    out = {}
    for polarity_file, df in partitioned.items():
        df = df.copy()
        excluded = (df["side"] == "WUR-DEV") & df["scaffold_group"].isin(sealed_groups)
        df.loc[excluded, "side"] = "EXCLUDED"
        out[polarity_file] = df
    return out


def build_dev_neg_keys(neg_partitioned: pd.DataFrame) -> dict:
    """The corrected negative-mode WUR-DEV list, after D6."""
    dev = neg_partitioned[neg_partitioned["side"] == "WUR-DEV"]
    return {
        "purpose": "Negative-mode WUR-DEV connectivity keys after rule D6. "
                   "No negative-mode external claim is made (rule D5).",
        "constructed_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "n_compounds": int(len(dev)),
        "n_scaffold_groups": int(dev["scaffold_group"].nunique()) if len(dev) else 0,
        "connectivity_keys": sorted(dev["connectivity_key"].tolist()),
    }


def build_sealed_partition(pos_partitioned: pd.DataFrame) -> dict:
    sealed = pos_partitioned[pos_partitioned["side"] == "WUR-SEALED"]
    return {
        "purpose": "SEALED WUR external-validation partition. Do not open "
                   "during Stage 2 development fitting.",
        "constructed_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "selection_unit": "bemis_murcko_scaffold_group",
        "n_scaffold_groups": int(sealed["scaffold_group"].nunique()),
        "n_compounds": int(len(sealed)),
        "connectivity_keys": sorted(sealed["connectivity_key"].tolist()),
        "disclosure": "These WUR compounds are reserved for one look at a "
                      "candidate frozen on development (Stage 3). Not read "
                      "for any mu or descriptor value before that freeze.",
    }
