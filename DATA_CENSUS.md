# DATA_CENSUS.md

Generated 2026-08-11 23:20 UTC. Source of every number: `artifacts/trajectories.parquet`, built in this run.

## Provenance

| Item | Value |
|---|---|
| Source repository | https://github.com/MassBank/MassBank-data |
| Release tag | `2026.03` |
| Commit (tag dereferenced) | `705afb7bccc3b2c42410a744eef73674716a60ef` |
| Contributor directory | `LCSB` |
| Files acquired | 5,582 |
| Bytes acquired | 25,501,603 |
| Corpus digest (SHA-256 over path+hash pairs) | `27f6499ec4672191039e91df78115e3d8384ff3822f287b0590b4507f4404039` |
| Manifest | `artifacts/MANIFEST_massbank.json` |

## Reconciliation against the publication

Elapavalore et al. 2023 report 3411 positive and 2171 negative records over 783 unique compounds. Master plan section 20 allows a 5% discrepancy before explanation is required.

| Quantity | Observed | Published | Difference | % |
|---|---|---|---|---|
| Positive-mode records | **3,411** | 3,411 | +0 | +0.00% |
| Negative-mode records | **2,171** | 2,171 | +0 | +0.00% |
| Total records | **5,582** | 5,582 | +0 | +0.00% |
| Unique compounds (InChIKey block) | **781** | 783 | -2 | -0.26% |
| Positive-mode compounds | **588** | 590 | -2 | -0.34% |
| Negative-mode compounds | **379** | 379 | +0 | +0.00% |

Largest discrepancy: 0.34%, well inside the 5% tolerance. **No release-drift explanation required.**

Compounds measured in both polarities: 588 + 379 - 781 = **186**.

## Metadata homogeneity (all 5,582 records)

| Field | Distinct values | Value(s) |
|---|---|---|
| AC$INSTRUMENT | 1 | `Q Exactive Orbitrap (Thermo Scientific)` (5,582) |
| AC$INSTRUMENT_TYPE | 1 | `LC-ESI-QFT` (5,582) |
| FRAGMENTATION_MODE | 1 | `HCD` (5,582) |
| RESOLUTION | 1 | `17500` (5,582) |
| MS_TYPE | 1 | `MS2` (5,582) |
| COMMENT: CONFIDENCE | 1 | `standard compound` (5,582) |
| PRECURSOR_TYPE | 2 | `[M+H]+` (3,411); `[M-H]-` (2,171) |
| ION_MODE | 2 | `POSITIVE` (3,411); `NEGATIVE` (2,171) |

Every acquisition covariate the master plan hoped was constant is constant. Instrument, instrument type, fragmentation mode, resolution, MS level and confidence class each take exactly one value across the whole corpus. **VERIFIED at full n** (the plan had verified this on 373 records).

## Accession slot convention

Convention `MSBNK-LCSB-LU<4-digit id><2-digit slot>`, slots 01-06 positive at NCE 15/30/45/60/75/90 and 51-56 negative at the same energies.

- Filenames matching the pattern: **5,582 / 5,582**
- Ion mode agrees with slot: **5,582 / 5,582** (0 violations)
- Collision energy agrees with slot: **5,582 / 5,582** (0 violations)
- Distinct slots observed: 12

**Assumption A3 VERIFIED corpus-wide.** Grouping needs no fuzzy matching and no title parsing fallback.

## Coverage per trajectory

| Mode | Records | Groups | 6/6 energies | >=5 | >=4 | <4 |
|---|---|---|---|---|---|---|
| Positive | 3,411 | 588 | 517 (87.9%) | 549 | 561 | 27 |
| Negative | 2,171 | 379 | 330 (87.1%) | 349 | 363 | 16 |

Positive energies-per-group distribution: {2: 16, 3: 11, 4: 12, 5: 32, 6: 517}

Negative energies-per-group distribution: {2: 8, 3: 8, 4: 14, 5: 19, 6: 330}

## Peak counts

| NCE | n records | min | Q1 | median | Q3 | max | % with <4 peaks |
|---|---|---|---|---|---|---|---|
| 15 | 574 | 1 | 4 | 6 | 10 | 115 | 23.9% |
| 30 | 566 | 1 | 7 | 12 | 24 | 273 | 6.0% |
| 45 | 569 | 1 | 12 | 22 | 50 | 374 | 3.7% |
| 60 | 564 | 1 | 17 | 33 | 73 | 445 | 1.8% |
| 75 | 574 | 2 | 20 | 40 | 84 | 473 | 1.6% |
| 90 | 564 | 1 | 20 | 39 | 79 | 395 | 2.0% |

Overall, 6.5% of positive-mode records carry fewer than four peaks, where entropy and any distributional summary are unstable.

## Mass range and mixtures

- Precursor m/z: 115.0 to 837.5
- CH$EXACT_MASS: 115.0 to 836.5
- Precursor charge states observed: [1]
- Mixtures: 10 ({499: 125, 500: 173, 501: 326, 502: 215, 503: 213, 504: 709, 505: 1424, 506: 1715, 507: 119, 508: 563})

## Missing fields and malformed records

| Check | Count |
|---|---|
| Records failing to parse | 0 |
| Records with parser warnings | 0 |
| PK$NUM_PEAK != parsed peak count | 0 |
| Records missing InChIKey | 0 |
| Records missing CH$SMILES | 0 |
| Records missing PRECURSOR_M/Z | 0 |
| Records missing PRECURSOR_TYPE | 0 |
| Records missing RETENTION_TIME | 0 |
| Records missing COLLISION_ENERGY | 0 |

## Identity audit

Every `CH$SMILES` was re-sanitized with RDKit and its InChIKey regenerated, then compared with `CH$LINK: INCHIKEY`.

| Status | Count |
|---|---|
| MATCH | 5,582 |

- Disconnected structures (salts / multi-fragment): **0**
- SMILES carrying stereo markers: 976
- Records excluded for identity reasons: **0**

**No mismatch table is required: all 5,582 records match exactly, on the full InChIKey including the stereo layer.** The MS-ready SMILES problem documented by Elapavalore et al. (stereochemistry stripped, salts removed, wrong names retrieved) leaves no detectable residue in the deposited records. Assumption A9 is **VERIFIED** for this corpus, and no compound is excluded on identity grounds.

## Repeated compounds inside the curated layer

Master plan section 9.4 states, from a 373-record sample, that zero InChIKeys map to more than one internal ID. At full corpus scale **6 compound-by-mode keys map to two internal IDs** (of 967).

| InChIKey block | Mode | Internal IDs | Mixtures |
|---|---|---|---|
| `BHAAPTBBJKJZER` | POSITIVE | [146, 201] | [500, 501] |
| `HSHNITRMYYLLCV` | POSITIVE | [207, 967] | [501, 502] |
| `VAIZTNZGPYBOGF` | POSITIVE | [215, 1256] | [504, 505] |
| `VEMKTZHHVJILDY` | POSITIVE | [158, 183] | [500, 501] |
| `WZZLDXDUQPOXNW` | POSITIVE | [648, 1075] | [499, 503, 505, 506] |
| `XUKUURHRXDUEBC` | POSITIVE | [358, 1385] | [505, 506] |

This **contradicts** the master plan's 'zero duplicates' claim, but the correction is small and does not change the conclusion that drove it: 6 duplicated compounds cannot support a repeatability estimate, so the raw mzML branch remains the only viable route. Recorded as a MINOR contradiction.
