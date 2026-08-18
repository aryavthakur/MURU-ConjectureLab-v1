# MURU V2 E4a Consolidated Readiness Decision (results-blind)

Third and final audit in the series, after
`MURU_V2_E4A_CONDITION_3B_GOVERNANCE_AUDIT.md` and
`MURU_V2_E4A_BLOCKER_RESOLUTION_AUDIT.md`. Incorporates the authoritative
macOS/ARM64 E2b replay pushed from the Mac.

**Nothing was executed.** No E4a, no M2/M3, no integration, no E6, no PySR
search, no E2a or E2b rerun, no scientific criterion amended. Work performed:
`git fetch` (no reset, no clean, no checkout, no overwrite), reading committed
artifacts, and re-hashing/recounting committed files.

---

## PHASE 0 — Synchronize and verify the Mac E2b PASS

`git fetch --all --tags` brought in one new ref: `origin/exec/muru-heldout-a3-6`,
tip `d6f607a` "E2b macOS/ARM64 authoritative replay: 144/144 exact identity,
E2B_PASS", authored 2026-08-18 10:37 -0400. Its parent is `8d87143` — the v1
held-out run commit itself, i.e. the replay was run from the same commit the
sealed evidence was produced at, not from the rescue-v2 branch. Local tree was
clean before and after; nothing was reset or overwritten.

### Verified independently (not taken from the replay's own summary)

| Requirement | Frozen source | Replay | Verdict |
|---|---|---|---|
| Host macOS/ARM64 | manifest `run.environment.platform = macOS-26.1-arm64-arm-64bit-Mach-O`, `machine = arm64` | `Sandeeps-MacBook-Air.local`, Darwin 26.1, arm64, `platform_full` identical | **MATCH** |
| Python | manifest `python_version = 3.13.12`, CPython | 3.13.12 CPython | **MATCH** |
| Dependency lock | manifest `environment_lock_digest = 13b21b8c…c357fa8` | `sha256sum requirements.lock.txt` recomputed here → `13b21b8c…c357fa8` | **MATCH** |
| Run commit | manifest/receipt `8d87143d4280602323aa33ee0b5481aaef0fb4a8` | report `run_commit` identical; replay commit's parent is that commit | **MATCH** |
| Sealed evidence integrity | `execution_seal_receipt.json`, `file_count = 482` | **re-hashed here: 482/482 verified, 0 mismatched, 0 missing**; `manifest_digest` recomputed under the manifest's own canonical-serialization convention → `bcd197dc…` matches | **PASS** |
| Cases / seeds / searches | plan `E2b: cases 144, seeds_per_case 30, searches 4320` | 144 / 30 / 4,320 | **MATCH** |
| Seed identity | manifest `science.case_search_seeds` | report `seed_identity = PASS`; corroborated by `E2B_REPLAY_PRECONDITION_CHECK.json` (`seed_derivation_reproduces_sealed_seeds_used = 144`) | **PASS** |
| selection_count exact | sealed `G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json` | **recomputed here: 144/144** | **PASS** |
| representative exact | same | **recomputed here: 144/144** | **PASS** |
| Full case identity | both fields | **recomputed here: 144/144, zero mismatches** | **PASS** |
| Execution errors | — | 0 | **PASS** |
| Decision | — | `FINAL_E2B_DECISION: E2B_PASS` | **recorded** |

The recomputation was done against this repository's own sealed record, not
against the replay's embedded "sealed" column — and that column was also checked
against the repo record (144/144 agreement on both fields), so the comparison is
not self-referential. The 144 sealed source records re-hash to their recorded
`source_record_sha256` (144/144).

### Julia and SymbolicRegression.jl — explicit finding

- **SymbolicRegression.jl:** manifest pins `~1.11.0`; replay ran **1.11.3**.
  Satisfies the frozen specifier. **MATCH.**
- **Julia:** the frozen manifest records `run.environment.julia.julia =
  "NOT_STARTED"` — the pre-execution manifest was written before Julia was
  started, so **no Julia version was ever pinned for E2b**, and none appears
  anywhere in the sealed evidence (`case_provenance.jsonl` records only
  `host_platform`, `commit`, timings). The replay ran Julia 1.12.7 and its
  provenance argues from binary mtime that the original held-out execution
  (Aug 16) used the same binary installed Aug 15. That argument is *not*
  verifiable from frozen artifacts; what *is* verifiable is that no frozen
  Julia pin exists to violate. The "1.12.6" figure appears in the RC4.1 identity
  proof and in `X86_E2A_FREEZE.json` — different layers (E2a/x86), not the E2b
  manifest.

**No discrepancy against the original frozen environment requirements was
found.** The one gap (Julia unpinned) is a pre-existing provenance gap in the
frozen manifest itself, not a deviation by the replay, and the 144/144 exact
identity is itself the strongest available evidence the environment reproduced.

```
E2B_GATE1_IDENTITY = PASS
```

Frozen. Nothing beyond the replay is inferred from it — in particular, see
Phase 1 item 9.

---

## PHASE 1 — The exact 69/57 falsification hook

### 1. What 69 and 57 are

From `v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.md` (primary, blob-hash
verified in `DESIGN_PROVENANCE.md:9-23`), §4.1 and §6.2, denominator **144**:

| First irreversible failure point | Cases | Root-cause class |
|---|---:|---|
| `REPRESENTATION` | 12 | GRAMMAR_REPRESENTABILITY |
| `GENERATION` (no seed matched support or family) | 45 | SEARCH_GENERATION_FAILURE |
| `GENERATION_FAMILY` (support reached, family never) | 12 | SEARCH_GENERATION_FAILURE |
| `SELECTION_WITHIN_SEED_RETENTION` | **69** | SELECTION_FAILURE |
| `SELECTION_CROSS_SEED_IDENTITY` | 2 | CANONICALIZATION_EQUIVALENCE_FAILURE |
| `NONE` (success) | 4 | NONE_SUCCESS |

§6.2 restates the class totals: SELECTION_FAILURE **69** (47.92%),
SEARCH_GENERATION_FAILURE **57** (39.58%) = 45+12, GRAMMAR_REPRESENTABILITY 12,
NONE_SUCCESS 4, CANONICALIZATION_EQUIVALENCE_FAILURE 2. Sum = 144. **The
category labels and counts given in the tasking prompt are confirmed from
primary frozen source, not adopted from the prompt.**

Both numbers are *inferences under a declared observability bound*, not
observations — this is stated in the sources themselves. §1.1
`WITHIN_SEED_PARETO_NOT_OBSERVABLE`: only `argmax(score)` per seed was
persisted, "The fronts are gone", so "never generated" means only "never reached
cross-seed selection". `MURU_V2_G2_PARETO_STUDY_DESIGN.md:28-34` tabulates
exactly which classes are certain and which are inferred: `REPRESENTATION` (12)
certain, `SELECTION_CROSS_SEED_IDENTITY` (2) certain, `NONE` (4) certain — while
**57 is "Only that no *retained* candidate was correct. The front is
unobserved."** and **69 is "Inferred from paired within-case behaviour … The
discarded candidates were never seen."**

### 2. What E2b is supposed to measure directly

`MURU_V2_G2_PARETO_STUDY_DESIGN.md:36-37`: "E2 replaces the inference in rows 2
and 3 with a direct measurement, and it does so by changing nothing except what
is written to disk." §2 title: "E2: full per-seed **Pareto front persistence**".
Line 70-73: "E2b, Held-out replay … The identical frozen search re-run on the
144 Held-out G2 cases **with front persistence enabled**."
`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json` E2 entry: `removes_observability_
bound: "WITHIN_SEED_PARETO_NOT_OBSERVABLE"`, `front_record_fields` (21 fields
including `score`, `loss`, `effective_support`, `template_key`) and
`scoring_pass_fields` (`g2_correct`, `support_status_vs_truth`,
`family_status_vs_truth`, …), metrics `P_front`, `P_retain_given_front`,
`P_win_given_retain`.

So the direct measurement is, per case: does any seed's **front** contain a
G2-correct row? If yes and it was not retained → retention-class. If no row on
any front is correct → generation-class. Hypothesis `H_partial` states the point
explicitly: "A material share of the `GENERATION` cases in fact have correct
rows on the front that never survived retention, meaning the decomposition's
57/69 split understates retention and overstates generation failure."

### 3. Denominator / population

144 G2 (`family_recovery`) held-out cases — plan `E2b.cases = 144`; sealed
`G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json` `denominator = 144`,
`population_source = registry.build_endpoint_population("family_recovery")`.
The comparison itself concerns the **126** cases in the two re-measured classes
(69 + 57); the other 18 (12 representation + 4 success + 2 cross-seed identity)
are "certain" and are not what E2 re-measures.

### 4. Case → category mapping

Partially frozen, and the frozen part matters:

- E2's own partition is 4-way: `SUCCESS | NEVER_ON_FRONT | LOST_IN_RETENTION |
  LOST_IN_CROSS_SEED` (plan `case_partition`), mapped onto pipeline stages A–E
  by `MURU_V2_E2_PREDECLARATION.md` §6.
- The v1 taxonomy is 5-way and includes `REPRESENTATION`, which E2's partition
  has no slot for. The study design resolves this by scoping the re-measurement
  to rows 2 and 3 only (line 36-37), leaving the 12 representation cases fixed.
- Because SUCCESS (4) and CROSS_SEED_IDENTITY (2) are decided by the same frozen
  `group_and_select` that the identity control has now reproduced exactly, the
  126-case pool is closed: retention + generation = 126 always, so
  `|Δretention| = |Δgeneration|`. Whether the tolerance is read per-number or
  jointly is therefore immaterial — a helpful accident, not a frozen rule.

What is **not** frozen anywhere: the row-level predicate for "a G2-correct row
is on the front" as applied to *held-out* cases (E2a's version is
`MURU_V2_E2_PREDECLARATION.md` §6's A–E sequence), and the per-seed vs per-case
aggregation ("in the majority of seeds" appears in `H_generate`'s wording but
not in the hook's).

### 5. The "materially contradicts" criterion

| Source | Text | Status |
|---|---|---|
| `MURU_V2_G2_PARETO_STUDY_DESIGN.md:193-199` (§2.9, primary) | "The decomposition predicts, on Held-out, **roughly** 69 retention-class and 57 generation-class cases. If E2b's direct measurement contradicts that split **materially** … every E4 ablation is suspended until the contradiction is resolved." | **no number** |
| `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json:411` / `.md:228` (primary) | "if E2b materially contradicts the decomposition's 69/57 retention-versus-generation split, ALL E4 ablations are suspended until resolved" | **no number** |
| `MURU_V2_CAUSAL_DECISION_TREE.md:188-190` (primary) | "contradicts the decomposition's 69/57 split **materially** … SUSPEND ALL E4 ABLATIONS until the contradiction is resolved. Republish the root-cause attribution first." | **no number** |
| `MURU_V2_G2_PARETO_STUDY_DESIGN.md:466` + `PLAN.json:1231-1232` (primary) | **PE2-4**: "E2b reproduces the decomposition's retention-versus-generation split **to within 10 cases of 69/57**." | a **prediction**, numerically pinned |
| `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` §4, as quoted verbatim in `MURU_V2_E2_ROUTING_LOCK_THEORY.md:37-41` | "IF E2b's direct measurement contradicts … **by more than 10 cases (PE2-4's own tolerance)** — THEN this protocol DOES NOT EXECUTE." | the **only** text that binds PE2-4's number to the hook — and it lives in the document proven unrecoverable |

**Answer to item 5/6:** every *primary* pre-result source states the hook
qualitatively ("materially") and never numerically. The only text converting
"materially" into "more than 10 cases" is the preregistration's §4, which
survives solely as a verbatim quotation inside a derivative document — the
document this audit series has established is not recoverable and has no
recorded digest, so it cannot be authenticated. PE2-4 is numerically pinned in
two primary sources, but it is registered as a *prediction*, and no primary text
elevates a prediction's tolerance into the hook's decision threshold.

**No tolerance, percentage rule, chi-square, effect size, confidence interval,
or "close enough" reading was invented here.**

### 7. Which artifact carries the hook verdict

**None is designated.** No frozen document names a report, file, or schema for
the hook's verdict. The nearest existing carriers are
`results/e2b_heldout/E2B_REPLAY_VERDICT.json`'s
`falsification_hook_not_evaluated` block (which records it as deliberately
uncomputed) and condition 2 of `MURU_V2_E4A_EXECUTION_GATE_CHECK.md`, which
consumes Gate 1's status. This audit adds a third record and no more.

### 8. Is E2b decision-admissible?

**No — explanatory only, mechanically enforced.** Plan E2 entry:
`decision_admissible: "E2a only"`; `populations.E2b.decision_admissible: false`,
`role: "explanatory only"`, `enforcement: "row-level
admissibility=DECISION_INADMISSIBLE plus a static citation checker"`.
`G2_PARETO_STUDY_DESIGN.md:76-86`: "No v2 threshold, retention rule, grammar
change, classifier change or benchmark change may be justified by E2b. E2b may
only corroborate or **contradict** a conclusion already reached on E2a."
This is coherent with Gate 1: the hook can only ever **suspend**, never license.

### 9. Does identity PASS validate the 69/57 split?

**No. They are logically separate tests, and the frozen documents place them in
different categories.**

- Identity is a **control**: plan E2 `controls[2]` — "E2b replayed retention
  must reproduce the sealed selection_count and representative for all 144
  cases; any case that does not is quarantined and reported";
  `G2_PARETO_STUDY_DESIGN.md:132-138` calls it "Replay fidelity for E2b" and
  §2.5 item 1 calls the sibling control "a hard gate before any E2 record is
  used."
- The hook is a **decision criterion**: plan E2 `decision_criterion.
  falsification_hook`.

Identity says *the replay is faithful, so its records may be used*. The hook
asks *what the fronts show about where correct structure was lost*. Passing the
first is a precondition for trusting the second, never a substitute for it.

---

## PHASE 2 — Evaluation of the hook

```
E2B_69_57_HOOK_NOT_OPERATIONALIZED
```

**This is neither PASS nor FAIL, and is not converted into either.** Two
independent bars, either one sufficient:

**Bar 1 — the criterion.** Per Phase 1 item 5: from primary pre-result authority
alone, "materially contradicts" carries no number. The 10-case tolerance is
bound to the hook only by the unrecoverable preregistration, quoted at second
hand. Issuing PASS or FAIL would require either adopting that unauthenticated
binding as decisive or inventing a threshold. Neither is permitted.

**Bar 2 — the input does not exist.** The hook consumes E2b's *direct
measurement*, which by frozen definition requires **front persistence**. It has
never been produced:

- The authoritative macOS replay computed, per case, only `selection_count`,
  `selection_denominator`, `selection_fraction`, and
  `representative_expression` (`scripts/run_e2b_macos_replay.py`,
  `replay_single_case`). No front rows, no `P_front`, no `score`/`loss`, no
  truth-joined scoring pass. It executed the **identity control**, correctly and
  completely — not the instrumented E2b the study design specifies.
- The earlier x86 replay likewise persisted only per-case match/mismatch
  (`results/e2b_heldout/replay_x86/e2b_log_shard_*.txt`).
- The sealed v1 evidence cannot supply it either — that is precisely
  `WITHIN_SEED_PARETO_NOT_OBSERVABLE`, the bound E2 exists to remove.

Consequently **no HISTORICAL vs E2B_DIRECT count table can be produced**.
Historical counts are recovered and stated above (69 / 57 / 12 / 4 / 2,
denominator 144, 126 in the re-measured pool). The E2b-direct column is not
"zero" or "unknown-but-estimable"; the measurement does not exist, and no
already-produced data substitutes for it. Producing it means running E2b again
with front persistence — new scientific compute, explicitly out of scope here
and not authorized by this audit.

The frozen FAIL consequence ("SUSPEND ALL E4 ABLATIONS", tree §B.1) is therefore
**not** applied: nothing has been shown to contradict the split.

---

## PHASE 3 — Gate 1 reconciliation

| Component | State | Authority |
|---|---|---|
| **A. Original-environment identity replay** | **PASS** — 144/144 exact, recomputed independently | plan E2 `controls[2]`; `G2_PARETO_STUDY_DESIGN.md:132-138`; `d6f607a` |
| **B. 69/57 falsification hook** | **UNRESOLVED — never evaluated** | plan E2 `decision_criterion.falsification_hook`; §2.9; tree §B.1 |

```
GATE1_STATE = PARTIAL — IDENTITY_PASS, HOOK_UNEVALUATED
```

**Not `GATE1_PASS`.** The frozen predicate's Gate 1 is the falsification hook
itself, not the replay-fidelity control: "IF E2b's direct measurement
contradicts … THEN this protocol DOES NOT EXECUTE" (prereg §4 as quoted in
`ROUTING_LOCK_THEORY.md:37-41`; tree §B.1). The identity control is the
precondition that makes E2b's records usable. Component A is now satisfied — a
real and material advance, and the harder of the two to obtain — but it does not
discharge component B, and this audit does not let it.

Honest statement of the residual: the hook is **unevaluated**, not failed. E4a
is blocked by the absence of a verdict, not by a negative one.

---

## PHASE 4 — Reconfirmation of prior findings against current HEAD

Every item re-verified at HEAD `62b4b55` + fetched refs. No finding changed.

| Established finding | Re-verification | Status |
|---|---|---|
| Gate 2 = `LOCKED_EXECUTE_E4A` | `X86_E2A_SEAL.json` `routing.state`, `r_remaining = 1` | unchanged |
| x86 E2a 540/540 accounted | seal: scheduled 540, completed 539, unresolved 1, accounted_for 540 | unchanged |
| literal fronts 539/540 | recounted `worlds_shard_*.jsonl` by `world_id`: **539** | unchanged |
| condition 3b requires literal 540 | `MURU_V2_E4A_CONDITION_3B_GOVERNANCE_AUDIT.md` verdict | unchanged |
| poison world identity | `V2C|E2|mass_power|c_low|n_default|r000`; absent from x86 corpus (verified) | unchanged |
| poison world OOMs on this host | `POISON_WORLD_DETERMINATION.json`, 4 independent kills | unchanged |
| historical ARM front exists, cannot be imported | `results/e2/run/`: **279** worlds, poison world **present**; seal `historical_worlds_merged: false`, freeze "no historical world is imported" | unchanged |
| no frozen path satisfies 3b | `MURU_V2_E4A_BLOCKER_RESOLUTION_AUDIT.md` Task C (6 routes) | unchanged |
| R0 requires `score` | `e4a_scoring.py:164`; synthetic control check | unchanged |
| R2 (mandatory) requires `score` | `e4a_scoring.py:183`; `PLAN.json:669` "top-k by score" | unchanged |
| x86 rows lack `score` | candidate row keys re-read: no `score` | unchanged |
| `loss` also absent → no reconstruction | candidate row keys re-read: no `loss`; `RawFrontRow` has neither | unchanged |
| R0/R2 unscoreable from the sealed x86 corpus | follows from the above | unchanged |
| R6 requires `score`; frozen status unresolved | `e4a_scoring.py:238`; R5/R6 absent from all primary sources | unchanged |
| R2 `k` / R4 `eps` authority missing | grids exist (`PLAN.json:669,671`); the registered value does not | unchanged |
| preregistration unrecovered | **re-run against the newly fetched refs**: `git rev-list --all --objects \| grep RETENTION_REMEDIATION` → 0 hits; `origin/exec/muru-heldout-a3-6` carries no `v2_design_reference/` at all; `f4c1105` still not a valid object | **still unrecovered** |

The new Mac branch is the v1 held-out lineage; it adds E2b replay artifacts and
the replay script, and contains no v2 design or preregistration material.

---

## PHASE 5 — Is E4a executable as frozen?

| # | Condition | State | Primary authority / reason |
|---|---|---|---|
| 1 | Routing authorization (Gate 2) | **PASS** | `X86_E2A_SEAL.json` `LOCKED_EXECUTE_E4A`, branch-1 margins 73 and 93 absorb `r_remaining = 1` adversarially; irreversibility proven in `ROUTING_LOCK_FREEZE.md` §3 |
| 2 | Gate 1 / E2b | **UNRESOLVED** | Identity component PASS (`d6f607a`, 144/144, verified here). Falsification hook never evaluated and not evaluable from existing data (Phase 2). Gate 1 is checked sequentially *before* Gate 2 |
| 3 | Balanced estimation sample | **PASS (not a prerequisite)** | `E4A_PREREQUISITE_VERIFICATION.md` §3 item 1 — a Rescue-v2-only construct |
| 3b | Full 540 population with fronts | **FAIL** | 539/540 literal fronts; `MURU_V2_E4A_CONDITION_3B_GOVERNANCE_AUDIT.md` |
| 4 | Corpus integrity | **PASS** | seal: 0 duplicates, 0 torn world/candidate/error records, 0 execution errors, 540 accounted, `world_id_set_sha256` recorded, per-file manifest. Disclosed caveat: the seal's own `SIMPLIFY_TIMEOUT` counter is dead (its ADDENDUM), superseded by `SIMPLIFY_TIMEOUT_AUDIT.json` |
| 5 | Control validity | **UNRESOLVED** | 81/81 recorded, but the only real-corpus control (`test_1_r0_replay`) resolves `OLD_RUN_DIR` to a non-existent path and self-skips **as a pass**, and skips again when rows lack `score`. Zero coverage against the authoritative corpus |
| 6 | Required scoring inputs | **FAIL** | `score` and `loss` absent from every sealed x86 row → R0 (control), R2 (mandatory), R6 all raise `InsufficientRowData`; no reconstruction without re-running searches |
| 7 | Frozen arm definitions / parameters | **UNRESOLVED** | R5/R6 attested by no primary source; the registered `k` and `eps` values live only in the unrecoverable preregistration |
| 8 | E4a execution manifest | **WAITING** | Not produced; deferred while 2, 3b and 6 are open |
| — | Dev/EVAL split frozen | **PASS** | `AMENDMENT_V1.md:26-28`; `e4a_scoring.py:89-90` |
| — | Equivalence-defect reachability | **PASS** | `MURU_V2_E4A_EQUIVALENCE_REACHABILITY_AUDIT.md` |
| — | Results-blind amendment frozen | **PASS** | `MURU_V2_E4A_RESULTS_BLIND_AMENDMENT_V1.md` |

```
E4A_NOT_EXECUTABLE_AS_FROZEN
```

Five independent conditions are open (2, 3b, 5, 6, 7), with 8 consequent. Any
one of 2, 3b or 6 alone is sufficient to block.

---

## PHASE 6 — Smallest justified next action

### Blocker classification

| # | Blocker | Class | Resolvable from existing evidence? |
|---|---|---|---|
| 1 | Gate 1's 69/57 hook unevaluated | **SCIENTIFIC** (needs the front-persisted E2b measurement) + **ARCHIVAL/GOVERNANCE** (the numeric binding of "materially" is unauthenticated) | **No** |
| 2 | Condition 3b: 1 missing front | **INFRASTRUCTURE** (a host that can run the world) + **GOVERNANCE** (admitting it to an x86-only corpus) | **No** |
| 3 | `score`/`loss` absent → R2 (and R6) unscoreable | **DATA_PROVENANCE** (irrecoverable without re-searching) | **No** |
| 4 | R0 unscoreable as implemented | **IMPLEMENTATION** (the argmax winner survives as `retained_by_argmax_score`; `e2_aggregate.evaluate_world:71` is the frozen precedent) | **Yes, in substance — but needs authorization to touch a sealed Step-4 artifact** |
| 5 | R5/R6 status, `k`, `eps` unknown | **ARCHIVAL** + **GOVERNANCE** | **No** (unless the preregistration is recovered from the Mac) |
| 6 | Preregistration unrecovered | **ARCHIVAL** | **Possibly — on the macOS machine, which is now demonstrably reachable by an operator** |
| 7 | Condition 5's self-skipping control | **IMPLEMENTATION** | **Yes**, once a scoreable corpus exists |

### Direct answers

**A. Does the successful macOS E2b replay eliminate the scientific Gate-1
blocker?** **Partially — it eliminates the component that was actually blocking
and leaves the other standing.** The replay-fidelity control is now PASS at
144/144 exact identity on the authoritative environment, which retires the
"E2b has never been validly executed" blocker and retires the cross-architecture
confound as an explanation. It does not touch the falsification hook, which has
never been evaluated anywhere. Gate 1 is not clear.

**B. Is condition 3b now purely governance/infrastructure?** **For the decision,
yes; for the execution, no.** No scientific definition is in dispute — the
world, its seeds, and its protocol are frozen and unchanged. What is missing is
a machine able to run it (infrastructure) and authority to admit its output into
an x86-only sealed corpus (governance). But *satisfying* 3b still means running
one world's 30 searches, which is new scientific compute and is not licensed
now.

**C. Is R0/R2 score loss irrecoverable from the homogeneous x86 corpus?**
**R2: yes, irrecoverable.** Ranks 2..k need per-row `score`; `score` is absent
and `loss` — the quantity it derives from — is absent too, so nothing can be
recomputed without re-running the searches. Same for R6. **R0: recoverable in
substance**, because the rank-1 argmax winner is persisted as the boolean
`retained_by_argmax_score`, computed at search time by the same frozen
`select_row_label`, and production's own `e2_aggregate` already reads the
retained row from exactly that flag — but rewiring `retain_r0` edits an artifact
sealed under condition 5, so it requires authorization, not an autonomous edit.

**D. Would a protocol-owner amendment be required to proceed?** **YES**, and for
more than one reason: condition 3b has no frozen-and-allowed route; R2/R6's
scoreability and the `k`/`eps` values cannot be settled from surviving sources;
and if the preregistration stays unrecovered, the hook's "materially" has no
authenticated numeric binding.

**E. Can an amendment be narrowly defined without changing observed scientific
outcomes?** **Yes — in principle, and the shape is visible without drafting it.**
Three of the four items touch no observed value: (i) an R0 input-source
clarification records that the same frozen rule is read from the persisted flag
rather than a recomputed score — the selected row is identical by construction;
(ii) a 3b ruling changes no A/B/C/D/E label, since the missing world has none and
routing already absorbs it adversarially with margins 73 and 93; (iii) recording
R2/R6 as unscoreable-on-this-corpus is a disclosed limitation on the arm set,
not a redefinition of any arm. Only the hook's binding is inherently a
scientific-criterion decision. **Not drafted here, as instructed.**

**F. Should M2/M3 remain blocked?** **Yes.** They sit downstream of E4a in the
frozen halt order that `CLOUD_X86_PARITY_QUALIFICATION.md:132-141` applied
verbatim ("no E4a, no M2/M3, no integration, no E6"), and E4a has neither run
nor been licensed.

**G. Should E6 remain blocked?** **Yes**, and for its own reason as well as the
chain's: E6 is the counterweight with veto over an *integrated* v2 candidate
(`MURU_V2_CAUSAL_DECISION_TREE.md` §3). No integrated candidate set exists or is
frozen, so E6 has nothing to evaluate. It stays blocked unless and until one is.

---

## FINAL REPORT

```
E2B_AUTHORITATIVE_REPLAY:
  commit:                 d6f607a (branch exec/muru-heldout-a3-6, parent 8d87143 = v1 run commit)
  environment_match:      MATCH -- macOS 26.1 / arm64 / Python 3.13.12 / lock 13b21b8c...c357fa8 /
                          run_commit 8d87143d; sealed evidence 482/482 re-hashed here;
                          SymbolicRegression.jl 1.11.3 satisfies the frozen "~1.11.0";
                          Julia was NEVER PINNED in the E2b manifest ("NOT_STARTED") -- a
                          pre-existing provenance gap, not a deviation by the replay
  cases:                  144 (denominator confirmed from the sealed G2 record)
  searches:               4,320 (144 x 30)
  selection_count_exact:  144/144   (recomputed here against the repo's sealed record)
  representative_exact:   144/144   (recomputed here)
  full_identity:          144/144   (recomputed here; 0 mismatches, 0 errors)
  decision:               E2B_PASS  (identity criterion only -- see the hook below)

69_57_HOOK_AUTHORITY:
  primary source(s):      MURU_V2_G2_PARETO_STUDY_DESIGN.md sect.2.9 (l.193-199) and l.466 (PE2-4);
                          MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json l.411 + l.1231-1232, .md l.228;
                          MURU_V2_CAUSAL_DECISION_TREE.md l.188-190;
                          MURU_V1_FAILURE_DECOMPOSITION.md sect.4.1, sect.6.2 (the counts)
  historical definition:  denominator 144. SELECTION_FAILURE 69 (= SELECTION_WITHIN_SEED_RETENTION),
                          SEARCH_GENERATION_FAILURE 57 (= GENERATION 45 + GENERATION_FAMILY 12),
                          GRAMMAR_REPRESENTABILITY 12, NONE_SUCCESS 4,
                          CANONICALIZATION_EQUIVALENCE_FAILURE 2. Both 69 and 57 are INFERENCES
                          under WITHIN_SEED_PARETO_NOT_OBSERVABLE, not observations.
  direct E2b definition:  the same frozen search replayed on the 144 held-out cases WITH FULL
                          PER-SEED FRONT PERSISTENCE, plus the truth-joined scoring pass; a case is
                          retention-class if a G2-correct row is on some seed's front but was not
                          retained, generation-class if no front carries a correct row.
  material_contradiction: "materially" -- undefined in every primary source. PE2-4 pins "within 10
                          cases of 69/57" but is registered as a PREDICTION; the only text binding
                          that number to the hook is the preregistration sect.4, which survives only
                          as a second-hand quotation and remains unrecoverable/unauthenticatable.
  criterion operationalized: NO (from primary authority alone)

69_57_HOOK_RESULT:
  historical counts:      69 retention / 57 generation / 12 representation / 4 success /
                          2 canonicalization; denominator 144; re-measured pool 126
  E2b direct counts:      NOT PRODUCED. The authoritative replay persisted only per-case
                          selection_count and representative; no fronts, no P_front, no scoring
                          pass. The x86 replay likewise. The sealed v1 evidence cannot supply it --
                          that is the very bound E2 exists to remove.
  verdict:                E2B_69_57_HOOK_NOT_OPERATIONALIZED
                          (explicitly NOT converted to PASS or FAIL; the frozen suspension
                          consequence is NOT triggered, because nothing has been shown to
                          contradict the split)

GATE1_FINAL_STATE:        PARTIAL -- IDENTITY_PASS (144/144, authoritative environment),
                          HOOK_UNEVALUATED. Not GATE1_PASS.

GATE2_FINAL_STATE:        LOCKED_EXECUTE_E4A -- unchanged, irreversible, Gate 2 only.

E4A_GATE_MATRIX:
  1  routing authorization ............ PASS
  2  Gate 1 / E2b ..................... UNRESOLVED  (identity PASS, hook unevaluated)
  3  balanced sample .................. PASS (proven not a prerequisite)
  3b full 540 population with fronts .. FAIL        (539/540)
  4  corpus integrity ................. PASS
  5  control validity ................. UNRESOLVED  (real-corpus control self-skips)
  6  required scoring inputs .......... FAIL        (score and loss absent -> R0, R2, R6)
  7  frozen arm definitions/params .... UNRESOLVED  (R5/R6 status; k, eps)
  8  execution-gate artifact .......... WAITING     (consequent on 2, 3b, 6)

E4A_EXECUTABLE_AS_FROZEN: NO

REMAINING_BLOCKERS:
  1. Gate 1's 69/57 falsification hook: never evaluated; requires an E2b run WITH front
     persistence, and an authenticated binding for "materially".
  2. Condition 3b: 539/540 literal fronts; no frozen-and-allowed route to the 540th.
  3. Condition 6: score (and loss) absent from the sealed x86 corpus -> R0, R2, R6 unscoreable.
  4. Condition 7: R5/R6 arm status and the registered k / eps values are unrecoverable.
  5. Condition 5: the only real-corpus control self-skips as a pass on this corpus.
  6. Condition 8: the execution manifest, consequent on the above.
  7. Archival: MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md still unrecovered (re-searched
     against the newly fetched refs).

BLOCKER_CLASSIFICATION:
  SCIENTIFIC ........ 1 (hook measurement)
  DATA_PROVENANCE ... 3 (score/loss irrecoverable for R2/R6)
  IMPLEMENTATION .... 3 (R0 rewiring), 5 (control path)
  ARCHIVAL .......... 4, 7 (and the hook's numeric binding)
  GOVERNANCE ........ 1, 2, 4 (rulings only an owner may make)
  INFRASTRUCTURE .... 2 (a host that can run the poison world)

NEW_SCIENTIFIC_COMPUTE_REQUIRED_NOW:  NO
    Nothing is licensed to run now. Note for planning, not a licence: two blockers can only ever
    be cleared by compute later -- the front-persisted E2b measurement, and the poison world's
    30 searches -- and R2/R6 would additionally need the E2a searches re-run to recover `score`.

PROTOCOL_OWNER_ACTION_REQUIRED:  YES

SMALLEST_JUSTIFIED_NEXT_ACTION:
    Commit and push this audit, and put five items to the protocol owner in one pass:
      (i)   Gate 1 -- authorize (or refuse) an E2b re-run WITH front persistence, the only way to
            produce the hook's input; and rule on how "materially" is bound if the preregistration
            is not recovered.
      (ii)  Recover the preregistration from the macOS machine, now demonstrably operator-reachable.
            It is the single artifact that would close items (i), (iv) and part of 3b at once.
      (iii) Condition 3b -- choose among the frozen-but-ungoverned routes (same-instance expansion,
            cross-host qualified execution, or a ruling), or rule that E4a does not proceed.
      (iv)  Conditions 6 and 7 -- authorize or refuse the R0 rewiring to `retained_by_argmax_score`;
            rule on R2/R6 given that their ranking key cannot be recovered without re-searching.
      (v)   Confirm M2/M3, integration and E6 remain blocked (they do, and nothing here changes it).
    No scientific file, frozen definition, or sealed artifact is touched by any of this.

UPDATED_DEPENDENCY_GRAPH:
    E2a x86 (SEALED, 539/540 fronts, 540 accounted)
      |
      +--> Gate 2 routing ............ LOCKED_EXECUTE_E4A  [DONE, irreversible]
      |
      +--> condition 3b (540th front) ..... BLOCKED --+
                                                      |
    E2b identity replay (macOS/ARM64) . PASS 144/144 --+
      |                                                |
      +--> E2b hook measurement (front persistence) ...+--> Gate 1 ... UNRESOLVED
             [NOT RUN -- requires authorization]       |
                                                       |
    E4a scoring inputs (score/loss) ... ABSENT --------+
    E4a arm definitions (R5/R6, k, eps)  UNRESOLVED ---+
                                                       |
                                                       v
                                            E4a ... NOT EXECUTABLE
                                                       |
                                                       v
                                            M2 / M3 ... BLOCKED
                                                       |
                                                       v
                                    integrated v2 candidate ... does not exist
                                                       |
                                                       v
                                            E6 ... BLOCKED (nothing to evaluate)
```

## Provenance

| Field | Value |
|---|---|
| Audit date (UTC) | 2026-08-18 |
| Repository / branch | `MURU-ConjectureLab-v1`, `claude/e2-rescue-v2-computational` |
| Refs read | HEAD `62b4b55`; `origin/exec/muru-heldout-a3-6` tip `d6f607a` (read via `git show`, not checked out) |
| Independent recomputations | 482/482 sealed-file hashes; 144/144 sealed source-record hashes; 144/144 selection_count and representative; manifest canonical digest; 539 x86 fronts; 279 historical worlds; candidate-row schema |
| Frozen documents amended | None |
| Waivers created | None |
| Thresholds invented | None |
| Experiments executed | None (E4a, M2/M3, integration, E6, E2a, E2b: all untouched) |
