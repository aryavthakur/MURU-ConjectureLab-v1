# MURU ConjectureLab v2 Remediation Experiment Plan

**Status:** DESIGN ONLY. Nothing in this plan has been executed. No v2 scientific
architecture is chosen, no threshold is set, no grammar is changed, and no
prospective benchmark is created. The official v1 result stands unchanged at
G1 67/164, G2 4/144, G3 26/36 violations.

**Terminal state:** `V2 REMEDIATION EXPERIMENTS PROSPECTIVELY DESIGNED` /
`NO FINAL V2 SCIENTIFIC ARCHITECTURE CHOSEN`

Machine-readable twin: `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json`

Detailed designs:
`MURU_V2_A1_STUDY_DESIGN.md` (E0, E1),
`MURU_V2_G2_PARETO_STUDY_DESIGN.md` (E2, E4),
`MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md` (E3, E5),
`MURU_V2_CAUSAL_DECISION_TREE.md` (result to change mapping).

Evidence base, treated as frozen: `MURU_V1_FAILURE_DECOMPOSITION.md` / `.json`,
`MURU_V1_ROOT_CAUSE_RANKING.md` / `.json`, and the G1/G2/G3 taxonomy CSVs.

---

## 1. What the diagnosis binds

Taken as given and not re-litigated:

| ID | Finding | Endpoint leverage |
|---|---|---|
| RC1 | The A1 unresolved-boundary rule has no magnitude floor. 154 of 240 cases are `BOUNDARY_LIMITED`, driving all 97 G1 adequacy failures and all 26 G3 violations. Median triggering improvement is 1.3 percent of the fold sum of squares; the largest anywhere is 28.9 percent. | Resolving it alone takes G1 to 154/164 and G3 to 0/36 violations. |
| RC2 | No A1 detector fired on any of 240 cases, including 0 of 48 planted positive controls. Max practical wins were 18/18/15 against a gate of 20. Independent of RC1: at the 10 percent counterfactual floor, where every case is evaluable, firing is still 0. | No count leverage. Voids the evidential content of the 67 `M0_NOT_REJECTED` verdicts. |
| RC1+RC2 | Must be solved together. RC1 says adequacy refuses to decide too often; RC2 says when it does decide it always decides the same way. | Fixing either alone converts a systematic non-decision into a systematic wrong decision. |
| RC3 | Within-seed `argmax(score)` retention discards more accurate, more complex correct expressions: +0.121 median `valid_r2` at +3.4 median complexity, in 70 of 75 paired cases. Pareto fronts were not persisted. | Bounded. Perfect post-search selection gives 75/144, Wilson lower 0.440, still FAIL. |
| RC4 | 57 representable cases never had a correct retained candidate. v1 cannot distinguish search failure from weak identifiability. | Sets G2's ceiling. |
| RC6 | F18 is impossible under the current grammar: the endpoint requires a literal `exp` node and the grammar excludes `exp`. | Caps G2 at 132/144 before any search runs. |
| Gates 7/8 | Not a bottleneck and barely exercised: 27 of 240 cases reach Gate 7, which passes 26 of 27; Gate 8 passes 25 of 26. | None. No experiment here targets them. |

**The consequence that shapes the whole plan.** G1 and G3 are one problem with a
known mechanism and a bounded fix. G2 is a separate and harder problem that
remains far below its gate even under a perfect post-search selector, and whose
two largest causes rest on evidence v1 did not persist. Half of this plan is
therefore instrumentation, not remediation.

---

## 2. Governance frame

### 2.1 Partition discipline

| Partition | Cases | v2 status | Permitted use |
|---|---|---|---|
| Held-out | 240 | **Spent.** Produced the official v1 result and has been exhaustively mined by the decomposition. | Explanatory replay only (E2b), marked `DECISION_INADMISSIBLE`. May not calibrate any v2 rule, threshold, grammar or benchmark change. |
| Development | 80 | Contaminated by v1 tuning history. | Not a calibration surface for v2. |
| Challenge | 60 | **Sealed and unopened.** | Reserved as v2's confirmation partition. Nothing in this plan touches it. |
| `V2C` calibration worlds | fresh | Generated under a disjoint seed namespace. | The only surface on which a v2 rule may be calibrated. |

### 2.2 Namespace separation, mechanically enforced

```
world_id     = "V2C|<experiment>|<cell_id>|r<replicate:03d>"
seed payload = "muru-v2-calibration|" + "|".join(parts)
```

`generator.derive_seed` prefixes `"paper-benchmark-v1|"`. The prefixes differ, so
no v2 world can collide with any benchmark case's seed stream or content hash. A
static check asserts prefix disjointness and that no `V2C|` identifier resolves
through `registry.resolve_case_id`.

### 2.3 Citation enforcement

Every proposed v2 design change must cite the experiment IDs supporting it. A
static citation checker rejects any change whose supporting set contains an E2b
identifier and no decision-admissible identifier. Held-out evidence can
corroborate a v2 conclusion; it cannot produce one.

### 2.4 Internal replication

E1's world set is split 80/20 into `CALIBRATE` and `CONFIRM` at generation time,
both sealed together. `CONFIRM` is opened exactly once, after the rule has been
selected on `CALIBRATE` alone. This is the control on E1's multiple-comparison
exposure.

---

## 3. Experiment register

Every experiment specifies hypothesis, independent variable, controls, metrics,
case count and seeds, decision criterion, computational cost, and what each
outcome supports.

### E0. `A1_ADMISSIBLE_RANGE_PROVENANCE`

**Hypothesis.** H_clip: the M3 boundary event is manufactured by the coincidence
`MU_CEIL == generator response clip == 1 - 1e-4`, so a floor calibrated with the
ceiling held fixed relocates the artifact instead of removing it. H_alias
(secondary): over a 6-point grid the M3 plateau and the M0 scale are partially
aliased. H_null: neither; the ceiling is exonerated.

*Motivating observation, recomputed from the frozen G1 taxonomy for this design:
72 of 164 G1 cases have `mu_max` exactly at the clip value 0.9999.
`BOUNDARY_LIMITED` cases sit at median `mu_max` 0.9999; `M0_NOT_REJECTED` cases
at 0.9802.*

**Independent variable.** Crossed 3 x 3: generator response clip in
{`1-1e-4`, `1-1e-3`, none} x fitter `MU_CEIL` in {`1-1e-4`, `1-1e-3`, open}.

**Controls.** True M0 worlds only, so every boundary event observed is false by
construction. Shared covariate, `mu_inf`, `phi_p`, `g` and noise seeds across all
nine cells, making the comparison paired at the fold level. The
`(1-1e-4, 1-1e-4)` cell is the control arm and must reproduce v1 boundary
behaviour or the study aborts. No symbolic search.

**Metrics.** `contact_rate`, `unresolved_rate`, `probe_gain_rel` distribution,
`evaluable_M3`, `boundary_limited_rate`, `pin_at_ceiling_share`,
`mu_max_at_clip_share`.

**Cases and seeds.** 9 cells x 60 worlds = **540 worlds**, 30 test compounds and
6 energies each. `V2C|E0|...` namespace.

**Decision criterion.** `boundary_limited_rate` drop on decoupling: above 0.50
confirms H_clip and requires the ceiling be re-derived before E1 calibrates any
floor; 0.10 to 0.50 makes the ceiling an explicit E1 factor; below 0.10
exonerates it and E1 proceeds with it fixed.

**Cost.** No search. Estimated **0.5 to 1.5 CPU-hours**, parallel. A 5-world
pilot replaces the estimate with a measurement.

**Outcomes support.** H_clip: RC1's remediation is the removal of a specification
coincidence, not a threshold change, and introduces no free parameter. H_alias:
an acquisition-geometry finding that no threshold fixes. H_null: RC1 really is a
magnitude-floor problem and E1's ladder is the right instrument.

---

### E1. `A1_JOINT_EVALUABILITY_POWER`

**Hypothesis.** H1: a boundary criterion and a practical-win rule exist that
jointly reach detector power at or above 0.80 at the v1-planted amplitude while
holding false rejection at or below 0.05 and the indeterminate rate at or below
0.10. H2: the v1 amplitudes lie below the detection floor of a 30-compound
6-energy LOEO contrast, so no threshold achieves that. H3: evaluability and power
trade off with no admissible point at any amplitude.

**Independent variable.** Design factors: deviation type in {M0, M1, M2, M3,
M1+M2+M3} x effect-size multiplier `alpha` in {0, 0.25, 0.5, 1.0, 2.0} of the
frozen standalone amplitude x noise sd in {0.0, 0.02, 0.06}. Analysis factors,
applied post hoc to persisted fits: boundary criteria C0 (frozen, control), C1
relative-SSE floor, C2 noise-scaled floor, C3 profile-interval, **C4 verdict
invariance** (zero magnitude parameters); win rules P0 (frozen, control), P1
ratio x win-count grid, P2 paired sign test, P3 conjunction of median error
reduction and win fraction.

**Controls.** `(C0, P0)` must reproduce v1's qualitative behaviour at
`alpha = 1.0`, or the study is invalid and aborts. Shared `alpha = 0` null
population across all deviation types. Paired seeds between each cell and its
null counterpart. Wrong-detector firing recorded separately as a failure. Truth
joined only in a separate downstream scoring pass.

**Metrics.** `FRR`, `power_D`, `misattribution`, `indeterminate_rate`,
`evaluable_dist`, `monotone_D`, and `alpha_star_D`, the smallest amplitude at
which power reaches 0.80 with Wilson lower 0.70. `alpha_star_D` is the headline
result above any pass/fail verdict. All proportions carry 95 percent Wilson
intervals.

**Cases and seeds.** 51 cells x 75 worlds = **3,825 worlds**, split 80/20
`CALIBRATE`/`CONFIRM` at generation. 2.02 million persisted fold records.

**Decision criterion.** A pair is ADMISSIBLE iff on `CALIBRATE`: FRR at most 0.05
(Wilson upper at most 0.10); indeterminate rate at most 0.10 (Wilson upper at
most 0.15); power at least 0.80 (Wilson lower at least 0.70) for each of M1, M2,
M3 at `alpha = 1.0`, noise 0.02; misattribution at most 0.05; power monotone in
`alpha`. Selection among admissible pairs is lexicographic and pre-declared:
fewest free parameters, then lowest null indeterminate rate, then highest minimum
power, then lowest ladder index. The selected pair is then confirmed once on
`CONFIRM`. If no pair is admissible, that is outcome H2 or H3 and is reported,
never a licence to weaken the criteria.

**Cost.** No symbolic search. **Under 12 CPU-hours**, about 400 MB of persisted
fold records. Rule re-scoring over the full criterion x rule grid takes minutes
because every rule is a pure function of the persisted record.

**Outcomes support.** See `MURU_V2_A1_STUDY_DESIGN.md` section 3.10 and the
decision tree branch A.1. In short: H1 with C4 selected means RC1 is resolved
without adding a free parameter; H1 with a floor selected means the floor is
prospectively calibrated with a measured false-rejection rate; H2 means no
threshold change is licensed and the amplitudes or the acquisition geometry are
the question; H3 means the adequacy statistic itself must be redesigned.

---

### E2. `G2_PARETO_INSTRUMENTATION`

**Hypothesis.** H_retain: in the majority of cases the decomposition classed
`SELECTION_WITHIN_SEED_RETENTION`, a correct row is on the front and
`argmax(score)` picks a lower-complexity mass-only row over it. H_generate: in
the majority classed `GENERATION`, no front row anywhere carries both correct
support and correct family. H_partial: a material share of the `GENERATION` cases
in fact have correct rows on the front, revising the decomposition's 57/69 split.

**Independent variable.** **None. E2 is observational by design.** Engine,
grammar, configuration, seeds, retention and cross-seed rules are all frozen at
their v1 values. The only change is the persistence layer.

**Controls.** A retention-identity regression: the instrumented engine's
`argmax(score)` candidate must be byte-identical to the frozen path's for every
seed, or the instrumentation has changed the search and is rejected.
`PYSR_CONFIG`, `GRAMMAR_VERSION`, `deterministic=True`, `parallelism="serial"`
and `SEEDS_PER_CASE = 30` unchanged. For E2b, replayed retention must reproduce
the sealed `selection_count` and representative for all 144 cases; any case that
does not is quarantined and reported.

**Metrics.** `P_front`, `P_retain_given_front`, `P_win_given_retain`,
`rank_of_correct`, `score_gap`, `complexity_gap`, `r2_gap`, `front_size`, and a
four-way case partition: `SUCCESS` / `NEVER_ON_FRONT` / `LOST_IN_RETENTION` /
`LOST_IN_CROSS_SEED`. The gaps are measured **within a front**, which is the
comparison that actually indicts the retention rule; v1 could only measure them
across seeds.

**Cases and seeds.** E2a: 5 truth families x 3 coefficient regimes x 3 noise
levels x 12 replicates = **540 worlds** x 30 seeds = **16,200 searches**,
decision-admissible. E2b: **144 Held-out cases** x 30 seeds = **4,320 searches**,
`DECISION_INADMISSIBLE`.

**Decision criterion.** Whichever non-success class dominates in E2a licenses its
corresponding ablation, per decision tree branch B.1. If `P_retain_given_front`
is near 1 wherever `P_front` is high, RC3 is withdrawn and no retention change is
licensed. **Falsification hook:** if E2b's direct measurement materially
contradicts the decomposition's 69/57 retention-versus-generation split, all E4
ablations are suspended until the contradiction is resolved.

**Cost.** 16,200 + 4,320 searches at 2.30 s serial (RUNTIME_BUDGET_P3 measured) =
13.2 CPU-hours, plus 3 to 5 CPU-hours of post-hoc `sympy.simplify` scoring.
**Total 16 to 19 CPU-hours**, under 200 MB. Scoring is the cost risk, not the
search: memoise by expression string, cap per-expression wall clock, and record
`SIMPLIFY_TIMEOUT` explicitly so it is distinguishable from genuine classifier
non-coverage.

**Outcomes support.** H_retain confirmed makes RC3 an observation and makes E4a a
zero-cost re-scoring. H_generate confirmed moves the question upstream to E3, and
no search-side change is licensed until E3 answers. H_partial confirmed revises
the decomposition's attribution and forces the root-cause ranking to be
recomputed before E4 proceeds.

---

### E3. `DESCRIPTOR_IDENTIFIABILITY`

**Hypothesis.** H_id_affine: `mass_affine_descriptor` is identifiable against
mass-only at the frozen coefficient range. H_id_sat and H_id_exp: the saturating
and exponential families are **not** distinguishable from the affine form at the
frozen range. H_id_noise: where a family fails, the failure survives at zero
response noise, meaning structural closeness rather than measurement error.
H_id_geometry: doubling the energy grid materially raises identifiability.

*Design-time arithmetic over the frozen generator specification, stated as
motivation and tested by the experiment: the exponential family's separation from
its best affine approximation is 0.03 to 0.13 percent relative rms across the
whole frozen coefficient support, against a default response noise sd of 0.02.
The saturating family's is 0.6 to 1.2 percent.*

**Independent variable.** Truth family in {`mass_power` (control),
`mass_affine_descriptor`, `mass_saturating_descriptor`, `mass_interaction`,
`mass_exponential_descriptor`} x coefficient `c` in {0.25, 0.40, 0.55, 1.1, 2.2}
x noise sd in {0.0, 0.02, 0.0295, 0.06} x energy grid in {6, 12}.

**Controls.** The `mass_power` negative-control family, on which the oracle must
not select a descriptor model; this is the study's own specificity arm. A
noise-free arm separating estimator error from structural closeness. Paired seeds
across the `c` ladder within each cell. The frozen `Phi`/`g` estimation stage
used unmodified, so identifiability is measured on the quantity the search
actually consumes. Model fitting on training scaffolds only; every statistic on
validation or test scaffolds. **No symbolic search anywhere.**

**Metrics.** `oracle_selection_rate` (primary), `false_structure_oracle`
(primary specificity), `delta_r2_vs_mass`, `delta_r2_vs_rival`, `c_hat_over_se`,
`lrt_p_true_vs_mass`, `lrt_p_true_vs_rival`, and `c_star`, the smallest
coefficient at which oracle selection reaches 0.80. Both BIC and validation-R2
selection are reported separately and neither is chosen after seeing results.

**Cases and seeds.** 5 x 5 x 4 x 2 x 50 replicates = **10,000 worlds**.

**Decision criterion.** Per cell: oracle selection at or above 0.80 is
IDENTIFIABLE and licenses search-side attribution; 0.50 to 0.80 is MARGINAL and
licenses nothing on its own; below 0.50 is WEAKLY IDENTIFIABLE and **forbids**
any search-side change citing that cell. If `false_structure_oracle` on the
`mass_power` control exceeds 0.10 the study is INVALID and must be redesigned
before any cell is used.

**Cost.** No symbolic search. **2 to 4 CPU-hours**, under 100 MB. The cheapest
experiment in the plan and the one with the highest decision leverage; it should
run first among the G2-side experiments, concurrently with E1.

**Outcomes support.** This is the study that settles RC4's open question. If the
oracle, handed the five correct models in closed form, cannot pick the truth,
then no symbolic search can, and the failure is a benchmark-construction fact
rather than an engine deficiency. It also gates E5 entirely: if the exponential
family is not separable from the affine form, adding `exp` to the grammar cannot
help.

---

### E4. `G2_SINGLE_FACTOR_ABLATIONS`

Six one-factor arms. No arm changes two factors. Any joint study is separately
authorised later, may combine only factors individually shown admissible, and
must re-measure false structure jointly because admissibility is not additive.
Full design in `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 3.

| Arm | Factor | Levels | Primary metric | Search cost | Prerequisite |
|---|---|---|---|---|---|
| **E4a** | retention policy | R0 `argmax(score)` (control), R1 `argmax(valid_r2)`, R2 top-k, R3 whole front, R4 accuracy-thresholded parsimony | G2 success **and** `false_structure_rate` **and** `selection_count` distribution | **0** (post hoc on E2 fronts) | E2 |
| **E4b** | search budget | `niterations` 40 (control), 120, 400 | `P_front` | 16 CPU-h | E2 **and** E3 |
| **E4c** | objective / parsimony | `parsimony` 0.0032 (control), 0.001, 0.01; separately `adaptive_parsimony_scaling` 20 (control), 5, 40 | `P_front`, front complexity distribution | 4.6 CPU-h | E2 **and** E3 |
| **E4d** | grammar / operators | G0 frozen (control), G1 unguarded `exp`, G2 clipped `exp_p`, G3 `exp` over linear argument only | F18-analogue `P_front`, **and** every other family's `false_structure_rate`, **and** overflow instrumentation | 11.5 CPU-h | E3 |
| **E4e** | coefficient regime | `c` in {0.25, 0.40, 0.55, 1.1, 2.2} | `c*_search`, and `engine_inefficiency = c*_search - c*_oracle` | 9.6 CPU-h | E3 |
| **E4f** | classifier / canonicalization | K0 frozen, K1 normal form, K2 behavioural; V0 `template_key` (control), V1 `(support, family)`, V2 algebraic | **`false_labelling_rate`** first, then coverage, then `k_inflation` | **0** (post hoc) | E2 |

**Common controls.** Frozen setting is always the control arm; identical worlds,
seeds and downstream stages; every arm reports its G2 metric and its E6
false-structure metric in the same table. Reporting a G2 gain without its safety
cost is not permitted.

**Common decision rule.** An arm is adopted only if its improvement over control
has a Wilson lower bound above 0 **and** its false-structure rate stays under the
E6 ceiling. Among qualifying arms, fewest free parameters wins, then lowest false
structure.

**Arm-specific decision criteria.**
- E4a: an arm that raises G2 but drives `selection_count` below the 20-of-30 gate
  for most cases is rejected, or adopted only with a re-derived stability gate,
  which is itself a change requiring its own experiment.
- E4b: flat `P_front` across budgets means no budget increase is licensed.
- E4c: a parsimony change is licensed only if it raises `P_front` (a generation
  effect). Raising only `P_retain_given_front` is E4a's territory, addressed
  there at zero cost; counting it twice would attribute one fix to two factors.
- E4d: G3 (`exp` restricted to the planted argument form) is presumptively
  rejected because it encodes the answer in the grammar. It is measured so the
  size of the encoding effect is on the record.
- E4e: `engine_inefficiency` near zero means the search is already near the
  statistical limit and no further search-side change is licensed.
- E4f: coverage is not the adoption criterion. `false_labelling_rate` on
  adversarial negative controls, constructed by substituting
  `correlated_distractor` or `descriptor2` for `descriptor` in the truth
  expression, is primary. RC5's risk is explicitly in the direction that flatters
  the result.

**Cost.** **About 42 CPU-hours of search** across E4b, E4c, E4d and E4e; E4a and
E4f cost nothing beyond re-scoring.

**Outcomes support.** Per decision tree branches B.2 through B.6. Every arm has a
`NO CHANGE LICENSED` outcome and several have a `REJECTED DESPITE IMPROVEMENT`
outcome.

---

### E5. `F18_EXPONENTIAL_RESOLUTION`

**Hypothesis.** The RC6 defect as stated (grammar excludes `exp`) is a symptom
rather than the binding constraint: even with `exp` admitted, the planted
exponential is numerically indistinguishable from an affine descriptor law at the
frozen coefficient magnitude, so a parsimony-driven search would still never emit
it and `_contains_exp_of` would still never see a literal `exp` node.

**Independent variable.** Resolution option: O1 status quo, O2 unguarded `exp`,
O3 domain-clipped `exp_p` with `NESTED_CONSTRAINTS["exp"] = {"exp": 0}`, O4 `exp`
over a linear argument in one primitive only, O5 remove F18 from the
family-recovery population (144 to 132), O6 re-specify F18's coefficient, O7
replace F18's truth with a grammar-expressible but algebraically difficult form.

**Controls.** All eleven other families are carried through every grammar arm, so
a global grammar change is never scored on a single family's benefit. Overflow
instrumentation on the actual design-matrix ranges. The frozen grammar arm is the
control.

**Metrics.** F18-analogue `P_front`; every other family's `false_structure_rate`;
`finite_mask` rejection rate; `MAX_INVALID_FRACTION` rejection rate; clip
activation rate for O3; and a direct empirical test of the standing invariant
that invalidity never improves a score, which `exp` stresses more than any other
operator.

**Cases and seeds.** Rides on E4d's arms plus a dedicated F18-analogue world set
at E3's coefficient ladder: 200 worlds x 30 seeds per grammar arm.

**Decision criterion.** Three ordered tests. **Test 1, coherence:** does the
option remove the contradiction between the endpoint's required operator and the
grammar's operator set? O1 fails and is eliminated. **Test 2, identifiability,
decided by E3:** if the exponential family is WEAKLY IDENTIFIABLE at the frozen
coefficient range, O2, O3 and O4 are futile and only O5, O6 and O7 remain live.
**Test 3, safety:** measured false-structure rate from E6; any option exceeding
the ceiling is eliminated. **G2 success rate is reported for every option and
ranks none of them.** That is the operative sense of not choosing based on making
scores easier.

**Cost.** About **3.8 CPU-hours per grammar arm**, on top of E4d.

**Outcomes support.** If E3 says weakly identifiable (the prediction), D1's
exclusion of `exp` stands, the grammar is exonerated, and F18's resolution is a
governance decision among O5, O6 and O7 about what claim the endpoint should
make. If E3 says identifiable and O3 clears safety, the grammar exclusion was the
binding defect and guarded `exp` is admitted with permanent overflow
instrumentation.

---

### E6. `FALSE_STRUCTURE_SAFETY_COUNTERWEIGHT`

Not a terminal stage. E6 runs against every candidate change from E1, E4 and E5,
as that change becomes a candidate.

**Why it is mandatory rather than optional.** RC1's own risk note: "Loosening
evaluability admits cases the current rule conservatively refused, so G3's safety
direction changes and must be re-argued from scratch rather than inherited."
RC3's: "An accuracy-weighted rule biases toward overfit high-complexity
expressions, which is exactly the failure mode the parsimony rule exists to
prevent." RC4's: "Increasing budget or operator richness increases the
false-structure rate, which G3 exists to punish." Every one of this plan's
remediations pulls against G3. E6 is where that is paid for.

**Hypothesis.** For each candidate change X, the unsafe structural acceptance
rate under X remains within the pre-declared ceiling on fresh worlds.

**Independent variable.** The candidate change X (one at a time, matching E4's
one-factor discipline).

**Controls.** The frozen v1 configuration is the control arm. Identical worlds
and seeds across arms. Both routes used by the v1 diagnosis are reproduced: the
frozen `g3_contract` classifiers, and an independent direct scan that bypasses
them and simply asks whether any case reached `STRUCTURAL_ACCEPTED` with non-mass
effective support. Agreement between the two routes is itself a check.

**Metrics.** Unsafe structural acceptance rate with Wilson upper bound, measured
on: mass-only truth worlds (F07 analogue), destroyed-link nulls (F19A),
mass-preserving nulls (F19B), destroyed-response worlds (F19C, which must be
flagged non-evaluable), and adversarial worlds (F20A latent driver, F20B
measurement coupling, F20C out-of-grammar). Plus the count of **evaluable** safety
opportunities.

**Cases and seeds.** Sized so that every candidate change is evaluated on **at
least 100 evaluable safety opportunities**. v1's safety result rested on 10,
which is why the decomposition calls it "a genuine absence of observed unsafe
acceptance, not a demonstration of safety". About 300 worlds x 30 seeds per
candidate change for the structural half; the adequacy half rides on E1's fits at
no search cost.

**Decision criterion.** Unsafe acceptance rate Wilson upper at or below the
pre-declared ceiling (0.15, mirroring G3's own gate) on at least 100 evaluable
opportunities. **E6 holds veto and has no positive power:** it can reject a
change, it can never license one. That asymmetry is deliberate. A safety
experiment that could authorise changes would become a route to justifying looser
rules by pointing at an unfired alarm.

**Cost.** About **5.8 CPU-hours** of search per candidate change, plus zero for
the adequacy half.

**Outcomes support.** A change that clears E6 on 100+ opportunities carries a
safety argument v1 never had. A change that fails E6 is rejected regardless of
its G1 or G2 benefit, which is the only mechanism in this plan that can stop a
score-improving change.

---

## 4. Cost and schedule

| Experiment | Search runs | CPU-hours | Storage | Prerequisite |
|---|---|---|---|---|
| E0 | 0 | 0.5 to 1.5 | small | none |
| E1 | 0 | up to 12 | ~400 MB | E0 |
| E2a | 16,200 | 13 to 15 | ~150 MB | none |
| E2b | 4,320 | 3 to 4 | ~50 MB | none |
| E3 | 0 | 2 to 4 | ~100 MB | none |
| E4a | 0 | under 1 | small | E2 |
| E4b | ~5,400 | 16 | small | E2, E3 |
| E4c | ~7,200 | 4.6 | small | E2, E3 |
| E4d | ~18,000 | 11.5 | small | E3 |
| E4e | ~15,000 | 9.6 | small | E3 |
| E4f | 0 | ~2 | small | E2 |
| E5 | ~6,000 | 3.8 per arm | small | E3, E4d |
| E6 | ~9,000 per change | 5.8 per change | small | runs against each change |
| **Total (single pass, three candidate changes through E6)** | **~99,000** | **about 100 CPU-hours** | **under 2 GB** | |

At 2.30 s per PySR run serial (RUNTIME_BUDGET_P3, measured), 100 CPU-hours is
roughly 13 wall-hours on 8 cores or 4 days on one. Every stage is checkpointed at
the world level and restartable. Every cost figure above is an estimate and each
experiment runs a 5-world pilot that replaces its estimate with a measurement
before the full run is authorised.

**Recommended execution order.** E0, E3 and E2 concurrently (E3 is cheapest and
most decisive; E2 is the longest pole). Then E1 behind E0. Then E4's arms behind
their prerequisites. E5 behind E3 and E4d. E6 against each candidate change as it
arises.

---

## 5. Hostile review of this plan

Eight lenses, written to falsify the plan rather than defend it.

### Lens 1: leakage from spent evidence

**Attack.** Held-out has produced the official result and been exhaustively
mined. Any v2 rule that performs well is suspect of having been chosen because
the designer knows what Held-out did.

**What the plan does.** Fresh `V2C` worlds under a disjoint seed namespace are
the only calibration surface; the Held-out replay E2b is marked
`DECISION_INADMISSIBLE` at the row level and a static citation checker rejects
any change supported only by E2b identifiers; the Challenge partition stays
sealed as the confirmation surface; the Development partition is also excluded as
v1-contaminated.

**Residual risk, declared.** The designer has read the decomposition, so the
*space of hypotheses* in this plan is Held-out-informed. C4's verdict-invariance
criterion exists because the decomposition showed the triggering improvements
were negligible. E0 exists because a `mu_max` pattern was visible in the frozen
taxonomy. This cannot be undone and should not be hidden. The honest statement:
**v2's design is Held-out-informed at the hypothesis level and Held-out-blind at
the parameter level.** Every threshold is fit on fresh worlds, confirmed on a
sealed split, and finally tested on the unopened Challenge partition. That is the
strongest available protection, and it is not complete protection.

### Lens 2: overfitting to v1

**Attack.** Ladders centred on v1's operating point would produce rules tuned to
v1's difficulty and nothing else.

**What the plan does.** E1's `alpha` ladder runs from 0.25x to 2x the frozen
amplitude and E3's `c` ladder from 0.25 to 2.2 against a frozen support of
`U(0.25, 0.55)`. Both are designed to **locate** a threshold (`alpha_star`,
`c_star`) rather than to verify a verdict at the v1 point. Those located
thresholds, not the pass rates, are the headline results.

**Residual risk.** The fresh worlds use the same generator machinery, so any
defect in that machinery is inherited. `descriptor` is min-max normalised per
sample (`descriptor /= descriptor.max()`), which makes its range sample-dependent;
`correlated` is `0.85*descriptor + 0.15*N(0,1)` with no renormalisation. E0
partially probes this, but a full generator audit is not in this plan and should
be. **Recorded as an open item.**

### Lens 3: multiple-comparison inflation

**Attack.** E1 evaluates roughly 5 boundary criteria against roughly 20 win-rule
combinations across 51 cells. That is thousands of comparisons on one world set,
and something will look admissible by chance.

**What the plan does.** Three mitigations. (i) Admissibility is a **conjunction
of pre-declared absolute thresholds**, not a "best of K" ranking, so it does not
inflate with K in the way a maximum does. (ii) The tie-break among admissible
pairs is a pre-declared lexicographic order with fewest-free-parameters first,
which cannot be gamed after seeing results. (iii) A sealed `CONFIRM` split,
generated at the same time and opened exactly once after selection, provides
internal replication.

**Residual risk, declared.** A conjunction of five thresholds evaluated at
thousands of points still has a non-trivial family-wise error rate, and the
`CONFIRM` split is 20 percent, so its own power to detect a false positive is
limited. If several pairs pass `CALIBRATE` and the selected one fails `CONFIRM`,
the plan requires reporting non-replication rather than trying the next pair.
That rule is what makes `CONFIRM` a replication rather than a second selection
round, and it must be honoured even when it costs the whole study.

### Lens 4: changes that merely lower difficulty

**Attack.** Every remediation in this plan makes something easier. Several would
raise the score without improving the science.

**Enumerated temptations and their specific guards:**

| Temptation | Guard |
|---|---|
| Raise the boundary floor until nothing is `BOUNDARY_LIMITED` | E1 requires power **and** specificity jointly. v1 already demonstrates that a 10 percent floor makes all 240 cases evaluable while detector firing stays at 0, so maximum evaluability is demonstrably not sufficient. |
| Raise planted amplitudes or coefficients until scores rise | The difficulty guard: the change requires a measured floor above the current magnitude, **and** an external scientific rationale written before the new magnitude is chosen, **and** the new magnitude set from that rationale rather than from the measured floor. Failing that, keep the magnitude and narrow the claim. |
| Loosen the family classifier until things match | `false_labelling_rate` on adversarial negatives is primary; coverage is secondary. |
| Retain the whole Pareto front until something correct is in it | E6 veto, plus rejection if `selection_count` collapses the 20-of-30 stability gate. |
| Coarsen the voting relation to inflate `selection_count` | `k_inflation` is a gating metric, and v1's own counterfactual for this change is net negative (3/144 against 4/144). |
| Add `exp` to make F18 possible | E5's ordered tests put identifiability before grammar and exclude G2 rate from the decision inputs entirely. |
| Lower `MIN_PRACTICAL_WINS` so detectors fire | Only adoptable inside a pair that simultaneously holds false rejection at or below 0.05; a win-count reduction alone fails criterion 1. |
| Relax Gate 7 or Gate 8 | No experiment targets them, because they are not the bottleneck, so no change to them is licensed by anything here. |

**Residual risk.** The difficulty guard depends on a scientific rationale being
written honestly and in advance. That is a governance control, not a technical
one, and it can be defeated by a determined author. Its only real protection is
that the rationale is committed before the new magnitude is chosen and is
therefore auditable after the fact.

### Lens 5: construct validity of the fresh worlds

**Attack.** If the fresh worlds are generated by the same code that will be
calibrated against, the resulting rule is tuned to the generator rather than to
chemistry.

**What the plan does.** E1's `(C0, P0)` control arm must reproduce v1's
qualitative behaviour, and E2a versus E2b divergence is a blocking finding, so
transfer between the fresh and benchmark regimes is checked rather than assumed.

**Residual risk, declared plainly.** Every claim this plan can produce is a claim
about **this synthetic regime**. None of it transfers to real spectra without
external validation. That limit is inherent to a fully synthetic benchmark and is
not introduced by this plan, but it must not be forgotten when the results read
well.

### Lens 6: instrumentation that changes what it measures

**Attack.** E2 claims that only the persistence layer changes. Persisting the
whole front touches the same code path that selects from it.

**What the plan does.** A byte-identity regression gate: for every seed in a
control set, the instrumented engine's `argmax(score)` retained candidate must be
byte-identical to the frozen path's. E2's records are unusable until that gate
passes.

**Residual risk.** The gate proves identity on the control set, not on every
world. Determinism (`deterministic=True`, `parallelism="serial"`) makes broad
divergence unlikely but not impossible.

### Lens 7: attribution exclusivity

**Attack.** E4c and E4a can both claim the same improvement: lowering parsimony
makes the engine emit more complex expressions, and the retention rule then keeps
them. Counting that once as a budget effect and once as a retention effect would
inflate the apparent benefit of both.

**What the plan does.** E4c is licensed only by a rise in `P_front`, a generation
metric. A rise in `P_retain_given_front` alone is explicitly assigned to E4a,
which achieves it at zero cost. Each arm's primary metric is chosen so that arms
cannot claim each other's effects.

**Residual risk.** `P_front` and `P_retain_given_front` are not perfectly
orthogonal, since a front with more high-complexity rows changes both. The
one-factor-at-a-time discipline limits but does not eliminate this.

### Lens 8: claim discipline and denominator closure

**Attack.** Experiments drift into claiming more than they measured, and case
counts silently fail to reconcile.

**What the plan does.** Every experiment carries pre-registered predictions
(A1 design section 6, G2 design section 5, identifiability design section 6) so a
miss is a finding rather than a quiet revision. Every experiment must reconcile
its case counts exactly, carrying forward the convention the v1 decomposition's
hostile review used, where all three denominators closed to 164, 144 and 36 with
zero symmetric difference. Every reported proportion carries a Wilson interval.

**Residual risk.** Pre-registration is only as strong as the discipline of
recording predictions before results are seen. The predictions in this plan are
committed now, before any world exists, which is the earliest point at which that
is possible.

### Hostile-review summary

| Lens | Attack survives? | Residual risk recorded |
|---|---|---|
| 1. Leakage | Partially | Hypothesis-level Held-out contamination is unavoidable and declared |
| 2. Overfitting to v1 | No | Generator audit recorded as an open item |
| 3. Multiple comparisons | Partially | Family-wise error not eliminated; `CONFIRM` power is limited |
| 4. Difficulty reduction | No | Guard depends on an honestly written rationale |
| 5. Construct validity | No | All claims are about the synthetic regime only |
| 6. Instrumentation effect | No | Identity proven on a control set, not universally |
| 7. Attribution exclusivity | No | `P_front` and `P_retain_given_front` are not fully orthogonal |
| 8. Claim discipline | No | Pre-registration depends on discipline |

No lens produces a fatal objection. Three produce declared residual risks that
must be carried into the v2 architecture decision rather than resolved here.

---

## 6. Open items this plan does not cover

Recorded so their absence is deliberate.

1. **Generator audit.** The per-sample min-max normalisation of `descriptor`, the
   unrenormalised `correlated_distractor`, and the response clip's interaction
   with `MU_CEIL` beyond what E0 probes. Should precede or accompany E0.
2. **Acquisition geometry design.** E1's `alpha_star` and E3's `H_id_geometry`
   arm both point at the 6-point energy grid and the 30-compound test population.
   Redesigning them is a prospective-benchmark question, explicitly out of scope
   here.
3. **The prospective benchmark itself.** Not created, per the mission's scope
   boundary.
4. **Real-data validation.** Everything in this plan is synthetic. No claim here
   transfers to real spectra.
5. **The v2 architecture.** Bounded by the decision tree, chosen by nothing in
   this plan.

---

## 7. Terminal state

```
V2 REMEDIATION EXPERIMENTS PROSPECTIVELY DESIGNED
NO FINAL V2 SCIENTIFIC ARCHITECTURE CHOSEN
```

No experiment executed. No world generated. No search run. No threshold set. No
grammar changed. No benchmark created. The official v1 result stands unchanged.
