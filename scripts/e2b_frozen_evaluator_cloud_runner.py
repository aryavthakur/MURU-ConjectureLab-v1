#!/usr/bin/env python3
"""AGENT_3: FROZEN_EVALUATOR_REPRODUCTION -- execution wrapper.

Executes the EXACT frozen evaluator (scripts/e2b_direct_evaluator.py,
SHA-256 ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743)
against the authoritative 4,320-front macOS/ARM64 corpus.

WHAT THIS WRAPPER DOES (execution tooling only):
  * one OS process per case (144 independent units), capped at N workers
  * memoises is_row_g2_correct on its FULL argument tuple
    (expression_string, truth_support, truth_family) -- a pure function of
    exactly those three inputs, so caching cannot change any return value,
    only how many times an identical computation is repeated
  * per-case JSON checkpoints so an interrupted run resumes without redoing work
  * per-case wall-time recording so expensive cases are visible, never hidden

WHAT THIS WRAPPER DOES NOT DO:
  * it does not alter, reimplement, or wrap the CLASSIFIER. Every classification
    decision is produced by calling the frozen module's own
    is_row_g2_correct / evaluate_seed_front / classify_case / evaluate_gate_1.
  * it applies NO timeout. The frozen semantics (g2_contract.simplify) contain
    no authoritative timeout, so no performance timeout may exist here either:
    an expensive expression is allowed to run to completion. A timeout is never
    interpreted as a classification.
"""
from __future__ import annotations

import argparse
import csv
import functools
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import e2b_direct_evaluator as frozen  # the exact frozen module, unmodified

REPLAY = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
FRONTS = REPLAY / "fronts"
OUTDIR = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
CKPT = OUTDIR / "_ckpt_frozen"

FROZEN_SHA256 = "ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743"


def _install_memo():
    """Per-process memo around the frozen is_row_g2_correct.

    Keyed on the complete argument tuple; the underlying frozen function is
    called verbatim on a cache miss and its result returned unchanged.
    """
    cache = {}
    orig = frozen.is_row_g2_correct

    @functools.wraps(orig)
    def wrapped(expression_string, truth_support, truth_family):
        key = (expression_string, truth_support, truth_family)
        if key not in cache:
            cache[key] = orig(expression_string, truth_support, truth_family)
        return cache[key]

    wrapped._orig = orig
    wrapped._cache = cache
    frozen.is_row_g2_correct = wrapped


def _worker_init():
    _install_memo()


def _ckpt_path(case_id: str) -> Path:
    return CKPT / (case_id.replace("|", "_") + ".json")


def process_case(args):
    case_id, rep_expr = args
    ck = _ckpt_path(case_id)
    if ck.exists():
        try:
            return json.loads(ck.read_text())
        except json.JSONDecodeError:
            ck.unlink()  # torn checkpoint: recompute

    t0 = time.time()
    from muru.paper_benchmark.generator import generate_case
    from muru.paper_benchmark.g2_contract import TRUTH_FAMILIES, truth_support_for_case

    truth = generate_case(case_id).truth

    if truth.mathematical_family not in TRUTH_FAMILIES:
        att = frozen.CaseAttribution(
            case_id=case_id,
            direct_class=frozen.DirectClass.NEVER_ON_FRONT,
            seeds_with_correct_on_front=0,
            seeds_with_retained_correct=0,
            representative_correct=False,
            valid=False,
            invalid_reason=f"Truth family {truth.mathematical_family!r} not in TRUTH_FAMILIES",
        )
        out = att.to_dict()
        out["wall_seconds"] = time.time() - t0
        ck.write_text(json.dumps(out))
        return out

    truth_support = truth_support_for_case(truth)
    truth_family = truth.mathematical_family

    case_fronts = frozen.load_case_fronts(FRONTS, case_id)
    if not case_fronts:
        att = frozen.CaseAttribution(
            case_id=case_id,
            direct_class=frozen.DirectClass.NEVER_ON_FRONT,
            seeds_with_correct_on_front=0,
            seeds_with_retained_correct=0,
            representative_correct=False,
            valid=False,
            invalid_reason="No front artifacts found for this case",
        )
        out = att.to_dict()
        out["wall_seconds"] = time.time() - t0
        ck.write_text(json.dumps(out))
        return out

    seed_results = []
    for ordinal in range(frozen.SEEDS_PER_CASE):
        rows = case_fronts.get(ordinal, [])
        if not rows:
            seed_results.append(frozen.SeedFrontResult(
                seed_ordinal=ordinal, seed=-1, front_size=0,
                correct_on_front=False, retained_correct=False, correct_row_count=0,
            ))
        else:
            seed_results.append(
                frozen.evaluate_seed_front(rows, truth_support, truth_family)
            )

    att = frozen.classify_case(case_id, seed_results, rep_expr, truth_support, truth_family)
    out = att.to_dict()
    out["wall_seconds"] = time.time() - t0
    out["front_rows_total"] = sum(len(r) for r in case_fronts.values())
    out["seeds_loaded"] = len(case_fronts)
    ck.write_text(json.dumps(out))
    print(f"[done] {case_id} -> {out['direct_class']} ({out['wall_seconds']:.1f}s)", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=20)
    args = ap.parse_args()

    CKPT.mkdir(parents=True, exist_ok=True)

    # provenance: confirm the frozen evaluator on disk is the frozen evaluator
    import hashlib
    actual = hashlib.sha256((ROOT / "scripts" / "e2b_direct_evaluator.py").read_bytes()).hexdigest()
    if actual != FROZEN_SHA256:
        raise SystemExit(f"FROZEN EVALUATOR HASH MISMATCH: {actual} != {FROZEN_SHA256}")

    report = json.loads((REPLAY / "E2B_FULLFRONT_REPLAY_REPORT.json").read_text())
    reps = {d["case_id"]: d.get("representative_replayed") for d in report.get("comparison_details", [])}

    case_ids = frozen.get_g2_case_ids()
    assert len(case_ids) == 144, f"expected 144 G2 cases, got {len(case_ids)}"

    work = [(cid, reps.get(cid)) for cid in case_ids]
    t0 = time.time()
    with Pool(processes=args.workers, initializer=_worker_init) as pool:
        results = pool.map(process_case, work, chunksize=1)
    wall = time.time() - t0

    order = {c: i for i, c in enumerate(case_ids)}
    results.sort(key=lambda d: order[d["case_id"]])

    attributions = [
        frozen.CaseAttribution(
            case_id=d["case_id"],
            direct_class=frozen.DirectClass(d["direct_class"]),
            seeds_with_correct_on_front=d["seeds_with_correct_on_front"],
            seeds_with_retained_correct=d["seeds_with_retained_correct"],
            representative_correct=d["representative_correct"],
            valid=d["valid"],
            invalid_reason=d["invalid_reason"],
        )
        for d in results
    ]
    gate = frozen.evaluate_gate_1(attributions)

    counts = {k: 0 for k in ("SUCCESS", "NEVER_ON_FRONT", "LOST_IN_RETENTION", "LOST_IN_CROSS_SEED")}
    for d in results:
        counts[d["direct_class"]] += 1

    manifest = {
        "schema": "muru-e2b-frozen-evaluator-execution-manifest-1.0.0",
        "agent": "AGENT_3_FROZEN_EVALUATOR_REPRODUCTION",
        "FROZEN_EVALUATOR_PATH": "scripts/e2b_direct_evaluator.py",
        "FROZEN_EVALUATOR_COMMIT": "dabcb4b (frozen at execution freeze); recovered into worktree from 6b18dd8",
        "FROZEN_EVALUATOR_SHA256": actual,
        "FROZEN_EVALUATOR_SHA256_MATCHES_FROZEN_VALUE": actual == FROZEN_SHA256,
        "execution_wrapper": "scripts/e2b_frozen_evaluator_cloud_runner.py",
        "wrapper_semantics_changed": False,
        "wrapper_techniques": [
            "one process per case (144 independent units)",
            "memoisation of is_row_g2_correct on its full argument tuple (pure function)",
            "per-case JSON checkpointing",
        ],
        "timeout_applied": None,
        "timeout_policy": "NO timeout applied. g2_contract contains no authoritative timeout, so no performance timeout is permitted to influence classification. Expensive expressions run to completion.",
        "host": {
            "os": os.uname().sysname,
            "release": os.uname().release,
            "arch": os.uname().machine,
            "cpu_count": os.cpu_count(),
            "workers": args.workers,
        },
        "corpus": {
            "fronts_dir": str(FRONTS.relative_to(ROOT)),
            "cases": len(case_ids),
            "front_files": sum(1 for _ in FRONTS.rglob("*.jsonl")),
            "front_rows_total": sum(d.get("front_rows_total", 0) for d in results),
        },
        "wall_seconds_total": wall,
        "slowest_cases": sorted(
            [{"case_id": d["case_id"], "wall_seconds": d.get("wall_seconds")} for d in results],
            key=lambda x: -(x["wall_seconds"] or 0),
        )[:10],
        "class_counts": counts,
        "FROZEN_SUCCESS": counts["SUCCESS"],
        "FROZEN_LOST_IN_CROSS_SEED": counts["LOST_IN_CROSS_SEED"],
        "FROZEN_LOST_IN_RETENTION": counts["LOST_IN_RETENTION"],
        "FROZEN_NEVER_ON_FRONT": counts["NEVER_ON_FRONT"],
        "FROZEN_DIRECT_RETENTION": gate.direct_retention,
        "FROZEN_DIRECT_GENERATION": gate.direct_generation,
        "FROZEN_DIRECT_THIRD_CLASS": gate.direct_third_class,
        "COUNT_SUM": sum(counts.values()),
        "COUNT_SUM_EQUALS_144": sum(counts.values()) == 144,
        "INVALID_CASES": sum(1 for d in results if not d["valid"]),
        "gate_1": gate.to_dict(),
        "FROZEN_EVALUATOR_COMPLETE": (
            sum(counts.values()) == 144 and all(d["valid"] for d in results)
        ),
    }

    (OUTDIR / "FROZEN_EVALUATOR_EXECUTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2))

    with open(OUTDIR / "FROZEN_DIRECT_CLASSES.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["CASE_ID", "FROZEN_CLASS", "VALID", "DETAIL"])
        for d in results:
            detail = (
                f"seeds_with_correct_on_front={d['seeds_with_correct_on_front']};"
                f"seeds_with_retained_correct={d['seeds_with_retained_correct']};"
                f"representative_correct={d['representative_correct']}"
            )
            if d["invalid_reason"]:
                detail += f";invalid_reason={d['invalid_reason']}"
            w.writerow([d["case_id"], d["direct_class"], d["valid"], detail])

    print(json.dumps({
        "wall_seconds": round(wall, 1),
        "counts": counts,
        "gate_1": gate.to_dict(),
        "COUNT_SUM": sum(counts.values()),
    }, indent=2))


if __name__ == "__main__":
    main()
