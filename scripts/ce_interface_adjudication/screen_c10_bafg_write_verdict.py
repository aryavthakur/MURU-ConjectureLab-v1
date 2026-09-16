"""Write the S10-C10 criteria evidence and verdict files (no network, no recomputation)."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = ROOT / "artifacts/ce_interface_adjudication/screen/c10_bafg"

R = "s10_verification_record.json"
P2 = "s10_verification_part2.json"
P3 = "s10_peak_count_census.json"

crit = {
    "candidate": "C10 MassBank BAFG (Bundesanstalt fuer Gewaesserkunde) SCIEX TripleTOF CE ladders",
    "task": "S10-C10",
    "written_utc": "2026-09-15",
    "method": "Metadata only. No model run (no ICEBERG, GLACIER, FIORA or MURU inference). No spectra file, release "
              "asset, MGF/MSP/mzML/HDF5, /records/{accession} response or peak row was downloaded, printed or stored. "
              "Identity came from the MassBank export-service JSON-LD endpoint and the GitHub git-tree listings; "
              "header fields came from GitHub code-search text-match fragments with peak-looking lines dropped before "
              "storage. The only peak-derived quantity used anywhere is the integer PK$NUM_PEAK count.",
    "independence": "Every count below was recomputed in scripts/ce_interface_adjudication/screen_c10_bafg_verify.py "
                    "from c10_records_identity.csv plus the P5 exclusion lists. The compound key and scaffold group "
                    "were re-derived from the record SMILES with scaffold_key.py rather than read from the first "
                    "pass's key columns; 20,658/20,658 rows agree with the first pass on both.",
    "criteria": {
        "1_absent_from_muru_development": {
            "status": "NOT_MET",
            "evidence": "571 of 1,070 positive-mode BAFG compound keys are in the MURU exposure registry "
                        "(31,507 keys) and 366 are in the union of the 16 exposed populations (1,912 keys); "
                        "370 of 525 positive-mode scaffold groups are in the registry's 18,402 scaffold groups. "
                        f"{R} :: checks.overlap_positive, checks.overlap_positive_scaffold.",
        },
        "2_absent_from_pr7_confirmation_population": {
            "status": "MET",
            "evidence": "0 of 1,070 keys and 0 of 525 scaffold groups intersect the frozen PR #7 MSnLib confirmation "
                        f"population (1,794 keys / 1,691 groups). {R} :: checks.overlap_positive.in_pr7. "
                        "The matching machinery is shown to work by the 366 MURU exposed-population hits above.",
        },
        "3_absent_from_comparator_benchmark_population": {
            "status": "MET",
            "evidence": "0 of 1,070 keys and 0 of 525 scaffold groups intersect the 1,327-key comparator common "
                        f"population (itself a subset of PR #7). {R} :: checks.overlap_positive.in_comparator.",
        },
        "4_absent_from_iceberg_glacier_training": {
            "status": "NOT_MET",
            "evidence": "911 of 1,070 positive keys (85.1%) are in MassSpecGym 1.5 all folds; 901 are in the "
                        "simulation_challenge subset that is the ICEBERG msg_simulation universe; 830 are in the "
                        "train fold. Beyond compound overlap there is row-level evidence that the BAFG spectra "
                        "themselves are in MassSpecGym: 1,839 of the 1,849 MassSpecGym QTOF rows with CE > 100 carry "
                        "a BAFG positive-mode key, MassSpecGym's QTOF collision_energy maximum is exactly 150.0 "
                        "(the BAFG ladder top) while its Orbitrap maximum is 358.4, and 13,265 MassSpecGym QTOF rows "
                        "sit exactly on the 10-150 step-10 grid with a BAFG key. "
                        f"{R} :: checks.overlap_positive, checks.msg_qtof; {P2} :: msg_qtof_vs_bafg.",
        },
        "5_known_ce_semantics": {
            "status": "MET",
            "evidence": "VERIFIED in the record text: 'AC$MASS_SPECTROMETRY: COLLISION_ENERGY <integer>' with no unit "
                        "and no percent sign, 'AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE CID', "
                        "'AC$INSTRUMENT: TripleTOF 5600 SCIEX', 'AC$INSTRUMENT_TYPE: LC-ESI-QTOF', and "
                        "'RECORD_TITLE: <name>; LC-ESI-QTOF; MS2; <integer> V'. Checked in BOTH accession blocks "
                        "(pre-2023.11 CSL231*, e.g. MSBNK-BAFG-CSL2311096 COLLISION_ENERGY 50 / title '50 V'; "
                        "post-2023.11 CSL250*, e.g. MSBNK-BAFG-CSL25011734176 COLLISION_ENERGY 140). All 20,658 "
                        "record titles end in '<number> V' and 0 records carry COLLISION_ENERGY_SPREAD, so these are "
                        "single fixed settings, not ramps. "
                        f"{R} :: checks.header_fields, checks.title_ce_tail. "
                        "INFERRED (one step): on a SCIEX QTOF the CE setting is a lab-frame accelerating potential in "
                        "volts, so the number equals the lab-frame collision energy in eV for singly charged "
                        "precursors; for the 1 sampled [M-2H]2- record that identity would need a charge factor.",
        },
        "6_mh_positive_available": {
            "status": "MET",
            "evidence": "In a 669-record code-search sample the precursor types are [M+H]+ 385, [M]+ 141, [M-H]- 132, "
                        "[M+HCOO]- 6, [M+Na]+ 3, [M-2H]2- 1, [M+NH4]+ 1; every [M]+ sits on a permanent-cation "
                        "parent (charge 1). 954 of the 1,070 positive keys have a charge-neutral parent, 116 do not. "
                        f"{P3} :: precursor_type_by_ion_mode; {P2} :: positive_keys_by_parent_charge.",
        },
        "7_compatible_fragmentation_instrument": {
            "status": "NOT_MET",
            "evidence": "BAFG is CID on SCIEX TripleTOF 5600 / 6600 / X500R (LC-ESI-QTOF), never HCD: a code search "
                        "for HCD anywhere under BAFG returns 0 hits, FRAGMENTATION_MODE is CID. This is compatible "
                        "with ms-pred's instrument vocabulary, which does carry a QTOF token "
                        "(src/ms_pred/common/chem_utils.py:277-283, instrument2onehot_pos = {Orbitrap:0 'Orbitrap "
                        "HCD', QTOF:1, IT-FT:2 'Orbitrap CID', Unknown:3}) and all three frozen checkpoints set "
                        "embed_instrument=True, so ICEBERG/GLACIER can be conditioned on it. It is NOT compatible "
                        "with MURU's frozen deployment, which is fixed Orbitrap ID-X HCD NCE 20 and 60 "
                        "(MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md:18 and :219). Different instrument class, "
                        "different activation type, and a CE axis in volts rather than normalized collision energy.",
        },
        "8_multiple_energies_per_compound": {
            "status": "MET",
            "evidence": "1,038 of 1,070 positive keys have >= 2 distinct CE, 912 have >= 10, and 795 carry the "
                        "complete 15-point ladder 10,20,...,150 V; the median key has 15 distinct energies. "
                        f"{R} :: checks.positive_compounds.",
        },
        "9_structural_diversity_after_exclusions": {
            "status": "NOT_MET",
            "evidence": "Cascade on positive-mode compounds: 1,070 keys / 525 scaffold groups -> 954 / 466 "
                        "(charge-neutral parent) -> 43 / 32 (minus MassSpecGym 1.5 all folds, either key route) -> "
                        "41 / 30 (minus the MURU exposure registry and exposed union) -> 18 / 18 (minus MURU, PR #7 "
                        "and comparator scaffold groups) -> 17 keys / 17 scaffold groups after requiring >= 2 CE and "
                        "an [M+H]+ m/z in 70-1042.6, or 15 / 15 if MassSpecGym scaffold groups are excluded too. "
                        "Every surviving group is a singleton, so a scaffold split would put roughly 8 compounds on "
                        "each side. "
                        f"{R} :: checks.exclusion_cascade, checks.v6_keys, checks.v6_scaffold_groups.",
        },
        "10_license_and_access": {
            "status": "MET",
            "evidence": "Every one of the 20,658 records carries 'LICENSE: dl-de/by-2-0' and 'COPYRIGHT: Copyright "
                        "2025 Federal Institute of Hydrology, Koblenz, Germany'; the JSON-LD license field is "
                        "https://www.govdata.de/dl-de/by-2-0 (Data licence Germany attribution 2.0, use permitted "
                        "with attribution) on 20,658/20,658 records. Access is a public GitHub repository "
                        "(MassBank/MassBank-data), the MassBank3 API and the MassBank export JSON-LD service; this "
                        "entire screen needed no authentication and no spectra. "
                        f"{R} :: checks.records_table.license, checks.header_fields.record_title.",
        },
        "11_hidden_massspecgym_inclusion_plausible": {
            "status": "NOT_MET",
            "evidence": "Hidden inclusion is not merely plausible, it is evidenced. 19,783 of the 20,658 records were "
                        "already in the repository at tag 2023.11 (tag -> commit 9dc52cb29b7ade23e81befc3ce9eb0014"
                        "77ce393, 2023-11-28 -> BAFG tree f3f72e005f4073bc7bc0e5af7b706a2645adc7f9 with exactly "
                        "19,783 entries, re-fetched independently), and P3 verified that MassSpecGym's construction "
                        "notebook 1 cell 3 ingests MassBank release 2023.11 and maps LC-ESI-QTOF -> QTOF, keeping a "
                        "collision energy that has no '%' as the raw first number (notes/p3_msg_curation.md:73, :220, "
                        ":456). MassSpecGym identifiers are opaque (MassSpecGymID#######; 0 of 231,104 contain "
                        "MSBNK), so inclusion cannot be checked by accession, which is exactly why the CE-ladder "
                        "fingerprint in criterion 4 is the operative evidence. Independent corroboration from the "
                        "depositor: MassBank-data issue #275 states '19,783 files keep their original ACCESSION ... "
                        "with only the file content updated' and 'The 646 new files received a new ACCESSION', "
                        "matching the 19,783 tree count exactly. "
                        f"{R} :: checks.tag_provenance, checks.refs_used_first_pass.",
        },
    },
    "disclosed_discrepancies_and_caveats": [
        {
            "id": "D1",
            "severity": "material for dating, not for the verdict",
            "text": "Every BAFG record's DATE / JSON-LD datePublished is 2025-01-17, including the 19,783 records that "
                    "demonstrably existed at the 2023.11 tag in November 2023. The depositor confirms the field is "
                    "the last-modification date, not deposition (issue #275: DATE 'shows the date of the last "
                    "modification'). A screen that trusted the record date would wrongly conclude the whole library "
                    "post-dates MassSpecGym. Only git tree membership dates these records.",
        },
        {
            "id": "D2",
            "severity": "unresolved, bounded",
            "text": "The post-2023.11 increment is 875 files (20,658 - 19,783, all with CSL250* accessions), but "
                    "MassBank-data issue #275 says 646 new spectra were added. 229 files are unexplained by that "
                    "message. It does not change the verdict: those keys were checked against MassSpecGym directly, "
                    "and 22 keys that appear only in post-2023.11 records are in MassSpecGym anyway by another route.",
        },
        {
            "id": "D3",
            "severity": "caveat on the identity join",
            "text": "Issue #275 records that all 19,783 retained files had their CONTENT regenerated in January 2025, "
                    "with corrections in the metadata area (CAS, InChIKey, InChI). The identity fields MassSpecGym "
                    "ingested from MassBank 2023.11 are therefore not guaranteed to equal the ones read today, so "
                    "the 911/1,070 compound overlap could be off in either direction at the margin. The row-level CE "
                    "fingerprint evidence for criterion 4 does not depend on identity and is unaffected.",
        },
        {
            "id": "D4",
            "severity": "material for usability, sample-based",
            "text": "The recorded spectra are sparse. In a 669-record code-search sample the median PK$NUM_PEAK is 8 "
                    "(positive mode 10, negative mode 4); 34.8% of records have <= 5 peaks and 58.1% have <= 10. "
                    "Peak count does not fall with CE across the ladder (median 9-16 from 40 V to 150 V), so this is "
                    "a library-wide reporting threshold, not high-energy attrition. A fragmentation-extent quantity "
                    "estimated from a peak distribution is poorly supported at that density. The sample is GitHub "
                    "best-match order, NOT random, so treat it as indicative. "
                    f"{P3} :: num_peak_summary, num_peak_by_ce.",
        },
        {
            "id": "D5",
            "severity": "definitional, off-by-one against the first pass",
            "text": "This pass defines the charge-neutral stratum as parent formal charge 0 (954 keys); the first "
                    "pass additionally required the RECORDED formula to be uncharged (953 keys). One compound has a "
                    "recorded charged formula but a neutral parent. Every downstream pool count here is therefore "
                    "exactly 1 or 2 higher than the first pass's Q-series (V6 17 vs Q6 16, V7 15 vs Q8 14). Not a "
                    "contradiction, a different stratum definition.",
        },
        {
            "id": "D6",
            "severity": "note on a quoted count",
            "text": "GitHub code-search total_count for path:BAFG queries is 18,400 while the directory holds 20,658 "
                    "records, so the search index does not cover every file. Code-search counts are used here only "
                    "for presence/absence of a field (for example 0 hits for HCD and 0 for COLLISION_ENERGY_SPREAD) "
                    "and for sampling, never as a population count.",
        },
    ],
}

verdict = {
    "candidate": "C10 MassBank BAFG SCIEX TripleTOF CE ladders (rank 10, proposed as a SUPPORTING QTOF eV control)",
    "task": "S10-C10",
    "written_utc": "2026-09-15",
    "verdict": "PARTIAL_OR_SUPPORTING_ONLY",
    "verdict_note": "Not usable as independent evaluation data: criteria 1, 4, 7, 9 and 11 are NOT_MET. 85.1% of its "
                    "positive-mode compounds are in MassSpecGym 1.5, and the row-level fingerprint (1,839 of 1,849 "
                    "MassSpecGym QTOF rows above CE 100 carry a BAFG key, QTOF CE max exactly 150.0) indicates the "
                    "spectra themselves are training data. It keeps real value in the role it was nominated for: a "
                    "clean, well-documented raw-volt QTOF CE ladder whose values are known to enter MassSpecGym "
                    "unconverted, which makes it a usable attribution control for what the checkpoints encode when a "
                    "collision energy carries no percent sign. As evaluation material it fails twice over, on "
                    "training contamination and on a post-exclusion pool of 17 compounds in 17 singleton scaffold "
                    "groups.",
    "status_by_criterion": {
        "1": "NOT_MET", "2": "MET", "3": "MET", "4": "NOT_MET", "5": "MET", "6": "MET",
        "7": "NOT_MET", "8": "MET", "9": "NOT_MET", "10": "MET", "11": "NOT_MET",
    },
    "headline_counts": {
        "records_total": 20658,
        "records_positive": 15495,
        "records_negative": 5163,
        "compounds_total_all_modes": 1173,
        "compounds_positive_mode": 1070,
        "scaffold_groups_positive_mode": 525,
        "compounds_after_all_exclusions": 17,
        "scaffold_groups_after_all_exclusions": 17,
        "compounds_after_all_exclusions_strict_msg_scaffold": 15,
        "energies_per_compound_median": 15,
    },
    "no_spectra_statement": "No MassBank record .txt blob, release asset, /records/{accession} response, MGF/MSP/mzML/"
                            "HDF5 file, peak list, model output or MURU measurement was downloaded or read. The only "
                            "peak-derived quantity anywhere in these artifacts is the integer PK$NUM_PEAK count, "
                            "harvested from code-search header fragments with peak-looking lines dropped first.",
    "artifacts": [R, P2, P3, "s10_peak_count_sample.csv", "c10_criteria_evidence.json",
                  "c10_screen_summary.json (first pass)", "c10_records_identity.csv (first pass)",
                  "c10_compounds_screen.csv (first pass)"],
    "scripts": [
        "scripts/ce_interface_adjudication/screen_c10_bafg_verify.py",
        "scripts/ce_interface_adjudication/screen_c10_bafg_verify2.py",
        "scripts/ce_interface_adjudication/screen_c10_bafg_verify3.py",
        "scripts/ce_interface_adjudication/screen_c10_bafg.py (first pass)",
    ],
}

(OUT / "c10_criteria_evidence.json").write_text(json.dumps(crit, indent=1))
(OUT / "c10_screen_verdict.json").write_text(json.dumps(verdict, indent=1))

man = {}
for f in sorted(OUT.glob("*.*")):
    if f.is_file():
        man[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
(OUT / "output_manifest_sha256.json").write_text(json.dumps(man, indent=1))
print(json.dumps(verdict, indent=1))
print()
print(json.dumps(man, indent=1))
