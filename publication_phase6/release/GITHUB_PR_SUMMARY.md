# Phase 6 pull request summary

## Scope

Phase 6 adds a source-specific investigation of the unresolved MSnLib collision-energy interface. It identifies all nine frozen archive families, verifies 1,428 allowlisted converted mzML members and 6,004 selected scans, inventories public MassIVE metadata, and documents one exact RAW-to-mzML file identity from a full-file SHA-1 check. It adds source and scan lineage, metadata extraction code, external scientific-review packets, rights-scoped archives, and an evidence-driven manuscript/SI update.

## Frozen outcomes

No model, prediction, measured fragmentation extent, exclusion, metric, bootstrap, comparator, or frozen decision was changed. The result remains 1,789 scored compounds, candidate/reference P1 RMSE 0.1296115107/0.1335276112, ratio 0.9706719801, 95% scaffold-bootstrap interval [0.9523611880, 0.9892672062], and 2.9328% relative reduction. The 5% practical target was not met; tail-risk improvement was not demonstrated; the least-similar structural quartile remains adverse.

## Verification

- Fresh extraction of the Phase 3 frozen-output reviewer package: PASS with Python 3.13; reconstructed counts, RMSEs, ratio, confidence interval, and decision match.
- Phase 6 metadata verification: PASS (nine archive families, 1,428 allowlisted files, 6,004 selected scan rows, 161 `.meth` summaries, nested NIH archive audit).
- Manuscript integrity: PASS (224-word abstract, 34 references/citations, required sections, five figure triplets).
- Internal and external ZIP integrity plus checksums: PASS; no raw/mzML/method/7z payloads included.

## Remaining limits

Converted mzML scan terms explicitly carry 20/60 eV, but run-linked native Xcalibur MS methods and conversion provenance were not recovered across the corpus. One RAW identity is exact; it is not source-wide linkage. Physical cross-instrument energy equivalence remains unverified. The external review package is prepared but not cleared to send pending owner approval of recipient, scope, and project-authored materials. No human review occurred. The historical development max-T interval remains unreproduced.

## PR relationships

This draft targets `publication/phase5-release-candidate` and is stacked on Phase 5. Keep PRs #10, #11, and #12 open and preserve their history. Review and merge only through the existing chain after human approval. Do not merge this draft automatically.
