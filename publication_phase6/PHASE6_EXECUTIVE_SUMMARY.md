# Phase 6 executive summary

Phase 6 verified converted-file collision-energy metadata for all frozen MSnLib selection rows: nine archive families, 1,428 allowlisted mzML members, and 6,004 selected MS2 scans. Every selected scan is represented in a SHA-256 checked mzML member and annotated with collision-energy CV term `MS:1000045`, electronvolt unit `UO:0000266`, and frozen numeric rung 20 or 60. The records identify Orbitrap ID-X and HCD.

The official MassIVE MSV000094528 listing had 18,281 entries, including 9,183 RAW and 9,085 mzML files; it contained no native-method-like extension. Filename normalization yielded candidates for 835 of 1,428 sourceFile RAW names. These are candidates only. One MCEBIO RAW file was streamed in full (31,994,595 bytes) and its SHA-1 matched the checksum embedded in the corresponding mzML sourceFile record. This establishes exact file identity for one pair, which contributes eight selected scan rows. Other source records were not all hash-tested; source-wide linkage remains incomplete. A different filename-associated Zenodo RAW object mismatched, and is treated as a distinct repository object.

No run-linked native Xcalibur MS method or source-specific conversion settings were recovered. The frozen adapter is a numerical coordinate, not calibrated eV-to-NCE conversion. Physical transfer to the WUR/IQ-X coordinate remains unresolved, and the A0 absolute-agreement gate failed.

The primary result remains unchanged: candidate/reference P1 RMSE 0.1296115107/0.1335276112; ratio 0.9706719801; scaffold-bootstrap 95% CI [0.9523611880, 0.9892672062]; relative reduction 2.9328%, below the 5% target. Tail benefit was not demonstrated; least-similar quartile ratio is approximately 1.0083. No human review occurred.
