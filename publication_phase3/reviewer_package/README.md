# MURU-WUR-v2 statistical reconstruction package

This archive reconstructs the frozen MSnLib external statistics from the committed measured-μ table, frozen molecular models, population and novelty records at release commit `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`. It does **not** reproduce raw mzML parsing, spectra acquisition, model training, or the original development search. Third-party MSnLib raw data are not included.

## Requirements

Python 3.13.12 with NumPy 2.5.2, SciPy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, and RDKit 2026.03.5. These are the versions recorded by the project for the reconstruction environment. Install them in an isolated environment using trusted package sources.

## Verify and run

From this directory:

```bash
python3.13 verify_reproduction.py
```

The verifier checks all SHA-256 entries and required source files, then executes the frozen analysis in this extracted package and compares the primary counts, RMSEs, ratio, interval and decision to `expected_primary.json`. It exits nonzero on integrity or result mismatch. The official analysis writes its detailed output to `artifacts/wur_v2_confirmation_v2/result/external_analysis.json`.

The package does not contact GitHub, access local machine paths, require a private credential, or decode the original spectra. A fresh extraction and runtime still require the listed Python dependencies.

## Integrity

`SHA256SUMS.txt` covers every package file except itself. Verify independently with `sha256sum -c SHA256SUMS.txt` on Linux or `shasum -a 256 -c SHA256SUMS.txt` on macOS. Do not modify an input and then treat the result as the frozen reconstruction.

## Data and rights

The package contains project code, frozen aggregate measurements, derived structures and model artifacts. It omits the third-party raw MSnLib mzML archive. To reproduce raw-data processing, acquire the source archive from the cited source in the manuscript/supplement, review its current terms, verify the published source checksum, and follow the repository protocol. This package supports statistical reconstruction from frozen μ values only.
