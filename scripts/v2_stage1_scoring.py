#!/usr/bin/env python3
"""Stage 1 post-hoc scoring pass — protocol v3 sections 17, 20 and 25.

A SEPARATE PROCESS THE SEARCH NEVER SEES (section 16). It joins the seven
truth-derived columns onto the persisted fronts and evaluates the frozen four-way
partition under the determinacy bound.

Every definition is IMPORTED, never reimplemented (section 17):
    g2_contract.classify_support / classify_family_match / evaluate_g2_event
    rc5_selection.group_and_select / select_row_label
    identity_contract.template_key
`g2_contract.py` is byte-unchanged. Only the control flow AROUND unresolved rows
differs, and that difference is strictly conservative: it can refuse to decide, never
decide differently.

THE DETERMINACY BOUND (section 25.1), two evaluations rather than 2^U:

    rho_bot : every UNRESOLVED row assigned INCORRECT
    rho_top : every UNRESOLVED row assigned CORRECT

Sound because the three reach predicates are MONOTONE in the row labels:
  * reach_front and reach_retain are disjunctions over row labels;
  * the cross-seed representative is selected by `template_key` grouping and NEVER
    reads g2_correct;
  * retained_by_argmax_score is a score comparison, also label-independent.
So a resolution can only move a world WEAKLY LATER in the frozen order A < B < C/D < E.

A world whose class differs between the two evaluations is INDETERMINATE. Its still
unresolved rows are DECISIVE and are escalated to completion with NO time cap
(section 25.2 tier 2). `INDETERMINATE_WORLDS == 0` is precondition P6'; a residual
decisive-unresolved row after uncapped escalation is a RESOURCE event and routes to
RUN_INCOMPLETE_RESOURCE_EXHAUSTION, which is NOT a terminal (section 25.4).
"""
from __future__ import annotations
import argparse, collections, hashlib, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "results" / "v2_calibration_surface"
CKPT = OUT / "_ckpt_worlds"

# ---------------------------------------------------------------------------------
# TIER-2 ESCALATION SUBPROCESS ISOLATION (execution-safety, not scientific).
#
# Pre-fix, `main()`'s escalate path called `CanonicalisationTable.escalate()`
# in-process, protected only by `e2c_classify.py`'s internal SIGPROF/ITIMER_PROF
# (self-delivered, not OS-enforced) and with NO memory bound at all -- exactly the
# D1/D2 defect class `e2a_instrument_diagnostic.py` was hostile-review-repaired to
# fix on the Stage 0 side, left unfixed here. A single pathological DECISIVE
# expression at tier 2 (uncapped by design, section 25.2) could exhaust host
# memory and take the entire scoring pass down with it, silently losing every
# already-checkpointed world in the same process.
#
# FIX: mirror `e2a_instrument_diagnostic.py`'s proven `_PAYLOAD`/`eval_one`
# pattern exactly. `e2c_classify.canonicalise()` is NOT edited or reimplemented
# -- it runs byte-identical, just inside a subprocess bounded by FP-3/FP-4's
# already-frozen scoring-tier-2 envelope (`STAGE1_RESOURCE_PROFILE.json`:
# 23.5 GiB RLIMIT_AS, WORKER_COUNT 1 -- "uncapped in TIME and serial in MEMORY").
# A worker that OOMs, is kernel-SIGKILLed, hangs, or dies for any reason can only
# ever surface here as an UNRESOLVED entry with a typed reason (never crash the
# caller, never silently become a scientific label) -- and per-expression
# checkpointing means a crash mid-escalation loses at most the one in-flight
# expression, not already-completed work.
SCORING_TIER2_RSS_GIB = 23.5     # FP-3, frozen, STAGE1_RESOURCE_PROFILE.json
SCORING_TIER2_WORKERS = 1        # FP-4, frozen, STAGE1_RESOURCE_PROFILE.json

_CANON_PAYLOAD = r'''
import sys, json, resource
resource.setrlimit(resource.RLIMIT_AS, ({AS}, {AS}))
sys.path.insert(0, {SRC!r})
from muru.v2_calibration import e2c_classify
entry = e2c_classify.canonicalise({EXPR!r}, None, tier=2)
print("R" + json.dumps({{
    "expression_string": entry.expression_string,
    "canonicalization_status": entry.canonicalization_status,
    "canonical_expression": entry.canonical_expression,
    "effective_support": list(entry.effective_support) if entry.effective_support else None,
    "discovered_family": entry.discovered_family,
    "template_key_repr": entry.template_key_repr,
    "cpu_seconds": entry.cpu_seconds,
    "tier": entry.tier,
    "unresolved_reason": None,
}}))
'''


def _unresolved_entry(expr: str, reason: str) -> dict:
    return {"expression_string": expr, "canonicalization_status": "UNRESOLVED",
            "canonical_expression": None, "effective_support": None,
            "discovered_family": None, "template_key_repr": None,
            "cpu_seconds": 0.0, "tier": 2, "unresolved_reason": reason}


def canonicalise_isolated(expr: str) -> dict:
    """Subprocess-isolated tier-2 escalation of one expression. Never raises."""
    as_bytes = int(SCORING_TIER2_RSS_GIB * 1024**3)
    code = _CANON_PAYLOAD.format(AS=as_bytes, SRC=str(ROOT / "src"), EXPR=expr)
    try:
        p = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                           env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    except OSError as ex:
        return _unresolved_entry(expr, f"SUBPROCESS_LAUNCH_FAILED:{type(ex).__name__}")
    for line in (p.stdout or "").splitlines():
        if line.startswith("R"):
            try:
                d = json.loads(line[1:])
            except json.JSONDecodeError:
                return _unresolved_entry(expr, "MALFORMED_OUTPUT")
            if d.get("expression_string") != expr:
                return _unresolved_entry(expr, "MALFORMED_OUTPUT")  # D11-analogue
            return d
    # D11-analogue: a dead subprocess must say WHY, exactly as in e2a_instrument_
    # diagnostic.py -- without stderr, an environment fault is indistinguishable
    # from a kernel OOM kill, which is precisely the attribution that matters.
    err = (p.stderr or "").strip().splitlines()
    tail = err[-1][:200] if err else ""
    if p.returncode in (-9, 137):
        why = "KERNEL_OOM_KILL"
    elif "ModuleNotFoundError" in (p.stderr or "") or "ImportError" in (p.stderr or ""):
        why = "ENVIRONMENT_IMPORT_FAILURE"
    else:
        why = f"SUBPROCESS_DIED_rc{p.returncode}"
    return _unresolved_entry(expr, f"{why}: {tail}" if tail else why)


def escalate_isolated(exprs: list[str], ckpt_dir: Path) -> dict[str, dict]:
    """Tier-2 escalation of `exprs`, subprocess-isolated and checkpointed per
    expression (keyed by sha256 of the expression string, since expression text
    is not a safe filename). Resumable: an expression already checkpointed is
    read back, not re-escalated -- material for uncapped tier 2, where a single
    expression's escalation cost is unbounded by design.

    De-duplicates `exprs` before dispatch: a repeated expression is escalated at
    most once. Caught by adversarial self-test -- without this, two identical
    DECISIVE expressions would race to write the SAME checkpoint file from two
    different pool threads, and (at `SCORING_TIER2_WORKERS > 1`) launch two
    redundant uncapped subprocesses for work that converges to one answer."""
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    def ckpt_path(e: str) -> Path:
        return ckpt_dir / (hashlib.sha256(e.encode()).hexdigest() + ".json")

    out: dict[str, dict] = {}
    todo = []
    for e in dict.fromkeys(exprs):        # de-dup, preserve first-seen order
        ck = ckpt_path(e)
        if ck.exists():
            try:
                out[e] = json.loads(ck.read_text())
                continue
            except json.JSONDecodeError:
                ck.unlink()
        todo.append(e)

    def run_one(e: str):
        d = canonicalise_isolated(e)
        ckpt_path(e).write_text(json.dumps(d))
        return e, d

    done = 0
    with ThreadPoolExecutor(max_workers=SCORING_TIER2_WORKERS) as ex:
        for fut in as_completed([ex.submit(run_one, e) for e in todo]):
            e, d = fut.result()
            out[e] = d
            done += 1
            if done % 5 == 0 or done == len(todo):
                print(f"[SCORING] tier-2 escalation {done}/{len(todo)} "
                      f"(+{len(exprs) - len(todo)} from checkpoint)", flush=True)
    return out


def scoring_preflight() -> None:
    """D12-analogue: verify the isolation subprocess can actually run BEFORE any
    real escalation, so an environment fault is never recorded as a spurious
    resource-exhaustion finding (exactly the failure mode e2a's own D12 closes)."""
    probe_as = int(SCORING_TIER2_RSS_GIB * 1024**3)
    probe = (f"import sys,resource\nresource.setrlimit(resource.RLIMIT_AS,({probe_as},{probe_as}))\n"
            f"sys.path.insert(0,{str(ROOT / 'src')!r})\nfrom muru.v2_calibration import e2c_classify\n"
            "import sympy\nprint('SCORING_PREFLIGHT_OK')\n")
    p = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=600,
                       env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    if "SCORING_PREFLIGHT_OK" not in (p.stdout or ""):
        sys.exit(f"[SCORING] PREFLIGHT FAILED for isolation subprocess (rc={p.returncode}).\n"
                 f"Refusing to run tier-2 escalation: an environment fault would be recorded\n"
                 f"as spurious UNRESOLVED entries indistinguishable from a genuine resource\n"
                 f"finding.\n{(p.stderr or '')[-2000:]}")
    print(f"[SCORING] preflight OK: isolation subprocess, "
         f"RLIMIT_AS={SCORING_TIER2_RSS_GIB}GiB, workers={SCORING_TIER2_WORKERS}", flush=True)


def _set_out(d: str) -> None:
    """Redirect output. Used ONLY for control runs, which must never write into the
    surface directory -- a control is not a surface (P10)."""
    global OUT, CKPT
    OUT = Path(d); CKPT = OUT / "_ckpt_worlds"
    CKPT.mkdir(parents=True, exist_ok=True)

CORRECT, INCORRECT, UNRESOLVED = "CORRECT", "INCORRECT", "UNRESOLVED"


def g2_correct_for_row(entry: dict, truth) -> str:
    """resolution_state for one (row, world), from the section 25.3 canonicalisation
    table entry and the world's TruthRecord, via the byte-unchanged primitives.

    Note what is NOT done here: an UNRESOLVED canonicalisation does NOT null
    effective_support or discovered_family. Those are functions of the expression
    alone (section 25.3) and are always present when the expression parses. This is
    the X-3 repair; e2_classify.py:161-162 did the opposite and that is the defect
    Gate 1 adjudicated.
    """
    from muru.paper_benchmark.g2_contract import (
        classify_support, classify_family_match, evaluate_g2_event, G2Event,
    )
    if entry["canonicalization_status"] == "UNPARSEABLE":
        return INCORRECT                      # deterministic, host-invariant (section 24)
    supp = entry.get("effective_support")
    fam = entry.get("discovered_family")
    if supp is None:
        return UNRESOLVED
    try:
        ev = evaluate_g2_event(
            classify_support(frozenset(supp), truth.support),
            classify_family_match(fam, truth.family))
    except Exception:
        return UNRESOLVED
    return CORRECT if ev == G2Event.SUCCESS else INCORRECT


def classify_world(states: dict[int, list[tuple[int, str, bool]]],
                   assume_unresolved_correct: bool) -> str:
    """The FROZEN four-way partition, witness order from befca0d section 2.7 /
    MURU_V2_E2_PREDECLARATION section 6, applied verbatim:

        A  if n_correct_on_front == 0
        B  elif n_retained_correct == 0
        E  elif representative_g2_correct
        D  elif representative_truth_equivalent
        C  else

    `states[k]` is a list of (front_rank, resolution_state, retained_by_argmax_score).
    """
    def ok(s: str) -> bool:
        return s == CORRECT or (assume_unresolved_correct and s == UNRESOLVED)

    any_front = any(ok(s) for rows in states.values() for _, s, _ in rows)
    if not any_front:
        return "A"                                   # NEVER_ON_FRONT
    any_retained = any(ok(s) and ret for rows in states.values() for _, s, ret in rows)
    if not any_retained:
        return "B"                                   # LOST_IN_RETENTION
    return "CD"                                      # LOST_IN_CROSS_SEED or SUCCESS


def representative_correct(world: dict, resolution: dict[str, str],
                           assume_unresolved_correct: bool) -> bool:
    """Whether the CROSS-SEED REPRESENTATIVE is g2-correct, using the frozen
    grouping. `group_and_select` never reads g2_correct, so the representative is
    the same object under both resolutions -- which is what makes the bound two
    evaluations rather than 2^U."""
    from muru.paper_benchmark.rc5_selection import (
        RetainedCandidate, SeedSelection, group_and_select,
    )
    from muru.paper_benchmark.calibration_contract import SeedStatus

    sels = []
    for s in world["seeds"]:
        if s["status"] != "COMPLETED_WITH_FRONT":
            sels.append(SeedSelection(k=s["k"], seed=s["seed"],
                                      status=SeedStatus.COMPLETED_NO_CANDIDATE))
            continue
        row = next((r for r in world["rows"]
                    if r["seed_ordinal_k"] == s["k"] and r["retained_by_argmax_score"]), None)
        if row is None:
            sels.append(SeedSelection(k=s["k"], seed=s["seed"],
                                      status=SeedStatus.COMPLETED_NO_CANDIDATE))
            continue
        sels.append(SeedSelection(
            k=s["k"], seed=s["seed"], status=SeedStatus.COMPLETED_WITH_CANDIDATES,
            candidate=RetainedCandidate(
                k=s["k"], seed=s["seed"], expression_string=row["expression_string"],
                complexity=row["engine_complexity"], valid_r2=row["valid_r2"],
                invalid_fraction=row["invalid_fraction"],
                candidate_test_r2=row["test_r2"])))
    try:
        css = group_and_select(sels)
    except Exception:
        return False
    rep = getattr(css, "winning", None)
    if rep is None or not getattr(rep, "members", ()):
        return False
    expr = rep.members[0].expression_string
    st = resolution.get(expr, UNRESOLVED)
    return st == CORRECT or (assume_unresolved_correct and st == UNRESOLVED)


def score_world(world: dict, truth_for) -> dict:
    truth = truth_for(world["case_id"])
    table = {e["expression_string"]: e for e in world["canonicalisation_table"]}
    resolution = {expr: g2_correct_for_row(e, truth) for expr, e in table.items()}

    states: dict[int, list[tuple[int, str, bool]]] = collections.defaultdict(list)
    for r in world["rows"]:
        states[r["seed_ordinal_k"]].append(
            (r["front_rank"], resolution.get(r["expression_string"], UNRESOLVED),
             bool(r["retained_by_argmax_score"])))

    out = {}
    for tag, assume in (("bot", False), ("top", True)):
        stage = classify_world(states, assume)
        if stage == "CD":
            stage = "E" if representative_correct(world, resolution, assume) else "CD"
        out[tag] = stage
    unresolved_exprs = sorted(e for e, s in resolution.items() if s == UNRESOLVED)
    return {
        "case_id": world["case_id"],
        "class_rho_bot": out["bot"], "class_rho_top": out["top"],
        "indeterminate": out["bot"] != out["top"],
        "n_rows": len(world["rows"]),
        "n_unresolved_rows": sum(1 for rows in states.values()
                                 for _, s, _ in rows if s == UNRESOLVED),
        "unresolved_expressions": unresolved_exprs,
        "reach_front_bot": classify_world(states, False) != "A",
        "reach_front_top": classify_world(states, True) != "A",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--escalate", action="store_true",
                    help="tier 2: re-canonicalise DECISIVE expressions with no cap")
    ap.add_argument("--out-dir", default="", help="control runs only; never the surface dir")
    a = ap.parse_args()
    if a.out_dir:
        _set_out(a.out_dir)
    scoring_preflight()

    from muru.paper_benchmark.calibration_surface import generate_calibration_case
    cache: dict[str, object] = {}

    def truth_for(case_id: str):
        if case_id not in cache:
            cache[case_id] = generate_calibration_case(case_id).truth
        return cache[case_id]

    files = sorted(CKPT.glob("*.json"))
    if not files:
        sys.exit("[SCORING] no world checkpoints; Stage 1 has not run.")
    scored = [score_world(json.loads(f.read_text()), truth_for) for f in files]

    indeterminate = [s for s in scored if s["indeterminate"]]
    subprocess_isolation_report = None
    if a.escalate and indeterminate:
        decisive = sorted({e for s in indeterminate for e in s["unresolved_expressions"]})
        print(f"[SCORING] tier 2: escalating {len(decisive)} DECISIVE expressions, uncapped, "
              f"subprocess-isolated (RLIMIT_AS={SCORING_TIER2_RSS_GIB}GiB, "
              f"workers={SCORING_TIER2_WORKERS})", flush=True)
        esc_ckpt = OUT / "_ckpt_escalation"
        esc = escalate_isolated(decisive, esc_ckpt)
        isolation_failures = collections.Counter(
            (d.get("unresolved_reason") or "").split(":")[0]
            for d in esc.values()
            if d["canonicalization_status"] == "UNRESOLVED" and d.get("unresolved_reason"))
        subprocess_isolation_report = {
            "n_escalated": len(esc),
            "n_isolation_detected_failures": sum(isolation_failures.values()),
            "isolation_failure_reasons": dict(isolation_failures),
        }
        for f in files:                       # write escalated entries back into the world
            w = json.loads(f.read_text())
            changed = False
            for row in w["canonicalisation_table"]:
                if row["expression_string"] in esc:
                    e = esc[row["expression_string"]]
                    row.update({"canonicalization_status": e["canonicalization_status"],
                                "canonical_expression": e["canonical_expression"],
                                "effective_support": e["effective_support"],
                                "discovered_family": e["discovered_family"],
                                "template_key_repr": e["template_key_repr"],
                                "cpu_seconds": round(e["cpu_seconds"], 3), "tier": 2,
                                "unresolved_reason": e.get("unresolved_reason")})
                    changed = True
            if changed:
                f.write_text(json.dumps(w))
        scored = [score_world(json.loads(f.read_text()), truth_for) for f in files]
        indeterminate = [s for s in scored if s["indeterminate"]]

    counts_bot = collections.Counter(s["class_rho_bot"] for s in scored)
    counts_top = collections.Counter(s["class_rho_top"] for s in scored)
    resource_blocked = sorted({e for s in indeterminate for e in s["unresolved_expressions"]})

    res = {
        "schema": "muru-v2-stage1-scoring-1.0.0",
        "worlds_scored": len(scored),
        "class_counts_rho_bot": dict(counts_bot),
        "class_counts_rho_top": dict(counts_top),
        "INDETERMINATE_WORLDS": len(indeterminate),
        "P6_prime_DETERMINACY_OK": len(indeterminate) == 0,
        "total_unresolved_rows": sum(s["n_unresolved_rows"] for s in scored),
        "total_rows": sum(s["n_rows"] for s in scored),
        "tier2_isolation": {  # execution-safety manifest, FP-3/FP-4
            "mechanism": "subprocess-per-expression, RLIMIT_AS + OS process death detection",
            "rss_ceiling_gib": SCORING_TIER2_RSS_GIB,
            "worker_count": SCORING_TIER2_WORKERS,
            "report": subprocess_isolation_report,
        },
    }
    if indeterminate:
        # Section 25.4: after UNCAPPED escalation an unresolved decisive row can only be
        # an envelope event. No scientific terminal is emitted.
        res["TERMINAL"] = None
        res["OPERATIONAL_STATE"] = "RUN_INCOMPLETE_RESOURCE_EXHAUSTION"
        res["resource_exhaustion_report"] = {
            "offending_expressions": resource_blocked[:200],
            "n_offending": len(resource_blocked),
            "worlds_left_undetermined": len(indeterminate),
        }
    else:
        res["TERMINAL"] = None      # section 22 assigns it; this pass only supplies P6'
        res["OPERATIONAL_STATE"] = None
    (OUT / "SCORING_RESULT.json").write_text(json.dumps(res, indent=2))
    (OUT / "SCORED_WORLDS.json").write_text(json.dumps(scored, indent=2))
    print(json.dumps(res, indent=2), flush=True)


if __name__ == "__main__":
    main()
