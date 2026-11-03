# Final Methods Audit

## Target definition

The implemented endpoint is the first moment of the processed mass distribution normalized by the declared precursor m/z: μ = Σ(Iⱼmⱼ)/(m_prec ΣIⱼ). The frozen base cell uses a zero relative-intensity cutoff, includes the precursor, and retains raw intensities. No peak identity or ion formula is predicted. The values are nonnegative but not mathematically restricted to 1 because observed m/z values can exceed the declared precursor m/z slightly. Matched replicate scans are aggregated by the frozen median rule per compound and energy rung.

## Model reconstruction

The frozen predictor maps a compound to a log scale ℓ=log(g). Its shared response profile is a decreasing isotonic function on log-u, represented by 60 knots. Candidate and reference share the profile and scale fitting procedure. The candidate uses 12 Tier A descriptors plus a radius-2, 2,048-bin Morgan count fingerprint transformed with log1p and weighted 0.1. Its Tier A block is standardized with fold-specific training means and standard deviations. The reference is a separately tuned Tier A ridge with α=0.1 and uses fixed scaled descriptors without the extra standardization. Candidate α is 0.3. Both use scikit-learn Ridge with a fitted, unpenalized intercept.

The scale is selected over a 241-point log grid from −1.6 to 1.6 with parabolic refinement. The empirical response profile is estimated from development data in three alternating updates. Candidate selection comprised multiple model families and grouped nested validation; it was not one prespecified candidate experiment. External evaluation did not refit either frozen predictor.

## Comparison fairness

Candidate and reference share the target, development data boundary, response profile, outer grouped evaluation design, support rule, and external P1 computation. They do not share feature representation, candidate feature scaling, model complexity, or selection grid/penalty. Therefore, the external result compares two selected frozen pipelines and does not identify the causal effect of Morgan features. The public comparator benchmark maps predicted spectra to the same μ endpoint but differs in training data, architecture, and energy convention.

## Data lineage and statistics

The external frame is 1,794 measured MSnLib compounds with two rungs each; five are excluded for model profile support, leaving 1,789 / 1,687 groups. The observed replacement was evaluated once. The earlier exposed sample was permanently excluded; recorded compound keys and scaffolds were excluded during replacement selection. No claim of zero chemical similarity is justified. P1 pools 3,578 paired compound-rung cells. Cluster resampling is at scaffold level, not compound-cell level. Novelty bins are descriptive and use maximum Morgan-count Tanimoto similarity; no quartile-specific interval was estimated.

## Source limitations

The described procedure was checked against frozen code, configuration, model records, and the frozen analysis output. Full raw MSnLib mzML reprocessing and model retraining were not part of the reviewer archive and are not claimed as reproduced.
