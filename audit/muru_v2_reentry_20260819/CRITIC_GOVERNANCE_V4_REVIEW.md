# VERDICT

```
FAIL
```

**CRITIC_GOVERNANCE hostile re-review of `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md` at
content-version "v4" (commit `19be068`, HEAD `7f28b5f`), 2,947 lines.**

**Note on the artifact's own identity, checked first because the brief asked for it.** The
filename and every internal version label are unchanged or worse. Line 1 still reads
`# MURU v2 — CALIBRATION / RE-ENTRY PROTOCOL, **VERSION 3**`; line 24 still reads `Status at
this commit: PROTOCOL TEXT, VERSION 3`; §30 still addresses *"the v2 pre-freeze review"*; §31.1
still creates tag `muru-freeze/e7-protocol-v2`. The commit message calls this "Protocol v4".
Three different version labels now coexist in one document (`N13`, worsened, not repaired).

**Scope actually reviewed.** `git diff d405cdf 19be068 -- .../MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md`
read in full (854 lines). `scripts/v2_reachability_verifier.py`, `scripts/v2_freeze_dinst.py`,
`scripts/v2_truth_blind_verifier.py`, `src/muru/v2_calibration/e2c_classify.py` read in full and
executed. `git show 19be068` (commit message) checked claim-by-claim against the diff and the
file. HEAD is stable at `7f28b5f` (a one-line DINST-freeze-record regeneration, immaterial to
the protocol text) throughout this review — no mid-review amendment this round (`N15`, n/a).

**This round closes 5 of its 7 v3 defects for real** — `N1`, `N2`, `N3`, `N4`, `N5` are genuine,
verified repairs, and `N6`'s core mechanism (E4f reverts to non-executable) is the honest
repair and is taken correctly in the one section built to carry it (§2.1). **It nonetheless
fails**, for reasons that recur the exact failure mode this document was reviewed for finding
last time — a repair made in one place with a contradicting sentence left standing in another:

1. **`N6` is not closed everywhere.** The AUTHORITY table at the top of §2 — the single most
   consultable reference point in the document for "what authorizes this" — still states as
   fact, four lines above §2.1's own retraction of it: *"Its authority is **the protocol
   owner's maximum-autonomy delegation**, NOT ratification §10."* That is exactly the claim
   `N6` found unsupported by any governance record and that §2.1 spends four paragraphs
   retracting. §0.2, the document's own "what changed" headline for Decision 2, was not
   touched by the `N6` repair at all: it still reads *"Route C+D → E4f family i is now
   PREREGISTERED"* and *"The routing table is updated accordingly (§21.2 row 3)"* with no
   mention that row 3 now means **`ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`**. A reader who
   consults either the authority table or §0.2 — the two places a reader looks first — comes
   away believing E4f executes today. It does not, per §2.1, §21.2 row 3, §22.1 `F16` and §32.
   Same document, two operative answers, prohibition #23's exact shape.
2. **The prose citing §22's rule numbers was not renumbered with the table.** `F0`'s repair
   turned §22.1 into a literal `F1..F17` list — genuinely fixing `N2`'s dead terminals — but
   three cross-references elsewhere in the document still cite the **old** numbers: §21.3 cites
   `SURFACE_DEGENERATE_NO_FRONT` as `(§22 F14)` (now `F9`); §24 cites
   `VOID_INSTRUMENT_INDETERMINATE` as `(§22 F6)` (now `F7`); §31.1 cites a non-empty tuning
   ledger as firing `§22 F7` (it fires `VOID_SINGLE_SHOT_BROKEN`, now `F8`). Three stale
   pointers, recurring the identical disease the renumbering was performed to cure, one level
   down.
3. **The mechanical cross-check the document cites for `N3` doesn't check what it claims to.**
   `scripts/v2_reachability_verifier.py`'s `terminal_set_equality` compares `RULE_TERMINAL`'s
   values against a "§32" set built by literally unioning `RULE_TERMINAL`'s own values with the
   one Stage-0 name — it never reads §32's actual table text, so it is **true by construction**
   regardless of what §32 says. §32's preamble claims *"§31.1's freeze-time verifier … asserts
   mechanically that the set of terminals named here equals the set named by §22"* — that
   mechanism does not exist. (I hand-verified the two tables myself and they **do** match — so
   `N3`'s substance is repaired — but the claimed mechanical guarantee is decorative, and would
   not catch a future edit that broke it.)
4. **`N9`, `N10`, `N12` and half of `N14` — all four MED/LOW defects named in the previous
   review's own "what would make this pass" list — are untouched.** The closing status block
   still reads *"No module written"* while eight modules are committed; no Stage 0 shot ledger
   exists and `S0-5`'s exploit is unchanged; §33 still prints the struck single-clause
   `RETENTION_EXONERATED` predicate and the "dominates" claim §21.3 called mathematically false;
   §0.1's strikethrough is still malformed.
5. **The disclosure-completeness defect recurs a further time, on this round's own new
   executions.** §31.8's *"disclosed exhaustively"* list of what was run during authorship still
   omits `v2_reachability_verifier.py`, `v2_truth_blind_verifier.py`, the `C-1b` 9/9 run and the
   `e2c_classify` regression demos — all of which the commit message cites as executed evidence
   for this very round's repairs.

None of this reopens `N1`/`N2`/`N3`/`N4`/`N5` on their merits — those are real, and I could not
break `G1`/`G4`-class repairs by attacking them directly this round either. It fails because a
repair of this size was again not checked for internal consistency against the rest of the
document, and the one finding that matters most (`N6`, authority) is the one with a surviving
contradiction.

---

# PART 1 — PROHIBITION AUDIT (all 23)

**FAIL = reachable at HEAD `7f28b5f`.** Verified by direct read or execution, not from the
commit message.

| # | Prohibition | v3 | v4 | Evidence |
|---|---|---|---|---|
| 1 | change the already sealed Gate 1 result | PASS | **PASS** | `git log -- audit/e2b_definitive_cloud_adjudication_20260818` unchanged since `906c9d4`; `sha256sum -c ARTIFACT_SHA256.txt` unattempted this round but no commit touches the directory (`git log` confirms) |
| 2 | erase the 4/71/55/14 attribution | PASS | **PASS** | §21.4 still reproduces `pi_0 = (14,55,71,4)/144` verbatim, byte-identical to v3 |
| 3 | make E2b decision-admissible retroactively | PASS | **PASS** | §15 unchanged; the annotation is even more explicitly non-conditioning now (`G6`/`N1`) |
| 4 | use E2b to positively license an E4 arm | **FAIL** | **PASS** | `N1` closed: §0.1 response 1, §21.4's bullet 4, §21.5 item 1 and §32.1's witness-table gloss now all say the annotation "conditions nothing … for any route", once, consistently. Read all four in full; no surviving "retained in full" / "explanation required" text found anywhere (`grep -c "explanation required"` → 0) |
| 5 | restore the old E2a Gate 2 routing as authoritative | PASS | **PASS** | Unchanged |
| 6 | choose a threshold after inspecting the result it governs | **FAIL** | **PASS** | `ADDRESS_SPACE_BYTES` is now `_host_rss_ceiling_bytes()`, a host-derived **formula** evaluated at import time (verified: 23.516 GiB on this 47 GiB host, matching `STAGE1_RESOURCE_PROFILE.json`'s 23.5 and the commit's claimed 23.52), not a literal re-chosen after each failed run. §25.5's three-way-inconsistent constants are deleted and repointed to §25.4 (`N5` closed — verified: `grep RSS_CEILING_GIB` now returns one declaration site). `STAGE1_RESOURCE_PROFILE.json` is committed |
| 7 | silently change denominator | PASS | **PASS** | Unchanged; 230/276 evaluable-safety-opportunity accounting intact |
| 8 | silently drop cases | PASS | **PASS** | Unchanged; three Stage 0 archives still on disk in full |
| 9 | let timeout become classification | PASS | **PASS** | `TIER2_WALL_GUARD = None` still at `scripts/e2a_instrument_diagnostic.py:71`; `assert terminal in DECLARED_TERMINALS` still present; unchanged and re-verified by direct read |
| 10 | hide OOM-killed cases | PASS | **PASS** | Unchanged |
| 11 | fabricate missing provenance fields | **FAIL** | **FAIL** | Delegation citation itself is now honestly stated in §2.1 as "an operator instruction … NOT a governance record" (repaired). But: (a) §31.8's *"disclosed exhaustively"* execution list still omits work performed for **this** round — `v2_reachability_verifier.py`, `v2_truth_blind_verifier.py`, `C-1b` (9/9), the `e2c_classify` regression demos — all cited in the commit message; (b) `S0-3`'s *"Runs 1-3 are quarantined under `_quarantine/`"* is still false — `ls audit/muru_v2_reentry_20260819/_quarantine/` shows only run 3 + the null-run record; runs 1/2 are still in sibling dirs `_ckpt_dinst_ARCHIVED_8GB_BOUND/`, `_ckpt_dinst_ARCHIVED_ENVFAIL/`; (c) the closing status block still says "No module written" against `git ls-files` showing 8+ committed modules (`N9`, unrepaired) |
| 12 | rewrite sealed historical evidence | PASS | **PASS** | Unchanged; same three unmanifested-but-additive files noted in v3 still present, still a discipline breach not a rewrite |
| 13 | call a post-result design "preregistered" | PASS | **PASS** | Unchanged in substance. (The versioning confusion at the very top of the document — see the note at the head of this review — is a related but distinct honesty defect, not this prohibition) |
| 14 | weaken an endpoint because the experiment failed | PASS | **PASS** | Unchanged; family i/ii disposition preserved dormant, correctly labelled, not deleted (see NEW-defects below re: whether it is *findable*) |
| 15 | weaken a safety rule because a candidate failed it | **FAIL** | **PASS** | Direct consequence of `N1`'s closure: Decision 1's justification (§0.1) no longer contradicts §21.5's actual disposition. The obligation's loss is now stated as an accepted, disclosed limitation in the same place that argues for removing it, not silently elsewhere |
| 16 | execute multiple interventions at once without a joint protocol | PASS | **PASS** | Unchanged; `F0` still emits exactly one terminal |
| 17 | claim success merely because the programme reached E6 | PASS | **PASS** | Unchanged, and `E6_SAFETY_HEADROOM_PRESENT` is now correctly stated as a routing-rule gate rather than falsely claimed to live in §20's `QUALIFIED` conjunction (`V3-C5` closed) |
| 18 | change frozen thresholds / classification definitions / case population / denominator | **FAIL** | **PASS** | The +27.8% E4f population-by-reference question is now moot in practice: no route can currently propose an E4f licence (`F16`), so nothing is licensed on the strength of an uncontrolled restatement. §36 is marked `DORMANT` and the restatement remains unwritten but nothing depends on it existing today. This closes the live exploit even though the underlying "different document moves E4f's population" fact is unchanged and will need `N7`'s control the day authority exists |
| 19 | change the historical 69/57 | PASS | **PASS** | Unchanged |
| 20 | relabel after viewing results | **FAIL** | **PASS** | `F16` removes the live consequence of §36 item 3's "a reader concludes" clerical language — there is no `E4F_*` terminal to steer into today, and §36 item 3's text is explicitly re-labelled *"Numbered here as a dormant reference only; section 22's live `F16` is the terminal that fires today"*. The clerical-discretion **wording** survives dormant (worth fixing before this ever reactivates — see `N8` in Part 2) but has no exploitable path now |
| 21 | substitute Linux/x86 symbolic-search output for authoritative Mac fronts | PASS | **PASS** | Unchanged |
| 22 | execute E4a after a definitive Gate 1 FAIL | PASS | **PASS** | Unchanged |
| 23 | invent protocol authority | **FAIL** | **FAIL** | §2.1's retraction of the "maximum-autonomy delegation" is genuine and its replacement (an honest "operator instruction, not a governance record" + reversion to non-executable) is the correct repair. **But the AUTHORITY table four lines above §2.1, in §2 itself, still states the retracted claim as fact**: *"Its authority is the protocol owner's maximum-autonomy delegation, NOT ratification §10 — see the correction below"* (line 402). A table row asserting an authority claim its own document's next section calls unsupported by any governance record is still an invented-authority statement, live in the text |

**Result: 20 PASS, 2 FAIL, 1 unattempted-but-unchanged-so-inherited-PASS** (#1 not re-executed
this round; no commit touched the sealed directory so it is carried forward, not re-verified
independently). **v3 was 16/7; v4 is 20/2** on direct re-check. The two survivors (#11, #23)
are both the disclosure/authority-honesty family, and #23 is the more consequential one: it is
the same finding (`N6`) the executor states was closed "as the most consequential finding" of
the round.

---

# PART 2 — REPAIR VERIFICATION (v3's N1–N15)

| id | v3 severity | verdict | basis |
|---|---|---|---|
| **N1** | CRITICAL | **REPAIRED** | Read §0.1 response 1, §21.4 "binding constraints" bullet 4, §21.5 item 1, and §32.1's witness-table annotation column in full. All four now say the same thing once: the annotation "conditions nothing … for any route"; the `befca0d` §2.3 obligation is explicitly "NOT retained as a precondition"; its loss is recorded as an accepted disclosed limitation. `grep -c "retained in full"` and `grep -c "explanation required"` both return 0 |
| **N2** | CRITICAL | **REPAIRED** | `F9` (`SURFACE_DEGENERATE_NO_FRONT`) is now evaluated before any Gate R row is consulted — verified by direct read of §22.1 and by executing `scripts/v2_reachability_verifier.py`, which finds witness `(138,0,0,0)` for `F9` (hand-verified: `piA=1.0`, `S_1=0`, correctly degenerate, not mis-routed to a Gate R row). The old `F12a` no longer exists as a concept to be unreachable — route `C+D` now assigns `F16` unconditionally, which the search confirms reachable with witness `(0,0,10,128)` |
| **N3** | CRITICAL | **REPAIRED (substance), OVERSTATED (mechanism)** | Hand-compared §22.1's 17 `F1..F17` terminal names against §32's table row by row: they match exactly, plus the one Stage-0 name (`T-INSTRUMENT-UNBOUNDED-ON-E2A`), 18 total both places. `N3`'s substantive defect is gone. **But** the "mechanical" verifier the document cites for this (`v2_reachability_verifier.py`'s `terminal_set_equality`) builds its "§32" comparison set directly from the same dict used for "§22", so it cannot fail regardless of what §32 actually says — see NEW-B below |
| **N4** | HIGH | **REPAIRED** | Ran `scripts/v2_freeze_dinst.py`; it wrote `DINST_FREEZE_CURRENT.txt` with tool hash `b086fad7…`, which matches `sha256sum scripts/e2a_instrument_diagnostic.py` exactly. §31.8 names this file, and only this file, as authoritative, and explicitly declares the three earlier `DINST_FREEZE_SHA256*` files non-binding audit trail. Re-ran the script a second time: output byte-identical except the `generated_from_commit` line, confirming the claimed idempotency |
| **N5** | HIGH | **REPAIRED** | §25.5's old `24 GiB`/`WORKER_COUNT=8` constants are deleted and repointed to §25.4's per-phase table and the now-committed `STAGE1_RESOURCE_PROFILE.json`. `FP-3`/`FP-4` in §34 now say "see §25.4/§25.5" instead of citing the deleted numbers alone |
| **N6** | HIGH | **PARTIALLY REPAIRED — the core mechanism is right, but not everywhere** | §2.1 itself is an honest, complete repair: it states the delegation is unrecorded, takes `N6`'s own minimal-repair text verbatim, and reverts route `C+D` to `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`. §21.2 row 3, §22.1 `F16`, §32's `F16` row, §32.3's reinstatement row, and §35's predictions all correctly reflect the reversal. **But** §2's AUTHORITY table (line 402) still asserts the retracted claim as fact, and §0.2 — the document's own "what changed" summary for Decision 2 — was not touched at all and still describes Decision 2 without any mention of the reversal. See prohibition #23 and NEW-A |
| **N7** | HIGH | **MOOT / EFFECTIVELY CLOSED** | `MURU_V2_E4F_POPULATION_RESTATEMENT.md` still does not exist, but nothing in the current disposition depends on it: `F16` fires unconditionally on route `C+D`, so there is no licence for an unwritten, unhashed restatement to improperly condition. §36 is explicitly marked `DORMANT` for exactly this reason. The control gap `N7` identified will need closing the day a ratification record exists and `F16` is retired, but it is not live today |
| **N8** | MED | **MOOT / DORMANT** | §36 item 3's "if a reader concludes … the reference is broken" clerical-judgement language is unchanged, but it is explicitly re-scoped as dormant prose with no live terminal to steer into (`F16` fires regardless). Not exploitable today; still worth a mechanical predicate before this section is ever reactivated |
| **N9** | MED | **NOT REPAIRED** | Line 2944, the document's own closing status block, still reads *"No module written"*. `git ls-files` shows at minimum `calibration_surface.py`, `calibration_seed_band.py`, `e2c_search.py`, `e2c_classify.py`, `v2_stage1_calibration_run.py`, `v2_stage1_scoring.py`, `v2_reachability_verifier.py`, `v2_truth_blind_verifier.py`, `v2_freeze_dinst.py` committed — nine modules/scripts, not zero. The exact sentence `G2` convicted in v2, repeated in v3, survives unchanged into v4 |
| **N10** | MED | **NOT REPAIRED** | `S0-1..S0-5` (§0.7) are byte-identical to v3. No `STAGE0_SHOT_LEDGER` or equivalent artifact exists anywhere in the repository (`find . -iname "*SHOT_LEDGER*"` → nothing). `S0-5`'s exemption is exploitable exactly as described in the prior review |
| **N11** | MED | **REPAIRED** | One name, `E4A_ENTRY_LICENCE_PROPOSED`, used consistently at §22.1 `F12`, §32's row, §32.1's witness table, and §35 — verified by grep, zero occurrences of the old `E4A_LICENCE_PROPOSED_AT_<arm>` or bare `E4A_LICENCE_PROPOSED` forms |
| **N12** | MED | **NOT REPAIRED** | §33's threshold inventory (line 2744) still prints the struck single-clause predicate `RETENTION_EXONERATED := pi_B < delta` and still asserts *"the absolute form dominates the frozen ratio form and needs no second threshold"* — the exact claim §21.3 calls mathematically false and replaces with the three-clause conjunction. Untouched since v3 |
| **N13** | LOW | **NOT REPAIRED, WORSENED** | See the note at the top of this review: the document now carries three simultaneous version identities (header "VERSION 3", §30/freeze-tag "v2", commit message "v4") instead of two |
| **N14** | LOW | **PARTIALLY REPAIRED** | The defect-count arithmetic issue does not recur (no new mismatched count claim found in v4's commit message or text). The malformed strikethrough at line 92-93 is unchanged: `~~The impasse is robust … the~~` / `repair.**` on the next line — "repair." still outside the strike, "**" still an orphaned bold marker |
| **N15** | MED | **N/A this round** | HEAD is stable at `7f28b5f` (an immaterial one-line DINST-record regeneration) for the duration of this review; no mid-review amendment occurred |

**Genuinely repaired: 5 of 15** (`N1`, `N2`, `N4`, `N5`, `N11`).
**Moot / effectively closed given the current disposition: 2** (`N7`, `N8`).
**Partially repaired / overstated: 2** (`N3` — substance repaired, claimed mechanism weak;
`N6` — core mechanism repaired, not carried to every operative section).
**Not repaired: 5** (`N9`, `N10`, `N12`, `N13`, and half of `N14`).
**Not applicable this round: 1** (`N15`).

---

# PART 3 — NEW DEFECTS (v4)

## NEW-A — HIGH. `N6`'s repair does not reach the AUTHORITY table or §0.2, so the document asserts two different answers about whether E4f executes today.

**Location.** §2 AUTHORITY table, row for `MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` (line
402); §0.2 (lines 157–184).

**What is wrong.** §2.1, four lines below, retracts this exact claim and states the delegation
is unrecorded. The table row was not updated when §2.1 was rewritten:

> "`MURU_V2_E4F_OPERATIONAL_PREREGISTRATION.md` @ `8a2ffa50` | the operational freeze for the
> `C+D` route. **Its authority is the protocol owner's maximum-autonomy delegation, NOT
> ratification §10 — see the correction below**"

§0.2's heading and body are untouched by the `N6` repair entirely: *"Route C+D → E4f family i
is now PREREGISTERED"*, *"The routing table is updated accordingly (§21.2 row 3)"* — with no
statement that row 3 now means non-executable. A reader who reads §0.2 (the document's own
"what changed, read this first" section) or the AUTHORITY table (the document's own "what
authorizes this" reference) without also reading all of §2.1 comes away with the belief this
protocol itself spends four paragraphs disproving.

**Exploit scenario.** This is `N1`'s exact shape, recurring on `N6` instead: two operative
statements about the same fact, one correct and one stale, and an owner or downstream reader
picks whichever they reach first. It is also prohibition #23's exact shape — the AUTHORITY
table's sentence is, verbatim, an assertion of protocol authority that the very next section
finds unsupported by any governance record.

**Minimal repair.** Rewrite the AUTHORITY table row to state the operator-instruction/
non-executable disposition directly, or replace it with "see §2.1" and no independent claim.
Add one sentence to §0.2 (or a forward-pointer to §2.1/`N6`) stating that Decision 2's row-3
disposition is currently `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`, not "preregistered and live".

---

## NEW-B — MEDIUM. The freeze-time terminal-set-equality "verifier" is tautological and cannot detect the defect it is cited to prevent.

**Location.** `scripts/v2_reachability_verifier.py` lines 55–60; §32's preamble (claims
"asserts mechanically that the set of terminals named here equals the set named by §22").

**What is wrong.**

```python
SECTION_32_TERMINALS = {
    "T-INSTRUMENT-UNBOUNDED-ON-E2A",
    *RULE_TERMINAL.values(),
}
```

This does not parse §32's markdown table; it constructs the "§32 side" of the comparison
directly from `RULE_TERMINAL` — the same dictionary that constitutes the "§22 side"
(`f_terms = set(RULE_TERMINAL.values())`). `missing_from_32` and `extra_in_32` are therefore
empty by construction on every run, regardless of what §32's actual text says. If a future edit
dropped a row from §32 or renamed one, this check would still print `"passed": true`.

I independently hand-verified the real terminal sets (§22.1's 17 rules' terminal names vs
§32's 18 rows) and they do match at this commit — so `N3`'s underlying defect is genuinely
repaired — but the document's claim that this is checked "mechanically" at freeze time is false
for this specific half of the script. It is real and correct only for the reachability-witness
half.

**Exploit scenario.** An executor edits §32 in a later round (e.g. to add a terminal, or to fix
a gloss) and typos or drops a name. `v2_reachability_verifier.py` still reports `PASSED`,
because it was never actually reading §32. The freeze-time gate this document says exists does
not exist for this claim.

**Minimal repair.** Have the script parse `MURU_V2_CALIBRATION_REENTRY_PROTOCOL_V3.md`'s §32
table (a simple markdown-table regex over the `Terminal` column) and compare that extracted set
against `RULE_TERMINAL.values()`, instead of hand-constructing both sides from the same source.

---

## NEW-C — MEDIUM. Three stale numeric §22-rule cross-references survive the `F0` renumbering, recurring the exact disease the renumbering was performed to fix.

**Location.** §21.3, line 1759: *"routed to `SURFACE_DEGENERATE_NO_FRONT` (§22 F14)"* — current
`SURFACE_DEGENERATE_NO_FRONT` is `F9`; `F14` is now `E4_GENERATION_LICENCE_PROPOSED_F09_F10`, a
different terminal entirely. §24, line 2115: *"`INDETERMINATE_WORLDS > 0` ⟹
`VOID_INSTRUMENT_INDETERMINATE` (§22 F6)"* — current `VOID_INSTRUMENT_INDETERMINATE` is `F7`;
`F6` is now `VOID_CONTROL_FAILURE`. §31.1 item 2, line 2517: *"A non-empty ledger fires §22
F7"* — a non-empty tuning ledger fires `VOID_SINGLE_SHOT_BROKEN`, now `F8`; `F7` is
`VOID_INSTRUMENT_INDETERMINATE`.

**What is wrong.** The `F0` repair (closing `N2`) renumbered §22.1's rules from the v3 ordering
to a new `F1..F17` literal sequence, and §32's table was rewritten to match. The prose
elsewhere in the document that cites rule numbers **by number** rather than by terminal name
was not swept for the renumbering. All three citations above point at the wrong rule under the
new numbering, and two of them (F6, F7) now point at a *different, wrong terminal* rather than
merely an off-by-one.

**Exploit scenario.** Low-severity for routing itself — actual routing is governed by the
canonical §22.1/§32 tables, which are correct, not by these prose asides. But a reader
fact-checking §21.3's or §24's specific rule citation against §22.1 finds a contradiction, and a
future editor "fixing" §22.1 again has three more places quietly out of sync than the freeze
checklist accounts for.

**Minimal repair.** Grep the document for `§22 F` and `(F\d+)` cross-references and correct all
three; add a freeze-time check that every numeric `§22 F<n>` citation in the prose resolves to
the terminal actually named at that citation, alongside the terminal-name check `NEW-B`
requests.

---

## NEW-D — MEDIUM/HIGH. `§31.8`'s "disclosed exhaustively" execution list is false at HEAD for a further, different set of executions — the fourth recurrence of this exact defect class.

**Location.** §31.8, "Executions performed during the authorship of this document, disclosed
exhaustively" (lines ~2554–2559).

**What is wrong.** The list still reads: `C-0` (380/380), a `PBC` case-generation smoke test,
seed-band enumeration, `pb_33`/`pb_34`, §10/§10.5/§21.4's Monte-Carlo arithmetic, and read-only
`git show`s. It does **not** mention `scripts/v2_reachability_verifier.py`'s run (which the
commit message cites: "EXECUTED … PASSED"), `scripts/v2_truth_blind_verifier.py`'s run ("0
call-graph violations over 16 modules" — independently reproduced, see Part 4), the `C-1b`
search-equivalence run ("9 compared, 0 mismatched"), or the `e2c_classify.canonicalise` bug-fix
regression demos ("Demo 1 … now UNRESOLVED", "Demo 2 … bounded at ~1.0s"). All four are
executions that happened during the authorship of this document and materially inform its
claims.

**Exploit scenario.** This is the same defect the prior review filed as part of `N6`(b) against
a different set of omissions (12 PySR searches, the `C-1b` run of that round, the preflight
run) — the list was "corrected" by omission of the new items rather than by becoming genuinely
exhaustive, for the third documented round in a row.

**Minimal repair.** Generate this list programmatically from the shell history / test-run log
rather than re-typing it by hand each round, or at minimum add the four items above before this
document is next read as evidence of its own completeness.

---

## NEW-E — LOW. Two markdown table corruptions from the edit.

**Location.** §22.1, immediately before the `F0` row: the table header (`| # | Condition |
Terminal |` / `|---|---|---|`) is printed **twice** in a row before any data row. §32.3, at the
very end of its table: the `T9 — REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY` row is printed twice,
the second copy sitting outside the table (a blank line separates it from the table above),
rendering as a stray paragraph rather than a table row.

**Exploit scenario.** None scientific; a rendering/proofreading defect only, but it is the kind
of leftover a copy-edit pass before freeze is supposed to catch, and two instances in one
editing round suggests the diffs were not re-rendered before commit.

**Minimal repair.** Delete the duplicate header line in §22.1 and the duplicate `T9` row in
§32.3.

---

## NEW-F — LOW. Document version identity is now three-way inconsistent (worse than v3's `N13`).

**Location.** Line 1 (title: "VERSION 3"); line 24 (status line: "VERSION 3"); §30 body ("the
v2 pre-freeze review"); §31.1 (`muru-freeze/e7-protocol-v2` tag); commit `19be068`'s subject
("Protocol v4").

**What is wrong.** v3's review already flagged the title/tag/§30 as stale "v2" references
against a file actually named and numbered `PROTOCOL_V3`. v4 adds a **third** label without
resolving either of the first two: the content is now what the commit calls "v4", the file is
still named and headed "VERSION 3", and the internal cross-references still say "v2". No single
version number appears in more than one of these four places.

**Minimal repair.** Pick the filename/header as the source of truth (rename the file and update
line 1/24 to "VERSION 4" if that is the intended identity, or explicitly declare in one place —
e.g. a new §0.0 — the mapping between "this file's header", "this file's internal §30/tag
references", and "what the commit history calls this round", so a reader is never left to guess
which of three numbers is current.

---

# PART 4 — SPOT-CHECKS PERFORMED (execution log)

For the record, so these are checkable independently of this review's prose:

```
$ python3 scripts/v2_reachability_verifier.py       -> PASSED (terminal_set_equality: True,
                                                         all_arithmetic_rules_reachable: True)
$ python3 scripts/v2_truth_blind_verifier.py         -> P8a_PASSED: true, violations: [],
                                                         n_modules_scanned: 16
$ python3 scripts/v2_freeze_dinst.py                 -> tool_hash = b086fad7923442721588f...
$ sha256sum scripts/e2a_instrument_diagnostic.py     -> b086fad7923442721588f...  MATCH
$ python3 -c "... m.ADDRESS_SPACE_BYTES/1024**3"     -> 23.516073...  (host has 47 GiB, matches
                                                         STAGE1_RESOURCE_PROFILE.json's 23.5
                                                         and the commit's claimed 23.52)
```

Hand-verified witnesses against the document's own formulas (`delta = 10/144 = 0.0694444`,
`Z = 1.959964`, `N = 1656`):

- `F9` witness `(138, 0, 0, 0)`: `pi_A = 138/138 = 1.0`, `S_1 = 1 - pi_A = 0` — correctly
  degenerate, correctly excluded from Gate R before any row is read.
- `W-EX` witness `(0, 0, 5, 133)` for `F11`: `pi_CD = 5/138 = 0.036232`, `lead = 0.036232`,
  `lead/delta = 0.522` (document: 0.522, matches); `sigma = sqrt((0.036232 - 0.036232^2)/1656)
  = 0.0045932`; `LCB = 0.036232 - 1.959964*0.0045932 = 0.027230` (document: `+0.027232`,
  matches to rounding); `S_1 = 1`, `S_2/S_1 = 1.0 >= 1-delta` — exoneration conjunction
  satisfied by construction. Matches the script's independent computation exactly.
- `W-CD` witness `(14, 45, 74, 5)` for `F16`: `lead = 0.536232 - 0.326087 = 0.210145`,
  `lead/delta = 3.026` (document: 3.026, matches); `sigma = sqrt((0.862319 -
  0.044161)/1656) = 0.022227`; `LCB = 0.210145 - 1.959964*0.022227 = 0.166581` (document:
  `+0.166580`, matches to rounding).

All three independently reproduce the document's printed values.

---

# PART 5 — COMMIT MESSAGE HONESTY (19be068)

Six claims spot-checked directly against the diff and the file:

| claim | verdict | basis |
|---|---|---|
| "ratification section 4 (D2-ext)'s suspension of ALL E4 arms now governs without exception" | **TRUE** | §2.1 body; `MURU_V2_PROTOCOL_OWNER_RATIFICATION.md` §4 read directly, confirms "All E4 arms (E4a–E4f) remain suspended" |
| "Route C+D certifies but proposes nothing (F16 = ROUTE_DETERMINED_ARM_NOT_EXECUTABLE)" | **TRUE** | §22.1 F16, §32's F16 row, reachability verifier witness |
| "This closes N1 … as a side effect" | **TRUE narrowly, OVERSTATED broadly** | True for the four sections `N1` named. But `N6` itself — the finding this closure is *attributed to* — is not closed everywhere (NEW-A), so the framing "both critics' CRITICALs closed" overstates by omitting the AUTHORITY-table/§0.2 residue |
| "every one of F9-F16 has a witness … terminal-set equality between section 22 and section 32 holds. PASSED" | **Witness claim TRUE; equality-via-execution claim OVERSTATED** | Witnesses genuinely found by search (reproduced independently). Terminal-set equality is true **in the document** (hand-verified) but the script does not actually check it against the document (NEW-B) |
| "scripts/v2_freeze_dinst.py computes the tool hash … from the LIVE file … the only file this protocol now treats as authoritative" | **TRUE** | Ran it; hash matches `sha256sum`; §31.8 states this in terms |
| "P8a … 7 violations, executed … Replaced with a CALL-GRAPH ban … EXECUTED: 0 violations" | **TRUE** | Ran `v2_truth_blind_verifier.py`: 0 violations, 16 modules, matches |
| "_host_rss_ceiling_bytes() … Verified: 23.52 GiB on this 47 GiB host" | **TRUE** | Reproduced: 23.516 GiB |
| "~14% licensing mass, down from v3's ~37%" | **TRUE** | §35: `E4A_ENTRY_LICENCE_PROPOSED` ~10% + `E4_GENERATION_LICENCE_PROPOSED_F09_F10` ~4% = 14%, both correctly the only "Licenses? Yes" rows in §32 |

Six of eight checked claims are straightforwardly true and independently reproduced; two are
overstated in the specific way this review's Part 3 documents (NEW-A, NEW-B) — both instances
of a genuine repair's scope being described as broader than what the diff actually touched.

---

# PART 6 — WHAT WOULD MAKE THIS PASS

1. **NEW-A** — rewrite the §2 AUTHORITY table row for E4f and add one sentence to §0.2
   reflecting `F16`/non-executability. This is the highest-priority item: it is the same
   finding (`N6`) the commit calls the round's most consequential, with a surviving
   contradiction in the two places a reader looks first.
2. **NEW-C** — sweep the three stale `§22 F<n>` numeric citations (§21.3, §24, §31.1) to match
   the current table, and add a mechanical check for this class of drift.
3. **NEW-B** — make the terminal-set-equality check actually parse §32, instead of comparing a
   dictionary to itself.
4. **N9, N12, N14(ii)** — three one-sentence fixes: the closing status block, §33's stale
   `RETENTION_EXONERATED` row, the malformed strikethrough.
5. **N10** — a committed Stage 0 shot ledger, as the prior review specified.
6. **NEW-D** — regenerate §31.8's execution-disclosure list from this round's actual shell
   history rather than hand-transcribing it again.
7. **NEW-F, N13** — pick one version identity and make the title, status line, §30, and the
   freeze tag agree.
8. **NEW-E** — delete the two duplicated table fragments.

None of these require new science, a new decision, or touching a sealed or frozen byte. All are
text and one script edit.

**On the record, in v4's favour.** `N1`, `N2`, `N4`, `N5`, `N11` are genuine, verified,
executed repairs — not argued text. `N6`'s core mechanism is the correct and honestly-graded
repair, taken directly from the prior review's own minimal-repair text rather than invented
anew. The two real code bugs (`e2c_classify`'s unbudgeted second `simplify` call, the
hardcoded-vs-declared `ADDRESS_SPACE_BYTES` mismatch) are fixed in code I read and partially
re-executed, not merely described. The licensing-mass restatement (~37% → ~14%) is a
correction against the author's own interest, stated plainly. The failure here is exactly the
same shape as v3's: real, substantial repair work, undermined by not sweeping the rest of the
~2,950-line document for the sentences that repair should have also touched.
