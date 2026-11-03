# Document reconciliation report

## Page-count discrepancy

Phase 4 `START_HERE.md` and `FINAL_PROJECT_REPORT.md` say the master manuscript is 13 pages. The current Phase 4 master PDF has 14 pages (`pdfinfo`); the standard-citation PDF has 14, the online-citation PDF 18, and the Supporting Information PDF 5. Phase 4 `qa/RENDER_VALIDATION.md` and `release/GITHUB_PR_SUMMARY.md` also state 14, so the 13-page values are stale reporting errors. Phase 5 records the measured page counts and leaves the Phase 4 documents unchanged as historical artifacts.

## Energy terminology conflict

Phase 4 describes selected MSnLib records as HCD NCE 20 and 60. The frozen MURU protocol uses that label and A0 assumes ID-X NCE equals IQ-X NCE. The peer-reviewed MSnLib methods report ID-X MS2 settings of 20 eV and 60 eV. The nine evaluated source archives lack instrument-method files resolving the difference. Phase 5 uses “recorded numeric settings 20 and 60; physical units unresolved,” gives both source descriptions, and discloses the failed A0/A1/A2 absolute-agreement anchor gate. This changes interpretation and labeling, not the frozen predictions, metrics, or rung membership.

## Development selection history

The Phase 4 manuscript describes a multi-family search and simplicity selection but omits that amendment A-3 restated c4 after development results and five adversarial reviews were visible, before external outcomes were accessed. The literal c4 failed for EXP08B; the candidate was admitted under the revised interpretation. Phase 5 discloses this amendment in Methods, Results, Discussion, and the supplement. Frozen model identity and outcomes are unchanged.

## Max-T provenance

Phase 3 said Phase 2 evidence was unavailable. Phase 4 recovered Phase 2 reports from an old local worktree, but not the original max-T script, exact seed, serialized resamples, or candidate-selection ledger. Phase 4’s current statement that the Phase 2 report was recovered is correct; the max-T calculation itself remains unreproduced. Phase 5 preserves that distinction and avoids implying that the original procedure never existed.

## Census defect

Phase 2’s full local verifier supports zero membership difference across four reconstructed frames and hashes. Phase 4’s sanitized JSON loses the frame identities and full hash data. Phase 5 records the full findings and their limited scope; no blanket claim that every historical downstream use was unaffected is made.

## External sample and metrics

The denominator remains 1,794 measured, 5 support exclusions, 1,789 scored, 1,687 scaffold groups, 3,578 compound-rung cells. The primary ratio and confidence interval match the frozen result. The external population was evaluated once and is now exposed. No metric or frozen study decision changed in Phase 5.

## Reproducibility and rights

The existing archive reproduces metrics from frozen measured-μ values and predictions and regenerates figures. It does not reproduce raw mzML parsing or retraining. The Phase 4 archive contains compound-associated derived outcomes. The precise rights basis for broad redistribution of these derivatives and WUR-derived artifacts is not conclusively established; Phase 5 external package is therefore restricted to publication/review materials and excludes the frozen per-compound reproduction payload until a rights decision is recorded.

## Reference count

The current manuscript contains 27 numbered references. This was checked by parsing the References section, not copied from the Phase 4 report. Phase 4’s source audit lists 27 records; manufacturer manual reference 22 is explicitly partial because exact version metadata is incomplete.
