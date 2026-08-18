#!/usr/bin/env python3
"""Escalate the handful of expressions that leave a case INDETERMINATE.

For each indeterminate case, find the specific front rows that hit the cost cap
and evaluate ONLY those, one per dedicated subprocess with a large budget. This
is the "isolate it, retry it on a dedicated worker, allow it to complete" remedy
applied at expression granularity, where it is actually affordable.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
REPLAY = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
FRONTS = REPLAY / "fronts"
RESULT = OUT / "_escalated_expressions.json"


def find_unresolved(case_id: str, cap_s: int = 5):
    """Re-run the bound and capture WHICH expressions hit the cap."""
    import e2b_direct_evaluator as frozen
    import e2b_bounded_determinacy_evaluator as BD
    from muru.paper_benchmark.generator import generate_case
    from muru.paper_benchmark.g2_contract import truth_support_for_case
    truth = generate_case(case_id).truth
    ts, tf = truth_support_for_case(truth), truth.mathematical_family
    memo = {}
    case_fronts = frozen.load_case_fronts(FRONTS, case_id)
    out = []
    for ordinal in range(frozen.SEEDS_PER_CASE):
        rows = case_fronts.get(ordinal, [])
        if not rows: continue
        best_i, best = 0, float("-inf")
        for i, r in enumerate(rows):
            s = r.get("score", float("-inf"))
            if s is None: continue
            if float(s) > best: best, best_i = float(s), i
        for i, r in enumerate(rows):
            e = r.get("equation", "")
            if not e: continue
            if BD.resolve_row(e, ts, tf, cap_s, memo) == BD.UNRESOLVED:
                out.append({"seed_ordinal": ordinal, "row_index": i,
                            "is_argmax_score_row": i == best_i, "equation": e})
    return out, str(ts), tf


def eval_one(expr: str, cap_s: int):
    code = (
        "import sys,json;"
        f"sys.path.insert(0,{str(ROOT/'scripts')!r});sys.path.insert(0,{str(ROOT/'src')!r});"
        "import e2b_direct_evaluator as F;"
        f"r=F.is_row_g2_correct({expr!r}, __import__('muru.paper_benchmark.g2_contract',fromlist=['x']).truth_support_for_case("
        "__import__('muru.paper_benchmark.generator',fromlist=['x']).generate_case(CASE).truth), FAM);"
        "print('VERDICT'+json.dumps(r))"
    )
    return code


def main():
    import e2b_bounded_determinacy_evaluator as BD
    cases = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    cap_big = int(os.environ.get("ESCALATION_CAP", "1800"))
    results = json.loads(RESULT.read_text()) if RESULT.exists() else {}
    for cid in cases:
        rows, ts, tf = find_unresolved(cid)
        print(f"[{cid}] {len(rows)} unresolved expression(s)", flush=True)
        recs = []
        for r in rows:
            code = (
                "import sys,json;"
                f"sys.path.insert(0,{str(ROOT/'scripts')!r});sys.path.insert(0,{str(ROOT/'src')!r});"
                "import e2b_direct_evaluator as F;"
                "from muru.paper_benchmark.generator import generate_case;"
                "from muru.paper_benchmark.g2_contract import truth_support_for_case;"
                f"t=generate_case({cid!r}).truth;"
                f"v=F.is_row_g2_correct({r['equation']!r}, truth_support_for_case(t), t.mathematical_family);"
                "print('VERDICT'+json.dumps(bool(v)))"
            )
            t0 = time.time()
            p = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                               timeout=cap_big,
                               env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}) \
                if True else None
            wall = round(time.time() - t0, 1)
            verdict = None
            for line in (p.stdout or "").splitlines():
                if line.startswith("VERDICT"):
                    verdict = json.loads(line[len("VERDICT"):])
            rec = {**r, "verdict": verdict, "returncode": p.returncode, "wall_seconds": wall}
            print(f"   seed={r['seed_ordinal']} argmax={r['is_argmax_score_row']} "
                  f"verdict={verdict} rc={p.returncode} {wall}s  {r['equation'][:60]}", flush=True)
            recs.append(rec)
        results[cid] = recs
        RESULT.write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
