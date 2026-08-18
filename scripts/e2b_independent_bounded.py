#!/usr/bin/env python3
"""AGENT_4 bounded-determinacy variant.

Same three-state bounding argument as the frozen side, but running through
AGENT 4's INDEPENDENT machinery -- rc5_selection.select_row_label for retention
and rc5_selection.group_and_select for the cross-seed representative -- so the
independence of the replication is preserved. A class is reported only when it
is invariant over every resolution of the UNRESOLVED rows.
"""
from __future__ import annotations
import json, sys, time, signal
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUD = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(AUD))
CKPT = AUD / "_ckpt_independent_bounded"

import pandas as pd
from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.g2_contract import (
    TRUTH_FAMILIES, G2Event, classify_discovered_family, classify_family_match,
    classify_support, evaluate_g2_event, extract_effective_support, truth_support_for_case)
from muru.paper_benchmark.generator import generate_case
from muru.paper_benchmark.rc5_selection import (
    RetainedCandidate, SeedSelection, SeedExecutionFailure, SeedNoCandidate,
    group_and_select, select_row_label)

FRONTS = ROOT / "results" / "e2b_macos_fullfront_replay_20260818" / "fronts"
SEEDS_PER_CASE = 30
CORRECT, INCORRECT, UNRESOLVED = "CORRECT", "INCORRECT", "UNRESOLVED"


class _Cap(BaseException):
    """BaseException: g2_contract's `except Exception` handlers must not swallow the cap."""


def _alarm(s, f): raise _Cap()


def g2_state(expr: str, ts, tf, cap_s: int, memo: dict) -> str:
    if not expr: return INCORRECT
    key = (expr, ts, tf)
    if key in memo: return memo[key]
    signal.signal(signal.SIGALRM, _alarm); signal.setitimer(signal.ITIMER_REAL, cap_s)
    try:
        ev = evaluate_g2_event(
            classify_support(extract_effective_support(expr), ts),
            classify_family_match(classify_discovered_family(expr), tf))
        r = CORRECT if ev == G2Event.SUCCESS else INCORRECT
    except _Cap:
        r = UNRESOLVED
    except Exception:
        r = UNRESOLVED
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    memo[key] = r
    return r


def retained_row(rows):
    frame = pd.DataFrame({"complexity": [r.get("complexity") for r in rows],
                          "equation": [r.get("equation") for r in rows],
                          "loss": [r.get("loss") for r in rows],
                          "score": [r.get("score") for r in rows]})
    try:
        return rows[int(select_row_label(frame))], None
    except (SeedExecutionFailure, SeedNoCandidate) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def classify(rep_ok, front_any, ret_any):
    if rep_ok: return "SUCCESS"
    if not front_any: return "NEVER_ON_FRONT"
    if ret_any: return "LOST_IN_CROSS_SEED"
    return "LOST_IN_RETENTION"


def process_case(case_id: str, cap_s: int = 5) -> dict:
    t0 = time.time()
    truth = generate_case(case_id).truth
    ts, tf = truth_support_for_case(truth), truth.mathematical_family
    memo: dict = {}
    case_dir = FRONTS / case_id.replace("|", "_")
    fronts = {}
    for p in sorted(case_dir.glob("*.jsonl")):
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        if rows: fronts[int(rows[0]["_seed_ordinal"])] = rows

    front_lo = front_hi = ret_lo = ret_hi = 0
    unresolved = 0; total = 0
    selections = []; seed_errors = []
    for k in range(SEEDS_PER_CASE):
        rows = fronts.get(k, [])
        if not rows: continue
        anyc = anyu = False
        for r in rows:
            e = r.get("equation", "")
            if not e: continue
            total += 1
            st = g2_state(e, ts, tf, cap_s, memo)
            if st == CORRECT: anyc = True
            elif st == UNRESOLVED: anyu = True; unresolved += 1
        front_lo += 1 if anyc else 0
        front_hi += 1 if (anyc or anyu) else 0

        row, err = retained_row(rows)
        seed_val = int(rows[0]["_seed"])
        if row is None:
            seed_errors.append(f"seed_ordinal={k}: {err}")
            selections.append(SeedSelection(k=k, seed=seed_val,
                              status=SeedStatus.COMPLETED_NO_CANDIDATE, error_message=err or ""))
            continue
        rst = g2_state(row.get("equation", ""), ts, tf, cap_s, memo)
        if rst == CORRECT: ret_lo += 1; ret_hi += 1
        elif rst == UNRESOLVED: ret_hi += 1
        selections.append(SeedSelection(k=k, seed=seed_val,
            status=SeedStatus.COMPLETED_WITH_CANDIDATES,
            candidate=RetainedCandidate(k=k, seed=seed_val,
                expression_string=str(row.get("equation", "")),
                complexity=int(row.get("complexity", 0)),
                valid_r2=float("nan"), invalid_fraction=float("nan"),
                candidate_test_r2=float("nan"))))

    cross = group_and_select(selections, selection_denominator=SEEDS_PER_CASE)
    rep_expr = cross.representative.expression_string if cross.representative else ""
    rep_state = g2_state(rep_expr, ts, tf, cap_s, memo) if rep_expr else INCORRECT

    rep_opts = [True] if rep_state == CORRECT else ([False] if rep_state == INCORRECT else [False, True])
    classes = {classify(a, b, c) for a, b, c in product(
        rep_opts, sorted({front_lo > 0, front_hi > 0}), sorted({ret_lo >= 1, ret_hi >= 1}))}
    det = len(classes) == 1
    out = {"case_id": case_id, "determined": det,
           "direct_class": classes.pop() if det else None,
           "possible_classes": None if det else sorted(classes),
           "seeds_with_correct_on_front": front_lo,
           "seeds_with_correct_on_front_upper": front_hi,
           "seeds_with_retained_correct": ret_lo,
           "seeds_with_retained_correct_upper": ret_hi,
           "independent_selection_count": cross.selection_count,
           "independent_representative_expression": rep_expr,
           "representative_state": rep_state,
           "representative_correct": rep_state == CORRECT,
           "unresolved_rows": unresolved, "total_rows": total,
           "voting_seeds": cross.voting_seeds,
           "valid": True, "invalid_reason": "", "seed_errors": seed_errors,
           "wall_seconds": round(time.time() - t0, 1)}
    CKPT.mkdir(parents=True, exist_ok=True)
    (CKPT / (case_id.replace("|", "_") + ".json")).write_text(json.dumps(out))
    print(f"[a4-bounded] {case_id} -> {out['direct_class'] or out['possible_classes']} "
          f"(unresolved {unresolved}/{total}, {out['wall_seconds']}s)", flush=True)
    return out


if __name__ == "__main__":
    import argparse, subprocess, os
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ap = argparse.ArgumentParser()
    ap.add_argument("--case"); ap.add_argument("--cap", type=int, default=5)
    ap.add_argument("--all-cases", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.case:
        process_case(a.case, a.cap); sys.exit(0)
    import agent4_independent_evaluator as A
    ids = A.enumerate_g2_cases()
    CKPT.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in CKPT.glob("*.json")}
    todo = [c for c in ids if c.replace("|", "_") not in have]
    print(f"[a4-bounded] {len(todo)} case(s), cap={a.cap}s, workers={a.workers}", flush=True)
    def run(c):
        p = subprocess.run([sys.executable, "-u", __file__, "--case", c, "--cap", str(a.cap)],
                           capture_output=True, text=True,
                           env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
        return c, p.returncode, (p.stdout or "").strip().splitlines()[-1:], (p.stderr or "")[-300:]
    n = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(run, c) for c in todo]):
            c, rc, out, err = f.result(); n += 1
            print(f"[{n}/{len(todo)}] rc={rc} {out[0] if out else 'FAILED '+c+' '+err}", flush=True)
