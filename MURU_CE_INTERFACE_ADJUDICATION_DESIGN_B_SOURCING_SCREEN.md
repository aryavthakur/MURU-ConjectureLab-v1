# MURU CE interface adjudication, Design B: sourcing screen

Status: EXECUTED 2026-09-18/19 from plan commit `f7825e2`. Metadata-only feasibility census. No spectrum acquired, no model run, no MS/MS outcome inspected, no compound selected. Design B is NOT preregistered.

**Outcome: PASS — PREFERRED DESIGN FEASIBLE.**

## Sources and provenance

| Item | Value |
|---|---|
| Catalogues | MedChemExpress (MCE), TargetMol, Selleck Chemicals |
| Retrieval | PubChem PUG REST vendor deposits, 2026-09-19 00:06 UTC: `substance/sourceall/<source>/sids`, SID `xrefs/RegistryID` (the vendor catalogue ID), standardized CIDs, CID properties |
| Register | 4 payloads with sha256 in `artifacts/ce_interface_adjudication/downloads_register.jsonl` (payloads untracked) |
| Scripts | `scripts/ce_interface_adjudication/design_b/10_fetch_catalogues.py`, `20_sourcing_screen.py` |
| Outputs | `artifacts/ce_interface_adjudication/design_b/sourcing/`: `sourcing_screen_summary.json`, `candidate_ledger_in_windows.csv.gz` (every in-window chemical with vendors, catalogue IDs, name, parent SMILES, key, [M+H]+, stratum, scaffold group, first exclusion reason), `eligible_universe.csv`, `vendor_spot_check.csv` |

Three catalogues were enough: the result is a surplus of more than 40x in every stratum, so no further vendor was screened.

## Frozen eligible universe

`eligible_universe.csv`, sha256 recorded in `sourcing_screen_summary.json` (`eligible_universe_sha256`). This is the frame for the later preregistered random draw. Nothing has been drawn and no compound has been chosen.

## Cascade

Chemical = MURU parent connectivity key (largest organic fragment, Uncharger, first InChIKey block). Listings of the same chemical across vendors and salt forms are merged before counting. A listing-level rule (S3 to S5) passes if any listing of the chemical passes.

| Step | Remaining |
|---|---|
| Raw catalogue listings screened (MCE 116,896; TargetMol 101,909; Selleck 15,797) | 234,602 |
| Listings with a standardized PubChem structure | 192,856 |
| Unique chemicals after vendor de-duplication | 96,591 |
| S2 theoretical [M+H]+ in L, N or H | 35,181 |
| S3 single covalent unit (no salt, solvate or mixture) | 32,714 |
| S4 no permanent or net charge | 32,309 |
| S5 no isotope label | 31,343 |
| S6 ms-pred element set, heavy atoms at most 160, [M+H]+ at most 995.556 | 31,325 |
| S7a absent from MassSpecGym 1.5 and ms-pred msg labels (recorded, parent keys) | 26,801 |
| S7b absent by canonical-tautomer key (formula-restricted, as Design A R8m) | 26,758 |
| S8 absent from Design A | 26,755 |
| S9 absent from the PR #8 population | 26,746 |
| S10 purity at least 95% where stated (the deposits state none, so nothing removed) | 26,746 |

Per stratum:

| | L 130-300 | N 485-515 | H 700-900 |
|---|---|---|---|
| In window | 25,342 | 4,370 | 5,469 |
| S3 single unit | -1,785 | -210 | -472 |
| S4 charge | -128 | -52 | -225 |
| S5 isotope | -849 | -87 | -30 |
| S6 model limits | -14 | -2 | -2 |
| S7a MassSpecGym key | **-3,472** | **-559** | **-493** |
| S7b MassSpecGym tautomer | -38 | -4 | -1 |
| S8 Design A | -3 | 0 | 0 |
| S9 PR #8 | -7 | -2 | 0 |
| **Eligible chemicals** | **19,046** | **3,454** | **4,246** |
| Distinct scaffold groups | 7,871 | 2,772 | 2,899 |
| **Usable, one per scaffold group across the whole design** | **7,727** | **2,772** | **2,803** |

Usable counts assign a scaffold group shared between strata to the scarcer stratum first, so no group is counted twice.

Main attrition: among the listed rules, MassSpecGym membership (S7a) is the largest in every stratum; in H the salt/multi-component rule (S3) is nearly as large. The largest single reduction overall is the one-per-scaffold-group constraint (H 4,246 chemicals to 2,803 usable groups).

## Go rule

| Criterion | Required | Achieved |
|---|---|---|
| N_eff = 4 / (1/nL + 1/nH) | at least 120 | **8,227** |
| nL | at least 50 | 7,727 |
| nH | at least 50 | 2,803 |
| nN | at least 60 | 2,772 |
| 66 / 66 / 66 procurement reserve | possible | **yes** |

## Stock, purity and cost (spot check, not binding)

PubChem deposits carry no purity, stock or price. A seeded random sample of 10 MCE-primary eligible listings per stratum (seed 20260918) was read from the live MCE catalogue on 2026-09-19, catalogue pages only.

| | L | N | H |
|---|---|---|---|
| Orderable at a list price | 5 | 4 | 5 (+1 priced but quote required) |
| Quote only | 3 | 6 | 4 |
| Unresolved or delisted | 2 | 0 | 0 |
| Smallest-pack list prices, USD | 25 to 191 (median 35) | 25 to 600 (median about 245) | 150 to 646 (median about 400) |

About half the eligible listings are orderable at a list price; the other half need a quote. Even at that rate every stratum keeps more than 1,000 usable scaffold groups. Stated purity, where shown (7 of 28 found), was 97.75% to 99.69%, all above 95%.

Approximate procurement at the smallest pack for 66 + 66 + 66 drawn from list-price items: L about USD 2,000 to 5,000, N about USD 15,000 to 20,000, H about USD 25,000 to 30,000, **total roughly USD 40,000 to 55,000**. This rests on 10 prices per stratum and is indicative only; quote-only items are unpriced.

For the preregistration, not decided here: whether the random-draw frame is the whole eligible universe or only its orderable-at-list-price subset, and the rule for replacing a drawn compound that turns out to be unobtainable.

## Limits

- Structures are the vendors' PubChem deposits; identity of the physical material is checked only at acquisition (plan section 4, item 4 and 5).
- Purity rule S10 could not be applied from catalogue metadata; it applies at purchase via the certificate of analysis, as the plan already requires.
- No window was widened, no purity threshold lowered, no excluded compound reused and no design parameter changed.
