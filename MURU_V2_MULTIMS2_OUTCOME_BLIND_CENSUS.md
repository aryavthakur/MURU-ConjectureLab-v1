# MURU v2: MultiMS2 outcome-blind identity, metadata and acquisition census

Date: 2026-09-12. Status: census only. No MultiMS2 peak, intensity or peak-derived value was read. MultiMS2 stays in exposure class "potential-future-external-not-outcome-accessed", with the disclosures in section 8.

Machine-readable output: `artifacts/wur_v2/external_census/multims2_census.json` (attrition for every step, survivor key lists, population hashes, and a provenance row for every fetched URL with its file, size and sha256). Scripts: `scripts/wur_v2/census/multims2_fetch.py` (a logged fetcher with a denylist) and `scripts/wur_v2/census/multims2_census.py` (deterministic, about 60 s). Downloaded metadata (40 MB, gitignored) is in `data/external/multims2_metadata/`.

## 1. Sources and versions

| Resource | Identifier | Version used |
|---|---|---|
| Paper | Rutz, Correia, Zamboni 2026, GigaScience, DOI 10.1093/gigascience/giag069 (PMC13312951, PMID 42271568) | NCBI BioC full text. I read the methods, Table 1 and data availability. I read the QC section only through a keyword filter. |
| Code and metadata repository | github.com/zamboni-lab/MultiMS2 | commit 659bd9b (2026-08-24). `metadata/` last changed at ae66078 (2025-10-04). `data/` last changed at 104eb88 (2026-07-08). Tag 0.0.1 is b6e1db2. `.zenodo.json` says version 0.0.2. |
| mzML release | Zenodo 17250693, DOI 10.5281/zenodo.17250693 (concept 10.5281/zenodo.14218308) | v2.0.0 of 2025-10-02: 33 centroided mzML zips, 6.82 GB. I used the API listing and the zip directory previews only. The earlier v1.0.0 (14218309) had 6 zips. |
| Processing archive | Zenodo 17417089, DOI 10.5281/zenodo.17417089 | v0.0.1 of 2025-10-22: a single repository zip (23.8 MB) that includes the MGF. Metadata cannot be separated from peaks there, so I did not download it. |
| MassIVE | MSV000099369, DOI 10.25345/C5GQ6RF85 | PROXI record plus the GNPS2 datasetcache file listing (22,886 rows). MassIVE reports 22,903 files and 41.0 GB. |

The MultiMS2 numbers were checked against primary files rather than taken from summaries. The released identity tables contain 43,728 spectra. They give 2,899 distinct InChIKey first blocks, and also 2,899 after v2 parent normalization (the two sets differ by 4 keys each way). There are 4,210 compound-adduct pairs, 17,170 compound-adduct-method-energy combinations and 2,924 full InChIKeys. All of these match the paper's Table 1.

## 2. License

Data are CC0 1.0. This is stated in `data/LICENSE`, in the "Data License (CC0)" section of the repository `LICENSE`, in the Zenodo 17250693 v2.0.0 metadata (`cc-zero`) and in the paper's data availability statement. Code is MIT (repository `LICENSE`; Zenodo 17417089). Two caveats: Zenodo mzML v1.0.0 was CC-BY-4.0, and the article itself is CC BY. The CC0 claim is verified for the current data releases.

## 3. Instrument, activation, energies, ions

- **Instrument:** SCIEX ZenoTOF 7600 with an Agilent Infinity II stack. Confirmed by the paper, the MassIVE CV term MS:1003293 and the mzmine batch (`ZENOTOF7600`, `qTof`). Every library record says INSTRUMENT qTof and IONSOURCE DI-ESI.
- **Sample introduction:** direct injection of 5 uL of pools of about 10 compounds, 0.6 min per run, one separate injection per energy.
  - MS1: TOF 50 to 1,500 m/z.
  - MS2 selection: IDA of up to 2 precursors per cycle, 50 mDa target tolerance, 2 s exclusion, dynamic background subtraction.
- **CID:** 20, 40 and 60 V (paper). The README says "eV" and the file names use `ev` or `eV`. For singly charged precursors the lab-frame energy in eV equals the voltage numerically. These are not NCE values, so transfer from MURU's Orbitrap NCE ladders needs a pre-registered energy mapping.
- **EAD:** 12, 16 and 24 eV electron kinetic energy (files labelled `KE`), 30 ms.
- **Collision-energy spread:** not mentioned in the paper, README or processing code. Every library record carries one CE value (0 multi-valued rows). Whether the instrument method used CE spread cannot be confirmed without opening mzML headers.
- **Ion coverage:** positive CID has 25,523 released records across 136 adduct labels. [M+H]+ accounts for 18,173 records from 2,136 compounds.
  - 290 positive CID compounds have only other adducts.
  - Notable other adducts, by compounds: [M+O+H]+ 97, [M+Na]+ 59, [M-H2O+H]+ 56, [M]+ 44, [M-NH3+H]+ 36, [M+2H]2+ 27, [M+K]+ 25, [M+NH4]+ 13. The full table is in the JSON.

## 4. Energy completeness per collection (positive CID)

Rungs are counted for the same connectivity key and the same ion within one collection. No released compound needed rungs from two collections to be complete.

| Collection | Plated pos. compounds | Released [M+H]+ compounds | Released 20/40/60 | 20/40 | 20/60 | 40/60 | Design frame (files) 20/40/60 | Design 40/60 |
|---|---|---|---|---|---|---|---|---|
| NEXUS | 4,485 | 2,122 | 1,491 | 1,725 | 1,587 | 1,676 | 3,167 | 3,335 |
| Selleck | 922 | 11 | 11 | 11 | 11 | 11 | 922 | 922 |
| MSMLS | 564 | 6 | 0 | 0 | 0 | 6 | 0 | 564 |

- **MSMLS has no positive 20 V CID.** Four sources agree: the README table, the Zenodo file list (no `msmls_mzml_centroided_pos_cid_20.zip`), the MassIVE listing (84 files at 40 V and 84 at 60 V, none at 20 V) and the released records (40 and 60 only).
- **NEXUS positive CID is not complete in the deposit.**
  - Sub-plate Q3 has only 39, 38 and 66 of its 96 wells at 20, 40 and 60 V.
  - Sub-plates P5, Q1, Q2 and Q4 each have 5 to 14 wells with 20 and 40 V but no 60 V file.
  - Zenodo zip listings and MassIVE agree file for file (the only difference is 5 blank files that sit in the NEXUS 20 V zip).
- **Selleck and MSMLS are badly under-represented after QC.** Only 100 of 922 plated Selleck compounds and 26 of 564 MSMLS compounds survive in any mode, against 2,799 of 4,485 for NEXUS. These are counts of released records (see the censoring disclosure in section 8).

## 5. Attrition

I censused two frames.

- **LIBRARY:** the released, QC-filtered library, read from the five peak-free GNPS batch identity tables.
- **DESIGN:** the pre-acquisition positive plate metadata joined by pool position to the public file listing. This frame is outcome-free, but ion formation and IDA triggering are unknown in it.

"Groups" means v2 primary scaffold groups (`scaffold_group_v2`). Records are released spectra. At steps 8 to 11, the records column counts rung spectra of survivors.

### 5a. LIBRARY frame, primary chain: three rungs 20/40/60 V

| Step | Compounds | Records | Groups | Notes |
|---|---|---|---|---|
| 1 All released compounds | 2,899 | 43,728 | 1,636 | NEXUS 2,799, Selleck 100, MSMLS 26 |
| 2 Positive CID | 2,426 | 25,523 | 1,429 | NEXUS 2,380, Selleck 42, MSMLS 12 |
| 3 [M+H]+ | 2,136 | 18,173 | 1,267 | NEXUS 2,122, Selleck 11, MSMLS 6 |
| 4 All of 20/40/60 V, same key and ion, one collection | 1,502 | 15,016 | 939 | NEXUS 1,491, Selleck 11. Between 1 and 130 QC-passing replicate scans per rung |
| 5 Identifiable parent structure | 1,502 | 15,016 | 939 | All CONSISTENT: SMILES parses, and the SMILES InChIKey equals the recorded InChIKey and the InChI-derived key. 9 keys draw their rungs from more than one stereoisomer |
| 6 Centroid data accessible (listings) | 1,502 | 15,016 | 939 | All 15,016 source files are listed as centroided mzML and mzXML on MassIVE, and the matching Zenodo zip exists. No raw .wiff and no profile mzML is public |
| 7 Precursor-preserving endpoint | 1,502 | 15,016 | 939 | Status flag only, not a filter. The library QC censors precursor-rich spectra and the MS2 window is undocumented (section 6) |
| 8 No exact connectivity overlap with any exposed MURU population | 1,378 | 13,841 | 863 | 124 removed |
| 9 No normalized parent overlap | 1,378 | 13,841 | 863 | 0 further removed (parent plus canonical-tautomer normalization on 1,625 MURU SMILES) |
| 10 No primary scaffold overlap with v2 development groups | 1,165 | 11,419 | 808 | NEXUS 1,161, Selleck 4 |
| 11 Independent structural groups | 1,165 | 11,419 | 808 | 701 groups of size 1 (701 compounds), largest group 28, 12 acyclic |

Step 8 overlaps by population (the same key can hit several populations):

| Population | Overlapping keys |
|---|---|
| LCSB-DEV | 38 |
| WUR-DEV-ANALYSIS | 47 |
| WUR-DEV-HOLD | 6 |
| WUR-SEALED | 23 |
| LCSB-CONFIRMATION | 14 |
| WUR-NEG-DEV | 2 |
| WUR-NEG-D6-EXCLUDED | 2 |
| LCSB-NEG | 33 |
| LCSB-RAW-MIXES | 6 |

Additional populations from the primary chain:

- **Identity-new but scaffold-seen:** 213 compounds, 2,422 rung records, 55 groups (30 of size 1).
- **Sensitivity checks on the 1,165 scaffold-new compounds:**
  - Scaffold-new against every SMILES-bearing exposed MURU record, not only v2 development: 1,142 compounds, 804 groups.
  - Strict similarity: 35 of the 1,165 have a maximum Morgan-count Tanimoto of 0.55 or more to some v2 development compound. The median maximum is 0.35. Below 0.55 there remain 1,130 compounds in 784 groups.
- **Precursor m/z of the scaffold-new survivors** (computed from structure): [M+H]+ runs from 126 to 847, so all are inside the documented MS1 range.

### 5b. LIBRARY frame, two-rung chains

- **Two-rung subsets at step 4**, distinct keys complete within a collection: 20/40 gives 1,735 compounds, 20/60 gives 1,598 and 40/60 gives 1,691. Two keys are complete in two collections independently.
- **Full 40/60 chain** (the chain that admits MSMLS):

| Step | Compounds | Groups |
|---|---|---|
| 4 | 1,691 | 1,052 |
| 5 | 1,691 | 1,052 |
| 8 | 1,551 | 966 |
| 9 | 1,551 | 966 |
| 10 | 1,321 (NEXUS 1,314, Selleck 4, MSMLS 3) | 907 (779 of size 1) |

  The identity-new but scaffold-seen population in this chain is 230 compounds in 59 groups.

### 5c. DESIGN frame (outcome-free upper bound)

Three rungs: 5,455 plated positive keys (6,211 rows) go to the following steps.

| Step | Compounds | Groups | Notes |
|---|---|---|---|
| 2 | 5,345 | 2,870 | Any positive CID file for the pool. 11 NEXUS positions have none |
| 3 | 5,345 | 2,870 | Not applicable in this frame |
| 4 | 3,955 | 2,215 | NEXUS 3,167, Selleck 922. 4 compounds complete only by combining two plated positions |
| 5 | 3,954 | 2,214 | 1 row has an empty structure. 34 keys changed by salt or charge normalization |
| 8 | 3,712 | 2,105 | |
| 9 | 3,711 | 2,104 | 1 tautomer match, JLGOGFIHBRJQHY |
| 10 | 2,982 | 2,006 | NEXUS 2,474, Selleck 508 |
| 11 | 2,982 | 2,006 | 1,727 groups of size 1 |

- **Identity-new but scaffold-seen:** 729 compounds in 98 groups.
- **Same-pool precursor conflicts among the step-10 survivors:** 78 within 50 mDa and 138 within 0.7 Da.
- **Precursor m/z:** 44 survivors have [M+H]+ below 100, and 8 fall outside 50 to 1,500.
- **Two-rung 40/60 design chain:** step 10 has 3,279 compounds in 2,198 groups (MSMLS 162).
- **Containment check:** all 1,165 library-frame step-10 survivors are inside the design-frame step-10 population. All 11,343 released positive file-compound pairs map to a pool whose plate metadata contains that compound.

### 5d. Population hashes

Each hash is sha256 over the sorted keys joined by "\n", with no trailing newline.

| Population | n | sha256 |
|---|---|---|
| LIBRARY 3-rung step 8 (and step 9, identical) | 1,378 | de3d0bc17f80533e39db9fc3e55b79f7f376a28cf2164abae7c9753c1bbb6b56 |
| LIBRARY 3-rung steps 10 and 11 (scaffold-new) | 1,165 | 5d7bb8c16f3f2da942b0253b74978725168ea1d388730e291c5bbe04c86866eb |
| LIBRARY 3-rung identity-new, scaffold-seen | 213 | 615e6b9c435eff722f897013581741bc5150905fae26bdd774845b8e19cf683f |
| LIBRARY 40/60 step 8 | 1,551 | 2e9fc3fa9766aa1b212f4003715a30fd04ae214d355e0b1f5880cd61df8ca17a |
| LIBRARY 40/60 steps 10 and 11 | 1,321 | d5ce3ebf2f737cf817b282d79d610fc60781dc30580409dedaa378b3ad2c68a4 |
| DESIGN 3-rung step 8 | 3,712 | 26d0ae6be7e4fac2174699259ddea0025297eeae7fee866497a8ee8adb11ed9b |
| DESIGN 3-rung steps 10 and 11 | 2,982 | 1dfc22c2b74759389f30bdd6f2041d2cb7543e1e377c839da6788c29b66f5ea9 |
| DESIGN 40/60 steps 10 and 11 | 3,279 | d323aee8d2ae6f4faba846eb8c8f825e34933059f83a112bfc4224f31e7242cd |

Step 11 removes no compound, so its hash equals step 10's.

The input exposure manifest was checked first. All 9 population hashes recompute (a 1,757-key union). The stored v2 `scaffold_group` values reproduce 1,325 of 1,325 under `scaffold_group_v2`.

## 6. Precursor window and censoring (step 7)

- **MS2 scan range and low-mass start:** not documented. The paper states only the MS1 range (50 to 1,500 m/z). The README, the mzmine batches and the notebooks do not set or state an MS2 window. A QTOF collision cell has no trap-type low-mass cutoff, but the method's MS2 start m/z is unknown.
- **Precursor isolation:** the Q1 isolation width is not documented. mzmine's chimeric check used a 0.6 Da isolation tolerance and flagged chimeric spectra without removing them.
- **Precursor peak removal:** none. The batch has no removal step, and "Export explained signals only" is false.
- **QC that censors outcomes:** applied after export by `notebooks/filter_spectra_consistent.py`, matching the paper's QC section. The filters are:
  - precursor MS1 height of at least 1,000
  - precursor purity of at least 0.9
  - at least 3 signals (`num_peaks`)
  - explained intensity of at least 0.4
  - explained signals of at least 0.05
  - replicate selection at 0.8 and 0.4 of the group maximum
  - at least 2 modalities per compound-adduct pair (the paper and README say 2; the code default is 3)
- **Consequence:** the three signal and explained-intensity filters preferentially drop spectra with few signals, which at 20 V are the precursor-dominated ones. The modality rule can then drop the compound-adduct pair altogether. Released-library membership is therefore selected on fragmentation outcome, and a precursor-survival or mean-mass endpoint built from released records would be biased. I could not determine without opening spectra (mzML scan headers) whether the MS2 window keeps the precursor and low-mass fragments.

## 7. Open questions

1. MS2 m/z window and CE spread. Both can only be resolved from mzML header CV parameters, which sit in files that also carry peaks, or from the authors. A header-only reader belongs in a frozen post-freeze protocol.
2. Does mzmine's `num_peaks` and explained intensity include the precursor peak? This sets how strongly the QC censors precursor-rich spectra.
3. Was `min_modalities` 2 or 3 in the released run? The paper and README say 2; the code default is 3.
4. Do the missing NEXUS Q3 and 60 V acquisitions exist but went undeposited?
5. The design frame is only an upper bound. Whether [M+H]+ was formed and IDA-selected at each energy in pools of about 10 is an MS1-level acquisition event. The MassIVE `ccms_metadata/*.mzML.scans` per-scan tables might settle it, but I did not open them because they may carry intensity summaries.
6. Replicate scans per rung (1 to 130) will need a pre-registered aggregation rule.
7. A mapping from Orbitrap NCE to lab-frame volts is needed. The scaffold-new population is also 99.7% NEXUS natural-product-like screening compounds, so any claim must be scoped to that chemistry.

## 8. Outcome-blindness statement

No spectral peak, intensity, fragment count, entropy, similarity or other per-spectrum quality value was downloaded, opened, parsed or computed.

**Refused or not downloaded:**
- `data/multims2_spectra.mgf` (refused by the denylist)
- all 33 Zenodo mzML zips
- the Zenodo 17417089 repository zip
- all MassIVE mzML and mzXML files, the `.mzML.scans` tables, `params.xml` and `summary.tsv`

**The GNPS PARTITION TSVs were downloaded only through a guarded path:**
- A range request first checked the header against the 29 peak-free columns emitted by `convert_spectra_to_tsv.py`.
- Every row was then checked to have exactly 29 fields.

**Columns dropped on load without inspecting values:** `LIBQUALITY`, a quality flag that the generating code writes as the constant "1", and `SELFIES`, which is redundant. The plate metadata tables contain no outcome columns.

**Outcome-adjacent information that was unavoidably seen, all aggregate or QC-conditioned:**
- Which compound, adduct and energy combinations have a QC-passing released spectrum, including per-energy record counts. For example, 20 V has fewer positive CID records than 40 or 60 V.
- Per-rung replicate counts.
- The README's filter-cascade spectrum counts.
- Two aggregate passages in the paper's QC section: 676 compounds appear in all positive modalities, and the explained-intensity fraction was higher for CID than for EAD.

None of this is a per-compound peak value, but library membership is a coarse QC outcome. Any future validation should define its population from the design frame, or from MS1 or precursor-selection events, not from library membership.

**Provenance incident:** seven Zenodo zip-listing previews were first saved under colliding local names. They were re-fetched under collection-qualified names, and the superseded rows are marked in the log. Four early fetches (GitHub repo and tree, the MassIVE dataset query, and FTP listing attempts that timed out) went through curl before the logger existed. All of them are recorded in the JSON.

## 9. Preliminary qualification

**Size and independence.** The released library alone clears the stated bar by a wide margin:

| Population | Compounds | Independent scaffold groups |
|---|---|---|
| Released library, 3-rung, identity-new and scaffold-new | 1,165 | 808 |
| Same, excluding compounds within 0.55 Tanimoto of v2 development | 1,130 | 784 |
| Design frame upper bound | 2,982 | 2,006 |

The instrument (SCIEX QTOF beam CID in volts), the laboratory and the compounds are all independent of MURU's exposed data.

**Verdict: conditionally qualified.**

- **Full claim:** a "three-rung fixed-energy transfer across an independent instrument" claim is supportable only through outcome-independent re-extraction from the public centroided mzML. That re-extraction must use the design frame, include compounds on MS1 or precursor-selection evidence alone, and confirm the MS2 window and CE spread from file headers under a frozen protocol.
- **Released records used as they are:** these support only a narrower claim, transfer within a subpopulation that passed fragment-count QC. That narrower claim cannot support a precursor-preserving endpoint, and the 20 V rung is the most affected.
- **Scope of either claim:** effectively NEXUS-only chemistry, on a lab-frame voltage ladder rather than NCE.
