# Final Model Fairness Audit

| Dimension | MURU-WUR-v2 candidate | Tier A reference | Implication |
|---|---|---|---|
| Training boundary | Development records; selected in grouped multi-experiment search | Development records; separate grouped selection | Both are frozen before external outcome use; candidate had broader experiment search context |
| Inputs | 12 Tier A plus 2,048 log1p Morgan count features | 12 Tier A descriptors | Not a one-feature ablation |
| Descriptor transform | Fixed scaling plus fold-specific training standardization | Fixed scaling only | Preprocessing differs |
| Morgan transform | Radius 2, 2,048 count bins, no chirality, log1p, block weight .1 | None | The observed contrast cannot be attributed to the Morgan block alone |
| Ridge penalty | α=.3; grid {0.1,.3,1,3,10,30,100,300} | α=.1; grid {.01,.1,1,10,100} | Selection opportunities and penalties differ |
| Shared trajectory | Same frozen monotone profile and scale parameterization | Same | Endpoint/profile comparison is shared |
| External fitting | No refit | No refit | Frozen transfer comparison |
| Scoring | Same support rule, population, μ, P1 and bootstrap | Same | Primary metric is paired and common |

Both use curvature-weighted ridge fitting with an intercept, but their representation, preprocessing, dimensionality and tuning differ. The result identifies the difference between two frozen modeling pipelines on the frozen MSnLib endpoint. A matched-feature nested experiment would be needed to estimate the incremental effect of adding Morgan counts.
