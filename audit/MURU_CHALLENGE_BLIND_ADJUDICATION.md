# MURU Challenge partition: blind governance adjudication

**Document ID:** `MURU-AUDIT-CHALLENGE-BLIND-ADJUDICATION-01`
**Classification:** `BLIND_PROSPECTIVE_AUTHORITY_ADJUDICATION`
**Adjudicated tree:** `.claude/worktrees/challenge-adjudication-blind`, RC5.1 / A3.6 engineering freeze
**Status:** `NOT COMMITTED` (working-tree document, per instruction)

**Question.** Under the frozen governing authorities as they stand at this
commit, and considering only what was prospectively written down before any
Held-out result existed, is the Challenge partition (a) prospectively required
or authorized as a scheduled next step, (b) conditional on the Held-out outcome,
or (c) not authorized at all by anything currently frozen?

---

## 1. Blinding attestation

### 1.1 What I did not read

I observed **no Held-out result of any kind**: no gate verdict, no rate, no
Wilson bound, no case record, no scoring artifact, no partial or summary figure.
I did not read, list, glob, grep or open anything under any `results/` path in
any worktree; anything under `muru-heldout-a3-6/`,
`muru-heldout-forensic-rescue/`, or `heldout-analysis-restoration/`; any file
whose name contains `RESCUE`, `RESTORED`, `RESTORATION`,
`heldout_g1_recovery`, `held_out_formal_analysis`, or `hostile_audit_report`; or
any git branch, log, or diff outside this worktree's HEAD. I ran no
`git log --all`, no `git worktree list`, and no cross-branch inspection.

**Environment hazard, disclosed.** The shell for this session was initialised
with its working directory inside
`.claude/worktrees/heldout-analysis-restoration`, which is on the prohibited
list. I never read, listed, or searched that directory. Every command I issued
used an **absolute path** into
`.claude/worktrees/challenge-adjudication-blind`, and every `grep`/`find` was
rooted at that absolute path. Two `git`-bearing commands aimed at the adjudicated
worktree were refused by the harness (worktree isolation); I did not retry them
by any other route, and no finding below depends on git history. I therefore
verified the adjudicated commit's contents by reading its files directly rather
than by resolving its SHA. For the same reason this document was staged outside
the tree and copied into place rather than written directly.

One consequence worth stating: the adjudicated tree contains **no `results/`
directory at all** (verified by a top-level listing), so there was no outcome
material present to encounter accidentally.

### 1.2 What I read

Frozen contract documents: `MURU_PAPER_BENCHMARK_PROTOCOL.md`,
`MURU_PAPER_BENCHMARK_FREEZE.md`, `MURU_PAPER_BENCHMARK_METRICS.md`,
`MURU_PAPER_BENCHMARK_CASE_FAMILIES.md`; amendments
`A1_ADEQUACY`, `A2_F16`, `A2_1_GENERATOR_VERSION`, `A3_1`, `A3_2`, `A3_3`,
`A3_4` (searched in full for Challenge references); frozen artifacts
`artifacts/paper_benchmark_partition_manifest.json`,
`artifacts/paper_benchmark_amendment_a3_4.json` (protected-path list).

Audit records: `audit/MURU_RC5_PROSPECTIVE_BINDINGS.md`,
`audit/MURU_RC5_UNFROZEN_EXECUTION_SEMANTICS.md`,
`audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md`,
`audit/MURU_RC5_FINAL_ENGINEERING_DECISION.md`,
`audit/MURU_RC5_1_FINAL_ENGINEERING_DECISION.md`,
`audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md`, `audit/MURU_RC4_2_CORE_DEFECT_REPAIR.md`.

Source: `src/muru/paper_benchmark/rc5_authorization.py`, `registry.py`,
`governance.py`, `g2_contract.py`, `g3_contract.py`, `rc5_g1_bridge.py`,
`structural_acceptance.py`, `rc5_runner.py`, `preflight.py`, `generator.py`;
`scripts/pb_rc5_a3_5_authorized_delta.py`,
`scripts/pb_50_build_global_science_plan.py`; tests
`test_rc5_preflight_partition.py`, `test_rc5_manifest.py`, `test_rc5_runner.py`,
`test_rc5_partition_identity.py`.

Supporting non-frozen material, read and **labelled as non-governing** wherever
cited: `paper/MURU_MANUSCRIPT_PRE_RESULTS.md`, `paper/MURU_TABLE_SHELLS.md`,
`paper/MURU_FIGURE_PLAN.md`, `paper/MURU_REPRODUCIBILITY_INVENTORY.md`,
`docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md`,
`README.md`, `MASTER_PLAN_CLARIFICATIONS.md`,
`MURU_ConjectureLab_v1_Master_Plan.md`, `ENVIRONMENT_CLOSURE.md`,
`BACKLOG.md`, `DEVIATIONS*.md`.

**A3.5 and A3.6 amendment texts are not present as standalone files at this
commit** (verified: `find` for `*A3_5*` / `*A3_6*` returns only
`audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md`, its JSON twin, and
`scripts/pb_rc5_a3_5_authorized_delta.py`). Their operative content reaches me
only through the audit records and through verbatim quotation inside the
engineering source, which I flag at each use.

---

## 2. Findings

### Finding 1. What the frozen text actually says about opening Challenge

**The complete set of Challenge statements in frozen governing instruments is
four items, and none of them is a trigger, a schedule, or a stopping rule.**

1. `MURU_PAPER_BENCHMARK_PROTOCOL.md:10-13` gives it existence and one negative
   role: the benchmark has "80 Development, 240 Held-out, and 60 Challenge", and
   "Challenge cases do not enter primary denominators."
2. `artifacts/paper_benchmark_partition_manifest.json` (an A3.4 protected path)
   records `"challenge": {"case_count": 60}`. A count and nothing else.
3. `src/muru/paper_benchmark/registry.py:14-15` (an A3.4 protected path):
   `PARTITIONS = ("development", "held_out", "challenge")` and
   `PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3}`.
4. `MURU_PAPER_BENCHMARK_AMENDMENT_A2_F16.md:235-236` and
   `MURU_PAPER_BENCHMARK_AMENDMENT_A2_1_GENERATOR_VERSION.md:97-98` list
   `inputs/challenge.jsonl` / `truth/challenge.jsonl` in row-hash tables. These
   establish that the content is sealed by digest, not that it may be opened.

**Amendments A1, A3.1, A3.2, A3.3 and A3.4 do not mention Challenge at all.**
Verified mechanically: `grep -c -i challenge` returns `0` for each of
`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md`, `_A3_1.md`, `_A3_2.md`,
`_A3_3.md`, `_A3_4.md`.

`MURU_PAPER_BENCHMARK_FREEZE.md` and `MURU_PAPER_BENCHMARK_METRICS.md` do not
mention Challenge either. The freeze record's "Required artifacts" list
(`FREEZE.md:36-45`) contains no Challenge record, and the metrics document's
denominator tables (`METRICS.md:12-19`, `:33-38`) are exhaustively Held-out.

**The only sequencing language anywhere lives in a self-declared writing
artifact.** `paper/MURU_MANUSCRIPT_PRE_RESULTS.md:539-541` says "The execution
sequence is fixed: content freeze, engineering release candidate,
structural-null calibration, threshold freeze, Development evaluation,
executable freeze, one-shot Held-out evaluation, and Challenge evaluation," and
`:1131-1133` says Challenge cases "are scored descriptively, as stress and
boundary conditions, after Held-out."

That document is **not a governing authority**, on its own record:

- `paper/MURU_REPRODUCIBILITY_INVENTORY.md:439` classifies `paper/*` as
  "manuscript scaffold ... writing artifact, not evidence".
- `paper/MURU_REPRODUCIBILITY_INVENTORY.md:51`: "It modifies files under
  `paper/` only. It is not merged into any active calibration, evidence, or
  engineering branch."
- It is absent from the 31 A3.4 `protected_paths` (enumerated from
  `artifacts/paper_benchmark_amendment_a3_4.json`; the list contains no `paper/`
  entry).
- Its own header (`:3-15`) classifies prospective results as CLASS C,
  "Placeholders only", and Section 5.21 carries
  `Challenge and Confirmation outcomes: [PROSPECTIVE RESULT TO INSERT]`.

So the fixed-sequence sentence records an **intention**, in a document that
explicitly disclaims evidentiary standing. It is not a frozen authorization, and
it does not appear in any protected path.

**Conclusion for Finding 1:** there is no pre-committed trigger, no schedule, no
stopping rule, and no frozen scoring contract for Challenge. There is existence,
a count, a seal digest, and one prohibition on its use in primary denominators.

### Finding 2. Is Challenge conditional on Held-out passing or failing?

**No. Neither model exists in the frozen text, and one of the two is affirmatively
foreclosed.**

*Promotion / escalation model ("open Challenge only if Held-out passes").*
Absent entirely. I found no frozen sentence conditioning Challenge on G1, G2 or
G3. The frozen decision rule that speaks to gate outcomes,
`MURU_PAPER_BENCHMARK_METRICS.md:75-78`, mentions only the paper's claim, never a
further partition.

*Diagnostic-retry / rescue model ("open Challenge if Held-out fails").*
Affirmatively excluded by the frozen role statement.
`MURU_PAPER_BENCHMARK_PROTOCOL.md:13`: "Challenge cases do not enter primary
denominators." `MURU_PAPER_BENCHMARK_METRICS.md:77-78`: "Any failed gate blocks
the positive claim while retaining descriptive endpoint reports." A partition
that enters no denominator cannot alter a gate, so it cannot function as a
retry. The non-governing manuscript states the same consequence explicitly
(`paper/MURU_TABLE_SHELLS.md:419`, limitation L13: "Challenge cases enter no
gate ... Cannot rescue a failed primary gate";
`paper/MURU_MANUSCRIPT_PRE_RESULTS.md:1458`: "Analysis of Challenge cases is
descriptive; they enter no gate").

**Conclusion for Finding 2:** the frozen record contains no outcome-conditional
trigger in either direction. It is silent on promotion and it forecloses rescue.
Silence in the promotion direction is not an authorization (see Finding 5).

### Finding 3. The frozen role and purpose of Challenge

The only **frozen** statement of role is negative and one clause long:
"Challenge cases do not enter primary denominators"
(`MURU_PAPER_BENCHMARK_PROTOCOL.md:13`).

The positive characterisation lives only in non-governing documents:
- `docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md:44`:
  "Descriptive robustness only; never in a primary denominator", and `:171-172`:
  "Challenge cases are excluded from every endpoint below."
- `paper/MURU_MANUSCRIPT_PRE_RESULTS.md:1490` (Table 2 row): "All Challenge
  endpoints | **CHALLENGE ONLY** | ... | descriptive only | ... | Stress
  behaviour; enters no primary claim."

**An important negative finding.** The frozen record does not support the claim
that Challenge cases are a harder or different population. The generator does not
branch on partition: `generator.py` uses `partition` only to parse the case ID
(`:246`) and to iterate IDs (`:288-289`), and A3.5 section 6.0 requires
truth-blindness "incl. **no branching on partition**" (quoted in
`audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md:98`). The architecture test
`tests/test_rc5_partition_identity.py:1-5,44-49` drives identical synthetic
content through the pipeline twice "changing only the partition label" and
requires the scientific payload to be byte-identical apart from four
administrative fields (`case_id`, `partition_label`, `seeds_used`,
`per_seed_status`).

So the 60 Challenge cases are three further replicates per family from the same
20 frozen families and the same generator, distinguished only by case ordinal and
therefore by search seed. **The scientific question Challenge answers that
Held-out does not is not specified anywhere frozen.** "Stress and boundary
conditions" is manuscript prose with no generative backing in the registry. On
the frozen record, Challenge is best described as a reserved, unspent replicate
pool with a standing prohibition on entering any primary denominator.

### Finding 4. Current authorization state in code, and what would have to change

**Current state.** `src/muru/paper_benchmark/rc5_authorization.py:23`:

> `AUTHORISED_PARTITIONS: frozenset[str] = frozenset({"development", "held_out"})`

The module's docstring (`:3-5`) quotes the governing amendment verbatim:

> Amendment A3.6: "authorises execution of the already-frozen Held-out partition
> under the exact existing RC5/A3.5 machinery ... RC5.1 is not authorized to
> construct or execute Challenge, or open Confirmation."

and its refusal message (`:41-43`) repeats it. The guard is deliberately
structural rather than a caller convention (`:7-11`) and is invoked at four
production sites: `preflight.py:79`, `rc5_manifest.py:564`, `rc5_runner.py:182`
and `rc5_runner.py:258`. `tests/test_rc5_preflight_partition.py:84-90` pins that
the refusal precedes any artifact read, asserting the temp directory is still
empty afterwards.

**A permission delta alone is not sufficient.** The frozen scorers have no
Challenge path, and would raise rather than score a 60-case partition:

- `rc5_g1_bridge.py:122`: `G1_DENOMINATOR = endpoint_case_count("scalar_competence")`
  (164), and `:432-436` raises when `len(outcomes) != G1_DENOMINATOR` because
  "a short sequence would silently change the endpoint's denominator".
- `g2_contract.py:475`: `G2_HELD_OUT_DENOMINATOR = 144`.
- `g3_contract.py:34` and `:258-262`: `G3_HELD_OUT_DENOMINATOR = 36`, and
  `score_g3` raises `expected 36 G3 events, got N`.
- `rc5_runner.py:839-843` states the design intent: "Every endpoint denominator
  is a **held-out** count computed from the frozen registry ... so an aggregate
  is only meaningful once that partition's whole population exists. Running it
  over a partial set would silently change the denominator."

A Challenge run yields different applicable counts (the non-governing
`paper/MURU_TABLE_SHELLS.md:78-80` computes 41 / 36 / 9 against Held-out's
164 / 144 / 36). No frozen instrument states Challenge denominators,
applicability sets, aggregation rule, uncertainty treatment, or reporting
contract. Specifying them is a scientific act, exactly the category
`audit/MURU_RC5_UNFROZEN_EXECUTION_SEMANTICS.md` section 3 labels
`UNFROZEN_SCIENTIFIC_DECISION` and for which RC5 stopped before implementation
("RC5 therefore stops before any implementation. Nothing in this document selects
an option", `:29-30`).

**What the change would mechanically involve**, using A3.6 as the worked
template (`audit/MURU_RC5_1_FINAL_ENGINEERING_DECISION.md:6-8`,
`audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md:6-7`): a new science freeze tag and
commit; a new engineering RC implementing it; a hostile review; a final
engineering decision; and an updated authorized-delta ledger, because
`rc5_authorization.py` is a ledger-pinned path
(`scripts/pb_rc5_a3_5_authorized_delta.py:342-350`) and a code-provenance path
for the global science plan (`scripts/pb_50_build_global_science_plan.py:51`).

**Incidental integrity observation, disclosed rather than acted on.** The RC5
ledger pins `rc5_authorization.py` at
`new_sha256='fd1dfe745feaf4344a08678eb6266e3bfb87add119b9927f78550ed70ebcfc72'`
with semantic scope "enforcing **development partition exclusivity**"
(`scripts/pb_rc5_a3_5_authorized_delta.py:342-350`). The file at this commit
hashes to `e8fc53c50fb8873cc4989db03e49ec5beb33872967f7cc1c4f5a14be8272ed2c`
(`shasum -a 256`), and no RC5.1 ledger exists in `scripts/` (only
`pb_rc4_2_authorized_delta.py` and `pb_rc5_a3_5_authorized_delta.py`). The
A3.6 / RC5.1 authorization expansion therefore edited a ledger-pinned path
without a corresponding ledger entry. This is outside the question I was asked,
but it is directly relevant to Finding 4: a further expansion inherits an
already-unclosed ledger obligation.

### Finding 5. Is there a frozen prohibition, and what discharges it?

**Yes, and it is explicit.** Amendment A3.6, quoted verbatim in
`rc5_authorization.py:3-5`: "RC5.1 is not authorized to **construct or execute
Challenge**, or open Confirmation." Note that it forbids *construction* as well
as execution.

Corroborated by the RC5.1 freeze record:
- `audit/MURU_RC5_1_FINAL_ENGINEERING_DECISION.md:19`: "**Quarantine
  Preserved**: Challenge partition remains unauthorized; Confirmation set remains
  sealed."
- `audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md:36-38`, Lens 4: "Confirm Challenge
  remains unexecutable ... **PASS**", and Lens 2: "`challenge` raises
  `PartitionNotAuthorised`."
- `audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md:54-55`: "Challenge NOT
  CONSTRUCTED OR EXECUTED".

The construction prohibition has one disclosed, bounded exception:
`audit/MURU_RC5_PROSPECTIVE_BINDINGS.md` section 6 discloses that generator
determinism tests invoke `generate_case` on Challenge case IDs to verify row
hashes, with "**Zero Outcome Contamination**": no Challenge case reached PySR, was
scored, or had any metric or verdict computed (`:108-113`). That exception covers
hash verification only and grants nothing further.

**What discharges the prohibition: only a superseding frozen amendment.** Nothing
in the repository discharges it automatically. There is no condition, no expiry,
and no triggering event. A3.6 is itself the proof of the mechanism: A3.5 section
14.2 authorized Development only (`rc5_runner.py:17-18`), and admitting Held-out
required a *new* amendment plus a whole engineering release (RC5.1) whose entire
delta was that one authorization line
(`audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md:13`: "the implementation delta of
RC5.1 is strictly restricted to partition authorization expansion as mandated by
Amendment A3.6"; `:23`, Lens 1: "Zero byte changes detected" across 27 scientific
modules).

### Finding 6. Frozen rules on consuming sealed partitions

**Held-out.** One-shot use is bound. The design spec
(`docs/superpowers/specs/2026-08-13-muru-paper-benchmark-design.md:43`) assigns
Held-out "One primary evaluation only". Its ordering constraint is fully
specified: `MURU_PAPER_BENCHMARK_PROTOCOL.md:30-34` refuses a held-out run "until
the evaluated implementation commit, strict evaluator, grammar, engine settings,
runtime budget, hashes, preflight, and clean-tree check are all locked and
verified", enforced in `governance.py:28-38`
(`assert_held_out_execution_allowed`), and
`MURU_PAPER_BENCHMARK_FREEZE.md:31-32`: "No command may load or score held-out
data before the complete executable freeze."

**Real-data Confirmation.** The strictest reuse rule in the project, at
`MURU_ConjectureLab_v1_Master_Plan.md:446`: "Opened once. If a result needs a
second look at the confirmation set, that is a new experiment requiring a new
pre-registration and disclosure in the report."

**Challenge.** *No one-shot rule, no reuse rule, and no ordering rule exists in
any frozen instrument.* `governance.py` contains a Held-out gate and nothing
else. The only ordering statement anywhere ("after Held-out") is the manuscript
sentence already classified as non-governing in Finding 1.

**No frozen rule requires the prior partition to be fully or correctly
interpreted before the next is opened.** I searched for such a requirement and
found none. What does exist is a general project-level stepwise-authorization
principle: `README.md:11-13`, "The fixed sequence is Phase 1 -> 2 -> 3 -> 4 -> 5.
Each phase authorizes **only** the next one", corrected and reinforced by
`MASTER_PLAN_CLARIFICATIONS.md` C1, which rejects the reading that one stage may
license a stage two steps ahead. Under that principle the completion of Held-out
does not carry authority for Challenge; it would carry authority only for
whatever instrument explicitly follows it, and no such instrument names
Challenge.

### Finding 7. Pre-committed decision tree once primary endpoints are evaluated

**There is exactly one frozen post-endpoint rule, and it is a claim rule, not an
execution rule.** `MURU_PAPER_BENCHMARK_METRICS.md:75-78`:

> The paper makes the positive umbrella claim only when preconditions hold and
> G1, G2, and G3 all pass. An adequacy failure that invalidates g therefore fails
> G1. Any failed gate blocks the positive claim while retaining descriptive
> endpoint reports.

That rule has two branches (make the claim / do not make the claim). **Neither
branch names Challenge, and neither branch specifies any further execution.**

Nothing else in the frozen corpus supplies a decision tree. The only other
"stopping rule" in the repository is unrelated:
`PHASE4_FROZEN_DISCOVERY_PROTOCOL.md:76` governs the search budget ("the search
stops at the frozen budget; no adaptive extension is permitted on seeing
results"). `PHASE1_DECISION.md`, `PHASE2_DECISION.md` and `PHASE3_DECISION.md`
are phase-level records and do not govern benchmark partitions.

In short: the frozen governance tells you what to **conclude** when the primary
endpoints have been evaluated. It does not tell you what to **run** next, and it
does not schedule anything after Held-out.

---

## 3. Verdict on the primary question

### **(c) - Challenge is not authorized by anything currently frozen.**

Opening it would itself require a new prospective amendment (an "A3.7") together
with an authorization delta, and no such instrument exists at this commit.

Reasoning, in the order the evidence forces:

1. **There is an explicit, live prohibition.** A3.6, quoted verbatim in
   `rc5_authorization.py:3-5`, states that RC5.1 "is not authorized to construct
   or execute Challenge". `AUTHORISED_PARTITIONS` at `:23` implements it, and the
   RC5.1 hostile review and engineering decision both certify the quarantine as
   intact. A prohibition in force is dispositive against (a) and (b) unless
   something discharges it, and nothing does (Finding 5).

2. **Nothing frozen grants the permission the prohibition withholds.** The entire
   frozen corpus on Challenge is four items: a case count in the protocol, a case
   count in the partition manifest, a case count in the registry, and hash rows
   in A2/A2.1 (Finding 1). A1, A3.1, A3.2, A3.3 and A3.4 contain zero mentions.
   None of these is a permission.

3. **The strongest counter-argument fails on its own document's terms.** The only
   text that reads like a schedule is
   `paper/MURU_MANUSCRIPT_PRE_RESULTS.md:539-541`, "The execution sequence is
   fixed: ... one-shot Held-out evaluation, and Challenge evaluation." That
   document is classified by its own companion inventory as a "writing artifact,
   not evidence" (`paper/MURU_REPRODUCIBILITY_INVENTORY.md:439`), is on no
   protected path, and is not merged into any engineering or evidence branch
   (`:51`). Even read at its most generous it records an intention; it does not
   discharge A3.6's refusal, and it supplies none of the missing scoring
   contract.

4. **Even with permission granted, opening Challenge would require new science,
   not only a new permission.** Every frozen primary scorer hard-asserts a
   Held-out denominator and raises otherwise: `rc5_g1_bridge.py:432-436` (164),
   `g2_contract.py:475` (144), `g3_contract.py:258-262` (36, with an explicit
   `expected 36 G3 events, got N` refusal). Challenge denominators,
   applicability, aggregation and reporting are unspecified in every frozen
   instrument. Under the project's own taxonomy
   (`audit/MURU_RC5_UNFROZEN_EXECUTION_SEMANTICS.md` section 3) that is an
   `UNFROZEN_SCIENTIFIC_DECISION`, and the precedent for encountering one is to
   stop and amend, not to choose.

5. **Absence of a prohibition would not have been enough, and here there is not
   even absence.** The project's governing principle is stepwise explicit
   authorization: "Each phase authorizes **only** the next one" (`README.md:13`),
   reinforced by `MASTER_PLAN_CLARIFICATIONS.md` C1, and demonstrated by the fact
   that admitting Held-out, a partition with a fully specified frozen scoring
   contract, still required a dedicated amendment and a dedicated engineering
   release. Challenge, which has no scoring contract at all, cannot be in a
   stronger position than Held-out was.

**Why not (a).** (a) requires a frozen instrument that requires or authorizes the
opening. There is none, and the one instrument that speaks to permission forbids
it. The intention recorded in the manuscript is real and I do not dismiss it as
noise, but an intention in a document that disclaims evidentiary standing is not
an authorization.

**Why not (b).** (b) requires the frozen text to make Challenge contingent on the
Held-out outcome. It does not, in either direction (Finding 2). Challenge's
status is unconditional, and the condition it is in is "prohibited", not
"pending a result".

**A distinction I want on the record.** (c) is a statement about authorization,
not about merit. The frozen record is entirely consistent with a Challenge stage
having been the designers' intent from the beginning, and nothing I found makes
Challenge outcome-conditional. An A3.7 would be writing down something the
project already meant, not inventing a new direction. That does not change the
verdict: at this commit, the instrument does not exist, and the instrument that
does exist says no.

---

## 4. Verdict on the decisive sub-question

**Would the decision to open Challenge be identical regardless of the Held-out
outcome?**

### **YES.**

The verdict in section 3 rests on exactly four load-bearing facts, and not one of
them is a function of any Held-out number:

1. `rc5_authorization.py:23` authorizes `{"development", "held_out"}` and A3.6's
   quoted text at `:3-5` forbids Challenge. A constant and a sentence.
2. A1 / A3.1 / A3.2 / A3.3 / A3.4 contain zero Challenge references
   (`grep -c` = 0 for each). A count of occurrences in frozen files.
3. `G1_DENOMINATOR` = 164, `G2_HELD_OUT_DENOMINATOR` = 144,
   `G3_HELD_OUT_DENOMINATOR` = 36, each with a hard length assertion. Four
   integers in frozen source.
4. No A3.7 exists in the tree. A file-existence check.

Running the two counterfactuals explicitly:

- **If I were told all three primary endpoints passed:** A3.6 still forbids
  Challenge, no amendment authorizes it, and the three scorers still assert
  Held-out lengths. Verdict unchanged: (c). Nothing in the frozen corpus turns a
  pass into a permission.
- **If I were told all three primary endpoints failed:** identical, and
  *additionally* the one frozen post-endpoint rule
  (`MURU_PAPER_BENCHMARK_METRICS.md:77-78`) says a failed gate blocks the positive
  claim while descriptive reporting continues, and the frozen role statement
  (`PROTOCOL.md:13`) keeps Challenge out of every primary denominator, so
  Challenge could not repair anything. Verdict unchanged: (c).

The three strongest textual bases for the YES:

1. `src/muru/paper_benchmark/rc5_authorization.py:3-5`, quoting A3.6: "RC5.1 is
   not authorized to construct or execute Challenge, or open Confirmation." The
   refusal is unconditional. It names no result, no gate, and no threshold.
2. `MURU_PAPER_BENCHMARK_PROTOCOL.md:13`: "Challenge cases do not enter primary
   denominators." Because Challenge can never move a gate, no Held-out outcome
   creates a reason to open it that a different outcome would not equally create
   or equally deny.
3. `MURU_PAPER_BENCHMARK_METRICS.md:75-78`: the sole frozen post-endpoint
   decision rule has two branches and mentions Challenge in neither. Both
   branches leave the authorization state exactly where it was.

**A hazard the YES does not cover, stated plainly.** The *decision to open* is
outcome-invariant. The *content of the instrument that would authorize opening*
is not automatically protected, because Challenge denominators, applicability and
aggregation are unspecified and would have to be written after a Held-out result
exists. That is a live prospectivity risk, and section 5 says what an A3.7 would
have to do about it.

---

## 5. What would have to be true for Challenge to be opened later

My verdict implies Challenge must **not** be opened at this commit. For it to be
opened legitimately later, all of the following would have to become true.

**A new frozen science instrument (an "A3.7") that:**

1. **Supersedes A3.6's refusal explicitly**, naming the clause it lifts. A3.6's
   text forbids construction as well as execution, so both must be lifted by
   name. Silence or a general expansion is not enough; A3.6's own drafting
   (quoted in `rc5_authorization.py:3-5`) is the model for how narrowly this is
   done.
2. **Specifies the Challenge scoring contract from scratch**, because none
   exists: applicable families and variants per endpoint; the Challenge
   denominators; the aggregation and uncertainty treatment; and an explicit
   restatement that no Challenge quantity enters any primary denominator or gate,
   preserving `PROTOCOL.md:13`. Without this the frozen scorers refuse
   (`rc5_g1_bridge.py:432-436`, `g3_contract.py:258-262`).
3. **States what scientific question Challenge answers.** Finding 3 establishes
   that no frozen instrument does, and that the generator does not make Challenge
   cases harder. A3.7 must either supply that rationale honestly (three further
   same-distribution replicates per family, reported descriptively) or drop the
   "stress and boundary conditions" framing, which the frozen registry does not
   support.
4. **Carries an outcome-invariance attestation.** A3.7 would be the first
   benchmark instrument written after a primary result exists. It must state, in
   the manner A3.5 section 6.9.1 establishes for outcome-invariance discipline
   (`audit/MURU_RC5_POST_A3_5_FREEZE_RECONCILIATION.md:72`), that no Challenge
   denominator, applicability set, threshold or reporting choice was selected
   with knowledge of the Held-out outcome, and record who wrote it and under what
   blinding. This is the single highest-risk aspect of a late A3.7 and the one an
   adversarial reviewer will attack first.
5. **Declares its temporal position with respect to sealed material**, as every
   prior amendment does (`paper/MURU_MANUSCRIPT_PRE_RESULTS.md:110-112` describes
   this as a standing convention across A1 through A3.5), including the fact that
   Held-out has been executed.
6. **Is frozen as a tag with a commit and a per-path digest artifact**, following
   `artifacts/paper_benchmark_amendment_a3_*.json` precedent, and added to the
   protected-path set.

**A corresponding engineering delta (an "RC5.2") that:**

7. Extends `AUTHORISED_PARTITIONS` in `rc5_authorization.py:23` to include
   `"challenge"`, and updates the refusal message so it stops asserting a
   boundary that no longer holds.
8. Implements the new Challenge scorers as an additive path that cannot reach the
   primary aggregate, preserving the guarantee at `rc5_runner.py:839-843`.
9. **Adds an RC5.2 authorized-delta ledger entry**, and closes the pre-existing
   gap identified in Finding 4: the RC5 ledger still pins `rc5_authorization.py`
   at `fd1dfe74...` while the file at this commit is `e8fc53c5...`, with no RC5.1
   ledger present. That inconsistency should be reconciled before, not
   simultaneously with, any further authorization expansion, so the reconciliation
   is not entangled with the expansion it would otherwise be auditing.
10. Passes an independent hostile review whose scope includes confirming that the
    Held-out record is unchanged and that the Confirmation set remains sealed,
    following `audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md` Lens 1 and Lens 4.

**Things that would not suffice, individually or together:** the manuscript's
"execution sequence is fixed" sentence; the fact that Held-out has been executed;
the absence of a rule forbidding Challenge in the protocol; the existence of
sealed Challenge inputs and their digests; or a judgement that Challenge is
harmless because it enters no gate. The last is the most tempting and should be
named as such: harmlessness is an argument for why A3.7 would be easy to write,
not a substitute for writing it.

---

## 6. Confidence and residual uncertainty

**High confidence.**

- That `AUTHORISED_PARTITIONS` excludes `challenge` and that the guard is
  enforced structurally at four production call sites. Read directly.
- That A1, A3.1, A3.2, A3.3 and A3.4 contain no Challenge reference. Verified by
  mechanical count, not by impression.
- That the three primary scorers hard-assert Held-out denominators and would
  raise on a Challenge population. Read directly in source.
- That `paper/MURU_MANUSCRIPT_PRE_RESULTS.md` is not a protected path and
  disclaims evidentiary standing. Verified against the enumerated 31-path A3.4
  protected list and the inventory's own classification.
- That no post-Held-out execution decision tree exists in the frozen corpus.
- That my verdict is outcome-invariant, because each of its four supports is a
  constant, a count, a sentence, or a file-existence check.

**Moderate confidence.**

- That A3.6 contains nothing about Challenge beyond the clause quoted in
  `rc5_authorization.py:3-5`. The amendment text is not in this tree. The quoted
  clause is corroborated independently by
  `audit/MURU_RC5_1_FINAL_ENGINEERING_DECISION.md:19`,
  `audit/MURU_RC5_1_FINAL_HOSTILE_REVIEW.md:28,36-38`, and two test docstrings
  (`test_rc5_preflight_partition.py:74`, `test_rc5_manifest.py:262`), all of
  which describe the same prohibition and none of which hints at a Challenge
  schedule. Four independent restatements agreeing is strong, but it is not the
  primary text.
- That A3.5 contains no Challenge scheduling clause. Same limitation. The
  reconciliation document's section 2 reconciles all fourteen D-items with no
  Challenge item, and A3.5 section 14.2 is described as authorizing "the
  **Development** partition only" (`rc5_runner.py:17-18`), which is consistent
  with no Challenge authorization existing there.

**Residual uncertainty I could not resolve from this tree.**

1. **A3.5 and A3.6 primary texts are absent.** If either contains a Challenge
   scheduling clause not surfaced in any audit record, test, or source docstring,
   my verdict could move from (c) toward (a). I judge this unlikely: A3.6's own
   quoted sentence forbids Challenge, and a scheduling clause coexisting with an
   explicit refusal in the same amendment would be a contradiction the RC5.1
   hostile review's four lenses would have had to address. But I cannot exclude
   it from inside this worktree, and whoever holds `benchmark-content-freeze-a3-6`
   at commit `327b5553...` should confirm it directly.
2. **Whether any *later* instrument exists outside this commit.** By construction
   I inspected no branch, tag, or history beyond this worktree's HEAD. If an A3.7
   was frozen after `8d87143`, my (c) is correct as of this commit and stale as
   of that one. My finding is therefore precisely: nothing frozen *at this
   commit* authorizes Challenge.
3. **Whether the RC5 ledger / `rc5_authorization.py` hash mismatch is closed
   elsewhere.** I found no RC5.1 ledger in `scripts/`. It may exist on another
   branch I did not and could not inspect.
4. **The intended scientific purpose of Challenge.** Genuinely unspecified in the
   frozen record, not merely unlocated by me. I searched the protocol, freeze
   record, metrics, case families, all seven present amendments, the registry and
   the generator. This is a real gap in the frozen corpus, and it is the main
   reason (c) is the right answer rather than a technicality: a partition whose
   scientific question was never written down cannot have been prospectively
   scheduled to answer it.

**Adversarial self-check, answered directly.**

- *Did I at any point infer or guess the Held-out result?* No. I never wrote or
  relied on any sentence of the form "since Held-out presumably ...". I struck no
  such reasoning because none was formed. I read no results directory, and none
  exists in the adjudicated tree.
- *Would my answer change if told Held-out passed all three primary endpoints?*
  No. Section 4 works the counterfactual explicitly.
- *Would it change if told all three failed?* No. Same section, and the failure
  branch is additionally foreclosed by `METRICS.md:77-78` and `PROTOCOL.md:13`.
- *Am I inventing a permission the frozen text does not grant?* I checked the
  opposite direction as well, and I want it recorded: I am also not inventing a
  prohibition. The prohibition is quoted text
  (`rc5_authorization.py:3-5`), certified intact by two independent RC5.1 audit
  records. Where the frozen text is merely *silent* (a Challenge schedule, a
  Challenge purpose, a Challenge scoring contract), I have treated silence as
  absence of authorization and said so, rather than reading intent into it.
