# Metadata extraction and validation tests

## Commands and tested outputs

The Phase 6 run used `/tmp/muru-phase5-venv/bin/python` (Python 3.13). The source parser range-reads public ZIP central directories and members, verifies extracted member size and CRC-32, checks the frozen SHA-256 allowlist, and parses selected mzML spectrum metadata. Population results are in `EXTRACTION_VALIDATION_REPORT.md`; sanitized summaries are in `INSTRUMENT_PARAMETERS.csv` and `SOURCE_TO_EVALUATION_LINEAGE.csv`. The 1,428-member cache and 12 MB run JSON were kept outside the repository.

The final retained-summary check was run with:

```bash
/tmp/muru-phase5-venv/bin/python publication_phase6/verification/verify_phase6_metadata.py
```

Exit status: 0. It verified 9 source families, 1,428 allowlisted members, 6,004 selected scans, all selected energy unit/value fields, 161 `.meth` summaries, and the nested archive listing record.

A representative mzML parser check identified selected scan `controllerType=0 controllerNumber=1 scan=1097` as MS2 HCD at 20 eV and confirmed precursor m/z against the frozen allowlist within 1e-5. The population validator checks all selected scans.

`EXTRACT_PUBLIC_METH_METADATA.py` inspected the 161 public `.meth` members. Each temporary payload passed ZIP CRC validation, was summarized to non-identifying fields, and was then removed. The retained-summary verifier checks 161 rows, CRC status, unique `Vanquish_H` / `SeparationMethod` fields, and zero explicit ID-X, NCE, or collision-energy phrase matches. This is field/text screening, not a semantic decoder of undocumented binary parameters.

The nested NIH `nih_positive_mzml.7z` member was range-downloaded in 16 MiB chunks with eight concurrent requests. The outer member length was 1,040,150,902 bytes and its CRC-32 was `8d41051a`. `bsdtar -tf` listed 536 names (535 `.mzML` names and one directory entry), with no method-like suffix. No spectrum was extracted. Temporary payload and listing were deleted. `audit_nested_nih_archive.py` preserves the range-download and listing workflow. The inner archive's member payload integrity was not tested because only its names were listed.

## Interpretation boundary

These checks establish converted mzML metadata semantics for the frozen selected scans and characterize public method-like archive entries. They do not establish the original Xcalibur MS method, prove the converter did not transform the field, authenticate RAW-to-mzML identity for every run, or calibrate physical energy between ID-X and IQ-X.


## MassIVE linkage test

The official MSV000094528 HTML file listing was parsed by `audit_massive_listing.py`. It reported 18,281 entries and filename candidates for 835/1,428 mzML sourceFile names after documented normalization. The saved HTML was temporary and is not bundled; independent regeneration must fetch the official listing URL in `MASSIVE_DATASET_INVENTORY.csv`.

One MassIVE RAW object was streamed using `verify_massive_representative_raw.py --allow-unverified-tls`; the environment rejected the endpoint certificate chain, so that one transfer explicitly bypassed TLS certificate validation. The response byte count was 31,994,595 and its SHA-1 matched the SHA-1 embedded in the hash-verified MCEBIO mzML sourceFile record. The payload was never saved. A later repeat attempt received HTTP 429. This is a documented one-time checksum identity test, not repeatable network validation or native-method verification.
