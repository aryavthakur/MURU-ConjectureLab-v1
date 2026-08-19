# CRITIC_SCIENCE — HOSTILE PRE-FREEZE REVIEW OF PROTOCOL v5

# VERDICT: FAIL

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md`
(2,995 lines at HEAD `0d63591`; filename and in-document header still literally read
"VERSION 3" — content is v5. This has now persisted across three consecutive rounds
without correction; noted, not separately scored, per v4's precedent.)
**Prior passes:** v2 FAIL, v3 FAIL, v3-again FAIL, v4 FAIL (3 CRITICAL/1 HIGH/1 MED new;
13/21 of my v3 defects genuinely repaired).
**Stance:** hostile. Default FAIL on uncertainty.
**Method:** full re-read against `git diff 19be068 0d63591`; **execution** of
`scripts/v2_reachability_verifier.py` and `scripts/v2_truth_blind_verifier.py`; **hand
re-derivation** of three reachability witnesses against the document's own δ/z/LCB formulas;
**fault injection** against `e2c_classify.canonicalise` (both the already-fixed call sites and
`_safe_parse`); a **live re-run** of the SIGPROF-defeat reproduction; and **four of my own
adversarial sabotage-then-restore tests**, none of which duplicate the three the v5 commit
message describes, each verified byte-identical (`md5sum`/`git status`) after restore.

**Counts (new/reproduced defects this pass): 0 CRITICAL · 1 HIGH · 1 MED · 1 LOW.**

---

## HEADLINE

v5 earns the credit it claims on both v4 CRITICALs, and the claim is not merely re-argued —
I re-derived it. `control_c1b` is gone from `e2c_search.py` (confirmed by diff, `grep`, and by
importing the module and checking `hasattr`); the P8a-banned call it made is no longer in the
search entry point's transitive closure by construction, not by a patched checker. I tried to
find a fourth way through the truth-blind verifier's blind spot — the task brief's own
suggestion, `importlib.import_module()` — and it works: a sabotage-then-restore test proves
`ast_import_targets` still cannot see a dynamically-imported module, so the "hardened AST-based
discovery" claim is real but incomplete. That gap is not currently exploited by anything in the
committed code, so I score it MED, not HIGH — but it means the verifier's "0 violations" result
is a check of the code that exists today, not a structural guarantee against every future edit,
and the document should say so rather than imply the blind-spot class is closed. NEW-C2's
disclosure is exactly what it claims to be: I reproduced the SIGPROF defeat fresh (a 0.5 s
budget deferred 12.6 s by an uncooperative `pbkdf2_hmac` call, live-rerun today, not just cited
from v4), confirmed `_safe_parse` is now genuinely inside the budget with typed
`MemoryError`/`RecursionError` handling (fault-injection: `UNRESOLVED`, not the old
`UNPARSEABLE`; normal-path regression on three expressions unchanged), and swept the whole
document for a contradicting "Stage 1 scoring is ready" claim — there is none. The disclosure
is honest, isolated to one place, consistent with the code (`v2_stage1_scoring.py` really does
run canonicalisation in-process with no subprocess/watchdog backstop — confirmed by reading the
script, not the docstring), and correctly gates *execution*, not *freezing*. I score NEW-C2
**ACCEPTABLE-DISCLOSED-LIMITATION**, per the task's own framing.

**But the repair that fixed the code broke the document that describes it, in the exact
paragraph written to fix that class of defect.** `control_c1b` was moved to a new module,
`e2c_search_controls.py` — correctly, and the move is real. The protocol text was never
updated to match. Two places still cite the function as `` `e2c_search.control_c1b` ``
(`:1430`, `:2603`) — a symbol that **does not exist**: `hasattr(e2c_search, "control_c1b")` is
`False`, executed. Worse, `:2603` is not stale leftover prose — it is **freshly authored in
this same commit**, inside the very paragraph GOVERNANCE `NEW-D` asked to be added because the
*previous* version of this list had gone stale twice already. It also states the truth-blind
verifier scans **"16 modules"** (`:2544`, and again at `:2602` — also freshly authored) when a
live run today scans **21** — the AST-import hardening this same commit added is what changed
that number, and the freshly-written sentence describing that same hardening cites the number
from before it. This is not a new failure mode; it is the identical one that has now recurred
in **five** consecutive rounds (v2 stale numbers, v3 `F14`/`F12a`, v4 `§22 F14`, and now this),
on the one document section whose explicit job is to not let this recur.

**Nothing in this pass reaches CRITICAL.** No P8a violation is live. No resource-budget claim
is contradicted elsewhere. No terminal is unreachable. The reachability verifier's arithmetic
checks out by hand on three independently chosen witnesses (`F9`, `F12`, `F16`) to six decimal
places against §10/§21's own δ=10/144, z=1.9599640, N=1656. The terminal-set-equality check now
genuinely parses §32's live table (confirmed: sabotaging a rule-ID *and*, separately, a terminal
name, each caught; each restore byte-identical) rather than comparing a dict to itself
(`CRITIC_GOVERNANCE NEW-B`'s finding, independently re-confirmed here). That is real,
non-trivial progress. It is not a freeze-ready document, because a HIGH-severity citation
defect survives in the one paragraph purpose-built to prevent exactly this.

---

# PART 1 — REPAIR VERIFICATION (v4's CRITICAL/HIGH items)

| v4 defect | v5 claim | **Verdict** | Executed evidence |
|---|---|---|---|
| **NEW-C1** `P8a` violated by `control_c1b`'s function-local import of `e2_search` (mandatory `C-1` conjunct) | Moved to a new module `e2c_search_controls.py`; no longer part of the entry point's call graph by construction | **REPAIRED (code), with a fresh HIGH-severity documentation regression — see NEW-H2** | `git diff 19be068 0d63591 -- src/muru/v2_calibration/e2c_search.py` shows the function's full 44-line body deleted, `__all__` no longer lists it. `hasattr(e2c_search, "control_c1b")` → `False`, executed. `truth_blind_verifier.py`'s `modules_scanned` (21 modules, executed) does not contain `e2_search`/`e2_worlds`. `e2c_search_controls.control_c1b()` executed directly: `{"compared": 9, "n_mismatched": 0, "passed": True}` — matches the document's cited "9 compared, 0 mismatched" exactly, but the document cites the wrong module path for it (`:1430`, `:2603`) |
| **NEW-C2** SIGPROF/`ITIMER_PROF` defeatable by a non-cooperative C-level call; no wall-clock backstop in Stage 1 orchestration | Disclosed as a "required pre-execution change," explicitly `v2_stage1_scoring.py` "not execution-ready" until subprocess isolation is built; `_safe_parse` separately fixed to be budget-protected | **ACCEPTABLE-DISCLOSED-LIMITATION** | Re-ran the SIGPROF-defeat reproduction fresh today: 0.5 s budget, `pbkdf2_hmac(..., 80_000_000)`, capped at **12.6 s**, not 0.5 s. Read `v2_stage1_scoring.py` in full: canonicalisation runs in-process (`from muru.v2_calibration import e2c_classify` at line 205, no `multiprocessing`, no `subprocess`, no `timeout=` anywhere in the file) — the disclosure's factual claim is accurate. Swept the whole document for `execution-ready`, `guarantee`, `watchdog`, `subprocess isolation` — the only "guarantee" language is about the *RSS* ceiling (§13, unrelated mechanism, itself correctly derived) and the pre-existing `e2_staleness_watchdog.sh`, which is E2-rescue-era, invoked by neither `v2_stage1_calibration_run.py` nor `v2_stage1_scoring.py` (`grep`, confirmed) — no contradicting readiness claim exists anywhere else in the text. `_safe_parse` fault injection: `MemoryError` → `UNRESOLVED` (was `UNPARSEABLE` in v4), executed; normal-path regression on `"x0 + x1"`, `"sqrt(x0)"`, `"x0*x1 - x2"` unchanged |
| **NEW-H1** `§21.3` cited `SURFACE_DEGENERATE_NO_FRONT` as stale `"§22 F14"` (should be `F9`) | Corrected to `F9` with an inline note | **REPAIRED** | `:1770` now reads `(§22 F9 — corrected from a stale "F14" reference...)`. Independent automated sweep of every terminal-name-plus-`F<n>`-on-the-same-line pattern in the whole document, cross-checked against the live `RULE_TERMINAL` map: the five genuine `§22 F<n>` citations (`:810` `F2`, `:1715` `F6`, `:1770` `F9`, `:2127` `F7`, `:2552` `F8`) are **all correct**. (The sweep's other hits — `"F09"`/`"F10"`/`"F17"` inside §32's own table prose and §35's probability table — are references to the *registry population-condition* codes, a distinct, pre-existing numbering scheme from the §22 rule ordinals; confirmed by reading each in context, not a new collision) |
| **NEW-M1** `N6`'s quoted `F12/F12a/F12b` block has no reconciling forward-pointer | Not specifically addressed in v5's commit message | **NOT RE-VERIFIED THIS PASS** | Out of this round's priority scope; low severity, not blocking |

---

# PART 2 — MY OWN ADVERSARIAL TESTS (deliberately not the ones the commit describes)

All four tests below were run against the live repository, then reverted; every restore was
confirmed byte-identical via `md5sum` (code) or `git status --short` / diff against a `/tmp`
backup (document), with the working tree clean at the end.

### Test 1 — dynamic import via `importlib.import_module()`

Appended a function to `e2c_search.py` that calls
`importlib.import_module("muru.v2_calibration.e2_search")` (a *call*, not an
`Import`/`ImportFrom` AST node) instead of a static import statement — the exact alternative
mechanism the task brief flagged.

```
P8a_PASSED: True
e2_search in scanned: False
n_modules: 21
```

**Result: the verifier does not see it.** `ast_import_targets` only walks `ast.Import` /
`ast.ImportFrom` nodes; a call to `importlib.import_module(...)` (or `__import__(...)`) is
neither, so the target module is never queued and never scanned, regardless of nesting depth.
This is the *same class* of blind spot NEW-C1 exploited (a way of reaching a module the
checker's discovery logic doesn't recognize as an import), through a different mechanism than
the three the commit message enumerates (module-level sabotage, qualified-submodule sabotage,
function-local sabotage — all three are static `Import`/`ImportFrom` variants). **This is not
a live violation** — nothing in the committed code currently reaches a banned symbol this way —
but it means "hardened, AST-based, catches it regardless of nesting" is true only for the
subclass of dynamic-reachability patterns that are syntactically `Import`/`ImportFrom`
statements, which the document does not qualify. Scored MED (NEW-M2 below), not HIGH, because
the primary NEW-C1 fix is structural (the call is removed, not merely hidden from a checker)
and this is a second-line-of-defense gap, not an active violation.

Restore verified: `md5sum src/muru/v2_calibration/e2c_search.py` identical before/after;
`git status --short` clean.

### Test 2 — sabotage a terminal's rule-ID at a row the commit's own description does not name

Changed `` `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` | F16 `` to `` | F15 `` in §32's live table
(a different terminal than whichever the authoring pass's own sabotage test used — not
disclosed in the commit message, so deliberately different by construction: I picked the last
row in the table).

```
rule_id_mismatches: [{'terminal': 'ROUTE_DETERMINED_ARM_NOT_EXECUTABLE',
                       'section_22_rule': 'F16', 'section_32_rule': 'F15'}]
passed: False
```

Caught correctly. Restore verified byte-identical (`md5sum`).

### Test 3 — sabotage a terminal *name* (not rule-ID) to test the other failure branch

Changed `` `VOID_SINGLE_SHOT_BROKEN` | F8 `` to `` `VOID_SINGLE_SHOT_BROKEN_X` | F8 ``.

```
missing_from_section_32: ['VOID_SINGLE_SHOT_BROKEN']
extra_in_section_32: ['VOID_SINGLE_SHOT_BROKEN_X']
passed: False
```

Caught correctly, via the set-difference path rather than the rule-ID-mismatch path — confirms
both of the parser's two failure-detection branches are live, not just one. Restore verified
byte-identical.

### Test 4 — re-verify the SIGPROF defeat is not host- or library-specific

Re-ran the exact `pbkdf2_hmac` reproduction fresh (not copy-pasted from the v4/v5 record) at a
different iteration count (80M vs. the prior 200M) to confirm the defeat isn't an artifact of
one specific call shape: capped at 12.6 s against a 0.5 s budget. Confirms NEW-C2's disclosure
describes a real, reproducible, host-independent property of `SIGPROF`/`ITIMER_PROF`, not a
one-off.

---

# PART 3 — HAND RE-VERIFICATION OF THREE REACHABILITY WITNESSES

Formulas taken from `:2670` (`sigma = sqrt((pi_top + pi_second - lead^2) / 1656)`,
`LCB = lead - 1.9599640 * sigma`) and `:1544-1549` (`delta = 10/144`, `z = 1.9599640`,
`n = 1656`), computed independently by hand, not by re-running the script's own function.

- **`F9`, witness `(138,0,0,0)`:** `piA=1`, all others 0 → `S1 = 1-piA = 0` → degenerate.
  `lead = 1-0 = 1.0`, `sigma = sqrt(max(1+0-1,0)/1656) = 0`, `LCB = 1.0`. Matches the script's
  reported `lead=1.0, lcb=1.0, gate_row=2` exactly. Also confirmed **structurally**: for any
  `A<138` at least one other component is positive, so `piA<1` and degeneracy is impossible —
  `(138,0,0,0)` is the *only* vector in the whole search space where `F9` can fire, which is
  why the search must exhaust nearly the full space before finding it (consistent with the
  budget-vs-459,929-combinations figure v4 already confirmed does not truncate).
- **`F12`, witness `(0,10,0,128)`:** `piB = 10/138 = 0.07246377`, `lead = piB - 0 = 0.07246377`
  (second-place tie between A and C+D at 0, stable-sorted). `sigma = sqrt((0.07246377 + 0 -
  0.07246377^2)/1656) = sqrt(0.0672138/1656) = 0.0063710`. `LCB = 0.07246377 -
  1.9599640*0.0063710 = 0.0599770`. Script reports `lead=0.072464, lcb=0.059977` — matches to
  the reported precision. `lead ≥ delta` (0.072464 ≥ 0.069444) and `LCB>0` → certified,
  `argmax=B` → `gate_row=1`, `headroom=True` → `F12` fires. Confirmed.
- **`F16`, witness `(0,0,10,128)`:** identical arithmetic to `F12` by symmetry (`C+D` in place
  of `B`), `lead=0.072464, lcb=0.059977`, `argmax=C+D` → `gate_row=3` → `F16` fires under
  `headroom=True`. Confirmed.

All three independently re-derived by hand match the script's output exactly. No arithmetic
defect found in the verifier.

---

# PART 4 — PRIORITY ITEMS (V3-H6, V3-M5, V3-M9): still open, correctly not claimed fixed

- **V3-H6** (§0.5's "widened in exactly one respect" claim + the `A∈[49,122]` etc. interval):
  `git diff 19be068 0d63591` over that section's line range is **empty** — byte-identical to
  v4. Not touched, not newly claimed fixed anywhere (`grep -n "V3-H6"` → no hits in the
  document). Still open. **Severity: MED**, per this round's guidance — it is long-standing,
  untouched debt from a prior round, not a defect this round introduced or misrepresented.
- **V3-M5** (62.7 vs. 82.1 CPU-hour search-cost figures): both numbers still present, at
  `:1181` and `:2319` respectively, unreconciled. Not addressed, not claimed fixed. **Severity:
  MED.**
- **V3-M9** (operational-branch routing quantities in `e2a_instrument_diagnostic.py`):
  `git diff 19be068 0d63591 -- scripts/e2a_instrument_diagnostic.py` is **empty** — the file is
  untouched. Not claimed fixed. **Severity: LOW-MED** (unchanged from v4's assessment; not
  re-executed this pass).

No new false claim of repair was introduced for any of these three.

---

# PART 5 — NEW DEFECTS

## NEW-H2 — HIGH. The move that fixed `P8a` left two stale module-path citations and a stale module count, one of them freshly authored in this same commit inside the paragraph built to prevent exactly this.

**Location:**
`audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md:1430` (`` `e2c_search.control_c1b` ``, carried forward unchanged from v4 — confirmed via `git show 19be068:...`, this line is byte-identical to the pre-v5 text and became false the moment `control_c1b` moved);
`:2603` (`` `e2c_search.control_c1b` ``, **newly authored in the v5 diff itself** — confirmed via `git diff`, this whole clause is a `+` line);
`:2544` and `:2602` (`` "over 16 modules" ``, the second of which is also newly authored in the v5 diff, in the same sentence as `:2603`'s citation).

Executed: `hasattr(muru.v2_calibration.e2c_search, "control_c1b")` → `False`. The function now
lives at `muru.v2_calibration.e2c_search_controls.control_c1b` — a module the protocol document
**never mentions by name, anywhere** (`grep -c e2c_search_controls` on the document → 0). A
reader who follows the document's own citation to reproduce the control that discharges `C-1`
(a mandatory conjunct of `QUALIFIED`, §20) gets an `AttributeError`. Separately, `` "16 modules" ``
is the count from *before* this same commit's AST-import hardening; a live run today scans
**21** (executed: `n_modules_scanned: 21`).

This is not a new failure *class* — it is the fourth occurrence, across five rounds, of "a
repair made in code, a contradicting or stale sentence surviving (or being freshly written) in
prose" (v2's stale numbers → v3's `F14`/`F12a` → v4's `§22 F14` → this). It lands specifically
in the `§31.8` disclosure paragraph that `CRITIC_GOVERNANCE NEW-D` asked to be rewritten
*because* the previous version of this exact list had gone stale twice already — meaning the
rewrite reintroduced the defect it was written to close, within the same commit.

**Why HIGH, not CRITICAL:** the underlying `P8a` violation is genuinely gone — this is a
citation-accuracy defect in the document's description of its own verification apparatus, not
a live truth-blindness violation or a silently-wrong scientific label. It does not change
whether `QUALIFIED` is reachable or whether any terminal's arithmetic is sound (independently
re-verified in Part 3). But `C-1`'s entire discharge argument in this protocol is "measured by
execution, not asserted" (`:1429`), and the one citation a reader would use to execute that
measurement is wrong in the frozen text, in the paragraph purpose-built to prevent this pattern.
Matches v4's own `NEW-H1` in kind and exceeds it in scope (four line-level facts wrong across
two paragraphs, one of them freshly authored, vs. one stale number in v4).

**Minimal repair.** `s/e2c_search\.control_c1b/e2c_search_controls.control_c1b/` at `:1430` and
`:2603`; `s/16 modules/21 modules/` at `:2544` and `:2602`; add one sentence to `§12` or `§16`
naming `e2c_search_controls.py` and stating why it is a separate module (the code's own
docstring in `e2c_search_controls.py` already has this text — it can be summarized, not
invented). Then grep the whole document once more for every other bare mention of
`e2c_search` to confirm none of the remaining ones implicitly assume `control_c1b` still lives
there.

## NEW-M2 — MED. The truth-blind verifier's "hardened, AST-based" import discovery does not see `importlib.import_module()` or `__import__()` calls, and the document does not qualify the claim.

**Location:** `scripts/v2_truth_blind_verifier.py:53-84` (`ast_import_targets`, handles only
`ast.Import`/`ast.ImportFrom`); `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md` (no discussion of
dynamic-import reachability anywhere in the `P8a`/`§16` text).

Demonstrated in Part 2, Test 1: a module reached only via `importlib.import_module("...")`
inside an entry-point function is invisible to `transitive_import_closure`; `P8a_PASSED`
remains `True` even though, if that module's return value were used to call a banned symbol,
the violation would be real and undetected. Not currently exploited — no such call exists in
the committed code today (confirmed: the only remaining reference to `e2_search`/`e2_worlds`
outside `e2c_search_controls.py` is in `e2c_search.py`'s docstring, prose only). This is a
second-line-of-defense gap in a checker whose first line (structural removal of the actual
call) is sound, not a live defect — but "AST-based... catches it regardless of nesting depth"
(the script's own docstring, `:62-66`) overstates what was actually closed: nesting depth,
yes; import *mechanism*, no.

**Minimal repair.** Either narrow the docstring's claim to "regardless of nesting depth, for
static `Import`/`ImportFrom` statements" (honest, cheap), or extend `ast_import_targets` to
also flag any `ast.Call` whose target is `importlib.import_module`, `__import__`, or
`importlib.__import__` with a string-literal argument (catches the common case; a
fully-dynamic module name built at runtime is undecidable statically and should be disclosed
as an accepted residual, not silently unhandled).

## NEW-L1 — LOW. Filename and in-document header still read "VERSION 3" at v5, unaddressed for a third consecutive round.

**Location:** the file itself (`MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md:1`, `:24`).

v4 noted this as non-scored housekeeping. It has now persisted through v5 without comment or
correction, despite this round's commit message internally referring to the work as "Protocol
v5." Not blocking; flagged because the document's own `§31.8`/`D3` discipline is built entirely
around "no number may be stated in one place and left stale in another," and a document that
cannot update its own version number across five rounds is a weak advertisement for that
discipline, even where — as here — the actual content is not misleading (the supersession
chain and defect ledgers make the true version unambiguous to a careful reader).

---

# PART 6 — WHAT WOULD CHANGE MY VERDICT

1. **Fix the four citations in NEW-H2.** Two `s///` edits and two number corrections, all
   within lines already identified. This alone would very plausibly move the verdict to PASS —
   nothing else found this pass rises to HIGH, and MED/LOW items do not block a freeze
   verdict under this round's own stated calibration.
2. **Either narrow `ast_import_targets`'s docstring claim or extend it to catch
   `importlib.import_module`/`__import__`** (NEW-M2). This would not by itself change the
   verdict (it is MED), but leaving an overstated robustness claim standing next to a freshly
   found gap in the same file that already needed one round of adversarial hardening is the
   kind of thing that compounds across rounds if left.
3. Continued silence on V3-H6/M5/M9 would **not** by itself change my verdict downward from
   here — they are correctly not claimed fixed, and this round's guidance treats them as
   MED/LOW debt, not blocking. Fixing them would help but is not required for a PASS.

**What would not change my verdict.** An argument that NEW-H2 "doesn't matter because the code
is actually right." The code being right is exactly why this is HIGH and not CRITICAL — but a
protocol whose central discipline is "every threshold and every citation is checkable, and a
citation to something that no longer exists is exactly the provenance failure this document was
rewritten five times to stop making" does not get to wave away the one paragraph, freshly
written this round, that fails its own rule.

---

**REVIEWER'S NOTE ON SCOPE.** Gate 1 = FAIL, E2b's decision-inadmissibility, E2a's
cap-invariance, and Decisions 1/2 were taken as fixed and not relitigated, consistent with v4.
`CRITIC_GOVERNANCE`'s NEW-A/B/C/D findings were read for context (they explain several of the
diff hunks touched here) but not independently re-adjudicated — that is governance's scope, not
science's. Executions performed: `v2_reachability_verifier.py` (fresh run, plus two independent
sabotage-then-restore cycles on section 32's table, both md5-verified restored); hand
computation of three witnesses' δ/z/LCB arithmetic; `v2_truth_blind_verifier.py` (fresh run,
plus one sabotage-then-restore cycle using a dynamic-import mechanism not described in the v5
commit message, md5-verified restored); `e2c_search_controls.control_c1b()`; `hasattr` probes
against `e2c_search`; fault injection against `_safe_parse` and normal-path regression on three
expressions; a fresh, independently-parameterized re-run of the SIGPROF-defeat reproduction. No
calibration world was generated, no search was executed, no sealed evidence was touched. Every
file this review modified for a test was restored and verified byte-identical before this
report was written; `git status` is clean of review artifacts.
