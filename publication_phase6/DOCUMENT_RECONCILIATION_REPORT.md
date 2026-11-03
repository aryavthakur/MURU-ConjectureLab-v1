# Phase 6 document and evidence reconciliation

## Page counts and manuscript descriptors

The Phase 5 master PDF has 14 pages, standard-citation PDF 14 pages, online-citation PDF 19 pages, and Supporting Information 6 pages (`pdfinfo`, run on the committed files). The canonical Markdown contains 236 whitespace-delimited abstract words (242 under the lexical tokenizer used in the Phase 5 QA), 29 numbered references, five main figures, and no main manuscript tables. The supplement contains eight formatted tables according to the Phase 5 check. These values agree with Phase 5 `FINAL_PROJECT_REPORT.md`, `qa/FINAL_MANUSCRIPT_CHECK.md`, and `release/FINAL_RELEASE_READINESS.md`.

The 13-page statement originated in stale Phase 4 summary text. Phase 4's QA reported 14 pages, and Phase 5 had already recorded and checked the correct 14-page count. It is retained only as historical reporting error and is not copied into current Phase 6 reports.

## Collision-energy description

Phase 5 described the selected MSnLib numeric settings as physically unresolved because it had not recovered archive-specific native method metadata. Phase 6 has now inspected public converted mzML members from the exact frozen allowlist. The selected spectrum records encode collision energy as `MS:1000045` with unit `UO:0000266` electronvolt. The values match the frozen rung field 20 or 60. This resolves what the converted mzML records state; it does not establish that the conversion preserves the Xcalibur method's exact setting or that the adapter is a physical calibration. A full-file SHA-1 match links one MCEBIO RAW file to its mzML sourceFile record. A separate filename-associated Zenodo RAW object did not match; these are distinct repository objects. The later MCEDIV-20K and TargetMol-NPHTS families have no normalized filename candidates in MassIVE and are not listed in the linked positive-RAW Zenodo record.

The new primary interpretation is therefore: **selected external mzML records declare 20 eV and 60 eV; exact native acquisition-method provenance and physical cross-instrument equivalence remain unverified.** The original numerical adapter and study metrics do not change.

## Result and denominator consistency

The frozen result remains 1,794 measured compounds, five support exclusions, 1,789 scored compounds across 1,687 scaffold groups; candidate P1 RMSE 0.1296115107, reference P1 RMSE 0.1335276112, ratio 0.9706719801, 95% scaffold-bootstrap interval [0.9523611880, 0.9892672062], and 2.9328% relative RMSE reduction. The predefined 5% practical criterion failed. Phase 6 performs metadata extraction only and does not change measured μ, frozen predictions, exclusions, bootstrap, subgroup outcomes, or comparator results.

## Source and archive status

The nine evaluated source ZIP identifiers are defined in the frozen `msnlib_design.py::ZIPS` mapping and listed in `metadata/MSNLIB_NINE_SOURCE_INVENTORY.csv`. The exact selected mzML member hashes and scan identifiers originate from the frozen validation scan allowlist. Zenodo record 15683784 is the current v5 converted mzML record. The public positive-RAW Zenodo record, DOI 10.5281/zenodo.13785391, has seven library-family archives, not the two later families. Filename-level presence in a RAW archive is not accepted as identity without hash confirmation. Phase 6 verified one MassIVE MCEBIO RAW by full-file SHA-1 and did not generalize that match to other files.

## Unresolved documentary points

- The initial full-file metadata extraction hit HTTP 429 rate limits after 343 members; the retry run uses cached CRC-checked members and backoff. Only the final complete run's validation report is treated as the all-population result.
- The public converted metadata and the MSnLib paper agree on eV for the original seven-library acquisition; native method files and exact per-file RAW linkage remain the shortest evidence gap.
- The WUR development collision-energy field is unitless in its exported record and is interpreted as NCE/SCE by reference to its source paper/acquisition context. This point is separate from the MSnLib selected file metadata.
- The Phase 5 development max-T interval and census-defect record have not been changed by Phase 6.

## Files corrected or superseded

Phase 6 prepares a targeted energy-section revision from the Phase 5 source. It does not alter historical Phase 3-5 files. Phase 5 source, master DOCX/PDF, and SI remain preserved in their original directories and Git history.


## Phase 6 current rendered files (verified 3 November 2026)

The Phase 6 master PDF and standard-citation PDF each contain 15 pages; the online-citation PDF contains 21 pages; the Phase 6 Supporting Information contains 6 pages. The canonical abstract contains 224 words under the Phase 6 lexical tokenizer. The current manuscript has 34 numbered references and five main figures. These differ from Phase 5's 14/19-page, 29-reference documents because Phase 6 added verified energy-source context and references; they are not a contradiction in the same file. The Phase 4 13-page report is a historical stale count and does not describe the Phase 5 or Phase 6 PDFs.

Phase 6 also resolves the prior wording “native method files not found” with a specific search result: 161 public `.meth` files were found, but all parsed as Vanquish LC `SeparationMethod` records with no explicit ID-X/NCE/CE setting or selected-run link. The nested NIH 7z listing contained 535 mzML file names and no method-like name. This does not establish a native MS method. The separate Zenodo mismatch and the one verified MassIVE match concern distinct repository objects; the reason for their differing checksum outcomes is not established.
