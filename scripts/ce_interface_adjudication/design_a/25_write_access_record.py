#!/usr/bin/env python3
"""Design A step 25: write the pre-access record.

Runs BEFORE any MassBank Eawag EQ record file is retrieved. It re-verifies every file the
freeze manifest pins, records the freeze commit and ref, the population, code, configuration
and checkpoint hashes, the environment, and the explicit statement that no candidate spectrum
peak list has been retrieved or read. The record is then committed and published as
refs/muru-access/muru-ce-interface-adjudication-design-a.

Refuses if any frozen file has changed, if the freeze ref does not resolve locally and on
origin, if the working tree is dirty, or if any artifact of a later step already exists.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STUDY_ID = "muru-ce-interface-adjudication-design-a"
FREEZE_REF = f"refs/muru-freeze/{STUDY_ID}"
ACCESS_REF = f"refs/muru-access/{STUDY_ID}"
ROOT = Path(__file__).resolve().parents[3]
STUDY_DIR = ROOT / "artifacts/ce_interface_adjudication/design_a"
FREEZE_MANIFEST = STUDY_DIR / "freeze/freeze_manifest.json"
OUT = STUDY_DIR / "access/access_record.json"
SIMILARITY_CONFIG_SHA = "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"
CHECKPOINT_ROOT = Path.home() / "muru-comparators/checkpoints"

# Nothing from a later step may exist when this runs.
FORBIDDEN_NOW = [
    "artifacts/ce_interface_adjudication/design_a/records",
    "artifacts/ce_interface_adjudication/design_a/prediction_outputs",
    "artifacts/ce_interface_adjudication/design_a/scores",
    "artifacts/ce_interface_adjudication/design_a/result",
    "data/massbank",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"refusing: git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def main() -> int:
    # 1. freeze ref resolves locally and on origin, at the same commit
    local = git("rev-parse", "--verify", FREEZE_REF)
    remote_ls = git("ls-remote", "origin", FREEZE_REF)
    if not remote_ls:
        raise SystemExit(f"refusing: {FREEZE_REF} is not published on origin")
    remote = remote_ls.split()[0]
    if local != remote:
        raise SystemExit(f"refusing: freeze ref local {local} != origin {remote}")

    # 2. clean tree
    if git("status", "--porcelain"):
        raise SystemExit("refusing: working tree is not clean")

    # 3. no later-step artifact exists yet
    for rel in FORBIDDEN_NOW:
        if (ROOT / rel).exists():
            raise SystemExit(f"refusing: {rel} already exists; this must run before retrieval")

    # 4. every frozen file still matches the freeze manifest
    manifest = json.loads(FREEZE_MANIFEST.read_text())
    mismatches, missing = [], []
    for rel, digest in manifest["files"].items():
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
        elif sha256(p) != digest:
            mismatches.append(rel)
    if missing or mismatches:
        raise SystemExit(f"refusing: frozen files missing {missing} mismatched {mismatches}")

    # 5. similarity configuration unchanged
    sim = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,'scripts/ce_interface_adjudication/design_a');"
         "import spectrum_similarity as s;print(s.frozen_config_sha256())"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if sim != SIMILARITY_CONFIG_SHA:
        raise SystemExit(f"refusing: similarity config {sim} != frozen {SIMILARITY_CONFIG_SHA}")

    # 6. checkpoints present and matching
    checkpoints = {}
    for rel, meta in manifest["models"]["checkpoints"].items():
        p = CHECKPOINT_ROOT / rel
        if not p.exists():
            raise SystemExit(f"refusing: checkpoint {rel} is not present")
        observed = sha256(p)
        if observed != meta["recorded_sha256"]:
            raise SystemExit(f"refusing: checkpoint {rel} hash changed")
        checkpoints[rel] = observed

    pop_dir = STUDY_DIR / "population"
    record = {
        "record": ("PRE-ACCESS RECORD, muru-ce-interface-adjudication-design-a, written and published "
                   "before any MassBank Eawag EQ record file is retrieved"),
        "utc_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authorization": (
            "Design A execution authorized by the principal investigator under the frozen preregistration "
            "at commit 518190b. The scientific design is not amended. The disclosed K2/K3 identifiability "
            "limitation is accepted, and an INTERFACE UNRESOLVED verdict will be preserved as the formal result."
        ),
        "order_note": (
            "The authorization requires the access record to be published strictly BEFORE retrieval. "
            "This is stricter than the preregistration's own section 13 ordering, which listed provisioning "
            "the records first. The stricter order is followed."
        ),
        "freeze": {"ref": FREEZE_REF, "commit": local, "remote_target_verified": remote},
        "execution_commit_git_rev_parse_HEAD": git("rev-parse", "HEAD"),
        "git_status_porcelain_empty": True,
        "freeze_manifest_sha256": sha256(FREEZE_MANIFEST),
        "frozen_files_verified": {
            "n_files": len(manifest["files"]),
            "all_match": True,
            "method": "sha256 of every path recorded in freeze_manifest.json, recomputed now",
        },
        "population": {
            "design_a_records_csv_sha256": sha256(pop_dir / "design_a_records.csv"),
            "design_a_compounds_csv_sha256": sha256(pop_dir / "design_a_compounds.csv"),
            "population_manifest_sha256": sha256(pop_dir / "design_a_manifest_sha256.json"),
            "n_compounds": 33, "n_records": 69, "n_scaffold_groups": 33,
            "nce_cells": [30, 60],
        },
        "code": {rel: manifest["files"][rel] for rel in sorted(manifest["files"])
                 if rel.startswith("scripts/ce_interface_adjudication/design_a/")},
        "configuration": {
            "spectrum_similarity_frozen_config_sha256": sim,
            "input_manifest_sha256": sha256(STUDY_DIR / "freeze/input_manifest.json"),
            "bootstrap_B": 10000, "bootstrap_seed": 20260916,
            "adjusted_level": 1.0 - 0.05 / 3,
            "resampling_unit": "compound (molecule-level paired bootstrap)",
            "mappings": manifest["frozen_mappings"],
        },
        "models": {"ms_pred_commit": manifest["models"]["ms_pred_commit"],
                   "checkpoints_sha256_verified_on_disk": checkpoints,
                   "retraining_or_finetuning": "none"},
        "retrieval_plan": {
            "n_records_to_retrieve": 69,
            "source": "MassBank/MassBank-data git blobs, addressed by the blob sha256 recorded per record "
                      "in design_a_records.csv, so each retrieved file is byte-verifiable against the frozen manifest",
            "scope": "exactly the 69 frozen accessions; no neighbouring records, no alternate releases, "
                     "no related compounds, no additional spectra",
        },
        "statement": (
            "NO candidate spectrum peak list has been retrieved or read. No MassBank Eawag EQ record file "
            "has been downloaded, opened, parsed, summarized or counted. No prediction has been generated for "
            "this study. The analysis has never been run. Every quantity in the frozen population was derived "
            "from compound, instrument and collision-energy metadata only."
        ),
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "hostname": platform.node(),
        },
    }
    for mod in ("numpy", "pandas", "scipy", "rdkit"):
        try:
            m = __import__(mod)
            record["environment"][f"{mod}_version"] = getattr(m, "__version__", "unknown")
        except Exception:
            record["environment"][f"{mod}_version"] = "not installed"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(f"access record written: {OUT.relative_to(ROOT)}")
    print(f"  freeze {local} verified on origin")
    print(f"  {len(manifest['files'])} frozen files re-verified, all match")
    print(f"  checkpoints verified: {len(checkpoints)}")
    print(f"  sha256 {sha256(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
