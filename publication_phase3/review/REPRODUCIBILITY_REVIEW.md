# Simulated Reviewer C — Reproducibility

**Nature of review:** adversarial AI-assisted internal review; not a human review. Package was checked from a detached release worktree and outputs were compared with the frozen analysis JSON.

## Overall assessment

The external statistical result can be reconstructed from committed measured μ values, model JSON, population and frozen code. This is not a raw mzML-to-model reproduction. The result sources, pinned software environment and output locations are clear, but a reviewer needs a compact extracted reproduction kit rather than access to the full repository. The Phase 2 archive cited in the directive was not available in the workspace. Phase 3 therefore preserves the source release and states exact limits.

## Concerns and dispositions

| Severity | Concern and evidence | Disposition |
|---|---|---|
| Major | Reproduction command can overwrite a result JSON in the checked-out tree. | Addressed in instructions: use a fresh detached worktree; run instructions identify the output path and do not claim raw-data reconstruction. |
| Major | Raw mzML archives and some third-party source data are not included. | Addressed: source DOI, acquisition instruction, no-redistribution statement and boundary between statistical reconstruction and raw-data reproduction are explicit. |
| Major | The Morgan representation was not tracked in the historical release but can be rebuilt. | Addressed: RDKit version, fingerprint definition and exact rebuilding command are recorded. The source release record notes hash parity. |
| Major | Dependency manifest has a documented missing `lxml` pin and full suite has pre-existing failures/errors. | Addressed as known repository-level limitations in the manuscript and reports; not silently presented as a clean full-suite run. |
| Major | Phase 2 audit outputs and previously cited ZIP are absent. | Unresolved provenance limitation documented in Supporting Information S2 and remaining human decisions. |
| Major | Figure/table values should be machine-derived. | Addressed: CSV tables and all five figures are generated from frozen JSON; compound-level residual plot data exported with a dedicated script. |
| Major | A user should not need undocumented local paths. | Addressed in the reviewer ZIP instructions; isolated archive is assembled and tested separately before delivery. |
| Minor | The whole repository has pre-existing unrelated tests needing generated large benchmark artifacts. | Disclosed with the exact historical baseline report; not run as a Phase 3 completeness claim. |
| Minor | Citation and result checksum verification should be recorded. | Addressed in literature matrices, file manifests and archive hash report. |

## Recommendation

The current detached run demonstrates exact reconstruction of the frozen statistical analysis. It does not establish full instrument-data-to-model reproducibility or legal redistribution rights. The reviewer archive must retain that boundary and include only rights-cleared inputs.
