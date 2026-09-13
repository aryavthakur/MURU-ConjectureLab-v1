# MURU-WUR-v2: MSnLib two-rung external validation protocol

**Status:** FROZEN by `MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md` Part III before any MSnLib peak is decoded. Authorization from the user (2026-09-13): anchors-first; if the anchor gate passes, stop and ask before the validation download and the one look.
**Source:** MSnLib (Brungs et al. 2025, Nat Methods, DOI 10.1038/s41592-025-02813-0), Zenodo 15683784 mzML zips (CC BY 4.0), plate metadata github.com/merlin-ms/mass-spectral-library-network @ ed7f85f. Census: `MURU_V2_MSNLIB_OUTCOME_BLIND_CENSUS.md`.
**Candidate and comparators:** unchanged from Part I (`V2_TA_MORGAN_JOINT`; primary comparator `V2_REF_TA_RIDGE`; secondary B1, B0, historical v1).

## 1. Claim

On independent Thermo Orbitrap ID-X Tribrid HCD spectra of [M+H]+ ions at fixed normalized collision energies 20 and 60, acquired by flow injection of plated commercial screening compounds whose connectivity and scaffold never entered MURU development, the frozen v2 candidate predicts precursor-including mean normalized ion mass mu at both rungs, through an energy adapter fitted only on identity-exposed anchors, with lower pooled error than the frozen Tier A ridge. **A two-rung fixed-NCE transfer claim**, scoped to commercial screening chemistry; not a trajectory claim.

## 2. Wells, scans and rungs (identity and allowlisted headers only)

- Well eligibility: a positive-mode well in which no other plated compound has an [M+H]+, [M+NH4]+, [M+Na]+, [M+K]+, [M-H2O+H]+ or 13C [M+H]+ ion (or a permanent-cation [M]+) within 0.7 m/z of the compound's [M+H]+ and no same-well isomer (census rule 12a). Only conflict-free wells are used.
- Injection per well: the Zenodo 15683784 mzML member of the production variant (`100AGC_60000Res_` for MCEBIO) or else the latest run date.
- Fixed rungs: within a run of consecutive MS2 scans sharing one selected-ion m/z, the first scan with collision energy 20 is rung 20 and the last scan (run of at least two) with energy 60 is rung 60; the Assisted scan is never used (`muru.wur_v2.external_msnlib.fixed_rung_scans`).
- Matching: selected-ion m/z within 0.01 of the theoretical monoisotopic [M+H]+; every matched scan must have scan window lower limit <= 40 and upper limit >= [M+H]+ + 1; a compound needs at least one matched scan at both rungs across its used wells.
- Library membership, the authors' detected-compound parquet and any QC field are never used to define, exclude or stratify anything.

## 3. Endpoint

Per spectrum `mu = sum(I m) / sum(I) / m_prec`, all centroid peaks of the mzML scan (precursor included, no cutoff), `m_prec` the theoretical [M+H]+. Per (compound, rung): median over all matched scans across the compound's used wells. Scored at the two native rungs; no outcome interpolation.

## 4. Anchors and adapter

- **Anchors:** the 402 identity-exposed v2 five-rung compounds of the census (`msnlib_census.json` anchors.design.v2_dev_five_rung, conflict-free well, development m/z range) that pass section 2 in their downloaded wells.
- **Reference:** `mu_ref(E) = Phi*((E/30)/g*)`, frozen candidate profile, `g*` fitted to the anchor's exposed aligned trajectory.
- **Families, in order, first passing is used:** A0 `E_LCSB = (NCE - a_WUR)/b_WUR` with the frozen Stage 1 map (no free parameter; assumes ID-X NCE equals IQ-X NCE); A1 `E_LCSB = k NCE` (k in [0.5, 3], 1,001 log points); A2 `E_LCSB = a + b NCE` (a in [-40, 40], 161 points; b in [0.3, 3], 161 log points). Least squares of `mu - mu_ref` over anchor cells.
- **Gate:** at each rung median |mu - mu_ref| <= 0.05 and Spearman >= 0.80; pooled RMSD <= 0.08; at least 30 anchors. If no family passes, MSnLib is not qualified and no validation spectrum is decoded.
- **Uncertainty:** anchor scaffold-group bootstrap of the chosen family's parameters (2,000); validation sensitivity at the 2.5 and 97.5 percentiles.

## 5. Validation population and success rule (applied only after a separate authorization)

- Population: census design-frame step 12b compounds (scaffold-new, charge-neutral scaffold-new, conflict-free well, [M+H]+ in 70.0 to 1,042.6; 39,238 keys in 29,562 groups), restricted to a seeded random sample of **2,000 v2 scaffold groups** (numpy default_rng seed 20261010, sampling without replacement from the sorted group list) to bound the download; then section 2 header rules; compounds whose Tier A descriptors or Morgan counts fail are excluded and counted. The sample is drawn from identity only before any validation file is downloaded.
- Primary: P1 ratio (candidate / TA ridge) on supported two-rung cells; whole-scaffold-group bootstrap, B = 10,000, seed 20261011, P1 recomputed per replicate; **supported if the 95 percent upper limit < 1.00**; practical target if the point ratio <= 0.95. Key secondary (only if supported): AF difference upper limit <= +0.03, AF = two-rung compound RMSE > 0.20. Supported range: a compound is excluded from the primary if either model's `u` falls outside the frozen profile knots at either rung (counted; sensitivity including them).
- Pre-registered expectation: plausibly 0.90 to 1.00 (development 0.889, strict clusters 0.926; rungs 20 and 60 sit near the low and middle of the development coordinate).
- One look, guard, prohibitions: as Part I sections 4 and 6.
