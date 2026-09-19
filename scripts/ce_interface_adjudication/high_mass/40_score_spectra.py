#!/usr/bin/env python3
"""High-mass replication, step 40: score every frozen record against every (model, mapping) prediction.

Reuses the Design A scoring module unchanged (pinned by sha256): the frozen similarity layer (FROZEN_CONFIG
sha256 655436...b252848), untransformed full-spectrum cosine as primary, JS as robustness, absolute
intensity column, theoretical [M+H]+ as parent mass, and the six mechanical drop reasons. Only study
identity, paths, execution variable and NCE grid are re-pointed.
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hm_constants as C  # noqa: E402

SCORER = HERE.parent / "design_a/40_score_spectra.py"


def load_scorer():
    got = hashlib.sha256(SCORER.read_bytes()).hexdigest()
    if got != C.DESIGN_A_SHA256["40_score_spectra.py"]:
        raise SystemExit(f"refusing: Design A scorer sha256 {got} != pinned")
    spec = importlib.util.spec_from_file_location("design_a_scorer", SCORER)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    A.STUDY_ID, A.FREEZE_REF, A.EXECUTE_ENV_VAR = C.STUDY_ID, C.FREEZE_REF, C.EXECUTE_ENV_VAR
    A.RECORDS_DIR_ENV_VAR = "MURU_CE_HIGH_MASS_RECORDS_DIR"
    A.RECORDS_CSV_REL = f"{C.STUDY_DIR_REL}/population/high_mass_records.csv"
    A.POP_MANIFEST_REL = f"{C.STUDY_DIR_REL}/population/high_mass_manifest_sha256.json"
    A.PRED_DIR_REL = f"{C.STUDY_DIR_REL}/prediction_outputs"
    A.SCORES_REL = f"{C.STUDY_DIR_REL}/scores/record_scores.csv"
    A.DEFAULT_RECORDS_DIR_REL = C.RECORDS_DIR_REL
    A.NCE_CELLS = tuple(C.NCE_GRID)
    return A


if __name__ == "__main__":
    A = load_scorer()
    if not (A.ROOT / C.STUDY_DIR_REL / "prediction_outputs/execution_provenance.json").exists():
        raise SystemExit("refusing: predictions not yet frozen")
    raise SystemExit(A.main(sys.argv[1:]))
