# Phase 5 Data Lineage and Provenance

**Review date:** 2026-11-03. This report maps the data and derived outputs visible in the Phase 4 external reviewer package and the associated Phase 1–4 records. It is a provenance summary, not a statement that each upstream data transformation was independently re-executed in Phase 5.

## Lineage overview

```text
WUR development records and other development inputs
  -> frozen WUR-v2 candidate/reference model artifacts and model-selection history
  -> frozen candidate/reference predictions on the selected external evaluation frame

MSnLib source measurements (Orbitrap ID-X, HCD; underlying mzML not in archive)
  -> study's frozen decoding/eligibility/measurement process
  -> measured μ values + population/exposure/novelty records
  -> frozen model predictions and compound-rung errors
  -> external metric JSON / machine-readable tables / figures
```

The two input histories converge at the frozen external evaluation. Phase 5 verified the final statistical calculation from included outputs, not either raw-source transformation end to end.

## Population and artifacts

| Stage/artifact | Observed contents | Provenance and boundary |
|---|---|---|
| WUR-v2 development | Phase 3 supporting information reports 1,325 development compounds and 765 scaffold groups. | This is the project's frozen development record. The Phase 4 reviewer archive includes frozen model JSONs and selection/provenance reports; it does not include the restricted WUR raw library. The Phase 5 independent run did not reconstruct training records or rerun model search. |
| MSnLib external measurement frame | 1,794 measured compounds, with two recorded energy rungs per compound. | Study records describe selected MSnLib observations and frozen eligibility/exposure records. The Phase 4 archive does not include the third-party raw mzML files or acquisition system. |
| Support eligibility | 5 compounds excluded as unsupported by the frozen model profile; 1,789 scored; 1,687 scaffold groups. | Reproduced from the nested frozen-output kit's `external_analysis.json`; all 1,794 had measurements at both rungs according to the project record. Support exclusion is an analysis eligibility rule, not missing measurement. |
| Measured endpoint | `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv` in the nested archive. | 1,794 compound-level rows/endpoint values; derived from spectra upstream. SHA-256 in the Phase 5 extraction: `987e25458d6694c4eecf80905b44881d2c8fec23f572f0dc4770f91fe087e806`. No raw spectral arrays are included in that table. |
| Frozen analysis result | `artifacts/wur_v2_confirmation_v2/result/external_analysis.json`. | Contains population counts, P1 and secondary metrics, bootstrap summaries and decision label. SHA-256 in this extraction: `87102d01c6ae70510211313c0f0ba41852d8d1c848664d04ebe033fbeee1ccd0`. Recomputed by the included script in the fresh-extraction audit. |
| Derived compound errors | `supplement/COMPLETE_SUPPLEMENTARY_TABLES/external_compound_errors.csv` in the Phase 4 archive. | 1,789 rows and 14 fields, including chemical key, canonical structure/scaffold-group representation, measured μ at two rungs, candidate/reference predictions, rung errors and compound RMSE summaries. SHA-256: `0fb171f6df260c88f4a15295fa14b0e49bf11f43ecca634f378f37f4de52e029`. This is record-level derived data, not a raw-data file. It exposes structure-associated outcomes and therefore requires source attribution and rights review. |
| Figures | Five figure source tables and scripts are packaged. | Regeneration from those source tables passed. It does not reproduce source-table construction from mzML. |

## Model and evaluation records

The nested kit contains candidate/reference JSON model artifacts (`V2_TA_MORGAN_JOINT.json`, `V2_REF_TA_RIDGE.json`), the frozen validation population, novelty bins, exposure registry, scan allowlist, measured μ table, project source code, analysis script and expected primary result. The included verifier hashes package files and runs `scripts/wur_v2_confirmation_v2/11_external_analysis.py`. It does not retrain the models or repeat the development candidate-selection search. Model JSON presence is not equivalent to full training provenance or proof that the original training-data license permits redistribution of all model-derived artifacts.

The Phase 4 package's errors table aligns with the Phase 3 table byte-for-byte based on the identical SHA-256 recorded above. The Phase 4 figure script reads package-local machine-readable tables, enabling a standalone rendering route. The full-checkout source-table builder is explicitly not a standalone source-data reconstruction route.

## Exposure and independence notes

The frozen project records state that an earlier MSnLib sample was exposed and burned/permanently excluded, followed by a replacement cohort selected using outcome-blind eligibility and recorded key/scaffold exclusions. This is a documented project governance history, not an assertion that the final test molecules are chemically disjoint from all development chemistry. The records support study-specific exposure controls; general molecular independence and absence of scaffold similarity should not be inferred. Phase 5 did not access instrument raw files to independently redo the exposure census.

## Rights-relevant lineage boundary

Official Zenodo records identify the MSnLib spectral-library v8 record (DOI `10.5281/zenodo.21105617`) as open and CC BY 4.0, and the converted mzML record (DOI `10.5281/zenodo.15683784`) as open. The latter records describe Flow Injection Orbitrap ID-X measurements and deposited converted mzML archives. WUR's Zenodo record (DOI `10.5281/zenodo.20552933`) is marked **Restricted**, notwithstanding its metadata license field; the record points users to request access. Phase 4 does not redistribute WUR raw spectra. See `../release/FINAL_DATA_RIGHTS_REPORT.md` for a provisional asset-by-asset assessment.

An open upstream license does not by itself establish that this particular set of record-level transformations, compound identifiers/structures, WUR-trained model parameters, comparator weights or the entire package is cleared for unrestricted onward publication. Preserve source record/version, hashes, attribution and transformation documentation; obtain project-owner or rights-holder review before public redistribution where required.

## Verified reproduction boundary

The Phase 5 clean extraction re-executed the frozen external analysis from included measured μ and frozen population/model records and recovered the pre-recorded counts, RMSEs, ratio, interval and decision within `1e-12` for floating metrics. It did not reprocess MSnLib mzML, recreate μ from raw spectra, retrain the WUR-v2 model, reproduce development selection, or perform new experimental measurements. The analysis is conditional on the frozen energy mapping and measured endpoint inputs.
