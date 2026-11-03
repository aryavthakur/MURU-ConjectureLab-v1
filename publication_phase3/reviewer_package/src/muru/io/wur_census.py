"""Annotate qualifying WUR trajectories against the existing LCSB
development corpus and sealed confirmation set, and summarize the census."""
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from muru.io import wur_raw
from muru.io.wur_identity import build_qualifying_trajectories
from muru.molecules import scaffold_group
from muru.synth.generators import sealed_keys

ROOT = Path(__file__).resolve().parents[3]


def dev_corpus_keys() -> set[str]:
    dev = pd.read_parquet(ROOT / "artifacts" / "p2_dev_corpus.parquet")
    return set(dev["inchikey_first_block"])


def load_annotated_trajectories(data_dir: Path) -> dict[str, pd.DataFrame]:
    sealed = sealed_keys()
    dev_keys = dev_corpus_keys()
    out = {}
    for polarity_file, polarity_symbol in (("POS", "+"), ("NEG", "-")):
        raw = wur_raw.read_all_libraries(data_dir, polarity_file)
        traj = build_qualifying_trajectories(raw, polarity_symbol)
        if len(traj):
            traj["scaffold_group"] = [
                scaffold_group(s, k) for s, k in
                zip(traj["smiles"], traj["connectivity_key"])
            ]
            traj["in_lcsb_dev"] = traj["connectivity_key"].isin(dev_keys)
            traj["in_lcsb_sealed"] = traj["connectivity_key"].isin(sealed)
        else:
            traj["scaffold_group"] = pd.Series(dtype=str)
            traj["in_lcsb_dev"] = pd.Series(dtype=bool)
            traj["in_lcsb_sealed"] = pd.Series(dtype=bool)
        out[polarity_file] = traj
    return out


def build_census(annotated: dict[str, pd.DataFrame]) -> dict:
    census = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "polarities": {}}
    for polarity_file, traj in annotated.items():
        n = len(traj)
        n_wfsr_fs = int(
            traj["source_libraries"].apply(
                lambda ls: "WFSR_food_safety" in ls).sum()) if n else 0
        census["polarities"][polarity_file] = {
            "n_trajectories": int(n),
            "n_scaffold_groups": int(traj["scaffold_group"].nunique()) if n else 0,
            "n_from_wfsr_food_safety": n_wfsr_fs,
            "n_in_lcsb_dev": int(traj["in_lcsb_dev"].sum()) if n else 0,
            "n_in_lcsb_sealed": int(traj["in_lcsb_sealed"].sum()) if n else 0,
            "adduct_counts": traj["adduct"].value_counts().to_dict() if n else {},
        }
    return census
