# MURU-WUR-v2: adversarial review adjudication

Five independent reviews ran on commit `52967a0` (reports in `docs/wur_v2_reviews/`): scientific red team, leakage audit, statistical review, implementation review, reproducibility review. Every Critical and Important finding is adjudicated here. Decisions that change protocol reading are amendment **A-3** (appended to `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md`).

## Reproducibility (clean)

An isolated worktree rebuilt the spectra, population, folds, representations, the PRIMARY and STRICT out-of-fold runs from an empty cache, the serialized candidate and Experiment 1 part A. Every rebuilt output is byte-identical to the committed copy (only timing fields differ); PRIMARY P1 0.13054598985817814 and 0.11599941847410669 reproduce exactly; results are identical at 1, 4 and 8 threads. Limitation: same machine and package versions.

## Leakage (no leak found)

A poison test replaced every held-out mu with random values for 9 models on 4 folds: predictions, selections and inner losses were bit-identical in all 36 cases. No key, scaffold group or strict cluster straddles folds; all 95 cached runs recompute exactly; the root_fold fix is effective.

## Critical

**RT-1 (red team; for external design).** Development contains no test of fixed-eV QTOF CID, the energy coordinate changes exactly the mass-dominated part of the model, chemistry reweighting to MultiMS2 structures alone predicts a ratio of 0.92 to 0.93, and library QC censors precursor-rich low-energy spectra. *Accepted.* The external protocol (a) uses the design frame and raw centroid mzML, never library membership or QC fields; (b) applies one frozen mass-aware energy adapter identically to candidate and comparator; (c) pre-registers the expected effect (ratio about 0.92 to 1.00 once instrument transfer is included) and a primary rule with power stated for it; (d) states in advance that a null external result does not refute the development finding and a positive one does not confirm the 11 percent.

## Important

| Id | Finding | Decision |
|---|---|---|
| S-01, L-01 | Admission criterion c4 was never recorded for EXP08B; read literally it fails (3 of 5 corrected joint permutations at 0.998 to 0.999 against TA_RIDGE) | **A-3.1** c4 is restated for models that contain the Tier A block: every permutation must lose to the unpermuted arm, and the mean permuted ratio must not fall below the arm's empty-fingerprint null by more than its bootstrap noise. EXP08B: all five permutations lose by 11 percent; mean 1.0003 against an empty-block null of 0.9989 (leakage review). **c4 passes as restated; the literal failure is disclosed.** EXP08C and EXP08E are unaffected in ordering |
| S-02, L-11 | No selection adjustment over 10 arms; the top arms are not separable | Accepted. The candidate's development estimate is reported as ratio 0.889, conditional 95 percent [0.865, 0.911], **ten-arm simultaneous [0.860, 0.918]**, selection optimism about 0.006, i.e. **about 10 to 11 percent**; EXP08B versus EXP08E is 0.993 [0.976, 1.007]; the choice among the top arms rests on the simplicity rule, not on data. EXP07 (ION_ENV) does not survive the simultaneous bound (upper 1.002) and is described as unadjusted-admitted |
| RT-2 | About half the gain is atom-type composition (radius-0 Morgan invariants); radius 1 matches radius 2 (1.007 [0.993, 1.020]) | Accepted as the scientific description: **"atom-type composition plus first-shell local environments"**. The candidate is **not** switched to radius 1: radius 1 is a post-hoc reviewer diagnostic, not a registered arm, it has the same model class and dimension, and it is not better. Switching after seeing it would be representation shopping |
| RT-3 | The connectivity-specific gain shrinks with novelty; conazoles carry 22 percent of the PRIMARY gain | Accepted. STRICT (7.4 percent) is quoted as the new-chemistry development estimate; similarity-stratified results are reported with the headline; the claim is scoped to chemistry covered by the training library |
| RT-4 | MultiMS2 scaffold-new compounds are drug-like screening chemistry, not natural-product-like | Accepted. Erratum added to the census report; external scope reads "low-similarity drug-like screening compounds" |
| RT-5 | Repeat floors are 30 to 32 percent of the candidate's trajectory MSE, not 6.5 to 10 percent (the latter was against Tier A log g error) | Accepted. The practical floor is P1 about 0.065 to 0.07; the remaining headroom above the floor is about 0.045 in P1 |
| L-02 | Census QC-pass membership is an outcome proxy | Accepted. The external protocol prohibits any use of library membership, replicate counts or QC fields for populations, exclusions, strata or anchors |
| S-03 | EXP04's R^2 result is largely mechanical | Accepted. Section 1 of the gate is corrected: EXP04 shows only that the survival/depth split carries no extra information in a regression that is mechanically dominated by total mu; it is not mechanistic evidence. The supplement's script is committed (`scripts/wur_v2/exp04b_supplement.py`) |
| S-04 | External statistical prerequisites | Accepted; adopted in the external protocol (section 6) |
| I-1, L-08 | Run caches not keyed to inputs | **Fixed.** Every cached run now records a sha256 of the outcome matrix and all representation files; a mismatch forces recomputation and raises `StaleCacheError` unless the result is identical. All 95 cached runs were revalidated identical (`scripts/wur_v2/backfill_cache_fingerprints.py`). Test `test_cache_is_invalidated_when_inputs_change` |
| I-2 | Candidate JSON lacked feature provenance | **Fixed.** Each serialized model carries `feature_spec` (Tier A order and scales, Morgan radius/size/counts/chirality/transform, RDKit version) and canary predictions for five reference compounds; `predict_log_g` refuses to run if either no longer reproduces. Tests added. Candidate hashes changed accordingly (pre-freeze) |

## Minor (decisions in brief)

- L-03: charged N-oxide scaffolds split 10 of 21 N-oxide/free-base pairs across PRIMARY folds (headline 0.889 to 0.8899). Development partitions stay frozen; the external novelty filter additionally excludes a compound whose charge-neutralized scaffold matches any development scaffold.
- L-04, L-05, S-14: the bridge was fitted on 124 development compounds, making EXP11's cross-instrument reproducibility and EXP13's train-on-WUR result partly circular; EXP13 source transfer is not scaffold-disjoint (25 and 42 percent of test scaffolds seen). Disclosed; these are not used as transfer evidence.
- L-06, M-1: EXP11's R^2 0.18 was not fully nested; clean labels give 0.1795. The A-2 licence stands.
- L-09: the manifest flag `confirmation_keys_present: 0` is vacuous by construction; 41 confirmation keys are in v2 through WUR copies (already stated in the registry), 20 more share a scaffold. Raw-mix counts are 40 compounds in the table, 39 in Phase 1, 30 non-confirmation, 26 with complete duplicates.
- L-10, RT-9: the permutation control permutes rows across all compounds and shows a structure-label link only, not "local connectivity".
- S-05: the shape arm is reported as "1.8 percent (1.2 to 2.4), below the pre-set bar".
- S-06: trust random PR-AUC baseline is about 0.068; calibration-in-the-large is -0.09 (the -2.15 was a joint-fit intercept). "Trust fails" stands.
- S-08, S-09, RT-6, RT-7, S-13: EXP02 noise share interval 4 to 12 percent; EXP03's 72/92 split is an attribution choice, the linear derivative-amplification mechanism is not supported (E30 scale RMSE is not lower for low-sensitivity compounds), so the conclusion is "scale misplacement dominates E30 error under an oracle-scale decomposition"; "Tier A representation-limited" rests also on the red team's quadratic-Tier-A control (at most 3.3 percent).
- RT-8: against quadratic Tier A the candidate's gain is 8.2 percent (PRIMARY) and 5.9 (STRICT).
- S-10, S-11: GIANT is one realization; bootstraps for S1 [0.858, 0.906], S2 [0.862, 0.915], LCSB [0.850, 0.918], WUR [0.861, 0.918] (statistical review).
- M-3 kernel unknown-key: fixed (raises). M-6 support flag: `candidate.supported` added. M-2, M-4, M-5, M-7 to M-13: documentation/robustness; M-12 (pre-fix EXP08A permutation numbers) is superseded by EXP08P.
- T-1 test gaps: new `tests/wur_v2/test_v2_data_contracts.py` (population and partition hashes, precursor-included endpoint, undefined depth, archive-copy collapse, energy-map direction, kernel key guard, cache invalidation) plus candidate provenance tests.
- S-15: dirty-tree ledger entries: the admission results were revalidated from committed code by the reproducibility review.

## Outcome

No finding invalidates the development result or the candidate. **`V2_TA_MORGAN_JOINT` is confirmed as the v2 final candidate** under the restated c4, with the corrected description: a Tier A ridge augmented by atom-type composition and first-shell environments from Morgan counts, about 10 to 11 percent lower pooled trajectory RMSE than the refitted v1 family on scaffold-held-out development folds (7.4 percent on strict clusters), absolute failures 10.3 to 6.3 percent, no trust output, one-scale shared profile.
