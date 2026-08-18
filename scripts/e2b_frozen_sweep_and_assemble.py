#!/usr/bin/env python3
"""AGENT_3 sweep + assembler.

Two jobs, both pure execution tooling around the UNMODIFIED frozen evaluator:

  SWEEP     Run every case that still lacks a checkpoint, ONE AT A TIME, each in
            its OWN subprocess so it gets the whole machine's memory and so a
            kernel OOM kill cannot take down the parent or its siblings. This is
            the "isolate it, retry it on a dedicated worker, allow it to
            complete" path for pathologically expensive cases.

  ASSEMBLE  Build FROZEN_DIRECT_CLASSES.csv and
            FROZEN_EVALUATOR_EXECUTION_MANIFEST.json from the per-case
            checkpoints, so aggregation no longer depends on a single
            long-lived pool.map surviving to completion.

A case that cannot be completed is recorded as an explicit EXECUTION FAILURE and
is NEVER given a classification. A resource limit is not a scientific result.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
CKPT = OUT / "_ckpt_frozen"
REPLAY = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
FROZEN_SHA256 = "ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743"
FAILLOG = OUT / "_frozen_execution_failures.json"


def ck_path(case_id): return CKPT / (case_id.replace("|", "_") + ".json")


def run_one(case_id: str) -> dict:
    """Run exactly one case in a dedicated subprocess."""
    code = (
        "import sys,json;"
        f"sys.path.insert(0,{str(ROOT/'scripts')!r});sys.path.insert(0,{str(ROOT/'src')!r});"
        "import e2b_frozen_evaluator_cloud_runner as R;"
        "R._install_memo();"
        "import json as J;"
        f"r=R.process_case(({case_id!r}, R._reps().get({case_id!r})));"
        "print('RESULT_JSON'+J.dumps(r))"
    )
    t0 = time.time()
    p = subprocess.run([sys.executable, "-u", "-c", code],
                       capture_output=True, text=True,
                       env={**os.environ, "OMP_NUM_THREADS": "1",
                            "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
                            "NUMEXPR_NUM_THREADS": "1"})
    wall = time.time() - t0
    if p.returncode != 0 or not ck_path(case_id).exists():
        return {"case_id": case_id, "ok": False, "returncode": p.returncode,
                "wall_seconds": round(wall, 1),
                "killed_by_signal": (-p.returncode if p.returncode < 0 else None),
                "stderr_tail": (p.stderr or "")[-800:]}
    return {"case_id": case_id, "ok": True, "wall_seconds": round(wall, 1)}


def assemble() -> dict:
    import e2b_direct_evaluator as frozen
    case_ids = frozen.get_g2_case_ids()
    results, missing = [], []
    for cid in case_ids:
        p = ck_path(cid)
        if not p.exists():
            missing.append(cid); continue
        try:
            results.append(json.loads(p.read_text()))
        except json.JSONDecodeError:
            missing.append(cid)

    if missing:
        return {"COMPLETE": False, "MISSING": missing}

    attributions = [
        frozen.CaseAttribution(
            case_id=d["case_id"], direct_class=frozen.DirectClass(d["direct_class"]),
            seeds_with_correct_on_front=d["seeds_with_correct_on_front"],
            seeds_with_retained_correct=d["seeds_with_retained_correct"],
            representative_correct=d["representative_correct"],
            valid=d["valid"], invalid_reason=d["invalid_reason"],
        ) for d in results
    ]
    gate = frozen.evaluate_gate_1(attributions)
    counts = {k: 0 for k in ("SUCCESS", "NEVER_ON_FRONT", "LOST_IN_RETENTION", "LOST_IN_CROSS_SEED")}
    for d in results: counts[d["direct_class"]] += 1

    with open(OUT / "FROZEN_DIRECT_CLASSES.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["CASE_ID", "FROZEN_CLASS", "VALID", "DETAIL"])
        for d in results:
            detail = (f"seeds_with_correct_on_front={d['seeds_with_correct_on_front']};"
                      f"seeds_with_retained_correct={d['seeds_with_retained_correct']};"
                      f"representative_correct={d['representative_correct']}")
            if d.get("invalid_reason"): detail += f";invalid_reason={d['invalid_reason']}"
            w.writerow([d["case_id"], d["direct_class"], d["valid"], detail])

    actual = hashlib.sha256((ROOT / "scripts" / "e2b_direct_evaluator.py").read_bytes()).hexdigest()
    walls = [(d["case_id"], d.get("wall_seconds")) for d in results]
    manifest = {
        "schema": "muru-e2b-frozen-evaluator-execution-manifest-1.1.0",
        "agent": "AGENT_3_FROZEN_EVALUATOR_REPRODUCTION",
        "FROZEN_EVALUATOR_PATH": "scripts/e2b_direct_evaluator.py",
        "FROZEN_EVALUATOR_COMMIT": "frozen at dabcb4b; recovered into worktree from 6b18dd8",
        "FROZEN_EVALUATOR_SHA256": actual,
        "FROZEN_EVALUATOR_SHA256_MATCHES_FROZEN_VALUE": actual == FROZEN_SHA256,
        "execution_wrapper": "scripts/e2b_frozen_evaluator_cloud_runner.py + scripts/e2b_frozen_sweep_and_assemble.py",
        "wrapper_semantics_changed": False,
        "wrapper_techniques": [
            "one process per case (maxtasksperchild=1, memory reclaimed per case)",
            "memoisation of is_row_g2_correct on its full argument tuple (pure function)",
            "per-case JSON checkpointing",
            "pathologically expensive cases isolated onto a dedicated full-memory subprocess",
            "aggregation decoupled from pool.map so one lost worker cannot block the result",
        ],
        "timeout_applied": None,
        "memory_cap_applied": None,
        "timeout_policy": "NO timeout and NO memory cap influences classification. g2_contract contains no authoritative timeout. An expensive case is isolated and allowed to run to completion; a case that cannot complete is recorded as an explicit execution failure and never classified.",
        "host": {"os": os.uname().sysname, "release": os.uname().release,
                 "arch": os.uname().machine, "cpu_count": os.cpu_count()},
        "corpus": {"cases": len(case_ids),
                   "front_rows_total": sum(d.get("front_rows_total", 0) or 0 for d in results)},
        "slowest_cases": sorted([{"case_id": c, "wall_seconds": w} for c, w in walls],
                                key=lambda x: -(x["wall_seconds"] or 0))[:10],
        "peak_rss_mb_top": sorted([{"case_id": d["case_id"], "peak_rss_mb": d.get("peak_rss_mb")}
                                   for d in results if d.get("peak_rss_mb")],
                                  key=lambda x: -x["peak_rss_mb"])[:10],
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
        "FROZEN_EVALUATOR_COMPLETE": sum(counts.values()) == 144 and all(d["valid"] for d in results),
    }
    (OUT / "FROZEN_EVALUATOR_EXECUTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    return {"COMPLETE": True, "counts": counts, "gate_1": gate.to_dict(),
            "COUNT_SUM": sum(counts.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent dedicated subprocesses; each case still gets its own process")
    ap.add_argument("--retry-failed", action="store_true",
                    help="re-attempt previously failed cases (use with --workers 1 for full memory)")
    ap.add_argument("--assemble", action="store_true")
    a = ap.parse_args()

    import e2b_direct_evaluator as frozen
    case_ids = frozen.get_g2_case_ids()

    if a.sweep:
        pending = [c for c in case_ids if not ck_path(c).exists()]
        prior = json.loads(FAILLOG.read_text()) if FAILLOG.exists() else []
        failed_before = {f["case_id"] for f in prior}
        if not a.retry_failed:
            pending = [c for c in pending if c not in failed_before]
        print(f"[sweep] {len(pending)} case(s) to run, workers={a.workers}", flush=True)

        from concurrent.futures import ThreadPoolExecutor, as_completed
        failures = list(prior)
        done_n = 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(run_one, c): c for c in pending}
            for fut in as_completed(futs):
                r = fut.result(); done_n += 1
                free_mb = int(os.popen("free -m | awk '/^Mem:/{print $7}'").read().strip() or 0)
                if r["ok"]:
                    print(f"[{done_n}/{len(pending)}] ok {r['case_id']} "
                          f"({r['wall_seconds']}s, free={free_mb}MB)", flush=True)
                    failures = [f for f in failures if f["case_id"] != r["case_id"]]
                else:
                    print(f"[{done_n}/{len(pending)}] FAILED {r['case_id']} rc={r['returncode']} "
                          f"signal={r.get('killed_by_signal')} after {r['wall_seconds']}s", flush=True)
                    failures = [f for f in failures if f["case_id"] != r["case_id"]] + [r]
                FAILLOG.write_text(json.dumps(failures, indent=2))

    if a.assemble:
        res = assemble()
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
