"""S4 screen, candidate C04 (ELIXDB lichen library): criterion adjudication pass.

Second pass on top of scripts/ce_interface_adjudication/screen_elixdb_lichen.py (which produced
artifacts/ce_interface_adjudication/screen/elixdb_lichen/{elixdb_records_identity_overlap.csv,screen_summary.json}).
This script adds the evidence the criterion table needs and does NOT recompute what the first pass already
verified, except the post-exclusion pools, which it re-derives from the first pass's per-record CSV.

What it adds
  1. Collision-energy semantics evidence: every CE-bearing string in the MetaboLights ISA-Tab, the MetaboLights
     MHD (MetabolomicsHub common data model) JSON, and the GNPS record fields; plus the per-compound spectrum
     count implied by the FTP listing (one merged spectrum per compound or three).
  2. Hidden-MassSpecGym-inclusion test (criterion 11): the 46 GNPS library names MassSpecGym 1.0 actually loaded
     (notebook 1 cell 1), same-group GNPS-LIBRARY uploads (PI Chooi / collector Bracegirdle) and their
     MassSpecGym rows matched on key AND 3-decimal precursor m/z, and the LDB (lichen, Q-TOF) library overlap.
  3. Post-exclusion pools restricted to the ICEBERG/GLACIER training universe (MassSpecGym simulation-challenge
     rows) in addition to all-fold MassSpecGym.

Metadata only. No spectra file (mzXML/mzML/MGF/MSP/raw) is fetched or read. No model is run.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
OUT = ADJ / "screen" / "elixdb_lichen"
DL = OUT / "downloads"
EXC = ADJ / "exclusion"
REGISTER = ADJ / "downloads_register.jsonl"
TASK = "S4-C04"
SCRIPT_REL = "scripts/ce_interface_adjudication/screen_elixdb_lichen_criteria.py"
MAX_BYTES = 50_000_000

FETCH = [
    ("gnps_libraryservlet_LDB_POSITIVE.json",
     "https://gnps.ucsd.edu/ProteoSAFe/LibraryServlet?library=LDB_POSITIVE",
     "GNPS LibraryServlet metadata for LDB_POSITIVE (lichen Q-TOF library that MassSpecGym 1.0 did load); "
     "peaks_json verified null for every record"),
    ("gnps_libraryservlet_LDB_NEGATIVE.json",
     "https://gnps.ucsd.edu/ProteoSAFe/LibraryServlet?library=LDB_NEGATIVE",
     "GNPS LibraryServlet metadata for LDB_NEGATIVE; peaks_json verified null for every record"),
    ("MTBLS8109.mhd.json",
     "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS8109/MTBLS8109.mhd.json",
     "MetaboLights MHD common-data-model study metadata JSON (protocols, parameters, file list, licence); "
     "no peak arrays"),
    ("massspecgym_nb1_1_Load_data_from_repositories.ipynb",
     "https://api.github.com/repos/pluskal-lab/MassSpecGym/contents/"
     "notebooks/dataset_construction/1_Load_data_from_repositories.ipynb?ref=1a54459",
     "MassSpecGym dataset-construction notebook 1 (GitHub source code, base64 contents API) listing the 46 GNPS "
     "libraries that were downloaded on 13/05/2024"),
]


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
        assert not url.lower().endswith((".mzxml", ".mzml", ".mgf", ".msp", ".raw", ".hdf5", ".h5")), url
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata screen)",
                                                   "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read(MAX_BYTES + 1)
            final_url = r.geturl()
        assert len(data) <= MAX_BYTES, f"{url} exceeds the 50 MB metadata cap"
        if name.endswith(".ipynb"):
            import base64
            data = base64.b64decode(json.loads(data)["content"])
        if name.startswith("gnps_libraryservlet"):
            spectra = json.loads(data.decode("utf-8", "replace"))["spectra"]
            nonnull = sum(1 for s in spectra if s.get("peaks_json") not in (None, "null", ""))
            if nonnull:
                raise SystemExit(f"{url}: {nonnull} non-null peaks_json; response discarded, nothing stored")
        low = data[:400_000].lower()
        if name.endswith(".mhd.json"):
            for bad in (b'"mz_array"', b'"intensity_array"', b'"peaks"'):
                assert bad not in low, f"{name} appears to carry peak arrays; not stored"
        (DL / name).write_bytes(data)
        append_register({
            "fetched_utc": datetime.now(timezone.utc).isoformat(),
            "task": TASK,
            "name": f"{name} ({desc})",
            "source_url": url,
            "final_url": final_url if final_url != url else None,
            "size_bytes": len(data),
            "sha256": sha256_bytes(data),
            "stored_as": str((DL / name).relative_to(ROOT)),
            "script": SCRIPT_REL,
        })
        print("fetched", name, len(data), sha256_bytes(data)[:12])


def jload(p: Path):
    return json.loads(p.read_bytes().decode("utf-8", "replace"))


def read_keys(p: Path) -> set[str]:
    return {x.strip() for x in p.read_text().splitlines() if x.strip()}


def walk_strings(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def analyze() -> None:
    import pandas as pd
    sys.path.insert(0, str(ROOT / "scripts" / "ce_interface_adjudication"))
    import scaffold_key as SK  # noqa: E402

    S: dict = {"script": SCRIPT_REL, "generated_utc": datetime.now(timezone.utc).isoformat()}

    # ------------------------------------------------------------------ 1. CE semantics evidence
    ce_ev = {}
    inv = (DL / "MTBLS8109_i_Investigation.txt").read_text(encoding="utf-8", errors="replace").split("\n")
    hits = []
    for i, line in enumerate(inv, 1):
        for m in re.finditer(r"[^\t]*(collision|energ|\beV\b|NCE|normali[sz]ed|stepped|HCD)[^\t]*", line, re.I):
            seg = m.group(0)
            if len(seg) > 900:
                j = max(0, seg.lower().find("collision") - 200)
                seg = seg[j:j + 700]
            hits.append({"file": "downloads/MTBLS8109_i_Investigation.txt", "line": i,
                         "field": line.split("\t")[0][:60], "text": seg.strip()})
    ce_ev["isa_investigation"] = hits

    s_tab = pd.read_csv(DL / "MTBLS8109_s_MTBLS8109.txt", sep="\t", dtype=str, keep_default_na=False)
    a_tab = pd.read_csv(DL / "MTBLS8109_a_LC-MS_metabolite_profiling.txt", sep="\t", dtype=str,
                        keep_default_na=False)
    ce_ev["isa_sample_columns_mentioning_energy"] = [c for c in s_tab.columns if re.search(r"energ|collision", c, re.I)]
    ce_ev["isa_assay_columns_mentioning_energy"] = [c for c in a_tab.columns if re.search(r"energ|collision", c, re.I)]
    ce_ev["isa_sample_collision_energy_value_counts"] = dict(
        collections.Counter(s_tab["Comment[Collision energy]"])) if "Comment[Collision energy]" in s_tab else {}
    ce_ev["isa_sample_collision_energy_unit_column_present"] = any(
        re.search(r"unit", c, re.I) for c in s_tab.columns)
    ce_ev["isa_assay_all_columns"] = list(a_tab.columns)

    mhd_path = DL / "MTBLS8109.mhd.json"
    if mhd_path.exists():
        mhd = jload(mhd_path)
        mhits = []
        for path, val in walk_strings(mhd):
            if re.search(r"collision|\beV\b|normali[sz]ed collision|NCE|stepped", val, re.I):
                v = val if len(val) <= 700 else val[max(0, val.lower().find("collision") - 200):][:700]
                mhits.append({"json_path": path, "text": v.strip()})
        ce_ev["mhd_json_matches"] = mhits[:40]
        ce_ev["mhd_json_match_count"] = len(mhits)
        ce_ev["mhd_licence_strings"] = sorted({v for p, v in walk_strings(mhd)
                                               if re.search(r"creativecommons|licen[cs]e|CC0|CC-BY|terms-of-use", v, re.I)})[:20]
    S["ce_semantics_evidence"] = ce_ev

    # spectra-per-compound: FTP listing vs GNPS record count (already stored in the first pass summary)
    first = jload(OUT / "screen_summary.json")
    S["spectra_per_compound"] = {
        "gnps_records": first["gnps_n_records"],
        "gnps_distinct_source_files": None,  # filled below
        "mtbls_FILES_mzXML": first["ftp_listing"]["FILES"]["by_extension"].get("mzXML"),
        "mtbls_RAW_FILES_mzXML": first["ftp_listing"]["RAW_FILES"]["by_extension"].get("mzXML"),
        "mtbls_DERIVED_FILES_mzXML": first["ftp_listing"]["DERIVED_FILES"]["by_extension"].get("mzXML"),
        "namesets_identical": first["ftp_mzxml_namesets_identical_FILES_RAW_DERIVED"],
        "nameset_equals_gnps_source_files": first["ftp_mzxml_nameset_equals_gnps_source_files"],
        "mzxml_size_strings": first["ftp_listing"]["FILES"]["mzxml_size_strings"],
        "assay_distinct_derived_files": first["mtbls_a_n_distinct_derived_files"],
        "assay_raw_spectral_data_file_counts": first["mtbls_a_Raw Spectral Data File_counts"],
    }

    # ------------------------------------------------------------------ 2. records table from pass 1
    df = pd.read_csv(OUT / "elixdb_records_identity_overlap.csv")
    S["spectra_per_compound"]["gnps_distinct_source_files"] = int(df["source_file"].nunique())
    S["spectra_per_compound"]["gnps_records_per_source_file_max"] = int(df.groupby("source_file").size().max())

    # ------------------------------------------------------------------ 3. MassSpecGym library list
    nb = jload(DL / "massspecgym_nb1_1_Load_data_from_repositories.ipynb")
    cells = ["".join(c["source"]) for c in nb["cells"]]
    libs = sorted(set(re.findall(r"'([A-Za-z0-9_\-\.]+)\.mgf'", cells[1])))
    S["massspecgym_gnps_libraries"] = {
        "download_date_string": re.search(r"downloaded on ([0-9/]+)", cells[0]).group(1) if re.search(r"downloaded on ([0-9/]+)", cells[0]) else None,
        "n_libraries": len(libs),
        "contains_ELIXDB": any("ELIX" in x.upper() for x in libs),
        "lichen_related": [x for x in libs if x.upper().startswith("LDB") or "LICHEN" in x.upper()],
        "contains_GNPS_LIBRARY": "GNPS-LIBRARY" in libs,
        "libraries": libs,
    }

    # ------------------------------------------------------------------ 4. same-group GNPS-LIBRARY uploads
    gl = pd.DataFrame(jload(DL / "gnps_libraryservlet_GNPS-LIBRARY.json")["spectra"]).drop(columns=["peaks_json"])
    txt = (gl["PI"].fillna("") + "|" + gl["Data_Collector"].fillna("") + "|" + gl["submit_user"].fillna("")).str.lower()
    grp = gl[txt.str.contains("bracegirdle") | (gl["PI"].fillna("").str.strip().str.lower() == "chooi")].copy()
    grp["key"] = [SK.key_and_group(s)[0] for s in grp["Smiles"].fillna("")]
    elix_keys = set(df.loc[df["key"].notna(), "key"])
    elix_by_key = df.groupby("key").first()
    grp["key_in_elixdb"] = grp["key"].isin(elix_keys)
    grp["elixdb_source_file_stem_match"] = [
        any(str(sf).split("/")[-1].split("[")[0].strip().lower() == str(e).split(".mzxml")[0].strip().lower()
            for e in df["source_file"].fillna(""))
        for sf in grp["source_file"].fillna("")
    ]
    S["gnps_library_same_group_uploads"] = {
        "n_records": int(len(grp)),
        "by_year": dict(collections.Counter(grp["create_time"].str[:4])),
        "orbitrap_records": int((grp["Instrument"].str.lower() == "orbitrap").sum()),
        "records": grp[["SpectrumID", "Compound_Name", "Adduct", "Instrument", "Ion_Mode", "PI", "Data_Collector",
                        "create_time", "Precursor_MZ", "source_file", "key", "key_in_elixdb",
                        "elixdb_source_file_stem_match"]].to_dict("records"),
    }

    # MassSpecGym rows for those keys, matched also on the 3-decimal precursor m/z
    msgrow = pd.read_parquet(EXC / "msg_row_msnlib_membership.parquet",
                             columns=["identifier", "inchikey14", "parent_key14", "fold", "simulation_challenge",
                                      "adduct", "instrument_type", "collision_energy", "precursor_mz_decimals"])
    msgmeta = pd.read_parquet(ADJ / "massspecgym15_metadata_columns.parquet",
                              columns=["identifier", "precursor_mz", "formula"])
    msg = msgrow.merge(msgmeta, on="identifier", how="left")
    msg["identifier_num"] = msg["identifier"].str.extract(r"(\d+)").astype(int)

    matches = []
    for r in grp.itertuples(index=False):
        if not isinstance(r.key, str):
            continue
        sub = msg[(msg["inchikey14"] == r.key) | (msg["parent_key14"] == r.key)]
        for m in sub.itertuples(index=False):
            matches.append({
                "gnps_spectrum_id": r.SpectrumID, "gnps_compound": r.Compound_Name, "gnps_adduct": r.Adduct,
                "gnps_instrument": r.Instrument, "gnps_create_time": r.create_time,
                "gnps_precursor_mz": float(r.Precursor_MZ), "key": r.key,
                "msg_identifier": m.identifier, "msg_identifier_num": int(m.identifier_num),
                "msg_precursor_mz": float(m.precursor_mz) if m.precursor_mz == m.precursor_mz else None,
                "msg_precursor_decimals": int(m.precursor_mz_decimals) if m.precursor_mz_decimals == m.precursor_mz_decimals else None,
                "msg_adduct": m.adduct, "msg_instrument": m.instrument_type,
                "msg_collision_energy": None if m.collision_energy != m.collision_energy else float(m.collision_energy),
                "msg_fold": m.fold, "msg_simulation_challenge": bool(m.simulation_challenge),
                "precursor_exact_3dp_match": (round(float(r.Precursor_MZ), 3) == round(float(m.precursor_mz), 3))
                if m.precursor_mz == m.precursor_mz else False,
            })
    S["gnps_library_same_group_msg_matches"] = matches

    # ------------------------------------------------------------------ 5. LDB overlap (lichen library IN MassSpecGym)
    ldb_rows = []
    for fn, lab in [("gnps_libraryservlet_LDB_POSITIVE.json", "LDB_POSITIVE"),
                    ("gnps_libraryservlet_LDB_NEGATIVE.json", "LDB_NEGATIVE")]:
        p = DL / fn
        if not p.exists():
            continue
        for s in jload(p)["spectra"]:
            ldb_rows.append({"library": lab, "SpectrumID": s.get("SpectrumID"),
                             "Compound_Name": s.get("Compound_Name"), "Adduct": s.get("Adduct"),
                             "Instrument": s.get("Instrument"), "Ion_Mode": s.get("Ion_Mode"),
                             "Precursor_MZ": s.get("Precursor_MZ"), "Smiles": s.get("Smiles"),
                             "create_time": s.get("create_time")})
    ldb = pd.DataFrame(ldb_rows)
    if len(ldb):
        ldb["key"] = [SK.key_and_group(s)[0] if isinstance(s, str) else None for s in ldb["Smiles"]]
        ldb_keys = set(ldb["key"].dropna())
        msg_all = read_keys(EXC / "msg15_keys_all.txt") | read_keys(EXC / "msg15_parent_keys_all.txt")
        msg_sim = read_keys(EXC / "msg15_simchallenge_keys_all.txt")
        S["ldb"] = {
            "records": int(len(ldb)),
            "by_library": dict(collections.Counter(ldb["library"])),
            "instrument_counts": dict(collections.Counter(ldb["Instrument"].fillna("NA"))),
            "adduct_counts": dict(collections.Counter(ldb["Adduct"].fillna("NA"))),
            "keys": len(ldb_keys),
            "keys_in_msg15_any_route": len(ldb_keys & msg_all),
            "keys_in_msg15_simulation_challenge": len(ldb_keys & msg_sim),
            "elixdb_keys_also_in_ldb": len(elix_keys & ldb_keys),
            "elixdb_MH_keys_also_in_ldb": int(df.loc[(df["adduct"] == "M+H") & df["key"].notna(), "key"]
                                              .isin(ldb_keys).groupby(df["key"]).any().sum()),
        }
        df["key_in_ldb"] = df["key"].isin(ldb_keys)
    else:
        S["ldb"] = {"records": 0}
        df["key_in_ldb"] = False

    # ------------------------------------------------------------------ 6. pools, incl. the ICEBERG/GLACIER universe
    dev = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv", usecols=["parent_key", "scaffold_group"])
    sim_keys = read_keys(EXC / "msg15_simchallenge_keys_all.txt")
    df["in_msg15_simchallenge_any_route"] = df["in_msg15_simchallenge_all"]
    key_excl_min = (df["in_msg15_any_route"] | df["in_muru_exposed_populations_union"]
                    | df["in_muru_dev_compounds_csv_keys"] | df["in_pr7_study2_population"]
                    | df["in_comparator_common_population"])
    key_excl_cons = (df["in_msg15_any_route"] | df["in_muru_registry_all"] | df["in_muru_exposed_union"]
                     | df["in_muru_dev_compounds_csv_keys"] | df["in_pr7_study2_population"]
                     | df["in_comparator_common_population"])
    key_excl_sim = (df["in_msg15_simchallenge_all"] | df["in_muru_registry_all"] | df["in_muru_exposed_union"]
                    | df["in_muru_dev_compounds_csv_keys"] | df["in_pr7_study2_population"]
                    | df["in_comparator_common_population"])
    sg_excl_muru = (df["sg_in_muru_registry_scaffold_groups"] | df["sg_in_muru_dev_scaffold_groups"]
                    | df["sg_in_pr7_scaffold_groups"] | df["sg_in_comparator_scaffold_groups"])

    def pool(mask, label):
        s = df[mask & df["key"].notna()]
        sgc = s.groupby("scaffold_group")["key"].nunique().sort_values(ascending=False)
        return {"label": label, "records": int(len(s)), "keys": int(s["key"].nunique()),
                "scaffold_groups": int(sgc.size),
                "singleton_scaffold_groups": int((sgc == 1).sum()),
                "largest_scaffold_group_key_counts": [int(x) for x in sgc.head(6).values],
                "keys_also_in_ldb": int(s.loc[s["key_in_ldb"], "key"].nunique()),
                "chemical_class": dict(collections.Counter(s["chemical_class"]))}

    mh = df["adduct"] == "M+H"
    S["pools"] = [
        pool(mh, "Q1 all [M+H]+ records"),
        pool(mh & ~key_excl_min, "Q2 [M+H]+ minus MSG1.5(all folds) + MURU exposed populations + dev + PR7 + comparator keys"),
        pool(mh & ~key_excl_cons, "Q3 = Q2 with the full MURU exposure registry (conservative)"),
        pool(mh & ~key_excl_sim, "Q4 [M+H]+ minus MSG1.5 SIMULATION-CHALLENGE keys only (the ICEBERG/GLACIER training universe) + MURU sets"),
        pool(mh & ~key_excl_cons & ~sg_excl_muru, "Q5 = Q3 and scaffold group not in MURU registry/dev/PR7/comparator"),
        pool(mh & ~key_excl_cons & ~df["sg_in_msg15_scaffold_groups"], "Q6 = Q3 and scaffold group not in MSG1.5"),
        pool(mh & ~key_excl_cons & ~df["key_in_ldb"], "Q7 = Q3 and key not in the GNPS LDB lichen library"),
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "c04_criteria_evidence.json").write_text(json.dumps(S, indent=1, default=str))
    df.to_csv(OUT / "c04_records_with_ldb_flag.csv", index=False)
    if len(ldb):
        ldb.to_csv(OUT / "c04_ldb_records.csv", index=False)
    print(json.dumps({k: v for k, v in S.items()
                      if k not in ("massspecgym_gnps_libraries", "ce_semantics_evidence")}, indent=1, default=str)[:12000])
    print("libs:", S["massspecgym_gnps_libraries"]["n_libraries"],
          "ELIXDB:", S["massspecgym_gnps_libraries"]["contains_ELIXDB"],
          "lichen:", S["massspecgym_gnps_libraries"]["lichen_related"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.analyze:
        analyze()
