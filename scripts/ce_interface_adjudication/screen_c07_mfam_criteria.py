#!/usr/bin/env python3
"""Emit the S7 criterion-by-criterion decision record for C07 (mFam), from the verified numbers."""
import json
from pathlib import Path

OUT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication"
    "/artifacts/ce_interface_adjudication/screen/c07_mfam/verify"
)

V = json.loads((OUT / "c07_verify_summary.json").read_text())
LA, LO, LM = V["ladder_all"], V["ladder_orbitrap_pos_mh"], V["ladder_orbitrap_pos_mh_multi"]

crit = [
    dict(
        n=1,
        criterion="Absent from MURU development (exposure registry, all populations)",
        status="NOT_MET",
        evidence=(
            f"MURU exposure-registry overlap (parent_connectivity_key): {V['overlap_counts_all']['muru_registry']}/"
            f"{V['n_distinct_keys']} of all mFam compounds; "
            f"{V['overlap_counts_orbitrap_pos_mh']['muru_registry']}/{V['orbitrap_pos_mh_keys']} of the Orbitrap+POS+[M+H]+ "
            f"subset; {V['overlap_counts_multi_energy']['muru_registry']}/{V['overlap_counts_multi_energy']['n']} (64.0%) of the "
            "multi-energy subset. Not absent; removal is possible but costs most of the subset. "
            "Keys: artifacts/ce_interface_adjudication/exclusion/muru_exposure_registry_keys.txt (n=31,507)."
        ),
    ),
    dict(
        n=2,
        criterion="Absent from the PR #7 (MSnLib confirmation study 2) population",
        status="MET",
        evidence=(
            f"{V['overlap_counts_all']['pr7_study2']}/{V['n_distinct_keys']} of all mFam compounds intersect the PR #7 "
            f"population; {V['overlap_counts_orbitrap_pos_mh']['pr7_study2']}/{V['orbitrap_pos_mh_keys']} of the Orbitrap+POS+[M+H]+ "
            f"subset; {V['overlap_counts_multi_energy']['pr7_study2']}/{V['overlap_counts_multi_energy']['n']} of the multi-energy "
            "subset. Set: exclusion/msnlib_study2_population_keys.txt. "
            "Caveat: the wider MSnLib 9-library key set overlaps heavily "
            f"({V['overlap_counts_all']['msnlib_9lib']}/{V['n_distinct_keys']} all, "
            f"{V['overlap_counts_multi_energy']['msnlib_9lib']}/{V['overlap_counts_multi_energy']['n']} multi-energy), so "
            "chemical-space novelty relative to MSnLib is NOT established, only PR #7 population membership."
        ),
    ),
    dict(
        n=3,
        criterion="Absent from the comparator benchmark population",
        status="MET",
        evidence=(
            f"{V['overlap_counts_all']['comparator_common']}/{V['n_distinct_keys']} of all mFam compounds intersect "
            "exclusion/comparator_common_population_keys.txt; 0 in every subset (Orbitrap+POS+[M+H]+ and multi-energy). "
            "Exact zero at all three levels."
        ),
    ),
    dict(
        n=4,
        criterion="Absent from ICEBERG/GLACIER training at compound level (MassSpecGym 1.5, all folds, InChIKey14)",
        status="NOT_MET",
        evidence=(
            f"{V['overlap_counts_all']['msg15_any']}/{V['n_distinct_keys']} (57.8%) of all mFam compounds are in MassSpecGym 1.5 "
            f"(train {V['overlap_counts_all']['msg15_train']}, val {V['overlap_counts_all']['msg15_val']}, "
            f"test {V['overlap_counts_all']['msg15_test']}); "
            f"{V['overlap_counts_orbitrap_pos_mh']['msg15_any']}/{V['orbitrap_pos_mh_keys']} (71.9%) of the Orbitrap+POS+[M+H]+ "
            f"subset; {V['overlap_counts_multi_energy']['msg15_any']}/{V['overlap_counts_multi_energy']['n']} (91.6%) of the "
            "multi-energy subset. The one usable sub-collection is almost entirely inside the training corpus at compound level."
        ),
    ),
    dict(
        n=5,
        criterion="Known CE semantics (exactly what quantity, documented where)",
        status="NOT_MET",
        evidence=(
            "MassBank spec makes COLLISION_ENERGY free text with no canonical quantity: the three worked examples are "
            "'20 kV', 'Ramp 10-50 kV' and '10% (nominal)' "
            "(downloads/github_docs/MassBank-web_Documentation_MassBankRecordFormat.md lines 792-803). Realized per-lab forms across "
            f"7,872 records: BARE_NUMBER {V['ce_form_records']['BARE_NUMBER']}, NUMBER_WITH_UNIT {V['ce_form_records']['NUMBER_WITH_UNIT']}, "
            f"MULTI_OR_RAMP {V['ce_form_records']['MULTI_OR_RAMP']}, MODE_PREFIXED {V['ce_form_records']['MODE_PREFIXED']}, "
            f"OTHER {V['ce_form_records']['OTHER']}, MISSING {V['ce_form_records']['MISSING']}. "
            "Decisive point: the ONLY lab supplying >=3 energies per compound is MC20, and its CE is a bare unitless integer "
            "(ladder 10/20/30/40/60/100), verified in record headers "
            "('AC$MASS_SPECTROMETRY: COLLISION_ENERGY 20' in MSBNK-mFam-MC20_000001, 'COLLISION_ENERGY 10' in MC20_001000). "
            "MC20 = Reinke/Boyce/Broadhurst, Edith Cowan University, on a Thermo Q-Exactive Focus. Neither the record, nor the "
            "mFam paper (PMC13328316, which says nothing about CE harmonisation or units), nor any located publication states "
            "whether that integer is NCE (%) or absolute eV. Other Orbitrap labs are each self-consistent but mutually "
            "incompatible: MC09 '15,30,45 (NCE)' (explicit NCE but a single STEPPED spectrum, not three energies), "
            "MC14 '50eV', MC19 '35eV'/'45eV', MC22 '30 eV', MC25 '0.3' (LTQ-Orbitrap XL normalised fraction, corroborated by the "
            "paper SI template row 'Collision energy 0.3' on an LTQ-Orbitrap XL), MC01 'CID 45'/'HCD 90'. "
            "Using a dataset whose CE unit is itself undetermined to adjudicate what CE quantity the checkpoints encode is circular."
        ),
    ),
    dict(
        n=6,
        criterion="[M+H]+ positive mode available",
        status="MET",
        evidence=(
            f"[M+H]+ is the most common adduct: {V['adduct_top']['[M+H]+']} of 7,872 records; "
            f"positive-mode records {V['ion_mode_records']['pos']}. Within the Orbitrap family, "
            f"{V['orbitrap_pos_mh_records']} [M+H]+ records over {V['orbitrap_pos_mh_keys']} distinct compounds."
        ),
    ),
    dict(
        n=7,
        criterion="Compatible fragmentation/instrument metadata (HCD beam-type Orbitrap preferred)",
        status="NOT_MET",
        evidence=(
            f"Orbitrap-family records (MassBank analyzer tokens ITFT + QFT) = {V['orbitrap_records']}/7,872; the remaining "
            "4,433 are ESI-TOF/LC-ESI-QTOF/ESI-QTOF and are outright incompatible with an Orbitrap deployment. "
            "Three defects inside the Orbitrap part: "
            "(a) FRAGMENTATION_MODE is absent from the ENTIRE mFam collection (GitHub code search "
            "'FRAGMENTATION_MODE repo:MassBank/MassBank-data path:mFam' returns total_count 0), so HCD vs CID is never declared; "
            "(b) MC01 mixes CID and HCD within one lab and uses APCI, not ESI; "
            "(c) the sole multi-energy lab MC20 declares 'AC$INSTRUMENT_TYPE: LC-ESI-ITFT' while 'AC$INSTRUMENT: Thermo Scientific "
            "Q-Exactive Focus' in 2,000/2,000 sampled headers (s7 and prior inst_MC20_pos/neg probes, unanimous) - a systematic "
            "mislabel, since a Q Exactive Focus is a quadrupole-Orbitrap (QFT, beam-type HCD), not an ion-trap-FT. "
            "Taken literally, LC-ESI-ITFT routes to the ms-pred token 'IT-FT' documented as 'Orbitrap CID' "
            "(/Users/aryav/muru-comparators/repos/ms-pred/src/ms_pred/common/chem_utils.py:280), whereas the hardware warrants "
            "'Orbitrap' documented as 'Orbitrap HCD' (chem_utils.py:278). The instrument token for the only usable sub-collection "
            "is therefore undecidable from the record, which is disqualifying for MURU's fixed NCE20/NCE60 Orbitrap HCD deployment."
        ),
    ),
    dict(
        n=8,
        criterion="Multiple energies per compound",
        status="PARTIAL",
        evidence=(
            f"Only {V['orbitrap_pos_mh_multi_energy_keys']}/{V['orbitrap_pos_mh_keys']} (25.6%) of Orbitrap+POS+[M+H]+ compounds "
            "carry >=3 distinct single-valued CEs within one lab, and every one of them comes from a single lab: "
            f"labs_supplying_ge3_energies = {V['labs_supplying_ge3_energies']}. Distribution of max distinct CE per compound "
            f"(Orbitrap+POS+[M+H]+): {V['orbitrap_pos_mh_max_ce_hist']} - i.e. 446 compounds have exactly one energy and 176 have "
            "the full MC20 6-point ladder. MC09's '15,30,45 (NCE)' is one stepped spectrum, not three energies, so it does not count."
        ),
    ),
    dict(
        n=9,
        criterion="Structural diversity and scaffold count after all exclusions",
        status="NOT_MET",
        evidence=(
            "Design-A target (Orbitrap + POSITIVE + [M+H]+ + >=3 energies), MURU scaffold_group_v2 definition: "
            f"start {LM['S0_all']['keys']} keys / {LM['S0_all']['scaffold_groups']} groups; after MURU registry "
            f"{LM['S1_not_in_muru_registry']['keys']}; after PR #7 and comparator {LM['S3_and_not_in_comparator']['keys']}; "
            f"after MassSpecGym 1.5 keys {LM['S4_and_not_in_msg15_key']['keys']} keys / "
            f"{LM['S4_and_not_in_msg15_key']['scaffold_groups']} groups; after scaffold-level novelty vs MURU "
            f"{LM['S5_and_scaffold_novel_vs_muru']['keys']}; final "
            f"{LM['S6_and_scaffold_novel_vs_msg15']['keys']} keys / {LM['S6_and_scaffold_novel_vs_msg15']['scaffold_groups']} "
            f"scaffold groups, of which {LM['S6_and_scaffold_novel_vs_msg15']['acyclic_groups']} are '__ACYCLIC__' pseudo-groups "
            "(so 2 genuine ring scaffolds) and 0 groups hold >=2 compounds. "
            f"Final 6 keys: {', '.join(LM['_final_keys'])}. "
            "Relaxing the multi-energy requirement to any Orbitrap+POS+[M+H]+ still yields only "
            f"{LO['S6_and_scaffold_novel_vs_msg15']['keys']} keys / {LO['S6_and_scaffold_novel_vs_msg15']['scaffold_groups']} groups; "
            f"dropping the Orbitrap and adduct filters entirely gives {LA['S6_and_scaffold_novel_vs_msg15']['keys']} keys / "
            f"{LA['S6_and_scaffold_novel_vs_msg15']['scaffold_groups']} groups. A scaffold-split calibration plus a held-out "
            "evaluation is not supportable at 6 compounds / 2 real scaffolds."
        ),
    ),
    dict(
        n=10,
        criterion="License and access",
        status="MET",
        evidence=(
            f"Uniform CC BY 4.0: {V['licenses']} over all 7,872 records (JSON-LD 'license' field; record headers carry "
            "'LICENSE: CC BY'). Public, no registration: MassBank 2025.10 release "
            "(downloads/massbank_api/metadata.json version 2025.10, timestamp 2025-10-24T10:33:06Z, spectra_count 134,756). "
            "All 7,872 record metadata bodies fetched with HTTP 200 and 0 title-parse failures, so identities are obtainable "
            "from metadata alone - no spectra download is needed to screen this candidate."
        ),
    ),
    dict(
        n=11,
        criterion="Release timing / deposition makes hidden MassSpecGym inclusion under a different identifier plausible",
        status="MET",
        evidence=(
            "PLAUSIBLE, and untestable from the release. mFam records were published to MassBank between "
            f"{V['date_published_range'][0]} and {V['date_published_range'][1]} (23 of 25 labs in 2023), i.e. before MassSpecGym 1.5. "
            "MassSpecGym 1.5 carries a large MassBank-derived block (rows_by_label MassBank_or_MoNA = 84,298 of 231,104, "
            "p3_msg15_row_source_attribution_summary.json), and its identifiers are opaque re-numbered strings "
            "('MassSpecGymID0000001' ... 'MassSpecGymID0414174'; 0 of 231,104 rows contain 'MSBNK' or 'mFam'), so source accessions "
            "are not recoverable and inclusion cannot be excluded by identifier. "
            "Counter-evidence specific to MC20: no MassSpecGym Orbitrap row has collision_energy == 100 (0 of 172,058; "
            "max Orbitrap CE 358.4, 2,017 rows > 90), and 0 MassSpecGym Orbitrap [M+H]+ compounds carry MC20's full "
            "10/20/30/40/60/100 ladder, so MC20's own spectra are probably NOT in MassSpecGym even though "
            f"{V['overlap_counts_multi_energy']['msg15_any']}/{V['overlap_counts_multi_energy']['n']} of its compounds appear there "
            "via other spectra. Spectrum-level duplication unlikely for MC20; compound-level leakage certain."
        ),
    ),
]

rec = dict(
    agent="S7",
    candidate="C07 mFam consortium MassBank contribution, Orbitrap subset",
    verdict="UNSUITABLE",
    verdict_rule="SUITABLE_DESIGN_A requires criteria 1-6 MET; criteria 1, 4 and 5 are NOT_MET, and criterion 9 fails independently.",
    criteria=crit,
    headline=dict(
        records=V["n_records"],
        labs=V["n_labs"],
        compounds_total_muru_key=V["n_distinct_keys"],
        scaffold_groups_total=V["n_scaffold_groups"],
        orbitrap_records=V["orbitrap_records"],
        orbitrap_pos_mh_records=V["orbitrap_pos_mh_records"],
        orbitrap_pos_mh_compounds=V["orbitrap_pos_mh_keys"],
        multi_energy_compounds=V["orbitrap_pos_mh_multi_energy_keys"],
        multi_energy_after_all_exclusions_keys=LM["S6_and_scaffold_novel_vs_msg15"]["keys"],
        multi_energy_after_all_exclusions_scaffolds=LM["S6_and_scaffold_novel_vs_msg15"]["scaffold_groups"],
        multi_energy_after_all_exclusions_real_ring_scaffolds=(
            LM["S6_and_scaffold_novel_vs_msg15"]["scaffold_groups"] - LM["S6_and_scaffold_novel_vs_msg15"]["acyclic_groups"]
        ),
    ),
)
(OUT / "c07_criteria.json").write_text(json.dumps(rec, indent=1))
for c in crit:
    print(f"{c['n']:2d}. {c['status']:9s} {c['criterion']}")
print("\nVERDICT:", rec["verdict"])
print(json.dumps(rec["headline"], indent=1))
