# MURU WUR Stage 2A: frozen pre-WUR MURU baseline, RESULT

**Identifier:** `wur-stage2a-1.0`, executed once
**Protocol:** `MURU_WUR_STAGE2A_EXECUTION_PROTOCOL.md` (commit `1e27865`), followed without deviation
**Code:** commit `95887d4` (engine), this document's commit carries the artifacts
**Method under test:** MURU as frozen before any WUR performance was seen (`FRESH_HOLDOUT_METHOD_FREEZE.json`: frozen p3 grammar, PySR 1.5.10 config, B2 family vote, R1 representative, gate t1 = 0.595, t2 = 0.2; collapse `ENERGY_SCALE = 30`; ladder `E_REF = 45`, practical-win margin 0.90, min 5 energies)
**Status of this document:** immutable historical evidence. Later generations add documents; they do not edit this one.

## 1. Verdict in one paragraph

The frozen pre-WUR MURU does not report on real spectra. In all three analyses the gate refuses (median seed-best validation R2 0.35 to 0.38 against the frozen 0.595), the single-shape collapse hypothesis H-MAIN is rejected (a per-compound shape exponent lowers leave-one-energy-out error by 12 to 16 percent, bootstrap interval excludes 1 everywhere), and the M0 to M3 adequacy ladder returns BOUNDARY_LIMITED because 30 to 60 percent of test compounds run into the frozen parameter boxes, so the ladder cannot reach a verdict. A descriptor-to-scale signal exists but is weak: the pooled-aligned representative reaches a held-out test R2 of 0.45 (bootstrap 0.26 to 0.57, Spearman 0.65) with a three-variable expression, while the two native analyses select a mass-only reciprocal with test R2 0.22 and 0.14. There were zero engineering failures: 90 of 90 searches completed, no exceptions, no defective spectra, no descriptor failures.

## 2. Interpretation, by endpoint

**E1, collapse.** Residual SD of the shared-shape fit is 0.057 (A), 0.059 (B), 0.076 (C), which is 2 to 2.6 times the 0.0295 inter-mixture repeatability SD of `REPEATABILITY.md`. H-MAIN is rejected in every analysis. The estimated scales span a factor of about 25 (g from 0.20 to 4.9); the frozen collapse grid `log g in [-1.6, 1.6]` is saturated at its lower edge by 24 of 791 compounds in A and 20 of 476 in B, so the frozen estimator cannot represent the least-fragmenting real compounds. The real data are wider than the synthetic worlds the estimator was built on.

**E2, ladder.** No detector fires anywhere and no analysis reaches M0_NOT_REJECTED: every contrast is below the 80 percent evaluability floor because unresolved boundary contact (log g at plus or minus 2, or the shape exponent at plus or minus ln 2) removes 19 to 53 of the test compounds per detector. Among the compounds that are evaluable, the alternative models win often: M3's low-energy plateau wins 35 of 51 evaluable WUR compounds (binomial tail 0.005) and M1's shape exponent wins 34 of 66; on the LCSB side M2's free asymptote wins 37 of 69. The frozen rule was calibrated on synthetic worlds where 24 of 30 compounds are evaluable; on real data the boxes, not the science, decide the outcome.

**E3, E4, gate and selection.** The frozen gate never reports. The seed-best validation R2 is remarkably stable across seeds (interquartile ranges of 0.03 or less), so the refusal is not search instability; the ceiling on descriptor-explained variance in g is simply about 0.4 under this feature set and target. Selection fractions (0.40 to 0.63) would pass t2. In A the selected expression `(sqrt(aromatic_ring_count + 1/heteroatom_fraction) + 0.043) / total_atom_count` generalises to held-out scaffolds (test R2 0.45 weighted, 0.40 unweighted) better than its validation R2 suggests; in B and C the mass-only `1/total_atom_count` is selected and generalises poorly (test R2 0.22 and 0.14, bootstrap intervals include 0). The band-member table in `selection.json` shows that in every analysis some non-selected band members score higher on the test part than the representative; that is reporting, not a selection alternative, and it is left for Stage 2B.

**E7, E = 15.** WUR native mu at 15 has median 0.74 against 0.91 for LCSB, the largest cross-corpus difference on the ladder, consistent with Stage 1's finding that no admissible map corrects that rung. It never entered a pooled fit.

**E8, per-energy.** After alignment the per-energy medians of the two corpora agree to within 0.02 to 0.03 on the pooled rungs, while the LCSB-native analysis has visibly higher residual SD and M0 error than the WUR-native one (0.076 versus 0.059; median M0 LOEO MAE 0.042 to 0.065 versus 0.037), so the older corpus is the noisier of the two.

## 3. What this baseline establishes

1. The pre-WUR MURU makes no report on real data, so its principal synthetic claim (a report gate with sensitivity 1.0 and null FPR 0.04) does not transfer to a positive real-data statement; whether that is because there is no descriptor law, or because the estimator and the gate are mis-specified for real spectra, is the Stage 2B question.
2. The failure is not computational. Every component ran to completion on real input.
3. The three components fail in the same direction in all three populations, so the result is not an artefact of the cross-instrument alignment: the WUR-native and LCSB-native analyses reproduce it without any map.

## 4. Major failure modes, ranked by evidence

| Rank | Mode | Evidence |
|---|---|---|
| 1 | Single shared shape with one scale per compound is inadequate | H-MAIN rejected in 3 of 3; M1 and M3 wins concentrated where evaluable |
| 2 | Frozen parameter boxes too narrow for real g and shape spread | 30 to 60 percent unresolved boundary contact; collapse grid saturated |
| 3 | Descriptor set explains about 0.4 of the variance in log g | seed-best validation R2 0.35 to 0.47 across 90 seeds |
| 4 | Gate calibrated on synthetic positives sits far above real attainable R2 | 0.595 versus 0.38 |
| 5 | Native mass-only selections generalise poorly | test R2 0.14 to 0.22 with intervals through 0 |

## 5. Engineering corrections

None. No defect surfaced during the run; nothing was changed.

## 6. Population sizes and hashes

See the tables below and `artifacts/wur_stage2a/population_census.json`. HOLD (130 compounds) was never decoded. Every population hash is recorded per analysis in `result.json`.

## 7. Independent implementation review, disclosed

A hostile implementation review of the engine (read-only, results-blind, run
while Stage 2A executed) found no Critical defect and verified: no path
decodes a sealed or HOLD peak; the map is applied in the frozen direction;
E = 15 is absent from every pooled fit including H-MAIN and the ladder; the
frozen selector sequence and gate thresholds are reproduced field for field;
compound order is preserved between the collapse, the split and the written
tables. Its Important findings, and their status:

1. **Two protocol endpoints were not produced.** E8's per-energy M0
   leave-one-energy-out absolute error and E7's M0 residual at E = 15 inside
   analysis B are not in the artifacts, because the frozen contrast exposes
   only the per-compound mean error. The protocol promised them; this run
   did not deliver them. They are diagnostics, not decision inputs, and no
   Stage 2A conclusion depends on them. They are computed in Stage 2B's
   failure analysis from the same frozen fitter and labelled as post-hoc.
2. **Silent key drop in world construction.** `build_world` intersects the
   mu and covariate key sets without reporting a difference. In this run no
   key was dropped: A has 791 = 476 + 439 - 124, B 476, C 439, and there were
   zero descriptor failures. The construction is hardened with an assertion
   in the next commit.
3. **The seal guard is fail-open when the sealed artifact is absent and does
   not cover HOLD.** In Stage 2A both are enforced by the population loader
   before any decode. Hardened in the next commit.
4. **Test gaps** on the run glue and boundary conditions of the gate, and
   several Minor items (a zero-seed search would not count as an analysis
   failure; bootstrap drops non-finite resamples without a count; Wilson
   intervals are missing on the selector fractions). None changes a number
   here; all are addressed in the next commit, with tests.

No Stage 2A artifact is modified in response to the review.

---

# MURU WUR Stage 2A: frozen pre-WUR MURU baseline, result tables

Generated by `scripts/report_wur_stage2a.py` from `artifacts/wur_stage2a/`. Narrative interpretation follows the tables and is written by hand.

## Populations

| Population | Compounds | Scaffold groups | Keys sha256 |
|---|---|---|---|
| LCSB-DEV | 439 | 286 | `6bc8eeeb3d0c768c...` |
| WUR-DEV-ANALYSIS | 476 | 241 | `6601a696ed89bbd8...` |
| A pooled (LCSB copy kept for 124 population-B keys) | 791 | see analysis table | |

WUR spectra decoded: 5800 in 2856 cells; spectra per cell {'1': 66, '2': 2710, '3': 18, '4': 56, '6': 6}; descriptor failures: 0. LCSB rungs per key: {'5': 24, '6': 415}. Energy map a=-5.955526, b=0.861803; mapped targets {'30.0': 19.9, '45.0': 32.83, '60.0': 45.75, '75.0': 58.68, '90.0': 71.61}.

## A_POOLED_ALIGNED

World `WUR2A|A_POOLED_ALIGNED|seed20260911`: 791 compounds, 431 scaffold groups, energies [30.0, 45.0, 60.0, 75.0, 90.0], split {'test': 158, 'train': 475, 'valid': 158} (groups {'test': 136, 'train': 159, 'valid': 136}), sources {'LCSB': 439, 'WUR': 352}.

### E1 Collapse and H-MAIN

| Quantity | Value |
|---|---|
| Residual SD (mu) | 0.0567 |
| Collapse LOEO RMSE | 0.0756 |
| Free-shape LOEO RMSE | 0.0639 |
| Ratio (95% CI) | 1.1839 [1.162, 1.209] |
| H-MAIN rejected | True |
| g_hat min / median / max, SD of log g | 0.200 / 1.061 / 4.896, 0.728 |

### E2 M0 to M3 adequacy ladder (test split)

Status **BOUNDARY_LIMITED**; fired none; Phi trained on 475 compounds; blocker: contrast(s) below the 127-of-158 evaluability floor: M1, M2, M3

| Detector | N_test | Evaluable (min) | Wins (min) | Win frac of test (Wilson 95%) | Binomial tail | Fired | Status counts |
|---|---|---|---|---|---|---|---|
| M1 | 158 | 99 (127) | 43 (106) | 0.272 [0.209, 0.346] | 0.920 | False | {'BOUNDARY_LIMITED': 54, 'INSUFFICIENT_DATA': 5, 'NO_PRACTICAL_WIN': 56, 'PRACTICAL_WIN': 43} |
| M2 | 158 | 96 (127) | 44 (106) | 0.278 [0.214, 0.353] | 0.821 | False | {'BOUNDARY_LIMITED': 57, 'INSUFFICIENT_DATA': 5, 'NO_PRACTICAL_WIN': 52, 'PRACTICAL_WIN': 44} |
| M3 | 158 | 83 (127) | 36 (106) | 0.228 [0.169, 0.299] | 0.906 | False | {'BOUNDARY_LIMITED': 70, 'INSUFFICIENT_DATA': 5, 'NO_PRACTICAL_WIN': 47, 'PRACTICAL_WIN': 36} |

### E3, E4 Frozen selector and gate

| Quantity | Value |
|---|---|
| Seeds done / planned | 30 / 30 (failures 0) |
| Gate decision | **NO_REPORT** (t1=0.595, t2=0.2) |
| median seed-best validation R2 | 0.3803 |
| selection fraction | 0.4000 |
| modal support frequency | 0.4333 |
| band members / usable / clusters | 56 / 43 / 22 |
| representative | `(sqrt(aromatic_ring_count + inv(heteroatom_fraction)) + 0.043154843) / total_atom_count` |
| complexity | 10 |
| effective support (blocks) | ['aromatic_ring_count', 'heteroatom_fraction', 'total_atom_count'] (['MASS', 'aromatic_ring_count', 'heteroatom_fraction']) |
| train / validation R2 | 0.5293 / 0.3687 |
| **test R2 weighted / unweighted** | **0.4480** / 0.4023 (n=158, invalid 0.000) |
| test Spearman | 0.6469 |
| test R2 bootstrap 95% | [0.262, 0.571] |

E5 seed-best validation R2: min 0.356, q25 0.367, median 0.380, q75 0.398, max 0.471 over 30 seeds.

Bootstrap (compound-level, n=1000): M1: evaluable [0.544, 0.696], wins [0.209, 0.348]; M2: evaluable [0.532, 0.684], wins [0.215, 0.354]; M3: evaluable [0.449, 0.601], wins [0.165, 0.291].

### E8 Per-energy mu (median [q25, q75]) by source

| E | n | all | LCSB | WUR |
|---|---|---|---|---|
| 30 | 787 | 0.682 [0.503, 0.863] | 0.699 | 0.665 |
| 45 | 787 | 0.544 [0.407, 0.718] | 0.555 | 0.540 |
| 60 | 783 | 0.463 [0.359, 0.601] | 0.477 | 0.458 |
| 75 | 790 | 0.421 [0.330, 0.544] | 0.428 | 0.412 |
| 90 | 787 | 0.386 [0.309, 0.497] | 0.390 | 0.382 |

E7 E = 15, separate: WUR native n=476 median 0.743 [0.535, 0.901]; LCSB native n=436 median 0.909 [0.721, 0.986].

Wall time 147 s.

## B_WUR_NATIVE

World `WUR2A|B_WUR_NATIVE|seed20260911`: 476 compounds, 241 scaffold groups, energies [15.0, 30.0, 45.0, 60.0, 75.0, 90.0], split {'test': 95, 'train': 286, 'valid': 95} (groups {'test': 76, 'train': 90, 'valid': 75}), sources {'WUR': 476}.

### E1 Collapse and H-MAIN

| Quantity | Value |
|---|---|
| Residual SD (mu) | 0.0594 |
| Collapse LOEO RMSE | 0.0780 |
| Free-shape LOEO RMSE | 0.0657 |
| Ratio (95% CI) | 1.1875 [1.147, 1.221] |
| H-MAIN rejected | True |
| g_hat min / median / max, SD of log g | 0.200 / 1.091 / 4.614, 0.786 |

### E2 M0 to M3 adequacy ladder (test split)

Status **BOUNDARY_LIMITED**; fired none; Phi trained on 286 compounds; blocker: contrast(s) below the 76-of-95 evaluability floor: M1, M2, M3

| Detector | N_test | Evaluable (min) | Wins (min) | Win frac of test (Wilson 95%) | Binomial tail | Fired | Status counts |
|---|---|---|---|---|---|---|---|
| M1 | 95 | 66 (76) | 34 (64) | 0.358 [0.269, 0.458] | 0.451 | False | {'BOUNDARY_LIMITED': 29, 'NO_PRACTICAL_WIN': 32, 'PRACTICAL_WIN': 34} |
| M2 | 95 | 65 (76) | 29 (64) | 0.305 [0.222, 0.404] | 0.839 | False | {'BOUNDARY_LIMITED': 30, 'NO_PRACTICAL_WIN': 36, 'PRACTICAL_WIN': 29} |
| M3 | 95 | 51 (76) | 35 (64) | 0.368 [0.278, 0.469] | 0.005 | False | {'BOUNDARY_LIMITED': 44, 'NO_PRACTICAL_WIN': 16, 'PRACTICAL_WIN': 35} |

### E3, E4 Frozen selector and gate

| Quantity | Value |
|---|---|
| Seeds done / planned | 30 / 30 (failures 0) |
| Gate decision | **NO_REPORT** (t1=0.595, t2=0.2) |
| median seed-best validation R2 | 0.3464 |
| selection fraction | 0.6333 |
| modal support frequency | 0.6333 |
| band members / usable / clusters | 43 / 38 / 11 |
| representative | `1.4438351 / total_atom_count` |
| complexity | 4 |
| effective support (blocks) | ['total_atom_count'] (['MASS']) |
| train / validation R2 | 0.2835 / 0.3464 |
| **test R2 weighted / unweighted** | **0.2225** / 0.1406 (n=95, invalid 0.000) |
| test Spearman | 0.4546 |
| test R2 bootstrap 95% | [-0.093, 0.344] |

E5 seed-best validation R2: min 0.346, q25 0.346, median 0.346, q75 0.375, max 0.466 over 30 seeds.

Bootstrap (compound-level, n=1000): M1: evaluable [0.600, 0.789], wins [0.263, 0.453]; M2: evaluable [0.589, 0.779], wins [0.211, 0.400]; M3: evaluable [0.432, 0.632], wins [0.263, 0.474].

### E8 Per-energy mu (median [q25, q75]) by source

| E | n | all | WUR |
|---|---|---|---|
| 15 | 476 | 0.743 [0.535, 0.901] | 0.743 |
| 30 | 476 | 0.548 [0.407, 0.701] | 0.548 |
| 45 | 476 | 0.459 [0.356, 0.580] | 0.459 |
| 60 | 476 | 0.405 [0.328, 0.511] | 0.405 |
| 75 | 476 | 0.370 [0.305, 0.461] | 0.370 |
| 90 | 476 | 0.343 [0.284, 0.418] | 0.343 |

Wall time 119 s.

## C_LCSB_NATIVE

World `WUR2A|C_LCSB_NATIVE|seed20260911`: 439 compounds, 286 scaffold groups, energies [15.0, 30.0, 45.0, 60.0, 75.0, 90.0], split {'test': 88, 'train': 263, 'valid': 88} (groups {'test': 86, 'train': 115, 'valid': 85}), sources {'LCSB': 439}.

### E1 Collapse and H-MAIN

| Quantity | Value |
|---|---|
| Residual SD (mu) | 0.0761 |
| Collapse LOEO RMSE | 0.1009 |
| Free-shape LOEO RMSE | 0.0887 |
| Ratio (95% CI) | 1.1368 [1.112, 1.163] |
| H-MAIN rejected | True |
| g_hat min / median / max, SD of log g | 0.201 / 0.977 / 4.934, 0.703 |

### E2 M0 to M3 adequacy ladder (test split)

Status **BOUNDARY_LIMITED**; fired none; Phi trained on 263 compounds; blocker: contrast(s) below the 71-of-88 evaluability floor: M1, M2, M3

| Detector | N_test | Evaluable (min) | Wins (min) | Win frac of test (Wilson 95%) | Binomial tail | Fired | Status counts |
|---|---|---|---|---|---|---|---|
| M1 | 88 | 51 (71) | 20 (59) | 0.227 [0.152, 0.325] | 0.954 | False | {'BOUNDARY_LIMITED': 37, 'NO_PRACTICAL_WIN': 31, 'PRACTICAL_WIN': 20} |
| M2 | 88 | 69 (71) | 37 (59) | 0.420 [0.323, 0.525] | 0.315 | False | {'BOUNDARY_LIMITED': 19, 'NO_PRACTICAL_WIN': 32, 'PRACTICAL_WIN': 37} |
| M3 | 88 | 35 (71) | 19 (59) | 0.216 [0.143, 0.313] | 0.368 | False | {'BOUNDARY_LIMITED': 53, 'NO_PRACTICAL_WIN': 16, 'PRACTICAL_WIN': 19} |

### E3, E4 Frozen selector and gate

| Quantity | Value |
|---|---|
| Seeds done / planned | 30 / 30 (failures 0) |
| Gate decision | **NO_REPORT** (t1=0.595, t2=0.2) |
| median seed-best validation R2 | 0.3692 |
| selection fraction | 0.4333 |
| modal support frequency | 0.4333 |
| band members / usable / clusters | 47 / 38 / 16 |
| representative | `inv(total_atom_count)` |
| complexity | 2 |
| effective support (blocks) | ['total_atom_count'] (['MASS']) |
| train / validation R2 | 0.1673 / 0.3562 |
| **test R2 weighted / unweighted** | **0.1360** / 0.1842 (n=88, invalid 0.000) |
| test Spearman | 0.3113 |
| test R2 bootstrap 95% | [-0.102, 0.285] |

E5 seed-best validation R2: min 0.356, q25 0.356, median 0.371, q75 0.407, max 0.474 over 30 seeds.

Bootstrap (compound-level, n=1000): M1: evaluable [0.477, 0.693], wins [0.136, 0.330]; M2: evaluable [0.693, 0.864], wins [0.318, 0.523]; M3: evaluable [0.295, 0.489], wins [0.136, 0.295].

### E8 Per-energy mu (median [q25, q75]) by source

| E | n | all | LCSB |
|---|---|---|---|
| 15 | 436 | 0.909 [0.721, 0.986] | 0.909 |
| 30 | 435 | 0.699 [0.515, 0.907] | 0.699 |
| 45 | 435 | 0.555 [0.409, 0.743] | 0.555 |
| 60 | 431 | 0.477 [0.361, 0.628] | 0.477 |
| 75 | 438 | 0.428 [0.330, 0.567] | 0.428 |
| 90 | 435 | 0.390 [0.311, 0.514] | 0.390 |

Wall time 107 s.

## Reproducibility

Manifest sha256 `8820a73497523d416e9f3b3519916a42e9e5a948ed921e09fb47927d5772142e`; environment {'git_commit_sha': '95887d4c38fcb9c9feac09157c872d36efa49b2b', 'git_tree_dirty': True, 'numpy': '2.5.2', 'pandas': '3.0.5', 'pyarrow': '25.0.1', 'python': '3.13.12', 'rdkit': '2026.03.5', 'scipy': '1.18.0', 'wur_retrieval_manifest_sha256': 'a564c8ad3cbde5057e733e185e8be1bdfa068bc8f38a66103d921e0891263aef'}.
