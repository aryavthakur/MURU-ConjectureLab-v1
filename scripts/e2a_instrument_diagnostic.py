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

v3 repairs, from CRITIC_SCIENCE_V2_REVIEW (DEF-C2) and CRITIC_GOVERNANCE_V2_REVIEW (G1, G4):

  G1  (CRITICAL) TERMINAL was keyed on `moved_lo == 0`, computed at the LOWER
      resolution, while `determinate` was computed and never used. An all-UNRESOLVED
      run therefore yields moved_lo == 0 and emits the BENIGN terminal. This ALREADY
      FIRED: the discarded null run recorded 396/396 SUBPROCESS_DIED_rc1,
      ALL_AFFECTED_WORLDS_DETERMINATE: false, and a pass terminal. FIX: the terminal
      is keyed on determinacy, and a run in which nothing resolved can never pass.
  G4  (CRITICAL) the tool emitted `D-INST-NO-WORLD-MOVED` /
      `D-INST-{n}-WORLDS-RECLASSIFIED`, neither of which is in protocol v2 section
      22.2's declared terminal set. An analyst would have chosen post hoc what they
      meant. FIX: the terminal is drawn ONLY from the declared set
      {D-INST-DETERMINATE, D-INST-INDETERMINATE, D-INST-PLURALITY-NOT-INVARIANT}.
      `worlds_whose_stage_MOVED` is retained as a DIAGNOSTIC, never as a terminal.
  C2  (CRITICAL) a 1500 s WALL budget and a 6 GiB address-space cap decided a
      scientific terminal, on a corpus containing an expression measured at 44.4 GB.
      That is the wall-clock defect reproduced one level up, inside the diagnostic
      convened to adjudicate it. FIX: section 25.2's two tiers are implemented --
      tier 1 is a CPU-time budget (ITIMER_PROF, so it is not a function of host load
      or co-tenancy), tier 2 escalates every DECISIVE pair with NO cap -- and
      section 25.4 is implemented: if a decisive pair is still unresolved for a
      RESOURCE reason, the run emits the OPERATIONAL state
      RUN_INCOMPLETE_RESOURCE_EXHAUSTION and NO scientific terminal at all.
"""
from __future__ import annotations
import argparse, hashlib, json, glob, os, sqlite3, subprocess, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "audit" / "muru_v2_reentry_20260819"
CKPT = OUT / "_ckpt_dinst"
CACHE = os.path.expanduser("~/e2_x86_cache/classify_cache.sqlite3")

# Section 25.2 tier 1: a CPU-time budget, NOT wall clock. Wall clock makes a label a
# function of host load and co-tenancy, which is the defect under adjudication.
TIER1_CPU_SECONDS = 60             # FP-2, declared (12x the retired 5 s)
# Tier 2 is UNCAPPED in time for decisive pairs (section 25.2).
TIER2_WALL_GUARD = None            # None == no wall cap. Deliberate.
# Section 25.5's frozen per-worker ceiling. Exceeding it is an OPERATIONAL event
# (section 25.4), never a label and never a terminal.
ADDRESS_SPACE_BYTES = 24 * 1024**3
RESOURCE_REASONS = ("MEMORY_SIMPLIFY", "MEMORY_PARSE", "MEMORY_CLASSIFY",
                    "RECURSION_SIMPLIFY", "KERNEL_OOM_KILL", "CPU_BUDGET_EXHAUSTED",
                    "ENVIRONMENT_IMPORT_FAILURE")
DECLARED_TERMINALS = ("D-INST-DETERMINATE", "D-INST-INDETERMINATE",
                      "D-INST-PLURALITY-NOT-INVARIANT")
# DEF-M3: the classifier version defining Stage 0's population is PINNED, not inferred.
# v2 picked it by frequency from a mutable out-of-repo file, so a different cache state
# could silently redefine the population.
CLASSIFIER_VERSION = "90a3b5ea3a83b0e9587e3b1e4e54e188afb8e893fabc9293d9177bc767089e7a"
CLASSIFY_CACHE_SHA256 = "66f30ea1d41d7063b3cb5a481281715011ba54ba897d5d17e058d8bb75273d50"
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
    # DEF-M3: assert the pinned version and cache hash; never infer them.
    digest = cache_sha256()
    if digest != CLASSIFY_CACHE_SHA256:
        sys.exit(f"[D-INST] classify cache sha256 mismatch\n  expected {CLASSIFY_CACHE_SHA256}\n  actual   {digest}")
    if CLASSIFIER_VERSION not in vers:
        sys.exit(f"[D-INST] pinned classifier version absent from cache: {CLASSIFIER_VERSION}")
    top = CLASSIFIER_VERSION
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
import sys,json,time,resource,signal
resource.setrlimit(resource.RLIMIT_AS,({AS},{AS}))

# Section 25.2: tier 1 is a CPU-TIME budget. ITIMER_PROF charges user+system CPU of
# this process only, so the bound is not a function of host load, co-tenancy or
# worker count. `None` means tier 2, which is uncapped by design.
class _Cap(BaseException):
    """BaseException DELIBERATELY (section 25.2): g2_contract wraps work in
    `except Exception: return None` in seven places, and a cap derived from
    Exception would be swallowed there and silently become SUPPORT_UNRESOLVED
    -> not-correct, which is the exact prohibited behaviour."""
_BUDGET = {CPU}
def _cap(sig, frm): raise _Cap("tier-1 CPU budget exhausted")
if _BUDGET is not None:
    signal.signal(signal.SIGPROF, _cap)
    signal.setitimer(signal.ITIMER_PROF, _BUDGET)
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
except _Cap:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"CPU_BUDGET_EXHAUSTED","wall":time.time()-t0}})); raise SystemExit
except MemoryError:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"MEMORY_PARSE"}})); raise SystemExit
if parsed is None:
    print("R"+json.dumps({{"v":"INCORRECT","why":"PARSE_FAIL","wall":time.time()-t0}})); raise SystemExit
try:
    sympy.simplify(parsed)                      # the call the 5s cap abandoned
except _Cap:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"CPU_BUDGET_EXHAUSTED","wall":time.time()-t0}})); raise SystemExit
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
except _Cap:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"CPU_BUDGET_EXHAUSTED","wall":time.time()-t0}})); raise SystemExit
except MemoryError:
    print("R"+json.dumps({{"v":"UNRESOLVED","why":"MEMORY_CLASSIFY","wall":time.time()-t0}})); raise SystemExit
print("R"+json.dumps({{"v":"CORRECT" if ev==G2Event.SUCCESS else "INCORRECT",
                      "why":"RESOLVED","wall":time.time()-t0}}))
'''


def eval_one(wm: dict, expr: str, tier: int = 1) -> tuple[str, str, float]:
    """tier 1: CPU budget TIER1_CPU_SECONDS. tier 2: UNCAPPED (section 25.2)."""
    budget = TIER1_CPU_SECONDS if tier == 1 else None
    code = _PAYLOAD.format(AS=ADDRESS_SPACE_BYTES, SRC=str(ROOT / "src"), EXPR=expr,
                           CPU=repr(budget),
                           FAM=wm["family"], REG=wm["regime"], NOI=wm["noise_level"],
                           REP=int(wm["replicate"]))
    try:
        p = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                           timeout=TIER2_WALL_GUARD,
                           env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    except subprocess.TimeoutExpired:
        return UNRESOLVED, "WALL_BUDGET_EXHAUSTED", -1.0
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

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def ckpt_path(w, k, rank):
        return CKPT / f"{w.replace('|','_')}__{k}_{rank}.json"

    def evaluate(items, tier, label):
        """Evaluate `items` at `tier`, checkpointing each. Tier 2 ignores an existing
        tier-1 checkpoint, because escalation is the whole point of tier 2."""
        def run(item):
            w, k, rank, ret, expr = item
            ck = ckpt_path(w, k, rank)
            if ck.exists():
                try:
                    prev = json.loads(ck.read_text())
                    if tier == 1 or prev.get("tier", 1) >= tier:
                        return prev
                except json.JSONDecodeError:
                    ck.unlink()
            v, why, wall = eval_one(meta[w], expr, tier=tier)
            rec = {"world_id": w, "seed_ordinal_k": k, "front_rank": rank,
                   "retained_by_argmax_score": ret, "expression_string": expr,
                   "verdict": v, "reason": why, "wall_seconds": round(wall, 1),
                   "sealed_stage": stage[w], "tier": tier}
            ck.write_text(json.dumps(rec)); return rec
        done = 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for fut in as_completed([ex.submit(run, it) for it in items]):
                fut.result(); done += 1
                if done % 20 == 0:      # D3: progress only, no verdicts streamed
                    print(f"[D-INST] {label} {done}/{len(items)} pairs", flush=True)
        print(f"[D-INST] {label} complete: {done}/{len(items)}", flush=True)

    def read_all():
        recs = [json.loads(q.read_text()) for q in CKPT.glob("*.json")]
        byw = collections.defaultdict(list)
        for r in recs: byw[r["world_id"]].append(r)
        return recs, byw

    def decisive_pairs(byw):
        """Section 25.2 tier 2: a pair is DECISIVE iff resolving it can change some
        world's stage, i.e. the world's LOWER and UPPER stages differ. Only decisive
        pairs are escalated -- the rest cannot move any verdict however they resolve."""
        out = []
        for w, sealed in stage.items():
            v = byw.get(w, [])
            if recompute_stage(sealed, v, False) != recompute_stage(sealed, v, True):
                out.extend((w, r["seed_ordinal_k"], r["front_rank"],
                            r["retained_by_argmax_score"], r["expression_string"])
                           for r in v if r["verdict"] == UNRESOLVED)
        return out

    if not a.analyze_only:
        evaluate(work, tier=1, label="tier-1")
        _, byw0 = read_all()
        esc = decisive_pairs(byw0)
        print(f"[D-INST] tier-2 escalation: {len(esc)} DECISIVE pairs, uncapped", flush=True)
        if esc:
            evaluate(esc, tier=2, label="tier-2")

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
        "tier1_cpu_seconds": TIER1_CPU_SECONDS,
        "tier2_wall_guard": TIER2_WALL_GUARD,
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
    }

    # ------------------------------------------------------- terminal assignment
    # G1/G4/C2. Three rules, in this order, and no other terminal may be emitted.
    #
    #  (i)  Section 25.4 has ABSOLUTE precedence. If any pair that is DECISIVE is
    #       still UNRESOLVED for a RESOURCE reason after uncapped tier-2 escalation,
    #       the run emits an OPERATIONAL state and NO scientific terminal at all.
    #       A resource envelope must never decide a scientific terminal -- that was
    #       the wall-clock defect reproduced one level up.
    #  (ii) Otherwise the terminal is keyed on DETERMINACY, never on `moved_lo`.
    #       Keying on `moved_lo` let a run in which NOTHING resolved emit the benign
    #       terminal, which already happened once.
    # (iii) The terminal is drawn ONLY from section 22.2's declared set.
    indeterminate_worlds = [w for w, sd in stage.items()
                            if recompute_stage(sd, byw.get(w, []), False)
                            != recompute_stage(sd, byw.get(w, []), True)]
    decisive_unresolved = [r for w in indeterminate_worlds for r in byw.get(w, [])
                           if r["verdict"] == UNRESOLVED]
    # After tier 2, which is UNCAPPED IN TIME, there is no legitimate mathematical
    # route to a residual UNRESOLVED. sympy.simplify either returns or the host
    # envelope stops it. So EVERY residual decisive-unresolved pair is an envelope
    # event, whatever its proximate reason, and section 25.4 routes all of them to
    # the operational state. Classifying only a hard-coded reason list would let an
    # unexplained `SUBPROCESS_DIED_rc{n}` fall through into a scientific terminal --
    # which is how the null run passed in the first place.
    resource_blocked = list(decisive_unresolved)

    res["indeterminate_world_count"] = len(indeterminate_worlds)
    res["decisive_unresolved_count"] = len(decisive_unresolved)
    res["resource_blocked_decisive_count"] = len(resource_blocked)

    if resource_blocked:
        # NOT a member of the section 32 terminal set, and NOT a finding about the
        # G2 contract, the pipeline, the surface or the instrument.
        res["TERMINAL"] = None
        res["OPERATIONAL_STATE"] = "RUN_INCOMPLETE_RESOURCE_EXHAUSTION"
        res["SCIENTIFIC_CONCLUSION"] = None
        res["resource_exhaustion_report"] = {
            "offending_expressions": sorted({r["expression_string"] for r in resource_blocked}),
            "reasons": collections.Counter(r["reason"].split(":")[0] for r in resource_blocked),
            "address_space_limit_bytes": ADDRESS_SPACE_BYTES,
            "tier1_cpu_seconds": TIER1_CPU_SECONDS,
            "worlds_left_undetermined": len(indeterminate_worlds),
            "note": ("Section 25.4: execution suspends, no seal is written, no routing "
                     "verdict is computed, and no scientific label or terminal of any "
                     "kind is emitted. The run may be resumed on a larger host under "
                     "the identical frozen protocol hash."),
        }
    else:
        # NOTE, and it is a finding rather than a convenience: with tier 2 uncapped,
        # `D-INST-INDETERMINATE` is UNREACHABLE BY CONSTRUCTION. A world is
        # indeterminate iff it still holds an UNRESOLVED row, and after uncapped
        # escalation an UNRESOLVED row can only be an envelope event, which the
        # branch above has already claimed. Genuine mathematical indeterminacy does
        # not survive the removal of the cap; what v1 and v2 called "the instrument
        # is unbounded" is really "this host is too small", and section 25.4 already
        # forbids that from being a scientific finding. The terminal is retained in
        # the declared set, and its unreachability is reported rather than hidden.
        terminal = "D-INST-DETERMINATE" if determinate else "D-INST-INDETERMINATE"
        res["D_INST_INDETERMINATE_reachable"] = False
        res["D_INST_INDETERMINATE_note"] = (
            "Unreachable by construction under uncapped tier-2 escalation: any residual "
            "UNRESOLVED row is an envelope event and routes to "
            "RUN_INCOMPLETE_RESOURCE_EXHAUSTION (section 25.4) before this branch.")
        # Reported alongside, never instead of: it is a fact about E2a, and D5 has
        # already invalidated E2a's routing on other grounds.
        if not (plur(lower) and plur(upper)):
            terminal = "D-INST-PLURALITY-NOT-INVARIANT"
        assert terminal in DECLARED_TERMINALS, f"undeclared terminal {terminal}"
        res["TERMINAL"] = terminal
        res["OPERATIONAL_STATE"] = None

    # A run in which nothing resolved can never pass. Belt and braces for G1.
    if res.get("TERMINAL") == "D-INST-DETERMINATE" and len(corr) == 0 and len(unres) == len(recs) > 0:
        raise SystemExit("[D-INST] REFUSING to emit a pass terminal: every pair is UNRESOLVED.")
    (OUT / "DINST_RESULT.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: res[k] for k in
        ("pairs_total","pairs_evaluated","verdicts","sealed_counts",
         "corrected_counts_LOWER_unresolved_as_incorrect",
         "corrected_counts_UPPER_unresolved_as_correct",
         "worlds_whose_stage_MOVED_at_LOWER","ALL_AFFECTED_WORLDS_DETERMINATE",
         "indeterminate_world_count","decisive_unresolved_count",
         "resource_blocked_decisive_count",
         "PLURALITY_INVARIANT_lower","PLURALITY_INVARIANT_upper",
         "TERMINAL","OPERATIONAL_STATE")}, indent=2))


if __name__ == "__main__":
    main()
