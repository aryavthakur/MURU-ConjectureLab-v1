# Phase 5 Verification — Development max-T Interval Provenance

**Scope:** Audit only. No new model evaluation, bootstrap, or performance experiment was run for this report.

## Finding

The WUR-v2 release and historical statistical review report a ten-arm simultaneous max-T interval of **[0.860, 0.918]** for the selected development candidate's pooled out-of-fold RMSE ratio. The number is a historical reported result; the calculation has not been independently reproduced from its original inputs and implementation.

The historical review also reports a **4,000-replicate scaffold bootstrap**, max-T on standardized log ratios, critical value **2.655**, marginal interval [0.866, 0.909] from that bootstrap, a separate module interval [0.865, 0.911], and an estimated selection optimism of about 0.0064. These are claims in the review record, not Phase 5 recomputations. The conditional interval [0.8650671579, 0.9105586626] is separately reproduced in the frozen repository's grouped-CV review from cached predictions; it is not the ten-arm max-T interval and must not be substituted for it.

## Evidence and integrity

| Artifact | Location | SHA-256 | What it establishes |
|---|---|---|---|
| Historical statistical review | `docs/wur_v2_reviews/review_statistics.md` | `8899bd3b1ece69e10d85d91a244bb8a7e753e8562590627e029df26274358671` | Reports historical interval, resampling description, selection and caveats |
| Phase 2 provenance report | Recovered local audit worktree, `publication_phase2/DEVELOPMENT_CI_PROVENANCE.md` | `ff8ae5d3bc00628196dc16a198b6886dc03dbbaa5c61bc2e9713c6006276e558` | States original script, seed, serialized resamples, and selection ledger were not recovered |
| Phase 3 development CI report | `publication_phase3/verification/DEVELOPMENT_CI_FINAL.md` | `7b451d680299bf46436f4cf2d410ed5600a32c723cc66edacc929fba7e6871e8` | Phase 3’s earlier statement that Phase 2 records were unavailable; now superseded by recovery |
| Phase 4 development CI report | `publication_phase4/verification/FINAL_DEVELOPMENT_CI_REVIEW.md` | `c901027ab97da4d2cb186b8200f5486f5ea52ae920405790928661e8c3257275` | Correctly distinguishes recovered provenance report from missing calculation artifacts |

The recovered `publication-astra-audit` worktree is checked out at release base `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`. The user-recorded Phase 2 audit commit `459a78a8ef0ac7a3e92d15c25be38cc8d86403b6` is not present in that worktree’s Git object database (`git cat-file -t` fails). The Phase 2 directory and reports are local untracked files there. This confirms recoverability of the report text in this environment, not a committed or independently published audit revision.

A repository search finds the historical numerical review and the grouped-CV reproduction discussion, but no recoverable original max-T code, exact seed, saved replicate statistics, serialized resample weights, or selection ledger. The Phase 2 provenance report records the same recovery gap. The evidence supports “the calculation artifacts were not recovered in the inspected sources,” not “the calculation never existed.”

## Manuscript discrepancy requiring correction

Phase 4 Results §3.2 correctly says the Phase 2 report and reviewer package were recovered, while the Discussion paragraph beginning **“The development simultaneous max-T interval [0.860, 0.918] remains a historical claim…”** still says the calculation source was unavailable “because the specified Phase 2 audit directory and commit were absent.” That reason is stale. The report was recovered; the underlying max-T calculation inputs remain missing. The manuscript should state this distinction consistently.

Phase 4 `FINAL_DEVELOPMENT_CI_REVIEW.md` is directionally accurate, but the manuscript should not state that the recovered report “confirms” the original implementation artifacts were never present. It documents a failed recovery, not proof of nonexistence.

## Permitted quantitative use

- The interval [0.860, 0.918] may be identified as a historical value reported in the release/review record.
- It must not be presented as Phase 5-reproduced, independently verified, or used as a current inferential interval.
- The development point estimates may be reported as frozen selection-history context, with selection caveats.
- The external MSnLib scaffold-bootstrap interval is a distinct calculation and does not repair the max-T provenance gap.
- No replacement max-T interval should be invented from a new bootstrap or mislabeled as the historical result.

## Evidence boundary

To reproduce the historical interval, the project would need the exact selected-arm input snapshot, the original resampling/random seed and replicate-level data or generation code, the max-T statistic and standardization procedure, the arm-selection ledger and rule replay, and a run environment sufficient to regenerate the reported critical value and endpoints. None of these was established as a complete reproducible set in the inspected records.
