#!/usr/bin/env python3
"""E2b BOUNDED-DETERMINACY evaluator.

WHY THIS EXISTS
---------------
The frozen evaluator (scripts/e2b_direct_evaluator.py, SHA-256 ee285a8b...)
calls g2_contract's sympy.simplify with NO cost cap. On ~30% of the Held-out
corpus that call does not terminate in practical time: sweep children sat at
99.9% CPU with <1 GB RSS for over an hour without completing a single case,
and two cases were OOM-killed above 25 GB. befca0d s2.10 states the reason
outright -- "simplify is unbounded in the worst case."

A per-expression cap is therefore unavoidable to make progress. But frozen
authority forbids the obvious shortcut: befca0d s2.10 requires a cap be
"recorded as an explicit SIMPLIFY_TIMEOUT status rather than silently becoming
None", and the master task forbids a timeout ever standing in for a class.

WHAT THIS DOES INSTEAD
----------------------
It never converts a timeout into a classification. Each front row is resolved to
one of THREE states:

    CORRECT | INCORRECT | UNRESOLVED     (UNRESOLVED = cap reached; NOT a class)

It then asks whether the frozen four-way class is INVARIANT over every possible
resolution of the UNRESOLVED rows, by evaluating the frozen decision tree at
both extremes (all UNRESOLVED treated as correct, and all treated as incorrect)
across the three booleans the tree actually reads:

    representative_correct , seeds_with_correct_on_front>0 , seeds_with_retained_correct>=1

If every consistent assignment yields the SAME class, that class is DETERMINED:
it is the frozen evaluator's own answer, established with certainty, and the
unresolved expressions provably cannot change it. If assignments disagree, the
case is reported as INDETERMINATE_UNDER_BOUND -- an honest statement that the
frozen semantics cannot be evaluated for that case within finite cost, never a
guessed class.

The decision tree is monotone in "more rows correct", so the two extremes bound
every intermediate assignment; the enumeration below is over the <=3 booleans
that remain undetermined, which is exhaustive.
"""
from __future__ import annotations

import argparse, json, os, signal, sys, time
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
CKPT = OUT / "_ckpt_bounded"
REPLAY = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
FRONTS = REPLAY / "fronts"

CORRECT, INCORRECT, UNRESOLVED = "CORRECT", "INCORRECT", "UNRESOLVED"


class _Cap(BaseException):
    """Derived from BaseException DELIBERATELY.

    g2_contract wraps sympy.simplify in `except Exception: return None` (lines
    164, 207, 268, 295, 306, 317, 330 -- verified: there is no bare `except:`).
    An Exception-derived cap would therefore be SWALLOWED by the contract and
    silently become None -> SUPPORT_UNRESOLVED -> not-correct: precisely the
    "timeout silently becoming None" that befca0d s2.10 forbids and that would
    let a cost limit masquerade as a classification. BaseException propagates
    past every one of those handlers, so a cap is always visible as UNRESOLVED.
    """
    pass


def _alarm(signum, frame):
    raise _Cap()


def resolve_row(expr: str, truth_support, truth_family, cap_s: int, memo: dict) -> str:
    """Frozen is_row_g2_correct under a cost cap. Cap => UNRESOLVED, never a class."""
    key = (expr, truth_support, truth_family)
    if key in memo:
        return memo[key]
    import e2b_direct_evaluator as frozen
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, cap_s)
    try:
        r = CORRECT if frozen.is_row_g2_correct(expr, truth_support, truth_family) else INCORRECT
    except _Cap:
        r = UNRESOLVED
    except Exception:
        # the frozen contract itself catches its own exceptions and returns None
        # (-> not correct); anything reaching here is a genuine evaluation error
        r = UNRESOLVED
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    memo[key] = r
    return r


def classify_from_booleans(rep_ok: bool, front_any: bool, retained_any: bool) -> str:
    """The frozen four-way tree from e2b_direct_evaluator.classify_case, verbatim."""
    if rep_ok:
        return "SUCCESS"
    if not front_any:
        return "NEVER_ON_FRONT"
    if retained_any:
        return "LOST_IN_CROSS_SEED"
    return "LOST_IN_RETENTION"


def process_case(case_id: str, cap_s: int) -> dict:
    import e2b_direct_evaluator as frozen
    from muru.paper_benchmark.generator import generate_case
    from muru.paper_benchmark.g2_contract import TRUTH_FAMILIES, truth_support_for_case

    t0 = time.time()
    truth = generate_case(case_id).truth
    if truth.mathematical_family not in TRUTH_FAMILIES:
        return {"case_id": case_id, "determined": True, "direct_class": "NEVER_ON_FRONT",
                "valid": False, "invalid_reason": f"Truth family {truth.mathematical_family!r} not in TRUTH_FAMILIES"}

    truth_support = truth_support_for_case(truth)
    truth_family = truth.mathematical_family
    memo: dict = {}

    case_fronts = frozen.load_case_fronts(FRONTS, case_id)
    reps = json.loads((REPLAY / "E2B_FULLFRONT_REPLAY_REPORT.json").read_text())
    rep_expr = {d["case_id"]: d.get("representative_replayed")
                for d in reps.get("comparison_details", [])}.get(case_id)

    # --- representative ---
    rep_state = resolve_row(rep_expr, truth_support, truth_family, cap_s, memo) if rep_expr else INCORRECT

    # --- per seed: correct_on_front and retained_correct, each as a 3-state ---
    front_lo = front_hi = 0          # seeds with a correct row: lower / upper bound
    ret_lo = ret_hi = 0              # seeds whose argmax(score) row is correct
    unresolved_rows = 0
    total_rows = 0
    for ordinal in range(frozen.SEEDS_PER_CASE):
        rows = case_fronts.get(ordinal, [])
        if not rows:
            continue
        # frozen argmax(score) selection, verbatim
        best_i, best = 0, float("-inf")
        for i, r in enumerate(rows):
            s = r.get("score", float("-inf"))
            if s is None:
                continue
            s = float(s)
            if s > best:
                best, best_i = s, i

        any_c = False; any_u = False; ret_state = INCORRECT
        for i, r in enumerate(rows):
            e = r.get("equation", "")
            if not e:
                continue
            total_rows += 1
            st = resolve_row(e, truth_support, truth_family, cap_s, memo)
            if st == UNRESOLVED:
                unresolved_rows += 1
            if i == best_i:
                ret_state = st
            if st == CORRECT:
                any_c = True
            elif st == UNRESOLVED:
                any_u = True

        front_lo += 1 if any_c else 0
        front_hi += 1 if (any_c or any_u) else 0
        if ret_state == CORRECT:
            ret_lo += 1; ret_hi += 1
        elif ret_state == UNRESOLVED:
            ret_hi += 1

    # --- which of the three booleans are still open? ---
    rep_opts = [True] if rep_state == CORRECT else ([False] if rep_state == INCORRECT else [False, True])
    front_opts = sorted({front_lo > 0, front_hi > 0})
    ret_opts = sorted({ret_lo >= 1, ret_hi >= 1})

    classes = {classify_from_booleans(a, b, c)
               for a, b, c in product(rep_opts, front_opts, ret_opts)}

    determined = len(classes) == 1
    out = {
        "case_id": case_id,
        "cap_seconds": cap_s,
        "determined": determined,
        "direct_class": classes.pop() if determined else None,
        "possible_classes": None if determined else sorted(classes),
        "representative_state": rep_state,
        "seeds_with_correct_on_front_lower": front_lo,
        "seeds_with_correct_on_front_upper": front_hi,
        "seeds_with_retained_correct_lower": ret_lo,
        "seeds_with_retained_correct_upper": ret_hi,
        "unresolved_rows": unresolved_rows,
        "total_rows": total_rows,
        "valid": True,
        "invalid_reason": None,
        "wall_seconds": round(time.time() - t0, 1),
    }
    CKPT.mkdir(parents=True, exist_ok=True)
    (CKPT / (case_id.replace("|", "_") + ".json")).write_text(json.dumps(out))
    print(f"[bounded] {case_id} -> {out['direct_class'] or out['possible_classes']} "
          f"(unresolved {unresolved_rows}/{total_rows}, {out['wall_seconds']}s)", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=5, help="per-expression cost cap in seconds")
    ap.add_argument("--case", help="single case id")
    ap.add_argument("--all-pending", action="store_true")
    ap.add_argument("--all-cases", action="store_true",
                    help="bound ALL 144 cases, including those the uncapped frozen run already "
                         "completed, so those become a large-scale validation of the bound")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    import e2b_direct_evaluator as frozen
    if a.case:
        process_case(a.case, a.cap); return

    ids = frozen.get_g2_case_ids()
    CKPT.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in CKPT.glob("*.json")}
    frozen_done = set() if a.all_cases else {p.stem for p in (OUT / "_ckpt_frozen").glob("*.json")}
    todo = [c for c in ids
            if c.replace("|", "_") not in have and c.replace("|", "_") not in frozen_done]
    print(f"[bounded] {len(todo)} case(s) to bound, cap={a.cap}s, workers={a.workers}", flush=True)

    import subprocess
    from concurrent.futures import ThreadPoolExecutor, as_completed
    def run(c):
        p = subprocess.run([sys.executable, "-u", __file__, "--case", c, "--cap", str(a.cap)],
                           capture_output=True, text=True,
                           env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
        return c, p.returncode, (p.stdout or "").strip().splitlines()[-1:] , (p.stderr or "")[-300:]
    n = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run, c) for c in todo]
        for f in as_completed(futs):
            c, rc, out, err = f.result(); n += 1
            print(f"[{n}/{len(todo)}] rc={rc} {out[0] if out else ('FAILED ' + c + ' ' + err)}", flush=True)


if __name__ == "__main__":
    main()
