# MURU-WUR-v2: FINAL CANDIDATE FREEZE

## PART I (committed before any MultiMS2 peak is decoded)

**Candidate id:** `V2_TA_MORGAN_JOINT` (generation MURU-WUR-v2)
**Code SHA at freeze:** parent of the commit carrying Part I: `cf76013`; the Part I commit itself is recorded in the anchor-calibration access record.
**Governing documents:** `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md` (wur-v2-dev-1.0, amendments A-1 to A-3), `MURU_WUR_V2_DECISION_GATE_1.md`, `MURU_WUR_V2_REVIEW_ADJUDICATION.md`, `MURU_WUR_V2_MULTIMS2_EXTERNAL_PROTOCOL.md` (draft r2, frozen by reference here with the values below).

### 1. Candidate specification

| Item | Frozen value |
|---|---|
| Endpoint (development) | `features.mu`, base cell (no cutoff, precursor included, raw intensities, 10 ppm, declared precursor m/z); WUR archive copies collapsed then median over distinct acquisitions; LCSB corpus value |
| Profile architecture | frozen v1 collapse on all 1,325 development compounds: shared isotonic Phi on log u (60 knots), one scale g per compound, u = (E/30)/g, unit geometric mean, curvature weights |
| Representation | 12 Tier A descriptors scaled by `protocol.SCALE`, standardized with the 1,325-compound mean and SD; Morgan radius 2, 2,048 hashed counts, no chirality, log1p, weighted by 0.1; RDKit 2026.03.5 |
| Model | ridge of log g on the concatenated block, alpha 0.3, curvature sample weights; alpha and block weight chosen by nested inner grouped folds with inner collapse refits and trajectory loss |
| Prediction | mu(E) = Phi((E/30)/exp(log g_hat)), E in the LCSB nominal NCE coordinate |
| Trust | none (Experiment 10 failed); no abstention |
| Serialized model | `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json`, sha256 `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b`, with feature_spec and canaries |
| Comparators | `V2_REF_TA_RIDGE` (primary; sha256 `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32`), `V2_REF_B1_MASS` (`3e8b889c9b096dec2e03b01ad900b49ad3046fb56c0795c54e39150c64c2ab56`), `V2_REF_B0_NULL` (`b910cc0d8a16002612a010d5898cf436edd4dd0ac60612371e8fdfac7b7ff56a`), historical `V1B_RIDGE_TIERA_FROZEN` (`da8ab9ba487419d455966b8e61ecb75b6a74146e34dad57a1ef9e8db5b3d7575`) |
| Training population | 1,325 keys, sha256 `81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd` |
| Excluded populations | LCSB confirmation set, WUR negative mode, LCSB negative mode |
| Development evidence | PRIMARY P1 0.1160 vs 0.1305 (ratio 0.889, conditional [0.865, 0.911], ten-arm simultaneous [0.860, 0.918]); STRICT 0.926; AF 6.3 vs 10.3 percent |

### 2. External populations (identity and allowlisted headers only; `artifacts/wur_v2/external/populations.json`)

| Population | Compounds | v2 scaffold groups | keys sha256 | Matched MS2 spectra | Use |
|---|---|---|---|---|---|
| VALIDATION | 1,297 (NEXUS 1,290, Selleck 7) | 942 | `c411bb04d909c3306d93a0fb3e79fad446d0fc5f3065e54197e24d4d3dc1cdc0` | 16,395 | the one look |
| ANCHOR | 106 (NEXUS 105, Selleck 1) | 88 | `bea5578581536bb56017297f8ca6828d0168c85b790377e4889948eb6a20d479` | 1,292 | adapter fit and gate only |
| SECONDARY (identity-new, scaffold-seen) | 228 | 64 | `bd5639d472688dcab4506a597027f0fee4e5ae9547b758843428adcae9bf40bb` | 3,195 | reported separately, never pooled |

Attrition of the 2,982 design-frame scaffold-new keys: R1 single position with 20/40/60 eV files 2,895; R3 no same-position isolation conflict 2,468; R2 MS2 triggered on [M+H]+ within 0.05 Da at all three energies 1,298; R4 scan window (every matched MS2 scan 50 to 1,000 or 1,500 m/z) and header collision energy equal to the file energy 1,298; R5 [M+H]+ in 70.0 to 1,042.6 m/z 1,297; R7 charge-neutral scaffold new 1,297. Anchors: 217 v2 five-rung keys in the design frame, 165, 147, 106, 106, 106 after R1, R3, R2, R4, R5. No spectrum is matched to both an anchor and a VALIDATION or SECONDARY compound (asserted).

Header facts (allowlisted CV terms only; 642,765 spectra, 413,712 MS2; parquet sha256 `643d1b07...5f110d`): every MS2 scan window starts at m/z 50 (WUR development: 40); upper limits 1,000 or 1,500; header collision energies 20, 40, 60. Disclosed selection mechanism: R2 depends on MS1-level IDA triggering of [M+H]+, an acquisition event that can correlate with ionization efficiency and in-source fragmentation, not with MS2 fragmentation outcomes; census QC-pass membership was not used.

### 3. Endpoint, adapter, gate, success rule

Exactly as `MURU_WUR_V2_MULTIMS2_EXTERNAL_PROTOCOL.md` draft r2 (status: frozen by this document) sections 3, 4 and 6, implemented in `src/muru/wur_v2/external_multims2.py` (`spectrum_mu`, `measured_mu`, `adapter_energy`, `fit_adapter`, `gate`, `score_population`, `decide`) and run by `scripts/wur_v2/ext02_anchor_calibration.py` and `scripts/wur_v2/ext03_validation.py`. Failure definition AF: three-rung compound RMSE > 0.20. Bootstrap: whole v2 scaffold groups of validation compounds, B = 10,000, seed 20261001, P1 of both models recomputed per replicate. Primary: upper 95 percent limit of the P1 ratio (candidate / TA ridge) below 1.00; practical target: point ratio at most 0.95; key secondary (only if primary supported): AF difference upper 95 percent limit at most +0.03.

### 4. Prohibited after any external access

No change to the candidate, comparators, features, profile, populations, rules R1 to R7, endpoint, adapter family, gate thresholds, success rule, bootstrap or any threshold; no second validation run; no repair-and-revalidate on MultiMS2. Anchor outcomes may be used only to fit the adapter and evaluate the gate. If the gate fails, no validation spectrum is decoded and MultiMS2 is reported as not qualified for this claim.

### 5. Pre-registered expectation and interpretation

Plausible external ratio about 0.92 to 1.00 (development 0.889, strict clusters 0.926, structure-only reweighting 0.92 to 0.93, plus an untested instrument and energy-coordinate change). Power about 0.89 at a true ratio 0.961 with about 800 groups (942 here). A null result bounds the transfer of the development gain to this regime and does not refute it; a positive result supports the three-rung transfer claim only, not the 11 percent.

### 6. Freeze-precedes-access

The anchor guard requires this document committed on a clean tracked tree and writes `artifacts/wur_v2/external/anchor_calibration_access.json` before the first anchor decode. Part II (fitted adapter, gate result) is appended in a separate commit before `scripts/wur_v2/ext03_validation.py`, whose guard writes `validation_access.json` before the first validation decode and refuses a second run.

## PART II (after anchor calibration): MultiMS2 NOT QUALIFIED; validation not executed

**Anchor access:** `artifacts/wur_v2/external/anchor_calibration_access.json`, 2026-09-13T02:26:16Z, HEAD `6c6cc4f`, clean tree, 1,292 anchor spectra of 106 anchors decoded; no VALIDATION or SECONDARY spectrum decoded.

**Gate result (`artifacts/wur_v2/external/anchor_calibration.json`):**

| Adapter | Parameters | 20 eV median abs delta / Spearman | 40 eV | 60 eV | pooled RMSD | passes |
|---|---|---|---|---|---|---|
| A1 `E = k e 500/m` | k 0.577 | 0.078 / 0.33 | 0.074 / 0.66 | 0.060 / 0.72 | 0.130 | no |
| A2 `E = k e (500/m)^gamma` | k 0.514, gamma 1.27 | 0.099 / 0.34 | 0.068 / 0.68 | 0.068 / 0.63 | 0.128 | no |
| required | | <= 0.05 / >= 0.80 | same | same | <= 0.08 | |

**Decision (frozen rule):** MultiMS2 is **not qualified** for the three-rung fixed-energy transfer claim. `scripts/wur_v2/ext03_validation.py` refuses to run (the calibration record says `qualified: false`), no validation spectrum has been decoded, and the 1,297-compound VALIDATION and 228-compound SECONDARY populations remain outcome-unaccessed. The 106 anchors are now exposed as calibration data.

**Diagnostics (anchors only, separately logged re-decode, `anchor_diagnostics_access.json`, `anchor_diagnostics.json`):** the MultiMS2 observable is internally sensible (95 percent of anchors monotone across 20/40/60 eV; within-cell scan SD 0.028, comparable to Orbitrap inter-preparation repeatability; median precursor fraction 0.52, 0.002, 0.00 at 20/40/60 eV). It is not an implementation defect: without any adapter or model, the best rank correlation between an anchor's MultiMS2 mu and its exposed Orbitrap mu at any development rung is 0.47 at 20 eV, 0.56 at 40 eV and 0.83 at 60 eV (against at least 0.87 at every rung for the 124 compounds measured on both Orbitraps). A 1 percent intensity cutoff or removing ions above the precursor does not change this (40 eV best 0.53 and 0.55). Contributing differences are fixed lab-frame energy on a QTOF against normalized HCD energy, a 50 m/z scan start against 40, raw centroids with a median 480 to 620 peaks per spectrum against vendor-thresholded library spectra, and pooled direct infusion (3.7 percent of intensity above the precursor at 20 eV). The compound ordering of fragmentation propensity at 20 to 40 eV on this instrument is only weakly aligned with the development coordinate, which no 1- or 2-parameter energy adapter can repair. These diagnostics are descriptive and do not change the frozen decision.

## PART III (before any MSnLib peak is decoded): MSnLib two-rung anchors-first gate

**Authorization.** The user chose "anchors-first MSnLib gate" (2026-09-13): download only the anchor wells (561 Zenodo 15683784 mzML members, 1.26 GB compressed), run the gate, and stop to ask before any validation download or look.

**Frozen by reference:** `MURU_WUR_V2_MSNLIB_EXTERNAL_PROTOCOL.md` (claim, well/scan/rung rules, endpoint, anchors, adapter families A0/A1/A2 and grids, gate thresholds, validation sampling of 2,000 scaffold groups at seed 20261010, primary rule, secondary rule, bootstrap seeds), implemented in `src/muru/wur_v2/external_msnlib.py` and `scripts/wur_v2/ext11_msnlib_anchor_gate.py`. Candidate, comparators, profile and all Part I prohibitions are unchanged. MultiMS2 remains not qualified and its validation population undecoded.

**Disclosure.** The MSnLib protocol was written after the MultiMS2 anchor gate failed and after the MSnLib outcome-blind census; no MSnLib outcome, library spectrum or detected-compound flag informed it. 96 of the 402 MSnLib anchor keys are MultiMS2 anchors (exposed calibration data).
