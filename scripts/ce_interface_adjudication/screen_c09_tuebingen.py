"""S9 screen, candidate C09: GNPS TUEBINGEN-NATURAL-PRODUCT-COLLECTION. ANALYSIS (metadata only).

Inputs (all metadata, fetched by screen_c09_tuebingen_fetch.py and registered in downloads_register.jsonl):
  screen/c09_tuebingen/downloads/gnps_libraryservlet_TUEBINGEN-NATURAL-PRODUCT-COLLECTION.json (peaks_json null)
  screen/c09_tuebingen/downloads/gnps_task_*_{status.json,params.xml}
  screen/c09_tuebingen/downloads/massive_*_MSV000092049.json, massive_massiveinformation_MSV000092050.json
  screen/c09_tuebingen/downloads/gnps2_datasetcache_{filelist,uniquemri}_MSV00009204{9,50}.csv
  screen/c09_tuebingen/downloads/MassSpecGym_nb1_Load_data_from_repositories_5a34ede.ipynb (GitHub API JSON)
  screen/elixdb_lichen/downloads/gnps_libraryservlet_GNPS-LIBRARY.json (S4-C04 download, peaks_json null)
  exclusion/* (P5), massspecgym15_metadata_columns.parquet (P4), artifacts/wur_v2/data/compounds.csv (ONLY the
  identity columns parent_key, scaffold_group are loaded).

No model (ICEBERG, GLACIER, FIORA, MURU) is run. No measured-mu, result or prediction file is read.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import base64
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors, rdMolDescriptors

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "c09_tuebingen"
DL = OUT / "downloads"
EXC = ADJ / "exclusion"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_c09_tuebingen.py"
LIB = "TUEBINGEN-NATURAL-PRODUCT-COLLECTION"
MSG_DOWNLOAD_DATE = "2024-05-13"  # MassSpecGym notebook 1 cell 0

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scaffold_key as SK  # noqa: E402

PROTON = 1.007276
ADDUCT_SHIFT = {  # (multiplier, shift) for theoretical m/z of the recorded adduct label
    "M+H": (1, PROTON), "M+Na": (1, 22.989218), "M+NH4": (1, 18.033823), "M-H": (1, -PROTON),
    "M+Cl-": (1, 34.969402), "M+FA-": (1, 44.998201)}
POS_ADDUCTS = {"M+H", "M+Na", "M+NH4"}
COISO_IONS = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
              "[M-H2O+H]+": PROTON - 18.010565, "[M+H]+13C": PROTON + 1.003355, "[M]+": -0.000549}
NA = {"", "N/A", "NA", "null", "None", " "}


def read_keys(p: Path) -> set[str]:
    return {x.strip() for x in p.read_text().splitlines() if x.strip()}


def load_servlet(p: Path) -> pd.DataFrame:
    spectra = json.loads(p.read_bytes().decode("utf-8", "replace"), strict=False)["spectra"]
    assert all(s.get("peaks_json") in (None, "null", "") for s in spectra)
    return pd.DataFrame(spectra).drop(columns=["peaks_json"])


def smiles_for(r) -> tuple[str | None, str]:
    s = (r["Smiles"] or "").strip()
    if s not in NA:
        return s, "gnps_smiles"
    i = (r["INCHI"] or "").strip().strip('"')
    if i not in NA and i.startswith("InChI="):
        m = Chem.MolFromInchi(i)
        if m is not None:
            return Chem.MolToSmiles(m), "gnps_inchi_to_smiles"
    return None, "no_structure"


def main() -> None:
    S: dict = {"script": SCRIPT_REL, "rdkit": rdBase.rdkitVersion, "frozen_rdkit": SK.FROZEN_RDKIT}
    g = load_servlet(DL / f"gnps_libraryservlet_{LIB}.json")
    g["source_file_clean"] = g["source_file"].str.strip()
    S["n_records"] = len(g)
    S["fields"] = sorted(g.columns)
    S["fields_mentioning_energy_or_collision"] = [c for c in g.columns if re.search(r"energ|collision|nce", c, re.I)]
    for c in ["Adduct", "Ion_Mode", "Instrument", "Ion_Source", "Charge", "ms_level", "Library_Class",
              "Compound_Source", "PI", "Data_Collector", "submit_user", "task", "library_membership",
              "spectrum_status", "Pubmed_ID", "CAS_Number"]:
        S[f"counts_{c}"] = dict(collections.Counter(g[c]).most_common(15))
    S["counts_create_time_date"] = dict(collections.Counter(g["create_time"].str[:10]))
    S["smiles_missing_records"] = int(g["Smiles"].str.strip().isin(NA).sum())
    S["inchi_present_records"] = int((~g["INCHI"].str.strip().str.strip('"').isin(NA)).sum())

    # task provenance
    tasks = {}
    for t in sorted(g["task"].unique()):
        st = json.loads((DL / f"gnps_task_{t}_status.json").read_text())
        px = (DL / f"gnps_task_{t}_params.xml").read_text()
        files = re.findall(r'name="upload_file_mapping">spec-\d+\.mzML\|([^<]+)<', px)
        tasks[t] = {"description": st["description"], "workflow": st["workflow"], "createtime": st["createtime"],
                    "user": st["user"], "n_spectrum_files": len(files),
                    "spec_dir": re.search(r'name="spec_on_server">([^<]+)<', px).group(1),
                    "annotation_table": re.search(r'name="annotation_table_on_server">([^<]+)<', px).group(1),
                    "file_basenames": sorted(f.split("/")[-1] for f in files)}
    S["upload_tasks"] = tasks
    pos_task = [t for t, v in tasks.items() if "POS" in v["description"]][0]
    neg_task = [t for t, v in tasks.items() if "NEG" in v["description"]][0]
    g["task_polarity"] = g["task"].map({pos_task: "Positive", neg_task: "Negative"})
    g["adduct_polarity"] = g["Adduct"].map(lambda a: "Positive" if a in POS_ADDUCTS else "Negative")
    bad_pol = g[(g["Ion_Mode"] != g["task_polarity"]) | (g["adduct_polarity"] != g["task_polarity"])]
    S["polarity_inconsistent_records"] = bad_pol[["SpectrumID", "Compound_Name", "Adduct", "Ion_Mode", "task_polarity",
                                                  "source_file", "scan", "create_time"]].to_dict("records")
    S["records_source_file_not_in_task_file_list"] = int(sum(
        sf not in tasks[t]["file_basenames"] for sf, t in zip(g["source_file_clean"], g["task"])))

    # MassIVE acquisition metadata
    acq = {}
    for msv in ["MSV000092049", "MSV000092050"]:
        info = json.loads((DL / f"massive_massiveinformation_{msv}.json").read_text(), strict=False)
        u = pd.read_csv(DL / f"gnps2_datasetcache_uniquemri_{msv}.csv")
        u2 = u[u["spectra_ms2"] > 0]
        acq[msv] = {k: info.get(k) for k in ["title", "instrument", "description", "doi", "filesize", "filecount",
                                             "private", "publications", "user"]}
        acq[msv]["uniquemri_files_with_ms2"] = int(len(u2))
        acq[msv]["uniquemri_Top_CEs_counts"] = dict(collections.Counter(u2["Top_CEs"].astype(str)))
        acq[msv]["uniquemri_all_ms2_at_top_ce"] = bool((u2["Top_CE_Counts"] == u2["spectra_ms2"]).all())
        acq[msv]["uniquemri_MassAnalyzer"] = dict(collections.Counter(u2["MassAnalyzer"]))
        acq[msv]["uniquemri_classification"] = dict(collections.Counter(u2["classification"]))
        acq[msv]["uniquemri_RT_Range_in_Min"] = dict(collections.Counter(u2["RT_Range_in_Min"].astype(str)))
        acq[msv]["uniquemri_ms2_total"] = int(u2["spectra_ms2"].sum())
        acq[msv]["mzml_basenames"] = sorted({p.split("/")[-1] for p in u2["filepath"]})
        lib_task = pos_task if "Positive" in info["title"] else neg_task
        acq[msv]["library_task_files_found_in_dataset"] = (
            f"{sum(b in acq[msv]['mzml_basenames'] for b in tasks[lib_task]['file_basenames'])}"
            f"/{len(tasks[lib_task]['file_basenames'])}")
    S["massive_acquisition"] = {k: {kk: vv for kk, vv in v.items() if kk != "mzml_basenames"} for k, v in acq.items()}

    # MassSpecGym 46 GNPS libraries (notebook 1 cell 1)
    nbj = json.loads((DL / "MassSpecGym_nb1_Load_data_from_repositories_5a34ede.ipynb").read_text())
    nb = json.loads(base64.b64decode(nbj["content"]))
    cell1 = "".join(nb["cells"][1]["source"])
    libs = re.findall(r"'([A-Za-z0-9_\-]+)\.mgf'", cell1)
    S["msg_gnps_libraries_n"] = len(libs)
    S["msg_gnps_libraries_contains_tuebingen"] = any("TUEBINGEN" in x.upper() for x in libs)
    S["msg_gnps_libraries_contains_GNPS-LIBRARY"] = "GNPS-LIBRARY" in libs

    # identity
    rows = []
    for r in g.to_dict("records"):
        smi, route = smiles_for(r)
        k, sg = SK.key_and_group(smi) if smi else (None, None)
        rec = {"spectrum_id": r["SpectrumID"], "compound_name": r["Compound_Name"], "adduct": r["Adduct"],
               "ion_mode": r["Ion_Mode"], "task_polarity": r["task_polarity"], "source_file": r["source_file_clean"],
               "scan": r["scan"], "create_time": r["create_time"], "precursor_mz_gnps": float(r["Precursor_MZ"]),
               "exact_mass_gnps": float(r["ExactMass"]), "structure_route": route, "smiles_used": smi,
               "key": k, "scaffold_group": sg}
        pm = SK.parent_mol(smi) if k else None
        if pm is not None:
            mono = Descriptors.ExactMolWt(pm)
            rec["formula_parent"] = rdMolDescriptors.CalcMolFormula(pm)
            rec["mono_parent"] = mono
            m, sh = ADDUCT_SHIFT.get(r["Adduct"], (None, None))
            rec["theoretical_mz"] = m * mono + sh if m else None
            rec["precursor_err_da"] = rec["precursor_mz_gnps"] - rec["theoretical_mz"] if m else None
            rec["mh_mz_theoretical"] = mono + PROTON
            rec["elements"] = ";".join(sorted({a.GetSymbol() for a in Chem.AddHs(pm).GetAtoms()}))
            m0 = Chem.MolFromSmiles(smi)
            rec["n_components_raw"] = len(smi.split("."))
            rec["charged_raw"] = sum(a.GetFormalCharge() for a in m0.GetAtoms()) != 0
            rec["charged_parent"] = sum(a.GetFormalCharge() for a in pm.GetAtoms()) != 0  # NET charge (nitro groups are neutral)
            rec["heavy_atoms"] = pm.GetNumHeavyAtoms()
        rows.append(rec)
    df = pd.DataFrame(rows)
    S["records_with_key"] = int(df["key"].notna().sum())
    S["records_by_structure_route"] = dict(collections.Counter(df["structure_route"]))
    S["records_structure_unparsed"] = df.loc[df["key"].isna() & (df["structure_route"] != "no_structure"),
                                             ["compound_name", "smiles_used"]].to_dict("records")
    S["unique_keys_all"] = int(df["key"].nunique())
    S["unique_scaffold_groups_all"] = int(df["scaffold_group"].nunique())
    bad = df[df["precursor_err_da"].abs() > 0.01]
    S["precursor_inconsistent_gt_0.01Da"] = int(len(bad))
    S["precursor_inconsistent_by_adduct"] = dict(collections.Counter(bad["adduct"]))
    S["precursor_inconsistent_examples"] = bad[["compound_name", "adduct", "precursor_mz_gnps", "theoretical_mz",
                                                "precursor_err_da"]].head(15).round(4).to_dict("records")
    S["precursor_err_da_quantiles_consistent"] = df.loc[df["precursor_err_da"].abs() <= 0.01,
                                                        "precursor_err_da"].quantile([0, .05, .5, .95, 1]).round(5).tolist()
    S["charged_parent_records"] = int(df["charged_parent"].fillna(False).astype(bool).sum())
    S["multicomponent_raw_records"] = int((df["n_components_raw"].fillna(1) > 1).sum())

    # names mapping to multiple keys / keys with multiple names (identity defects)
    kd = df[df["key"].notna()]
    nk = kd.groupby("compound_name")["key"].nunique()
    kn = kd.groupby("key")["compound_name"].nunique()
    S["compound_names_with_multiple_keys"] = int((nk > 1).sum())
    S["keys_with_multiple_compound_names"] = int((kn > 1).sum())
    S["keys_with_multiple_compound_names_examples"] = [
        {"key": k, "names": sorted(kd.loc[kd["key"] == k, "compound_name"].unique())[:5]}
        for k in kn[kn > 1].index[:12]]

    # energies per compound
    mh = df[(df["adduct"] == "M+H") & (df["task_polarity"] == "Positive")]
    per = mh.groupby("key").agg(n_mh=("spectrum_id", "size"), n_files=("source_file", "nunique"))
    S["mh_records_positive_task"] = int(len(mh))
    S["mh_records_per_key_distribution"] = dict(collections.Counter(per["n_mh"]))
    S["mh_keys_with_records_from_multiple_files"] = int((per["n_files"] > 1).sum())
    S["mh_records_per_file_scan_max"] = int(mh.groupby(["source_file", "scan"]).size().max())
    S["positive_adduct_records_per_key_distribution"] = dict(collections.Counter(
        df[(df["task_polarity"] == "Positive") & df["key"].notna()].groupby("key").size()))

    # within-pool co-isolation (lower bound: only compounds that made it into the library are known)
    pos = df[(df["task_polarity"] == "Positive") & df["key"].notna()].drop_duplicates(["source_file", "key"])
    co_rows = []
    for rr in mh[mh["key"].notna()].itertuples():
        others = pos[(pos["source_file"] == rr.source_file) & (pos["key"] != rr.key)]
        hit_ion = hit_iso = 0
        for o in others.itertuples():
            if o.formula_parent == rr.formula_parent:
                hit_iso += 1
            if any(abs(o.mono_parent + sh - rr.mh_mz_theoretical) <= 0.7 for sh in COISO_IONS.values()):
                hit_ion += 1
        co_rows.append({"spectrum_id": rr.spectrum_id, "pool_library_keys": int(others["key"].nunique()) + 1,
                        "coiso_other_ion_within_0.7": hit_ion, "coiso_isomer_in_pool": hit_iso})
    co = pd.DataFrame(co_rows)
    df = df.merge(co, on="spectrum_id", how="left")
    S["pool_library_keys_per_positive_file"] = dict(collections.Counter(pos.groupby("source_file")["key"].nunique()))
    S["mh_records_with_library_coisolation_conflict"] = int(((co["coiso_other_ion_within_0.7"] > 0)
                                                             | (co["coiso_isomer_in_pool"] > 0)).sum())

    # exclusion sets
    sets = {
        "msg15_recorded_all": read_keys(EXC / "msg15_keys_all.txt"),
        "msg15_parent_all": read_keys(EXC / "msg15_parent_keys_all.txt"),
        "msg15_simchallenge_all": read_keys(EXC / "msg15_simchallenge_keys_all.txt"),
        "msg15_recorded_train": read_keys(EXC / "msg15_keys_train.txt"),
        "msg15_recorded_val": read_keys(EXC / "msg15_keys_val.txt"),
        "msg15_recorded_test": read_keys(EXC / "msg15_keys_test.txt"),
        "muru_registry_all": read_keys(EXC / "muru_exposure_registry_keys.txt"),
        "muru_registry_direct_reason": read_keys(EXC / "muru_exposure_registry_keys_direct_reason.txt"),
        "muru_exposed_union": read_keys(EXC / "muru_exposed_union_keys.txt"),
        "pr7_study2_population": read_keys(EXC / "msnlib_study2_population_keys.txt"),
        "comparator_common_population": read_keys(EXC / "comparator_common_population_keys.txt"),
        "msnlib_9lib": read_keys(EXC / "msnlib_9lib_keys.txt"),
        "msnlib_v1_0_4lib": read_keys(EXC / "msnlib_v1_0_4lib_keys.txt"),
        "multims2_reserved_validation_secondary": read_keys(EXC / "multims2_reserved_validation_secondary_keys.txt"),
    }
    pops = {p.name[len("muru_exposure_registry_population_"):-len("_keys.txt")]: read_keys(p)
            for p in sorted(EXC.glob("muru_exposure_registry_population_*_keys.txt"))}
    sets["muru_exposed_populations_union"] = set().union(*pops.values())
    dev = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv", usecols=["parent_key", "scaffold_group"])
    sets["muru_dev_compounds_csv_keys"] = set(dev["parent_key"].dropna())
    groups = {
        "msg15_scaffold_groups": read_keys(EXC / "msg15_scaffold_groups_all.txt"),
        "muru_registry_scaffold_groups": read_keys(EXC / "muru_exposure_registry_scaffold_groups.txt"),
        "muru_dev_scaffold_groups": set(dev["scaffold_group"].dropna()),
        "pr7_scaffold_groups": read_keys(EXC / "msnlib_study2_population_scaffold_groups.txt"),
        "comparator_scaffold_groups": read_keys(EXC / "comparator_common_population_scaffold_groups.txt"),
    }
    S["exclusion_set_sizes"] = {k: len(v) for k, v in {**sets, **groups}.items()}
    for k, v in sets.items():
        df[f"in_{k}"] = df["key"].isin(v)
    for k, v in pops.items():
        df[f"in_pop_{k}"] = df["key"].isin(v)
    for k, v in groups.items():
        df[f"sg_in_{k}"] = df["scaffold_group"].isin(v)
    df["in_msg15_any_route"] = df["in_msg15_recorded_all"] | df["in_msg15_parent_all"]

    kdf = df[df["key"].notna()]
    ov = {}
    for sub, m in [("all", kdf["key"].notna()), ("M+H_positive_task", (kdf["adduct"] == "M+H") & (kdf["task_polarity"] == "Positive")),
                   ("positive_task", kdf["task_polarity"] == "Positive"), ("negative_task", kdf["task_polarity"] == "Negative")]:
        s = kdf[m]
        d = {"records": int(len(s)), "keys": int(s["key"].nunique()), "scaffold_groups": int(s["scaffold_group"].nunique())}
        for col in [c for c in kdf.columns if c.startswith("in_") or c.startswith("sg_in_")]:
            d[col + "__unique_keys"] = int(s.loc[s[col], "key"].nunique())
        ov[sub] = d
    S["overlap_unique_keys_by_subset"] = ov

    # MSG rows for overlapping keys
    msg = pd.read_parquet(EXC / "msg_row_msnlib_membership.parquet",
                          columns=["identifier", "identifier_num", "inchikey14", "parent_key14", "fold",
                                   "simulation_challenge", "adduct", "instrument_type", "collision_energy",
                                   "in_msnlib_v1_compound", "key_first_identifier_num"])
    ek = set(kdf["key"])
    mrows = msg[msg["inchikey14"].isin(ek) | msg["parent_key14"].isin(ek)].copy()
    mrows["k"] = [a if a in ek else b for a, b in zip(mrows["parent_key14"], mrows["inchikey14"])]
    mrows["region"] = pd.cut(mrows["key_first_identifier_num"], [0, 190000, 239028, 10**9],
                             labels=["A_lt190000_MassBank_MoNA_mixed", "B_190000_239028_MSnLib_dense_or_mixed",
                                     "C_ge239029_GNPS_first"])
    mh_keys = set(mh["key"].dropna())
    S["msg_rows_matching_keys"] = {
        "rows": int(len(mrows)), "keys": int(mrows["k"].nunique()),
        "mh_positive_keys_in_msg": int(len(mh_keys & set(mrows["k"]))),
        "instrument_type": dict(collections.Counter(mrows["instrument_type"].fillna("NA"))),
        "adduct": dict(collections.Counter(mrows["adduct"])),
        "fold_rows": dict(collections.Counter(mrows["fold"])),
        "fold_keys": {f: int(mrows.loc[mrows["fold"] == f, "k"].nunique()) for f in ["train", "val", "test"]},
        "simulation_challenge_rows": int(mrows["simulation_challenge"].sum()),
        "simulation_challenge_keys": int(mrows.loc[mrows["simulation_challenge"], "k"].nunique()),
        "ce_nonnull_rows": int(mrows["collision_energy"].notna().sum()),
        "first_appearance_region_keys": {str(r): int(mrows.loc[mrows["region"] == r, "k"].nunique())
                                         for r in mrows["region"].cat.categories},
        "keys_only_ce_missing_orbitrap_rows": int(mrows.groupby("k").apply(
            lambda x: bool(x["collision_energy"].isna().all() and (x["instrument_type"] == "Orbitrap").all())).sum()),
    }
    perkey = mrows.groupby("k").agg(
        n_rows=("identifier", "size"), first_identifier=("key_first_identifier_num", "min"),
        instruments=("instrument_type", lambda x: ";".join(sorted(set(x.fillna("NA"))))),
        adducts=("adduct", lambda x: ";".join(sorted(set(x)))),
        folds=("fold", lambda x: ";".join(sorted(set(x)))),
        sim_rows=("simulation_challenge", "sum"),
        ce_nonnull_rows=("collision_energy", lambda x: int(x.notna().sum()))).reset_index()
    names = kdf.groupby("key")["compound_name"].first()
    perkey["tuebingen_name"] = perkey["k"].map(names)

    # hidden-inclusion proxies
    mk = pd.read_parquet(EXC / "msg15_row_keys.parquet", columns=["identifier", "parent_key", "scaffold_group"])
    mm = pd.read_parquet(ADJ / "massspecgym15_metadata_columns.parquet", columns=["identifier", "formula"])
    mk = mk.merge(mm, on="identifier", how="left")
    form_sg = set(zip(mk["formula"], mk["scaffold_group"]))
    df["formula_in_msg"] = df["formula_parent"].isin(set(mk["formula"]))
    df["formula_and_scaffold_in_msg"] = [(f, s) in form_sg for f, s in zip(df["formula_parent"], df["scaffold_group"])]
    gl = load_servlet(ADJ / "screen/elixdb_lichen/downloads/gnps_libraryservlet_GNPS-LIBRARY.json")
    gl["source_file_clean"] = gl["source_file"].str.strip().str.split("/").str[-1].str.rstrip(";")
    tfiles = {b for v in tasks.values() for b in v["file_basenames"]}
    same_files = gl[gl["source_file_clean"].isin(tfiles)]
    petras = gl[gl["PI"].fillna("").str.contains("Petras") | gl["Data_Collector"].fillna("").str.contains("Vitale|Geibel")]
    keys_gl = []
    for r in gl.to_dict("records"):
        s = (r["Smiles"] or "").strip()
        k, _ = SK.key_and_group(s) if s not in NA else (None, None)
        keys_gl.append(k)
    gl["key"] = keys_gl
    gl_pre = gl[gl["create_time"].str[:10] < MSG_DOWNLOAD_DATE]
    S["gnps_library_crosscheck"] = {
        "gnps_library_records_current_listing": int(len(gl)),
        "records_with_tuebingen_source_file_names": int(len(same_files)),
        "records_PI_Petras_or_collector_Vitale_Geibel": int(len(petras)),
        "records_PI_Petras_or_collector_Vitale_Geibel_before_msg_download": int(
            (petras["create_time"].str[:10] < MSG_DOWNLOAD_DATE).sum()),
        "petras_records_sharing_tuebingen_keys": int(petras["key"].isin(ek).sum()) if "key" in petras else None,
        "tuebingen_keys_in_gnps_library_pre_2024-05-13_records": int(len(ek & set(gl_pre["key"].dropna()))),
        "tuebingen_mh_keys_in_gnps_library_pre_2024-05-13_records": int(len(mh_keys & set(gl_pre["key"].dropna()))),
    }
    petras = gl[gl.index.isin(petras.index)]
    S["gnps_library_crosscheck"]["petras_records_sharing_tuebingen_keys"] = int(petras["key"].isin(ek).sum())

    # pools after exclusion
    def pool(mask, label):
        s = df[mask & df["key"].notna()]
        sgc = s.groupby("scaffold_group")["key"].nunique().sort_values(ascending=False)
        return {"label": label, "records": int(len(s)), "keys": int(s["key"].nunique()),
                "scaffold_groups": int(s["scaffold_group"].nunique()),
                "acyclic_keys": int(s.loc[s["scaffold_group"].str.startswith("__ACYCLIC__"), "key"].nunique()),
                "largest_scaffold_group_key_counts": [int(x) for x in sgc.head(8).values],
                "largest_scaffold_groups": [str(x)[:80] for x in sgc.head(5).index],
                "singleton_scaffold_groups": int((sgc == 1).sum()),
                "precursor_mz_min_max": [round(float(s["precursor_mz_gnps"].min()), 4),
                                         round(float(s["precursor_mz_gnps"].max()), 4)] if len(s) else None,
                "precursor_inconsistent_gt_0.01Da": int((s["precursor_err_da"].abs() > 0.01).sum()),
                "records_with_library_coisolation_conflict": int(((s["coiso_other_ion_within_0.7"].fillna(0) > 0)
                                                                  | (s["coiso_isomer_in_pool"].fillna(0) > 0)).sum()),
                "elements_keys": dict(collections.Counter(e for x in s.drop_duplicates("key")["elements"].dropna()
                                                          for e in x.split(";") if e))}

    mhm = (df["adduct"] == "M+H") & (df["task_polarity"] == "Positive")
    in_range = df["mh_mz_theoretical"].between(70.0, 1042.6)
    key_excl_min = (df["in_msg15_any_route"] | df["in_muru_exposed_populations_union"]
                    | df["in_muru_dev_compounds_csv_keys"] | df["in_pr7_study2_population"]
                    | df["in_comparator_common_population"])
    key_excl = key_excl_min | df["in_muru_registry_all"] | df["in_muru_exposed_union"]
    sg_excl = (df["sg_in_muru_registry_scaffold_groups"] | df["sg_in_muru_dev_scaffold_groups"]
               | df["sg_in_pr7_scaffold_groups"] | df["sg_in_comparator_scaffold_groups"])
    clean = (df["precursor_err_da"].abs() <= 0.01) & ~df["charged_parent"].fillna(False).astype(bool)
    df["excluded_key_level_conservative"] = key_excl
    df["excluded_scaffold_level_muru_pr7_comparator"] = sg_excl
    S["pools"] = [
        pool(df["key"].notna(), "P0 all records with a structure key"),
        pool(mhm, "P1 [M+H]+ records from the positive-mode upload task"),
        pool(mhm & ~key_excl_min, "P2 = P1, key not in MSG1.5 (either route), MURU exposed populations, MURU dev, PR7, comparator"),
        pool(mhm & ~key_excl, "P3 = P1, conservative key exclusion incl. full MURU registry"),
        pool(mhm & ~key_excl & ~sg_excl, "P4 = P3 and scaffold group not in MURU registry/dev, PR7, comparator groups"),
        pool(mhm & ~key_excl & ~sg_excl & ~df["sg_in_msg15_scaffold_groups"], "P5 = P4 and scaffold group not in MSG1.5 (strict)"),
        pool(mhm & ~key_excl & ~sg_excl & in_range, "P6 = P4 and [M+H]+ within MURU development range 70.0-1042.6"),
        pool(mhm & ~key_excl & ~sg_excl & in_range & clean,
             "P7 = P6 and GNPS precursor within 0.01 Da of SMILES [M+H]+ and uncharged parent"),
        pool(mhm & ~key_excl & ~sg_excl & in_range & clean & ~df["in_msnlib_9lib"], "P8 = P7 and key not in MSnLib 9-lib (FIORA proxy)"),
        pool(mhm & ~key_excl & ~sg_excl & in_range & clean & ~df["formula_and_scaffold_in_msg"],
             "P9 = P7 and not (same parent formula AND scaffold group as some MSG1.5 compound)"),
        pool(mhm & ~key_excl & ~sg_excl & in_range & clean & (df["coiso_other_ion_within_0.7"].fillna(0) == 0)
             & (df["coiso_isomer_in_pool"].fillna(0) == 0), "P10 = P7 and no known in-pool co-isolation conflict (lower bound)"),
    ]
    S["P1_mh_outside_70_1042.6"] = int((mhm & df["key"].notna() & ~in_range).sum())
    p3 = df[mhm & ~key_excl & df["key"].notna()]
    p7 = df[mhm & ~key_excl & ~sg_excl & in_range & clean & df["key"].notna()]
    gl_pre_keys = set(gl_pre["key"].dropna())
    S["hidden_inclusion_proxies"] = {
        "P3_keys": int(p3["key"].nunique()),
        "P3_keys_parent_formula_in_msg15": int(p3.loc[p3["formula_in_msg"], "key"].nunique()),
        "P3_keys_formula_and_scaffold_in_msg15": int(p3.loc[p3["formula_and_scaffold_in_msg"], "key"].nunique()),
        "P3_keys_in_gnps_library_records_created_before_msg_download": int(len(set(p3["key"]) & gl_pre_keys)),
        "P3_keys_in_gnps_library_pre_download_examples": sorted(
            p3.loc[p3["key"].isin(gl_pre_keys), "compound_name"].unique())[:15],
        "P7_keys": int(p7["key"].nunique()),
        "P7_keys_parent_formula_in_msg15": int(p7.loc[p7["formula_in_msg"], "key"].nunique()),
        "P7_keys_in_gnps_library_records_created_before_msg_download": int(len(set(p7["key"]) & gl_pre_keys)),
        "P7_records_created_2025": int((p7["create_time"].str[:4] == "2025").sum()),
        "P7_mh_mz_quantiles": p7["mh_mz_theoretical"].quantile([0, .25, .5, .75, 1]).round(2).tolist(),
        "P7_heavy_atom_quantiles": p7["heavy_atoms"].quantile([0, .25, .5, .75, 1]).tolist(),
    }
    gpk = gl_pre[gl_pre["key"].isin(set(p3["key"]))]
    S["hidden_inclusion_proxies"]["gnps_library_pre_download_records_for_P3_keys"] = gpk[
        ["SpectrumID", "Compound_Name", "PI", "Data_Collector", "Instrument", "Adduct", "create_time"]].to_dict("records")

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "c09_records_identity_overlap.csv", index=False)
    perkey.to_csv(OUT / "c09_keys_in_msg15_row_summary.csv", index=False)
    (OUT / "c09_screen_summary.json").write_text(json.dumps(S, indent=1, default=str))
    man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("c09_*"))}
    (OUT / "output_manifest_sha256.json").write_text(json.dumps(man, indent=1))
    print(json.dumps({k: v for k, v in S.items() if k not in ("fields",)}, indent=1, default=str))


if __name__ == "__main__":
    main()
