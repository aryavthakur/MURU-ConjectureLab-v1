# Reproducibility review packet

## Purpose and scope
This packet supports review of statistical reconstruction from permitted frozen outputs. It does not claim raw mzML reprocessing, model retraining, or independent experimental replication.

## Instructions
# External reviewer reproduction instructions

This folder documents how to use the Phase 4 external reviewer package without access to the project author's workstation. It does not contain or redistribute the underlying Phase 4/Phase 3 archives; those are in `publication_phase4/release/` in the project repository.

## 1. Verify and extract the Phase 4 archive

From the repository root:

```bash
shasum -a 256 publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip
unzip -t publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip
mkdir -p /tmp/muru-reviewer-phase4
unzip -q publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip -d /tmp/muru-reviewer-phase4
```

Expected outer archive SHA-256 at the time of the Phase 5 audit:
`fbb730ae35cb33a2691b5fae158826b76de2e4c9610f739063670b57b867bf32`.

## 2. Verify/extract the frozen statistical kit

```bash
cd /tmp/muru-reviewer-phase4/MURU_PHASE4_REVIEWER_PACKAGE
unzip -t phase3_frozen_output_reviewer_archive.zip
mkdir -p /tmp/muru-reviewer-phase4/nested
unzip -q phase3_frozen_output_reviewer_archive.zip -d /tmp/muru-reviewer-phase4/nested
cd /tmp/muru-reviewer-phase4/nested/reviewer_package
python3.13 verify_reproduction.py
```

Use Python 3.13.12 and the versions declared by the included README: NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.0, scikit-learn 1.9.0 and RDKit 2026.03.5. Use an isolated environment and trusted package sources. The verifier checks the nested SHA-256 manifest and required inputs, runs the frozen external analysis script and compares results to `expected_primary.json`.

Expected headline output: 1,794 measured; 5 unsupported; 1,789 scored; 1,687 scaffold groups; candidate P1 0.12961151072591617; reference P1 0.13352761116871245; ratio 0.9706719800607511; 95% scaffold interval [0.9523611879747089, 0.9892672061846276]; decision `MODEST EXTERNAL CONFIRMATION`.

## 3. Regenerate figures from packaged tables

In the extracted Phase 4 package root:

```bash
python3.13 -m pip install -r scripts/requirements_figures.txt
python3.13 scripts/generate_phase4_figures.py
```

The script regenerates five figures from included source tables. For source-table construction from repository frozen outputs, use `scripts/build_source_tables.py` from a full repository checkout; that is a separate provenance route and is not required for the standalone figure run.

## What this does not do

The package supports frozen-output statistical reconstruction and rendering of packaged tables. It does not include third-party raw MSnLib mzML, reproduce spectrum decoding or measured μ from raw spectra, retrain the model, reproduce the complete original development search, or establish physical calibration of collision-energy conventions. It is not an independent experimental replication. Package integrity does not establish redistribution rights. See `SOURCE_NOTES.md` and `../../verification/FINAL_DATA_LINEAGE.md`.


## Source notes
# Source and artifact notes for external reviewers

## Phase 4 outer archive

- Repository path: `publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip`
- SHA-256 observed 2026-11-03: `fbb730ae35cb33a2691b5fae158826b76de2e4c9610f739063670b57b867bf32`
- Contains final Phase 4 manuscript/supporting documents, figures and generation scripts, machine-readable tables, audits/reviews, references and an embedded Phase 3 frozen-output archive.
- ZIP integrity test passed with `unzip -t` in a fresh extraction.
- It does not include the raw third-party MSnLib mzML archive. No clear top-level license/rights file was observed in the outer archive inventory; consult the project records and provisional rights report before onward redistribution.

## Embedded frozen-output archive

- Archive path within the outer ZIP: `MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip`
- SHA-256 observed: `4a68ff73a98933ff9e827831812006d8a2ce3ae1d55674523013a5ba8a1e857a`
- The nested README attributes the frozen records to release commit `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`.
- `verify_reproduction.py` validates listed SHA-256 records, required source files, fixed software versions and the primary output from the included external analysis script.
- The frozen source table `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv` SHA-256 in the inspected extraction: `987e25458d6694c4eecf80905b44881d2c8fec23f572f0dc4770f91fe087e806`.
- The analysis result JSON SHA-256: `87102d01c6ae70510211313c0f0ba41852d8d1c848664d04ebe033fbeee1ccd0`.
- The fixed expected result is in `expected_primary.json`.

The reproduced analysis reruns `scripts/wur_v2_confirmation_v2/11_external_analysis.py` over committed μ values and model/population records. This is not reproduction of raw mzML processing, prediction training, or a separate implementation. The current Phase 4 archive's own source-table build helper expects a complete repository checkout; the portable figure generator reads the included CSV tables.

## External source records relevant to rights and acquisition

These are official records reviewed on 2026-11-03:

- MSnLib spectral libraries v8: [Zenodo 21105617](https://zenodo.org/records/21105617), DOI `10.5281/zenodo.21105617`; page identifies Open access, v8, published 2026-07-01, and states MSnLib data is split across records. The record describes generated MGF/JSON spectral libraries, not the converted mzML collection.
- Converted MSnLib mzML positive/negative: [Zenodo 15683784](https://zenodo.org/records/15683784), DOI `10.5281/zenodo.15683784`; page identifies Open access, v5, published 2025-06-17, and describes converted mzML from Flow Injection Orbitrap ID-X measurements.
- WUR Mass Spectral Library: [Zenodo 20552933](https://zenodo.org/records/20552933); page marks the dataset **Restricted** and directs readers to request download access. It describes UHPLC-Orbitrap IQ-X measurements and HCD/UVPD methods.

The local Phase 2 clearance review cautions that open source terms do not automatically settle rights for derived record-level tables or model artifacts, and that WUR's restricted access must be respected. The package's error table contains 1,789 structure-associated derived outcome rows. Refer to `publication_phase5/release/FINAL_DATA_RIGHTS_REPORT.md`; it is explicitly a draft requiring human review, not legal advice or a clearance certificate.


## Phase 5 fresh-extraction findings
# Phase 5 Reproducibility Report

**Review date:** 2026-11-03
**Scope:** Independent fresh-extraction inspection and rerun of the Phase 4 external reviewer package. This is a computational audit of delivered artifacts, not a new experiment or human peer review.

## Archives and integrity

The Phase 4 external reviewer archive inspected was `publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip` (SHA-256 `fbb730ae35cb33a2691b5fae158826b76de2e4c9610f739063670b57b867bf32`). `unzip -t publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip` completed without archive errors. I extracted it into a new temporary directory created with `mktemp` (`/tmp/muru-phase5-review.MaBt8G` for this run; that path is ephemeral and machine-specific).

The outer archive embeds `MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip`, SHA-256 `4a68ff73a98933ff9e827831812006d8a2ce3ae1d55674523013a5ba8a1e857a`. Its ZIP integrity check also passed. The embedded archive's own README specifies Python 3.13.12 and NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.0, scikit-learn 1.9.0, and RDKit 2026.03.5.

## Exact reproduction commands and output

Commands run from the repository root, then from fresh extraction:

```bash
unzip -t publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip
unzip -q publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip -d /tmp/muru-phase5-review.MaBt8G
unzip -t /tmp/muru-phase5-review.MaBt8G/MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip
mkdir -p /tmp/muru-phase5-review.MaBt8G/nested
unzip -q /tmp/muru-phase5-review.MaBt8G/MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip -d /tmp/muru-phase5-review.MaBt8G/nested
cd /tmp/muru-phase5-review.MaBt8G/nested/reviewer_package
python3.13 verify_reproduction.py
```

The verifier exited **0** and printed `PASS: checksums, required files, environment, frozen external result`. Reconstructed results:

| Output | Reconstructed |
|---|---:|
| Measured compounds | 1,794 |
| Support-excluded compounds | 5 |
| Scored compounds | 1,789 |
| Scaffold groups | 1,687 |
| Candidate pooled P1 RMSE | 0.12961151072591617 |
| Reference pooled P1 RMSE | 0.13352761116871245 |
| Candidate/reference ratio | 0.9706719800607511 |
| Scaffold-bootstrap 95% interval | [0.9523611879747089, 0.9892672061846276] |
| Frozen decision label | `MODEST EXTERNAL CONFIRMATION` |

The script compares counts and decision exactly and floating metrics with absolute tolerance `1e-12`. It validates the nested archive's SHA-256 manifest and required files, checks the exact declared package versions, executes `scripts/wur_v2_confirmation_v2/11_external_analysis.py`, then compares results to `expected_primary.json`. Thus the strongest reproduced level is **recalculation of the frozen external statistics from included measured-μ values, frozen eligible-population/model records, and frozen model artifacts**. It is a fresh extraction and execution, but not an independent implementation of the full scientific pipeline.

The Phase 4 package's portable figure-generation route was also run from the clean extraction:

```bash
cd /tmp/muru-phase5-review.MaBt8G/MURU_PHASE4_REVIEWER_PACKAGE
python3.13 scripts/generate_phase4_figures.py
```

It exited **0** and reported regeneration of five figures in SVG/PDF/PNG from packaged source tables. The generator script hash is `e53d27c438a4bc21159dcbd4443f4f3572928cb393e2a1b7ea5d0adc22aee0b7`. The source table `supplement/COMPLETE_SUPPLEMENTARY_TABLES/external_compound_errors.csv` has SHA-256 `0fb171f6df260c88f4a15295fa14b0e49bf11f43ecca634f378f37f4de52e029`; it contains 1,789 derived compound-level rows. Figure regeneration verifies that packaged scripts execute on packaged data; it does not independently validate the scientific derivation of those source values.

## What these checks do and do not reproduce

| Reproduction level | Status from this review | Scope |
|---|---|---|
| Frozen-output metric/statistical reconstruction | Reproduced | Reruns the packaged analysis from measured μ and frozen prediction/model/population records. |
| Figure generation from packaged source tables | Reproduced | Recreates five figure exports from packaged tables; not raw-spectrum figure derivation. |
| Prediction regeneration from source structures and saved models | Not independently tested here | The verifier checks model JSON files are present but does not assert that complete inference preprocessing regenerates every frozen prediction. |
| Model retraining and original model-selection search | Not reproduced | Requires full training inputs, selection chronology, and reproducible historical search records. |
| Raw MSnLib mzML processing through endpoint μ | Not reproduced | The raw third-party MSnLib mzML files are not in the reviewer archive. |
| New independent measurement or laboratory replication | Not performed | Requires a new external experiment. |

## Limitations and reproducibility risks

1. The verifier invokes the project's own frozen analysis script and compares its output to a bundled expected-result JSON. This is a reproducibility check of the supplied calculation and inputs, not an independent reimplementation or proof that upstream mzML-to-μ processing was correct.
2. The outer Phase 4 archive has an embedded nested archive and the nested archive has its own checksum manifest. The outer extraction and nested checks passed. A consumer should still verify each archive and the nested file manifest before use.
3. The Phase 4 archive does not include raw MSnLib spectra. It includes detailed derived records (including compound keys/structures, μ values, predictions and errors) and model artifacts. Their redistribution status must be determined from source records and rights holders; archive integrity is not a license.
4. Python package versions are strict. Install from trusted package sources in an isolated environment; the README does not provide a lockfile with wheel hashes. This run found the specified environment available and passed the verifier, but portability to other platforms is not established.
5. The external result is conditional on the frozen two-rung energy input convention and empirical numerical bridge. It is not physical cross-instrument energy calibration.
6. The run did not test deliberate input corruption during this Phase 5 audit. Phase 4's report describes prior fault-injection checks, but those are historical report claims rather than checks repeated here.

## Conclusion

The Phase 4 external reviewer archive is extractable, its embedded statistical reconstruction kit passes integrity and result checks in a fresh extraction, and its five-figure generator runs from packaged tables. The evidence supports reproducibility of the **frozen-output external statistical analysis** and package-local figure generation. It does not support a claim of raw-data-to-model reproduction, retraining, independent experimental replication, or legal clearance for public redistribution of every packaged derived artifact.
