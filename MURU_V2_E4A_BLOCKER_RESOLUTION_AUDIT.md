# MURU V2 E4a Blocker-Resolution Audit (results-blind)

Companion to `MURU_V2_E4A_CONDITION_3B_GOVERNANCE_AUDIT.md`. Resolves the
remaining documentary and implementation questions blocking E4a, from frozen
sources only.

**Nothing scientific was executed.** No E4a, no M2/M3, no E6, no poison world,
no search of any kind. The only computation performed was: reading `world_id`
strings and JSON *key names* out of persisted corpora, and calling the frozen
retention functions on **hand-built synthetic rows** (a control check, the same
device `tests/test_e4a_scoring_controls.py` uses). No A/B/C/D/E stage, rate,
score value, or per-cell figure was read from any corpus.

---

## TASK A — Recovery of the authoritative preregistration

```
AUTHORITATIVE_SOURCE_NOT_RECOVERABLE
```

`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` (cited authority commit
`f4c1105`) is not present in, and not recoverable from, anything reachable from
this host. Search performed, each avenue exhausted:

| Avenue | Method | Result |
|---|---|---|
| All git objects | `git rev-list --all --objects \| grep -i RETENTION_REMEDIATION` | 0 hits |
| Named authority commit | `git cat-file -t f4c1105` | "Not a valid object name" |
| Design-pack source commits | `git cat-file -t befca0d` / `4bfd4a8` (from `v2_design_reference/DESIGN_PROVENANCE.md:3-7`) | both invalid object names |
| Theory commit cited by the amendment | `git cat-file -t 3c5bbab` (`AMENDMENT_V1.md:159`) | invalid object name |
| Historical commits that *do* exist | `git ls-tree -r` on `c4e75d0`, `dc66e27`, `4892c76`, `8d87143` | present, none contains the file |
| Tags | `git tag` | none exist |
| Stash / dangling objects | `git stash list`; `git fsck --lost-found` | empty; no dangling objects |
| Local worktrees | `git worktree list` | one worktree (this checkout) |
| Provenance-named worktree | `.claude/worktrees/e2-rescue-v2-computational` (`ROUTING_LOCK_FREEZE.md:29`) | path absent on this host |
| Provenance-named checkpoints | `/tmp/e2_rescue_v2_checkpoint_TRULY_FINAL_20260817_165554`, `/tmp/e2_rescue_v2_production_out`, `/tmp/e2_rescue_v2_smoke_output` (`ROUTING_LOCK_FREEZE.md:33`) | all absent |
| Remote branches | `git ls-remote --heads --tags origin` | exactly 3 heads, 0 tags, all already fetched; none contains it |
| Other GitHub repositories | `gh repo list`; full recursive tree of `aryavthakur/muru-conjecturelab` (17,592 paths) | no matching path |
| Whole filesystem | `find / -xdev -name "*RETENTION_REMEDIATION*"` | 0 hits |
| Archives | search for `*.tar*`, `*.zip`, `*.gz` in-repo | none |
| Cited memories | `muru-v2-retention-decision-theory`, `muru-v2-master-reconciliation`, `muru-v2-recoverability-ceiling` | memory directories are empty |
| Recorded digest | search every `*.json`/`*.md` for a sha256 keyed to this filename | **none exists** |

Three consequences, stated plainly:

1. **No text was reconstructed.** The only occurrences on this filesystem are
   secondary quotations inside repository documents (`ROUTING_LOCK_THEORY.md`
   §1, `E4A_RESULTS_BLIND_AMENDMENT_V1.md`, `E4A_PREREQUISITE_VERIFICATION.md`,
   `routing_lock.py`), session transcripts, and this task's own paste-cache
   entry. Per the audit's terms, none was used as a recovery source.
2. **Even a recovered copy could not be provenance-verified.** No sha256, blob
   hash, or size for this file is recorded anywhere in the repository — unlike
   `PHASE3_PREREGISTRATION.md` and `TYPE2_VALIDATION_PREREGISTRATION.md`, which
   do have recorded digests (`artifacts/ov_prereg_hash.json:6,9`), and unlike
   the ten design-pack files, which have recorded blob sha1s
   (`DESIGN_PROVENANCE.md:9-23`). Verification is impossible in principle, not
   merely unavailable.
3. **The most plausible location is the unreachable macOS/arm64 machine.** The
   provenance chain names `/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/
   worktrees/...` (`E2B_ORIGINAL_ENV_RECONCILIATION.json`,
   `required_environment_from_sealed_manifest.sealed_evidence_root_original`),
   the same host the E2b original-environment replay was just unable to reach.
   Recovery is therefore an operator action on that machine, not a search
   problem on this one.

**Nothing was persisted for Task A**, because nothing authoritative was found.

---

## TASK B — R2/R6 status

```
R2_R6_MANDATORY_BUT_UNSCOREABLE
```

### B.1 What the surviving *primary* frozen source says about the arm set

The authoritative preregistration is gone (Task A), so arm status is read from
the design pack, whose fidelity *is* verifiable (blob sha1s in
`DESIGN_PROVENANCE.md`, re-checked by `scripts/verify_e0_design_fidelity.py`).

`v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json:662-672` defines
E4a's independent variable and its levels verbatim:

```
"independent_variable": {"factor": "retention policy", "levels_key": "levels"},
"levels": {
  "R0": "argmax(score) (control, frozen v1)",
  "R1": "argmax(valid_r2)",
  "R2": "top-k by score, k in {1,2,3,5}",
  "R3": "whole front, seed votes for its best member by valid_r2",
  "R4": "accuracy-thresholded parsimony: lowest complexity among rows within
         eps of max valid_r2, eps in {0.001, 0.005, 0.02}"
}
```

- **R2 is a declared level of E4a's independent variable** — not a diagnostic,
  not optional. The same arm set appears in
  `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md:311` and
  `MURU_V2_CAUSAL_DECISION_TREE.md:214`. The frozen decision criterion ("adopt
  the simplest arm clearing both the improvement and the E6 ceiling",
  plan JSON `decision_criterion`; tree §B.2) ranges over the levels, so
  omitting one changes what "simplest such arm" means. R2 is **mandatory**.
- **R5 and R6 do not appear in any primary frozen source.** The design pack and
  the causal tree both stop at R4. R6 exists only in the Step-4 implementation
  (`e4a_scoring.py:228-246`), which attributes its two constants to
  "section 5.2" of the missing preregistration. **R6's arm status cannot be
  established from any surviving authoritative source** — it is neither
  confirmable as mandatory nor dismissable as optional. Treating it as
  droppable would be inventing a governance fact; this audit does not.
- Only one arm carries a frozen exemption, and it is not R2 or R6: R3 is
  "Oracle/control. Not adoption-eligible (section 5.1)" (`e4a_scoring.py:190`).
  The absence of any comparable clause for R2/R6 is itself evidence.

### B.2 The exact source field and data dependency

| Link in the chain | Artifact | Status |
|---|---|---|
| Definition | "top-**k by score**" (R2), "top-3 **by score**" + template recurrence (R6, `e4a_scoring.py:228-232`) | ranking key is PySR's native `score` column |
| Production access path | `rc5_selection.select_row_label` → `equations["score"].idxmax()` on PySR's `equations_` frame | frozen, unchanged |
| Old exhaustive persistence | `e2_search.FrontRow.score` (`e2_search.py:72`), written from `float(equations["score"].iloc[position])` (`e2_search.py:181`) | **carries `score`** |
| Rescue-v2 persistence | `lazy_classify.RawFrontRow` (`lazy_classify.py:123-135`) — 9 fields, no `score`, **no `loss`**, no `train_r2` | **does not carry `score`** |
| The sealed x86 corpus | `results/e2/run_x86_e2a_v1/candidates_shard_*.jsonl`, verified by key names: `retained_by_argmax_score` present, `score` absent, `loss` absent | Rescue-v2 schema |
| Guard | `_require_score` raises `InsufficientRowData` (`e4a_scoring.py:122-128`), called by R0/R2/R6 at lines 164, 183, 238 | never substitutes or guesses |

Two closures follow mechanically:

- `score` **cannot be recomputed** from what the sealed corpus persists. PySR's
  `score` is derived from `loss` along the front, and `loss` is not persisted by
  the Rescue-v2 schema. Recovering it requires re-running the searches — new
  scientific compute — and reconstructing it post hoc is forbidden by this
  audit's own terms.
- The **frozen alternative source exists but is inadmissible.** The ARM-era
  corpus at `results/e2/run/` (tracked, read-only, 18 files) does carry `score`
  and `loss` — but it covers **279** of 540 worlds, and it is the corpus
  governance option 1 discarded: `X86_E2A_SEAL.json:4-5` records
  `corpus_is_x86_only: true`, `historical_worlds_merged: false`, and
  `X86_E2A_FREEZE.json:196-201` records that no historical world is imported.
  Joining its `score` column onto x86 rows would manufacture exactly the
  cross-host hybrid that `CLOUD_X86_PARITY_QUALIFICATION.md` (PARITY_FAILED)
  exists to prevent. So: not `R2_R6_SCOREABLE_FROM_FROZEN_SOURCE`.

### B.3 Two findings strictly larger than the reported defect

1. **R0 — the control arm — is also unscoreable, and the module docstring is
   wrong about it.** `e4a_scoring.py:38-42` states "R0 needs only the boolean
   flag (already present) and is unaffected." But `E4aRow` has no
   `retained_by_argmax_score` field at all, and `retain_r0` calls
   `_require_score(rows, "R0")` (`e4a_scoring.py:164`). Verified on synthetic
   rows with `score=None`: **R0, R2, R6 raise `InsufficientRowData`; R1, R3,
   R4, R5 do not.** Since every adoption decision is defined against R0
   ("no arm beats R0 → NO CHANGE LICENSED", tree §B.2; plan JSON
   `outcome_support.none_beats_R0`), the defect blocks the comparison itself,
   not merely two arms.
   *Recoverable in principle:* the argmax-by-score winner survives as the
   persisted boolean `retained_by_argmax_score`, computed at search time by the
   same frozen `select_row_label` (`raw_search.py:97-98,137`), and production's
   own `e2_aggregate.evaluate_world:71` selects the retained row from exactly
   that flag. Rewiring `retain_r0` to the flag would therefore reuse a frozen
   precedent rather than invent one — **but it edits a Step-4 artifact sealed
   under condition 5, so it is an authorization question, not an autonomous
   edit.** Ranks 2..k, which R2 and R6 need, are *not* recoverable from a
   rank-1 flag.
2. **Condition 5's only real-corpus control silently self-skips on the corpus
   that matters.** `tests/test_e4a_scoring_controls.py:206-243` (test 1, "R0
   reproduces frozen production retention exactly (real replay)") reads
   `OLD_RUN_DIR`, which resolves to
   `/home/worktrees/exp-v2-e2-pareto-observability/results/e2/run` on this host
   — a path that does not exist — and then `check(... SKIPPED ..., True)`. It
   also skips, again as a pass, when rows lack `score` (line 239-241). So the
   "81/81 passing" recorded for condition 5 includes a replay control with
   **zero coverage against the authoritative x86 corpus**. Reported, not fixed.

### B.4 A second casualty of the missing preregistration

`retain_r2(rows, k)` and `retain_r4(rows, eps)` take their parameters from the
caller with **no default and no frozen constant in the implementation** — unlike
R6, whose 3 and 2 are hard-coded with a citation to section 5.2. The design pack
does supply grids (`k in {1,2,3,5}`, `eps in {0.001, 0.005, 0.02}`), but which
value the preregistration fixed — or whether it registered the whole grid as
sub-arms — is recorded only in the missing document. This is a separate
open question from the `score` gap and cannot be closed by finding score data.

---

## TASK C — The only frozen-compliant routes to a 540th front

| # | Route | Status |
|---|---|---|
| 1 | Same-host retry | **EXPLICITLY_DISALLOWED** |
| 2 | Same-instance hardware expansion | **NOT_DEFINED** |
| 3 | Cross-host qualified execution | **REQUIRES_NEW_GOVERNANCE** |
| 4 | Formal missingness / quarantine rule | **EXPLICITLY_DISALLOWED** |
| 5 | Protocol-owner amendment / ratification | **REQUIRES_NEW_GOVERNANCE** |
| 6 | *(found during this audit)* Import the existing ARM-era front for this same world | **EXPLICITLY_DISALLOWED** |

**1. Same-host retry — EXPLICITLY_DISALLOWED.** The frozen procedure's own
terminal branch has already fired: "If it repeatedly fails even in a clean,
uncontended, isolated environment, **stop retrying entirely** and produce a
dedicated execution diagnosis" (`PENDING_EXECUTION_DIAGNOSIS.md:27`). Three
isolated, alone-on-host attempts failed (`POISON_WORLD_DETERMINATION.json:23-30`)
and the diagnosis exists. The frozen resource threshold in
`E2_EXECUTION_DEVIATION.md` §14 points the same way. Tuning the run to make it
fit is separately foreclosed: no memory cap may be imposed ("the frozen protocol
declares no memory budget, so imposing one would be a per-world scientific
definition change") and the determination's own corollary records that fewer
workers "would NOT have prevented the original failure, only delayed it"
(`RESUME_ENGINEERING_DECISION.json`, `POISON_WORLD_DETERMINATION.json:36`).

**2. Same-instance hardware expansion — NOT_DEFINED.** No frozen text addresses
enlarging this instance's RAM. Two frozen constraints bound the space without
resolving it: swap was explicitly refused on the ground that "an infrastructure
change must not perturb the wall-clock the frozen protocol measures against"
(`RESUME_ENGINEERING_DECISION.json`, `remediation_3_no_swap`), and
`X86_E2A_FREEZE.json:10-21` pins `host_identity` including `ram_total_gib: 47`
and the exact CPU model. A resize that changes CPU model or memory-subsystem
speed falls under route 3's host-change rule; a pure RAM increase preserving CPU
identity is addressed by nothing. Because the resulting machine would no longer
match the recorded frozen `host_identity`, acting on this route needs owner
ratification even though no rule forbids it.

**3. Cross-host qualified execution — REQUIRES_NEW_GOVERNANCE.** A frozen
procedure does exist: replay already-completed worlds on the new host and
"confirm exact scientific parity before trusting any output from that
environment", merging only after that check and a world_id-uniqueness check
(`PENDING_EXECUTION_DIAGNOSIS.md:27`), at the tightened standard "PARITY_PASS
requires 100% agreement on **every** replayable completed world"
(`MURU_V2_E2_RESCUE_V2_HOSTILE_REVIEW.md:70-78`). What is *not* frozen is its
application to the current corpus: the procedure's merge target is
`results/e2/run/`, superseded by governance option 1; `X86_E2A_SEAL.json:4-5`
declares the authoritative corpus x86-only with no historical worlds merged; and
the one execution of this procedure across hosts returned
`NEW_CLOUD_HOST_PARITY_FAILED`, root-caused to a wall-clock classification
boundary that is host-dependent on "*any* change of machine"
(`CLOUD_X86_PARITY_QUALIFICATION.md:52-67,78-95,143-150`). Admitting a second
host into an x86-only sealed corpus is precisely the decision that document
places outside autonomous authority.

**4. Formal missingness / quarantine rule — EXPLICITLY_DISALLOWED.** No such
rule is frozen, and each operation one would authorise is foreclosed by name:
"NOT omitted from the population", "No substitute seed, replicate, or world was
generated in its place. There is no scientific workaround", "not scientifically
classified as failed" (`PENDING_EXECUTION_DIAGNOSIS.md:3,20-23`), and "No
scientific analysis proceeds on a corpus that omits it as though it were absent
by design" (line 29). Creating such a rule is route 5, not route 4.

**5. Protocol-owner amendment / ratification — REQUIRES_NEW_GOVERNANCE.** The
only open path, and the repository's own established mechanism for exactly this
class of gap (`ROUTING_LOCK_THEORY.md:160-183` surfaces a ratification item
rather than resolving it; `CLOUD_X86_PARITY_QUALIFICATION.md:143-155` states
that resolving the wall-clock boundary "is a scientific-governance decision, not
an execution one, and is explicitly outside what may be done autonomously").
This audit does not draft, propose a threshold for, or pre-approve any
amendment.

**6. Import the existing ARM-era front — EXPLICITLY_DISALLOWED.** Found during
this audit and reported because it is the most tempting shortcut available:
`results/e2/run/` **already contains world and candidate records for
`V2C|E2|mass_power|c_low|n_default|r000`** — the world that is poison on x86 ran
to completion on the ARM host. (This also corroborates
`POISON_WORLD_DETERMINATION.json:63`, which declined to claim the world would
fail on any other host.) Importing it is forbidden by
`X86_E2A_SEAL.json:4-5` (`historical_worlds_merged: false`),
`X86_E2A_FREEZE.json:196-201` ("no historical world is imported"), and the
authorization behind option 1 itself. It would also reintroduce the exact
host-dependent labelling the rerun was performed to eliminate.

*Correction issued:* `MURU_V2_E4A_CONDITION_3B_GOVERNANCE_AUDIT.md` §5 obstacle
4 previously stated that `results/e2/run/` "is now empty" and that the poison
world "has never completed anywhere". Both were wrong — the directory is tracked
and holds 279 worlds with front data, including this one. That document has been
corrected in place with a dated correction note; its verdict is unchanged, and
obstacles 1-3 of its §5 stand.

---

## TASK D — Decision tree, incorporating the pending E2b result

**The pending result has landed, and it is not PASS or FAIL.** Commit `7035215`
records `E2B_ORIGINAL_ENVIRONMENT_REPLAY = FAILED_TO_EXECUTE`: the sealed
manifest requires macOS 26.1 / arm64 / Python 3.13.12, this session has
Linux / x86_64 / 3.13.5, the OS and architecture mismatches are not remediable
on a running Linux VM, no macOS/arm64 host was reachable (three peer sessions
enumerated; one is this same host — I answered that query directly), and **no
scientific work was attempted and no verdict emitted**
(`results/e2b_heldout/replay_macos_arm64/E2B_ORIGINAL_ENV_RECONCILIATION.json`).
The live branch of this tree is therefore the third one.

### If E2b PASS (identity criterion met on the original environment)

Condition 2 clears **the replay-validity criterion only**. Four blockers remain,
in order:

1. **Gate 1 itself still has to be evaluated.** Gate 1 is the falsification
   hook — "IF E2b's direct measurement contradicts the v1 decomposition's 69/57
   retention-vs-generation split by more than 10 cases … STOP"
   (`ROUTING_LOCK_THEORY.md:37-41`). `E2B_REPLAY_VERDICT.json`
   (`falsification_hook_not_evaluated`) records that this hook has **never been
   computed**, deliberately, because a confounded replay would have converted an
   architecture artifact into a scientific verdict. A valid replay makes the
   hook evaluable; it does not answer it. This is post-hoc analysis on the
   replay's own outputs — no new search.
2. **Condition 3b** — literal 540 fronts, unchanged, with only routes 2/3/5 of
   Task C even potentially open.
3. **The `score` defect** — R0/R2/R6 unscoreable on the sealed corpus (Task B),
   which blocks producing an E4a result even with conditions 2 and 3b clear,
   plus the unresolved `k`/`eps` parameter question (§B.4).
4. **Condition 8** — the E4a execution manifest, deferred by design until 2 and
   3b clear (`E4A_GATE_CHECK_POST_RESUME.json:34`).

Conditions 1, 4, 6, 7 remain PASS; condition 5 is PASS-with-a-caveat given §B.3
item 2.

### If E2b FAIL (identity criterion met, hook contradicted by more than 10 cases)

**Blocked, but not permanently — and E4a as currently specified would not run.**
The two frozen statements differ in exactly one respect, and the difference
matters:

- Preregistration §4, as reproduced in `ROUTING_LOCK_THEORY.md:37-41`: "this
  protocol DOES NOT EXECUTE. All E4 ablations are suspended. **STOP.**" — no
  reopening clause in the quoted text.
- Causal decision tree §B.1 (`MURU_V2_CAUSAL_DECISION_TREE.md:187-190`, primary
  blob-verified source): "CHANGE: SUSPEND ALL E4 ABLATIONS **until the
  contradiction is resolved. Republish the root-cause attribution first.**"

The tree supplies the reopening path the §4 restatement omits: suspension runs
until the contradiction is resolved and the root-cause attribution is
republished — a scientific act, not an execution one. So: **not permanent**,
but E4a is suspended indefinitely and cannot be reopened by any amount of E2a
work, poison-world resolution, or scoring-code repair. Note also that Gate 2's
`LOCKED_EXECUTE_E4A` does not survive this: Gate 1 is checked first, and a fired
Gate 1 stops the predicate before Gate 2 is reached.

### If E2b cannot be evaluated (**the current state**)

Gate 1 is neither cleared nor fired, so condition 2 stays FAIL and E4a stays
WAITING indefinitely — the state is stable, not degrading, and no amount of
further autonomous work changes it. Exactly one of three owner decisions is
required, and none may be taken autonomously:

1. **Provide the environment.** Run the committed, portable
   `scripts/e2_rescue_v2/e2b_replay_shard.py` from a session on the original
   macOS/arm64 host at `/Users/aryav/Documents/MURU-ConjectureLab-v1`; or
   authorise a *substitute* macOS 26.1 / arm64 / Python 3.13.12 host, which
   removes the architecture confound at weaker provenance and would need its own
   environment verification (`E2B_ORIGINAL_ENV_RECONCILIATION.json`,
   `what_would_unblock_this`).
2. **Ratify a changed criterion** — e.g. a coefficient tolerance, or a
   structural-skeleton identity in place of exact-string identity. This is an
   amendment to a frozen criterion; the evidence a ratifier would need is
   already recorded results-blind (92 of 143 mismatches structurally identical,
   median coefficient drift ~1.09e-06, `E2B_REPLAY_VERDICT.json`). Explicitly
   forbidden to adopt autonomously, and doing so silently would fabricate a
   PASS.
3. **Formally record Gate 1 as unevaluable** and decide the consequence for E4a
   — including whether E4a is suspended indefinitely on that basis. This is the
   `DIAGNOSTIC_ONLY`-class governance question the routing documents already
   reserve to a protocol owner.

---

## FINAL OUTPUT

```
AUTHORITATIVE_PREREGISTRATION:            AUTHORITATIVE_SOURCE_NOT_RECOVERABLE
R2_R6_STATUS:                             R2_R6_MANDATORY_BUT_UNSCOREABLE
CONDITION_3B_AVAILABLE_FROZEN_PATHS:      NONE that are already-frozen-and-allowed.
    1 same-host retry ................... EXPLICITLY_DISALLOWED
    2 same-instance hardware expansion .. NOT_DEFINED
    3 cross-host qualified execution .... REQUIRES_NEW_GOVERNANCE
    4 formal missingness rule ........... EXPLICITLY_DISALLOWED
    5 owner amendment / ratification .... REQUIRES_NEW_GOVERNANCE
    6 import the ARM-era front .......... EXPLICITLY_DISALLOWED

IF_E2B_PASS:        Gate 1's 69/57 falsification hook still has to be EVALUATED
                    (never computed); then conditions 3b (literal 540 fronts),
                    the score-column defect blocking R0/R2/R6 plus the
                    unresolved k/eps values, and condition 8 (manifest) remain.
IF_E2B_FAIL:        Not permanent, but E4a is SUSPENDED INDEFINITELY. The causal
                    tree reopens it only "until the contradiction is resolved",
                    and only after the root-cause attribution is republished.
                    Gate 2's LOCKED_EXECUTE_E4A does not survive a fired Gate 1.
IF_E2B_UNEVALUABLE: (current state) One owner decision, none autonomous:
                    (a) provide the macOS/arm64/Python-3.13.12 environment, or
                    (b) ratify a changed identity criterion, or
                    (c) formally record Gate 1 unevaluable and rule on E4a.

SMALLEST_JUSTIFIED_NEXT_ACTION:
    Commit this audit and put four items to the protocol owner, in one pass:
    (i) Gate 1 — choose (a)/(b)/(c) above;
    (ii) condition 3b — choose among Task C routes 2/3/5, or rule that E4a
         does not proceed;
    (iii) authorise or refuse the R0 rewiring to `retained_by_argmax_score`,
         and rule on R2/R6 given that their ranking key is unrecoverable
         without re-running searches;
    (iv) note that the E4a authority text is unrecoverable from this host and
         may exist only on the macOS machine — recovery is an operator action.
    No file in the frozen scientific manifest is touched by any of this.

NEW_SCIENTIFIC_COMPUTE_REQUIRED_NOW:      NO
```

Every remaining blocker is a governance decision or an environment the operator
must supply. No compute is licensed now, and none was performed.

## Provenance

| Field | Value |
|---|---|
| Audit date (UTC) | 2026-08-18 |
| Repository / branch | `MURU-ConjectureLab-v1`, `claude/e2-rescue-v2-computational` |
| Repo state read | through commit `7035215` |
| Corpora read (ID fields and key names only) | `results/e2/run_x86_e2a_v1`, `results/e2/run` |
| Frozen documents amended | None |
| Waivers created | None |
| Arms dropped, metrics substituted, scores reconstructed | None |
| Experiments executed | None (E4a, M2/M3, E6, poison world: all untouched) |
