# Phase 5 Verification — Candidate/Reference Fairness and Selection Provenance

**Scope:** Code and record audit only. No model retraining, prediction experiment, or new performance comparison was run.

## Fairness question and conclusion

The external comparison is a paired evaluation of two frozen pipelines on the same measured-μ compounds, energy rungs, joint support-qualified population, pooled P1 metric, and scaffold bootstrap. It can estimate their comparative performance for this fixed endpoint and setting. It is **not** a feature ablation and cannot attribute the measured contrast to Morgan fingerprints alone. Feature preprocessing, feature dimension, candidate family, regularization grid, and model-selection history differ.

| Dimension | MURU-WUR-v2 candidate | Tier A reference | Interpretation |
|---|---|---|---|
| Development observations | Same WUR-v2 training corpus (1,325 compounds) | Same WUR-v2 training corpus | Common source population; no MSnLib outcomes used for fitting |
| Feature block | 12 Tier A + 2,048 hashed Morgan count features | 12 Tier A descriptors | The contrast is not a single-block ablation |
| Descriptor preprocessing | Divide by frozen descriptor-specific scale constants, then fold-specific training mean/SD standardization | Divide by frozen scale constants; no further fold standardization | Preprocessing differs |
| Morgan processing | Radius 2; 2,048 count bins; no chirality; `log1p`; candidate block multiplier 0.1 | None | Structural block exists only for candidate |
| Model | Curvature-weighted ridge with fitted intercept; selected α=0.3 | Curvature-weighted ridge with fitted intercept; selected α=0.1 | Both are ridge scale models but not identical designs |
| Hyperparameter space | α `{0.1, 0.3, 1, 3, 10, 30, 100, 300}` and Morgan weight `{0.1, 0.3, 1.0}` | α `{0.01, 0.1, 1, 10, 100}` | Candidate had a larger joint feature/penalty search |
| Development evaluation | Scaffold-grouped five-fold outer evaluation; four grouped inner folds; multiple candidate families | Same grouped evaluation procedure when used as the development baseline | Grouping limits same-scaffold leakage; it does not remove selection optimism across model families |
| Shared response profile | Same frozen 60-knot monotone profile and one-scale parameterization | Same | Shared target/trajectory scaffold |
| External use | Frozen model applied without refit | Frozen model applied without refit | Paired one-look external comparison |
| Support rule | Exclude compound if either model is unsupported at one or more evaluated rungs | Same joint rule | Analysis is conditional on support-qualified compounds |
| External metric | Same measured μ and pooled two-rung P1 | Same | Directly comparable endpoint on same cells |

The final external result compares complete, separately selected implementations. It supports a candidate-versus-reference prediction comparison under the frozen method. It does not identify the incremental value of fingerprints, standardization, the selected ridge penalty, or any individual candidate-selection decision. A causal feature claim would require a matched-design ablation that shares all other inputs, preprocessing, selection opportunities, and evaluation rules.

## Selection history and consequential qualification

The development protocol and final-freeze record show a multi-stage, 13-family candidate search, not a single prespecified candidate test. The final model was selected before MSnLib validation was opened, which preserves a useful external evaluation boundary. However, its development selection was not wholly fixed before all results were observed:

- The frozen protocol’s amendment A-3 is dated 2026-09-13, after all development results and five adversarial reviews were visible.
- A-3 restated admission criterion c4 for models combining Tier A with fingerprints. It explicitly says that literal c4 had failed for EXP08B and records that EXP08B was admitted under the restated criterion, with no other admission changes.
- The original `EXP08B_TA_MORGAN_JOINT.json` has no recorded c4 criterion result and an empty permutation-ratio field. The corrected permutation-control file is a separate artifact.
- The Phase 2 historical statistical review records the concern that c4 was not originally applied and gives corrected permutation ratios around the Tier A null. The later A-3 protocol provides the project’s formal adjudication, but it is a post-result rule amendment.

This disclosure does not by itself invalidate the one-look MSnLib estimate. It does mean that the manuscript’s current wording—“admitted under the documented simplicity rule”—is incomplete unless it also describes the timing and nature of A-3. Development performance and selection uncertainty should be treated as exploratory/selected-model evidence, not as a single fully prospective test. The external result should remain described as a comparison of the frozen pipeline after a multiexperiment search.

## Population and exposure boundaries

The primary external frame has 1,794 measured compounds, of which five are excluded by the frozen joint support rule; 1,789 compounds in 1,687 groups remain. This denominator and support rule are source-supported. The Phase 4 abstract phrase “five were outside either model’s profile support” is slightly ambiguous; a precise formulation is that a compound failed the joint rule if **at least one** model lacked support at one or more rungs.

The exposure record says sample 1 was accidentally exposed during parser preflight, was not scored, and was permanently excluded. The replacement sample was selected under an outcome-blind process after excluding recorded exposed compound keys and scaffolds, then analyzed once. This supports a separate external evaluation against recorded exposure controls. It does not demonstrate zero structural similarity to development compounds, guarantee the absence of every unrecorded exposure, or establish that the replacement sample represents all MSnLib chemistry. Because selection exclusions are at compound/scaffold level, the valid claim is bounded operational independence, not universal chemical independence.

The results are conditional on the 1,789 support-qualified compounds. The five out-of-support compounds are not missing data. Their descriptive inclusion sensitivity is reported elsewhere, but those predictions lie outside the profile support and do not replace the frozen primary estimand.

## Additional comparator fairness

The public-comparator analysis reduces FIORA-OS, ICEBERG, and GLACIER predicted spectra to the same scalar μ endpoint and computes P1 on a common 1,327-compound/1,254-group population. This is more comparable than a cross-task spectral-similarity contrast, but it still compares different trained systems, training data, preprocessing, prediction artifacts, energy conventions, and energy inputs. Ratios reverse for ICEBERG and GLACIER under the raw-NCE diagnostic. The result cannot establish full-spectrum fidelity, general model superiority, or a fair architecture-only comparison.

## Source paths and hashes

| Evidence | File | SHA-256 |
|---|---|---|
| Development protocol including amendments A-1–A-3 | `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md` | `33fe27cd986d09f3c53f6c7556852e451c8a67a667698a72fa4156bc35a01485` |
| Final candidate freeze | `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md` | `810fd271532ca176330eff8e0864eace2863b19898c6aed515740acac60000ae` |
| Decision Gate 1 | `MURU_WUR_V2_DECISION_GATE_1.md` | `0bd395a745ee80fddb8dbcdad48e3b8025de5193c6886c6ecbab974ed1c72a91` |
| Review adjudication | `MURU_WUR_V2_REVIEW_ADJUDICATION.md` | `bcb8a7712ddb3cd1d9fec11b8428d51322257f6af8ea59e60a26035b641e50a3` |
| EXP08B development record | `artifacts/wur_v2/exp08/EXP08B_TA_MORGAN_JOINT.json` | `9514c77c6d5b0c7a12c0baccb682df9e7da17153a07b2b0038d8fa70b7dd5f73` |
| Corrected permutation controls | `artifacts/wur_v2/exp08/permutation_controls_corrected.json` | `971a5441b7847cc1283ba5f4d06c5fb2323c635337e2121515831f4f9e5eaf5d` |
| Model implementation | `src/muru/wur_v2/models.py` | `572c0ed668ad277fe69ef7f7521d9e44696c722bd035b4464719352db6b70ee1` |
| Candidate model JSON (raw-file SHA-256) | `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json` | `f2ca0322ab75bbcc2ee91e66be07172966d0492060c7669107e1f9081edf58c3` |
| Candidate model canonical-JSON SHA-256 | `artifacts/wur_v2/candidate/candidate_manifest.json` entry `V2_TA_MORGAN_JOINT.sha256` | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` |
| Reference model JSON (raw-file SHA-256) | `artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json` | `de9afa119b80ddc46ffebf98783ac18bfa97c79f0e9e7adf57c300cd9fc6146f` |
| Reference model canonical-JSON SHA-256 | `artifacts/wur_v2/candidate/candidate_manifest.json` entry `V2_REF_TA_RIDGE.sha256` | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` |

The raw-file and canonical-JSON hashes intentionally differ: `scripts/wur_v2/build_v2_candidate.py` writes newline-terminated serialized JSON, while `muru.wur_v2.candidate.sha256_of` hashes canonicalized parsed JSON. Recomputing the canonical SHA-256 from each model JSON reproduces the manifest values. This is a representation difference, not evidence of an altered frozen model.

## Manuscript correction needed

Phase 4 Methods §2.2 reports the multiexperiment history but omits that A-3 changed c4 after development results and reviews were visible. It should identify this as a post-result amendment made before external sample access and explain the literal-versus-restated criterion boundary. The Discussion should continue to treat development uncertainty as unreproduced. The external result’s 0.9707 ratio and [0.9524, 0.9893] interval remain unchanged; neither indicates a 5% practical improvement.
