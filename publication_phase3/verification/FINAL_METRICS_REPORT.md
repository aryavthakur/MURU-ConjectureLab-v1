# Final metrics verification

## Frozen external endpoint reconstruction

**Source commit:** `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`
**Reconstruction:** detached Git worktree; executed frozen `scripts/wur_v2_confirmation_v2/11_external_analysis.py` using committed inputs and release dependencies.

The rerun reproduced the result JSON values exactly at machine precision:

| Check | Frozen | Rebuilt | Status |
|---|---:|---:|---|
| Measured compounds | 1,794 | 1,794 | Match |
| Support exclusions | 5 | 5 | Match |
| Scored compounds | 1,789 | 1,789 | Match |
| Scaffold groups | 1,687 | 1,687 | Match |
| Candidate P1 | 0.12961151072591617 | 0.12961151072591617 | Exact |
| Reference P1 | 0.13352761116871245 | 0.13352761116871245 | Exact |
| Ratio | 0.9706719800607511 | 0.9706719800607511 | Exact |
| 95% scaffold bootstrap CI | [0.9523611879747089, 0.9892672061846276] | Same | Exact |
| Decision | MODEST EXTERNAL CONFIRMATION | Same | Exact |

The rebuilt novelty-bin results also matched all four stored values. Tables were exported programmatically by `analysis/generate_assets.py`. Compound-level residuals for figures were independently derived from the frozen candidate/reference JSON and measured μ table by `analysis/export_external_predictions.py`.

## Interpretation controls

- Relative P1 reduction is 1 − 0.9706719801 = 2.9328%.
- The practical target was ratio ≤0.95; observed ratio and its interval fail that criterion.
- AF difference is +0.000559, CI [−0.014525, +0.015538]; no tail-risk improvement is demonstrated.
- Q1 is explicitly the lowest-similarity/most-novel quartile; ratio 1.0082968.
- The development max-T CI was not independently reproduced in this phase; do not label it reproduced.
- The full raw mzML-to-endpoint decoding pipeline was not rerun; this verifies statistical reconstruction from committed measured-μ inputs.
