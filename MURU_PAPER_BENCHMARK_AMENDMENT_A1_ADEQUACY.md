# MURU paper benchmark — Amendment A1: model adequacy decision rule

## A1.0 Amendment record

| Field | Value |
|---|---|
| Amendment | A1 — model adequacy decision rule |
| Original content freeze | `d94d2c9` ("Prepare prospective paper benchmark content freeze") |
| Original freeze designation | BENCHMARK CONTENT FREEZE V1, preserved permanently and unmodified |
| Branch | `science/muru-paper-benchmark-adequacy-amendment`, created from `d94d2c9` |
| Contract version | `paper-benchmark-adequacy-1.0.0` |
| Effective content freeze | the commit introducing this document, tagged `benchmark-content-freeze-a1` |

**Reason for amendment.** A pre-execution governance review found that content
freeze V1 defines M0 and the M1/M2/M3 generative alternatives but never binds
the rule that converts their fits into `M0 REJECTED` or `M0 NOT REJECTED`.
`MURU_PAPER_BENCHMARK_METRICS.md` makes "no M0 rejection" a necessary component
of G1, and G1 is a necessary gate for the sole primary paper claim, so the gap
propagates directly into the primary claim. The design document states only that
the ladder "compares M0 with M1, M2, and M3 using the same held-out compound
split"; it names no statistic, no threshold, no aggregation, and no failure
semantics. This is a specification gap, not an error in any frozen scientific
object.

**Contamination status.** No Development scientific outcome and no Held-out
outcome was executed, scored, enumerated, parsed, summarised, or inspected in
preparing this amendment. The row-level `inputs/*.jsonl` and `truth/*.jsonl`
artifacts are untracked regenerable bytes under `.gitignore`; they were not
present in, generated in, or read from the amendment worktree. Only the
specification documents, the registry, generator source, model definitions, the
protocol adapter, frozen scientific constants, and the existing tests were read,
plus mechanical byte hashing of already-frozen tracked artifacts.

**Scientific change.** Binding of the previously unspecified M0/M1/M2/M3
adequacy decision rule, and nothing else.

**Historical benchmark changes.** None beyond this prospective rule completion.
No case generator, truth, seed, coefficient, partition, family population,
endpoint denominator, G1/G2/G3 threshold, or held-out scientific artifact is
altered. `d94d2c9` is not rewritten.

**Precedence.** This amendment does not weaken any frozen refusal. The held-out
guard remains `PENDING_LOCK`; A1 does not authorise held-out execution, and does
not authorise Phase 4.

---

## A1.1 Scope

A1 binds exactly the five decisions the governance review identified:

1. the M0-vs-Mk comparison statistic;
2. identifiability and extra-parameter treatment;
3. the rejection threshold;
4. compound-to-case aggregation;
5. missing-energy and boundary handling.

Everything else in the benchmark is untouched. A1 owns the scientific decision
contract only. It does not implement the production adequacy fitter; Engineering
RC 2 consumes this contract afterwards.

The adequacy rule is executed for every case whose frozen applicable endpoint
set contains `m0_specificity` or any of `m1_sensitivity`, `m2_sensitivity`, or
`m3_sensitivity`. For cases where none of those endpoints applies — F19C and
F20A–F20C — adequacy is not an applicable endpoint and any computed value is
descriptive only.

---

## A1.2 Model definitions

The frozen M0 definition is preserved exactly. M0 remains the shared
horizontal-scaling model

```
mu_i(E) ~= Phi(E / g_i)
```

fitted with the already-frozen training-only `Phi` and fold-local chronology
prescribed by the frozen execution boundary: all shared objects are fitted from
training trajectories only, then frozen, and each test compound is estimated
independently against them.

### Training-side objects (frozen, never refitted per compound or per fold)

A1 introduces no new training-side fitting. It names the objects the frozen
training-only `Phi` already implies, so that a horizontal-scaling model can be
evaluated away from the six grid energies:

| Object | Definition |
|---|---|
| `Phi` | the frozen training-only profile function, with its frozen support, normalisation, residual weighting, constants, and profile bounds |
| `A_LO` | the low-argument plateau of `Phi`, i.e. `Phi` evaluated under its frozen extrapolation rule as its argument tends to zero |
| `A_HI` | the high-argument asymptote of `Phi`, under the same frozen extrapolation rule |
| `S(t)` | the normalised shape `S(t) = (Phi(t) - A_HI) / (A_LO - A_HI)`, clipped to `[0, 1]` |

`S` is monotonically non-increasing with `S(0) = 1` and `S(inf) = 0`. `Phi`'s
evaluation away from the grid, including its extrapolation rule, is a frozen
deterministic property of the locked implementation, fixed before any test
compound is touched. If `A_LO - A_HI < MIN_VERTICAL_AMPLITUDE` the case is a
`CONTRACT_FAILURE`: the frozen profile carries no usable vertical span and no
adequacy contrast is defined.

### The four models

`E_REF = 45.0` is the frozen generator horizontal normalisation energy
(`u = (E / 45) / g` in `generator._response_matrix`). Each Mk adds exactly one
compound-specific deviation degree of freedom in addition to M0's
compound-specific `g`, and each reduces to M0 exactly at the stated value.

| Model | Deviation | Prediction | Reduces to M0 when | Frozen generative source |
|---|---|---|---|---|
| **M0** | none | `mu_i(E) = A_HI + (A_LO - A_HI) * S(E / g_i)` | — | shared branch: `mu = mu_inf + (1 - mu_inf) * exp(-u**phi_p)` |
| **M1** | horizontal shape | `mu_i(E) = A_HI + (A_LO - A_HI) * S(E_REF * (E / (E_REF * g_i))**s_i)` | `s_i = 1` | kinds `no_scalar`, `m1_horizontal`: the shape exponent `phi_p` is scaled per compound |
| **M2** | high-energy vertical / asymptotic | `mu_i(E) = a_i + (A_LO - a_i) * S(E / g_i)` | `a_i = A_HI` | kind `m2_high_energy`: a compound-specific floor replaces `mu_inf` |
| **M3** | low-energy vertical | `mu_i(E) = A_HI + (b_i - A_HI) * S(E / g_i)` | `b_i = A_LO` | kind `m3_low_energy`: a compound-specific ceiling replaces the unit low-energy plateau |

Each form is the exact `Phi`-agnostic transcription of the corresponding frozen
generative deviation. For M1, the generator's `exp(-(u**(phi_p * s)))` equals
`F(u**s)` where `F` is the M0 profile in the normalised coordinate, which is the
power warp written above. For M2 and M3, the generator substitutes a
compound-specific vertical endpoint into the frozen two-endpoint profile, which
is the affine rescaling of `S` written above.

No additional alternatives exist. The ladder is exactly M0 versus M1, M2, M3.

### Frozen fitting parameterisation and bounds

| Model | Free parameters | Scale | Lower | Upper |
|---|---|---|---|---|
| M0 | `log_g` | natural log | `-2.0` | `+2.0` |
| M1 | `log_g`, `log_shape` | natural log | `-2.0`, `-ln 2` | `+2.0`, `+ln 2` |
| M2 | `log_g`, `a` | natural log, response | `-2.0`, `MU_FLOOR` | `+2.0`, `A_LO - MIN_VERTICAL_AMPLITUDE` |
| M3 | `log_g`, `b` | natural log, response | `-2.0`, `A_HI + MIN_VERTICAL_AMPLITUDE` | `+2.0`, `MU_CEIL` |

with frozen constants `MU_FLOOR = 1e-4`, `MU_CEIL = 1 - 1e-4`,
`MIN_VERTICAL_AMPLITUDE = 0.05`, `ln 2 = 0.6931471805599453`.

Provenance of every bound, none of which was chosen from an outcome:

- `log_g in [-2, +2]` is inherited unchanged from the already-frozen
  training-side scalar support (`protocol.FrozenScalarObjects.support`). A1 does
  not widen or narrow it.
- `log_shape in [-ln 2, +ln 2]` admits a horizontal warp of up to a factor of
  two in either direction and is symmetric in log space, so neither direction of
  M1 deviation is favoured.
- `MU_FLOOR` and `MU_CEIL` are the frozen generator response clip
  (`mu = np.clip(mu, 1e-4, 1 - 1e-4)`), reused as the admissible response range.
- `MIN_VERTICAL_AMPLITUDE = 0.05` is the smallest vertical span for which the
  normalised shape stays numerically conditioned given that clip. It keeps the
  M2 and M3 models identifiable and non-degenerate.

These bounds are permissive supersets of the frozen generative ranges, not tight
fits to them, and are derived from frozen generator and protocol constants as
the instruction to use the frozen generator/model definitions as the source of
model meaning requires. They may not be loosened to rescue any case.

### Frozen search protocol

The fit objective is the unweighted sum of squared residuals on the `mu`
response scale over the energies in the fold — the maximum-likelihood choice
under the frozen additive-Gaussian noise mechanism. The search is identical for
every model so that no model receives a better-optimised fit than its
competitor:

- for M2 and M3 the deviation parameter enters linearly given `g`, so it is
  solved in closed form and clipped to its bounds, which is the exact
  constrained minimiser of a convex quadratic on an interval;
- every remaining free dimension is searched by the same deterministic
  coarse-to-fine grid: a coarse uniform grid inclusive of both endpoints
  (81 points for `log_g`, 29 points for `log_shape`), then
  `REFINEMENT_ROUNDS = 3` rounds of a 21-point grid per dimension centred on the
  current best with half-width equal to the previous step and step shrunk by a
  factor of 10, clipped to the bounds;
- ties in the objective resolve to the lexicographically smallest parameter
  vector in the frozen dimension order.

The scheme uses no random restart, no library optimiser, and no data-dependent
initialisation, so two conforming implementations reach the same estimate.

---

## A1.3 Extra-parameter treatment: within-compound leave-one-energy-out

In-sample fits are **not** compared. Because M1, M2, and M3 each add one
compound-specific parameter, an in-sample loss comparison is structurally biased
toward the alternative. The prospective treatment of that extra parameter is
within-compound leave-one-energy-out (LOEO) prediction. No information-criterion
or parameter-count penalty is added.

For every eligible test compound `i` with observed energy set `E_i`, and for
each observed energy `e` in `E_i`:

1. omit `e`;
2. fit the M0 compound-specific parameter using the other observed energies,
   keeping all training-side `Phi`, `S`, `A_LO`, `A_HI`, support, normalisation,
   weighting, and constants frozen;
3. predict `mu_i(e)`;
4. independently fit Mk using exactly the same remaining energies and exactly
   the same frozen training-side objects;
5. predict `mu_i(e)`.

Repeated for every observed energy. Constraints:

- the omitted energy may not influence either fit used to predict it;
- no test compound may influence another test compound, extending the frozen
  per-compound independence canary to adequacy;
- validation compounds are not used; the adequacy population is the 30 test
  compounds of the case;
- M0 and Mk see the identical fold, the identical energies, and the identical
  frozen training-side objects.

---

## A1.4 Compound-level comparison statistic

For each eligible compound `i`, on the `mu` response scale and over exactly the
same observed energies for both models:

```
MAE_0,i = mean over e in E_i of |mu_i(e)_observed - mu_i(e)_LOEO-predicted under M0|
MAE_k,i = mean over e in E_i of |mu_i(e)_observed - mu_i(e)_LOEO-predicted under Mk|
```

Mean absolute LOEO prediction error is used, never a training loss.

**Practical win.** Compound `i` is a practical win for Mk if and only if

```
MAE_0,i > 0    and    MAE_k,i <= 0.90 * MAE_0,i
```

so the alternative must improve out-of-energy prediction by at least 10%.

**Frozen floating-point comparison and tolerance semantics.** All quantities are
IEEE-754 binary64. The right-hand side is the binary64 multiplication of the
binary64 literal `0.90` by `MAE_0,i`. The comparison is the binary64 `<=`
operator. No epsilon is added or subtracted, and no rounding, quantisation, or
relative-tolerance helper is applied. Consequences, all deterministic:

- an exact tie `MAE_k,i == MAE_0,i > 0` fails the test, because
  `MAE_0,i > 0.90 * MAE_0,i`, so exact ties are never alternative wins;
- when `MAE_0,i == 0.0` — M0 already predicts every omitted energy exactly —
  there is no 10% margin to win and the compound can never be a practical win,
  including when `MAE_k,i` is also exactly zero. This resolves the degenerate
  case in the direction that is conservative toward M0 rejection;
- a non-finite `MAE` is `NUMERICAL_FAILURE`, never a win and never a loss;
- a negative `MAE` is impossible by construction and is a `CONTRACT_FAILURE`.

---

## A1.5 Case-level aggregation

The frozen test population is 30 test compounds per case (5 test scaffold groups
of 6 compounds each, from the frozen generator split).

For each M0-vs-Mk contrast, count the compounds that are practical wins for Mk.
**A case-level Mk detector fires if and only if both hold:**

- **A.** at least **24 of 30** test compounds are evaluable for that contrast;
  and
- **B.** at least **20** test compounds are practical wins for Mk.

**Population contract.** If more than 30 test compounds appear, that is a
`CONTRACT_FAILURE`, not permission to alter the threshold. If fewer than 30
appear because of the frozen benchmark structure itself, stop and report a
registry inconsistency.

### Mathematical rationale for 20 of 30

Under an equal-probability directional null — the alternative is as likely to
predict an omitted energy better as worse, with no systematic advantage:

```
P[X >= 20 | X ~ Binomial(30, 0.5)] = 0.049369 ~= 0.0494
```

The fixed absolute count of 20 never becomes more permissive as evaluability
drops. Across the admissible evaluable range the same directional-null tail is:

| evaluable | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
|---|---|---|---|---|---|---|---|
| `P[X >= 20]` | 0.00077 | 0.00204 | 0.00468 | 0.00958 | 0.01785 | 0.03071 | 0.04937 |

so 0.0494 is the upper bound on the directional-null false-fire rate over every
admissible evaluable count. The separate 10% error-reduction requirement of
A1.4 supplies the practical-effect margin, so numerically trivial advantages do
not count as wins. The two requirements are conjunctive: statistical consistency
of direction and a practical effect size.

---

## A1.6 M0 rejection

For an evaluable case:

- **M0 is REJECTED** if **any** of M1, M2, or M3 fires.
- **M0 is NOT REJECTED** only if **all three** required contrasts are evaluable
  **and none** of M1, M2, M3 fires.

Model fit failure, timeout, insufficient data, boundary limitation, and
numerical failure are **never** evidence for M0. They produce an indeterminate
adequacy state, never M0 acceptance. A firing detector still rejects M0 even
when another contrast is indeterminate: rejection is evidence, indeterminacy is
not.

---

## A1.7 Detector-specific sensitivity

Detector identity is preserved. For the frozen M1 sensitivity endpoint, success
means **M1 fires**; for M2 sensitivity, **M2 fires**; for M3 sensitivity,
**M3 fires**. A wrong alternative firing may reject M0, but does not count as
successful identification for the correct detector-specific endpoint.

For F16, multiple alternatives may legitimately fire, and each detector-specific
endpoint is scored independently according to its frozen applicability.

The M0 specificity endpoint succeeds only on a case whose adequacy status is
`M0_NOT_REJECTED`.

Frozen denominators, reconstructed from the registry and unchanged by A1:

| Endpoint | Applicable families | Held-out denominator |
|---|---|---:|
| M0 specificity | F01–F05, F07–F12, F17–F18, F19A–F19B | 164 |
| M1 sensitivity | F06, F13, F16 | 36 |
| M2 sensitivity | F14, F16 | 24 |
| M3 sensitivity | F15, F16 | 24 |

**Recorded observation, no change made.** F16's frozen registry applicability
includes `m3_sensitivity`, while the frozen `combined_violation` generator
introduces a horizontal shape term and a high-energy floor term. A1 does not
alter that applicability or the 24-case M3 denominator, and does not use any
outcome to reconsider it. It is recorded here so the M3 sensitivity report is
read against its frozen construction rather than as a silent A1 decision.

---

## A1.8 F04 missing-energy handling

F04 contains compounds with one of six energies missing.

- A compound remains adequacy-evaluable if it has at least **5 observed distinct
  energies**. With five observed energies each LOEO fold fits on four and
  predicts the fifth.
- With fewer than five observed energies the compound status is
  `INSUFFICIENT_DATA` for adequacy.
- The missing energy is **not** imputed. No other compound's response is
  borrowed. The denominator is never changed silently: every compound status is
  counted and reported.
- The case still requires at least 24 evaluable test compounds for **each**
  required contrast.

---

## A1.9 F05 boundary handling

A parameter estimate that reaches a frozen admissible fitting boundary is
explicitly recorded. Boundary contact is evidence for neither M0 nor an
alternative.

- **Boundary contact** — a fitted free parameter equals one of its frozen bounds
  to within `BOUNDARY_CONTACT_TOL = 1e-9` in that parameter's own scale.
- **Unresolved boundary** — boundary contact where the fit still wants to leave
  the admissible region: displacing the parameter outward by
  `BOUNDARY_OUTWARD_PROBE = 1e-3` in its own scale strictly reduces the
  objective. The constrained optimum is a corner solution, not an interior
  optimum that happens to coincide with a bound.
- **Resolved boundary contact** is recorded but does not disqualify the
  compound; the fit is usable.

A compound whose required LOEO fits under M0 or Mk cannot produce a valid finite
prediction without relying on an unresolved boundary condition is
`BOUNDARY_LIMITED` for that contrast, and is counted as neither a practical win
nor a loss. It is therefore not evaluable.

If at least 24 of 30 compounds remain fully evaluable, the case-level adequacy
decision is performed on those valid compounds, with all boundary counts
reported. If fewer than 24 remain, the case adequacy status is
`BOUNDARY_LIMITED` and M0 cannot be recorded as not rejected for G1.

Parameter bounds may not be loosened to rescue F05.

---

## A1.10 Failure semantics

Case-level adequacy statuses, exhaustive:

| Status | Meaning |
|---|---|
| `M0_NOT_REJECTED` | all three contrasts evaluable, none fires |
| `M0_REJECTED_M1` | exactly M1 fires |
| `M0_REJECTED_M2` | exactly M2 fires |
| `M0_REJECTED_M3` | exactly M3 fires |
| `M0_REJECTED_MULTIPLE` | more than one alternative fires |
| `INSUFFICIENT_DATA` | a required contrast falls below the evaluability floor, dominated by too few observed energies |
| `BOUNDARY_LIMITED` | a required contrast falls below the floor, dominated by unresolved boundary contact |
| `NUMERICAL_FAILURE` | a required contrast falls below the floor, dominated by non-finite results |
| `MODEL_FIT_FAILURE` | a required contrast falls below the floor, dominated by fits that did not converge |
| `TIMEOUT` | a required contrast falls below the floor, dominated by fits that exceeded the frozen runtime budget |
| `CONTRACT_FAILURE` | the population, the record set, or the frozen profile violates the contract |

Compound-level statuses within one contrast: `PRACTICAL_WIN`,
`NO_PRACTICAL_WIN`, `INSUFFICIENT_DATA`, `BOUNDARY_LIMITED`,
`NUMERICAL_FAILURE`, `MODEL_FIT_FAILURE`, `TIMEOUT`. Only `PRACTICAL_WIN` and
`NO_PRACTICAL_WIN` are evaluable.

**Compound precedence**, applied in this order: structural data adequacy first,
because a compound below the five-energy floor is never fitted at all; then
execution state; then unresolved boundary contact; then numerical validity; then
the practical-win comparison.

**Case indeterminate precedence.** When no detector fires and at least one
required contrast is below the floor, the case is reported under the most severe
non-evaluable cause present, in the order `CONTRACT_FAILURE`, `TIMEOUT`,
`MODEL_FIT_FAILURE`, `NUMERICAL_FAILURE`, `BOUNDARY_LIMITED`,
`INSUFFICIENT_DATA`, so an execution failure can never hide behind a declared
structural limitation. Every compound status count is reported regardless of
which one names the case.

`TIMEOUT` is declared by the locked engine under the runtime budget frozen at
executable freeze. A1 does not set that budget; it binds only that a timeout can
never become M0 acceptance.

**A non-success execution state cannot silently become M0 acceptance.**

---

## A1.11 G1 interaction

The frozen G1 gate is preserved. A case satisfies the adequacy component of G1
only if its adequacy status is `M0_NOT_REJECTED`. Any indeterminate or failure
state leaves G1 unsatisfied. `CaseOutcome.m0_accepted` may be populated only
through `analysis.m0_accepted_from_adequacy`.

Unchanged by A1:

- `Spearman(log g_hat, log g) >= 0.80`;
- trajectory MAE `<= 0.80` of the per-energy baseline MAE;
- the G1 Wilson lower-bound threshold `>= 0.70`;
- the 164-case G1 denominator, and the G2 and G3 gates in full.

---

## A1.12 Contract tests

`tests/test_paper_benchmark_adequacy.py` verifies the decision logic using
constructed outcome records only. It runs no Development or Held-out benchmark
outcome and materialises no case. Coverage includes: 19 wins of 30 does not
fire; 20 of 30 fires; 20 wins with 23 evaluable is indeterminate rather than
firing or accepting; 24 evaluable with 20 wins fires; no detector firing with
all contrasts evaluable gives `M0_NOT_REJECTED`; M1-, M2-, and M3-only
rejections; multiple alternatives; model fit failure, timeout, insufficient
data, and sub-floor boundary limitation each failing to produce M0 acceptance; a
five-energy F04 compound evaluable and a four-energy compound
`INSUFFICIENT_DATA`; the practical-win threshold, exact ties, and the zero-error
degenerate case; population contract violations; detector identity under a wrong
alternative firing; independent scoring of the F16 detectors; the frozen
denominators; the binomial rationale and its monotonicity; the frozen
parameterisation, bounds, and search protocol; and the absence of any
information-criterion penalty.

---

## A1.13 Effective content freeze

- **ORIGINAL BENCHMARK CONTENT FREEZE V1 = `d94d2c9`**, preserved permanently
  and byte-identical for every artifact unrelated to the adequacy rule.
- **EFFECTIVE BENCHMARK CONTENT FREEZE = the commit introducing this
  amendment**, on branch `science/muru-paper-benchmark-adequacy-amendment`,
  tagged `benchmark-content-freeze-a1`.

`artifacts/paper_benchmark_amendment_a1.json` carries the per-path SHA-256
integrity manifest: the allowed changed paths and every unchanged protected
benchmark path, verified against the `d94d2c9` blobs. The A1 commit, not
`d94d2c9` alone, is the benchmark contract supplied to Engineering RC 2 and to
subsequent executable integration.
