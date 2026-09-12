# MURU WUR Stage 2B: adversarial review adjudication

Five independent reviews were run on the selection record at commit `73362ce`: scientific red team, leakage audit, statistical review, implementation review, reproducibility review. Every Critical and Important finding is adjudicated here. Decisions marked **A-3** are carried into the protocol as amendment A-3 and into the selection record.

## Reproducibility (verdict: clean)

An isolated worktree at `73362ce` rebuilt the internal holdout (both hashes identical), one Stage 2A analysis from scratch including all 30 PySR seeds (every number, every checkpoint byte-identical), the folds hash, the Tier A2 descriptor table, the 15-fold P1 vectors of five ledger arms (zero difference) and one S2A fold from an empty checkpoint (byte-identical fronts, identical expression and gate). Only two additive JSON keys added by the post-run hardening commit differ. Noted: a naive re-run replays committed checkpoints; delete `ckpt/` to exercise the search.

## Critical findings

**RT-C1 (red team), ST-C2 (statistics). The gain is the removal of the frozen selector and gate, not a new MURU.** Decomposition: S2A to the three-input law 10.2 points, law to 12-feature ridge 1.5, ridge to 24 features 0.9. The frozen pipeline does not beat the mass-only null (8 of 15 wins; cluster bootstrap through zero). *Accepted.* The final claim is restated in the weak form the reviewers wrote (section "Claim" below). The generation label stays MURU-WUR-v1 because the protocol defines labels by lineage, and the freeze document says in its first paragraph what the label does and does not mean.

**RT-C2 (red team), LK-1, LK-2 (leakage), ST-C1 (statistics), IM-C1 (implementation). V1C is not separable from LIN, and its pre-registered hypothesis failed.** H-R required 5 percent over LIN; delivered 0.9 (0.4 on fresh seeds, 0.9 on stereo-merged folds with 10 of 15 wins). Cluster-bootstrap 95 percent CI of the V1C minus LIN difference [-0.0036, +0.0011]; the fold-paired SE that separated them is 2.5x too small because fold 0 is the same 183-compound benzene scaffold in every repeat (13 distinct held-out sets, not 15). One Tier A2 descriptor (`n_amine`) equals Tier A's `n_N` exactly; the median in-sample R2 of the rest on Tier A is 0.80. *Accepted.* **A-3: V1C's ledger outcome is "hypothesis not supported; rejected". The final candidate is the twelve-descriptor ridge (the LIN arm), registered as candidate `V1B_RIDGE_TIERA` with the LIN ledger as its evidence.** This is a decision taken after results were seen. It moves no threshold, and it selects the simpler and slightly lower-scoring of two statistically indistinguishable models, which is the protocol's own tie principle applied with a valid standard error. V1A (three-input law) is retained as the named interpretable secondary; V1C is retained as an exploratory non-inferiority comparator.

**IM-C1, ST-C1. The frozen folds have 13 distinct held-out sets; "12 of 15" is 3 to 6x anticonservative under a cluster-permutation null.** *Accepted as a defect of the frozen design that cannot be repaired without changing the folds.* The type-I control of the rule comes from the 5 percent clause (joint null pass probability 0.0003 to 0.0018 per candidate); every "beats S2A" verdict survives the correct tests (cluster-bootstrap CIs entirely below zero, permutation p < 0.001). Every fold-based comparison in the record is now accompanied by the cluster-bootstrap value, and the protocol text's "122" is corrected to 183 (the pooled benzene group counts both corpora).

## Important findings

| Id | Finding | Decision |
|---|---|---|
| RT-I1 | Benzene scaffold is 23 percent of DEV2B, always fold 0, easiest fold | Stage 3 pre-registers a per-scaffold stratum endpoint (benzene versus other) |
| RT-I2, ST-I3 | Winner's curse: exploratory arms on the same folds; V1A's form chosen after its CV R2; optimism 2 to 3 percent for V1A, all of V1C's 0.9 percent | Disclosed in ledger and freeze; HOLD and SEALED are the only unbiased reads; V1A expected 1.5 to 2.5 percent behind LIN there |
| RT-I3, ST-I4 | HOLD (n = 130) has power 0.15 to 0.19 for the 2.5 percent floor, 0.85 to 0.95 for the DEV-observed effects over S2A and B1, 0.14 to separate V1C from LIN | The frozen HOLD conditions are kept and their power stated; the check is a guard against a gross failure, not a fine comparison |
| RT-I4 | Profile-side ceiling: a perfect second parameter would gain at most 5.9 percent; the aliasing argument is sound; a population-level mass-aware asymptote was not tried | Recorded as the bounded, untried direction for a future generation; not pursued before Stage 3 |
| RT-I5 | The law is mostly the instrument's energy transfer (g proportional to atoms^-1.2), not chemistry | Carried into the scientific conclusion verbatim |
| RT-I6 | Pooling is defensible; WUR-only training scores 0.1288 versus 0.1272 pooled on WUR held-out compounds | Stage 3 pre-registers a WUR-only-trained secondary arm |
| LK-1 | Murcko scaffolds keep stereochemistry; two steroid scaffolds straddle folds (17 compounds); Stage 2A split does not straddle | Accepted; effect confined to the V1C-versus-LIN margin; the freeze records the stereo-aware grouping as a known limitation and Stage 3 reports the stereo-merged stratum |
| LK-3 | The Stage 1 map used population-B LCSB targets that are DEV2B targets (fold-0 refit moves V1C by +0.0026, LIN by +0.0004) | Accepted as a DEV2B-only dependence; the map is frozen and is applied identically to sealed compounds, which never informed it; no Stage 3 impact |
| LK-4 | HOLD is not scaffold-disjoint from LCSB-DEV at the stereo level: 8 of 130 compounds share a scaffold with an LCSB-DEV compound of a different key | Disclosed in the HOLD record; HOLD is reported with and without those 8 |
| LK-5 | Source is predictable from descriptors (AUC 0.70); 17 WUR compounds carry non-protonated adducts | Transfer caveat recorded; residual source effect on log g is -0.045 (p = 0.25) |
| IM-I1 | The S2A arm's inner split is 60/20/20 (the frozen `protocol.group_split`), not the 75/25 the protocol text said | Protocol text corrected in A-3; the arm is the frozen method as deployed, which is what "beats S2A" means |
| IM-I2 | Black-box bar was applied in condition 2 instead of the section 8 gate | Fixed in code (commit `9a88c10`); V1D's outcome unchanged |
| IM-I3 | S2A checkpoint keyed by world id and seed only | Reproduction from an empty checkpoint verified byte-identical; documented |
| IM-I4 | No runtime assertion that DEV2B matches the folds' population | Added (commit `9a88c10`) |
| IM-I5 | Positional contract between B0 predictions and held-out order | Test added (commit `9a88c10`) |
| ST-I5 | Condition 5 (S3) is vacuous for every one-scale collapse arm | Accepted; A-1/A-2 already said so; it can only bite profile-changing candidates |

Minor findings are recorded in the review transcripts under `docs/wur_stage2b_reviews/` and were fixed where they touched code.

## Claim, as adjudicated

On DEV2B, a ridge regression of log g on the twelve Tier A descriptors, on the frozen shared-profile collapse, predicts held-out mu trajectories with P1 0.1349 against 0.1539 for the frozen pre-WUR symbolic pipeline forced to predict (12 percent relative; cluster-bootstrap 95 percent CI on the P1 difference [-0.027, -0.014]) and 0.1523 for the mass-only null. The frozen pipeline does not beat the mass-only null. The 24-descriptor ridge is not distinguishable from the 12-descriptor ridge. The improvement is attributable to replacing the symbolic search, selector and gate with a regularised linear regressor, not to a new law or representation. The descriptor set explains about half the variance of the scale; the other half is real, compound-specific and un-encoded.
