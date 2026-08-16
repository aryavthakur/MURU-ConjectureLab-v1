#!/usr/bin/env python
"""Run the restored Held-out analysis over the sealed evidence.

Read-only with respect to the evidence root: every output is written into this
repair worktree's ``results/restored/``, never into ``results/held_out/``.

Usage:
    PYTHONPATH=src python scripts/run_heldout_restored_analysis.py \
        --evidence-root <path to sealed results/held_out> \
        [--g1-mode exact|bound]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.paper_benchmark.heldout_contract_analysis import (  # noqa: E402
    analyze_sealed_partition,
)
from muru.paper_benchmark.heldout_g1_recovery import (  # noqa: E402
    recover_g1_observables,
)
from muru.paper_benchmark.heldout_independent_scoring import (  # noqa: E402
    compare_to_primary,
    recompute_independently,
)

DEFAULT_EVIDENCE_ROOT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/"
    "muru-heldout-a3-6/results/held_out"
)


def load_frozen_null_threshold() -> dict[int, float]:
    """The frozen A3.2 structural-null calibration table."""
    payload = json.loads(
        (REPO_ROOT / "calibration" / "a3_2" / "threshold_table.json").read_text(
            encoding="utf-8"
        )
    )
    if payload["validity"] != "VALID":
        raise SystemExit(f"calibration table is {payload['validity']}, not VALID")
    return {int(k): float(v) for k, v in payload["thresholds"].items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument("--g1-mode", choices=("exact", "bound"), default="exact")
    parser.add_argument(
        "--out-dir", type=Path, default=REPO_ROOT / "results" / "restored"
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_root = args.evidence_root.resolve()

    if out_dir.resolve() == evidence_root or evidence_root in out_dir.resolve().parents:
        raise SystemExit(
            "refusing to write analysis output inside the sealed evidence root"
        )

    null_threshold = load_frozen_null_threshold()

    exact_outcomes = None
    if args.g1_mode == "exact":
        print("recovering exact G1 observables (zero searches) ...", flush=True)
        recovery = recover_g1_observables(evidence_root)
        (out_dir / "heldout_g1_recovery.json").write_text(
            json.dumps(recovery.to_dict(), indent=1, sort_keys=True), encoding="utf-8"
        )
        exact_outcomes = recovery.outcomes
        print(
            f"  {len(recovery.records)} cases, "
            f"searches_run={recovery.searches_run}, "
            f"pysr_imported={recovery.pysr_imported}",
            flush=True,
        )

    print("running restored primary analysis ...", flush=True)
    analysis = analyze_sealed_partition(
        evidence_root, null_threshold, exact_g1_outcomes=exact_outcomes
    )
    primary = analysis.to_dict()
    (out_dir / "heldout_restored_analysis.json").write_text(
        json.dumps(primary, indent=1, sort_keys=True), encoding="utf-8"
    )

    print("running independent recomputation ...", flush=True)
    independent = recompute_independently(evidence_root, null_threshold)
    disagreements = compare_to_primary(independent, primary)
    (out_dir / "heldout_independent_recomputation.json").write_text(
        json.dumps(
            {
                "result": independent.to_dict(),
                "disagreements_vs_primary": disagreements,
                "disagreement_count": len(disagreements),
            },
            indent=1,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print()
    print(f"  endpoint denominators : {primary['endpoint_denominators']}")
    print(
        f"  G1 ({primary['g1']['mode']:11s}): {primary['g1']['competent']}/"
        f"{primary['g1']['denominator']}  wilson_lower="
        f"{primary['g1']['wilson_lower_95']:.6f}  gate_passed="
        f"{primary['g1']['gate_passed']}"
    )
    print(
        f"  G2                     : {primary['g2']['successes']}/"
        f"{primary['g2']['denominator']}  wilson_lower="
        f"{primary['g2']['wilson_lower_95']:.6f}  gate_passed="
        f"{primary['g2']['gate_passed']}"
    )
    print(
        f"  G3                     : {primary['g3']['violations']}/"
        f"{primary['g3']['denominator']} violations  wilson_upper="
        f"{primary['g3']['wilson_upper_95']:.6f}  gate_passed="
        f"{primary['g3']['gate_passed']}"
    )
    print(
        f"  Gate 7                 : {primary['gate7']['reached']} reached, "
        f"{primary['gate7']['passed']} pass, "
        f"{primary['gate7']['passed_via_ceiling_waiver_only']} via waiver"
    )
    print(
        f"  Gate 8                 : {primary['gate8']['reached']} reached, "
        f"{primary['gate8']['passed']} pass"
    )
    print(f"  independent disagreements: {len(disagreements)}")
    for item in disagreements:
        print(f"    {item}")
    print()
    print(f"  decision: {primary['decision']}")

    return 1 if disagreements else 0


if __name__ == "__main__":
    raise SystemExit(main())
