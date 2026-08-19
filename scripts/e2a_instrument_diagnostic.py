#!/usr/bin/env python3
"""D-INST v2: E2a instrument diagnostic (post-hostile-review).

Implements MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md. v1 was hash-frozen then
FAILED hostile review; every defect below is repaired here. The repairs are
ENGINEERING, not scientific: no threshold, definition, population or decision rule
changed. See DINST_HOSTILE_REVIEW.md.

  D1 (CRITICAL) v1 bounded no memory: one pair measured 44.4 GB RSS in 95s on a
     47 GB host, and v1 ran 12 of them. Removing the 5s cap removed a *memory*
     bound as well as a time bound. FIX: hard RLIMIT_AS per subprocess + low
     concurrency + an explicit MEMORY verdict.
  D2 (CRITICAL) an OOM was recorded as INCORRECT, re-committing the very defect
     under test: g2_contract's `except Exception: return None` swallows
     MemoryError/RecursionError into SUPPORT_UNRESOLVED -> not-correct. FIX: run
     sympy.simplify OUTSIDE that swallow first, typing MemoryError/RecursionError
     explicitly, so resource exhaustion can only ever yield UNRESOLVED.
  D3 (HIGH) the protocol's primary statement was unimplemented and CORRECT
     verdicts were streamed to stdout, so the inference would have been authored
     with the answer visible. FIX: the full stage recomputation, LOWER/UPPER
     bounds and terminal state are implemented HERE, before execution, and
     per-pair verdicts are not streamed.
  D4 (HIGH) terminal-state names inverted their own meaning. FIX: renamed to say
     what they mean (see TERMINAL below).
  D5 (HIGH) E2A_PLURALITY_INVARIANT is forced TRUE and provable pre-execution.
     FIX: reported as a PRE-EXECUTION ANALYTIC RESULT, not an experimental one.
  D6 (MED) "verbatim" was false: Gate 1's escalation budget was 1500s, not 1800.
     FIX: 1500, matching Gate 1 exactly.
  D9 (MED) the sqlite input was unhashed and read without its `version` filter.
     FIX: hashed and version-filtered.
  D10 (MED) UNRESOLVED carried no reason. FIX: reason code recorded.
"""
from __future__ import annotations
import argparse, hashlib, json, glob, os, sqlite3, subprocess, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "audit" / "muru_v2_reentry_20260819"
CKPT = OUT / "_ckpt_dinst"
CACHE = os.path.expanduser("~/e2_x86_cache/classify_cache.sqlite3")

ESCALATION_SECONDS = 1500        # D6: Gate 1's actual budget
ADDRESS_SPACE_BYTES = 6 * 1024**3  # D1: hard per-pair memory bound
CORRECT, INCORRECT, UNRESOLVED = "CORRECT", "INCORRECT", "UNRESOLVED"


def cache_sha256() -> str:                                   # D9
    h = hashlib.sha256()
    with open(CACHE, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def timed_out_expressions() -> tuple[set[str], dict]:        # D9: version-filtered
    con = sqlite3.connect(f"file:{CACHE}?mode=ro", uri=True)
    vers = collections.Counter(v for (v,) in con.execute("select version from classify_cache"))
    top = vers.most_common(1)[0][0]
    out = {e for e, rj in con.execute(
        "select expression_string,result_json from classify_cache where version=?", (top,))
        if json.loads(rj).get("canonicalization_status") == "SIMPLIFY_TIMEOUT"}
    return out, {"classifier_versions": dict(vers), "version_used": top,
                 "cache_sha256": cache_sha256()}


def load_corpus():
    stage, meta = {}, {}
    for f in glob.glob(str(ROOT / "results/e2/run_x86_e2a_v1/worlds_shard_*.jsonl")):
        for l in open(f):
            if l.strip():
                d = json.loads(l); stage[d["world_id"]] = d["first_loss_stage"]; meta[d["world_id"]] = d
    rows = collections.defaultdict(list)
    for f in glob.glob(str(ROOT / "results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl")):
        for l in open(f):
            if l.strip():
                d = json.loads(l); rows[d["world_id"]].append(d)
    return stage, meta, rows


# D1+D2: simplify runs OUTSIDE g2_contract's exception swallow, with typed
# resource failures, under a hard address-space limit.
_PAYLOAD = r'''
import sys,json,time,resource
resource.setrlimit(resource.RLIMIT_AS,({AS},{AS}))
sys.path.insert(0,{SRC!r})
from muru.v2_calibration import e2_worlds
from muru.paper_benchmark.g2_contract import (
    _safe_parse, extract_effective_support, classify_discovered_family,
    classify_support, classify_family_match, evaluate_g2_event, G2Event)
import sympy
e = {EXPR!r}
t0 = time.time()
try:
    parsed = _safe_parse(e)
except MemoryError:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"MEMORY_PARSE"}})); raise SystemExit
if parsed is None:
    print("R"+json.dumps({{"v":"INCORRECT","why":"PARSE_FAIL","wall":time.time()-t0}})); raise SystemExit
try:
    sympy.simplify(parsed)                      # the call the 5s cap abandoned
except MemoryError:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"MEMORY_SIMPLIFY","wall":time.time()-t0}})); raise SystemExit
except RecursionError:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"RECURSION_SIMPLIFY","wall":time.time()-t0}})); raise SystemExit
except Exception as ex:
    print("R"+json.dumps({{"v":"INCORRECT","why":"SIMPLIFY_EXC:"+type(ex).__name__,"wall":time.time()-t0}})); raise SystemExit
w = e2_worlds.build_world({FAM!r},{REG!r},{NOI!r},{REP})
try:
    ev = evaluate_g2_event(
        classify_support(extract_effective_support(e), w.truth.support),
        classify_family_match(classify_discovered_family(e), w.truth.family))
except MemoryError:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"MEMORY_CLASSIFY","wall":time.time()-t0}})); raise SystemExit
print("R"+json.dumps({{"v":"CORRECT" if ev==G2Event.SUCCESS else "INCORRECT",
                      "why":"RESOLVED","wall":time.time()-t0}}))
'''


def eval_one(wm: dict, expr: str) -> tuple[str, str, float]:
    code = _PAYLOAD.format(AS=ADDRESS_SPACE_BYTES, SRC=str(ROOT / "src"), EXPR=expr,
                           FAM=wm["family"], REG=wm["regime"], NOI=wm["noise_level"],
                           REP=int(wm["replicate"]))
    try:
        p = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                           timeout=ESCALATION_SECONDS,
                           env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    except subprocess.TimeoutExpired:
        return UNRESOLVED, "WALL_BUDGET_EXHAUSTED", float(ESCALATION_SECONDS)
    for line in (p.stdout or "").splitlines():
        if line.startswith("R"):
            d = json.loads(line[1:])
            return d["v"], d["why"], float(d.get("wall", 0.0))
    # D11: a dead subprocess must say WHY. Without stderr an environment failure
    # (missing dependency) is indistinguishable from a kernel OOM kill, which is
    # precisely the attribution this diagnostic exists to make.
    err = (p.stderr or "").strip().splitlines()
    tail = err[-1][:200] if err else ""
    if p.returncode in (-9, 137):
        why = "KERNEL_OOM_KILL"
    elif "ModuleNotFoundError" in (p.stderr or "") or "ImportError" in (p.stderr or ""):
        why = "ENVIRONMENT_IMPORT_FAILURE"
    else:
        why = f"SUBPROCESS_DIED_rc{p.returncode}"
    return UNRESOLVED, f"{why}: {tail}" if tail else why, 0.0


# ---------------------------------------------------------------- analysis (D3)
def recompute_stage(sealed: str, verdicts: list[dict], assume_unresolved_correct: bool) -> str:
    """Frozen witness order (MURU_V2_E2_PREDECLARATION.md section 6), applied to the
    corrected evidence. A timed-out row can only ever ADD a correct row."""
    any_correct = any(v["verdict"] == CORRECT or
                      (assume_unresolved_correct and v["verdict"] == UNRESOLVED)
                      for v in verdicts)
    retained_correct = any((v["verdict"] == CORRECT or
                            (assume_unresolved_correct and v["verdict"] == UNRESOLVED))
                           and v["retained_by_argmax_score"] for v in verdicts)
    if sealed == "A":
        if not any_correct:      return "A"
        return "C" if retained_correct else "B"   # A->C only via a retained row
    if sealed == "B":
        return "C" if retained_correct else "B"
    return sealed                                  # C/D/E cannot move earlier


def preflight() -> None:
    """D12: verify the evaluation interpreter can actually run the payload BEFORE
    any pair is evaluated. Without this, a missing dependency yields a full run of
    UNRESOLVED records that look like a scientific result and are not one."""
    probe = ("import sys,resource\n"
             f"resource.setrlimit(resource.RLIMIT_AS,({ADDRESS_SPACE_BYTES},{ADDRESS_SPACE_BYTES}))\n"
             f"sys.path.insert(0,{str(ROOT / 'src')!r})\n"
             "from muru.v2_calibration import e2_worlds\n"
             "from muru.paper_benchmark.g2_contract import _safe_parse\n"
             "import sympy, numpy\n"
             "print('PREFLIGHT_OK')\n")
    p = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=600,
                       env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    if "PREFLIGHT_OK" not in (p.stdout or ""):
        sys.exit("[D-INST] PREFLIGHT FAILED for interpreter %s (rc=%s).\n"
                 "Refusing to run: an environment fault would be recorded as %d UNRESOLVED\n"
                 "pairs indistinguishable from a genuine resource-exhaustion finding.\n%s"
                 % (sys.executable, p.returncode, 396, (p.stderr or "")[-2000:]))
    print(f"[D-INST] preflight OK: {sys.executable}, RLIMIT_AS={ADDRESS_SPACE_BYTES/1024**3:.0f}GiB", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)   # D1
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    CKPT.mkdir(parents=True, exist_ok=True)
    if not a.analyze_only:
        preflight()

    timeout, cache_meta = timed_out_expressions()
    stage, meta, rows = load_corpus()
    work = [(w, d["seed_ordinal_k"], d["front_rank"], bool(d.get("retained_by_argmax_score")),
             d["expression_string"])
            for w, rs in rows.items() for d in rs if d.get("expression_string") in timeout]

    if not a.analyze_only:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        def run(item):
            w, k, rank, ret, expr = item
            ck = CKPT / f"{w.replace('|','_')}__{k}_{rank}.json"
            if ck.exists():
                try: return json.loads(ck.read_text())
                except json.JSONDecodeError: ck.unlink()
            v, why, wall = eval_one(meta[w], expr)
            rec = {"world_id": w, "seed_ordinal_k": k, "front_rank": rank,
                   "retained_by_argmax_score": ret, "expression_string": expr,
                   "verdict": v, "reason": why, "wall_seconds": round(wall, 1),
                   "sealed_stage": stage[w]}
            ck.write_text(json.dumps(rec)); return rec
        done = 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for fut in as_completed([ex.submit(run, it) for it in work]):
                fut.result(); done += 1
                if done % 20 == 0:      # D3: progress only, no verdicts streamed
                    print(f"[D-INST] {done}/{len(work)} pairs evaluated", flush=True)
        print(f"[D-INST] evaluation complete: {done}/{len(work)}", flush=True)

    # ------------------------------------------------------------- analysis
    recs = [json.loads(p.read_text()) for p in CKPT.glob("*.json")]
    byw = collections.defaultdict(list)
    for r in recs: byw[r["world_id"]].append(r)
    sealed_counts = collections.Counter(stage.values())
    lo = collections.Counter(stage); up = collections.Counter(stage)
    lower, upper = collections.Counter(), collections.Counter()
    for w, s in stage.items():
        v = byw.get(w, [])
        lower[recompute_stage(s, v, False)] += 1
        upper[recompute_stage(s, v, True)] += 1
    unres = [r for r in recs if r["verdict"] == UNRESOLVED]
    corr = [r for r in recs if r["verdict"] == CORRECT]
    moved_lo = sum(1 for w, s in stage.items() if recompute_stage(s, byw.get(w, []), False) != s)
    determinate = all(recompute_stage(s, byw.get(w, []), False) == recompute_stage(s, byw.get(w, []), True)
                      for w, s in stage.items())
    def plur(c): return c["B"] > c["A"] and c["B"] > c["C"] + c["D"]
    res = {
        "schema": "muru-v2-dinst-1.0.0",
        "protocol": "MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md",
        "protocol_sha256": "5b2d2ae549241fbef993b928807a52122a7c8bc7cba73dff4eb63ee9ca71b646",
        "tool_version": "v2 post-hostile-review",
        "cache_provenance": cache_meta,
        "escalation_seconds": ESCALATION_SECONDS,
        "address_space_limit_bytes": ADDRESS_SPACE_BYTES,
        "pairs_total": len(work), "pairs_evaluated": len(recs),
        "verdicts": dict(collections.Counter(r["verdict"] for r in recs)),
        "unresolved_reasons": dict(collections.Counter(r["reason"] for r in unres)),
        "sealed_counts": dict(sealed_counts),
        "corrected_counts_LOWER_unresolved_as_incorrect": dict(lower),
        "corrected_counts_UPPER_unresolved_as_correct": dict(upper),
        "worlds_whose_stage_MOVED_at_LOWER": moved_lo,
        "rows_found_CORRECT_that_the_cap_had_scored_incorrect": len(corr),
        "ALL_AFFECTED_WORLDS_DETERMINATE": determinate,
        "PLURALITY_note": ("Analytic, established BEFORE execution and requiring no computation: "
                           "A->C/E and B->C/E each need a RETAINED row to flip, and abandoned rows "
                           "land on a retained row in only 2 A-worlds, 0 B-worlds. Hence B>=196, "
                           "A<=122, C+D<=104 always, so the Gate 2 predicate is CAP-INVARIANT."),
        "PLURALITY_INVARIANT_lower": plur(lower), "PLURALITY_INVARIANT_upper": plur(upper),
        "TERMINAL": ("D-INST-NO-WORLD-MOVED" if moved_lo == 0 else
                     f"D-INST-{moved_lo}-WORLDS-RECLASSIFIED"),
    }
    (OUT / "DINST_RESULT.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: res[k] for k in
        ("pairs_total","pairs_evaluated","verdicts","sealed_counts",
         "corrected_counts_LOWER_unresolved_as_incorrect",
         "corrected_counts_UPPER_unresolved_as_correct",
         "worlds_whose_stage_MOVED_at_LOWER","ALL_AFFECTED_WORLDS_DETERMINATE",
         "PLURALITY_INVARIANT_lower","PLURALITY_INVARIANT_upper","TERMINAL")}, indent=2))


if __name__ == "__main__":
    main()
