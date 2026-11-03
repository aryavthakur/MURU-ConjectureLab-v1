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
