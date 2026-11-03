# Reproducibility report

## Frozen statistical reconstruction

The Phase 3 run used detached release commit `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61` and the frozen script `scripts/wur_v2_confirmation_v2/11_external_analysis.py`. It reads the committed measured-μ CSV, frozen population, novelty bins and model JSONs. It reproduced the external primary counts, errors, scaffold-bootstrap interval, novelty ratios and verdict exactly. This is statistical reconstruction from frozen endpoint values, not raw mzML parsing or model retraining.

## Standalone reviewer archive

`release/MURU_PHASE3_REVIEWER_PACKAGE.zip` was extracted into a new temporary directory, then its included `verify_reproduction.py` command passed. The extracted kit reported: 1,794 measured; 5 unsupported; 1,789 scored; 1,687 scaffold groups; P1 0.12961151072591617 versus 0.13352761116871245; ratio 0.9706719800607511; 95% interval [0.9523611879747089, 0.9892672061846276]; verdict `MODEST EXTERNAL CONFIRMATION`.

Integrity negative checks were also run on disposable copies: a modified input, a missing required measured-μ file, and a corrupted checksum entry each failed with a nonzero exit. A separate `python -S` invocation without site packages failed at dependency import as expected. The verified package environment expects Python 3.13.12, NumPy 2.5.2, SciPy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0 and RDKit 2026.03.5.

## Boundaries

- Third-party MSnLib raw mzML files are omitted; no raw-data-to-model reproduction is claimed.
- The historical ten-arm development max-T interval was not independently reconstructed.
- The full repository regression suite is not claimed clean; the frozen Phase 1 record reports existing failures/errors at the comparison base.
- Figures and CSV tables are regenerated from the frozen result JSON and exported prediction residuals; figure generation does not fit models or decode spectra.
- The exact extraction command and expected values are in the reviewer archive README.
