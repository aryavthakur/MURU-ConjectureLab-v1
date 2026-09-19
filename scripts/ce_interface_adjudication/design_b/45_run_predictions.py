"""Design B step 45: prediction harness. Reuses the Design A harness unchanged (pinned by sha256) and re-points
only its study identity, paths, execution variable and NCE grid. Adds one gate: the observed spectra must be
frozen (refs/muru-spectra/<study>) before any prediction is generated.

Population predicted: the ANALYSABLE compounds of artifacts/.../observed/acquisition_outcomes.csv only.
compound_id = parent_key, representative_smiles = parent_smiles, theoretical_mh = mh (procurement manifest).
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_b_constants as C  # noqa: E402

ROOT = HERE.parents[2]
DESIGN_A_HARNESS = HERE.parent / "design_a/30_run_predictions.py"
DESIGN_A_HARNESS_SHA256 = "461b18fbd2b10a10d1ac6d6097ea7bde258e3e0efdeba5a369469679c6270680"
STUDY_DIR = ROOT / "artifacts/ce_interface_adjudication/design_b"
EXECUTE_ENV_VAR = "MURU_CE_DESIGN_B_EXECUTE"


def load_harness():
    got = hashlib.sha256(DESIGN_A_HARNESS.read_bytes()).hexdigest()
    if got != DESIGN_A_HARNESS_SHA256:
        raise SystemExit(f"refusing: Design A harness sha256 {got} != pinned {DESIGN_A_HARNESS_SHA256}")
    spec = importlib.util.spec_from_file_location("design_a_harness", DESIGN_A_HARNESS)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    A.STUDY_ID, A.FREEZE_REF, A.EXECUTE_ENV_VAR = C.STUDY_ID, C.FREEZE_REF, EXECUTE_ENV_VAR
    A.STUDY_DIR, A.POP_DIR = STUDY_DIR, STUDY_DIR / "prediction_population"
    A.IN_DIR, A.OUT_DIR = STUDY_DIR / "prediction_inputs", STUDY_DIR / "prediction_outputs"
    A.NCE_RUNGS = tuple(C.NCE_GRID)
    return A


def require_spectra_frozen() -> str:
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", C.SPECTRA_REF],
                       capture_output=True, text=True)
    if not r.stdout.strip():
        raise SystemExit(f"refusing: {C.SPECTRA_REF} does not resolve; no prediction before the observed spectra are frozen")
    return r.stdout.strip()


def write_population(A) -> Path:
    man = pd.read_csv(STUDY_DIR / "procurement/procurement_manifest.csv")
    out = pd.read_csv(STUDY_DIR / "observed/acquisition_outcomes.csv")
    keep = set(out.loc[out["status"] == "ANALYSABLE", "parent_key"])
    pop = man[man["parent_key"].isin(keep)].rename(columns={"parent_key": "compound_id", "parent_smiles": "representative_smiles",
                                                            "mh": "theoretical_mh"})
    A.POP_DIR.mkdir(parents=True, exist_ok=True)
    p = A.POP_DIR / "prediction_population.csv"
    pop[["compound_id", "representative_smiles", "theoretical_mh", "stratum", "scaffold_group"]].to_csv(p, index=False)
    return p


def main(argv=None) -> int:
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["emit-inputs", "execute"])
    a = ap.parse_args(argv)
    require_spectra_frozen()
    A = load_harness()
    if a.mode == "emit-inputs":
        p = write_population(A)
        A.emit_inputs(p, STUDY_DIR / "observed/acquisition_outcomes.csv", A.IN_DIR)
        return 0
    return A.execute(in_dir=A.IN_DIR, out_dir=A.OUT_DIR)


if __name__ == "__main__":
    raise SystemExit(main())
