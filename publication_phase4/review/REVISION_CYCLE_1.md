# Revision cycle 1 — source audit and first full revision

**Date:** 2026-11-02.

The initial assessment identified a material comparator endpoint error, omitted ridge intercept, asymmetric feature scaling, denominator provenance differences, incomplete energy nomenclature, stale Phase 2 availability statements, and under-documented statistical/reproduction boundaries. Phase 4 corrected these against the frozen source code, Phase 2 records, metric JSON, and original data lineage.

Implemented changes: (1) corrected comparator scoring to common derived μ/P1 while explicitly excluding full-spectrum fidelity claims; (2) added the unpenalized Ridge intercept to the objective; (3) documented distinct candidate/reference scaling and model-selection differences; (4) identified MassBank-declared versus structure-derived precursor denominators; (5) corrected base μ preprocessing and source energy labels; (6) stated scaffold bootstrap unit/count/seed and conditional uncertainty; (7) reported the +0.03 AF override and failed 5% criterion; (8) retained adverse Q1 and non-improved tail result; (9) corrected census evidence using recovered Phase 2 verifier; (10) added peer-reviewed ICEBERG source and claim mapping; (11) regenerated five figures and expanded the supplement.

No frozen outcomes were changed. Main unresolved issues were carried into the review stage: historical max-T implementation provenance, physical energy calibration, raw-data processing, and human confirmation of declarations/rights.
