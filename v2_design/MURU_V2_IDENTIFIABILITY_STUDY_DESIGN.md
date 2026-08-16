# MURU v2: Descriptor Identifiability Study Design

**Status:** DESIGN ONLY. Nothing here has been executed.

**Covers:** E3 (`DESCRIPTOR_IDENTIFIABILITY`) and E5
(`F18_EXPONENTIAL_RESOLUTION`), which E3 gates.

**Addresses:** RC4 (57 representable cases never had a correct retained
candidate; v1 cannot distinguish search failure from weak identifiability) and
RC6 (F18 is impossible under the current grammar).

**The question the sealed evidence could not answer.** Decomposition section 9,
item 2: "It cannot distinguish 'the search cannot find the descriptor term' from
'the descriptor term is not identifiable at the planted coefficient magnitudes'.
The 57 generation failures, and F09's complete absence of any correct candidate
across 360 searches, are consistent with either."

E3 answers it without running a symbolic search at all.

---

## 1. Design principle: remove the search from the question

Whether a descriptor effect is recoverable has two independent parts:

1. **Is it there to be found?** Given the benchmark's noise, sample size, energy
   grid and covariate geometry, can *any* procedure separate the planted family
   from a mass-only alternative, and from its nearest structured rival?
2. **Does this search find it?** Given that it is separable, does PySR under the
   frozen grammar and budget reach it?

v1 conflated these. E3 measures only the first, by handing a model-selection
criterion the five correct parametric families in closed form. That is an
**oracle**: it faces no search space, no grammar, no complexity penalty, no
parsimony heuristic. Its success rate is therefore a hard ceiling on what any
symbolic search could achieve on the same data.

If the oracle cannot pick the truth out of five known candidates, no engine
change can rescue that cell, and the failure is a benchmark-construction fact.

---

## 2. Design-time arithmetic that motivates the study

The following is arithmetic over the **frozen generator specification**, not an
experimental result and not evidence from any partition. It is stated because it
makes E3's hypotheses precise and falsifiable.

### 2.1 The planted descriptor multipliers

From `generator.py::_law`, with `coefficient ~ rng.uniform(0.25, 0.55)` and
`descriptor` min-max normalised into `[0, 1]`:

| Family | Descriptor factor | Multiplier range at `c = 0.40` |
|---|---|---|
| `mass_affine_descriptor` (F01-F05, F08, F11, F12, F17) | `1 + c*d` | 1.000 to 1.400 |
| `mass_saturating_descriptor` (F09) | `1 + c*d/(1+d)` | 1.000 to 1.200 |
| `mass_interaction` (F10) | `1 + c*d*d2` | 1.000 to 1.400, but on a product with far smaller variance |
| `mass_exponential_descriptor` (F18) | `exp(c*d/3)` | 1.000 to 1.143 |

### 2.2 Distance from the nearest simpler rival

For each nonlinear family, the residual after subtracting its **best least-squares
affine approximation** in `d` over `d` in `[0, 1]`. This is the signal a
classifier must detect to distinguish the family from `mass_affine_descriptor`:

| Family | `c` | max abs residual | rms residual | rms relative to mean multiplier |
|---|---|---|---|---|
| saturating (F09) | 0.25 | 0.0171 | 0.0062 | 0.0058 |
| saturating (F09) | 0.40 | 0.0274 | 0.0099 | 0.0088 |
| saturating (F09) | 0.55 | 0.0377 | 0.0136 | 0.0117 |
| exponential (F18) | 0.25 | 0.00061 | 0.00027 | 0.00026 |
| exponential (F18) | 0.40 | 0.00161 | 0.00071 | 0.00066 |
| exponential (F18) | 0.55 | 0.00313 | 0.00137 | 0.00125 |

The F18 exponent is `c*d/3`, so it never exceeds 0.183 over the whole coefficient
support. Over that range `exp` is affine to within roughly one part in a
thousand.

**The reading.** F18's planted truth is separated from an affine descriptor law
by a relative rms of 0.03 to 0.13 percent. The default response noise sd for that
family is 0.02 on a response in `[0, 1]`, and the scalar `g` is not observed
directly but estimated from a 6-point trajectory, which adds further error. The
exponential structure is therefore, on its face, far below the noise floor of the
quantity the search consumes.

This has a consequence that matters more than RC6 as stated. RC6 says F18 is
impossible because the grammar lacks `exp`. The arithmetic above says that even
**with** `exp` in the grammar, an affine candidate would fit as well at lower
complexity, so a parsimony-driven search would essentially never emit the
exponential form, and `g2_contract._contains_exp_of` would still never see a
literal `exp` node. Adding the operator would convert F18 from impossible-by-
representation to impossible-by-identifiability, at the cost of a richer grammar
everywhere else.

F09's separation is 0.6 to 1.2 percent, roughly an order of magnitude larger than
F18's but still small, which is consistent with its 0 of 12 oracle recovery.

**These are predictions, not conclusions.** E3 measures them on real generated
worlds, through the actual `Phi`/`g` estimation stage, with the actual covariate
correlation structure. The arithmetic above ignores the estimator's error, the
descriptor's empirical distribution and the mass term's confounding, all of which
E3 includes.

---

## 3. E3: the identifiability measurement

### 3.1 Hypotheses

| ID | Statement |
|---|---|
| **H_id_affine** | `mass_affine_descriptor` is identifiable against mass-only at the frozen coefficient range and noise levels, with oracle-selection at or above 0.80. |
| **H_id_sat** | `mass_saturating_descriptor` is **not** distinguishable from `mass_affine_descriptor` at the frozen coefficient range, with oracle-selection below 0.50. |
| **H_id_exp** | `mass_exponential_descriptor` is **not** distinguishable from `mass_affine_descriptor` at the frozen coefficient range, with oracle-selection near chance. |
| **H_id_noise** | Where a family fails, the failure survives at zero response noise, meaning it is structural closeness rather than measurement error. |
| **H_id_geometry** | Doubling the energy grid from 6 to 12 points materially raises oracle-selection, meaning a share of the problem is acquisition geometry rather than family closeness. |

H_id_noise and H_id_geometry are the two diagnostic splits that determine whether
the remediation is a benchmark change, an acquisition change, or neither.

### 3.2 Independent variables

| Factor | Levels |
|---|---|
| truth family | `mass_power` (control), `mass_affine_descriptor`, `mass_saturating_descriptor`, `mass_interaction`, `mass_exponential_descriptor` |
| coefficient `c` | 0.25, 0.40, 0.55 (spanning the frozen `U(0.25, 0.55)`), 1.1, 2.2 (2x and 4x extensions) |
| response noise sd | 0.0, 0.02 (default), 0.0295 (F02), 0.06 (F03) |
| energy grid | 6 points (frozen `ENERGY_GRID`), 12 points (exploratory) |

The `c` ladder extends well past the frozen support so the study locates the
identifiability threshold `c*` rather than reporting a single verdict at the v1
operating point. This is the same anti-anchoring discipline as E1's `alpha`
ladder.

### 3.3 Procedure, per world

1. Generate the world with the frozen covariate machinery
   (`generator._synthetic_compounds`), fresh `V2C` seeds, and the target law set
   by the cell's family and `c`.
2. Run the **frozen** `Phi`/`g` estimation stage (`rc5_estimate.fit_case_scalars`)
   to obtain the per-compound estimate `g_hat`. This is exactly the quantity the
   symbolic search consumes, so the identifiability question is asked at the
   right place in the pipeline and not on an idealised target.
3. Fit, by least squares on the scaffold-disjoint training split, the five
   parametric candidates in closed form:

   | ID | Model |
   |---|---|
   | `M_mass` | `g = a * mass^b` |
   | `M_affine` | `g = a * mass^b * (1 + c*descriptor)` |
   | `M_sat` | `g = a * mass^b * (1 + c*descriptor/(1+descriptor))` |
   | `M_exp` | `g = a * mass^b * exp(c*descriptor)` |
   | `M_inter` | `g = a * mass^b * (1 + c*descriptor*descriptor2)` |

4. Evaluate every candidate on the held-out validation and test scaffolds.
5. Record the statistics in section 3.5.

No symbolic search is run. No grammar is involved. No complexity penalty is
applied. The oracle is handed the answer set.

### 3.4 Controls

1. **Negative control family.** `mass_power` worlds, where the truth has no
   descriptor at all. The oracle must **not** select a descriptor model. This is
   the study's own specificity arm, and without it a high oracle-selection rate
   would be uninterpretable.
2. **Noise-free arm.** `noise sd = 0.0` separates "the `g_hat` estimator is too
   noisy" from "the structures are too close even with perfect data".
3. **Paired seeds.** Within a `(family, noise, grid)` cell, all `c` levels share
   covariate and noise seeds across replicates, so the `c` response curve is
   measured on matched geometry.
4. **Frozen estimation.** `fit_case_phi` / `estimate_case_g` are used unmodified.
   E3 measures identifiability under the pipeline as it exists, not under an
   idealised estimator.
5. **Split discipline.** Model fitting on training scaffolds only; every reported
   statistic on validation or test scaffolds. The scaffold-disjoint split is the
   frozen 20/5/5 group structure.

### 3.5 Metrics

| Metric | Definition | Role |
|---|---|---|
| `oracle_selection_rate` | fraction of worlds where the true model wins among the five, by BIC and separately by validation R2 | **primary** |
| `false_structure_oracle` | on `mass_power` worlds, fraction where a descriptor model wins | **primary specificity** |
| `delta_r2_vs_mass` | validation R2 of the true model minus that of `M_mass` | detectability of any descriptor effect |
| `delta_r2_vs_rival` | validation R2 of the true model minus that of its nearest structured rival | separability of the *family* |
| `c_hat_over_se` | estimated coefficient divided by its standard error | signal-to-noise on the parameter |
| `lrt_p_true_vs_mass` | likelihood-ratio p-value, true against mass-only | |
| `lrt_p_true_vs_rival` | likelihood-ratio p-value, true against nearest rival | |
| `c_star` | smallest `c` at which `oracle_selection_rate >= 0.80` | **headline per family** |

Nearest structured rival, declared in advance: for `M_sat` and `M_exp` it is
`M_affine`; for `M_affine` it is `M_mass`; for `M_inter` it is `M_affine`.

Both selection criteria (BIC and validation R2) are reported. They are not
combined into a single number, and neither is chosen after seeing the results.

### 3.6 Case count and seeds

5 families x 5 coefficients x 4 noise levels x 2 energy grids x 50 replicates =
**10,000 worlds**.

Fifty replicates gives a standard error of at most 0.071 on any measured
proportion, adequate for decision thresholds set at 0.50 and 0.80.

Seeds derive from the `muru-v2-calibration|` namespace as in the A1 design,
section 5.

### 3.7 Decision criterion

Pre-declared, per `(family, c, noise, grid)` cell:

| Observation | Classification | Consequence |
|---|---|---|
| `oracle_selection_rate >= 0.80` | **IDENTIFIABLE** | G2 failures in this cell are attributable to the search. E4b/c/d are licensed for it. |
| `0.50 <= rate < 0.80` | **MARGINAL** | Attribution is ambiguous. No search-side change may be justified from this cell alone. |
| `rate < 0.50` | **WEAKLY IDENTIFIABLE** | G2 failures here are **not** attributable to search. No search-side change may cite this cell. |
| `false_structure_oracle > 0.10` on the `mass_power` control | **STUDY INVALID** | The oracle itself invents structure; its selection rates are uninterpretable and E3 must be redesigned before use. |

The `STUDY_INVALID` branch is a genuine abort condition, not a formality. An
oracle that picks descriptor models on mass-only truth would inflate every other
cell's rate.

**Where the frozen benchmark's coefficient distribution lies.** The frozen range
is `U(0.25, 0.55)`. A family classified WEAKLY IDENTIFIABLE across that whole
range is a family whose endpoint could not have been met by any engine, and that
is a finding about the benchmark, reported as such.

### 3.8 Cost

No symbolic search. Per world: one `Phi` fit, 180 `g_hat` grid searches, five
small least-squares fits. Measured basis: `rc5_estimate`'s per-compound scale
estimate is a grid search plus parabolic refinement, which v1 ran across 240
cases inside its normal execution.

| Item | Estimate |
|---|---|
| 10,000 worlds x under 1 CPU-second | **2 to 4 CPU-hours** |
| Storage | per-world coefficient and statistic rows, under 100 MB |

E3 is the cheapest experiment in the plan and the one with the highest decision
leverage. It should run first among the G2-side experiments, in parallel with E1.

### 3.9 What each outcome supports

| Outcome | Conclusion | Licensed change |
|---|---|---|
| Affine IDENTIFIABLE, saturating and exponential WEAKLY IDENTIFIABLE at frozen `c` | The G2 ceiling is partly a benchmark-construction fact. RC4's 57 generation failures split into a genuinely searchable part and an unreachable part. | Re-declare the family-recovery endpoint's population, or re-specify the unreachable families' coefficient magnitudes under the difficulty guard. **No search change licensed for those cells.** |
| Everything IDENTIFIABLE at frozen `c` | The signal is there and the search misses it. RC4 is a genuine search-generation failure. | E4b/c/d are fully licensed. The engine, not the benchmark, is the target. |
| Failures persist at zero noise (H_id_noise) | Structural closeness, not measurement error. | More energies, more compounds and lower noise will not help. Only a coefficient re-specification or an endpoint re-declaration can. |
| Failures resolve at 12 energies (H_id_geometry) | Acquisition geometry is a material constraint. | Feeds directly into the prospective benchmark's energy-grid design, which is a later authorised stage. |
| `c*` measured above the frozen range for a family | That family's planted magnitude is below the identifiability floor. | Same difficulty guard as E1 section 3.11: report `c*` as the primary result; change the planted magnitude only from an external scientific rationale, never from `c*` itself. |

---

## 4. Why E3 must precede E4 and E5

Without E3, every G2 remediation is uninterpretable in the same way v1's was.

- Increasing the search budget against a WEAKLY IDENTIFIABLE target buys nothing
  but compute, and any apparent gain is noise or false structure.
- Lowering parsimony against a WEAKLY IDENTIFIABLE target buys complex
  expressions that fit noise, which is precisely what G3 exists to punish.
- Adding `exp` to the grammar to rescue F18 is futile if the exponential is not
  separable from the affine form at the planted coefficient, and it imposes a
  false-structure cost on all eleven other families.

RC4's own risk note states this: "If the descriptor contribution is genuinely
below the identifiability floor at the planted coefficients, this is a
benchmark-construction issue and no search change will fix it."

E3 is the study that decides it.

---

## 5. E5: F18 and the exponential family, resolved prospectively

### 5.1 The specification contradiction

`discovery/grammar.py` `UNARY_OPERATORS` omits `exp` (DEVIATIONS_P3 D1). F18's
planted truth is `sqrt(mass) * exp(coefficient * descriptor / 3)`.
`g2_contract._contains_exp_of` requires a literal `sympy.exp` node. No
grammar-legal expression can carry one. Twelve of the 144 G2 cases had a success
probability of exactly zero before any search ran.

This is a governance defect as much as a technical one: a family was
preregistered into an endpoint that the preregistered grammar could not express.
Whatever v2 does, it must remove the contradiction rather than paper over it.

### 5.2 The options

| ID | Option | Removes contradiction | Notes |
|---|---|---|---|
| O1 | status quo | **no** | G2 capped at 132/144 by construction; endpoint stays mis-specified |
| O2 | admit `exp` unguarded | yes | reintroduces the overflow pathologies D1 excluded it for |
| O3 | admit domain-clipped `exp_p(x) = exp(clip(x, -B, B))`, with `NESTED_CONSTRAINTS["exp"] = {"exp": 0}` | yes | clipping makes a saturated `exp` a constant, which is a new false-structure channel that must be measured |
| O4 | admit `exp` only over a linear argument in a single primitive | yes | encodes the planted form in the grammar; presumptively rejected |
| O5 | remove F18 from the family-recovery population, denominator 144 to 132 | yes | governance-honest; shrinks the claim |
| O6 | keep the family, re-specify its coefficient so `exp` is separable from affine | yes | legitimate only under the difficulty guard |
| O7 | replace F18's truth with an algebraically difficult but grammar-expressible form preserving the family's scientific question | yes | preserves the endpoint's intent without an excluded operator |

### 5.3 Decision criterion: three ordered tests, and G2 rate is not one of them

**Test 1, coherence.** Does the option remove the contradiction between the
endpoint's required operator and the grammar's operator set? O1 fails and is
eliminated.

**Test 2, identifiability, decided by E3.** Is the exponential family separable
from its nearest rival at the truth's coefficient magnitude?

- If E3 classifies the exponential family **WEAKLY IDENTIFIABLE** at the frozen
  coefficient range, then O2, O3 and O4 are **futile**: adding the operator
  cannot make a search prefer a form that fits no better than a simpler rival.
  Only O5, O6 and O7 remain live.
- If E3 classifies it **IDENTIFIABLE**, the grammar question is real and O2, O3
  and O4 are evaluated on Test 3.

Section 2.2's arithmetic predicts the first branch. E3 decides it.

**Test 3, safety.** Measured `false_structure_rate` under the option, on
mass-only, null and adversarial worlds, from E6. Any option raising it above the
E6 ceiling is eliminated regardless of every other property.

**G2 success rate is reported for every option and ranks none of them.** That is
the operative sense of "do not choose based on making scores easier". An option
that raises G2 by making an impossible family possible is only admissible if it
passes coherence, identifiability and safety on their own terms.

### 5.4 Overflow evaluation, concretely

For O2, O3 and O4:

1. Enumerate the largest argument reachable by a grammar-legal expression at
   complexity at most 20 under the nested constraints, on the actual design
   matrix ranges (`mass ~ exp(5.55 + 0.25*latent + noise)`, so of order 100 to
   600; `descriptor` in `[0, 1]`; `distractor ~ N(0,1)`).
2. Measure the empirical rate of `grammar.finite_mask` rejection
   (`|value| >= 1e12`) per front row.
3. Measure the rate of `MAX_INVALID_FRACTION` (0.005) outright rejection.
4. Verify empirically the invariant `PROTECTED_SEMANTICS` already asserts:
   invalidity never improves a score. Under `exp` this is the invariant most
   likely to be stressed, and it must be tested rather than trusted.
5. For O3 specifically, measure how often the clip is active, since a saturated
   `exp_p` is a constant and a constant that wins is a false structure of a new
   kind.

### 5.5 Case count and cost

E5 rides on E4d's grammar arms plus a dedicated F18-analogue world set at E3's
coefficient ladder: 200 worlds x 30 seeds x 2.3 s ≈ **3.8 CPU-hours** per grammar
arm.

### 5.6 What each outcome supports

| Outcome | Conclusion |
|---|---|
| E3 says WEAKLY IDENTIFIABLE (predicted) | RC6 is a symptom. The real defect is that F18's planted coefficient makes its family unrecoverable in principle. The grammar is exonerated, D1's exclusion of `exp` stands, and the resolution is O5, O6 or O7. |
| E3 says IDENTIFIABLE and O3 passes safety | The grammar exclusion was the binding defect. Admit guarded `exp`, with the overflow instrumentation permanently on. |
| E3 says IDENTIFIABLE and no grammar option passes safety | The operator cannot be admitted safely. Resolve by O5 or O7. |
| O4 outperforms O3 | Expected, and it is evidence of encoding rather than of merit. O4 stays rejected; the margin is reported as the size of the encoding effect. |

---

## 6. Pre-registered predictions

| ID | Prediction |
|---|---|
| PE3-1 | `mass_affine_descriptor` is IDENTIFIABLE at all frozen coefficients and noise levels. |
| PE3-2 | `mass_exponential_descriptor` is WEAKLY IDENTIFIABLE across the whole frozen coefficient range, and remains so at zero noise. |
| PE3-3 | `mass_saturating_descriptor` is WEAKLY IDENTIFIABLE or MARGINAL at the frozen range, and becomes IDENTIFIABLE at `c = 2.2`. |
| PE3-4 | `false_structure_oracle` on `mass_power` worlds is below 0.10, so the study is valid. |
| PE3-5 | `mass_interaction` is MARGINAL, because the product of two `[0,1]` variables has materially lower variance than either. |
| PE3-6 | `c*` for the exponential family exceeds 2.2, that is, above the top of the tested ladder. |
| PE5-1 | Test 2 eliminates O2, O3 and O4, and F18's resolution is O5, O6 or O7. |

PE3-2 and PE5-1 are the strong claims. If they fail, the arithmetic in section
2.2 is missing something about how the `g_hat` estimator or the covariate
correlation structure interacts with the exponential form, and that would itself
be worth knowing.

---

**Terminal state for this document:** design only. No world generated, no
estimate computed, no option chosen.
