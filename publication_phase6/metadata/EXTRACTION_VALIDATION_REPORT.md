# Extraction validation report

Status: PASS for frozen evaluated mzML members and selected spectra, subject to native-file linkage limitation.

- Nine source ZIP families: 9
- Unique allowlisted mzML files extracted and SHA-256 checked: 1428
- Selected frozen scan rows present in parsed mzML: 6004
- Every selected ID occurred in its hashed member: yes (script hard-fails on missing IDs)
- Selected scan energy term: PSI-MS MS:1000045, `collision energy`
- Selected scan unit: UO:0000266, electronvolt
- Selected collision-energy values matched frozen rung labels: yes (20/60)
- Selected scan activation term: beam-type collision-induced dissociation, MS:1000422
- Instrument model terms: Orbitrap ID-X (MS:1003112) in selected source records
- Software recorded in mzML: Xcalibur and ProteoWizard; versions are in `INSTRUMENT_PARAMETERS.csv`
- Native method files: none in the evaluated mzML ZIP central directories. A separate audit of the public RAW-positive archives found 161 `.meth` members across four source families; all 161 were classified as Thermo `Vanquish_H` `SeparationMethod` files and none exposed an explicit ID-X, NCE, or collision-energy setting. These LC method files were not linked to the selected mass-spectrometer runs.
- Exact mzML-to-public-RAW byte identity: independently verified for one MCEBIO RAW file by a full-file SHA-1 match to the mzML sourceFile checksum; no source-wide conclusion is supported. An earlier Zenodo filename-associated file mismatched.
- MassIVE inventory: 18,281 listing rows; 9,183 RAW, 9,085 mzML; 835/1,428 normalized filename candidates across families, candidate matches only.
- MassIVE native method-like extensions: none in the inspected listing.

Validation checks compare source member SHA-256 with the frozen allowlist, confirm ZIP CRC-32, parse the selected spectrum identifiers, require MS level 2, require exactly one collision-energy term with the expected unit and value, and compare the selected ion m/z against the frozen row metadata within the file audit. The raw archive itself was not redistributed. The 161 public `.meth` members were inspected from CRC-verified temporary extractions; only hashes and non-identifying parsed fields were retained. Their contents are insufficient to establish the ID-X MS energy mode. These results establish the converted mzML metadata semantics for the evaluated scan records, not the original mass-spectrometer method or cross-instrument calibration.


The public RAW-positive archive search found 161 `.meth` files in four source families; all parsed as Vanquish_H SeparationMethod methods with no explicit ID-X/NCE/CE setting or link to selected MS2 runs. The nested NIH 7z member passed outer ZIP size and CRC verification; its 536-name listing contained 535 mzML names and one directory entry, with no method-like suffix. See `METHOD_FILE_AUDIT.md`, `NESTED_NIH_ARCHIVE_AUDIT.csv`, and `METADATA_EXTRACTION_TESTS.md`.

## MassIVE linkage extension (2026-11-03)

MassIVE MSV000094528 file-list inventory and the one-file stream/hash verification are reported in `MASSIVE_DATASET_INVENTORY.csv`, `MASSIVE_SOURCE_FILE_COVERAGE.csv`, and `MASSIVE_RAW_LINKAGE_TESTS.csv`. Of 1,428 mzML sourceFile RAW names, 835 had a normalized candidate in the official listing; the remaining names either differed or were absent. Filename candidates are not identity proof. The MCEBIO match is direct full-file SHA-1 identity for the stated file only. No RAW payload is included in the Phase 6 package.
