# Statistical review packet

## Estimand and data

The primary estimand is the paired pooled P1 RMSE ratio for two frozen pipelines evaluated on all supported compounds and both recorded numeric settings 20/60. P1 pools 3,578 compound-setting cells from 1,789 compounds. Five of 1,794 measured compounds were excluded because at least one model was outside response-profile support. Clustering is by 1,687 Bemis–Murcko groups; all compounds in a sampled group and their repeated measurements remain together.

## Primary inference

Candidate P1 = 0.1296115107; reference P1 = 0.1335276112; ratio = 0.9706719801. The percentile interval is [0.9523611880, 0.9892672062] from 10,000 scaffold resamples with seed 20261011. The interval describes scaffold sampling uncertainty conditional on frozen models, endpoint, population, support rule and numeric adapter; it excludes training/model-selection uncertainty. The ratio is below one but above the practical threshold 0.95 throughout the interval. Relative RMSE reduction is 2.9328%; this is not an accuracy percentage.

## Secondary outcomes

The two setting-specific ratios are 0.9821913 at numeric 20 and 0.9272829 at numeric 60 (n=1,789 each). The least-similar quartile ratio is 1.0083; novelty bins are descriptive and have no quartile-specific intervals. Q90, Q95, CVaR95, AF, and AF_max do not establish tail-risk improvement. The protocol’s adverse-tail override is upper 95% bound on candidate-minus-reference AF exceeding +0.03; it did not trigger. This threshold is an engineering decision boundary, not a clinical standard.

## Selection and independence limitations

The development search involved 13 experiment families. Amendment A-3 restated c4 after development results and five adversarial reviews were visible, before external outcome access. The original c4 failed for EXP08B; A-3 admitted it based on a revised null/permutation interpretation. Development point estimates remain frozen, but that amendment weakens the prospective status of the development selection. The max-T interval [0.860, 0.918] remains historical and unreproduced because its implementation artifacts, seed, resamples and selection ledger were not recovered.

The external replacement population followed recorded exposure exclusions after an earlier sample was exposed and excluded. The new sample was analyzed once and is now exposed. It is not a second independent validation dataset.

## Candidate/reference comparison

Both models share endpoint, development boundary, fixed profile, external support rule, scored population and metric. They differ in feature representation, candidate Tier A scaling, dimensionality, regularization and selection grid. Consequently, the external contrast compares frozen pipelines and does not identify the causal contribution of Morgan fingerprints.

## Reproduction route

From the extracted Phase 4 reviewer archive, enter its embedded `reviewer_package/` folder and run `python3.13 verify_reproduction.py` after following `README.md`'s environment instructions. This reconstructs metrics from frozen measured μ and model outputs; it does not retrain or process raw mzML. Exact environment and fresh-extraction run output are in `verification/FINAL_REPRODUCIBILITY_REPORT.md`.

## Requested reviewer assessment

Please assess the pooled-cell estimand, scaffold bootstrap, interval interpretation, practical threshold, A-3 selection amendment, multiplicity, adverse subgroup presentation, and whether any model-comparison asymmetry invalidates or only narrows the external conclusion. Please distinguish calculation correctness from the appropriateness of the target/energy adapter.
