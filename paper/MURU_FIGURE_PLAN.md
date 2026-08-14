# MURU pre-results figure plan

Companion to `MURU_MANUSCRIPT_PRE_RESULTS.md`.

**Binding rule.** No final scientific figure may be generated from fabricated,
simulated-for-illustration, or predicted data. Figures 1 to 4 and Figure 6 are
schematic or design figures and can be produced now, because their content is
the frozen design itself. Figure 5 is a design figure with one illustrative
panel that must be drawn from calibration output once it exists. Figures 7 and
8 require prospective results and are specified but not drawn.

Where a figure would benefit from a small illustrative example trajectory, that
example must come from an actual generated Development or Challenge input row,
be labelled as an illustration of the generator rather than a result, and never
from Held-out or Confirmation.

Governance base: `07c64c8` (`engineering-rc3-1-a3-2`).

---

## Figure 1. MURU conceptual pipeline

**Can be created now: YES.** Schematic; no data.

**Scientific question.** What object is being estimated, what is the symbolic
target, and where does truth enter and not enter?

**Panels.**

- **1A. The collapse hypothesis.** A family of `mu_i(E)` trajectories on the
  six-energy grid, and the same trajectories after rescaling the energy axis by
  a per-compound `g_i`, collapsing onto a shared profile `Phi`. Annotate the
  frozen M0 form `mu_i(E) = A_HI + (A_LO - A_HI) * S(E / g_i)`.
- **1B. Two-stage estimation.** Left: fold-local target estimation, showing
  that all shared objects (`Phi`, scale centring, residual variance, weights)
  are fitted from training trajectories only and then frozen, after which each
  validation or test compound is estimated independently. Right: symbolic search
  over `g` as a function of the five covariates.
- **1C. Where truth enters.** A barrier diagram: the structural acceptance
  predicate is truth-blind; planted truth is read only for post-hoc G2/G3
  scoring, downstream of acceptance.

**Data source.** `MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` A1.2 for the
model forms; `MURU_PAPER_BENCHMARK_PROTOCOL.md` for the execution boundary;
`src/muru/paper_benchmark/g2_contract.py` for the truth-blindness statement.
Panel 1A trajectories from an actual Development or Challenge generated input
row, labelled as a generator illustration.

**Axes.** 1A: x = collision energy (15 to 90) and, after rescaling, `E / g`;
y = `mu`. 1B and 1C: none.

**Statistics.** None.

**Caption outline.** State the collapse hypothesis; state that the symbolic
target is the per-compound scalar `g`, not the trajectory; state that shared
objects are training-only; state that acceptance never reads truth. State
explicitly that panel 1A is a generator illustration and not a result.

---

## Figure 2. Prospective study design and partition flow

**Can be created now: YES.** Schematic plus frozen counts.

**Scientific question.** What was frozen, when, and what remains sealed at each
stage?

**Panels.**

- **2A. Case population.** 380 cases; 20 families; 80 Development, 240 Held-out,
  60 Challenge; 4/12/3 per family. Within a case: 180 compounds, 30 scaffold
  groups of 6, scaffold-disjoint 20/5/5 split, six-energy grid.
- **2B. Execution sequence with seals.** Content freeze, engineering RC,
  calibration (100 worlds), threshold freeze, Development rerun, executable
  freeze, one-shot Held-out, Challenge. Annotate each stage with the seal state
  of Held-out and Confirmation at that point. Mark the current position of this
  manuscript.
- **2C. Amendment timeline.** V1 `d94d2c9`, A1 `2ac86c5`, A2 `03cc4d3`,
  A2.1 `80a7803`, A3.1 `c8938e8`, A3.2 `1194fcb`, A3.3 `71f5369`, A3.4 `be23b80`,
  with the A3.4 Temporal Provenance Erratum `220c9cb` (tag `a3-4-temporal-provenance-erratum`),
  and Engineering RC2 `c7c2332`, RC3 `adfdec0`, RC3.1 `07c64c8`, and active RC4 on `eng/muru-rc4-a3-4`.
  Each amendment annotated with its declared temporal position relative to calibration,
  Development, Held-out and Confirmation.

**Data source.** `artifacts/paper_benchmark_partition_manifest.json`,
`artifacts/paper_benchmark_case_manifest.json`,
`MURU_PAPER_BENCHMARK_FREEZE.md`, the seven amendment documents (A1 to A3.4) and their
`artifacts/paper_benchmark_amendment_*.json` records, and `audit/muru_a3_4_temporal_provenance_erratum.json`.

**Axes.** 2C: time, ordered by commit, not calendar.

**Statistics.** None; counts only.

**Caption outline.** Every count is frozen and hashed. Emphasise that the
denominators of Table 2 derive mechanically from case applicability in 2A, and
that each amendment declares and evidences its temporal position.

---

## Figure 3. Synthetic truth families

**Can be created now: YES.** Design figure with generator-illustration curves.

**Scientific question.** What relationships does the benchmark plant, and what
does each family test?

**Panels.**

- **3A. Family map.** A 20-cell grid, F01 to F20, grouped into scalar-truth
  families, adequacy-violation families, and null/adversarial families, colour
  coded by which endpoint group they enter.
- **3B. The five truth families.** `mass_affine_descriptor`, `mass_power`,
  `mass_saturating_descriptor`, `mass_interaction`,
  `mass_exponential_descriptor`, each drawn as `g` against the driving covariate
  at fixed values of the other, to make the shapes visually distinguishable.
- **3C. Adequacy deviations.** M0 against M1 (horizontal shape), M2
  (high-energy floor) and M3 (low-energy ceiling), each shown at its frozen
  standalone amplitude (0.45, 0.18, 0.22), plus F16's attenuated combination
  (0.15, 0.05, 11/180).
- **3D. Covariate structure.** The correlation structure of the five
  covariates, showing that `distractor` is independent and
  `correlated_distractor = 0.85*descriptor + 0.15*noise` is a near-proxy. This
  panel is what makes F11 and F12 legible.

**Data source.** `src/muru/paper_benchmark/registry.py`,
`src/muru/paper_benchmark/generator.py`,
`src/muru/paper_benchmark/g2_contract.py`.

**Axes.** 3B: x = covariate value, y = `g`. 3C: x = collision energy, y = `mu`.
3D: correlation matrix or pairwise scatter.

**Statistics.** 3D may show Pearson or Spearman correlations computed from
generated Development or Challenge covariate frames only.

**Caption outline.** These are planted relationships, not chemistry. State the
frozen amplitudes. State that F20C is outside the grammar by construction.

---

## Figure 4. Null calibration architecture

**Can be created now: YES for the design panels.** Panel 4D requires calibration
output.

**Scientific question.** What is a discovery being compared against, and why is
that comparison constructed the way it is?

**Panels.**

- **4A. Why a calibrated threshold is required.** A purely diagrammatic panel
  with **unlabelled, unscaled axes**, showing only the logical relation: the
  search always returns a candidate, so the candidate's score must be compared
  against a null distribution read at its own complexity. No distribution shape,
  no location, and no percentile value may be drawn until the calibration
  artifact exists; the populated version is panel 4D.
- **4B. The A3.2 base target.** Two rows. Top: the rejected provisional design,
  where the frozen-law target vector is scaffold-structured through `mass` and
  `descriptor`, both driven by the per-scaffold latent, so that permuting only
  the covariates leaves the target's scaffold structure intact and produces a
  train/validation mean shift against a scaffold-disjoint split. Bottom: the
  corrected design, where the target values are globally permuted across all
  180 compound identities before any null-family transformation and before any
  partition use, preserving the marginal distribution exactly while destroying
  the assignment.
- **4C. Seed and namespace separation.** The six independent seed namespaces
  (including `PB|PRED_EQUIV|FRAME|{index:03d}`) and the calibration/smoke seed-band separation.
- **4D. Threshold table.** `T(c)` against complexity 1 to 20, with the
  2,000-resample bootstrap band, and per-construction 95th percentiles overlaid.
  **Requires prospective results: `[PROSPECTIVE RESULT TO INSERT]`.**

**Data source.** `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`,
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md`,
`src/muru/paper_benchmark/rc3_calibration_worlds.py`,
`src/muru/paper_benchmark/rc3_provenance.py`. Panel 4D from the calibration
threshold artifact once it exists.

**Axes.** 4A: unlabelled and unscaled by design. 4D: x = complexity, y =
validation R2.

**Statistics.** 4D: 95th percentile with `method="linear"`, cumulative maximum,
and world-level bootstrap at seed 20260812.

**Caption outline.** The statistic is the maximum over 30 seeds of the best
validation R2 at complexity at most c, which gives the null the same search
multiplicity the protocol takes. The threshold is read at the candidate's own
complexity. The bootstrap band gates nothing and is reported so a reader can see
whether a margin lies inside the calibration's own uncertainty.

Optional historical inset, clearly labelled CLASS A: the Phase 3 complexity-20
threshold of +0.4889 with interval [+0.2603, +0.6859] against Type 2's narrower
[+0.6392, +0.6993], illustrating why calibration size matters. This inset must
not be placed on the same axes as prospective results.

---

## Figure 5. Scalar recovery and adequacy evaluation design

**Can be created now: partially.** Panels 5A to 5C are design; 5D needs results.

**Scientific question.** How is a scalar estimate judged competent, and how is
the collapse model falsified?

**Panels.**

- **5A. G1's three conditions.** Spearman between true and fold-local estimated
  log-`g` at least 0.80; held-out trajectory MAE at most 0.80 of the
  per-energy-mean baseline; and `M0_NOT_REJECTED`. Show that all three are
  required and that an indeterminate adequacy state fails the third.
- **5B. The adequacy ladder.** M0 against M1, M2, M3 by within-compound
  leave-one-energy-out MAE. Show the firing rule: at least 24 of 30 test
  compounds evaluable, and at least 20 of them practical wins at a MAE ratio of
  at most 0.90.
- **5C. Typed states.** A decision tree from the eight-step ordered acceptance
  predicate to its terminal states: accepted, `REJECTED_A1_INADEQUATE`,
  `UNEVALUABLE`, and the individual gate failures.
- **5D. Observed scalar recovery.** Estimated against true log-`g` across the
  164 applicable Held-out cases, coloured by family.
  **Requires prospective results: `[PROSPECTIVE RESULT TO INSERT]`.**

**Data source.** `MURU_PAPER_BENCHMARK_METRICS.md`,
`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md`,
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`.

**Axes.** 5B: x = MAE ratio to M0, y = compound count; mark 0.90. 5D: x = true
log-`g`, y = estimated log-`g`, identity line.

**Statistics.** 5D: Spearman per case; mark the 0.80 criterion.

**Caption outline.** G1 is a conjunction, not a best-of. Indeterminate adequacy
is never acceptance. The 0.90 ratio and the 24/30 and 20/30 counts are frozen by
Amendment A1.

---

## Figure 6. Family versus exact equation recovery

**Can be created now: YES as a concept figure.** Historical panel is CLASS A and
must be labelled as such.

**Scientific question.** Why are family recovery, parameter recovery, predictive
equivalence, and exact algebra recovery different claims, and why does the
benchmark gate on family recovery only?

**Panels.**

- **6A. Ladder of claims.** Five nested levels, weakest to strongest: variable
  support; mathematical family; parameters (exponents and coefficients); predictive
  equivalence on the declared reference distribution; exact algebraic identity.
  Annotate each with its endpoint and Held-out denominator (144, 144 jointly as G2,
  156 with mass 156 / descriptor 84, 144 across 2,160 reference points, 60).
- **6B. Why they diverge.** Schematic Pareto front over complexity and
  validation R2, showing a lower-complexity approximation sitting within a small
  R2 distance of the higher-complexity true form, and a selection rule choosing
  the approximation. Annotate with the mechanism Phase 3 diagnosed: a
  complexity-6 expression within 0.004 held-out R2 of a complexity-13 planted
  form, selected in 30 of 30 seeds.
- **6C. Historical evidence, CLASS A.** Type 2 positive controls: dense-lattice
  family recovery 16 of 20 measured, the study's composite success gate 17 of 20,
  and support 20 of 20, against symbolic equivalence of 0 in every
  positive-control block, with a median of 8.5 distinct functional-equivalence
  classes inside a single reported family. Both the 16/20 and the 17/20 must be
  shown, distinctly labelled, since neither is the G2 definition. Label the
  panel HISTORICAL and do not place it on axes shared with prospective results.
- **6D. Prospective comparison.** G2 rate on 144 against exact-algebra rate on
  60, parameter recovery rate on 156, and predictive equivalence on 144.
  **Requires prospective results: `[PROSPECTIVE RESULT TO INSERT]`.**

**Data source.** 6B and 6C from `PHASE3_DECISION.md` and
`TYPE2_VALIDATION_DECISION.md`. 6A from
`MURU_PAPER_BENCHMARK_METRICS.md`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`,
and the case manifest.

**Axes.** 6B: x = complexity, y = validation R2.

**Caption outline.** Family recovery, parameter recovery, predictive equivalence,
and exact algebra are separate endpoints because historical evidence and
mathematical identifiability limits show they diverge. A low exact-algebra rate
is a finding about identifiability, not a failure of G2. Predictive equivalence
does not imply family recovery; family recovery does not imply exact algebra;
and parameter recovery does not imply exact law identification.

---

## Figure 7. Held-out performance summary

**Can be created now: NO.** Specification only.
**`[PROSPECTIVE RESULT TO INSERT]` for every panel.**

**Scientific question.** Did the three frozen gates pass, and how did the
endpoint ladder behave across families?

**Panels.**

- **7A. The three gates.** Forest plot: G1 (164), G2 (144), G3 (36), each as a
  point estimate with its 95% Wilson interval, with the gate lines drawn at 0.70
  (lower bound, G1 and G2) and 0.15 (upper bound, G3). This single panel carries
  the primary result.
- **7B. Endpoint ladder.** Support (144), family (144), parameter recovery (156,
  with mass /156 and descriptor /84), predictive equivalence (144, over 2,160
  reference points across 12 frames), exact algebra (60), each with Wilson 95%
  interval, ordered from weakest to strongest claim so that any monotone structure,
  in either direction, is visible without being asserted in advance. No pattern is
  predicted; interpretation belongs behind `[INTERPRET HELD-OUT PERFORMANCE]`.
- **7C. By family.** G1 and G2 rates for each applicable family. G1's 164 cases
  are F01 to F05, F07 to F12, F17 and F18 at 12 each (156) plus the F19A and
  F19B variants at 4 each (8); G2's 144 are 12 families at 12 each. The F19A and
  F19B bars must be drawn, since they carry scalar truth with null symbolic
  structure and are the cases where the two gates are expected to disagree by
  construction rather than by performance.
- **7D. By noise.** F01, F02, F03 across every endpoint, giving the prospective
  noise envelope.

**Data source.** Held-out scoring artifacts, after the executable freeze and the
one-shot Held-out run.

**Axes.** 7A and 7B: x = rate 0 to 1, y = endpoint. 7C: x = family, y = rate.
7D: x = noise regime, y = rate.

**Statistics.** Wilson 95% throughout. Denominators are the frozen ones and are
printed on the figure.

**Caption outline.** State numerators and denominators explicitly. State the
gate verdicts. Do not interpret in the caption; interpretation belongs in the
Discussion behind `[INTERPRET HELD-OUT PERFORMANCE]`.

---

## Figure 8. Failure mode map

**Can be created now: partially.** The taxonomy is frozen; the counts are not.

**Scientific question.** When the pipeline does not produce a correct accepted
discovery, what happened instead?

**Panels.**

- **8A. Failure taxonomy.** A frozen map of every typed non-success state and
  where it arises: `REJECTED_A1_INADEQUATE`, `UNEVALUABLE`,
  `SUPPORT_UNRESOLVED`, `FAMILY_AMBIGUOUS`, `COMPLETED_NO_CANDIDATE`,
  `EXECUTION_FAILURE`, each of the eight acceptance gates, and each of the six
  falsification rungs (F1, F4, F5, F7, F9, F10). **Can be drawn now.**
- **8B. Observed census.** Counts of each state across the Held-out run.
  **`[PROSPECTIVE RESULT TO INSERT]`.**
- **8C. Correct refusals against failures.** Separate the worlds where refusal
  is the correct answer (F06, F19C, F20A to F20C) from the worlds where a
  non-discovery is a miss (F01 to F05, F08 to F12, F17, F18). This distinction
  is essential: refusing in F06 is a success, not a failure.
  **`[PROSPECTIVE RESULT TO INSERT]` for the counts; the partition itself can be
  drawn now.**
- **8D. Historical failure modes, CLASS A.** The 14 catalogued historical
  failure modes FM-01 to FM-14, each marked as closed by the prospective design,
  partially addressed, or still live, matching Table 10. Label HISTORICAL.
  **Can be drawn now.**

**Data source.** 8A from `MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md` and
`src/muru/paper_benchmark/structural_acceptance.py`. 8D from
`MURU_SYNTHETIC_FAILURE_MODE_CATALOG.md`. 8B and 8C from Held-out scoring
artifacts.

**Axes.** 8B: x = count, y = state.

**Caption outline.** A typed failure is information, not noise. `UNEVALUABLE`
counts as a G3 violation because a pipeline that avoids unsafe acceptances by
failing to evaluate has not demonstrated safety. Correct refusals are not
penalised.

---

## Figure production status summary

| Figure | Can be created now | Blocking artifact |
|---|---|---|
| 1 conceptual pipeline | **Yes** | none |
| 2 study design and partition flow | **Yes** | none |
| 3 synthetic truth families | **Yes** | none |
| 4 null calibration architecture | Panels 4A to 4C yes; 4D no | calibration threshold artifact |
| 5 scalar recovery and adequacy design | Panels 5A to 5C yes; 5D no | Held-out scoring |
| 6 family versus exact equation recovery | Panels 6A to 6C yes; 6D no | Held-out scoring |
| 7 held-out performance summary | **No** | Held-out scoring |
| 8 failure mode map | Panels 8A, 8C partition, 8D yes; 8B and 8C counts no | Held-out scoring |

**Figures deliberately not planned.** No figure shows a single "discovered
equation" as a headline object, because no expression from this work is a law
and presenting one that way would be an overclaim. No figure places historical
CLASS A rates on the same axes as prospective CLASS C rates. No figure is
generated from fabricated data.
