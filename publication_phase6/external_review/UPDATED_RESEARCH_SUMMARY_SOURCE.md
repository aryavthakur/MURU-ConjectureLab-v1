# MURU-WUR-v2: summary for external scientific review

## Question and endpoint

MURU-WUR-v2 predicts a scalar fragmentation-extent statistic, μ, from molecular descriptors and Morgan count fingerprints. For each spectrum, μ is the intensity-weighted mean fragment mass divided by the precursor mass, with precursor signal included. It summarizes mass-distribution shift; it is not fragment identity, bond-cleavage count, survival yield, full-spectrum fidelity, or identification accuracy.

## Design and populations

A candidate was developed through a multi-experiment, scaffold-grouped WUR-v2 program and compared externally, without external refitting, against a separately selected Tier A ridge reference. An earlier MSnLib sample was exposed and excluded; a replacement sample was frozen and evaluated once. The replacement is now exposed and cannot serve as a fresh independent confirmation set. The final scored population was 1,789 compounds from 1,794 measured (five profile-support exclusions), across 1,687 scaffold groups. Exposure exclusions concerned recorded keys/scaffolds; they do not prove no chemical similarity to development compounds.

## Frozen external result

MURU pooled P1 RMSE was 0.1296115107; the reference was 0.1335276112. The paired ratio was 0.9706719801, with a whole-scaffold bootstrap 95% interval [0.9523611880, 0.9892672062], a 2.9328% relative reduction. The interval is below one, but the predeclared practical target of ratio ≤0.95 was not met. Tail-risk improvement was not demonstrated. In the least-similar structure quartile, the point ratio was adverse (approximately 1.0083). The frozen interpretation remains modest external confirmation under its defined numerical interface.

## What Phase 6 investigated

The nine evaluated archive families are specified in the frozen design code and allowlist. The public Zenodo v5 record identifies converted Orbitrap ID-X mzML. Phase 6 extracted exact allowlisted member bytes, checked the frozen SHA-256 and ZIP CRC, and examined all 6,004 selected MS2 scans for unit-bearing collision-energy CV terms and traceable identifiers. The peer-reviewed MSnLib methods report 20 eV and 60 eV. The original project protocol had called the numeric rungs NCE 20 and 60. The frozen adapter treats them as numeric coordinates; it is not an eV-to-NCE conversion.

The public RAW-positive archive contains 161 `.meth` files across four source families, but all are `Vanquish_H` LC `SeparationMethod` files without explicit ID-X energy settings or linkage to selected MS2 runs. The nested NIH archive lists 535 mzML files and no method-like file. The converted mzML declaration, even when matched to each selected file, cannot establish the original Xcalibur method or prove that a converter did not transform metadata. One MCEBIO RAW/mzML pair is linked by full-file SHA-1 (31,994,595 bytes; SHA-1 ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3). MassIVE has filename candidates for 835/1,428 source names, but these are not identity proof; exact source-wide linkage remains incomplete. A0's absolute-agreement gate failed, and CE Design A remains INTERFACE_UNRESOLVED.

## Questions for reviewers

- Is the converted-file eV term sufficient for describing the selected mzML setting while qualifying native-method provenance?
- What native method and RAW-to-mzML evidence is needed to establish physical semantics?
- Is the frozen score comparison interpretable when restricted to the numeric adapter, and what language avoids implying calibration?
- Is μ a valid, reproducible endpoint for the stated question?
- Do the adverse novelty and non-improved tail results constrain the conclusions adequately?
- Does candidate/reference asymmetry prevent attributing the observed difference to Morgan fingerprints?

## Evidence boundary

The strongest supported computation is statistical reconstruction from frozen measured-μ values and predictions. Phase 6 does not claim raw-spectrum reprocessing, model retraining, new independent experimental replication, physical energy calibration, or actual expert review. Development max-T interval [0.860, 0.918] remains historically reported but unreproduced.
