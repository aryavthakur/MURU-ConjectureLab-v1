"""Master deterministic result ingestion and reporting CLI for MURU ConjectureLab v1.

CRITICAL INGESTION & REPORTING RULES:
1. Fail closed: If required input artifacts are missing, exit immediately with RESULT_ARTIFACT_MISSING (code 2).
2. Zero mock/fake data: Never insert synthetic or fabricated numbers into publication outputs.
3. Exact denominators: Recompute Wilson intervals strictly from numerator and frozen denominators.
4. Mechanical status selection: Status and wording templates are selected strictly by numerical rules without LLM subjectivity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path for direct script execution
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from paper.results.schema.validators import (
        validate_calibration_result,
        validate_development_aggregate,
        validate_held_out_aggregate,
        SchemaValidationError,
    )
    from paper.results.scripts.verdict_engine import evaluate_all_gates, evaluate_claims
    from paper.results.scripts.populate_tables import populate_all_tables
    from paper.results.scripts.render_prospective_figures import (
        render_all_prospective_figures,
        ResultArtifactMissingError,
    )
    from paper.results.scripts.update_claim_matrix import update_claim_matrix_file
    from paper.results.scripts.update_evidence_ledger import update_evidence_ledger_file
    from paper.results.scripts.export_paper_results_json import (
        assemble_master_payload,
        export_master_payload_file,
    )
except ImportError:
    from ..schema.validators import (
        validate_calibration_result,
        validate_development_aggregate,
        validate_held_out_aggregate,
        SchemaValidationError,
    )
    from .verdict_engine import evaluate_all_gates, evaluate_claims
    from .populate_tables import populate_all_tables
    from .render_prospective_figures import (
        render_all_prospective_figures,
        ResultArtifactMissingError,
    )
    from .update_claim_matrix import update_claim_matrix_file
    from .update_evidence_ledger import update_evidence_ledger_file
    from .export_paper_results_json import (
        assemble_master_payload,
        export_master_payload_file,
    )


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest_and_report(
    cal_path: Path | None,
    dev_path: Path | None,
    ho_path: Path | None,
    output_dir: Path,
    check_only: bool = False,
    dry_run: bool = False,
) -> int:
    """Execute the end-to-end ingestion and reporting pipeline."""
    # Check for presence of required inputs (Fail closed)
    missing = []
    if cal_path is None or not cal_path.exists():
        missing.append(f"calibration artifact ({cal_path})")
    if dev_path is None or not dev_path.exists():
        missing.append(f"development aggregate ({dev_path})")
    if ho_path is None or not ho_path.exists():
        missing.append(f"held-out aggregate ({ho_path})")

    if missing:
        print("=" * 70, file=sys.stderr)
        print("RESULT_ARTIFACT_MISSING: The pipeline cannot run without frozen result artifacts.", file=sys.stderr)
        print(f"Missing required artifact(s): {', '.join(missing)}", file=sys.stderr)
        print("Fail closed: No mock or fake results will be generated.", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return 2

    # Load and validate JSON inputs
    try:
        cal_raw = json.loads(cal_path.read_text(encoding="utf-8"))
        dev_raw = json.loads(dev_path.read_text(encoding="utf-8"))
        ho_raw = json.loads(ho_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: Failed to parse input JSON: {exc}", file=sys.stderr)
        return 1

    try:
        cal_data = validate_calibration_result(cal_raw)
        dev_data = validate_development_aggregate(dev_raw)
        ho_data = validate_held_out_aggregate(ho_raw)
    except SchemaValidationError as exc:
        print(f"SCHEMA VALIDATION ERROR: {exc}", file=sys.stderr)
        return 1

    cal_sha = _file_sha256(cal_path)
    dev_sha = _file_sha256(dev_path)
    ho_sha = _file_sha256(ho_path)

    # Assemble master payload
    payload = assemble_master_payload(
        cal_data=cal_data,
        dev_data=dev_data,
        held_out_data=ho_data,
        cal_sha256=cal_sha,
        dev_sha256=dev_sha,
        ho_sha256=ho_sha,
    )

    verdicts = payload["gate_verdicts"]
    print("=" * 70)
    print("MURU CONJECTURELAB v1: RESULT INGESTION & EVALUATION")
    print("=" * 70)
    print(f"Calibration: {verdicts['calibration']['status']} ({verdicts['calibration']['n_worlds_valid']}/100 valid worlds)")
    print(f"Gate G1 (Scalar): {verdicts['G1']['verdict']} (Rate: {verdicts['G1']['rate']:.4f}, Wilson: {verdicts['G1']['wilson_95']['bracket']})")
    print(f"Gate G2 (Family): {verdicts['G2']['verdict']} (Rate: {verdicts['G2']['rate']:.4f}, Wilson: {verdicts['G2']['wilson_95']['bracket']})")
    print(f"Gate G3 (Safety): {verdicts['G3']['verdict']} (Violations: {verdicts['G3']['numerator']}/36, Rate: {verdicts['G3']['rate']:.4f}, Wilson: {verdicts['G3']['wilson_95']['bracket']})")
    print(f"Umbrella Claim: {verdicts['umbrella_claim']['verdict']}")
    print("-" * 70)

    if check_only or dry_run:
        print("Dry run / check complete. No files written.")
        return 0

    # 1. Export Master JSON
    json_out = output_dir / "paper" / "results" / "paper_results.json"
    export_master_payload_file(payload, json_out)
    print(f"[OK] Exported master results payload: {json_out}")

    # 2. Populate Tables (MD, TeX, JSON)
    populate_all_tables(payload, output_dir)
    print("[OK] Populated result tables (Tables 3b through 9) in paper/tables/results/")

    # 3. Render Prospective Figures
    try:
        render_all_prospective_figures(payload, output_dir)
        print("[OK] Rendered prospective figures (Figure 4D, 5D, 6D, 7, 8B/C) in paper/figures/results/")
    except ResultArtifactMissingError as exc:
        print(f"[WARN] Figure rendering skipped: {exc}")

    # 4. Update Claim Matrix
    claim_matrix_src = output_dir / "paper" / "MURU_CLAIM_MATRIX.md"
    if claim_matrix_src.exists():
        updated_matrix = update_claim_matrix_file(claim_matrix_src, payload["claim_evaluations"])
        print(f"[OK] Generated populated claim matrix: {updated_matrix}")

    # 5. Update Evidence Ledger
    ledger_src = output_dir / "paper" / "MURU_EVIDENCE_LEDGER.json"
    if ledger_src.exists():
        updated_ledger = update_evidence_ledger_file(ledger_src, payload)
        print(f"[OK] Generated populated evidence ledger: {updated_ledger}")

    print("=" * 70)
    print("RESULT INGESTION & REPORTING COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic prospective result ingestion and reporting for MURU ConjectureLab v1.",
    )
    parser.add_argument("--calibration", type=Path, default=None, help="Path to calibration result artifact")
    parser.add_argument("--development", type=Path, default=None, help="Path to development aggregate artifact")
    parser.add_argument("--held-out", type=Path, default=None, help="Path to held-out aggregate artifact")
    parser.add_argument("--output-dir", type=Path, default=None, help="Target repository root directory")
    parser.add_argument("--check-only", action="store_true", help="Validate inputs without writing outputs")
    parser.add_argument("--dry-run", action="store_true", help="Execute calculations without modifying files")

    args = parser.parse_args()
    repo_root = args.output_dir or Path(__file__).resolve().parent.parent.parent.parent

    code = ingest_and_report(
        cal_path=args.calibration,
        dev_path=args.development,
        ho_path=args.held_out,
        output_dir=repo_root,
        check_only=args.check_only,
        dry_run=args.dry_run,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
