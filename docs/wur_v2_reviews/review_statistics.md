# MURU-WUR-v2 development program: statistical review

**Reviewer role:** statistical reviewer (estimands, uncertainty, dependence, nesting, search bias, multiplicity, trust calibration, tail definitions, giant-group handling).
**Worktree and commit:** `recursive-executor-framework-07dd81` at `52967a0`. Nothing in the repository was modified except this file.
**Evidence base:** protocol `wur-v2-dev-1.0` with amendments A-1 and A-2, `MURU_WUR_V2_DECISION_GATE_1.md`, `src/muru/wur_v2/{metrics,admission,runner,engine,trust}.py`, scripts `exp01` to `exp13`, the ledger (23 entries), the result JSONs, and the cached out-of-fold (OOF) parquet predictions under `artifacts/wur_v2/runs/`. Every number below that is not quoted from an artifact was recomputed by me from the cached OOF predictions, with independent code written for this review (scratch scripts, not committed).

**Bottom line.** I found no Critical problem. The estimands are implemented and labelled correctly, the cluster bootstrap is correct, and EXP08B's admission reproduces exactly from the cached predictions. The headline development claim, that TA_MORGAN_JOINT lowers pooled trajectory RMSE by about 11 percent against the refitted Tier A ridge, survives every correction I could apply. The corrections covered selection optimism across arms, a simultaneous interval over the ten arms, refit and partition variability, and benzene dominance of the bootstrap. After these corrections the gain is closer to 10.5 percent, with a simultaneous lower limit near 8 percent. The Important findings are four. First, admission criterion 4 (the permutation control) was never formally applied to EXP08B, and read literally it fails. Second, the gate reports no selection-adjusted uncertainty. Third, the EXP04 R squared result is largely mechanical. Fourth, the external validation needs several statistical prerequisites fixed before anyone accesses outcomes. Section 10 recommends the external primary endpoint, comparator, uncertainty procedure and power.

---

## 1. Estimands and the cluster bootstrap

**Code.** `metrics.p1` is `sqrt(nanmean(E^2))` over all observed cells, which is the protocol's P1. `compound_rmse` is the per-compound root mean over observed rungs, `MRMSE` is its mean, `AF` is `mean(RMSE_i > 0.20)`, `AF_max` is `mean(max_E |e| > 0.30)`, and `P1_cw` is `sqrt(mean_i L_i)`. All of these match protocol section 6. Missing cells are excluded rather than zero-filled (the tests cover this). `CVaR95` averages the worst `ceil(0.05 n)` compounds, which is a sound finite-sample definition. The Gate labels P1 and MRMSE as distinct throughout. For example, section 1 reports P1 0.1251 against mean compound RMSE 0.1080 for Stage 3.

**Bootstrap mechanics.** `cluster_bootstrap` builds per-cluster sums of squared error and observed-cell counts for both arms. It draws multinomial cluster multiplicities `W` (G draws from G clusters, equal probability), which is whole-cluster resampling with replacement. It then computes `sqrt(W@S_c / W@N)` and `sqrt(W@S_r / W@N)` per replicate. P1 of each arm is therefore recomputed from resampled cells, and the ratio and difference are formed inside each replicate. MRMSE and AF differences are ratio estimators, `(W@R_c - W@R_r) / W@M`, on the same resample. This is exactly the protocol section 7 procedure. The `_codes` string cast could merge missing cluster labels into one cluster. On this population it does not: there are 0 NaN scaffold groups, and the 88 acyclic parents carry unique `__ACYCLIC__<key>` labels.

**Numeric check.** On PRIMARY, from the cached parquet files:

| Quantity | Recomputed | Gate |
|---|---|---|
| P1 joint / TA_RIDGE | 0.11600 / 0.13055 | 0.1160 / 0.1305 |
| P1 ratio | 0.88857 | 0.889 |
| Module bootstrap 95% CI (seed 20260925) | [0.8651, 0.9106] | [0.865, 0.911] |
| Independent loop bootstrap (explicit cluster index resampling, other seed) | [0.8653, 0.9101] | |
| MRMSE 0.1005 vs 0.1148, diff CI | [-0.0173, -0.0117] | |
| AF 0.0634 vs 0.1026, diff CI | [-0.055, -0.023] | 0.063 vs 0.103 |
| Compound-unit bootstrap (for contrast) | [0.8700, 0.9071] | |

The bootstrap distribution is centred on the point estimate (mean 0.88857). The SD of the log ratio is 0.0129. The scaffold-cluster interval is about 23 percent wider than the compound-unit interval, which shows the cluster unit is doing its job. The unit tests include a sign-reversal case, `test_bootstrap_recomputes_p1_not_mean_rmse`, that would catch a regression to the v1 mean-RMSE estimand.

**EXP01 (v1 Stage 3 corrected intervals).** The historical procedure is recomputed in `historical_procedure_recomputed`. It gives the mean paired per-compound RMSE difference, with compound and stereo-scaffold bootstraps. It matches the recorded intervals to the third decimal (for example V1B vs S2A: recorded [-0.0270, -0.0167], recomputed [-0.0272, -0.0170]). The corrected P1-ratio intervals are computed with three cluster units. Because Stage 3 scored models fitted once, a cluster bootstrap over the 404 test compounds is the appropriate interval for that frozen-model estimand. The correction changes no v1 conclusion, but two readings weaken. B1 vs S2A (0.963) now spans 1 under every unit, [0.902, 1.032] with v2 scaffolds and [0.849, 1.094] with stereo scaffolds. V1A vs V1B is borderline, [1.000, 1.090]. The Gate states the first correctly.

## 2. Conditional intervals, arm search and selection optimism

The protocol labels the interval "conditional descriptive uncertainty". I tested three ways it could understate uncertainty for the development claim.

**2a. Refit and partition variability.** The pooled OOF predictions come from five fold models. The bootstrap treats those models as fixed, so a shared fold-model error component is not propagated. I tested for that component directly. Within each partition, I compared the dispersion of the five per-fold P1 ratios with the dispersion predicted by the cluster bootstrap within each fold, using a Cochran Q test on log ratios:

| Partition | Per-fold ratios | Observed SD | Within-fold bootstrap SD | Q (4 df), p |
|---|---|---|---|---|
| PRIMARY | 0.877, 0.933, 0.890, 0.894, 0.838 | 0.034 | 0.023 to 0.031 | 6.20, p = 0.18 |
| PARTITION_S1 | 0.891, 0.882, 0.907, 0.869, 0.868 | 0.016 | 0.023 to 0.034 | 1.52, p = 0.82 |
| PARTITION_S2 | 0.887, 0.903, 0.838, 0.893, 0.924 | 0.032 | 0.027 to 0.036 | 5.02, p = 0.29 |

No partition shows fold heterogeneity beyond cluster sampling. The pooled ratio moves little across repartitions (0.8886, 0.8825, 0.8897; SD 0.004), and that spread is itself an estimate of the refit component. Combining it with the bootstrap SD (about 0.0115 on the ratio scale) widens the interval by roughly 5 percent. S1 and S2 are genuinely different partitions: for non-benzene pairs held out together in PRIMARY, the probability of also being together in S1 or S2 is 0.23, against 0.20 by chance. The exception is the benzene group, which is always in fold 0 (section 4). Refit variance is not a material understatement here.

**2b. Selection across arms (winner's curse).** Ten representation arms were run on PRIMARY: eight predeclared and two from A-1. The shape arm from A-2 was run later against the joint model. Their errors are highly correlated. I estimated optimism in two ways, using a common 4,000-replicate scaffold-cluster bootstrap over all ten arms.

- *Best-of-ten bias.* In each replicate, take the arm with the lowest ratio, then compare its original ratio with its bootstrap ratio. Mean optimism is **0.0061** on the ratio scale. The expected bootstrap minimum is 0.8782, against an observed minimum of 0.8820.
- *The actual section 12 rule replayed inside each replicate.* The rule is: the simplest admitted arm within 1 percent of the best; an A-1 arm displaces a predeclared arm of equal class only if more than 1 percent better; admitted set fixed at the observed set; AF override ignored. Mean optimism of the selected arm's ratio is **0.0064**. The rule selects EXP08B in 45 percent of replicates, EXP09D in 35, EXP08E in 15 and EXP08C in 4.
- *Simultaneous 95 percent band over the ten arms (max-T on standardized log ratios).* The critical value is 2.655, against 1.96 for a single arm. EXP08B's simultaneous interval is **[0.860, 0.918]**. Its marginal interval is [0.866, 0.909] in this bootstrap and [0.865, 0.911] in the module.

A selection-adjusted description of the joint model is therefore: ratio about 0.895 (a gain of about 10.5 percent), marginal conditional interval [0.865, 0.911], simultaneous interval [0.860, 0.918]. Every version excludes 1 by a wide margin, so the admission and the qualitative claim are robust. Two things are not robust. The "above 10 percent major" label from protocol section 1 sits on the heuristic boundary once optimism is removed. And the ordering among the top arms is not determined by the data. The paired ratios against EXP08B are: EXP08E 0.993 [0.976, 1.007], EXP09D 0.997 [0.969, 1.021], EXP08C 1.005 [0.999, 1.012]. The choice of EXP08B follows from the simplicity rule and prespecification, which is legitimate. The Gate's "EXP08E is 0.8 percent better" should carry this interval and should not be read as a real difference. These optimism estimates are plug-in bootstrap approximations: they treat the observed sample as the truth. They also cannot capture pre-protocol degrees of freedom: Tier A descriptors chosen in v1 on compounds that are now in the v2 population, the Morgan settings, and the A-1 and A-2 additions made after results were seen. Only an external look removes those.

**2c. Is [0.865, 0.911] a fair descriptive summary?** Yes, as labelled: an interval for these fold models' pooled OOF P1 ratio on this population, with scaffold-cluster sampling. It is not a confidence interval for the ratio a model refit on all 1,325 compounds would achieve on new chemistry. The STRICT interval [0.896, 0.955] and the similarity strata (section 10) are better guides to that. I recommend reporting the triple: point 0.889, conditional [0.865, 0.911], simultaneous over ten arms [0.860, 0.918], with a selection-optimism note of about 0.006.

**Multiplicity in admission.** Admission criterion 1 uses an unadjusted per-arm upper bound. Under the ten-arm simultaneous band, EXP08A (upper 0.991), EXP09A (0.992) and EXP09C (0.988) still pass. **EXP07 does not** (simultaneous [0.955, 1.002]). EXP07 was not selected. However, Gate section 7 cites "ION_ENV admitted" as satisfying the first clause of the quantum-pilot gate, and that clause rests on an unadjusted admission. The pilot was not run, so there is no downstream consequence.

## 3. PRIMARY plus S1/S2; fold-level summaries

A single primary partition with two sensitivity repartitions is adequate here. The repartition spread (0.004) is small against the cluster-sampling SD (0.0115), and the fold heterogeneity tests are null. Averaging the three partition point estimates, as in repeated cross-validation, would be legitimate and would not conflict with protocol section 7 (which forbids pooling them as extra samples), but it would change nothing. The admission bars for S1 and S2 (ratio below 1.00) are sign-consistency checks, not precision checks. That is appropriate.

Protocol section 7 asks for bootstraps on S1, S2 and source strata wherever a stratum has at least 50 groups. `admission.evaluate` bootstraps only PRIMARY and STRICT. I computed the missing intervals:

- S1 0.8825 [0.858, 0.906]
- S2 0.8897 [0.862, 0.915]
- LCSB-primary (439 compounds, 285 groups) 0.8837 [0.850, 0.918]
- WUR-primary (886, 527 groups) 0.8916 [0.861, 0.918]
- non-benzene (1,142, 764 groups) 0.8869 [0.861, 0.911]
- high-mass tercile (442, 328 groups) 0.936 [0.903, 0.969]
- non-[M+H]+ (36 compounds, 30 groups) 0.994 [0.881, 1.128]

The last stratum is below the 50-group rule and is shown only to note that the gain is absent or unmeasurable there.

I found no misuse of fold-level summaries. No fold standard errors, fold t-tests or nominal fold counts appear. EXP13's per-fold range (0.84 to 0.93) is descriptive, and its spread is what cluster sampling predicts. EXP11's "stable across folds" statement is about basis vectors, not inference. EXP06 uses subsample-seed SDs (section 9, Minor).

## 4. The giant benzene group

- **In the PRIMARY bootstrap.** The `c1ccccc1` group holds 183 of 1,325 compounds (13.8 percent) and resamples as one cluster, so about 37 percent of replicates omit it entirely. I checked whether this makes the interval lumpy. The mean replicate ratio at benzene multiplicity 0, 1, 2, 3 and 4 is 0.8873, 0.8889, 0.8893, 0.8901 and 0.8917. The effect is negligible, because the benzene-stratum ratio inside PRIMARY (0.900) is close to the non-benzene ratio (0.887). Treating the group as one cluster is conservative and correct under the frozen grouping.
- **GIANT (leave-benzene-out).** The scored set is a single scaffold group and also a single strict cluster, so no cluster-level uncertainty can be computed. The module returns a degenerate interval [0.896, 0.896]. A compound-unit bootstrap, [0.850, 0.948], ignores within-group dependence and should not be quoted as an interval. The admission bar (GIANT ratio at most 1.02) is a lenient single-realization check. It is also a weak novelty test. The "benzene" scaffold is a heterogeneous bin of monocyclic benzene derivatives, and the 1,142 training compounds still contain many benzene-bearing scaffolds, so the substituent Morgan environments are well covered. STRICT and the low-similarity strata are the meaningful novelty tests. The Gate's "10.4 on benzene held out" should be described as one realization with no interval.
- **Partition structure.** Benzene sits in fold 0 of PRIMARY, S1 and S2, with only 13 or 14 of its 82 fold-mates shared across partitions. Fold 0 therefore has 83 groups against about 170 in the other folds. This is handled correctly: groups are never split, and the pooled metric weights cells, not folds.

No issue affects the conclusions. For the external set, whose largest group has 28 compounds (2.4 percent), no giant-group problem arises.

## 5. Admission and selection (section 12, A-1, A-2)

**EXP08B recomputed from cached predictions against TA_RIDGE on the same cells:**

| Criterion | Value | Bar | Pass |
|---|---|---|---|
| c1 PRIMARY ratio | 0.8886 | at most 0.98 | yes |
| c1 PRIMARY 95% upper bound | 0.9106 | below 1.00 | yes |
| c2 S1, S2 | 0.8825, 0.8897 | below 1.00 | yes |
| c2 STRICT | 0.9256 | below 1.00 | yes |
| c2 LCSB, WUR strata | 0.8837, 0.8916 | below 1.00 | yes |
| c2 non-benzene | 0.8869 | below 1.00 | yes |
| c2 GIANT | 0.8960 | at most 1.02 | yes |
| c3 MRMSE | 0.1005 vs 0.1148 | lower | yes |
| c3 AF | 0.0634 vs 0.1026 | not higher by more than 0.01 | yes |
| c4 permutation control | see below | loses to arm, does not beat TA_RIDGE | **not evaluated; fails if read literally** |

These match `EXP08B_TA_MORGAN_JOINT.json` exactly.

**Criterion 4.** `run_arms.py` passed permutation models only for EXP08A, so EXP08B's recorded criteria contain no c4. Worse, EXP08A's recorded c4 used five identical permutations; the corrected run EXP08P documents this bug. The corrected joint-model permutations give ratios of 0.9987, 1.0046, 1.0021, 0.9979 and 0.9982. Three of five are below 1.00. The coded rule, `v > ratio and v >= 1.0`, would return False for EXP08B, and so does the protocol text "does not beat TA_RIDGE" read literally. The EXP08P ledger entry says "c4 re-read for EXP08A/B", but I found no written re-reading or deviation. Scientifically, the permuted joint model is TA_RIDGE plus a noise block that inner CV down-weights. A gain of 0.1 to 0.2 percent is noise (the permutation mean is 1.0003, and the per-arm bootstrap SD is about 1.3 percent). The real control result is that every permutation loses to the unpermuted arm by 11 percent. The conclusion stands, but the rule was not applied as written, and the c4 bar is badly posed for joint models. A deviation record is needed. A sensible restatement would be: "the permuted arm loses to the unpermuted arm in every permutation, and the mean permuted ratio is not below 1.00 beyond its bootstrap interval".

**One-percent selection margin.** Relative to the best admitted P1 (EXP08E 0.11515), the gaps are EXP08B +0.74 percent, EXP09D +0.44 percent and EXP08C +1.24 percent. Only 08B, 09D and 08E fall inside the 1 percent window. EXP08C is outside it; the Gate calls it "slightly worse", which is correct, but 08C was not eligible in any case. The candidates in the window divide three ways. EXP09D is equal in class to 08B and better by 0.30 percent, but as an A-1 arm it must beat the predeclared 08B by more than 1 percent, and it does not. EXP08E is an A-1 arm, at least as complex, 0.78 percent better, and reduces AF by only 0.5 points (the override needs 2). The Gate's selection of EXP08B is therefore a correct application of section 12 plus A-1. As section 2b shows, these margins are well inside the noise, so the rule's simplicity preference is what decides.

**A-2 shape arm.** Recomputed: shape/joint ratio 0.9821, cluster interval [0.9761, 0.9884]. Bar (ii) requires the ratio to be at most 0.98, and it is not. Every other A-2 condition holds: upper bound below 1; below 1 on S1 (0.9816), S2 (0.9815), STRICT (0.9919), GIANT (0.9808) and both sources; AF not higher. Rejection is the correct application of a rule frozen before the arm ran (the amendment commit 3861837 precedes the arm commit 531abe2).

- *Is the bar sensible?* A 2 percent practical bar for the most complex model class is consistent with protocol section 1, which says gains below 2 percent are usually not worth new complexity. It is a defensible engineering threshold.
- *Robustness.* The interval straddles 0.98, and 24 percent of bootstrap replicates satisfy the bar, so the decision is not robust at the margin. The honest reading is "the point gain of 1.8 percent (interval 1.2 to 2.4) is below the pre-set 2 percent practical bar", not "shape gains less than 2 percent".
- *Optimism.* The arm was designed after EXP11, including a non-nested estimate (0.1132) that was visible when it was registered. Its true gain is more likely below 1.8 percent than above.
- *Design.* A bar stated as a point estimate is coin-flip sensitive near the threshold. For future complexity bars, pair it with an interval condition, for example "upper bound at most 0.99", or treat an interval straddling the bar as "not demonstrated". Otherwise the decision can flip on 0.1 percent of noise.

## 6. Repeatability and the variance budget (EXP02)

**ICC formula.** `icc()` computes one-way ANOVA with k = 2: `MSB = 2 * sum((xbar_i - xbar)^2) / (n - 1)` and `MSW = sum_ij (x_ij - xbar_i)^2 / n`, with `ICC(1,1) = (MSB - MSW) / (MSB + MSW)`. That is correct. `sqrt(MSW)` is the single-measurement within-compound SD. Since `MSW = sum (a - b)^2 / (2n)`, it is the uncentered analogue of `SD(A - B)^2 / 2`. The two agree here (0.1156^2 = 0.01336 against 0.1658^2 / 2 = 0.01374; mean difference -0.017).

**Precision with n = 26.** A within-SD estimate on 26 df has a chi-square 95 percent interval of **[0.091, 0.158]**, assuming normal differences; heavy tails would widen it. The variance share therefore runs from **4.0 to 11.9 percent** (point 6.5 percent). The cross-instrument share has an interval of 8.1 to 13.4 percent (n = 124). Its point estimate is optimistic by construction, because the energy map was fitted on those 124 compounds, as the script notes. The per-rung within-SD at E30 (0.066) is 4 to 5 times that at E75 to E90, which matters for any low-energy external rung. ICC 0.97 largely reflects the large between-compound SD (0.66) of these 26 compounds. It should not be transported to populations with less scale spread.

**Variance-budget logic.** The share is `sigma^2_single / Var(logg_pred - logg_label)`. The label is the scale fitted to the compound's development trajectory, so it contains label noise. If that noise is independent of the prediction, then `Var(error) = Var(pred - true) + sigma^2_label`. The ratio is then exactly the fraction of OOF error variance due to label noise, and one minus it is the reproducible part. This is correct. It does not double count, because the numerator is the noise the label actually carries, not an extra term. The mu-space check agrees: the per-rung within-SDs give an RMS single-measurement noise of about 0.035, which is 7 percent of TA_RIDGE's P1 squared and 9 percent of the joint model's. Three caveats apply, none of which reverses "noise does not dominate":

1. The noise is measured only on 26 LCSB Q Exactive compounds. WUR labels (886 compounds) have no technical repeats, so their noise is unmeasured.
2. `curated_vs_raw_mu_rmsd` = 0.0506 is about the same as the direct preparation difference (0.0498). If the curated label were one of the two raw preparations, the expected RMSD to their mean would be about 0.025. The curated labels therefore carry a preprocessing or curation component beyond preparation noise that R1 does not capture, so the true label-noise share is probably above 6.5 percent. Even doubling it leaves roughly 13 to 24 percent.
3. The scale fits for A and B share one profile, so profile misfit cancels in A - B. That is appropriate for "repeatability" but excludes profile error from the noise term, as intended.

## 7. EXP03 decomposition and EXP04 R squared

**EXP03.** The identity `e = e_scale + r_shape` holds, with `MSE = MSE_scale + MSE_shape + 2 cov`, and the script reports the cross term. Over the E30 minus E90 MSE gradient (0.0212), the split is scale 0.0154 (72.5 percent), shape 0.0016 (7.6 percent) and cross 0.0042 (19.9 percent). The cross term is not noise. Per rung it is positive at low energy (+0.0023 at E30, +0.0029 at E45) and negative at high energy (-0.0019 at E90), and pooled over rungs it is almost zero (2 percent). That pattern follows from the oracle definition. `z*` is the least-squares scale on the compound's own trajectory, so `sum_E s_E r_E` is about 0 per compound. A compound whose true shape is tilted has part of the tilt absorbed into `z*`, which correlates the "scale error" with the shape residual in opposite directions at the two ends. Assigning the cross term to scale (92 percent) or to shape (28 percent unexplained) is therefore an attribution choice, not a finding. The Gate correctly reports both, and gate 13(a) correctly fired on the stricter reading. Two smaller points. `z*` carries measurement noise (about 6 percent of the `dz` variance). And the gradient is a difference of two MSEs, so component shares of it are not bounded to [0, 1] in general.

**EXP04.** `e = pred - mu`, and the supplement regresses `e` on observed `mu`, then adds survival `s` and depth `d`. Two mechanical couplings make the result close to a tautology.

1. **Error on observed mu.** For any shrunken predictor, `Cov(pred - mu, mu) = Cov(pred, mu) - Var(mu)` is strongly negative. I checked: `sd(pred)/sd(mu)` is 0.49 to 0.73 per rung, and R squared of `e` on `mu` (0.47 to 0.79) tracks the unexplained variance of the prediction, as shrinkage predicts. A high R squared of the error on observed mu is therefore expected for any imperfect model and says nothing about mechanism.
2. **s and d beyond mu.** `mu = s * r_p + (1 - s) * d` exactly (identity residual reported), so given `mu` the pair `(s, d)` has one remaining degree of freedom. A small increment "beyond total mu" (at most 2 percent) is largely implied by the identity.

The partial R squared table (unique_s, unique_d) regresses the error on components of the observed outcome, so it shares coupling 1. The Gate's finding "Neither beyond total mu" should not be presented as evidence about survival versus depth mechanisms. The E30 bias-by-regime table ("symmetric onset misplacement") is descriptive and acceptable. A non-mechanical test would regress errors on quantities not built from the scored cell, for example onset energy or survival estimated from the other rungs (leave-one-rung-out), or on predicted-side quantities. Also, `supplement_beyond_total_mu.json` has no committed generating script (only the artifact was committed, in d33aa69), which is a provenance gap.

## 8. Trust (EXP10)

**Implementation checks.**

- *PR-AUC.* `trust.pr_auc` is step-wise average precision. It equals `sklearn.metrics.average_precision_score` to four decimals for every continuous ranker. For tied scores it breaks ties by row order: the binary domain flag alone gives 0.0729 against sklearn's 0.0675. The reported composite (flag times 10 plus distance) has few ties, so it is unaffected.
- *Random baseline.* The Gate compares the best PR-AUC (0.084) with "a random 0.063", the prevalence (84 of 1,325). With 84 positives, the expected average precision of a random ranking is **0.068**, with a 95th percentile of 0.085 and a 99th of 0.095 (4,000 permutations). The best ranker's permutation p is 0.057 before accounting for having looked at eight rankers. No other PRIMARY ranker has p below 0.15.
- *AUROC* (not reported; I computed it with scaffold-cluster bootstrap intervals): learned log-RMSE 0.517 [0.457, 0.579], distance 0.559 [0.498, 0.627], sensitivity 0.525 [0.466, 0.582]. STRICT is similar (best 0.554).
- *Calibration.* `calibration()` fits a logistic of `y` on `logit(p)` with slope and intercept free. The reported "calibration_intercept" (-2.15) is the intercept of that joint fit, not calibration-in-the-large. With the slope fixed at 1, the calibration-in-the-large intercept is **-0.09**. That is close to calibrated in the mean, as expected, since the inner-CV training AF rates (6.3 to 7.5 percent) are close to test prevalence. The slope is 0.20 with a Wald interval of [-0.37, 0.78], which is consistent with no discrimination. Brier 0.0597 against 0.0594 for a constant.
- *Fixed-membership bootstrap.* The Route B interval fixes which compounds are retained at 80 or 90 percent coverage and resamples scaffold clusters. Re-ranking and re-thresholding inside each replicate gives nearly the same intervals: at 80 percent [-0.208, 0.143] against the stored [-0.241, 0.103], and at 90 percent [-0.129, 0.057] against [-0.125, 0.043]. The paired design (the same resample for learned and distance-only) is correct.
- *Nesting.* Training rows use inner cross-fitted errors and signals computed against their inner training sets; test rows use the outer training set. No held-out spectrum enters a signal. That is correct.

**Is "trust fails" sound?** Yes, for the decision it supports. Route B needs a relative reduction of at least 25 percent against distance-only, with an interval excluding no improvement. The upper limits are +10 percent at 80 percent coverage and +4 percent at 90 percent, so the data exclude the required effect, not merely fail to confirm it. The broader statement "cannot identify bad predictions" should be scoped. With 84 events the study excludes practically useful discrimination (AUROC upper limits 0.58 to 0.63). It cannot exclude weak signals: the non-[M+H]+ domain flag shows AF 13.2 percent (5 of 38) against 6.1 percent (Fisher p = 0.09). The corrected random baseline (0.068) should replace 0.063 in the Gate and ledger, and the intercept label should be fixed.

## 9. Absolute failure thresholds (0.20 / 0.30)

**Frozen before use.** Verified. The protocol containing section 6 was committed in 7674ab3 (20:54), before the first v2 fit (EXP01, e6e25d1, 21:01). `metrics.py` (AF_RMSE 0.20, AF_MAX 0.30) first appears in e6e25d1 and is unchanged since. The only protocol changes afterwards are the appended amendments. The inputs to the derivation (population per-rung SD, within-compound excursion, repeatability) are model-blind but outcome-derived. The protocol discloses this, together with the visible Stage 3 rates.

**Reasoning.** The thresholds are sensible engineering tolerances: 0.20 is about 1.14 times the pooled no-information RMSE of 0.175 and about 77 percent of a typical trajectory's excursion, and 0.30 is 1.43 times the largest per-rung SD. Three weaknesses:

1. "Worse than a no-information prediction for that compound" is imprecise. The population SD is a population-level RMSE, and an individual compound's B0 error depends on how far it sits from the rung means. S4, the per-compound relative failure metric, is the per-compound version.
2. AF dichotomizes a continuous quantity, and near the threshold single-cell noise (RMS about 0.035) flips compounds. The paired AF difference partly cancels this, but AF should always appear alongside Q90, Q95 and CVaR95 (it does).
3. On an external three-rung set, `RMSE_i` is a mean over different energies. The per-rung SDs there are unknown, and E30-like rungs carry much more error, so the same 0.20 threshold measures something different. Keep it frozen, but report the external B0 AF and per-rung no-information RMSE for context.

## 10. Recommended design for the fixed-energy external validation (MultiMS2)

Population per the census: 1,165 scaffold-new [M+H]+ compounds with all three CID rungs (20/40/60 V), in 808 scaffold groups (701 singletons, largest 28); hash `5d7bb8c1...`.

**Primary estimand.** The pooled trajectory RMSE ratio `P1(TA_MORGAN_JOINT) / P1(TA_RIDGE)` over all observed external cells (compound times the three rungs). Both models are refit once on all 1,325 development compounds under protocol section 5, serialized, and hashed before any external outcome is accessed (the Gate reports they already are). Cells are the pre-registered aggregated value per compound and rung, so heavily replicated compounds (1 to 130 scans) get no extra weight. The energy mapping from lab-frame volts to the model's NCE coordinate must be pre-registered and frozen. If it is fitted from outcomes, fit it only on bridging compounds disjoint from the scored set; the 124 identity-overlap compounds are a natural choice.

**Comparator.** TA_RIDGE refit on 1,325 is the only primary comparator: it is the fair v1-family baseline. B1 (mass-only isotonic) and B0 (per-rung training mean) are reported as frozen secondary floors, not tested.

**Uncertainty.** A cluster bootstrap over external scaffold groups, using the frozen `scaffold_group` rule applied within the external set (808 clusters). Use B = 10,000, a pre-registered seed, and percentile limits, recomputing both arms' P1 inside every replicate (the existing `metrics.cluster_bootstrap`). Because the models are frozen, this is the correct interval for the external estimand. It is not "conditional" in the development sense. Sensitivity analyses: strict clusters (Morgan-count Tanimoto 0.55 single-linkage merged with scaffolds, computed within the external set) and the compound unit. In my simulation of the external design (below), this percentile procedure had a one-sided type I error of 0.03 at a true ratio of 1.00, against a nominal 0.025. It is adequately calibrated.

**Decision rules (one look, fixed sequence, no alpha splitting):**

1. **Primary superiority.** Success if the upper limit of the two-sided 95 percent interval of the P1 ratio is below 1.00. Report the point estimate and the interval. Report "ratio at most 0.98" descriptively, not as a success condition: it roughly halves power at plausible effects and duplicates the interval rule's intent. An interval that includes 1.00 is reported as "improvement not demonstrated", never as equivalence.
2. **Key secondary, tested only if (1) succeeds: AF noninferiority.** `AF_joint - AF_TA` with an upper 95 percent limit below **+3.0 percentage points**, followed by AF superiority (upper limit below 0) as a third step. Compute AF with the frozen 0.20 threshold on three-rung RMSE. A 2-point margin is also defensible but underpowered when the true difference is zero (power 0.67, against 0.95 for 3 points).
3. **Descriptive only:** MRMSE ratio, Q90, Q95, CVaR95, AF_max, per-rung P1, strata by maximum similarity to development compounds and by mass tercile, and, separately and never pooled, the 213 identity-new but scaffold-seen compounds.

**Power.** I simulated external datasets from the development PRIMARY OOF errors of the two frozen-architecture models. Each dataset had 701 singleton compounds plus 107 multi-member groups resampled from development groups of size 2 to 28, and three rungs (30/60/90 or 30/45/60 in the NCE coordinate). I also added an optional shared additive error (SD 0.05) to both arms to mimic energy-map and instrument error. For each dataset I ran a 500-replicate cluster bootstrap. Effect shrinkage was modelled by swapping the two arms' per-compound errors for a random fraction of compounds, which keeps the realistic dispersion of the paired difference. Simply interpolating the errors understates variance and gave spurious 100 percent power. The SD of the external ratio is 0.012 to 0.014.

| Retained share of development effect | Expected ratio (30/60/90) | P(superiority) | P(AF NI, 2 pp) |
|---|---|---|---|
| 100 percent | 0.894 | 1.00 | 1.00 |
| 50 percent | 0.946 | 1.00 (0.99 with shared noise) | 0.99 |
| 35 percent | 0.961 | 0.89 (0.87) | 0.95 to 0.99 |
| 25 percent | 0.973 | 0.60 (0.56) | 0.90 to 0.93 |
| 15 percent | 0.984 | 0.27 (0.28) | 0.81 to 0.85 |
| 0 percent | 1.000 | 0.03 | 0.67 (0.95 at a 3 pp margin) |

The minimum detectable effect at 80 percent power is a ratio of about 0.965 (a 3.5 percent improvement). What effect to expect: development effect size depends strongly on similarity to training chemistry. Scaffold-cluster intervals by maximum MinMax similarity to the training fold:

- below 0.35 (405 compounds): 0.947 [0.914, 0.988]
- 0.35 to 0.50: 0.883
- 0.50 to 0.70: 0.838

The census reports a median maximum similarity of 0.35 of external compounds to development compounds, with 97 percent below 0.55. The high-mass tercile also shows a smaller gain (0.936). A plausible external ratio before instrument and energy-map dilution is 0.92 to 0.95. A shared additive error of SD 0.05 moved the development ratio from 0.894 to 0.907. The study is therefore well powered for the plausible range and underpowered only if transfer keeps less than about a third of the development effect. That limit should be stated in the pre-registration.

**Statistical prerequisites before outcome access:**

- **(a) Outcome-dependent censoring.** Library QC drops spectra with few signals or low explained intensity, which preferentially removes precursor-rich low-energy spectra. Membership in the released library is therefore selected on the outcome. Since the development gain is largest at the lowest rung (E30 0.153 against 0.172), this missing-not-at-random selection can bias the ratio, not just the levels. Prefer the design frame (raw mzML with a pre-registered extraction and aggregation) or pre-register a censoring sensitivity analysis.
- **(b)** Replicate aggregation rule (1 to 130 scans per rung).
- **(c)** The energy map and its uncertainty (a bootstrap over bridging compounds as a sensitivity analysis; both arms share it).
- **(d)** A rule for compounds that lose a rung after extraction QC, written before outcomes are seen, with the count reported.
- **(e)** A scope statement: 99.7 percent of the population is NEXUS screening chemistry.
- **(f)** A single look with no interim analysis. Any second external set is a separate study with its own primary endpoint.

## 11. Other observations (Minor)

- **Learning curves (EXP06).** Subsamples at 75 percent of groups overlap heavily across the three seeds, and the 100 percent point is a single run, so seed SDs understate sampling variability. Benzene's 183 compounds are kept or dropped as one group, which adds variance at low fractions. "Tier A flattens by half" rests on a 50 to 100 percent change (0.1327 to 0.1305) about the size of one seed SD at 50 percent (0.0027). The pretrained-encoder gate refers to the learning curve "for" the admitted fingerprint model, but only single-block MORGAN_RIDGE curves exist. Its not-run decision is reasonable on cost grounds but is not evidenced by a joint-model curve.
- **Source transfer (EXP13).** Train-on-LCSB/score-WUR and the reverse are not scaffold-disjoint: 25 and 42 percent of test scaffold groups appear in training. The protocol already calls this descriptive. The Gate's 0.90 figures should carry that caveat.
- **Provenance.** Most arm and diagnostic ledger entries (EXP03 to EXP11) record `tree_dirty: true`. The cached predictions reproduce, but a clean-tree regeneration of the admission tables before external freeze would close this.

---

## Findings

| Id | Severity | Finding | Evidence | Action |
|---|---|---|---|---|
| S-01 | Important | Admission criterion 4 was never applied to EXP08B. Read literally, and as coded (`v >= 1.0`), it fails: 3 of 5 corrected joint permutations beat TA_RIDGE (0.9979, 0.9982, 0.9987). The EXP08P ledger says "c4 re-read" but no written deviation exists. Scientifically the permuted model is TA_RIDGE plus noise (mean 1.0003), and every permutation loses to the arm by 11 percent. | `EXP08B_TA_MORGAN_JOINT.json` criteria lack c4; `permutation_controls_corrected.json`; `admission.py` line 38 | Record a deviation restating c4 for joint models (loses to the arm in every permutation; mean permuted ratio not below 1.00 beyond its interval) and re-evaluate EXP08B, 08C and 08E under it before external freeze |
| S-02 | Important | The Gate reports only the marginal conditional interval, with no selection or multiplicity adjustment over 10 arms. Winner's curse is about 0.006 on the ratio (0.0064 replaying the section 12 rule); the simultaneous 95 percent band for EXP08B is [0.860, 0.918]. The "major, above 10 percent" label sits on the heuristic boundary once optimism is removed. The top-arm ordering is noise (08E/08B 0.993 [0.976, 1.007]; 08B selected in 45 percent of bootstrap replicates). | Recomputed from cached PRIMARY OOF; section 2b | Report point 0.889, conditional [0.865, 0.911], simultaneous [0.860, 0.918], optimism about 0.006; describe the gain as about 10 to 11 percent; state that arm ordering within 1 percent is not data-determined |
| S-03 | Important | The EXP04 "survival or depth beyond total mu" R squared is largely mechanical: error regressed on observed mu reflects prediction shrinkage (sd(pred)/sd(mu) 0.49 to 0.73), and the exact identity mu = s r_p + (1 - s) d leaves one degree of freedom. The supplement JSON has no committed script. | `exp04_results.json`, `supplement_beyond_total_mu.json`, recomputation in section 7 | Do not present as mechanistic evidence; if the question matters, use leave-one-rung-out onset or survival predictors; commit the generating script |
| S-04 | Important | External validation needs statistical prerequisites fixed before outcome access: outcome-dependent library QC censoring (missing not at random at the low rung where the gain is largest), replicate aggregation, a frozen energy map fitted on disjoint bridging compounds, a missing-rung rule, and a single look. | Census sections 4, 6, 7; per-rung gains in EXP13 | Adopt the section 10 design: P1 ratio vs frozen TA_RIDGE, 808-scaffold cluster bootstrap B = 10,000, superiority if upper 95 percent limit below 1.00, gatekept AF noninferiority at +3 pp; state MDE ratio about 0.965 |
| S-05 | Minor | The shape-arm rejection at 0.9821 vs 0.98 is a correct application of a pre-frozen rule, but the interval [0.976, 0.988] straddles the bar (24 percent of replicates pass), and the arm was designed after seeing a non-nested 0.1132 estimate. | `exp12_shape_arm.json`; recomputed bootstrap | Describe as "1.8 percent (1.2 to 2.4), below the pre-set practical bar", not "below 2 percent"; pair future point bars with an interval condition |
| S-06 | Minor | Trust reporting: the random PR-AUC baseline should be about 0.068 (expected random average precision with 84 positives), not prevalence 0.063; the best of 8 rankers has p = 0.057 unadjusted; "calibration_intercept" -2.15 is the joint-fit intercept, while calibration-in-the-large is -0.09; the PR-AUC tie handling is order-dependent for binary signals. The "trust fails" decision is sound (upper limit +10 percent against the 25 percent bar; AUROC upper limits 0.58 to 0.63). | `trust.py`, `exp10_results.json`, recomputation in section 8 | Correct the baseline and intercept label in the Gate and ledger; report AUROC with intervals; scope the claim to "no practically useful discrimination" |
| S-07 | Minor | EXP07 (ION_ENV) admission does not survive a ten-arm simultaneous bound (upper 1.002); the quantum-pilot gate clause cites it. | Section 2b | Note the unadjusted basis wherever "ION_ENV admitted" is used |
| S-08 | Minor | The EXP02 variance-budget logic is correct (label-noise share of OOF error variance), but it is imprecise and LCSB-only. Share interval 4.0 to 11.9 percent (n = 26); curated vs raw mu RMSD 0.051 is about twice what a single-preparation label implies, pointing to unmeasured curation noise; WUR noise is unmeasured. The conclusion "noise does not dominate" is robust. | `exp02_results.json`; chi-square interval | Report the interval and the curation-noise caveat; do not transport ICC 0.97 to lower-spread populations |
| S-09 | Minor | In EXP03 the cross term is 20 percent of the E30 to E90 gradient, with an antisymmetric sign pattern induced by the least-squares oracle scale; the 72 vs 92 percent split is an attribution choice. | `exp03_results.json` per-rung cross terms | Keep both readings; describe the cross term as tilt absorbed into the oracle scale |
| S-10 | Minor | GIANT is one cluster, so no interval exists (the module returns a degenerate one), the at-most-1.02 bar is lenient, and the benzene bin is not a chemical-novelty test. Benzene dominance of the PRIMARY bootstrap was checked and is negligible (mean ratio 0.887 to 0.892 across multiplicities). | `runner.py` TEST_FOLDS; recomputation in section 4 | Report GIANT as a single realization; rely on STRICT and similarity strata for novelty |
| S-11 | Minor | Protocol section 7 bootstraps for S1, S2 and source strata (at least 50 groups) were not produced by the admission evaluator. | `admission.py` boots PRIMARY and STRICT only | Add them (computed here: S1 [0.858, 0.906], S2 [0.862, 0.915], LCSB [0.850, 0.918], WUR [0.861, 0.918]) |
| S-12 | Minor | The AF thresholds were frozen before any v2 fit (verified by commit order), but "worse than no-information for that compound" is imprecise, and the meaning of 0.20 shifts on a three-rung external set at different energies. | Protocol section 6; git history 7674ab3 before e6e25d1 | Keep frozen; report external B0 AF and per-rung no-information RMSE for context; always pair AF with Q90, Q95 and CVaR95 |
| S-13 | Minor | Learning-curve inference is weak: overlapping subsamples, a single 100 percent run, benzene in or out variance, "flattening" differences near one seed SD, and no curve for the admitted joint model. | `learning_curves.csv` | Soften "representation-limited" to "consistent with"; add a joint-model curve if the encoder question is reopened |
| S-14 | Minor | The source-transfer stress test is not scaffold-disjoint (25 and 42 percent of test scaffolds seen). | `exp13_results.json` | Caveat the 0.90 figures in the Gate |
| S-15 | Minor | Most EXP03 to EXP11 ledger entries record a dirty tree. | `ledger.jsonl` | Regenerate admission tables from a clean tree before external freeze |
