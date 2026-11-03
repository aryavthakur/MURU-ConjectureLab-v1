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
