# MURU-WUR-v2 MSnLib Confirmation Study 2: Final Freeze (before the one look)

**Study:** `muru-v2-msnlib-confirmation-2.0`. **Protocol:** `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` (commit 445f563,
sha256 `2b468fc6e5d37fa0de4faacd1ba0cddff5d8fb1abf68965917dc186379d88654`) with Amendment A-1
(`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2_AMENDMENT_A1.md`, commit a097c4d, sha256
`b216db8979c25d1dff7611c0f1affbef4d6d71d4364d07ca4191bb408589e6ac`).
**Machine-readable companion:** `artifacts/wur_v2_confirmation_v2/freeze/freeze_manifest.json`, added in the same commit as
this document; it records the sha256 of every frozen file. The commit that adds both is the freeze commit; validation
access HEAD must equal it (`ConfirmationV2Authority` enforces this).

No replacement-population peak array, intensity, endpoint value or model residual has been decoded or computed at this
commit. Only rung-only header metadata (spectrum ids, selected-ion m/z, fixed-rung labels, scan windows) has been read.

## 1. Full disclosure: confirmation sample 1 was burned

Sample 1 (seed 20261010; 2,000 scaffold groups, 2,690 compounds) was permanently EXPOSED on 2026-09-13, before its one
look: a parser-preflight script selected scans by file position in pooled anchor wells, decoded validation-population
spectra, and printed one validation mu value (`MURU_V2_MSNLIB_CONFIRMATION_POPULATION_EXPOSED.md`). Sample 1 was never
scored. This study replaces its validation population only. It is the last MSnLib attempt.

## 2. Frozen model (unchanged)

| Role | Model | Canonical-JSON sha256 |
|---|---|---|
| Candidate | `V2_TA_MORGAN_JOINT` | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` |
| Primary comparator | `V2_REF_TA_RIDGE` | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` |

Training population 1,325 keys (`81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd`). Both hashes are
recomputed from the committed model files by the freeze manifest builder and again by the authority at the look.

## 3. Frozen rules (unchanged from protocol 1.0; protocol V2 section 2)

- **A0 map:** `E_LCSB = (NCE - a_WUR) / b_WUR`, `a_WUR = -5.95552603907965`, `b_WUR = 0.8618030610784555`; zero
  MSnLib-fitted parameters.
- **Endpoint:** per spectrum `mu = sum(I*m)/sum(I)/m_prec`, all centroid peaks, precursor included, no cutoff, `m_prec`
  = theoretical [M+H]+; per (compound, rung) the median over matched scans across used wells.
- **Rungs:** fixed NCE 20 and 60 (`external_msnlib.fixed_rung_scans`); Assisted scan never used.
- **Matching:** selected-ion m/z within 0.01 Da of [M+H]+; scan window lower <= 40, upper >= [M+H]+ + 1.
- **Support exclusion:** either model's `u = (E/30)/g_hat` outside the profile knot range at either rung; counted.
- **Metrics:** P1 (pooled two-rung RMSE), P1 ratio and difference, MRMSE, median compound RMSE, Q90, Q95, CVaR95,
  AF (compound RMSE > 0.20), AF_max (any rung |error| > 0.30), per rung.
- **Bootstrap:** whole scaffold groups, B = 10,000, seed 20261011, `metrics.cluster_bootstrap`.
- **Decision:** ratio >= 1.00, or AF difference upper 95% > +0.03 → FAILED TO TRANSFER; else ratio upper 95% < 1.00
  with ratio <= 0.95 → PRACTICALLY MEANINGFUL EXTERNAL CONFIRMATION, 0.95 < ratio < 1.00 → MODEST EXTERNAL
  CONFIRMATION; else DIRECTIONALLY FAVORABLE BUT INCONCLUSIVE.
- **Novelty bins:** section 7 below; secondary, interpreted strongly only if the primary confirmation holds.
- **Claim scope:** protocol V2 section 2, qualified by the outcome that produced it.
- **Analysis code:** `scripts/wur_v2_confirmation_v2/11_external_analysis.py` (frozen), same rules as study 1's
  `12_external_analysis.py`; one-look decode `scripts/wur_v2_confirmation_v2/10_one_look.py` (frozen).

## 4. Exclusion registry and eligible universe

- Exposure registry manifest sha256 `ef64541d71be977f65e880c616a8cb895b6c9f3657ff8d8019797ca7d69a9675` (pinned in code
  and test): 31,507 excluded compound keys, 18,402 excluded scaffold groups (design 12b: 23,703 compounds, 15,163 groups).
- Eligible universe: 14,399 scaffold groups (15,535 compounds), list sha256
  `bcdf07dac4a5a84c9063cc4c95e87951ece7e747bc1c22ac78ddb87d8f4e2f1d`, committed with the protocol before the pulse.

## 5. Randomness and the single draw

- NIST Randomness Beacon 2.0, predeclared pulse `2026-09-14T03:00:00.000Z` = chain 2 pulse 1940454, retrieved at
  03:01:23Z; raw response sha256 `6a4eed54b9000c9f6aaa788205788418c83aa4d17dc1dc001f125d4d7d48aa5a`.
- The RSA signature could not be verified: NIST's designated certificate (certificateId = SHA-512 of its DER) has a
  2,048-bit key and the signature is 4,096 bits. The study stopped with no seed and no draw. Amendment A-1, committed
  and pushed before any seed, keeps the same pulse and accepts it on exact timestamp, valid outputValue, certificateId
  binding and an identical second retrieval via the canonical URI (all true).
- Seed `9177898864924233209` = `int(SHA256(bytes.fromhex(outputValue)).hexdigest()[:16], 16)`; beacon output sha256
  `7f5e72641c450df902339e1d272ecec8d47cec83e366a42c92b309df16ac454b`.
- `numpy.random.default_rng(seed).choice(sorted eligible groups, size=2000, replace=False)`, numpy 2.5.2, drawn once at
  03:04:46Z (commit 6433a74). Sampled group sha256 `71a4ec38b488a83c5ed78ba00d1e2b25549046d16c0af5c8f1c83fca51464f5e`;
  sampled compound sha256 `dc898e82a983a15eeea1cfda227660fbc2efe634fc86ac58eb97e692e061b107` (2,154 compounds).
  Record: `artifacts/wur_v2_confirmation_v2/randomness/randomness_and_draw_record.json`.

## 6. Header-only eligibility and the frozen population

Nine authenticated positive-mode ZIPs (sha256 verified at run time; `msnlib_design.ZIPS`), members read in memory,
`scan_headers_rung_only` only (no collision energy value, Assisted scan or MS3+ row returned), no array decoded.

| Stage | Compounds | Scaffold groups |
|---|---|---|
| Sampled | 2,154 | 2,000 |
| Conflict-free dev-range well with a ZIP member | 2,154 | |
| Matched at any fixed rung | 1,816 | |
| **Eligible (both rungs, windows ok)** | **1,794** | **1,691** |

- 1,691 >= the 500-group floor. Largest scaffold group 7 compounds; 1,612 singleton groups.
- Frozen population `artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv` (key, scaffold group, [M+H]+,
  plated wells, SMILES): key sha256 `58f180a0fd15096bd26b7d8deb998be39953c0dee19d2573ba7bfe3b03123be3`, group sha256
  `b5788cab23bacfc4fa89ca66d54f52b7b23436c3467c0744eeba5631cd52e681`.
- Frozen scan allowlist `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv`: 6,004 scans (NCE20
  3,012; NCE60 2,992) in 1,428 files from 1,670 ZIP members read; spectrum manifest sha256
  `2987b6c4fc87a817d8945c85c5625146a2b23a4705f01995a8ce87c49adb8e11`. Every row carries its ZIP, member, file content
  sha256, well, spectrum id, selected-ion m/z, key and rung. Member provenance: `population/required_members.csv`.
- Registry disjointness, well membership, precursor-to-[M+H]+ agreement and live rung labels are re-verified by the
  authority from the ZIP bytes before the access record is written.

## 7. Structural novelty bins (frozen)

Fixed bands gave `>=0.70` only 3 compounds (< 30), so the predeclared quartile fallback applies, over the 2,154 sampled
compounds: Q1 [0, 0.281) 538; Q2 [0.281, 0.319) 535; Q3 [0.319, 0.364) 541; Q4 [0.364, 1] 540
(`freeze/novelty_bins_per_compound.csv`).

## 8. Parser preflight (exposed anchors only)

1,747 anchor spectra already decoded by the original anchor gate, in 433 exposed files, each the precursor of exactly
one admissible census anchor: decoded twice through `AnchorPreflightAuthority`, 0 failures, 0 nondeterministic decodes,
0 non-finite endpoints. The decode log shows every decoded spectrum on the anchor allowlist and in the registry's
decoded set, with no file or content hash in population 2 (`anchor_preflight/anchor_preflight_log_audit.json`).

## 9. Prior anchor-gate mismatch (not revisited)

The absolute-agreement anchor gate failed at A0/A1/A2 by small margins (A0 NCE20 median |Δmu| 0.0501 vs 0.05; A1 pooled
RMSD 0.0811 vs 0.08; A2 NCE20 median 0.0506). This study tests the comparative claim under A0 only.

## 10. Environment

Python 3.13.12, numpy 2.5.2, pandas 3.0.5, rdkit 2026.03.5, scipy 1.18.0, scikit-learn 1.9.0, lxml 6.0.2 (recorded in the
manifest).

## 11. Access procedure and after-access rules

1. `scripts/wur_v2_confirmation_v2/09_verify_and_publish_freeze.py --verify-only`, then without the flag: registers the
   freeze commit locally and pushes `refs/muru-freeze/muru-v2-msnlib-confirmation-2.0` create-only.
2. One final focused pre-access check.
3. `scripts/wur_v2_confirmation_v2/10_one_look.py`: `ConfirmationV2Authority` writes, commits and pushes the access
   record (`refs/muru-access/muru-v2-msnlib-confirmation-2.0`) before any decode; only the 6,004 frozen scans are decoded.
4. `scripts/wur_v2_confirmation_v2/11_external_analysis.py`, unchanged; the four-way decision is reported as it falls.

Population 2 is permanently EXPOSED from the first decode intent onward. No change to the model, comparator, A0 map,
endpoint, population, allowlist, bootstrap, thresholds or novelty bins after this commit. No repair and revalidation.
No redraw. No third MSnLib population.

## 12. Deferred review findings (disclosed, protocol V2 section 4)

Deliberate circumvention of the in-process boundary remains possible and is not claimed to be prevented; rung-only
header indices weakly track MSn tree size; co-isolation of earlier-well compounds is not excluded; the one-look
guarantee relies on the canonical GitHub remote.
