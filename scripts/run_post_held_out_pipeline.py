#!/usr/bin/env python3
"""Unified post-Held-out pipeline: sealing, double-blind analysis, independent recomputation, and hostile audit.

Executes automatically the moment the raw 240-case / 7,200-search run completes.
Preserves all frozen governance, blinding, provenance, and sealed-boundary constraints.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.held_out_analyzer import (
    HeldOutAnalysisReport,
    analyze_held_out_records,
)
from muru.paper_benchmark.hostile_reviewer import run_full_hostile_audit
from muru.paper_benchmark.independent_recomputation import (
    compare_analysis_reports,
    recompute_held_out_metrics,
)
from muru.paper_benchmark.post_execution_sealer import (
    SealingError,
    guard_analysis_boundary,
    verify_held_out_completeness,
    verify_sealed_integrity,
    write_execution_seal_receipt,
)
from muru.paper_benchmark.rc3_record import canonical_json

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("post_held_out_pipeline")


def run_pipeline(
    results_dir: Path,
    run_commit: str = "8d87143d4280602323aa33ee0b5481aaef0fb4a8",
    output_report_dir: Path | None = None,
) -> dict[str, object]:
    """Execute the full sealing, verification, analysis, and hostile audit sequence."""
    results_dir = Path(results_dir)
    if output_report_dir is None:
        output_report_dir = results_dir

    logger.info("=== STEP 1: VERIFYING HELD-OUT COMPLETENESS ===")
    report = verify_held_out_completeness(results_dir)
    report.assert_valid()
    logger.info(
        f"Verified {report.found_case_records}/{report.expected_case_count} cases, "
        f"{report.total_seeds_recorded}/{report.expected_seeds_total} seeds. 0 duplicates."
    )

    logger.info("=== STEP 2: SEALING RAW EXECUTION ARTIFACTS ===")
    receipt_file = results_dir / "execution_seal_receipt.json"
    if receipt_file.exists():
        seal_receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        logger.info("Existing execution seal receipt loaded.")
    else:
        seal_receipt = write_execution_seal_receipt(
            results_root=results_dir,
            report=report,
            run_commit=run_commit,
        )
    logger.info("DECLARATION: CURRENT-CONTRACT HELD-OUT RAW EXECUTION SEALED")

    logger.info("=== STEP 3: CROSSING ANALYSIS BOUNDARY WITH BOUNDARY GUARD ===")
    guard_analysis_boundary(results_dir)

    logger.info("=== STEP 4: EXECUTING FROZEN PRIMARY ANALYSIS ===")
    primary_analysis = analyze_held_out_records(results_dir)
    primary_dict = primary_analysis.to_dict()

    logger.info("=== STEP 5: EXECUTING INDEPENDENT RECOMPUTATION ===")
    independent_analysis = recompute_held_out_metrics(results_dir)

    logger.info("=== STEP 6: AUTOMATED PRIMARY VS INDEPENDENT COMPARISON ===")
    diff_report = compare_analysis_reports(primary_analysis, independent_analysis)
    diff_report.assert_identical()
    logger.info("Primary analyzer and independent recomputation are 100% byte-identical. 0 discrepancies.")

    logger.info("=== STEP 7: EXECUTING 7-PERSPECTIVE HOSTILE AUDIT ===")
    hostile_audit = run_full_hostile_audit(results_dir, primary_analysis)
    if not hostile_audit.overall_passed:
        logger.error("HOSTILE AUDIT FAILED DISCREPANCIES:")
        logger.error(hostile_audit.to_markdown())
        raise RuntimeError("Hostile audit failed")
    logger.info("Hostile audit passed all 7 dimensions cleanly.")

    # Save formal analysis artifacts
    formal_analysis_path = output_report_dir / "held_out_formal_analysis.json"
    formal_analysis_path.write_text(canonical_json(primary_dict), encoding="utf-8")

    hostile_report_path = output_report_dir / "held_out_hostile_audit_report.md"
    hostile_report_path.write_text(hostile_audit.to_markdown(), encoding="utf-8")

    logger.info(f"Saved formal analysis to {formal_analysis_path}")
    logger.info(f"Saved hostile audit report to {hostile_report_path}")

    return {
        "sealed": True,
        "seal_receipt": seal_receipt,
        "primary_analysis": primary_dict,
        "hostile_audit_passed": hostile_audit.overall_passed,
    }


def main() -> None:
    worktree_path = ROOT / ".claude" / "worktrees" / "muru-heldout-a3-6" / "results" / "held_out"
    local_path = ROOT / "results" / "held_out"
    results_dir = worktree_path if worktree_path.exists() else local_path

    logger.info(f"Target results directory: {results_dir}")
    try:
        res = run_pipeline(results_dir)
        print("\n" + "=" * 70)
        print("MURU HELD-OUT POST-EXECUTION PIPELINE COMPLETE")
        print(f"Overall Decision: {'PASSED' if res['primary_analysis']['decision_passed'] else 'FAILED'}")
        print("=" * 70)
    except Exception as exc:
        logger.error(f"Pipeline blocked: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
