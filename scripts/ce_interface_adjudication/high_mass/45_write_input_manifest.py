#!/usr/bin/env python3
"""High-mass replication, step 45: record the sha256 of the score table and the population before the one look."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hm_constants as C  # noqa: E402

ROOT = HERE.parents[2]
if __name__ == "__main__":
    if not subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", C.FREEZE_REF],
                          capture_output=True, text=True).stdout.strip():
        raise SystemExit("refusing: freeze ref does not resolve")
    rels = [f"{C.STUDY_DIR_REL}/scores/record_scores.csv", f"{C.STUDY_DIR_REL}/population/high_mass_compounds.csv"]
    out = ROOT / C.STUDY_DIR_REL / "freeze/input_manifest.json"
    if out.exists():
        raise SystemExit("refusing: input manifest already written")
    out.write_text(json.dumps({"sha256": {r: hashlib.sha256((ROOT / r).read_bytes()).hexdigest() for r in rels}}, indent=1) + "\n")
    print(out.read_text())
