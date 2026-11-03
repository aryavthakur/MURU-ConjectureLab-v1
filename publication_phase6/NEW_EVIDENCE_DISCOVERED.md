# New evidence recovered in Phase 6

## Converted mzML records

For all 6,004 frozen selected scan rows, the exact mzML member was extracted from Zenodo record 15683784 v5, matched to the frozen SHA-256 allowlist, and passed ZIP CRC validation. Each selected scan is MS2/HCD with collision-energy term `MS:1000045`, electronvolt unit `UO:0000266`, and value 20 or 60 matching its frozen rung. These establish converted-file annotations, not native-method settings.

## MassIVE RAW repository

The official MassIVE MSV000094528 listing contained 18,281 entries (9,183 RAW; 9,085 mzML) and no `.meth`, `.method`, `.mth`, `.msmethod`, or `.rawmethod` extension. Normalized file-name comparison gave candidates for 835/1,428 mzML sourceFile RAW names. These candidates are not identity verification. One full RAW payload was streamed and not retained: the 31,994,595-byte MCEBIO file `20220613_100AGC_60000Res_pluskal_mce_1D1_A18_id.raw` had SHA-1 `ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3`, exactly matching the SHA-1 embedded in its mzML sourceFile record. This is one-file exact identity evidence only. A distinct filename-associated Zenodo RAW object previously tested had a nonmatching checksum.

## Public method files and remaining gaps

The separate public RAW-positive Zenodo record has 161 `.meth` files across four families. They parse as `Vanquish_H` LC `SeparationMethod` records, not linked ID-X MS methods. A nested NIH archive listing contained 535 mzML names and no method-like names. Native Xcalibur MS methods, conversion logs/settings, source-wide RAW linkage, and physical equivalence to WUR/IQ-X normalized energy remain unresolved.
