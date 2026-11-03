# MURU Phase 4 reviewer package

This archive contains the complete internal manuscript and supporting information, final figures in SVG/PDF/PNG with generation code, machine-readable source tables, scientific audit reports, simulated-review reports, verified references, integrity checks, and the Phase 3 frozen-output reviewer reproduction archive.

## Start

1. Read `manuscript/MURU_PHASE4_MANUSCRIPT_FINAL.pdf` and `supplement/MURU_PHASE4_SUPPORTING_INFORMATION.pdf`.
2. Verify the included `phase3_frozen_output_reviewer_archive.zip` with `unzip -t`.
3. Extract that archive and from its `reviewer_package/` directory run `python3.13 verify_reproduction.py`. Follow its README for the pinned environment and source data terms.
4. The strongest reproduction is recalculation of frozen external statistics from committed measured-μ and prediction/model outputs. Raw third-party MSnLib mzML reprocessing, model training, and a new independent experiment are not included.
5. Do not redistribute raw MSnLib files. Follow their source acquisition and license requirements.

To regenerate all five included figures from the packaged frozen CSV inputs, install `scripts/requirements_figures.txt` and run `python3.13 scripts/generate_phase4_figures.py` from the extracted Phase 4 package root. The per-figure `generate.py` wrappers use the same package-local tables. `scripts/build_source_tables.py` is supplied for full-checkout provenance and consumes the frozen repository JSON/Phase 3 tables; it requires the complete project checkout.

The 0.9706719801 candidate/reference ratio has a 95% scaffold-bootstrap interval [0.9523611880, 0.9892672062]. The 5% practical-improvement threshold failed; tail-risk improvement was not demonstrated. The paper does not claim full-spectrum accuracy or physical cross-instrument energy calibration.
