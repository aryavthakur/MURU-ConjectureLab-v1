#!/usr/bin/env python
"""Merges N per-shard full_corpus_parity_audit.py output files into the
single operator-facing MURU_V2_E2_REPLAY_PARITY.json summary. Only sums
counts and concatenates opaque detail lists -- never recomputes or
inspects any scientific field itself.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def merge(shard_paths: list[Path]) -> dict:
    shards = [json.loads(p.read_text()) for p in shard_paths]

    n_completed_snapshot = shards[0]["N_COMPLETED_SNAPSHOT"]
    n_replayable_global = shards[0]["N_REPLAYABLE_GLOBAL"]
    for s in shards:
        assert s["N_COMPLETED_SNAPSHOT"] == n_completed_snapshot, "shards disagree on snapshot -- not from the same run"
        assert s["N_REPLAYABLE_GLOBAL"] == n_replayable_global, "shards disagree on global replayable count"

    n_match = sum(s["N_MATCH"] for s in shards)
    n_mismatch = sum(s["N_MISMATCH"] for s in shards)
    n_error = sum(s["ERROR_COUNT"] for s in shards)
    n_covered = sum(s["N_REPLAYABLE_THIS_SHARD"] for s in shards)

    det_shards = [s for s in shards if s["N_DETERMINISM_CHECKED"] > 0]
    n_det_checked = sum(s["N_DETERMINISM_CHECKED"] for s in det_shards)
    n_det_match = sum(s["N_DETERMINISM_MATCH"] for s in det_shards)

    mismatch_detail = [d for s in shards for d in s.get("mismatch_detail", [])]
    error_detail = [d for s in shards for d in s.get("error_detail", [])]

    summary = {
        "N_COMPLETED_SNAPSHOT": n_completed_snapshot,
        "N_REPLAYABLE": n_replayable_global,
        "N_SHARD_COVERAGE_CHECK": n_covered,  # must equal N_REPLAYABLE for a valid merge
        "N_MATCH": n_match,
        "N_MISMATCH": n_mismatch,
        "ERROR_COUNT": n_error,
        "PARITY_PASS": bool(n_covered == n_replayable_global and n_match == n_replayable_global
                             and n_mismatch == 0 and n_error == 0),
        "N_DETERMINISM_CHECKED": n_det_checked,
        "N_DETERMINISM_MATCH": n_det_match,
        "DETERMINISM_PASS": bool(n_det_checked > 0 and n_det_match == n_det_checked),
        "n_shards_merged": len(shards),
        "mismatch_detail": mismatch_detail,
        "error_detail": error_detail,
    }
    if n_covered != n_replayable_global:
        summary["WARNING"] = (
            f"shard coverage {n_covered} != global replayable count {n_replayable_global} -- "
            "not every world was actually attempted; PARITY_PASS forced False"
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-file", action="append", required=True, dest="shard_files")
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    summary = merge([Path(f) for f in args.shard_files])
    Path(args.out).write_text(json.dumps(summary, indent=2))

    print(f"N_COMPLETED_SNAPSHOT: {summary['N_COMPLETED_SNAPSHOT']}")
    print(f"N_REPLAYABLE: {summary['N_REPLAYABLE']}")
    print(f"N_MATCH: {summary['N_MATCH']}")
    print(f"N_MISMATCH: {summary['N_MISMATCH']}")
    print(f"ERROR_COUNT: {summary['ERROR_COUNT']}")
    print(f"PARITY_PASS: {summary['PARITY_PASS']}")
    print(f"N_DETERMINISM_CHECKED: {summary['N_DETERMINISM_CHECKED']}")
    print(f"N_DETERMINISM_MATCH: {summary['N_DETERMINISM_MATCH']}")
    print(f"DETERMINISM_PASS: {summary['DETERMINISM_PASS']}")
    if "WARNING" in summary:
        print(f"WARNING: {summary['WARNING']}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
