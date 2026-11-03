# Final Reproducibility Report

## Fresh-extraction run

- Archive: `publication_phase3/release/MURU_PHASE3_REVIEWER_PACKAGE.zip`
- Extraction: clean temporary directory `/tmp/muru-phase4-repro.YzvKI3/reviewer_package` (created with `mktemp`; no cached package outputs used).
- Archive check: `unzip -t publication_phase3/release/MURU_PHASE3_REVIEWER_PACKAGE.zip` — exit 0.
- Exact verifier command from extracted package root: `python3.13 verify_reproduction.py` — exit 0; output `PASS: checksums, required files, environment, frozen external result`.
- Runtime: 5.872 seconds; Python 3.13.12 and package versions required by the archive.
- Reported values: measured 1,794; unsupported 5; scored 1,789; groups 1,687; candidate P1 0.12961151072591617; reference P1 0.13352761116871245; ratio 0.9706719800607511; CI [0.9523611879747089, 0.9892672061846276]; verdict `MODEST EXTERNAL CONFIRMATION`.

The command recalculates frozen-output statistics from committed measured-μ values and prediction/model records. It does not recreate predictions from raw structures, retrain, reprocess raw mzML, or perform a new experiment.

## Integrity failure controls

The reviewer archive verifier was separately fault-injected in disposable extractions: appending text to a manifest-covered README triggered `CHECKSUM MISMATCH` and exit 1; removing `expected_primary.json` triggered `MISSING` and exit 1. The archive checksum protects the manifest itself.

## Reproduction levels

| Level | Status | Boundary |
|---|---|---|
| Metric reconstruction from measured μ and frozen outputs | Reproduced | Conditional on committed endpoint values, eligible population, frozen model outputs and energy map. |
| Prediction regeneration from coefficients and structures | Not performed in this clean-extraction check | Does not establish inference pipeline reproduction. |
| Retraining from source spectra | Not reproduced | Source data, complete training records and historical search artifacts are not all in the reviewer package. |
| Raw MSnLib mzML processing | Not reproduced | Third-party raw files are not redistributed; acquisition terms apply. |
| Independent experimental replication | Not performed | Requires new measurements. |

The Phase 2 census verifier was independently rerun using the recovered Phase 2 virtual environment and source worktree; all four recorded frames matched their frozen counts/hashes and the watched inputs remained unchanged. Its sanitized output is `census_neutral_filter_verification_rerun.json`. This result is limited to those four frames.

The Phase 4 reviewer package was then extracted into a second fresh temporary directory. Its ZIP integrity check passed, and its nested copy of the Phase 3 frozen-output archive was extracted and rerun with the same command; the verifier again exited 0 and reproduced the listed metrics. This confirms package completeness for the frozen-output reproduction route, not the raw-data workflow.
