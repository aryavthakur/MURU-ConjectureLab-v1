# Phase 6 final collision-energy adjudication

**Status: converted-file energy semantics established for the allowlisted records examined; native method provenance and physical cross-instrument comparability remain unresolved.** This adjudication supplements and narrows Phase 5. It does not alter the frozen prediction analysis.

## Evidence and scope

The frozen protocol selects numeric rungs 20 and 60. The original code matches those values numerically and passes them through the fixed adapter; the code does not parse an eV/NCE unit and does not perform an eV-to-NCE conversion. The protocol's NCE label was therefore an assumption in the frozen interface.

The MSnLib primary study describes Orbitrap ID-X MS2 settings of 20 eV and 60 eV [Brungs et al., 2025, Methods, Data acquisition](https://pmc.ncbi.nlm.nih.gov/articles/PMC12510872/). The v5 Zenodo record describes converted flow-injection mzML from Orbitrap ID-X for the compound libraries [Zenodo 15683784](https://zenodo.org/records/15683784). Phase 6 extracts exact allowlisted mzML members by byte range, checks each member against its frozen SHA-256 and ZIP CRC, then checks frozen spectrum identifiers, MS level, precursor m/z, and collision-energy CV values. The population-wide result is stated only in `metadata/EXTRACTION_VALIDATION_REPORT.md`, after that validator passes.

The PSI-MS CV distinguishes `MS:1000045` collision energy from `MS:1000138` normalized collision energy; the former's selected records specify electronvolt units (`UO:0000266`). Thermo's ID-X method documentation describes both normalized percentage and absolute-voltage settings. These facts establish what the converted mzML records declare; they do not establish what was entered in each original Xcalibur method or whether conversion preserved an unmodified acquisition setting.

The public raw-positive Zenodo record (10.5281/zenodo.13785391) lists seven earlier source families. Its ZIP central directories contain 161 `.meth` files across four families (67 MCEBIO, 54 NIHNP, 1 MCESCAF, 39 MCEDRUG). All parsed as Thermo `Vanquish_H` `SeparationMethod`; none exposes an explicit ID-X, NCE, or collision-energy setting, and none is linked to a selected MS2 run. These are LC separation methods, not evidence of the ID-X HCD mode. One MassIVE MCEBIO RAW file matches the mzML sourceFile SHA-1; a distinct filename-associated Zenodo RAW object did not. The two latest library families are absent from that raw-positive record. The nested NIH archive was range-downloaded and its outer ZIP size/CRC verified; listing its inner 7z showed 535 mzML names plus one directory entry and no method-like extension. Only names were listed, so no claim is made about unlisted metadata in the spectra. Filename similarity is not a source identity proof.

## MassIVE source identity result

The official MassIVE MSV000094528 file listing was audited. It contained 18,281 entries, including 9,183 `.raw` and 9,085 `.mzML` files, but no native-method-like extension. A documented filename normalization generated 835 candidate matches among 1,428 mzML sourceFile RAW names; these remain candidate associations. One full RAW object was streamed, checked for its listed byte count, and hashed: `20220613_100AGC_60000Res_pluskal_mce_1D1_A18_id.raw` (31,994,595 bytes) matched the sourceFile SHA-1 `ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3`. This verifies exact file identity for one MCEBIO file. It does not link the file to a native Xcalibur method, prove how the eV CV term was generated, or establish identity for other files.

## Source classifications

For all nine archive families, converted scan-level eV annotations are directly verified for the frozen selected records. At the raw-source identity level, the MCEBIO family has one exact matched file; other MCEBIO files are not covered by that match. The other eight families have converted-file evidence and, at most, normalized filename candidates. The classification is therefore **partially established** for the nine-family corpus: converted-file units are established; original run-linked methods and source-wide RAW identity are not. The MassIVE file listing has no method-like extension. The 161 Zenodo `.meth` files are LC separation methods.

## Adjudication by claim

| Claim | Finding |
|---|---|
| Frozen numeric comparison can be recalculated | Yes, from frozen measured-μ values/predictions and the fixed numeric interface. |
| Selected converted mzML declares eV values | Yes for rows whose full population verification passes; see the validation report. |
| Original native MS method for every evaluated run is recovered | No. The 161 public `.meth` files are LC separation methods without run linkage. |
| eV metadata is a byte-verified, source-specific native-method record | No. mzML metadata is converted-file evidence. |
| 20/60 eV are physically equivalent to WUR/IQ-X NCE 20/60 | Not established. |
| Frozen map is a calibrated physical conversion | No. It is a computational coordinate adapter. |
| A0 absolute trajectory agreement passed | No. The preregistered absolute-agreement anchor gate failed. |

The source-specific label is **partially established**: one-file MassIVE source identity is verified for one MCEBIO source file, in addition to the converted mzML scan-level eV annotations. This does not establish the native-method setting.  the converted evaluation records declare eV, while the upstream native method and conversion chain are not independently authenticated for each selected run. The WUR protocol and MSnLib record labels therefore cannot be treated as interchangeable physical units. No finding changes the numerical result computed under the frozen interface.

## Interpretation of the frozen result

The external P1 comparison remains a reproducible model-score comparison against measured μ values selected at the frozen numeric settings, conditional on the existing fixed adapter and support rules. It is not evidence of calibrated physical energy transfer between instruments. The interval below one describes the candidate/reference ratio under that frozen analysis; the ratio did not reach the prespecified 0.95 practical threshold. The frozen category remains “modest external confirmation,” with the energy-interface qualification stated prominently.

## Evidence needed to resolve the remaining question

For each selected run: the original Thermo RAW file with verified identity, native Xcalibur method or authoritative method export identifying HCD energy mode and setting, and conversion software/version/settings showing how the mzML `MS:1000045` term and eV unit were produced. For stronger physical transfer claims, a matched-compound cross-instrument calibration design would also be needed. The exact minimum request is in `../external_requests/NATIVE_METHOD_REQUESTS.md`; it remains unsent.
