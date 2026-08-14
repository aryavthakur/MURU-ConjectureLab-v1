# Table 2. Frozen Endpoints and Success Criteria

**Status: Fully populated from frozen sources.**

| Endpoint | Role | Denominator (Held-Out) | Mathematical Definition | Gate Threshold | Failure Handling |
|---|---|---:|---|---|---|
| scalar competence (G1) | PRIMARY | 164 | Spearman >= 0.80 AND MAE <= 0.80 x baseline AND M0_NOT_REJECTED | Wilson lower >= 0.70 | fails G1 |
| family recovery (G2) | PRIMARY | 144 | support_status == MATCH AND family_status == MATCH | Wilson lower >= 0.70 | fails G2 |
| principal structural safety (G3) | PRIMARY | 36 | Unsafe structural acceptance across F07, F19, F20 | Wilson upper <= 0.15 | fails G3 (UNEVALUABLE is violation) |
| support recovery | SECONDARY | 144 | support_status == MATCH under algebraic normalisation | Descriptive / ungated | non-success |
| parameter recovery (joint) | SECONDARY | 156 | p_mass within +/-0.15 AND c_desc within +/-0.10 at x0 = (250, 0, 0, 0, 0) | Descriptive / ungated | non-success |
| mass exponent recovery | SECONDARY | 156 | p_mass within +/-0.15 of planted exponent at x0 | Descriptive / ungated | non-success |
| descriptor coupling recovery | SECONDARY | 84 | c_desc within +/-0.10 of planted coefficient at x0 | Descriptive / ungated | non-success |
| predictive equivalence | SECONDARY | 144 | valid >= 0.995, c* > 0, REL_RMSE <= 0.05, Pearson r >= 0.990 over 12 ref frames (2,160 rows) | Descriptive / ungated | non-success |
| exact algebra recovery | SECONDARY | 60 | Symbolic equivalence to planted law up to positive scale | Descriptive / ungated | non-success |
| M0 specificity | SECONDARY | 164 | M0_NOT_REJECTED in M0-truth worlds | Descriptive / ungated | non-success |
| M1 sensitivity | SECONDARY | 36 | M1 detector fires for M1 truth (F06, F13, F16) | Descriptive / ungated | non-success |
| M2 sensitivity | SECONDARY | 24 | M2 detector fires for M2 truth (F14, F16) | Descriptive / ungated | non-success |
| M3 sensitivity | SECONDARY | 24 | M3 detector fires for M3 truth (F15, F16) | Descriptive / ungated | non-success |
| trajectory prediction | DIAGNOSTIC | 164 | MAE <= 0.80 of baseline on held-out test compounds | Descriptive / ungated | non-success |
| profile stability | DIAGNOSTIC | 164 | Profile variation across bootstrap resamples | Descriptive / ungated | non-success |
| scalar target yield | DIAGNOSTIC | 164 | Fraction of test compounds with successful scalar fit | Descriptive / ungated | non-success |
| boundary hit | DIAGNOSTIC | 12 | Flags boundary condition hits in F05 | Descriptive / ungated | non-success |
| response structure diagnostic | DIAGNOSTIC | 4 | Flags destroyed response cells in F19C | Descriptive / ungated | non-success |
