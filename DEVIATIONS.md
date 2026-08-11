# DEVIATIONS.md

Deviations from the master plan and from `PREREGISTRATION.md` recorded during
Phase 2. Phase 1 deviations D1–D6 live in
`PROPOSED_DEVIATION_FROM_MASTER_PLAN.md` and are not restated here.

Severity uses the project bug policy: BLOCKER / IMPORTANT / MINOR.

**D7 and D8 were identified from pre-registration diagnostics, before any
outcome model was fitted, and are reflected in the frozen pre-registration
rather than applied on top of it.** They are recorded here because they change a
method the master plan specified.

---

## D7 — The logit link is undefined on this response (IMPORTANT)

**Original criterion.** Master plan §9.2 specifies the core model on the logit
scale:

```
logit(mu_ij) = alpha_i + beta_i * h(E_j) + eps_ij
```

justified by "working on the logit scale to respect mu ∈ (0,1]".

**Why the data make it inappropriate.** mu is not confined to (0,1] in this
corpus. Measured on the 549-compound analysis population
(`artifacts/p2_prereg_diagnostics.json`):

| Quantity | Value |
|---|---|
| min mu | 0.09539 |
| max mu | **1.00000085** |
| rows with mu > 1 | **9** |
| rows with mu exactly 1 | 1 |
| rows with mu ≥ 1 − 1e−6 | 19 |

`logit(1) = +inf`, and `logit(x)` is undefined for `x > 1`. A Beta likelihood is
likewise undefined outside (0,1).

This is not a data defect. It is the same ppm-level effect Phase 1 documented as
deviation **D1**: RMassBank recalibrates masses, so the observed precursor m/z
can slightly exceed the declared `MS$FOCUSED_ION: PRECURSOR_M/Z` that forms mu's
denominator. Phase 1 measured
`max |1 − mz_observed/mz_declared| = 9.087e−06`, which bounds the excess exactly.
mu's excursion above 1 is real, correctly computed, and physically meaningless
at the 1e−6 level.

**Replacement criterion.** mu is modelled on the **natural scale**. Justifying
measurements:

- the response occupies [0.095, 1.0] — the lower bound is nowhere near active,
  so the compression a logit provides at 0 buys nothing here;
- per-energy SD ranges 0.153 to 0.215, a max/min ratio of **1.41** —
  heteroskedasticity is mild and does not motivate a variance-stabilizing link;
- every pre-registered metric (MAE, RMSE) is defined on natural-scale mu anyway,
  so a link would have to be inverted before evaluation, reintroducing the
  boundary problem at prediction time.

The alternative — clipping mu into (0,1) to make the link defined — was
rejected. It would silently edit 19 measured values to satisfy a modelling
convenience, which is the same failure mode Phase 1's D1 warned against when it
refused to snap peak masses onto the declared precursor m/z.

**Consequences.** None adverse. Predictions stay on the scale the metrics are
defined on. Coefficients become differences in mu rather than log-odds, which is
more directly interpretable. No Phase 2 claim depends on the link.

---

## D8 — The two-parameter linear energy form does not fit (IMPORTANT)

**Original criterion.** Master plan §9.2 models the energy response with a
per-compound intercept and a single slope, `alpha_i + beta_i * h(E_j)`, with `h`
"identity, log, or the fitted rescaling under test".

**Why the data make it inappropriate.** Fitted per compound on the 517 complete
trajectories, before any structure model existed:

| Form | median R² | 10th-percentile R² | fraction below R² 0.9 |
|---|---|---|---|
| logit(mu) linear in NCE | 0.824 | 0.615 | **69.8%** |
| logit(mu) linear in log NCE | 0.926 | — | **40.2%** |

A two-parameter form that fails to reach R² 0.9 on 70% of subjects in the plan's
own preferred parameterization is not describing the trajectory shape. log NCE
is better but still misses 40%.

**Replacement criterion.** **Energy is treated nonparametrically throughout
Phase 2**: as a 6-level factor in the structure-blind baselines B0/B1/B2, and as
a natural cubic B-spline basis in MASS FLEX, the Tier A model, and the flexible
benchmark. The energy grid is a designed 6-level factor, so a factor
representation is assumption-free and costs 5 degrees of freedom on 2,610 rows —
affordable.

The hierarchical model (HIER) retains a random slope in **centred energy**,
because its purpose is variance decomposition rather than trajectory
reconstruction, and a random slope there answers "how much do compounds differ
in energy response" without asserting that the response is linear.

**Consequences.** MASS FLEX becomes a genuinely strong competitor rather than a
straw man, which makes K4B harder to pass — the conservative direction. No
pre-registered claim changes.

---

## D9 — Duplicated compound-by-mode keys are averaged, not interleaved (MINOR)

**Original state.** Phase 1's `trajectory_stats` iterated records sorted by
energy without deduplicating. Six compound-by-mode keys map to two internal
MassBank IDs each (`DATA_CENSUS.md`; Phase 1 deviation D3, backlog M1), so those
trajectories were read as 12-point sequences with an energy reversal in the
middle.

**Why the change.** The unit of analysis for Phase 2 is the compound
(master plan §9.1). A compound must contribute one trajectory, not two
interleaved ones, or it is silently double-weighted and its energy ordering is
corrupted.

**Replacement.** The two records are averaged per (compound, energy) into a
single trajectory.

**Consequences.** Small and in Phase 1's favour. Recomputing Phase 1's headline
monotonicity under this rule raises mu from 437/517 (84.5%) to 443/517 (85.7%),
entropy from 27.9% to 28.2%, survival yield from 20.1% to 20.3%, and fragment
depth from 67.1% to 68.1%. Phase 1's published figures are therefore
**conservative**, and no Phase 1 conclusion changes. Phase 1 artifacts are
**not** edited; this is recorded as a Phase 2 methodological choice.

---

## D10 — Confirmation-set draw needs a size tolerance (MINOR)

**Original criterion.** Master plan §10.5: "20% of compounds, selected by
scaffold before any analysis".

**Why the data make it inappropriate.** Scaffold-group sizes are extremely
uneven: 322 singletons against one benzene group holding 80 compounds (14.6% of
the corpus). A plain "add scaffold groups until ≥ 20%" loop overshot to **157
compounds (28.6%)**, leaving only 392 compounds for development.

**Replacement criterion.** Walk groups in seeded random order and take each
unless it would push the set past **115% of the 20% target**. Every group stays
eligible (80 < 1.15 × 110), so large scaffolds are not systematically excluded
from the confirmation set — which would have left it unrepresentative of the
corpus's commonest chemistry.

**Result.** 110 compounds, **20.04%**, 82 scaffold groups; 439 development
compounds.

**Consequences.** None scientifically. Fixed before the pre-registration was
committed and before any model existed. Recorded because it is a construction
rule the master plan did not specify.

---

## D11 — Environment additions for Phase 2 (MINOR)

**Original criterion.** Master plan §25 lists PyMC ≥ 5.16 + ArviZ, numpyro,
lightgbm, joblib, rich, PyYAML, pydantic.

**What was actually installed.** `scikit-learn 1.9.0` and `statsmodels 0.14.6`,
added to `requirements.lock.txt`.

**What was deliberately not installed, and why.**

| Package | Reason |
|---|---|
| PyMC / ArviZ / numpyro | Instruction 14. mu has no censoring, n is ample, and all intervals come from a compound-level bootstrap. A probabilistic programming framework would add sampling-diagnostic and implementation risk without changing a Phase 2 answer. `statsmodels` MixedLM delivers the variance decomposition transparently. |
| lightgbm | `HistGradientBoostingRegressor` is adequate at this n, as the plan itself states. |
| PySR / Julia / gplearn / SymPy | Phase 3+ scope. Explicitly out of bounds for this session. |

**Consequences.** The variance decomposition is frequentist with bootstrap
intervals rather than posterior credible intervals. Stated in
`VARIANCE_DECOMPOSITION.md`.
