# MURU V2 E4a Condition 3b: Results-Blind Governance Audit

**Question audited.** Does E4a condition 3b ("Full 540-case E2a population
complete with persisted front data", `MURU_V2_E4A_EXECUTION_GATE_CHECK.md:12`)
require

- **A.** literal front data for all 540 worlds, or
- **B.** full population accounting, in which a formally quarantined,
  unresolved poison world is permitted and represented adversarially through
  `r_remaining`, or
- **C.** some other already-frozen rule?

**Method.** Frozen pre-result governance only, read mechanically. No waiver
created, no protocol amended, no authorial intent inferred, no E4a outcome
used (E4a has not run). No experiment executed by this audit; the only
computation performed was reading `world_id` fields and JSON key names out of
the sealed corpus — no A/B/C/D/E stage, rate, or per-cell value was read.

---

## Verdict

```
E4A_CONDITION_3B_REQUIRES_LITERAL_540_FRONTS
```

Reading A. Option B is not supported by any frozen text: the adversarial
`r_remaining` device is defined, by its own governing documents, as a
**Gate-2 routing** construct and is nowhere extended to E4a's analysis
population.

---

## 1. What the frozen texts actually say

### 1.1 The population requirement (the basis of 3b)

| Source | Text | Line |
|---|---|---|
| `MURU_V2_E4A_PREREQUISITE_VERIFICATION.md` | "Full 540-case E2a population complete with persisted front data (section 6: **\"Population. All 540 E2a cases\"**). ... the frozen protocol's own population definition (section 6) is simply 'All 540 E2a cases,' un-sampled." | 75–83 |
| `MURU_V2_E4A_EXECUTION_GATE_CHECK.md` | "What the frozen protocol actually requires (section 6: 'Population. All 540 E2a cases') is the FULL population" | 11 |

Both quote `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` section 6. That
population definition carries **no exception clause, no missing-data rule, no
minimum-N, and no quarantine carve-out** anywhere in any surviving quotation
of it. Absent an exception, "all 540" is all 540.

### 1.2 E4a's input *is* front data — so "all 540 cases" entails 540 fronts

`v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md:311` fixes E4a's
cost at "**0** (post hoc on E2 fronts)", and
`src/muru/v2_calibration/e2_rescue_v2/e4a_scoring.py:32-33` restates it: "No
PySR run, no Julia call, no new search — every function here operates on
already-persisted front rows." A case with no persisted front rows cannot
enter any of the nine metrics under any policy R0–R6. For E4a specifically,
"population = all 540 cases" and "front data for all 540" are the same
requirement, not two.

### 1.3 The frozen decomposition is exhaustive over 540 by declaration

`v2_design_reference/MURU_V2_E2_PREDECLARATION.md:205-208` (primary frozen
text, present in the repository):

> "This is mechanical and exhaustive: every one of the 540 E2a cases receives
> exactly one of A/B/C/D/E, in that decision order, **with no case left
> unclassified and no case double-counted**."

E4a performs a **per-policy A–E recomputation** over the population
(`e4a_scoring.py:30-31`, "the per-policy A-E recomputation (section 2,
mechanically reusing `e2_aggregate.evaluate_world`'s own decision sequence)").
A world with zero front rows receives no label under any policy, so scoring
E4a over 539 produces an A–E decomposition that is, by the predeclaration's
own words, not exhaustive over the frozen population.
`MURU_V2_E2_ROUTING_LOCK_THEORY.md:219-224` restates the same rule and adds
that "there is no separate 'invalid' or 'excluded' category for E2a proper."

### 1.4 The poison-world procedure

`results/e2/run_poison_world/PENDING_EXECUTION_DIAGNOSIS.md` — the frozen
procedure the current determination follows
(`POISON_WORLD_DETERMINATION.json:8` names `E2_EXECUTION_DEVIATION.md` §13 as
"procedure_followed"; §13 is at `E2_EXECUTION_DEVIATION.md:193-199`):

- line 22: "It has **not** been dropped from the 540-world population. It
  remains outstanding, exactly one world, pending re-attempt under different
  execution conditions."
- line 29: "E2 completion accounting must treat this world as **539 ordinary +
  1 pending** until one of the above outcomes occurs. **No scientific analysis
  proceeds on a corpus that omits it as though it were absent by design.**"
- line 27 enumerates the only outcomes that discharge "pending": (i) it
  succeeds and is merged after a parity check and a world_id-uniqueness check;
  or (ii) it repeatedly fails in a clean isolated environment, retries stop
  entirely, and a dedicated execution diagnosis is produced — "**not a
  scientific workaround, not a fabricated result**."

Outcome (ii) has occurred (`POISON_WORLD_DETERMINATION.json`, four independent
OOM kills). Note what outcome (ii) does and does not do: it discharges the
*retry obligation* and converts "pending re-attempt" into "diagnosed
unrunnable on this host." **It does not supply the missing front, and no
frozen text states that a diagnosed world may be scored, imputed, excluded, or
treated as analytically absent.** The same document's own line 21 forecloses
the only substitute that would let analysis proceed: "no search was ever
completed for this world, so it cannot be scored."

The same accounting discipline is frozen upstream at
`E2_EXECUTION_DEVIATION.md:217`: "535 ordinary worlds + 5 quarantined (pending
execution diagnosis, **not scientifically classified, not omitted, no
substitutes**) = 540."

### 1.5 Why option B fails mechanically

`r_remaining` is defined only for the Gate-2 routing predicate, and every
document that defines it says so in its own text:

| Source | Text | Line |
|---|---|---|
| `routing_lock.py` (`evaluate_gate2` docstring) | "`r_remaining` is the number of the 540 E2a cases with no stage yet (includes any quarantined-but-unresolved world, e.g. the poison world ... since its eventual stage is exactly as unknown as any other outstanding world's, and must be treated as adversarially unknown, never assumed)." | 146–150 |
| `MURU_V2_E2_ROUTING_LOCK_THEORY.md` §2 | "`r = 540 - n` = number outstanding (this includes any quarantined-but-unresolved world, e.g. the poison world ...)" — introduced expressly to bound "the frozen E4a routing gate's eventual verdict" | 75–81, cf. 10–13 |
| `MURU_V2_E2_ROUTING_LOCK_THEORY.md` §3.5 | "`LOCKED_EXECUTE_E4A` locks Gate 2 only. **Actually running E4a additionally requires** Gate 1 to clear" | 201–207 |
| `MURU_V2_E2_ROUTING_LOCK_FREEZE.md` §4 | "this locks **Gate 2 only**" | 104–112 |
| `POISON_WORLD_DETERMINATION.json` | the world is "counted_as": "r_remaining = 1, i.e. adversarially unknown", with authority cited to `evaluate_gate2`'s docstring, and consequence stated purely in Gate-2 terms | 54–59 |

The scope of the device is the *routing verdict*, i.e. which branch of the
frozen gate fires. Condition 3b is a population-completeness condition on
E4a's analysis input. No frozen text transfers `r_remaining` from the former
to the latter, and the routing documents repeatedly and explicitly decline to
make that transfer. `MURU_V2_CAUSAL_DECISION_TREE.md` §B.1/§B.2 (lines
182–237) likewise defines what *enables* E4a and what E4a decides, and states
no population-completeness rule at all — so it cannot be the source of a
permission for B either.

The existing post-resume check reached the same reading independently and
declined to waive it (`results/e2/run_x86_e2a_v1/E4A_GATE_CHECK_POST_RESUME.json:27-28`):
"the frozen protocol's condition is the full 540-case population WITH
persisted front data. `V2C|E2|mass_power|c_low|n_default|r000` has no front
data and no world record, so a literal 540/540 is still not reached ... this
world cannot affect the routing decision ... but condition 3b is a
population-completeness condition, not a routing condition, and is not waived
on the grounds that routing survives it." This audit confirms that reading
from source; it does not merely inherit it.

### 1.6 What is *not* in dispute

The population is fully **accounted for**, and this audit does not claim
otherwise. `X86_E2A_SEAL.json:6-24`: scheduled 540, completed 539,
unresolved 1 (`V2C|E2|mass_power|c_low|n_default|r000`), accounted_for 540,
0 duplicates, 0 torn records, 0 execution errors. Accounting completeness and
population completeness are different conditions; 3b is the latter.

---

## 2. Integrity findings surfaced by this audit (reported, not resolved)

1. **The cited authority document is absent from the repository.**
   `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` (commit `f4c1105`) — the
   source of section 4 (the routing gate), section 6 (the population and the
   DEV/EVAL split), and sections 3/5/5.1/7/13 — exists nowhere in this
   repository or in any reachable git history (`git cat-file -t f4c1105` →
   "Not a valid object name"; the design pack's own provenance table,
   `v2_design_reference/DESIGN_PROVENANCE.md:9-23`, does not list it). Every
   quotation of it available here is second-hand, inside derivative documents
   (`MURU_V2_E2_ROUTING_LOCK_THEORY.md:31-54`,
   `MURU_V2_E4A_RESULTS_BLIND_AMENDMENT_V1.md:18,26-28,158`,
   `MURU_V2_E4A_PREREQUISITE_VERIFICATION.md:13-22,75-83`,
   `routing_lock.py:8-13`). Those quotations are mutually consistent and none
   supports reading B — and the verdict above does not depend on the missing
   file alone, since §1.3's exhaustiveness declaration is primary text that is
   present. This is nevertheless a standing archival defect: the authority text
   for the E4a gate is not retained in the repository it governs.

2. **Two documents name the wrong poison world.**
   `MURU_V2_E4A_EXECUTION_GATE_CHECK.md:36-41` and
   `MURU_V2_E4A_PREREQUISITE_VERIFICATION.md:86-93` both identify the blocking
   world as `V2C|E2|mass_affine_descriptor|c_low|n_noiseless|r000`. That is the
   **superseded, ARM-era** poison world (`E2_EXECUTION_DEVIATION.md:195`;
   `results/e2/run_poison_world/PENDING_EXECUTION_DIAGNOSIS.md:6`). The poison
   world of the authoritative single-host x86 corpus is
   `V2C|E2|mass_power|c_low|n_default|r000`
   (`POISON_WORLD_DETERMINATION.json:4`; `X86_E2A_SEAL.json:19-21`). Both
   documents' live figures are also superseded (481/540 vs 540 accounted for),
   as `E4A_GATE_CHECK_POST_RESUME.json:4` itself records. The conclusion is
   unaffected — the two worlds occupy the same governance position — but the
   identifiers are stale and should not be quoted forward.

3. **A second, independent E4a blocker already disclosed and still open.**
   `e4a_scoring.py:34-56` discloses that Rescue-v2's `RawFrontRow` schema omits
   PySR's native `score` column, so **R2 and R6 raise `InsufficientRowData`
   rather than guessing, for every Rescue-v2-sourced world**. Verified
   mechanically against the sealed corpus by key names only: candidate rows
   carry `retained_by_argmax_score` but no `score` field. The entire x86 corpus
   is Rescue-v2/lazy-sourced (`X86_E2A_FREEZE.json:182-187`), so two of the
   seven arms cannot be scored on it as sealed. This is orthogonal to 3b and is
   noted so it is not discovered after conditions 2 and 3b clear.

---

## 3. A materiality fact, derived mechanically, offered *without* a waiver

The frozen DEV/EVAL split is `DEV = replicate in {0,1}`,
`V2C_RET_EVAL = replicate in {2..11}`
(`MURU_V2_E4A_RESULTS_BLIND_AMENDMENT_V1.md:26-28`, quoting section 6;
implemented at `e4a_scoring.py:89-90`). The missing world is replicate `r000`,
i.e. a **DEV** case. Counted from the sealed corpus by `world_id` alone:

```
EVAL (replicates 2-11) present: 450 / 450
DEV  (replicates 0-1)  present:  89 /  90   <- the poison world is the one absent
```

So every EVAL-restricted endpoint — including metric 2's `mass_power` EVAL
denominator of 90 (`e4a_scoring.py:86`) — has a literally complete input set.

**This is stated as a fact for a protocol owner, not as a resolution.**
Condition 3b's frozen basis is a population condition over all 540 cases, not
over EVAL; no frozen text reduces it to the EVAL split, and this audit does not
invent one. Reading A stands.

---

## 4. Mechanically required next action

1. **E4a does not execute.** Condition 3b is unsatisfied. Independently,
   condition 2 (Gate 1) is unsatisfied: E2b executed 144/144 but reproduced the
   frozen identity criterion for 1 of 144 cases, verdict
   `INCONCLUSIVE__IDENTITY_CRITERION_NOT_EVALUABLE_CROSS_ARCHITECTURE`, "Gate 1
   cannot be cleared here — neither affirmatively nor negatively"
   (`results/e2b_heldout/E2B_REPLAY_VERDICT.json`). Gate 1 is checked
   sequentially **before** Gate 2 and is not superseded by
   `LOCKED_EXECUTE_E4A` (`MURU_V2_E4A_PREREQUISITE_VERIFICATION.md:24-37`;
   `MURU_V2_E2_ROUTING_LOCK_FREEZE.md:104-112`). Clearing 3b alone would not
   license E4a.
2. **Condition 8 stays unproduced.** The E4a execution manifest is deferred
   while 2 and 3b are open (`E4A_GATE_CHECK_POST_RESUME.json:34`).
3. **Escalate, do not resolve autonomously.** The only frozen-compliant exits
   from 3b are (a) obtaining a genuine front for
   `V2C|E2|mass_power|c_low|n_default|r000` under a procedure that satisfies the
   frozen parity discipline (see §5 — currently blocked), or (b) an explicit
   protocol-owner ratification of what "all 540" means when a world is
   determined unrunnable. (b) is a governance decision of exactly the class
   `CLOUD_X86_PARITY_QUALIFICATION.md:143-152` places outside autonomous
   authority, and this document does not make it, propose a threshold for it,
   or act as one.
4. **Do not quote the stale poison-world identifiers** from
   `MURU_V2_E4A_EXECUTION_GATE_CHECK.md:36-41` or
   `MURU_V2_E4A_PREREQUISITE_VERIFICATION.md:86-93` forward (finding 2).

---

## 5. Does any already-frozen procedure permit running the poison world on a
higher-memory host without invalidating the single-host x86 corpus?

**Answer: a cross-host execution procedure is frozen and exists, but it cannot
currently be satisfied, and no frozen text authorizes admitting a second host's
output into the x86-only sealed corpus. Not run; not recommended without a
governance decision.**

**What is frozen and permissive.**
`results/e2/run_poison_world/PENDING_EXECUTION_DIAGNOSIS.md:27` does
contemplate a different machine: "once sufficient uncontended compute is
available, re-attempt this single world alone ... using exactly commit
`4892c76`, the same dependency/environment lock, the same PySR/Julia versions,
the same seed, the same search budget, the same classifier, the same
`SIMPLIFY_TIMEOUT_SECONDS=5`. **If run on a different host/environment, first
replay several already-completed ordinary rescue worlds there and confirm exact
scientific parity before trusting any output from that environment.** If it
succeeds, merge ... only after that parity check and a world_id-uniqueness
check." The standard for that parity check was subsequently tightened, also
pre-result: "PARITY_PASS requires 100% agreement on **every** replayable
completed world" — a sample is not "every world"
(`MURU_V2_E2_RESCUE_V2_HOSTILE_REVIEW.md:70-78`), implemented as
`scripts/e2_rescue_v2/full_corpus_parity_audit.py`.

**Why it cannot currently be satisfied — four frozen obstacles, none of which
this audit may waive.**

1. **The last cross-host execution of exactly this procedure failed.**
   `CLOUD_X86_PARITY_QUALIFICATION.md:52-67`: `PARITY_PASS = false`,
   `NEW_CLOUD_HOST_PARITY_FAILED`, and per line 132–141 "scientifically relevant
   parity failure halts execution ... **Zero worlds were executed on this
   host.**"
2. **The root cause is host-speed, not architecture, so more RAM does not
   avoid it.** `CLOUD_X86_PARITY_QUALIFICATION.md:78-95`:
   "`SIMPLIFY_TIMEOUT_SECONDS` is a wall-clock budget, so host speed determines
   a scientific label," on a witness classified in 4.80 s against a 5 s budget —
   a 200 ms margin — and the affected field `first_loss_stage` is
   routing-relevant. Line 143–150 generalizes it: the boundary "is
   host-dependent on *any* change of machine, and in principle on load, thermal
   state, or a CPU generation change on the *same* architecture. The existing
   corpus is internally consistent only because it was produced on one machine
   at one speed." Exposure is not marginal: 834 candidate rows carrying
   `SIMPLIFY_TIMEOUT` across 237 of 530 worlds (lines 112-120).
3. **The single-host constraint is the authorization itself, not a preference.**
   `X86_E2A_FREEZE.json:4`: "user governance option 1 — rerun the complete
   frozen E2a population from scratch on **this single x86_64 host**, to
   eliminate the mixed-architecture / wall-clock `SIMPLIFY_TIMEOUT`
   reproducibility problem," with `X86_E2A_SEAL.json:4-5`
   `corpus_is_x86_only: true`, `historical_worlds_merged: false`, and
   `X86_E2A_FREEZE.json:196-201` recording that no historical world may be
   imported. Admitting a second host's world into that corpus is precisely the
   mixed-host record option 1 was chosen to eliminate; no frozen text authorizes
   it, and the second cross-host data point is consistent — E2b reproduced the
   sealed identity criterion for 1 of 144 cases across an ARM→x86 move
   (`E2B_REPLAY_VERDICT.json`).
4. **The parity procedure structurally cannot validate this particular world,
   and its merge target no longer exists.** Parity qualification works by
   replaying *already-completed* worlds against sealed references; the poison
   world has never completed anywhere, so it has no reference and its own
   `SIMPLIFY_TIMEOUT`-sensitive labels would be qualified by nothing. Separately,
   the frozen procedure's merge target is `results/e2/run/`
   (`PENDING_EXECUTION_DIAGNOSIS.md:27`), the pre-rerun corpus namespace, which
   governance option 1 superseded and which is now empty; no frozen text
   redirects that merge into `results/e2/run_x86_e2a_v1/`.

**Consequence.** A higher-memory host could plausibly make the world *run* —
the failure is memory-bound and deterministic (33.4 GiB with ~34 GiB headroom;
47.72 / 47.71 / 47.53 GiB with ~46 GiB headroom, a 0.4% spread —
`POISON_WORLD_DETERMINATION.json:12-37`). But "it would run" is an execution
fact, and whether its output may enter a corpus declared single-host is a
governance fact, and only the second one is at issue. Under frozen governance
as it stands, the honest position is: the procedure exists, its precondition is
currently failed, its merge target is superseded, and it cannot qualify the one
world it would be used for. **Nothing was run.**

---

## 6. What this document does not do

- Does not create, propose, or imply a waiver for condition 3b or any other.
- Does not amend, edit, or reinterpret any frozen protocol, and adds no
  threshold, tolerance, epsilon, or exception.
- Does not infer authorial intent; where frozen text is silent (e.g. the
  treatment of a diagnosed-unrunnable world in the analysis population), it
  reports the silence and escalates rather than filling it.
- Does not use any E4a outcome — E4a has not run — and reads no A/B/C/D/E
  stage, rate, or per-cell value from the sealed corpus. The only corpus reads
  performed were `world_id` strings and JSON key names.
- Does not execute, schedule, or authorize any scientific run, including the
  poison world.

## Provenance

| Field | Value |
|---|---|
| Audit date (UTC) | 2026-08-18 |
| Repository | `MURU-ConjectureLab-v1`, branch `claude/e2-rescue-v2-computational` |
| Corpus audited | `results/e2/run_x86_e2a_v1` (sealed; `X86_E2A_SEAL.json`) |
| Verdict | `E4A_CONDITION_3B_REQUIRES_LITERAL_540_FRONTS` |
| Frozen documents amended | None |
| Waivers created | None |
| Experiments executed | None |
