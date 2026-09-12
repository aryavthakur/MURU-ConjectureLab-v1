"""CLI: write artifacts/wur_population_audit.json from data/external/wur/.

No logic lives here -- everything testable is in
muru.io.wur_population_audit. Identity-only: no peak blobs are read.
"""
import json
import sys
from pathlib import Path

from muru.io import wur_raw
from muru.io.wur_identity import accepted_rows
from muru.io.wur_population_audit import build_population_audit

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    accepted = {}
    for polarity_file, symbol in (("POS", "+"), ("NEG", "-")):
        raw = wur_raw.read_all_libraries(data_dir, polarity_file)
        accepted[polarity_file] = accepted_rows(raw, symbol)

    audit = build_population_audit(accepted)
    (ROOT / "artifacts" / "wur_population_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n")

    print("Wrote wur_population_audit.json")
    for polarity_file, entry in audit["polarities"].items():
        print(f"  {polarity_file}: {entry['n_accepted_rows']} accepted rows, "
              f"{entry['n_qualifying_keys']} qualifying keys, "
              f"clean={entry['is_clean']}")
    if not audit["is_clean"]:
        print("POPULATION DEFINITION DEFECT: see the artifact", file=sys.stderr)
        sys.exit(1)
