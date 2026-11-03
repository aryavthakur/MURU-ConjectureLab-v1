# MassIVE source-file identity audit

**Finding:** one of the 1,428 evaluated mzML source-file RAW references was positively verified by full-file checksum against a RAW payload in MassIVE. Only this one was hash-tested in Phase 6; no conclusion is made that no other file could be linked. The RAW payload was streamed and hashed but not retained.

- Dataset: MassIVE MSV000094528; public record lists CC0 1.0 and status Partial Public.
- File listing: 18,281 entries, including 9,183 RAW and 9,085 mzML; no `.meth`, `.method`, `.mth`, `.msmethod`, or `.rawmethod` extension.
- Candidate name map: 835/1,428 names match after documented lower-case, `_id`, and ENAMMOL-prefix normalization. These are candidate names, not source identity.
- Exact match: source `20220613_100AGC_60000Res_pluskal_mce_1D1_A18.raw`; MassIVE object `raw/20220601_positive/20220613_100AGC_60000Res_pluskal_mce_1D1_A18_id.raw`; 31,994,595 bytes; both SHA-1 `ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3`. The source file is in the frozen MCEBIO archive and contributes eight selected scan rows.
- A previously tested Zenodo RAW object associated by filename had a different checksum. The repository objects have distinct names and locations; the mismatch is not interpreted as contradictory evidence about the MassIVE match.
- Source families MCEDIV-20K and TARGETMOL-NPHTS have no normalized filename candidates in this MassIVE listing.

This result establishes byte identity for one RAW/mzML pair. It does not establish the original Xcalibur method, instrument collision-energy mode, conversion behavior, run linkage for other files, or physical comparability with the WUR/IQ-X energy coordinate.
