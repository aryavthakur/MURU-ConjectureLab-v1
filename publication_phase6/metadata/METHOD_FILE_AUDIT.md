# Audit of public method-like files

**Finding:** the linked public positive RAW archives contain 161 Thermo `.meth` files, but the inspected files are Vanquish liquid-chromatography separation methods. They do not establish the Orbitrap ID-X HCD energy mode used for the evaluated MS2 scans.

The inventory was built from the Zenodo 10.5281/zenodo.13785391 record and its ZIP central directories. The 161 members occur in four archives: MCEBIO (67), NIHNP (54), MCESCAF (1), and MCEDRUG (39). Every extracted method member passed the enclosing ZIP CRC check. `EXTRACT_PUBLIC_METH_METADATA.py` summarized the OLE compound-file fields and text without retaining the unredacted payloads. The record has one observed instrument field value (`Vanquish_H`), one method type (`SeparationMethod`), and stored type version `7.0.0.179`. No member contained an explicit ID-X designation, an NCE setting, or a collision-energy setting. The two occurrences of HCD per file are text-label matches, not evidence of a numerical HCD energy parameter.

These files are not linked to specific selected scan IDs or original ID-X acquisition runs. A `.meth` extension alone is not evidence that a file contains a mass-spectrometer method: Thermo method containers can hold LC methods as well. Accordingly, the files narrow the archive search but do not resolve the physical interpretation of the converted mzML `MS:1000045` values.

The four evaluated mzML archives still contain only mzML payloads (plus directory entries where present); their ZIP central directories contain no `.raw`, `.meth`, or other native method file. The Zenodo positive RAW archive has files for seven of the nine families. A separate MassIVE file-list audit found normalized filename candidates for 835 of 1,428 sourceFile names; one MCEBIO RAW file was streamed and fully SHA-1 matched to its mzML sourceFile checksum, while a distinct filename-associated Zenodo RAW object mismatched. These objects are not treated as interchangeable. The last two families are absent from the Zenodo positive RAW record and have no normalized candidates in the MassIVE listing. The nested NIH `nih_positive_mzml.7z` member was range-downloaded from the public outer ZIP, and its outer member length (1,040,150,902 bytes) and CRC-32 (`8d41051a`) passed. Listing the 7z produced 536 names: 535 `.mzML` files and one directory entry; no method-like extension appeared. The nested archive was listed but its spectra were not extracted, and its names do not establish run-level method provenance without a validated link to the selected records.

## Audit outputs

- Per-file hashes and parsed fields: `PUBLIC_METH_FILE_METADATA.csv`.
- Archive counts and file types: `PUBLIC_RAW_ZIP_CONTENT_AUDIT.csv` and `PUBLIC_RAW_ZIP_MEMBERS.csv`.
- Public-source record metadata: `zenodo_raw_record_13785391.json`.
- Parser: `EXTRACT_PUBLIC_METH_METADATA.py`.
- Unredacted `.meth` payloads are not retained in this repository or external reviewer package.
