# MURU-WUR-v2: final report

**Date:** 2026-09-13. **Branch:** `claude/muru-wur-v2-generation-b2ffa1`, descended from the accepted WUR lineage `fable/wur-stage2-muru-development` at `17027e1` (no drift found). Governing documents: `MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md`, `MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md` (wur-v2-dev-1.0, amendments A-1 to A-3), `MURU_WUR_V2_DECISION_GATE_1.md`, `MURU_WUR_V2_REVIEW_ADJUDICATION.md`, `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md`, `MURU_WUR_V2_MULTIMS2_EXTERNAL_PROTOCOL.md`, census reports, ledger `artifacts/wur_v2/ledger/ledger.jsonl` (23 entries), run state `MURU_V2_RUN_STATE.md`.

**Bottom line.** v2 is a materially better point predictor than v1 on every hard development split, built by one simple change: add atom-type composition and first-shell environments (log Morgan counts) to the Tier A scale ridge. It is not externally validated. The first external candidate, MultiMS2, failed its pre-registered observable-compatibility gate on calibration anchors, so its validation population was correctly left undecoded. No trust mechanism survived, and the one-scale shared profile stays.

## 1. Measurement and statistics corrections

- **P1 versus the old intervals.** v1 Stage 3 reproduces exactly from committed code. Recomputing P1 inside a scaffold-cluster bootstrap changes no v1 conclusion: V1B/S2A P1 ratio 0.849 [0.807, 0.891], V1B/mass-only 0.882 [0.826, 0.939]; mass-only versus S2A and V1C versus V1B still include 1. The historical intervals were for mean per-compound RMSE differences, not P1; P1 0.1251 is not the mean compound RMSE 0.1080.
- **Empirical repeatability.** WUR has no technical replicates: 5,580 of 6,060 cells are two archive copies of one acquisition, and 41 of 42 multi-acquisition keys are different isomers. Independent LCSB preparations (26 compounds) give log g ICC 0.97 and a per-measurement log g SD of 0.116, 1.6 times the curvature SD behind v1's "0.988 reliability", which was not a repeatability. Cross-instrument pairs (124) give ICC 0.94. A scale measured on one preparation predicts the other at trajectory P1 0.065: that, not 0.052, is the practical floor.
- **Scale identifiability.** 42 of 1,325 scales sit at the grid edge (heavy compounds already fragmented at E30); median likelihood-interval width 0.15 log units; weakly identified scales carry no absolute failures.
- **Absolute failure.** Frozen before any v2 fit as compound trajectory RMSE > 0.20 (worse than a no-information per-rung mean, about 77 percent of a typical trajectory's excursion, 4 to 7 times measurement variation), with a single-rung error > 0.30 as secondary. Historical S4 is kept.
- **v1 interpretation.** Unchanged in direction; its uncertainty statements are now exact, and the 0.988 claim is withdrawn.

## 2. Experiments

| Exp | Hypothesis | Model / population | Result | Decision |
|---|---|---|---|---|
| 1A | Estimand fix changes v1 reading | Stage 3 reproduction, 404 compounds | exact reproduction; intervals corrected, conclusions unchanged | diagnostic |
| 1B | Fair v2 baseline | TA_RIDGE refit, 1,325 compounds, PRIMARY | P1 0.1305, MRMSE 0.1148, AF 10.3 percent; v1 selection shortcut irrelevant (< 0.001) | accepted baseline |
| 2 | Noise dominates / scales unidentifiable | repeats, identifiability | repeat noise 4 to 12 percent of Tier A log g error variance, 30 to 32 percent of the candidate's trajectory MSE; scales identifiable | diagnostic |
| 3 | E30 error is scale error | TA_RIDGE OOF decomposition | scale-only term 72 percent of the E30 to E90 MSE gradient (92 with cross term); linear derivative mechanism not supported | diagnostic |
| 4 | Survival versus depth | exact decomposition | no information beyond total mu (regression mechanically dominated) | diagnostic |
| 5 | Acquisition/ion effects | paired and unpaired | per-rung mu equivalent within 0.02 after the map; log g source x mass slope +0.13 per 100 m/z; modelling it moves P1 < 1 percent; non-[M+H]+ worse | diagnostic |
| 6 | Sample- versus representation-limited | learning curves | Tier A flat by half the data; Morgan improves to 100 percent on PRIMARY, flat by 75 on STRICT | diagnostic |
| 7 | Audited ion-environment block helps | TA + 12 SMARTS features | 0.1277, ratio 0.978 [0.960, 0.995]; not robust to ten-arm adjustment; adds 0.8 percent beyond Morgan | admitted (unadjusted), not selected |
| 8A | Morgan alone | ridge | 0.1239, 0.949 | admitted, not selected |
| **8B** | **Tier A + Morgan joint** | **ridge** | **0.1160, 0.889 [0.865, 0.911]; STRICT 0.926; GIANT 0.896; AF 6.3 percent** | **selected** |
| 8C | Tier A then Morgan residual | two stage | 0.1166, 0.893 | admitted, tied class |
| 8D | Tanimoto kernel | MinMax kernel ridge | 0.1189, 0.911 | admitted |
| 8E | + ION_ENV (A-1) | joint | 0.1151, 0.882; STRICT 0.905 | admitted, within 1 percent, more complex |
| 9A | Alternative metric | atom-pair ridge | 0.1229, 0.941 | admitted |
| 9B | MACCS | ridge | 0.1326, 1.016 | rejected |
| 9C | Neighbour residuals | kNN on Morgan | 0.1215, 0.931; GIANT 1.00 | admitted |
| 9D | Metric in joint model (A-1) | Tier A + atom pairs | 0.1157, 0.886 | admitted, equivalent |
| 10 | Pre-measurement trust | 6 signals + small models | no discrimination (PR-AUC 0.084 vs random 0.068; retained AF at 80 percent coverage unchanged) | rejected |
| 11 | Shape oracle | tangent-orthogonal PC1 | reproducible (r 0.77, 0.85), weakly predictable (R^2 0.18), held-energy oracle -12.7 percent | diagnostic |
| 12 | One predicted shape coefficient (A-2) | joint + shape | 0.1139, 0.982 vs joint [0.976, 0.988]; below the frozen 2 percent bar | rejected |
| 13 | Disprove the winner | sensitivities | ratio 0.84 to 0.94 on every sensitivity (weighting, folds, cluster unit, leverage, novelty, native energies, source transfer) | diagnostic |

## 3. Learning curve

Tier A is representation-limited (flat from 50 percent of groups, supported by a nonlinear Tier A control). The fingerprint gain is partly coverage-limited: it grows with data and shrinks with novelty (Morgan alone 11, 5.1 and 1.7 percent on random, scaffold and strict-cluster splits; the joint model 15.5, 11.1 and 7.4 percent). More diverse training chemistry is the most direct route to further gains.

## 4. Structural representation

Tier A alone 0.1305; ION_ENV 0.1277; Morgan 0.1239; atom pairs 0.1229; Tier A + Morgan 0.1160; Tier A + atom pairs 0.1157; Tier A + ION_ENV + Morgan 0.1151. **Best clean gain: about 10 to 11 percent after selection adjustment** (ten-arm simultaneous interval 0.860 to 0.918), 7.4 percent on strict clusters, 8.2 percent against a quadratic Tier A control. The red team decomposed it: about half is atom-type composition (radius-0 invariants: ring CH, quaternary carbon, ring ethers, chlorine lower g; substituted aromatic carbon and methyls raise it) and half first-shell environments; radius 1 matches radius 2; conazole fungicides carry 22 percent of the scaffold-split gain.

## 5. Trust

Predictors: maximum training similarity, leverage, Mahalanobis distance, Tier A versus joint disagreement, profile sensitivity, adduct/mass domain flag, and a small learned combination, all cross-fitted. None beats random or distance-only rejection at 70 to 90 percent coverage; calibration slope 0.20. **Trust is not retained**; only the documented [M+H]+ domain restriction remains.

## 6. Shape

Oracle gain descriptive 12.7 percent but negative on held energies; the residual tilt is reproducible and weakly predictable; the nested predicted-shape model gains 1.8 percent (1.2 to 2.4) over the joint model, below the pre-set bar. **Decision: keep one shared profile with one scale.**

## 7. Quantum, pretrained encoder, direct trajectory model

Not run. Quantum: the ion-environment block adds under 1 percent once Morgan is present, and xTB is not installed. Pretrained encoder: two structural metrics give the same joint result and the fingerprint learning curve is nearly flat at 100 percent, which points at chemical coverage, not representation. Direct trajectory: the shape phase closed.

## 8. Final v2 candidate

| Item | Value |
|---|---|
| Candidate id | `V2_TA_MORGAN_JOINT` |
| Architecture | frozen v1 shared isotonic profile, one scale per compound; ridge (alpha 0.3) of log g on standardized Tier A (12) plus 0.1 x log1p Morgan r2 2,048 counts; trained on 1,325 compounds |
| Development P1 (PRIMARY) | 0.1160 vs refitted Tier A 0.1305 (ratio 0.889, conditional [0.865, 0.911], simultaneous [0.860, 0.918]) |
| Mean compound RMSE | 0.1005 vs 0.1148 |
| Tail | Q95 0.212 vs 0.231; AF 6.3 vs 10.3 percent (difference [-0.055, -0.023]); AF_max 6.5 vs 10.0; S4 7.0 vs 9.4 percent |
| Hard splits | STRICT 0.926; benzene held out 0.896; S1/S2 0.883/0.890; both sources 0.88 to 0.89 |
| Trust | none |
| Complexity | 12 descriptors + one hashed count fingerprint in one linear model; deterministic; seconds to train |
| Versus historical v1 | on the 404 formerly sealed compounds (descriptive, different training data): 0.1121 out-of-fold versus frozen v1 0.1251 |
| Reason selected | simplest admitted model within 1 percent of the best; the added ION_ENV and atom-pair variants are not separable from it and not simpler |
| Serialized | `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json`, sha256 `11aa801c...e9b`, feature provenance and canaries checked at prediction time |

## 9. MultiMS2 census

- Release: Zenodo 17250693 v2.0.0 centroided mzML, CC0 1.0; paper DOI 10.1093/gigascience/giag069; SCIEX ZenoTOF 7600, direct injection of pools, CID 20/40/60 eV (lab frame), MS2 scan window 50 to 1,000/1,500 m/z.
- Initial size 2,899 compounds; library frame three-rung [M+H]+ 1,502; exact overlap removed 1,378; scaffold-new 1,165 (808 groups). Library QC censors precursor-rich spectra, so the design frame and raw mzML were used instead.
- Design frame: 2,982 scaffold-new identity-new keys; after single position with all three energy files 2,895; no same-pool isolation conflict 2,468; MS2 triggered on [M+H]+ at all energies 1,298; scan window and energy headers 1,298; mass range 1,297; charge-neutral scaffold new 1,297 compounds in 942 groups (VALIDATION, sha256 `c411bb04...cdc0`). Anchors 106 in 88 groups; SECONDARY 228.
- Scope correction: drug-like screening chemistry, not natural-product-like.
- Claim it could have supported: three-rung fixed-energy transfer across an independent instrument.

## 10. External validation

**Not performed; correctly preserved.** The final-candidate freeze (Part I, commit `24a4ca1`) fixed the candidate, comparators, populations, endpoint, adapter families, compatibility gate and success rule before any MultiMS2 peak was decoded. The anchor calibration (106 identity-exposed compounds, access record at HEAD `6c6cc4f`, clean tree) failed the gate: best adapter Spearman 0.33/0.66/0.72 and median absolute difference 0.078/0.074/0.060 at 20/40/60 eV, pooled RMSD 0.13 (required 0.80, 0.05, 0.08); the two-parameter adapter also failed. Model-free diagnostics confirm a real incompatibility rather than a defect: even the best rank correlation between MultiMS2 mu and a compound's exposed Orbitrap trajectory at any rung is 0.47 at 20 eV and 0.56 at 40 eV. The frozen rule therefore stopped the study: the 1,297-compound validation population and the 228-compound secondary population remain outcome-unaccessed, and **MultiMS2 is not qualified for the desired external claim**.

**Second source evaluated (outcome-blind): MSnLib** (`MURU_V2_MSNLIB_OUTCOME_BLIND_CENSUS.md`). Orbitrap ID-X Tribrid, flow injection of 8 to 10 compound wells, three HCD scans per precursor: fixed NCE 20, an outcome-adaptive "Assisted" energy (unusable as a rung), fixed NCE 60; first mass 40 m/z as in development; released library spectra are denoised and TIC-selected and cannot be used for mu, so unmerged scans must be re-extracted. Design frame: 53,609 plated compounds; after [M+H]+, parent, overlap, scaffold-new, charge-neutral scaffold, same-well conflict and mass-range rules, 39,238 compounds in 29,562 groups; 402 identity-exposed anchors in 281 groups. It can support at most a **two-rung fixed-NCE transfer claim** and is **not yet qualified**: MS2 triggering at both rungs needs a header pass over about 13 GB of compressed positive mzML, and an anchor ordering gate (where MultiMS2 failed) must pass on an energy coordinate that is plausibly compatible (NCE on a Thermo Tribrid). Data volume and a new external protocol make this a separate, deliberately authorized step, not something to rush at the end of this program.

## 11. Scientific conclusion

1. **What was missing from v1?** Local chemistry beyond elemental totals: atom-type composition and first-shell environments that shift the fragmentation scale.
2. **How much better is v2?** About 10 to 11 percent lower pooled trajectory RMSE than the refitted v1 family on scaffold-held-out development data (7.4 percent on strict structural clusters), with absolute failures falling from 10.3 to 6.3 percent. Not externally confirmed.
3. **What made it better?** Adding a weakly weighted log-count Morgan block to the Tier A ridge; nothing else survived.
4. **Did local structure matter?** Yes, and permuting it removes the gain; about half is composition, half near-neighbour environment; the gain shrinks for structurally novel chemistry.
5. **Did ion-environment features matter?** Alone modestly (2.2 percent, not robust to multiplicity adjustment); almost nothing beyond Morgan.
6. **Is the shared profile still justified?** Yes: scale error dominates, a reproducible shape residual exists but a predicted shape coefficient adds only about 2 percent.
7. **Can MURU identify risky predictions?** No, not with pre-measurement signals tested here.
8. **What remaining errors are probably learnable?** Scale error for chemistry poorly covered by the training library (the fingerprint learning curve is still rising on scaffold splits), and a small predictable shape tilt.
9. **What is measurement or identifiability limited?** A trajectory floor near P1 0.065 from preparation-to-preparation variation, a few percent of heavy compounds whose scale is unidentifiable above E30, and instrument-specific energy transfer, which MultiMS2 shows cannot be bridged by a simple adapter between a QTOF fixed-eV regime and the Orbitrap NCE coordinate.
10. **Is further model complexity worth pursuing?** Not on the current data. The remaining gap to the floor is about 0.05 in P1, the untested ideas are expensive and unlikely to transfer, and the binding constraint is now data: more diverse chemistry measured on the development energy coordinate, and a compatible external source (ideally a prospective dense NCE acquisition with calibration anchors).
