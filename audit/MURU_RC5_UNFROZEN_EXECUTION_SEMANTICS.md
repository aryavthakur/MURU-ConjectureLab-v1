# RC5 blocked: unfrozen scientific execution semantics

**Document ID:** `MURU-RC5-UNFROZEN-EXECUTION-SEMANTICS-01`
**Classification:** `GATE_1_AUTHORITY_ADJUDICATION`
**Status:** `RC5_BLOCKED_PENDING_GOVERNANCE`
**Mode:** read-only adjudication. No production engine was implemented. Development
was not opened, Held-out was not opened, Challenge was not run, Confirmation
remains sealed.

**Adjudicated parent:** `6a6798273d00af374b7a62976a80cea1ae7df32c`
**Branch:** `eng/muru-rc5-case-execution` (created from that parent, no science modified)

---

## 1. Why this document exists

RC5 was authorized to build the production case-execution path only if every
scientific semantic required to produce a `CaseExecutionRecord` is already
prospectively frozen. Gate 1 required each required semantic to be classified,
and required an absolute stop if any of them turned out to be an unfrozen
scientific decision.

Six required semantics are unfrozen. They are not gaps in engineering
convenience. Each one changes the value of a primary endpoint, and for each one
the repository contains at least two mutually incompatible historical
precedents, at least one of which was chosen after seeing results.

RC5 therefore stops before any implementation. Nothing in this document selects
an option.

---

## 2. Gate 0 result: post-freeze provenance

Independently verified on the parent lineage.

| Check | Result |
|---|---|
| `engineering-rc4-1-environment-closure` resolves to `8c5dd41` | `8c5dd413264fa6661982ae70fbeb323d4a647a27`, confirmed |
| `44e5e36` is preservation only | confirmed: 105 files, 6,647 insertions, **0 deletions**, all under `calibration/a3_2/` plus `scripts/pb_36_run_a3_2_calibration.py` |
| `6a67982` is engineering/integrity only | confirmed: 3 files, `configs/rc4_1_environment_manifest.json` (two test-name registrations), `scripts/pb_34_rc3_integrity.py`, new `tests/test_eng_calibration_evidence.py`. No file under `src/` touched |
| Neither commit modifies frozen benchmark science | confirmed by full name-status diff `8c5dd41..6a67982` |
| All 31 A3.4 protected paths byte-identical | confirmed: 31/31 SHA-256 match against `artifacts/paper_benchmark_amendment_a3_4.json`, recorded aggregate `d24cc916...` |
| No sealed partition opened | confirmed: no `artifacts/inputs/`, no `artifacts/truth/`, no case-execution output anywhere in the tree |
| Integrity verifiers | `pb_30`, `pb_31`, `pb_32`, `pb_33`, `pb_34`, `pb_35` all pass. `pb_34` reports `EXECUTED (AUTHORIZED A3.2, VERIFIED)` |

**Classification: `POST_FREEZE_COMMITS_SAFE_TO_CARRY_FORWARD`.**

The RC4.1 environment tag was not moved or rewritten.

---

## 3. Authority matrix

Classification legend: `FROZEN_EXPLICIT` (a prospective frozen artifact states
it), `FROZEN_DERIVABLE_ENGINEERING` (a mechanical consequence of a frozen
statement, with no scientific choice available), `HISTORICAL_PRECEDENT_ONLY` (an
implementation exists on another track but no prospective artifact binds it to
the paper benchmark), `UNFROZEN_SCIENTIFIC_DECISION` (a choice that changes a
scientific result and has no prospective authority), `NOT_REQUIRED`.

| # | Semantic | Classification | Frozen source | Consequence |
|---|---|---|---|---|
| 1 | benchmark-case to engine input adapter | `FROZEN_DERIVABLE_ENGINEERING` | `registry.py`, `generator.py`, A2.1 generator version | Frame construction is mechanical, but cannot be completed without #3 and #7 |
| 2 | training / validation / test split use | `FROZEN_EXPLICIT` | `generator.py` 20/5/5 scaffold groups; A3.2 states its 18/6/6 applies to calibration worlds only; `CEILING_ESTIMATOR_SPEC` train/test | Case split is unchanged. Fit on train, score validation, follows from the null statistic being a validation R2 |
| 3 | **fold-local scalar target construction (`Phi`)** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 1**, see 4.1 |
| 4 | M0 fitting | `FROZEN_EXPLICIT`, conditional on #3 | A1 sections A1.2, "Frozen fitting parameterisation and bounds", "Frozen search protocol" | Fully specified given `Phi`, unreachable without it |
| 5 | M1 / M2 / M3 adequacy fitting | `FROZEN_EXPLICIT`, conditional on #3 | A1, same sections | Same |
| 6 | adequacy decision | `FROZEN_EXPLICIT` | A1.3 LOEO, 24/30 evaluable, 20/30 practical wins, ratio 0.90; `adequacy.py` | Implementable as-is |
| 7 | **exact PySR target supplied to search** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 2**, see 4.2 |
| 8 | search covariates | `FROZEN_EXPLICIT` | `g2_contract.GRAMMAR_PRIMITIVES`, reused by `rc3_ceiling.CEILING_COVARIATE_ORDER` and `rc3_calibration_worlds.CALIBRATION_COVARIATE_ORDER` | Column identity and order fixed |
| 9 | exact search settings | `FROZEN_EXPLICIT` | A3.1 "Search settings (frozen)"; `calibration_contract.SEARCH_SETTINGS`; digest `36c1ef3c...` | Implementable as-is |
| 10 | number of search seeds per case | `FROZEN_DERIVABLE_ENGINEERING` | `structural_acceptance.STABILITY_DENOMINATOR = 30`; `rc3_record` refuses any other denominator | 30 seeds per case is forced |
| 11 | **prospective case search-seed derivation** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 3**, see 4.3 |
| 12 | **seed namespace / seed band** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 3**, see 4.3 |
| 13 | **per-seed candidate retention** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 4**, see 4.4 |
| 14 | **Pareto candidate handling** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 4**, see 4.4 |
| 15 | **cross-seed candidate selection** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 4**, see 4.4 |
| 16 | **meaning and computation of `selection_count`** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 4**, see 4.4 |
| 17 | stability threshold k >= 20/30 | `FROZEN_EXPLICIT` | A3.1 predicate step 3; `STABILITY_GATE = 20` | The gate is frozen. What is counted is not |
| 18 | candidate `valid_r2` | `FROZEN_DERIVABLE_ENGINEERING` for the metric, unreachable pending #15 | validation-partition R2, forced by the A3.2 null statistic being the same quantity | Metric fixed, subject undefined |
| 19 | candidate complexity | `FROZEN_DERIVABLE_ENGINEERING` | `maxsize = 20`; PySR `equations_["complexity"]`, the same field the calibration consumed | Consistent with calibration by construction |
| 20 | **`invalid_fraction`** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 5**, see 4.5 |
| 21 | null-threshold lookup | `FROZEN_EXPLICIT` | A3.1 predicate step 2, `min(complexity, 20)`; A3.2 VALID table | Implementable as-is |
| 22 | ceiling test | `FROZEN_EXPLICIT`, conditional on #3 and #15 | `CEILING_ESTIMATOR_SPEC`, `rc3_ceiling.estimate_ceiling` | Estimator and gate frozen; its `target` argument depends on #3 and its `candidate_test_r2` on #15 |
| 23 | support recovery inputs | `FROZEN_EXPLICIT` | A3.1 effective-support rules; `g2_contract` | Implementable as-is |
| 24 | **falsification rung execution** | **`UNFROZEN_SCIENTIFIC_DECISION`** | none | **Blocker 6**, see 4.6 |
| 25 | falsification rung order and membership | `FROZEN_EXPLICIT` | A3.1 required-rung list; `REQUIRED_FALSIFICATION_RUNGS`; `FALSIFICATION_RUNG_ORDER` with its drift assertion | Membership, order and the "NOT_APPLICABLE is never a PASS" rule are fixed |
| 26 | final structural acceptance | `FROZEN_EXPLICIT` | `evaluate_structural_acceptance`, ordered 8-gate predicate, 10 typed states | Implementable as-is |
| 27 | A3.4 parameter-recovery scoring | `FROZEN_EXPLICIT` | A3.4 section A3.4.1; `a34_parameter_recovery.py` | Integrate unmodified |
| 28 | A3.4 predictive-equivalence scoring | `FROZEN_EXPLICIT` | A3.4 reference frames `PB\|PRED_EQUIV\|FRAME\|000..011`, digest `4fef2379...`; `a34_predictive_equivalence.py` | Integrate unmodified |
| 29 | exact-algebra scoring | `NOT_REQUIRED` for RC5, with a governance observation | `registry.py` registers the `exact_algebra` endpoint on F01, F08, F09, F10, F17 (60 held-out cases) | `CaseExecutionRecord` has no exact-algebra field, so RC5 does not need it. But no amendment binds its contract, unlike A3.3/A3.4 for the other two secondary endpoints. See section 6 |
| 30 | **case-level failure semantics** | **`UNFROZEN_SCIENTIFIC_DECISION`** | per-seed statuses frozen; case-level aggregation not | See 4.7 |
| 31 | resume semantics | `FROZEN_DERIVABLE_ENGINEERING` | A3.1 "No selective retries or replacement worlds"; `SeedRecordStore` | The no-retry-for-a-better-outcome rule is frozen in principle. Realization is engineering |
| 32 | Development / Held-out partition parameterization | `FROZEN_EXPLICIT` | `registry.PARTITIONS`, `PARTITION_CASE_COUNTS`, `PB\|{partition}\|{family}\|r{replicate:03d}` | Partition is data, as required |
| 33 | raw artifact schema | `FROZEN_EXPLICIT` | `muru-rc3-case-record-1.0.0` | Do not replace |
| 34 | case sidecar schema | `FROZEN_EXPLICIT` | `rc3_record.ProvenanceSidecar` | Do not replace |
| 35 | execution manifest schema | `FROZEN_DERIVABLE_ENGINEERING` | `calibration/a3_2/execution_manifest.json` precedent; `rc3_provenance.build_provenance_manifest` | Carries no scientific decision |

Twenty-six of thirty-five are frozen or mechanically derivable. Six are not, and
they sit on the critical path: without them no `CaseExecutionRecord` field
downstream of the search can be computed at all.

---

## 4. The unfrozen decisions

### 4.1 Blocker 1: the fold-local training-side profile `Phi`

**Missing decision.** The definition and off-grid evaluation of `Phi`, together
with its support, normalisation, residual weighting, constants, profile bounds
and extrapolation rule, and therefore `A_LO`, `A_HI` and `S(t)`.

**Why scientifically material.** Amendment A1 is explicit that it introduces no
new training-side fitting and only *names* objects that the frozen training-only
`Phi` already implies:

> `Phi`'s evaluation away from the grid, including its extrapolation rule, is a
> frozen deterministic property of the locked implementation, fixed before any
> test compound is touched.

The locked implementation does not exist. `paper_benchmark.governance`
`ImplementationLock` is `PENDING_LOCK`, and `MURU_PAPER_BENCHMARK_FREEZE.md`
confirms the executable freeze still requires a locked implementation commit.
What the lineage actually contains is `protocol.fit_training_scalar`, described
in its own module docstring as a "minimal fold-local scalar adapter boundary",
which returns per-energy training means over the six-point grid and a support of
`(-2.0, 2.0)`. It has no profile function, no off-grid evaluation and no
extrapolation rule, so `A_LO` (the limit as the argument tends to zero) and
`A_HI` (the high-argument asymptote) are not computable from it.

Every downstream quantity depends on this. M0, M1, M2 and M3 are written in
terms of `A_HI`, `A_LO` and `S`, so the entire A1 adequacy ladder is
unreachable. G1's "fold-local estimated log-g" is unreachable. The symbolic
search has no target. This single gap makes FM-06 unresolvable in the strict
sense: there is no frozen production semantic to trace a call graph to.

**Historical precedents.** `engineering/muru-completion` `c7c2332` carries
`src/muru/estimators/foldlocal.py`, `src/muru/adequacy/{fit,loeo,models,stage}.py`
and `src/muru/pipeline.py`, on a branch that deliberately does not contain
`muru.paper_benchmark`. The master plan describes T1 as a joint collapse fit
alternating an isotonic shared `Phi` against per-compound scales. Neither is
bound to the paper benchmark by any prospective artifact.

**Options, none selected.** (a) Adopt the RC2 fold-local estimator by amendment,
naming its exact commit and asserting its extrapolation rule. (b) Bind the
isotonic-`Phi` collapse fit from the master plan explicitly. (c) Bind a
grid-mean profile with a declared extrapolation rule, which is what
`protocol.py` would become if extended. (d) Declare that `protocol.py` as it
stands is `Phi`, and separately bind the extrapolation rule that A1 requires.

**Minimum governance action.** A prospective amendment that binds the
training-side `Phi` object completely: definition, support, normalisation,
residual weighting, constants, bounds, off-grid evaluation and extrapolation
rule, with the commit that realizes it, before any partition is opened.

### 4.2 Blocker 2: the exact search target for a benchmark case

**Missing decision.** What vector is handed to `PySRBackend` for a benchmark
case, and on which rows.

**Why scientifically material.** `PySRBackend.search` is typed on
`CalibrationWorld` and consumes `world.design_matrix()` and `world.target`.
For a calibration world the target is defined by A3.2. For a benchmark case no
frozen artifact states whether the target is the fold-local estimated `g`, its
logarithm, whether it is inverse-variance weighted, whether it is normalized to
unit geometric mean, or which compounds contribute rows. `SYMBOLIC_SEARCH_SPEC`
does answer all of this, but for Phase 3's T2 target on 12 real Tier A
descriptors, which is a different track. Choosing between `g` and `log g`
alone changes every recovered expression, every complexity, and therefore every
comparison against a null threshold calibrated at a given complexity.

**Historical precedents.** Phase 3 T2 (`SYMBOLIC_SEARCH_SPEC.md`): the estimated
scale, inverse-variance weighted, normalized to unit geometric mean, compared up
to positive scaling. Type 2 `muru.objval`. The master plan section 13.4.

**Options, none selected.** (a) `log g` on training compounds. (b) `g` on
training compounds. (c) inverse-variance weighted `g` as in Phase 3 T2. (d)
some other prospectively declared construction.

**Minimum governance action.** A prospective amendment binding the target
construction, its weighting, its normalisation and its row set, consistent with
what A3.2 calibrated against.

### 4.3 Blocker 3: case search-seed derivation and seed band

**Missing decision.** The rule that derives 30 search seeds for a benchmark
case, and the seed band it occupies.

**Why scientifically material.** `derive_calibration_seeds` is calibration-only:
it hashes a world ID of the form `PB|NCAL|{construction}|r{index:03d}` and lands
in `PB_SEED_BASE = 2_110_000_000` plus `PB_SEED_SPREAD = 370_000` buckets of
100. A3.1 froze it for the 100 calibration worlds only. No prospective artifact
declares a Development or Held-out band, and `rc3_provenance` declares only
`CALIBRATION_SEED_MIN/MAX` and the engineering smoke band. Seeds are recorded in
the scientific payload of `CaseExecutionRecord` (`seeds_used`), so they are a
scientific object, not an engineering detail. Reusing the calibration band would
collide 2,400 Development seeds and 7,200 Held-out seeds with the 3,000 seeds
already spent on the null, which is exactly the separation
`assert_seed_band_separation` exists to enforce.

**Historical precedents.** The calibration derivation itself. `OV_SEED_BASE` in
`muru.objval.plan2`, chosen to sit above `P3_SEED_THEORETICAL_MAX`. The Phase 3
manifest `artifacts/p3_seed_manifest.json`.

**Options, none selected.** (a) The calibration derivation applied to the frozen
case ID, in a new declared band. (b) A per-partition band with the partition in
the hash namespace. (c) An explicit enumerated seed manifest frozen before
execution, as Phase 3 did.

**Minimum governance action.** A prospective amendment declaring the derivation
and the band, with the disjointness invariant against the calibration, smoke,
reference-frame and historical bands stated and tested.

### 4.4 Blocker 4: per-seed retention, cross-seed selection, and `selection_count`

This is the most consequential of the six.

**Missing decision.** What each seed contributes, how candidates are compared
across seeds, and what `k` in `k/30` counts.

**Why scientifically material.** `structural_acceptance.StructuralCandidate`
documents `selection_fraction` only as "fraction of 30 seeds that selected
this", and `rc3_record.CaseExecutionRecord` documents `selection_count` only as
"k, out of 30". Neither says what "selected" means. The frozen predicate then
compares `k/30` against a gate of `20/30`, so the gate is frozen and its input
is not. `selection_count`, `valid_r2` and `complexity` are all outputs of this
one rule, and `complexity` in turn drives the null-threshold lookup. G2, the
primary family-recovery endpoint, is scored on the expression this rule returns.

The repository contains two mutually incompatible frozen rules, on two other
tracks, and the second exists specifically because the first failed:

*Rule A, Phase 3 and Phase 4.* Per seed, the complexity elbow at absolute
tolerance 0.01 over that seed's Pareto front. Across seeds, cluster picks by
numerical fingerprint into expression families, take the largest family, require
its share to be at least 20/30, tie-break on lower complexity then higher
validation R2 then lexicographic string, and advance a maximum of one candidate.
Recorded in `PHASE3_PREREGISTRATION.md` and `PHASE4_FROZEN_DISCOVERY_PROTOCOL.md`.

*Rule B, Type 2.* Retain the whole Pareto band at the same 0.01 tolerance rather
than collapsing it to its cheapest member, group by Type 2 family (support,
sign, exponent, monotonicity, dense predictive agreement) rather than by exact
numerical fingerprint, report the family, and report the number of distinct
algebraic forms inside it. Recorded in `TYPE2_SELECTION_RULE.md` and implemented
in `muru.objval.select`.

Neither may be silently imported.

Rule A carries a known, reproducible defect that is directly adverse to what
this benchmark measures. `PHASE3_DECISION.md` and `BACKLOG.md` I7 record it:

> The elbow rule resolves near-degenerate Pareto fronts in favour of the wrong
> expression. With a tolerance of 0.01 absolute R2, a complexity-6 approximation
> that sits 0.004 R2 below the complexity-13 planted form is preferred to it, in
> 30 of 30 seeds, at every noise level tested.

Search capability was 100 percent and system report rate 0 to 10 percent. That
is precisely the G2 recovery question. Phase 3 also recorded that any fix
requires recalibrating the null thresholds, because the threshold is conditioned
on the complexity the rule selects.

Rule B was chosen after seeing that failure. `OBJECTIVE_ALIGNMENT_AMENDMENT.md`
is explicit that old Phase 3 artifacts are admissible for exactly one purpose,
to choose the Type 2 selection rule, and for no other. Importing it into the
paper benchmark would carry a result-informed choice into a benchmark that
claims prospective freezing.

There is a third, weaker candidate: master plan section 13.4, "the reported
candidate is chosen by the complexity elbow, not by best fit", and section 13.5,
rank by validation error at matched complexity then by selection frequency
across the 30 seeds. A1 and A3.3 do cite the master plan as an authority for
tolerances, so it cannot be dismissed outright, but it does not resolve
per-seed retention or cross-seed grouping at the precision this record requires.

One point in favour of any eventual choice: the A3.2 null statistic is
`S(w,c) = max over 30 seeds of best validation R2 at complexity <= c`, which
upper-bounds what any selection rule can report at complexity `c` within a
world. `TYPE2_NULL_CALIBRATION.md` states this property explicitly. The
preserved VALID threshold table therefore stays conservative under any of the
candidate rules, so the calibration does not have to be repeated for this
decision alone, and equally does not settle it.

**Options, none selected.** (a) Rule A unchanged. (b) Rule B unchanged. (c)
Master plan 13.4/13.5 stated to the required precision. (d) Carry the whole
Pareto front forward and adjudicate every knee against the null, which is
candidate direction 2 in `PHASE3_DECISION.md`. (e) Report variable support and
scaling exponents as the claim and treat functional form as unidentified, which
is candidate direction 3 there.

**Minimum governance action.** A prospective amendment, in the A3.x series,
binding: what each seed contributes, the per-seed retention rule and its
tolerance, the cross-seed equivalence relation used to group candidates, the
definition of `k`, the tie-break order, the number of candidates that advance,
and the definitions of `valid_r2` and `complexity` for the advanced candidate.
The amendment must state its own contamination position with respect to Phase 3
outcomes, since both leading precedents are entangled with them.

### 4.5 Blocker 5: `invalid_fraction`

**Missing decision.** The numerator, and the evaluation domain it is a fraction
of.

**Why scientifically material.** A3.1 freezes the gate, `invalid_fraction <=
0.005`, and freezes nothing about what counts as invalid or where it is counted.
The benchmark's own strict evaluator, `contract.validate_candidate`, is
all-or-nothing: it raises if any prediction is non-finite or complex. That is
structurally incompatible with a gate that tolerates up to 0.5 percent invalid
points, so the frozen benchmark modules do not, between them, define the
quantity the frozen predicate consumes. The protected-numerics definition that
would supply it (denominator magnitude below 1e-12, `inv` argument below 1e-12,
`log` argument at or below zero, `sqrt` of a negative, overflow at or above
1e12, NaN or non-finite) exists only in `SYMBOLIC_SEARCH_SPEC.md`, a Phase 3
artifact. `contract.py` also carries an unbound `grammar_version`, consistent
with `PENDING_LOCK`.

**Historical precedents.** Phase 3 protected numerics and its 0.5 percent
rejection rule. `TYPE2_ENGINE_VALIDATION.md`, which plants `1/(a-a)` and
`log(a-b)` at `invalid_fraction` 1.0.

**Options, none selected.** (a) Adopt the Phase 3 protected numerics and its
evaluation domain by amendment. (b) Define invalidity against the benchmark's
own covariate frames. (c) Keep `contract.validate_candidate` all-or-nothing and
amend the gate accordingly.

**Minimum governance action.** A prospective amendment binding the invalidity
predicate, the evaluation domain, and its relationship to
`contract.validate_candidate`, plus a declared `grammar_version`.

### 4.6 Blocker 6: falsification rung semantics for a benchmark case

**Missing decision.** What each of the six required rungs does on a benchmark
case, and what constitutes `PASS`, `FAIL` or `NOT_APPLICABLE`.

**Why scientifically material.** A3.1 and `structural_acceptance` freeze the
membership of the six rungs, their emission order, and the rule that
`NOT_APPLICABLE` is never counted as `PASS`. `check_falsification_harness`
consumes an already-computed mapping. No frozen benchmark artifact defines the
perturbation, the statistic or the pass criterion for any rung. Gate 8 of the
acceptance predicate is the last gate before `STRUCTURAL_ACCEPTED`, so rung
criteria set the acceptance rate directly, and through it G2 and all three G3
components.

**Historical precedents.** `FALSIFICATION_HARNESS.md`, generated from the Phase 3
preregistration, defines the ladder and its constant-refitting convention
(re-fit affine scale and offset by weighted least squares on training only, then
evaluate on the holdout). Phase 3's `muru/discovery/falsify.py`. The observed
Phase 3 pass counts in that same document are results, and were seen.

**Options, none selected.** (a) Adopt the Phase 3 rung definitions by amendment.
(b) Define benchmark-specific rung semantics against the synthetic case
geometry, where F5 scaffold holdout and F9 energy-subset stability have exact
synthetic analogues. (c) Reduce the required set, which would change the
predicate and is therefore a science change.

**Minimum governance action.** A prospective amendment binding, per rung, the
perturbation, the statistic, the pass criterion, and the applicability rule,
before any partition is opened.

### 4.7 Case-level failure semantics

**Missing decision.** What a case reports when some of its 30 seeds fail.

**Why scientifically material.** The per-seed statuses are frozen
(`COMPLETED_WITH_CANDIDATES`, `COMPLETED_NO_CANDIDATE`, `EXECUTION_FAILURE`),
and the calibration aggregation rule is frozen for worlds: any failed seed
forces that world's whole `S(w,1..20)` row to +1.0, which is conservative
because it can only raise a threshold. That rule is calibration-specific and
inverts for a case: the conservative direction for a null threshold is not the
conservative direction for an acceptance claim. Nothing states whether a case
with failed seeds is `UNEVALUABLE`, is scored on its surviving seeds, or fails
outright, and `UNEVALUABLE` is a G3 violation that stays in the denominator, so
the choice moves G3 directly.

**Minimum governance action.** Bind the case-level aggregation of per-seed
failures, including the denominator used for `k` when seeds fail.

---

## 5. Historical-precedent-only behaviour explicitly rejected

None of the following was implemented, and none may be adopted without a
prospective amendment.

| Behaviour | Source | Why rejected here |
|---|---|---|
| Complexity-elbow per-seed pick at tolerance 0.01 | `PHASE3_PREREGISTRATION.md`, `PHASE4_FROZEN_DISCOVERY_PROTOCOL.md`, master plan 13.4 | Not bound to the paper benchmark; carries the reproducible defect recorded as `BACKLOG.md` I7 |
| Numerical-fingerprint cross-seed clustering, largest family, max 1 candidate advancing | same | Same, plus the tie-break order is Phase 4's, not the benchmark's |
| Type 2 retained Pareto band with family grouping by support/sign/exponent/monotonicity/dense agreement | `TYPE2_SELECTION_RULE.md`, `muru.objval.select` | Chosen after seeing Phase 3 outcomes; `OBJECTIVE_ALIGNMENT_AMENDMENT.md` restricts that use to the Type 2 study |
| Phase 3 protected numerics and the 0.5 percent invalid-point rejection | `SYMBOLIC_SEARCH_SPEC.md` | Not bound to the benchmark; incompatible as written with `contract.validate_candidate` |
| Phase 3 falsification rung definitions and constant re-fitting convention | `FALSIFICATION_HARNESS.md` | Not bound to the benchmark; the document also reports seen Phase 3 outcomes |
| RC2 fold-local estimator and adequacy stage | `engineering/muru-completion` `c7c2332` | On a branch without `paper_benchmark`; A1 defers `Phi` to a locked implementation that does not exist |
| Phase 3 T2 target construction (inverse-variance weighted estimated scale, unit geometric mean) | `SYMBOLIC_SEARCH_SPEC.md` | Defined over 12 real Tier A descriptors, a different track |
| Calibration seed band `2_110_000_000 + ...` reused for cases | `calibration_contract.derive_calibration_seeds` | Would collide 9,600 case seeds with the 3,000 already spent on the null |
| Calibration "any failed seed forces +1.0" aggregation applied to cases | `calibration_contract` | Conservative for a threshold, not for an acceptance claim |

---

## 6. Governance observations, not blockers

These do not block RC5 and are recorded so they are not lost.

1. **`exact_algebra` has no bound contract.** The frozen registry assigns the
   endpoint to F01, F08, F09, F10 and F17, which is 60 held-out cases, and
   `MURU_PAPER_BENCHMARK_METRICS.md` names it beside parameter recovery and
   predictive equivalence. A3.3 and A3.4 bound the other two and left this one.
   `CaseExecutionRecord` has no field for it, so RC5 does not need it, but it
   will need binding before held-out scoring reports it.

2. **Calibration and case validation-set sizes differ.** A3.2 assigned
   calibration worlds an 18/6/6 scaffold split (108/36/36 compounds) and held
   60/20/20 authoritative for calibration, explicitly leaving benchmark case
   partitions at the generator's 20/5/5 (120/30/30). A case therefore scores
   `valid_r2` on 30 compounds against a threshold calibrated on 36. This was
   adjudicated in A3.2 and is not reopened here; it is noted because the null
   statistic's conservatism argument is a within-world argument.

3. **The Julia identity verifier still has no prospective caller.**
   `pb_37_environment_closure.assert_julia_identity()` exists and
   `configs/rc4_1_julia_identity_proof.json` records a live reading. Wiring it
   ahead of the first scientific seed is pure engineering and was scoped to
   Gate 2.2, which RC5 did not reach.

---

## 7. Disposition

Development remains unopened. Held-out remains sealed. Challenge was not run.
Confirmation remains sealed. No engine was implemented, no manifest was
instantiated, and no seed was spent.

The next authorization should be a science-governance task that binds the six
decisions in section 4, prospectively and blind to every partition, in the A3.x
amendment series. Once those are frozen, RC5 becomes what it was intended to
be: an engineering realization with nothing left to choose.

**RC5 BLOCKED: UNFROZEN SCIENTIFIC EXECUTION SEMANTICS REQUIRE GOVERNANCE**
