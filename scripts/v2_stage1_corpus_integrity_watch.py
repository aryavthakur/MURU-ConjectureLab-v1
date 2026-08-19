#!/usr/bin/env python3
"""Incremental Stage 1 corpus-integrity watcher — execution-only, not scientific.

Built to run CONCURRENTLY with Stage 1's search (scripts/v2_stage1_calibration_run.py)
so that when the last of the 57,960 searches finishes, integrity checking on the
already-completed worlds is largely done rather than starting cold.

Deliberately scoped to what is safe to check on an INCOMPLETE, still-being-written
corpus, per the speed-optimization authorization's own boundary:

    "Do NOT perform any routing, scientific scoring, qualification decision, or
    result-dependent adaptation early if the protocol requires the complete
    sealed corpus first."

This script does exactly four things, all on already-written, immutable per-world
checkpoint files (never on a file mid-write -- `run_world`'s atomic
`tmp.replace(ck)` means a checkpoint is either fully absent or fully valid JSON,
so there is no torn-write case for this watcher to defend against, but it still
checks JSON validity defensively):

    1. schema check      -- every CalFrontRow field present, nullable set respected
    2. duplicate check    -- exactly one checkpoint file per case_id, no extras
    3. missing check      -- which of the 1,932 expected case_ids have no checkpoint yet
    4. admissibility check -- every row's row-level admissibility is DECISION_ADMISSIBLE

It does NOT read truth, does NOT score, does NOT compute rho_bot/rho_top, does NOT
touch any routing predicate. Those remain strictly post-completion, per protocol.

Run:
    --once           one pass over whatever checkpoints currently exist, print + write
                      INTEGRITY_WATCH.json, exit
    --watch SECONDS  loop, re-checking only NEW checkpoints since the last pass,
                      sleeping SECONDS between polls (default 30), until all 1,932
                      expected checkpoints are accounted for or interrupted
"""
from __future__ import annotations
import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "results" / "v2_calibration_surface"
CKPT = OUT / "_ckpt_worlds"


def _expected_case_ids() -> list[str]:
    from muru.paper_benchmark import calibration_surface as cs
    return cs.iter_calibration_case_ids()


def _required_fields() -> tuple[list[str], set[str]]:
    from muru.v2_calibration import e2c_search
    required = [f.name for f in dataclasses.fields(e2c_search.CalFrontRow)]
    nullable = {"effective_support", "template_key", "canonical_expression",
                "discovered_family", "coefficient_value", "noise_sd"}
    return required, nullable


def check_one(path: Path, required: list[str], nullable: set[str]) -> dict:
    """Never raises. A malformed checkpoint is reported, not fatal to the watcher."""
    try:
        w = json.loads(path.read_text())
    except json.JSONDecodeError as ex:
        return {"path": str(path), "valid_json": False, "error": str(ex)}
    missing = []
    for row in w.get("rows", []):
        missing += [f for f in required if f not in row or
                    (row[f] is None and f not in nullable)]
    n_seeds = len(w.get("seeds", []))
    admiss = sorted({r.get("admissibility") for r in w.get("rows", [])})
    return {
        "case_id": w.get("case_id"),
        "valid_json": True,
        "n_seeds": n_seeds,
        "n_seeds_expected": 30,
        "seeds_ok": n_seeds == 30,
        "n_rows": len(w.get("rows", [])),
        "missing_or_null_fields": sorted(set(missing)),
        "schema_ok": not missing,
        "admissibility_row_level": admiss,
        "admissibility_ok": admiss in ([], ["DECISION_ADMISSIBLE"]),
        "content_hash_present": bool(w.get("content_hash")),
    }


def run_pass(expected_ids: list[str], required: list[str], nullable: set[str],
             already_checked: dict) -> dict:
    present = {}
    dupes_by_stem = {}
    for p in CKPT.glob("*.json"):
        stem = p.stem
        dupes_by_stem.setdefault(stem, []).append(p)
        if stem in already_checked:
            present[stem] = already_checked[stem]
            continue
        present[stem] = check_one(p, required, nullable)

    expected_stems = {cid.replace("|", "_") for cid in expected_ids}
    present_stems = set(present)
    missing_stems = expected_stems - present_stems
    unexpected_stems = present_stems - expected_stems
    duplicate_files = {k: [str(x) for x in v] for k, v in dupes_by_stem.items() if len(v) > 1}

    bad = [v for v in present.values() if not v.get("valid_json") or not v.get("schema_ok")
           or not v.get("seeds_ok") or not v.get("admissibility_ok")]

    result = {
        "schema": "muru-v2-stage1-corpus-integrity-watch-1.0.0",
        "expected_worlds": len(expected_ids),
        "checkpoints_present": len(present_stems),
        "checkpoints_missing": len(missing_stems),
        "checkpoints_unexpected": sorted(unexpected_stems),
        "duplicate_files": duplicate_files,
        "n_bad": len(bad),
        "bad_examples": bad[:20],
        "COMPLETE": len(missing_stems) == 0 and len(unexpected_stems) == 0,
        "INTEGRITY_OK_SO_FAR": not bad and not duplicate_files and not unexpected_stems,
    }
    return result, present


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", type=float, default=0.0,
                    help="poll interval in seconds; 0 (default) means run once")
    a = ap.parse_args()

    expected_ids = _expected_case_ids()
    required, nullable = _required_fields()
    CKPT.mkdir(parents=True, exist_ok=True)

    checked: dict = {}
    while True:
        result, checked = run_pass(expected_ids, required, nullable, checked)
        (OUT / "INTEGRITY_WATCH.json").write_text(json.dumps(result, indent=2))
        print(f"[WATCH] {result['checkpoints_present']}/{result['expected_worlds']} "
              f"present, {result['n_bad']} bad, ok_so_far={result['INTEGRITY_OK_SO_FAR']}",
              flush=True)
        if not a.watch or result["COMPLETE"]:
            break
        time.sleep(a.watch)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
