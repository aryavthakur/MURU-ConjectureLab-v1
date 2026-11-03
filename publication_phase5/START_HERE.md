# MURU Phase 5 release candidate

This is the authoritative internal Phase 5 manuscript package. No journal submission, external email, or public release has occurred.

## Read in this order
1. `manuscript/MURU_PHASE5_MANUSCRIPT_FINAL.pdf`
2. `supplement/MURU_PHASE5_SUPPORTING_INFORMATION.pdf`
3. `verification/FINAL_STATISTICAL_VERIFICATION.md`
4. `verification/FINAL_ENERGY_INTERFACE_ADJUDICATION.md`
5. `verification/FINAL_REPRODUCIBILITY_REPORT.md`
6. For expert assessment: `external_review/RESEARCH_SUMMARY.pdf` and the three specialist review packets.

## Main result
1,794 measured; 5 support-excluded; 1,789 scored across 1,687 scaffolds. Candidate/reference P1 ratio 0.9706719800607511, 95% paired scaffold-bootstrap interval [0.9523611879747089, 0.9892672061846276], corresponding to a 2.9328% relative RMSE reduction. The 5% practical target failed. Tail-risk improvement was not demonstrated; the least-similar quartile ratio was 1.0083.

## Interpretation boundary
The MSnLib selected settings are called recorded numeric values 20 and 60; physical units remain unresolved. The frozen analysis is reproducible as a numerical adapter comparison, but the data do not establish physical cross-instrument energy calibration. The historical development max-T interval is unreproduced. The replacement MSnLib sample is exposed and cannot serve as a new confirmation cohort.

## Reproduction and sharing
The strongest supported reproduction claim is statistical reconstruction from frozen measured-μ values and frozen predictions/model outputs. Raw mzML reprocessing, full model retraining, and an independent laboratory replication are not provided. The Phase 4 historical reviewer archive is retained for internal technical reference at `publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip`; it contains row-level derivative/model artifacts and must not be redistributed until rights are confirmed.

`release/MURU_PHASE5_EXTERNAL_REVIEW_PACKAGE.zip` contains the rights-bounded external review materials, but is not sent or publicly posted. The rights assessment remains provisional and requires project-owner/license review before sharing. No human scientific review has occurred; see `external_review/ACTUAL_REVIEW_STATUS.md`.
