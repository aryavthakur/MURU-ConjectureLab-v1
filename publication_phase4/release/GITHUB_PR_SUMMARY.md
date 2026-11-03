# Phase 4 draft pull request summary

Phase 4 is committed on `publication/phase4-final-review-2026-11-02` and is proposed as [draft PR #11](https://github.com/aryavthakur/MURU-ConjectureLab-v1/pull/11), targeting `publication/phase3-complete-2026-11-02`. PR #10 remains the Phase 3 draft against the frozen release. The frozen release and `main` are unchanged; no journal submission was made.

## Scientific corrections

- Corrected comparator scoring: predicted full-spectrum peaks were reduced to the common scalar μ endpoint before pooled P1 scoring.
- Completed the Ridge objective and documented asymmetric candidate/reference scaling, precursor-denominator provenance, model-selection differences, and frozen reference application.
- Narrowed exposure and collision-energy claims; the fixed energy map is computational and not physically calibrated.
- Preserved external results, failed 5% criterion, adverse least-similar quartile, lack of demonstrated tail benefit, unresolved CE Design A, prior exposure, and unreproduced historical max-T interval.
- Reconciled recovered Phase 2 census evidence and bounded zero-impact finding to four hashed frames.

## Deliverables and checks

- Revised 14-page master manuscript, 18-page inline-citation version, and 5-page Supporting Information.
- Five source-driven figures in SVG/PDF/PNG, machine-readable tables, figure/table scripts, literature and claim crosswalks.
- Three simulated adversarial reviews, two substantive revision cycles, Validex 20-control crosswalk, and AI-assistance log.
- Integrity checker: 42/42 pass. Fresh reviewer-package extraction recreates all figures and reproduces frozen external metrics.
- Full archive checksum is recorded in `FINAL_PACKAGE_SHA256.txt`.

## Limitations

Physical energy calibration, original max-T computation artifacts, raw mzML/training reproduction, and human author declarations remain unresolved and are described in the manuscript. The package does not claim raw-data-to-model reproduction or experimental replication.
