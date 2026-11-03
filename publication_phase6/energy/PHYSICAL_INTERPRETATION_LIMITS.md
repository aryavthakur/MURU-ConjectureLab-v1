# Physical interpretation limits

The converted mzML scan-level CV term `MS:1000045` with unit `UO:0000266` records a collision-energy annotation in eV. This is a source-file observation; it does not by itself prove which Xcalibur mode was selected, how the method generated the value, or whether the RAW-to-mzML conversion transformed it.

The MSnLib publication reports 20/60 eV for its ID-X library acquisition, and the Zenodo v5 record describes the converted collection as Orbitrap ID-X data. This aligns the project evidence at the article/repository level and narrows the Phase 5 “units unresolved” statement. It does not supply a run-specific native-method export. The public raw-positive archive contains seven families, not the two latest selected families. One MassIVE MCEBIO RAW file was full-file SHA-1 matched to its mzML sourceFile record; source-wide linkage is incomplete.

The model input adapter accepts numeric values and maps the frozen rung coordinate through an empirical affine transform. It does not translate absolute eV to normalized collision energy, deposited internal energy, or a universal cross-instrument scale. The A0 absolute-agreement gate failed, so physical trajectory agreement is not established. Comparator model input conventions remain different and their rank order is convention-dependent.

**Safe claim:** the fixed prediction pipelines were scored at the frozen numeric labels against the measured endpoint; the selected converted mzML records annotate those values in eV, subject to unresolved native-method and conversion provenance. **Unsafe claim:** the models were calibrated or physically validated at matched collision energies across ID-X and IQ-X.


## Public method-file search update

The public RAW-positive archive was not devoid of all files with a method extension: 161 Thermo `.meth` files were inventoried and summarized. Their declared method type and instrument field were `SeparationMethod` and `Vanquish_H`; none exposed an explicit ID-X designation, NCE setting, or collision-energy value. No selected MS2 run linkage was found. They therefore do not resolve the native Orbitrap energy mode. This search result narrows the missing-evidence statement but does not change the physical interpretation boundary. See `../metadata/METHOD_FILE_AUDIT.md`.
