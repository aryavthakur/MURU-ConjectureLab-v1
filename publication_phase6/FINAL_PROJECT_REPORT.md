# MURU Phase 6 final project report

## Work completed

- Verified the Phase 5 head and the three open stacked draft PRs. Created this phase on `publication/phase6-evidence-recovery`; no frozen branch was modified.
- Reconstructed all nine frozen source archive families from study code and allowlist. Verified 1,428 mzML members and all 6,004 selected scans, including per-member SHA-256, ZIP CRC, scan ID, MS level, precursor m/z, activation term, CE term/unit/value.
- Parsed the official MassIVE MSV000094528 listing (18,281 rows; 9,183 RAW and 9,085 mzML), identified 835/1,428 filename candidates, and verified one full-file MCEBIO RAW-to-mzML SHA-1 identity (31,994,595 bytes). Filename candidates are not identity proof. Parsed method summaries only; removed unredacted method payloads from the temporary cache and did not add them to Git.
- Verified the nested NIH 7z outer member size and CRC and listed its contents. It lists 535 mzML files and no method-like member. No spectra were extracted.
- Updated the collision-energy adjudication, source inventories, SI, manuscript, review packet, literature records, and human-review materials.
- Re-rendered the manuscript and SI after the MassIVE evidence update. Master and standard-citation PDFs are 15 pages; online-citation PDF is 21 pages; SI is 6 pages. The structured abstract is 224 words under the recorded tokenizer; the bibliography has 34 entries; five figures are embedded.
- Reproduced frozen-output statistics from the prior fresh-extraction reviewer archive and confirmed corruption/missing-file checks fail as expected.

## Scientific outcome

Converted mzML eV annotations are established for the selected scans. Native ID-X energy mode, conversion history, and physical equivalence to the WUR/IQ-X energy coordinate are not established. One MCEBIO sourceFile/RAW identity is now verified by full-file hash; native Xcalibur methods, conversion settings, source-wide RAW linkage, and physical energy comparability remain unresolved. The primary frozen outcome and its 5% practical-target failure are unchanged. The external population remains exposed, so Phase 6 does not add an independent validation claim.

## External circulation

A qualified-review package is prepared but marked **not cleared to send** pending owner confirmation of recipient, sharing scope, and project-authored material rights. No email was sent. No independent human review occurred.

## Final package verification

The rights-scoped external review archive and complete Phase 6 archive were rebuilt from the final source files on 3 November 2026. Both ZIP integrity tests passed; no RAW, mzML, `.meth`, or 7z payloads were included. The external package is explicitly marked prepared but not cleared to send. SHA-256 values are recorded in `release/FINAL_SHA256SUMS.txt`; `release/FINAL_FILE_MANIFEST.csv` lists individual included-source-file sizes and hashes. Human review remains pending.
