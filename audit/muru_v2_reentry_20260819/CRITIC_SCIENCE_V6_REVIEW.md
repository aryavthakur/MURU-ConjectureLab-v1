# CRITIC_SCIENCE — HOSTILE PRE-FREEZE REVIEW OF PROTOCOL v6

# VERDICT: PASS

**Target:** `audit/muru_v2_reentry_20260819/MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md`
(3,003 lines at HEAD `3a490f5`; document content is v6, filename/header still literally read
"VERSION 3" — fourth consecutive round unaddressed, see NEW-L1 carried forward.)
**Prior passes:** v2 FAIL, v3 FAIL, v3-again FAIL, v4 FAIL, v5 FAIL (0 CRITICAL / 1 HIGH
`NEW-H2` / 1 MED `NEW-M2` / 1 LOW `NEW-L1`).
**Stance:** hostile. Default FAIL on uncertainty. Scope this round: verify the named
four-citation fix precisely, hunt for a sixth-round regression in the newly-added disclosure
paragraph, sweep every `e2c_search`-family reference independently, reconsider the open
MED/LOW carryover, and answer the freeze-readiness question honestly.

**Counts (new/reproduced defects this pass): 0 CRITICAL · 0 HIGH · 0 MED · 1 LOW (carried
forward, unchanged severity).**

---

## HEADLINE

v6 does exactly what it claims and nothing less. The two stale `e2c_search.control_c1b`
citations (`:1430`, `:2603` in v5's line numbering) are gone; both are corrected to
`e2c_search_controls.control_c1b`, executed and confirmed live at that path. Both stale "16
modules" citations are corrected to "21 modules" (one gains ", post-hardening"), matching a
fresh execution of `v2_truth_blind_verifier.py` exactly. `git diff 0d63591 555fe88` on the
document is four hunks, all inside the two paragraphs `NEW-H2` named — no drive-by edits
elsewhere, no new claim of repair for anything out of scope. The fifth hunk — the new
"disclosed residual gap" paragraph about `importlib.import_module`/`__import__()` — is not
part of the four-citation fix proper but directly answers v5's `NEW-M2`, and its central
factual claim ("neither mechanism appears anywhere in the current entry-point closure or
Stage 1 driver") is true: I grepped all 21 scanned modules plus both Stage 1 driver scripts
independently and got zero hits; the only four occurrences of either mechanism anywhere in
`src/`/`scripts/` are in files this closure does not import (`ov_00_env.py`,
`e2b_escalate_unresolved.py`, `pb_34_rc3_integrity.py`, E2-rescue-era
`e2_run_shard_lazy.py`), confirmed by grepping those filenames against the closure/driver
files with zero hits. No sixth-round regression found — the fix that closed `NEW-H2` did not
break anything new, and the new paragraph's claims hold up under independent re-derivation
rather than re-reading.

The fresh sweep of every `e2c_search`-family reference in the document (6 for `e2c_search`
itself, 5 for `e2c_classify`, 2 for `e2c_search_controls` — 13 total, exceeding the 10-site
floor) turned up nothing else wrong: `e2c_search.assert_design_truth_blind` exists at
`e2c_search.py:130`; `e2c_search_controls.control_c1b` exists and runs (`9 compared, 0
mismatched, passed: True`, matching the document's cited figures exactly); the one citation to
the sealed original `e2_search` (distinct module, at `:2611`, correctly used as `C-1b`'s
comparison target, not confused with the truth-blind entry point) is accurate. Nothing drifted
that the four-citation commit didn't already catch.

**Nothing in this pass reaches CRITICAL or HIGH.** `NEW-M2` (the `importlib`/`__import__`
blind spot) is now honestly disclosed in the document itself, using the exact "accepted
residual" framing my own v5 report proposed as an acceptable alternative repair — I score it
**ACCEPTABLE-DISCLOSED-LIMITATION**, the same category v5 already gave `NEW-C2`. It does not
rise to HIGH: the gap is unchanged in kind and severity from v5 (still not exploited by any
committed code, still a second-line-of-defense checker limitation behind a structural fix
that is itself sound), and disclosure is the correct response to an undecidable-in-general
static-analysis limit, not a defect that repair can eliminate. `NEW-L1` (stale "VERSION 3"
header) persists into a fourth round untouched — still LOW, still non-blocking, still not
misleading to a careful reader given the supersession chain and defect ledgers, but I note the
pattern-recognition irony explicitly in Part 5 below.

---

# PART 1 — STEP 1: THE NAMED FIX, VERIFIED PRECISELY

```
$ grep -n "e2c_search\.control_c1b\|16 module" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md
(zero hits, exit 1)

$ grep -n "e2c_search_controls\.control_c1b\|21 module" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md
1438:mismatched, PASSED** (`e2c_search_controls.control_c1b` -- moved out of `e2c_search.py`...
2552:   over 21 modules, post-hardening), `scripts/v2_freeze_dinst.py` ...
2610:     verifier.py` (AST call-graph walk over 21 modules, no execution of search or scoring);
2611:     control `C-1b` (`e2c_search_controls.control_c1b`, 9 compared against the sealed `e2_search`
```

Both required greps return exactly what the task specification demands: zero hits on the
stale forms, four hits (across the two fix sites) on the corrected forms.

```
$ python3 scripts/v2_truth_blind_verifier.py
  ...
  "n_modules_scanned": 21,
  "violations": [],
  "P8a_PASSED": true

$ python3 scripts/v2_reachability_verifier.py
  ...
  "all_arithmetic_rules_reachable": true,
  "PASSED": true

$ PYTHONPATH=src python3 -c "
from muru.v2_calibration import e2c_search_controls
print(e2c_search_controls.control_c1b())"
  {'control': 'C-1b', 'compared': 9, 'n_mismatched': 0, 'mismatches': [], 'passed': True}

$ PYTHONPATH=src python3 -c "
from muru.v2_calibration import e2c_search
print(hasattr(e2c_search, 'control_c1b'))"
  False
```

All four executed confirmations required by Step 1 pass exactly as specified:
`n_modules_scanned == 21`, `P8a_PASSED == true`, reachability `PASSED == true`, and
`control_c1b` executed successfully from its new location (`e2c_search_controls`) while
confirmed absent (`hasattr` → `False`) from the old one.

---

# PART 2 — STEP 2: SIXTH-ROUND REGRESSION CHECK ON THE NEW DISCLOSURE PARAGRAPH

The new paragraph (document `:1413-1419`, added in the v5→v6 diff) reads in full:

> **Disclosed residual gap (`CRITIC_SCIENCE`, this pass, scored MED — not currently
> exploited).** The verifier's AST-based import discovery finds `import`/`from...import`
> statements; it does **not** resolve `importlib.import_module("...")` calls with a
> dynamically-built module-name string, or `__import__(...)`. `grep` confirms **neither
> mechanism appears anywhere** in the current entry-point closure or Stage 1 driver, so no
> live violation exists. But a future edit that introduced one would not be caught. This is
> recorded as a known limitation of the checker, not silently left implicit.

I independently identified the "entry-point closure" as the exact 21-module list the live
`v2_truth_blind_verifier.py` run reports, mapped each to its file under `src/`, added both
Stage 1 driver scripts (`scripts/v2_stage1_calibration_run.py`,
`scripts/v2_stage1_scoring.py`, per the document's own naming at `:2212`), and grepped all 23
files together:

```
$ grep -n "importlib\.import_module\|__import__(" <21 closure files> \
      scripts/v2_stage1_calibration_run.py scripts/v2_stage1_scoring.py
(zero hits, exit 1)
```

The claim is true, executed, not merely re-read. A broader sweep of the whole `src/`/`scripts/`
tree does find four occurrences of these mechanisms, all in files structurally outside the
closure and confirmed (by grepping their filenames against the closure/driver files) never
referenced by any of them: `scripts/ov_00_env.py`, `scripts/e2b_escalate_unresolved.py`,
`scripts/pb_34_rc3_integrity.py` (an independent integrity checker, not part of Stage 1),
`scripts/e2_rescue_v2/e2_run_shard_lazy.py` (E2-rescue-era, pre-dates v2 Stage 1 entirely). The
paragraph's scope ("current entry-point closure or Stage 1 driver") is precisely the right
scope — it does not overclaim by silently including the wider codebase, nor underclaim by
excluding a file that should have been in scope.

`scripts/v2_truth_blind_verifier.py` itself is untouched in this diff (confirmed:
`git diff 0d63591 555fe88 -- scripts/v2_truth_blind_verifier.py` is empty). Its own docstring
at `ast_import_targets` (`:56-63`) claims only "catches it regardless of nesting" — a narrower,
already-true claim about nesting depth, not a general robustness claim about import
*mechanism* — so v5's characterization of that docstring as overstated stands as a
non-blocking observation about the *script*, separate from the *protocol document*'s new
paragraph, which is accurate as written. No inconsistency, new or old, found between the two.

**No sixth-round regression.** This is the first round in six where a newly-added paragraph's
factual claims survive independent re-verification rather than needing correction next round.

---

# PART 3 — STEP 3: FULL FRESH SWEEP OF `e2c_search`-FAMILY REFERENCES

```
$ grep -n "e2c_search" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md | wc -l
6
$ grep -n "e2c_classify" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md | wc -l
5
$ grep -n "e2c_search_controls" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md | wc -l
2
```

13 total citations across the three module names — exceeding the 10-site spot-check floor.
Each checked against the live file structure:

| Line | Citation | Verified against |
|---|---|---|
| `:1230` | `muru.v2_calibration.e2c_search` paired with `e2c_classify` | both files exist at `src/muru/v2_calibration/` |
| `:1407` | `e2c_search` + `e2c_classify` as "the entry point named below" | matches `v2_truth_blind_verifier.py`'s actual scan target |
| `:1427` | `e2c_search.assert_design_truth_blind` implements P8b | `grep -n "def assert_design_truth_blind" e2c_search.py` → `130:def assert_design_truth_blind(...)`, confirmed present |
| `:1431` | `muru.v2_calibration.e2c_search` paired with `e2c_classify` for canonicalisation | both files exist, roles match docstrings |
| `:1438` | `e2c_search_controls.control_c1b`, moved out of `e2c_search.py` | executed: function present in new module, absent from old |
| `:2205` | `e2c_classify.py`'s resource-leak regression | file exists, has `_cpu_budget`, `_Cap`, `canonicalise` at the cited lines |
| `:2552` | `v2_truth_blind_verifier.py` scans 21 modules post-hardening | executed, matches |
| `:2610-2611` | truth-blind verifier over 21 modules; `e2c_search_controls.control_c1b` vs. sealed `e2_search` | executed, matches; correctly distinguishes `e2c_search_controls` (comparison harness) from `e2_search` (sealed original being compared against) |
| `:2613` | `e2c_classify` resource-leak regression demos | consistent with `:2205` |

No drift found beyond what the four-citation commit already fixed. The document consistently
and correctly distinguishes three similarly-named things: `e2c_search.py` (the truth-blind
search entry point), `e2c_search_controls.py` (the relocated `C-1b` equivalence control), and
`e2_search.py` (the sealed, un-editable v1 original `C-1b` compares against) — a naming
adjacency that would be easy to blur under six rounds of hasty editing, and isn't.

---

# PART 4 — STEP 4: RECONSIDERING THE OPEN MED/LOW ITEMS

**`NEW-M2` (dynamic-import blind spot) — does it rise to HIGH?** No. Nothing about its
underlying technical severity changed this round: it was, and remains, a second-line-of-defense
gap behind a structural fix (`P8a`'s actual mechanism is "the banned call doesn't exist," not
"the checker would catch it if it did") that is itself sound, and it remains unexploited by
any committed code (re-confirmed fresh this round, not just cited from v5). What changed is
that the document now says so, in the reader's own words rather than mine. My v5 report offered
two alternative repairs — "extend the checker" or "disclose as an accepted residual, not
silently unhandled" — and explicitly treated the second as sufficient ("MED... not currently
exploited"). v6 chose the second, correctly and completely. I close it as
**ACCEPTABLE-DISCLOSED-LIMITATION**, matching `NEW-C2`'s v5 disposition. Extending the checker
to also flag `importlib.import_module`/`__import__` calls with string-literal arguments (my
v5 "minimal repair," option two) would still be a genuine hardening and is worth doing
eventually, but it is not required for freeze-readiness now that the gap is disclosed rather
than implied away.

**`NEW-L1` (stale "VERSION 3" header) — anything new?** No change; still un-touched, now a
fourth consecutive round of persistence (v4 noted it non-scored, v5 carried it LOW, v6's diff
does not touch line 1 or line 24). I keep it LOW, non-blocking, for the same reason as before:
the actual supersession chain (filename, defect ledgers, six rounds of dated reviews) makes the
true version unambiguous to anyone reading the audit directory, so no reader is actually
misled about which version they hold. I will say directly what I only implied in v5: it is a
small, standing embarrassment for a document whose entire `§31.8` discipline is "no number
may be stated once and left stale elsewhere," to have gotten its own version number wrong for
four rounds running — but embarrassment is not the same as risk, and I am not inflating this
to HIGH to make a point. It stays LOW.

**V3-H6 / V3-M5 / V3-M9 (long-standing carryover debt)** — reconfirmed untouched this round:
`grep -n "V3-M5\|V3-H6\|V3-M9"` on the document returns zero hits (no false claim of repair
anywhere), the 62.7-vs-82.1 CPU-hour figures are both still present unreconciled (`:1181`,
`:1199`, `:2327`), and `git diff 0d63591 555fe88 -- scripts/e2a_instrument_diagnostic.py` is
empty. None of these were in this round's scope (the task brief scoped this pass to the named
citation fix plus a fresh sweep), none are newly misrepresented, and per v5's own calibration
(explicitly restated in that report's Part 6) they do not block a freeze verdict on their own.
I am not relitigating that calibration this round; I note the debt is still there and still
correctly un-claimed.

---

# PART 5 — STEP 5: THE BIG QUESTION

**Is this protocol text genuinely ready to be called scientifically sound, six hostile rounds
in, with Stage 1 execution separately gated on the SIGPROF/subprocess fix?**

Yes, with the two-tier reading the task itself proposes, and I want to be precise about what
"yes" means here rather than just asserting it.

What "sound" means for *this* artifact is narrower than "every number in 3,000 lines is
correct forever" — no document of this size and this density of executable claims earns that
standard, and demanding it would be exactly the "manufacture severity to avoid saying PASS"
failure mode I was warned against. What it can mean, and does now mean, is: every load-bearing
claim that determines whether `QUALIFIED` is reachable, whether a terminal's arithmetic is
sound, whether the truth-blind ban actually holds, and whether the document's account of its
own verification apparatus matches what that apparatus does — is either independently
re-derivable by hand (§32's δ/z/LCB arithmetic, re-checked to six decimal places across three
witnesses in v5 and not re-litigated here since nothing touched it) or directly executable
(P8a: 0 violations, 21 modules; reachability: PASSED; C-1b: 9/9 from its real, cited location).
Six rounds in, I can no longer find a citation in this document that points to something that
doesn't exist, a number that contradicts a fresh execution, or a readiness claim contradicted
elsewhere in the text. That is a materially different state than v2 through v5, each of which
handed me at least one of those on a hostile read.

The pattern that failed four rounds running — a code fix landing correctly while the prose
describing it went stale, sometimes in the very paragraph written to prevent that — did not
recur a fifth time. That is not a small thing to have broken. It is also not proof it can never
recur a sixth time on some future edit; nothing about six clean rounds constitutes a
mathematical guarantee about a seventh. What it does constitute is five rounds of hostile,
independently-executed adversarial review (mine) plus five of governance's, converging on
"nothing exploitable remains," with the sixth finding of the *sixth* round being a genuine,
correctly-scoped, honestly-disclosed residual limitation rather than a new defect. At some
point continuing to withhold a PASS on the theory that a seventh round might find something is
no longer hostile skepticism; it is refusing to ever certify anything, which the task brief
explicitly asked me not to do.

So: the protocol **text** is scientifically sound and freeze-ready, under the two-tier model
where "freeze-ready text" and "execution-ready system" are different questions. It is not,
and should not be read as, a certification that Stage 1 can safely *run* today — the SIGPROF
gap (`NEW-C2`, v5) is real, reproduced fresh in v5, unchanged and untouched this round, and the
document itself says `v2_stage1_scoring.py` "must not be treated as execution-ready" until
subprocess isolation is built (`:2218`). That gate is doing its job precisely by remaining
separate from this verdict: I am certifying the document that says "do not execute Stage 1
yet," not overriding what it says.

---

# PART 6 — WHAT WOULD CHANGE THIS VERDICT

Nothing found this round changes it downward. For the record, since the pattern across five
rounds has been "the next round finds the previous round's blind spot": the two things I'd
flag as worth doing before or shortly after freeze, neither blocking now —

1. Extend `ast_import_targets` to flag `importlib.import_module`/`__import__` calls with
   string-literal arguments (closes `NEW-M2`'s gap structurally rather than by disclosure
   alone — a nice-to-have, not required).
2. Fix the filename and `:1`/`:24` header to say "VERSION 6" (or whatever the eventual frozen
   number is) instead of "VERSION 3" — five minutes of work, zero remaining excuse.

Neither is required for PASS. Both would remove the last two items on an otherwise-clean
ledger.

---

**REVIEWER'S NOTE ON SCOPE.** Gate 1, E2b's decision-inadmissibility, E2a's cap-invariance,
Decisions 1/2, and the reachability/arithmetic verification already completed by hand in v5
were taken as fixed/unchanged and not relitigated (confirmed via `git diff 0d63591 555fe88`
touching only the four-hunk citation/disclosure region — nothing else in the document changed,
so nothing else needed re-deriving). `CRITIC_GOVERNANCE`'s v5 review (`PASS`, confirmed by
reading its verdict line) was read for context, not re-adjudicated — governance's scope, not
science's. Executions performed this round: `v2_truth_blind_verifier.py` (fresh run, 21
modules, 0 violations); `v2_reachability_verifier.py` (fresh run, PASSED);
`e2c_search_controls.control_c1b()` (executed directly, 9/9); `hasattr` probes against both
`e2c_search` and `e2c_search_controls`; a 23-file grep sweep (21 closure modules + 2 Stage 1
driver scripts) for `importlib.import_module`/`__import__`, zero hits; a full-tree sweep of
the same pattern locating and disambiguating its four unrelated, out-of-closure occurrences;
independent mapping and spot-check of 13 `e2c_search`-family document citations against live
file structure. No file was modified and reverted this round — no sabotage-then-restore test
was needed, since no new mechanism was introduced to sabotage (the diff is prose-only). No
calibration world was generated, no search was executed, no sealed evidence was touched.
`git status` is clean of review artifacts.
