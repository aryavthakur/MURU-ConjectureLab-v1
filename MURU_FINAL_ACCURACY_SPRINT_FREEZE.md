# MURU FINAL ACCURACY SPRINT — DESIGN FREEZE

**Written BEFORE any scored comparison.** Every candidate-side feature definition,
every architecture variant, every hyper-parameter grid and both gate forms are
fixed here. Nothing below may be added, widened or re-specified after an
outer-fold number is seen.

Baseline under test: `MURU_ACCURACY_OPTIMIZATION.md` (branch
`claude/muru-accuracy-optimization-bd5982`, commit `465dff9`) =
**B2 family vote + R1 representative + two-quantity gate**, on the 323-world x
30-seed development surface, 26,600 Pareto-band candidates.

The genuinely fresh independent holdout is NOT touched by this task. No
fresh-holdout world is generated, read, scored or planned against here.

---

## 1. Data surface

* `artifacts/ov_ckpt` — 9,690 existing PySR seed-runs, read-only.
* `artifacts/accopt/candidate_cache.json` — 323 worlds, 26,600 band members,
  structural signature + family cluster + (evaluation-only) truth fields.
* World data rebuilt deterministically from `muru.objval.generators2` +
  `muru.discovery.protocol.build_world_data`; identical splits to the search run
  (`train` 263 / `valid` 88 / `test` 88 for real-covariate worlds).
* The world `test` split is used by NOTHING in this study.

Populations: positives = G1A(6) + G1B(40) + G1C(10) = 56.
nulls = NCAL(100) + G4(100) + G4M(30) = 230. refusal = G2,G3,G5,GC,GRT = 37.

---

## 2. Candidate-side feature cache — definitions

All features below are computed from candidate structure and world data only.
No truth field is an input to any of them.

### 2.1 FEATURE GROUP 1 — deterministic constant refit

For each band member expression `E`:

1. Parse with the frozen `muru.discovery.grammar.parse`.
2. **Free constants** = the distinct `sympy.Float` atoms of `E` that do NOT occur
   as the exponent argument of any `Pow`. Every `Integer`, `Rational` and every
   `Pow` exponent is STRUCTURAL and is preserved exactly (this keeps
   `sqrt`/`square`/`cube`/`inv` and all integer/rational exponents frozen).
3. Each distinct free-constant VALUE becomes one free scalar parameter; repeated
   occurrences of the same value are tied to one parameter.
4. Fail closed — `refit_ok = false`, original quality retained — when:
   * there are 0 free constants, or
   * there are more than 10 free constants, or
   * `lambdify` of the parameterised structure raises, or
   * the optimizer does not report success, or
   * the refitted expression exceeds the frozen `MAX_INVALID_FRACTION = 0.005`
     on the validation split.
5. Refit: `scipy.optimize.least_squares`, method `trf`, `x0` = the original
   fitted values, `max_nfev = 200 * n_params`, `xtol = ftol = gtol = 1e-10`,
   residual `sqrt(w) * (y - E(X;theta))` on the world **TRAIN** split only,
   invalid points charged a penalty of `sqrt(w) * 3 * sd(y_train)`. Fully
   deterministic; no random restarts.
6. Evaluate ONLY on the world **VALID** split, with the frozen
   `engine.score_candidate` semantics (weighted R^2, invalid points excluded and
   charged by `invalid_fraction`).

Recorded per candidate: `valid_r2` (original), `refit_valid_r2`,
`valid_rmse`, `refit_valid_rmse`, `refit_ok`, `n_params`, `optimizer_status`,
`refit_reason`.

The symbolic structure is never changed. Constants are never fitted on
validation data. The world `test` split is never used.

### 2.2 FEATURE GROUP 2 — cross-stratum generalization

Computed on the world's VALID molecules only, for the refit prediction (and, in
parallel, the original prediction).

Predefined stratifications:

* `precursor_mz` low / middle / high tertile — always.
* for each descriptor in the candidate's **effective support** other than
  `precursor_mz`: that descriptor's low / middle / high tertile.

Tertile cuts are the 33.3/66.7 percentiles of the VALID split. A stratum is
usable only with **>= 15** validation molecules; otherwise it is marked
unavailable and contributes nothing (never fabricated).

Recorded: `global_valid_r2`, `strat_median_r2`, `strat_min_r2`, `strat_sd_r2`,
`strat_median_rmse`, `strat_worst_norm_rmse` (worst-stratum RMSE / sd of y in
that stratum), `n_strata`. If fewer than 2 usable strata exist all stratum
fields are `null`.

### 2.3 FEATURE GROUP 3 — residual structure

On the VALID split, `e = y - y_hat`, for both original and refit predictions.

* `|Spearman(e, c)|` for each of the **12 frozen protocol descriptors**
  (`muru.discovery.protocol.FEATURES`) — a fixed 12-element set, not a library
  grown after inspecting failures.
* `resid_max_abs_spearman` = max over those 12.
* `resid_med_abs_spearman` = median over those 12.
* ONE interaction diagnostic: `|Spearman(e, precursor_mz * d*)|` where `d*` is
  the descriptor with the largest main-effect `|Spearman|` among the candidate's
  effective support excluding `precursor_mz`. Reported separately as
  `resid_interaction_spearman`; it is NOT folded into the max/median above.

Lower is preferable.

---

## 3. Nested world-level cross-validation

* **Outer** = the EXACT existing 5-fold assignment,
  `scripts/accopt_selectors.assign_folds`: stratified by
  `(block, noise_regime, category)`, worlds ordered inside a stratum by
  `sha256(world_id)` and dealt round-robin. All 30 seeds of a world stay
  together. Folds are NOT regenerated from outcomes.
* **Inner** = the same deterministic rule applied to the outer-training worlds
  only, giving 5 inner folds. Used to choose: architecture C's
  `(alpha, beta, gamma)`, architecture D's `C`, and the gate FORM
  (CURRENT_GATE vs MONOTONIC_LINEAR_GATE).
* Gate *thresholds/coefficients* are fitted on the full outer-training fold
  (training data), never on the outer test fold.
* All z-standardisations use outer-training-fold (or inner-training-fold, where
  the quantity is being tuned) statistics only.

---

## 4. Architectures (exactly four; no fifth is admissible)

Shared substrate for A, B, C: modal-**support** consensus over usable band
members (frozen from the baseline), then a family vote over the Type 2 clusters
inside that support, then a within-family representative rule.

**A — CURRENT_FINAL.** B2 validation-quality-weighted family vote + R1
highest-validation-R^2 representative + the existing two-quantity gate. No change.

**B — CONSTANT_REFIT.** Identical to A with one substitution: wherever A uses a
candidate's raw `valid_r2` as its QUALITY, B uses
`q = refit_valid_r2 if refit_ok else valid_r2`. This affects the support
consensus tie-break, the B2 vote, and the representative rule
(highest `q`, then lowest complexity, then deterministic expression tie-break).

**C — ROBUST_GENERALIZATION.** Candidate quality is the predeclared score

```
SCORE_C = z(refit_valid_r2)
        + alpha * z(strat_median_r2)
        - beta  * z(strat_sd_r2)
        - gamma * z(resid_max_abs_spearman)
```

z-statistics from training-fold candidates only. A candidate with an
unavailable stratum statistic contributes `z = 0` for that term (the training
median), which is neutral, never favourable. `alpha, beta, gamma in
{0.25, 0.5, 1.0}`, chosen by inner CV on family recovery; ties broken by the
smallest `(alpha, beta, gamma)` lexicographically. Family score = sum over
seeds of that seed's best `SCORE_C` in the family. **Stability floor**: the
existing floor is the downstream gate's selection-fraction threshold; no
additional family-level floor is introduced. Representative = highest
`SCORE_C`, then lowest complexity, then deterministic tie-break.

**D — SMALL_FAMILY_RANKER.** Ranks over ALL Type 2 clusters in the world (it
replaces family aggregation, so it is not given the support-consensus
substrate). Per-family features, all candidate-side, no truth-derived feature:

```
n_seeds, selection_fraction,
sum_seed_best_raw_r2, median_raw_r2, sd_raw_r2,
sum_seed_best_refit_r2, median_refit_r2,
median_strat_median_r2, median_strat_min_r2, median_strat_sd_r2,
median_resid_max_abs_spearman,
min_complexity, median_complexity
```

Missing values imputed with the inner/outer-training median, then standardised
on training statistics. Model: L2 logistic regression, `C in {0.1, 1.0, 10.0}`
chosen by inner CV, no class weighting, no polynomial features, no ensembles.
**Training target (development-only use of truth):** a family is labelled
positive iff the member that D's own within-family representative rule would
select is `t_family == True`. At inference the ranker sees only the 13 features
above. Selected family = highest predicted probability; ties by
`(-selection_fraction, min_complexity, representative expression)`.
**Representative rule for D, declared here before outer scoring:** highest
`refit_valid_r2` (falling back to `valid_r2` where `refit_ok` is false), then
lowest complexity, then deterministic tie-break. D does **not** use SCORE_C.

---

## 5. Gates (exactly two)

**GATE 1 — CURRENT_GATE.**
`REPORT iff median_over_seeds(best valid R^2) >= t1 AND selection_fraction(reported family) >= t2`.
Grid as frozen in the baseline; fitted to maximise training sensitivity subject
to training null FPR <= 5%.

**GATE 2 — MONOTONIC_LINEAR_GATE.**
`G = a*z(median_seed_best_r2) + b*z(selection_fraction) + c*z(family_quality_margin)`,
`a,b,c >= 0`, where `family_quality_margin` = selected-family score minus
runner-up-family score under the architecture's OWN family score. Coefficients
from the nonnegative grid `{0, 0.25, 0.5, 0.75, 1.0}^3` excluding all-zero,
normalised to sum 1; threshold swept over the training-fold score quantiles.
Fitted to maximise training sensitivity subject to training null FPR <= 5%.
No further gate feature may be added.

---

## 6. Objective, constraints, ship criterion

PRIMARY = pooled outer-fold **family recovery, ungated** (the quantity the
baseline reports as 83.9%). End-to-end family recovery is reported beside it.

Constraints: ungated support >= 95%, end-to-end support >= 95%, null FPR <= 5%,
positive/null ROC AUC >= 0.98, computational failure <= 2%.

Tie-break: G1B family, then G1C family, then lower null FPR, then simpler
architecture.

SHIP a new architecture only if outer-CV family improvement >= 3 percentage
points (i.e. >= 87.0% pooled, >= 49/56) AND all constraints hold AND no major
catastrophic subgroup regression AND no leakage. Otherwise retain
CURRENT_FINAL.

---

## 7. Frozen quantities NOT touched

`EXPONENT_TOL = 0.15`, `FAMILY_MIN_R`, `FAMILY_REL_RMSE`, `BAND_TOL = 0.01`,
`MAX_COMPLEXITY = 20`, `MAX_INVALID_FRACTION = 0.005`, the family-equivalence
definition, the CAS (SymPy only), and the search grammar for architectures A-D.

---

## 8. Conditional SAFE_EXP experiment (separate, after A-D are frozen)

Runs only after A-D selection is complete. G1C development worlds only.
`SAFE_EXP` = `exp(clip(z, -K, K))` with **K = 8.0 chosen before any recovery
number is seen**, complexity cost deliberately high. No other operator is added.
BASE_GRAMMAR (30 base seeds) vs PORTFOLIO_GRAMMAR (15 base + 15 SAFE_EXP seeds),
`niterations`, population size and every other search setting held constant.

---

## 9. Implementation clarifications (added before any scored comparison)

1. **D's training rows.** The ranker is trained on the Type 2 clusters of every
   *truth-scorable* development world in the training fold (G1A, G1B, G1C, G3,
   G4M). Non-scorable worlds (NCAL, G4, GC, G2, G5, GRT) carry no family label
   and contribute no training row.
2. **`family_quality_margin`.** Selected-family score minus runner-up-family
   score under the architecture's own family score (predicted probability for
   D). When a world has exactly one family the runner-up score is taken as
   `0.0`.
3. **C's clamp.** `SCORE_C` is a z-score sum and is NOT clamped at zero; the
   family score is the plain sum over seeds of each seed's best `SCORE_C`.
   A feature whose training standard deviation is zero contributes `z = 0`.
4. **A/B family score** keeps the frozen B2 form exactly:
   `sum_over_seeds( max(0, best quality in family for that seed) ) / n_seeds`.
5. **Gate-form choice** (CURRENT_GATE vs MONOTONIC_LINEAR_GATE) is made by inner
   CV inside each outer-training fold, maximising pooled inner-test sensitivity
   subject to inner-test null FPR <= 5%; ties go to CURRENT_GATE. The chosen
   form's parameters are then refitted on the whole outer-training fold.
6. **Phase 0 parity** was established before any of this ran: re-running
   `scripts/accopt_run.py` on the copied cache reproduces the frozen baseline
   bit-identically (support 55/56 ungated, 54/56 end-to-end, family 47/56,
   G1A 6/6, G1B 35/40, G1C 6/10, FPR 3.04%, ROC AUC 0.99907, B2+R1 in all 5
   folds).
