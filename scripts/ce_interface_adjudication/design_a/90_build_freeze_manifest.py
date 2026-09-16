#!/usr/bin/env python3
"""Build the Design A freeze manifest.

Hashes every document, script, test and artifact that the preregistration binds, plus the
upstream inputs the population was built from and the checkpoint identities that execution
will re-verify. Writes two files:

  freeze/freeze_manifest.json : the complete record, for the freeze tag
  freeze/input_manifest.json  : the digests 50_analysis.py reads (population now; the score
                                table digest is merged in by the scoring step at execution,
                                and the analysis refuses if it is absent or does not match)

Deterministic: sorted paths, no timestamps, no randomness. Re-running on an unchanged tree
reproduces the file byte for byte.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PREREG_ID = "muru-ce-interface-adjudication-design-a"
FREEZE_REF = f"refs/muru-freeze/{PREREG_ID}"
OUT_DIR = ROOT / "artifacts/ce_interface_adjudication/design_a/freeze"

DOCUMENTS = [
    "MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_PREREGISTRATION.md",
    "MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md",
    "MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md",
    "MURU_CE_INTERFACE_ADJUDICATION_PREREGISTRATION_OUTLINE_DRAFT.md",
]
CODE_DIRS = ["scripts/ce_interface_adjudication/design_a"]
ARTIFACT_DIRS = [
    "artifacts/ce_interface_adjudication/design_a/population",
    "artifacts/ce_interface_adjudication/design_a/diagnostics",
    "artifacts/ce_interface_adjudication/design_a/notes",
]
UPSTREAM_INPUTS = [
    "artifacts/ce_interface_adjudication/screen/c01_eawag_eq/c01_record_metadata.csv.gz",
    "artifacts/ce_interface_adjudication/screen/c01_eawag_eq/c01_compound_screen.csv",
    "artifacts/ce_interface_adjudication/screen/c01_eawag_eq/c01_tautomer_recheck.csv",
    "scripts/ce_interface_adjudication/scaffold_key.py",
]
CHECKPOINTS = {
    "iceberg21_msg_simulation/gen/best.ckpt":
        "1eda5f3d9cda8345a93c0c480c3c848de840a611017a3f1641007fec1afb7a70",
    "iceberg21_msg_simulation/inten_contr/best.ckpt":
        "e074c0392638a71589e68d80acfd9ad53ae0587c523249cfa90e04ee50ee4f58",
    "glacier_msg/best.ckpt":
        "5a47cecca707d3abd5a49c7dbac99d100aa2a586d5d4f848f1e8e35140d7db11",
}
CHECKPOINT_ROOT = Path.home() / "muru-comparators/checkpoints"
MS_PRED_COMMIT = "ed8311f22958cb37f055b663b5f56c5c77a2ee33"
SIMILARITY_CONFIG_SHA = "655436863b02262585609d5582f43a73a0f51f84d04d0bba0da9c2b3db252848"

SKIP_PARTS = {"__pycache__", ".pytest_cache"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(rel_dirs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in rel_dirs:
        base = ROOT / rel
        if not base.exists():
            raise SystemExit(f"refusing: {rel} does not exist")
        for p in sorted(base.rglob("*")):
            if not p.is_file() or set(p.parts) & SKIP_PARTS:
                continue
            out[str(p.relative_to(ROOT))] = sha256(p)
    return out


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main() -> int:
    files: dict[str, str] = {}
    for rel in DOCUMENTS + UPSTREAM_INPUTS:
        p = ROOT / rel
        if not p.exists():
            raise SystemExit(f"refusing: {rel} does not exist")
        files[rel] = sha256(p)
    files.update(collect(CODE_DIRS))
    files.update(collect(ARTIFACT_DIRS))

    similarity_sha = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,'scripts/ce_interface_adjudication/design_a');"
         "import spectrum_similarity as s;print(s.frozen_config_sha256())"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if similarity_sha != SIMILARITY_CONFIG_SHA:
        raise SystemExit(
            f"refusing: spectrum_similarity FROZEN_CONFIG sha256 is {similarity_sha!r}, "
            f"expected {SIMILARITY_CONFIG_SHA!r}")

    checkpoints = {}
    for rel, expected in CHECKPOINTS.items():
        p = CHECKPOINT_ROOT / rel
        observed = sha256(p) if p.exists() else None
        if observed is not None and observed != expected:
            raise SystemExit(f"refusing: checkpoint {rel} hash {observed} != recorded {expected}")
        checkpoints[rel] = {"recorded_sha256": expected, "verified_on_disk": observed is not None}

    manifest = {
        "prereg_id": PREREG_ID,
        "freeze_ref": FREEZE_REF,
        "statement": (
            "Freeze manifest for the Design A collision-energy interface adjudication. "
            "No candidate spectrum has been accessed, no prediction has been generated and "
            "the analysis has never been run. Execution requires explicit authorization."
        ),
        "git_head_at_build": git("rev-parse", "HEAD"),
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "n_files": len(files),
        "files": dict(sorted(files.items())),
        "frozen_mappings": {
            "K1": "float(NCE)",
            "K2": "float(NCE) * theoretical_mh / 500.0, IEEE-754 binary64, multiply then divide, no rounding",
            "K3": "math.floor(K2) as a float, floor toward negative infinity",
        },
        "spectrum_similarity_frozen_config_sha256": SIMILARITY_CONFIG_SHA,
        "analysis_constants": {
            "bootstrap_B": 10000,
            "bootstrap_seed": 20260916,
            "alpha": 0.05,
            "n_contrasts": 3,
            "adjusted_level": 1.0 - 0.05 / 3,
            "resampling_unit": "compound (molecule-level paired bootstrap)",
            "resampling_unit_basis": (
                "0 of 33 compounds share a scaffold group, below the frozen 0.10 threshold; "
                "decided from identities only, before any outcome exists"
            ),
            "primary_metric": "untransformed full-spectrum cosine",
            "robustness_metric": "jensen_shannon",
        },
        "models": {
            "ms_pred_commit": MS_PRED_COMMIT,
            "checkpoints": checkpoints,
            "retraining_or_finetuning": "none",
            "fiora": "does not participate",
            "muru": "does not participate",
        },
        "execution_gates": {
            "predictions_and_scoring": "MURU_CE_ADJUDICATION_EXECUTE=1 plus the freeze ref plus matching hashes",
            "analysis": "MURU_CE_ADJUDICATION_ONE_LOOK=1 plus the freeze ref plus matching hashes plus a complete score table",
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "freeze_manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=False) + "\n")

    pop_rel = "artifacts/ce_interface_adjudication/design_a/population/design_a_compounds.csv"
    rec_rel = "artifacts/ce_interface_adjudication/design_a/population/design_a_records.csv"
    input_manifest = {
        "prereg_id": PREREG_ID,
        "note": (
            "Digests read by 40_score_spectra.py and 50_analysis.py. The record_scores.csv "
            "digest does not exist at freeze time; the scoring step writes it into its sidecar "
            "at execution and it is merged here before the single analysis run. The analysis "
            "refuses if a required input has no recorded digest or does not match."
        ),
        "outputs_written": {pop_rel: files[pop_rel], rec_rel: files[rec_rel]},
    }
    (OUT_DIR / "input_manifest.json").write_text(
        json.dumps(input_manifest, indent=1, sort_keys=False) + "\n")

    print(f"freeze manifest: {len(files)} files")
    print(f"  documents {len(DOCUMENTS)}, upstream inputs {len(UPSTREAM_INPUTS)}")
    print(f"  similarity config sha256 {similarity_sha}")
    print(f"  checkpoints verified on disk: "
          f"{sum(1 for v in checkpoints.values() if v['verified_on_disk'])} of {len(checkpoints)}")
    for rel in (OUT_DIR / "freeze_manifest.json", OUT_DIR / "input_manifest.json"):
        print(f"  wrote {rel.relative_to(ROOT)} sha256 {sha256(rel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
