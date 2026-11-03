# Phase 5 Reproducibility Report

**Review date:** 2026-11-03
**Scope:** Independent fresh-extraction inspection and rerun of the Phase 4 external reviewer package. This is a computational audit of delivered artifacts, not a new experiment or human peer review.

## Archives and integrity

The Phase 4 external reviewer archive inspected was `publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip` (SHA-256 `fbb730ae35cb33a2691b5fae158826b76de2e4c9610f739063670b57b867bf32`). `unzip -t publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip` completed without archive errors. I extracted it into a new temporary directory created with `mktemp` (`/tmp/muru-phase5-review.MaBt8G` for this run; that path is ephemeral and machine-specific).

The outer archive embeds `MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip`, SHA-256 `4a68ff73a98933ff9e827831812006d8a2ce3ae1d55674523013a5ba8a1e857a`. Its ZIP integrity check also passed. The embedded archive's own README specifies Python 3.13.12 and NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.0, scikit-learn 1.9.0, and RDKit 2026.03.5.

## Exact reproduction commands and output

Commands run from the repository root, then from fresh extraction:

```bash
unzip -t publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip
unzip -q publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip -d /tmp/muru-phase5-review.MaBt8G
unzip -t /tmp/muru-phase5-review.MaBt8G/MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip
mkdir -p /tmp/muru-phase5-review.MaBt8G/nested
unzip -q /tmp/muru-phase5-review.MaBt8G/MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip -d /tmp/muru-phase5-review.MaBt8G/nested
cd /tmp/muru-phase5-review.MaBt8G/nested/reviewer_package
python3.13 verify_reproduction.py
```

The verifier exited **0** and printed `PASS: checksums, required files, environment, frozen external result`. Reconstructed results:

| Output | Reconstructed |
|---|---:|
| Measured compounds | 1,794 |
| Support-excluded compounds | 5 |
| Scored compounds | 1,789 |
| Scaffold groups | 1,687 |
| Candidate pooled P1 RMSE | 0.12961151072591617 |
| Reference pooled P1 RMSE | 0.13352761116871245 |
| Candidate/reference ratio | 0.9706719800607511 |
| Scaffold-bootstrap 95% interval | [0.9523611879747089, 0.9892672061846276] |
| Frozen decision label | `MODEST EXTERNAL CONFIRMATION` |

The script compares counts and decision exactly and floating metrics with absolute tolerance `1e-12`. It validates the nested archive's SHA-256 manifest and required files, checks the exact declared package versions, executes `scripts/wur_v2_confirmation_v2/11_external_analysis.py`, then compares results to `expected_primary.json`. Thus the strongest reproduced level is **recalculation of the frozen external statistics from included measured-μ values, frozen eligible-population/model records, and frozen model artifacts**. It is a fresh extraction and execution, but not an independent implementation of the full scientific pipeline.

The Phase 4 package's portable figure-generation route was also run from the clean extraction:

```bash
cd /tmp/muru-phase5-review.MaBt8G/MURU_PHASE4_REVIEWER_PACKAGE
python3.13 scripts/generate_phase4_figures.py
```

It exited **0** and reported regeneration of five figures in SVG/PDF/PNG from packaged source tables. The generator script hash is `e53d27c438a4bc21159dcbd4443f4f3572928cb393e2a1b7ea5d0adc22aee0b7`. The source table `supplement/COMPLETE_SUPPLEMENTARY_TABLES/external_compound_errors.csv` has SHA-256 `0fb171f6df260c88f4a15295fa14b0e49bf11f43ecca634f378f37f4de52e029`; it contains 1,789 derived compound-level rows. Figure regeneration verifies that packaged scripts execute on packaged data; it does not independently validate the scientific derivation of those source values.

## What these checks do and do not reproduce

| Reproduction level | Status from this review | Scope |
|---|---|---|
| Frozen-output metric/statistical reconstruction | Reproduced | Reruns the packaged analysis from measured μ and frozen prediction/model/population records. |
| Figure generation from packaged source tables | Reproduced | Recreates five figure exports from packaged tables; not raw-spectrum figure derivation. |
| Prediction regeneration from source structures and saved models | Not independently tested here | The verifier checks model JSON files are present but does not assert that complete inference preprocessing regenerates every frozen prediction. |
| Model retraining and original model-selection search | Not reproduced | Requires full training inputs, selection chronology, and reproducible historical search records. |
| Raw MSnLib mzML processing through endpoint μ | Not reproduced | The raw third-party MSnLib mzML files are not in the reviewer archive. |
| New independent measurement or laboratory replication | Not performed | Requires a new external experiment. |

## Limitations and reproducibility risks

1. The verifier invokes the project's own frozen analysis script and compares its output to a bundled expected-result JSON. This is a reproducibility check of the supplied calculation and inputs, not an independent reimplementation or proof that upstream mzML-to-μ processing was correct.
2. The outer Phase 4 archive has an embedded nested archive and the nested archive has its own checksum manifest. The outer extraction and nested checks passed. A consumer should still verify each archive and the nested file manifest before use.
3. The Phase 4 archive does not include raw MSnLib spectra. It includes detailed derived records (including compound keys/structures, μ values, predictions and errors) and model artifacts. Their redistribution status must be determined from source records and rights holders; archive integrity is not a license.
4. Python package versions are strict. Install from trusted package sources in an isolated environment; the README does not provide a lockfile with wheel hashes. This run found the specified environment available and passed the verifier, but portability to other platforms is not established.
5. The external result is conditional on the frozen two-rung energy input convention and empirical numerical bridge. It is not physical cross-instrument energy calibration.
6. The run did not test deliberate input corruption during this Phase 5 audit. Phase 4's report describes prior fault-injection checks, but those are historical report claims rather than checks repeated here.

## Conclusion

The Phase 4 external reviewer archive is extractable, its embedded statistical reconstruction kit passes integrity and result checks in a fresh extraction, and its five-figure generator runs from packaged tables. The evidence supports reproducibility of the **frozen-output external statistical analysis** and package-local figure generation. It does not support a claim of raw-data-to-model reproduction, retraining, independent experimental replication, or legal clearance for public redistribution of every packaged derived artifact.


## Phase 5 final rerun

On 2026-11-03 I repeated extraction from a new temporary directory and reran the nested verifier:

```bash
unzip -q publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip -d /tmp/muru_phase5_repro.1Vrff8
unzip -q /tmp/muru_phase5_repro.1Vrff8/MURU_PHASE4_REVIEWER_PACKAGE/phase3_frozen_output_reviewer_archive.zip -d /tmp/muru_phase5_repro.1Vrff8/nested
cd /tmp/muru_phase5_repro.1Vrff8/nested/reviewer_package
python3.13 verify_reproduction.py
```

Exit code 0; verifier output was `PASS: checksums, required files, environment, frozen external result`. Values: measured 1,794; unsupported 5; scored 1,789; scaffolds 1,687; candidate P1 0.12961151072591617; reference P1 0.13352761116871245; ratio 0.9706719800607511; interval [0.9523611879747089, 0.9892672061846276]; decision `MODEST EXTERNAL CONFIRMATION`. This verifies frozen-output statistical reconstruction, not raw-spectrum processing, retraining, or independent replication.

The Phase 5 source-table figure generator was also run as `/tmp/muru-phase5-venv/bin/python publication_phase5/scripts/generate_phase5_figures.py`; exit code 0, five SVG/PDF/PNG sets regenerated.
