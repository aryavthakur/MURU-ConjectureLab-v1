# MURU ConjectureLab v1 Failure Decomposition

**Status:** DIAGNOSIS ONLY. No scientific code, threshold, grammar setting or search setting was changed. No production search was run. The official v1 result is unchanged and is not reinterpreted by anything in this document.

**Terminal state:** `V1 FAILURE MODES EXHAUSTIVELY CHARACTERIZED` / `NO V2 SCIENTIFIC CHANGES MADE`

Machine-readable twin: `MURU_V1_FAILURE_DECOMPOSITION.json`
Per-case taxonomies: `MURU_V1_G1_FAILURE_TAXONOMY.csv` (164 rows), `MURU_V1_G2_FAILURE_TAXONOMY.csv` (144 rows), `MURU_V1_G3_FAILURE_TAXONOMY.csv` (36 rows)
Ranking: `MURU_V1_ROOT_CAUSE_RANKING.md` / `.json`

---

## 1. Method and evidence base

| Item | Value |
|---|---|
| Sealed evidence root | `.claude/worktrees/muru-heldout-a3-6/results/held_out` |
| Run commit | `8d87143d4280602323aa33ee0b5481aaef0fb4a8` |
| Frozen source tree used for all re-derivation | `.claude/worktrees/heldout-analysis-restoration/src` |
| Relationship of that tree to the run commit | additions only: 7 new analysis files, 3016 insertions, **0** deletions or modifications to any module the run executed |
| Cases | 240 |
| Searches | 7,200 |
| Execution failures | 0 |
| Searches run by this diagnosis | 0 |
| PySR imported by this diagnosis | never |

Every scientific predicate in this decomposition is the frozen one, imported and observed rather than reimplemented. Where the sealed record schema stored only a summary, the underlying quantity was re-derived from regenerated case content and then checked against the seal before being used:

- All 240 sealed `a1_case_adequacy_status` values were reproduced exactly by recomputation.
- All 144 sealed G2 `selection_count` values and cross-seed representatives were reproduced exactly by replaying the frozen `group_and_select`.
- G1, G2 and G3 counts recomputed from the taxonomy CSVs alone reproduce the restored analysis, including its Wilson bounds, to within 1e-12.

### 1.1 Two declared observability bounds

**`WITHIN_SEED_PARETO_NOT_OBSERVABLE`.** `rc5_selection` section 7.1 retains exactly one candidate per seed, `argmax(score)` of that seed's PySR Pareto front, and only that one row is persisted. The fronts are gone. So every statement below of the form "the correct expression was never generated" means **never reached cross-seed selection**, which is the population every downstream stage actually saw. It does not mean "never appeared anywhere in the search". This bound is respected throughout and is enforced by a hostile-review check.

**`A1_PER_COMPOUND_DETAIL_NOT_SEALED`.** The record schema stores only the case-level A1 status. Per-detector evaluability, per-compound boundary attribution and per-fold parameter values were recomputed. The recomputation reproduced all 240 sealed verdicts, which is the strongest available content-identity test.

---

## 2. Headline finding

**One defect explains the entire G1 gap and the entire G3 gap.**

The A1 adequacy rule declares a compound `BOUNDARY_LIMITED` when a fitted parameter sits on a bound and a single outward probe improves the sum of squared residuals by *any* amount. There is no magnitude floor:

```
if math.isfinite(obj) and obj < best_obj - 1e-12:
    unresolved = True
```

Enough compounds are removed this way that the M3 contrast falls below its 24-of-30 evaluability minimum, and the case becomes indeterminate. `structural_acceptance` gate 1 maps every A1 indeterminate state to `UNEVALUABLE`, and `g3_contract` charges `UNEVALUABLE` as a G3 violation by design. The chain is:

```
M3 low-energy plateau pins at MU_CEIL
  -> compound BOUNDARY_LIMITED for M3 (and, when the M2 asymptote also pins, for M2)
  -> M3 contrast evaluable < 24
  -> case A1 status = BOUNDARY_LIMITED
  -> G1 m0_accepted conjunct fails          (97 of 164 G1 cases)
  -> acceptance status = UNEVALUABLE        (154 of 240 cases)
  -> G3 VIOLATION                           (26 of 36 G3 cases)
```

154 of 240 cases are `BOUNDARY_LIMITED`. Zero are `INSUFFICIENT_DATA`, `NUMERICAL_FAILURE`, `MODEL_FIT_FAILURE`, `TIMEOUT` or `CONTRACT_FAILURE`.

**G2 does not share this root cause and is not rescued by fixing it.** G2 fails for independent reasons that survive every counterfactual tested.

---

## 3. A1 and G1: why only 67 of 164

### 3.1 The failure is entirely in the adequacy conjunct

G1's success predicate is `g_spearman >= 0.80 AND trajectory_mae <= 0.80 * per_energy_mean_mae AND m0_accepted`.

| Failing conjunct set | Cases |
|---|---|
| none (G1 success) | 67 |
| `m0_accepted` only | 87 |
| `m0_accepted` + `trajectory_mae_ratio` | 7 |
| `m0_accepted` + `g_spearman` | 2 |
| all three | 1 |
| **total failures** | **97** |

Every one of the 97 failures fails `m0_accepted`. No case fails a continuous condition while satisfying adequacy. This is why the stated fact that "all 67 A1-adequate cases passed the two continuous G1 competence conditions" holds: adequacy is not one bottleneck among several, it is the only gate the G1 population ever hit.

The continuous observables are comfortable, not marginal. Median `g_spearman` is 0.981 against a 0.80 gate, minimum 0.673. Median trajectory ratio is 0.362 against a 0.80 gate, maximum 0.971.

### 3.2 A1 status across the whole partition

| Population | `M0_NOT_REJECTED` | `BOUNDARY_LIMITED` | any `M0_REJECTED_*` |
|---|---|---|---|
| All 240 Held-out cases | 86 | 154 | **0** |
| G1 eligible (164) | 67 | 97 | 0 |
| G2 eligible (144) | 60 | 84 | 0 |
| G3 eligible (36) | 10 | 26 | 0 |

### 3.3 Which detector blocks, and why

| Blocking detector set | Cases (of 240) |
|---|---|
| M3 alone | 127 |
| M2 and M3 | 27 |
| none (adequate) | 86 |

M1 never blocks. The shared M0 fit is never unresolved on any compound anywhere in the partition, so M0's own admissible range is not implicated.

Unresolved compound fits, summed over all 240 cases (30 test compounds each):

| Model | Unresolved compound fits |
|---|---|
| M0 | 0 |
| M1 | 31 |
| M2 | 644 |
| M3 | 2,542 |

Bound contacts carrying a positive outward improvement, by parameter and side:

| Bound | Count | Share |
|---|---|---|
| `M3:low_energy_plateau@upper` | 7,399 | 83.9% |
| `M2:high_energy_asymptote@lower` | 1,309 | 14.8% |
| `M1:log_shape@lower` | 44 | 0.5% |
| `M2:high_energy_asymptote@upper` | 33 | 0.4% |
| `M3:low_energy_plateau@lower` | 24 | 0.3% |
| `M1:log_shape@upper` | 7 | 0.1% |
| **total** | **8,816** | |

A further 4 contacts on `M2:log_g@lower` occur on fits that were unresolved through their other parameter, and carry no positive improvement of their own.

The M3 low-energy plateau pinning at its `MU_CEIL` upper bound is 84 percent of all boundary events.

### 3.4 The triggering improvements are numerically negligible

Measured over every probe that fired, as a *relative* reduction in the fold's sum of squared residuals:

| Statistic (across the 228 cases with any trigger) | Median value |
|---|---|
| smallest triggering improvement in the case | 5.5e-4 |
| median triggering improvement in the case | 1.3e-2 |
| largest triggering improvement in the case | 6.1e-2 |

The single largest relative improvement anywhere in the partition is 0.289. In other words: **no boundary trigger in the entire Held-out partition corresponded to more than a 29 percent improvement, and the typical one corresponded to 1.3 percent.** The rule fires on slope, not on a demonstrated identifiability failure.

Counterfactual A1 status if the rule had required a relative improvement floor instead of `> 0` (the 0.0 row is the control arm and reproduces the frozen result exactly):

| Relative floor | `M0_NOT_REJECTED` | `BOUNDARY_LIMITED` | any `M0_REJECTED_*` |
|---|---|---|---|
| **0.0 (frozen rule)** | **86** | **154** | **0** |
| 1e-6 | 86 | 154 | 0 |
| 1e-4 | 86 | 154 | 0 |
| 1e-3 | 89 | 151 | 0 |
| 1e-2 | 117 | 123 | 0 |
| 1e-1 | 240 | 0 | 0 |

A worked example, case `PB|held_out|F20|r004`, compound C150 fold 0: M0 fits at SSE 3.816e-3; M3 fits at its plateau bound 0.9999 with SSE 3.808e-3; the outward probe to 1.0009 reaches 3.757e-3. The improvement is 5.1e-5 absolute, 1.3 percent relative, and the probe value is physically inadmissible because `mu` is a bounded fraction. The compound is nonetheless removed from the evaluable pool for M3.

### 3.5 Data geometry is not the cause

| Property | Value |
|---|---|
| Scaffold and compound layout | identical in all 240 cases: 20 train scaffolds / 5 test, 120 train / 30 test compounds |
| Energy grid | 6 points |
| Cases with any missing cells | 12 (one sixth missing); the other 228 are complete |
| Compounds anywhere below the 5-energy minimum | 0 |
| `INSUFFICIENT_DATA` verdicts | 0 |

Correlation of case properties with M3 evaluable-compound count:

| Predictor | r |
|---|---|
| `mu_max` (how close the low-energy response saturates to 1) | **-0.550** |
| fitted `a_lo` | **-0.455** |
| shape amplitude | -0.315 |
| missing cell fraction | -0.043 |
| observed energies median | +0.043 |

The one strong predictor is response geometry against a fixed admissible ceiling, not sparsity or missingness. This is a specification artifact, not a data problem.

### 3.6 The A1 detectors have no demonstrated power

**No detector fired on any of the 240 cases.** This includes the 48 cases whose planted truth *is* the deviation the detector exists to catch:

| Family | Planted deviation | Cases | Detections | Max wins for the target detector (gate is 20 of 30) |
|---|---|---|---|---|
| F13 | M1 horizontal shape | 12 | 0 | M1 max 12 |
| F14 | M2 high-energy vertical | 12 | 0 | M2 max 15 |
| F15 | M3 low-energy vertical | 12 | 0 | M3 max 15 |
| F16 | M1+M2+M3 combined | 12 | 0 | M1 max 8, M2 max 9, M3 max 6 |

The maximum practical-win count ever observed anywhere in the partition is 18 for M1, 18 for M2 and 15 for M3, against a required 20.

**This defect is independent of the boundary defect.** In no case did a detector reach 20 wins while being evaluability-blocked, and at the 10 percent counterfactual floor, where every case is evaluable, the firing count is still 0.

The consequence is a validity finding rather than a count finding: it does not change any v1 number, but it means the 67 `M0_NOT_REJECTED` verdicts carry no discriminating evidential content. A1, as executed on this partition, is an evaluability filter, not a model-adequacy test.

---

## 4. G2: 4 of 144

### 4.1 Sealed outcome and first irreversible failure point

| Sealed G2 event | Cases |
|---|---|
| SUCCESS | 4 |
| FAILURE | 103 |
| UNEVALUABLE | 37 |
| **total** | **144** |

| First irreversible failure point | Cases | Root-cause class |
|---|---|---|
| `REPRESENTATION` (grammar cannot express the family) | 12 | GRAMMAR_REPRESENTABILITY |
| `GENERATION` (no seed matched support or family) | 45 | SEARCH_GENERATION_FAILURE |
| `GENERATION_FAMILY` (support reached, family never) | 12 | SEARCH_GENERATION_FAILURE |
| `SELECTION_WITHIN_SEED_RETENTION` | 69 | SELECTION_FAILURE |
| `SELECTION_CROSS_SEED_IDENTITY` | 2 | CANONICALIZATION_EQUIVALENCE_FAILURE |
| `NONE` (success) | 4 | NONE_SUCCESS |

### 4.2 Per-family pipeline outcome

`oracle` is the number of cases in which at least one of the 30 retained candidates was G2-correct: the ceiling any post-search selection rule could reach from the persisted evidence.

| Family | Truth family | n | oracle | sealed SUCCESS | sealed UNEVALUABLE |
|---|---|---|---|---|---|
| F01 | mass_affine_descriptor | 12 | 12 | 2 | 1 |
| F02 | mass_affine_descriptor | 12 | 3 | 0 | 5 |
| F03 | mass_affine_descriptor | 12 | 1 | 0 | 8 |
| F04 | mass_affine_descriptor | 12 | 8 | 0 | 6 |
| F05 | mass_affine_descriptor | 12 | 9 | 0 | 2 |
| F08 | mass_affine_descriptor | 12 | 9 | 0 | 3 |
| F09 | mass_saturating_descriptor | 12 | **0** | 0 | 0 |
| F10 | mass_interaction | 12 | 6 | 0 | 0 |
| F11 | mass_affine_descriptor | 12 | 8 | 1 | 4 |
| F12 | mass_affine_descriptor | 12 | 10 | 1 | 4 |
| F17 | mass_affine_descriptor | 12 | 9 | 0 | 4 |
| F18 | mass_exponential_descriptor | 12 | **0** | 0 | 0 |

### 4.3 Representability: F18 had a zero success probability by construction

`discovery/grammar.py` excludes `exp` (DEVIATIONS_P3 D1). F18's planted truth is `sqrt(mass) * exp(coefficient * descriptor / 3)`, and `g2_contract._contains_exp_of` requires a literal `sympy.exp` node in the simplified expression. No grammar-legal expression can carry one, so the label `mass_exponential_descriptor` is unreachable regardless of search outcome. Empirically: 0 of 12 F18 cases had any correct retained candidate across 360 searches, and 29 of 30 seeds in a typical F18 case retained a mass-only expression.

This caps G2 at 132 of 144 before any search runs.

### 4.4 What the search actually produced

Across all 4,320 seed slots in the G2 population (2 produced no candidate, 2 more failed to parse):

| Discovered family | Candidates | Share |
|---|---|---|
| `mass_power` (mass only) | 2,450 | 56.7% |
| unclassifiable (`None`) | 1,477 | 34.2% |
| `mass_affine_descriptor` | 355 | 8.2% |
| `mass_saturating_descriptor` | 21 | 0.5% |
| `mass_interaction` | 17 | 0.4% |

Seed-level G2 events: 371 SUCCESS, 2,472 FAILURE, 1,477 UNEVALUABLE.

The modal answer is `mass_power` in 92 of 144 cases and unclassifiable in 50. **The search's dominant behaviour is to collapse onto the mass-only term and drop the descriptor structure entirely.**

### 4.5 Selection: the correct answer existed in 75 cases and won in 4

A G2-correct candidate reached cross-seed selection in **75 of 144** cases but was the sealed winner in only 4.

| Correct-seed share | Value |
|---|---|
| median across all 144 cases | 1 of 30 |
| 75th percentile | 5 of 30 |
| maximum anywhere | 16 of 30 |
| cases with a correct majority at or above 15 of 30 | 1 |
| cases with a correct majority at or above the 20 of 30 stability gate | **0** |

All four sealed G2 successes won with `selection_count` of 1 or 2 out of 30, by the lowest-ordinal tie-break. Every one of them was structurally rejected as unstable. G2 scoring and structural acceptance are decoupled, so the four successes are scoring artifacts rather than accepted discoveries.

### 4.6 The within-seed retention rule is the discarding layer

Each seed retains `argmax(score)`, PySR's marginal-return-per-unit-complexity heuristic, and only that row survives. Comparing, within each case, the seeds that retained a correct candidate against those that did not:

| Paired statistic (75 cases with both) | Value |
|---|---|
| median accuracy gap, correct minus incorrect | **+0.121 `valid_r2`** |
| accuracy gap positive in | 98.7% of paired cases |
| median complexity gap, correct minus incorrect | **+3.4** |
| complexity gap positive in | 94.7% of paired cases |
| correct candidate is both more accurate and more complex | **70 of 75 cases** |

Whenever seeds disagreed, the correct-family candidate was substantially more accurate at slightly higher complexity, and it was the minority. That is the signature of a parsimony rule trading accuracy away.

Subject to `WITHIN_SEED_PARETO_NOT_OBSERVABLE`: this shows which candidate the rule kept across disagreeing seeds, not what each individual front contained.

### 4.7 Coarsening the equivalence relation does not rescue G2

Three arms, all replaying the same frozen evidence, the same tie-break, and the same frozen G2 predicates:

| Arm | Grouping key | Successes |
|---|---|---|
| **IDENTITY (frozen v1, control)** | `identity_contract.template_key` | **4 / 144** |
| G2_LABEL | `(effective_support, discovered_family)`, the pair the endpoint is scored on | **3 / 144** |
| ORACLE_ANY | any correct retained candidate counts | **75 / 144** |

The control arm reproduces the seal exactly. Regrouping by the endpoint's own equivalence relation recovers 2 cases and loses 3, for a net loss.

The fragmentation is real but not decisive: median 11 identity classes per case against median 3 label classes, and correct answers spread across a median of 5 identity classes but 1 label class, in 61 of 144 cases occupying more than one identity class. It cannot help when the correct answer is a small minority, which it almost always is.

### 4.8 Classifier coverage

1,475 of the 4,318 actual retained candidates (34.2 percent) could not be labelled into any truth family. Only 2 candidates failed to parse, so this is classifier coverage and not a parser defect. All 37 G2 `UNEVALUABLE` cases carry `family_status = FAMILY_UNRESOLVED`, meaning the cross-seed winner was one of the unlabelable expressions. Under the frozen predicate `UNEVALUABLE` and `FAILURE` are both non-successes, so this confounds interpretation without moving the numerator.

---

## 5. G3: 26 violations of 36, and zero unsafe acceptances

| G3 event | Cases |
|---|---|
| SAFE | 10 |
| VIOLATION | 26 |
| UNSAFE | **0** |

| Violation cause | Cases |
|---|---|
| `A1_INDETERMINATE` | **26 (100%)** |
| any other unevaluable route | 0 |
| unsafe structural acceptance | 0 |

Every single G3 violation is a case whose A1 status was `BOUNDARY_LIMITED`, routed to `UNEVALUABLE` by `structural_acceptance` gate 1 and charged as a violation by the conservative `g3_contract` rule. **The G3 gap and the G1 gap are the same defect.**

Overlap detail: 20 of the 36 G3 cases (F07 and F19A/F19B) also carry the `scalar_competence` endpoint and therefore appear in G1's 164. The other 16 (F19C, F20A, F20B, F20C) do not, but still run A1 and still route to `UNEVALUABLE` on an indeterminate verdict.

### 5.1 Independent safety confirmation

Checked twice, once through the frozen `g3_contract` classifiers and once by a direct scan that bypasses them entirely and simply asks whether any G3 case reached `STRUCTURAL_ACCEPTED` with non-mass effective support:

| Check | Result |
|---|---|
| G3 cases structurally accepted at all | 2 |
| their effective support | `PB\|held_out\|F07\|r010`: `{mass}`; `PB\|held_out\|F19\|r007`: `{mass}` |
| accepted with non-mass support | **0** |
| accepted under a variant where no acceptance is safe (F19C, F20A/B/C) | **0** |
| classifier-derived UNSAFE events | **0** |

Both routes agree. **No unsafe formula was ever structurally accepted anywhere in the Held-out partition.** Across all 240 cases only 25 reached structural acceptance at all.

The complementary caution: the safety evidence rests on 10 evaluable opportunities, which is far too thin to support a safety claim in either direction. Resolving the A1 defect is what would make G3 informative.

---

## 6. Root-cause quantification

### 6.1 G1, denominator 164

| Root-cause class | Cases | Percent |
|---|---|---|
| MODEL_ADEQUACY_LIMITATION | 97 | 59.15% |
| NONE_SUCCESS | 67 | 40.85% |

No G1 case is attributable to grammar, search, selection, voting, canonicalization or scoring. G1 is a single-cause endpoint.

### 6.2 G2, denominator 144

| Root-cause class | Cases | Percent |
|---|---|---|
| SELECTION_FAILURE | 69 | 47.92% |
| SEARCH_GENERATION_FAILURE | 57 | 39.58% |
| GRAMMAR_REPRESENTABILITY | 12 | 8.33% |
| NONE_SUCCESS | 4 | 2.78% |
| CANONICALIZATION_EQUIVALENCE_FAILURE | 2 | 1.39% |

Read together with section 4.7: the SELECTION_FAILURE class is dominated by the within-seed retention layer, not by cross-seed voting. Only 2 cases are recoverable by changing the equivalence relation.

### 6.3 G3, denominator 36

| Root-cause class | Cases | Percent |
|---|---|---|
| MODEL_ADEQUACY_LIMITATION | 26 | 72.22% |
| EXPECTED_NEGATIVE_CONTROL | 10 | 27.78% |

### 6.4 Where cases actually stop, across all 240

| Stage reached | Cases |
|---|---|
| A1 adequacy | 154 |
| stability gate | 43 |
| null threshold | 16 |
| ceiling (Gate 7) | 1 |
| falsification (Gate 8) | 1 |
| all passed | 25 |

Only 27 cases ever reach Gate 7 and only 26 reach Gate 8. **Late falsification is not the bottleneck: it is barely exercised.** Gate 7 passes 26 of 27 and Gate 8 passes 25 of 26, and the single Gate 8 failure was a correct `F10_NEGATIVE_CONTROL` rejection.

---

## 7. Counterfactual diagnostics

These are diagnostic recomputations over frozen evidence. **The official v1 result stands at G1 67/164, G2 4/144, G3 26/36 violations.** Nothing below supersedes it.

| Counterfactual | Result | Gate |
|---|---|---|
| **G1** if A1 indeterminacy alone were resolved | 154/164, Wilson lower **0.891** | passes 0.70 |
| **G3** if A1 indeterminacy alone were resolved | 0/36 violations, Wilson upper **0.096** | passes 0.15 |
| **G2** under a perfect post-search selector | 75/144, Wilson lower **0.440** | **still fails** 0.70 |

G1's residual after removing the adequacy cause is 10 cases that would also fail a continuous competence condition.

### 7.1 G2 decomposed: search versus selection versus representation

| Partition of the 144 G2 cases | Cases |
|---|---|
| representation infeasible (grammar lacks `exp`) | 12 |
| correct answer never reached cross-seed selection | 57 |
| correct answer reached selection but lost | 71 |
| correct answer reached selection and won | 4 |
| of the 71 losses, recoverable by coarsening the equivalence relation | 2 |
| cases with a correct majority at or above 15 of 30 | 1 |
| cases with a correct majority at or above the 20 of 30 stability gate | 0 |

Answering the question directly: **among representable cases, truth-equivalent structure was discovered in 75 of 132 (56.8 percent). Where it was discovered, it was lost later in 71 of 75 (94.7 percent). The loss is overwhelmingly at the within-seed retention layer, not at cross-seed voting or canonicalization.**

---

## 8. Hostile review

Eight independent lenses, 44 checks, each written to falsify the diagnosis rather than confirm it. Every check recomputes its quantity from a different starting point than the stage that produced it.

| Lens | Checks | Result |
|---|---|---|
| 1. Denominator closure | 13 | PASS |
| 2. Seal fidelity | 3 | PASS |
| 3. Endpoint arithmetic | 8 | PASS |
| 4. Attribution exclusivity | 8 | PASS |
| 5. Safety | 3 | PASS |
| 6. Counterfactual honesty (control arms) | 2 | PASS |
| 7. Search-freedom | 3 | PASS |
| 8. Claim discipline | 4 | PASS |
| **total** | **44** | **44 PASS / 0 FAIL** |

### 8.1 Reconciliation

| Endpoint | Rows | Partition | Frozen manifest eligibility |
|---|---|---|---|
| G1 | 164 | 67 successes + 97 failures = 164 | exact match, 0 symmetric difference |
| G2 | 144 | 4 SUCCESS + 103 FAILURE + 37 UNEVALUABLE = 144 | exact match, 0 symmetric difference |
| G3 | 36 | 10 SAFE + 26 VIOLATION = 36 | exact match, 0 symmetric difference |

All three denominators also match `heldout_restored_analysis.json`'s `endpoint_denominators`, and all three Wilson bounds recomputed from the CSVs reproduce the restored analysis to within 1e-12.

### 8.2 Checks that specifically constrain the claims made here

- Every G1 failure fails the `m0_accepted` conjunct: **verified for all 97**, which is what licenses "adequacy is the whole G1 gap".
- No case labelled `SEARCH_GENERATION_FAILURE` had a correct retained candidate: **verified, 0 contradictions**.
- Every case labelled a selection-class failure had at least one correct retained candidate: **verified, 0 contradictions**.
- Grammar-representability failures are exactly the 12 F18 cases and their only missing operator is `exp`: **verified**.
- Both counterfactual control arms reproduce the frozen rule exactly (A1 at floor 0.0 gives 86/154; G2 IDENTITY gives 4): **verified**.
- No stage imported PySR or ran a search: **verified**.

---

## 9. What this decomposition does not establish

Stated so no later reader over-reads it.

1. **It cannot see inside a seed's Pareto front.** Section 4.6's attribution to the retention rule is inference from paired within-case behaviour, not direct observation of discarded candidates.
2. **It cannot distinguish "the search cannot find the descriptor term" from "the descriptor term is not identifiable at the planted coefficient magnitudes".** The 57 generation failures, and F09's complete absence of any correct candidate across 360 searches, are consistent with either. Separating them needs a study this evidence cannot support.
3. **The counterfactual floors in section 3.4 are diagnostic probes, not proposals.** Any floor is a new free parameter and would have to be calibrated prospectively.
4. **The safety result rests on 10 evaluable G3 opportunities.** It is a genuine absence of observed unsafe acceptance, not a demonstration of safety.
5. **No v2 remediation is designed here.** `MURU_V1_ROOT_CAUSE_RANKING.md` names remediation *classes* and their risks, and stops there.

---

## 10. Reproduction

The stage scripts live in `scripts/diagnostics/` and run in order against the sealed evidence, which they never write to. Intermediate stage outputs land in `artifacts/diagnostics/`, which the repository's existing `.gitignore` excludes; they are fully regenerable from the committed scripts, and the hostile-review findings they feed are embedded verbatim in `MURU_V1_FAILURE_DECOMPOSITION.json`.

```bash
for stage in 01_a1_decomposition 02_boundary_probe_magnitude 03_g2_pipeline_trace \
             04_g2_counterfactuals 05_retention_objective 06_g3_trace \
             07_case_geometry 08_build_taxonomies 09_hostile_review 10_build_reports; do
  .venv/bin/python scripts/diagnostics/diag_${stage}.py || break
done
```

Stages 01, 02 and 07 regenerate case content and take a few minutes each. Stages 01, 03 and 09 abort rather than continue if the recomputation diverges from the seal, so a silent drift cannot reach the reports.
