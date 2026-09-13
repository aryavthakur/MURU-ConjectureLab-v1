# MURU-WUR-v2 adversarial review: leakage and exposure bookkeeping

Reviewer role: leakage auditor. Commit under review: `52967a0` (branch `claude/muru-wur-v2-generation-b2ffa1`). Scope: every path by which information about a held-out compound or a held-out outcome could reach the model that predicts it, and every place where exposure bookkeeping could be wrong. Evidence below is either code read at `52967a0` or a check I ran. All checks ran from the worktree with `PYTHONPATH=src`, `OMP_NUM_THREADS=2`, and wrote nothing under `artifacts/` (scripts and logs are in the session scratchpad; the engine functions `run_cv`, `run_fold` and `_run_selected_folds` were called directly, never `runner.run`, which writes caches).

Note: while this review ran, other untracked files appeared in the worktree (`MURU_WUR_V2_MULTIMS2_EXTERNAL_PROTOCOL.md`, `src/muru/wur_v2/external_guard.py`, `external_mzml.py` and their tests). They are not part of `52967a0` and are not reviewed here except where the census section refers to the population definition.

## Summary

I found no leakage path from a held-out compound's outcome into its own prediction in any development number reported at `52967a0`. The strongest evidence is a poison test. I replaced every held-out mu with random values and reran whole folds for nine models. The held-out predictions came out bit-identical, and so did the selected configuration and every inner loss (section 4). I also recomputed all 95 cached out-of-fold runs from scratch with the current code. Every run matched its cache exactly, so no stale cache feeds a reported number (section 9). Identity and scaffold grouping hold on the real data: no connectivity key, scaffold group or strict cluster straddles folds in any partition, and there are no parent-key or canonical-tautomer collisions.

The findings are about three things: records, residual structural similarity across PRIMARY folds, and low-dimensional or within-training optimism.

- Important: the selected candidate has no recorded outcome for admission criterion c4. Its corrected permutation controls fall below 1.00 against TA_RIDGE for 3 of 5 seeds, which the coded c4 rule would count as a failure. My control run shows those values sit exactly at the null of the joint architecture, so this is not leakage. The record still needs an adjudication.
- Important: the MultiMS2 census saw compound-level library-QC membership by energy. That membership is an outcome proxy, and the stored library-frame key lists must stay quarantined from any future population, exclusion or stratification decision.
- Minor: nine findings. They cover N-oxide and charged-scaffold splits, the frozen bridge's two-parameter dependence on development outcomes, a source-transfer stress test that is not scaffold-disjoint, the not-fully-nested EXP11 predictability estimate, within-training optimism in cross-fitted arms, cache keys without a code or data hash, several misleading manifest fields, a wording deviation in the permutation control, and program-level selection on the same PRIMARY predictions.

## 1. Identity leakage

**Code.** `population.build` assigns `group_key` from the source connectivity key: the LCSB `inchikey_first_block` or the WUR `connectivity_key`. It also computes `parent_key = identity.parent_connectivity_key(smiles)`. The parent step picks the largest organic fragment and runs the Uncharger. A key measured on both instruments contributes one aligned trajectory: the LCSB one. `long_aligned` takes WUR rows only for keys not in LCSB-DEV, and the builder raises on any duplicated (key, energy) cell.

**Checks run.**

- `parent_key == group_key` for 1,325 of 1,325 compounds, and the 1,325 parent keys are unique. Two source keys never collapse to one parent.
- All 1,058 distinct SMILES on WUR positive spectrum rows (`wur_pos_spectra.parquet`, 12,432 rows) give a parent connectivity key equal to their assigned key. No acquisition sits under the wrong identity.
- Stereo-free parent SMILES: 0 duplicates across keys.
- The 124 keys measured on both instruments carry one aligned trajectory each. The WUR copies are used only in the Experiment 2, 5 and 11 diagnostics and in the bridge (section 9).
- Recomputing all six partitions from `compounds.csv` with `folds.all_partitions` reproduces `folds.json` exactly (equal assignments, equal sha256).

**Verdict.** Clean. The only fold-level identity risk would be two keys for one parent, and it does not occur.

## 2. Scaffold and near-duplicate leakage

**Checks run** (script `check_identity.py`, `check_sim.py`).

- Groups straddling folds: PRIMARY, PARTITION_S1, PARTITION_S2 and GIANT have 0 straddling `scaffold_group` values. STRICT has 0 straddling `strict_cluster` values and 0 straddling `scaffold_group` values.
- There are 88 acyclic singletons, each its own group, so an acyclic homologue series can span PRIMARY folds. Strict clusters absorb those at Morgan-count Tanimoto of 0.55 or more.
- Maximum cross-fold MinMax (count Tanimoto) similarity per compound:

| Partition | median | >= 0.99 | >= 0.9 | >= 0.8 | >= 0.7 |
|---|---|---|---|---|---|
| PRIMARY | 0.420 | 0 | 4 | 21 | 70 |
| PARTITION_S1 | 0.434 | 0 | 2 | 19 | 71 |
| STRICT | 0.365 | 0 | 0 | 0 | 0 |
| RANDOM | 0.548 | 0 | 20 | 104 | 288 |

- **Charged scaffolds (finding L-03).** `scaffold_group_v2` keeps formal charge. An N-oxide `[N+]([O-])` cannot be neutralized by the Uncharger, and the Murcko step then leaves `[NH+]` in the ring. Quaternary nitrogens behave the same way.
  - 31 compounds sit in 17 groups whose scaffold string carries a charge.
  - The population has 58 N-oxides. For 21 of them, the reduced free base is also in the population. 10 of those 21 pairs are split across PRIMARY folds and 0 across STRICT. Most are pyrrolizidine alkaloids, for example the `C=C1CCCC(=O)OCC2=CCN3CCC(OC1=O)C23` / `...CC[NH+]3...` pair in folds 3 and 4.
  - When I neutralize the scaffold (reduce N-oxides, strip charges), 765 groups become 751. 11 of the merged groups (37 compounds) straddle PRIMARY and 1 straddles STRICT.
  - One further pair differs only in how the ring tautomer is drawn: the pyrazolotriazinone sulfonylpiperazines `O=c1[nH]c(...)nc2cn[nH]c12` and `O=c1nc(...)[nH]c2cn[nH]c12`, with 2 compounds each in PRIMARY folds 3 and 1.
- **Impact on the headline.** PRIMARY cached out-of-fold predictions, TA_MORGAN_JOINT against TA_RIDGE. With all compounds, the P1 ratio is 0.889. Removing the 21 compounds with cross-fold maximum similarity of 0.8 or more gives 0.8899, and removing the 4 at 0.9 or more gives 0.8887. By similarity band, the ratio is 0.859 (n=4) at 0.9 or more, 0.743 (n=17) at 0.8 to 0.9, 0.909 (n=49) at 0.7 to 0.8, 0.838 (n=374) at 0.5 to 0.7, and 0.911 (n=881) below 0.5. The near-duplicates do gain the most, but they are too few to move the pooled number. STRICT, which has no cross-fold pair at 0.55 or more, still gives 0.926.

**Verdict.** The protocol's grouping holds as written. The residual charged-scaffold splits are a small, real optimism in PRIMARY, and STRICT already bounds it. The same scaffold function is used for the MultiMS2 scaffold-novelty filter, so the external novelty test inherits the blind spot.

## 3. Stereo and tautomer leakage

- The identity unit is the InChIKey first block, so stereoisomers and E/Z isomers share one key and one fold. Per the registry, WUR isomer acquisitions (222 cells, 42 keys) are aggregated by the median under their key. They can therefore never be split across folds.
- All features ignore stereochemistry: Tier A, Morgan and atom pairs are built with `includeChirality=False`, and MACCS carries no stereo information.
- Canonical tautomer check (RDKit `TautomerEnumerator.Canonicalize` on the stereo-free parent, then the InChIKey first block): 0 collisions across the 1,325 keys.
- The only tautomer effect found is at scaffold-string level (one pair, section 2).

**Verdict.** Clean.

## 4. Target and profile-target leakage

**Code.**

- The outer fold is fit by `engine.trainset(data, train_keys)` -> `collapse_for`. That call filters `data.long` to the training keys before `fit_collapse`, so Phi, the log g labels, the unit-geometric-mean gauge (`log_g -= log_g.mean()` over the training compounds) and the curvature weights all come from training compounds only.
- Inner selection builds 4 grouped inner training sets. Each refits its own collapse, predicts inner-validation trajectories through the inner Phi, and scores against `data.Y.loc[va]`, which covers training compounds only.
- The held-out prediction is `mu_from_log_g(ts.fit, model.predict(test_keys))` and reads only features.
- B0 is the per-rung training mean.

**Checks run** (script `recompute.py poison`).

- **Poison test.** For each (partition, fold) in PRIMARY 0 and 2, STRICT 1 and GIANT 0, I ran `run_fold` twice for nine models: TA_RIDGE, TA_RIDGE_V1SEL, B1_MASS_ISOTONIC, TA_MORGAN_JOINT, TA_THEN_MORGAN, MINMAX_KRR_MORGAN, KNN10_RESIDUAL_MORGAN, JOINT_PLUS_SHAPE and TA_MORGAN_JOINT_PERMUTED_s0.
  - The first run used the real data. Before the second, every held-out mu in `long` and `Y` was replaced by uniform random values, and the collapse cache was cleared before each run.
  - Result in all 36 cases: held-out predictions bit-identical (max abs difference 0.0), selected configuration identical, and every inner loss identical.
  - Each fold made exactly 5 collapse fits. None of the key sets touched a held-out key, and the outer set equalled the training keys.
- **Inner-set check** (PRIMARY fold 0, joint model): each of the 4 inner collapse sets equals the training keys minus exactly one inner fold (795 compounds), and the inner-validation scaffold groups are disjoint from the inner-training groups.
- The existing unit tests (`tests/wur_v2/test_v2_engine_nesting.py`) pass.

**Verdict.** Clean for outer held-out compounds. Within-training approximations are listed in section 7.

## 5. Feature filtering and standardization leakage

- **Morgan.** `representations.morgan_counts` is a pure per-molecule function (radius 2, 2,048 bits, no chirality, `log1p`), with no frequency filter and no supervised bit selection. The same holds for atom pairs and MACCS. The MinMax kernels are precomputed over all compounds from structure only. Fitting uses the training-by-training block and prediction the test-by-training block.
- **Tier A.** `tier_a_scaled` divides by the fixed `protocol.SCALE` constants. The parquet equals a fresh `tier_a_scaled(cov)` (max difference 0.0).
- **JointRidge standardization.** Mean and SD come from `ts.X(base)` over `ts.keys` only, inside both outer and inner training sets.
- **Feature poison test** (PRIMARY fold 0). I replaced the held-out rows of TIER_A and MORGAN with random values. For JointRidge and TwoStage the selected configuration and all inner losses stayed identical, while the held-out predictions changed (max 0.85). Held-out features therefore enter only prediction.
- **Strict clusters** are built over all 1,325 compounds from structure only, which is permissible.
- **Trust signals** (`trust.signals`) standardize Tier A on the training keys and exclude self-similarity.

**Verdict.** Clean.

## 6. Hyperparameter leakage

- The grids (`RIDGE_ALPHAS_TA`, `RIDGE_ALPHAS_FP`, `BLOCK_WEIGHTS`, `KERNEL_ALPHAS`) were introduced in `e6e25d1` and never changed afterwards (git log -p on `models.py`). They match protocol section 9, which was frozen in `7674ab3`. The ION alpha grid and the shape grid were committed before their arms ran (`265388e`, `3861837`).
- All development out-of-fold runs select by nested inner trajectory loss (section 4). The PRIMARY joint configurations vary by fold: (0.3, 0.1) for folds 0, 2 and 3, and (3.0, 0.3) for folds 1 and 4.
- `candidate.fit_all` selects on all 1,325 compounds and passes a training key as the dummy test key. That is appropriate for deployment and touches no development number.
- **Program level (L-11).** The candidate was chosen by comparing arms on the same PRIMARY, STRICT and GIANT out-of-fold predictions that report its performance. Amendments A-1 and A-2 were written after the results were visible. No untouched internal holdout remains. Protocol section 7 and amendment A-1 both disclose this, and the selection margin (11 percent over TA_RIDGE, with 12 arms) is large against the between-arm differences (under 1 percent among the top four). It is still a reason to treat 0.1160 and 0.889 as optimistic.
- The AF tolerance of 0.20 was derived from the whole-population per-rung SD of mu, and the protocol discloses this. It shapes a metric threshold, not a model.

## 7. Two-stage, residual, kNN, shape and trust cross-fitting

**Code read.**

- **TwoStage (EXP08C) and KNNResidual (EXP09C).**
  - The stage-1 alpha is selected by `RidgeV1Selection` on all training compounds.
  - Residuals are then cross-fitted over 4 grouped inner folds (seed `outer_fold + 777`) using that alpha, and all of it rests on labels and Phi from the one training collapse.
  - The residual target is therefore out-of-sample with respect to the stage-1 ridge coefficients, but not with respect to the alpha choice or the collapse labels (L-07).
  - The kNN correction for a query averages the cross-fitted residuals of training neighbours only.
- **ShapeCorrectedJoint (EXP12).**
  - The basis is PC1 of training residuals. Coefficients are cross-fitted with sub-TrainSets that share the outer training collapse.
  - The joint configuration comes from `joint_cfgs[ts.root_fold]`, the configuration the nested joint run selected on the whole outer training set. When inner sets select the shape alpha, the joint configuration has already seen those inner-validation compounds (L-07). None of this reaches the outer test set.
- **root_fold bug.** Before `7943711`, `_cfg` mapped fold 0's inner sets (outer_fold 0 to 3) to outer folds 0 to 3. Fold 0's shape-alpha selection therefore used joint configurations that folds 1 to 3 had selected on training sets containing fold 0's test compounds: a real, if tiny, outer leak into selection. The fix makes inner sets carry `root_fold`, and a regression test covers it.
  - I verified the cached `JOINT_PLUS_SHAPE` PRIMARY run was produced by post-fix code. Its cached fold-0 inner out-of-fold predictions match a fresh post-fix recomputation exactly (max diff 0.0) and differ from a pre-fix recomputation (max diff 0.069). Fold-0 inner losses also differ between the two, for example 75.015 post-fix against 74.502 pre-fix at alpha 10.
  - The held-out predictions happen to coincide for fold 0 because both versions select alpha 10.
  - All six shape caches have `created_utc` 01:27:08Z to 01:27:38Z, after the fix commit time (01:27:00Z), and the EXP12 ledger row carries `code_sha` `7943711`.
- **Trust (EXP10, `scripts/wur_v2/exp10_trust.py`).**
  - Held-out signals are computed against the outer training set from structure, out-of-fold log g predictions and the training Phi.
  - Trust-model training rows are the outer-training compounds' inner cross-fitted RMSE. They take inner out-of-fold predictions from the cached runs, filtered to `outer_fold == f`, with signals computed against each inner training set.
  - The inner split is reproduced with the engine's own seed and key order.
  - The inner out-of-fold predictions are those at the configuration selected on the same inner losses, a mild within-training optimism in the trust target (L-07). Thresholds come from training quantiles.
  - No held-out spectrum enters a signal. The trust result was negative anyway.

**Verdict.** No outer leakage in the reported runs. The within-training approximations bias inner selection mildly toward optimism; they are not leakage into the test set.

## 8. Permutation controls (EXP08P)

- **Seed bug.** The seed-free cache of the permuted block was fixed in `912cf74` and has a regression test (`test_permutation_seeds_are_distinct`).
  - `EXP08A_MORGAN_RIDGE.json` still shows the buggy controls: five identical 1.3967 values. The corrected controls in `permutation_controls_corrected.json` are distinct, and their seed 0 value equals the old one, as expected.
  - Corrected runs are cached under the tag `_v2fix`, so no buggy cache can be picked up. No untagged permuted caches exist on disk.
- **Implementation (L-10).** `PermutedFeatures` permutes rows across all 1,325 compounds, test rows included. Protocol section 9 says "across training compounds". A global permutation is still a valid null because it breaks every structure-label link, but the wording differs.
- **Selected candidate (L-01).**
  - `EXP08B_TA_MORGAN_JOINT.json` has no c4 criterion, because `run_arms.py` attached controls only to EXP08A. The EXP08P ledger row says "c4 re-read for EXP08A/B" but records no outcome for B.
  - The corrected joint controls are 0.99865, 1.00464, 1.00208, 0.99788 and 0.99817 against TA_RIDGE.
  - `admission.evaluate` codes c4 as `v > primary_ratio and v >= 1.0` for every seed, so 3 of 5 seeds fail it. The protocol text requires that the control "does not beat TA_RIDGE".
- **Control check** (`zero.py`, no writes). The joint architecture with a zero fingerprint block, which is just training-standardized Tier A on the fingerprint alpha grid, gives a PRIMARY ratio of 0.9989 against TA_RIDGE.
  - The permuted controls are therefore centred on the architecture's own null. The whole 11 percent gain is attributable to the structure-label link, which is what a leakage-free pipeline predicts.
  - A pure random-count block gives 0.9937, which is also null-sized.
  - The poison test in section 4 included the permuted joint.

## 9. Bridge, source and exposure bookkeeping

- **Bridge (L-04).**
  - The frozen Stage 1 map (a = -5.9555, b = 0.8618, from `wur_bridge_gate.json`) was fitted by differential evolution. The objective was the per-energy median signed WUR-LCSB delta over population B: 124 keys that are LCSB-primary v2 development compounds spread over all folds.
  - The map transforms the aligned targets of the 886 WUR-primary compounds. A held-out population-B compound's LCSB and WUR outcomes therefore shape, through 2 global parameters, the training targets of WUR-primary compounds in other folds. Two medians-based parameters cannot carry per-compound information, and the transformation is common to every arm, so its effect on the development ratios is negligible.
  - It does create partial circularity in:
    - EXP02 R2: cross-instrument log g ICC 0.94. Disclosed in the script note.
    - EXP05: per-rung equivalence within 0.02. Disclosed as "partly by construction".
    - EXP11 R2: shape-coefficient reproducibility r = 0.85 on the same 119 compounds. Not disclosed.
    - EXP13 "train on WUR, predict LCSB". The WUR training targets were aligned by a map fitted partly on the test compounds' LCSB outcomes. Not disclosed.
  - For an external claim, the candidate's energy coordinate is LCSB NCE, and WUR-primary training targets depend on the map. An external instrument therefore needs its own adapter, fitted on anchors that are disjoint from validation compounds.
- **Source (L-05).**
  - No candidate uses `primary_source`. It appears only in the diagnostic `DIAG_TA_RIDGE_SOURCE_X_MASS`, which is labelled non-deployable.
  - `precursor_mz` for WUR-primary compounds is the median observed precursor mass. It carries adduct identity (20 [M+NH4]+, 8 [M+Na]+, 8 [M]+), which counts as acquisition metadata known before measurement, not an outcome.
  - The EXP13 source-transfer stress test is not scaffold-disjoint: 25.3 percent of WUR test compounds and 42.4 percent of LCSB test compounds have their scaffold group in the training source (`exp13_results.json`). It also inherits the bridge dependency above.
  - The decision gate lists it among sensitivities that "keep the joint model ahead" without either caveat.
- **LCSB confirmation set (L-09).**
  - LCSB confirmation spectra are absent from v2. The corpus is filtered by key, and `exposure_manifest` asserts no confirmation key outside WUR-SEALED.
  - However, 41 of the 110 confirmation keys are v2 development compounds through their WUR-SEALED copies. Of the remaining 69, 20 share a v2 scaffold group, so only 49 are identity- and scaffold-new.
  - The registry says the set cannot support an independent claim, which is correct. Two records still mislead:
    - `population_manifest.json` field `confirmation_keys_present: 0` is vacuous. The builder tests membership in `conf & lcsb_dev`, which the preceding line asserts to be empty.
    - The exposure class "prohibited-excluded" understates that 41 of the set's identities have now been fitted.
- **Negative mode.** All WUR positive spectrum rows carry a positive scan filter, and every LCSB corpus key has positive-mode trajectories. The excluded negative populations share keys with the v2 population (WUR-NEG-DEV 26, WUR-NEG-D6-EXCLUDED 20, LCSB-NEG 171). Their spectra are unused, but any future negative-mode claim is not compound-disjoint from v2.
- **Raw mixes (Experiment 2).** `exp02_repeatability.py` and `exp11_shape_oracle.py` drop confirmation keys before use. Counts are inconsistent across records:
  - `raw_branch_merged.parquet` has 40 keys: 30 non-confirmation, all in v2.
  - `raw_branch_scans.parquet` (the exposure manifest) has 39.
  - The registry says 29 usable; the Experiment 2 docstring says 30.
- **External pretraining.** None. No torch, transformers or tensorflow is importable, and no source or script references a pretrained model. All representations are RDKit functions of the SMILES.

## 10. MultiMS2 census outcome-blindness

- **What was seen.**
  - The peak MGF was refused by the denylist, and no mzML or `.scans` table was downloaded. Two TSV columns (`LIBQUALITY`, `SELFIES`) were dropped unseen.
  - The census did retain compound-level membership of the QC-filtered released library by collection, adduct and energy. The survivor key lists are stored in `multims2_census.json` (library frame, 3-rung and 40/60 chains), along with per-rung replicate scan counts (1 to 130), the README filter cascade, and two aggregate passages from the QC section.
  - The QC drops spectra with fewer than 3 signals or low explained intensity, which at 20 V are the precursor-dominated ones. A design-frame compound that lacks a released 20 V spectrum is therefore more likely to be precursor-dominated at 20 V. That is a per-compound outcome proxy.
- **Could it bias a future validation population? (L-02)** Yes, if library membership, the replicate counts or the choice between chains were allowed to influence population definition, exclusions, strata, anchors or energy-adapter choices. The census says this itself and recommends the design frame. The draft external protocol in the worktree (uncommitted) defines VALIDATION from design-frame step 10, which is the right frame.
  - Remaining risks: the scaffold-novelty filter uses `scaffold_group_v2`, which has the charged-scaffold blind spot of section 2; and the stored library-frame lists sit next to the design-frame lists in the same JSON.
- **Action.** Declare the library-frame survivor lists and replicate counts outcome-conditioned in the freeze document, forbid their use in any selection or stratification, and add a neutralized-scaffold (N-oxide-reduced, charge-stripped, canonical-tautomer) novelty check to the population definition before the population hash is frozen.

## 11. Cache contamination

- **Keys.** `runner.run` keys a cache file by `model.id + tag + assignment_sha256[:12]` only. There is no code sha, grid, feature-content or data hash, and `engine._COLLAPSE_CACHE` is keyed by the sorted training key set only (L-08). No script at `52967a0` mutates `data.long` or `data.Y` in-process. The TA_RIDGE cache is shared between `load_data()` and `load_data(False)` plus `tier_a_scaled`, but the two feature blocks are identical.
- **Git history and timestamps.**
  - Tracked run files were each committed once, in the commit that follows their `created_utc`.
  - The only engine or model changes after any run are `7943711` (root_fold, which affects only the shape arm) and `3861837` (adds the shape class).
  - The shape arm caches are gitignored and untracked (`.gitignore` `artifacts/*`; the other runs were force-added), so the EXP12 numbers rest on untracked files.
- **Full recomputation** (script `recompute.py cache`, log `cache_log.txt`). All 95 cached runs were recomputed from scratch: every model on every partition, including the permutation controls, EXP07, the diagnostic source model and the shape arm.
  - Result: 95 of 95 match their caches exactly. The maximum absolute difference is 0.0 for mu and 0.0 for log g, the selected configurations are equal in every fold, and the held-out index sets are equal. Every model id on disk had a reconstructable factory.
  - This covers every number in the decision gate that reads a cache, including EXP10 and EXP13, which read the cached TA_MORGAN_JOINT and TA_RIDGE runs, and EXP12, which reads the untracked shape caches.
- **Verdict.** No reported number uses a stale cache. The key design would allow one after a future code change.

## Findings

| Id | Severity | Finding | Evidence | Action |
|---|---|---|---|---|
| L-01 | Important | The selected candidate EXP08B has no recorded c4 (permutation) admission outcome. Its corrected joint controls are 0.9987, 1.0046, 1.0021, 0.9979 and 0.9982 against TA_RIDGE, so the coded c4 rule (`v >= 1.0` for all seeds) fails for 3 of 5. The ledger says "c4 re-read for EXP08A/B" with no result, and the gate table says "admitted". Not leakage: a zero-fingerprint joint ridge gives 0.9989, so the controls sit at the architecture null. | `EXP08B_TA_MORGAN_JOINT.json` (no c4); `permutation_controls_corrected.json`; `admission.py` c4; ledger row V2-EXP08P; scratchpad `zero.py` | Record an explicit c4 adjudication for EXP08B in the adjudication document: define the null as the joint architecture with a null fingerprint block (0.9989), state that the controls do not beat it, and note that the literal coded rule fails. No rerun needed. |
| L-02 | Important | The MultiMS2 census retained compound-level QC-pass library membership by energy and replicate scan counts. The QC censors precursor-rich spectra, so membership is an outcome proxy that could bias a future population, exclusion, stratum, anchor or energy-chain choice. | `MURU_V2_MULTIMS2_OUTCOME_BLIND_CENSUS.md` sections 6 and 8; `multims2_census.json` library_frame survivor lists | In the external freeze, declare the library-frame lists and counts outcome-conditioned and forbid their use. Define the population from the design frame only (the draft does), and hash it before any decode. |
| L-03 | Minor | Stereo-free scaffolds keep formal charge, so N-oxides and quaternary N get `[NH+]` scaffolds. 10 of 21 N-oxide/free-base pairs are split across PRIMARY folds (0 in STRICT). 11 neutralized-scaffold groups (37 compounds) straddle PRIMARY, and one tautomer-drawn scaffold pair splits. Impact: ratio 0.889 becomes 0.8899 after removing the 21 compounds with cross-fold similarity of 0.8 or more. The same scaffold function feeds the MultiMS2 novelty filter. | scratchpad `check_identity.py`, `check_sim.py`; `identity.scaffold_group_v2` | Disclose in the adjudication. Use a neutralized scaffold (N-oxide reduction, charge strip, canonical tautomer) for the external novelty filter and any future grouping. Keep STRICT as the guard. |
| L-04 | Minor | The frozen bridge (2 parameters) was fitted on outcomes of 124 LCSB-primary development compounds spread over all folds and transforms the targets of the 886 WUR-primary compounds. Held-out population-B outcomes therefore influence training targets globally. Effect on ratios is negligible, but it makes EXP11 R2 (r = 0.85) and EXP13 train-WUR/predict-LCSB partly circular, and these are undisclosed (EXP02 R2 and EXP05 are disclosed). | `wur_bridge_gate.json` population_b; `population.build`; `exp11_shape_oracle.py`; `exp13_candidate_stress.py` | Add the circularity note to EXP11 and EXP13 in the adjudication. Any external claim uses an adapter fitted on anchors disjoint from validation. |
| L-05 | Minor | The EXP13 source-transfer stress test is not scaffold-disjoint (25.3 and 42.4 percent of test compounds have a training scaffold) and inherits the bridge dependency. The gate document cites it as a passed sensitivity without these caveats. | `exp13_results.json` source_transfer; `MURU_WUR_V2_DECISION_GATE_1.md` section 5 | Caveat it in the gate reading, or rerun as a scaffold-disjoint source transfer if the claim is used. |
| L-06 | Minor | EXP11 predictability (R^2 0.18, which passed the 0.10 bar that justified A-2) trains on coefficients produced by other folds' models, which had seen the test fold. Alpha was chosen on an ungrouped 80/20 split of sorted keys. A-2 discloses this for the 0.1132 estimate only. No effect on the candidate: EXP12 was nested and failed. | `exp11_shape_oracle.py` c-predictability block; amendment A-2 | Extend the A-2 disclosure to the R^2 value. |
| L-07 | Minor | Within-training optimism. TwoStage and kNN residual targets are cross-fitted with a stage-1 alpha chosen on all training compounds and labels from the full training collapse. The shape arm's inner selection uses a joint configuration selected on the whole outer training set. Trust training targets are inner out-of-fold predictions at the configuration selected on those losses. None reaches the outer test set; the poison and feature-poison tests pass. | `models.py` TwoStage, KNNResidual, ShapeCorrectedJoint; `exp10_trust.py`; scratchpad `poison_test.csv` | Document as approximations. If those arms are revisited, nest the stage-1 alpha and the collapse inside the residual folds. |
| L-08 | Minor | Run caches are keyed by model id, tag and assignment hash only (no code, grid or feature hash), and the collapse cache by key set only. Shape arm caches are untracked. All 95 cached runs recompute exactly at `52967a0` (see section 11), so no reported number is stale. | `runner.run`, `engine.collapse_for`; `.gitignore`; scratchpad `cache_recompute.csv` | Add the code sha and a feature-block hash to the cache key (or store them in the meta and refuse on mismatch). Commit or hash-record the EXP12 caches. |
| L-09 | Minor | Bookkeeping. `confirmation_keys_present: 0` is vacuous: the true count of confirmation keys in v2 is 41, 20 more are scaffold-seen, and 49 are new. The LCSB-CONFIRMATION class understates this. Excluded negative-mode populations share 26, 20 and 171 keys with v2. Raw-mix counts disagree (40, 39, 30, 29). | `population.build` manifest line; `population_manifest.json`; `exposure_manifest.json`; `exp02_repeatability.py` docstring; registry | Fix the manifest field to count `group_key in conf`. Annotate LCSB-CONFIRMATION as "LCSB spectra excluded; 41 identities fitted via WUR". Reconcile raw-mix counts. |
| L-10 | Minor | The permutation control permutes feature rows across all 1,325 compounds, not "across training compounds" as protocol section 9 says. It is valid as a null. The EXP08A JSON retains the buggy identical controls (superseded in the ledger). | `models.PermutedFeatures._ensure`; protocol section 9; `EXP08A_MORGAN_RIDGE.json` | Correct the protocol wording in an amendment note. Point the EXP08A record to EXP08P. |
| L-11 | Minor | Program-level selection. Arms and amendments were chosen on the same PRIMARY, STRICT and GIANT out-of-fold predictions that report the candidate, with no internal holdout left. The AF threshold was derived from the whole-population outcome SD. Both are disclosed. | protocol sections 6, 7 and 16; decision gate section 8 | Keep reporting 0.1160 and 0.889 as selection-optimistic development evidence. The first unbiased number must come from the frozen external validation. |
