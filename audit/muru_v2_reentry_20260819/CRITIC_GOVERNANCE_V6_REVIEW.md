# VERDICT

```
PASS  --  for the committed text at HEAD `3a490f5` / `555fe88`.
          A blocking condition is attached below (Part 0) to an uncommitted
          working-tree edit discovered DURING this review, which must NOT
          be committed as currently written.
```

**CRITIC_GOVERNANCE hostile re-review (round six) of
`MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md` at content-version "v6" (commit `555fe88`, HEAD
`3a490f5`), 3,003 lines.**

---

# PART 0 — CRITICAL PROCESS FINDING, DISCOVERED DURING THIS REVIEW (not part of any commit)

**While completing this review, `git status` revealed an UNCOMMITTED modification to the
target document itself, made by some other process while this review was in progress.** This
was not made by me and I did not request it. Because a hostile governance review exists
precisely to catch exactly this kind of thing, it is reported here rather than silently
ignored, reverted, or folded into the PASS without comment.

**What changed, on disk, uncommitted, right now:**

```diff
-# MURU v2 — CALIBRATION / RE-ENTRY PROTOCOL, **VERSION 3**
+# MURU v2 — CALIBRATION / RE-ENTRY PROTOCOL, **VERSION 6**

-**Status at this commit: PROTOCOL TEXT, VERSION 3. NOT YET FROZEN. D3 item 7 is UNMET.**
+**Status at this commit: PROTOCOL TEXT, VERSION 6 -- passed CRITIC_SCIENCE and
+CRITIC_GOVERNANCE hostile review (six rounds; see V6 review files). NOT YET FROZEN. D3 item 7
+is UNMET.**

-   `muru-freeze/e7-protocol-v2` is created.
+   `muru-freeze/e7-protocol-v6` is created (bumped from the stale `-v2` suffix, itself a
+small instance of the citation-staleness pattern this document names repeatedly).
```

**Two of these three hunks are fine on their own merits.** The title bump ("VERSION 3" →
"VERSION 6") and the freeze-tag suffix correction (`-v2` → `-v6`) are exactly the fix v5's
Part 6 and `CRITIC_SCIENCE_V6_REVIEW.md`'s `NEW-L1` both named as open, non-blocking, LOW-
severity staleness — and §31's tag line is prescriptive procedure text describing a step of a
freeze that has **not yet happened** (no `muru-freeze/e7-protocol-*` git tag exists at all;
confirmed by `git tag -l`), so bumping its literal suffix is not itself a false completed-
action claim.

**The third hunk is not fine, and is the most serious finding of this round.** The status
line now asserts, in the present-perfect, as a statement about the current state of the
world: *"passed CRITIC_SCIENCE and CRITIC_GOVERNANCE hostile review (six rounds; see V6
review files)."* I checked file mtimes to reconstruct the order of events:

```
CRITIC_SCIENCE_V6_REVIEW.md (verdict: PASS)  written at   ...:71
this protocol-document edit (adds the claim) written at   ...:99   (28s later)
this review file, CRITIC_GOVERNANCE_V6_REVIEW.md           written at  ...:...21  (122s later)
```

**At the moment this claim was written into the document, no `CRITIC_GOVERNANCE_V6_REVIEW.md`
existed anywhere — my review had not been conducted, let alone concluded, let alone filed.**
The document asserted its own passage of a hostile review that, from its own timeline, could
not yet have happened. It happens to be **true** now, because my independent investigation
(Parts 1–4 above, conducted before I ran the final `git status` that surfaced this edit)
genuinely reaches PASS on its own merits — but that is coincidence, not causation, and a
process that produces a true statement by asserting it before the check that would justify it
is not different in kind from the pattern this exact document spends dozens of paragraphs
forbidding for scientific results: **§0.7**'s lesson ("looking at outcomes... before the
instrument was final... is the channel `D7` exists to close"), **§4.1(iv)**'s "Order
enforcement, mechanical" (a verdict must be hash-sealed *before* anything downstream of it is
written, not after), and **§31.5**'s "Order seals" (the annotation's artifact commit must be a
strict *descendant* of the sealed verdict, never the reverse). A protocol document whose
entire governance argument is built on artifact-order enforcement had its own status line
edited to assert a reviewer's verdict ahead of that reviewer's artifact, with **no commit, no
author, no hash, and no accountability trail of any kind** — which is procedurally worse than
the citation-staleness pattern (`NEW-G`/`NEW-H`, `NEW-L1`) that has recurred for six rounds,
because those were at least committed, attributable edits a reviewer could trace to a specific
diff and author.

**Disposition.** This finding does **not** change my verdict on the actually-reviewed,
committed text at `555fe88`/`3a490f5` — every prohibition and repair audited in Parts 1–4
below was checked against that committed state and stands independently of this stray edit.
But: **this uncommitted change must not be committed in its current form.** Before any commit:
(1) the self-certifying clause must be removed or rewritten to something that does not assert
a reviewer's verdict pre-emptively — e.g. state only that CRITIC_SCIENCE's PASS is on record,
with CRITIC_GOVERNANCE's outcome cited **after** this file exists and by reference to it, not
asserted inline; (2) whoever makes that edit should do so as a normal, attributed, committed
change, the same standard this document holds every other repair to. I am not able to
determine who or what produced this edit; I can only report that it exists, when it was
written relative to my own artifact, and why it matters. Per my task instructions I have not
committed anything and have not reverted this edit myself — that decision belongs to whoever
is driving this repository next.

This is a re-confirmation, not a rubber stamp of my own v5 PASS. I re-ran all 23 prohibitions
fresh against the current HEAD rather than carrying v5's table forward, independently executed
`v2_truth_blind_verifier.py`, `v2_reachability_verifier.py`, and `control_c1b()` from their
current locations, and devised a new sabotage test against `scripts/v2_freeze_dinst.py` that I
had not run in any prior round. Result: **23/23 PASS**, both named repairs (`NEW-G`, `NEW-H`)
genuinely closed with executed re-verification (not just text edits), the new "disclosed
residual gap" paragraph's factual claims independently confirmed true by grep, and my own
sabotage test caught the failure mode it was designed to catch. **Zero new defects filed.**

One governance-level finding is recorded, not as a blocking defect but because the brief asked
for it directly: the sixth round is the second consecutive round with no new staleness
introduced, which is the first real evidence (n=1, not yet a pattern-break) that the process is
improving — but the improvement is a change in reviewer/author diligence, not a change in
tooling. No mechanical citation-sweep tool exists in this repository. See Part 3.

---

# STEP 1 — NEW-G / NEW-H FIX, VERIFIED

```
$ grep -n "e2c_search\.control_c1b\|16 module" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md
(no output, exit 1)

$ grep -n "e2c_search_controls\.control_c1b\|21 module" MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md
1438: ...PASSED** (`e2c_search_controls.control_c1b` -- moved out of `e2c_search.py` itself...
2552: ...over 21 modules, post-hardening)...
2610: ...AST call-graph walk over 21 modules...
2611: ...control `C-1b` (`e2c_search_controls.control_c1b`, 9 compared...

$ python3 scripts/v2_truth_blind_verifier.py
n_modules_scanned: 21, P8a_PASSED: true    -- matches the document exactly

$ grep -n control_c1b src/muru/v2_calibration/e2c_search.py
(zero definition hits -- only a docstring prose reference to the concept)

$ python3 -c "from muru.v2_calibration.e2c_search_controls import control_c1b; print(control_c1b())"
{'control': 'C-1b', 'compared': 9, 'n_mismatched': 0, 'mismatches': [], 'passed': True}
```

**Both fixes are real, not cosmetic.** The document's own count and path now match what
independent execution of the current, live tools produces, in both locations each defect
named. This closes `NEW-G` and `NEW-H` as filed.

---

# STEP 2 — FULL FRESH PROHIBITION AUDIT (all 23, re-run at HEAD `3a490f5`)

**FAIL = reachable at HEAD.** Every row below is evidence gathered this round by direct read,
grep, or execution — not copied from the v5 table. The v5→v6 diff is confined to four spots
(§16 P8a paragraph +8 lines, §16 `C-1b` citation, §31.1 module count, §31.8 module count +
`C-1b` citation), so most prohibitions are unaffected by this round's edit in principle, but
each was independently re-checked rather than assumed.

| # | Prohibition | v5 | v6 | Evidence (this round) |
|---|---|---|---|---|
| 1 | change the already sealed Gate 1 result | PASS | **PASS** | `git log --oneline 0d63591..HEAD -- audit/e2b_definitive_cloud_adjudication_20260818/` returns nothing; sealed dir untouched. The pre-existing `M _frozen_execution_failures.json` visible in the session's opening `git status` produces an **empty** `git diff` — no actual content change is pending against that path |
| 2 | erase the 4/71/55/14 attribution | PASS | **PASS** | Line 1816: `pi_0 = (A, B, C+D, E) = (14, 55, 71, 4)/144` verbatim, unchanged |
| 3 | make E2b decision-admissible retroactively | PASS | **PASS** | `DECISION_INADMISSIBLE` still asserted at §0.1, §3, §15 (line 1328: "enforced mechanically rather than by convention") |
| 4 | use E2b to positively license an E4 arm | PASS | **PASS** | Line 1909: the §21.4 annotation "**conditions nothing**. No terminal, licence, gate or ratification..." — unchanged from v5 |
| 5 | restore the old E2a Gate 2 routing as authoritative | PASS | **PASS** | §0.5 unchanged: Stage 0 explicitly "is not an explanation of the E2a/E2b divergence"; no routing authority reassigned to E2a |
| 6 | choose a threshold after inspecting the result it governs | PASS | **PASS** | `_host_rss_ceiling_bytes()`/`RSS_CEILING_GIB` machinery not touched by the v5→v6 diff; re-grepped `scripts/e2a_instrument_diagnostic.py:74` and `scripts/v2_stage1_calibration_run.py:44`, one declaration site each, unchanged |
| 7 | silently change denominator | PASS | **PASS** | `n=1656` (G2) and `276`/`230` (NEG, evaluable) consistent across lines 719, 1557, 1940–1996, 2142, 2798, 2961 — same figures throughout, no drift |
| 8 | silently drop cases | PASS | **PASS** | §5.2's `1932 worlds x 30 seeds = 57,960 searches` and the F06/F13–F16/F20 exclusion are stated with reasons (no symbolic truth), not silently |
| 9 | let timeout become classification | PASS | **PASS** | `TIER2_WALL_GUARD = None` at `scripts/e2a_instrument_diagnostic.py:71`, `assert terminal in DECLARED_TERMINALS` at line 452 — both re-read directly, unchanged. The disclosed-residual-gap paragraph (new this round) is about the truth-blind import scanner, not about timeout-as-classification; it does not touch this prohibition |
| 10 | hide OOM-killed cases | PASS | **PASS** | Line 1189: "`POISON_WORLD_DETERMINATION.json` records one world OOM-killed **four** times at 33.4/47.7/47.7/47.5 GB" — disclosed in the text, not hidden |
| 11 | fabricate/omit provenance fields | PASS | **PASS, and the v5-flagged staleness sub-defects are now closed** | §31.8's disclosure list still names `v2_reachability_verifier.py`, `v2_truth_blind_verifier.py`, `C-1b`, and the `e2c_classify` regression demos. This round's specific repair: both stale figures inside that same list (`NEW-G`'s "16 modules", `NEW-H`'s `e2c_search.control_c1b` path) are corrected to the figures/paths independent re-execution actually produces (21 modules; `e2c_search_controls.control_c1b`). Also verified: `E4f` freeze commit `8a2ffa50` is a confirmed ancestor of HEAD (`git merge-base --is-ancestor` = true), and the E4f artifact sha256 `0ce2755d...` reproduces exactly from `sha256sum` on the live file |
| 12 | rewrite sealed historical evidence | PASS | **PASS** | Unchanged; no touch to any file under `audit/e2b_definitive_cloud_adjudication_20260818/` or other sealed dirs this round |
| 13 | call a post-result design "preregistered" | PASS | **PASS** | Line 5 banner unchanged: "IT IS NOT HISTORICALLY PREREGISTERED AND MUST NEVER BE DESCRIBED AS SUCH." Title/version-identity mismatch (still "VERSION 3") is the pre-existing `N13`/`NEW-F` LOW finding, not this prohibition, and is unaffected by this round's diff |
| 14 | weaken an endpoint because the experiment failed | PASS | **PASS** | Unchanged; no endpoint definition touched by the v5→v6 diff |
| 15 | weaken a safety rule because a candidate failed it | PASS | **PASS** | §21.5/E6 safety-headroom machinery (lines 1929–1996) untouched by this round's diff |
| 16 | execute multiple interventions at once without a joint protocol | PASS | **PASS** | `F0` (line 2021) still assigns exactly one terminal via first-match-wins over the literal `F1..F17` order; `v2_reachability_verifier.py` re-executed this round confirms `PASSED: true`, `all_arithmetic_rules_reachable: true` |
| 17 | claim success merely because the programme reached E6 | PASS | **PASS** | No such claim found; E6-adjacent terminals (`E4A_ROUTE_CERTIFIED_NO_SAFETY_HEADROOM`, line 2648) are explicitly "Certified, not licensing" |
| 18 | change frozen thresholds / classification definitions / case population / denominator | PASS | **PASS** | Still moot in practice: `F16` fires unconditionally on route `C+D`, §36 (line 2894) still explicitly `DORMANT`. No E4f population restatement is exploitable because nothing proposes on that route today |
| 19 | change the historical 69/57 | PASS | **PASS** | Line 1006, 2795: "within 10 cases of 69/57" and its derivation unchanged |
| 20 | relabel after viewing results | PASS | **PASS** | §21.3's `RETENTION_EXONERATED := pi_B < delta` (lines 1739, 1769, 2800) is a pre-declared arithmetic predicate, unchanged; the dormant §36 clerical language (line 2914) flagged in prior rounds is unchanged and inert (route not reachable) |
| 21 | substitute Linux/x86 symbolic-search output for authoritative Mac fronts | PASS | **PASS** | `worlds_executed_on_this_host: 0` still asserted at lines 554, 1278, 2458, unchanged; no cross-architecture numeric claim added |
| 22 | execute E4a after a definitive Gate 1 FAIL | PASS | **PASS** | `GATE_1 = "FAIL"`, `GATE_1_DEFINITIVE = "YES"` (line 1687) still governs; "nothing in the ratification re-arms it" unchanged |
| 23 | invent protocol authority | PASS | **PASS, re-verified as the load-bearing check** | Re-ran `grep -n "EXECUTABLE\|maximum.autonomy\|maximum delegat\|Decision 2\b"` fresh — **21 hits** (not v5's stated "16"; see note below), read every one in full context. `diff` of the matched-line **text** (stripped of line numbers) between v5's copy of the document and this HEAD is **byte-identical** — the v5→v6 diff did not touch any of these lines; only line numbers shifted by the +8 lines inserted earlier in the file. Every hit states the same fact once, consistently: E4f is `PREREGISTERED but NOT AUTHORIZED TO EXECUTE` today. `grep -rniI "maximum.autonomy\|maximum delegat"` across the **whole repository** (not just this file) returns hits only inside prior review documents (`CRITIC_GOVERNANCE_V3/V4/V5_REVIEW.md`, `V3_REPAIR_LEDGER.md`) describing the *retracted* claim historically — zero live instances in the current protocol text, in `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md`, or in any tag |

**Result: 23/23 PASS.** Identical to v5's tally, independently re-derived. No prohibition
regressed. The v5 review's own hit-count for the #23 sweep ("16") does not reproduce under the
same command against v5's own document text — my count is 21 against both v5's and v6's copies
of the file, and the matched text is identical between the two versions. This looks like a
counting slip in the v5 report rather than a missed instance (the important fact — zero
surviving stale authority claims — holds under both counts, and I read all 21).

---

# CONFIRMATION OF NEW-G / NEW-H

| id | v5 finding | v6 verdict | basis |
|---|---|---|---|
| **NEW-G** | Disclosed module-scan count ("16 modules") stale by the round's own AST-hardening; live count is 21 | **REPAIRED, executed re-verification matches exactly** | Both occurrences (§31.1 line 2552, §31.8 line 2610) now read "21 modules"; `python3 scripts/v2_truth_blind_verifier.py` run fresh this round reports `n_modules_scanned: 21, P8a_PASSED: true` — exact match, not just a plausible-looking number |
| **NEW-H** | `C-1b` path citation (`e2c_search.control_c1b`) stale after the function's move to `e2c_search_controls.py` | **REPAIRED, and the reason for the move is now stated inline** (satisfies the "add one sentence naming the new module" part of the minimal repair, done at §16 line 1438 rather than §12, which is an equivalent placement since §12 never carried a path citation to begin with) | Both occurrences (§16 line 1438, §31.8 line 2611) now read `e2c_search_controls.control_c1b`. `grep control_c1b src/muru/v2_calibration/e2c_search.py` returns zero definition hits (one docstring prose mention only); `control_c1b()` imported and run fresh from `e2c_search_controls.py` reproduces `compared: 9, n_mismatched: 0, passed: True` exactly as disclosed |

---

# STEP 2b — THE NEW "DISCLOSED RESIDUAL GAP" PARAGRAPH, FACT-CHECKED INDEPENDENTLY

**Location.** §16, immediately after the `P8a` execution paragraph (lines 1413–1420), added
this round in response to `CRITIC_SCIENCE`'s finding.

**Claim 1: "The verifier's AST-based import discovery finds `import`/`from...import`
statements; it does not resolve `importlib.import_module(...)` calls ... or `__import__(...)`."**
Read `scripts/v2_truth_blind_verifier.py` in full: its AST walk (`ast_import_targets`,
`module_call_targets`) matches on `ast.Import`/`ast.ImportFrom` node types only. There is no
handling of `ast.Call` nodes whose function is `importlib.import_module` or the `__import__`
builtin as an import-discovery mechanism (the module's own use of `importlib.import_module` at
line 103 is the verifier's *own* mechanism for loading a module *once its name is already
known from static `import` discovery* — it does not detect a *target* module reached only via
a dynamic string). **Claim verified true by direct code read.**

**Claim 2: "`grep` confirms neither mechanism appears anywhere in the current entry-point
closure or Stage 1 driver."** Independently enumerated the verifier's own 21-module closure
(`transitive_import_closure(ENTRY_MODULES)`, executed fresh this round) and grepped every one
of the 21 source files, plus both Stage 1 driver files
(`scripts/v2_stage1_calibration_run.py`, `scripts/v2_stage1_scoring.py`), for
`importlib.import_module\(|__import__\(`. **Zero hits in every file.** Claim verified true.

**Claim 3 (implicit): the gap is disclosed as a known limitation, not silently left implicit.**
True on its face — the paragraph exists and is boxed/called out, is scored MED, and states the
exploit condition plainly ("a future edit that introduced one would not be caught").

**This paragraph passes its own fact-check.** It is an honest disclosure of a real, currently-
inert tooling limitation, and its factual claims reproduce under independent execution rather
than being asserted on faith.

---

# STEP 3 — NEW ADVERSARIAL TEST (not run in any prior round)

**Target:** `scripts/v2_freeze_dinst.py`, the freeze-record generator §31.8 credits with
"closing the four-times-stale pattern." No prior round (`CRITIC_GOVERNANCE_V2` through `V5`)
tested this specific script. `CRITIC_GOVERNANCE_V5`'s sabotage tests targeted
`v2_reachability_verifier.py`'s §32 table parsing instead.

**Test A — does the generator correctly detect and flag a live tool change?**

```
$ cp scripts/e2a_instrument_diagnostic.py /tmp/e2a_backup.py
$ cp DINST_FREEZE_CURRENT.txt /tmp/dinst_freeze_backup.txt
$ python3 scripts/v2_freeze_dinst.py            # baseline
tool_hash = b086fad7...

$ sed -i 's/TIER1_CPU_SECONDS = 60/TIER1_CPU_SECONDS = 61   # SABOTAGE TEST/' \
    scripts/e2a_instrument_diagnostic.py
$ python3 scripts/v2_freeze_dinst.py
WARNING: the tool has uncommitted changes; commit before treating this as a freeze.
tool_hash = 948853b3...                          # CHANGED, correctly

$ cat DINST_FREEZE_CURRENT.txt
# generated_from_commit: 3a490f54...  [UNCOMMITTED CHANGES TO THE TOOL]
    TIER1_CPU_SECONDS = 61                        # reflects the sabotage, correctly
```

The generator worked exactly as documented: the hash changed, the sabotaged constant's new
value propagated into the binding statement, and the uncommitted-change warning fired both on
stderr and inside the written file's header. **PASS — the generator itself is honest.**

**Test B — the sharper question: does anything gate *execution* on the freeze record still
being current, or only the act of *regenerating* it?**

```
$ cp /tmp/dinst_freeze_backup.txt DINST_FREEZE_CURRENT.txt   # restore OLD (pre-sabotage)
                                                              # record; tool STAYS sabotaged
$ grep -n "DINST_FREEZE_CURRENT\|freeze_dinst" scripts/e2a_instrument_diagnostic.py
(no output -- the tool never reads its own freeze record)

$ python3 scripts/e2a_instrument_diagnostic.py --analyze-only
{ ... "TERMINAL": "D-INST-DETERMINATE", ... }        # RC=0, runs clean, no error,
                                                       # no warning of any kind
```

**Result: the sabotaged tool ran to a clean terminal under a stale, uncommitted freeze record,
with no mechanical objection from anywhere in the pipeline.** `scripts/e2a_instrument_diagnostic.py`
contains no self-hash check against `DINST_FREEZE_CURRENT.txt` at preflight or anywhere else. The
only thing standing between "tool changed" and "stale freeze record used for a real run" is an
executor remembering to run `v2_freeze_dinst.py` and reading its warning before proceeding — the
exact same reliance-on-discipline-not-code pattern `CRITIC_GOVERNANCE_V5`'s Part 4 already flagged
for the SIGPROF gap, now confirmed to apply to Stage 0's own freeze binding as well.

**Is this a new defect, or already covered?** I am **not** filing it as a new numbered defect,
for the same reason v5 didn't file the SIGPROF gap as blocking: §31.8's actual claim is narrower
than "Stage 0 cannot run under a stale record" — it claims only that regeneration "states whether
the tool has uncommitted changes, so a stale freeze cannot be committed silently," which is true
and which Test A confirms. The document never claims execution-time enforcement here, so this is
not a fabricated-safety-property finding under prohibition #9/#23. It is, however, worth recording
explicitly as a second instance of the same **class** of gap Part 4 of the v5 review already
named — restated below in Step 4, since it directly bears on what "freeze-ready" does and does not
mean.

**Cleanup.** Both files restored from backup and confirmed byte-identical (`diff` clean); the
stray `DINST_RESULT.json` produced by the `--analyze-only` probe run was deleted; `git status`
is clean.

**Structural question — is the "stale citation survives a repair made elsewhere" pattern now
less likely to recur a sixth time?** Searched for a mechanical sweep tool (something that greps
a diff for every symbol/path touched and checks the whole document for other citations of it)
under `scripts/`. **None exists.** The document repeatedly invokes a "static citation checker"
(§4.1, §16, §31.1, §31.8) but that tool is scoped narrowly to rejecting a *proposed change*
that cites an E2b or Stage-0 identifier as decision support — a different mechanism from a
general staleness sweep, and it is not implemented as a script anywhere in this repository
either (grep across `scripts/*.py` for "citation" returns zero hits). **So: no, the document's
own structure does not yet make this failure mode mechanically harder to reintroduce.** What
changed this round is not tooling but outcome: this is the first round (of five rounds that
each closed a hostile review's named findings) in which the closing edit introduced **zero**
fresh staleness of its own, confirmed by re-running every tool the round's disclosure text
cites and finding every cited number and path reproduces exactly. That is one clean data point,
not a structural guarantee — the next author who moves a function or changes a scanned-module
count still has no automated backstop, only a hostile reviewer's grep. I record this as a
genuine, if modest, governance finding: **diligence improved; tooling did not.**

---

# NEW DEFECTS THIS ROUND

**None.** Zero new defects filed. Test A confirms the named repair tool works as documented.
Test B surfaces a real but already-disclosed-in-kind gap (freeze-record staleness has no
execution-time mechanical gate, same class as the SIGPROF gap) that does not meet the bar for a
numbered defect because the document's own claim about it is accurately scoped and true, not
overstated.

---

# STEP 4 — THE BIG QUESTION: SIX ROUNDS IN, IS THIS SOUND ENOUGH TO FREEZE AS PROTOCOL TEXT?

**Yes, for the protocol *text*, with the same two-tier boundary v5 already drew and this round
does not disturb.** The trajectory (v2🔴 → v3🔴 → v3-again🔴 → v4🔴 → v5🟢 → v6🟢) is two
consecutive clean rounds, the first genuinely fresh 23/23 re-derivation this round confirms
rather than assumes, and — new information this round — the first round in which a hostile
reviewer's own newly-devised test (Test A/B above) found the tooling behaving exactly as
documented rather than finding an undisclosed gap. Six rounds of adversarial pressure against
the same 23 prohibitions with zero live FAILs surviving to round six is a real signal, not a
formality.

**What is settled, as of this commit, for the frozen *text*:**
- All 23 prohibitions are reachable-clean, independently re-verified this round.
- §21.2 row 3 / §22 `F16` / §32 correctly assign `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` to a
  certified `C+D` route today, and no live text anywhere asserts otherwise (#23, checked with a
  full-document sweep plus a whole-repository grep, both this round).
- The disclosure text in §16 and §31.8 (the object of `NEW-G`/`NEW-H`) is now internally
  accurate: every count and path it cites reproduces under independent execution of the current
  code.
- The new §16 disclosure paragraph is itself accurate, checked against the actual verifier
  source and the actual 21-module closure, not merely asserted.
- The status line (line 24), §31's "NOT YET PERFORMED," and the closing block (line 3000, with
  the pre-existing "No module written" imprecision carried unrepaired but disclosed elsewhere in
  §0's own status table) all still correctly say freeze has not happened and nothing is sealed.

**What is explicitly NOT settled by this PASS, and must be true separately at Stage 1
*execution* time before this document's own disclosed gates are satisfied:**

1. **The SIGPROF/subprocess-isolation fix (§25.2).** `v2_stage1_scoring.py` must actually
   implement the subprocess-isolated, OS-enforced timeout the box already names and points at a
   working reference implementation for (`e2a_instrument_diagnostic.py`'s own pattern). As of
   this commit it is **not implemented and not enforced by any preflight check** — the document
   says so itself. Per v5's Part 4 recommendation (not repeated as a new finding, since it is
   unchanged and already on record): this should become a hard preflight assertion, the same
   pattern `S0-5` already uses for the interpreter check, before Stage 1 runs at scale.
2. **The freeze-record binding for Stage 0 (this round's Test B).** `DINST_FREEZE_CURRENT.txt`
   must actually be regenerated after any change to `scripts/e2a_instrument_diagnostic.py` and
   *read and acted on* by whoever runs Stage 0 — nothing in the tool itself refuses a run under
   a stale record. This is a discipline requirement, not a code-enforced one, same as (1).
3. **A protocol-owner ratification record for E4f**, or the route stays permanently at
   `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE` regardless of certification strength. `§2.1`/`N6`'s
   finding is that no such record exists today; nothing in this document can create it, and the
   document is correct not to claim it does.
4. **The freeze procedure itself (§31)** — commit hashing, tag creation, the tuning ledger, the
   Stage 0/Stage 1 ordering seal — must actually be executed once, results-blind, as a discrete
   act this document currently states has "NOT YET BEEN PERFORMED." Six rounds of text review
   have never substituted for that act, and this document does not claim they have.

**In one sentence:** the protocol *text* is freeze-ready — its governance claims are accurate,
its disclosed gaps are honestly disclosed and independently verified as honestly disclosed, and
six rounds of hostile review have driven its prohibition surface to a clean, re-derived 23/23 —
but "freeze-ready text" here means the document no longer lies about its own state, not that
Stage 1 is clear to execute; items 1–4 above are the concrete, checkable list of what changes
between "text frozen" and "Stage 1 admissible," and a reader who treats this PASS as clearance
to run Stage 1 today is misreading it.

---

# SPOT-CHECK LOG, THIS ROUND

```
$ grep -n "e2c_search\.control_c1b\|16 module" ...PROTOCOL_V3.md       -> zero hits
$ grep -n "e2c_search_controls\.control_c1b\|21 module" ...            -> 4 hits, all correct
$ python3 scripts/v2_truth_blind_verifier.py                           -> n_modules_scanned: 21,
                                                                            P8a_PASSED: true
$ grep -n control_c1b src/.../e2c_search.py                             -> 0 definition hits
$ python3 -c "control_c1b()" from e2c_search_controls.py               -> compared:9, mismatched:0,
                                                                            passed: True
$ python3 scripts/v2_reachability_verifier.py                          -> PASSED: true,
                                                                            all_arithmetic_rules_
                                                                            reachable: true
$ git merge-base --is-ancestor 8a2ffa50 HEAD                           -> true
$ sha256sum MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md                 -> 0ce2755d... (matches
                                                                            document exactly)
$ grep -rniI "maximum.autonomy|maximum delegat" (whole repo)           -> hits only in prior
                                                                            *_REVIEW.md files
$ grep "importlib.import_module(|__import__(" across 21-module closure -> 0 hits (all 21 files
                                                                            + both Stage-1 driver
                                                                            files individually
                                                                            checked)
$ [sabotage: TIER1_CPU_SECONDS 60->61, uncommitted] + v2_freeze_dinst.py -> hash changed,
                                                                            uncommitted-change
                                                                            warning fired, value
                                                                            propagated correctly
$ [restore pre-sabotage freeze record, tool stays sabotaged]
   python3 e2a_instrument_diagnostic.py --analyze-only                  -> RC=0, clean terminal,
                                                                            no staleness warning
                                                                            anywhere (Test B)
$ [restore both files from backup]                                      -> diff clean, git status
                                                                            clean after removing
                                                                            the stray probe output
```
