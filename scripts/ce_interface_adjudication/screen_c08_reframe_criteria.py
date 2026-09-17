"""S8 criteria record for candidate C08 (GNPS REFRAME-POSITIVE-LIBRARY, sibling CMMC-REFRAME-POSITIVE-LIBRARY).

Reads the first-pass screen_summary.json and the second-pass verify_summary.json and emits the
eleven-criterion adjudication with its evidence pointers. No new network access, metadata only.
"""
from __future__ import annotations

import json
from pathlib import Path

SCREEN = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication"
              "/artifacts/ce_interface_adjudication/screen/c08_reframe")

s1 = json.loads((SCREEN / "screen_summary.json").read_text())
s2 = json.loads((SCREEN / "verify_summary.json").read_text())
pools = {p["label"]: p for p in s1["pools"]}
ov = s1["overlap_unique_keys_by_subset"]["all"]
ce = s2["raw_file_collision_energy_metadata"]

C = []


def c(n, name, status, evidence):
    C.append({"n": n, "criterion": name, "status": status, "evidence": evidence})


c(1, "absent from MURU development", "PARTIAL",
  f"{ov['in_muru_registry_all__unique_keys']} of {ov['keys']} parent keys are in the MURU exposure registry "
  f"(muru_exposure_registry_keys.txt, 31,507 keys); {ov['in_muru_dev_compounds_csv_keys__unique_keys']} in the "
  f"v2 development population; {ov['in_muru_exposed_union__unique_keys']} in the exposed union. Not absent, but "
  f"every overlap is identifiable at InChIKey14 level and removable: pool P3 keeps "
  f"{pools['P3 = P2 and key not in the full MURU exposure registry (conservative)']['keys']} [M+H]+ keys.")

c(2, "absent from the PR #7 confirmation population", "PARTIAL",
  f"{ov['in_pr7_study2_population__unique_keys']} of {ov['keys']} keys overlap the PR #7 (MSnLib confirmation "
  f"study 2) population of 1,794 keys; 48 keys share a PR #7 scaffold group. Small and cleanly excludable.")

c(3, "absent from the comparator benchmark population", "MET",
  f"{ov['in_comparator_common_population__unique_keys']} of {ov['keys']} keys overlap the 1,327-key comparator "
  f"common population (comparator_common_population_keys.txt). Only 8 keys share a comparator scaffold group.")

c(4, "absent from ICEBERG/GLACIER training (MassSpecGym 1.5, all folds, InChIKey14)", "PARTIAL",
  f"{ov['in_msg15_any_route__unique_keys']} of {ov['keys']} keys are in MassSpecGym 1.5 by either key route "
  f"(SMILES-derived parent key 2,643, library-recorded InChIKey first block 2,496, union 2,646); by fold "
  f"{ov['in_msg15_recorded_train__unique_keys']} train / {ov['in_msg15_recorded_val__unique_keys']} val / "
  f"{ov['in_msg15_recorded_test__unique_keys']} test. Removable: 4,533 [M+H]+ keys survive (pool P1b). "
  f"Residual risk is structural near-identity rather than key identity: 1,613 P3 keys share a parent formula "
  f"with some MassSpecGym compound and 114 P3 records share both formula and scaffold group.")

c(5, "known CE semantics (exactly what quantity, documented where)", "NOT_MET",
  "Three independent routes, all negative. (a) Library field: collision_energy is blank in 9,618/9,618 "
  "REFRAME-POSITIVE-LIBRARY rows and 17,210/17,210 CMMC-REFRAME-POSITIVE-LIBRARY rows of the processed GNPS CSVs "
  "(the 88,424/96,016 total rows include an unrelated 78,806-row MONA_ML_Export block that does carry CE, which "
  "is why a naive count looks non-empty); msDissociationMethod is blank in all of them too. (b) Schema: the GNPS "
  "batch-upload template has no collision-energy field at all, and the GNPS LibraryServlet record for this library "
  "exposes 31 fields, none mentioning energy. (c) Raw data: MassIVE MSV000093469 records exactly one "
  f"collision-energy value, '{list(ce['pos_Top_CEs'])[0]}', covering {ce['pos_ms2_covered_by_top_ce']:,} of "
  f"{ce['pos_ms2_total']:,} positive MS2 scans in all {ce['pos_files']} files. Whether that 37 is NCE percent or "
  "absolute eV is documented nowhere: the MassIVE record is flagged 'Dataset with no associated published "
  "manuscript', and the GNPS Drug Library paper (Nat Commun 2025, s41467-025-65993-5 / PMC12689629) neither "
  "lists MSV000093469 nor describes this acquisition. The quantity is exactly the ambiguity this study exists "
  "to adjudicate, so it cannot be assumed.")

c(6, "[M+H]+ positive mode available", "MET",
  "All 9,620 records are positive mode, Charge 1. [M+H]+ 8,261 records by the GNPS servlet adduct / 8,110 by the "
  "processed CSV adduct ([M+H]1+); the 149-record disagreement is servlet [M+H]+ vs CSV [M]1+ on permanently "
  "charged parents, which the pool drops. Pool P1 ([M+H]+ on both routes, charge-neutral parent) = 8,108 records, "
  f"{pools['P1 [M+H]+ (servlet and processed CSV agree), charge-neutral parent']['keys']} keys.")

c(7, "compatible fragmentation / instrument metadata", "PARTIAL",
  "Compatible at the token level, unverified at the field level. Library metadata: Instrument 'Orbitrap' (9,620/"
  "9,620), msManufacturer Thermo, msMassAnalyzer orbitrap, msIonisation ESI, Ion_Source LC-ESI. Raw data: MassIVE "
  "PROXI instrument 'Q Exactive' (MS:1001911); GNPS2 dataset cache gives MassAnalyzer 'orbitrap;quadrupole', "
  "Ionization 'electrospray inlet;electrospray ionization', classification DDA for all 305 positive files. A "
  "Q Exactive fragments only by beam-type HCD, so HCD is INFERRED from the instrument model, not recorded: "
  "msDissociationMethod is blank in every library row. This maps to the ms-pred token 'Orbitrap' "
  "(src/ms_pred/common/chem_utils.py:277-283, commented '# Orbitrap HCD'), the same token the frozen benchmark "
  "used, and to MURU's Orbitrap HCD deployment class. Not compatible with MURU's fixed NCE20/NCE60 two-rung "
  "deployment, which needs two known normalized energies; this dataset has one unlabelled energy. The other "
  "ms-pred tokens (QTOF, IT-FT = Orbitrap CID, Unknown) do not apply.")

c(8, "multiple energies per compound", "NOT_MET",
  f"One energy, dataset-wide. GNPS2 dataset cache uniquemri reports a single distinct Top_CEs value for every one "
  f"of the {ce['pos_files']} positive mzML files, and Top_CE_Counts equals spectra_ms2 exactly in all of them "
  f"(0 exceptions), so all {ce['pos_ms2_total']:,} positive MS2 scans carry the same recorded collision energy. "
  "The negative files agree (349/350 at the same value; 1 file has no MS2). At the library level the same picture: "
  "7,496 of 8,489 key+adduct pairs have exactly 1 spectrum, and the 854 [M+H]+ keys with several spectra are "
  "plate/well replicates (only 29 of the 854 have two spectra inside one well), not an energy ladder. No "
  "energy-resolved design is "
  "possible from this dataset, with or without spectra access.")

p3 = pools["P3 = P2 and key not in the full MURU exposure registry (conservative)"]
p5 = pools["P5 = P3 and scaffold group not in MURU registry/dev, PR7, comparator groups"]
p8 = pools["P8 = P5 and precursor in 70-1042.6, precursor consistent within 0.01 Da, no co-injected ion/isomer "
           "(lower bound)"]
c(9, "structural diversity and scaffold count after all exclusions", "MET",
  f"Ample in count, weak in identity quality. After all compound-level exclusions (P3): {p3['keys']} keys / "
  f"{p3['scaffold_groups']} MURU scaffold groups ({p3['singleton_scaffold_groups']} singletons). Also excluding "
  f"MURU/PR7/comparator scaffold groups (P5): {p5['keys']} keys / {p5['scaffold_groups']} groups. Adding the "
  f"quality filters (P8: precursor in 70-1042.6 Da, precursor consistent within 0.01 Da, no co-injected annotated "
  f"ion within 0.7 Da and no co-injected isomer): {p8['keys']} keys / {p8['scaffold_groups']} groups. Chemistry is "
  "drug-like, not natural-product-like (largest groups benzene 339 keys, then steroid and tetrahydrofuranyl-"
  "pyrimidinone cores; 1,490 keys contain F, 1,222 Cl). Identity caveat: Compound_Source is 'crude' for all 9,620 "
  "records, the library is typed GNPS-PROPOGATED, compound names carry '(known structural isomers: n; isobaric "
  "peaks in run: m)' pooled-plate annotations, and 3,456 of the 7,152 [M+H]+ keys share a well with another "
  "annotated compound within 0.7 Da (lower bound, since the full plate map is not public).")

c(10, "license and access", "MET",
  "GNPS reference spectra are CC0 by default (GNPS documentation, batch upload page: 'All GNPS Reference spectra "
  "contributed directly to GNPS by default will have the CC0 license'). The processed library CSV and the GNPS "
  "LibraryServlet metadata are anonymous HTTP, no login. Underlying raw data MassIVE MSV000093469 is public "
  "(private=false), doi:10.25345/C5W08WS91, 1,311 files / 39.22 GB, FTP ftp://massive-ftp.ucsd.edu/v06/"
  "MSV000093469/. The ReFrame compound collection itself is a Calibr repurposing library, but the spectra and "
  "their metadata are openly redistributable.")

c(11, "release timing / hidden MassSpecGym inclusion under a different identifier", "MET",
  "Spectrum-level inclusion is excluded for REFRAME and very unlikely for the sibling. MassSpecGym's source "
  "libraries were downloaded 13/05/2024 (notebooks/dataset_construction/1_Load_data_from_repositories.ipynb "
  "cell 0) from 46 named GNPS MGFs (cell 1); neither REFRAME-POSITIVE-LIBRARY nor any CMMC library is in that "
  "list, and GNPS-LIBRARY.mgf, which is in it, is the user-contribution library rather than an aggregate of all "
  "named libraries. REFRAME-POSITIVE-LIBRARY's own accessions postdate the download outright: create_time "
  "2024-11-22 (36 spectra, CCMSLIB00013568884-13569949) and 2025-07-04 (9,584 spectra, "
  "CCMSLIB00016142638-16153191), both from GNPS ADD-BATCH-ANNOTATED tasks on d.MSV000093469. MassSpecGym 1.5 "
  "changed only SMILES canonicalization, so no compound entered later. The sibling CMMC-REFRAME-POSITIVE-LIBRARY "
  "(CCMSLIB00012246958-12273429) has no public servlet listing (HTTP 500 on two attempts) so its dates are "
  "unknown; calibrating the global accession counter against CMMC-LIBRARY gives 12.1M = 2024-02-02..03-28 and "
  "12.4M = 2024-05-01..05-09, so CMMC-REFRAME was deposited around April 2024, i.e. before the MassSpecGym "
  "download, and its exclusion rests on its absence from the 46-library list rather than on timing. Compound-level "
  "co-presence is a separate matter and is large (2,646 keys), but it is handled by criterion 4's exclusion.")

out = {
    "candidate": "C08 GNPS REFRAME-POSITIVE-LIBRARY (sibling CMMC-REFRAME-POSITIVE-LIBRARY)",
    "task": "S8",
    "verdict": "UNSUITABLE",
    "verdict_reason": ("Criteria 5 and 8 fail decisively and the failure is not an access problem. The library "
                       "carries no collision-energy field by construction (the GNPS batch-upload schema has none), "
                       "and the underlying acquisition used a single collision energy for 100% of its 771,634 "
                       "positive MS2 scans, whose unit (NCE percent vs absolute eV) is undocumented and has no "
                       "associated manuscript. Downloading spectra could only confirm the single energy, not "
                       "supply a second one or a documented quantity, so the verdict is UNSUITABLE rather than "
                       "UNRESOLVED_NEEDS_SPECTRA_OR_ACCESS."),
    "criteria": C,
    "headline_counts": {
        "library_records": ov["records"],
        "parent_keys": ov["keys"],
        "scaffold_groups": ov["scaffold_groups"],
        "mh_keys": pools["P1 [M+H]+ (servlet and processed CSV agree), charge-neutral parent"]["keys"],
        "mh_keys_after_msg15": pools["P1b = P1 and key not in MassSpecGym 1.5 (either key route) only"]["keys"],
        "mh_keys_after_all_compound_level_exclusions_P3": p3["keys"],
        "scaffold_groups_P3": p3["scaffold_groups"],
        "mh_keys_after_scaffold_exclusion_P5": p5["keys"],
        "scaffold_groups_P5": p5["scaffold_groups"],
        "mh_keys_P8_quality_filtered": p8["keys"],
        "scaffold_groups_P8": p8["scaffold_groups"],
        "distinct_collision_energies": 1,
    },
    "inputs": {"screen_summary.json": s1["inputs"], "verify_summary.json": s2["identity_csv"]},
}
(SCREEN / "s8_criteria.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
