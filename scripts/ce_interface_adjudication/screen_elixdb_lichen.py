"""S4 screen, candidate C04: ELIXDB lichen library (GNPS ELIXDB-LICHEN-DATABASE; MetaboLights MTBLS8109).

Metadata-only overlap and feasibility screen for the MURU collision-energy interface adjudication (outcome-blind).

Modes
  --fetch    download METADATA ONLY (GNPS LibraryServlet JSON with peaks_json verified null for every record,
             MTBLS8109 ISA-Tab tables, FTP directory listings, MetaboLights announcement/study JSON, the article
             landing page) into artifacts/ce_interface_adjudication/screen/elixdb_lichen/downloads/ and append one
             line per file to artifacts/ce_interface_adjudication/downloads_register.jsonl.
             Never fetches any mzXML/raw/mgf spectra file.
  --analyze  compute MURU parent keys and scaffold groups from metadata SMILES, overlaps against the P5 exclusion
             inventory, identity sanity checks, and post-exclusion scaffold counts. Writes CSV/JSON outputs.

No model (ICEBERG, GLACIER, FIORA, MURU) is run. No measured-mu or result file is read. From the MURU development
compounds table only the identity columns parent_key and scaffold_group are loaded.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "elixdb_lichen"
DL = OUT / "downloads"
EXC = ADJ / "exclusion"
REGISTER = ADJ / "downloads_register.jsonl"
TASK = "S4-C04"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_elixdb_lichen.py"

MTBLS = "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS8109"
FETCH = [
    # (stored name, url, description)
    ("gnps_libraryservlet_ELIXDB-LICHEN-DATABASE.json",
     "https://gnps.ucsd.edu/ProteoSAFe/LibraryServlet?library=ELIXDB-LICHEN-DATABASE",
     "GNPS LibraryServlet library metadata listing (JSON); peaks_json verified null for all records; no peak arrays"),
    ("MTBLS8109_i_Investigation.txt", f"{MTBLS}/i_Investigation.txt", "MetaboLights ISA-Tab investigation file"),
    ("MTBLS8109_s_MTBLS8109.txt", f"{MTBLS}/s_MTBLS8109.txt", "MetaboLights ISA-Tab sample table"),
    ("MTBLS8109_a_LC-MS_metabolite_profiling.txt", f"{MTBLS}/a_MTBLS8109_LC-MS___metabolite_profiling.txt",
     "MetaboLights ISA-Tab assay table"),
    ("MTBLS8109_m_LC-MS_metabolite_profiling_v2_maf.tsv",
     f"{MTBLS}/m_MTBLS8109_LC-MS___metabolite_profiling_v2_maf.tsv",
     "MetaboLights metabolite assignment file (compound identities, no spectra)"),
    ("MTBLS8109_ftp_root_listing.html", f"{MTBLS}/", "FTP HTTP directory listing (file names/sizes only)"),
    ("MTBLS8109_ftp_FILES_listing.html", f"{MTBLS}/FILES/", "FTP HTTP directory listing (file names/sizes only)"),
    ("MTBLS8109_ftp_FILES_RAW_FILES_listing.html", f"{MTBLS}/FILES/RAW_FILES/",
     "FTP HTTP directory listing (file names/sizes only)"),
    ("MTBLS8109_ftp_FILES_DERIVED_FILES_listing.html", f"{MTBLS}/FILES/DERIVED_FILES/",
     "FTP HTTP directory listing (file names/sizes only)"),
    ("MTBLS8109.announcement.json", f"{MTBLS}/MTBLS8109.announcement.json",
     "MetaboLights announcement metadata (license, dates, file lists)"),
    ("MTBLS8109_ws_public_study.json", "https://www.ebi.ac.uk/metabolights/ws/studies/public/study/MTBLS8109",
     "MetaboLights web-service public study metadata JSON"),
]
# The article page https://pmc.ncbi.nlm.nih.gov/articles/PMC11814408/ is NOT fetched here: a urllib fetch on
# 2026-09-15 returned a reCAPTCHA challenge page. downloads/PMC11814408_article.html is a manual curl copy
# (register entry task S4-C04 "CORRECTION").
MAX_BYTES = 50_000_000


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def append_register(rec: dict) -> None:
    line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(REGISTER, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def fetch() -> None:
    DL.mkdir(parents=True, exist_ok=True)
    for name, url, desc in FETCH:
        low = url.lower()
        assert not low.endswith((".mzxml", ".mzml", ".mgf", ".msp", ".raw", ".hdf5", ".h5")), url
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read(MAX_BYTES + 1)
            final_url = r.geturl()
        assert len(data) <= MAX_BYTES, f"{url} exceeds size cap"
        if name.startswith("gnps_libraryservlet"):
            spectra = json.loads(data)["spectra"]
            nonnull = sum(1 for s in spectra if s.get("peaks_json") not in (None, "null", ""))
            if nonnull:
                raise SystemExit(f"GNPS response carries {nonnull} non-null peaks_json; discarded, not stored")
        (DL / name).write_bytes(data)
        rec = {
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
            "task": TASK,
            "name": f"{name} ({desc})",
            "source_url": url,
            "final_url": final_url if final_url != url else None,
            "size_bytes": len(data),
            "sha256": sha256_bytes(data),
            "stored_as": str((DL / name).relative_to(ROOT)),
            "script": SCRIPT_REL,
        }
        append_register(rec)
        print(name, len(data), rec["sha256"][:12])


# ---------------------------------------------------------------- analysis
def read_keys(p: Path) -> set[str]:
    return {x.strip() for x in p.read_text().splitlines() if x.strip()}


def ftp_listing(p: Path) -> list[tuple[str, str, str]]:
    t = p.read_text(errors="replace")
    rows = re.findall(r'<a href="([^"]+)">[^<]*</a>\s*</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>', t)
    return [(urllib.parse.unquote(a), b.strip(), c.strip()) for a, b, c in rows if not a.startswith("/")]


def analyze() -> None:
    import pandas as pd
    from rdkit import Chem, rdBase
    from rdkit.Chem import Descriptors, rdMolDescriptors

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import scaffold_key as SK  # noqa: E402

    PROTON = 1.007276
    summary: dict = {"script": SCRIPT_REL, "rdkit": rdBase.rdkitVersion, "frozen_rdkit": SK.FROZEN_RDKIT}

    # --- GNPS metadata (peaks column dropped immediately)
    spectra = json.loads((DL / "gnps_libraryservlet_ELIXDB-LICHEN-DATABASE.json").read_bytes())["spectra"]
    summary["gnps_n_records"] = len(spectra)
    summary["gnps_peaks_json_nonnull"] = sum(1 for s in spectra if s.get("peaks_json") not in (None, "null", ""))
    g = pd.DataFrame(spectra).drop(columns=["peaks_json"])
    for c in ["Adduct", "Ion_Mode", "Instrument", "Ion_Source", "Charge", "ms_level", "Library_Class",
              "Compound_Source", "create_time", "library_membership", "Data_Collector", "PI"]:
        summary[f"gnps_{c}_counts"] = dict(collections.Counter(g[c]))
    summary["gnps_fields"] = sorted(g.columns)
    summary["gnps_inchi_nonempty"] = int((g["INCHI"].str.strip() != "").sum())
    summary["gnps_fields_mentioning_energy"] = [c for c in g.columns if re.search(r"energ|collision", c, re.I)]

    # --- MTBLS8109 ISA tables
    s_tab = pd.read_csv(DL / "MTBLS8109_s_MTBLS8109.txt", sep="\t", dtype=str, keep_default_na=False)
    a_tab = pd.read_csv(DL / "MTBLS8109_a_LC-MS_metabolite_profiling.txt", sep="\t", dtype=str, keep_default_na=False)
    m_tab = pd.read_csv(DL / "MTBLS8109_m_LC-MS_metabolite_profiling_v2_maf.tsv", sep="\t", dtype=str,
                        keep_default_na=False, usecols=["database_identifier", "chemical_formula", "smiles", "inchi",
                                                        "metabolite_identification", "mass_to_charge",
                                                        "modifications", "charge", "retention_time"])
    summary["mtbls_s_collision_energy_counts"] = dict(collections.Counter(s_tab["Comment[Collision energy]"]))
    summary["mtbls_s_chemical_class_counts"] = dict(collections.Counter(s_tab["Factor Value[Chemical class]"]))
    for c in ["Parameter Value[Scan polarity]", "Parameter Value[Scan m/z range]", "Parameter Value[Instrument]",
              "Parameter Value[Mass analyzer]", "Raw Spectral Data File"]:
        summary[f"mtbls_a_{c}_counts"] = dict(collections.Counter(a_tab[c]))
    summary["mtbls_a_n_distinct_derived_files"] = int(a_tab["Derived Spectral Data File"].nunique())

    # FTP listings: only metadata (names and sizes)
    listing = {}
    for key, fn in [("root", "MTBLS8109_ftp_root_listing.html"), ("FILES", "MTBLS8109_ftp_FILES_listing.html"),
                    ("RAW_FILES", "MTBLS8109_ftp_FILES_RAW_FILES_listing.html"),
                    ("DERIVED_FILES", "MTBLS8109_ftp_FILES_DERIVED_FILES_listing.html")]:
        rows = ftp_listing(DL / fn)
        ext = collections.Counter("DIR" if r[0].endswith("/") else (r[0].rsplit(".", 1)[-1] if "." in r[0] else "none")
                                  for r in rows)
        sizes = [r[2] for r in rows if r[0].lower().endswith(".mzxml")]
        listing[key] = {"n_entries": len(rows), "by_extension": dict(ext),
                        "entries_not_mzxml": [r for r in rows if not r[0].lower().endswith(".mzxml")],
                        "mzxml_size_strings": dict(collections.Counter(sizes)),
                        "mzxml_names": sorted(r[0] for r in rows if r[0].lower().endswith(".mzxml"))}
    gnps_files = sorted(g["source_file"])
    summary["ftp_listing"] = {k: {kk: vv for kk, vv in v.items() if kk != "mzxml_names"} for k, v in listing.items()}
    summary["ftp_mzxml_namesets_identical_FILES_RAW_DERIVED"] = (
        listing["FILES"]["mzxml_names"] == listing["RAW_FILES"]["mzxml_names"] == listing["DERIVED_FILES"]["mzxml_names"])
    summary["ftp_mzxml_nameset_equals_gnps_source_files"] = listing["FILES"]["mzxml_names"] == gnps_files
    ann = json.loads((DL / "MTBLS8109.announcement.json").read_bytes())
    summary["mtbls_announcement"] = {k: ann.get(k) for k in ["license", "submission_date", "public_release_date",
                                                              "revision", "revision_datetime"]}
    summary["mtbls_announcement_n_derived_data_files"] = len(ann.get("derived_data_file_list") or [])
    summary["mtbls_announcement_n_supplementary_files"] = len(ann.get("supplementary_file_list") or [])
    ws = json.loads((DL / "MTBLS8109_ws_public_study.json").read_bytes())["content"]
    summary["mtbls_ws"] = {k: ws.get(k) for k in ["studySize", "studyHumanReadable", "revisionNumber",
                                                   "revisionDatetime"]}

    # link GNPS record -> assay row -> MAF row (by file basename then sample name)
    a_tab["file_base"] = a_tab["Derived Spectral Data File"].str.split("/").str[-1]
    link = a_tab[["Sample Name", "file_base"]].merge(
        m_tab, left_on="Sample Name", right_on="metabolite_identification", how="left")
    link = link.merge(s_tab[["Sample Name", "Factor Value[Chemical class]", "Factor Value[Adduct]"]],
                      on="Sample Name", how="left")
    g = g.merge(link, left_on="source_file", right_on="file_base", how="left")
    assert len(g) == len(spectra), "link merge changed the row count"
    summary["n_gnps_linked_to_mtbls_assay"] = int(g["Sample Name"].notna().sum())
    summary["n_gnps_linked_to_maf"] = int(g["metabolite_identification"].notna().sum())
    summary["gnps_vs_mtbls_adduct_disagreements"] = int((g["Adduct"] != g["Factor Value[Adduct]"]).sum())

    # --- identity
    rows = []
    for r in g.to_dict("records"):
        rec = {"spectrum_id": r["SpectrumID"], "compound_name": r["Compound_Name"], "adduct": r["Adduct"],
               "ion_mode": r["Ion_Mode"], "charge": r["Charge"], "precursor_mz_gnps": float(r["Precursor_MZ"]),
               "exact_mass_gnps": float(r["ExactMass"]), "source_file": r["source_file"],
               "chemical_class": r["Factor Value[Chemical class]"], "smiles_gnps": r["Smiles"],
               "smiles_maf": r["smiles"], "formula_maf": r["chemical_formula"], "mz_maf": r["mass_to_charge"],
               "adduct_maf": r["modifications"], "retention_time_maf": r["retention_time"]}
        k, sg = SK.key_and_group(r["Smiles"])
        rec["key"], rec["scaffold_group"] = k, sg
        km, sgm = SK.key_and_group(r["smiles"]) if isinstance(r["smiles"], str) and r["smiles"] else (None, None)
        rec["key_maf"], rec["scaffold_group_maf"] = km, sgm
        pm = SK.parent_mol(r["Smiles"]) if k else None
        if pm is not None:
            mono = Descriptors.ExactMolWt(pm)
            rec["formula_rdkit_parent"] = rdMolDescriptors.CalcMolFormula(pm)
            rec["monoisotopic_mass_parent"] = mono
            add = r["Adduct"]
            mult = 2 if add.startswith("2M") else 1
            sign = 1 if add.endswith("+H") else (-1 if add.endswith("-H") else 0)
            theo = mult * mono + sign * PROTON if sign else None
            rec["theoretical_precursor_mz"] = theo
            rec["precursor_err_da"] = (float(r["Precursor_MZ"]) - theo) if theo else None
            rec["exactmass_err_da"] = float(r["ExactMass"]) - mono
            rec["elements"] = "".join(e + ";" for e in sorted({a.GetSymbol() for a in Chem.AddHs(pm).GetAtoms()}))
            rec["n_components_raw"] = len(r["Smiles"].split("."))
            rec["charged_raw"] = any(a.GetFormalCharge() for a in Chem.MolFromSmiles(r["Smiles"]).GetAtoms())
        rows.append(rec)
    df = pd.DataFrame(rows)

    summary["n_key_parsed"] = int(df["key"].notna().sum())
    summary["n_unique_keys_all"] = int(df["key"].nunique())
    summary["n_unique_scaffold_groups_all"] = int(df["scaffold_group"].nunique())
    summary["n_key_maf_parsed"] = int(df["key_maf"].notna().sum())
    both = df[df["key"].notna() & df["key_maf"].notna()]
    summary["gnps_vs_maf_key_disagreements"] = int((both["key"] != both["key_maf"]).sum())
    summary["gnps_vs_maf_key_disagreement_examples"] = both.loc[both["key"] != both["key_maf"],
                                                                ["compound_name", "key", "key_maf"]].head(10).to_dict("records")
    fm = df[df["formula_maf"].fillna("") != ""]
    summary["formula_maf_vs_rdkit_disagreements"] = int((fm["formula_maf"] != fm["formula_rdkit_parent"]).sum())
    bad_mz = df[df["precursor_err_da"].abs() > 0.01]
    summary["precursor_mz_inconsistent_gt_0.01Da"] = int(len(bad_mz))
    summary["precursor_mz_inconsistent_by_adduct"] = dict(collections.Counter(bad_mz["adduct"]))
    summary["precursor_mz_inconsistent_examples"] = bad_mz[["compound_name", "adduct", "precursor_mz_gnps",
                                                            "theoretical_precursor_mz", "precursor_err_da"]].head(12).to_dict("records")
    summary["precursor_err_da_quantiles_consistent"] = (
        df.loc[df["precursor_err_da"].abs() <= 0.01, "precursor_err_da"].quantile([0, .05, .5, .95, 1]).round(4).tolist())
    summary["exactmass_inconsistent_gt_0.01Da"] = int((df["exactmass_err_da"].abs() > 0.01).sum())
    dup = df[df["key"].notna()].groupby("key").size()
    summary["keys_with_multiple_records"] = int((dup > 1).sum())
    summary["records_in_multi_record_keys"] = int(dup[dup > 1].sum())
    summary["charged_raw_smiles"] = int(df["charged_raw"].fillna(False).astype(bool).sum())
    summary["multicomponent_raw_smiles"] = int((df["n_components_raw"].fillna(1) > 1).sum())

    # --- exclusion sets
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
        nm = p.name[len("muru_exposure_registry_population_"):-len("_keys.txt")]
        pops[nm] = read_keys(p)
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
    summary["muru_exposed_population_sizes"] = {k: len(v) for k, v in pops.items()}

    for k, v in sets.items():
        df[f"in_{k}"] = df["key"].isin(v)
    for k, v in pops.items():
        df[f"in_pop_{k}"] = df["key"].isin(v)
    for k, v in groups.items():
        df[f"sg_in_{k}"] = df["scaffold_group"].isin(v)
    df["in_msg15_any_route"] = df["in_msg15_recorded_all"] | df["in_msg15_parent_all"]

    kdf = df[df["key"].notna()]
    ov = {}
    for sub, m in [("all", kdf["key"].notna()), ("M+H", kdf["adduct"] == "M+H"), ("M-H", kdf["adduct"] == "M-H"),
                   ("positive_mode", kdf["ion_mode"] == "Positive")]:
        s = kdf[m]
        d = {"records": int(len(s)), "keys": int(s["key"].nunique()), "scaffold_groups": int(s["scaffold_group"].nunique())}
        for col in [c for c in kdf.columns if c.startswith("in_") or c.startswith("sg_in_")]:
            d[col + "__unique_keys"] = int(s.loc[s[col], "key"].nunique())
        ov[sub] = d
    summary["overlap_unique_keys_by_subset"] = ov

    # MSG rows for overlapping keys (identity/metadata columns only)
    msg = pd.read_parquet(EXC / "msg_row_msnlib_membership.parquet",
                          columns=["identifier", "inchikey14", "parent_key14", "fold", "simulation_challenge", "adduct",
                                   "instrument_type", "collision_energy", "in_msnlib_v1_compound"])
    ek = set(kdf["key"])
    mrows = msg[msg["inchikey14"].isin(ek) | msg["parent_key14"].isin(ek)].copy()
    mrows["k"] = [a if a in ek else b for a, b in zip(mrows["parent_key14"], mrows["inchikey14"])]
    summary["msg_rows_matching_elixdb_keys"] = {
        "rows": int(len(mrows)), "keys": int(mrows["k"].nunique()),
        "instrument_type": dict(collections.Counter(mrows["instrument_type"].fillna("NA"))),
        "adduct": dict(collections.Counter(mrows["adduct"])),
        "fold": dict(collections.Counter(mrows["fold"])),
        "simulation_challenge_rows": int(mrows["simulation_challenge"].sum()),
        "ce_nonnull_rows": int(mrows["collision_energy"].notna().sum()),
        "in_msnlib_v1_compound_rows": int(mrows["in_msnlib_v1_compound"].sum()),
    }
    perkey = mrows.groupby("k").agg(
        n_rows=("identifier", "size"),
        instruments=("instrument_type", lambda x: ";".join(sorted(set(x.fillna("NA"))))),
        adducts=("adduct", lambda x: ";".join(sorted(set(x)))),
        folds=("fold", lambda x: ";".join(sorted(set(x)))),
        sim_rows=("simulation_challenge", "sum"),
        ce_nonnull_rows=("collision_energy", lambda x: int(x.notna().sum()))).reset_index()
    summary["msg_overlap_keys_instrument_pattern"] = dict(collections.Counter(perkey["instruments"]))
    summary["msg_overlap_keys_with_simulation_rows"] = int((perkey["sim_rows"] > 0).sum())

    # hidden-inclusion proxy: keys whose parent formula AND scaffold group both occur in MSG under another key
    mk = pd.read_parquet(EXC / "msg15_row_keys.parquet", columns=["identifier", "parent_key", "scaffold_group"])
    mm = pd.read_parquet(ADJ / "massspecgym15_metadata_columns.parquet", columns=["identifier", "formula"])
    mk = mk.merge(mm, on="identifier", how="left")
    form_sg = set(zip(mk["formula"], mk["scaffold_group"]))
    df["formula_in_msg"] = df["formula_rdkit_parent"].isin(set(mk["formula"]))
    df["formula_and_scaffold_in_msg"] = [(f, s) in form_sg for f, s in zip(df["formula_rdkit_parent"], df["scaffold_group"])]

    # --- pools after exclusion
    def pool(mask, label):
        s = df[mask & df["key"].notna()]
        sgc = s.groupby("scaffold_group")["key"].nunique().sort_values(ascending=False)
        mhs = s[s["adduct"] == "M+H"]
        return {"label": label, "records": int(len(s)), "keys": int(s["key"].nunique()),
                "scaffold_groups": int(s["scaffold_group"].nunique()),
                "acyclic_records": int(s["scaffold_group"].str.startswith("__ACYCLIC__").sum()),
                "largest_scaffold_group_key_counts": [int(x) for x in sgc.head(8).values],
                "singleton_scaffold_groups": int((sgc == 1).sum()),
                "precursor_mz_min_max": [float(s["precursor_mz_gnps"].min()), float(s["precursor_mz_gnps"].max())] if len(s) else None,
                "mh_precursor_outside_70_1042.6": int(((mhs["precursor_mz_gnps"] < 70.0) | (mhs["precursor_mz_gnps"] > 1042.6)).sum()),
                "precursor_inconsistent_gt_0.01Da": int((s["precursor_err_da"].abs() > 0.01).sum()),
                "chemical_class": dict(collections.Counter(s["chemical_class"])),
                "elements_records": dict(collections.Counter(e for x in s["elements"].dropna() for e in x.split(";") if e))}

    mh = df["adduct"] == "M+H"
    key_excl = (df["in_msg15_any_route"] | df["in_muru_registry_all"] | df["in_muru_exposed_union"]
                | df["in_muru_dev_compounds_csv_keys"] | df["in_pr7_study2_population"]
                | df["in_comparator_common_population"])
    key_excl_min = (df["in_msg15_any_route"] | df["in_muru_exposed_populations_union"]
                    | df["in_muru_dev_compounds_csv_keys"] | df["in_pr7_study2_population"]
                    | df["in_comparator_common_population"])
    sg_excl_muru = (df["sg_in_muru_registry_scaffold_groups"] | df["sg_in_muru_dev_scaffold_groups"]
                    | df["sg_in_pr7_scaffold_groups"] | df["sg_in_comparator_scaffold_groups"])
    df["excluded_key_level_conservative"] = key_excl
    df["excluded_scaffold_level_muru_pr7_comparator"] = sg_excl_muru
    pools = [
        pool(df["key"].notna(), "P0 all records"),
        pool(mh, "P1 [M+H]+ records"),
        pool(mh & ~key_excl_min, "P2 [M+H]+, key not in MSG1.5 (either route), MURU exposed populations, MURU dev, PR7, comparator"),
        pool(mh & ~key_excl, "P3 [M+H]+, key-level exclusion incl. full MURU registry (conservative)"),
        pool(mh & ~key_excl & ~df["in_msnlib_9lib"], "P4 = P3 and key not in MSnLib 9-lib (FIORA proxy)"),
        pool(mh & ~key_excl & ~sg_excl_muru, "P5 = P3 and scaffold group not in MURU registry/dev, PR7, comparator groups"),
        pool(mh & ~key_excl & ~sg_excl_muru & ~df["sg_in_msg15_scaffold_groups"],
             "P6 = P5 and scaffold group not in MSG1.5 scaffold groups (strict)"),
        pool(mh & ~key_excl & ~df["formula_and_scaffold_in_msg"],
             "P7 = P3 and not (same parent formula AND same scaffold group as some MSG1.5 compound)"),
        pool(mh & ~key_excl & (df["precursor_err_da"].abs() <= 0.01),
             "P8 = P3 and GNPS precursor consistent with SMILES within 0.01 Da"),
        pool((df["ion_mode"] == "Negative") & ~key_excl, "N1 [M-H]- records, key-level exclusion (outside MURU domain)"),
    ]
    summary["pools"] = pools
    summary["P3_formula_and_scaffold_in_msg"] = int((mh & ~key_excl & df["formula_and_scaffold_in_msg"]).sum())

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "elixdb_records_identity_overlap.csv", index=False)
    perkey.to_csv(OUT / "elixdb_keys_in_msg15_row_summary.csv", index=False)
    (OUT / "screen_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("gnps_fields", "ftp_listing")}, indent=1, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.analyze:
        analyze()
