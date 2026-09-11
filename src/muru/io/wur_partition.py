"""Stage 0 partition rules D1-D5. D1 (scaffold group of the
lexicographically-first deposited SMILES) is already applied upstream, in
wur_census.load_annotated_trajectories -- this module applies D2-D5 to the
result."""
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
