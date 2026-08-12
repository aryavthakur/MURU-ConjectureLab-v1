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

## D12 — Tier B feature floor and a reduced flexible-benchmark grid (IMPORTANT)

**Original criterion.** `PREREGISTRATION.md` §7 froze Tier B as Morgan radius-2
2048-bit fingerprints (1,823 bits ever set) plus a 26-descriptor RDKit block,
and §10 froze a 48-point hyperparameter grid
(`max_depth` 3 × `learning_rate` 2 × `max_iter` 2 × `min_samples_leaf` 2 ×
`l2_regularization` 2).

**Why it was changed.** Measured cost, not measured performance. A single
gradient-boosted fit on 2,610 rows × 1,850 features takes 15.6 s at
`max_iter=500, max_depth=None`. Nested CV at 48 grid points × 4 inner folds ×
5 outer folds is ~965 fits per split, ≈ 5 hours for three splits, before any
negative control — and the controls need hundreds of permutation replicates
each. The pre-registered configuration is not executable within this phase.

**Replacement criterion.** Two reductions, both fixed before any Phase 2
performance was observed:

1. **Fingerprint floor.** Retain Morgan bits set in **≥ 5 development
   molecules**: 1,823 → 692 bits, so Tier B is 719 features. The filter is
   computed from structures only and is **blind to mu**, so it cannot bias the
   comparison. Bits appearing in fewer than five molecules cannot support a
   generalizable split in a tree ensemble evaluated on held-out chemistry.
2. **Grid.** `min_samples_leaf` fixed at 20 and `l2_regularization` at 0.0,
   leaving `max_depth ∈ {3, 6, None}` × `learning_rate ∈ {0.05, 0.1}` ×
   `max_iter ∈ {200, 500}` = **12 points**. The two dropped axes are the two
   least influential for a dataset of this size.

**Direction of the effect.** Both reductions can only **weaken** the flexible
structure-aware benchmark. They therefore make **K4A and K4B harder to pass**,
which is the conservative direction: a structure claim surviving this
configuration is a stronger result, not a weaker one. Neither change was made
after seeing that performance disappointed, and the search space is **not**
enlarged later.

**Consequences.** The flexible benchmark estimates recoverable predictive
information under a slightly smaller pre-registered family than originally
frozen. It was never a ceiling (`MASTER_PLAN_CLARIFICATIONS` C2), and this
narrows it further; `FLEXIBLE_PREDICTIVE_BENCHMARK.md` states so explicitly.

---

## D16 — The negative-control adjudication rule was wrong, and is corrected (IMPORTANT)

**Original criterion.** `PREREGISTRATION.md` §15 specified one rule for all six
controls: "the observed statistic is compared against the 95th percentile of its
own matched permutation null", with Benjamini-Hochberg at q = 0.10 across the
family.

**Why it is wrong.** The six controls belong to two families that ask *opposite*
questions, and a single rule cannot serve both.

- **Destruction controls (NC1–NC3).** Permutation is applied to the real
  structure and the question is whether signal *survives destruction*. The
  object under test is the **null distribution itself**. The real-data statistic
  exceeding that null is the **desired** outcome — it confirms the permutation
  worked. Comparing "observed vs null p95" here asks a question with no
  scientific content.
- **Nuisance controls (NC4, NC6, NC7).** The observed statistic *is* the
  nuisance predictor's own performance, and it must sit inside its own null.
  Here "observed vs null p95" is exactly right.

The first implementation compounded the error with an inversion: it computed
`p = fraction of null replicates beating B1` and then treated a **small** p as
evidence that a control had fired. That is backwards. NC1 produced
`p = 0.000` — meaning **no** permuted replicate beat the baseline, a control
passing perfectly — and was reported as firing and as a BLOCKER. The same
inversion hid the one control that genuinely does fire.

**Replacement criterion.**

- Destruction controls fire if the null's 95th percentile retains more than
  **10%** of the real structural effect (`b1_mae - tierA_mae`). Measured: NC1
  −35.9%, NC2 −0.5%, NC3 +2.2%. All pass with wide margin.
- Nuisance controls fire if the observed statistic exceeds its own null 95th
  percentile, with BH at q = 0.10 across that family of three. Measured: NC4 and
  NC6 pass; **NC7 (retention time) fires**, observed +0.01006 against a null p95
  of +0.00021, p = 0.

**Direction.** The correction is conservative in both directions at once: it
stops three passing controls from being misreported as blockers, and it surfaces
a real firing control the original rule concealed.

**Consequences.** NC7's firing is adjudicated in `PHASE2_DECISION.md` under the
pre-registered "BLOCKER until explained" clause, with the explanation resting on
a pre-specified test — the incremental gain from adding RT to Tier A — judged
against the same 10% magnitude limit, so no new threshold was invented.

---

## D15 — Negative-mode replication folded into the verdict rule (MINOR)

**Original criterion.** `PREREGISTRATION.md` §22's decision table conditions
`GO TO PHASE 3` on K4A, K4B, K5, the secondary splits S1/S3, and the raw-branch
check. It does not mention the negative-mode replication that §18
pre-registered.

**Why it is inadequate.** §18 pre-registered negative mode explicitly "to
establish whether the qualitative conclusion replicates". Omitting it from the
verdict rule would let Phase 2 report an unqualified `GO` while a pre-registered
replication check had failed — which is exactly what happened: negative-mode
K4A passes but **K4B fails** (+1.93% against the 5% minimum, scaffold interval
spanning zero).

**Replacement criterion.** Negative-mode disagreement is folded into the
`RESTRICT` condition alongside secondary-split and raw-branch disagreement.

**Direction.** This can only make the verdict **more** conservative, never less.
It cannot turn a STOP into a GO, and it cannot manufacture a positive result.

**Consequences.** The verdict is `RESTRICT AND GO TO PHASE 3` rather than
`GO TO PHASE 3`, with the negative-mode non-replication stated as a binding
restriction.

---

## D14 — Execution redesign of the baseline ladder (IMPLEMENTATION ONLY)

**This deviation changes no science.** No pre-registered model, split, metric,
hyperparameter value, threshold or decision criterion is altered. It is recorded
here for transparency because it changes how the pre-registered experiment is
executed.

**What went wrong.** The first execution of `scripts/t2_05_baselines.py` ran for
**2 hours 8 minutes** without completing and was terminated. Diagnosis, from
read-only inspection while it ran:

| Symptom | Measurement |
|---|---|
| CPU burned on contention, not work | 3-second process sample: **22** stack frames in `Splitter.find_node_split` / `compute_histograms_brute` against **234** in wait primitives |
| Oversubscription | 18 threads, 590–674% CPU, load average 11.79 on 8 cores |
| Memory waste | RSS grew 290 MB → 462 MB; `nested_cv` returned test-fold slices carrying all ~718 Tier B feature columns, and ~30 such frames were accumulated before trimming at write time |
| No observability | stdout piped to `tail`, which buffers until exit; no checkpoint, so no progress signal existed on disk and proximity to completion was unmeasurable |
| Nothing recoverable | termination discarded 100% of the computation |

**Changes made, all response-blind.**

1. **Thread caps.** `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
   `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS` and `NUMEXPR_NUM_THREADS` are set
   to **4** before numpy/sklearn import, matching the four performance cores.
2. **Concurrent fits: 1.** Fits run sequentially. A single fit already uses four
   threads efficiently, and parallel worker processes would multiply the
   ~650 MB footprint against a machine already under memory pressure.
3. **Prediction frames trimmed at source.** `nested_cv` projects to
   `PRED_COLS` before returning, so accumulating 30 frames costs ~1 MB instead
   of ~450 MB. Projection only; no value is altered.
4. **Incremental checkpoints.** Each (split, model) unit is written to
   `artifacts/p2_ckpt/{split}__{model}.parquet` the moment it completes.
5. **Resumable.** A unit whose checkpoint exists is loaded rather than refitted,
   so an interruption costs at most the unit in flight.
6. **Progress visible.** The `| tail` arrangement is removed and every unit
   prints on completion with `flush=True`.

**Proof that the optimization is scientifically inert.**
`scripts/t2_05a_runtime_budget.py` fits the most expensive grid point
(`max_iter=500, max_depth=None`) at 1, 2 and 4 threads and compares the
resulting predictions:

```
max |1 thread - 2 threads| = 0.0     bitwise identical: True
max |1 thread - 4 threads| = 0.0     bitwise identical: True
```

Thread count does not change the fitted result, so the cap changes cost and
nothing else. Checkpointing, column projection and progress printing cannot
affect a fitted value by construction.

**Runtime budget computed before relaunch — and it was wrong.** BACKLOG I4 now
requires such a budget before every expensive experiment. The first one produced
under that rule contained an arithmetic error, which is recorded here rather
than quietly corrected, because the failure mode is instructive.

| Quantity | Projected (wrong) | Actual |
|---|---|---|
| Fits per flex unit | 53 = 12 grid × 4 inner + 5 outer | **245** = 5 outer × (12 grid × 4 inner) + 5 |
| Total gradient-boosted fits | 371 | **1,715** |
| Per flex unit | 106.3 s | **667–748 s** observed |
| Projected wall time | 14.5 min (21.7 min with contention) | **~95 min** |

**The error.** The inner hyperparameter loop runs *inside each outer fold*, so
its cost multiplies by the number of outer folds. The projection added the two
loops instead of nesting them, understating the job by a factor of five. The
per-fit benchmark itself was accurate — 24.06 s for a 12-point grid on one inner
fold — and correct arithmetic against that same measurement gives ~491 s per
unit, within contention distance of the 667–748 s observed.

**Corrected rule for future budgets.** Compute the fit count from the loop
structure explicitly — `outer_folds × grid_points × inner_folds + outer_folds`
per unit — and state it as a formula in the budget rather than a bare number, so
the nesting is visible and checkable.

**Why the rerun was allowed to continue past its stated limit.** The user's
45-minute limit applied to the pre-launch projection. When the true cost became
apparent at 46 minutes with 17 of 30 units complete, the run was reported
immediately and continued on the user's explicit instruction. Continuing carried
no risk to the work: because of change 4 above, every completed unit was already
on disk and an interruption at any point would have cost only the unit in
flight.

| Quantity | Value |
|---|---|
| Measured cost, 12-point grid on one inner fold, 4 threads | 24.06 s |
| Projected peak RSS | ~700 MB (measured 649 MB single fit; 388–674 MB observed in the rerun) |
| Threads per fit / concurrent fits | 4 / 1 |

**Consequences.** None scientific. The rerun executes the identical
pre-registered experiment.

---

## D13 — Negative controls use fixed hyperparameters (MINOR)

**Original criterion.** `PREREGISTRATION.md` §15 specifies 200 permutation
replicates per negative control; §12 specifies nested grouped CV with inner
hyperparameter selection.

**Why it was changed.** Nested selection inside every permutation replicate is
200 × 12 × 4 × 5 fits per control — computationally impossible, and
statistically pointless: a permutation null needs the *same* estimator applied
to permuted data, not a re-tuned one. Re-tuning per replicate would make the
null distribution reflect search variance rather than the mechanism under test.

**Replacement criterion.** Each control fixes the estimator's hyperparameters at
the modal configuration selected by the real run's inner loops, and applies that
frozen estimator identically to the observed and permuted data.

**Consequences.** The null is a permutation null for a fixed estimator, which is
the standard and correct construction. Stated in `NEGATIVE_CONTROLS_P2.md`.

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
