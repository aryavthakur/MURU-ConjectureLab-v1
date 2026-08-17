#!/usr/bin/env python
"""Operator-facing CLI: exact routing-lock monitor for the frozen E4a gate.

Reads world-outcome records (the SAME `worlds_shard_*.jsonl` schema
`scripts/e2_run_shard.py` writes, specifically the `first_loss_stage` and
`world_id` fields -- nothing else) from one or more directories, counts how
many of the 540 E2a cases carry each of A/B/C/D (E is read too, only to
compute n_classified correctly), and prints ONLY the lock state.

DELIBERATELY DOES NOT PRINT counts, rates, or per-family/per-cell
breakdowns -- see routing_lock.py's module docstring and
MURU_V2_E2_ROUTING_LOCK_THEORY.md section 5. This script itself never
executes against the live E2a run's real (still-incomplete) output during
the rescue-v2 design task -- see that document's section 6 for why, and
`tests/test_routing_lock_monitor_synthetic.py` for the synthetic-data
demonstration used instead, mirroring the outcome-blind interim
characterization's own "dry run on schema-faithful synthetic data"
precedent (`muru-e2-interim-characterization`, step 9).

Usage:
    routing_lock_monitor.py --world-outcome-dir DIR [DIR ...] [--total 540]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from muru.v2_calibration.e2_rescue_v2.routing_lock import evaluate_gate2_opaque  # noqa: E402

STAGES = ("A", "B", "C", "D", "E")


def _count_stages(dirs: list[Path]) -> dict[str, int]:
    """Internal only -- the caller of this module's CLI entry point never
    sees this dict; see `main()`. Deduplicates by world_id across
    directories/files exactly as `e2_run_shard._already_done` does, so a
    world persisted in more than one place (e.g. quarantine-recovery
    duplicates, see E2_EXECUTION_DEVIATION.md §16) is not double
    counted."""
    seen: dict[str, str] = {}
    for d in dirs:
        for path in sorted(d.glob("worlds_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    wid = rec.get("world_id")
                    stage = rec.get("first_loss_stage")
                    if wid is None or stage not in STAGES:
                        continue
                    seen[wid] = stage  # last write wins; duplicates are byte-identical per §16
    counts = {s: 0 for s in STAGES}
    for stage in seen.values():
        counts[stage] += 1
    return counts, len(seen)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-outcome-dir", action="append", required=True, dest="dirs")
    parser.add_argument("--total", type=int, default=540)
    args = parser.parse_args()

    dirs = [Path(d) for d in args.dirs]
    counts, n_classified = _count_stages(dirs)
    r_remaining = args.total - n_classified
    if r_remaining < 0:
        raise SystemExit(
            f"n_classified ({n_classified}) exceeds --total ({args.total}) -- "
            "duplicate world_id across directories not fully resolved, refusing to report"
        )

    state = evaluate_gate2_opaque(
        a_n=counts["A"], b_n=counts["B"], c_n=counts["C"], d_n=counts["D"],
        r_remaining=r_remaining,
    )

    # The ONLY things printed. No A/B/C/D counts, no rates.
    print(f"ROUTING_LOCK_STATE: {state}")
    print(f"N_CLASSIFIED: {n_classified}/{args.total}")
    print(f"R_REMAINING: {r_remaining}")


if __name__ == "__main__":
    main()
