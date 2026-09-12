"""CLI: build artifacts/wur_split_manifest.json and
artifacts/wur_sealed_partition.json from data/external/wur/.

No logic lives here -- everything testable is in
muru.io.wur_partition (see that module's own tests). This script only
wires it to real files.
"""
import json
import sys
from pathlib import Path

from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import build_sealed_partition, build_split_manifest, partition

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    partitioned = partition(load_annotated_trajectories(data_dir))

    split_manifest = build_split_manifest(partitioned)
    (ROOT / "artifacts" / "wur_split_manifest.json").write_text(
        json.dumps(split_manifest, indent=2) + "\n")

    sealed_partition = build_sealed_partition(partitioned["POS"])
    (ROOT / "artifacts" / "wur_sealed_partition.json").write_text(
        json.dumps(sealed_partition, indent=2) + "\n")

    floor = split_manifest["polarities"]["POS"]["sealed_floor_check"]
    print("Wrote wur_split_manifest.json and wur_sealed_partition.json")
    print(f"  POS WUR-SEALED: {floor['n_trajectories']} trajectories, "
          f"{floor['n_scaffold_groups']} scaffold groups")
    if not (floor["passes_trajectory_floor"] and floor["passes_scaffold_group_floor"]):
        print(f"WARNING: sealed part below floor: {floor}", file=sys.stderr)
        sys.exit(1)
