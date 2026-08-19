# CRITIC_SCIENCE — HOSTILE PRE-FREEZE REVIEW OF PROTOCOL v4

# VERDICT: FAIL

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md`
(2,947 lines at HEAD `7f28b5f`; filename says v3, header still literally reads "**VERSION
3**", content is v4 — see "housekeeping" below).
**Prior passes:** v2 FAIL (3 CRITICAL/9 HIGH/10 MED/1 LOW), v3 FAIL (5 CRITICAL/6 HIGH/9
MED/1 LOW).
**Stance:** hostile. Default FAIL on uncertainty.
**Method:** full re-read of the target against the v3→v4 diff (`git diff faad279 HEAD`);
**execution** of `scripts/v2_reachability_verifier.py`, `scripts/v2_truth_blind_verifier.py`,
`scripts/v2_freeze_dinst.py`, `e2c_search.control_c1b()`; **reading the source, not the
docstring,** of every script named in v4's "closed by execution" claims; **hand-computation**
of `_host_rss_ceiling_bytes()` at four host sizes; and **five independent fault-injection
demonstrations** against `e2c_classify.canonicalise` and the CPU-budget mechanism it depends
on, including a minimal reproduction proving `signal.setitimer(ITIMER_PROF, …)` can be
silently defeated by an ordinary non-cooperative C-level call. Transcripts below are the
actual command output, not a paraphrase.

**Counts (new/reproduced defects this pass): 3 CRITICAL · 1 HIGH · 1 MED.**
**Of my 21 v3 defects (5 CRITICAL + 6 HIGH + 9 MED + 1 LOW), 13 are genuinely repaired.**

---

## HEADLINE

v4 earns real credit on exactly the four items it claims and I could re-derive independently.
`scripts/v2_reachability_verifier.py` is a genuine, exhaustive (not budget-truncated:
459,929 ≤ 600,000) enumeration; I read its source for the bug class that killed v3 — does it
respect `F0` precedence, does it silently truncate — and it does not have either. Run fresh,
it reports `terminal_set_equality: passed=true` and **all 8 arithmetic rules `F9`–`F16`
REACHABLE**, including the two v3 killed the document over: `F9` (`SURFACE_DEGENERATE_NO_FRONT`,
witness `(138,0,0,0)`) is now evaluated *before* Gate R is read, and the old `F13`
(`D3_ITEMS_UNMET_NO_REENTRY`) is honestly deleted as a terminal and demoted to a rider, closing
`V3-C1` and `V3-C2` for real. `E6_SAFETY_HEADROOM_PRESENT` (`V3-C5`) is now precisely defined,
correctly kept out of `QUALIFIED`, and its "not double use of evidence" argument is sound
because `R0` is a parameter-free fixed rule, never fit to data — I could not break it. `N6`'s
authority narrowing (Decision 2 reverted to non-executable) is honored **everywhere** I grepped
for `EXECUTABLE` and `Decision 2` — no stale sentence survives.

**And v4 introduces exactly the class of defect its own priority instruction asked me to hunt
for: two of its three named CRITICAL repairs are false when re-executed, not merely re-argued
— and both fail for the same underlying reason the last three rounds failed for: a checker
was written, but it does not check what it claims to.**

1. **`P8a` (`V3-C3`) is violated today, by the mandatory control the document cites as its own
   evidence.** `control_c1b()` — control `C-1`, a **mandatory conjunct of `QUALIFIED`** — is
   executed inside `e2c_search.py`, imports `e2_search` **inside the function body**, and calls
   `e2_search.run_seed_search`, which (per `e2c_search.py`'s own docstring, and confirmed by
   grep at `e2_search.py:192`) calls `e2_classify.classify_expression` — a symbol `P8a` bans by
   **name**. I ran `control_c1b()` myself: `9 compared, 0 mismatched, PASSED`, matching the
   document's citation exactly, which proves the banned call executes on every run that
   discharges `QUALIFIED`. `scripts/v2_truth_blind_verifier.py` reports **zero violations**
   because `transitive_import_closure` discovers modules only via `dir(module)` after import —
   it cannot see a **function-local** import, which is exactly what `control_c1b` uses. `ls` of
   its own `modules_scanned` output confirms `e2_search` and `e2_worlds` are never scanned.
   `QUALIFIED` is unreachable by an independent route, for the fourth time, through a checker
   that passes on the input it was never able to see.

2. **`e2c_classify.py`'s resource→label leak (`V3-C4`) is reproduced at the one call the fix
   did not move, and the CPU budget it claims to enforce can be silently defeated by an
   ordinary C-level call.** `_safe_parse(expression_string)` still runs **outside** the shared
   `_cpu_budget`, under a bare `except Exception:` that swallows `MemoryError`. Executed:
   injecting `MemoryError` into `_safe_parse` yields `canonicalization_status: UNPARSEABLE` —
   a content label, not `UNRESOLVED` — exactly the defect the rewritten function's docstring
   says it fixed, one call site over. Separately, and worse: `_cpu_budget` relies solely on
   `signal.setitimer(ITIMER_PROF, …)`; I constructed a minimal, unrelated Python reproduction
   (`hashlib.pbkdf2_hmac` with a large iteration count, budget 0.5 s) that ran for the full 20 s
   test window **without the cap ever firing**, because CPython only delivers a pending signal
   at a bytecode-dispatch boundary and a single tight C-level call does not yield one. The
   Stage 1 driver (`scripts/v2_stage1_calibration_run.py`) has **no wall-clock backstop** on its
   `multiprocessing.Pool.imap_unordered` loop — no `timeout=`, no watchdog integration in the
   committed code — so one pathological expression whose dominant cost lands inside such a call
   (plausible given the corpus's own already-measured 44.4 GB / 95 s and 262–446 CPU-second
   `MEMORY_SIMPLIFY` pairs) can hang a worker, and the run, indefinitely. This is precisely what
   §25's governing rule (block capitals, "**NO … COMPUTE BUDGET MAY DECIDE A SCIENTIFIC LABEL …
   AT ANY LEVEL**") forbids being possible.

Two more findings, smaller but real: `V3-H6` (`§0.5`'s false "widened in exactly one respect"
claim and its impossible determinacy interval) is **not touched at all** — the section is
byte-identical to v3 (`git diff faad279 HEAD -- …` shows zero change in that range) — and
`§21.3` cites `SURFACE_DEGENERATE_NO_FRONT` as **"`§22 F14`"**, which is stale: `F14` is now
`E4_GENERATION_LICENCE_PROPOSED_F09_F10`, a licence-proposing terminal, the opposite of what
the sentence needs; the correct rule is `F9`. A reader who trusts that citation is sent to the
wrong rule by exactly the renumbering that repaired `V3-C1`.

**Credit where it is due, at length, because it is real.** `V3-C1`, `V3-C2`, `V3-C5`, `V3-H1`,
`V3-H2`, `V3-H3`, `V3-H4`, `V3-H5`, `N4`, `N6` are genuinely repaired, most of them re-derivable
from the source rather than the prose. The reachability verifier and the freeze-record generator
are exactly the kind of artifact my v2 and v3 reviews asked for, and running them is not a
formality — they do pass. The document is materially better than v3. It is still not freezable,
because the two repairs load-bearing enough to be named "CRITICAL" in the executor's own commit
message are, on execution, not repairs.

---

# PART 1 — REPAIR VERIFICATION (my 21 v3 defects)

| v3 defect | v4 claim | **Verdict** | Executed evidence |
|---|---|---|---|
| **V3-C1** `F14`/degenerate-front unreachable | Renamed `F9`, moved before all Gate R rows | **REPAIRED** | `v2_reachability_verifier.py`: `F9` REACHABLE, witness `(138,0,0,0)`, `headroom=true`, `gate_row=2`, `lead=1.0`. Confirmed by hand: `S1=0 ⟹` degenerate check fires before `gate_row` is even consulted for routing, per the script's `rule_fires` order |
| **V3-C2** `F13`/D3-unmet unreachable | Deleted as a terminal, demoted to a mandatory rider on `F12`–`F16` (option (a), as I recommended) | **REPAIRED** | §22.1 and §32 both state the deletion consistently; `terminal_set_equality` in the verifier passes (`missing_from_section_32: []`, `extra_in_section_32: []`) over the live 17-rule table, which would fail if a stray `D3_ITEMS_UNMET` terminal existed anywhere |
| **V3-C3** `P8a` unsatisfiable (module ban) | Replaced with a call-graph ban, checked by `v2_truth_blind_verifier.py`, "0 violations over 16 modules" | **NOT REPAIRED — reproduced through a channel the verifier cannot see** | See headline item 1. `control_c1b()` executed: `9 compared, 0 mismatched, PASSED`. `e2_search.py:192` calls `e2_classify.classify_expression` (confirmed by grep and by AST `module_call_targets` run directly against the imported module: `{'classify_expression'}`). `transitive_import_closure`'s own `modules_scanned` list (16 modules) **omits `e2_search` and `e2_worlds` entirely** — proven by print, not inference |
| **V3-C4** `e2c_classify` resource→label leak, `X-3` reproduced | Both extraction calls moved inside a shared, remaining-budget `_cpu_budget` | **PARTIALLY REPAIRED, NEWLY BROKEN ELSEWHERE** | Demo B confirms the *specific* named leak is fixed (`MemoryError` inside `extract_effective_support` → `UNRESOLVED`, correctly). But `_safe_parse` (line 129) is untouched, outside the budget, and a `MemoryError` there is swallowed to `UNPARSEABLE` — reproduced, executed (Demo A below). And the `_cpu_budget` mechanism itself is shown defeatable (Demo D below) |
| **V3-C5** `E6_SAFETY_HEADROOM_PRESENT` undefined, no arm, DEV/EVAL mix | `false_structure_events` defined on the NEG stratum, `R0`-only (no arm), full 230, kept out of `QUALIFIED` | **REPAIRED** | Precise definition present at §21.5; consistent everywhere I grepped (`F12`–`F15`, §32, §35); the "not double use of evidence" argument is sound because `R0 = argmax(score)` is a parameter-free rule fixed at §12, never fit to any data — there is no channel by which the 230-world safety test could be informed by anything the same 230 worlds' retention outcome depended on, because retention never depended on data. Honestly marked "declared, not yet implemented" — confirmed: `false_structure_events` has zero hits in `v2_stage1_scoring.py` — so no false claim of execution exists to catch |
| **V3-H1** `F12a` unreachable / `F0` order undefined | `F12a` deleted as a construct; folded into `F16` unconditionally | **REPAIRED (moot)** | No `F12a`/`F12b` remain in the live §22.1 table; `F0` is now a literal printed list (`RULE_ORDER` in the verifier matches §22.1's table order exactly, checked by eye against both) |
| **V3-H2** §25.5 stale vs §25.4 | §25.5's numbers deleted, repointed to §25.4/`STAGE1_RESOURCE_PROFILE.json` | **REPAIRED** | Read in full: §25.5 now contains no numeric constant, only a pointer and the same 2.0/19, 4.0/9, 23.5/1 table as §25.4, byte-identical |
| **V3-H3** Stage 0 in-process 24 GiB constant | `_host_rss_ceiling_bytes()` computes from `os.sysconf` | **REPAIRED** | Formula matches §25.4 exactly: `min(0.5·total, 24·scale)`, `scale=max(1,⌊total/47⌋)`. Hand-computed: 4 GiB→2.0 GiB; 47 GiB→23.5 GiB (matches doc); 200 GiB→96 GiB; 2048 GiB→1024 GiB (=exactly half, capped by the first term, never exceeds total RAM, never negative). One residual note: `scale` steps discretely at multiples of 47 GiB, so a 93.9 GiB host gets ceiling 24 GiB while a 94.0 GiB host gets ~47 GiB — a real but monotone, bounded, disclosed-by-formula discontinuity, not a defect I am scoring |
| **V3-H4** §32 missing 6 terminals, F10 has 3 names | §32 rewritten against the full `F1`–`F17` set | **REPAIRED** | Verifier's `terminal_set_equality`: `passed: true`, both diff sets empty. Manually cross-checked §32's 17-row table against §22.1's 17-row table by eye — identical terminal strings and rule numbers |
| **V3-H5** §32.1 witness verifier does not exist | `scripts/v2_reachability_verifier.py` committed, run at freeze time | **REPAIRED** | Exists, executes, exhaustive (459,929 vectors < 600,000 budget, confirmed never truncates), `PASSED: true`. This is the single most consequential repair in the document and it holds up |
| **V3-H6** §0.5 false "widened in exactly one respect" claim + impossible interval | (no specific claim made in v4's commit message) | **NOT REPAIRED — untouched** | `git diff faad279 HEAD` over §0.5's line range: **zero lines changed**. The same `A∈[49,122], B∈[196,267], C+D∈[99,104], E∈[119,124]` interval is still printed, still measurably impossible in two of four cells against `recompute_stage`'s actual bounds |
| **V3-M1** `F2a` unreachable, undisclosed | `F2a` renamed `F3` in the new scheme (`SURFACE_POPULATION_CONTAMINATED`, P7 fails) | **MOOT / not re-verified this pass** | The old `F2a`/registry-contamination framing is gone from the live table; F3's condition is a direct `P7` failure, not the same construction. Not independently re-derived this round; flagged for the next pass if reintroduced |
| **V3-M2** E6 denominator mixes DEV/EVAL | Subsumed by `V3-C5`'s R0/230 argument | **REPAIRED** | See V3-C5. `R0` is never selected, so DEV/EVAL split (relevant only to arm-*selecting* comparisons like D7) does not apply; 230 is the correct, honestly-justified denominator now |
| **V3-M3** §12/§16 mandate incompatible entry points, neither exists | §12 rewritten to name `e2c_search`/`e2c_classify`, both now exist and are committed | **REPAIRED** | §12's "Execution path" row now matches §16 exactly; `src/muru/v2_calibration/e2c_search.py` and `e2c_classify.py` exist, import, and run |
| **V3-M4** §35 assigns probability to an unreachable terminal, missing 6 terminals | §35 rewritten against the live 17-rule set, 50+18+10+5+4+8+5=100 | **REPAIRED, with a minor gap** | Arithmetic checks: sums to 100; licensing mass 10%+4%=**14%**, matches the "~14%" claim exactly. `SURFACE_DEGENERATE_NO_FRONT` (F9) and the two `*_NO_SAFETY_HEADROOM` terminals (F13/F15) are folded into their parent route's probability without a separate line — defensible (F9 is now reachable but pathologically unlikely on a real surface; F13/F15 are explicitly called out as "some of this mass" within the B/A rows) but not itemized per-rule the way the verifier itemizes reachability |
| **V3-M5** two incompatible frozen search costs (62.7 vs 82.1 CPU-hours) | Not addressed in v4's stated repairs | **NOT REPAIRED — both figures still present** | §10.6 still states **62.7 CPU-hours** (3.86 s/search basis); §25.4 states **82.1 CPU-hours** (5.1 s/search, `STAGE1_RESOURCE_PROFILE.json`'s measured mean) for the same "Stage 1 search cost" quantity. Not re-executed to compute a third value this pass; flagged as still open |
| **V3-M6** stale D-INST freeze record | Superseded by N4's `v2_freeze_dinst.py` mechanism | **REPAIRED** | See N4 below |
| **V3-M7** `P8b` cannot detect a reference-vs-copy leak | Not specifically addressed | **NOT REPAIRED — same structural weakness** | `e2c_search.py`'s `assert_design_truth_blind` still does value-identity comparison (`np.allclose(est, truth_vec, …)`), which cannot catch `g = truth.g_by_compound[c]` (a value copy, not a reference) being silently substituted for an estimate. Not re-executed as a fault injection this pass |
| **V3-M8** `pi_E` never enters the certification argmax | Not addressed (still accepted-disclosed per v3) | **NOT REPAIRED, still disclosed as a residual** | Confirmed in `v2_reachability_verifier.py`: `cands = {"A": piA, "B": piB, "C+D": piCD}` — `piE` is structurally excluded from `argmax`, exactly as V3-M8 described |
| **V3-M9** operational branch (`RUN_INCOMPLETE_RESOURCE_EXHAUSTION`) still publishes routing quantities computed from nothing | Not addressed | **NOT REPAIRED — untouched code** | `git diff faad279 HEAD -- scripts/e2a_instrument_diagnostic.py` shows the **only** change in the whole file is `_host_rss_ceiling_bytes()`. `corrected_counts_UPPER_unresolved_as_correct`, `PLURALITY_INVARIANT_lower/upper` and `worlds_whose_stage_MOVED_at_LOWER` are still computed and placed into `res` **before** the `resource_blocked` branch is evaluated, and are not stripped when that branch fires |
| **V3-L1** `Positive?` column not split | Split into `Positive?` / `Licenses?` | **SUBSTANTIALLY REPAIRED, cosmetically inexact** | §32's header is now `\| Terminal \| §22 rule \| Meaning \| Positive? \| Licenses? \|` — two columns exist, and `RC3_WITHDRAWN_RETENTION_NOT_THE_LOSS_STAGE`'s row correctly shows a distinct "concludes but does not license" state (`**Concludes: Yes**` / `No`). The column header still reads "Positive?" rather than the "Concludes?" the ledger names, and one cell's content ("Concludes: Yes") doesn't match its own column header ("Positive?") — a naming mismatch, not a functional one |

**Score: 13 of 21 genuinely repaired** (`V3-C1`, `C2`, `C5`, `H1`, `H2`, `H3`, `H4`, `H5`,
`M2`, `M3`, `M4`, `M6`(via N4), `L1`-substantially), plus `N4` and `N6` from
`CRITIC_GOVERNANCE`'s chain, both independently verified here. **8 not repaired, or
repaired-then-reproduced elsewhere: `C3`, `C4`, `H6`, `M1`(not re-verified), `M5`, `M7`,
`M8`, `M9`.**

---

# PART 2 — EXECUTED DEMONSTRATIONS

## Demo A — the resource→label leak, reproduced at `_safe_parse`

```
>>> mock _safe_parse to raise MemoryError("simulated 44GB parse")
>>> canonicalise("x**2 + y", cpu_budget=60, tier=1)
canonicalization_status : UNPARSEABLE      <-- should be UNRESOLVED (resource event)
cpu_seconds             : 2.5e-05
```

`_safe_parse` at `e2c_classify.py:129` runs **before** any `_cpu_budget` context is entered and
is wrapped in `except Exception: parsed = None`. `MemoryError` is an `Exception` subclass, so
it is silently absorbed and reported as if the expression were syntactically bad — the exact
"resource event masquerading as a content label" defect `V3-C4` was about, now living in the
one call the rewrite did not move.

## Demo B — the two named call sites ARE now fixed (control)

```
>>> mock extract_effective_support to raise MemoryError
>>> canonicalise(...) -> status: UNRESOLVED, effective_support: None
```

Confirms the specific repair the document claims is real, for that specific pair of functions.
This is not disputed.

## Demo C — pure-Python CPU load: the timer works as advertised

```
>>> sympy.simplify replaced with a 4s pure-Python busy loop, cpu_budget=1
status: UNRESOLVED, cpu_seconds measured: 1.003
```

## Demo D — a single non-cooperative C-level call defeats the timer entirely

```
$ timeout 20 python3 -c '
import signal, time, hashlib
class Cap(BaseException): pass
signal.signal(signal.SIGPROF, lambda *_: (_ for _ in ()).throw(Cap()))
signal.setitimer(signal.ITIMER_PROF, 0.5)
hashlib.pbkdf2_hmac("sha256", b"password", b"salt", 200_000_000)
'
exit status: 124        # killed by the OUTER 20s wall-clock timeout; the 0.5s
                         # in-process CPU cap NEVER fired
```

CPython delivers a pending signal only at a bytecode-dispatch checkpoint. A single call into a
tight C loop that does not return control to the interpreter (`pbkdf2_hmac` here; plausibly any
of `sympy`'s C-accelerated backends, big-integer/rational arithmetic, or polynomial GCD routines
on a pathological expression) runs to completion regardless of `setitimer`. (For comparison, I
also tried `int ** int` with an astronomical exponent and a regex catastrophic-backtracking
case — both **did** get interrupted at ~0.5 s, showing this is not a universal signal-delivery
failure, but a real, non-hypothetical, call-dependent one. That is worse, not better: the budget
"usually" works, which is exactly the kind of intermittent behaviour that survives a 12-search
profiling run and fails on the corpus's actual pathological tail.)

## Demo E — the mandatory control that discharges `QUALIFIED` calls a `P8a`-banned symbol

```
>>> e2c_search.control_c1b()
{"control": "C-1b", "compared": 9, "n_mismatched": 0, "passed": true}
```

Matches §12's citation exactly. `control_c1b` is defined at `e2c_search.py:295`, does
`from . import e2_search, e2_worlds` **inside the function body** (line 304), and calls
`e2_search.run_seed_search(...)`. `e2_search.py:192` reads
`classification = e2_classify.classify_expression(expression)` — confirmed by grep and by
running `module_call_targets` (the verifier's own AST walker) directly against the imported
`e2_search` module: `{'classify_expression'}`, a member of `BANNED`.

```
>>> v2_truth_blind_verifier.transitive_import_closure(ENTRY_MODULES)
# n_modules_scanned = 16; 'muru.v2_calibration.e2_search' NOT in the list
# 'muru.v2_calibration.e2_worlds' NOT in the list
```

`transitive_import_closure` walks `dir(module)` after `importlib.import_module`, which only
surfaces names bound at **module scope**. A `from . import e2_search` written inside a function
body is invisible to it. `control_c1b` is itself defined inside the entry-point module
(`e2c_search.py`), and `C-1` is a mandatory conjunct of `QUALIFIED` (§20:
`QUALIFIED := Q1 AND C-0 AND C-1 AND …`); the document is not free to treat it as out of scope.

---

# PART 3 — NEW / REPRODUCED DEFECTS

## NEW-C1 — CRITICAL. `P8a` is violated today by control `C-1`, and the checker that reports "0 violations" structurally cannot see it.

**Location:** `src/muru/v2_calibration/e2c_search.py:304` (`from . import e2_search,
e2_worlds`, function-local); `src/muru/v2_calibration/e2_search.py:192`
(`e2_classify.classify_expression(expression)`); `scripts/v2_truth_blind_verifier.py:52-70`
(`transitive_import_closure`).

`P8a`: *"No function in the search entry point's transitive CALL GRAPH may INVOKE any of: …
`e2_classify.classify_expression`…"*. `control_c1b()`, defined **inside** `e2c_search.py` (the
named entry-point module) and required by `§20`'s `QUALIFIED` conjunction as control `C-1`,
imports `e2_search` locally and calls `run_seed_search`, which calls
`e2_classify.classify_expression` directly. Demonstrated by execution (Demo E): the control
runs, passes (`9/0`, matching the document's own citation), and necessarily executes the banned
call every time.

`v2_truth_blind_verifier.py`'s `transitive_import_closure` discovers reachable modules by
`importlib.import_module` + `dir(module)`, which only finds names bound in a module's **global**
namespace after import. It cannot discover a module imported inside a function body — proven by
printing its own `modules_scanned` output, which omits `e2_search` and `e2_worlds` entirely. The
verifier therefore reports `P8a_PASSED: true` on a codebase where `P8a` is, in fact, violated by
the one function that must execute for `QUALIFIED` to be evaluable at all.

**Failure scenario.** Any real Stage 1 run computes `QUALIFIED`, which requires `C-1`, which
requires running `control_c1b()`, which calls a symbol `P8a` bans by name. §22 `F6`
(`VOID_CONTROL_FAILURE`, triggered by `P8` failing) should fire on **every execution**, exactly
`V3-C3`'s finding, reproduced through a channel neither the document's own freeze-time checker
nor a naive `grep` for the banned names in `e2c_search.py`/`e2c_classify.py` (which the task
brief specifically asked me to also try, and which — taken alone — would have reported "clean",
the same false negative the verifier gives) can detect.

**Minimal repair.** Either (a) rewrite `control_c1b` to compare against a frozen, pre-computed
record of `e2_search`'s output rather than importing and calling `e2_search` live, removing the
banned call from the entry point's runtime call graph entirely; or (b) make
`transitive_import_closure` walk the **AST** of every already-scanned module for `Import`/
`ImportFrom` nodes at **any** nesting depth (not `dir()` after execution), so a function-local
import is discovered the same as a module-level one. (a) is preferable: it removes the actual
violation rather than only detecting it.

## NEW-C2 — CRITICAL. The tier-1 CPU budget's enforcement mechanism can be silently defeated by an ordinary non-cooperative C-level call, and Stage 1's orchestration has no independent backstop.

**Location:** `src/muru/v2_calibration/e2c_classify.py:67-84` (`_cpu_budget`, `ITIMER_PROF`
only); `scripts/v2_stage1_calibration_run.py:157-168` (`ctx.Pool(...).imap_unordered`, no
`timeout=`, no watchdog call in the committed code, despite §13/§25.5's prose claiming a
"smoke-tested" watchdog is mandatory hardening for this exact surface).

Demo D shows `signal.setitimer(ITIMER_PROF, …)` is not delivered until the interpreter reaches
a bytecode-dispatch checkpoint, and a single call into a tight C loop (proven with
`hashlib.pbkdf2_hmac`; plausible for `sympy.simplify`'s C-accelerated internals on a
pathological expression, e.g. the corpus's own already-measured 44.4 GB / 95 s pair) can run
indefinitely past its declared budget with the cap never firing. This is not a hypothetical
edge case invented for this review — the v3 review already measured two decisive pairs at
262.2 s and 446.2 s CPU under the *old* mechanism, and this protocol's own §35 assigns Stage 0
only a 65% pass probability specifically because of this expression class.

`v2_stage1_calibration_run.py`'s `main()` calls `pool.imap_unordered(_worker, ids, chunksize=1)`
with **no timeout argument** and no watchdog integration anywhere in the committed Python. If
one world's canonicalisation hangs in the manner Demo D demonstrates is possible, that worker
process runs forever (bounded only by its 2 GiB `RLIMIT_AS`, which a CPU-bound, not
memory-bound, hang will never hit), and the `Pool.imap_unordered` generator blocks the entire
57,960-search run indefinitely, with no terminal, no operational state, and no diagnosis —
worse than `RUN_INCOMPLETE_RESOURCE_EXHAUSTION`, because nothing is ever reported at all.

**Failure scenario.** §25's governing rule states, in block capitals, that no compute budget may
decide a scientific label or terminal "at any level." A budget that cannot be relied upon to
fire is not a budget; the protocol's central resource-handling claim (§25.2: tier 1 "produces
`UNRESOLVED`, never a label" — implicitly, never *nothing at all*) is unenforced for exactly the
expression class it was written for.

**Minimal repair.** Run each canonicalisation call in a subprocess with both `RLIMIT_AS` **and**
an outer wall-clock `subprocess.run(..., timeout=…)` kill — exactly what
`e2a_instrument_diagnostic.py`'s `_PAYLOAD` actually does (subprocess + `RLIMIT_AS` + outer
`timeout=`), which is what `e2c_classify.py`'s own docstring claims to imitate but does not:
it drops both the subprocess isolation and the memory cap, keeping only the in-process signal
handler that Demo D shows is insufficient alone.

## NEW-H1 — HIGH. A stale terminal-number cross-reference sends a reader to the wrong rule, introduced by the `F0`/`F9` renumbering that repaired `V3-C1`.

**Location:** `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md:1758-1759` (§21.3's `S_1 > 0` guard
note).

§21.3 states: *"That degenerate path is routed to `SURFACE_DEGENERATE_NO_FRONT` (§22 F14), not
to an exoneration."* In the live §22.1 table, `SURFACE_DEGENERATE_NO_FRONT` is **`F9`** (moved
there precisely to fix `V3-C1`); `F14` is now `E4_GENERATION_LICENCE_PROPOSED_F09_F10` — a
licence-**proposing** terminal, the opposite of a degenerate-surface catch. This is not a
cosmetic old-numbering echo (like the `N6` quotation block's `F12/F12a/F12b`, which is bounded
inside a quoted historical finding and does not misdirect to a *different currently-live* rule);
this sentence asserts a *current* routing fact using the *wrong* rule number for a rule that
currently means something else. §31.1's freeze-time verifier checks reachability and
terminal-set equality; it does not check prose cross-references, so this survived the freeze
gate that caught `V3-C1`/`V3-C2`/`V3-H1`.

**Minimal repair.** `s/§22 F14/§22 F9/` at line 1759. One character.

## NEW-M1 — MED. The `N6` quoted minimal-repair block cites terminal labels that no longer exist in the live §22 table, without a reconciling note.

**Location:** `:449-452` (inside §2.1's `N6` block: *"Section 21.2 row 3, section 22
F12/F12a/F12b, and section 32's E4f rows are VOID."*).

This is a verbatim quotation of `N6`'s own finding text, written against v3's numbering, and it
is clearly scoped as a quotation (the surrounding prose says so). But nothing in the document
reconciles it with the fact that §22 no longer has an `F12a` or `F12b` at all — those symbols
now name nothing, and the live rule that plays their role is `F16`. A reader who greps the
document for `F12a` to understand what's currently blocked will find only this quotation and
§32.3's "REINSTATED as F16" note, several hundred lines apart, with no forward pointer between
them.

**Minimal repair.** One parenthetical after the quoted block: *"(F12/F12a/F12b are v3's
numbering; the current rule is F16.)"*

---

# PART 4 — WHAT WOULD CHANGE MY VERDICT

1. **Remove the live call, don't just re-check for it.** Rewrite `control_c1b` so the entry
   point's actual runtime call graph never invokes `e2_search`/`e2_classify.classify_expression`
   — compare against a frozen recorded output instead of a live call. Then, separately, fix
   `transitive_import_closure` to find function-local imports via AST inspection (not `dir()`),
   so the checker and the code it checks agree by construction, not by the luck of where an
   import statement sits in a file.
2. **Give the tier-1 CPU budget a mechanism that cannot be silently defeated.** Subprocess
   isolation with `RLIMIT_AS` **and** an outer `subprocess.run(timeout=…)` kill, per
   canonicalisation call or per world, matching what `e2a_instrument_diagnostic.py` actually
   does (not what `e2c_classify.py`'s docstring claims it does). Move `_safe_parse` inside
   whatever that mechanism becomes.
3. **Fix the `§22 F14` cross-reference at `:1759`** and grep the whole document once more for
   any other post-renumbering stale rule citation in prose (I found one by reading closely; I
   did not exhaustively enumerate every `F\d+` mention against the live table).
4. **Either repair or explicitly re-disclose `V3-H6`, `V3-M5`, `V3-M9`.** These were named
   defects in the prior round and the underlying files are, by `git diff`, unchanged. Silence is
   not a disposition.

**What would *not* change my verdict.** An argument that `control_c1b`'s call to `e2_search` is
"just a control, not the real search path." Control `C-1` is named in `QUALIFIED`'s conjunction
in §20 without qualification, and the document's own §12 cites `control_c1b`'s numeric result as
the thing that discharges §12's execution-path requirement. If a control is exempt from `P8a`,
that exemption has to be written into `P8a`, not asserted after the fact by a reviewer who wants
the terminal to be reachable.

**What earned real credit.** The reachability verifier is the single best artifact this
programme has produced across four rounds — exhaustive, source-readable, and it holds up under
adversarial re-execution. `V3-C5`'s repair of `E6` is careful and its non-circularity argument
is actually sound, not merely asserted. `N6`'s authority narrowing is honored with a discipline
I could not find a single exception to by grep. None of that reaches a freeze while the
mandatory control that discharges `QUALIFIED` calls a symbol the document bans by name, and the
resource budget that stands between a search process and an indefinite hang can be defeated by
an ordinary library call.

---

**REVIEWER'S NOTE ON SCOPE.** As before: Gate 1 = FAIL, E2b's decision-inadmissibility, E2a's
cap-invariance, and Decisions 1/2 were taken as fixed and not relitigated. Executions performed:
`v2_reachability_verifier.py`, `v2_truth_blind_verifier.py` (twice, once via CLI and once via
direct `transitive_import_closure` call), `v2_freeze_dinst.py` (output reverted with
`git checkout` afterward — the only file touched by re-running it, restored to its committed
state), `e2c_search.control_c1b()`, five fault-injection demonstrations against
`e2c_classify.canonicalise` and the bare `_cpu_budget` mechanism (all via `unittest.mock`,
nothing written to disk), and `os.sysconf`-based hand computation of the Stage 0 ceiling formula
at four host sizes. No calibration world was generated, no search was executed, no sealed
evidence was touched. `git status` confirmed clean of review artifacts at the end of this pass.
