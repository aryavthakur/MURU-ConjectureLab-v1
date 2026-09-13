# MURU-WUR-v2: MultiMS2 external validation protocol

**Status: FROZEN by reference in `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md` Part I; EXECUTED to the anchor gate, which FAILED (Part II). No validation spectrum was decoded.** Original status line: DRAFT r2 (after review adjudication), not frozen. Nothing in this document authorizes access to any MultiMS2 peak, intensity or peak-derived value. It becomes binding only when committed as part of `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md`. Revision r2 incorporates red-team RT-1 and RT-4, leakage L-02 and L-03, and statistical S-04 (`MURU_WUR_V2_REVIEW_ADJUDICATION.md`).

**Source:** MultiMS2 (Rutz, Correia, Zamboni 2026, GigaScience, DOI 10.1093/gigascience/giag069), Zenodo 17250693 v2.0.0 centroided mzML, CC0 1.0. Census: `MURU_V2_MULTIMS2_OUTCOME_BLIND_CENSUS.md`.

## 1. Claim that can be tested

On independent SCIEX ZenoTOF 7600 beam-type CID spectra of [M+H]+ ions at 20, 40 and 60 eV (lab frame), acquired by direct injection of plated standards (NEXUS and Selleck), for compounds whose connectivity and scaffold never entered MURU development, the frozen v2 candidate predicts the precursor-including mean normalized ion mass mu at the three measured energies, through an m/z-aware energy adapter fitted only on identity-exposed calibration anchors, with lower pooled error than the frozen Tier A ridge refit on the same 1,325 development compounds.

This is a **three-rung fixed-energy transfer claim across an independent instrument, laboratory and chemistry**, scoped to low-similarity drug-like screening compounds (median maximum Morgan similarity to development 0.35). It is not a dense onset-to-plateau trajectory claim and not a claim about the historical v1 coordinate system.

## 2. Populations, defined by identity and acquisition headers only

Header data come from `muru.wur_v2.external_mzml.scan_headers` (allowlisted CV terms; no binary array, no intensity summary).

Library membership, released-spectrum counts, replicate counts and any QC field recorded in the census are outcome proxies and are never used to define, exclude, stratify or anchor anything (leakage finding L-02).

- **VALIDATION.** Design-frame step-10 compounds (scaffold-new and identity-new against every exposed MURU population; 2,982 keys, sha256 `1dfc22c2...`) that pass all of:
  - R1: a single plate position whose pool has positive CID files at 20, 40 and 60 eV;
  - R2: in each of the three files, at least one MS2 spectrum whose selected-ion m/z is within 0.05 Da of the theoretical monoisotopic [M+H]+ m/z;
  - R3: no other compound on the same plate position has a theoretical [M+H]+, [M+Na]+, [M+NH4]+, [M+K]+ or [M+H]+ 13C isotope m/z within 0.7 Da of that [M+H]+;
  - R4: every matched MS2 spectrum has a scan window lower limit at most 50 m/z and an upper limit at least [M+H]+ + 1;
  - R5: theoretical [M+H]+ between 70.0 and 1,042.6 m/z (the development precursor range);
  - R6: SMILES parses and every Tier A descriptor and Morgan count computes;
  - R7: the scaffold of the charge-neutralized parent is not a scaffold of any development compound computed either way (N-oxide and quaternary forms cannot pass as scaffold-new; leakage finding L-03).
- **ANCHORS.** MultiMS2 compounds whose connectivity key belongs to the v2 development population with a complete five-rung exposed primary trajectory, passing R1 to R6. Anchors are scaffold-seen by construction and therefore disjoint from every validation scaffold group.
- **SECONDARY.** Design-frame identity-new but scaffold-seen compounds (step 8 minus step 10) passing R1 to R6; reported separately, never pooled.
- Hashes of all three populations are recorded before any decode.

## 3. Endpoint

For compound c and energy e: `mu_ce` = median over matched MS2 spectra of `sum(I m) / sum(I) / m_prec`, all centroid peaks included (no intensity cutoff, precursor included), `m_prec` the theoretical [M+H]+ m/z. A spectrum with no peaks or non-positive total intensity is excluded and counted. Scoring is at the three native energies; no outcome is interpolated.

## 4. Energy adapter (fitted on anchors only)

Model energies are in the LCSB nominal NCE coordinate of development.

- **A1 (primary):** `E_LCSB = k * e * 500 / m_prec`, one parameter `k > 0` (the Thermo normalized-energy definition scales applied energy with precursor m/z).
- **A2 (fallback, only if A1 fails the gate):** `E_LCSB = k * e * (500 / m_prec)^gamma`.
- **Anchor reference:** `mu_ref(E) = Phi*((E / 30) / g*)`, with `Phi*` the frozen candidate profile and `g*` the scale fitted to the anchor's exposed aligned trajectory with `Phi*`. Parameters minimize the anchor sum of squared `mu_obs - mu_ref` on a fixed log grid (`k` in [0.2, 5], 2,001 points; `gamma` in [0, 2], 201 points). Sensitivity: PCHIP of the exposed trajectory for in-range cells only.
- **Compatibility gate (anchors):** at each of 20, 40 and 60 eV, median |mu_obs - mu_ref| <= 0.05 and Spearman >= 0.80; pooled anchor RMSD <= 0.08; at least 30 anchors. A1 is used if it passes; otherwise A2 if it passes; otherwise MultiMS2 is **not qualified** for this claim and no validation spectrum is decoded.
- **Uncertainty:** anchor-cluster bootstrap of the adapter parameters (2,000); the primary result is recomputed at the 2.5 and 97.5 percentile parameters as a sensitivity.
- **Supported range:** a validation cell is unsupported if `u = (E_LCSB / 30) / g_hat` falls outside the frozen profile's knot range for the candidate or the comparator; a compound with any unsupported cell is excluded from the primary analysis and counted.

## 5. Models (all frozen, `artifacts/wur_v2/candidate/`)

Candidate `V2_TA_MORGAN_JOINT`; primary comparator `V2_REF_TA_RIDGE`; secondary `V2_REF_B1_MASS`, `V2_REF_B0_NULL`, and the historical `V1B_RIDGE_TIERA` as frozen at Stage 3. One adapter for all.

## 6. Expected effect, primary rule and power (statistical review S-04, red team RT-1)

**Pre-registered expectation.** Development ratio 0.889 (scaffold-held-out), 0.926 on strict clusters; chemistry-only reweighting to the MultiMS2 scaffold-new structures predicts about 0.92 to 0.93 before any instrument effect, and the energy-coordinate change bears on the mass-dominated part of both models. The plausible external ratio is therefore about 0.92 to 1.00. A null result would not refute the development finding (it would bound its transfer to this regime); a positive result would not confirm the 11 percent.

**Primary estimand.** P1 ratio, candidate `V2_TA_MORGAN_JOINT` over comparator `V2_REF_TA_RIDGE`, on the supported three-rung cells of the VALIDATION population, one frozen adapter for both.

**Uncertainty.** Whole v2 scaffold groups of the validation compounds resampled with replacement, B = 10,000, seed 20261001, P1 of both models recomputed in every replicate, percentile limits.

**Primary rule.** The external claim of Section 1 is **supported** if the upper limit of the two-sided 95 percent interval of the P1 ratio is below 1.00. It is additionally described as **meeting the practical target** if the point ratio is at most 0.95.

**Key secondary (tested only if the primary is supported).** AF non-inferiority: the upper 95 percent limit of AF(candidate) - AF(TA ridge) is at most +0.03, AF being three-rung compound RMSE > 0.20. The tolerance is not re-derived for three rungs; per-rung B0 RMSE is reported for context.

**Power (statistical review simulation on the external group structure, 808 groups).** Type I error about 0.03; power about 1.00 at a true ratio of 0.946, 0.89 at 0.961, 0.60 at 0.973, 0.27 at 0.984; minimum detectable ratio at 80 percent power about 0.965. The final validation count after R1 to R7 is recorded before any decode; if it falls below 400 compounds or 250 groups the study is labelled a limited transfer study and the rule above is unchanged.

**Descriptive, always reported.** MRMSE difference with its own interval, per-energy RMSE, AF_max, Q90, Q95, CVaR95, NEXUS versus Selleck and mass strata, similarity strata, the SECONDARY population, adapter sensitivities (A2 if A1 is used, parameter bounds, PCHIP anchor reference), unsupported-cell count and a sensitivity including those cells, B1, B0 and v1 comparisons.

## 7. One look

`muru.wur_v2.external_guard.AccessGuard` must be constructed before any decode: kind `ANCHOR_CALIBRATION` for anchors, kind `VALIDATION` for the single validation run; each writes its access record before decoding and refuses spectra outside its population; a second VALIDATION guard refuses to construct. After the validation decode MultiMS2 is exposed; no repair-and-revalidate on it.
