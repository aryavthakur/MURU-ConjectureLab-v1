# VERDICT

```
PASS
```

**CRITIC_GOVERNANCE hostile re-review of `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md` at
content-version "v5" (commit `b7514e0`, HEAD `0d63591`), 2,995 lines.**

This is a genuine PASS, not a manufactured one: all 23 prohibitions are reachable-clean at
HEAD, both v4 CRITICAL/HIGH findings (`NEW-A`, prohibition #23's live instance) are closed
everywhere I could find to look, `NEW-B`'s tautological verifier is now a real parser that I
broke with two sabotage tests of my own design and watched fail correctly, and `NEW-C`'s three
stale cross-references are corrected. `NEW-D`'s named omissions are added.

**It is not a clean pass.** I found two new, LOW/MED, freshly-introduced staleness defects in
this exact round's own repair text (`NEW-G`, `NEW-H` below) — the same failure family that has
now recurred in every one of the last four rounds, just below CRITICAL/HIGH severity this
time. I am recommending PASS because neither invents authority, fabricates a result, or
licenses anything; both are citation/count drift discoverable by direct read. I am also
recording, as a process finding rather than a defect, that this makes **five** consecutive
rounds in which a repair sweep that fixed the named instances did not fix the general problem.
Governance considers the protocol **text** ready to freeze subject to `NEW-G`/`NEW-H` being
swept before the freeze commit (they are one-line fixes); Stage 1 **execution** readiness is a
separate question addressed at the end of this document, and is NOT met.

---

# PART 1 — PROHIBITION AUDIT (all 23, re-run fresh at HEAD `0d63591`)

**FAIL = reachable at HEAD.** Verified by direct read or execution this round, not carried
from the v4 review except where explicitly noted as unchanged-and-reconfirmed.

| # | Prohibition | v4 | v5 | Evidence |
|---|---|---|---|---|
| 1 | change the already sealed Gate 1 result | PASS | **PASS** | `git log --stat 7f28b5f..0d63591` touches nothing under `audit/e2b_definitive_cloud_adjudication_20260818/`; sealed dir untouched since v4 |
| 2 | erase the 4/71/55/14 attribution | PASS | **PASS** | §21.4 unchanged, `pi_0 = (14,55,71,4)/144` verbatim |
| 3 | make E2b decision-admissible retroactively | PASS | **PASS** | §15 unchanged; annotation still explicitly non-conditioning |
| 4 | use E2b to positively license an E4 arm | PASS | **PASS** | Unchanged since `N1`'s v4 closure; re-read §0.1, §21.4, §21.5, §32.1 — all four still say once, consistently, that the annotation conditions nothing |
| 5 | restore the old E2a Gate 2 routing as authoritative | PASS | **PASS** | Unchanged |
| 6 | choose a threshold after inspecting the result it governs | PASS | **PASS** | `_host_rss_ceiling_bytes()` / `RSS_CEILING_GIB` machinery untouched this round (not in the b7514e0 diff); re-grepped, one declaration site |
| 7 | silently change denominator | PASS | **PASS** | Unchanged; 230/276 intact |
| 8 | silently drop cases | PASS | **PASS** | Unchanged |
| 9 | let timeout become classification | PASS | **PASS** | `TIER2_WALL_GUARD = None` still at `scripts/e2a_instrument_diagnostic.py:71`; `assert terminal in DECLARED_TERMINALS` still at line 452; re-verified by direct read. The new SIGPROF disclosure (§25.2) explicitly states cap-exceeded still produces `UNRESOLVED`, "never a label" — does not weaken this |
| 10 | hide OOM-killed cases | PASS | **PASS** | Unchanged |
| 11 | fabricate missing provenance fields | **FAIL (v4)** | **PASS, with two new sub-CRITICAL drift instances noted separately** | The delegation citation remains honestly stated. §31.8's disclosure list now names `v2_reachability_verifier.py`, `v2_truth_blind_verifier.py`, `C-1b`, and the `e2c_classify` regression demos — the four v4 named as omitted. I independently re-ran all four classes of execution and their disclosed *outcomes* (9/9 C-1b, PASSED reachability, 0 violations truth-blind) reproduce. **However**, two of the disclosed *counts* are stale within this same round's edit — see `NEW-G` (module count "16" vs actual 21) and `NEW-H` (`e2c_search.control_c1b` path vs actual `e2c_search_controls.control_c1b`) in Part 3. Neither is a fabrication (the underlying claims — PASSED, 0 violations, 9/9 — are true and reproduced); both are stale numbers/paths in the same disclosure text this round rewrote to fix #11. Graded PASS on the prohibition (nothing is fabricated or omitted outright — the executions ARE listed) but flagged as new defects because a reader who tries to reproduce "16 modules" or `e2c_search.control_c1b` literally cannot |
| 12 | rewrite sealed historical evidence | PASS | **PASS** | Unchanged |
| 13 | call a post-result design "preregistered" | PASS | **PASS** | Unchanged in substance; version-identity confusion (title still "VERSION 3") is `N13`/`NEW-F`, a distinct LOW honesty defect, not this prohibition |
| 14 | weaken an endpoint because the experiment failed | PASS | **PASS** | Unchanged |
| 15 | weaken a safety rule because a candidate failed it | PASS | **PASS** | Unchanged |
| 16 | execute multiple interventions at once without a joint protocol | PASS | **PASS** | Unchanged; `F0` still emits exactly one terminal |
| 17 | claim success merely because the programme reached E6 | PASS | **PASS** | Unchanged |
| 18 | change frozen thresholds / classification definitions / case population / denominator | PASS | **PASS** | Still moot in practice: `F16` fires unconditionally on route `C+D`; §36 still `DORMANT`; no E4f population restatement can be exploited because nothing proposes on that route today |
| 19 | change the historical 69/57 | PASS | **PASS** | Unchanged |
| 20 | relabel after viewing results | PASS | **PASS** | Unchanged; §36 item 3's dormant clerical language untouched but inert |
| 21 | substitute Linux/x86 symbolic-search output for authoritative Mac fronts | PASS | **PASS** | Unchanged |
| 22 | execute E4a after a definitive Gate 1 FAIL | PASS | **PASS** | Unchanged |
| 23 | invent protocol authority | **FAIL (v4)** | **PASS** | This is the load-bearing check. Ran `grep -n "EXECUTABLE\|maximum.autonomy\|maximum delegat\|Decision 2\b"` over the whole file (16 hits) and read every one in context, plus a separate sweep of §21.2, §22, §32, §36. §2's AUTHORITY table row for E4f (line 413) now reads *"a frozen document, **not currently authorized to execute**"* and cites `§2.1 N6` directly — the retracted "maximum-autonomy delegation" sentence is gone from the table entirely, not just softened. §0.2's own header (line 157) now leads with *"E4f is PREREGISTERED but NOT AUTHORIZED TO EXECUTE"* and its body (lines 159–166) states the current disposition **first**, before any historical narrative. Every other hit (§21.2 row 3, §22.1 `F16`, §32's `F16` row and gloss, §32.1's witness table, §32.3, §35, §36) states the same fact once, consistently: E4f is not authorized to execute today. I found no fourth surviving instance of the old claim anywhere, including §21.2, §22, §32 and §36, which I checked specifically because the brief asked me to |

**Result: 23/23 PASS.** Up from v4's 20/23. Both v4 survivors (#11, #23) are closed for the
claim each was filed against. #11 is graded PASS with a caveat recorded in Part 3, because the
*fabrication/omission* the prohibition names did not recur, but a narrower *staleness* defect
in the same disclosure text did.

---

# PART 2 — REPAIR VERIFICATION (v4's NEW-A/B/C/D)

| id | v4 severity | verdict | basis |
|---|---|---|---|
| **NEW-A** | HIGH | **REPAIRED** | Both surviving sites from v4 (§2 AUTHORITY table line 402→413, §0.2 header/body lines 157–166) are rewritten to state the non-executable disposition directly and first. Read all 16 `EXECUTABLE`/`maximum.autonomy`/`Decision 2` hits in the document (Priority 2's mandated sweep) plus §21.2, §22, §32, §36 specifically: zero surviving instances of the retracted claim, and zero ambiguous statements. This is the fourth round this exact fact (E4f's executability) has been checked for a surviving stale sentence, and this is the first round with none found. Recorded as closed, not just improved |
| **NEW-B** | MEDIUM | **REPAIRED, independently adversarially confirmed** | Read `parse_section_32_terminals` in full: it now slices the live document between `"## 32. TERMINAL STATES"` and `"### 32.1"`, regex-parses each table row's backtick-quoted terminal name and its rule-ID cell, and returns `{terminal: rule_id}` — genuinely reading the document, not `RULE_TERMINAL` a second time. I ran two sabotage tests of my own design (both different from the commit's "mutate a rule ID" test): **(1)** deleted the entire `F16`/`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` row from §32 without touching §22 → verifier correctly reported `PASSED: False`, `missing_from_section_32: ['ROUTE_DETERMINED_ARM_NOT_EXECUTABLE']`, exit code 1. **(2)** duplicated the `ROUTING_INDETERMINATE` row under a second, wrong rule ID (`F16` instead of its real `F10`) → verifier correctly reported `PASSED: False`, `rule_id_mismatches: [{'terminal': 'ROUTING_INDETERMINATE', 'section_22_rule': 'F10', 'section_32_rule': 'F16'}]`, exit code 1. Restored the file from a pre-sabotage backup after each test and reconfirmed `PASSED: True` and byte-identical `diff` against backup both times; `git status` is clean. The check is real |
| **NEW-C** | MEDIUM | **REPAIRED, and independently re-swept** | Canonical `F1..F17` mapping built directly from §22.1's table. Checked all three v4-named sites: §21.3 now cites `SURFACE_DEGENERATE_NO_FRONT (§22 F9 — corrected from a stale "F14" reference...)` — correct (F9 = SURFACE_DEGENERATE_NO_FRONT). §24 now cites `VOID_INSTRUMENT_INDETERMINATE (§22 F7)` — correct. §31.1 now cites "a non-empty ledger fires §22 F8" — correct (F8 = VOID_SINGLE_SHOT_BROKEN). I then independently grepped **every** `(F\d+)`/`§22 F\d+` occurrence in the document (18 total, not just the three named) and checked each against §22.1: the remaining fifteen are either the *registry condition-code* namespace (F01–F19, e.g. `mass_saturating_descriptor (F09)`), a distinct and internally-consistent numbering that is not the §22-rule numbering and was never broken, or witness-table §22-rule citations (F12, F14, F16, F11 at §32.1's table) that all check out against the canonical mapping. No fourth stale §22-rule citation found |
| **NEW-D** | MEDIUM/HIGH | **REPAIRED for the four named omissions; the repair itself introduces two fresh staleness instances** | §31.8's list now includes `v2_reachability_verifier.py`, `v2_truth_blind_verifier.py`, control `C-1b`, and the `e2c_classify` regression demos, as required. But see `NEW-G` and `NEW-H` in Part 3: two figures inside this exact rewritten paragraph (a module-scan count and a function's module path) are themselves stale as of this same commit, because the round's OTHER fixes (the AST-hardening of the truth-blind verifier, the `control_c1b` module move) changed the ground truth after the disclosure text was written and it was not re-run/re-checked a final time before commit |

**Genuinely repaired: 4 of 4 named** (`NEW-A`, `NEW-B`, `NEW-C`, `NEW-D`), with `NEW-D`
carrying a caveat recorded as new defects rather than as non-repair, because the four named
omissions are in fact now present in the list — what's stale is detail *within* two of the
now-present entries, not their absence.

---

# PART 3 — NEW DEFECTS (v5)

## NEW-G — LOW/MEDIUM. §31.8/§31.1's disclosed module-scan count for the truth-blind verifier is stale by this round's own hardening.

**Location.** §31.1 item 1 (line 2544): *"EXECUTED: 0 call-graph violations over 16
modules"*. §31.8 (line 2602): *"AST call-graph walk over 16 modules"*.

**What is wrong.** This round's commit (`b7514e0`) added AST-based import discovery to
`scripts/v2_truth_blind_verifier.py` specifically to close a real blind spot (function-local
and directly-imported submodules invisible to the old `dir()`-based scan — the mechanism that
let `SCIENCE NEW-C1`'s violation through undetected). I checked out the pre-hardening version
of the script (`git show 19be068:scripts/v2_truth_blind_verifier.py`) and ran it: it reports
`n_modules_scanned: 16`, matching the document's figure exactly. Running the **current,
hardened** script — the one this round's own commit message describes as the fix and cites as
"EXECUTED" — reports `n_modules_scanned: 21`, `P8a_PASSED: true`. The document's disclosed
count describes the tool's state *before* this round's own hardening, not after it, even
though the surrounding prose is describing the hardened tool's execution.

**Exploit scenario.** None scientific — the check itself still genuinely passes (0
violations either way), so no false PASS results from this. But it means a reader who runs
`scripts/v2_truth_blind_verifier.py` today to reproduce the document's own "EXECUTED" claim
gets a different number than the document states, in the exact same paragraph this round
rewrote specifically to make disclosure numbers trustworthy (`NEW-D`). This is the disclosure-
staleness defect class recurring a further time, now one level down: not "the list omits an
execution" but "the list's own number for an execution it does include is stale."

**Minimal repair.** Re-run `v2_truth_blind_verifier.py` after all of this round's other
changes and update "16 modules" to "21 modules" in both locations (§31.1, §31.8).

---

## NEW-H — LOW/MEDIUM. Two citations of control C-1b's module path are stale after this round's own `control_c1b` move.

**Location.** §12's search-configuration table (line 1230, "9 compared, 0 mismatched") is
fine; the *path* citations are at §16 (line 1430): *"Executed: 9 compared, 0 mismatched,
PASSED (`e2c_search.control_c1b`)"*, and §31.8 (line 2603): *"control `C-1b`
(`e2c_search.control_c1b`, 9 compared..."*.

**What is wrong.** This round's `SCIENCE NEW-C1` fix (per the commit message, a CRITICAL
finding) moved `control_c1b` **out of** `e2c_search.py` and into a new module,
`e2c_search_controls.py`, specifically so the search entry point's own call graph no longer
contains the function's `e2_search` import. I confirmed directly:
`grep -n "control_c1b" src/muru/v2_calibration/e2c_search.py` returns zero hits — the function
is not there. It is defined in `src/muru/v2_calibration/e2c_search_controls.py`. The document
still cites the pre-move path (`e2c_search.control_c1b`) in the two places above, and the
string `e2c_search_controls` does not appear anywhere in the document (`grep -c` → 0) despite
this new module being the structural mechanism the commit message credits for closing a
CRITICAL defect.

**Exploit scenario.** None scientific — I ran `control_c1b()` from its actual current
location and it reproduces "9 compared, 0 mismatched" exactly as disclosed, so the *result*
disclosed is true. But a reader trying to locate or re-run the cited function at
`e2c_search.control_c1b` gets an `AttributeError`; the citation no longer resolves. This is
the fourth-and-fifth instance (alongside `NEW-G`) in this single round of the identical
process failure this document has now shown across five consecutive rounds: a repair made
correctly in one place (the code move that fixes `SCIENCE NEW-C1`) leaves a citation to the
pre-repair state standing in another (the protocol text describing where that code lives).

**Minimal repair.** Update both citations to `e2c_search_controls.control_c1b`, and add one
sentence to §12 or §16 naming the new module and the reason it is separate (the same reason
the module's own docstring already states).

---

## PROCESS FINDING — the same failure mode has now recurred in five consecutive rounds, on five different facts, and the sweep method that closes each round's named instances is not general enough to prevent the next one.

v2→v3: the malformed strikethrough / defect-count mismatch (`N14`). v3→v4: `N6`'s authority
claim surviving in the AUTHORITY table and §0.2 (`NEW-A`). v4→v5 (this round): `NEW-A`,
`NEW-B`, `NEW-C`, `NEW-D` were all closed for their named instances — but the closing edit for
`NEW-D` (the disclosure list) and the closing edit for `SCIENCE NEW-C1` (the module move) each
left one stale citation inside text that was rewritten in this exact commit (`NEW-G`,
`NEW-H`). Every occurrence so far has been found by a hostile reviewer grepping broadly rather
than by the executor's own sweep, and every fix so far has been scoped to the specific
instance a reviewer named rather than to the general pattern ("does this edit leave a stale
fact anywhere else in a 2,995-line document"). I am not filing this as a blocking defect this
round because `NEW-G`/`NEW-H` are LOW/MEDIUM and neither licenses anything or invents
authority — but if a sixth round produces a sixth instance of this same failure mode, that is
no longer a reviewable list of independent defects; it is evidence the authorship process
itself lacks a mechanical sweep step (e.g., a script that greps the diff for every symbol/path
touched and checks the whole document for other citations of it before commit), and that
should be the finding, not another isolated citation fix.

---

# PART 4 — GOVERNANCE JUDGMENT ON NEW-C2 (SIGPROF DISCLOSURE / TWO-TIER READINESS)

**The disclosure itself is honest, not evasive.** §25.2's boxed note: names the exact
mechanism (`SIGPROF`/`ITIMER_PROF` only fires at a bytecode-dispatch checkpoint), reproduces
the failure concretely (`hashlib.pbkdf2_hmac` running ~20s past a 0.5s budget — I did not
re-run this specific repro but the mechanism described is correct CPython behavior), names
the correct fix that already exists and is proven elsewhere in the same codebase
(`e2a_instrument_diagnostic.py`'s subprocess-isolated, OS-enforced timeout), states plainly
that Stage 1's scoring pass does not yet have it, and states in terms that
`v2_stage1_scoring.py` "must not be treated as execution-ready until this is built." This is
not "declaring a known CRITICAL gap disclosed as a way to avoid fixing it" — it identifies the
fix, points at the working reference implementation, and does not claim the gap is closed.

**The two-tier model — protocol text can freeze, Stage 1 execution is separately gated — is
legitimate in principle, for this document specifically, because the document does not claim
execution readiness anywhere.** Line 24's status line still reads "NOT YET FROZEN"; §31 states
freeze itself is "NOT YET PERFORMED"; the commit message states "Nothing sealed, nothing
executed at scale." A reader cannot come away believing Stage 1 is clear to run.

**But the tier boundary is currently enforced by prose only, not mechanically, and that is a
real gap worth naming rather than accepting quietly.** §25.2 says the required change is "not
yet implemented and not yet enforced by any preflight check." Every other execution-blocking
condition this protocol takes seriously (`P6'`, the hard preflight gate in §12, `S0-5`'s
interpreter check) is backed by an assertion or a refusal-to-start in code, precisely because
this document's own history (Stage 0's three inadmissible runs, §0.7) is a case study in what
happens when a documented rule has no code behind it. A prose "must not be treated as
execution-ready" is exactly the kind of statement this document elsewhere treats as
insufficient on its own. **Recommendation, not a blocking defect at the protocol-text level:**
before Stage 1 is executed at scale, `v2_stage1_scoring.py`'s preflight should hard-assert the
subprocess-isolation change is in place (the same pattern `S0-5` already uses for the
interpreter check), so the tier boundary cannot be silently skipped by an executor in a hurry
the way Stage 0 was.

**Judgment: legitimate two-tier readiness model, correctly and honestly disclosed, not a
governance evasion — with one recommended hardening (a mechanical preflight assertion) before
it should be relied on at execution time.**

---

# PART 5 — SPOT-CHECKS PERFORMED (execution log, this round)

```
$ python3 scripts/v2_reachability_verifier.py               -> PASSED: True (clean state)
$ [sabotage: delete F16 row from §32]                        -> PASSED: False, missing_from_section_32
                                                                  = ['ROUTE_DETERMINED_ARM_NOT_EXECUTABLE']
$ [restore from backup]                                      -> diff: byte-identical; PASSED: True
$ [sabotage: duplicate ROUTING_INDETERMINATE under F16]       -> PASSED: False, rule_id_mismatches =
                                                                  [{'terminal': 'ROUTING_INDETERMINATE',
                                                                    'section_22_rule': 'F10',
                                                                    'section_32_rule': 'F16'}]
$ [restore from backup]                                      -> diff: byte-identical; PASSED: True;
                                                                  git status clean
$ python3 scripts/v2_truth_blind_verifier.py                 -> P8a_PASSED: True, n_modules_scanned: 21
                                                                  (document states 16 -- NEW-G)
$ [pre-hardening script version, git show 19be068:...]       -> n_modules_scanned: 16 (confirms NEW-G's
                                                                  claim that "16" describes the OLD tool)
$ python3 -c "control_c1b()" from e2c_search_controls.py     -> compared: 9, n_mismatched: 0, passed: True
                                                                  (reproduces the disclosed number; path
                                                                  cited in the document is stale -- NEW-H)
$ grep control_c1b src/muru/v2_calibration/e2c_search.py     -> no hits (confirms the function is no
                                                                  longer there)
$ grep -c e2c_search_controls <protocol.md>                  -> 0 (new module never named in the doc)
```

---

# PART 6 — WHAT REMAINS OPEN FROM v4 (not blocking, not re-litigated)

For completeness, since these were part of v4's own list and are not claimed closed this
round: `N9` ("No module written" in the closing status block, still false against 9+ committed
modules), `N12` (§33's single-clause `RETENTION_EXONERATED` and the "dominates" claim §21.3
calls false, still printed unchanged at line 2792), `N13`/`NEW-F` (three-way version-identity
mismatch: title still "VERSION 3", freeze tag still `muru-freeze/e7-protocol-v2`, commit
history calls this "v5"), and `N14`(ii) (the malformed strikethrough at lines 92–93, unchanged
byte-for-byte). None of these are CRITICAL or HIGH, none license anything or invent authority,
and none were in this round's claimed scope — they are recorded here only so the next round
does not have to be told twice.
