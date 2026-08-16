#!/usr/bin/env python
"""Run the seven hostile lenses over the restored Held-out analysis.

Read-only with respect to the sealed evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.paper_benchmark.heldout_hostile_lenses import (  # noqa: E402
    LensContext,
    run_all_lenses,
)
from muru.paper_benchmark.rc5_store import case_slug  # noqa: E402
from muru.paper_benchmark.registry import iter_case_ids  # noqa: E402

DEFAULT_EVIDENCE_ROOT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/"
    "muru-heldout-a3-6/results/held_out"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument(
        "--restored-dir", type=Path, default=REPO_ROOT / "results" / "restored"
    )
    args = parser.parse_args()

    restored = args.restored_dir
    primary = json.loads((restored / "heldout_restored_analysis.json").read_text())
    independent = json.loads(
        (restored / "heldout_independent_recomputation.json").read_text()
    )
    recovery_path = restored / "heldout_g1_recovery.json"
    recovery = json.loads(recovery_path.read_text()) if recovery_path.exists() else None

    table = json.loads(
        (REPO_ROOT / "calibration" / "a3_2" / "threshold_table.json").read_text()
    )
    null_threshold = {int(k): float(v) for k, v in table["thresholds"].items()}

    records = args.evidence_root / "records"
    payloads = {
        case_id: json.loads((records / f"{case_slug(case_id)}.json").read_text())
        for case_id in iter_case_ids("held_out")
    }

    ctx = LensContext(
        evidence_root=args.evidence_root,
        repo_root=REPO_ROOT,
        primary=primary,
        independent=independent,
        g1_recovery=recovery,
        payloads=payloads,
        null_threshold=null_threshold,
    )

    result = run_all_lenses(ctx)
    (restored / "heldout_hostile_review.json").write_text(
        json.dumps(result, indent=1, sort_keys=True), encoding="utf-8"
    )

    for lens in result["lenses"]:
        status = "PASS" if lens["passed"] else "FAIL"
        print(f"[{status}] {lens['lens']:32s} {lens['checks']:>3d} checks")
        for failure in lens["failures"]:
            print(f"         FAILED: {failure['check']} -- {failure['detail']}")
    print()
    print(
        f"{result['lens_count']} lenses, {result['total_checks']} checks, "
        f"{result['total_failures']} failures"
    )
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
