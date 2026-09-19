#!/usr/bin/env python3
"""High-mass replication, step 30: K1/K2/K3 predictions for ICEBERG 2.1 and GLACIER.

Reuses the Design A harness unchanged (pinned by sha256) and re-points only the study identity, paths,
execution variable and NCE grid. Mappings, command lines, checkpoints, seeds and tokens are Design A's.
Execute mode additionally requires the retrieval summary to exist (records retrieved after the access ref).

Usage: 30_run_predictions.py emit-inputs | execute
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hm_constants as C  # noqa: E402

ROOT = HERE.parents[2]
STUDY = ROOT / C.STUDY_DIR_REL
HARNESS = HERE.parent / "design_a/30_run_predictions.py"


def load_harness():
    got = hashlib.sha256(HARNESS.read_bytes()).hexdigest()
    if got != C.DESIGN_A_SHA256["30_run_predictions.py"]:
        raise SystemExit(f"refusing: Design A harness sha256 {got} != pinned")
    spec = importlib.util.spec_from_file_location("design_a_harness", HARNESS)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    A.STUDY_ID, A.FREEZE_REF, A.EXECUTE_ENV_VAR = C.STUDY_ID, C.FREEZE_REF, C.EXECUTE_ENV_VAR
    A.STUDY_DIR, A.POP_DIR = STUDY, STUDY / "population"
    A.IN_DIR, A.OUT_DIR = STUDY / "prediction_inputs", STUDY / "prediction_outputs"
    A.NCE_RUNGS = tuple(C.NCE_GRID)
    return A


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["emit-inputs", "execute"])
    a = ap.parse_args(argv)
    A = load_harness()
    if a.mode == "emit-inputs":
        A.emit_inputs(A.POP_DIR / "high_mass_compounds.csv", A.POP_DIR / "high_mass_records.csv", A.IN_DIR)
        return 0
    if not (STUDY / "records/retrieval_summary.json").exists():
        raise SystemExit("refusing: records not yet retrieved under the access ref")
    return A.execute(in_dir=A.IN_DIR, out_dir=A.OUT_DIR)


if __name__ == "__main__":
    raise SystemExit(main())
