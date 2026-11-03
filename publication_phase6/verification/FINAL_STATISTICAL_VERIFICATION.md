# Phase 5 Statistical Evidence and Source-Path Audit

**Scope.** This task audited the Phase 4 statistical claims against frozen source code, protocols, model records, and saved outputs. It did not run a new model comparison, alter predictions, or construct any new interval. Numerical values below are the frozen output values and checked definitions; Phase 5 is not an independent reproduction of the analysis script.

## Primary MSnLib estimate

The frozen record `artifacts/wur_v2_confirmation_v2/result/external_analysis.json` (SHA-256 `87102d01c6ae70510211313c0f0ba41852d8d1c848664d04ebe033fbeee1ccd0`) reports:

| Quantity | Candidate | Tier A reference |
|---|---:|---:|
| Pooled P1 RMSE | 0.12961151072591617 | 0.13352761116871245 |
| Per-compound mean RMSE | 0.1121373873 | 0.1175157920 |
| AF, compound RMSE > 0.20 | 0.1185019564 | 0.1179429849 |
| CVaR95 | 0.2656786395 | 0.2648634968 |

The saved candidate/reference ratio is **0.9706719800607511**, and the 95% scaffold-bootstrap interval is **[0.9523611879747089, 0.9892672061846276]**. Relative P1 reduction is 2.9328%. The point and both interval endpoints are greater than 0.95; the directional result is below one, but the frozen 5% practical-improvement target is not met.

The population records identify 1,794 measured compounds, five compounds outside the joint support rule, 1,789 scored compounds, and 1,687 scaffold groups (3,578 two-rung cells). The analysis excludes a compound when either model is outside profile-knot support at one or more rungs. This is a joint-rule exclusion, not a finding that the five were missing or unmeasured.

## Statistical definitions checked against implementation

| Manuscript quantity | Source implementation | Audit result |
|---|---|---|
| P1 | `src/muru/wur_v2/metrics.py::p1` | `sqrt(nanmean(errors**2))`, pooled over finite cells; manuscript equation agrees |
| Compound RMSE and AF | `metrics.py::compound_rmse`, `summary` | Two-rung compound RMSE; AF is proportion >0.20; AF_max is any-rung absolute error >0.30 |
| Ratio | `metrics.py::cluster_bootstrap` | Candidate P1 / reference P1; below one favors candidate |
| Bootstrap unit | `metrics.py::cluster_bootstrap` | Whole scaffold group; group multiplicity is multinomial, groups sampled with replacement; all member compounds and both rungs retained |
| Bootstrap settings | `scripts/wur_v2_confirmation_v2/11_external_analysis.py` | B=10,000; seed=20261011 |
| Percentile interval | `metrics.py::cluster_bootstrap` | `numpy.percentile` at the equal-tail endpoints (default linear quantile interpolation); no BCa/max-T correction |
| Practical criterion | Frozen MSnLib protocol and decision code | Point ratio ≤0.95 is the 5% practical threshold; a confidence interval below 1 is not sufficient |
| Tail override | `11_external_analysis.py` | Adverse tail gate when upper 95% bound of candidate-minus-reference AF exceeds +0.03; frozen result is below that adverse limit |
| Novelty quartiles | `freeze/novelty_bins_per_compound.csv`, `05_novelty_bins.py` | Four fixed bins from maximum Morgan-count Tanimoto similarity; descriptive estimates, no quartile CIs |

The bootstrap is conditional on the scored frame, endpoint, frozen models and energy mapping. It quantifies sampling variation across the 1,687 observed scaffold groups; it does not quantify training uncertainty, model-selection uncertainty, raw-data processing uncertainty, or physical energy-calibration uncertainty. Quartile and per-rung summaries are secondary/descriptive. No multiplicity-adjusted subgroup claim is supported.

## Source chain and hashes

| File | SHA-256 | Role |
|---|---|---|
| `scripts/wur_v2_confirmation_v2/11_external_analysis.py` | `5a8acda42963e0e48ca0e5f6be9794695e76bd86af58a004d9d162f66c033c89` | Applies energy map, joint support rule, P1 summaries, bootstrap, AF decision, and secondary outputs |
| `src/muru/wur_v2/metrics.py` | `48c8cfb984808887ce20594ca88976e7d05717296ed27b03242953fbaaef6374` | Metric and cluster-bootstrap implementations |
| `src/muru/wur_v2/candidate.py` | `c82835f1b9b82bee1e25f4b67699b4055108705bbcde5a0805b3e7e62a256c1c` | Frozen model inference and profile support |
| `src/muru/wur_v2/models.py` | `572c0ed668ad277fe69ef7f7521d9e44696c722bd035b4464719352db6b70ee1` | Ridge model and feature preprocessing |
| `src/muru/wur_v2/representations.py` | `3c28730b5cb45b7a63fa65168e0e4630ef8cafbc127a6aae1f4c2e5d1123a323` | Morgan fingerprint generation |
| `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv` | `987e25458d6694c4eecf80905b44881d2c8fec23f572f0dc4770f91fe087e806` | Measured external μ values |
| `artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv` | `37b573d38955629e6959f310f4a6c0de14e0dca47ab31695d4edab5485ca0e8d` | Frozen structures, masses, scaffold groups and evaluation population |
| `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json` | `f2ca0322ab75bbcc2ee91e66be07172966d0492060c7669107e1f9081edf58c3` | Candidate coefficients, profile and canaries |
| `artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json` | `de9afa119b80ddc46ffebf98783ac18bfa97c79f0e9e7adf57c300cd9fc6146f` | Tier A reference coefficients/profile |
| `publication_phase3/reviewer_package/SHA256SUMS.txt` | `6222405b56f12cd0879109b3e30fce2b28c6e768598a11f3d1ccd9ce19edb911` | Phase 3 reviewer-package internal checksum manifest |
| `publication_phase3/release/MURU_PHASE3_REVIEWER_PACKAGE.zip` | `4a68ff73a98933ff9e827831812006d8a2ce3ae1d55674523013a5ba8a1e857a` | Distribution archive used as reproduction entry point |

The Phase 3 package includes the saved predictions’ generating script and frozen model/input artifacts, so a package reproduction runs the frozen analysis code over frozen inputs. This is a statistical reconstruction from derived measured-μ values and model artifacts, not independent implementation or independent experimental replication. Raw MSnLib mzML is not included and retraining is not part of this source chain.

## Phase 4 manuscript/reports: discrepancies requiring reconciliation

1. **Tail gate omitted from manuscript Methods.** Results report AF difference and the +0.03 rule is described in the frozen analysis, but Phase 4 Methods §2.7 does not state the +0.03 adverse-tail override or the ordered decision rule. “Direction and tail rule” in the Abstract/Introduction is not enough for a reader to reconstruct the frozen verdict. The Phase 4 verification report should add the threshold and decision order.
2. **Historical development selection amendment omitted.** Methods §2.2 says the candidate was selected from a 13-family search and admitted under a simplicity rule. The frozen protocol’s amendment A-3 (2026-09-13) says it was made after all development results and five reviews were visible; it restated criterion c4 for Tier-A-plus-fingerprint models and says EXP08B was admitted under the restated rule, while the literal original c4 failed. The manuscript does not disclose this timing/deviation. This is selection-history provenance and should be stated explicitly; it does not change the external frozen P1 values.
3. **Development CI discussion gives the wrong missingness explanation.** Phase 4 §3.2 says Phase 2 reports were recovered, but the Discussion says the calculation source was unavailable “because the specified Phase 2 audit directory and commit were absent.” The report was recovered; the original max-T code/seed/resamples/selection ledger were not. See `FINAL_MAXT_PROVENANCE.md`.
4. **“Refitted” reference terminology is inconsistent.** Methods §2.5 calls the external contrast one with a “refitted descriptor reference”; Methods §2.6 correctly says the frozen Tier A reference was trained/selected on development data and applied without external refitting. Use “frozen reference” for MSnLib; reserve “refitted within each development training fold” for grouped development estimates.
5. **“Independent” wording is too broad in Figure 1.** The caption separates “independent external evidence.” The replacement sample was an outcome-blind external draw under recorded compound-key/scaffold exposure controls, but the record does not establish no analog similarity or absence of every unrecorded exposure. Prefer “external evaluation” and preserve the exposure history.
6. **P2 sanitized census JSON is not a sufficient source artifact.** It lists four frames only as repeated “step 10b/step 12b” and does not distinguish DESIGN from DETECTED_POSITIVE or retain the four population hashes and watched-input hashes. The Phase 4 narrative has the numbers, but the JSON cannot independently regenerate or substantiate that table. See `FINAL_CENSUS_ERRATUM.md`.

## Overall finding

No discrepancy was found in the stored external population counts, candidate/reference P1 values, ratio, scaffold-bootstrap interval, threshold interpretation, or adverse Q1 result. The central numerical contrast is correctly bounded as a conditional, one-time external evaluation of two frozen pipelines. Important remaining fixes concern decision-rule transparency, candidate-selection chronology, max-T provenance wording, terminology, and the loss of frame-level machine-readable census provenance—not a new favorable or unfavorable performance estimate.

## Phase 6 fresh extraction

The Phase 4 nested frozen-output reviewer package was extracted into a new temporary directory and `python3.13 verify_reproduction.py` was run there. Exit code 0; output began `PASS: checksums, required files, environment, frozen external result`. Reconstructed counts and statistics matched the expected JSON exactly within the verifier's 1e-12 floating tolerance: n=1794, excluded=5, scored=1789, scaffolds=1687, candidate P1=0.12961151072591617, reference P1=0.13352761116871245, ratio=0.9706719800607511, CI=[0.9523611879747089,0.9892672061846276], decision `MODEST EXTERNAL CONFIRMATION`.

Separate fault injection altered `expected_primary.json` and removed `measured_mu.csv`; the verifier returned nonzero in both cases with `CHECKSUM MISMATCH: expected_primary.json` and `MISSING: artifacts/wur_v2_confirmation_v2/result/measured_mu.csv`. This is statistical reconstruction from frozen derived outputs; it is not raw mzML-to-μ reprocessing or retraining.
