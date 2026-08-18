#!/usr/bin/env python
"""Targeted, isolated retry for worlds that ERRORed (timed out) during the
full-corpus audit -- same discipline as Part X's poison-world handling:
never silently mark a slow-but-maybe-successful world as permanently
failed without at least one patient, isolated retry. Re-identifies the
opaque IDs from the audit's error_detail by recomputing the SAME salted
hash over the frozen snapshot's real world_ids (one-way hash forward, not
reversed) -- this script alone briefly holds the real world_id for these
specific worlds, only to re-run them; it prints and writes nothing but
opaque IDs and match/error outcomes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_classify  # noqa: E402
import full_corpus_parity_audit as fca  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", action="append", required=True, dest="dirs")
    parser.add_argument("--frozen-snapshot-file", type=str, required=True)
    parser.add_argument("--error-opaque-ids", type=str, required=True, nargs="+")
    parser.add_argument("--timeout-seconds", type=float, default=600.0)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    dirs = [Path(d) for d in args.dirs]
    snapshot = json.loads(Path(args.frozen_snapshot_file).read_text())
    target_opaque = set(args.error_opaque_ids)

    # Re-identify: forward-hash every candidate world_id, match against the
    # target opaque set. Never reverses the hash.
    wid_by_opaque = {fca._opaque(wid): wid for wid in snapshot["all_replayable_ids"]}
    targets = {op: wid_by_opaque[op] for op in target_opaque if op in wid_by_opaque}
    missing = target_opaque - set(targets.keys())
    if missing:
        print(f"WARNING: {len(missing)} opaque id(s) not found in frozen snapshot: {sorted(missing)}")

    dirs_valid = fca._valid_result_dirs(dirs)
    outcomes = fca._load_outcomes(dirs_valid)
    cand_index = fca._build_candidate_index(dirs_valid)

    pool = fca._SafePool(fca._replay_worker)
    results = []
    try:
        for opaque_id, wid in targets.items():
            rec = outcomes[wid]
            payload = (wid, rec["family"], rec["regime"], rec["noise_level"], rec["replicate"],
                       cand_index.get(wid, {}))
            result, err = pool.run(payload, timeout=args.timeout_seconds)
            if err is not None or result is None or not result.get("ok"):
                results.append({"opaque_id": opaque_id, "outcome": "ERROR",
                                 "category": err or f"WORKER_EXCEPTION:{result.get('error_type') if result else 'unknown'}"})
                print(f"  {opaque_id}: ERROR ({results[-1]['category']})", flush=True)
                continue

            exhaustive_stage = rec["first_loss_stage"]
            stage_match = result["first_loss_stage"] == exhaustive_stage
            if exhaustive_stage in ("A", "B"):
                rep_g2_match = rep_te_match = True
            else:
                rep_g2_match = result["representative_g2_correct"] == rec["representative_g2_correct"]
                rep_te_match = True if exhaustive_stage == "E" else (
                    result["representative_truth_equivalent"] == rec["representative_truth_equivalent"])
            is_match = stage_match and rep_g2_match and rep_te_match
            results.append({"opaque_id": opaque_id, "outcome": "MATCH" if is_match else "MISMATCH"})
            print(f"  {opaque_id}: {'MATCH' if is_match else 'MISMATCH'}", flush=True)
    finally:
        pool.close()
        e2_classify.shutdown()

    n_match = sum(1 for r in results if r["outcome"] == "MATCH")
    n_mismatch = sum(1 for r in results if r["outcome"] == "MISMATCH")
    n_error = sum(1 for r in results if r["outcome"] == "ERROR")
    summary = {
        "N_RETRIED": len(results), "N_MATCH": n_match, "N_MISMATCH": n_mismatch, "N_ERROR": n_error,
        "N_NOT_FOUND": len(missing), "results": results,
    }
    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(f"N_RETRIED: {summary['N_RETRIED']}  N_MATCH: {n_match}  N_MISMATCH: {n_mismatch}  N_ERROR: {n_error}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
