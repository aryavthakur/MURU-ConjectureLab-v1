# Statistical review packet

## Data selection and status

The external population was evaluated once after a previously exposed MSnLib sample was excluded and replaced. The replacement was selected under the frozen exposure controls, was not used for refitting, and is now exposed. The population is not an untouched future replication. Of 1,794 measured compounds, five failed profile support; the primary comparison uses 1,789 compounds in 1,687 Bemis–Murcko scaffold groups.

## Primary statistic

For compound i and each of the two observed rungs, error is predicted μ minus measured μ. Pooled P1 is the square root of the sum of squared cell errors divided by the number of compound-rung cells. Candidate/reference ratio below one favors the candidate. The frozen candidate P1 is 0.1296115107; Tier A reference is 0.1335276112; ratio 0.9706719801 (2.9328% relative reduction). The prespecified practical target was ratio ≤0.95 and failed.

## Uncertainty

The primary interval resamples whole scaffolds in paired fashion, carries all observations within each sampled group, and recomputes both model P1 values and their ratio. The frozen implementation uses 10,000 replicates, seed 20261011, and empirical 2.5th/97.5th percentiles. Its 95% interval is [0.9523611880, 0.9892672062]. It represents scaffold-sampling uncertainty conditional on frozen models, evaluated records, endpoint, support rule, and energy map; it does not include training/selection uncertainty or account for unresolved physical energy interpretation.

## Secondary results and selection

Tail-risk improvement was not demonstrated. The least-similar structural quartile's point ratio was approximately 1.0083; subgroup intervals were not estimated. The candidate and reference differ in feature representation, scaling, and tuning; the comparison does not isolate a fingerprint effect. The development program involved multiple experiments and a post-results amendment before external outcomes; the historical development max-T interval [0.860,0.918] is unreproduced. No new analysis retunes on the exposed external outcomes.

## Review questions

Assess the paired scaffold bootstrap, interpretation of an interval below one alongside a failed 5% practical criterion, limits from selection and exposure, the descriptive nature of quartiles/tail summaries, and whether the paper clearly confines inference to the frozen comparison.
