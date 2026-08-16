#!/usr/bin/env python
"""Seals the finished E2 deliverable set: SHA-256 of every deliverable file,
plus the preflight manifest and retention-identity control result, written
to results/e2/E2_SEAL.json. Run only after e2_report.py and
e2_write_md_report.py have produced their outputs.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DELIVERABLES = [
    "results/e2/manifest.json",
    "results/e2/retention_identity_control.json",
    "results/e2/E2_REPORT.json",
    "results/e2/E2_REPORT.md",
    "results/e2/E2_HOSTILE_REVIEW.md",
    "results/e2/E2_CASE_ATTRITION_TABLE.csv",
    "results/e2/E2_CANDIDATE_DATASET.parquet",
    "results/e2/E2_CANDIDATE_DATASET.meta.json",
    "v2_design_reference/MURU_V2_E2_PREDECLARATION.md",
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    hashes = {}
    missing = []
    for rel in DELIVERABLES:
        path = REPO_ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        hashes[rel] = {"sha256": sha256_of(path), "bytes": path.stat().st_size}

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True).stdout

    seal = {
        "sealed_commit": head,
        "branch": branch,
        "working_tree_dirty_at_seal_time": bool(dirty.strip()),
        "deliverable_hashes": hashes,
        "missing_deliverables": missing,
    }
    out_path = REPO_ROOT / "results" / "e2" / "E2_SEAL.json"
    out_path.write_text(json.dumps(seal, indent=2, sort_keys=True))
    print(json.dumps(seal, indent=2))
    if missing:
        print(f"\nWARNING: {len(missing)} deliverable(s) missing: {missing}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
