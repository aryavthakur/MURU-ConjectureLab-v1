# Phase 6 reproducibility results

## Frozen statistical reconstruction

A fresh ZIP was created from the frozen `publication_phase3/reviewer_package` inputs, extracted to a new temporary directory, and executed. The exact command sequence was:

```bash
P6TMP=$(mktemp -d /tmp/muru-p6-repro.XXXXXX)
(cd publication_phase3/reviewer_package && zip -qr "$P6TMP/reviewer.zip" .)
mkdir "$P6TMP/unpacked"
unzip -q "$P6TMP/reviewer.zip" -d "$P6TMP/unpacked"
(cd "$P6TMP/unpacked" && python3.13 verify_reproduction.py)
```

A first attempt with `/tmp/muru-phase5-venv/bin/python` exited with `ModuleNotFoundError: scipy`; that virtualenv also lacked scikit-learn and RDKit. The documented Python 3.13 environment was then used. Exit status: 0. It reported `PASS: checksums, required files, environment, frozen external result`.

Reconstructed output:

| Quantity | Reconstructed value | Frozen expected |
|---|---:|---:|
| Measured | 1,794 | 1,794 |
| Support excluded | 5 | 5 |
| Scored | 1,789 | 1,789 |
| Scaffold groups | 1,687 | 1,687 |
| Candidate P1 RMSE | 0.12961151072591617 | 0.1296115107 |
| Reference P1 RMSE | 0.13352761116871245 | 0.1335276112 |
| Candidate/reference ratio | 0.9706719800607511 | 0.9706719801 |
| Scaffold bootstrap 95% interval | [0.9523611879747089, 0.9892672061846276] | [0.9523611880, 0.9892672062] |
| Decision | MODEST EXTERNAL CONFIRMATION | MODEST EXTERNAL CONFIRMATION |

Floating values agreed within the package's absolute tolerance of 1e-12. The relative RMSE reduction is 2.9328%, below the frozen 5% practical target.

## Integrity fault injection

Two disposable fresh copies were altered. Appending whitespace to `expected_primary.json` produced exit status 1 and `CHECKSUM MISMATCH: expected_primary.json`. Removing `artifacts/wur_v2_confirmation_v2/result/measured_mu.csv` produced exit status 1 and `MISSING: artifacts/wur_v2_confirmation_v2/result/measured_mu.csv`.

The Phase 4 outer archive passed `unzip -t`. The Phase 5 external review archive SHA-256 was independently computed as `0f49275086cbcc5554e8cf585b4420962b36c37630e0a44fe0e16cc7be6918b4`; this historical archive is not presumed rights-cleared for circulation.

## Phase 6 source metadata extraction

The Phase 6 extraction script range-reads the evaluated public Zenodo v5 ZIP members, checks ZIP CRC-32 and each member against the frozen SHA-256 allowlist, then parses the selected mzML spectrum IDs and energy CV terms. One representative selected scan was independently parsed with the same parser and verified as MS2, HCD, 20 eV with precursor m/z matching the frozen allowlist within 1e-5. The completed all-scan validation in `../metadata/EXTRACTION_VALIDATION_REPORT.md` covers all 6,004 selected scan rows across the evaluated source members. The raw/native-method provenance gap remains separate.

## MassIVE RAW identity verification

The official MassIVE dataset listing was saved in the temporary audit workspace and parsed by `metadata/audit_massive_listing.py`. The raw payload itself was streamed from the documented file descriptor and hashed, without saving it to disk. The retained result is `metadata/MASSIVE_RAW_LINKAGE_TESTS.csv`: listed/downloaded byte count 31,994,595 and SHA-1 `ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3`, equal to the mzML sourceFile checksum. The endpoint's TLS chain failed system validation in the execution environment, so the successful one-time check used the script's explicit `--allow-unverified-tls` option. This means the TLS server certificate was not authenticated during that transfer; confidence in file identity rests on the file size and checksum match to the separately SHA-256-validated source mzML metadata. The RAW payload was not retained. A repeat fetch later encountered MassIVE rate limiting (HTTP 429), so it was not represented as repeatable in the final run.

The MassIVE file-list HTML used to derive the extension and filename-candidate counts was retained only in the temporary audit workspace, not in the package. The published CSVs retain aggregates and the exact tested file descriptor; independent regeneration requires fetching the current official listing.

## Reproduction boundary

The verified calculation reconstructs statistics from frozen measured-μ values and model predictions/artifacts. It does not independently reimplement model inference; reprocess all raw spectra; reconstruct native acquisition methods; retrain models; or constitute a new experimental replication. The Phase 6 mzML metadata extraction is a separate source-metadata validation and does not extend the statistical reconstruction to RAW-to-μ processing.


## Phase 6 final metadata checks

Command: `python3.13 publication_phase6/verification/verify_phase6_metadata.py`. Exit status 0. It passed 9 source archives, 1,428 allowlisted members, 6,004 selected scan rows, 161 public `.meth` summaries (Vanquish_H / SeparationMethod, no explicit ID-X/NCE/CE terms), and the nested NIH record (535 mzML names, no method-like member, verified outer-member CRC). Scope and limitations are in `../metadata/METADATA_EXTRACTION_TESTS.md`.

## Phase 6 archive recheck

The final Phase 6 internal and external ZIPs were rebuilt after the last document edits. Both passed `unzip -t`; the external ZIP contains 15 members and the complete ZIP 159. SHA-256 checks passed using `(cd publication_phase6 && shasum -a 256 -c release/FINAL_SHA256SUMS.txt)`. The final checks are recorded in `../qa/FINAL_PHASE6_VALIDATION.md`.
