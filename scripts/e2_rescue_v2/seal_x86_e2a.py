#!/usr/bin/env python
"""Seal the x86-only E2a corpus and recompute the routing decision from it alone.

Reads ONLY results/e2/run_x86_e2a_v1. Never reads, merges, or falls back to any
historical ARM/macOS result directory. Verifies 540 accounted-for world IDs, no
duplicates, no torn records, then recomputes Gate 2 with the frozen, unmodified
routing_lock.evaluate_gate2 over this corpus's own stage counts.
"""
from __future__ import annotations
import json, hashlib, sys, glob, collections
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from muru.v2_calibration import e2_worlds
from muru.v2_calibration.e2_rescue_v2.routing_lock import evaluate_gate2

OUT = REPO / "results/e2/run_x86_e2a_v1"

def main() -> None:
    expected = {e2_worlds.world_id(*w) for w in e2_worlds.iter_worlds()}
    assert len(expected) == 540

    # --- world records ---
    records, torn_w = [], 0
    for f in sorted(OUT.glob("worlds_shard_*.jsonl")):
        for ln in f.read_text().splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                records.append(json.loads(ln))
            except Exception:
                torn_w += 1
    ids = [r["world_id"] for r in records]
    dups = [k for k, v in collections.Counter(ids).items() if v > 1]
    completed = set(ids)

    # --- execution errors (orchestration failures, NOT scientific timeouts) ---
    errors, torn_e = [], 0
    for f in sorted(OUT.glob("errors_shard_*.jsonl")):
        for ln in f.read_text().splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                errors.append(json.loads(ln))
            except Exception:
                torn_e += 1
    error_ids = {e["world_id"] for e in errors} - completed

    # --- candidate rows + scientific timeouts ---
    crows, torn_c, simplify_timeouts = 0, 0, 0
    worlds_with_st = set()
    for f in sorted(OUT.glob("candidates_shard_*.jsonl")):
        for ln in f.read_text().splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                torn_c += 1
                continue
            crows += 1
            if r.get("canonicalization_status") == "SIMPLIFY_TIMEOUT":
                simplify_timeouts += 1
                worlds_with_st.add(r["world_id"])

    unresolved = sorted(expected - completed - error_ids)

    # --- routing, from THIS corpus only ---
    stages = collections.Counter(r.get("first_loss_stage") for r in records)
    a_n, b_n, c_n, d_n = stages.get("A", 0), stages.get("B", 0), stages.get("C", 0), stages.get("D", 0)
    r_remaining = len(unresolved) + len(error_ids)
    lock = evaluate_gate2(a_n, b_n, c_n, d_n, r_remaining)

    # --- file manifest ---
    manifest = {}
    for f in sorted(OUT.glob("*.jsonl")):
        manifest[f.name] = {"sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                            "bytes": f.stat().st_size}

    seal = {
        "schema_version": "v2_e2a_x86_seal_v1",
        "corpus": "results/e2/run_x86_e2a_v1",
        "corpus_is_x86_only": True,
        "historical_worlds_merged": False,
        "scheduled": 540,
        "completed": len(completed),
        "duplicates": len(dups),
        "duplicate_ids": sorted(dups),
        "torn_world_records": torn_w,
        "torn_candidate_records": torn_c,
        "torn_error_records": torn_e,
        "candidate_rows": crows,
        "scientific_timeouts_simplify_timeout_rows": simplify_timeouts,
        "worlds_containing_simplify_timeout": len(worlds_with_st),
        "execution_errors": len(error_ids),
        "execution_error_ids": sorted(error_ids),
        "unresolved": len(unresolved),
        "unresolved_ids": unresolved,
        "accounted_for": len(completed) + len(error_ids) + len(unresolved),
        "all_540_accounted_for": len(completed) + len(error_ids) + len(unresolved) == 540,
        "population_matches_frozen_definition": completed | error_ids | set(unresolved) == expected,
        "world_id_set_sha256": hashlib.sha256("\n".join(sorted(completed)).encode()).hexdigest(),
        "routing": {
            "n_classified": a_n + b_n + c_n + d_n,
            "r_remaining": r_remaining,
            "state": lock.state,
            "note": lock.note,
        },
        "file_manifest": manifest,
    }
    (OUT / "X86_E2A_SEAL.json").write_text(json.dumps(seal, indent=1))

    print(f"scheduled=540 completed={len(completed)} errors={len(error_ids)} unresolved={len(unresolved)}")
    print(f"duplicates={len(dups)} torn_w={torn_w} torn_c={torn_c} candidate_rows={crows}")
    print(f"scientific SIMPLIFY_TIMEOUT rows={simplify_timeouts} across {len(worlds_with_st)} worlds")
    print(f"all_540_accounted_for={seal['all_540_accounted_for']}")
    print(f"ROUTING STATE (x86-only corpus) = {lock.state}")
    print(f"  n_classified={a_n+b_n+c_n+d_n} r_remaining={r_remaining}")

if __name__ == "__main__":
    main()
