# Supporting Information

## S1. Study population, lineage, and exclusions

| Stage | Compounds | Groups | Status and source |
|---|---:|---:|---|
| WUR-v2 development set | 1,325 | 765 scaffold groups | Development; frozen training population |
| MSnLib final confirmation population | 1,794 | 1,691 before support exclusion | Two fixed HCD NCE rungs; no incomplete compounds |
| Unsupported-profile exclusions | 5 | 4 groups removed from scored group count | Outside at least one candidate/reference profile support point |
| Primary scored population | 1,789 | 1,687 | Frozen external analysis denominator |
| Scored compound-rung cells | 3,578 | — | Two measured rungs per scored compound |
| Earlier MSnLib sample 1 | 2,690 | 2,000 sampled groups | Exposed before outcome scoring; not scored; permanently excluded |
| CE Design A | 33 | 33 singleton groups | Separate exposed CE-interface adjudication population |

Population flow, header eligibility, exposure registry and record hashes are stored under `artifacts/wur_v2_confirmation_v2/` and described in `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md`. The final sample was selected once from an outcome-blind eligible universe. Source records show 6,004 of 6,004 allowlisted spectra decoded, with zero empty/nonpositive spectra. The 5 support exclusions are not missing measurements; all 1,794 compounds had both rungs.

## S2. Dataset lineage and provenance

The WUR development corpus combines a MassBank/LCSB multi-collision-energy acquisition collection and WUR spectral records. The release's development protocol specifies positive mode, fixed feature/identity handling, a five-fold scaffold-grouped primary partition, two additional partition sensitivity checks and a strict similarity-cluster split. The external confirmation used positive-mode MSnLib screening-library spectra collected on a Thermo Orbitrap ID-X at fixed HCD NCE 20 and 60. The final measured values are in `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv`; per-spectrum derivations are in `measured_mu_per_spectrum.csv`. Raw MSnLib mzML ZIPs are referenced by source DOI 10.5281/zenodo.15683784 and checksums, but are not redistributed here.

The supplied Phase 2 audit folder, named reports, audit commit `459a78a8ef0ac7a3e92d15c25be38cc8d86403b6`, and Phase 2 deliverables archives were not present in the workspace or remote refs inspected for this phase. The frozen release branch and its root records are used instead. This is a provenance limitation for claims specifically attributed to the absent audit artifacts.

## S3. Model specification

The frozen candidate is `V2_TA_MORGAN_JOINT`, fit on 1,325 development compounds. The 12 Tier A inputs are precursor m/z, total atoms, rotatable bonds, ring count, aromatic-ring count, RDBE, TPSA, heteroatom fraction, nitrogen count, oxygen count, sulfur count and halogen count. Tier A values are divided by frozen descriptor-specific scale constants, then standardized using training-only means and standard deviations. The Morgan block is a radius-2, 2,048-dimensional count fingerprint, `log1p` transformed, no chirality, RDKit 2026.03.5; its design columns are multiplied by 0.1. Candidate ridge α is 0.3, selected from `{0.1, 0.3, 1, 3, 10, 30, 100, 300}` jointly with Morgan block weights `{0.1, 0.3, 1.0}`. The reference is a separate Tier A ridge with α = 0.1, selected from `{0.01, 0.1, 1, 10, 100}`. Selection uses grouped inner folds and curvature inverse-variance weights normalized to mean one. The shared response profile is fitted by decreasing isotonic regression on log-u, represented by 60 evenly spaced knots, in three alternating updates; per-compound log-scale uses a 241-point grid over [−1.6, 1.6] with parabolic refinement. Both feed the same frozen 60-knot monotone response profile. Exact coefficient vectors, knots, profile values, canaries and model hashes are in `artifacts/wur_v2/candidate/*.json`.

## S4. Metric definitions and uncertainty

For cell error `e_iE = μhat_iE − μ_iE`, P1 is `sqrt(sum(e_iE^2) / N_cells)`. Compound RMSE is `sqrt(mean_E(e_iE^2))`. MRMSE is the arithmetic mean of compound RMSEs. CVaR95 is the arithmetic mean of the largest `ceil(0.05*n)` compound RMSE values. AF is the proportion with compound RMSE greater than 0.20. AF_max is the proportion with at least one absolute per-rung residual greater than 0.30. The primary ratio is candidate P1 divided by Tier A reference P1; it is below one when the candidate has lower pooled error.

The primary confidence interval resamples whole Bemis–Murcko scaffold groups with replacement. In each of 10,000 replicates, the code recomputes pooled P1 separately for both models and then the ratio. The random seed is 20261011. The resulting percentile 95% interval is [0.95236118797, 0.98926720618]. This interval reflects observed-group sampling uncertainty under the frozen model and endpoint; it does not account for model selection, external dataset selection, instrument transfer, or energy-map uncertainty.

## S5. Full external performance

| Metric | MURU | Tier A reference |
|---|---:|---:|
| P1 | 0.1296115 | 0.1335276 |
| MRMSE | 0.1121374 | 0.1175158 |
| Median compound RMSE | 0.0995566 | 0.1075164 |
| Q90 | 0.2070537 | 0.2065879 |
| Q95 | 0.2315082 | 0.2348610 |
| CVaR95 | 0.2656786 | 0.2648635 |
| AF, RMSE > 0.20 | 0.1185020 | 0.1179430 |
| AF_max, any |error| > 0.30 | 0.0620458 | 0.0609279 |

| Paired contrast | Estimate | 95% scaffold bootstrap interval |
|---|---:|---:|
| P1 ratio | 0.9706720 | [0.9523612, 0.9892672] |
| P1 difference | −0.0039161 | [−0.0064386, −0.0014271] |
| MRMSE difference | −0.0053784 | [−0.0077144, −0.0030316] |
| AF difference | +0.0005590 | [−0.0145253, +0.0155383] |

## S6. Per-energy and novelty results

| Rung | n compounds | MURU RMSE | Reference RMSE | Ratio | Mean signed residual MURU | Mean signed residual reference |
|---:|---:|---:|---:|---:|---:|---:|
| NCE 20 | 1,789 | 0.1643762 | 0.1673566 | 0.9821913 | −0.0077006 | +0.0353532 |
| NCE 60 | 1,789 | 0.0811095 | 0.0874700 | 0.9272829 | +0.0033380 | +0.0206737 |

| Frozen novelty quartile | Similarity interval | n | MURU P1 | Reference P1 | Ratio |
|---|---|---:|---:|---:|---:|
| Q1, most novel | [0.000, 0.281) | 449 | 0.1276850 | 0.1266343 | 1.0082968 |
| Q2 | [0.281, 0.319) | 462 | 0.1330779 | 0.1378284 | 0.9655334 |
| Q3 | [0.319, 0.364) | 456 | 0.1267815 | 0.1321610 | 0.9592956 |
| Q4, least novel | [0.364, 1.000] | 422 | 0.1308194 | 0.1373041 | 0.9527711 |

The similarity is maximum Morgan-count Tanimoto similarity to the 1,325 development compounds. No quartile-specific confidence intervals are available in the frozen primary output; these results are descriptive.

## S7. Comparator benchmark and energy conventions

The public comparator result is a separate full-spectrum metric study and must not be numerically merged with the scalar P1 study. Under the primary mapped convention, MURU P1 = 0.1265, FIORA-OS v0.1.0 = 0.2046 (ratio 0.619), ICEBERG 2.1 = 0.1621 (ratio 0.781), and GLACIER = 0.1384 (ratio 0.914). In the raw-NCE diagnostic, ICEBERG P1 = 0.1176 (MURU/comparator ratio 1.076) and GLACIER P1 = 0.1022 (ratio 1.238). The comparator models have different architectures, feature sets, training data, model-selection processes, spectral objectives, and CE provenance; these are not feature-matched algorithm comparisons.

The MURU development-to-validation map is `T(E) = −5.95552603907965 + 0.8618030610784555 × E`. External scoring inverts it at NCE 20 and 60. This is fixed and outcome-free for MSnLib, but no physical calibration experiment validates it as a universal NCE-to-eV transform. Thermo describes NCE as dimensionless and approximately equivalent to energy for a reference ion of mass 500 and charge 1; source training labels and checkpoint preprocessing for public comparator models remain partly unresolved. CE Design A used 33 compounds and concluded `INTERFACE_UNRESOLVED` because adjusted contrast intervals included zero.

## S8. Development interval provenance

The release records development P1 = 0.1159994 versus 0.1305460 (ratio 0.8885713), conditional interval [0.865, 0.911] and ten-arm simultaneous max-T interval [0.860, 0.918]. The supplied audit package's max-T code and underlying draw records were not available in the workspace or remote refs. The reported interval is therefore preserved as a historical release statement, not independently re-estimated in Phase 3. This phase does not alter that outcome or claim to reproduce its interval.

## S9. Census defect disclosure

The user-specified Phase 2 census defect report and its four frame definitions were not found in the current workspace, frozen release tree, or inspected remote refs. No specific zero-impact conclusion can be independently verified without those source frames, defect definition and census outputs. No historical census input was rewritten. This supplement records the gap as unresolved provenance and does not claim to have completed a technical erratum for an unidentified defect. The repository's census records remain preserved at their frozen hashes.

## S10. Reproducibility commands and environment

From the repository root, use Python 3.13.12 with the pinned project environment. The frozen external statistical analysis can be reconstructed with:

```bash
PYTHONPATH=src python3.13 scripts/wur_v2_confirmation_v2/11_external_analysis.py
```

For a non-mutating independent rebuild, create a detached worktree at the release commit and run the command there. It reads the committed measured μ table, final population, frozen model JSONs, and novelty bins, and writes `artifacts/wur_v2_confirmation_v2/result/external_analysis.json` in the detached copy. The figure and table assets can be regenerated with:

```bash
python3.13 publication_phase3/analysis/generate_assets.py
```

The environment recorded for the Phase 2 reconstruction is Python 3.13.12, NumPy 2.5.2, SciPy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, RDKit 2026.03.5 and pymzML 2.6.1. Raw mzML is not included. Full raw-data-to-model reconstruction requires acquisition of third-party MSnLib archives and is outside the scope of this reviewer package; statistical reconstruction from frozen μ outputs is available locally.

## S11. Source manifests, integrity, and rights

Frozen release and result artifacts are identified by Git commit and repository manifests. The release commit is `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`. External result JSON and measured μ CSV are committed under `artifacts/wur_v2_confirmation_v2/result/`; the population and scan allowlist are under `freeze/`. Archive-level hashes are generated for the Phase 3 deliverables after final generation. Third-party mzML data are excluded from the archive. External users must retrieve them from the cited source and verify against the manifest before attempting raw parsing.

## S12. Technical limitations

1. The MSnLib outcome population was used once and is now exposed; no future blind validation is possible on it.
2. Five measured compounds were excluded for model support, although the all-1,794 sensitivity produced the same qualitative result.
3. External uncertainty resamples scaffolds but does not include model-selection or CE-mapping uncertainty.
4. The fixed affine map is computationally specified but not physically calibrated across instruments.
5. Model and comparator differences preclude attribution of the external gain to Morgan fingerprints alone.
6. No demonstrated tail-risk benefit; the candidate AF point estimate is slightly higher.
7. Q1 most-novel subgroup ratio is 1.0083 and has no confidence interval.
8. The development simultaneous interval cannot be independently reconstructed from available records in this phase.
9. The requested census defect, its four frames and the Phase 2 audit package were unavailable; no defect erratum can be fact-checked here.
10. Full-spectrum comparator metrics are not directly commensurate with scalar μ prediction error.
11. The manuscript's author declarations require the owner's confirmation before any external circulation.
