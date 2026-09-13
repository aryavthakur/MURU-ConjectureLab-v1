# MURU-WUR-v2 implementation review

Reviewer role: implementation reviewer (bugs that could change numbers or deployment behavior).
Commit reviewed: 52967a0 ("wur v2 run state: M5"), worktree recursive-executor-framework-07dd81.
Environment: /opt/miniconda3/bin/python3, RDKit 2026.03.5, pandas 3.0.5, scikit-learn 1.9.0, numpy 2.5.2, PYTHONPATH=src, OMP_NUM_THREADS=2.
Scope: src/muru/wur_v2/ (all modules), scripts/wur_v2/ (build scripts, exp01 to exp13, run_arms), the one-look guards in src/muru/wur_stage2/stage3.py and holdcheck.py, and src/muru/wur_bridge.py apply_energy_map as used by v2.
No existing file was modified. All scratch code and outputs are under docs/wur_v2_reviews/impl_scratch/. No cache file under artifacts/wur_v2/runs was written: fresh recomputations called engine.run_cv or runner._run_selected_folds directly.

Note on the working tree: at review time the worktree also carried untracked files that are not part of 52967a0 (src/muru/wur_v2/external_guard.py, src/muru/wur_v2/external_mzml.py, their two test files, MURU_WUR_V2_MULTIMS2_EXTERNAL_PROTOCOL.md). They appear to be a concurrent session's work in progress and were not reviewed. The census scripts under scripts/wur_v2/census/ were only skimmed for peak reads.

## Verdict

No Critical defect was found. Every reported number I re-derived reproduces exactly.

- All 30 cached runs I recomputed from scratch match their cache files to 0.0 in predictions, log g and selected configuration: PRIMARY for 18 models (including TA_MORGAN_JOINT, JOINT_PLUS_SHAPE and three corrected permutation controls) and GIANT for 12 models. The inner out-of-fold tables also match for the two models the brief named.
- Candidate-style serialization of PRIMARY fold 0 reproduces the engine's held-out mu to 6.7e-16 on all 265 held-out compounds. It also reproduces native WUR energies passed as a per-compound energy matrix to 4.4e-16.
- The energy map direction, precursor inclusion, D-AGG aggregation, the NaN (never zero) handling of fragment depth, identity normalization, group disjointness and the population and partition hashes all check out.

The two Important findings are latent risks that would change numbers or deployment behavior silently if the code or environment moved:

1. The run cache key is only the model id plus the assignment hash, so stale predictions would be served after any change to outcomes, features, grids or code.
2. The serialized candidate carries no feature-specification or toolkit provenance and no canary, so a different RDKit, a changed descriptor function or changed fingerprint constants would silently change its predictions while its hash stays the same.

The remaining findings are Minor. They are mostly robustness guards, one small and quantified label leak in a diagnostic gate (Experiment 11), serialization cosmetics and test gaps.

## Checks performed

### 1. Energy map direction and units

apply_energy_map (src/muru/wur_bridge.py:158-192) builds targets = a + b * LADDER and reads each WUR ladder at those targets by PCHIP, keyed by the LCSB energy E. The frozen gate record says the same thing in words ("applied to the LCSB nominal energy to give the WUR nominal energy at which WUR is read"). So E_WUR = a + b * E_LCSB with a = -5.95553, b = 0.86180, and a WUR measurement at native energy E_WUR belongs at E_LCSB = (E_WUR - a) / b.

- Numerically, T(30) = 19.90, T(90) = 71.61 and T(15) = 6.97. T(15) lies below the first WUR rung and is clamped, which is why population.py:87 keeps only 30 to 90. The inverse gives 24.32, 41.72 and 111.34 for native 15, 30 and 90.
- A hand PCHIP read of one key at a + b * E reproduces wur_aligned_all.csv (max abs 5.6e-17). Reading at the inverse direction would differ by up to 0.125 in mu.
- Native scoring in exp04:31, exp05:101 and exp13:46 uses (E_native - A) / B, which is the correct inverse. candidate.predict_mu with a per-compound matrix of (NE - a) / b matches EN.mu_from_log_g to 4.4e-16.
- The pooled table contains only 30, 45, 60, 75 and 90. All 1,010 WUR keys carry the full six-rung ladder, which apply_energy_map enforces loudly.
- The only defect nearby: the inverse map is re-typed inline in three scripts, and exp05:104 hard-codes ENERGY_SCALE as 30.0. Both are correct today and untested (M-7).

### 2. Precursor inclusion and mu

- BASE_CELL has include_precursor True and relative_cutoff 0.0, and Spectrum.preprocess only removes the precursor when that flag is False.
- For 40 random WUR spectra with a matched precursor, a hand recomputation from the raw blobs, sum(I * mz) / sum(I) / precursor, equals the stored mu to 0.0. Survival yield and fragment depth are also exact. Excluding the precursor would move mu by up to 0.48.
- All 12,432 accepted rows are HCD (no UVPD rows), and the scan-filter energy equals ce_numeric on every row.
- The precursor is matched within 10 ppm on 84 percent of spectra at E15 and 0.7 percent at E90. Unmatched spectra have no peak near the precursor (median nearest-peak distance far above 10 ppm), so the tolerance is not the cause.
- v1 against v2 aligned cells (DEV2B WUR plus SEALED, 3,780 matched cells): 25 cells differ, max abs 0.0659, in 5 keys, all of them multi-acquisition keys. This matches the registry statement exactly.

### 3. Duplicate aggregation (D-AGG) and acquisition ids

acquisition_id (spectra.py:115-125) converts each part to object dtype and fills missing values with "" before concatenating.

- On a synthetic pandas 3 frame, missing creation dates give "h|1|" for both rows. Distinct hashes with all-NaN scan and date give distinct ids.
- The fill matters on real data: 330 of 12,432 accepted rows (49 keys; WFSR_Polar 258, WUR 36, WFSR_food_safety 24, ETE 12) have no creation date. None of the 12,432 ids contains "nan", "None" or "NaT", and the 36 undated archive-copy pairs collapse to one acquisition each. peak_hash and scan_number are never missing; scan_number is int64. No spectrum carries a decode defect.
- Cell structure (rows, distinct acquisitions) breaks down as (1,1) 234, (2,1) 5,580, (3,2) 30, (4,1) 6, (4,2) 192, (6,3) 6 and (10,5) 12.
- Zero (key, energy, peak_hash) groups carry more than one acquisition id, so no archive copy failed to collapse because of a scan or date difference.
- Archive-copy groups are WFSR_food_safety plus WUR (5,898 pairs), ETE plus WUR (144) and FCH plus WUR (6).
- Hand check on BCJMNZRQJAVDLD and COHUFMBRBUPZPA (E/Z isomer pairs, 4 rows and 2 acquisitions) and AABILZKQMVKFHP (2 rows and 1 acquisition) at E30 and E90: the manual median over distinct acquisitions equals the stored cell to 1e-16. For symmetric duplication the v1 median coincides, as expected.

### 4. Fragment depth

- spectrum_quantities calls features.fragment_depth, which returns NaN for a precursor-only spectrum. No WUR spectrum is precursor-only (0 NaN, 0 zero).
- The LCSB native cells carry 18 NaN depths, all with survival yield at least 0.999, and 0 zeros. No WUR cell mixes defined and undefined depths across acquisitions.
- exp04 uses d.isna() to define the precursor_only regime. It computes partial R2 and correlations only on rows with t.d.notna(), and restricts its reported identity residual to defined cells.
- The fillna(0.0) at exp04:38 only feeds the identity-residual column, where the multiplier (1 - s) is at most 0.001 for those cells. It never reaches a reported depth.

### 5. Population

- Union of keys, primary copy LCSB (the 124 both-instrument compounds are excluded from the WUR aligned rows at population.py:120), confirmation keys removed by key, 0 parent-key mismatches.
- All 439 LCSB-primary compounds are [M+H]+ in trajectories.parquet, so the hard-coded adduct at population.py:98 is correct.
- 2 of the 124 both-instrument compounds are [M+NH4]+ on WUR, so the cross-instrument diagnostics compare different precursor ions for them (M-10).
- Recomputing the population hash from compounds.csv matches folds.json.

### 6. Identity and folds

- On test molecules, parent normalization removes counter-ions (cocaine HCl and cocaine, sodium benzoate and benzoic acid) and keeps permanent cations (choline).
- E/Z and R/S forms share the connectivity key and the scaffold. Scaffold strings contain no stereo marks (0 of 1,325).
- On 200 sampled compounds, recomputed parent keys and v2 scaffolds equal the stored values (0 mismatches). No scaffold group is split across strict clusters.
- All six stored assignment hashes recompute, and rebuilding every partition from compounds.csv reproduces all six hashes. No scaffold group straddles folds in PRIMARY, S1, S2, STRICT or GIANT (RANDOM straddles 149, by design).

### 7. Engine and models: wrong-fold training

- The nesting tests pass, and the collapse cache is keyed by the sorted training key set.
- inner_folds is called with the same (sorted keys, group column, outer fold) in engine.run_fold and in exp10, so the inner partitions match.
- Since 7943711, inner training sets carry root_fold, and ShapeCorrectedJoint reads its joint configuration from root_fold. JOINT_PLUS_SHAPE caches were first committed in 531abe2, after that fix, and a fresh recomputation matches them exactly.
- TwoStage and KNNResidual cross-fit residuals on grouped inner folds seeded by outer_fold + 777. Inner training sets carry outer_fold * 10 + k, so every set gets its own seed and no held-out key enters. Both reproduce exactly.
- KernelRidgeMinMax indexes the precomputed kernel through index.get_indexer on d.cov.index. The stored .npy rows are in compounds.csv order: MORGAN_COUNTS.parquet index equals compounds.csv order, and recomputing kernel rows 0, 500 and 1,324 from counts gives max abs 0.0.
- The risk that remains is that an unknown key maps silently to the last row (M-3).
- Across every outer and inner training set of all six partitions, the smallest standard deviation of any Tier A or ION_ENV column is 0.098, and max |log g| in the joint caches is 3.07. The + 1e-12 standardization guard has never been exercised (M-5).

### 8. Candidate serialization

- A candidate-style JSON for PRIMARY fold 0 (fold-0 profile, fold-0 joint fit at the nested configuration (0.3, 0.1)), serialized with canonical_json and reloaded, predicts all 265 held-out compounds from SMILES and precursor m/z.
- Held-out mu matches the engine's OOF mu to 6.7e-16 and log g to 1.6e-15. Tier A from SMILES matches TIER_A.parquet to 4.4e-16; Morgan log1p counts match exactly.
- The shipped candidate hash matches its manifest, with configuration (0.3, 0.1) and n = 1,325.
- Gaps: no provenance or feature-specification canary (I-2). The null comparator silently clamps energies outside 30 to 90 (native E15 at 24.3 returns the E30 mean 0.6685, and energies of 100 and 111.3 return the E90 mean). No support flag exists in predict_mu (M-6).

### 9. Checkpoint and cache contamination

- Fresh engine.run_cv against the cache for PRIMARY TA_MORGAN_JOINT and JOINT_PLUS_SHAPE: predictions, log g, folds and configurations are identical (max abs 0.0), and all 5,300 inner OOF rows are identical.
- Every other PRIMARY cached model is identical too: TA_RIDGE, TA_RIDGE_V1SEL, B1, DIAG source by mass, EXP07 ION_ENV, MORGAN_RIDGE, TA_THEN_MORGAN, MINMAX_KRR, ATOMPAIR, MACCS, KNN10, TA_ATOMPAIR_JOINT, TA_ION_MORGAN_JOINT and the permuted controls s0 and s3 (Morgan ridge) and s1 (joint). All 12 GIANT runs are identical.
- The PermutedFeatures fix wrote new cache names (tag _v2fix). No pre-fix untagged PERMUTED cache file exists in this worktree or any other worktree under the repository.
- The pre-fix EXP08A artifact (artifacts/wur_v2/exp08/EXP08A_MORGAN_RIDGE.json) still shows five identical permutation ratios (1.3967) and c4 True. The immutable ledger entry V2-EXP08P supersedes it, but the JSON itself carries no pointer (M-12).
- The structural risk remains: the cache key cannot detect changed inputs (I-1, demonstrated on synthetic data).

### 10. One-look guards

- stage3.sealed_tables raises when artifacts/wur_stage3/first_sealed_access.json exists, before any sealed read or record write. holdcheck.run raises when hold_check.json exists. The top-level scripts run_wur_stage3.py and run_wur_stage2b_hold_check.py carry their own existence checks.
- exposure.assert_wur_exposed requires both records, a git_head starting with 69ca1a6, and hold_status EXPOSED. The records read utc 2026-09-12T19:55:23Z, head 69ca1a6a, clean tree and EXPOSED.
- wur_v2.spectra.wur_pos_spectra calls the guard before passing allow_sealed=True.
- No bypass was found in the reviewed code. The guards depend on the record files being present, which is inherent to the design.

### 11. Tests

python3 -m pytest tests/wur_v2 tests/test_wur_*.py -q: 272 passed, 0 failed, in 6 min 10 s. Four of those tests come from the two untracked external test files. The brief's test list against what exists:

| Area | Status |
|---|---|
| identity normalization (parent, stereo-free scaffold, strict clusters) | missing (tests/test_wur_identity.py covers the v1 io layer, not muru.wur_v2.identity) |
| group splits | present on synthetic data (test_group_disjoint_partitions_and_mutation); no test on the frozen folds.json |
| absence of group leakage | present on synthetic data (test_heldout_never_in_training_collapse_or_fit, test_inner_validation_keys_excluded_from_inner_collapse) |
| external-seal guard | not at 52967a0 (an untracked test_v2_external_guard.py exists) |
| historical one-look guards | present (test_v2_one_look_guards.py) |
| endpoint definition (base-cell mu with precursor, 10 ppm) | missing for the v2 path (spectrum_quantities, aggregate_cells) |
| P1 metric | present |
| bootstrap resampling | present |
| energy map direction | v1 clamp test only implies it; no v2 test of the inverse used for native scoring |
| native-energy support | missing |
| precursor inclusion | missing for v2 |
| undefined fragment depth | v1 features tests only; no v2 aggregate or exp04 test |
| acquisition id and archive collapse (D-AGG, pandas 3 NaN) | missing |
| target-generation nesting | present for collapse and labels; missing for ShapeCorrectedJoint coefficients |
| Morgan determinism | present (in-process only; no cross-environment canary) |
| trust target cross-fitting | missing |
| candidate serialization | weak: hash and shape only. Held-out mu parity is not tested; the build script checks training log g only |
| exact population and partition hashes | missing |
| runner cache key and cached-versus-fresh type parity | missing |
| kernel index alignment | missing |

## Findings in detail

### I-1 (Important) The run cache key cannot see the inputs it depends on

runner.run (runner.py:47-56) returns a cached run when RUNS/partition/{model.id}{tag}__{assignment_sha[:12]}.parquet exists. The key encodes neither of these:

- the outcome table (long_aligned.csv or Y)
- the feature blocks (MORGAN, ATOMPAIR, TIER_A_ION with its kept columns, TIER_A_SOURCE)
- the kernel matrices
- the model grid
- joint_cfgs for JOINT_PLUS_SHAPE
- code version

In addition, most representation files are gitignored (.gitignore:34). Only TIER_A.parquet and MACCS.parquet are tracked, while the MORGAN and ATOMPAIR blocks and both MinMax kernels are not. Their hashes are printed to stdout by build_v2_representations.py and recorded nowhere.

Evidence:

- demo_latent_defects.py halves every mu and reruns RU.run. It returns the old predictions (allclose True), while a fresh run differs.
- A second, related latent defect: engine.collapse_for (engine.py:77-83) keys the profile cache by the key set alone, so it returns the same CollapseFit object after the outcomes change.
- Today no contamination exists: every cached run I recomputed matches exactly (section 9).

Impact: any future fix to spectra aggregation, population, representations or a model grid would silently reuse old predictions on the next script run, and the ledger would record them as new.

Proposed fix: store in the meta JSON the sha256 of the Y matrix over the partition keys, of every feature block and kernel the model reads, of repr(model.grid()) plus model parameters, and the code sha. On load, recompute these and raise (or miss) on any mismatch. Key _COLLAPSE_CACHE by (keys hash, sha of the long table). Commit the representation hashes to a manifest.

Regression test: a synthetic Data with a tmp RUNS directory. Run, mutate Y, assert that RU.run raises or recomputes. Mutate a feature block and assert the same. Call collapse_for twice with different long tables and assert different objects.

### I-2 (Important) The serialized candidate has no feature-specification provenance or canary

V2_TA_MORGAN_JOINT.json (candidate.py:40-44) stores the profile, the standardization, coefficients, the configuration and training_keys_sha256. predict_log_g recomputes features with whatever the current environment supplies, and records none of the following:

- the Tier A feature order or protocol.SCALE values
- the tier_a_descriptors implementation
- the Morgan radius, size, chirality flag or log1p transform (representations.py constants)
- the RDKit version

A different RDKit hashing or rotatable-bond definition, or an edit to protocol.FEATURES, representations.MORGAN_RADIUS or FP_SIZE, would change every external prediction without changing the model hash. The 12 at candidate.py:44 is also hard-coded rather than taken from len(protocol.FEATURES).

Evidence: the JSON keys are cfg, coef_morgan, coef_tier_a, inner_loss, intercept, kind, n_training, profile, tier_a_mean, tier_a_sd and training_keys_sha256. The manifest adds only hashes, configurations and the training log g reload parity.

Proposed fix: add a feature_spec block (feature names in order, SCALE values, Morgan radius, size, includeChirality and transform, RDKit version) and a canary block (Morgan-count sha and expected log g and mu for about 10 fixed SMILES from the training set). predict_mu should verify the spec against the running code and the canary against a fresh computation before predicting, and raise on mismatch.

Regression test: load the JSON, perturb feature_spec (for example the radius) or monkeypatch representations.FP_SIZE, and assert predict_mu raises. Assert the canary log g reproduces within 1e-12 in the current environment.

### M-1 (Minor) Experiment 11's structure-predictability R2 uses training labels built with test-fold information

exp11_shape_oracle.py:77 trains the coefficient ridge for fold f on c values of training compounds taken from the other folds' held-out oracle fits. Each of those used a profile fitted with fold f compounds and a joint scale predicted by a model trained on fold f labels. The alpha hold-back at line 78 is also a non-grouped 80/20 split of sorted keys.

This R2 (0.18 against a 0.10 bar) is the evidence Amendment A-2 cites to license EXP12.

Evidence: check_exp11_predictability.py reproduces 0.18353 exactly. Rebuilding the training labels from the fold-f training set alone (inner cross-fitted joint scales, fold-f profile and basis) gives 0.17951. The leak is real but immaterial, and the license stands.

Fix: build training labels inside the training set, as ShapeCorrectedJoint already does, and select alpha on grouped inner folds.

Test: a synthetic check that every label used to train the c ridge for fold f is invariant to perturbing fold f's Y.

### M-2 (Minor) Cached and fresh CVRun objects differ in types

A cache hit returns cfgs keyed by str and inner_oof columns named "30.0" and so on. A fresh run returns int keys and float columns (demonstrated). exp10_trust.py:38 indexes inner_oof with string column names, so it works only from cache and would raise KeyError on a fresh run. exp12 and check scripts convert keys by hand.

Fix: normalize on load (int fold keys, float energy columns) or on save.

Test: the RU.run fresh and cached objects compare equal field by field.

### M-3 (Minor) kernel_block silently maps an unknown key to the last kernel row

models.py:180 uses index.get_indexer, which returns -1 for a missing label, and numpy then reads the last row (demonstrated: an unknown key "Z" returns row C). The kernel's row order is also implied by compounds.csv at load time (runner.py:31-32) rather than stored with the .npy. It is correct today (index equality and exact recomputation of three rows).

Fix: assert that every indexer is at least 0, and save the key index next to each kernel (or as an npz with keys), asserting equality on load.

Test: kernel_block with an unknown key raises; a shuffled compounds.csv with the stored kernel raises.

### M-4 (Minor) PermutedFeatures caches the permuted block by name inside data.features

models.py:228-232 caches the permuted block, so if a caller replaces data.features[feature] on the same Data object (exp05b does this for TIER_A), a previously built permuted block goes stale. There is no live impact.

Fix: key the permuted name by a hash of the source block, or rebuild when the source identity changes.

### M-5 (Minor) Standardization guard A.std(0) + 1e-12 would amplify a column that is constant in a training set by 1e12

JointRidge (models.py:100) and ShapeCorrectedJoint (models.py:303) share the guard. It is never triggered here (smallest standard deviation 0.098, max |log g| 3.07). A new base block or a smaller population could hit it.

Fix: use np.where(sd > 1e-8, sd, 1.0).

Test: a training set with one constant column predicts a finite value for a test row whose value differs.

### M-6 (Minor) The candidate has no native-energy support flag, and the null comparator clamps silently

predict_mu (candidate.py:83-95) evaluates the profile with constant extrapolation outside its knots. profile_support_u exists but nothing calls it. The null model's np.interp (candidate.py:89) clamps energies to 30 to 90, so for native WUR E15 (24.3) and E90 (111.3) the B0 comparator returns the E30 and E90 rung means with no warning.

Evidence: null_model_2d in check_cache_and_candidate_out.json. exp05 reports 3.0 percent of native E90 cells outside profile support.

Fix: return, or optionally raise on, an out-of-support mask for u outside the profile knots and for energies outside the null grid.

Test: energies of 24.3 and 111.3 produce support flags.

### M-7 (Minor) The inverse energy map is re-implemented inline in three scripts

The inverse appears at exp04:31, exp05:101 and 104, and exp13:46, and exp05:104 hard-codes ENERGY_SCALE as 30.0. All are correct today.

Fix: add wur_bridge.lcsb_energy_for_wur(E_wur, a, b) and use ENERGY_SCALE.

Test: lcsb_energy_for_wur(a + b * E) equals E, and apply_energy_map on a linear ladder agrees with the inverse.

### M-8 (Minor) Gate booleans serialize as 0.0 or 1.0 through default=float

exp11_shape_oracle.py:102 records stop_if_predictability_R2_lt_0.10 as 0.0 (a numpy bool passed through json default=float), while its sibling key holds a Python bool and records true. The same pattern could affect other json.dumps(..., default=float) calls when criteria come from numpy scalars.

Fix: cast with bool() or use the ledger's _default.

Test: dumping the exp11 gate dict gives a JSON boolean.

### M-9 (Minor) Within-training shape coefficients use the full training-set profile, and predictions are clipped only in the shape arm

ShapeCorrectedJoint cross-fits the joint scale but computes each inner-validation coefficient against ts.fit, which was fitted with that compound's own trajectory (models.py:293). predict_mu clips only this arm to [0, 1] (models.py:317). The effect on this dataset is negligible (one Y cell exceeds 1 by 3e-7), and the arm failed its bar.

Fix: document this, or refit the profile per inner split, and apply the same clip to both arms of a comparison.

### M-10 (Minor) Cross-instrument pairs include two adduct mismatches

2 of the 124 both-instrument compounds are [M+H]+ on LCSB and [M+NH4]+ on WUR, so exp02 R2, exp05 (a) and exp11 R2 compare different precursor ions for them.

Fix: restrict paired analyses to matching adducts, or report the count.

Test: an assert on adduct equality inside the paired selection.

### M-11 (Minor) Trust training-row targets carry selection optimism

exp10_trust.py:36-38 uses inner OOF errors at the configuration that those same inner losses selected. This slightly understates training-row error relative to test rows. It is diagnostic, and trust was rejected anyway.

Fix: nest the configuration selection or use a fixed configuration for trust targets.

### M-12 (Minor) The pre-fix EXP08A artifact is not annotated

artifacts/wur_v2/exp08/EXP08A_MORGAN_RIDGE.json still records five identical permutation ratios and c4 True. The correction lives only in V2-EXP08P and permutation_controls_corrected.json, so a reader of the arm JSON gets the invalid control.

Fix: add a superseded_by pointer file next to it (the ledger stays immutable).

### M-13 (Minor) Scripts on load_data(False) depend on cache hits

exp02 to exp05, exp01c and the exp05b TA_RIDGE call use load_data(False) or no MORGAN block. Without the tracked caches they raise KeyError on TIER_A or MORGAN, which is loud rather than wrong. The untracked representation files mean a clean checkout cannot rebuild the uncached arms without first running build_v2_representations.py.

Fix: document the dependency, or load features lazily.

## Findings table

| id | severity | file:line | finding | evidence | proposed fix / regression test |
|---|---|---|---|---|---|
| I-1 | Important | src/muru/wur_v2/runner.py:47-56; src/muru/wur_v2/engine.py:77-83; .gitignore:34 | Run cache keyed only by model id + assignment hash; profile cache keyed only by key set; representation blocks and kernels untracked and unhashed. Any change to outcomes, features, grids or code silently serves stale results | demo_latent_defects.py: after halving mu, RU.run returns the old predictions and collapse_for returns the same object; today all 30 recomputed caches match exactly | Store and verify sha of Y, features, kernels, model params and code in the run meta; key the collapse cache by long-table hash; commit a representation hash manifest. Test: mutate Y or a feature in a tmp RUNS dir and assert a miss or raise |
| I-2 | Important | src/muru/wur_v2/candidate.py:40-44, 58-80 | Serialized candidate lacks feature spec (Tier A order and SCALE, Morgan radius, size, chirality, transform), RDKit version and canary; coefficient split hard-coded at 12 | JSON keys listed in I-2; RDKit 2026.03.5 recorded nowhere | Add feature_spec and canary blocks and verify both in predict_mu. Test: perturbing the spec or the fingerprint constants makes predict_mu raise; canary log g reproduces within 1e-12 |
| M-1 | Minor | scripts/wur_v2/exp11_shape_oracle.py:77-78 | Predictability R2 (A-2 license) trains on c labels built with test-fold profile and scale information; non-grouped alpha hold-back | 0.18353 reproduced; training-set-only labels give 0.17951 (check_exp11_predictability_out.json) | Build labels inside the training set with grouped inner selection. Test: training labels invariant to perturbing test-fold Y |
| M-2 | Minor | src/muru/wur_v2/runner.py:50-56; scripts/wur_v2/exp10_trust.py:38 | Cached run returns str fold keys and str energy columns in inner_oof; fresh run returns int and float; exp10 works only from cache | demo_latent_defects.py prints ['0','1'] against [0,1] and ['30.0',...] against [30.0,...] | Normalize types on load. Test: fresh and cached CVRun fields equal |
| M-3 | Minor | src/muru/wur_v2/models.py:178-180; src/muru/wur_v2/runner.py:31-32 | kernel_block maps unknown keys to the last row (-1 indexer); kernel row order implied, not stored | Demo: unknown key "Z" returns row C value 1.0; stored kernel currently aligned (0.0 diff on recomputed rows) | Assert indexers at least 0; save keys with kernel and assert on load. Test: unknown key raises |
| M-4 | Minor | src/muru/wur_v2/models.py:228-232 | Permuted block cached by name; stale if the source block is replaced on the same Data | Code inspection; exp05b replaces TIER_A in place | Key by source-block hash. Test: replace block, assert permuted block rebuilt |
| M-5 | Minor | src/muru/wur_v2/models.py:100, 303 | std + 1e-12 guard amplifies a training-constant column by 1e12 | Not triggered: min column sd 0.098 over all outer and inner sets, max abs log g 3.07 | Use sd where sd > 1e-8 else 1. Test: constant training column gives finite predictions |
| M-6 | Minor | src/muru/wur_v2/candidate.py:83-95 | No out-of-support flag; null model clamps energies outside 30-90 silently | Null mu at 24.3 equals the E30 mean 0.6685; at 111.3 equals the E90 mean; 3.0 percent of native E90 cells outside profile support (exp05) | Return or raise on an out-of-support mask. Test: 24.3 and 111.3 flagged |
| M-7 | Minor | scripts/wur_v2/exp04_survival_depth.py:31; exp05_acquisition.py:101,104; exp13_candidate_stress.py:46 | Inverse map re-typed inline; ENERGY_SCALE hard-coded as 30.0 | Correct today: 24.32, 41.72, 111.34 | Shared lcsb_energy_for_wur helper. Test: round trip with a + bE and PCHIP agreement |
| M-8 | Minor | scripts/wur_v2/exp11_shape_oracle.py:102-103 | numpy bool gate serialized as 0.0 via default=float | exp11_results.json gate stop_if_predictability_R2_lt_0.10 is 0.0 | Cast with bool(). Test: JSON boolean type |
| M-9 | Minor | src/muru/wur_v2/models.py:293, 317 | Inner shape coefficients use the full training profile; clip to [0,1] applied only to the shape arm | One Y cell above 1 (1.0000003); arm failed its bar | Document, or refit the profile per inner split and clip both arms |
| M-10 | Minor | scripts/wur_v2/exp02_repeatability.py:70-75; exp05_acquisition.py:35-37; exp11_shape_oracle.py:95-98 | 2 of 124 cross-instrument pairs differ in adduct ([M+NH4]+ on WUR) | check_data_out.json both_instrument_adduct_mismatch = 2 | Restrict to matching adducts or report. Test: assert adduct equality in paired sets |
| M-11 | Minor | scripts/wur_v2/exp10_trust.py:36-38 | Trust training targets come from inner OOF at the configuration selected on those same losses | Code inspection | Nest or fix the configuration for trust targets |
| M-12 | Minor | artifacts/wur_v2/exp08/EXP08A_MORGAN_RIDGE.json | Pre-fix permutation ratios (five identical 1.3967, c4 True) remain unannotated | File contents; correction only in V2-EXP08P | Add a superseded_by pointer file |
| M-13 | Minor | scripts/wur_v2/exp02_repeatability.py:18 and siblings using load_data(False) | Scripts depend on tracked cache hits; untracked representations block clean-checkout reruns of uncached arms | load_data(False) raises KeyError on TIER_A for any cache miss | Document or load lazily; see I-1 manifest |
| T-1 | Minor | tests/wur_v2/ | Missing tests: v2 identity normalization, frozen folds and population hashes, D-AGG and acquisition id, v2 endpoint and precursor inclusion, v2 fragment-depth NaN, energy-map inverse and native support, trust cross-fitting, held-out candidate mu parity, runner cache parity and key, kernel alignment | Section 11 table | Add the tests listed in the findings above; turn check_identity.py, check_data.py and check_cache_and_candidate.py into pytest cases on the committed artifacts |

Scratch files (all under docs/wur_v2_reviews/impl_scratch/): check_data.py (+ _out.json), check_precursor.py, check_scanfilter.py, check_mu_manual.py, check_identity.py, check_constant_columns.py, check_cache_and_candidate.py (+ _out.json, .log), check_all_primary_caches.py (+ _out.json, .log), check_exp11_predictability.py (+ _out.json), demo_latent_defects.py.
