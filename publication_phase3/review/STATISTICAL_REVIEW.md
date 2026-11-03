# Simulated Reviewer B — Statistics

**Nature of review:** adversarial AI-assisted internal review; not a human statistical review. Recalculation was performed by rerunning the frozen external analysis in a detached worktree.

## Overall assessment

The primary external estimand is clear: pooled RMSE over paired compound-rung cells, with whole-scaffold resampling and the ratio recomputed per replicate. The manuscript distinguishes statistical direction from the 5% practical target. The primary external analysis reproduced exactly. The largest unresolved statistical evidence issue is development uncertainty: the ten-arm max-T interval in the release could not be independently recreated from the absent audit files and should not be presented as independently verified.

## Concerns and dispositions

| Severity | Concern and evidence | Disposition |
|---|---|---|
| Major | Candidate selection involved multiple experiments; naïve reporting of the selected point estimate risks selection optimism. | Addressed: development is described as a 13-family search, with the documented simplicity rule. Development interval is explicitly historical, not independently reproduced. |
| Major | The candidate/reference models differ in features and α; paired comparison cannot identify Morgan's causal contribution. | Addressed: Results and Discussion state this estimates a pipeline contrast, not an isolated feature effect. |
| Major | The 5% practical criterion needs a pre-result basis and clear direction. | Addressed: Methods §2.7 states ratio ≤0.95 and Results states the interval is entirely above this threshold. Frozen protocol is linked. |
| Major | Compound-rung cells are correlated within compounds and related compounds share scaffold. | Addressed: scaffold bootstrap is the primary interval and compound measurements are described as paired/repeated; 1,687 groups are resampled. |
| Major | Tail metrics are easy to overinterpret from point summaries. | Addressed: AF interval is reported, Q90/Q95/CVaR95 are descriptive; no tail advantage is claimed. |
| Major | Q1 adverse result has no interval and multiple secondary comparisons may be unstable. | Addressed: all four quartiles shown, flagged as descriptive, no subgroup significance language. |
| Major | Excluding five unsupported compounds can affect the estimand. | Addressed: reasons and complete denominator stated; all-1,794 sensitivity numbers and qualitative conclusion reported. |
| Major | Sample 1 exposure could contaminate the sample-selection history. | Addressed: sample 1 is disclosed as exposed and unscored; replacement draw process and no-reuse status described. |
| Major | Development max-T CI [0.860, 0.918] cannot be traced to data/code in the available Phase 3 workspace. | Unresolved: separated from independently reconstructed external CI in Results, Discussion and `DEVELOPMENT_CI_FINAL.md`. |
| Minor | AF threshold 0.20 and single-rung 0.30 can appear arbitrary. | Addressed: described as frozen engineering thresholds, not physical constants; cited protocol/source record. |
| Minor | Relative reduction rounding should match ratio. | Addressed: figure/table generator computes 1−ratio from stored JSON; 2.9328% as reported. |

## Recommendation

The primary result is reproducible and supports the conservative conclusion. Do not use the development max-T interval for a new claim unless its original code, resampling draws and source commit are recovered. The bootstrap interval is conditional on the frozen model and dataset; this is explicitly stated in Supporting Information S4.
