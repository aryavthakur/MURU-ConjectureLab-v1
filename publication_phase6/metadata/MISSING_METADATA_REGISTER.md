# Missing metadata register

## Resolved at converted-file level

The frozen evaluation allowlist resolves to nine positive-mode source ZIPs, 1,428 unique mzML members, and 6,004 selected MS2 scan rows. Exact selected member bytes were checked against frozen SHA-256 values; ZIP CRCs and selected scan identifiers were verified. Each selected scan records collision energy as eV in mzML.

## Newly resolved source identity

The official MassIVE MSV000094528 listing was compared with the sourceFile RAW names. Normalized filename candidates were found for 835 of 1,428 names; this is a candidate count only. One complete RAW payload was streamed, without retention: 31,994,595 bytes, SHA-1 `ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3`. It matches the SHA-1 embedded in the selected MCEBIO mzML sourceFile record. Exact RAW-to-mzML identity is therefore proven for one file, not all files. A different filename-associated Zenodo RAW object previously tested had a different checksum; the repository objects are not treated as interchangeable.

## Still missing or not linked

1. Run-linked native Xcalibur MS methods for the evaluated spectra remain unavailable. The MassIVE listing contained no `.meth`, `.method`, `.mth`, `.msmethod`, or `.rawmethod` file extensions. The 161 `.meth` records in the separate Zenodo archive are `Vanquish_H` LC `SeparationMethod` records, not ID-X MS methods.
2. The broader RAW identity mapping remains incomplete. MassIVE filename candidates outside the one SHA-1-tested file are not identity evidence; two later source families have no candidate names there.
3. Source-specific conversion settings and logs are unavailable, so the path from native Xcalibur method to converted mzML CV annotation is not fully established.
4. Physical equivalence between MSnLib's reported eV setting and the WUR/IQ-X normalized energy coordinate is not established.

## Shortest recovery route

Request run-linked Xcalibur method exports, original RAW identifiers/checksums for the remaining eight-family coverage and conversion software/settings from the MSnLib data custodian. The drafted request is unsent. A qualified mass-spectrometry reviewer should assess the converted-file semantics and the limited one-file RAW link before stronger wording is adopted.
