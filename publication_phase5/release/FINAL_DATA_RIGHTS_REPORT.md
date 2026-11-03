# Draft Data Rights and Redistribution Assessment

**Status:** Provisional technical inventory for human owner/legal review; not legal advice, not a rights-holder determination, and not a public-distribution authorization.
**Review date:** 2026-11-03.
**Scope:** Phase 4 reviewer archive and supporting local Phase 2 rights records. The external source pages were checked for source identity/access status. This report does not replace the terms attached to specific downloaded files or advice from the relevant rights holder.

## Executive assessment

The Phase 4 reviewer archive is technically reproducible for frozen-output statistical calculations, but **archive integrity is not legal clearance**. The archive does not contain raw MSnLib mzML. It does contain record-level derived MSnLib results associated with compound keys/structures: 1,789 rows with measured endpoints, predictions and errors. The project’s earlier rights assessment considered MSnLib v8 source records open under CC BY 4.0, subject to version-specific attribution, transformation documentation and hashes. Before broad public distribution of this derived table, confirm that the analyzed source cohort/version and the applicable terms match the data actually used, and preserve required attribution and notices.

The WUR source record remains marked Restricted and requires an access request. Do not distribute WUR raw library data or private access links. WUR-derived record-level records and model JSONs trained on restricted-source records need explicit project-owner/rights review; the underlying license/access terms do not establish that all derivatives may be publicly redistributed. Comparator source-code licenses do not grant rights to third-party model weights. No comparator checkpoint weights or raw MSnLib spectra were identified in the Phase 4 external ZIP inventory.

## Evidence reviewed

1. Phase 4 package: `publication_phase4/release/MURU_PHASE4_REVIEWER_PACKAGE.zip`, SHA-256 `fbb730ae35cb33a2691b5fae158826b76de2e4c9610f739063670b57b867bf32`. The inventory includes a nested frozen-output archive, project scripts, frozen model JSONs, validation/exposure/novelty tables, 1,789-row derived error table and figure outputs. No top-level license/rights notice was observed in the archive inventory.
2. Phase 2 file-level assessment `DATA_AND_LICENSE_CLEARANCE.md` and `tables/license_clearance.csv` in the recovered publication audit worktree. That document itself characterizes the review as conservative and not legal advice. It distinguishes WUR raw data, WUR-derived records, MSnLib open records, MURU model artifacts, comparator code, and comparator weights.
3. Official source pages checked 2026-11-03: [MSnLib spectral library v8, Zenodo 21105617](https://zenodo.org/records/21105617), [converted MSnLib mzML, Zenodo 15683784](https://zenodo.org/records/15683784), and [WUR Mass Spectral Library, Zenodo 20552933](https://zenodo.org/records/20552933). MSnLib pages identify open access; local rights records state CC BY 4.0. The WUR record is visibly marked **Restricted** and directs users to request access. These page checks do not determine the rights status of each downstream derivative.
4. Local Phase 2 notices explicitly state that MIT licenses for comparator code do not license weights trained on restricted or separately licensed data; comparator weights should be excluded absent exact terms.

## Asset-by-asset provisional status

| Asset in/related to the package | Evidence and current disposition | Required action before broader redistribution |
|---|---|---|
| MSnLib raw mzML | Not present in the Phase 4 reviewer archive. Official converted mzML record is open; local audit identifies CC BY 4.0. | Keep raw archive out unless separately obtained and redistribution assessed; provide citation and source-acquisition instructions. Verify exact version/file hashes if included in a later package. |
| MSnLib source spectral libraries / MGF / JSON | Raw/library source assets are not included as a complete third-party dataset in the Phase 4 reviewer ZIP. Zenodo 21105617 is Open, v8; source page asks users to cite the MSnLib paper. | Cite MSnLib and exact Zenodo record/version; preserve CC BY 4.0 attribution/notice if any source content is redistributed. Confirm exact record actually used. |
| MSnLib derived external table | Included CSV `external_compound_errors.csv` has 1,789 structure-associated rows and measured μ, predictions and errors; SHA-256 `0fb171f6df260c88f4a15295fa14b0e49bf11f43ecca634f378f37f4de52e029`. Phase 2 audit treated corresponding MSnLib-derived summaries as shareable with attribution/version/hash/transformation record. | Record exact upstream source files and version, transformation description, attribution and table hash. Human owner/legal review should confirm that compound-level derived outcomes may be publicly released under applicable source terms; do not describe as raw data. |
| WUR raw spectral library and access link | The WUR Zenodo record 20552933 is Restricted and says access is requested via WUR. Phase 2 audit says raw data/access link excluded. | Do not commit or redistribute raw files or access-specific links; use authorized access routes. Obtain written rights-holder permission for any distribution. |
| WUR-derived data/records | Local Phase 2 clearance table says record-level derivatives require clarification/permission. | Keep restricted WUR-derived record-level data out pending written permission. Aggregate results may still require project-owner review of source terms and confidentiality obligations. |
| MURU candidate/reference model JSONs and predictions | Frozen model JSONs and predictions are included in nested reviewer package for reproducibility. Training provenance includes WUR-related and other data. Phase 2 clearance says reviewer access was considered acceptable but public redistribution requires project-owner confirmation. | Confirm model artifact authorship, training-data rights, derivative status and intended public license. Do not claim that model weights inherit an open source license. |
| Comparator software/code | Project records identify MIT licenses for certain comparator source code; Phase 4 archive contains analysis scripts, not necessarily all original comparator source. | Retain upstream attribution/license notices and exact versions if code is redistributed. |
| Comparator weights/checkpoints | No third-party checkpoint weights were identified in inspected Phase 4 ZIP. Local audit says exact checkpoint license/source is required. | Exclude weights unless exact provenance and redistribution license are verified. |
| Project-authored scripts, tables, documents, figures | Likely project-owned, but the archive itself had no observed top-level license notice. | Project owner should select and apply an explicit license, confirm ownership and third-party embedded content, and ensure source attribution notices accompany release. |
| Synthetic symbolic discovery outputs | Separate research effort; not the WUR-v2 performance result. No specific Phase 4 package rights determination made here. | Keep scientifically and legally distinct; verify its own input/output provenance before redistribution. |

## Recommended notices and package hygiene

For a public reviewer package, include a `DATA_AND_LICENSE_NOTICES.md` that identifies project-owned code/data, exact MSnLib source record/version/DOI, CC BY 4.0 attribution and transformation details for derived records, and excluded restricted data. Include a file-level manifest with hashes and provenance. Keep third-party raw data, WUR access links, and unverified model/checkpoint files excluded. An attribution notice is necessary where applicable but does not replace confirmation that redistribution of a derivative is permitted.

The current technical reproduction bundle should be described as containing frozen project measurements/outputs and derived chemistry records. Do not call it fully open, raw-data-complete, or legally cleared. Sharing with a designated reviewer is distinct from unrestricted public distribution and should be reviewed under actual project and source terms.

## Human decisions still required

1. Project owner must confirm rights and chosen license for project-authored Phase 4/5 documents, code, tables, model JSONs and predictions.
2. Rights-holder or qualified legal review must determine whether the specific structure-associated MSnLib derived table may be distributed as packaged and whether its provenance/attribution notice is sufficient.
3. WUR permission is required before distributing restricted raw or record-level WUR-derived materials; the public Zenodo record is marked restricted.
4. Any later addition of third-party comparator weights requires checkpoint-specific provenance and license verification.
5. If public release is planned, verify current source terms and exact input hashes at release time. The November 3, 2026 web check is a snapshot, not a permanent legal conclusion.
