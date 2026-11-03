# Focused analytical chemistry review packet: energy semantics and endpoint

**For a qualified external reviewer. Prepared, not sent.** The Phase 6 metadata audit is technical evidence collection, not human adjudication.

## Study and unresolved point

The frozen MURU-WUR-v2 evaluation selected MS2 scans with numeric collision-energy settings 20 and 60. The project protocol called these NCE. The MSnLib paper reports ID-X MS2 settings of 20 eV and 60 eV. Thermo documentation distinguishes normalized percentage from absolute-voltage settings. The frozen software selects by numeric header value and passes the number through an empirical affine adapter; there is no physical eV-to-NCE conversion.

## Source record and checks

- Frozen source identifiers: nine ZIP families declared in `src/muru/wur_v2/msnlib_design.py::ZIPS` and selected scan membership in `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv`.
- Converted source: Zenodo record 15683784, version 5, DOI 10.5281/zenodo.15683784. It describes converted flow-injection mzML from Orbitrap ID-X compound libraries.
- Primary study: Brungs et al., *Nature Methods* (2025), DOI 10.1038/s41592-025-02813-0; its Data Acquisition methods describe ID-X MS2 energy settings as 20 and 60 eV.
- Instrument documentation: Thermo Orbitrap ID-X Method Editor Help distinguishes normalized collision energy percentage from absolute collision-energy voltage.
- Phase 6 extraction: `../metadata/RAW_METADATA_EXTRACTION.py` uses ZIP byte-range reads, verifies member CRC and frozen SHA-256, locates selected spectrum IDs, and extracts mzML instrument/source/software and activation CV terms. The complete all-population validation outcome is in `../metadata/EXTRACTION_VALIDATION_REPORT.md`.
- Linked RAW source: Zenodo 13785391 has seven positive-mode RAW families. Its ZIP central directories include 161 `.meth` files across four source families (67 MCEBIO, 54 NIHNP, 1 MCESCAF, 39 MCEDRUG). Parsed fields identify all 161 as `Vanquish_H` `SeparationMethod` files; none exposes an explicit ID-X/NCE/collision-energy setting or a run-level link to selected MS2 spectra. These LC methods do not establish the ID-X MS energy mode. The MassIVE MSV000094528 listing contains 18,281 files and has no method-like extension. Of 1,428 mzML sourceFile RAW names, 835 have a normalized filename candidate, which is not proof of identity. One MCEBIO RAW file (31,994,595 bytes) was streamed and its SHA-1 matched the checksum embedded in the mzML sourceFile record. This establishes identity for that file only. A different filename-associated Zenodo RAW object mismatched; those objects are distinct. The two later families have no candidates in the MassIVE listing. Native methods remain unrecovered.

## Frozen processing chain

1. Frozen selector recognizes numeric header values 20 and 60 without decoding their physical units.
2. The measured μ values and model predictions are frozen; Phase 6 does not change spectrum processing or metrics.
3. Candidate and reference are evaluated at the same measured endpoints using the fixed adapter `E=(c-a)/b`, where `a=-5.95552603907965` and `b=0.8618030610784555`.
4. The affine map is a computational coordinate adapter. No source record establishes it as an eV-to-NCE conversion or an instrument calibration.

## Statistical outcome and boundary

1,794 compounds were measured; five failed either model's profile support; 1,789 were scored in 1,687 scaffolds. Candidate P1=0.1296115107, reference P1=0.1335276112, ratio=0.9706719801, paired scaffold-bootstrap 95% interval [0.9523611880, 0.9892672062]. The 2.9328% relative reduction did not pass the predefined ratio≤0.95 practical target. Tail improvement was not demonstrated; the least-similar novelty quartile had ratio approximately 1.0083. The absolute-agreement A0 gate failed; Design A remains `INTERFACE_UNRESOLVED`.

The comparison is numerically reproducible conditional on the fixed adapter and frozen outputs. It does not establish physical energy-aligned cross-instrument transfer, calibrated collision-energy equivalence, or universal performance. Full raw mzML-to-model reconstruction is not supported by the current package.

## Questions for the specialist

Please cite the records/manual version behind each answer.

- **Q1.** Do the selected converted mzML records justify calling the annotated values 20 and 60 eV, while qualifying original-method provenance?
- **Q2.** What native Xcalibur method fields distinguish absolute voltage from normalized energy for the relevant software version?
- **Q3.** What evidence is required to show ProteoWizard copied rather than transformed the energy metadata?
- **Q4.** Does the one verified MCEBIO RAW-to-mzML SHA-1 match change the evidence standard for other files? What source-specific mapping or native-method records are still needed?
- **Q5.** Are the paper-level method statement and later v5 library families sufficiently connected for source-specific claims?
- **Q6.** Does the fixed affine adapter support any physical interpretation, or must it remain only a numeric model coordinate?
- **Q7.** Is the paired candidate/reference score comparison interpretable under the fixed coordinate, given that the A0 absolute-agreement gate failed?
- **Q8.** Is the precursor-including mass-weighted endpoint μ chemically meaningful for this bounded question, and what does it omit?
- **Q9.** Are the energy inputs to full-spectrum comparator models sufficiently fair and transparent for the conditional μ comparison?
- **Q10.** What exact records or matched instrument experiment would be necessary for a physical transfer claim?

**Review status:** no human review has occurred. Native method and RAW mapping request drafts are in `../external_requests/`; they have not been sent.
