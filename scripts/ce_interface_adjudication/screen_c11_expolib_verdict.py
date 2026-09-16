"""S11 screen, candidate C11: ExpoLib 1.0 (Zenodo 20715576). Step 3: criteria 1-11 and verdict.

Reads only the two machine-readable outputs of steps 1 and 2 plus the P5 exclusion counts, and writes the
criterion-by-criterion table with its evidence pointers. No new download, no model, no spectra.

Evidence strings are file:line / file:sheet:cell / URL pointers. Status vocabulary: MET, NOT_MET, PARTIAL, UNKNOWN.

Output: artifacts/ce_interface_adjudication/screen/c11_expolib/c11_verdict.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "ce_interface_adjudication" / "screen" / "c11_expolib"

S1 = json.loads((OUT / "c11_screen_summary.json").read_text())
S2 = json.loads((OUT / "c11_criteria.json").read_text())
T = S2["tiers"]
EV = S2["evidence"]

OVL = S1["overlap_of_mh_compounds"]
BASE = OVL["base_mh_with_key"]

CRIT = [
    {
        "n": 1,
        "criterion": "Absent from MURU development",
        "status": "NOT_MET",
        "evidence": (
            f"{OVL['muru_registry_key']}/{BASE} ExpoLib ESI+ [M+H]+ compounds are in the frozen MURU v2 exposure "
            f"registry by compound key, and {OVL['muru_registry_scaffold_group']}/{BASE} by scaffold group "
            "(exclusion/muru_exposure_registry_keys.txt, 31,507 keys; _scaffold_groups.txt, 18,402 groups; P5 note "
            "section 2). Populations hit include V2-DEVELOPMENT-POPULATION (45), WUR-POS-IDENTITY (40), "
            "WUR-DEV-ANALYSIS (18), LCSB-ALL-MASSBANK-V1-EXPOSURE-SET (18), WUR-SEALED (16). "
            f"{T['T1_minus_muru_registry_key']['n_compounds']} compounds survive the key-level registry exclusion. "
            "Tautomer hazard CONFIRMED once: Citrinin enters ExpoLib as CBGDIJWINPWWJW (not in the registry) while "
            "the registry holds the tautomer CQIUKKVOEOPUDV, so a key-only registry check misses it "
            "(c11_criteria.json tautomer_recheck)."
        ),
    },
    {
        "n": 2,
        "criterion": "Absent from the PR #7 confirmation population",
        "status": "MET",
        "evidence": (
            f"0/{BASE} by compound key and 0/{BASE} by scaffold group against "
            "exclusion/msnlib_study2_population_keys.txt (1,794 keys) and _scaffold_groups.txt (1,691 groups). "
            "Re-derived independently in pass 2 with 106/106 agreement (c11_criteria.json "
            "pass1_vs_pass2_agreement.in_pr7). Tautomer/skeleton recheck against the PR #7 population SMILES "
            "(validation_population.csv, 1,794 unique SMILES, 2 sharing a C11 molecular formula) adds 0 hits."
        ),
    },
    {
        "n": 3,
        "criterion": "Absent from the comparator benchmark population",
        "status": "MET",
        "evidence": (
            f"0/{BASE} by compound key and 0/{BASE} by scaffold group against "
            "exclusion/comparator_common_population_keys.txt (1,327 keys, sha256 dbdba9ca..., a subset of the PR #7 "
            "population) and _scaffold_groups.txt (1,254 groups). Re-derived with 106/106 agreement. Tautomer/"
            "skeleton recheck against common_population.csv model_smiles adds 0 hits. Only the identity key list and "
            "the population SMILES column were read; no benchmark result, prediction or measured mu was opened."
        ),
    },
    {
        "n": 4,
        "criterion": "Absent from ICEBERG/GLACIER training (MassSpecGym 1.5, all folds, InChIKey14)",
        "status": "NOT_MET",
        "evidence": (
            f"{OVL['msg15_any_fold_key']}/{BASE} compounds are in MassSpecGym 1.5 across all folds "
            f"({OVL['msg15_train_key']} in train, {OVL['msg15_simchallenge_key']} in the simulation_challenge subset "
            "that is the ICEBERG msg_simulation universe), and "
            f"{OVL['msg15_scaffold_group']}/{BASE} by scaffold group "
            "(exclusion/msg15_keys_all.txt 28,929 keys UNION msg15_parent_keys_all.txt 28,923; "
            "msg15_scaffold_groups_all.txt). "
            f"{OVL['msg15_key_with_mh_qtof_rows']}/{BASE} already have [M+H]+ QTOF rows in MassSpecGym; the pooled "
            "MassSpecGym row mix for these molecules is 3,513 Orbitrap and 1,491 QTOF. Only "
            f"{T['M_msg15_key_only']['n_compounds']} compounds "
            f"({T['M_msg15_key_and_scaffold']['n_compounds']} after scaffold-group exclusion) are MassSpecGym-absent."
        ),
    },
    {
        "n": 5,
        "criterion": "Known CE semantics (exactly what quantity, documented where)",
        "status": "MET",
        "evidence": (
            "The CE quantity is the ABSOLUTE laboratory-frame collision energy in VOLTS set per acquisition file on a "
            "SCIEX QTOF, with NO normalization and NO precursor-m/z dependence. Documented three ways, all read: "
            "(a) paper SI Table S2 ('S2 - Data Acquisition', 11306_2026_2481_MOESM1_ESM.xlsx sha256 e68578cd...) MS "
            "method cells 'Collision energy +/- (V) = 35/-35' and 'Collision energy spread (V) = 15', and its note "
            "'Data files containing \"CES\" in the name refer to data acquired using collision energy spread, with "
            "the following values representing the centered collision energy and the spread, respectively. Example: "
            "250527_ExoMix_Cal100_CES30-10_POS represents the data file acquired under CES of 30 +- 10 V)'. "
            "(b) The mzmine batch file lists the imported raw files by name, which encode the value per file: "
            "250527_ExoMix_Cal100_CE{20,25,...,70}_POS.wiff plus CES30-10, CES30-20, CES40-10, CES40-20. "
            "(c) The .msp field is 'Collision_energy:' and may hold a bracketed list, per the deposited R script "
            "(R_Script_-_Lib_Summary_From_msp.Rmd, step 5). "
            "Reconciled contradiction: the Zenodo description says '13 different single collision energies with four "
            "additional collision energy spread experiments', while the ESI+ library carries 11 single values "
            "(20-70 step 5). Table S2 lists 14 single-CE POS acquisition files CE00, CE10, CE15, CE20...CE70, i.e. 13 "
            "nonzero single CEs; the mzmine batch imports only CE20...CE70, so CE00/CE10/CE15 were acquired but not "
            "built into the library. Both statements are true of different objects. Separately, ESI- imported only 8 "
            "single CEs (20,25,30,35,40,50,60,70) and 1 spread (40+-10), so the ladder is polarity-dependent."
        ),
    },
    {
        "n": 6,
        "criterion": "[M+H]+ positive mode available",
        "status": "MET",
        "evidence": (
            f"{S1['has_mh']}/{S1['overview_esi_plus_compounds']} ESI+ overview compounds carry at least one [M+H]+ "
            "spectrum (adduct counts parsed from 'Library Overview - ESI+.xlsx', sha256 62c27a83...; the same table "
            "appears as SI sheet 'S5 - Libraries overview - ESI+' and the two name sets are identical). Median 15 "
            "[M+H]+ spectra per compound, min 3, max 29. A separate ESI- library and [M-H]- only files exist and are "
            "out of scope."
        ),
    },
    {
        "n": 7,
        "criterion": "Compatible fragmentation / instrument metadata",
        "status": "PARTIAL",
        "evidence": (
            "Instrument VERIFIED as SCIEX ZenoTOF 7600 (mzmine presets and batch XML, INSTRUMENT_NAME\">SCIEX ZenoTOF "
            "7600<, INSTRUMENT\">qTof<), resolving the candidate card's 'model UNVERIFIED'. Fragmentation is "
            "beam-type CID in DDA with Zeno pulsing on (SI S2). "
            "COMPATIBLE with the ms-pred instrument vocabulary: instrument2onehot_pos = {Orbitrap: 0 (Orbitrap HCD), "
            "QTOF: 1, IT-FT: 2 (Orbitrap CID), Unknown: 3} at "
            "/Users/aryav/muru-comparators/repos/ms-pred/src/ms_pred/common/chem_utils.py:277-283, so ExpoLib maps to "
            "the 'QTOF' token; both frozen checkpoints set embed_instrument: true "
            "(artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl lines 1-3). ICEBERG 2.1's "
            "native CE input is absolute eV (feasibility audit line 218), which is the same kind of quantity ExpoLib "
            "records, and MassSpecGym's QTOF rows are raw integers from MassBank/MoNA strings without a '%' (P5/P3 "
            "note p3_msg_curation.md line 26), so ExpoLib is unit-matched to the MassSpecGym QTOF pathway. "
            "NOT COMPATIBLE with MURU's deployment: MURU's claim scope is fragmentation extent at fixed Orbitrap ID-X "
            "HCD NCE 20/60 (MURU_COMPARATOR_FEASIBILITY_AUDIT.md line 313). ExpoLib is a different instrument family "
            "(TOF analyser, SCIEX beam-type CID cell) and a different CE unit (absolute V, not normalized NCE); no NCE "
            "is recoverable from an absolute-V QTOF setting, so ExpoLib can never supply a MURU NCE20/NCE60 rung. "
            "Also of note: 39/105 [M+H]+ compounds carry the library's own 'Chimeric precursor selection' flag and 88/105 "
            "have another co-injected mix component within 0.7 m/z of their [M+H]+, because the whole library was "
            "acquired from one 223-compound working solution (SI S2 inclusion-list note)."
        ),
    },
    {
        "n": 8,
        "criterion": "Multiple energies per compound",
        "status": "MET",
        "evidence": (
            "Up to 15 [M+H]+ spectra per compound in ESI+ (11 single CEs 20-70 step 5 plus 4 CE-spread experiments). "
            "Distribution over the 105-compound base: 91 compounds have >= 11 [M+H]+ spectra, 103 have >= 5, all 105 "
            "have >= 3 (min 3, median 15, max 29). 86/105 list all 11 single CE values. Counting single CEs only, "
            "this is an 11-point absolute-eV ladder, denser than the 5-6 point NCE ladders elsewhere in this study."
        ),
    },
    {
        "n": 9,
        "criterion": "Structural diversity and scaffold count after all exclusions",
        "status": "NOT_MET",
        "evidence": (
            f"Before exclusions: {T['T0_all_mh_with_key']['n_compounds']} compounds in "
            f"{T['T0_all_mh_with_key']['n_scaffold_groups']} MURU scaffold groups. "
            f"After MURU-registry key exclusion: {T['T1_minus_muru_registry_key']['n_compounds']} compounds / "
            f"{T['T1_minus_muru_registry_key']['n_scaffold_groups']} groups. "
            f"After also PR #7 and comparator: {T['T2_T1_minus_pr7_comparator_key']['n_compounds']} / "
            f"{T['T2_T1_minus_pr7_comparator_key']['n_scaffold_groups']} (both add nothing). "
            f"After also MassSpecGym all folds (key level): {T['T3_T2_minus_msg15_key']['n_compounds']} compounds / "
            f"{T['T3_T2_minus_msg15_key']['n_scaffold_groups']} scaffold groups, of which "
            f"{T['T3_T2_minus_msg15_key']['n_with_ge11_mh_spectra']} have the full 11-point ladder. "
            f"If scaffold-group exclusion is also applied against every population: "
            f"{T['T4_T3_minus_all_scaffold_groups']['n_compounds']} compounds / "
            f"{T['T4_T3_minus_all_scaffold_groups']['n_scaffold_groups']} groups (Aflatoxicol, Deoxynivalenol "
            "3-glucuronide, SN-38-glucuronide, Tilimycin). "
            "The key-level survivors are chemically narrow: 7 of the 18 are monoester phthalate metabolites sharing "
            "one benzene-dicarboxylate scaffold, and 3 more are glucuronides. "
            "The tautomer/skeleton recheck would remove one more (Aflatoxicol), but that hit is a demonstrable FALSE "
            "POSITIVE of the deliberately over-inclusive skeleton key: the matched MassSpecGym structure is aflatoxin "
            "B2 (parent key WWSYXEZEXMQWHT), a different substance that merely shares aflatoxicol's heavy-atom "
            "skeleton and molecular formula C17H14O6. So 18 compounds / 11 scaffold groups is the defensible "
            "key-level number. Neither 11 nor 4 groups supports a scaffold-split calibration plus a held-out "
            "evaluation."
        ),
    },
    {
        "n": 10,
        "criterion": "License and access",
        "status": "MET",
        "evidence": (
            "Zenodo record 20715576, DOI 10.5281/zenodo.20715576, concept DOI 10.5281/zenodo.18186810, "
            "license cc-by-4.0, access_right 'open', 20 files, no registration "
            "(https://zenodo.org/api/records/20715576, stored as downloads/zenodo_20715576_record.json sha256 "
            "c8fcdf4f...). Depositors Verri Hernandes, Vinicius and Warth, Benedikt (University of Vienna). "
            "Open .msp / .json / .SDF libraries for both polarities (ESI+ .msp 1,651,755 B), plus [M+H]+-only and "
            "[M-H]--only variants, plus RawData_ESI+.tar (7.2 GB) and RawData_ESI-.tar (4.9 GB). The paper SI is at "
            "https://static-content.springer.com/esm/art%3A10.1007%2Fs11306-026-02481-x/MediaObjects/"
            "11306_2026_2481_MOESM1_ESM.xlsx (the PMC mirror returned a reCAPTCHA page, disclosed in the register). "
            "Caveat on route, not on licence: per-spectrum CE values live only inside the .msp/.json spectra files, "
            "which this task's download policy forbids, so every per-spectrum figure here is from the per-compound "
            "overview table, not from spectra."
        ),
    },
    {
        "n": 11,
        "criterion": "Plausibility of hidden MassSpecGym inclusion under a different identifier",
        "status": "MET",
        "evidence": (
            "IMPLAUSIBLE for ExpoLib SPECTRA, on dates alone. MassSpecGym's source libraries were downloaded "
            "2024-05-13 per dataset-construction notebook 1 cell 0 (paper says 2024-05-27) from GNPS, MoNA, MassBank "
            "release 2023.11 and Zenodo 11163381 / MSnLib v1.0 (p3_msg_curation.md lines 67-74); the 1.0 -> 1.5 diff "
            "changed only smiles (221,859 rows), with collision_energy 2 rows and instrument_type 0 rows changed "
            "(p3_msg_curation.md lines 336-352), so 1.5 added no new library. ExpoLib's ESI+ raw acquisitions are "
            "dated 250527 (2025-05-27) in every imported file name and the ESI- Colibactin/DON/Tilimycin runs 260416 "
            "(2026-04-16); the first Zenodo deposit of the concept is 2026-05-25 (record 18186811) and the screened "
            "version 2026-06-16 (record 20715576). Every ExpoLib acquisition postdates the MassSpecGym snapshot by "
            "about a year or more, and ExpoLib is not in GNPS/MoNA/MassBank. "
            "This criterion is about hidden inclusion only; the 85/105 compound-level overlap recorded under "
            "criterion 4 comes from OTHER libraries holding the same common exposome chemicals, not from ExpoLib."
        ),
    },
]

VERDICT = {
    "script": "scripts/ce_interface_adjudication/screen_c11_expolib_verdict.py",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate": "C11 ExpoLib 1.0 (Zenodo 20715576), University of Vienna",
    "verdict": "PARTIAL_OR_SUPPORTING_ONLY",
    "verdict_rule_check": {
        "suitable_design_a_requires": "criteria 1-6 MET and post-exclusion scaffold count sufficient for a "
                                      "scaffold-split calibration plus held-out evaluation",
        "criteria_1_to_6_status": [c["status"] for c in CRIT[:6]],
        "criterion_1": "NOT_MET", "criterion_4": "NOT_MET",
        "post_exclusion_scaffold_groups_key_level": T["T3_T2_minus_msg15_key"]["n_scaffold_groups"],
        "post_exclusion_scaffold_groups_scaffold_level": T["T4_T3_minus_all_scaffold_groups"]["n_scaffold_groups"],
        "conclusion": "SUITABLE_DESIGN_A fails on three independent grounds (criterion 1, criterion 4, criterion 9).",
    },
    "what_it_is_good_for": (
        "A clean, fully documented absolute-volt QTOF CE control. The CE quantity is unambiguous (absolute V per "
        "acquisition file, three independent documentations, no normalization anywhere), the ladder is dense (11 "
        "single CEs 20-70 step 5 plus 4 CE-spread settings), the instrument maps to the ms-pred 'QTOF' token that both "
        "frozen checkpoints embed, and it postdates MassSpecGym so no ExpoLib spectrum can be in training. That makes "
        "it usable as a SUPPORTING probe of what CE quantity the ICEBERG/GLACIER QTOF pathway encodes, on a small "
        "MassSpecGym-absent subset (18 compounds / 11 scaffold groups at key level; 4/4 if scaffold-level exclusion is "
        "enforced), and as a descriptive eV-axis reference. It cannot carry an independent MURU evaluation: the "
        "instrument and CE unit are incompatible with MURU's fixed Orbitrap ID-X HCD NCE 20/60 deployment, and two "
        "thirds of its compounds are already MURU-exposed."
    ),
    "criteria": CRIT,
    "counts": {
        "compounds_total_esi_plus_overview": S1["overview_esi_plus_compounds"],
        "compounds_with_mh_and_muru_key": BASE,
        "compounds_without_structure": S1["no_structure"],
        "tiers": {k: {kk: vv for kk, vv in v.items() if kk != "compounds"} for k, v in T.items()},
        "survivors_key_level": T["T3_T2_minus_msg15_key"]["compounds"],
        "survivors_scaffold_level": T["T4_T3_minus_all_scaffold_groups"]["compounds"],
    },
    "data_defects_found": [
        "Database_File_mzmine_ESI+.csv: 2 of 107 rows carry a recorded 'InChI Key' that disagrees with the recorded "
        "SMILES. Glycitein's SMILES gives DXYUAIFZCFRPTH but the row records YKGCBLWILMDSAV; Isoxanthohumol's SMILES "
        "gives YKGCBLWILMDSAV but the row records MATGKVZWFZHCLI. The pattern (one compound's recorded key equal to "
        "the next compound's SMILES-derived key) suggests a one-row shift in the key column rather than two "
        "independent errors. Neither compound's exclusion status changes under either key route "
        "(c11_compounds_screen.csv anyroute_* columns), so no count in this screen depends on which is right. "
        "The other 104 rows agree.",
        "1 ESI+ overview compound has no structure anywhere in the deposited metadata: 'Colibactin 540 DNA-Adduct' "
        "(no SMILES in the mzmine database file or SI S1), so it has no MURU key and is excluded from the 105 base.",
        "Zenodo overview and SI S5 name sets are identical (106 = 106) but the CE-or-adduct strings differ for 2 "
        "compounds: 4-methylbenzylidene camphor and Mono-(3-carboxypropyl) phthalate.",
        "Zenodo description says 13 single collision energies; the ESI+ library has 11. Reconciled under criterion 5 "
        "(13 = the nonzero single-CE acquisition files in SI S2; 11 = the subset mzmine imported).",
    ],
    "blindness_record": {
        "no_model_run": True,
        "no_spectra_downloaded": "No .msp, .json spectral, .SDF, .mgf, .mzML or RawData tar was fetched. Only the "
                                 "Zenodo record API JSON, the library overview xlsx, the mzmine files zip (batch and "
                                 "presets XML plus compound tables), the R script, the paper SI xlsx and the Zenodo "
                                 "versions JSON.",
        "forbidden_paths_not_opened": [
            "MURU_COMPARATOR_BENCHMARK_RESULT.md",
            "artifacts/comparator_benchmark/{result,predictions,prediction_verification}/",
            "artifacts/comparator_benchmark/technical/*_spectra.json / *_preds.hdf5 / *.mgf",
            "/Users/aryav/muru-comparators/runs/",
            "any *_RESULT.md or measured-mu/result/analysis file",
        ],
        "allowed_identity_files_read": [
            "artifacts/comparator_benchmark/population/common_population.csv (key, scaffold_group, model_smiles)",
            "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv (key, scaffold_group, smiles)",
            "artifacts/wur_v2/data/compounds.csv (smiles column only)",
            "artifacts/ce_interface_adjudication/exclusion/* (P5 key and scaffold-group lists)",
            "artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl (hyperparameters only)",
            "MURU_COMPARATOR_FEASIBILITY_AUDIT.md (interface definitions only)",
        ],
        "new_downloads_this_step": 0,
    },
}

(OUT / "c11_verdict.json").write_text(json.dumps(VERDICT, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(VERDICT, indent=1, ensure_ascii=False))
