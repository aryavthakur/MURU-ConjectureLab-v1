#!/usr/bin/env python3
"""AGENT_4 sweep + assembler -- same robustness treatment as Agent 3.

multiprocessing.Pool loses a task permanently when a worker is OOM-killed, and
pool.map then blocks forever, so aggregation must not depend on it. Each case
runs in its OWN subprocess; a case that cannot complete is recorded as an
explicit execution failure and is NEVER given a classification.
"""
from __future__ import annotations

import argparse, csv, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUD = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(AUD))

CKPT = AUD / "_ckpt_independent"
REPLAY = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
FAILLOG = AUD / "_independent_execution_failures.json"


def ck_path(case_id): return CKPT / (case_id.replace("|", "_") + ".json")


def run_one(case_id: str) -> dict:
    code = (
        "import sys;"
        f"sys.path.insert(0,{str(ROOT/'src')!r});sys.path.insert(0,{str(AUD)!r});"
        "import agent4_independent_evaluator as A;"
        f"A.process_case({case_id!r})"
    )
    t0 = time.time()
    p = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                       env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                            "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    wall = time.time() - t0
    if p.returncode != 0 or not ck_path(case_id).exists():
        return {"case_id": case_id, "ok": False, "returncode": p.returncode,
                "wall_seconds": round(wall, 1),
                "killed_by_signal": (-p.returncode if p.returncode < 0 else None),
                "stderr_tail": (p.stderr or "")[-800:]}
    return {"case_id": case_id, "ok": True, "wall_seconds": round(wall, 1)}


def assemble():
    import agent4_independent_evaluator as A
    case_ids = A.enumerate_g2_cases()
    results, missing = [], []
    for cid in case_ids:
        p = ck_path(cid)
        if not p.exists(): missing.append(cid); continue
        try: results.append(json.loads(p.read_text()))
        except json.JSONDecodeError: missing.append(cid)
    if missing:
        return {"COMPLETE": False, "MISSING": missing, "have": len(results)}

    report = json.loads((REPLAY / "E2B_FULLFRONT_REPLAY_REPORT.json").read_text())
    sealed = {d["case_id"]: (d["selection_count_replayed"], d["representative_replayed"])
              for d in report.get("comparison_details", [])}
    counts = {k: 0 for k in ("SUCCESS", "NEVER_ON_FRONT", "LOST_IN_RETENTION", "LOST_IN_CROSS_SEED")}
    sel_match = rep_match = 0
    for d in results:
        counts[d["direct_class"]] += 1
        sc, sr = sealed.get(d["case_id"], (None, None))
        d["matches_sealed_selection_count"] = (d.get("independent_selection_count") == sc)
        d["matches_sealed_representative_expression"] = (d.get("independent_representative_expression") == sr)
        sel_match += bool(d["matches_sealed_selection_count"])
        rep_match += bool(d["matches_sealed_representative_expression"])

    with open(AUD / "INDEPENDENT_DIRECT_CLASSES.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "direct_class", "seeds_with_correct_on_front",
                    "seeds_with_retained_correct", "independent_selection_count",
                    "independent_representative_expression", "representative_correct",
                    "matches_sealed_selection_count", "matches_sealed_representative_expression",
                    "valid", "invalid_reason"])
        for d in results:
            w.writerow([d["case_id"], d["direct_class"], d["seeds_with_correct_on_front"],
                        d["seeds_with_retained_correct"], d.get("independent_selection_count"),
                        d.get("independent_representative_expression"), d["representative_correct"],
                        d["matches_sealed_selection_count"], d["matches_sealed_representative_expression"],
                        d["valid"], d.get("invalid_reason", "")])

    summary = {
        "schema": "muru-e2b-independent-replication-1.1.0",
        "agent": "AGENT_4_INDEPENDENT_ATTRIBUTION_REPLICATION",
        "implementation": "audit/e2b_definitive_cloud_adjudication_20260818/agent4_independent_evaluator.py",
        "execution_wrapper": "scripts/e2b_independent_sweep_and_assemble.py (subprocess per case)",
        "shares_with_agent3": "src/muru/paper_benchmark/g2_contract.py only (the frozen G2 definition itself)",
        "timeout_applied": None, "memory_cap_applied": None,
        "cases": len(results), "counts": counts, "COUNT_SUM": sum(counts.values()),
        "DIRECT_RETENTION": counts["LOST_IN_RETENTION"],
        "DIRECT_GENERATION": counts["NEVER_ON_FRONT"],
        "DIRECT_THIRD_CLASS": counts["SUCCESS"] + counts["LOST_IN_CROSS_SEED"],
        "INVALID_CASES": sum(1 for d in results if not d["valid"]),
        "selection_count_matches_sealed": f"{sel_match}/{len(results)}",
        "representative_matches_sealed": f"{rep_match}/{len(results)}",
    }
    (AUD / "INDEPENDENT_REPLICATION_SUMMARY.json").write_text(json.dumps(summary, indent=2))
    return {"COMPLETE": True, **{k: summary[k] for k in
            ("counts", "COUNT_SUM", "selection_count_matches_sealed", "representative_matches_sealed")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--retry-failed", action="store_true")
    a = ap.parse_args()
    import agent4_independent_evaluator as A
    case_ids = A.enumerate_g2_cases()

    if a.sweep:
        pending = [c for c in case_ids if not ck_path(c).exists()]
        prior = json.loads(FAILLOG.read_text()) if FAILLOG.exists() else []
        if not a.retry_failed:
            bad = {f["case_id"] for f in prior}; pending = [c for c in pending if c not in bad]
        print(f"[sweep-A4] {len(pending)} case(s), workers={a.workers}", flush=True)
        from concurrent.futures import ThreadPoolExecutor, as_completed
        failures = list(prior); n = 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(run_one, c): c for c in pending}
            for fut in as_completed(futs):
                r = fut.result(); n += 1
                free_mb = int(os.popen("free -m | awk '/^Mem:/{print $7}'").read().strip() or 0)
                tag = "ok" if r["ok"] else f"FAILED rc={r['returncode']} sig={r.get('killed_by_signal')}"
                print(f"[{n}/{len(pending)}] {tag} {r['case_id']} ({r['wall_seconds']}s, free={free_mb}MB)", flush=True)
                failures = [f for f in failures if f["case_id"] != r["case_id"]]
                if not r["ok"]: failures.append(r)
                FAILLOG.write_text(json.dumps(failures, indent=2))

    if a.assemble:
        print(json.dumps(assemble(), indent=2))


if __name__ == "__main__":
    main()
