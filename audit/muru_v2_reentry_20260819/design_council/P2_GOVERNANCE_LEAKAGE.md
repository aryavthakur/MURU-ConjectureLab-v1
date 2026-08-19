# P2 — GOVERNANCE / LEAKAGE ADVERSARY

**Role.** Pre-emptive hostile attack on the class of designs that could be proposed
for the replacement calibration/re-entry experiment. This document does **not**
design an experiment. It defines the traps and issues binding constraints.

**Standing.** Written results-blind with respect to any new scientific outcome. No
new scientific compute was performed. Two read-only integrity audits over already
sealed artifacts were performed (§1.6, §1.7); they create no new scientific evidence
and license nothing.

**Posture.** Adversarial. Every constraint below assumes the designer is under
pressure to reach re-entry and will take the cheapest path that survives review.

---

## 0. VERDICT SUMMARY (read this if you read nothing else)

| # | Question | Ruling |
|---|---|---|
| R1 | Is "qualify a synthetic surface by reproducing E2b, then route from it" non-circular? | **NO. INADMISSIBLE as stated.** Survives only under the extreme discipline of §2.5, which no realistic design will meet. |
| R2 | Is "qualification criterion = matches E2b's dominant mechanism" admissible? | **NO. Categorically inadmissible.** Conditional on qualification the route becomes a deterministic function of E2b. |
| R3 | Can an x86 Linux surface be decision-admissible for this endpoint? | **YES, but only for a decision computed entirely *within* the surface**, with a host-independent classifier. **NO** for any quantitative Held-out-matching qualification. |
| R4 | Is a determinacy-bound classifier a prohibited semantic change? | **MANDATORY CORRECTION**, under the six conditions in §3.2. |
| R5 | Is T9 (architecture execution boundary) forced? | **Not by internal validity. YES and unavoidably, if Held-out-matching qualification is retained as a requirement.** |
| R6 | Is E2a tainted beyond the ratified D5 invalidation? | **YES — new, quantified, and material.** See §1.6/§1.7. Recommend a new decision **D7**. |
| R7 | Is a defensible qualification possible at all? | **Not by Held-out matching.** A narrow internal-validity qualification is defensible but has low prior probability of reaching re-entry, and one cheap prerequisite (§11.2) must be discharged before any surface is commissioned. |

---

## 1. EVIDENCE I VERIFIED MYSELF

### 1.1 The sealed result
`GATE_1 = FAIL`, `GATE_1_DEFINITIVE = YES`, `E2B_IDENTITY = PASS`, both critics PASS.
Direct classes over 144 Held-out cases: `LOST_IN_CROSS_SEED` 71, `LOST_IN_RETENTION` 55,
`NEVER_ON_FRONT` 14, `SUCCESS` 4. `DIRECT_RETENTION` 55 vs 69 → dev 14;
`DIRECT_GENERATION` 14 vs 57 → dev 43. Frozen tolerance: strictly more than 10 cases.
124 of 144 cases relabelled relative to v1.
(`audit/e2b_definitive_cloud_adjudication_20260818/{GATE_1_DEFINITIVE.md,FINAL_TERMINAL_REPORT.md}`)

### 1.2 The frozen invalidation rule, verbatim
`befca0d` §2.3: *"**If E2a and E2b disagree**, that is itself a finding and it blocks
adoption of any E4 conclusion until explained. Divergence would mean the fresh worlds
do not reproduce the Held-out regime, **which invalidates E2a as a calibration surface.**"*

Note precisely what this sentence is: a **one-way destructive rule**. It says
disagreement invalidates. It does **not** say agreement validates. Every design that
treats agreement as qualification is affirming the consequent of a frozen rule that was
never written to license anything.

### 1.3 The inadmissibility, verbatim
`befca0d` §2.3: *"**E2b outputs are `DECISION_INADMISSIBLE`.** No v2 threshold, retention
rule, grammar change, classifier change or benchmark change may be justified by E2b.
E2b may only corroborate or contradict a conclusion **already reached on E2a**."*

Enforced mechanically by design: row-level `admissibility` field, mandatory experiment-ID
citation on every proposed change, and a **static citation checker that rejects any change
whose supporting set contains an E2b identifier and no E2a identifier.**

### 1.4 The ratified owner decisions
D5: E2a is **INVALIDATED AS A HELD-OUT-FACING CALIBRATION SURFACE**; `LOCKED_EXECUTE_E4A`
has **no forward-licensing force**; the `B` plurality may **not** be cited to license E4a.
D6: any new decision-relevant corpus must satisfy the frozen required schema **from
inception**; no retroactive field fabrication; no silent waiver; where a corpus lacks
needed fields, **regenerate prospectively**.
D2-ext: no automatic E4 re-entry. `EXPERIMENTAL_REENTRY_RESOLUTION` requires all eight
items, of which 1–7 are protocol construction and 8 is successful execution.
(`audit/muru_v2_reentry_20260819/MURU_V2_PROTOCOL_OWNER_RATIFICATION.md`)

### 1.5 Completed experiments that already constrain the route
`E3` (`1d20731`, audited `94abf97`) is COMPLETE:
`mass_affine_descriptor` **MARGINAL** (bic_rate 0.553, `search_side_attribution_licensed: false`);
`mass_exponential_descriptor` **MARGINAL** (0.527, licensed false);
`mass_saturating_descriptor` **IDENTIFIABLE** (0.820); `mass_interaction` **IDENTIFIABLE** (1.000).
Study validity: BIC `false_structure_oracle_rate` 0.095 → `VALID_NARROW` (clears the >0.10
bar by 0.005); the R² variant 0.685 → `STUDY_INVALID`, excluded from all licensing.
E0 and E1 COMPLETE; E1 = "no pair admissible, H3, no v2 change licensed". E6 self-blocked.
**Consequence:** a `NEVER_ON_FRONT`-dominant route is already half-dead on arrival — two of
five families cannot support search-side attribution, and the E3 validity margin is 0.005.

### 1.6 NEW FINDING A — the sealed E2a timeout counter is structurally dead
`results/e2/run_x86_e2a_v1/X86_E2A_SEAL.json` reports
`scientific_timeouts_simplify_timeout_rows: 0` and `worlds_containing_simplify_timeout: 0`.
**Both numbers are meaningless.** The run's own audit says so verbatim
(`SIMPLIFY_TIMEOUT_AUDIT.json`):

> *"candidates_shard_*.jsonl carries structural fields only and never a
> canonicalization_status column, so seal_x86_e2a.py's own SIMPLIFY_TIMEOUT counter is
> **structurally dead and always reports 0**."*

I confirmed this directly: all **189,467** persisted candidate rows carry
`classified: false` and exactly 16 fields —
`world_id, cell_id, family, regime, noise_level, replicate, seed_ordinal_k, seed,
front_rank, expression_string, engine_complexity, valid_r2, invalid_fraction, test_r2,
retained_by_argmax_score, classified`.
**No `score`. No `loss`. No `g2_correct`. No `canonicalization_status`. No `admissibility`.**

The true timeout rate lives only in an out-of-tree sqlite cache
(`/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3`): **397 of 52,450 distinct
expressions (0.757%) returned `SIMPLIFY_TIMEOUT`** under the frozen classifier version
`90a3b5ea…7089e7a`.

**Governance consequence:** the sealed decision-admissible corpus cannot be audited
row-wise for the defect that decided part of its own attribution. That is a D6-class
schema failure inside the corpus that D5 already demoted, and it is not the same defect
D5 addressed.

### 1.7 NEW FINDING B — E2a's stage-A attribution is provably decided by a wall-clock timer
`lazy_classify.py:186` hard-codes:

```
if not (classification.parse_ok and classification.canonicalization_status == "OK"):
    return False          # <-- SIMPLIFY_TIMEOUT becomes "not G2-correct"
```

A timed-out expression is therefore **silently consumed as evidence of absence**. The
frozen A–E order (`E2_PREDECLARATION` §6) is
`A if n_correct_on_front == 0`, so every timed-out row pushes a world **toward A**, and
never away from it. The distortion is **monotone in one direction**: A and B are inflated,
C+D and E are deflated.

I joined the timeout expression set against the sealed corpus. Exposure by sealed stage:

| Sealed stage | Worlds with ≥1 timed-out front row | Timed-out rows | Witness path |
|---|---|---|---|
| **A** (`NEVER_ON_FRONT`) | **73 / 122 = 59.8%** | 314 | `PHASE2_FULL_SCAN_A` |
| B (`LOST_IN_RETENTION`) | 20 / 196 = 10.2% | 78 | `PHASE2_FRONT_SCAN_B` |
| C (`LOST_IN_CROSS_SEED`) | 3 / 102 = 2.9% | 3 | `PHASE1_RETAINED_ONLY` |
| E (`SUCCESS`) | 1 / 119 = 0.8% | 1 | `PHASE1_RETAINED_ONLY` |

For stage A this exposure is **exact, not an upper bound**: for all 122 A-worlds
`n_classify_calls == n_persisted_rows` exactly (difference min = median = max = 0), i.e.
the full scan classified **every** front row, so every one of those 314 timed-out rows
was consumed as `False` in the A determination.

**Worst-case correction bound.** Correcting the defect can only move worlds *out of* A and
*out of* B. Upper bound: A → 122−73 = **49** (9.1% of 539); B → 196−20 = **176**;
C+D → 102+93 = **195**. Under that bound the frozen Gate 2 predicate
`B > A AND B > C+D` **fails**, and the plurality flips from `B` (retention) to `C+D`
(cross-seed) — **which is exactly E2b's finding.**

I state the bound honestly: it is a worst case, it assumes every exposed world flips
maximally, and it is not a measurement of the true corrected attribution. But it is
sufficient to establish three things that are not currently on the record:

1. E2a's `A = 122` is an **upper bound**, not a measurement.
2. `LOCKED_EXECUTE_E4A` is **not robust** to correction of a known instrument defect.
3. **The E2a/E2b divergence has a live, cheap-to-test, mundane explanation — an
   instrument asymmetry — that has never been controlled for.** E2a let a 5-second timer
   decide labels; the sealed E2b adjudication used a determinacy bound under which a cap
   can never decide. The two surfaces were never measured with the same instrument.

The corrected-A upper-bound range (9.1%–22.6%) **brackets E2b's `NEVER_ON_FRONT` share of
9.7%** at its lower end. That is not proof. It is enough to forbid commissioning a
540-world re-run until the hypothesis is discharged (see BC-0).

### 1.8 The x86 parity artifact — what it established and what it did not
`results/e2/cloud_x86_parity/CLOUD_X86_PARITY_QUALIFICATION.json`,
`verdict: NEW_CLOUD_HOST_PARITY_FAILED`, `PARITY_PASS: false`.

**ESTABLISHED:**
- Environment reconstruction `EXACT`: python 3.13.5, sympy 1.14.0, julia 1.12.6,
  pysr 1.5.10, symbolic_regression.jl 1.11.3; `dependency_lock_deviations: 0` over 50
  entries; julia manifest unchanged after instantiate; `classifier_version` byte-matches
  the ARM host; classify cache seed matches ARM exactly (143,232 rows / 119,448 distinct);
  single-threaded env pinned.
- **x86 internal determinism**: `N_DETERMINISM_CHECKED 30`, `N_DETERMINISM_MATCH 30`,
  `DETERMINISM_PASS: true`.
- **Instrumentation neutrality on x86**: `tests/test_raw_search_identity.py` PASS — every
  structural field byte-identical between `e2_search.run_seed_search` and
  `raw_search.run_seed_search_raw` **on x86_64**.
- Corpus reconciliation: 31/31 authoritative files match, 530 completed worlds,
  0 duplicates, 0 torn records.

**NOT ESTABLISHED — and this is the load-bearing half:**
- **Cross-architecture SEARCH equivalence.** `worlds_executed_on_this_host: 0`. The audit
  replayed sealed ARM candidate rows through the x86 *classifier*. It never re-ran PySR on
  x86 and compared fronts to ARM fronts. The bridge test compares **two x86 code paths to
  each other**, not x86 to ARM. There is no measurement anywhere in the corpus of how far
  an x86 front differs from an ARM front for the same world and seed.
- **Cross-architecture LABEL equivalence.** The one comparison actually attempted **FAILED**:
  1 confirmed scientific mismatch on `first_loss_stage` — explicitly *"a routing/gate-relevant
  field consumed by Gate 2 of the frozen E4a routing rule"*. Root cause, verbatim:
  *"SIMPLIFY_TIMEOUT_SECONDS = 5 is a WALL-CLOCK budget. The faster x86_64 host completes a
  sympy canonicalization that the slower ARM64/macOS host abandoned, so the same unmodified
  classifier assigns a different scientific label to the same expression purely as a function
  of host speed."* `not_floating_point: true`.
- **The magnitude of the divergence.** 834 `SIMPLIFY_TIMEOUT` rows across 237/530 worlds
  (44.7%); the artifact states the 1/530 mismatch **is a lower bound** because the lazy replay
  short-circuits and never classifies most timeout-affected rows. 2 further worlds unresolved
  (still timing out at 600 s), so conclusive coverage is 528/530.

### 1.9 No ARM/macOS host is reachable
`uname -m` = `x86_64`. Commit `7035215`: *"E2b original-environment replay: FAILED_TO_EXECUTE
— no macOS/ARM64 host reachable."* Commit `93d8e98`: *"identity criterion not evaluable
cross-architecture."*

### 1.10 E4f has no operational freeze
`FORWARD_AUTHORITY_MAP.md` §6: E4f has **no** standalone preregistration, **no** numeric
`false_labelling_rate` ceiling anywhere in the corpus, **no** `k_inflation` ceiling,
**no** population declaration, **no** DEV/EVAL split, **no** statistical procedure, and
**no** identity/replay control. It is *"not executable as frozen authority stands."*
This matters because the cross-seed route — the one E2b points at — terminates in E4f.

---

## 2. RULING 1 — THE CENTRAL CIRCULARITY

### 2.1 The attacked design
> *Generate a new synthetic surface S. Qualify S by checking it reproduces the Held-out
> (E2b) attribution. Route from the qualified S.*

### 2.2 Is E2b-as-one-way-falsifier genuinely non-circular?
Only under conditions that no realistic design will meet, and **not** as usually stated.

The frozen §2.3 rule is destructive-only: disagreement invalidates. It attaches **no**
positive force to agreement. A design that says "S is qualified because it agrees with
E2b" has silently upgraded a veto into a **selector**. A selector over surfaces is a
licensing instrument: it decides which surface's attribution gets to route the programme.
That is precisely what `DECISION_INADMISSIBLE` forbids, and it defeats the frozen static
citation checker by laundering the E2b identifier out of the change's citation set and
into the *admissibility* of the corpus the change cites.

Formally, write the route as `route = f(S)` and qualification as `q(S, E2b) ∈ {pass, void}`.
Non-circularity requires that, **conditional on `q = pass`**, `route` retains variance that
is not a function of E2b. Two things destroy that:

- **Retry.** If the analyst may generate `S₁, S₂, …` and keep the first that qualifies,
  E2b is the objective function of a search over surfaces. Leakage is not bounded; it grows
  with the number of attempts. One qualifying surface out of N attempts is a fitted surface.
- **Statistic collision.** If `q` is keyed to the same statistic `f` reads, then conditional
  on `pass` the route is constant and equal to E2b's. Variance is zero. See §2.4.

### 2.3 Where is the line between "designing to reproduce the regime" and "tuning until it matches"? — an operational test
The distinction is **not** about intent and cannot be adjudicated by reading a rationale.
It is about **information flow and commit order**, and it is fully mechanical. I propose the
**Generator Immutability + Single-Shot Test** (five parts; all five must pass):

| # | Test | How it is checked |
|---|---|---|
| T-a | **Ancestry.** Every generator parameter (families, coefficient ladder, noise ladder, replicate count, seed band, `world_ordinal` formula, `PYSR_CONFIG`, `GRAMMAR_VERSION`, seeds-per-case) is bit-identical to a value already fixed in a commit that is a **strict ancestor** of the first commit containing any E2b front. | `git merge-base --is-ancestor <spec-commit> <e2b-commit>` and a field-by-field diff. A parameter that postdates the observation cannot have been chosen independently of it. |
| T-b | **No orphan constants.** Any parameter that cannot satisfy T-a must be set by a *rule* that provably never reads Held-out (e.g. "unchanged from v1 production", "the value E2a already used"), and the rule — not the value — is what is registered. | Static review of the rule; the value is derived, not chosen. |
| T-c | **Single shot.** Exactly **one** surface is generated. The number of generated surfaces is an auditable integer. `N > 1` with any Held-out comparison performed between attempts is fitting, without exception and without a rehabilitation path. | Count of surface manifests in the repository; commit history. |
| T-d | **Route-before-veto.** The route is computed and hash-sealed **from S alone**, in a commit that is a **strict ancestor** of the first commit containing any Held-out comparison artifact. | `git merge-base --is-ancestor <route-commit> <comparison-commit>`; hashes in both. |
| T-e | **Empty tuning ledger.** A pre-registered ledger records every parameter changed after the frozen spec, the reason, and the evidence consulted. It must be **empty**. A non-empty ledger is not a disclosure that rehabilitates the design; it is the measurement of how much fitting occurred. | The ledger file itself. |

T-d is the decisive one and it is the cheapest to enforce. If the route is sealed before the
comparison exists, E2b can only destroy the run; it cannot select the route. If the
comparison runs first, the route is conditioned on its outcome no matter what the protocol
text claims.

### 2.4 Is "qualification = matches E2b's dominant mechanism" admissible? — **NO**
**Categorically inadmissible.** If `q` requires `dominant_mechanism(S) == dominant_mechanism(E2b)`
and `route` is keyed to `dominant_mechanism(S)`, then conditional on qualification
`route ≡ dominant_mechanism(E2b)`. The routing decision is then a **deterministic function of
E2b with zero residual variance**. Every intervening step — the 540 worlds, the 16,200
searches, the CPU-hours — is decoration on a lookup of an inadmissible corpus. This is the
purest form of the laundering the design's own static citation checker exists to prevent, and
it would be more honest, and cheaper, to simply declare that the programme is routing off E2b.

This yields a general, testable rule (BC-9): **the qualification statistic and the routing
statistic must be different functions, and the qualification statistic may not be a monotone
function of the routing variable.** Note the synonyms that violate it: `P_front` is essentially
the complement of stage A; `P_retain_given_front` determines the B/{C,D,E} split; the
`SUCCESS` rate is stage E. Any of these smuggles the routing variable back in.

### 2.5 The narrow survivor
The only qualification shape I would not veto on circularity grounds is:

> qualification is keyed **exclusively to instrument correctness and internal validity**
> (does the surface measure the attribution without letting a cap decide? does the R0 replay
> reproduce? do the known-answer and negative controls recover?), the route is a predeclared
> mechanical function of the surface's **own** attribution, sealed before any Held-out
> artifact exists, and the Held-out comparison is executed **once**, afterwards, as a
> **pure veto whose only permitted outcomes are VOID or SILENT**.

"Silent" is load-bearing: a passing veto must be reported as *"the falsification hook did not
trip"* and must **never** appear in the citation set of any downstream change. If the design
cites the passing veto as support, it has converted it into a licence and BC-9 is violated.

### 2.6 The strongest case for the negative terminal (argued at full strength)
I am obliged to argue this at its strongest, and I find it stronger than the survivor.

Under §2.3 as frozen, exactly two things can happen to any new surface S that is compared
to Held-out:

- **S disagrees with Held-out.** §2.3 fires verbatim: the fresh worlds do not reproduce the
  Held-out regime, S is invalidated as a calibration surface. Identical outcome to E2a.
  No route. Terminal.
- **S agrees with Held-out.** S survives, but agreement licenses nothing (§2.2). The route
  then comes from S's own attribution — which, by construction of the agreement, **is**
  E2b's attribution. The route is observationally indistinguishable from routing off an
  inadmissible corpus, and a hostile reviewer will say so correctly.

So under Held-out-matching qualification, **no synthetic surface can ever positively license
a route that differs from E2b's, and any route that matches E2b's cannot be distinguished
from E2b's.** The family of designs is structurally incapable of producing a
decision-admissible route. This is not a defect in any particular proposal; it is a property
of combining §2.3's destructive-only rule with D6's inadmissibility.

The §2.5 survivor escapes only by making qualification independent of the routing variable —
and here the dilemma closes:

> **A qualification criterion strong enough to establish that the surface reproduces the
> Held-out *regime* is necessarily keyed to the attribution, and is therefore circular. A
> criterion weak enough to avoid the attribution is too weak to establish regime fidelity,
> and therefore qualifies nothing.**

Front-size distributions, complexity distributions and `valid_r2` marginals can match while
the attribution regime is entirely different. A qualification that passes almost anything is
not a qualification; it is a ceremony. I do not see a third option, and I have looked for one.

**Therefore:** the honest reading is that "generate a surface and qualify it against Held-out"
is **dead**, and the live question is whether an *internal-validity* qualification (§2.5) with
a **silent** veto is enough for the protocol owner. That is a governance question about how
much evidential weight a route may carry, not a scientific one — and it must be answered by
the owner, in writing, **before** any design is written, because the answer determines whether
there is anything to design.

---

## 3. RULING 2 — ARCHITECTURE

### 3.1 The precise parity ruling
The x86 parity artifact establishes **environment identity, x86 internal determinism, and
x86-internal instrumentation neutrality**. It establishes **no cross-architecture scientific
equivalence of any kind** — not of search, not of labels. The single cross-host comparison it
attempted **failed**, on a routing-relevant field, with a stated lower-bound caveat and 44.7%
exposure. `worlds_executed_on_this_host: 0` is the sentence that settles it: no front produced
on x86 has ever been compared to a front produced on ARM for the same world and seed.

### 3.2 Q1 — determinacy-bound classifier: prohibited change or mandatory correction? — **MANDATORY CORRECTION**
`befca0d` §2.10 prospectively mandates a per-expression wall-clock cap **and** forbids the
timeout *"silently becoming `None`"*. The sealed E2a pipeline satisfies the letter (the status
is recorded in a cache) and violates the substance: `lazy_classify.py:186` converts
`SIMPLIFY_TIMEOUT` to `g2_correct = False` and the **cap decides the label** (§1.7). §1.6/§1.7
demonstrate that this is not hypothetical — it decided 314 row labels inside 73 of 122 stage-A
worlds, in the direction that determines the stage.

The determinacy bound does not alter the *definition* of G2-correctness. `g2_contract` is
untouched. It alters only whether a label is emitted while the definition's value is unknown,
and it is **strictly conservative**: it can refuse to decide, never decide differently. It is a
correction of an instrument defect, not a semantic change, and mandating it is required rather
than merely permitted.

**Six binding conditions on that correction** (all six, or it is a semantic change after all):
1. `g2_contract.py` and the classification **semantics** are byte-unchanged; only the control
   flow around unresolved rows changes.
2. The bound is proven to **over-approximate**: a class is emitted only when it is invariant
   over *every* resolution of every unresolved row.
3. Rows that are decisive under that enumeration are **escalated to completion**, not guessed.
4. A residual undecidable case is emitted as an explicit `UNRESOLVED` class — never folded into
   any substantive class — with a predeclared maximum `UNRESOLVED` fraction above which the
   entire run is **VOID** (BC-13).
5. The implementation is validated against **uncapped** ground truth on a predeclared sample,
   with the sample and the pass bar frozen before execution.
6. The whole correction is hash-frozen before any new world is generated, and it applies
   **identically** to every surface any comparison touches.

The precedent exists and was hostile-audited: the sealed Gate 1 adjudication used exactly this
bound (140/144 invariant outright; 4 cases hinging on 6 expressions escalated to completion;
101/101 against uncapped ground truth; 158/51,411 = 0.31% rows unresolved at the cap).

**Corollary — a hidden variable nobody has registered.** Under a wall-clock cap, **worker count,
machine load, and CPU model are scientific variables**: they change labels. `WORKER_COUNT_CALIBRATION.json`
exists in the sealed E2a run directory and was treated as an engineering artifact. It was not.
Either the determinacy bound removes the dependence, or worker count and host load must be
frozen and load-isolated and declared as scientific parameters. There is no third option, and
the first is obviously correct.

### 3.3 Q2 — does a fresh x86 surface need cross-architecture search equivalence? — **NO for internal validity; YES for any cross-host comparison**
The routing decision under §2.5 is a **within-surface** comparison: which stage is the plurality
on this surface, measured by one instrument, on one host, under one frozen configuration.
Nothing in that statement references ARM. x86 determinism is demonstrated (30/30), the
environment is reconstructed exactly with a verified dependency lock, and instrumentation
neutrality is demonstrated on x86. **A fresh x86 surface is decision-admissible for a
within-surface routing decision** provided BC-11 (host-independent classifier) holds.

The moment the protocol asserts a **numeric relation between the x86 surface and the macOS/ARM64
Held-out corpus**, it makes a cross-architecture scientific claim that no artifact in this
repository supports and one artifact actively contradicts. The unquantified quantity is the
front-level delta between an x86 search and an ARM search — never measured, because zero worlds
were ever executed on both.

**Ruling:** x86 Linux **is** admissible for a fresh calibration surface whose decision is
computed entirely within itself. x86 Linux is **not** admissible for a quantitative
Held-out-matching qualification. Note that this is an **independent** kill-shot on the design
family already killed in §2: that family dies on circularity *and* dies on architecture, and
removing either objection does not save it.

### 3.4 Q3 — is T9 forced? — **Not by internal validity. Yes, if Held-out matching is retained.**
I will not shade this. If the protocol owner requires that the replacement surface be
**numerically qualified against the macOS/ARM64 Held-out corpus**, then cross-architecture
search equivalence is a precondition of that comparison; establishing it requires executing
worlds on a macOS/ARM64 host; no such host is reachable (§1.9); and the honest terminal is

> **T9 — REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY.**

I would rule T9 in that case without hesitation and would treat any attempt to substitute a
weaker comparison ("compare only the ordering", "compare only the plurality") as an
unregistered relaxation of the qualification requirement — which is threshold tuning by
another name (PM-6).

The only way T9 is avoided is by **abandoning Held-out-matching qualification entirely**,
which §2.6 concludes is required on independent grounds anyway.

### 3.5 Q4 — does the timeout exposure taint E2a beyond D5? — **YES, and it is a separate defect**
Two corrections to the framing:

- The 44.7% figure is the **ARM** E2a corpus. The corpus that produced the ratified attribution
  `A=122 B=196 C=102 D=0 E=119` and `LOCKED_EXECUTE_E4A` is the **x86-only** corpus
  (`corpus_is_x86_only: true`, `historical_worlds_merged: false`, 539 worlds).
- That corpus's own timeout counter reads 0 and is **structurally dead** (§1.6). The real x86
  figure is 397/52,450 distinct expressions, and the exposure is 20× concentrated in the stage
  the mechanism biases toward (§1.7).

So: **yes.** E2a's attribution is partly an artifact of a 5-second timer; the corpus cannot be
audited row-wise for it; the worst-case correction reverses the Gate 2 plurality from `B` to
`C+D`, i.e. **toward E2b**; and the E2a/E2b divergence has never been controlled for the one
methodological asymmetry that provably exists between the two surfaces — E2a let a cap decide,
E2b did not.

This is **not** the defect D5 ratified. D5 is a ruling on *role* ("invalidated as a Held-out-facing
calibration surface", data not repudiated). This is a ruling on *measurement validity*: part of
the attribution is instrument output, not pipeline behaviour. I recommend the protocol owner
issue a new decision:

> **D7 — the sealed E2a attribution is INSTRUMENT-CONTAMINATED.** `A = 122` is an upper bound.
> The corpus lacks the per-row `canonicalization_status` needed to audit the contamination.
> No statement of the form "E2a and E2b disagree about the mechanism" may be made, cited, or
> used to justify commissioning new work until the contamination is quantified under a
> host-independent instrument.

---

## 4. BINDING CONSTRAINTS

Any acceptable design **must** satisfy all of the following. Each is stated so that a reviewer
can mechanically check pass/fail.

**BC-0 — Discharge the instrument-artifact hypothesis first.** No new surface may be
commissioned until the sealed E2a fronts are re-scored under the determinacy-bound instrument
(§3.2) and the corrected A/B/C+D counts are published. This is zero new search, uses an
existing local corpus, and is explanatory-only (it licenses nothing and cannot be cited by any
change). Rationale: commissioning a 540-world, ~16 CPU-hour re-run to explain a divergence that
may be an artifact of a 5-second timer is the single most expensive avoidable error available
to this programme. Verifiable: a corrected-attribution artifact exists and is a strict ancestor
of any new-surface commit.

**BC-1 — Route sealed before veto.** The routing decision is computed from the new surface alone
and hash-sealed in a commit that is a strict ancestor of the first commit containing any Held-out
comparison artifact. Verifiable: `git merge-base --is-ancestor`.

**BC-2 — Single shot, no retry.** Exactly one surface may be generated. The surface count is an
auditable integer. If the surface fails any control or any veto, the terminal is negative; there
is no second surface under this protocol, and no amended protocol may be written after seeing the
first surface's outcome. Verifiable: surface manifests, commit history.

**BC-3 — Generator ancestry.** Every generator parameter is bit-identical to a value fixed in a
commit that is a strict ancestor of the first E2b front commit, or is derived by a registered rule
that provably never reads Held-out. Verifiable: ancestry check plus field diff. Practically this
means the frozen `V2C` population specification (5 families × 3 coefficient regimes × 3 noise
levels × 12 replicates = 540 worlds × 30 seeds, `world_ordinal` and seed-band formulae from
`MURU_V2_E2_PREDECLARATION` §4/§5) is **re-used unchanged**, not re-specified.

**BC-4 — Empty tuning ledger.** A ledger of post-freeze parameter changes is registered and must
be empty at execution time. A non-empty ledger voids the surface.

**BC-5 — Full §2.4 schema from inception.** Every persisted front row carries all 21 search-side
fields and all 7 scoring-pass fields enumerated in §9, including `admissibility`. Verifiable:
schema validator run against the corpus at seal time, with the field list hard-coded from §2.4
and the validator itself frozen. A corpus missing any field is VOID; **no field may be
back-filled, imputed, or recomputed after the fact** (D6).

**BC-6 — Truth-blind boundary preserved.** The seven truth-derived columns are computed in a
separate scoring pass the search never sees, by a distinct process (§2.4). Verifiable: static
import check that the search path imports nothing truth-derived.

**BC-7 — Retention-identity control is a hard gate.** The instrumented engine's `argmax(score)`
retained candidate must be **byte-identical** to the frozen path's for every seed on a control
world set, before any record is used (§2.5.1). Failure blocks everything, including reporting.

**BC-8 — R0 replay self-consistency.** The re-scoring pipeline scored under R0 must reproduce the
surface's own sealed A/B/C/D/E counts and `selection_count` values exactly. Any discrepancy is a
defect in the implementation, not a finding, and blocks all results (`f4c1105` §9 control 1).

**BC-9 — Statistic separation.** The qualification statistic must not be the routing statistic and
must not be a monotone function of the routing variable. Explicitly barred as qualification
statistics: the A/B/C+D counts or shares, `P_front`, `P_retain_given_front`, the `SUCCESS`/stage-E
rate, and any dominant-mechanism label. Verifiable by inspection of the qualification definition.

**BC-10 — The Held-out veto is silent and single-use.** It is executed once, after BC-1's seal.
Its only permitted outcomes are VOID and SILENT. A passing veto may not appear in the citation set
of any downstream change and may not be described as support. Verifiable: the static citation
checker (§1.3) must reject any change citing the veto artifact.

**BC-11 — Host-independent classifier, mandatory.** The determinacy bound of §3.2 with all six
conditions. No label anywhere in the protocol may be a function of wall-clock time, worker count,
host load, or CPU model. Verifiable: condition-by-condition review plus the uncapped validation
sample.

**BC-12 — Architecture declaration.** The protocol must state, in one sentence, that its decision
is computed entirely within a single-host surface and makes no cross-architecture numeric claim.
If it cannot state that, it must declare T9 and stop.

**BC-13 — Predeclared unresolved and invalid handling.** Before execution: the disposition of
`UNRESOLVED` cases (own class, never folded), the maximum `UNRESOLVED` fraction above which the
run is VOID, the disposition of unparseable rows, the disposition of `invalid_fraction` above the
frozen `MAX_INVALID_FRACTION = 0.005`, and the quarantine rule for any world failing a control
(quarantined and reported, never silently dropped — §2.5.3).

**BC-14 — Predeclared, mechanical routing table with tie and failure branches.** §7 below, adopted
verbatim or superseded only by an explicitly argued amendment written before execution.

**BC-15 — Thresholds reused, not invented.** Every numeric bar must be either (a) reused verbatim
from frozen authority with its source cited, or (b) newly derived with an explicit written argument
for why no frozen bar applies, registered before execution. §6 is the inventory of what is
genuinely available. Any newly derived bar must be justified structurally (by analogy to an existing
constant), never by a power calculation performed against the surface it will be applied to.

**BC-16 — Scale-correct threshold porting.** The frozen materiality tolerance is *"more than 10
cases"* against `n = 144`. It is an absolute count, not a rate. Porting it to a population of a
different size **must** be done as the proportion `10/144 = 0.0694` with the strict inequality
preserved, and the port must be declared explicitly. Silently reusing "10" against 539 or 540
worlds tightens the bar by 3.7× and is threshold tuning.

**BC-17 — Endpoint fixed at G2.** The endpoint is G2 support-and-family recovery as defined by
`src/muru/paper_benchmark/g2_contract.py`, unchanged. `P_front`, `P_retain_given_front`,
`conditional_retention_recall`, coverage, and stage-share statistics are **diagnostics**. None of
them may be substituted as the primary endpoint, and no re-entry may be licensed on a proxy that
moves while G2 does not.

**BC-18 — Independent adjudication.** A named adjudicator, independent of the design author,
applies the frozen routing table to the sealed artifacts and produces a signed verdict. The
adjudication procedure is registered before execution (D3 item 6). Two hostile reviews — one
scientific, one governance — are run against the design **before** freeze and against the result
**before** the verdict is accepted, matching the CRITIC_A/CRITIC_B discipline that the Gate 1
adjudication actually used.

**BC-19 — Results-blind freeze with hashes.** The complete protocol, the routing table, the
qualification criterion, the failure rules and the analysis code are hash-frozen and committed
before any new world is generated (D3 item 7). Verifiable: the freeze commit is a strict ancestor
of the first data commit, and the recorded hashes verify.

**BC-20 — Controls: identity, negative, known-answer.** All three required; see §10. A surface
with no negative control cannot be qualified, because a criterion that has never rejected anything
has never been shown capable of rejecting anything.

**BC-21 — Downstream executability declared in advance.** The routing table must state, for each
branch, whether the licensed arm is actually executable under frozen authority. E4f is **not**
(§1.10). A route to a non-executable arm is a legitimate terminal and must be pre-labelled as one,
so that discovering it later cannot be used as grounds to re-route.

**BC-22 — E3's completed verdicts bind the generation branch.** `mass_affine_descriptor` and
`mass_exponential_descriptor` are MARGINAL with `search_side_attribution_licensed: false`; no
search-side change may cite those cells. The routing table must encode this, not rediscover it.

**BC-23 — No new symbolic search on Held-out.** Under no branch may the protocol re-run search on
Held-out or Challenge cases. Verifiable: static import check plus a corpus-path allowlist.

**BC-24 — Every artifact hashed and reconciled.** A manifest with SHA-256 for every produced
artifact, verified after writing, with a recorded statement that no sealed evidence was modified —
matching the discipline already used at `ARTIFACT_SHA256.txt` and `RATIFICATION_VERIFICATION.json`.

---

## 5. PROHIBITED DESIGN MOVES

**PM-1 — Qualification by matching the Held-out attribution.** Barred by §2.4 and §2.6 (circularity)
and independently by §3.3 (architecture). No variant survives: not "matching the dominant
mechanism", not "matching the ordering", not "matching within a tolerance", not "matching the
plurality".

**PM-2 — Generating more than one surface, or amending the protocol after seeing the first.**
Retry converts the veto into a fitting objective.

**PM-3 — Choosing any generator parameter after inspecting Held-out.** Families, coefficient ladder,
noise ladder, replicate count, seed count, search configuration, grammar. Including "we chose 12
replicates because it matches the v1 per-family case count" **if** that reasoning is reconstructed
now rather than reused from the existing frozen text.

**PM-4 — Running the Held-out comparison before the route is sealed.** Order is the control; a
protocol sentence promising not to be influenced is not.

**PM-5 — Citing a passing veto as positive support.** The veto is silent or it is a licence.

**PM-6 — Weakening the qualification comparison to dodge the architecture boundary.** If the
comparison is required, its preconditions are required. Substituting a coarser comparison because
the fine one is unavailable is threshold tuning.

**PM-7 — Reusing the E2b front corpus as the new calibration surface.** Explicitly foreclosed by
the ratification: it lacks `admissibility` and 15 other §2.4 fields, and may not be promoted into
a decision-licensing corpus. Its richness (it is the only local corpus carrying `score` and `loss`)
is precisely the temptation D6 anticipated.

**PM-8 — Reusing the sealed E2a corpus as the new calibration surface.** It lacks `score`, `loss`,
`g2_correct`, `canonicalization_status`, and `admissibility`; every row is `classified: false`
(§1.6). Any arm keyed on `score` — R0, R2, R6 — is not computable from it. Back-filling those
columns is retroactive field fabrication, barred by D6.

**PM-9 — Substituting an easier endpoint.** `P_front`, retention recall, coverage, stage shares,
"conditional" success rates, or any per-stage improvement in place of G2 support-and-family
recovery. Watch specifically for a design that reports a large `conditional_retention_recall` gain
and calls it re-entry evidence while G2 case success is unchanged.

**PM-10 — Redefining the population to a subset after seeing results.** Excluding a family, a
regime, a noise level, or the quarantined/poison worlds post hoc. The `mass_exponential_descriptor`
family is the standing temptation, since E3 has already ruled it MARGINAL.

**PM-11 — Letting any cost limit become a classification.** A wall-clock cap, memory cap, or
worker-count choice that changes a scientific label. This is the defect that produced §1.7 and the
x86 parity failure; it must not recur under a different name.

**PM-12 — Post-hoc tie-breaking.** Inventing a tie-break after seeing counts that produced a tie.
The frozen rule already covers this branch (DIAGNOSTIC-ONLY, adoption suspended pending a *named*
review); it must be adopted verbatim.

**PM-13 — Multi-factor changes inside one arm.** One factor at a time (§3 discipline). A design
that changes the retention rule and the voting relation together, or the classifier and the
grammar together, cannot attribute its effect.

**PM-14 — Adopting a rule that wins by retaining everything.** Full-Pareto retention is registered
as an oracle/control and is excluded from any adoption set by construction (`f4c1105` §5.1).

**PM-15 — Trading coverage for correctness.** A more permissive family classifier converts
`UNEVALUABLE` into false `SUCCESS`. Coverage is never an adoption criterion; `false_labelling_rate`
is primary — and its ceiling **does not exist in frozen authority** (§1.10), so any design routing
to E4f must derive it before execution or declare the arm non-executable.

**PM-16 — Reporting a G2 gain without its false-structure cost.** Explicitly *"not permitted"*
by `befca0d` §3.

**PM-17 — Describing any new document as preregistered.** These are prospective post-Gate-1
protocol-owner amendments (ratification §10). Calling them preregistration is a provenance
misstatement of exactly the kind the Gate 1 record already had to withdraw once.

**PM-18 — Treating `LOCKED_EXECUTE_E4A` as surviving evidence.** D5 removed its forward-licensing
force; §1.7 shows it is not even robust to correction of a known instrument defect.

**PM-19 — Silently changing classification machinery under cover of "fixing the timeout".** The
determinacy bound is licensed by §3.2 under six conditions. Any change to `g2_contract` semantics,
family definitions, equivalence tolerance, or the A–E decision order rides in under the same
banner and is prohibited.

**PM-20 — Publishing a route whose licensed arm is not executable, without saying so.** See BC-21.

---

## 6. THRESHOLD INVENTORY — WHAT MAY BE REUSED VS WHAT MUST BE DERIVED

Reuse is strongly preferred. Every row marked REUSE is available today with a citation.

### 6.1 Genuinely available (REUSE)

| Threshold | Value | Source | Notes on reuse |
|---|---|---|---|
| Materiality tolerance | strictly **> 10 cases** out of 144 | `f4c1105` §4 (PE2-4's own tolerance) | Absolute count. **Must be ported as the proportion 10/144 = 0.0694** if applied to a different n (BC-16). |
| Gate 2 plurality rules | `B > A AND B > C+D`; the A branch; the C+D branch; the exoneration branch; the no-strict-plurality branch | `f4c1105` §4 | Complete and mechanical, **including the tie branch**. Adopt verbatim. |
| Identifiability bars | ≥ 0.80 IDENTIFIABLE; 0.50–0.80 MARGINAL; < 0.50 WEAKLY IDENTIFIABLE | `MURU_V2_IDENTIFIABILITY_STUDY_DESIGN` §5, decision tree B.0 | Already **applied**: E3 is complete; the verdicts bind (BC-22). |
| E3 study-validity bar | `false_structure_oracle > 0.10` on the `mass_power` control → STUDY INVALID | same | Already applied: BIC 0.095 = `VALID_NARROW`, margin 0.005. R² variant 0.685 = STUDY_INVALID, excluded. |
| E6 safety ceiling | unsafe structural acceptance **Wilson upper ≤ 0.15** on **≥ 100** evaluable safety opportunities | decision tree §3 and A.2 | The only numeric safety ceiling in the corpus. E6 has veto and no positive power. |
| Stability gate | `STABILITY_GATE / STABILITY_DENOMINATOR = 20/30` | `structural_acceptance.py`, reused by `f4c1105` §7 metric 5 | Import, do not reimplement. |
| Invalid-fraction bar | `MAX_INVALID_FRACTION = 0.005` | `befca0d` §3.4 | Frozen. |
| CI method | Wilson 95%, `g2_contract.wilson_lower_95` / `wilson_upper_95` | `f4c1105` §7 | *"reused, not reimplemented"* — import them. |
| Paired primary statistic | exact McNemar on discordant pairs **plus** case-level bootstrap 95% CI, `B = 10,000`, resampling within EVAL only | `f4c1105` §8 | Directly reusable for any paired case-level comparison. |
| Bootstrap seed derivation | `derive_seed_v2("bootstrap", "<policy_id>")` truncated to 64-bit | `f4c1105` §8 | Deterministic, reproducible, no new seed band. |
| Multiplicity control | Development-only pre-reduction of internal grids, **plus** Holm–Bonferroni at `alpha = 0.05` across the head-to-head comparisons, reported alongside unadjusted CIs | `f4c1105` §8 | Reuse the two-layer structure exactly. |
| DEV/EVAL split | `replicate ∈ {0,1}` → DEV (90); `replicate ∈ {2..11}` → EVAL (450); stratified by construction across all 45 cells | `f4c1105` §6 | Function of `replicate` only, fixed before any front is read. Reuse verbatim. |
| Gate-evaluation population | full 540 cases, **not** the split | `f4c1105` §6 | The gate is a diagnostic fact about the surface's own attribution. |
| Adoption tie-break order | fewest free parameters, then lowest false structure | `befca0d` §3.1 | Reuse. |
| Improvement bar | paired improvement's 95% lower bound **> 0** | `f4c1105` §6.1, `befca0d` §3.1 | Reuse. |
| A–E taxonomy and decision order | verbatim, with the C/D refinement via `discovery.equivalence.algebraically_equivalent` | `MURU_V2_E2_PREDECLARATION` §6, reproduced in `f4c1105` §2 | Frozen against real pipeline functions. Do not redefine. |
| Population, ordinals, seed band | 540 worlds; `world_ordinal = ((family_idx*3 + regime_idx)*3 + noise_idx)*12 + replicate`; `e2a_seed = E2A_SEED_BASE + world_ordinal*30 + k` | `MURU_V2_E2_PREDECLARATION` §4/§5, `befca0d` §2.8 | Reuse unchanged — this is also how BC-3 is satisfied. |
| Search configuration | `PYSR_CONFIG`, `GRAMMAR_VERSION`, `SEEDS_PER_CASE = 30`, `deterministic=True`, `parallelism="serial"` | `befca0d` §2.5.2 | Frozen. Any deviation is a factor change and needs its own arm. |
| Quarantine rule | a case failing a replay/identity control is **quarantined and reported, not silently dropped** | `befca0d` §2.5.3 | Reuse as the general failure discipline. |
| Timeout status discipline | timeout recorded as explicit `SIMPLIFY_TIMEOUT`, never silently `None` | `befca0d` §2.10 | Reuse — and note §1.7: the letter was met and the substance was not. BC-11 closes it. |

### 6.2 Must be newly derived (unavoidable gaps)

| Item | Why no frozen bar exists | Least-discretionary prospective choice |
|---|---|---|
| The qualification criterion and its numeric bar | Frozen authority contains **no** qualification concept at all — §2.3 is destructive-only | Do not invent a numeric bar. Make qualification **binary and structural**: all controls pass, schema complete, `UNRESOLVED` fraction under BC-13's bar. No tunable number is introduced. |
| Maximum `UNRESOLVED` fraction | New concept introduced by the determinacy bound | Structural analogy, not a fresh magnitude: the sealed Gate 1 run achieved 0.31% rows unresolved and **0** cases indeterminate. Set the case-level bar at **0 indeterminate cases** (VOID otherwise) — the strictest available and the one already demonstrated achievable. |
| Adjudicator identity and procedure | Absent from every commit; the Gate 1 report names this explicitly as requiring the owner | Reuse the structure that was actually executed: a named independent adjudicator, plus CRITIC_A (scientific) and CRITIC_B (governance), both required PASS. |
| `false_labelling_rate` ceiling (only if the route is E4f) | Never declared anywhere; grep returns the phrase, never a number | Do **not** improvise. Declare E4f non-executable (BC-21) and route to a terminal, or commission a separate operational preregistration for it. Inventing this ceiling after the route is known is the highest-leverage cheat available. |
| `k_inflation` ceiling (E4f) | Same defect | Same disposition. |
| Definition of "regime fidelity", if any qualification claims it | No frozen definition | Do not claim it. §2.6 shows any definition strong enough to be meaningful is circular. |

**Reviewer's rule of thumb:** if a proposed design introduces more than one new number, it is
almost certainly tuning. The count of newly introduced magnitudes is itself a review metric.

---

## 7. THE DEFENSIBLE ROUTING TABLE

Computed on the new surface's own attribution, over the full population, **before** any
Held-out comparison exists (BC-1). `A`, `B`, `C`, `D`, `E` are the frozen A–E stages;
`NONSUCCESS = A + B + C + D`.

| # | Predicate (evaluated in this order) | Route | Executable today? |
|---|---|---|---|
| 0 | Any control in §10 fails, or schema incomplete, or indeterminate cases > 0 | **VOID** — no route, negative terminal, no retry | — |
| 1 | `P_retain_given_front` near 1 wherever `P_front` is high (exoneration) | RC3 **WITHDRAWN**. No retention change licensed. STOP | n/a |
| 2 | `B > A` **and** `B > C+D` (strict plurality of B) | RC3 confirmed → **E4a** (retention policy) | **Yes** — `f4c1105` is a complete operational freeze |
| 3 | `A` strict plurality | RC4 confirmed → route **through E3's completed verdicts per cell** | **Partially**: `mass_saturating_descriptor` and `mass_interaction` only. **Blocked** for `mass_affine_descriptor` and `mass_exponential_descriptor` (MARGINAL, `search_side_attribution_licensed: false`) |
| 4 | `C+D` strict plurality | RC7 larger than v1's 2 cases → **E4f** (voting / canonicalization) | **NO.** E4f has no operational freeze, no population, no split, no statistics, no control, and no numeric ceiling for its primary metric. Terminal: *route determined, arm not executable, STOP pending a separate E4f preregistration* |
| 5 | No strict plurality (tie or near-uniform) | **DIAGNOSTIC-ONLY.** Every metric reported; the adoption rule is **suspended** pending a *named* tie-breaking review | n/a — and inventing a tie-break now, after seeing the counts, is barred (PM-12) |

**Tie rules.** "Strict plurality" means strictly greater than each of the other two aggregates.
Equality is **not** a plurality and falls to row 5. This is `f4c1105` §4's own rule and is adopted
verbatim rather than restated, so that no boundary case is silently redefined.

**Failure rules.**
- F1. Any control failure → VOID (row 0). Negative terminal. No retry (BC-2).
- F2. `UNRESOLVED` cases > 0 → VOID.
- F3. Schema incomplete at seal → VOID. No back-fill (D6).
- F4. Held-out veto trips after the route is sealed → **VOID**, never re-route. A tripped veto
  means the surface does not reproduce the Held-out regime and §2.3 fires exactly as it did for
  E2a. It must not be used to select a different branch.
- F5. Held-out veto passes → **SILENT**. Reported as "the falsification hook did not trip".
  Never cited (BC-10, PM-5).
- F6. Route determined but arm not executable (row 3 partial, row 4) → terminal
  `ROUTE_DETERMINED_ARM_NOT_EXECUTABLE`, pre-labelled (BC-21).
- F7. Any of D3's eight `EXPERIMENTAL_REENTRY_RESOLUTION` items unmet at verdict time → no
  re-entry, regardless of the route.

**Note on row 4.** Row 4 is the branch E2b's measurement points at. It is also the branch with no
executable arm. A designer who notices this before execution will be tempted to reshape the
routing table so that row 4 is unreachable or is folded into row 2. That is why the table must be
sealed under BC-1/BC-19 and why F6 is pre-labelled as a legitimate terminal.

---

## 8. HIDDEN DEGREES OF FREEDOM

Every analyst choice available in an experiment of this class. **FROZEN** = fixed by prior
authority and must be reused; **OPEN** = a real degree of freedom requiring a prospective,
least-discretionary choice.

| # | Choice | Status | Authority / least-discretionary prospective choice |
|---|---|---|---|
| 1 | Truth families | **FROZEN** | 5 families, `befca0d` §2.8. Reuse; no addition, no removal. |
| 2 | Coefficient regimes | **FROZEN** | 3 regimes, §2.8. Do not re-ladder. |
| 3 | Noise levels | **FROZEN** | 3 levels, §2.8. |
| 4 | Replicates per cell | **FROZEN** | 12, §2.8, justified as matching the v1 per-family case count. |
| 5 | Population size | **FROZEN** | 540 worlds = 5 × 3 × 3 × 12. |
| 6 | World enumeration | **FROZEN** | `world_ordinal` formula, `E2_PREDECLARATION` §4. |
| 7 | Seeds per case | **FROZEN** | 30, §2.5.2. |
| 8 | Seed derivation / band | **FROZEN** | `E2A_SEED_BASE + world_ordinal*30 + k`, `E2_PREDECLARATION` §5. A new surface needs a **new disjoint band**, derived by the same rule — that is the one permitted extension and it must be registered. |
| 9 | Search configuration | **FROZEN** | `PYSR_CONFIG`, `GRAMMAR_VERSION`, `deterministic=True`, `parallelism="serial"`, §2.5.2. |
| 10 | Grammar / operator set | **FROZEN** | `sqrt, log, square, cube, inv`; `exp` excluded (DEVIATIONS_P3 D1). Changing it is E4d, a suspended arm. |
| 11 | Within-seed retention rule | **FROZEN** | `argmax(score)` = R0 control. Alternatives are E4a arms, not surface parameters. |
| 12 | Cross-seed grouping | **FROZEN** | `rc5_selection.group_and_select` on `identity_contract.template_key`, largest-class-wins, lowest-ordinal tie-break. Alternatives are E4f arms. |
| 13 | Vote reduction for multi-row policies | **FROZEN** | `argmax(valid_r2)` among the retained set, one rule for every arm (`f4c1105` §5). |
| 14 | Stability gate | **FROZEN** | 20/30, `structural_acceptance.py`. Import. |
| 15 | Invalid handling | **FROZEN** | `MAX_INVALID_FRACTION = 0.005`; plus the direct check that an invalid candidate never outscores a valid one (§3.4). |
| 16 | Stage taxonomy and decision order | **FROZEN** | A–E, `E2_PREDECLARATION` §6. Strict A-B-(E-or-D-or-C) order. |
| 17 | Equivalence semantics | **FROZEN** | `discovery.equivalence.algebraically_equivalent`, up to a positive multiplicative constant. |
| 18 | G2-correctness definition | **FROZEN** | `g2_contract.py`. Byte-unchanged (BC-11 condition 1). |
| 19 | **Scoring cap semantics** | **OPEN — and defective as frozen** | 5 s SIGALRM/process-kill cap that decides labels (§1.7). Least-discretionary: the determinacy bound with the six conditions of §3.2, `UNRESOLVED` never folded, 0 indeterminate cases required. |
| 20 | **Classification mode (lazy vs exhaustive)** | **OPEN — unregistered and consequential** | Lazy classification makes the number of classify calls a function of the stage (A: full scan, median 345 calls; C/E: 30). Under a wall-clock cap that means **stage A is systematically more exposed to timeouts than stage E** (§1.7). Least-discretionary: classify exhaustively, or use lazy classification only under a determinacy bound where call count cannot change a label. Declare the mode prospectively. |
| 21 | **Worker count / host load / CPU model** | **OPEN — currently a scientific variable** | Under a wall-clock cap these change labels (§3.2 corollary). Least-discretionary: eliminate the dependence via BC-11; additionally freeze worker count and pin single-threaded env vars as the sealed runs already do. |
| 22 | DEV/EVAL split | **FROZEN (reusable)** | `replicate ∈ {0,1}` / `{2..11}`, stratified, fixed before any front is read, opened once (`f4c1105` §6). |
| 23 | Which surface the gate is evaluated on | **FROZEN (reusable)** | Full population, not the split (`f4c1105` §6). |
| 24 | Primary statistic | **FROZEN (reusable)** | Exact McNemar on discordant pairs + case-level bootstrap CI, `B = 10,000` (`f4c1105` §8). |
| 25 | CI method | **FROZEN (reusable)** | Wilson 95% via `g2_contract`, imported not reimplemented. |
| 26 | Bootstrap RNG | **FROZEN (reusable)** | `derive_seed_v2("bootstrap", id)`. |
| 27 | Multiple comparisons | **FROZEN (reusable)** | DEV-only grid pre-reduction + Holm–Bonferroni at `alpha = 0.05`, both reported. |
| 28 | Improvement bar | **FROZEN (reusable)** | Paired 95% lower bound > 0. |
| 29 | Adoption tie-break | **FROZEN (reusable)** | Fewest free parameters, then lowest false structure. |
| 30 | Materiality tolerance | **FROZEN (reusable, with a port hazard)** | > 10 of 144. Port as the proportion 0.0694 (BC-16). |
| 31 | Identifiability bars | **FROZEN and already applied** | 0.80 / 0.50 / 0.10; E3 complete; verdicts bind (BC-22). |
| 32 | Safety ceiling | **FROZEN** | E6: Wilson upper ≤ 0.15 on ≥ 100 opportunities. Veto only. |
| 33 | `false_labelling_rate` ceiling | **OPEN — genuinely absent** | Do not invent it after the route is known. Declare E4f non-executable (BC-21). |
| 34 | `k_inflation` ceiling | **OPEN — genuinely absent** | Same. |
| 35 | **Qualification criterion** | **OPEN — the whole subject of this document** | Binary and structural only (§6.2). Never keyed to the routing variable (BC-9). |
| 36 | **Number of surfaces generated** | **OPEN — the largest single leakage channel** | Exactly one (BC-2). |
| 37 | **Order of route vs veto** | **OPEN — the decisive control** | Route sealed first, strictly (BC-1). |
| 38 | **Which Held-out statistic the veto compares** | **OPEN** | Fix it in the freeze, or omit the veto entirely. Choosing it after the route is known is fitting. |
| 39 | Disposition of quarantined / poison / unresolved worlds | **OPEN (discipline is frozen)** | Quarantine and report, never silently drop (§2.5.3). Declare the arithmetic effect on every denominator in advance. |
| 40 | Endpoint | **FROZEN** | G2 support-and-family recovery (BC-17). Diagnostics may not be promoted. |
| 41 | Adjudicator | **OPEN** | Named, independent, registered before execution; plus CRITIC_A and CRITIC_B (BC-18). |
| 42 | Corpus schema | **FROZEN** | `befca0d` §2.4, all 28 fields, from inception (§9, BC-5). |
| 43 | Host architecture | **OPEN, with a hard boundary** | Single-host x86 permitted for a within-surface decision (BC-12); barred for any cross-architecture numeric claim (§3.3). |

---

## 9. THE MANDATED FRONT-RECORD SCHEMA (befca0d §2.4) — EXACT REQUIRED FIELDS

Persisted for **every (world, seed, front row), before retention is applied** — 21 fields:

```
 1  world_id                  8  engine_complexity        15  loss
 2  cell_id                   9  grammar_complexity       16  score
 3  replicate                10  expression_string        17  invalid_fraction
 4  split                    11  parse_ok                 18  effective_support
 5  seed_ordinal_k           12  train_r2                 19  template_key
 6  seed                     13  valid_r2                 20  retained_by_argmax_score
 7  front_rank               14  test_r2                  21  admissibility
```

Joined in a **separate scoring pass the search never sees** — 7 fields:

```
22  discovered_family        25  g2_correct               28  coefficient_regime
23  support_status_vs_truth  26  truth_family
24  family_status_vs_truth   27  truth_support
```

**28 fields total.** `admissibility` is mandatory at the **row** level — it is the mechanism by
which `DECISION_INADMISSIBLE` is enforced mechanically rather than by convention (§2.3), and it is
the field whose absence is the stated reason the E2b corpus cannot be reused (ratification §8).

**Compliance of existing corpora (verified):**

| Corpus | Fields present | Missing | Verdict |
|---|---|---|---|
| E2b Held-out fronts | `complexity`, `equation`, `loss`, `score`, `sympy_format` + manifest | `admissibility` + 15 others | Non-compliant; explicitly barred from reuse (ratification §8) |
| E2a x86 (`run_x86_e2a_v1`) | 16 fields; every row `classified: false` | `score`, `loss`, `grammar_complexity`, `parse_ok`, `train_r2`, `split`, `effective_support`, `template_key`, `admissibility`, and **all 7** scoring-pass fields | Non-compliant. Arms keyed on `score` (R0/R2/R6) are **not computable** from it. Back-fill is barred by D6 |

**BC-5 restated as a check:** a validator with this 28-field list hard-coded, frozen before
execution, run against the new corpus at seal time. Any absent field → VOID. Any field written
after the seal → VOID.

---

## 10. SELF-QUALIFICATION AND REQUIRED CONTROLS

**Is there circularity in a surface qualifying itself?** Yes, in a specific and narrower sense
than the E2b circularity, and it is not fatal if the controls below are built in.

A surface computes its own attribution using an instrument. If the *only* check on that
instrument is the attribution it produces, the instrument is unfalsifiable: any output is
self-consistent. §1.7 is the concrete demonstration — E2a's instrument silently converted
"we ran out of time" into "the structure is absent", and nothing in E2a's own outputs could
reveal it. The corpus was internally consistent and wrong.

The escape is that the controls must be **answerable against something other than the
surface's own attribution**. Three are mandatory:

**C-1 — Identity / replay control (already frozen, `befca0d` §2.5.1, `f4c1105` §9.1).**
The instrumented engine's retained `argmax(score)` candidate must be **byte-identical** to the
frozen production path's, for every seed on a control world set. *"Instrumentation that changes
the search is not instrumentation."* Hard gate before any record is used. Answerable against the
production pipeline, not against the attribution.

**C-2 — Negative control.** Adversarial constructions that are **known not truth-equivalent by
construction**: substitute `correlated_distractor` for `descriptor`; substitute `descriptor2` for
`descriptor`; replace the descriptor factor with a constant of matched magnitude (`befca0d` §3.6).
These must be **rejected** by the instrument. A qualification criterion that has never rejected
anything has not been shown capable of rejecting anything. Additionally, the `mass_power` family
is the in-population truth-negative-support control and must be scored **identically** to the four
descriptor-bearing families, with no more permissive rule, so the specificity signal cannot be
inflated by construction (`f4c1105` §9.4).

**C-3 — Known-answer control.** Worlds whose stage is determinable analytically, run through the
full instrument, which must recover the known stage. This is the control that would have caught
§1.7: plant a correct row that is expensive to canonicalize and verify the instrument does not
report `NEVER_ON_FRONT`. **I regard C-3 as the single most important addition to any new design**,
because it is the only control that directly probes the failure mode that produced the current
crisis.

**C-4 — Uncapped validation sample (from BC-11 condition 5).** A predeclared sample re-scored with
**no** cap, and 100% agreement required with the bounded instrument. The sealed Gate 1 run achieved
101/101; that is the demonstrated-achievable bar.

**C-5 — Determinism replay.** Re-execute a predeclared subset and require byte-identity, matching
the 30/30 determinism check the x86 host already passed.

Note that C-1 through C-5 are all **internal-validity** controls. That is deliberate: under
BC-9 they are the only things a qualification may be keyed to, and they are exactly the checks
that would have caught the defects the programme actually suffered.

---

## 11. HONEST TERMINAL ASSESSMENT

### 11.1 Is a defensible qualification possible?
**By Held-out matching: no.** §2.6 establishes it structurally, and §3.3 kills it a second time on
architecture. The two objections are independent; removing either does not save the design.

**By internal validity (§2.5): yes, it is logically defensible** — a surface qualified on instrument
correctness alone, routing from its own attribution, sealed before a silent single-use veto. But I
must be honest about what that buys. Such a protocol reaches re-entry only if:

1. it executes cleanly (controls pass, schema complete, zero indeterminate cases); **and**
2. its attribution yields a strict plurality; **and**
3. that plurality routes to an arm that is actually executable — which today means **row 2 only**,
   since row 4 (E4f) has no operational freeze and row 3 is blocked for two of five families by E3's
   completed MARGINAL verdicts; **and**
4. the Held-out veto does not trip — and if the new surface behaves like the sealed E2a, it will
   produce a `B` plurality, which disagrees with E2b's cross-seed-dominant measurement, which trips
   §2.3 exactly as it did the first time.

Conditions 3 and 4 are in direct tension. The route that is executable (E4a, retention) is the route
that **disagrees** with Held-out. The route that agrees with Held-out (cross-seed) is the route with
**no executable arm**. A design can satisfy either, not obviously both. I put the prior probability
that a fresh surface run under these constraints reaches licensed E4 re-entry as **low**, and I
would not want that estimate to be the reason anyone spends 16–19 CPU-hours before BC-0 is
discharged.

### 11.2 The one thing that should happen before any of this
**BC-0 is not a formality; it is the highest-value action available to this programme.**

§1.6 and §1.7 establish, with exact numbers, that the sealed decision-admissible E2a attribution was
partly decided by a 5-second timer, in a direction that inflates the `NEVER_ON_FRONT` stage, in
59.8% of the worlds carrying that stage, with a worst-case correction that **flips the Gate 2
plurality from `B` to `C+D` — i.e. onto E2b's answer**. The E2a/E2b divergence, which is the entire
reason the programme is stopped, has a live mundane explanation that has never been tested: the two
surfaces were measured with **different instruments**, one of which lets a cap decide and one of
which does not.

Re-scoring the existing E2a fronts under the determinacy-bound instrument costs **zero new search**,
uses a corpus that is already local, licenses nothing, and is explanatory-only — the same status
E2b holds. It could discharge D3's *"until the contradiction is resolved"* without a new surface at
all. If instead the programme commissions a 540-world re-run and the divergence turns out to have
been a timer, that will be the most expensive avoidable error in the record.

### 11.3 The terminals I would accept as honest
- **T1 — NO_ADMISSIBLE_QUALIFICATION_EXISTS.** The programme reports that §2.3's destructive-only
  rule combined with D6's inadmissibility admits no qualification that is both non-circular and
  non-vacuous, publishes the divergence, and stops. **This is a legitimate scientific result and
  the decision tree already contains it**: *"No v2 architecture is proposed at all."*
- **T2 — QUALIFICATION_ATTEMPTED_AND_FAILED.** One surface, one shot, controls or veto fail. Negative
  terminal, no retry, no amended protocol.
- **T9 — REQUIRED_ARCHITECTURE_EXECUTION_BOUNDARY.** Forced if and only if Held-out-matching
  qualification is retained as a requirement (§3.4).
- **T-INSTRUMENT — DIVERGENCE_EXPLAINED_AS_INSTRUMENT_ARTIFACT.** Available today via BC-0, and not
  yet excluded.

### 11.4 What I will veto on sight
Any design that (a) qualifies by matching Held-out in any form; (b) generates more than one surface;
(c) runs the Held-out comparison before the route is sealed; (d) reuses the E2a or E2b corpus as the
calibration surface; (e) introduces more than one new numeric threshold; (f) substitutes a
non-G2 endpoint; (g) leaves any label a function of wall-clock time; or (h) routes to E4f without
first declaring it non-executable.

---

*P2, GOVERNANCE / LEAKAGE ADVERSARY. Nothing in this document licenses any experiment, change,
threshold, or re-entry. It constrains what a design may be, and it records two previously
unrecorded defects (§1.6, §1.7) that bear directly on whether the programme's central divergence
is real.*
