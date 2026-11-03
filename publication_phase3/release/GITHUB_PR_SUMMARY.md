# Draft pull request summary

## Summary

Add the MURU Phase 3 internal manuscript package: complete scientific paper, supporting information, five figures, verified citations and claim matrix, statistical reconstruction, simulated adversarial reviews, and publication-readiness records.

## Scientific outcomes preserved

- MSnLib result remains 1,794 measured, 5 support excluded, 1,789 scored, 1,687 scaffold groups.
- Candidate P1 0.1296115107; Tier A reference P1 0.1335276112; ratio 0.9706719801; scaffold bootstrap 95% interval [0.9523611880, 0.9892672062].
- Frozen result remains MODEST EXTERNAL CONFIRMATION; practical 5% threshold not met; no tail-risk improvement demonstrated.
- Q1 least-similar structural quartile ratio is 1.0082968.
- Energy-interface Design A remains INTERFACE_UNRESOLVED; raw-NCE comparator diagnostic reversals remain visible.
- No frozen model or historical outcome was modified.

## Reproducibility

Reran the release's frozen external analysis script in a detached worktree and compared result values with the committed JSON. Figure/table data are derived programmatically from verified JSON and compound-level residual export. The reviewer ZIP excludes raw MSnLib mzML and states the statistical reconstruction boundary. It passed from a fresh extraction; modified, missing, and corrupted-manifest inputs failed integrity checks as expected.

## Known limitations

Phase 2 audit materials and the named four-frame census defect evidence were absent from the available workspace/remote refs. The max-T development interval is retained as historical but not claimed independently reproduced. No journal submission or human review has occurred.

## Files

All deliverables reside in `publication_phase3/`; the complete package ZIP is at repository root, the reviewer ZIP and SHA256 manifests are under `publication_phase3/release/`. The final standard-citation PDF is 13 pages and the abstract is 246 words. Citation audit matched all 26 in-text sources to the bibliography. This PR is an internal working branch and does not modify the frozen release branch.
