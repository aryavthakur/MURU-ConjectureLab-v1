# MURU v2: A1 Remediation Study Design

**Status:** DESIGN ONLY. No experiment in this document has been executed. No v1
number is changed, reinterpreted, or superseded. No v2 scientific architecture is
chosen here.

**Covers:** E0 (`A1_ADMISSIBLE_RANGE_PROVENANCE`) and E1
(`A1_JOINT_EVALUABILITY_POWER`).

**Addresses:** RC1 (boundary rule has no magnitude floor, 154/240 cases
`BOUNDARY_LIMITED`, drives all 97 G1 adequacy failures and all 26 G3 violations)
and RC2 (M1/M2/M3 detectors fired 0/240 including 0/48 planted positive
controls).

**Binding constraint from the ranking:** RC1 and RC2 pull in opposite directions
and cannot be tuned independently. Every rule in this study is therefore scored
on evaluability and power *jointly*, on the same worlds, in the same pass. A rule
that fixes one and destroys the other is inadmissible by construction, not by
later judgement.

---

## 1. Why a floor cannot simply be chosen

The decomposition's section 3.4 counterfactual is a diagnostic probe, not a
proposal. Three separate facts make "pick a relative floor" an unsafe move.

**First, the counterfactual is measured on spent evidence.** Held-out produced
the official v1 result and has now been exhaustively mined. Choosing 1e-2 because
it converts 123 cases is selection on the outcome surface.

**Second, evaluability is not the binding problem.** At the 10 percent
counterfactual floor every one of the 240 cases becomes evaluable and the
detector firing count is *still zero*. A floor chosen to maximise evaluability
would produce a v2 in which A1 decides every case and decides every case the same
way, which is a worse validity failure than v1's, not a better one.

**Third, the admissible range is not independently justified.** `MU_CEIL` is
`1.0 - 1e-4`. `generator.py` line 221 clips every generated response with
`np.clip(mu, 1e-4, 1 - 1e-4)`. The fitter's admissible ceiling and the
generator's response clip are *the same constant*. `adequacy.py` says so in its
own comment: "The frozen generator response clip, reused as the admissible
response range."

### 1.1 A new observation from the frozen taxonomy

Recomputed from `MURU_V1_G1_FAILURE_TAXONOMY.csv` for this design, and stated as
a motivating observation rather than a result:

| Population | n | median `mu_max` | min | max |
|---|---|---|---|---|
| `M0_NOT_REJECTED` | 67 | 0.9802 | 0.9277 | 0.9999 |
| `BOUNDARY_LIMITED` | 97 | **0.9999** | 0.9487 | 0.9999 |

72 of the 164 G1 cases have a `mu_max` of exactly `0.9999`, the clip value. The
boundary-limited population sits at the clip by median; the adequate population
does not.

This sharpens RC1's mechanism. The decomposition reported `mu_max` as the single
strong predictor of M3 evaluability at r = -0.550 and correctly called it
"response geometry against a fixed admissible ceiling". The stronger reading
available from the same table is that the ceiling and the clip are one constant,
so the generator manufactures a point mass of observations exactly at the value
the fitter treats as its upper bound, and the M3 plateau parameter pins there
deterministically. The worked example in decomposition section 3.4, C150 fitting
at plateau 0.9999 and probing to 1.0009, is that mechanism firing.

If this is right, calibrating a floor while holding `MU_CEIL` fixed relocates the
artifact instead of removing it, exactly as RC1's third risk warns. E0 tests it
before E1 is allowed to run.

---

## 2. E0: admissible-range provenance and circularity test

### 2.1 Hypotheses

| ID | Statement |
|---|---|
| **H_clip** (primary) | The M3 boundary event is manufactured by the coincidence `MU_CEIL == generator response clip`. Breaking the coincidence removes most boundary events on true-M0 worlds. |
| **H_alias** (secondary) | Over a 6-point energy grid, the M3 plateau `b` and the M0 scale `g` are partially aliased, so a true-M0 compound with an unusually small `g` drives `b` toward its upper bound even without a clip. Breaking the coincidence reduces but does not remove boundary events. |
| **H_null** | Neither. Boundary events track fold noise, and `MU_CEIL` is exonerated. |

H_clip and H_alias are not exclusive. E0 measures their relative contribution.

### 2.2 Independent variable

A crossed 3 x 3 manipulation of two constants that v1 held equal:

| Factor | Levels |
|---|---|
| generator response clip `C_gen` | `1 - 1e-4` (v1), `1 - 1e-3`, no clip |
| fitter admissible ceiling `MU_CEIL` | `1 - 1e-4` (v1), `1 - 1e-3`, `1.0 + 1e-2` (open) |

The `(1 - 1e-4, 1 - 1e-4)` cell is the control arm and must reproduce v1
boundary behaviour on a v1-matched world within Monte Carlo error. If it does
not, E0 aborts and the discrepancy is resolved before anything else runs.

### 2.3 Controls

- **True M0 only.** No planted M1/M2/M3 deviation anywhere in E0. Every boundary
  event observed is by construction a false one.
- **Shared randomness.** All nine cells use the same covariate seeds, the same
  `mu_inf`, `phi_p`, `g` draws and the same noise draws. Cells differ only in the
  two manipulated constants. This makes the comparison paired at the compound and
  fold level.
- **No search.** PySR is never imported by E0.

### 2.4 Metrics

Per cell, per detector, at the compound-fold level and aggregated to the case:

| Metric | Definition |
|---|---|
| `contact_rate` | fraction of fits with `boundary_contact` |
| `unresolved_rate` | fraction of fits with `unresolved_boundary` |
| `probe_gain_rel` | distribution of `(best_obj - probe_obj) / best_obj` on triggering probes |
| `evaluable_M3` | evaluable test compounds for the M3 contrast, 0..30 |
| `boundary_limited_rate` | fraction of cases with case status `BOUNDARY_LIMITED` |
| `pin_at_ceiling_share` | share of M3 fits whose `low_energy_plateau` equals the ceiling to `BOUNDARY_CONTACT_TOL` |
| `mu_max_at_clip_share` | share of test compounds whose observed max response equals `C_gen` exactly |

### 2.5 Case count and seeds

9 cells x 60 worlds = **540 worlds**, all true M0, 30 test compounds each,
6 energies. Seeds derive from the v2 namespace (section 5).

Sixty worlds per cell gives a standard error of at most 0.065 on any measured
proportion, which is ample for a manipulation predicted to move
`boundary_limited_rate` by tens of points.

### 2.6 Decision criterion

Pre-declared, evaluated on the 540 worlds:

| Outcome | Conclusion | Consequence for E1 |
|---|---|---|
| `boundary_limited_rate` falls by **more than 0.50** when the clip and ceiling are decoupled | H_clip carries the mechanism | `MU_CEIL` must be re-derived from an identifiability argument **before** any floor is calibrated. E1 runs with the re-derived ceiling as its control, and the v1 ceiling as a reported arm. |
| falls by **0.10 to 0.50** | H_clip and H_alias both contribute | E1 runs with the ceiling as an explicit third factor, not a fixed constant. |
| falls by **less than 0.10** | H_null; `MU_CEIL` is exonerated | E1 runs with `MU_CEIL` fixed at the v1 value and the floor question is the whole question. |

### 2.7 Cost

No symbolic search. One case's A1 pass is 3 detectors x 30 compounds x 6 folds
x 2 models = 1,080 vectorised grid fits. Measured basis: v1 executed this over
240 cases inside diagnostic stages the decomposition describes as taking "a few
minutes each".

Budget: **540 worlds, estimated 0.5 to 1.5 CPU-hours**, embarrassingly parallel.
A 5-world pilot measures the true per-world cost and the estimate is replaced by
the measurement before the full run.

### 2.8 What each outcome supports

- **H_clip confirmed.** RC1's remediation is not a threshold change at all. It is
  the removal of a specification coincidence. This is the cheapest and most
  defensible possible v2 change, and it is not a difficulty reduction: it removes
  an artifact that has no scientific content.
- **H_alias confirmed.** The 6-point energy grid cannot separate the M3 plateau
  from the M0 scale. That is an acquisition-geometry finding, and it propagates
  directly into the prospective benchmark's energy design. No threshold fixes it.
- **H_null confirmed.** RC1 is genuinely a magnitude-floor problem and E1's floor
  ladder is the right instrument.

---

## 3. E1: joint evaluability and detector-power calibration

### 3.1 Hypotheses

| ID | Statement |
|---|---|
| **H1** | There exists a boundary/identifiability criterion and a practical-win rule which jointly achieve detector power at or above 0.80 for M1, M2 and M3 at the v1-planted deviation amplitude, while holding false rejection on true-M0 worlds at or below 0.05 and the indeterminate rate at or below 0.10. |
| **H2** | The v1 detector amplitudes lie *below* the detection floor of the 30-compound, 6-energy LOEO contrast, so no threshold choice achieves power 0.80 at those amplitudes, and power is only reachable at larger amplitudes. |
| **H3** | Evaluability and power trade off monotonically: every criterion that raises the evaluable-compound count also raises the false-rejection rate, so no admissible point exists. |

H1, H2 and H3 are mutually exclusive on the primary cells and are the three
outcomes the decision tree branches on.

### 3.2 Independent variables

**Design factors (world construction).**

| Factor | Levels | Note |
|---|---|---|
| deviation type `D` | M0, M1, M2, M3, M1+M2+M3 | M1+M2+M3 mirrors F16 |
| effect-size multiplier `alpha` | 0, 0.25, 0.5, 1.0, 2.0 | multiplies the frozen standalone amplitude for `D` |
| response noise sd | 0.0, 0.02, 0.06 | spans F01 / default / F03 |

The frozen standalone amplitudes are `M1_HORIZONTAL_AMPLITUDE = 0.45`,
`M2_HIGH_ENERGY_AMPLITUDE = 0.18`, `M3_LOW_ENERGY_AMPLITUDE = 0.22`, and for the
combined family `COMBINED_M1_AMPLITUDE = 0.15`, `COMBINED_M2_AMPLITUDE = 0.05`,
`COMBINED_M3_AMPLITUDE = 11/180`. `alpha = 1.0` reproduces the v1-planted
amplitude exactly. `alpha = 0` is the true-M0 null and is shared across deviation
types, so the null arm is one population of worlds, not five.

The ladder deliberately extends to `alpha = 2.0` and down to `alpha = 0.25` so
the study **locates** the detection threshold rather than assuming the v1
amplitude is the right operating point. This is the guard against calibrating to
v1's difficulty.

Cell count: 4 non-null deviation types x 4 non-zero alphas x 3 noise levels = 48,
plus 3 null cells (one per noise level) = **51 cells**.

**Analysis factors (rules, applied post hoc to persisted fits).**

Boundary / identifiability criteria:

| ID | Criterion | Free parameters |
|---|---|---|
| **C0** | v1 frozen: unresolved iff `probe_obj < best_obj - 1e-12` | 0 (control) |
| **C1** | relative-SSE floor: unresolved iff `(best_obj - probe_obj)/best_obj > delta` | 1, `delta` in {1e-3, 3e-3, 1e-2, 3e-2, 1e-1} |
| **C2** | noise-scaled floor: unresolved iff `best_obj - probe_obj > delta * sigma_hat^2 * n_fold`, `sigma_hat` a fold-local residual scale | 1, `delta` in {0.25, 0.5, 1, 2, 4} |
| **C3** | interval criterion: unresolved iff the parameter's profile-SSE one-standard-error interval crosses the bound **and** extends outward beyond a declared fraction `rho` of the admissible range | 1, `rho` in {0.05, 0.10, 0.25} |
| **C4** | **verdict invariance**: refit the model with the bound relaxed by a declared margin, recompute the compound's LOEO practical-win verdict under both fits, and declare `BOUNDARY_LIMITED` **only if the two fits disagree on the verdict** | 0 magnitude parameters; 1 declared relaxation margin |

C4 is the design's preferred candidate and is stated here so it can be refuted
rather than assumed. Its motivation is direct: the boundary only matters if it
could change the answer. v1 removed compounds whose triggering improvement was a
median 1.3 percent of fold sum of squares, which almost certainly left the
win/no-win verdict untouched, so those removals were pure loss of evaluability
with no protective content. C4 converts a tuned threshold into a decision
invariance test and introduces no magnitude parameter at all. If C4 is
admissible, RC1 is resolved without adding a free parameter to the contract.

Practical-win / firing rules:

| ID | Rule | Free parameters |
|---|---|---|
| **P0** | v1 frozen: `mae_alt <= 0.90 * mae_m0`, wins >= 20 of 30, evaluable >= 24 | 3 (control) |
| **P1** | ratio `r` in {0.80, 0.90, 0.95, 0.98} x win count `w` in {15, 18, 20, 24}, evaluable floor fixed at 24 | 2 swept |
| **P2** | paired sign test on per-compound LOEO error differences at level `q` in {0.05, 0.01, 0.001}, replacing the fixed win count; uses `directional_null_tail`, which is already implemented and currently gates nothing | 1 |
| **P3** | conjunction: median relative LOEO error reduction >= `m` **and** win fraction >= `f`; `m` in {0.05, 0.10}, `f` in {0.5, 0.6, 0.67} | 2 |

The evaluability floor `MIN_EVALUABLE_COMPOUNDS = 24` is swept as a fourth level
{18, 21, 24, 27} only in a clearly-labelled secondary sweep, because moving it
changes the denominator of every other metric.

### 3.3 The joint structure, and why it is the point

Evaluability and power cannot be measured separately because a criterion that
admits more compounds changes both the contrast denominator and the win count.
The full analysis grid is the cross product `C x P`, evaluated on every cell.
Every point on that grid is scored on the **same** persisted fits, so the
comparison is exactly paired and costs no additional computation.

### 3.4 Controls

1. **Control arm.** `(C0, P0)` is the frozen v1 rule. It must reproduce v1's
   qualitative behaviour on `alpha = 1.0` worlds: near-zero detector firing and a
   high `BOUNDARY_LIMITED` rate. If it does not, the fresh worlds do not
   reproduce the v1 regime and the study is invalid. This is a hard abort.
2. **Shared null.** The `alpha = 0` worlds are the single false-rejection
   population for every criterion and rule.
3. **Paired worlds.** Every `(D, alpha, noise)` cell shares covariate and noise
   seeds with its `alpha = 0` counterpart at the same replicate index, so
   power and false rejection are measured on matched geometry.
4. **Detector identity.** Firing of the *wrong* detector is recorded separately
   and is a failure, not a success. v1's contract already preserves detector
   identity (`detector_sensitivity_success`); E1 measures whether the candidate
   rules preserve it.
5. **Truth blindness.** The fitting and rule-evaluation code never reads the
   planted deviation type. Truth is joined in a separate scoring pass.

### 3.5 The fit-record instrument

E1's load-bearing engineering property: **fit once, score every rule post hoc.**

For every (world, detector, compound, fold) the following is persisted before any
rule is applied:

```
world_id, cell_id (D, alpha, noise), replicate, split (CALIBRATE|CONFIRM),
detector, compound_id, fold_index, n_observed_energies,
m0_params, m0_objective, m0_boundary_contact, m0_probe_objectives_by_param_side,
mk_params, mk_objective, mk_boundary_contact, mk_probe_objectives_by_param_side,
mk_relaxed_params, mk_relaxed_objective,          # C4
mk_profile_sse_curve_at_bound,                     # C3
fold_residual_scale_sigma_hat,                     # C2
held_energy, held_response, m0_abs_error, mk_abs_error
```

Nothing in that record is a verdict. Every criterion in section 3.2 is a pure
function of it. This makes the rule comparison a re-scoring pass measured in
seconds, and it makes the whole grid reproducible from the persisted record
without refitting.

Record volume: 3,750 worlds x 3 detectors x 30 compounds x 6 folds = **2.02
million fold records**, roughly 400 MB as columnar parquet.

### 3.6 Metrics

Per `(criterion, rule, cell)`:

| Metric | Definition | Direction |
|---|---|---|
| `FRR` | P(any detector fires) on `alpha = 0` worlds | lower better |
| `power_D` | P(the correct detector for `D` fires) | higher better |
| `misattribution` | P(a detector other than `D`'s fires) on `D` worlds | lower better |
| `indeterminate_rate` | P(status not in {`M0_NOT_REJECTED`, `M0_REJECTED_*`}) | lower better |
| `evaluable_dist` | distribution of evaluable compounds per detector | reported |
| `alpha_star_D` | smallest `alpha` at which `power_D >= 0.80` with Wilson lower >= 0.70 | **headline** |
| `monotone_D` | is `power_D` non-decreasing in `alpha` | must hold |

All proportions carry 95 percent Wilson intervals, matching the endpoint
convention already used by `g2_contract.wilson_lower_95` / `wilson_upper_95`.

`alpha_star_D` is the headline result of the entire study, above any pass/fail
verdict. It is the deviation amplitude at which the A1 contrast, as specified,
becomes detectable on this acquisition geometry. Reporting it is what converts
E1 from threshold tuning into a measurement.

### 3.7 Case count and seeds

51 cells x 75 worlds = **3,825 worlds**.

Seventy-five replicates per cell gives a standard error of 0.046 at p = 0.8, so a
Wilson lower bound at an observed 0.80 clears 0.70 comfortably, which is what the
decision criterion requires.

**Split.** At generation time each world is assigned to `CALIBRATE` (80 percent,
60 per cell) or `CONFIRM` (20 percent, 15 per cell) by a dedicated seed. Both
sets are generated in the same pass and sealed together. **`CONFIRM` is opened
exactly once, after the rule is selected on `CALIBRATE` alone.** This is the
internal replication that controls the multiple-comparison exposure described in
section 3.10.

### 3.8 Decision criterion

Declared before any world is generated.

**Admissibility.** A pair `(C, P)` is ADMISSIBLE iff, on the `CALIBRATE` set:

1. `FRR <= 0.05` with Wilson upper `<= 0.10`, pooled over the three null cells;
2. `indeterminate_rate <= 0.10` with Wilson upper `<= 0.15` on the null cells;
3. `power_D >= 0.80` with Wilson lower `>= 0.70` for each of M1, M2, M3 at
   `alpha = 1.0`, noise 0.02;
4. `misattribution <= 0.05` on every non-null cell at `alpha = 1.0`;
5. `power_D` monotone non-decreasing in `alpha` within every deviation type.

Criterion 5 is a validity check, not a performance check. A rule that is
non-monotone in effect size is rejected however well it scores at a point.

**Selection among admissible pairs.** Pre-declared lexicographic order:

1. fewest total free parameters;
2. lowest `indeterminate_rate` on the null cells;
3. highest `min(power_M1, power_M2, power_M3)` at `alpha = 1.0`;
4. lowest ladder index (the most conservative parameter value).

Fewest-free-parameters first is deliberate. It makes C4 win any tie against a
tuned floor, and it prevents the study from selecting the most elaborate rule
merely because elaboration buys fit.

**Confirmation.** The selected pair is then evaluated once on `CONFIRM`. It is
adopted only if criteria 1 to 4 hold again there. If they do not, no rule is
adopted from this study and the result is reported as a failure to replicate.

**If no pair is admissible.** That is outcome H2 or H3 and is reported as such.
It is not a licence to weaken the criteria. See section 3.10.

### 3.9 Cost

| Item | Basis | Estimate |
|---|---|---|
| A1 fitting, 3,825 worlds | 1,080 grid fits per world, doubled for C4's relaxed refit | 6 to 10 CPU-hours |
| C3 profile curves | one extra profile sweep per bounded parameter per fold | +1 to 2 CPU-hours |
| Rule re-scoring, full `C x P` grid | pure function of persisted records | minutes |
| Storage | 2.02 M fold records | ~400 MB parquet |

**Total: under 12 CPU-hours, no symbolic search, fully parallel.** A 5-world
pilot replaces every estimate above with a measurement before the full run is
authorised.

### 3.10 What each outcome supports

| Outcome | Conclusion | Licensed v2 change |
|---|---|---|
| **H1**, and C4 is the selected criterion | The boundary defect was a decision-irrelevance defect. Removing it needs no new free parameter. | Replace the `obj < best_obj - 1e-12` test with verdict invariance. Adopt the selected win rule. Nothing else in A1 changes. |
| **H1**, and C1/C2/C3 is selected | A magnitude or interval floor is genuinely needed. It is now calibrated on fresh worlds, with a measured false-rejection rate and a measured `alpha_star`. | Adopt the floor at the selected value, and record `alpha_star_D` as the endpoint's declared sensitivity limit. |
| **H2**: no pair admissible at `alpha = 1.0`, but admissible at `alpha >= 2.0` | The v1-planted deviation amplitudes are below the detection floor of a 30-compound, 6-energy LOEO contrast. F13 to F16 were not tests of the detector. | **No threshold change is licensed.** Either the acquisition geometry changes (more energies per compound, more test compounds) or the benchmark's planted amplitudes are re-declared. Both are benchmark changes and must clear section 3.11. |
| **H3**: evaluability and power trade off with no admissible point at any `alpha` | The A1 contrast design, not its constants, is inadequate. | Escalate to redesigning the adequacy statistic. No constant in `adequacy.py` may be edited on this evidence. |

### 3.11 The difficulty-reduction guard

H2 is the dangerous outcome, because its natural response is to raise the planted
amplitudes until the detectors fire, which improves every score and demonstrates
nothing.

The guard is a declared asymmetry:

- **Reporting `alpha_star_D` is mandatory and is the primary result.** It is a
  measurement of the method's sensitivity on this geometry and it stands whatever
  the benchmark then does.
- **Changing a planted amplitude is permitted only if** (a) E1 measures
  `alpha_star_D` above the current amplitude, **and** (b) an external scientific
  rationale states what deviation magnitude is chemically meaningful, written
  before the new amplitude is chosen, **and** (c) the new amplitude is set from
  that rationale, not from `alpha_star_D`.
- If (b) cannot be written, the correct action is to keep the amplitude and
  narrow the endpoint claim to "the detector is sensitive to deviations at or
  above `alpha_star`", reporting the current amplitude as below that floor.

A benchmark that is easier because the planted signal was raised to meet the
method is a different benchmark. A benchmark whose planted signal is set from a
stated scientific criterion, and whose method's sensitivity floor is separately
measured and reported, is a stronger one. Only the second is licensed.

---

## 4. Interaction with G3

RC1's second risk is explicit: loosening evaluability admits cases the current
rule conservatively refused, so G3's safety direction changes and must be
re-argued from scratch rather than inherited.

E1 therefore does not conclude on its own. Every admissible pair is carried into
E6 (`FALSE_STRUCTURE_SAFETY_COUNTERWEIGHT`), which measures unsafe structural
acceptance on mass-only, null and adversarial worlds under that pair. **E6 holds
veto.** A pair that satisfies every criterion in section 3.8 and fails E6 is not
adopted.

v1's safety evidence rested on 10 evaluable G3 opportunities. E6 requires at
least 100. That is the specific sense in which resolving RC1 makes G3 informative
rather than merely passing.

---

## 5. Seed and namespace discipline

Every world in E0 and E1 is generated under a namespace disjoint from the
benchmark's:

```
world_id     = "V2C|<experiment>|<cell_id>|r<replicate:03d>"
seed payload = "muru-v2-calibration|" + "|".join(parts)
```

`generator.derive_seed` prefixes `"paper-benchmark-v1|"`. The v2 payload prefix
differs, so no v2 calibration world can collide with any benchmark case's seed
stream or content hash. A static check asserts the two prefixes are distinct and
that no `V2C|` world id resolves through `registry.resolve_case_id`.

**Partition discipline:**

| Partition | Cases | v2 status |
|---|---|---|
| Held-out | 240 | **Spent.** Produced the official v1 result and has been exhaustively mined. May not calibrate any v2 rule. |
| Development | 80 | Contaminated by v1 tuning history. Not a calibration surface for v2. |
| Challenge | 60 | **Sealed and unopened.** Reserved as v2's confirmation partition. Nothing in this plan touches it. |
| `V2C` worlds | fresh | The only surface on which a v2 rule may be calibrated. |

---

## 6. Pre-registered predictions

Recorded before execution so a miss is itself a finding.

| ID | Prediction |
|---|---|
| PE0-1 | E0's decoupled cells reduce `boundary_limited_rate` on true-M0 worlds by more than 0.50, confirming H_clip. |
| PE0-2 | `pin_at_ceiling_share` in the v1 control cell exceeds 0.5 of M3 fits. |
| PE1-1 | `(C0, P0)` on `alpha = 1.0` worlds reproduces near-zero firing, matching v1's 0/48 positive-control result. |
| PE1-2 | C4 is admissible and is selected under the lexicographic order. |
| PE1-3 | `alpha_star_M3` exceeds 1.0, meaning the F15 planted amplitude is at or below the detection floor. |
| PE1-4 | `alpha_star` for the combined family exceeds `alpha_star` for the standalone families, because F16's components are attenuated to 1/3, 5/18 and 5/18 of standalone. |

PE1-2 and PE1-3 are in tension: if PE1-3 holds, C4 may be admissible only at
larger amplitudes. That tension is the substance of the study and the decision
tree branches on which way it resolves.

---

**Terminal state for this document:** design only. No world generated, no fit
executed, no rule selected.
