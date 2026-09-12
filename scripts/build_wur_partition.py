"""CLI: build artifacts/wur_split_manifest.json,
artifacts/wur_sealed_partition.json and artifacts/wur_dev_neg_keys.json
from data/external/wur/.

No logic lives here -- everything testable is in
muru.io.wur_partition (see that module's own tests). This script only
wires it to real files. Identity-only: no peak blobs are read.
"""
import json
import sys
from pathlib import Path

from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import (
    apply_d6, build_dev_neg_keys, build_sealed_partition, build_split_manifest,
    partition, sealed_scaffold_groups,
)

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    pre_d6 = partition(load_annotated_trajectories(data_dir))

    sealed_groups = sealed_scaffold_groups(pre_d6["POS"])
    partitioned = apply_d6(pre_d6, sealed_groups)

    # D6 invariants, asserted rather than assumed.
    sealed_before = sorted(pre_d6["POS"].loc[
        pre_d6["POS"]["side"] == "WUR-SEALED", "connectivity_key"])
    sealed_after = sorted(partitioned["POS"].loc[
        partitioned["POS"]["side"] == "WUR-SEALED", "connectivity_key"])
    assert sealed_before == sealed_after, "D6 moved a sealed row"
    assert partitioned["POS"]["side"].equals(pre_d6["POS"]["side"]), \
        "D6 was not a no-op on POS"
    for polarity_file, df in partitioned.items():
        dev_groups = set(df.loc[df["side"] == "WUR-DEV", "scaffold_group"])
        assert not (dev_groups & sealed_groups), \
            f"{polarity_file}: a WUR-DEV row sits in a sealed scaffold group"
        assert len(df) == len(pre_d6[polarity_file]), \
            f"{polarity_file}: D6 changed the row count"

    split_manifest = build_split_manifest(
        partitioned, pre_d6=pre_d6, sealed_keys=set(sealed_after))
    (ROOT / "artifacts" / "wur_split_manifest.json").write_text(
        json.dumps(split_manifest, indent=2) + "\n")

    sealed_partition = build_sealed_partition(partitioned["POS"])
    (ROOT / "artifacts" / "wur_sealed_partition.json").write_text(
        json.dumps(sealed_partition, indent=2) + "\n")

    dev_neg = build_dev_neg_keys(partitioned["NEG"])
    (ROOT / "artifacts" / "wur_dev_neg_keys.json").write_text(
        json.dumps(dev_neg, indent=2) + "\n")

    floor = split_manifest["polarities"]["POS"]["sealed_floor_check"]
    print("Wrote wur_split_manifest.json, wur_sealed_partition.json and "
          "wur_dev_neg_keys.json")
    print(f"  POS WUR-SEALED: {floor['n_trajectories']} trajectories, "
          f"{floor['n_scaffold_groups']} scaffold groups")
    print(f"  sealed key hash: {sealed_partition['connectivity_keys_sha256']}")
    for polarity_file, entry in split_manifest["polarities"].items():
        d6 = entry.get("d6", {})
        print(f"  {polarity_file} D6: dev {d6.get('dev_trajectories_before')} -> "
              f"{d6.get('dev_trajectories_after')}, excluded "
              f"{d6.get('excluded_trajectories')} in "
              f"{d6.get('excluded_scaffold_groups')} groups "
              f"({d6.get('excluded_by_direct_key_match')} by direct key match, "
              f"{d6.get('excluded_as_scaffold_group_neighbour')} as neighbours)")
    if not (floor["passes_trajectory_floor"] and floor["passes_scaffold_group_floor"]):
        print(f"WARNING: sealed part below floor: {floor}", file=sys.stderr)
        sys.exit(1)
