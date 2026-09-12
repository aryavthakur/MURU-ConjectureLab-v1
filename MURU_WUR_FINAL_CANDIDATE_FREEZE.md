# MURU WUR: final candidate freeze

**Candidate id:** `V1B_RIDGE_TIERA` (generation label MURU-WUR-v1; the label records lineage under the Stage 2B protocol and does not claim a new law or representation)
**Frozen at:** the commit carrying this document; code SHA at freeze time `a8f9539b49629853e51bafe65b5017956376d88c` (parent) plus this commit
**Evidence:** `MURU_WUR_STAGE2B_SELECTION.md`, `MURU_WUR_STAGE2B_REVIEW_ADJUDICATION.md`, `artifacts/wur_stage2b/ledger/`, `artifacts/wur_stage2b/hold_check.json`
**Status of WUR-SEALED at freeze:** untouched. No peak, mu, descriptor, g or outcome of any of the 404 sealed compounds has been computed. The only code path that can decode a sealed spectrum is `muru.wur_stage2.stage3.sealed_tables`, which passes `allow_sealed=True`; every other builder refuses.

## 1. Exact scientific specification

| Item | Frozen value |
|---|---|
| Endpoint | `features.mu` at the base preprocessing cell (`relative_cutoff 0.0, include_precursor true, intensity_transform raw, precursor_match_ppm 10.0`); WUR duplicates at a (key, energy) collapse by the median; LCSB by the corpus mean |
| Energy representation | LCSB nominal NCE coordinate; pooled rungs 30, 45, 60, 75, 90; `ENERGY_SCALE = 30` |
| Stage 1 map | `T(E) = -5.95552603907965 + 0.8618030610784555 E`, applied to the LCSB nominal energy to give the WUR nominal energy at which WUR is read, PCHIP on each compound's six-rung ladder, clamped, never extrapolated, never refitted |
| E = 15 | never in a pooled fit; reported separately, native |
| Collapse | `discovery.estimate.fit_collapse` on the training compounds: 3 alternations, 60 isotonic knots on log u, `log g` grid `[-1.6, 1.6]` x 241, unit geometric mean; inverse-variance weights |
| Descriptors | the twelve Tier A features `protocol.FEATURES`, scaled by `protocol.SCALE`; WUR `precursor_mz` = median declared precursor mass over the key's accepted spectra; SMILES-derived features from `molecules.tier_a_descriptors` |
| Model | `cv.LinRidge`: ridge regression of log g on the twelve scaled descriptors with sample weights = collapse weights; alpha chosen from {0.01, 0.1, 1, 10, 100} by inner 4-fold scaffold-group CV (`folds.inner_folds`, seed 20260916 + 0) on the training population; prediction `mu(E) = Phi_train((E/30) / exp(log g_pred))` |
| Training population for Stage 3 | DEV2B (791 keys, sha `f38f2d806df6659059e7aea6639481cb5d72c37ab2291485c50afb58239c1ee3`) plus WUR-DEV-HOLD (130 keys, sha `3c45858224363e8ad132dbe46706311238db675e656a5a3bf5b2b6b1854edd94`), 921 compounds. This is a deviation from the fold estimates (trained on ~633) and is stated as such |
| Excluded populations | WUR negative mode (all); LCSB confirmation set (110 keys); the 32 D6-excluded negative trajectories; nothing else |
| Selector / gate | none. The candidate always predicts. The frozen pre-WUR gate (t1 0.595, t2 0.2) is evaluated only inside the S2A comparator arm |
| Thresholds | none in the candidate |
| Adequacy rule | not part of the candidate; the frozen M0 to M3 ladder is reported descriptively only |
| Uncertainty / calibration | no confidence output (the exploratory one was inert and dropped). Uncertainty on every Stage 3 comparison: compound-level paired bootstrap of per-compound RMSE differences (2,000 resamples, seed 20260911), 90 and 95 percent percentile intervals, plus a stereo-merged-scaffold cluster bootstrap |
| Seeds | collapse deterministic; ridge deterministic; S2A comparator PySR seeds `protocol.seed_list("WUR2B|S2A|r3f0")`; bootstrap 20260911 |
| Preprocessing robustness | S7: +2.3 percent under cutoff 0.01, -3.5 percent without precursor, ordering unchanged (`artifacts/wur_stage2b/s7_preprocessing_perturbation.json`) |
| WUR-SEALED hash | `6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52`, 404 compounds, 275 scaffold groups |

Comparator arms, trained on the same 921 compounds: `S2A_FROZEN_PIPELINE` (the pre-WUR method: same collapse, 30-seed PySR on an inner 60/20/20 scaffold split, B2/R1 selector, gate recorded, forced prediction scored), `B0_NULL_PROFILE`, `B1_MASS_ONLY_ISOTONIC`, `V1A_STABLE_LAW` (secondary), `V1C_RICH_RIDGE_24` (exploratory), and `V1B_WUR_ONLY_TRAINED` (the candidate trained on the WUR rows only, secondary).

## 2. Development evidence, for the record

| Population | V1B | S2A | B1 | B0 |
|---|---|---|---|---|
| DEV2B, 13 distinct scaffold-group folds (P1 mean) | 0.1349 | 0.1539 | 0.1523 | 0.1814 |
| HOLD, one look, n = 130 | 0.1298 | 0.1588 | 0.1438 | 0.1684 |

HOLD: V1B versus S2A relative improvement 18.3 percent, 90 percent compound interval on the paired difference [-0.040, -0.023], cluster interval [-0.043, -0.022]; versus B1 9.7 percent, [-0.024, -0.009]. All four frozen HOLD conditions passed. 21 of the 130 HOLD compounds share a stereo-merged scaffold with an LCSB development compound; excluding them V1B is 0.1327, S2A 0.1623, B1 0.1402. V1C and V1A are not distinguishable from V1B on HOLD (intervals through zero), as the reviews predicted.

## 3. Stage 3 endpoints, pre-registered

Population: all 404 sealed positive-mode trajectories, no exclusions. Every compound's descriptors must compute; a failure is reported and excluded with its count. Aligned coordinate is primary; native is secondary.

| Id | Endpoint |
|---|---|
| S3-1 (primary) | P1 of V1B versus S2A on the aligned pooled rungs; paired compound bootstrap 90 and 95 percent; cluster interval |
| S3-2 (primary) | P1 of V1B versus B1 |
| S3-3 | P1 of V1B versus B0; B1 versus S2A (does the pre-WUR method beat mass at all) |
| S3-4 | per-rung S1 and per-compound S2, S4 for every arm |
| S3-5 | strata: benzene scaffold (`c1ccccc1`) versus other |
| S3-6 | S2A under its own gate: report or abstain, with its gate features |
| S3-7 | secondaries: V1A versus S2A; V1A versus V1B; V1C versus V1B (non-inferiority, exploratory); V1B trained on WUR rows only versus V1B |
| S3-8 | native-coordinate P1 for V1B, S2A, B0, B1 |
| S3-9 | E = 15, native, separate, descriptive only |

**Success:** the principal claim survives iff P1(V1B) < P1(S2A), P1(V1B) < P1(B1), relative improvement over S2A >= 2.5 percent, and the 90 percent compound interval of the paired V1B - S2A difference lies below zero. Anything else is a failure of the principal claim and is reported as such. No endpoint may be added, removed or reweighted after the sealed read.

## 4. The claim being tested

On independent real HCD spectra of compounds whose scaffolds were never seen, a ridge regression of the collapse scale on twelve molecular descriptors, on the frozen shared-profile collapse, predicts mu trajectories better than the pre-WUR MURU pipeline forced to predict and better than a mass-only model. That is the whole claim. It does not claim a discovered law, a calibrated report gate, or a representation beyond Tier A.

## 5. Prohibitions after the reveal

No refit of the map, the collapse, the ridge or any comparator; no change to features, thresholds, population, metric or endpoint list; no second model run against the sealed data; no repair-and-revalidate on the same population. A weakness found at Stage 3 is diagnosed and recorded; a future generation needs a new untouched external set for any definitive claim.

## 6. Allowed artifact outputs

`artifacts/wur_stage3/`: `first_sealed_access.json` (written before the decode), `stage3_result.json`, `stage3_percompound.csv`, `sealed_long_aligned.csv`, `sealed_long_native.csv`, `sealed_covariates.csv`, `ckpt_s2a_stage3/`, `freeze_precedes_access_audit.json`. Nothing else.
