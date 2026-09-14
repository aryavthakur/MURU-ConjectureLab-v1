# MURU-WUR-v2 MSnLib External Confirmation: Replacement Study Protocol (V2)

**Identifier:** `muru-v2-msnlib-confirmation-2.0`
**Status:** pre-registered. This file is committed and pushed before the randomness pulse in section 6 exists.
**Supersedes for execution:** `muru-v2-msnlib-confirmation-1.0` (`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL.md`), for the
validation population only. Every scientific rule of that protocol is kept unchanged (section 2).

## 0. Why this is a replacement study

Confirmation sample 1 (seed 20261010, 2,000 scaffold groups, 2,690 compounds) was burned before its formal one look.
On 2026-09-13 a parser-preflight script, meant to re-test the mzML/Numpress parser on already-exposed anchor wells,
selected scans by file position in pooled wells and decoded real MS2 peak arrays of co-plated validation compounds.
One validation mu value was printed to the operator. The whole sample is permanently EXPOSED
(`MURU_V2_MSNLIB_CONFIRMATION_POPULATION_EXPOSED.md`). No P1, ratio, bootstrap or AF was ever computed for it.

This protocol draws one replacement population from what remains of the same outcome-blind MSnLib design frame. It is
not model development: the model, comparator and every analysis rule are the ones frozen before sample 1.

**This is the last MSnLib attempt.** Whatever the result, no third MSnLib confirmation population will be drawn. A
further external claim would need a different source or a prospective acquisition.

## 1. What changed and what did not

Changed, relative to protocol 1.0:
1. the validation population (sections 3 to 5, 7 and 8);
2. the randomness source (section 6: a public beacon pulse, not a chosen seed);
3. the access machinery (sections 9 to 11): the decode boundary was rebuilt after the incident and two rounds of
   independent review (`src/muru/wur_v2/decode_authority.py`, `external_mzml.py`).

Not changed (section 2): candidate, comparator, coefficients, descriptors, Morgan settings, shared profile, A0 energy
map, endpoint, NCE 20/60 rungs, matching tolerances, AF thresholds, P1 definition, bootstrap, practical 0.95
criterion, four-way classification, novelty-bin rule, claim scope.

## 2. Frozen scientific model and rules (unchanged)

| Role | Model | File | Canonical-JSON sha256 |
|---|---|---|---|
| Candidate | `V2_TA_MORGAN_JOINT` | `artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json` | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` |
| Primary comparator | `V2_REF_TA_RIDGE` | `artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json` | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` |

Training population: 1,325 keys, sha256 `81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd`.
Neither model is refit on anything MSnLib.

- **A0 deployment map, zero MSnLib-fitted parameters:** `E_LCSB = (NCE - a_WUR) / b_WUR`,
  `a_WUR = -5.95552603907965`, `b_WUR = 0.8618030610784555`.
- **Endpoint:** per spectrum `mu = sum(I*m)/sum(I)/m_prec` over all centroid peaks of the matched MS2 scan, precursor
  included, no intensity cutoff, `m_prec` = theoretical [M+H]+; per (compound, rung) the median over matched scans
  across the compound's used wells.
- **Rungs:** fixed NCE 20 and NCE 60 only (`external_msnlib.fixed_rung_scans`: first scan of a same-precursor run
  with CE 20; last scan of a run of at least two with CE 60). The Assisted scan is never used.
- **Matching:** selected-ion m/z within 0.01 Da of theoretical [M+H]+; scan window lower limit <= 40 and upper
  limit >= [M+H]+ + 1.
- **Support exclusion:** a compound is excluded from the primary if either model's `u = (E/30)/g_hat` falls outside
  the frozen profile's knot range at either rung (`muru.wur_v2.candidate.supported`); counted, never silently dropped.
- **P1** = pooled two-rung RMSE over all eligible compound-rung cells (`muru.wur_v2.metrics.p1`), both models.
  `P1_ratio = P1_candidate / P1_TierA`. Also reported: P1 difference, MRMSE, median compound RMSE, Q90, Q95, CVaR95,
  AF (compound two-rung RMSE > 0.20), AF_max (any rung |error| > 0.30), per-rung breakdown, coverage and exclusions.
- **Bootstrap:** whole validation scaffold groups, B = 10,000, seed 20261011, `muru.wur_v2.metrics.cluster_bootstrap`,
  every statistic recomputed in every replicate. Group count and size distribution reported.
- **Decision rule, applied literally, in this order:**
  1. point `P1_ratio >= 1.00`, or the whole-group bootstrap upper 95% limit of `AF_candidate - AF_TierA` exceeds
     +0.03 → **FAILED TO TRANSFER**;
  2. otherwise, if the bootstrap upper 95% limit of `P1_ratio` is < 1.00: point ratio <= 0.95 →
     **PRACTICALLY MEANINGFUL EXTERNAL CONFIRMATION**; 0.95 < ratio < 1.00 → **MODEST EXTERNAL CONFIRMATION**;
  3. otherwise (ratio < 1.00 but the upper 95% limit includes 1.00) → **DIRECTIONALLY FAVORABLE BUT INCONCLUSIVE**.
- **Per-rung analysis:** NCE20 and NCE60 separately (candidate RMSE, comparator RMSE, ratio, mean signed residual,
  median absolute residual). A pooled result driven by one rung while the other reverses is discussed prominently.
- **Structural novelty (secondary, descriptive, never an exclusion):** maximum Morgan-count (radius 2, 2048)
  Tanimoto similarity to the 1,325 development compounds; bands `<0.30`, `0.30-0.50`, `0.50-0.70`, `>=0.70`,
  replaced by quartile bins if any band holds fewer than 30 population compounds; frozen before the look;
  interpreted strongly only if the primary confirmation holds.
- **Claim scope:** if positive, *"On an independent, scaffold-separated MSnLib screening-library population measured
  on a Thermo Orbitrap ID-X at fixed HCD NCE 20 and 60, the frozen MURU-WUR-v2 structural scale model outperformed the
  frozen Tier A scale comparator under a fixed zero-parameter deployment energy map"*, always qualified by which of
  the two confirmation outcomes produced it. Never: universal MS/MS prediction, all instruments, adducts, negative
  mode, dense energy trajectories, QTOF transfer, natural products generally, or perfect cross-instrument calibration.
- **Prior anchor-gate disclosure:** the absolute-agreement anchor gate failed at A0/A1/A2 by small margins (A0 NCE20
  median |Δmu| 0.0501 vs 0.05). Not revisited.

## 3. Permanent exposure exclusion registry

`artifacts/wur_v2_confirmation_v2/exposure_registry/`, built header-only by
`scripts/wur_v2_confirmation_v2/01_build_exposure_registry.py`. Registry manifest sha256
**`ef64541d71be977f65e880c616a8cb895b6c9f3657ff8d8019797ca7d69a9675`** (pinned in `decode_authority.py` and in
`tests/wur_v2/test_v2_exposure_registry.py`). Every entry carries its reason codes.

It excludes, deduplicated and expanded to whole scaffold groups (census `scaffold_group_v2`, all SMILES variants,
tautomer-closed): all 2,000 groups of sample 1; every compound whose MSnLib spectra were decoded in any past event
(same-well ions within 0.7 Da, same-plate carryover ions within 0.01 Da and, for multiply charged, cluster, solvent and
in-source forms, within 5 ppm); owners of the three printed spectra in any library (5 ppm); same-library owners of
unexplained decoded spectra (3 ppm); every compound co-plated in a decoded well; every compound plated in any of the
2,811 study-1 wells whose full headers were parsed (those headers carry the outcome-adaptive Assisted energy and MS3+
fragment m/z); all MSnLib census and anchor-gate anchors; the MultiMS2 anchors; every previously exposed MURU
population (LCSB, WUR, v2 development, ENTACT raw-mix lists and others); and two precautionary exclusions from the
registry review (enamine 5008 H11-H14; IZSBMDHDBLUZOI).

Counts: 31,507 excluded compound keys and 18,402 excluded scaffold groups across all sources; of the design-12b frame,
23,703 compounds in 15,163 groups. Decode events reconstructed and verified against their records: buggy preflight
3,366 spectra (561 files), fixed preflight rerun 1,816 (472 files), anchor gate attempt 2 1,935 (470 files), attempt 1
4 requests.

## 4. Deferred review findings and disclosed residuals

The two pre-sampling review rounds closed every CRITICAL finding. These are documented, not fixed, because none gives
a premature path to a validation outcome through ordinary use of the committed code:
- deliberate circumvention stays possible: a new stdlib or third-party decoder for bytes on disk, in-memory mutation
  of the boundary modules, setting the decode permit by hand, or faking test mode. The static choke-point test flags
  every known spelling in committed code; uncommitted code is out of its reach;
- the rung-only header reader returns spectrum ids and indices, whose gaps weakly track the size of the data-dependent
  MSn tree (measured rank correlation 0.08-0.16 with anchor mu). Header metadata is used for population construction
  as protocol 1.0 already allowed; the Assisted energy and MS3+ precursors are never returned for population 2;
- co-isolation of earlier-well compounds inside a decoded spectrum's 1.2 m/z window is not excluded (no measured
  carryover presence for remaining-pool compounds);
- the one-look guarantee assumes the canonical GitHub remote `github.com/aryavthakur/MURU-ConjectureLab-v1`.

## 5. Replacement eligible universe

The design-12b frame of the census (39,238 compounds, 29,562 scaffold groups; key sha256
`8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e`, group list sha256
`809f14c4d2528661be39e169aacf67b8618f736db6d1d17afd2a7914c67f07b9`) minus every registry group.
Built by `scripts/wur_v2_confirmation_v2/02_build_eligible_universe.py`, committed with this protocol:

- `artifacts/wur_v2_confirmation_v2/population/eligible_scaffold_groups.txt` (sorted, one group per line)
- **14,399 eligible scaffold groups**, 15,535 compounds
- eligible group list sha256 (sorted, newline-joined, no trailing newline):
  **`bcdf07dac4a5a84c9063cc4c95e87951ece7e747bc1c22ac78ddb87d8f4e2f1d`**
- file sha256 `3c6b57eaef63f84ac43b03451689bff25871bbe58b1469d801a068df18800e8a`

## 6. External randomness (not chosen by us)

**Source:** NIST Randomness Beacon 2.0.
**Predeclared pulse:** the pulse with `timeStamp` **`2026-09-14T03:00:00.000Z`** (epoch ms 1789354800000).
**Request:** `https://beacon.nist.gov/beacon/2.0/pulse/time/1789354800000`, made once, after this protocol commit is
pushed to origin and after that instant. Transient network errors may be retried on the same URL only.

Rules (implemented in `scripts/wur_v2_confirmation_v2/03_randomness_and_draw.py`):
1. the returned `pulse.timeStamp` must equal `2026-09-14T03:00:00.000Z` exactly; otherwise STOP;
2. save the raw response and the certificate from `https://beacon.nist.gov/beacon/2.0/certificate/<certificateId>`;
3. verify the RSA-SHA512 `signatureValue` over the NIST 2.0 pulse serialization, and that `outputValue` equals
   SHA-512 of that serialization followed by the signature bytes; if either fails, STOP;
4. `seed = int(hashlib.sha256(bytes.fromhex(pulse.outputValue)).hexdigest()[:16], 16)`;
5. record the raw response sha256, the pulse fields, the verification result, SHA-256 of the output bytes, and the seed.

No other pulse is retrieved for seeding and no seed is ever chosen among alternatives. If the pulse is unavailable, has
a different timestamp, or fails verification, the study STOPS; a different pulse may be used only after a separately
committed and pushed amendment made before any replacement-population data is seen.

Verifier self-test, disclosed: before this protocol was committed the verifier was run once on the public NIST chain 1
pulse 1 (`2018-07-23T19:26:00.000Z`, stored in `artifacts/wur_v2_confirmation_v2/randomness_verifier_selftest/`);
signature and outputValue both verified. That pulse was never used for any seed.

## 7. The single replacement draw

`numpy.random.default_rng(seed).choice(np.array(sorted_eligible_groups, dtype=object), size=2000, replace=False)`
with numpy 2.5.2, where `sorted_eligible_groups` is the committed list of section 5. One draw, no reroll, no
inspection-based preference. Recorded: eligible-list hash, the randomness record, the seed, the draw order, the
sampled-group hash and the sampled-compound hash (the 12b compounds of the sampled groups). Committed immediately.

## 8. Header-only eligibility

Using only the nine authenticated positive-mode Zenodo mzML ZIPs (sha256 values in `muru.wur_v2.msnlib_design.ZIPS`),
read as members in memory, never extracted:

1. wells of each sampled compound that are free of the census 12a isolation conflicts (another co-plated compound's
   adduct within 0.7 Da, or the same parent formula) and whose [M+H]+ lies in 70.0-1042.6 (`msnlib_design.conflict_free_dev_wells`);
2. one acquisition per well by the study-1 tie-break (production variant, latest run date, plain name over a
   resubmission-suffixed one, then name) (`msnlib_design.zip_members`);
3. headers only through `external_mzml.scan_headers_rung_only` (fixed-rung MS2 rows; no collision energy value, no
   Assisted scan, no MS3+ row is returned); no binary array is decoded;
4. `external_msnlib.match_compounds` and `external_msnlib.eligible`: both rungs matched with window ok and no
   window-failing matched scan;
5. outputs: surviving compound, scaffold-group and scan manifests (population CSV with each key's plated wells, the
   frozen scan allowlist with ZIP member, content sha256, spectrum id, selected-ion m/z and rung), attrition table.

**Floor:** if fewer than 500 scaffold groups survive, STOP before any outcome access.

## 9. Parser preflight on exposed anchors only

`AnchorPreflightAuthority` authorizes only re-decodes of spectra already decoded by the original anchor gate
(registry `decoded_spectra.csv`, event `E_anchor_gate_attempt2`) whose precursor is within 0.01 Da of a census anchor
plated in that well, in files whose content sha256 is in the registry's exposed files. Checks: Numpress/zlib decode
repeated twice and bit-identical, array lengths equal `defaultArrayLength`, finite endpoint, precursor presence. The
log lists every decoded (file, spectrum, anchor key); outputs are counts and pass/fail only. No population-2 file is
opened.

## 10. Final freeze

`MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md` and `artifacts/wur_v2_confirmation_v2/freeze/freeze_manifest.json` freeze the
candidate/comparator hashes, the population, group, scan-manifest and registry hashes, ZIP and member provenance,
environment, A0, endpoint, metrics, bootstrap, decision rule, novelty bins, prior anchor mismatch and this protocol,
with full disclosure of the burned sample 1. Committed on a clean tree. `decode_authority.verify_freeze_candidate` runs
every look-time check read-only; only if it passes does `decode_authority.publish_freeze` register the freeze commit
and push `refs/muru-freeze/muru-v2-msnlib-confirmation-2.0` (create-only). Validation-access HEAD must equal that
freeze commit. One final focused pre-access check follows.

## 11. The single validation look

`ConfirmationV2Authority` re-runs every freeze check, re-reads every allowlisted header, then writes, fsyncs, commits
and pushes `refs/muru-access/muru-v2-msnlib-confirmation-2.0` and ledger entries before any validation array is decoded.
Only frozen allowlisted scans are decoded. From the first decode intent onward, population 2 is permanently EXPOSED
whatever happens. If construction fails after the access record exists but before any decode intent
(`ATTEMPT_FAILED_NO_DECODE`), the study halts and may resume only under a committed amendment with the same freeze.
If a crash follows decoding, only the same frozen allowlist may be decoded again under an amendment.

The frozen analysis of section 2 is then applied without any change, and the four-way classification is reported.

## 12. Stop

If positive, MURU-v2 development closes. If negative, the failure is preserved and this population is closed. No
third MSnLib replacement sample.
