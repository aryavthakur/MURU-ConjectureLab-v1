# MURU pre-results table shells

Companion to `MURU_MANUSCRIPT_PRE_RESULTS.md`.

**Filling rule.** Cells whose value is a frozen design fact or a verified
historical observation are populated. Cells requiring a prospective outcome
carry `[PROSPECTIVE RESULT TO INSERT]` and must not be filled from
expectation, extrapolation, or a historical analogue. Cells whose frozen source
was not located carry `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`.

Governance base: `07c64c8` (`engineering-rc3-1-a3-2`).

---

## Table 1. Benchmark partitions and case families

**Status: fully populated from frozen sources.** Counts verified by enumerating
`artifacts/paper_benchmark_case_manifest.json` (380 cases) against
`src/muru/paper_benchmark/registry.py`.

Caption: Twenty prospectively frozen case families, their scientific question,
their truth content, and their case counts in each partition. Every family
contributes 4 Development, 12 Held-out and 3 Challenge cases. Each case contains
180 synthetic compounds in 30 scaffold groups of 6, split 20/5/5 scaffold groups
(120/30/30 compounds), on the energy grid 15, 30, 45, 60, 75, 90.

| Family | Name | Scientific question | Scalar truth | M0 truth | Symbolic truth | Dev | Held-out | Challenge | Applicable endpoint groups |
|---|---|---|---|---|---|---:|---:|---:|---|
| F01 | noiseless scalar collapse | recover unambiguous collapse | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F02 | moderate-noise scalar collapse | recover under moderate noise | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F03 | stronger realistic noise | characterize graceful degradation | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F04 | missing-one-energy | recover with declared missingness | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F05 | boundary-scale | detect profile boundaries | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, boundary hit |
| F06 | no molecule-specific scalar truth | reject an unsupported scalar | no | M1 | none | 4 | 12 | 3 | M1 sensitivity |
| F07 | mass-only g truth | avoid invented non-mass structure | yes | M0 | mass only | 4 | 12 | 3 | scalar, parameter recovery, false extra structure, structural safety |
| F08 | simple descriptor law | recover a monotone descriptor law | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F09 | nonlinear descriptor law | recognize saturation | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F10 | interaction law | recognize interpretable interaction | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F11 | irrelevant distractors | exclude independent nuisance variables | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F12 | correlated distractors | separate support from correlation | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F13 | horizontal-shape violation | detect M1 | no | M1 | none | 4 | 12 | 3 | M1 sensitivity |
| F14 | high-energy vertical violation | detect M2 | no | M2 | none | 4 | 12 | 3 | M2 sensitivity |
| F15 | low-energy vertical violation | detect M3 | no | M3 | none | 4 | 12 | 3 | M3 sensitivity |
| F16 | combined mild non-scalar violation | flag combined violations | no | M1+M2+M3 | none | 4 | 12 | 3 | M1, M2, M3 sensitivity, scored independently |
| F17 | equivalent symbolic forms | canonicalize equivalent laws | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic, exact algebra |
| F18 | algebraically difficult, predictively simple | separate prediction from exact algebra | yes | M0 | defined | 4 | 12 | 3 | scalar, symbolic |
| F19 | target-specific null worlds | prevent the specified null structure from being accepted | by variant | by variant | none / mass-only allowance | 4 | 12 | 3 | false null structure, structural safety; **plus the scalar endpoints for F19A and F19B only**; response structure diagnostic for F19C. See variant rows |
| F20 | adversarial worlds | reject or flag specified traps | no | not applicable | none | 4 | 12 | 3 | false adversarial structure, structural safety |
| **Total** | | | | | | **80** | **240** | **60** | |

### Table 1a. F19 and F20 variant semantics

Variants cycle across replicates, so each variant receives 4 of the 12 Held-out
cases in its family.

| Variant | Mechanism | Scalar truth | M0 truth | Symbolic truth | Correct behaviour |
|---|---|---|---|---|---|
| F19A | descriptor-link permutation | yes | M0 | none | Trajectories preserved; accepting descriptor structure is false-null structure. Mass-only acceptance permitted; unsupported non-mass structure is unsafe. **Carries the scalar endpoints** (G1, M0 specificity, trajectory prediction, profile stability, scalar target yield) |
| F19B | mass-preserving target null | yes | M0 | mass-only allowance | Mass-only truth preserved; accepted non-mass structure is unsafe. **Carries the scalar endpoints** |
| F19C | response-cell resampling | no | not applicable | none | Destroyed trajectories must be flagged non-evaluable. An accepted structural claim is unsafe; legitimate non-acceptance is safe; `UNEVALUABLE` is a violation. **Excluded from scalar, M0 and symbolic denominators** |
| F20A | latent driver | no | not applicable | none | An accepted structural claim is unsafe |
| F20B | measurement coupling | no | not applicable | none | An accepted structural claim is unsafe |
| F20C | out-of-grammar trap | no | not applicable | none | Generating relationship is not representable in the frozen grammar; an accepted structural claim is unsafe |

### Table 1b. Held-out denominators by endpoint

Verified by enumeration over the 380-case manifest. These are the frozen
denominators; they are never adjusted after execution.

The four 164-denominator endpoints are **not** simply "13 families at 12". They
are 13 families at 12 (156) plus the F19A and F19B variants at 4 each (8), since
those two carry scalar truth while their symbolic structure is null. F19C is
excluded. Similarly, exact algebra 60 is five families (F01, F08, F09, F10, F17)
at 12, and parameter recovery 156 is the 12 symbolic families plus F07.

| Endpoint | Development | **Held-out** | Challenge |
|---|---:|---:|---:|
| scalar competence (G1) | 55 | **164** = 156 + F19A/F19B 8 | 41 |
| family recovery (G2) | 48 | **144** | 36 |
| principal structural safety (G3) | 12 | **36** | 9 |
| support recovery | 48 | **144** | 36 |
| parameter recovery | 52 | **156** | 39 |
| predictive equivalence | 48 | **144** | 36 |
| exact algebra | 20 | **60** | 15 |
| M0 specificity | 55 | **164** | 41 |
| M1 sensitivity | 12 | **36** | 9 |
| M2 sensitivity | 8 | **24** | 6 |
| M3 sensitivity | 8 | **24** | 6 |
| trajectory prediction | 55 | **164** | 41 |
| profile stability | 55 | **164** | 41 |
| scalar target yield | 55 | **164** | 41 |
| boundary hit | 4 | **12** | 3 |
| false extra structure (F07) | 4 | **12** | 3 |
| false null structure (F19) | 4 | **12** | 3 |
| false adversarial structure (F20) | 4 | **12** | 3 |
| response structure diagnostic (F19C) | 1 | **4** | 1 |

### Table 1c. Frozen adequacy-violation amplitudes

Source: `src/muru/paper_benchmark/generator.py`. F16's M3 amplitude is the
Amendment A2 repair.

| Constant | Value | Family |
|---|---|---|
| `M1_HORIZONTAL_AMPLITUDE` | 0.45 | F13 standalone |
| `M2_HIGH_ENERGY_AMPLITUDE` | 0.18 | F14 standalone |
| `M3_LOW_ENERGY_AMPLITUDE` | 0.22 | F15 standalone |
| `M3_CEILING_CLIP` | (0.6, 0.99) | F15, reused by F16 |
| `COMBINED_M1_AMPLITUDE` | 0.15 (attenuation 1/3) | F16 |
| `COMBINED_M2_AMPLITUDE` | 0.05 (attenuation 5/18) | F16 |
| `COMBINED_M3_AMPLITUDE` | 11/180 (attenuation 5/18, the smaller of F16's two existing ratios) | F16, Amendment A2 |

Per-family noise levels, F04 missingness pattern and F05 boundary parameters:
`[METHOD DETAIL REQUIRES VERIFIED SOURCE]`. To be extracted from the frozen
generator and truth manifest before submission, without opening any outcome.

---

## Table 2. Frozen endpoints and success criteria

**Status: fully populated from frozen sources.**

Caption: Prospectively frozen endpoints, their role, denominator, gate and
failure handling. Roles were assigned before any prospective execution and are
not conditioned on observed performance. All secondary endpoint specifications
(Parameter Recovery on 156 cases at canonical anchor $\mathbf{x}_0$ and
Predictive Equivalence on 144 cases over 2,160 reference points across 12
case-shaped frames) are frozen under Amendment A3.4.

Reproduce Section 6 of `MURU_MANUSCRIPT_PRE_RESULTS.md` in full as Table 2.

### Table 2a. Structural acceptance predicate

Ordered; the first failing gate determines the typed state. Truth-blind: family
correctness is not part of acceptance.

| Order | Gate | Frozen value | State on failure |
|---:|---|---|---|
| 1 | A1 adequacy | only `M0_NOT_REJECTED` proceeds | `REJECTED_A1_INADEQUATE` (rejection states) or `UNEVALUABLE` (failure, timeout, contract states) |
| 2 | null-calibrated fit | `valid_r2 > null_threshold[min(complexity, 20)]` | not accepted |
| 3 | seed stability | `selection_fraction >= 20/30` | not accepted |
| 4 | complexity cap | `complexity <= 20` | not accepted |
| 5 | invalid fraction | `invalid_fraction <= 0.005` | not accepted |
| 6 | effective support | non-empty | not accepted |
| 7 | ceiling | `ceiling_fraction >= 0.80` OR `ceiling_r2 < 0.05` (waiver) | not accepted |
| 8 | falsification harness | F1, F4, F5, F7 (influence-drop component), F9, F10 all pass; `NOT_APPLICABLE` never counts as `PASS`; F8 is labelling, not a gate | not accepted |

Ceiling estimator:
`HistGradientBoostingRegressor(max_iter=150, max_depth=3, min_samples_leaf=20, random_state=0)`,
bound to `scikit-learn==1.9.0`, trained on the train partition, scored on the
test partition, frozen covariate order equal to the grammar primitive order.

---

## Table 3. Calibration summary

**Status: design columns populated; every outcome column pending.**

Caption: Structural-null calibration under Amendments A3.1 and A3.2. One hundred
worlds, 30 search seeds each. The base target is a global permutation of the
frozen-law target values across all 180 compound identities, applied before any
null-family transformation and before any partition use.

### Table 3a. Design (frozen)

| Item | Frozen value |
|---|---|
| Worlds | 100 |
| Allocation | `target_permuted_across_compounds` 34; `descriptors_permuted_across_compounds` 33; `gaussian_targets_with_observed_variance` 33 |
| Excluded construction | `within_compound_energy_permutation` (unconstructible in RC3.1) |
| Compounds per world | 180 in 30 scaffold groups of 6 |
| Calibration split | 18 / 6 / 6 scaffolds = 108 / 36 / 36 compounds |
| Seeds per world | 30 (3,000 total) |
| World ID | `PB\|NCAL\|{construction}\|r{index:03d}`, index 0..99 |
| `PB_SEED_BASE` | 2,110,000,000 |
| `PB_SEED_SPREAD` | 370,000 |
| Base-target seed namespace | `PB\|NCAL\|<world_id>\|BASE_TARGET` |
| Split seed namespace | `PB\|NCAL\|<world_id>\|SPLIT` |
| Statistic | max over 30 seeds of best validation R2 at complexity <= c; prefix-monotone |
| Quantile | 0.95, `numpy.quantile(method="linear")`, then `np.maximum.accumulate` |
| Bootstrap | 2,000 world-level resamples, seed 20260812, reporting only |
| Validity floor | at least 95 of 100 worlds with zero `EXECUTION_FAILURE` seeds |
| Any-failure rule | one `EXECUTION_FAILURE` seed sets that world's entire S(w, 1..20) to +1.0 |

### Table 3b. Execution outcome (pending)

| Quantity | Value |
|---|---|
| Worlds executed | `[PROSPECTIVE RESULT TO INSERT]` |
| Worlds with zero execution-failure seeds | `[PROSPECTIVE RESULT TO INSERT]` |
| Validity verdict against 95/100 | `[PROSPECTIVE RESULT TO INSERT]` |
| Seed-runs completed of 3,000 | `[PROSPECTIVE RESULT TO INSERT]` |
| `COMPLETED_NO_CANDIDATE` seeds | `[PROSPECTIVE RESULT TO INSERT]` |
| `EXECUTION_FAILURE` seeds | `[PROSPECTIVE RESULT TO INSERT]` |
| Wall-clock runtime | `[PROSPECTIVE RESULT TO INSERT]` |

### Table 3c. Threshold table (pending)

| Complexity c | Null median | Threshold T(c) | 95% bootstrap interval |
|---:|---|---|---|
| 1 to 20, one row each | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |

### Table 3d. Per-construction diagnostic (pending)

This breakdown is the diagnostic that Amendment A3.2 exists to make
interpretable. Whether the three constructions still differ systematically after
the global base-target permutation is a prospective observation and is not
predicted here; the pre-correction values below are the reference point against
which the observed breakdown will be read.

| Construction | Worlds | p95 at c=4 | p95 at c=10 | p95 at c=20 | mean constant-model validation R2 |
|---|---:|---|---|---|---|
| `target_permuted_across_compounds` | 34 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `descriptors_permuted_across_compounds` | 33 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `gaussian_targets_with_observed_variance` | 33 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |

Pre-correction reference values, verified and citable as motivation only
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md`, 20 worlds per construction): mean
constant-model validation R2 was -0.055, -0.246 (minimum -1.28) and -0.077
respectively. These are diagnostic measurements of the rejected provisional
design, not calibration results.

---

## Table 4. Development results

**Status: entirely pending. Development must not be opened to fill this.**

Caption: Development sanity check, 80 cases, under the A3.1/A3.2 contract.
Development performance cannot alter architecture, generator, coefficients,
endpoints, grammar or thresholds.

| Endpoint | Denominator | Numerator | Rate | 95% Wilson |
|---|---:|---|---|---|
| scalar competence | 55 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| family recovery | 48 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| principal structural safety | 12 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| support recovery | 48 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| parameter recovery | 52 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| predictive equivalence | 48 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| exact algebra | 20 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| M0 specificity | 55 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| M1 / M2 / M3 sensitivity | 12 / 8 / 8 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| Engine failures | n/a | `[PROSPECTIVE RESULT TO INSERT]` | | |
| Runtime, CPU time, peak memory | n/a | `[PROSPECTIVE RESULT TO INSERT]` | | |

Historical note, not a result: 80 Development cases were executed once before
Amendment A3.1, at which time G2 and G3 were not producible. Those G2/G3 scores
do not exist. A rerun under the A3.1/A3.2 contract is required.

---

## Table 5. Held-out primary outcomes

**Status: entirely pending. Held-out is sealed.**

Caption: The three frozen gates on the 240-case Held-out partition. Denominators
are frozen from case applicability; gates were fixed before execution.

| Gate | Definition | Denominator | Numerator | Rate | 95% Wilson interval | Gate | Verdict |
|---|---|---:|---|---|---|---|---|
| G1 scalar competence | Spearman >= 0.80 AND MAE <= 0.80 x baseline AND `M0_NOT_REJECTED` | 164 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | lower >= 0.70 | `[PROSPECTIVE RESULT TO INSERT]` |
| G2 family recovery | support MATCH AND family MATCH | 144 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | lower >= 0.70 | `[PROSPECTIVE RESULT TO INSERT]` |
| G3 structural safety | unsafe structural acceptance | 36 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | upper <= 0.15 | `[PROSPECTIVE RESULT TO INSERT]` |
| **Umbrella claim** | preconditions AND G1 AND G2 AND G3 | | | | | all three pass | `[PROSPECTIVE RESULT TO INSERT]` |

### Table 5a. Secondary and diagnostic endpoints, Held-out

| Endpoint | Denominator | Numerator | Rate | 95% Wilson |
|---|---:|---|---|---|
| support recovery | 144 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| parameter recovery (joint) | 156 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| mass exponent ($p_{\text{mass}}$) | 156 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| descriptor coupling ($c_{\text{desc}}$) | 84 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| predictive equivalence | 144 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| exact algebra | 60 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| M0 specificity | 164 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| M1 sensitivity | 36 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| M2 sensitivity | 24 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| M3 sensitivity | 24 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| trajectory prediction | 164 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| profile stability | 164 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| scalar target yield | 164 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| boundary hit | 12 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| response structure diagnostic | 4 | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |

---

## Table 6. Symbolic discovery outcomes by truth family

**Status: taxonomy populated; all outcomes pending.**

Caption: Recovery decomposed by level. Support, family, coefficients, prediction
and exact algebra are separate claims; historical evidence shows they diverge.
Columns are ordered from weakest to strongest claim, left to right.

| Truth family | Held-out cases | Support MATCH | Family MATCH | **G2 (both)** | Parameter recovery | Predictive equivalence | **Exact algebra** | Distinct functional classes in the reported result |
|---|---|---|---|---|---|---|---|---|
| `mass_affine_descriptor` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `mass_power` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `mass_saturating_descriptor` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `mass_interaction` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `mass_exponential_descriptor` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| `FAMILY_AMBIGUOUS` | n/a | n/a | count: `[PROSPECTIVE RESULT TO INSERT]` | | | | | |
| `SUPPORT_UNRESOLVED` | n/a | count: `[PROSPECTIVE RESULT TO INSERT]` | | | | | | |
| **Total** | **144** (G2); **60** (exact algebra) | | | | **156** | **144** | | |

The mapping from case family (F01 to F18) to truth family is a frozen property of
the truth payloads and must be read from
`artifacts/paper_benchmark_truth_manifest.json` before submission:
`[METHOD DETAIL REQUIRES VERIFIED SOURCE]`.

---

## Table 7. False discovery and refusal cases

**Status: structure and correct-behaviour column populated; outcomes pending.**

Caption: The 36 G3 opportunities and the refusal families. `UNEVALUABLE` is
counted as a violation and retained in the denominator: a pipeline that avoids
unsafe acceptances by failing to evaluate has not demonstrated safety.

| Component | Variant | Held-out cases | Correct behaviour | Unsafe events | Rate | 95% Wilson |
|---|---|---:|---|---|---|---|
| F07 false extra structure | base | 12 | accept mass-only; reject richer structure | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| F19 false null structure | F19A | 4 | mass-only acceptance permitted; unsupported non-mass structure unsafe | `[PROSPECTIVE RESULT TO INSERT]` | | |
| F19 false null structure | F19B | 4 | mass-only permitted; accepted non-mass structure unsafe | `[PROSPECTIVE RESULT TO INSERT]` | | |
| F19 false null structure | F19C | 4 | flag non-evaluable; accepted structural claim unsafe; `UNEVALUABLE` is a violation | `[PROSPECTIVE RESULT TO INSERT]` | | |
| F19 subtotal | | 12 | | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| F20 false adversarial structure | F20A | 4 | reject latent-driver trap | `[PROSPECTIVE RESULT TO INSERT]` | | |
| F20 false adversarial structure | F20B | 4 | reject measurement-coupling trap | `[PROSPECTIVE RESULT TO INSERT]` | | |
| F20 false adversarial structure | F20C | 4 | reject out-of-grammar trap | `[PROSPECTIVE RESULT TO INSERT]` | | |
| F20 subtotal | | 12 | | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` |
| **G3 aggregate** | | **36** | | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]` | `[PROSPECTIVE RESULT TO INSERT]`; gate: upper <= 0.15 |
| F06 no scalar truth | base | 12 | reject M0 in favour of M1; refusal is correct | `[PROSPECTIVE RESULT TO INSERT]` | | |

Legitimate refusals are correct outcomes and are not penalised.

---

## Table 8. Challenge and stress test outcomes

**Status: entirely pending. Descriptive only; enters no primary denominator.**

Caption: The 60 Challenge cases, three per family. Challenge results are
descriptive stress and boundary evidence and cannot alter any gate verdict.

| Family | Challenge cases | Endpoint(s) applicable | Outcome |
|---|---:|---|---|
| F01 to F20, one row each | 3 each | see Table 1b Challenge column | `[PROSPECTIVE RESULT TO INSERT]` |
| **Total** | **60** | | |

| Aggregate stress measure | Value |
|---|---|
| Challenge scalar competence (41 applicable) | `[PROSPECTIVE RESULT TO INSERT]` |
| Challenge family recovery (36 applicable) | `[PROSPECTIVE RESULT TO INSERT]` |
| Challenge structural safety (9 applicable) | `[PROSPECTIVE RESULT TO INSERT]` |
| Challenge exact algebra (15 applicable) | `[PROSPECTIVE RESULT TO INSERT]` |

---

## Table 9. Historical evidence versus prospective evidence

**Status: fully populated. Historical column is verified; prospective column is
pending by design.**

Caption: Historical synthetic evidence is background, method development, or
supporting context. It is never the prospective primary endpoint, and the two
columns are never combined into a single rate.

| Question | Historical evidence (CLASS A, already observed) | Prospective evidence (CLASS C, pending) |
|---|---|---|
| Does the pipeline recover variable support? | Type 2 G1B moderate: 20/20 block supports recovered | Support recovery on 144 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it recover mathematical family? | Type 2 G1B moderate: dense-lattice family recovery 16/20 **measured, not gated**; the study's composite success gate (support, exponent, shape) passed 17/20 (85%). Neither is the G2 definition | G2 on 144 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it recover exact algebra? | Phase 3 selected functional and symbolic recovery 0% at every G1B noise regime; Type 2 symbolic equivalence 0 in G1A, G1B, G1C and G3 | Exact algebra on 60 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it recover scaling exponents? | Type 2 G1B moderate: mass exponent median 0.500, range [0.448, 0.540], 20/20 within +/-0.15; exponent recovery 18/20 | Parameter recovery on 156 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it manufacture structure in pure nulls? | Phase 3 and Type 2 each: 0/100 accepted, Clopper-Pearson 95% [0.0000, 0.0362] | G3 on 36 Held-out opportunities: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it refuse mass-only worlds? | Type 2 G3 block: 0/8 non-mass structural claims (95% upper 0.3694). Phase 3: 0/8 | F07 on 12 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it refuse latent-confounded worlds? | Type 2 G5: 0/8 (95% upper 0.3694). Phase 3 G5: 1/8 | F20A on 4 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it refuse measurement-coupling worlds? | Type 2 GC: 0/9 (95% upper 0.3363). Phase 3 GC: 0/9 | F20B on 4 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Does it refuse non-compressible worlds? | Type 2 G2: 0/8 accepted (95% upper 0.3694); H-MAIN rejected 8/8 | F06 on 12 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Is structure beyond mass established? | Type 2 F8 labelling: 1/19 accepted G1B moderate worlds. Weak | F8 labelling, reported as a label and never a gate: `[PROSPECTIVE RESULT TO INSERT]` |
| Is the null calibration clean for a scalar target? | No. Within-compound energy permutation set the pooled gate almost alone (Type 2 p95 0.7228 at c=20 against 0.0835 to 0.1509) | Construction excluded prospectively; per-construction breakdown: `[PROSPECTIVE RESULT TO INSERT]` |
| Was the target estimated fold-locally? | No. Historical `fit_collapse` was transductive: perturbing one trajectory changed other compounds' scales by up to 0.0987 | Frozen execution boundary requires training-only shared objects: `[PROSPECTIVE RESULT TO INSERT]` for its measured behaviour |
| Was symbolic evaluation strict? | No. Complex outputs were cast to float; historical reach unquantified | Strict evaluation with typed `SUPPORT_UNRESOLVED`: `[PROSPECTIVE RESULT TO INSERT]` |
| Were boundary hits recorded? | No. Prevalence unknown | F05 boundary hit on 12 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]` |
| Is missing-energy robustness established? | No. 0.97% dropout, at least five energies retained, no coverage guard or stress study | F04 on 12 Held-out cases: `[PROSPECTIVE RESULT TO INSERT]`; still bounded |
| Is there independent-engine corroboration? | No. The frozen gate failed (15% support, 25% exponent, against 50%), and a later audit showed the comparison arm itself failed C0/C1/C2 competence | None. No corroborating engine is included prospectively |
| Real-data claims ladder | L3, unchanged by every synthetic study | Unchanged. No real-data claim is available from this work |
| Phase 4 authorization | Phase 3: STOP BEFORE PHASE 4. Type 2: DO NOT AUTHORIZE PHASE 4 | Unchanged. This benchmark does not authorize Phase 4 |

---

## Table 10. Known limitations and evidence boundary

**Status: fully populated. This table is complete now and does not wait for
results.**

Caption: What this study can and cannot support, separated into limitations of
the evidence class, live limitations of the prospective system, and historical
defects that the prospective design closes.

| # | Limitation | Kind | Status in the prospective system | Effect on claims |
|---|---|---|---|---|
| L1 | Synthetic evidence does not establish real-world accuracy | evidence class | inherent | No real-data claim of any kind |
| L2 | Five truth families over five synthetic covariates may not span real fragmentation mechanisms | evidence class | inherent; F20C deliberately sits outside the grammar | Recovery does not generalise beyond the tested space |
| L3 | Collision-energy conventions differ between instruments | evidence class | no cross-instrument mapping provided | No transferability claim |
| L4 | Chemical realism absent by construction | evidence class | inherent | No chemical interpretation of any recovered expression |
| L5 | No prospective physical acquisition | evidence class | inherent | No new instrumental evidence |
| L6 | Mass and descriptor confounding not eliminated | **live** | F07, F11, F12, F20A, F20B test it; G2 contract forbids proxy substitution | Structure-beyond-mass claims remain guarded |
| L7 | Symbolic expressions can be non-identifiable | **live** | endpoints separated by claim level | Family recovery never implies exact algebra |
| L8 | Exact equation recovery may be unstable | **live** | measured, ungated | A low rate is a finding, not a gate failure |
| L9 | Finite calibration uncertainty | **live** | 100 worlds; 2,000-resample bootstrap reported per complexity | A margin inside the interval is inconclusive |
| L10 | Noise envelope bounded by F01 to F03 | **live** | measured | Claims restricted to tested residual scales |
| L11 | Missing-energy coverage bounded | **live** | F04 declares one missing energy; no broader stress study | No general missingness robustness claim |
| L12 | Boundary-scale denominator is small (12) | **live** | F05 records boundary hits | Rate estimate is imprecise |
| L13 | Challenge cases enter no gate | **live** | by design | Cannot rescue a failed primary gate |
| L14 | No independent-engine corroboration | **live** | single engine; historical comparison arm shown incompetent for a veto | Search-artifact status is not excluded by convergence evidence |
| L15 | Python 3.13.12 against the plan's stated 3.12 target | **live**, procedural | full stack verified working; nothing caps below 3.13 | Recorded deviation, not a scientific limitation |
| C1 | FM-05 scalar-null information preservation | **closed** | construction excluded and made unconstructible | Calibration no longer dominated by a level-preserving null |
| C2 | Scaffold-structured null base target | **closed** | A3.2 global permutation before any transformation or partition use | The mechanism by which a non-null family could bias the threshold permissively is removed. The effect on the threshold table was never measured, because no threshold table existed at either design |
| C3 | Calibration split not matching the written 60/20/20 | **closed** | A3.2 dedicated helper at 18/6/6 scaffolds | Specification and implementation agree |
| C4 | FM-06 transductive target construction | **closed by specification; production-path conformance pending executable-freeze verification** | frozen execution boundary: training-only shared objects, then independent per-compound estimation | The frozen boundary requires held-out target quantities to be fold-local. Production-path conformance: `[PROSPECTIVE RESULT TO INSERT]` at executable freeze |
| C5 | FM-07 complex-cast evaluator | **closed by specification and reference contract; production-path conformance pending executable-freeze verification** | strict evaluation, deterministic SymPy normalisation, typed unresolved state | The contract requires strict invalidity screening. Production-path conformance: `[PROSPECTIVE RESULT TO INSERT]` at executable freeze |
| C6 | FM-08 boundary-scale invisibility | **closed** | F05 boundary-hit endpoint with a frozen denominator | Boundary prevalence measurable |
| C7 | Unspecified adequacy decision rule | **closed** | Amendment A1 binds statistic, threshold, aggregation, failure semantics | G1's adequacy component is deterministic |
| C8 | F16 generator not honouring its declared M1+M2+M3 truth | **closed** | Amendment A2 repair; A2.1 version bump | F16 detector endpoints are scorable |
| P1 | FM-09 missing-energy robustness | **partially addressed** | F04 exists where historical work had nothing; robustness still unestablished | See L11 |
| P2 | FM-04 comparison-arm competence | **inference corrected, verdict unchanged** | non-agreement no longer supports an artifact inference; the historical gate still failed and `DO NOT AUTHORIZE PHASE 4` stands | See L14 |
