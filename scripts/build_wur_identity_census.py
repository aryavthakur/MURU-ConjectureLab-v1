"""CLI: build artifacts/wur_identity_census.json from data/external/wur/."""
import json
import sys
from pathlib import Path

from muru.io.wur_census import build_census, load_annotated_trajectories

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    annotated = load_annotated_trajectories(data_dir)
    census = build_census(annotated)
    out = ROOT / "artifacts" / "wur_identity_census.json"
    out.write_text(json.dumps(census, indent=2) + "\n")
    print(f"Wrote {out}")
    for pf, entry in census["polarities"].items():
        print(f"  {pf}: {entry['n_trajectories']} trajectories, "
              f"{entry['n_scaffold_groups']} scaffold groups")
