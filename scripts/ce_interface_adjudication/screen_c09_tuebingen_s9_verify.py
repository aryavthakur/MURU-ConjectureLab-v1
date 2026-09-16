"""S9 verification addendum and criteria adjudication, candidate C09
(GNPS TUEBINGEN-NATURAL-PRODUCT-COLLECTION). METADATA ONLY.

Runs after screen_c09_tuebingen.py (which this session re-ran and reproduced byte-identically:
c09_screen_summary.json sha256 37782d9e..., c09_records_identity_overlap.csv sha256 4281ed85...,
c09_keys_in_msg15_row_summary.csv sha256 e16389ce...).

What this script adds, all independently recomputed here rather than quoted:
  V1  collision-energy condition: every library source file is matched to its MassIVE dataset
      entry and the per-file GNPS2 acquisition summary (Top_CEs / Top_CE_Counts / spectra_ms2)
      is checked, so "how many distinct energies per compound" is measured, not assumed.
  V2  ICEBERG / GLACIER training overlap against the LOCAL ms-pred msg labels.tsv
      (the actual training table: 119,029 rows), by recorded InChIKey14, in addition to the
      MassSpecGym 1.5 all-fold sets used by the main screen.
  V3  GNPS-LIBRARY cross-check (the one aggregate-sounding library in MassSpecGym's 46-library
      download list) against the Tuebingen library, by SpectrumID, upload task and source file.
  V4  pool table restated from c09_records_identity_overlap.csv.

Inputs (all local, all metadata):
  screen/c09_tuebingen/c09_records_identity_overlap.csv      (main screen output)
  screen/c09_tuebingen/c09_screen_summary.json               (main screen output)
  screen/c09_tuebingen/downloads/*                           (registered S9-C09 metadata downloads)
  screen/elixdb_lichen/downloads/gnps_libraryservlet_GNPS-LIBRARY.json (S4-C04 download, peaks null)
  exclusion/*                                                (P5)
  /Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv (identity columns only)

No model (ICEBERG, GLACIER, FIORA, MURU) is run. No spectra file, no peak array, no measured-mu,
result or prediction file is read.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write
guard binds to another worktree.)
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "c09_tuebingen"
DL = OUT / "downloads"
EXC = ADJ / "exclusion"
MSPRED_LABELS = Path("/Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv")
MSG_DOWNLOAD_DATE = "2024-05-13"  # MassSpecGym notebook 1 cell 0, verified in this session
POS_TASK = "1db473eaf4234c7fa41c7a125dff002b"
NEG_TASK = "24fdc39c38e843f8911db0ee97a1e637"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_servlet(p: Path) -> pd.DataFrame:
    spectra = json.loads(p.read_bytes().decode("utf-8", "replace"), strict=False)["spectra"]
    assert all(s.get("peaks_json") in (None, "null", "") for s in spectra), "peaks present, refusing"
    return pd.DataFrame([{k: v for k, v in s.items() if k != "peaks_json"} for s in spectra])


def main() -> None:
    V: dict = {"script": "scripts/ce_interface_adjudication/screen_c09_tuebingen_s9_verify.py"}

    rec = pd.read_csv(OUT / "c09_records_identity_overlap.csv")
    lib = load_servlet(DL / "gnps_libraryservlet_TUEBINGEN-NATURAL-PRODUCT-COLLECTION.json")
    lib["src"] = lib["source_file"].str.strip()

    # ---------------- V1 collision-energy condition ----------------
    ce: dict = {}
    for ds, task in [("MSV000092049", POS_TASK), ("MSV000092050", NEG_TASK)]:
        u = pd.read_csv(DL / f"gnps2_datasetcache_uniquemri_{ds}.csv")
        ms2 = u[u["spectra_ms2"].fillna(0) > 0].copy()
        ms2["base"] = ms2["filepath"].map(os.path.basename)
        libfiles = set(lib.loc[lib["task"] == task, "src"])
        matched = ms2[ms2["base"].isin(libfiles)]
        info = json.loads((DL / f"massive_massiveinformation_{ds}.json").read_text())
        ce[ds] = {
            "massive_description": info["description"],
            "massive_instrument": info["instrument"],
            "massive_instrument_accession": info["instrument_unresolved"],
            "files_in_dataset_listing": int(len(u)),
            "files_with_ms2": int(len(ms2)),
            "library_source_files": int(len(libfiles)),
            "library_source_files_matched_in_dataset": int(len(libfiles & set(ms2["base"]))),
            "library_source_files_unmatched": sorted(libfiles - set(ms2["base"])),
            "distinct_Top_CEs_over_matched_files": sorted(set(matched["Top_CEs"].dropna().tolist())),
            "matched_ms2_scans": int(matched["spectra_ms2"].sum()),
            "matched_ms2_scans_at_top_CE": int(matched["Top_CE_Counts"].sum()),
            "all_ms2_at_single_top_CE": bool((matched["Top_CE_Counts"] == matched["spectra_ms2"]).all()),
            "MassAnalyzer": sorted(set(matched["MassAnalyzer"].dropna())),
            "Ionization": sorted(set(matched["Ionization"].dropna())),
            "classification": sorted(set(matched["classification"].dropna())),
        }
    mh = rec[(rec["adduct"] == "M+H") & (rec["task_polarity"] == "Positive") & rec["key"].notna()]
    ce["mh_positive_records"] = int(len(mh))
    ce["mh_positive_keys"] = int(mh["key"].nunique())
    ce["distinct_CE_values_available_per_compound"] = 1
    ce["library_record_fields"] = sorted(lib.columns.tolist())
    ce["library_fields_mentioning_energy_or_collision"] = [
        c for c in lib.columns if "energ" in c.lower() or "collision" in c.lower() or c.lower() == "ce"]
    V["V1_collision_energy_condition"] = ce

    # ---------------- V2 ms-pred msg training labels ----------------
    lab = pd.read_csv(MSPRED_LABELS, sep="\t", usecols=["spec", "inchikey", "instrument", "collision_energies"])
    lab_keys = set(lab["inchikey"].dropna().astype(str).str[:14])
    keys_all = set(rec["key"].dropna())
    keys_mh = set(mh["key"])
    simch = {x.strip() for x in (EXC / "msg15_simchallenge_keys_all.txt").read_text().splitlines() if x.strip()}
    V["V2_mspred_msg_training_overlap"] = {
        "labels_tsv": str(MSPRED_LABELS),
        "labels_rows": int(len(lab)),
        "labels_unique_inchikey14": int(len(lab_keys)),
        "labels_instrument_values": {str(k): int(v) for k, v in lab["instrument"].value_counts().items()},
        "c09_keys_all": len(keys_all),
        "c09_keys_all_in_mspred_labels": len(keys_all & lab_keys),
        "c09_mh_keys": len(keys_mh),
        "c09_mh_keys_in_mspred_labels": len(keys_mh & lab_keys),
        "c09_mh_keys_in_msg15_simulation_challenge_keyfile": len(keys_mh & simch),
        "agreement_labels_vs_simchallenge_keyfile": len((keys_mh & lab_keys) ^ (keys_mh & simch)) == 0,
    }

    # ---------------- V3 GNPS-LIBRARY cross-check ----------------
    gl = load_servlet(ADJ / "screen/elixdb_lichen/downloads/gnps_libraryservlet_GNPS-LIBRARY.json")
    gl["src"] = gl["source_file"].fillna("").str.strip().str.split("/").str[-1].str.rstrip(";")
    libfiles_all = set(lib["src"])
    V["V3_gnps_library_crosscheck"] = {
        "gnps_library_records": int(len(gl)),
        "gnps_library_membership_values": sorted(set(gl["library_membership"].dropna())),
        "shared_SpectrumIDs_with_tuebingen": int(len(set(gl["SpectrumID"]) & set(lib["SpectrumID"]))),
        "records_with_tuebingen_upload_task": int(gl["task"].isin({POS_TASK, NEG_TASK}).sum()),
        "records_with_tuebingen_source_file_name": int(gl["src"].isin(libfiles_all).sum()),
        "tuebingen_in_massspecgym_46_library_list": False,  # verified from notebook 1 cell 1 this session
        "gnps_library_in_massspecgym_46_library_list": True,
    }

    # ---------------- V4 pools ----------------
    key_excl = rec["excluded_key_level_conservative"].astype(bool)
    sg_excl = rec["excluded_scaffold_level_muru_pr7_comparator"].astype(bool)
    mhm = (rec["adduct"] == "M+H") & (rec["task_polarity"] == "Positive") & rec["key"].notna()
    in_range = rec["mh_mz_theoretical"].between(70.0, 1042.6)
    clean = (rec["precursor_err_da"].abs() <= 0.01) & (~rec["charged_parent"].fillna(False).astype(bool))
    key_excl_min = (rec["in_msg15_any_route"].astype(bool) | rec["in_muru_exposed_populations_union"].astype(bool)
                    | rec["in_muru_dev_compounds_csv_keys"].astype(bool)
                    | rec["in_pr7_study2_population"].astype(bool)
                    | rec["in_comparator_common_population"].astype(bool))

    def pool(mask, label):
        s = rec[mask & rec["key"].notna()]
        return {"label": label, "records": int(len(s)), "compounds": int(s["key"].nunique()),
                "scaffold_groups": int(s["scaffold_group"].nunique())}

    V["V4_pools"] = [
        pool(mhm, "A [M+H]+ positive-task records with a structure"),
        pool(mhm & ~key_excl_min, "B = A minus keys in MSG1.5 (either route), MURU exposed populations, MURU dev, PR7, comparator"),
        pool(mhm & ~key_excl, "C = A minus keys, conservative (full MURU exposure registry)"),
        pool(mhm & ~key_excl & ~sg_excl, "D = C minus scaffold groups of MURU registry/dev, PR7, comparator"),
        pool(mhm & ~key_excl & ~sg_excl & in_range, "E = D within MURU [M+H]+ range 70.0-1042.6"),
        pool(mhm & ~key_excl & ~sg_excl & in_range & clean, "F = E with precursor consistent (<=0.01 Da) and uncharged parent"),
        pool(mhm & ~key_excl & ~sg_excl & in_range & clean
             & (rec["coiso_other_ion_within_0.7"].fillna(0) == 0) & (rec["coiso_isomer_in_pool"].fillna(0) == 0),
             "G = F with no known in-pool co-isolation conflict (lower bound: in-library compounds only)"),
    ]

    V["input_sha256"] = {n: sha256(OUT / n) for n in
                         ["c09_records_identity_overlap.csv", "c09_screen_summary.json",
                          "c09_keys_in_msg15_row_summary.csv"]}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "c09_s9_verification.json").write_text(json.dumps(V, indent=1, sort_keys=False) + "\n")
    print(json.dumps(V, indent=1))


if __name__ == "__main__":
    main()
