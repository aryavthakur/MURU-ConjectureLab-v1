# Reproducibility review packet

## Supported claim

The existing Phase 5 archive supports statistical reconstruction from frozen measured-μ outcomes and frozen predictions. It is not raw mzML-to-μ reproduction, model retraining, or independent experimental replication. Third-party raw data and restricted WUR records are not included.

## Phase 6 metadata extraction

Run from the repository root with the documented Phase 5 Python environment:

```bash
python publication_phase6/metadata/RAW_METADATA_EXTRACTION.py \
  --cache-dir /tmp/muru_phase6_cache \
  --output /tmp/phase6_allowlisted_mzml.json \
  --record-json publication_phase6/metadata/zenodo_record_15683784.json \
  --workers 2
python publication_phase6/verification/build_phase6_evidence.py \
  /tmp/phase6_allowlisted_mzml.json publication_phase6
```

This reads selected member ranges from the public converted mzML ZIP, compares member SHA-256 against the frozen allowlist, verifies ZIP CRC, and parses selected spectra and metadata. It does not retain the raw mzML inside the project package. Execution is subject to Zenodo rate limits; retries honor backoff. The validator is required to pass before using its population-wide conclusion.

## Frozen-output statistical reconstruction

The Phase 5 package's standalone README is `publication_phase5/external_review/repro/README.md`. It verifies the package SHA manifest, runs the frozen external analysis verifier, and reports the headline counts, P1, ratio, and scaffold-bootstrap interval. Follow those exact extraction and command steps in a fresh directory. The bundle excludes raw MSnLib spectra and restricted WUR source records.

## Independent integrity checks

For the Phase 6 evidence JSON, check all selected member hashes against the frozen allowlist and re-run the builder. For archive contents, use `unzip -t` and the supplied SHA-256 manifest. Missing/corrupt records must fail the validator. The builder fails if any selected scan ID, MS2 level, energy term/unit/value, selected-ion m/z, or expected count differs. The actual pass/fail record is in `verification/FINAL_REPRODUCIBILITY_RESULTS.md`.

## Acquisition boundaries

Instrument metadata extraction from converted mzML is distinct from source provenance. The exact native-method and RAW-to-mzML links remain unresolved pending the acquisition records described in `../external_requests/NATIVE_METHOD_REQUESTS.md`. No claims of raw-data reconstruction or physical energy calibration should be inferred from the converted-file metadata check.
