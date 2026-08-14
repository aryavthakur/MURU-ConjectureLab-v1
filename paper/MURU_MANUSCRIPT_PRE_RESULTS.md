# MURU ConjectureLab v1: pre-results manuscript

## Document status

**PRE-RESULTS DRAFT.** Synchronized through Amendment A3.4 and the subsequent
temporal-provenance adjudication, before Development G2/G3 were scored, and
while Held-out and Confirmation remained strictly sealed and unopened.

Every section below is one of three kinds, and they are never mixed:

| Class | Meaning | Writable now |
|---|---|---|
| **CLASS A** | Historical development evidence (Phase 2, Phase 3, Type 2, engine-competence audit, soundness audits) | Yes, as background, motivation and explicitly labelled supporting synthetic evidence |
| **CLASS B** | Frozen prospective methods (benchmark architecture, A1/A2/A2.1/A3.1/A3.2/A3.3/A3.4, Engineering RC3/RC3.1, A3.4 temporal provenance erratum, endpoints, thresholds, provenance rules) | Yes |
| **CLASS C** | Prospective results (calibration, Development, Held-out, Confirmation) | **No.** Placeholders only |

Placeholder tokens used literally in this document:

- `[PROSPECTIVE RESULT TO INSERT]`
- `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
- `[CITATION REQUIRED: ...]`
- `[INTERPRET ...]`

Governance base of this draft: Amendment A3.4 (`be23b80d63fbd30227f0ab8f200dddc2121f3bfe`,
tag `benchmark-content-freeze-a3-4`), following Amendment A3.3 (`71f53697e8894df6469ad0ff7150a049fa531b74`,
tag `benchmark-content-freeze-a3-3`), the A3.3 hostile mathematical review (`78cc7c2`),
the A3.4 pre-engineering integrity review (`f1fb943`), and the A3.4 Temporal Provenance Erratum
(`220c9cb679e03865f1b2a02b975397de9f4c7b46`, tag `a3-4-temporal-provenance-erratum`),
with active executable engineering integration on branch `eng/muru-rc4-a3-4`.

Two historical verdicts are preserved verbatim and are never rescored:
Phase 3 is **STOP BEFORE PHASE 4**; the prospective Type 2 objective-alignment
study is **DO NOT AUTHORIZE PHASE 4**.

---

# Section 1. Title options (provisional)

All titles are **PROVISIONAL** until prospective Held-out results exist. None
may imply real-world biological or instrumental validation.

1. Prospectively frozen synthetic validation of symbolic discovery for
   molecule-conditional collision-energy scaling in tandem mass spectrometry
2. A frozen synthetic benchmark for symbolic recovery of collision-energy
   scaling relationships in MS/MS
3. Separating family-level and exact-algebraic recovery in symbolic regression:
   a synthetic benchmark for energy-resolved tandem mass spectrometry
4. Null-calibrated symbolic discovery of collision-energy scaling: a
   prospective synthetic benchmark with sealed evaluation partitions
5. What a symbolic regression pipeline can and cannot recover about
   collision-energy scaling: a pre-registered synthetic study
6. Falsification-first evaluation of symbolic discovery on synthetic
   energy-resolved fragmentation trajectories
7. Prospective synthetic benchmarking of molecule-specific energy-axis
   rescaling in tandem mass spectrometry
8. Structural safety and false-discovery control in symbolic regression for
   collision-energy scaling: a frozen synthetic benchmark
9. Design and prospective evaluation of a 380-case synthetic benchmark for
   symbolic collision-energy scaling discovery

Rejected title vocabulary, recorded so it cannot re-enter: "universal law",
"physical law", "mechanistic law", "the collision energy law", "discovering the
equation of fragmentation", and any construction implying a real biological or
instrumental result. Wording is bounded by Section 13.

---

# Section 2. Structured abstract shell

**Background.** Collision energy is a principal experimental determinant of
how a precursor ion fragments in tandem mass spectrometry
`[CITATION REQUIRED]`, and energy-resolved
acquisitions are routinely recorded. Downstream spectral modelling nonetheless
frequently treats collision energy as a nuisance label or a fixed condition
rather than as a continuous axis along which molecule-specific behaviour can be
aligned. A molecule-conditional rescaling of the energy axis, if it exists,
would be a compact and interpretable object. Symbolic regression is an
attractive tool for recovering such an object because it returns a closed-form
expression rather than an opaque predictor, but for the same reason it creates
false-discovery and identifiability risks that ordinary predictive validation
does not test.

**Objective.** To evaluate, under prospectively frozen synthetic conditions
where the generating relationship is known exactly, whether a symbolic
discovery pipeline can (i) recover a molecule-specific horizontal energy scale,
(ii) reject worlds in which the scalar collapse model is inadequate, (iii)
recover the correct variable support and mathematical family of the generating
expression, and (iv) refrain from accepting structural claims in null and
adversarial worlds. Parameter recovery, predictive equivalence, and exact
algebraic recovery are evaluated as separate, explicitly secondary endpoints.

**Methods.** We constructed a fully synthetic benchmark of 380 cases in 20
prospectively defined case families (F01 to F20), partitioned into 80
Development, 240 Held-out, and 60 Challenge cases. Each case contains 180
synthetic compounds in 30 scaffold groups measured on a six-point energy grid
(15, 30, 45, 60, 75, 90), with a scaffold-disjoint 20/5/5 group split into
training, validation and test. Case content, generator, truth payloads, seeds,
partitions, endpoint denominators and gate thresholds were frozen before
execution and hashed; subsequent changes were made only through numbered,
recorded amendments (A1, A2, A2.1, A3.1, A3.2, A3.3, A3.4, and the A3.4
temporal provenance erratum), each of which declares its temporal position with
respect to sealed material. Three primary gates were frozen in advance: G1 scalar
competence on 164 applicable Held-out cases (Wilson lower 95% bound at least
0.70), G2 family recovery on 144 applicable Held-out cases (Wilson lower 95%
bound at least 0.70), and G3 principal structural safety on 36 Held-out
opportunities (Wilson upper 95% bound at most 0.15). Structural acceptance is
truth-blind and ordered: adequacy status, a null-calibrated validation R2
threshold at the candidate's own complexity, seed stability of at least 20 of 30,
complexity at most 20, invalid fraction at most 0.005, non-empty effective
support, a gradient-boosted ceiling condition, and a reduced falsification
harness. The acceptance threshold is not assumed; it is calibrated on 100
structural-null worlds, 30 search seeds each, using the maximum across seeds of
the best validation R2 at complexity at most c, taken at the 95th percentile and
made non-decreasing in complexity. Secondary endpoints were prospectively bound
under Amendment A3.4: Parameter Recovery on 156 cases (joint /156, mass exponent
/156 with tolerance 0.15, descriptor coupling /84 with tolerance 0.10, at the
frozen anchor) and Predictive Equivalence on 144 cases (relative RMSE <= 0.05
and Pearson r >= 0.990 over 2,160 reference points across 12 case-shaped frames
from the frozen synthetic covariate generator). Symbolic search used PySR 1.5.10
under a frozen operator grammar and frozen search settings. The 240-case Held-out
partition was sealed and is opened once, after threshold freeze and executable
freeze. The separately governed real-data Confirmation set remains sealed and is
not opened by this work.

**Results.** `[PROSPECTIVE RESULT TO INSERT]`

Specifically pending: calibration validity and threshold table
`[PROSPECTIVE RESULT TO INSERT]`; Development sanity outcome
`[PROSPECTIVE RESULT TO INSERT]`; G1 numerator/denominator and Wilson interval
`[PROSPECTIVE RESULT TO INSERT]`; G2 numerator/denominator and Wilson interval
`[PROSPECTIVE RESULT TO INSERT]`; G3 numerator/denominator and Wilson interval
`[PROSPECTIVE RESULT TO INSERT]`; parameter recovery on the 156 applicable
Held-out cases (joint /156, mass /156, descriptor /84)
`[PROSPECTIVE RESULT TO INSERT]`; predictive equivalence on the 144 applicable
Held-out cases `[PROSPECTIVE RESULT TO INSERT]`; exact-algebra recovery on the 60
applicable Held-out cases `[PROSPECTIVE RESULT TO INSERT]`.

**Conclusions.** `[PROSPECTIVE RESULT TO INSERT]`

No conclusion is precommitted. The umbrella positive claim is available only if
preconditions hold and G1, G2 and G3 all pass; any failed gate blocks it while
the descriptive endpoint reports are retained. Secondary endpoints remain
subordinate to the primary gates and never merge into G1, G2, or G3.

---

# Section 3. Introduction

## 3.1 Collision energy determines fragmentation, and is under-modelled

In tandem mass spectrometry the collision energy applied to a selected
precursor governs the extent and pattern of its dissociation. As energy
increases, precursor survival falls and product-ion distributions shift toward
lower-mass fragments. This dependence is not incidental; it is the mechanism by
which MS/MS produces structural information at all
`[CITATION REQUIRED: standard reference for collision-induced dissociation and energy dependence]`.

Energy-resolved acquisition, in which the same precursor is fragmented across a
grid of collision energies, is widely available and is recorded in public
spectral libraries
`[CITATION REQUIRED: MassBank / spectral library reference]`. Despite this,
collision energy is often handled downstream as a categorical acquisition label,
a matching constraint during library search, or a fixed setting held constant
across a study, rather than as a continuous axis with molecule-dependent
structure `[CITATION REQUIRED: representative spectral prediction or library
matching work that conditions on discrete CE settings]`. Three practical
consequences follow: spectra acquired at nominally identical instrument settings
are not directly comparable across molecules; energy is frequently
re-parameterised per instrument vendor in ways that do not transfer; and models
trained at one energy setting generalise poorly to another
`[CITATION REQUIRED: evidence that models fitted at one collision-energy setting degrade at another]`.

A statement of the reporting problem that this project treats as binding: the
collision energy field in a spectral record is frequently a bare number whose
unit and normalisation convention are not declared by the record itself. In this
project's own real-data audit, collision energy is therefore never stored as a
single field; the raw string, the parsed numeric value, the declared energy
type, and separately derived laboratory-frame and centre-of-mass values are
retained as distinct columns
(`README.md`, "Collision energy is never one field").

## 3.2 Molecule-specific scaling and trajectory alignment

If the energy dependence of a fragmentation functional had a shared shape across
molecules, and differed between molecules mainly by a horizontal stretch of the
energy axis, then a single shared curve plus one scalar per molecule would
describe the whole family. Writing `mu_i(E)` for a scalar fragmentation
functional of molecule `i` at energy `E`, the object of interest is

```
mu_i(E) ~= Phi(E / g_i)
```

with `Phi` shared across molecules and `g_i` a molecule-specific horizontal
scale that depends only on molecular descriptors. This is the hypothesis the
project labels H-MAIN in `MURU_ConjectureLab_v1_Master_Plan.md`.

The scientific attraction of this form is that it factors an experimentally
awkward two-dimensional object into a shared curve and a one-dimensional
molecule property. The scientific danger is equally clear. A scalar per molecule
is a very flexible device, and a rescaling that improves apparent alignment is
not by itself evidence that the rescaling means anything. The project's own
master plan records an early warning of exactly this kind: on a 56-compound
sample, a power-law sweep over energy rescalings found its optimum at an
exponent of -0.5, pointing opposite to the direction unimolecular-dissociation
theory would suggest, and more plausibly absorbing the response's own
normalisation by precursor mass than revealing physics
(`MURU_ConjectureLab_v1_Master_Plan.md` Section 1). That observation motivated
building falsification machinery before, not after, the search engine.

## 3.3 Why symbolic regression, and why it is dangerous here

Symbolic regression searches over closed-form expressions rather than over the
parameters of a fixed model class
`[CITATION REQUIRED: symbolic regression method reference, e.g. the PySR / SymbolicRegression.jl description]`.
If the aim is a compact, inspectable description of `g` as a function of
molecular descriptors, an expression is the natural output: it can be read,
differentiated, argued with, and falsified in a way a gradient-boosted ensemble
cannot.

The same property creates three risks that ordinary predictive benchmarking does
not surface.

**Manufactured structure.** A genetic-programming search always returns
something. A raw goodness-of-fit score for a discovered expression is therefore
uninterpretable on its own: it must be compared against what the same search,
with the same budget and the same number of restarts, achieves on data where no
structural relationship exists. This is why an empirically calibrated null
threshold, evaluated at the candidate's own complexity, is treated here as part
of the definition of a discovery rather than as a robustness check.

**Non-identifiability.** Distinct expressions can be numerically
indistinguishable on the available design. Two candidates may differ in
algebraic form, agree to within noise on every observed point, and disagree
about what the underlying relationship is. In that situation a pipeline that
reports one expression as "the" recovered law is overstating what the data
determine.

**Selection, not search, as the failure point.** Given a Pareto front over
complexity and accuracy, the rule that picks one candidate from the front is a
scientific decision, not an implementation detail. This project has direct
evidence that the selection rule, and not the search, can be the binding
failure: see Section 4.2.

## 3.4 Why synthetic truth, and why prospective freezing

Real spectra do not come with a known generating expression. Whatever a symbolic
pipeline returns on real data, there is no external object against which support
recovery, family recovery, or exact-algebra recovery can be scored. Synthetic
worlds solve exactly this problem and no other: the generating law, the variable
support, the mathematical family, and the noise scale are all known by
construction, so recovery is measurable rather than assessable.

The corresponding cost is that synthetic truth families are chosen by the
investigator and may not span real fragmentation mechanisms. This is a
limitation of the evidence class, not a defect of a particular study, and it is
stated as such in Section 11.

Prospective freezing addresses a different failure. In symbolic discovery, the
number of defensible-looking analysis choices is large: the operator grammar,
the complexity budget, the selection tolerance, the acceptance threshold, the
denominators of each endpoint, and the definition of a "successful recovery".
Each of these can be adjusted after seeing performance in a direction that
improves the headline number, and each such adjustment is individually
justifiable. The only durable defence is to fix them before the evaluation data
are opened and to record the fixing in a way a reader can verify. That is the
design principle of the benchmark described in Section 5: case content,
generator, truth, seeds, partitions, denominators and gate thresholds are hashed
and frozen, later changes proceed only by numbered amendment, and each amendment
must declare and evidence its temporal position with respect to sealed material.

## 3.5 What this manuscript claims and does not claim

This is a computational methods study on fully synthetic data. It does not
report a discovered relationship in real spectra, and no expression reported
here is described as a physical, mechanistic, or universal law. The project's
real-data arm is separately governed and remains at claims-ladder rung L3, which
states that descriptor structure is associated with between-compound variation
beyond mass on scaffold-disjoint holdouts, with no causal interpretation
attached; it does not extend to a real-data symbolic candidate (`PHASE3_DECISION.md`, `TYPE2_VALIDATION_DECISION.md`).

The central claim direction, stated in the benchmark protocol before execution,
is: under controlled, prospectively frozen synthetic conditions, the pipeline
recovers meaningful family-level mathematical structure while rejecting
specified null and adversarial worlds
(`MURU_PAPER_BENCHMARK_PROTOCOL.md`). Whether that claim is supported is
`[PROSPECTIVE RESULT TO INSERT]`.

---

# Section 4. Historical development

**Evidence class A throughout.** This section explains why the prospective
benchmark of Section 5 has the shape it has. It is not a results section, and no
number in it is a prospective endpoint. Two frozen verdicts are preserved
without reinterpretation.

## 4.1 The real-data arm, and where it stopped

Phases 1 and 2 audited a single-instrument, energy-resolved corpus and
established the response definition and the representation used downstream. The
Phase 2 verdict was `RESTRICT AND GO TO PHASE 3`, with the highest defensible
real-data claims-ladder rung recorded as **L3**
(`PHASE3_DECISION.md`, Phase 2 gate verification table). A sealed confirmation
set of 110 compounds across 82 scaffold groups was selected by scaffold group
before any model existed and has never been opened; its SHA-256 was recomputed
unchanged before and after each subsequent study
(`PHASE3_DECISION.md`, `TYPE2_VALIDATION_DECISION.md`).

Phase 2 also produced the two restrictions that most shape the synthetic
benchmark. First, the structure-beyond-mass result did not replicate in negative
mode. Second, a mass-coupling audit showed that a mass association in the
response can be manufactured mechanically: under a stipulated common
fragmentation programme with a 50 Da absolute low-mass cutoff, the response
correlated with precursor mass at rho = -0.4791 at the top energy, with no
chemistry anywhere in the construction
(`PHASE3_DECISION.md`; historical dossier HS-00). That is a sensitivity result,
not an identification of the artifactual share of the real association, and no
such share is claimed.

## 4.2 Phase 3: the selector, not the search, was the failure

Phase 3 built the discovery engine, the synthetic ground truth, the
falsification harness, and the null calibration, and ran 240 synthetic-response
worlds at 30 PySR seeds each (7,200 runs), with a 680-run gplearn comparison
subset. Its pre-registration was frozen before any governed symbolic run and its
verdict was computed from that pre-registration's decision rule.

The verdict was **STOP BEFORE PHASE 4**, and it is preserved. The stop condition
that fired was G1 recovery below 80% at the moderate noise regime: selected-form
functional and symbolic recovery was 0% at every noise regime tested
(`PHASE3_DECISION.md`).

The diagnosis is the durable contribution. A dedicated diagnostic separated two
questions that a single recovery rate conflates: whether the search puts a
matching expression anywhere on the 30 seeds' Pareto fronts, and whether the
frozen ranking rule then selects it. In the G1 low and moderate worlds the
search placed an expression matching the planted law on the Pareto front in 100%
of worlds, and the system reported it in 0% and 10% respectively. The mechanism was specific: the planted law needed complexity 13,
while a complexity-6 expression approximated it closely enough to sit within
0.004 held-out R2 of it, and the frozen elbow rule, which takes the smallest
complexity whose validation R2 is within 0.01 absolute of the best on the front,
therefore took the approximation in 30 of 30 seeds at every noise level
(`PHASE3_DECISION.md`).

This is recorded as a **candidate-selection failure**, not a search failure, and
it was not repaired: the pre-registration scoped its repair allowance to the
false-positive gate alone, which did not fire. Changing the selection rule after
observing that recovery had failed is precisely the move Phase 3 existed to
prevent.

Two further Phase 3 facts carry forward. The pure-null false-positive rate was
0 of 100 with a Clopper-Pearson 95% interval of [0.0000, 0.0362]; the project's
convention is that the interval, not the point estimate, is the claim, and
`p = 0` language is not used for a finite simulation count. And the frozen
40-world null threshold table was a point estimate with wide uncertainty: at
complexity 20 the threshold was +0.4889 with a bootstrap interval of
[+0.2603, +0.6859] (`NULL_CALIBRATION.md`, `PHASE3_DECISION.md`).

## 4.3 Type 2: family recovery succeeded where exact algebra did not

The prospective objective-alignment study asked a deliberately different
question: whether the machinery identifies a compact, interpretable,
molecule-conditional empirical **family** (support, scaling and shared shape),
even when the exact algebraic generating form is not identifiable. Its
pre-registration was frozen before any fresh world existed, and its verdict was
computed by code from machine-readable artifacts.

The verdict was **DO NOT AUTHORIZE PHASE 4**, and it is preserved. Exactly one
of thirteen decision conditions failed: independent-engine corroboration, which
required at least 50% agreement on block-level effective support and at least
50% agreement on the mass-block exponent within +/-0.15, and observed 15% and
25% respectively (`TYPE2_VALIDATION_DECISION.md`).

Twelve conditions passed. On the 20 G1B moderate worlds, the study's composite
Type 2 success gate passed 17 of 20 (85%), support was recovered in 20 of 20,
exponent recovery was 18 of 20, shape recovery was 20 of 20, and median seed
selection frequency was 30 of 30. Dense-lattice family recovery, measured rather
than gated, was 16 of 20. Across 100 fresh pure-null worlds, 0 were accepted,
with the same [0.0000, 0.0362] interval.

Refusal blocks produced no accepted structural claims in the tested
constructions, at denominators too small to bound the rate tightly. Reporting
the Clopper-Pearson 95% upper bound rather than the zero count: G2 (no compact
collapse) 0 of 8 accepted (upper 0.3694), G3 (mass-only) 0 of 8 non-mass
structural claims (0.3694), G4M 0 of 30 (0.1157), GC 0 of 9 (0.3363), G5 0 of 8
(0.3694), GRT 0 of 4 (0.6024) (`TYPE2_VALIDATION_DECISION.md`; bounds computed
as `1 - 0.025**(1/n)`, the method that reproduces the repository's recorded
[0.0000, 0.0362] at n = 100). The intervals, not the zero counts, are the
claim.

The separately reported Type 3 diagnostic failed, and this is the finding that
most directly shapes the prospective benchmark's endpoint structure. **Not once
in the entire study was a reported expression symbolically equivalent to the
planted law.** Symbolic equivalence was 0 in G1A, G1B, G1C and G3. The reported
family contained a median of 8.5 distinct functional-equivalence classes on the
G1B moderate worlds, and in 0 of 20 worlds did the system claim the algebraic
form was identified. The sharpest case is G1C, whose generating law lies outside
the frozen grammar by construction: the system recovered support in 8 of 10
worlds and shape family in 10 of 10, and claimed algebraic identification in 0
of 10 (`TYPE2_VALIDATION_DECISION.md`).

**Family recovery and exact algebra recovery are therefore kept as separate
endpoints in the prospective benchmark, and the primary endpoint is the family
one.** Historical evidence shows the two can diverge sharply, and no prospective
success at one is assumed from the other.

Type 2 also enlarged null calibration from 40 to 100 worlds, narrowing the mean
bootstrap interval width across complexities to 0.109 against Phase 3's 0.426 at
complexity 20 alone (`TYPE2_VALIDATION_DECISION.md`).

## 4.4 The scalar null problem

The governed symbolic target is a scalar collapse scale per compound, not the
raw six-energy trajectory. A null construction that preserves a compound's mean
trajectory level therefore preserves much of the scalar target even while
destroying energy order.

The historical calibration cycled four constructions from the master plan, one
of which was `target_permuted_across_energy_within_compound`. In Type 2 that
construction produced a 95th percentile of +0.7228 at complexity 20 against
+0.0835 to +0.1509 for the other three, and set the pooled gate almost
single-handedly; Phase 3 had shown the same asymmetry at 10 worlds per
construction (`TYPE2_VALIDATION_DECISION.md`; failure mode FM-05). Its inclusion
made the historical threshold conservative, which is the safe direction, but it
is not a clean calibration of the intended scalar null.

The prospective benchmark therefore **excludes** within-compound energy
permutation from its null family set (Amendment A3.1), and the RC3.1
implementation makes it unconstructible rather than merely unused.

## 4.5 Engine asymmetry and the competence audit

The frozen comparison arm (gplearn 0.4.3) returned a single best program per
seed at 10 seeds, against PySR's Pareto front at 30 seeds, with different
operators, a different search objective and different protected semantics. A
later prospective audit measured that arm's own competence against fresh planted
truth rather than against PySR: its C0, C1 and C2 competence gates all failed
(mean elementary scaling 57.5% against an 80% requirement; non-mass carrier
scaling 25% against 50%; mean E5/E6 support 15% and exponent 45% against 50%),
and on the fresh G1B-style analogue it achieved 30% block support and 45%
mass-exponent recovery where matched PySR achieved 100% on both legs
(historical dossier HS-04; failure modes FM-03, FM-04).

Three facts must be stated together and never merged. The historical
corroboration gate failed. The Type 2 verdict `DO NOT AUTHORIZE PHASE 4` stands
because of that failure. And the later audit removes the *inference* that
non-agreement demonstrated PySR's candidates were engine-specific artifacts,
without turning either historical result into a pass.

## 4.6 Technical defects found after the historical studies

Two defects were established in the historical implementation and are recorded
as such. Neither has been used to recalculate any historical result.

**Transductive target construction (FM-06).** The historical collapse fit
estimated the shared curve, scale centring, residual variance and weights across
all compounds before the grouped split. In a synthetic 40-compound perturbation
check, changing one trajectory changed other compounds' estimated scales by up
to 0.0987, weights by up to 1.2818, profile knots by 0.0908, and residual SD
from 0.00963 to 0.01050. Historical scaffold and cluster metrics are therefore
not fold-local held-out target validation and must not be described as such.

**Complex-valued evaluator (FM-07).** The historical grammar evaluator cast
complex candidate outputs to float, silently discarding the imaginary part, and
thereby accepted expressions such as `sqrt(-1.5)*a`. Its historical reach was
never quantified; no historical artifact records how often complex-valued
candidates occurred, or whether the defect changed a decision.

Two instrumentation gaps accompany them. Boundary-scale hits were not recorded:
the historical estimator returned a grid endpoint when the optimum lay outside
its search interval and did not flag this, so historical boundary prevalence is
unknown (FM-08). And missing-energy robustness was never established: historical
worlds used 0.97% dropout and retained at least five energies, with no
per-trajectory coverage guard, coverage report, or missingness stress study
(FM-09).

These four items are precisely why the prospective benchmark contains
fold-local target estimation, strict symbolic evaluation, an explicit
boundary-hit endpoint (F05), and a declared missing-energy family (F04). Section
11 separates which of them the current system closes from which remain live
limitations.

## 4.7 Mass and descriptor confounding, and noise

Mass and descriptor confounding is established as a risk and is not eliminated
(FM-11). Beyond the Phase 2 coupling sensitivity above, the Type 2 F8 labelling
rung certified "structure beyond mass" in only 1 of 19 accepted G1B moderate
worlds despite support being recovered in 20 of 20; on a fully synthetic
covariate frame with independent descriptors the same rung fired 3 of 6. That
contrast is consistent with mass-block dominance on the real frame. The share of
fit attributable to the mass block was not quantified:
`[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
(`TYPE2_VALIDATION_DECISION.md`).

Noise sensitivity is established (FM-10). Type 2 G1B success was 100% at
residual SD 0.010, 85% at 0.0295, and 30% at 0.060. The 0.0295 figure is the
Phase 1 conservative inter-mixture variability estimate, which the project
records as an **upper bound on technical repeatability, not an instrument noise
floor**; negative-mode repeatability is UNKNOWN (`README.md`).

## 4.8 What historical work is and is not eligible for

No historical record may serve as the prospective primary endpoint. No
historical synthetic result raises the real-data claims ladder above L3 or
authorizes Phase 4. Historical material enters this manuscript as background and
method development, as explicitly labelled supporting synthetic evidence, or as
a reportable limitation, and never otherwise
(`MURU_HISTORICAL_CLAIM_MATRIX.md`).

---

# Section 5. Methods

**Evidence class B throughout.** Every value stated here is traceable to a
frozen artifact; see `MURU_EVIDENCE_LEDGER.json`. Where the frozen record does
not determine a detail, the token `[METHOD DETAIL REQUIRES VERIFIED SOURCE]`
appears rather than an invented setting.

## 5.1 Study overview

This is a prospective computational validation study on fully synthetic data.
Its object of evaluation is the discovery pipeline, not a chemical system. The
benchmark contains 380 cases in three partitions: 80 Development, 240 Held-out,
60 Challenge. Challenge cases do not enter primary denominators
(`MURU_PAPER_BENCHMARK_PROTOCOL.md`).

The execution sequence is fixed: content freeze, engineering release candidate,
structural-null calibration, threshold freeze, Development evaluation,
executable freeze, one-shot Held-out evaluation, and Challenge evaluation.
Held-out execution is refused by a guard until the evaluated implementation
commit, strict evaluator, grammar, engine settings, runtime budget, hashes,
preflight and clean-tree check are all locked and verified. At the time of this
draft that status is `WAITING_FOR_LOCKED_IMPLEMENTATION`
(`artifacts/paper_benchmark_content_freeze.json`), and the protocol's
implementation lock is `PENDING_LOCK`
(`MURU_PAPER_BENCHMARK_PROTOCOL.md`, `MURU_PAPER_BENCHMARK_FREEZE.md`).

The benchmark does not validate a real biological or instrumental system. Phase
3 remains `STOP BEFORE PHASE 4`, Type 2 remains `DO NOT AUTHORIZE PHASE 4`, the
real-data confirmation set stays sealed, and no real-data symbolic discovery is
permitted (`MURU_PAPER_BENCHMARK_PROTOCOL.md`).

## 5.2 MURU conceptual model

The modelled object is a scalar fragmentation functional `mu_i(E)` for compound
`i` at collision energy `E`. The scalar collapse model M0 asserts a shared
profile and one compound-specific horizontal scale:

```
mu_i(E) = A_HI + (A_LO - A_HI) * S(E / g_i)
```

where `Phi` is a training-only profile function, `A_LO` and `A_HI` are its
low-argument plateau and high-argument asymptote under its frozen extrapolation
rule, and `S(t) = (Phi(t) - A_HI) / (A_LO - A_HI)` clipped to [0, 1] is the
normalised shape, monotonically non-increasing with `S(0) = 1` and
`S(inf) = 0` (`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` A1.2).

Three alternatives each add exactly one compound-specific deviation degree of
freedom beyond M0's `g_i`, and each reduces to M0 exactly at a stated value:

| Model | Deviation | Prediction | Reduces to M0 when |
|---|---|---|---|
| M1 | horizontal shape | `A_HI + (A_LO - A_HI) * S(E_REF * (E / (E_REF * g_i))**s_i)` | `s_i = 1` |
| M2 | high-energy vertical / asymptotic | `a_i + (A_LO - a_i) * S(E / g_i)` | `a_i = A_HI` |
| M3 | low-energy vertical | `A_HI + (b_i - A_HI) * S(E / g_i)` | `b_i = A_LO` |

`E_REF = 45.0` is the frozen generator horizontal normalisation energy. If
`A_LO - A_HI` falls below the frozen minimum vertical amplitude the case is a
`CONTRACT_FAILURE`: the profile carries no usable vertical span and no adequacy
contrast is defined
(`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` A1.2).

The symbolic discovery target is `g` as a function of molecular descriptors, not
the trajectory itself.

## 5.3 Synthetic benchmark architecture

Every case is generated by a single frozen module,
`src/muru/paper_benchmark/generator.py`, at
`GENERATOR_VERSION = "paper-benchmark-generator-1.1.0"`, which depends only on
the benchmark registry and standard numerical libraries and is deliberately
independent of all historical and real-data code. The registry
(`src/muru/paper_benchmark/registry.py`) is metadata-only and is the sole
authority for the case population; it cannot load inputs, truth values,
outcomes, or real-world records. `ROOT_SEED = 20260813`.

Each case has 180 synthetic compounds in 30 scaffold groups of 6, on the energy
grid `(15, 30, 45, 60, 75, 90)`.

Twenty case families F01 to F20 are frozen. They cover scalar truth under
noiseless, moderate-noise, stronger-noise, missing-energy and boundary-scale
conditions; no-scalar, mass-only, simple, nonlinear, interaction, distractor and
equivalent-form conditions; M1/M2/M3 and combined violations; difficult algebra;
target-specific nulls; and adversaries
(`MURU_PAPER_BENCHMARK_CASE_FAMILIES.md`). The per-family scientific question,
truth kind and endpoint applicability are given in Table 1.

F19 and F20 each cycle three variants across replicates: F19A descriptor-link
permutation, F19B mass-preserving target null, F19C response-cell resampling;
F20A latent driver, F20B measurement coupling, F20C out-of-grammar trap.

Adequacy-violation amplitudes are frozen: standalone M1 0.45 (F13), M2 0.18
(F14), M3 0.22 (F15) with ceiling clip window (0.6, 0.99). The combined family
F16 uses attenuated components: M1 0.15 (attenuation 1/3), M2 0.05 (attenuation
5/18), and, following Amendment A2, M3 = 11/180, the smaller of F16's two
pre-existing attenuation ratios applied to F15's standalone amplitude, bound as
the binary64 nearest the exact rational
(`src/muru/paper_benchmark/generator.py`).

## 5.4 Benchmark partitions

Case counts per family are 4 Development, 12 Held-out, 3 Challenge, giving
80/240/60 across 20 families
(`registry.PARTITION_CASE_COUNTS`;
`artifacts/paper_benchmark_partition_manifest.json`;
`artifacts/paper_benchmark_case_manifest.json`, 380 cases).

Within a case, the 30 scaffold groups are split 20 train / 5 validation / 5 test,
i.e. 120 / 30 / 30 compounds, with scaffold identity atomic
(`generator._synthetic_compounds`). Adequacy contrasts are scored on the case's
30 test compounds
(`MURU_PAPER_BENCHMARK_METRICS.md`).

Held-out and Confirmation partitions are sealed. Development had already been
executed once before Amendment A3.1, at a time when G2 and G3 were not
producible; those Development G2/G3 scores do not exist and were never used to
choose any A3.1 rule (`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`, temporal
position).

## 5.5 Molecular descriptor representation

Each synthetic compound carries five covariates, which are also the frozen
grammar primitives, in this order: `mass`, `descriptor`, `descriptor2`,
`distractor`, `correlated_distractor`
(`g2_contract.GRAMMAR_PRIMITIVES`).

Their frozen correlation structure is generated from a per-scaffold latent:
`group_latent ~ N(0,1)` per scaffold; `latent = group_latent[scaffold] +
N(0, 0.35)` per compound; `mass = exp(5.55 + 0.25*latent + N(0, 0.18))`;
`descriptor` is a min-shifted, max-normalised `latent + N(0, 0.45)`;
`descriptor2` is a min-max normalised `0.65*latent + N(0, 0.65)`;
`distractor ~ N(0,1)` independent; and
`correlated_distractor = 0.85*descriptor + 0.15*N(0,1)`
(`generator._synthetic_compounds`).

This construction is what makes F11 (irrelevant distractors) and F12 (correlated
distractors) meaningful: `distractor` is independent of the target by
construction, while `correlated_distractor` is a near-proxy for `descriptor`.
The G2 support contract explicitly declares that the F12 proxy is **not**
interchangeable with `descriptor`
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`).

## 5.6 Synthetic trajectory generation

The shared M0 branch is `mu = mu_inf + (1 - mu_inf) * exp(-u**phi_p)` in the
normalised coordinate `u = (E / E_REF) / g` with `E_REF = 45`. The simultaneous
M1/M2/M3 response used by the combined family is

```
mu_i(E) = a_i + (b_i - a_i) * S(E_REF * (E / (E_REF * g_i)) ** s_i)
```

with `S(t) = exp(-(t ** phi_p))` the frozen M0 profile shape, `s_i` the M1
horizontal-shape deviation, `a_i` the M2 high-energy floor and `b_i` the M3
low-energy ceiling (`generator.combined_response`).

Per-case randomness is derived deterministically, never drawn from global state:
`derive_seed(*parts) = int.from_bytes(sha256("paper-benchmark-v1|" +
"|".join(parts)).digest()[:8], "big")`, and every generation stage requests its
own `(case_id, stage)` seed (`generator.derive_seed`, `generator._rng`).

Every case's inputs and truth are canonicalised and hashed into a
`content_hash`; the 380 hashes are recorded in
`artifacts/paper_benchmark_case_manifest.json`. Because `GENERATOR_VERSION` is
part of the hashed payload, the A2.1 version bump mechanically changed all 380
hashes although only 19 cases' scientific payload changed; the distinction
between version-metadata-only and scientific-payload change is proved in
`MURU_PAPER_BENCHMARK_AMENDMENT_A2_1_GENERATOR_VERSION.md`.

Per-family noise levels, missing-energy dropout rates and boundary-scale
parameters: `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` (present in the frozen
generator and truth payloads; to be extracted and tabulated for Table 1 before
submission, from `generator.py` and
`artifacts/paper_benchmark_truth_manifest.json`, without opening any outcome).

## 5.7 Fold-local target estimation

The frozen execution boundary requires that all shared objects be fitted from
training trajectories only, then frozen, after which each validation or test
compound is estimated independently against those frozen objects
(`MURU_PAPER_BENCHMARK_PROTOCOL.md`, execution boundary;
`MURU_PAPER_BENCHMARK_AMENDMENT_A1_ADEQUACY.md` A1.2).

This is a direct response to historical failure mode FM-06: the historical
estimator fitted the shared curve, scale centring, residual variance and weights
across all compounds before the grouped split, making historical held-out
quantities transductive. The prospective boundary forbids that ordering.

At the A1 adequacy stage the search is frozen: `log_g` is estimated on a natural
log scale over the interval [-2.0, +2.0] at `COARSE_LOG_G_POINTS = 81` grid
points, under `FIT_OBJECTIVE = "unweighted_sum_of_squared_mu_residuals"`, with
`LOG_SHAPE_BOUNDS = (-log 2, +log 2)` for the M1 shape exponent and
`MIN_VERTICAL_AMPLITUDE = 0.05`; M2's floor and M3's ceiling are solved in
closed form (`src/muru/paper_benchmark/adequacy.py`).

The optimiser and convergence rule used by the RC3.1 **production** path for
per-compound `g_i` estimation, as distinct from this adequacy-stage grid:
`[METHOD DETAIL REQUIRES VERIFIED SOURCE]`.

## 5.8 Scalar adequacy and falsification

**The adequacy ladder (Amendment A1).** M0 is compared with M1 (horizontal
shape), M2 (high-energy vertical) and M3 (low-energy vertical) on the case's 30
test compounds, by within-compound leave-one-energy-out mean absolute error.

A detector **fires** only when both conditions hold: at least 24 of the 30 test
compounds are evaluable for that contrast, and at least 20 of them are practical
wins. A practical win requires the alternative's within-compound
leave-one-energy-out MAE to be no more than 0.90 of M0's
(`MURU_PAPER_BENCHMARK_METRICS.md`, adequacy endpoint scoring).

M0 is rejected when any alternative fires. M0 may be recorded as
`M0_NOT_REJECTED` only when all three contrasts are evaluable and none fires.
Detector identity is preserved: a wrong alternative firing may reject M0 but
never satisfies another detector's sensitivity endpoint, and for F16 each
detector endpoint is scored independently.

Insufficient data, boundary limitation, numerical failure, model fit failure and
timeout produce indeterminate adequacy states and are **never** M0 acceptance.

**The reduced falsification harness.** Structural acceptance requires the
following rungs to pass: F1 reproducibility, F4 compound holdout, F5 scaffold
holdout, F7 influence-drop component only, F9 energy-subset stability, F10
negative control. F8 is structural labelling and is explicitly **not** an
acceptance gate. `NOT_APPLICABLE` is never counted as `PASS`
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`).

## 5.9 Symbolic regression engine

PySR 1.5.10, backed by SymbolicRegression.jl, run deterministically and
serially. Frozen search settings: `niterations = 40`, `populations = 15`,
`population_size = 33`, `parsimony = 0.0032`,
`adaptive_parsimony_scaling = 20.0`, maximum complexity 20, 30 seeds per world
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`, search settings).

Environment versions verified operationally in a separate readiness audit:
PySR 1.5.10, Julia 1.12.6, SymbolicRegression.jl 1.11.3, PythonCall.jl 0.9.26,
gplearn 0.4.3, SymPy 1.14.0, numpy 2.5.2, scipy 1.18.0, pandas 3.0.5,
scikit-learn 1.9.0, RDKit 2026.03.5, pyarrow 25.0.1, on Python 3.13.12
(`MURU_PAPER_EXECUTION_ENVIRONMENT.md` at `c443a7f`). The master plan's stated
Python target was 3.12; the deviation to 3.13.12 is recorded there, with the
finding that nothing in the lockfiles or the PySR/Julia stack caps the version
below 3.13.

The gplearn comparison arm is **not** part of the prospective acceptance
predicate. Its historical role and the audit that removed its veto inference are
Section 4.5 material only.

## 5.10 Candidate grammar

Binary operators: `+`, `-`, `*`, `/`. Unary operators: `sqrt`, `log`, `square`,
`cube`, `inv`. `exp` is excluded and trigonometric operators are excluded
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`).

Primitive variables are the five covariates of Section 5.5, in frozen order.

The frozen truth-family taxonomy against which discovered expressions are
classified is: `mass_affine_descriptor`, `mass_power`,
`mass_saturating_descriptor`, `mass_interaction`, `mass_exponential_descriptor`
(`g2_contract.TRUTH_FAMILIES`). Note that F20C is an out-of-grammar trap by
construction: its generating relationship cannot be represented exactly under
this grammar, and accepting a structural claim there is an unsafe event.

## 5.11 Complexity control

Maximum complexity is 20. Parsimony pressure is `0.0032` with adaptive parsimony
scaling `20.0`. Complexity enters acceptance twice: as a hard cap
(`complexity <= 20`) and as the index at which the null threshold is read, since
the acceptance comparison is `valid_r2 > null_threshold[min(complexity, 20)]`
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`).

Reading the threshold at the candidate's own complexity is what prevents a
high-complexity interpolant from being compared against a low-complexity null.

## 5.12 Strict symbolic evaluation

Effective support is extracted deterministically from symbolic expressions
rather than read off the expression string. The contract
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`) is:

- parse under the protected grammar;
- deterministic algebraic normalisation via SymPy `simplify`;
- cancelled variables do not count;
- exact-zero terms do not count;
- constants contribute no support;
- duplicated primitive variables count once;
- nested transforms preserve primitive dependence;
- interactions contribute every primitive input;
- correlated proxy variables remain distinct, and the F12 proxy
  `correlated_distractor` is not interchangeable with `descriptor`;
- no new magnitude threshold is invented.

Expressions that cannot be resolved produce `SUPPORT_UNRESOLVED`.

Discovered-side family classification is structural and coefficient-agnostic;
algebraic reorderings classify identically; a degenerate exact intersection of
families yields `FAMILY_AMBIGUOUS`.

Strict evaluation replaces the historical evaluator that cast complex outputs to
float (FM-07). The reference contract lives in
`src/muru/paper_benchmark/g2_contract.py`; the production path is Engineering
RC3/RC3.1.

## 5.13 Null calibration

The acceptance threshold is empirical, not assumed. One hundred structural-null
calibration worlds are generated, each with 180 compounds in 30 scaffold groups,
the same five synthetic covariates and the same frozen correlation structure as
a benchmark case.

Allocation across the three admitted constructions is frozen at 34 / 33 / 33:

| Construction | Worlds |
|---|---:|
| `target_permuted_across_compounds` | 34 |
| `descriptors_permuted_across_compounds` | 33 |
| `gaussian_targets_with_observed_variance` | 33 |

`within_compound_energy_permutation` is **excluded**, because it preserves each
compound's mean level and therefore much of the scalar target being estimated
(Section 4.4). RC3.1 makes it unconstructible: it is not a branch, and requesting
it raises (`src/muru/paper_benchmark/rc3_calibration_worlds.py`).

**World identity and seeds.** World ID is
`PB|NCAL|{construction_name}|r{index:03d}` for index 0 to 99. Search seeds are

```
PB_SEED_BASE   = 2_110_000_000
PB_SEED_SPREAD = 370_000
h    = int.from_bytes(sha256(world_id.encode("utf-8")).digest()[:4], "big", signed=False)
base = PB_SEED_BASE + (h % PB_SEED_SPREAD) * 100
seeds = [base + k for k in range(30)]
```

Verified invariants: 100 unique world IDs, 100 unique base buckets, 3,000 unique
seeds, all signed-32-bit safe so the Julia backend can consume them
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`).

**The null statistic.** `S(w, c)` is the maximum over the world's 30 seeds of
the best validation R2 attainable at complexity at most `c`. Taking the maximum
over seeds is what prices in search multiplicity: the protocol runs the search 30
times and keeps the best, so the null is allowed the same. Per-seed curves are
prefix-monotone by cumulative maximum, and a contract canary asserts that once
finite at `c` a curve cannot become non-finite at larger `c`.

**Per-seed failure semantics.** Three explicit statuses:
`COMPLETED_WITH_CANDIDATES`; `COMPLETED_NO_CANDIDATE`, which contributes
negative infinity; and `EXECUTION_FAILURE` for crash, timeout, out-of-memory or
malformed output. `np.isfinite` alone does not determine status. If **any** seed
in a world has `EXECUTION_FAILURE`, that world's entire `S(w, 1..20)` becomes
`+1.0`. This is conservative: it cannot lower the threshold, and it may cost
power.

**Calibration validity.** At least 95 of 100 worlds must have zero
execution-failure seeds. More than five failed worlds yields
`CALIBRATION_INVALID` and no threshold table is activated. Selective retries and
replacement worlds are forbidden.

**Threshold table.** `numpy.quantile(..., 0.95, method="linear")`; for N = 100
this is `x[94] + 0.05 * (x[95] - x[94])`. The result is then passed through
`np.maximum.accumulate` so thresholds are non-decreasing in complexity: a larger
hypothesis space cannot be allowed to make chance fitting harder. A world-level
bootstrap with 2,000 resamples at seed 20260812 is computed for **uncertainty
reporting only** and enters no gate.

## 5.14 A3.2 null target correction

Amendment A3.2 corrects two defects in the calibration design, prospectively and
before any calibration world was executed.

**Defect 1: the base target was scaffold-structured.** A3.1 fixed world
geometry, covariates and the three null constructions but did not pin the
pre-permutation target, and Engineering RC3 provisionally used the frozen law's
target vector directly. That vector depends on `mass` and `descriptor`, both
driven by the per-scaffold latent, so under
`descriptors_permuted_across_compounds`, which permutes only the covariates, the
target retains its scaffold structure. Against a scaffold-disjoint split this
produces a systematic train/validation mean shift. Measured mean validation R2
of the train-mean constant model, 20 worlds per construction: -0.055 for
`target_permuted_across_compounds`, -0.077 for
`gaussian_targets_with_observed_variance`, and **-0.246** (minimum -1.28) for
`descriptors_permuted_across_compounds`. One of three nominal null families was
therefore systematically non-null, which would be expected to drag the pooled
95th percentile below what a homogeneous null would give and so to make the
resulting threshold more permissive than intended, the one direction of error
this benchmark may not take. The direction and size of that effect on the
threshold table were never measured, because no threshold table existed at
either the provisional or the corrected design; the defect was identified and
corrected on structural grounds.

**The corrected base target.** Generate the frozen-law target vector exactly as
the unchanged frozen law defines it; preserve its values and therefore its exact
marginal distribution; and, before applying any of the three null-family
transformations and before any partition use, randomly reassign those values
across all 180 compound identities under one dedicated deterministic
world-specific seed. The reassignment is a true permutation: no value added, none
removed, no numerical alteration, no re-estimation, and no conditioning on
descriptors, scaffold, mass, split or symbolic-search results. Its seed is
derived through the canonical `generator.derive_seed` from the namespace
`PB|NCAL|<world_id>|BASE_TARGET`, independent of the null-family, split, search,
bootstrap and smoke seeds. The frozen 34/33/33 allocation then applies unchanged.

Residual finite-sample correlation arising by chance after a valid random
permutation is **permitted and expected, and must not be tuned away**. One
deterministic permutation per world means one permutation per world: no
reshuffling until a correlation looks small, no rejection sampling, no selection
among candidate permutations.

**Defect 2: the calibration scaffold split.** A3.1 specifies a
scaffold-disjoint 60/20/20 split; the inherited generator produces 20/5/5
scaffold groups, i.e. 66.7/16.7/16.7. A3.2 holds the written 60/20/20
specification authoritative rather than amending the contract to match the code.
For the 30-scaffold, 180-compound calibration worlds this gives:

| Partition | Scaffolds | Compounds |
|---|---:|---:|
| train | 18 | 108 |
| validation | 6 | 36 |
| test | 6 | 36 |

Scaffold identity is atomic. Assignment is deterministic from the namespace
`PB|NCAL|<world_id>|SPLIT` and depends on nothing but scaffold identity: not
target values, descriptor values, mass, symbolic-search output, or null-family
outcome. The A3.1 protected generator remains byte-identical and is not edited;
the corrected split is implemented in a new calibration-specific partition
helper. **This split applies to calibration worlds only** and changes no
benchmark case partition. Development, Held-out, Confirmation and historical
partition logic are untouched (`MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md`).

**Temporal legitimacy.** At the time of A3.2 the 100 calibration worlds had not
been executed, no threshold table existed, Development G2/G3 had not been
scored, and Held-out and Confirmation were sealed and unopened. The defect was
found by read-only review of the RC3 implementation, from the construction of
the null itself, and not by looking at a result, because no result existed to
look at (`MURU_PAPER_BENCHMARK_AMENDMENT_A3_2.md`;
`artifacts/paper_benchmark_amendment_a3_2.json`, `governance_form`).

## 5.15 Amendments A3.3 and A3.4: Secondary endpoint contracts and domain repair

Amendment A3.3 (`71f5369`, tag `benchmark-content-freeze-a3-3`) bound prospective
scientific evaluation contracts for two secondary symbolic endpoints:
**Parameter Recovery** (156 held-out cases) and **Predictive Equivalence** (144
held-out cases).

A subsequent hostile mathematical and domain-conformance audit (`78cc7c2`,
`audit/MURU_A3_3_MATHEMATICAL_REVIEW.md`) verified that the parameter recovery
derivative operators and tolerances were mathematically sound, but identified
two defects in the A3.3 specification:
1. **Predictive domain mismatch:** A3.3 proposed evaluating predictive equivalence
   over an independent Cartesian Sobol hypercube $[-2.5, 2.5]^4 \times [100, 800]$ ($N=2048$).
   For Family F09 (`mass_saturating_descriptor`), setting descriptor $d \in [-2.5, 2.5]$
   encountered a division-by-zero pole/singularity at $d = -1.0$ and generated negative
   truth values, which never existed in the data generator ($d \in [0, 1]$). Furthermore,
   the independent box destroyed the authentic $r \approx 0.98$ joint covariance between
   `descriptor` and `correlated_distractor` and sampled 96% of points outside the generator's
   physical descriptor support.
2. **Terminology imprecision:** Describing descriptor coupling recovery as
   "coordinate-free" was inaccurate; while scale-invariant to $g$ and invariant to candidate
   factoring, $c_{\text{desc}}$ has dimension $[\text{descriptor}]^{-1}$ and depends on the
   coordinate scale of the descriptor.

Amendment A3.4 (`be23b80`, tag `benchmark-content-freeze-a3-4`) prospectively resolved
both issues before any Development rerun, before structural-null calibration execution
was completed or inspected, and while Held-out and Confirmation remained strictly sealed:
- **Reference distribution repair:** Withdrew the Cartesian hypercube entirely. Replaced it
  with 12 complete, case-shaped reference covariate frames generated by the unchanged frozen
  synthetic generator ($12 \times 180 = 2,160$ evaluation rows), preserving exact marginal
  distributions, finite-frame normalizations, scaffold structures, and joint covariance.
- **Reference frame IDs and canonical digest:** Bound 12 logical reference frame IDs
  (`PB|PRED_EQUIV|FRAME|000` to `011`) with deterministic seeds derived from
  `derive_seed(id, "compounds")` and bound the aggregate canonical SHA-256 digest:
  $$\mathbf{4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44}$$
- **Invariant parameter terminology:** Formally defined parameter recovery as "scale-invariant
  and algebraically invariant within the frozen benchmark coordinate system".
- **Metric formalization:** Formally codified the valid evaluation point set $\mathcal{V}$,
  least-squares positive multiplicative scale alignment $c^*$, scale-adjusted relative RMSE
  ($\text{REL\_RMSE} \le 0.05$), Pearson correlation ($r \ge 0.990$), and an explicit zero-variance
  correlation failure rule ($r = 0.0 \to \text{FAIL}$).
- **Decomposition reporting:** Mandated separate reporting for Joint Parameter Recovery (/156),
  Mass Exponent Recovery (/156), and Descriptor Coupling Recovery (/84).
- **Immutability of primary gates:** Left G1 (164), G2 (144), G3 (36), null calibration
  protocols, and all primary decision rules completely unchanged.

## 5.16 Temporal provenance adjudication and execution chronology

A subsequent pre-engineering integrity audit (`f1fb943`, `audit/MURU_A3_4_PRE_ENGINEERING_INTEGRITY.md`)
audited repository-wide execution logs and filesystem timestamps without inspecting any
calibration or sealed outcomes. It confirmed exact zero seed collisions across all 4,632 logical
identities, verified all 31 protected paths against aggregate digest
`d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8`, and identified a minor
temporal-provenance statement defect: while calibration had not been run on the science branch,
calibration execution had been initiated at 10:08 EDT in a parallel engineering worktree.

The additive Temporal Provenance Erratum (`220c9cb`, tag `a3-4-temporal-provenance-erratum`,
`audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md`) adjudicated the exact chronology in EDT (UTC-04:00):

| Event | Timestamp (EDT) | Immutable reference |
|---|---|---|
| Preflight created | 2026-08-13T23:59:01-04:00 | Read-only preflight provenance timestamp |
| Calibration directory and manifest setup | 2026-08-14T10:08:17-04:00 | Read-only directory/manifest provenance timestamp |
| Runner sidecar `started_utc` | 2026-08-14T10:08:17.932248-04:00 | Source field name retained; recorded offset is EDT |
| First `backend.search` start | Strictly after 10:08:17.932248 and strictly before 10:08:31 | Inferred open interval, not an exact timestamp |
| First non-quarantined `PB__NCAL__` durable record | 2026-08-14T10:08:31-04:00 | Frozen execution definition |
| A3.4 creation commit | 2026-08-14T11:56:17-04:00 | `d0ea5d4b0309e4e95dcab4035b9be66e166765b1` |
| A3.4 freeze commit | 2026-08-14T11:56:23-04:00 | `be23b80d63fbd30227f0ab8f200dddc2121f3bfe` |
| Annotated A3.4 freeze tag | 2026-08-14T11:56:26-04:00 | `benchmark-content-freeze-a3-4` tag object `326727d5...` |
| Runner finished | 2026-08-14T11:58:40.935600-04:00 | Read-only runner provenance timestamp |
| Terminal summary files | 2026-08-14T11:58:41-04:00 | Read-only terminal-summary provenance timestamp |
| A3.4 lineage merged with `--no-ff` | 2026-08-14T12:27:08-04:00 | `5055f69097aa0c6ce2ded6a3e57f0edfaea69faf` |

**Outcome-Blindness Guarantee:** No calibration, held-out, development, or confirmation outcome
was opened, read, compared, or used to create A3.3, A3.4, or the provenance erratum. All mathematical
definitions and reference covariate frames were derived strictly from prospective principles and
the unchanged frozen synthetic generator.

## 5.17 Scaffold partitioning

Two distinct partitioning regimes exist and must not be confused.

| Context | Scaffold groups | Compounds | Source |
|---|---|---|---|
| Benchmark case (all 380) | 20 / 5 / 5 | 120 / 30 / 30 | `generator._synthetic_compounds`, frozen V1 |
| Calibration world (100) | 18 / 6 / 6 | 108 / 36 / 36 | A3.2 `assign_calibration_split` |

In both, scaffold identity is atomic: a scaffold group appears in exactly one
partition. Benchmark-case splits derive from the frozen generator's own `split`
column; calibration worlds ignore that column and use the A3.2 helper.

## 5.18 Calibration threshold construction

The threshold table is the vector `T(c)`, `c = 1..20`, defined as the 95th
percentile across valid calibration worlds of `S(w, c)`, computed with
`numpy.quantile(..., 0.95, method="linear")` and made non-decreasing by
`np.maximum.accumulate`. It becomes operational only if calibration is valid
(Section 5.13). A candidate at complexity `k` must satisfy
`valid_r2 > T(min(k, 20))`.

The bootstrap interval (2,000 world-level resamples, seed 20260812) is reported
alongside every threshold and is **not** a gate. Its role is to let a reader see
whether a candidate's margin over the threshold is comfortable or lies inside
the calibration's own uncertainty; historical precedent for that concern is the
Phase 3 complexity-20 interval of [+0.2603, +0.6859].

Calibration outcome: `[PROSPECTIVE RESULT TO INSERT]`.

## 5.19 Development evaluation

Development is an 80-case sanity partition. Development scientific performance
cannot alter the case architecture, generator, coefficients, endpoints, grammar
or thresholds (`MURU_PAPER_BENCHMARK_PROTOCOL.md`).

The Development-only preflight may measure runtime, CPU time, peak memory,
engine failures, candidate counts and artifact size; it cannot load or score a
held-out record. A locked-engine preflight must establish runtime feasibility
before final executable freeze.

Development had been executed once before Amendment A3.1, at which time G2 and
G3 were not producible. Under the A3.1/A3.2 contract a Development rerun is
required before the executable freeze. Development outcome:
`[PROSPECTIVE RESULT TO INSERT]`.

## 5.20 Held-out evaluation

Held-out contains 240 cases and is sealed. It is opened once, after calibration
validity, threshold freeze, Development rerun and executable freeze, and is
scored against the frozen denominators of Table 2. Held-out outcome:
`[PROSPECTIVE RESULT TO INSERT]`.

## 5.21 Confirmation and Challenge evaluation

Sixty Challenge cases exist and do not enter primary denominators
(`MURU_PAPER_BENCHMARK_PROTOCOL.md`). They are scored descriptively, as stress
and boundary conditions, after Held-out.

The separately governed real-data Confirmation set (110 compounds, 82 scaffold
groups) remains sealed with SHA-256
`d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07`, verified
unchanged before and after each prior study
(`PHASE3_DECISION.md`, `TYPE2_VALIDATION_DECISION.md`). It is not opened by this
manuscript's work and no real-data symbolic discovery is authorised.

Challenge and Confirmation outcomes: `[PROSPECTIVE RESULT TO INSERT]`.

## 5.22 Primary and secondary endpoints

The benchmark evaluates three primary gates and a structured ladder of secondary
and diagnostic endpoints (`MURU_PAPER_BENCHMARK_METRICS.md`,
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`, `MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`).

### 5.22.1 Primary Gates (G1, G2, G3)

**G1, scalar competence, denominator 164.** For a scalar-applicable case,
success requires all three of: Spearman correlation between true and fold-local
estimated log-`g` of at least 0.80; held-out trajectory MAE no greater than 0.80
of the per-energy-mean baseline; and no M0 rejection under the A1 rule, where
the adequacy component is satisfied only by an `M0_NOT_REJECTED` status and
never by an indeterminate or failure state. G1 passes when the lower 95% Wilson
bound over 164 cases is at least 0.70.

**G2, family recovery, denominator 144.** Case success requires both
`support_status == MATCH` and `family_status == MATCH` under the five-member
frozen truth taxonomy. G2 passes when the lower 95% Wilson bound over 144 cases
is at least 0.70.

**G3, principal structural safety, denominator 36.** Thirty-six equally weighted
opportunities from F07 (12), F19 (12) and F20 (12). An unsafe structural
acceptance counts 1; a safe evaluable non-acceptance counts 0; an `UNEVALUABLE`
outcome is a **G3 violation** and remains in the denominator. G3 passes when the
upper 95% Wilson bound is at most 0.15. The three component numerators,
denominators, rates and intervals are reported beside the aggregate.

A note on a source-document slip, recorded so it is not resolved in the wrong
direction. The A3.1 G3 section's parenthetical reads "36 Held-out G3
opportunities (F19 + F20, 3 variants each, 12 held-out per family)", and F19 plus
F20 alone is 24. The denominator 36 is correct: it is the three-component
decomposition F07 12 + F19 12 + F20 12 stated in
`MURU_PAPER_BENCHMARK_METRICS.md`, and it is independently reproduced by
enumerating `principal_structural_safety` over the case manifest. The
parenthetical omits F07; the denominator does not change.

The positive umbrella claim is made only when preconditions hold and G1, G2 and
G3 all pass. An adequacy failure that invalidates `g` therefore fails G1. Any
failed gate blocks the positive claim while descriptive endpoint reports are
retained.

### 5.22.2 Parameter Recovery (Secondary Endpoint, Denominator 156)

Parameter recovery evaluates whether the discovered candidate expression $\hat{g}$
recovers the identifiable physical parameters of the generating law within declared
numerical tolerances, under the frozen benchmark coordinate system (Amendment A3.4).

- **Scientific Role:** SECONDARY descriptive endpoint (never part of G1, G2, or G3).
- **Applicable Families:** F01–F05, F07–F12, F17, F18 (13 families $\times$ 12 held-out cases = **156 cases**).
- **Denominator Discipline:** Strictly fixed at **156**. Unresolved, non-finite, missing, or unparseable candidate expressions count as non-successes and never reduce the denominator.
- **Invariance Properties:** In the M0 collapse model ($\mu(E) \approx \Phi(E/g)$), the overall multiplicative scale of $g$ is non-identifiable. The derivative operators normalize by $\hat{g}(\mathbf{x}_0)$, ensuring that the extracted parameters are **scale-invariant** (invariant to any global positive multiplier $A > 0$) and **algebraically invariant** (invariant to factoring, expansion, or mass reference shifts) within the frozen coordinate system of the benchmark. They are **not** coordinate-free, as descriptor coupling has physical dimension $[\text{descriptor}]^{-1}$.
- **Canonical Reference Anchor:** All derivatives are evaluated at the frozen anchor:
  $$\mathbf{x}_0 = (\text{mass} = 250.0, \text{descriptor} = 0.0, \text{descriptor2} = 0.0, \text{distractor} = 0.0, \text{correlated\_distractor} = 0.0)$$
  At $\mathbf{x}_0$, all chemical modulations in the generative laws evaluate to exactly $1.0$, isolating the logarithmic mass elasticity from chemical modulations and enabling clean extraction of descriptor couplings.

**Parameter Definitions and Tolerances:**
1. **Mass Scaling Exponent ($p_{\text{mass}}$):**
   Applicable to all 156 cases. Defined as the dimensionless logarithmic elasticity of $\hat{g}$ with respect to mass at $\mathbf{x}_0$:
   $$p_{\text{mass}}(\hat{g}) = \left. \frac{\partial \ln \hat{g}}{\partial \ln \text{mass}} \right|_{\mathbf{x}_0} = \left. \frac{\text{mass}}{\hat{g}} \frac{\partial \hat{g}}{\partial \text{mass}} \right|_{\mathbf{x}_0}$$
   - **Planted Truth ($p_{\text{truth}}$):** $0.50$ for F01–F05, F08–F12, F17, F18; drawn from $[0.45, 0.75]$ for F07.
   - **Absolute Tolerance:** $|p_{\text{mass}}(\hat{g}) - p_{\text{truth}}| \le 0.15$.
2. **Normalized Descriptor Coupling Coefficient ($c_{\text{desc}}$):**
   Applicable to the 84 held-out cases in descriptor-dependent families (F08, F09, F10, F11, F12, F17, F18). Defined as the relative sensitivity of $\hat{g}$ to the active descriptor(s) at $\mathbf{x}_0$:
   - For linear/affine (`mass_affine_descriptor`, F08, F11, F12, F17) and saturating (`mass_saturating_descriptor`, F09):
     $$c_{\text{desc}}(\hat{g}) = \left. \frac{1}{\hat{g}} \frac{\partial \hat{g}}{\partial \text{descriptor}} \right|_{\mathbf{x}_0}$$
   - For interaction (`mass_interaction`, F10):
     $$c_{\text{desc}}(\hat{g}) = \left. \frac{1}{\hat{g}} \frac{\partial^2 \hat{g}}{\partial \text{descriptor} \partial \text{descriptor2}} \right|_{\mathbf{x}_0}$$
   - For exponential (`mass_exponential_descriptor`, F18, where generative law is $\exp(c \cdot d / 3)$):
     $$c_{\text{desc}}(\hat{g}) = \left. \frac{3}{\hat{g}} \frac{\partial \hat{g}}{\partial \text{descriptor}} \right|_{\mathbf{x}_0}$$
   - **Planted Truth ($c_{\text{truth}}$):** $c = \text{coefficient} \in [0.25, 0.55]$.
   - **Absolute Tolerance:** $|c_{\text{desc}}(\hat{g}) - c_{\text{truth}}| \le 0.10$.

**Reporting Contract:**
- **Joint Parameter Recovery Rate:** $N_{\text{joint\_success}} / 156$ with Wilson 95% CI (governing secondary).
- **Mass Exponent Recovery Rate:** $N_{p\text{\_success}} / 156$ with Wilson 95% CI (descriptive decomposition).
- **Descriptor Coupling Recovery Rate:** $N_{c\text{\_success}} / 84$ with Wilson 95% CI (descriptive decomposition).

### 5.22.3 Predictive Equivalence (Secondary Endpoint, Denominator 144)

Predictive equivalence evaluates whether the discovered expression $\hat{g}$ accurately
predicts the true scaling law $g_{\text{true}}$ over an independent prospective reference
sample from the frozen synthetic covariate-generating process (Amendment A3.4).

- **Scientific Role:** SECONDARY descriptive endpoint (never part of G1, G2, or G3).
- **Applicable Families:** F01–F05, F08–F12, F17, F18 (12 families $\times$ 12 held-out cases = **144 cases**).
- **Denominator Discipline:** Strictly fixed at **144**.
- **Reference Covariate Distribution:** Evaluated across 12 independent case-shaped reference covariate frames (`PB|PRED_EQUIV|FRAME|000` to `011`, 180 compound rows and 30 scaffold groups per frame, 6 compounds per scaffold = **2,160 total reference points**) generated by the unchanged frozen synthetic generator with authentic marginal distributions and joint covariance ($r \approx 0.98$ between descriptor and correlated distractor).
- **Aggregate Reference Digest:**
  $$\mathbf{4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44}$$
- **Nomenclature Rule:** Described strictly as *an independent prospective reference sample from the frozen synthetic covariate-generating process*; never referred to as a "physical domain", "chemical domain", or "realistic molecular domain".

**Evaluation Metrics and Constraints:**
1. **Valid Point Set ($\mathcal{V}$):**
   $$\mathcal{V} = \{i \in \{1, \dots, 2160\} \mid \hat{y}_i \text{ is finite and } \hat{y}_i > 0, \text{ and } y_{\text{true}, i} \text{ is finite and } y_{\text{true}, i} > 0\}$$
   - Validity Threshold: $\text{valid\_fraction} = \frac{|\mathcal{V}|}{2160} \ge 0.995$ (at most 10 invalid points out of 2,160).
2. **Positive Scale Alignment ($c^*$):**
   Because $g$ is identified up to global positive scale in the collapse model, $\hat{\mathbf{y}}$ is aligned to $\mathbf{y}_{\text{true}}$ via least-squares scalar multiplier computed strictly over $\mathcal{V}$:
   $$c^* = \frac{\sum_{i \in \mathcal{V}} y_{\text{true}, i} \cdot \hat{y}_i}{\sum_{i \in \mathcal{V}} \hat{y}_i^2}$$
   - Constraint: $c^*$ must exist, be finite, and satisfy $c^* > 0$.
   - Affine intercept shifts ($a + b \hat{g}$ with $a \ne 0$), coefficient refitting, structure refitting, and candidate reselection are strictly **FORBIDDEN**.
3. **Scale-Adjusted Relative RMSE:**
   $$\text{RMSE} = \sqrt{\frac{1}{|\mathcal{V}|} \sum_{i \in \mathcal{V}} (c^* \hat{y}_i - y_{\text{true}, i})^2}, \quad \text{TRUTH\_RMS} = \sqrt{\frac{1}{|\mathcal{V}|} \sum_{i \in \mathcal{V}} y_{\text{true}, i}^2}, \quad \text{REL\_RMSE} = \frac{\text{RMSE}}{\text{TRUTH\_RMS}}$$
   - Success Threshold: $\text{REL\_RMSE} \le 0.05$.
4. **Pearson Correlation ($r$):**
   Computed over $\mathcal{V}$.
   - Zero-Variance Rule: If either $\hat{\mathbf{y}}_{\mathcal{V}}$ or $\mathbf{y}_{\text{true}, \mathcal{V}}$ has zero sample variance, $r \equiv 0.0 \to \text{FAIL}$.
   - Success Threshold: $r \ge 0.990$.

**Complete Per-Case Success Rule:**
A case achieves Predictive Equivalence Success if and only if: (1) $\hat{g}$ is present and parseable under the frozen grammar; (2) $\text{valid\_fraction} \ge 0.995$; (3) $c^* > 0$ and finite; (4) $\text{TRUTH\_RMS} > 0$ and finite; (5) $\text{REL\_RMSE} \le 0.05$; (6) non-zero sample variance on $\mathcal{V}$; and (7) $r \ge 0.990$.

### 5.22.4 Exact Algebra Recovery (Secondary Endpoint, Denominator 60)

Exact algebra evaluates symbolic equivalence of the discovered expression to the planted
law after deterministic SymPy canonicalization.
- **Scientific Role:** SECONDARY descriptive endpoint (**no gate**, never merged into G2).
- **Applicable Families:** F01, F08, F09, F10, F17 (five families $\times$ 12 held-out cases = **60 cases**).
- **Subordination Principle:** Non-recovery is a reportable outcome and is not a failure of any gate; positive recovery does not alter the G2 gate verdict.

### 5.22.5 Diagnostic Endpoints

Diagnostic endpoints (M0 specificity 164, M1 sensitivity 36, M2 sensitivity 24,
M3 sensitivity 24, trajectory prediction 164, profile stability 164, scalar target yield 164,
boundary hit 12, response structure diagnostic 4, and G3 components at 12 each) provide
mechanistic diagnostic reporting and enter no primary gate.

## 5.23 Failure semantics

Failure states are typed and are never silently converted into successes.

**Adequacy.** Insufficient data, boundary limitation, numerical failure, model
fit failure and timeout produce indeterminate states that are never M0
acceptance (`MURU_PAPER_BENCHMARK_METRICS.md`).

**Structural acceptance.** The ordered predicate is truth-blind and family
correctness is not part of it
(`MURU_PAPER_BENCHMARK_AMENDMENT_A3_1.md`):

1. A1 adequacy: only `M0_NOT_REJECTED` proceeds; rejection states give
   `REJECTED_A1_INADEQUATE`; failure, timeout and contract states give
   `UNEVALUABLE`.
2. `valid_r2 > null_threshold[min(complexity, 20)]`
3. `selection_fraction >= 20/30`
4. `complexity <= 20`
5. `invalid_fraction <= 0.005`
6. effective support non-empty
7. `ceiling_fraction >= 0.80` OR `ceiling_r2 < 0.05` (waiver)
8. reduced falsification harness passes

**Calibration.** Three per-seed statuses as in Section 5.13; any
`EXECUTION_FAILURE` seed makes its world's entire curve `+1.0`; more than five
failed worlds invalidates calibration entirely.

**G2 support.** Unresolvable expressions give `SUPPORT_UNRESOLVED`; degenerate
exact family intersection gives `FAMILY_AMBIGUOUS`.

**G3.** `UNEVALUABLE` is counted as a violation, not excluded. This is
deliberate: a pipeline that avoids unsafe acceptances by failing to evaluate has
not demonstrated safety.

## 5.24 Deterministic seeds

All randomness is derived, never global. Six distinct namespaces
route through the canonical `generator.derive_seed`, none derived from another
(`src/muru/paper_benchmark/rc3_calibration_worlds.py`,
`MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md`):

| Purpose | Namespace |
|---|---|
| base-target permutation | `PB\|NCAL\|<world_id>\|BASE_TARGET` |
| calibration scaffold split | `PB\|NCAL\|<world_id>\|SPLIT` |
| null-family transformation | `PB\|NCAL\|<world_id>\|null_construction` |
| frozen-law draw | `PB\|NCAL\|<world_id>\|law` |
| PySR search seeds | `calibration_contract.derive_calibration_seeds` |
| predictive equivalence frames | `PB\|PRED_EQUIV\|FRAME\|{index:03d}` |

Benchmark case generation uses `derive_seed(case_id, stage)` per stage, with
`ROOT_SEED = 20260813`.

**Resolved payload form.** The amendment notation above, read literally, doubles
the `PB|NCAL` prefix, because `world_id` already is
`PB|NCAL|<construction>|r<index:03d>`. The amendment wording is authoritative
and is not restated differently here; what `derive_seed` actually hashes is

```
paper-benchmark-v1|<world_id>|<namespace>
```

for example
`paper-benchmark-v1|PB|NCAL|target_permuted_across_compounds|r000|BASE_TARGET`.
This is recorded so a replicator can reconstruct a calibration seed from the
manuscript alone rather than from the notation
(`src/muru/paper_benchmark/rc3_provenance.py`, `a3_2_world_construction`).

Seed bands are separated by construction: the calibration band is derived from
`PB_SEED_BASE` and `PB_SEED_SPREAD`, and the engineering smoke band lies
strictly below it with a wide guard gap, both signed-32-bit safe, with an
explicit `assert_seed_band_separation` guard
(`src/muru/paper_benchmark/rc3_provenance.py`).

## 5.25 Resume and checkpoint semantics

The calibration runner is resumable at the granularity of one `(world, seed)`
unit. Seed records are appended and are **never rewritten or deleted**; a resumed
run appends only, and resumes without re-executing any completed seed. A seed
that did not produce a record is simply not yet done and is re-executed on
resume. Records carry a search-settings digest and a world-construction binding,
so a record produced under different settings or a differently built world has a
different digest and **cannot be adopted on resume**
(`src/muru/paper_benchmark/rc3_calibration_runner.py`). RC3.1 additionally binds
seed records to their world and fails the settings gate closed (`07c64c8`).

A wall-clock budget guard exists per seed; the timeout path is an
`EXECUTION_FAILURE` under Section 5.13 semantics.

## 5.26 Contamination controls

- **Registry isolation.** The registry is metadata-only and cannot load inputs,
  truth, outcomes or real-world records.
- **Generator isolation.** The generator depends only on the registry and
  standard numerical libraries, and is independent of all historical and
  real-data code.
- **Truth blindness.** The structural acceptance predicate never reads planted
  truth; the G2 contract reads truth only for post-hoc scoring, which is
  separated from acceptance by design.
- **Held-out guard.** No command may load or score held-out data before the
  complete executable freeze; the guard refuses while status is `PENDING_LOCK`.
- **Seal integrity.** Confirmation is sealed and hash-verified.
- **Amendment discipline.** Each amendment records its temporal position with
  respect to calibration, Development, Held-out and Confirmation, and
  machine-readable `governance_form` flags assert that it was not informed by
  development, threshold, held-out or confirmation results
  (`artifacts/paper_benchmark_amendment_a3_4.json`).
- **Temporal provenance adjudication.** The execution chronology is documented
  and adjudicated under the outcome-blind A3.4 Temporal Provenance Erratum
  (`audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md`).
- **Seed-band separation.** Engineering smoke seeds cannot collide with
  calibration seeds.
- **Engineering smoke is not scientific evidence** and is excluded from the
  evidence ledger's evidentiary tier.

## 5.27 Dependency environment

The RC3 dependency pin source is `configs/rc3_requirements_lock_c7c2332.txt`, a
byte-identical copy of `requirements.lock.txt` at RC2 commit `c7c2332`, with
SHA-256 `13b21b8ca409b82d1ef8d94aa5e487e2523d5264807f04fc1e65a5553c357fa8`. It
lives under `configs/` rather than `artifacts/` because `artifacts/` is
gitignored wholesale and a runtime guard that reads a file absent from a fresh
clone is not a guard. The repository's own root `requirements.lock.txt` is a
reduced Phase-1 lock that omits PySR, SymPy, gplearn and the Julia bridge, and
cannot serve as the RC3 pin source
(`src/muru/paper_benchmark/rc3_provenance.py`).

Versions are read from installed distribution metadata and never by importing
the module, because importing `juliacall` ahead of `pysr` segfaults the
interpreter, and a provenance check must not be able to crash the run it
protects. A version mismatch against the pinned lock fails loudly.

The ceiling estimator is bound to `scikit-learn==1.9.0`, with the pin parsed
from the frozen `CEILING_ESTIMATOR_SPEC` so it can only be changed by editing a
module RC3 may not edit (`src/muru/paper_benchmark/rc3_ceiling.py`).

## 5.28 Reproducibility and artifact hashing

Content freeze consists of the case registry, the fully synthetic generator,
partition assignment, truth schema, generated input artifacts, metrics, endpoint
denominators, null definitions, hashes, reference covariate frames, and the
Development-only preflight record. The executable freeze additionally requires a
locked implementation commit, strict evaluator version, grammar, engine configuration,
runtime budget, complete engine preflight, verified hashes and a clean tracked tree
(`MURU_PAPER_BENCHMARK_FREEZE.md`).

Required tracked artifacts: `paper_benchmark_partition_manifest.json`,
`paper_benchmark_case_manifest.json`, `paper_benchmark_truth_manifest.json`,
`paper_benchmark_hash_inventory.json`, `paper_benchmark_preflight.json`,
`paper_benchmark_content_freeze.json`, and the per-amendment integrity artifacts
`paper_benchmark_amendment_a1.json`, `..._a2.json`, `..._a2_1.json`,
`..._a3_1.json`, `..._a3_2.json`, `..._a3_3.json`, `..._a3_4.json`, and
`audit/muru_a3_4_temporal_provenance_erratum.json`.

Each amendment records per-path SHA-256 verification of the claim that every
frozen scientific artifact unrelated to that amendment is byte-identical to its
parent. Integrity scripts `scripts/pb_30_*` through `scripts/pb_34_*` re-verify
these mechanically. Full inventory: `MURU_REPRODUCIBILITY_INVENTORY.md`.

## 5.29 Statistical analysis

**Binomial endpoints.** G1, G2 and G3 use Wilson score intervals at 95%. G1 and
G2 are gated on the lower bound at 0.70; G3 is gated on the upper bound at 0.15.
Secondary endpoints (parameter recovery, predictive equivalence, exact algebra,
support recovery, diagnostic sensitivity/specificity) report Wilson 95% intervals
without gates. Denominators are frozen from case applicability and are never
adjusted after execution.

**Zero-count reporting.** A point estimate of 0 out of N does not license a
claim that the population rate is zero. The interval is the claim, and `p = 0`
language is not used for a finite simulation count. Historical practice used
Clopper-Pearson exact intervals for false-positive rates
(`PHASE3_DECISION.md`, `TYPE2_VALIDATION_DECISION.md`).

**Threshold uncertainty.** World-level bootstrap, 2,000 resamples, seed
20260812, reported for every complexity level and gating nothing.

**Multiplicity.** Search multiplicity is handled inside the null statistic
itself, by allowing the null the same 30-seed maximum the protocol takes. No
separate multiple-testing correction is applied across the 20 case families;
each endpoint has its own frozen denominator and its own single frozen gate.

**Adequacy aggregation.** Compound-level leave-one-energy-out MAE ratios are
aggregated to case level by the 24-of-30 evaluability and 20-of-30 practical-win
counting rule of Section 5.8. No continuous test statistic or p-value is used at
the case level.

Analysis of Challenge cases is descriptive; they enter no gate.

---

# Section 6. Prospective endpoint table

Classification below is fixed by the frozen record and **not** by observed
prospective performance, none of which exists. This table is reproduced as
Table 2 in `MURU_TABLE_SHELLS.md`.

| Endpoint | Role | Definition | Partition | Denominator | Success rule | Failure handling | Uncertainty | Claim supported if successful |
|---|---|---|---|---:|---|---|---|---|
| G1 scalar competence | **PRIMARY** | Spearman(true, fold-local est. log-g) >= 0.80 AND held-out trajectory MAE <= 0.80 x per-energy-mean baseline AND `M0_NOT_REJECTED` | Held-out | 164 | Wilson lower 95% >= 0.70 | indeterminate adequacy is never acceptance; case counts as failure | Wilson 95% | Under frozen synthetic truth, a molecule-specific horizontal scale is estimable out of sample |
| G2 family recovery | **PRIMARY** | `support_status == MATCH` AND `family_status == MATCH` | Held-out | 144 | Wilson lower 95% >= 0.70 | `SUPPORT_UNRESOLVED` / `FAMILY_AMBIGUOUS` count as non-success | Wilson 95% | Correct variable support and mathematical family are recoverable under frozen synthetic truth |
| G3 principal structural safety | **PRIMARY** | Unsafe structural acceptance across F07+F19+F20 opportunities | Held-out | 36 | Wilson upper 95% <= 0.15 | `UNEVALUABLE` is a **violation**, retained in denominator | Wilson 95% | The unsafe structural-acceptance rate across the 36 tested opportunities has a 95% Wilson upper bound of at most 0.15, for the frozen pipeline and these constructions only |
| F07 false extra-structure | SECONDARY (G3 component) | acceptance of non-mass structure where truth is mass-only | Held-out | 12 | reported with numerator, rate, interval | as G3 | Wilson 95% | The rate at which mass-only truth induces accepted non-mass structure is bounded above by the reported interval |
| F19 false-null-structure | SECONDARY (G3 component) | acceptance of the specified null structure | Held-out | 12 | reported with numerator, rate, interval | as G3 | Wilson 95% | The acceptance rate in the specified target-null worlds is bounded above by the reported interval |
| F20 false-adversarial-structure | SECONDARY (G3 component) | acceptance under latent-driver, measurement-coupling, out-of-grammar traps | Held-out | 12 | reported with numerator, rate, interval | as G3 | Wilson 95% | The acceptance rate in the specified adversarial traps is bounded above by the reported interval |
| M0 specificity | SECONDARY | adequacy status is `M0_NOT_REJECTED` | Held-out | 164 | descriptive rate + interval | indeterminate states are never acceptance | Wilson 95% | The scalar collapse model is not spuriously rejected where it holds |
| M1 sensitivity | SECONDARY | the M1 detector fires | Held-out | 36 | descriptive rate + interval | detector identity preserved | Wilson 95% | Horizontal-shape violations are detected |
| M2 sensitivity | SECONDARY | the M2 detector fires | Held-out | 24 | descriptive rate + interval | detector identity preserved | Wilson 95% | High-energy vertical violations are detected |
| M3 sensitivity | SECONDARY | the M3 detector fires | Held-out | 24 | descriptive rate + interval | detector identity preserved | Wilson 95% | Low-energy vertical violations are detected |
| Support recovery | SECONDARY | `support_status == MATCH` alone | Held-out | 144 | descriptive rate + interval | `SUPPORT_UNRESOLVED` is non-success | Wilson 95% | Relevant variable support is recoverable |
| Parameter recovery | SECONDARY | $|p_{\text{mass}} - p_{\text{truth}}| \le 0.15$ at anchor $\mathbf{x}_0$ across 156 cases AND (for 84 descriptor cases) $|c_{\text{desc}} - c_{\text{truth}}| \le 0.10$ | Held-out | 156 | joint rate /156, mass exponent /156, descriptor coupling /84; descriptive rate + interval | unparseable, missing, non-finite, or unresolved expressions count as non-success | Wilson 95% | Dimensionless mass scaling exponents and descriptor coupling sensitivities are recoverable within specified tolerances at the canonical benchmark anchor |
| Predictive equivalence | SECONDARY | discovered expression predictively equivalent to true law across 12 case-shaped reference covariate frames (2,160 rows, digest `4fef2379...`) | Held-out | 144 | valid fraction $\ge 0.995$, $c^* > 0$, $\text{REL\_RMSE} \le 0.05$, Pearson $r \ge 0.990$ (zero variance fails); descriptive rate + interval | invalid points > 10, non-positive scale, zero variance, or parse failure counts as non-success | Wilson 95% | Discovered expressions predictively match generating truth across an independent prospective reference sample from the synthetic covariate-generating process |
| **Exact algebra recovery** | SECONDARY (never merged into G2) | symbolic equivalence of the reported expression to the planted law | Held-out | 60 | descriptive rate + interval; **no gate** | non-recovery is a reportable outcome and is not a failure of any gate | Wilson 95% | Nothing beyond itself; the rate is a finding in either direction, and neither direction is a verdict on G2 |
| Trajectory prediction | DIAGNOSTIC | held-out trajectory MAE vs per-energy-mean baseline | Held-out | 164 | descriptive | numerical failure recorded | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | Out-of-sample trajectory usefulness |
| Profile stability | DIAGNOSTIC | frozen profile-stability criterion | Held-out | 164 | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | The shared profile is stable across folds |
| Scalar target yield | DIAGNOSTIC | fraction of compounds yielding a usable scalar target | Held-out | 164 | descriptive | boundary/failure states recorded | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | Target estimability, reported separately from accuracy |
| Boundary hit | DIAGNOSTIC | estimated scale lands at a grid boundary | Held-out | 12 | descriptive rate | boundary hits are **recorded**, closing FM-08 | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | Boundary prevalence is now measurable, unlike historically |
| Response structure diagnostic | DIAGNOSTIC | destroyed-trajectory worlds flagged non-evaluable (F19C) | Held-out | 4 | descriptive | failure to flag is also a G3 violation via F19C | `[METHOD DETAIL REQUIRES VERIFIED SOURCE]` | Response destruction is detected rather than modelled |
| Calibration validity | DIAGNOSTIC (precondition) | worlds with zero `EXECUTION_FAILURE` seeds | Calibration | 100 | at least 95; else `CALIBRATION_INVALID` | no retries, no replacement worlds | none (count) | The threshold table may be activated at all |
| All Challenge endpoints | **CHALLENGE ONLY** | as above, on the 60 Challenge cases | Challenge | 60 cases; per-endpoint counts of Table 1 | descriptive only | descriptive | descriptive | Stress behaviour; enters no primary claim |

### Section 6a. Historical supporting context (CLASS A, never a prospective endpoint)

Held separately from the table above so that no historical rate occupies a
denominator column beside a prospective one. None of these rows is an endpoint
of this study, and none is comparable to a prospective rate: the world families,
the pipelines and the success definitions all differ.

| Historical question | Historical source | Historical finding | Eligible prospective use |
|---|---|---|---|
| Did PySR recover planted support? | Type 2 G1B moderate | 20 of 20 block supports recovered | Motivation for G2 support contract |
| Did PySR recover functional family? | Type 2 G1B moderate | 16 of 20 dense-lattice family recovered (measured, not gated); composite success gate 17/20 | Motivation for G2 family contract; neither is the G2 definition |
| Did PySR recover exact equations? | Phase 3 G1B; Type 2 positive controls | Functional/symbolic recovery 0% across all noise regimes; 0 in Type 2 G1A, G1B, G1C, G3 | Motivation for separating exact algebra from G2; basis for L8 |
| Did PySR accept pure nulls? | Phase 3; Type 2 | 0 of 100 in each study, Clopper-Pearson 95% [0.0000, 0.0362] | Motivation for G3 |
| Did PySR accept confounded worlds? | Type 2 G5 | 0 of 8, Clopper-Pearson 95% [0.0000, 0.3694] | Motivation for F20A |
| Did PySR accept measurement-coupled worlds? | Type 2 GC | 0 of 9, Clopper-Pearson 95% [0.0000, 0.3363] | Motivation for F20B |
| Did PySR accept non-compressible worlds? | Type 2 G2 | 0 of 8, Clopper-Pearson 95% [0.0000, 0.3694]; H-MAIN rejected 8 of 8 | Motivation for F06 |
| Did PySR certify structure beyond mass? | Type 2 F8 labelling | 1 of 19 accepted G1B moderate worlds | Basis for C7 status: weak |
| Was historical gplearn non-agreement meaningful? | Engine competence audit | Comparison arm failed C0/C1/C2 competence gates | Removes inference that candidates were artifacts; corroboration gate still failed |
| Did within-compound permutation preserve levels? | Type 2 null calibration | p95 of 0.7228 at c=20 against 0.0835 to 0.1509 | Motivation for excluding the construction |
| Was `fit_collapse` transductive? | Soundness audit | Perturbing one trajectory changed others by up to 0.0987 | Motivation for frozen execution boundary |
| Were complex outputs cast to float? | Historical evaluator | Casting unquantified reach | Motivation for strict evaluation and typed unresolved states |
| Was energy dropout bounded? | Historical generator | 0.97% dropout, >=5 energies retained | Motivation for F04; basis for L11 |
| Were boundary hits invisible? | Historical estimator | Returned grid endpoint outside [-1.6, 1.6]; prevalence unknown | Motivation for F05 endpoint |

---

# Section 7. Results shell

**Evidence class C. Nothing in this section may be written before the
corresponding artifact exists.** Each subsection states what must populate it.

## 7.1 Calibration execution and validity

Required: number of the 100 worlds with zero `EXECUTION_FAILURE` seeds; the
validity verdict against the 95/100 floor; per-construction world counts
actually executed (34/33/33); total seed-runs attempted and completed out of
3,000; the full 20-row threshold table `T(c)` with its 2,000-resample bootstrap
intervals; and the per-construction 95th percentile breakdown, which is the
diagnostic that A3.2 exists to make interpretable.

Artifact: calibration threshold artifact and per-world seed records emitted by
`rc3_calibration_runner`. Status: `[PROSPECTIVE RESULT TO INSERT]`.

Note for the writer: if calibration is invalid, no threshold table is activated,
and the manuscript reports that and stops rather than substituting a fallback.

## 7.2 Development sanity check

Required: the 80-case Development execution record under the A3.1/A3.2 contract,
including per-endpoint counts, engine failure count, runtime and peak memory,
and any typed failure states. Status: `[PROSPECTIVE RESULT TO INSERT]`.

Note: Development is a sanity and feasibility check. It cannot alter
architecture, generator, coefficients, endpoints, grammar or thresholds, and no
Development number may be used to choose anything.

## 7.3 Held-out primary evaluation

Required: G1 numerator/164, G2 numerator/144, G3 numerator/36, each with the
Wilson 95% interval and the pass/fail verdict against its frozen gate; and the
umbrella-claim verdict, which is positive only if preconditions hold and all
three pass. Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.4 Scalar recovery

Required: distribution of Spearman correlation between true and fold-local
estimated log-`g` across the 164 applicable cases; the fraction meeting the 0.80
criterion; scalar target yield; and the family-level breakdown. The 164 comprise
13 families at 12 cases each (F01 to F05, F07 to F12, F17, F18 = 156) **plus
F19A and F19B at 4 cases each (8)**, which carry scalar truth even though their
symbolic structure is null; F19C is excluded from the scalar denominator. The
same 156 + 8 composition applies to M0 specificity, trajectory prediction,
profile stability and scalar target yield, all at 164. Status:
`[PROSPECTIVE RESULT TO INSERT]`.

## 7.5 Model adequacy

Required: M0 specificity on 164; M1 sensitivity on 36; M2 on 24; M3 on 24; the
F16 per-detector independent scoring; and the counts of each indeterminate
state (insufficient data, boundary limitation, numerical failure, model fit
failure, timeout). Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.6 Symbolic support recovery

Required: support recovery on 144; the F11 (independent distractor) and F12
(correlated proxy) breakdown, which is the direct test of whether the proxy is
distinguished from `descriptor`; and the `SUPPORT_UNRESOLVED` count. Status:
`[PROSPECTIVE RESULT TO INSERT]`.

## 7.7 Family recovery

Required: G2 by truth family across the five taxonomy members; the joint
support-and-family success rate that constitutes G2; and the `FAMILY_AMBIGUOUS`
count. Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.8 Parameter recovery

Required: Joint Parameter Recovery rate on 156 cases (/156) with Wilson 95% interval;
Mass Exponent Recovery rate on 156 cases (/156) with Wilson 95% interval ($|p_{\text{mass}} - p_{\text{truth}}| \le 0.15$);
Descriptor Coupling Recovery rate on 84 cases (/84) with Wilson 95% interval ($|c_{\text{desc}} - c_{\text{truth}}| \le 0.10$);
and the distribution of recovered parameter errors at canonical anchor $\mathbf{x}_0 = (250, 0, 0, 0, 0)$.

Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.9 Predictive equivalence

Required: Predictive Equivalence rate on 144 applicable Held-out cases (/144)
with Wilson 95% interval, evaluated over the 2,160 reference points across 12
case-shaped frames (aggregate digest `4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44`);
the relative RMSE and Pearson correlation distributions across valid cases; and
the F18 subset specifically (12 cases), which evaluates predictive accuracy on
algebraically non-equivalent expressions.

Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.10 Exact algebra recovery

Required: symbolic-equivalence rate on the 60 applicable Held-out cases (F01,
F08, F09, F10, F17; five families at 12 cases each), with Wilson 95% interval;
the number of distinct functional-equivalence classes in each reported result;
and an explicit statement of how many cases claimed algebraic identification.

Status: `[PROSPECTIVE RESULT TO INSERT]`.

Writer's note, binding, and symmetric. A low or zero exact-algebra rate is a
**finding**, is consistent with the historical record, and is not to be
presented as a failure of the primary endpoint or repaired by re-defining
equivalence. A high rate is equally a **finding** and must be reported together
with the count of distinct functional-equivalence classes, because a high
equivalence rate does not by itself establish that the algebra is identified.
Neither direction may be inferred in advance.

## 7.11 False discoveries and refusal cases

Required: F07 numerator/12, F19 numerator/12, F20 numerator/12, each with rate
and interval, reported beside the aggregate G3; the F19A/F19B/F19C and
F20A/F20B/F20C variant-level breakdown; the count of `UNEVALUABLE` outcomes
counted as violations; and the count of legitimate refusals, which are correct
outcomes and are not penalised. Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.12 Boundary and missing energy cases

Required: F05 boundary-hit rate on 12 applicable cases, which is the endpoint
that closes historical instrumentation gap FM-08; and F04 recovery under
declared missingness, which is the first measurement addressing FM-09. Status:
`[PROSPECTIVE RESULT TO INSERT]`.

## 7.13 Noise dependence

Required: the F01 (noiseless), F02 (moderate), F03 (stronger) comparison across
every endpoint, giving the prospective noise envelope. Status:
`[PROSPECTIVE RESULT TO INSERT]`.

## 7.14 Mass and descriptor confounding

Required: F07 (mass-only truth) behaviour; F12 (correlated proxy) support
outcomes; F20A (latent driver) and F20B (measurement coupling) outcomes; and any
structural-beyond-mass labelling recorded by F8, reported as a label and never
as an acceptance gate. Status: `[PROSPECTIVE RESULT TO INSERT]`.

## 7.15 Challenge results

Required: all endpoints on the 60 Challenge cases, reported descriptively and
labelled as entering no primary denominator. Status:
`[PROSPECTIVE RESULT TO INSERT]`.

## 7.16 Failure analysis

Required: a full census of typed failure states across the run: adequacy
indeterminates, `UNEVALUABLE`, `REJECTED_A1_INADEQUATE`, `SUPPORT_UNRESOLVED`,
`FAMILY_AMBIGUOUS`, `COMPLETED_NO_CANDIDATE`, `EXECUTION_FAILURE`, and
falsification-rung failures by rung (F1, F4, F5, F7, F9, F10). Status:
`[PROSPECTIVE RESULT TO INSERT]`.

## 7.17 Reproducibility

Required: the executable freeze record; verified hashes of all frozen paths;
clean-tree confirmation; the dependency provenance manifest with observed
versions against the pinned lock; total runtime and unit counts; and
confirmation that resume recomputed no completed unit. Status:
`[PROSPECTIVE RESULT TO INSERT]`.

---

# Section 8. Table shells

See `MURU_TABLE_SHELLS.md` for Tables 1 to 10.

# Section 9. Figure plan

See `MURU_FIGURE_PLAN.md` for Figures 1 to 8.

---

# Section 10. Discussion shell

Outcome-dependent interpretation is deliberately absent. Five explicit
placeholders mark where it goes.

## 10.1 Formula discovery requires stronger validation than prediction

A predictive model is validated by out-of-sample error. A discovered formula is
not, because the formula makes a claim beyond its own predictions: it asserts
which variables matter, in what functional relationship. Two expressions with
identical held-out error can make incompatible structural claims, so predictive
accuracy cannot arbitrate between them.

Three additional requirements follow, and each is built into the design of
Section 5. First, a discovery must be scored against something the search itself
could have produced by chance, at the same complexity and with the same number of
restarts; hence the null-calibrated threshold. Second, the pipeline must be
capable of returning nothing; hence a typed acceptance predicate with refusal
states, and worlds (F06, F19C, F20) where refusal is the correct answer. Third,
the claim must be decomposed into levels that can succeed and fail
independently: support, family, coefficients, prediction, exact algebra.

## 10.2 Family recovery and exact algebra recovery are different claims

The distinction is not a technicality; the project has direct evidence that it
is the dominant one. In the historical Type 2 study, family-level recovery was
16 of 20 as measured on the moderate-noise positive controls, with support
recovered in 20 of 20; that study's composite success gate, which combined
support, exponent and shape rather than dense-lattice family identity, passed 17
of 20. Neither number is defined as the prospective G2 endpoint and neither is
comparable to it. Against both, symbolic equivalence to the planted law was zero
in every positive-control block, with a median of 8.5 distinct
functional-equivalence classes inside a single reported family (Section 4.3).

The G1C block sharpens it further: with a generating law outside the frozen
grammar by construction, support was recovered in 8 of 10 worlds and shape family
in 10 of 10, and the system claimed algebraic identification in 0 of 10. That is
the behaviour the claim class requires. The correct reading of such a result is
that the empirical family and its scaling are identified within the experimental
domain, and the exact algebraic form is not identified at the current
experimental resolution.

The prospective benchmark therefore gates on family recovery (G2) and reports
exact algebra as a separate, ungated secondary endpoint. A reader should not
infer either from the other in either direction.

`[INTERPRET EXACT ALGEBRA RESULT]`

## 10.3 Falsification and null calibration are central, not ancillary

Genetic programming always returns something, so a raw goodness-of-fit score for
a discovered expression carries no information about whether structure exists.
The threshold a candidate must clear is built empirically at the candidate's own
complexity from worlds where no valid structural relationship exists, and the
statistic allows the null the same 30-seed maximum that the protocol itself
takes. Search multiplicity is thereby priced in rather than corrected for
afterwards.

Which null constructions are admissible depends on the target. Because the
symbolic target here is a per-compound scalar rather than a trajectory, a null
that preserves compound mean level preserves much of the target; this is why
within-compound energy permutation is excluded prospectively (Sections 4.4 and
5.13) and why A3.2 replaces a scaffold-structured base target with a global
permutation (Section 5.14). Both corrections remove a mechanism by which the threshold could be
biased in the permissive direction, which is the direction a safety-oriented
benchmark may not accept. Neither correction's effect on the threshold table has
been measured, because no calibration has been executed; the observed
per-construction breakdown is `[PROSPECTIVE RESULT TO INSERT]`.

## 10.4 How this differs from mechanistic inference

Nothing in this design identifies a mechanism. The synthetic laws are chosen
functional forms over synthetic descriptors; recovering one demonstrates that the
pipeline can recover that form, not that the form describes fragmentation
physics. Even where a recovered expression is correct by construction, the
correctness is about the recovery machinery.

The distinction is made concrete by the project's own real-data audit, where a
mass association in the response was reproduced at rho = -0.4791 by a stipulated
low-mass cutoff with no chemistry in the construction (Section 4.1). An
association, a good fit, and a compact expression are jointly insufficient for a
mechanistic reading.

## 10.5 Why synthetic truth allows what real spectra do not

Real spectra provide no external object against which support recovery, family
recovery or exact-algebra recovery can be scored: whatever the pipeline returns,
there is nothing to compare it to. Synthetic worlds supply exactly that object,
and only that object. They allow the measurement of quantities that are
undefined on real data, and they allow adversarial worlds (F19, F20) in which the
correct answer is known to be refusal.

What they cannot do is establish that the pipeline would behave the same way on
real fragmentation data, because the truth families are investigator-chosen and
the covariates are synthetic.

## 10.6 Limitations of synthetic validation

See Section 11 for the full treatment. In summary: synthetic evidence bounds
what the machinery can do under known truth and says nothing about real-world
accuracy; the five truth families and five synthetic covariates are a
deliberately small, investigator-chosen space; and the synthetic covariate
correlation structure, while designed to include a near-proxy and an independent
distractor, does not reproduce the correlation structure of real molecular
descriptors.

## 10.7 Instrument transferability

Collision energy conventions differ between instruments and vendors, and a
recorded energy value frequently arrives without a declared unit or
normalisation. The project's own real-data handling reflects this by storing raw
string, parsed numeric, declared type and separately derived laboratory-frame and
centre-of-mass values as distinct fields. A scaling relationship expressed on one
instrument's energy axis does not transfer to another's without an explicit
mapping, and this benchmark provides none.

The project's real-data arm is additionally restricted to positive mode: the
structure-beyond-mass result did not replicate in negative mode.

## 10.8 Chemical realism

The synthetic covariates are generated from a per-scaffold latent with declared
correlation structure; they are not molecular descriptors and carry no chemistry.
The synthetic response is a chosen profile function with chosen deviations, not a
fragmentation simulation. No claim about chemical realism is made, and none can
be inferred from any result in Section 7.

## 10.9 The need for external real-data validation

Real-data validation is separately governed and is not authorised. Phase 3 is
`STOP BEFORE PHASE 4`; Type 2 is `DO NOT AUTHORIZE PHASE 4`; the real-data
claims ladder stands at L3; and the 110-compound Confirmation set remains sealed.
Any real-data symbolic discovery requires a new pre-registration and a fresh
authorisation, not an extension of this work.

## 10.10 Outcome-dependent interpretation

`[INTERPRET HELD-OUT PERFORMANCE]`

`[INTERPRET FAILURE MODES]`

`[INTERPRET FALSE DISCOVERY RESULT]`

`[INTERPRET CHALLENGE SET]`

No positive conclusion is precommitted. If any gate fails, the manuscript reports
the failure and the descriptive endpoint tables, and does not substitute a
weaker claim chosen after the fact.

---

# Section 11. Limitations

## 11.1 Limitations of the evidence class

**L1. Synthetic evidence does not establish real-world accuracy.** Every case in
this benchmark is generated. No result here supports any statement about real
spectra, real molecules, or a real instrument.

**L2. The truth families may not span real fragmentation mechanisms.** Five
truth families (`mass_affine_descriptor`, `mass_power`,
`mass_saturating_descriptor`, `mass_interaction`,
`mass_exponential_descriptor`) over five synthetic covariates are an
investigator-chosen space. Recovery within it does not generalise to forms
outside it, and F20C exists precisely to include a case the grammar cannot
represent.

**L3. Collision-energy conventions differ between instruments.** Section 10.7.
No cross-instrument mapping is provided or validated.

**L4. Chemical realism is absent by construction.** Section 10.8.

**L5. Absence of prospective physical acquisition.** No new spectra were
acquired for this work. The real-data arm uses a fixed historical corpus and is
separately governed.

## 11.2 Limitations that remain live in the prospective system

**L6. Descriptor relationships can be confounded, and this is not eliminated.**
The synthetic frame deliberately contains a near-proxy
(`correlated_distractor = 0.85*descriptor + 0.15*noise`) and mass driven by the
same latent as the descriptors. The G2 contract requires the proxy to be
distinguished from `descriptor`, but whether the pipeline achieves that is
`[PROSPECTIVE RESULT TO INSERT]`. Historically, structure-beyond-mass labelling
was weak: 1 of 19 accepted worlds on the real descriptor frame (Section 4.7).

**L7. Symbolic expressions can be non-identifiable.** Established historically
(FM-14): family recovery of 80% coexisted with zero symbolic equivalence and a
median 8.5 functional-equivalence classes per reported family. The prospective
design responds by separating endpoints, not by claiming identifiability.

**L8. Exact equation recovery may be unstable.** Established historically
(FM-01, FM-02). The prospective benchmark does not assume it will succeed and
does not gate on it.

**L9. Finite calibration uncertainty remains.** The threshold is a 95th
percentile over 100 worlds and rests on its top few order statistics. A bootstrap
interval is reported for every complexity, and a candidate whose validation R2
falls inside that interval should be treated as inconclusive rather than as
clearing the null. Historical precedent: the Phase 3 complexity-20 threshold of
+0.4889 carried an interval of [+0.2603, +0.6859].

**L10. Noise envelope is bounded.** Claims are restricted to the tested noise
levels (F01 to F03). Historically, Type 2 success fell from 100% at residual SD
0.010 to 85% at 0.0295 to 30% at 0.060. A candidate found at comparable or worse
residual scale is unconfirmed.

**L11. Missing-energy coverage is bounded.** F04 provides declared missingness
of one energy. Robustness to materially more missing data is not established.

**L12. Boundary-scale behaviour is measured but bounded.** F05 records boundary
hits on 12 Held-out cases. That closes the historical instrumentation gap, but 12
cases is a small denominator for a rate.

**L13. Challenge cases enter no gate.** They are descriptive stress tests, and a
good Challenge outcome cannot rescue a failed primary gate.

**L14. Search-artifact status is not independently corroborated.** The
prospective acceptance predicate uses a single search engine. The historical
comparison arm was shown insufficiently competent for a veto role (FM-04), and no
replacement corroborating engine is included here. Convergence of two independent
engines is therefore not among this work's evidence.

**L15. Python version deviates from the master plan target.** The plan named
Python 3.12; the verified execution environment is 3.13.12. Nothing in the
lockfiles or the PySR/Julia stack caps the version below 3.13, and the full stack
was verified working, but the deviation is recorded rather than absorbed.

## 11.3 Historical defects that the prospective system closes

These are stated as **corrected**, not as live limitations, and they must not be
described as still active.

A distinction runs through the table and must be preserved. Some items are
closed **by specification and by a verified artifact**: the correction is
written into a frozen contract and its presence is mechanically checkable
today. Others are closed **by specification, with implementation conformance
pending verification at the executable freeze**: the contract forbids the old
behaviour, but this draft did not verify the production path against it, and the
content freeze remains `WAITING_FOR_LOCKED_IMPLEMENTATION`. The second kind is
not yet an achieved property of running code.

| Historical defect | Closed by | Closure basis |
|---|---|---|
| FM-05 scalar-null information preservation: within-compound energy permutation preserved compound level and dominated the pooled threshold | Amendment A3.1 excludes the construction; RC3.1 makes it unconstructible, not merely unused | specification and verified artifact |
| Scaffold-structured null base target, a mechanism for permissive threshold bias | Amendment A3.2 Decision 1: global permutation of the frozen-law target across all compound identities before any null-family transformation or partition use | specification and verified artifact |
| A3.1's specified 60/20/20 calibration split not realised by the inherited generator | Amendment A3.2 Decision 2: dedicated calibration split helper at 18/6/6 scaffolds (108/36/36 compounds), generator left byte-identical | specification and verified artifact |
| FM-06 transductive target construction | Frozen execution boundary: all shared objects fitted from training trajectories only, then frozen; each validation or test compound estimated independently (Section 5.7) | **closed by specification; production-path conformance pending executable-freeze verification** |
| FM-07 complex-cast evaluator accepting complex-valued expressions | Strict symbolic evaluation under the protected grammar with deterministic SymPy normalisation and typed `SUPPORT_UNRESOLVED` (Section 5.12) | **closed by specification; production-path conformance pending executable-freeze verification** |
| FM-08 boundary-scale invisibility | F05 boundary-hit is a declared endpoint with a frozen Held-out denominator of 12 | specification and verified artifact |
| Unspecified adequacy decision rule (a specification gap in content freeze V1) | Amendment A1 binds statistic, identifiability treatment, threshold, aggregation and failure semantics | specification and verified artifact |
| F16's declared M1+M2+M3 truth not honoured by the generator | Amendment A2 repairs the F16 generator; A2.1 bumps `GENERATOR_VERSION` accordingly | specification and verified artifact |

Two nuances must be preserved rather than smoothed over.

**FM-09 is only partially addressed.** F04 introduces a declared missing-energy
family, which historical work lacked entirely. It does not establish robustness
to materially missing trajectories, and L11 above remains live.

**FM-04 changes an inference, not a verdict.** The engine-competence audit
removes the inference that historical gplearn non-agreement demonstrated PySR's
candidates were artifacts. It does not turn the failed historical corroboration
gate into a pass, and `DO NOT AUTHORIZE PHASE 4` remains binding.

## 11.4 Claims that remain unavailable regardless of outcome

No prospective result in this benchmark can establish that a real collision-energy
law exists, that any expression is a physical or mechanistic law, or that a
mechanism has been identified. These require real-data evidence that is not
authorised and has not been collected. See `MURU_CLAIM_MATRIX.md`, final two
rows.

---

# Section 12. Reproducibility package

See `MURU_REPRODUCIBILITY_INVENTORY.md`.

# Section 13. Claim matrix

See `MURU_CLAIM_MATRIX.md`.

# Section 14. Evidence ledger

See `MURU_EVIDENCE_LEDGER.json`.

---

## Appendix A. Non-contamination attestation for this draft

This draft was synchronized in an isolated git worktree on branch
`writing/muru-preresults-manuscript-a3-4`, branching from commit `6e3dbc9`
(`claude/muru-preresults-manuscript-ba5ca5`).

| Item | Status during synchronization |
|---|---|
| A3.3 / A3.4 scientific contracts and audits | Incorporated from frozen artifacts (`71f5369`, `78cc7c2`, `be23b80`, `f1fb943`) |
| A3.4 Temporal Provenance Erratum | Incorporated from frozen audit artifact (`220c9cb`, tag `a3-4-temporal-provenance-erratum`) |
| Calibration execution | **NOT RUN BY THIS TASK; NO RESULTS INSPECTED** |
| Calibration result records | **NOT INSPECTED.** Read-only temporal timestamps used for provenance adjudication; no calibration score, output, or threshold table inspected |
| Development execution | **NOT RUN** |
| Development result artifacts | **NOT OPENED** |
| G1/G2/G3 prospective scoring | **NOT PERFORMED** |
| Parameter recovery / Predictive equivalence prospective scoring | **NOT PERFORMED** |
| Held-out partition | **SEALED, NOT OPENED** |
| Confirmation partition | **SEALED, NOT OPENED** |
| Frozen scientific code | **UNCHANGED** |
| Threshold rules and gates | **UNCHANGED** |
| Benchmark cases | **UNCHANGED** |

The only files modified by this work are under `paper/`. No tracked scientific
artifact, source module, test, script or benchmark governance document was modified.
