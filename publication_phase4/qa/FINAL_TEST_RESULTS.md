# Final test results

Final machine-readable run from repository root:

```text
python3.13 publication_phase4/qa/run_integrity_checks.py
SUMMARY: 42/42 passed
```

Fresh extraction of the preserved reviewer archive passed `unzip -t` and `python3.13 verify_reproduction.py` (exit code 0; runtime 5.872 seconds). It confirmed the primary counts, P1 values, ratio, bootstrap interval and frozen verdict. Altered README and removed expected-result file controls both failed verification with the expected checksum/missing-file errors (exit 1). Census verifier rerun passed all four recovered frames with watched inputs unchanged. Document page counts and render checks are in `RENDER_VALIDATION.md`.

The successful checks reproduce committed summary-level statistics, not raw mzML processing, model training, or external experimental replication.

The final Phase 4 reviewer ZIP passed `ZipFile.testzip()` and a fresh extraction test; its packaged table-driven figure generator recreated all five figures and its nested frozen-output archive reproduced the primary result with exit 0. The complete Phase 4 package passed ZIP integrity. All final file-manifest and SHA256 entries verified at release build time.
