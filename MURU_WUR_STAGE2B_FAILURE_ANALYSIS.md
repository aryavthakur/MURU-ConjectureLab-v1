# MURU WUR Stage 2B: failure analysis of the frozen method on real spectra

**Inputs:** the committed Stage 2A artifacts, the Stage 2B reference-arm ledger, the frozen folds, and the extended spectral summaries of both corpora. Nothing sealed or held out was read. Scripts, tables and plots are under `docs/wur_stage2b_failure_analysis/`.

**Disclosure.** Section 9 of the analysis compared several descriptor-only arms (gradient boosting, direct per-energy regression, ridge with a predicted shape exponent or asymptote, oracle arms) on the frozen folds outside the ledger, as exploratory diagnosis. Those numbers informed the hypotheses below; they are not candidate results and are not used for selection. Every candidate that Stage 2B compares is ledgered separately, and the internal HOLD check exists precisely because hypotheses were shaped on DEV2B.

## Headline

1. **Dominant, about 86 percent of held-out MSE: the twelve Tier A descriptors explain only half of the variance of the per-compound scale g.** Ridge, gradient boosting, quadratic ridge, log-augmented ridge and direct per-energy regression all reach held-out R2 0.49 to 0.50 on log g and P1 0.133 to 0.135. Estimation noise in g is negligible (reliability 0.988), so the unexplained half is real, compound-specific variation the descriptors do not encode. Mass alone gives 0.45; the other nine descriptors add 0.04.
2. **Profile misspecification is real but second-order for prediction.** Per-compound plateau, asymptote and slope each carry about a third of the shared-shape misfit (32 / 37 / 31 percent), which is why H-MAIN is rejected and the ladder's M1 to M3 all win where evaluable. Yet shape error is only 14 percent of held-out MSE (29 percent at E = 90), and none of the shape parameters is predictable from descriptors (held-out R2 -0.07 for the slope, 0.00 for the asymptote). Freeing a second per-compound parameter and predicting it from descriptors aliases with g and raises P1 (0.137 to 0.141 against 0.135).
3. **The selector and gate are mis-set for real data.** In the pooled analysis 39 of 56 band members beat the R1 representative on the test part; Spearman between validation and test R2 is 0.55. A three-input law, g proportional to sqrt(ring_count + 1/heteroatom_fraction)^p / total_atom_count^q, recurs in 14 of 15 fold searches and, refit log-linearly per fold, reaches CV R2 0.496, equal to the twelve-feature ridge, while the gate (t1 = 0.595) refuses in 15 of 15 folds because the attainable ceiling is 0.50.

## Evidence by question

- **Residual structure.** Pooled collapse residual SD 0.051 (1.7 x the 0.0295 repeatability SD); population-level means by energy, source, g tercile and mass tercile all within 0.02, so no systematic plateau or asymptote bias at the population level; 74 percent of residual sum of squares is a per-compound mean plus a per-compound tilt in log E, with low-E and high-E residuals anticorrelated (-0.66). The held-out E = 30 error is 85 percent g-prediction error: with the oracle g it is 0.068 against 0.176 with the ridge g.
- **Boundary compounds.** The 24 collapse grid-edge compounds are heavy (median m/z 678 against 288) and already at the profile floor at E = 30, so g is unidentifiable to the left; widening the box would move, not resolve, the estimate. Ladder unresolved-boundary cases are shape incompatibility, not box width: M1 binds on flat trajectories, M2 and M3 bind at the physical limits 0 and 1.
- **Trajectory heterogeneity.** Four-parameter logistic fits: low plateau below 0.9 in 38 percent, high asymptote above 0.4 in 30 percent and below 0.2 in 21 percent, SD of log slope 0.76. Only the asymptote correlates with descriptors (m/z -0.45, n_O -0.46). Source differences are detectable but small.
- **Descriptor signal.** Spearman with log g: m/z -0.61, atoms -0.58, rotatable bonds -0.54, n_O -0.48, tpsa -0.35, the rest below 0.21 in magnitude. The frozen symbolic representative reaches 0.27 raw and 0.39 recentred; 0.12 of its loss is a scale offset.
- **Source and interface.** Source coefficient on log g after descriptors: -0.045 (p = 0.25). Interface parity between the pooled table and the feature files: 5e-6. Cross-instrument mu for the 119 shared keys after the map: r = 0.958, RMSD 0.056, mean difference -0.005; the WUR-native versus LCSB-native g shift is 0.140 against the 0.149 the map predicts.
- **Noise floor.** Median M0 leave-one-energy-out MAE 0.038, 1.3 x repeatability; a third of compounds at the floor. Noise is not why descriptor-only prediction fails (achieved 0.134 against a floor of 0.03 to 0.05).
- **Spectral summaries.** mu is the most monotone (88 percent), smoothest and most descriptor-predictable summary (its g reaches CV R2 0.49; fragment depth 0.39; survival yield and the high-x fraction are censored for 43 and 21 percent of compounds and their g is unpredictable). Peak count and TIC are instrument-specific and unusable across corpora; spectral entropy carries a -0.23 nat WUR offset. The spectral representation is not the lever.

## Hypothesis verdicts

| Hypothesis | Verdict |
|---|---|
| (a) data / interface defects | refuted |
| (b) preprocessing | not indicated (S7 is run on the final candidate) |
| (c) insufficient spectral representation | refuted as a lever |
| (d) profile misspecification | supported, second-order for P1 |
| (e) g = f(descriptors) misspecified | partially: the symbolic form loses 0.10 R2 to ridge, but all forms share the 0.50 ceiling |
| (f) selector failure | supported |
| (g) identifiability | supported for a heavy minority |
| (h) adequacy boxes | proximate, not root, cause |
| (i) irreducible noise | refuted for P1 |

## Directions licensed for Stage 2B candidates

1. Replace the frozen symbolic selection with the stable three-input law or the ridge; recalibrate reporting to what real data can deliver.
2. A richer, still interpretable molecular representation for g, within the 24-feature cap. This is the only route materially below P1 0.133; a log g R2 of 0.70 would give about 0.108.
3. Do not pursue descriptor-predicted second shape parameters; use predictability as a confidence signal instead.
4. A population-level mass-aware asymptote is a supporting idea with a bounded gain (a few percent) and is not pursued as a headline candidate.
5. Ladder box widening helps only M1 and is a reporting repair, not a prediction one.
