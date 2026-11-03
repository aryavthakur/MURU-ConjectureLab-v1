# Final Metrics Verification

## Primary MSnLib external evaluation

The frozen output at `artifacts/wur_v2_confirmation_v2/result/external_analysis.json` reports **1,794 measured compounds**, **5 support exclusions**, **1,789 scored compounds**, **1,687 scaffold groups**, and **3,578 scored compound-rung cells**.

| Quantity | Candidate | Tier A reference |
|---|---:|---:|
| Pooled P1 RMSE | 0.1296115107 | 0.1335276112 |
| MRMSE | 0.1121373873 | 0.1175157920 |
| Median compound RMSE | 0.0995566039 | 0.1075164229 |
| Q90 | 0.2070536854 | 0.2065879135 |
| Q95 | 0.2315081577 | 0.2348610414 |
| CVaR95 | 0.2656786395 | 0.2648634968 |
| AF (compound RMSE > 0.20) | 0.1185019564 | 0.1179429849 |
| AF_max | 0.0620458357 | 0.0609278927 |

The candidate/reference P1 ratio is **0.9706719801**, with a 95% whole-scaffold percentile interval **[0.9523611880, 0.9892672062]**. Relative reduction is **2.9328%**. The interval excludes 1.0, while the interval and point estimate remain above 0.95; the prespecified 5% practical threshold was not met. The estimate is conditional on the frozen models, endpoint, eligible sample, and energy mapping.

### Per-rung outputs

| MSnLib HCD NCE setting | n | Candidate RMSE | Reference RMSE | Ratio |
|---:|---:|---:|---:|---:|
| 20 | 1,789 | 0.1643762142 | 0.1673566149 | 0.9821913179 |
| 60 | 1,789 | 0.0811094793 | 0.0874700482 | 0.9272828931 |

### Resampling specification and reproduction boundary

The frozen method resamples 1,687 scaffold groups with replacement for 10,000 replicates (seed 20261011), retains all compounds and both rung cells within sampled groups, and recomputes both P1 values and their ratio. The interval is percentile-based at 2.5% and 97.5%. It does not include model-selection or training uncertainty. A fresh Phase 4 reconstruction from frozen measured-μ inputs and prediction outputs reproduced the stored values; it is not raw mzML reprocessing or retraining.
