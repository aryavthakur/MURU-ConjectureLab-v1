# MURU Phase 3 — Start here

This directory contains a complete internal scientific draft and its supporting files. Start with `manuscript/MURU_MANUSCRIPT_MASTER.pdf` for the full paper, then read `supplement/MURU_SUPPORTING_INFORMATION.pdf`.

The main finding is modest external confirmation of a narrow scalar fragmentation-extent prediction task: 1,789 scored MSnLib compounds in 1,687 scaffold groups; candidate/reference P1 ratio 0.97067; scaffold-bootstrap 95% CI [0.95236, 0.98927]. The predeclared 5% practical-improvement criterion was not met. Tail-risk improvement was not demonstrated. The least-similar quartile had ratio 1.0083. The energy-interface result remains unresolved.

## Key contents

- `manuscript/`: source Markdown, Word files and PDFs, including standard and online citation variants.
- `figures/`: five publication-style figures in SVG, PDF and 400-dpi PNG formats.
- `tables/`: machine-readable data used for the results and figures.
- `analysis/`: figure, table and compound-error export scripts.
- `supplement/`: complete supporting-information source, Word and PDF.
- `verification/`: metric, energy, model fairness, development interval and census-defect reports.
- `review/`: three simulated adversarial reviews, revision log and Validex control crosswalk.
- `literature/`: references master, relevance matrix and claim-to-reference audit.
- `reviewer_package/`: standalone statistical reconstruction source kit without raw third-party mzML; `release/MURU_PHASE3_REVIEWER_PACKAGE.zip` is the tested archive.
- `release/`: reviewer ZIP, file manifest, hashes, GitHub PR summary, readiness and AI-assistance records.
- `MURU_PHASE3_COMPLETE_PACKAGE.zip` is delivered at the repository root; its SHA-256 is in `MURU_PHASE3_COMPLETE_PACKAGE.sha256`.

## Reproduce

The detached-release reconstruction is described in `reviewer_package/README.md`. It reconstructs the published external statistics from committed measured-μ values and frozen model JSON; it does not reparse original mzML. No third-party raw spectra are redistributed.

For the full repository, regenerate figures/tables using `python3.13 publication_phase3/analysis/export_external_predictions.py` followed by `python3.13 publication_phase3/analysis/generate_assets.py`. Render Word/PDF with `python3.13 publication_phase3/analysis/render_documents.py` and LibreOffice.

## Important record gaps

The specified Phase 2 folder, reports, audit commit and ZIP were not present in the supplied workspace or inspected remote refs. The historical development max-T interval is preserved but not independently reproduced here. The census defect's four frames and zero-impact evidence were also unavailable; no defect-specific erratum is invented. These limits are explicit in Supporting Information and the remaining-human-decisions file.
