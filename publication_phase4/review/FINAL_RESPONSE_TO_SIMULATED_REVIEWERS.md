# Final response to simulated reviewers

These are internal adversarial simulations, not human peer-review reports or expert approvals.

## Reviewer A — chemistry and mass spectrometry

**Concern:** μ denominator differs between WUR and MSnLib and the 10-ppm tolerance does not filter μ; comparator energy conventions differ by model; claims could imply physical energy transfer or independence.

**Response:** Methods §2.3 now gives the source-specific denominators and removes the tolerance from the target calculation. Methods/Results specify FIORA native NCE and ICEBERG/GLACIER `ev_primary`, with raw-NCE diagnostics for the latter two. The paper narrows interpretation to fixed numerical endpoint comparison under the frozen map. The separately sampled replacement/exposure control is stated without implying zero analog similarity or no unrecorded exposure. No physical calibration is claimed.

## Reviewer B — statistics and machine learning

**Concern:** practical rule and adverse-tail override should be reconstructable; subgroup/tail evidence must remain descriptive; development max-T provenance and reference tuning should not be overstated.

**Response:** Methods §2.7 states both decision boundaries (P1 ratio ≥1 or upper 95% AF difference >+0.03), and reports the 5% criterion separately. The external interval is conditional on frozen models and observed scaffold groups. Novelty strata lack intervals and remain descriptive. The max-T point estimate/interval is labeled historical and unreproduced because core calculation artifacts are unavailable. Candidate/reference differences are explicitly co-interventions, and the external reference is identified as development-selected and not refitted on MSnLib.

## Reviewer C — reproducibility and research integrity

**Concern:** fresh-extraction evidence, corruption tests, figure paths, and exact reproduction boundary should be auditable.

**Response:** The preserved Phase 3 reviewer archive passed fresh extraction and `python3.13 verify_reproduction.py`; counts, P1 values, ratio, CI, and verdict match. Tampering and missing-file fault injections fail as expected. Figure links point to Phase4-local figure directories. Reports distinguish metric reconstruction from prediction generation, retraining, raw mzML reprocessing, and new experiments. Raw files remain excluded under third-party rights constraints.

All three simulated reviewers' original reports are preserved unchanged in this directory. The Phase 4 corrections are separately recorded in this response and revision log.
