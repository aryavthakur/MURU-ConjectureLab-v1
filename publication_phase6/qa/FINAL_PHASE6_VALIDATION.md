# Phase 6 final validation record

Date: 3 November 2026
Branch base: `c945b1e90f017beebd7c58386bbbdb6b6a65e38e` (`publication/phase5-release-candidate`)

## Scientific reconstruction

A new ZIP was created from `publication_phase3/reviewer_package`, extracted into a fresh temporary directory, and run with `python3.13 verify_reproduction.py`. Exit status was 0. The verifier passed checksums, required files, environment, and frozen results. Reconstructed counts were 1,794 measured, 5 excluded, 1,789 scored, and 1,687 scaffold groups. Candidate/reference P1 RMSE was 0.12961151072591617 / 0.13352761116871245; ratio 0.9706719800607511; scaffold bootstrap interval [0.9523611879747089, 0.9892672061846276]. Decision remains `MODEST EXTERNAL CONFIRMATION`; relative reduction 2.9328%, below the 5% criterion.

`python3.13 publication_phase6/verification/verify_phase6_metadata.py` exited 0: nine source archives, 1,428 allowlisted mzML members, 6,004 selected scans, all energy CV terms matched the frozen 20/60 eV rung labels; 161 public `.meth` files were LC `SeparationMethod` records and did not expose ID-X collision settings; the nested archive listing contained 535 mzML names and no method-like file.

`python3.13 publication_phase6/verification/check_phase6_release.py` exited 0: abstract 224 words, 34 references and mapped citations, 6,004 lineage rows, frozen metrics and adverse findings present, five figure SVG/PDF/PNG triplets, and required Word/PDF outputs present.

## Archive and integrity checks

`python3 publication_phase6/release/build_phase6_packages.py` rebuilt both archives, verified each ZIP member, rejected raw/mzML/method/7z payload extensions and members >=100 MB, wrote the file manifest and SHA-256 list. The external archive has 15 members; the complete archive has 159 members. `shasum -a 256 -c release/FINAL_SHA256SUMS.txt` passed when run from `publication_phase6/`. ZIP `unzip -t` checks passed for both archives.

The existing statistical package integrity fault tests were performed in disposable copies: checksum modification and a missing required measured-mu file each caused the expected nonzero failure. A stale Phase 5 virtual environment lacked SciPy; the documented system Python 3.13 environment completed the clean extraction successfully.

## Document rendering

Final master, standard-citation, online-citation, Supporting Information, feedback form, and reviewer packets were rendered from DOCX to PDF with the document skill renderer. Page-image contact sheets were inspected. Counts were 15 pages (master/standard), 21 pages (online), and 6 pages (SI); external analytical chemistry review packet: 2 pages. No clipping, missing graphics, broken tables, or corrupted symbols were observed in the inspected final renders.

## Reproduction boundary

This is statistical reconstruction from frozen measured-μ values and frozen prediction artifacts, plus mzML metadata validation. It is not raw-spectrum reprocessing, model retraining, native method reconstruction, or a new independent experimental validation. The single exact RAW/mzML SHA-1 identity used an unverified-TLS transfer and was not repeated because of rate limiting; the limitation is disclosed in the report and source CSV.
