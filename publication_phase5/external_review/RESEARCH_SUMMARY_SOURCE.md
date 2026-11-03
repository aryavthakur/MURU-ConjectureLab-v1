# MURU-WUR-v2: technical summary for external review

## Question and scope

MURU-WUR-v2 predicts a scalar fragmentation-extent endpoint, μ, across a modeled energy-response profile from molecular features. This is not full-spectrum prediction, fragment identification, or collision-energy calibration. The research question is whether the frozen joint structure model predicts μ with lower error than a Tier A descriptor ridge on a separately sampled MSnLib replacement population, and how observed differences vary across two recorded numeric settings and structure-similarity strata.

## Data and design

Development used 1,325 positive-mode compounds and scaffold-grouped folds across 13 experiment families. The final candidate was a ridge model using 12 Tier A descriptors plus 2,048 radius-2 Morgan count bins transformed by log1p and weighted 0.1. The shared monotone energy response was learned on development data. The external population was selected once after an earlier sample had been exposed and excluded. It contains 1,794 compounds, of which five fell outside profile support; the primary analysis includes 1,789 compounds in 1,687 scaffold groups and 3,578 compound-rung cells. The model and reference were frozen and were not refit on the external outcomes. The replacement sample is now exposed and cannot be reused as a fresh confirmation population.

## Primary result

Candidate P1 RMSE was 0.1296115107; reference P1 RMSE was 0.1335276112. The candidate/reference ratio was 0.9706719801, with a 95% whole-scaffold percentile bootstrap interval [0.9523611880, 0.9892672062] (10,000 replicates, seed 20261011). The relative RMSE reduction was 2.9328%. The interval excludes 1, but the point and entire interval are above the prespecified practical target of 0.95. The practical criterion therefore failed.

The least-similar structural quartile had ratio 1.0083 (descriptive; no subgroup interval). Tail metrics were similar, and AF difference interval included zero; no tail-risk improvement was demonstrated.

## Interpretation limits

The comparison is between two selected pipelines, not an ablation isolating Morgan fingerprints: candidate and reference differ in features, scaling, and tuning. The public full-spectrum comparators were reduced to the same scalar μ before P1, but their rankings change with energy convention and do not measure full-spectrum accuracy.

The selected MSnLib records have numeric settings 20 and 60. The frozen project protocol calls these NCE; the peer-reviewed MSnLib paper describes its ID-X MS2 energies as 20 eV and 60 eV. Native method records for the nine evaluated archives were not found. The frozen A0 adapter assumes ID-X NCE equals IQ-X NCE, but anchor agreement thresholds failed at A0 (median absolute μ difference 0.0501 vs limit 0.05), A1 (pooled RMSD 0.0811 vs 0.08), and A2 (median absolute difference 0.0506). The numerical comparison can be reconstructed; physical energy equivalence cannot be claimed.

Development estimate ratio 0.8886 is historical selection context. The original ten-arm max-T interval [0.860, 0.918] is unreproduced. After development results and five reviews were visible, amendment A-3 restated a permutation admission rule; the original literal criterion failed for the selected EXP08B. This was before external outcome access and is disclosed as a selection limitation.

## Questions for reviewers

- Does the energy-unit discussion correctly distinguish protocol labels, published method, and absent file-specific evidence?
- Is the anchor-gate failure adequately integrated into interpretation?
- Is the scalar μ endpoint chemically meaningful and sufficiently named?
- Is the modest observed effect described proportionately?
- Do the candidate/reference asymmetries limit the conclusion in the right way?
- What evidence is needed before stronger claims about physical energy transfer or novel-chemistry performance?

The manuscript is an internal AI-assisted draft. No journal submission or human expert review has occurred.
