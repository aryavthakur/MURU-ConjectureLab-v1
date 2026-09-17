"""S8 screen, candidate C08: GNPS REFRAME-POSITIVE-LIBRARY (+ sibling CMMC-REFRAME-POSITIVE-LIBRARY). ANALYSIS.

Metadata-only overlap and feasibility screen for the MURU collision-energy interface adjudication (outcome-blind).
Inputs are the metadata files stored by screen_c08_reframe_fetch.py (processed CSVs, LibraryServlet JSON with
peaks_json null, GNPS task parameters, MassIVE dataset records, GNPS2 dataset-cache file listing, GNPS2 library
listing) and the P5 exclusion inventory. From the MURU development compounds table only parent_key and
scaffold_group are loaded. No model is run; no spectra, measured-mu or result file is read.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "c08_reframe"
DL = OUT / "downloads"
EXC = ADJ / "exclusion"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_c08_reframe.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scaffold_key as SK  # noqa: E402

PROTON = 1.007276
ION_SHIFTS = {  # neutral monoisotopic mass M -> ion m/z (charge 1)
    "[M+H]+": lambda m: m + PROTON, "[M+Na]+": lambda m: m + 22.989218, "[M+NH4]+": lambda m: m + 18.033823,
    "[M+K]+": lambda m: m + 38.963158, "[M-H2O+H]+": lambda m: m - 18.010565 + PROTON,
    "[M+H]+13C": lambda m: m + PROTON + 1.003355, "[M]+": lambda m: m - 0.000549,
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_keys(p: Path) -> set[str]:
    return {x.strip() for x in p.read_text().splitlines() if x.strip()}


def counts(s) -> dict:
    return {str(k): int(v) for k, v in collections.Counter(s).most_common()}


def main() -> None:
    summary: dict = {"script": SCRIPT_REL, "rdkit": rdBase.rdkitVersion, "frozen_rdkit": SK.FROZEN_RDKIT,
                     "inputs": {}}
    for f in sorted(DL.iterdir()):
        summary["inputs"][f.name] = {"size": f.stat().st_size, "sha256": sha(f)}

    # ------------------------------------------------------------ processed CSVs
    csv_all = pd.read_csv(DL / "REFRAME-POSITIVE-LIBRARY.csv", dtype=str, keep_default_na=False)
    cm_all = pd.read_csv(DL / "CMMC-REFRAME-POSITIVE-LIBRARY.csv", dtype=str, keep_default_na=False)
    summary["processed_csv_columns"] = list(csv_all.columns)
    summary["processed_csv_rows_by_membership"] = {"REFRAME-POSITIVE-LIBRARY.csv": counts(csv_all["GNPS_library_membership"]),
                                                   "CMMC-REFRAME-POSITIVE-LIBRARY.csv": counts(cm_all["GNPS_library_membership"])}
    mona_a = csv_all[csv_all["GNPS_library_membership"] == "MONA_ML_Export"]
    mona_b = cm_all[cm_all["GNPS_library_membership"] == "MONA_ML_Export"]
    summary["mona_ml_export_rows_identical_across_the_two_csvs"] = bool(
        mona_a.drop(columns=["scan"]).reset_index(drop=True).equals(mona_b.drop(columns=["scan"]).reset_index(drop=True)))
    rf = csv_all[csv_all["GNPS_library_membership"] == "REFRAME-POSITIVE-LIBRARY"].copy()
    cm = cm_all[cm_all["GNPS_library_membership"] == "CMMC-REFRAME-POSITIVE-LIBRARY"].copy()
    for label, d in (("reframe_csv", rf), ("cmmc_csv", cm)):
        summary[f"{label}_n_rows"] = int(len(d))
        for c in ["collision_energy", "msDissociationMethod", "msManufacturer", "msMassAnalyzer", "msIonisation",
                  "Adduct", "Charge", "Ion_Mode", "Compound_Source"]:
            summary[f"{label}_{c}_counts"] = counts(d[c])
        summary[f"{label}_collision_energy_nonempty"] = int((d["collision_energy"].str.strip() != "").sum())
        summary[f"{label}_msDissociationMethod_nonempty"] = int((d["msDissociationMethod"].str.strip() != "").sum())
        summary[f"{label}_spectrum_id_min_max"] = [d["spectrum_id"].min(), d["spectrum_id"].max()]

    # ------------------------------------------------------------ LibraryServlet (REFRAME only)
    sp = json.loads((DL / "gnps_libraryservlet_REFRAME-POSITIVE-LIBRARY.json").read_bytes().decode("utf-8", "replace"),
                    strict=False)["spectra"]
    summary["servlet_n_records"] = len(sp)
    summary["servlet_peaks_json_nonnull"] = sum(1 for s in sp if s.get("peaks_json") not in (None, "null", ""))
    g = pd.DataFrame(sp).drop(columns=["peaks_json"])
    for c in ["Adduct", "Instrument", "Ion_Source", "Compound_Source", "PI", "Data_Collector", "submit_user",
              "create_time", "task", "ms_level", "Library_Class", "Pubmed_ID", "CAS_Number", "spectrum_status"]:
        summary[f"servlet_{c}_counts"] = counts(g[c])
    summary["servlet_fields"] = sorted(g.columns)
    summary["servlet_fields_mentioning_energy"] = [c for c in g.columns if re.search(r"energ|collision|nce|hcd", c, re.I)]
    g["well"] = g["source_file"].str.extract(r"reframe_drugs_pos_(P\d_[A-H]\d+)_id\.mzML")[0]
    summary["servlet_records_with_plate_well_source"] = int(g["well"].notna().sum())
    summary["servlet_non_well_source_files"] = counts(g.loc[g["well"].isna(), "source_file"])
    summary["servlet_distinct_wells"] = int(g["well"].nunique())
    summary["servlet_plates"] = counts(g["well"].str[:2])
    summary["servlet_name_with_isomer_annotation"] = int(g["Compound_Name"].str.contains("known structural isomers").sum())
    iso = g["Compound_Name"].str.extract(r"known structural isomers: (\d+); isobaric peaks in run: (\d+)")
    summary["servlet_isomer_annotation_values"] = counts(zip(iso[0].dropna(), iso[1].dropna()))

    # join servlet to processed CSV on spectrum_id
    j = g.merge(rf[["spectrum_id", "Adduct", "Smiles", "InChIKey_smiles", "Precursor_MZ", "ppmBetweenExpAndThMass",
                    "classyfire_superclass", "collision_energy"]].rename(
        columns={"Adduct": "Adduct_csv", "Smiles": "Smiles_csv", "Precursor_MZ": "Precursor_MZ_csv"}),
        on="spectrum_id", how="outer", indicator=True)
    summary["servlet_vs_csv_join"] = counts(j["_merge"])
    both = j[j["_merge"] == "both"]
    summary["servlet_vs_csv_adduct_pairs"] = counts(zip(both["Adduct"], both["Adduct_csv"]))
    summary["servlet_vs_csv_smiles_string_differs"] = int((both["Smiles"] != both["Smiles_csv"]).sum())
    summary["servlet_only_ids"] = j.loc[j["_merge"] == "left_only", "spectrum_id"].tolist()

    # ------------------------------------------------------------ identity
    cache: dict = {}

    def chem(smi):
        if smi in cache:
            return cache[smi]
        k, sg = SK.key_and_group(smi)
        rec = {"key": k, "scaffold_group": sg}
        pm = SK.parent_mol(smi) if k else None
        if pm is not None:
            rec["mono_parent"] = Descriptors.ExactMolWt(pm)
            rec["formula_parent"] = rdMolDescriptors.CalcMolFormula(pm)
            rec["elements"] = ";".join(sorted({a.GetSymbol() for a in Chem.AddHs(pm).GetAtoms()}))
            m0 = Chem.MolFromSmiles(smi)
            rec["charged_raw"] = any(a.GetFormalCharge() for a in m0.GetAtoms())
            rec["n_components_raw"] = len(Chem.GetMolFrags(m0))
            # net formal charge of the parent (zwitterions such as nitro groups and N-oxides are net neutral)
            rec["charged_parent"] = sum(a.GetFormalCharge() for a in pm.GetAtoms()) != 0
            rec["any_formal_charge_parent"] = any(a.GetFormalCharge() for a in pm.GetAtoms())
        cache[smi] = rec
        return rec

    rows = []
    for r in j[j["_merge"] != "right_only"].to_dict("records"):
        c = chem(r["Smiles"])
        rec = {"spectrum_id": r["spectrum_id"], "compound_name": r["Compound_Name"], "adduct": r["Adduct"],
               "adduct_csv": r["Adduct_csv"], "precursor_mz": float(r["Precursor_MZ"]), "source_file": r["source_file"],
               "well": r["well"], "scan": r["scan"], "task": r["task"], "create_time": r["create_time"],
               "smiles": r["Smiles"], "recorded_inchikey_csv": r["InChIKey_smiles"],
               "ppm_csv": r["ppmBetweenExpAndThMass"], "classyfire_superclass": r["classyfire_superclass"], **c}
        if c.get("mono_parent") is not None and r["Adduct"] in ION_SHIFTS:
            rec["theoretical_mz"] = ION_SHIFTS[r["Adduct"]](c["mono_parent"])
            rec["precursor_err_da"] = rec["precursor_mz"] - rec["theoretical_mz"]
        rows.append(rec)
    df = pd.DataFrame(rows)
    df["recorded_block1"] = df["recorded_inchikey_csv"].str[:14]
    summary["n_records"] = int(len(df))
    summary["n_key_parsed"] = int(df["key"].notna().sum())
    summary["n_unique_keys_all"] = int(df["key"].nunique())
    summary["n_unique_scaffold_groups_all"] = int(df["scaffold_group"].nunique())
    kk = df[df["key"].notna() & (df["recorded_block1"] != "")]
    summary["parent_key_ne_csv_recorded_block1_records"] = int((kk["key"] != kk["recorded_block1"]).sum())
    summary["parent_key_ne_csv_recorded_block1_keys"] = int(kk.loc[kk["key"] != kk["recorded_block1"], "key"].nunique())
    summary["charged_raw_records"] = int(df["charged_raw"].fillna(False).astype(bool).sum())
    summary["charged_parent_records_net_charge_ne_0"] = int(df["charged_parent"].fillna(False).astype(bool).sum())
    summary["parent_with_any_formal_charge_records"] = int(df["any_formal_charge_parent"].fillna(False).astype(bool).sum())
    summary["multicomponent_raw_records"] = int((df["n_components_raw"].fillna(1) > 1).sum())
    summary["charged_parent_by_adduct"] = counts(df.loc[df["charged_parent"].fillna(False).astype(bool), "adduct_csv"])
    bad = df[df["precursor_err_da"].abs() > 0.01]
    summary["precursor_inconsistent_gt_0.01Da"] = int(len(bad))
    summary["precursor_inconsistent_by_adduct_servlet_csv"] = counts(zip(bad["adduct"], bad["adduct_csv"]))
    summary["precursor_err_da_quantiles_all"] = df["precursor_err_da"].quantile([0, .01, .05, .5, .95, .99, 1]).round(4).tolist()

    # records per compound and adduct (one spectrum per compound-adduct expected for a DDA library upload)
    ka = df[df["key"].notna()].groupby(["key", "adduct"]).agg(n=("spectrum_id", "size"), wells=("well", "nunique"),
                                                               scans=("scan", "nunique")).reset_index()
    summary["records_per_key_adduct_distribution"] = counts(ka["n"])
    summary["wells_per_key_adduct_distribution"] = counts(ka["wells"])
    mh_ka = ka[ka["adduct"] == "[M+H]+"]
    summary["mh_keys_with_multiple_records"] = int((mh_ka["n"] > 1).sum())
    summary["mh_keys_with_multiple_records_in_same_well"] = int(((mh_ka["n"] > 1) & (mh_ka["wells"] == 1)).sum())
    # consecutive-scan structure inside a well for the same key+adduct (a separate-energy DDA pattern would show
    # runs of adjacent scans; a single stepped scan would not)
    df["scan_i"] = pd.to_numeric(df["scan"], errors="coerce")
    multi = df[df["key"].notna()].groupby(["key", "adduct", "well"])["scan_i"].apply(lambda x: sorted(x)).reset_index()
    multi = multi[multi["scan_i"].map(len) > 1]
    gaps = [b - a for s in multi["scan_i"] for a, b in zip(s, s[1:])]
    summary["same_key_adduct_well_scan_gap_distribution_top"] = counts(gaps) if gaps else {}
    summary["same_key_adduct_well_groups_with_multiple_scans"] = int(len(multi))

    # ------------------------------------------------------------ pooled-well co-injection (lower bound)
    wells = df[df["well"].notna() & df["key"].notna()]
    per_well_keys = wells.groupby("well")["key"].nunique()
    summary["annotated_keys_per_well_quantiles"] = per_well_keys.quantile([0, .1, .5, .9, 1]).tolist()
    summary["annotated_keys_per_well_total"] = int(per_well_keys.sum())
    comp = wells.drop_duplicates(["well", "key"])[["well", "key", "mono_parent", "formula_parent"]]
    cofl, isofl = {}, {}
    for w, grp in comp.groupby("well"):
        ions = [(k, f(m)) for k, m in zip(grp["key"], grp["mono_parent"]) for f in ION_SHIFTS.values()]
        forms = collections.Counter(grp["formula_parent"])
        for k, m, fo in zip(grp["key"], grp["mono_parent"], grp["formula_parent"]):
            target = m + PROTON
            cofl[(w, k)] = any(k2 != k and abs(mz - target) <= 0.7 for k2, mz in ions)
            isofl[(w, k)] = forms[fo] > 1
    df["coinjected_ion_within_0p7_lower_bound"] = [cofl.get((w, k), False) for w, k in zip(df["well"], df["key"])]
    df["coinjected_isomer_lower_bound"] = [isofl.get((w, k), False) for w, k in zip(df["well"], df["key"])]
    summary["isolation_rule_note"] = ("lower bound: only compounds that are themselves annotated in the library are "
                                      "known to be in a well; the plate map of all pooled compounds is not public "
                                      "metadata here")

    # ------------------------------------------------------------ CMMC sibling identity and duplication
    cm_rows = []
    for r in cm.to_dict("records"):
        c = chem(r["Smiles"])
        cm_rows.append({"spectrum_id": r["spectrum_id"], "adduct": r["Adduct"], "precursor_mz": float(r["Precursor_MZ"]),
                        "compound_name": r["Compound_Name"], "key": c["key"], "scaffold_group": c["scaffold_group"]})
    cdf = pd.DataFrame(cm_rows)
    rk_mh = set(df.loc[df["adduct_csv"] == "[M+H]1+", "key"].dropna())
    ck_mh = set(cdf.loc[cdf["adduct"] == "[M+H]1+", "key"].dropna())
    rk, ck = set(df["key"].dropna()), set(cdf["key"].dropna())
    summary["cmmc"] = {
        "n_rows": int(len(cdf)), "keys": len(ck), "mh_keys": len(ck_mh), "scaffold_groups": int(cdf["scaffold_group"].nunique()),
        "keys_shared_with_reframe": len(rk & ck), "keys_only_cmmc": len(ck - rk), "keys_only_reframe": len(rk - ck),
        "mh_keys_shared": len(rk_mh & ck_mh), "mh_keys_only_cmmc": len(ck_mh - rk_mh), "mh_keys_only_reframe": len(rk_mh - ck_mh),
        "adduct_counts": counts(cdf["adduct"]),
        "note": "CMMC-REFRAME-POSITIVE-LIBRARY has no public LibraryServlet listing (HTTP 500) so source_file/task are unknown",
    }
    # precursor m/z agreement for shared [M+H]+ keys (both libraries give 3-4 decimal precursor values)
    a = df[df["adduct_csv"] == "[M+H]1+"].groupby("key")["precursor_mz"].median()
    b = cdf[cdf["adduct"] == "[M+H]1+"].groupby("key")["precursor_mz"].median()
    ab = pd.concat([a.rename("reframe"), b.rename("cmmc")], axis=1).dropna()
    summary["cmmc"]["shared_mh_precursor_abs_diff_quantiles"] = (ab["reframe"] - ab["cmmc"]).abs().quantile([.5, .9, .99, 1]).round(5).tolist()

    # ------------------------------------------------------------ exclusion sets
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
    pops = {}
    for p in sorted(EXC.glob("muru_exposure_registry_population_*_keys.txt")):
        pops[p.name[len("muru_exposure_registry_population_"):-len("_keys.txt")]] = read_keys(p)
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
    summary["exclusion_set_sizes"] = {k: len(v) for k, v in {**sets, **groups}.items()}
    for k, v in sets.items():
        df[f"in_{k}"] = df["key"].isin(v)
    for k, v in pops.items():
        df[f"in_pop_{k}"] = df["key"].isin(v)
    for k, v in groups.items():
        df[f"sg_in_{k}"] = df["scaffold_group"].isin(v)
    # MSG membership by either route: MURU parent key, or the library's own recorded InChIKey first block
    df["in_msg15_any_route"] = (df["in_msg15_recorded_all"] | df["in_msg15_parent_all"]
                                | df["recorded_block1"].isin(sets["msg15_recorded_all"]))

    kdf = df[df["key"].notna()]
    ov = {}
    for sub, m in [("all", kdf["key"].notna()), ("servlet_[M+H]+", kdf["adduct"] == "[M+H]+"),
                   ("csv_[M+H]1+", kdf["adduct_csv"] == "[M+H]1+")]:
        s = kdf[m]
        d = {"records": int(len(s)), "keys": int(s["key"].nunique()), "scaffold_groups": int(s["scaffold_group"].nunique())}
        for col in [c for c in kdf.columns if c.startswith("in_") or c.startswith("sg_in_")]:
            d[col + "__unique_keys"] = int(s.loc[s[col], "key"].nunique())
        ov[sub] = d
    summary["overlap_unique_keys_by_subset"] = ov

    # MSG rows for overlapping keys (identity/metadata columns only)
    msg = pd.read_parquet(ADJ / "p3_msg15_row_source_attribution.parquet",
                          columns=["identifier", "inchikey", "fold", "simulation_challenge", "adduct", "instrument_type",
                                   "collision_energy", "source_label"])
    mk = pd.read_parquet(EXC / "msg15_row_keys.parquet", columns=["identifier", "parent_key", "scaffold_group"])
    msg = msg.merge(mk, on="identifier", how="left")
    ek = set(kdf["key"])
    mrows = msg[msg["inchikey"].isin(ek) | msg["parent_key"].isin(ek)].copy()
    mrows["k"] = [a if a in ek else b for a, b in zip(mrows["parent_key"], mrows["inchikey"])]
    summary["msg_rows_matching_reframe_keys"] = {
        "rows": int(len(mrows)), "keys": int(mrows["k"].nunique()),
        "instrument_type": counts(mrows["instrument_type"].fillna("NA")), "adduct": counts(mrows["adduct"]),
        "fold_rows": counts(mrows["fold"]), "simulation_challenge_rows": int(mrows["simulation_challenge"].sum()),
        "source_label_rows": counts(mrows["source_label"]),
        "keys_by_fold_set": counts(mrows.groupby("k")["fold"].apply(lambda x: ";".join(sorted(set(x))))),
        "keys_with_simulation_rows": int(mrows.groupby("k")["simulation_challenge"].any().sum()),
    }
    mm = pd.read_parquet(ADJ / "massspecgym15_metadata_columns.parquet", columns=["identifier", "formula"])
    mk2 = mk.merge(mm, on="identifier", how="left")
    form_sg = set(zip(mk2["formula"], mk2["scaffold_group"]))
    df["formula_in_msg"] = df["formula_parent"].isin(set(mk2["formula"]))
    df["formula_and_scaffold_in_msg"] = [(f, s) in form_sg for f, s in zip(df["formula_parent"], df["scaffold_group"])]

    # ------------------------------------------------------------ pools after exclusion
    def pool(mask, label):
        s = df[mask & df["key"].notna()]
        sgc = s.groupby("scaffold_group")["key"].nunique().sort_values(ascending=False)
        return {"label": label, "records": int(len(s)), "keys": int(s["key"].nunique()),
                "scaffold_groups": int(s["scaffold_group"].nunique()),
                "acyclic_keys": int(s.loc[s["scaffold_group"].str.startswith("__ACYCLIC__"), "key"].nunique()),
                "largest_scaffold_group_key_counts": [int(x) for x in sgc.head(8).values],
                "largest_scaffold_groups": [str(x) for x in sgc.head(5).index],
                "singleton_scaffold_groups": int((sgc == 1).sum()),
                "precursor_mz_min_max": [float(s["precursor_mz"].min()), float(s["precursor_mz"].max())] if len(s) else None,
                "precursor_outside_70_1042.6_records": int(((s["precursor_mz"] < 70.0) | (s["precursor_mz"] > 1042.6)).sum()),
                "precursor_inconsistent_gt_0.01Da_records": int((s["precursor_err_da"].abs() > 0.01).sum()),
                "charged_parent_keys": int(s.loc[s["charged_parent"].fillna(False).astype(bool), "key"].nunique()),
                "coinjected_ion_within_0p7_lb_keys": int(s.loc[s["coinjected_ion_within_0p7_lower_bound"], "key"].nunique()),
                "coinjected_isomer_lb_keys": int(s.loc[s["coinjected_isomer_lower_bound"], "key"].nunique()),
                "keys_with_multiple_records": int((s.groupby("key").size() > 1).sum()),
                "classyfire_superclass_records": counts(s["classyfire_superclass"].replace("", "(blank)")),
                "elements_keys": counts(e for x in s.drop_duplicates("key")["elements"].dropna() for e in x.split(";") if e)}

    mh = (df["adduct"] == "[M+H]+") & (df["adduct_csv"] == "[M+H]1+") & ~df["charged_parent"].fillna(False).astype(bool)
    key_excl_min = (df["in_msg15_any_route"] | df["in_muru_exposed_populations_union"] | df["in_muru_dev_compounds_csv_keys"]
                    | df["in_pr7_study2_population"] | df["in_comparator_common_population"])
    key_excl = key_excl_min | df["in_muru_registry_all"] | df["in_muru_exposed_union"]
    sg_excl_muru = (df["sg_in_muru_registry_scaffold_groups"] | df["sg_in_muru_dev_scaffold_groups"]
                    | df["sg_in_pr7_scaffold_groups"] | df["sg_in_comparator_scaffold_groups"])
    in_range = (df["precursor_mz"] >= 70.0) & (df["precursor_mz"] <= 1042.6)
    consistent = df["precursor_err_da"].abs() <= 0.01
    clean_iso = ~df["coinjected_ion_within_0p7_lower_bound"] & ~df["coinjected_isomer_lower_bound"]
    df["excluded_key_level_conservative"] = key_excl
    df["excluded_scaffold_level_muru_pr7_comparator"] = sg_excl_muru
    pools = [
        pool(df["key"].notna(), "P0 all REFRAME-POSITIVE records"),
        pool(mh, "P1 [M+H]+ (servlet and processed CSV agree), charge-neutral parent"),
        pool(mh & ~df["in_msg15_any_route"], "P1b = P1 and key not in MassSpecGym 1.5 (either key route) only"),
        pool(mh & ~key_excl_min, "P2 = P1, key not in MSG1.5, MURU exposed populations, MURU dev, PR7, comparator"),
        pool(mh & ~key_excl, "P3 = P2 and key not in the full MURU exposure registry (conservative)"),
        pool(mh & ~key_excl & ~df["in_msnlib_9lib"], "P4 = P3 and key not in MSnLib 9-lib (FIORA proxy)"),
        pool(mh & ~key_excl & ~sg_excl_muru, "P5 = P3 and scaffold group not in MURU registry/dev, PR7, comparator groups"),
        pool(mh & ~key_excl & ~sg_excl_muru & ~df["sg_in_msg15_scaffold_groups"],
             "P6 = P5 and scaffold group not in any MSG1.5 scaffold group (strict)"),
        pool(mh & ~key_excl & ~df["formula_and_scaffold_in_msg"],
             "P7 = P3 and not (same parent formula AND scaffold group as some MSG1.5 compound)"),
        pool(mh & ~key_excl & ~sg_excl_muru & in_range & consistent & clean_iso,
             "P8 = P5 and precursor in 70-1042.6, precursor consistent within 0.01 Da, no co-injected ion/isomer (lower bound)"),
        pool(mh & ~key_excl & ~sg_excl_muru & ~df["sg_in_msg15_scaffold_groups"] & in_range & consistent & clean_iso,
             "P9 = P6 with the P8 quality filters"),
    ]
    summary["pools"] = pools

    # CMMC sibling after the same key/scaffold exclusions ([M+H]+ records, net-neutral parent)
    cmc = cdf[(cdf["adduct"] == "[M+H]1+") & cdf["key"].notna()].copy()
    cmc["charged_parent"] = [bool(cache[x].get("charged_parent")) for x in cm.loc[cmc.index, "Smiles"]]
    cmc["recorded_block1"] = cm.loc[cmc.index, "InChIKey_smiles"].str[:14]
    cmc = cmc[~cmc["charged_parent"]]
    c_msg = (cmc["key"].isin(sets["msg15_recorded_all"]) | cmc["key"].isin(sets["msg15_parent_all"])
             | cmc["recorded_block1"].isin(sets["msg15_recorded_all"]))
    c_kex = (c_msg | cmc["key"].isin(sets["muru_exposed_populations_union"]) | cmc["key"].isin(sets["muru_dev_compounds_csv_keys"])
             | cmc["key"].isin(sets["pr7_study2_population"]) | cmc["key"].isin(sets["comparator_common_population"])
             | cmc["key"].isin(sets["muru_registry_all"]) | cmc["key"].isin(sets["muru_exposed_union"]))
    c_sg = (cmc["scaffold_group"].isin(groups["muru_registry_scaffold_groups"]) | cmc["scaffold_group"].isin(groups["muru_dev_scaffold_groups"])
            | cmc["scaffold_group"].isin(groups["pr7_scaffold_groups"]) | cmc["scaffold_group"].isin(groups["comparator_scaffold_groups"]))
    c3, c5 = cmc[~c_kex], cmc[~c_kex & ~c_sg]
    r3 = set(df.loc[mh & ~key_excl, "key"])
    r5 = set(df.loc[mh & ~key_excl & ~sg_excl_muru, "key"])
    summary["cmmc_pools"] = {
        "C1_mh_neutral_keys": int(cmc["key"].nunique()), "C1_keys_in_msg15": int(cmc.loc[c_msg, "key"].nunique()),
        "C3_keys": int(c3["key"].nunique()), "C3_scaffold_groups": int(c3["scaffold_group"].nunique()),
        "C5_keys": int(c5["key"].nunique()), "C5_scaffold_groups": int(c5["scaffold_group"].nunique()),
        "C3_keys_not_in_reframe_P3": len(set(c3["key"]) - r3), "C5_keys_not_in_reframe_P5": len(set(c5["key"]) - r5),
        "union_P3_C3_keys": len(set(c3["key"]) | r3), "union_P5_C5_keys": len(set(c5["key"]) | r5),
        "union_P5_C5_scaffold_groups": len(set(c5["scaffold_group"]) | set(df.loc[mh & ~key_excl & ~sg_excl_muru, "scaffold_group"])),
    }
    # MSG row source labels for REFRAME keys whose ONLY MSG rows are GNPS-labelled (the route by which a REFRAME
    # spectrum could have entered MSG); informational, these keys are excluded anyway
    lab = mrows.groupby("k")["source_label"].apply(lambda x: ";".join(sorted(set(x))))
    summary["msg_reframe_keys_by_source_label_set"] = counts(lab)
    summary["P3_records_formula_and_scaffold_in_msg"] = int((mh & ~key_excl & df["formula_and_scaffold_in_msg"]).sum())
    summary["P3_keys_formula_in_msg"] = int(df.loc[mh & ~key_excl & df["formula_in_msg"], "key"].nunique())

    # ------------------------------------------------------------ provenance files
    prov = {}
    for f in sorted(DL.glob("gnps_task_*_status.json")):
        prov[f.name] = json.loads(f.read_text())
    for f in sorted(DL.glob("gnps_task_*_params.xml")):
        t = f.read_text()
        prov[f.name] = {"parameters_except_file_mapping": re.findall(r'<parameter name="(?!upload_file_mapping)([^"]+)">([^<]*)<', t),
                        "n_upload_file_mapping": t.count('name="upload_file_mapping"')}
    prov["massive_proxi"] = json.loads((DL / "massive_proxi_MSV000093469.json").read_text())
    prov["massive_information"] = json.loads((DL / "massive_massiveinformation_MSV000093469.json").read_text())
    fl = pd.read_csv(DL / "gnps2_datasetcache_filelist_MSV000093469.csv", dtype=str)
    fl["dir"] = fl["filepath"].str.rsplit("/", n=1).str[0]
    fl["ext"] = fl["filepath"].str.rsplit(".", n=1).str[-1]
    prov["msv000093469_filelist"] = {"n_files": int(len(fl)), "by_dir": counts(fl["dir"]), "by_ext": counts(fl["ext"]),
                                     "non_mzml_files": fl.loc[fl["ext"].str.lower() != "mzml", "filepath"].tolist(),
                                     "total_size_bytes": int(pd.to_numeric(fl["size"]).sum())}
    lt = (DL / "gnps2_external_gnpslibrary_listing.html").read_text()
    prov["gnps2_listing_reframe_entries"] = [json.loads(m.group(0)) for m in re.finditer(r"\{[^{}]*\}", lt)
                                             if "REFRAME" in m.group(0)]
    summary["provenance"] = prov

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "c08_reframe_records_identity_overlap.csv", index=False)
    cdf.to_csv(OUT / "c08_cmmc_reframe_records_identity.csv", index=False)
    (OUT / "screen_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    man = {p.name: {"size": p.stat().st_size, "sha256": sha(p)} for p in sorted(OUT.glob("*.csv")) if p.is_file()}
    man["screen_summary.json"] = {"size": (OUT / "screen_summary.json").stat().st_size, "sha256": sha(OUT / "screen_summary.json")}
    (OUT / "output_manifest_sha256.json").write_text(json.dumps(man, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("inputs", "provenance", "servlet_fields",
                                                                     "processed_csv_columns")}, indent=1, default=str))


if __name__ == "__main__":
    main()
