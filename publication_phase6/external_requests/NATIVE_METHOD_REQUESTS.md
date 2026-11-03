# Targeted request for native acquisition and conversion evidence

**Draft only; not sent.** The public records have been inspected directly. This request asks for the minimum source documentation needed to distinguish converted mzML annotations from the original acquisition method.

## Scope

- Converted mzML: Zenodo record 15683784, v5, DOI `10.5281/zenodo.15683784`.
- Selected library families: the nine source ZIPs named in `../metadata/MSNLIB_NINE_SOURCE_INVENTORY.csv` or the frozen source map in `src/muru/wur_v2/msnlib_design.py::ZIPS`.
- Positive raw archive record: Zenodo 13785391, DOI `10.5281/zenodo.13785391`.
- Selected scan linkage: `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv`.

## Minimum evidence requested

1. For each acquisition family, the Xcalibur method or an authoritative method export specifying HCD energy mode (normalized percentage or absolute voltage) and values for the selected MS2 scans.
2. An authoritative mapping from every evaluated mzML source file to its native Thermo RAW filename and file hash.
3. The ProteoWizard version and conversion options used for the evaluated mzML files, including whether the collision-energy term/unit was copied from RAW metadata or transformed.
4. Equivalent method and RAW mapping for the later MCEDIV-20K and TargetMol-NPHTS families included in the v5 mzML record.

An original method file is preferred; a method export or documented confirmation tied to exact file/run identifiers is acceptable. No additional spectra, compound tables, or broad repository access are requested. If this evidence cannot be shared, a source-specific written statement and corresponding method/software version would still narrow the remaining uncertainty.

## Current outcome

The evaluated mzML source ZIPs contain mzML payloads only. A separate audit of the Zenodo raw-positive archives found 161 `.meth` files, all `Vanquish_H` `SeparationMethod` files without explicit ID-X/NCE/collision-energy settings or selected-run linkage. The MassIVE MSV000094528 listing contained 18,281 files and no native-method-like extension. Of 1,428 mzML sourceFile RAW names, 835 have normalized filename candidates; these are not identity proofs. One MCEBIO RAW file was streamed in full and SHA-1 matched its mzML sourceFile checksum, establishing exact identity for that file only. A distinct filename-associated Zenodo RAW object mismatched. Native methods, source-wide RAW identity, and conversion settings remain unresolved. The request remains unsent pending owner approval of recipient and sharing scope.
