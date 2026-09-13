# MURU-WUR-v2: exposure and data registry

**Created:** 2026-09-12, before any v2 model comparison.
**Machine-readable manifest:** `artifacts/wur_v2/exposure_manifest.json` (per-population key lists and sha256).
**Builders:** `scripts/wur_v2/build_v2_spectra.py`, `scripts/wur_v2/build_v2_population.py`, `scripts/wur_v2/build_v2_exposure_manifest.py`.

## 1. Repository state and drift check

| Item | Value |
|---|---|
| Accepted lineage | `fable/wur-stage2-muru-development` |
| Head named in the v2 brief | `17027e13614cc850d88bcb72b3e8b8c2458eb00a` |
| `origin/fable/wur-stage2-muru-development` at audit time | `17027e1`, identical; no later legitimate state exists |
| v2 branch | `claude/muru-wur-v2-generation-b2ffa1`, reset onto `17027e1` (it had no commits of its own; it had been created from `main`, which does not carry the WUR program) |
| Stage 3 one look | HEAD `69ca1a6`, 2026-09-12T19:55:23Z, clean tree (`artifacts/wur_stage3/first_sealed_access.json`) |
| WUR test suite at `17027e1` | 242 passed |

**Drift found and repaired (environment, not science).** The WUR release bytes lived only in a `wur-stage0-partition-and-seal` worktree that no longer exists; the symlink chain `data/external/wur` was dangling in every surviving worktree. The bytes were restored from the original download (`~/Downloads/20552933.zip`, 203,752,342 bytes, sha256 `96fe2b1a...d2`, equal to the pinned whole-archive hash) and all 20 per-file hashes in `muru.io.wur_retrieval.EXPECTED_FILES` verify. LCSB parquets were copied from the main checkout and are byte-identical to the Stage 2 worktree's copies.

## 2. Population registry

Exposure classes: **development-exposed**; **historical holdout now exposed**; **historical external validation now exposed**; **prohibited/excluded**; **potential future external source, not outcome-accessed**.

| Population | Keys | Class | v2 use | Basis |
|---|---|---|---|---|
| LCSB-DEV | 439 | development-exposed | development | Phase 2 corpus, fitted since Phase 2 |
| WUR-DEV-ANALYSIS | 476 (124 also LCSB-DEV) | development-exposed | development | Stage 2A/2B; the 124 shared keys fitted the Stage 1 bridge |
| WUR-DEV-HOLD | 130 | historical holdout, now exposed | development | one look, `artifacts/wur_stage2b/hold_check.json` |
| WUR-SEALED | 404 | historical external validation, now exposed | development | one look at `69ca1a6`; **can never again support an independent external claim** |
| LCSB-CONFIRMATION | 110 | prohibited/excluded | excluded | Phase 2 seal, never fitted or scored; Phase 1 endpoint screen saw it. 41 keys are also WUR-SEALED: their WUR copies are v2 data, their LCSB spectra stay excluded. 10 of its compounds appear in the Phase 1 raw-mixture repeatability scans; v2 repeatability analyses drop them |
| WUR-NEG-DEV | 209 | prohibited/excluded | excluded | negative mode, header/identity read in Stage 0, peaks never decoded; outside the v2 positive-ion domain |
| WUR-NEG-D6-EXCLUDED | 32 | prohibited/excluded | excluded | rule D6 |
| LCSB-NEG | 379 | prohibited/excluded | excluded | Phase 1 descriptive census only; outside domain |
| LCSB raw mixes 499/503/505 | 39 | development-exposed | repeatability only (29 non-confirmation compounds) | Phase 1 `REPEATABILITY.md` |
| MultiMS², MSnLib, MetaSci, BMDMS-NP, non-LCSB MassBank/MoNA cohorts | n/a | potential future external, not outcome-accessed | identity/metadata census only (MultiMS² first) | no peak, mu, survival, count or residual may be read before a committed v2 final-candidate freeze |

**v2 development population:** LCSB-DEV union WUR-DEV-ANALYSIS union WUR-DEV-HOLD union WUR-SEALED = **1,325 connectivity keys**, sha256 `81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd`; 439 LCSB-primary, 886 WUR-primary, 124 measured on both instruments; 765 stereo-free Murcko scaffold groups (785 with v1's stereo-retaining scaffolds), 88 acyclic singletons, 558 strict structural clusters; adducts 1,289 [M+H]+, 20 [M+NH4]+, 8 [M+Na]+, 8 [M]+. Every v2 result is development evidence, including results on formerly held-out or sealed compounds.

## 3. Spectrum-level facts that change v1's reading

1. **Most WUR "duplicates" are archive copies.** The release's combined library repeats every sub-library spectrum with the same SpectrumId, scan number, creation date and byte-identical peaks. Of 6,060 positive-mode (key, energy) cells, 5,580 hold two archive copies of one acquisition and 234 hold one row. v1's `n_spectra` (for example "5,030 spectra" on WUR-SEALED) counts archive rows, not measurements.
2. **Distinct acquisitions at one key are almost all different isomers.** 222 cells (42 keys) carry 2 to 5 distinct acquisitions; in 41 of the 42 keys these are different stereoisomers or E/Z isomers sharing a connectivity key (for example pyrrolizidine alkaloid E/Z pairs eluting 0.04 min apart in one batch). They are not technical repeats. v1's median merged them with their archive copies; v2 collapses archive copies first, then takes the median over distinct acquisitions (policy D-AGG). That moves 25 of the 5,954 v1 aligned cells, at most 0.066 in mu.
3. **WUR contains essentially no independent technical replicate of a stereo-defined compound** (one key). Empirical WUR injection/day repeatability cannot be measured from this release.
4. **Repeat structures that do exist:** LCSB raw inter-mixture scans (separate preparations and injections, Q Exactive, 29 usable compounds); within-run DDA scans (a lower bound); the 124 compounds measured on both instruments (a cross-lab, cross-instrument pair that includes the bridge); and the 42 WUR stereoisomer groups (an isomer-plus-noise diagnostic, not repeatability).
5. **Acquisition metadata available in the mzVault files:** scan filter with scan range (WUR low-mass bound m/z 40; FCH 47), retention time, scan number, creation date (batch), operator group (WFSR 12,132 rows, ETE 288, FCH 12), curation type "Averaged,Thresholded". LCSB records carry RMassBank recalibration and formula-annotation filtering and no scan range.

## 4. Inventory of prior evidence reconciled with the research report

| Report claim | Repository evidence | Reconciliation |
|---|---|---|
| V1B P1 0.1251; S2A 0.1475; B1 0.1420; B0 0.1676; V1C 0.1236; V1A 0.1306; WUR-only 0.1265 | `artifacts/wur_stage3/stage3_result.json`, `MURU_WUR_STAGE3_RESULT.md` | confirmed from artifacts; recomputed in v2 Experiment 1 |
| Training population at freeze 921 = 791 DEV2B + 130 HOLD | freeze document, `stage3.training_population` | confirmed |
| P1 is pooled-cell RMSE; Stage 3 intervals bootstrap per-compound RMSE differences | `cv.fold_metrics` (P1 = sqrt(nanmean over cells)); `stage3.run` builds `dc = rmse[c] - rmse[r]` and `holdcheck.paired_boot` resamples its mean | confirmed; the intervals are for the mean per-compound RMSE difference, not for the P1 difference |
| "Reliability 0.988" is curvature-based | `docs/wur_stage2b_failure_analysis/t4_t5_t6_descriptors.py` line 93: `1 - median(g_var) / Var(log g)`, with `g_var = sigma^2 / sum_E (d mu / d log g)^2` from `estimate.fit_collapse` | confirmed; not empirical repeatability |
| 0.0295 repeatability is inter-mixture | `REPEATABILITY.md` | confirmed; an upper bound on technical repeatability at the Q Exactive, worst at NCE 30 (0.056) |
| 15 folds, 13 distinct held-out sets, benzene always fold 0 | `artifacts/wur_stage2b/folds.json`, adjudication IM-C1 | confirmed; benzene group is 183 compounds, 23 percent of DEV2B, 13.8 percent of the v2 population |
| Earlier Morgan work | Phase 2 Tier B: Morgan r2 2048 bits, 692 bits set in >= 5 molecules (structure-only floor computed on the whole dev corpus) + 26 RDKit descriptors, HistGradientBoosting on energy + features, direct per-cell mu, LCSB only (439), scaffold split S2 | a different model family and endpoint: FLEX 0.1004 vs Tier A 0.1123 cell MAE (a 10.6 percent gain over Tier A, CI excluding zero). Prior evidence that fingerprints carry information beyond Tier A for a direct per-cell model; never tested as a scale predictor on the collapse |
| Shape / two-parameter attempts | Stage 2A ladder (H-MAIN rejected, M1-M3 win where evaluable); failure analysis T3/T9/T10 (logistic 4-parameter fits, direct per-energy ridge, tilt, asymptote); ledger V2A two-parameter ridge (P1 0.1513, fails); red-team two-parameter oracle ceiling 5.9 percent | shape parameters were descriptively real and not predictable from Tier A; aliasing with g confirmed |
| Other negative results | Stage 2A NO_REPORT in all analyses; V1C (+0.9 percent, hypothesis failed), V1D (black-box bar failed), S2A gate refused 15/15 folds; spectral summaries other than mu less predictable | recorded; none are repeated under a new name in v2 |
| 24 boundary compounds, heavy, at the profile floor at E30 | failure analysis T2 | to be re-measured on the v2 population (Experiment 2) |

## 5. Audit findings carried into v2

| Id | Finding | Consequence |
|---|---|---|
| AU-1 | Archive copies and isomer acquisitions were aggregated as if duplicates (section 3) | v2 policy D-AGG; spectra keep acquisition ids |
| AU-2 | No WUR technical replicates | Experiment 2 states exactly what cannot be measured |
| AU-3 | Curvature "reliability" mislabelled as a noise ceiling | never repeated; empirical quantities only |
| AU-4 | Estimand mismatch between P1 and the bootstrap | v2 bootstraps recompute P1 inside each replicate and report both estimands separately |
| AU-5 | `stage3.sealed_tables` and `holdcheck.run` would overwrite their one-look records if called directly (the scripts guarded, the functions did not) | function-level refusal added, with tests (`tests/wur_v2/test_v2_one_look_guards.py`); no historical artifact touched |
| AU-6 | v1 scaffold strings kept stereochemistry (LK-1) | v2 groups on the stereo-free parent scaffold |
| AU-7 | v1 fold design repeated one giant group in fold 0 of three repeats | v2 uses one primary grouped partition, each compound held out once, pooled out-of-fold scoring, explicit giant-group stress tests |
| AU-8 | `precursor_mz` descriptor is the adduct m/z, so 36 non-protonated WUR compounds carry an ion-mass shift | domain flag in trust; [M+H]+ stratum reported |
| AU-9 | Low-mass acquisition bound differs by campaign (WUR m/z 40, FCH 47; LCSB unstated, formula-filtered) | observable-compatibility gate for any external source |
| AU-10 | WUR raw bytes were not reachable from any worktree (section 1) | restored and hash-verified; registry records it |

## 6. Guards in force

- `muru.wur_v2.exposure.assert_wur_exposed` must pass before any v2 code decodes HOLD or SEALED peaks; it requires both one-look records.
- `stage3.sealed_tables` and `holdcheck.run` refuse a second call.
- v2 loaders drop LCSB confirmation keys by key before any value column is used, and the population builder asserts none remain.
- Any external source is handled by a separate outcome-blind census; a v2 external result path will refuse to run twice (see the final-candidate freeze when it exists).
