#!/usr/bin/env python3
"""S2 screen C02: CyanoMetDB spectra in MassBank 2026.03 (MSBNK-EAWAG-EC/ED, MSBNK-MLU-ED).

Metadata only. Inputs (all under artifacts/ce_interface_adjudication/screen/c02_cyanometdb/downloads/):
  np6c00107_si_002.xlsx                   extended Table S4 (compound identities, levels, accession lists)
  np6c00107_si_001.pdf                    SI (Table S4 short form with '#' marks for previously deposited compounds)
  massbank_data_Eawag_tree_tag_2026.03.json, ..._branch_dev.json   git tree listings (names + blob sha)
  massbank_codesearch_fragments.jsonl     header-line fragments per record (no peaks)
Exclusion sets from P5 (artifacts/ce_interface_adjudication/exclusion/) and scaffold_key.py.

Outputs (screen/c02_cyanometdb/):
  records.csv        one row per MassBank record file (3,126), parsed header fields
  compounds.csv      one row per S4 compound or isomer-group member, with keys, scaffolds, overlap flags, CE ladders
  summary.json       all counts used in the screen verdict
"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import Descriptors, rdMolDescriptors, AllChem, DataStructs
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina

RDLogger.DisableLog("rdApp.*")
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

OUT = W / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb"
DL = OUT / "downloads"
EX = W / "artifacts/ce_interface_adjudication/exclusion"
PROTON = 1.007276467
MSG_MAX_PRECURSOR = 999.396          # MassSpecGym 1.5 max precursor_mz (candidate brief; re-verified below)
MURU_MH_RANGE = (70.0, 1042.6)       # src/muru/wur_v2/msnlib_design.py:27 DEV_MH_RANGE (P5 note section 4)
GLACIER_UPPER_LIMIT = 1500           # checkpoint hparams upper_limit (t1/checkpoint_hyperparameters.jsonl)
NAME_RE = re.compile(r"MSBNK-(EAWAG-E[CD]|MLU-ED)\d+\.txt")


def readset(name):
    return set(x.strip() for x in (EX / name).read_text().splitlines() if x.strip())


def parse_fragments():
    recs = collections.defaultdict(dict)
    shas = {}
    meta = []
    for line in (DL / "massbank_codesearch_fragments.jsonl").open():
        j = json.loads(line)
        meta.append({k: j[k] for k in ("query_id", "prefix", "expected_files_in_tag_tree", "total_count",
                                        "incomplete_results")} | {"n_items": len(j["items"])})
        for it in j["items"]:
            fn = it["path"].split("/")[-1]
            shas.setdefault(fn, set()).add(it["blob_sha"])
            d = recs[fn]
            d.setdefault("_queries", set()).add(j["query_id"])
            for frag in it["fragments"]:
                for ln in frag.split("\n"):
                    m = re.match(r"^(ACCESSION|RECORD_TITLE|DATE|LICENSE|COPYRIGHT|COMMENT|AUTHORS): ?(.*)$", ln)
                    if m:
                        d[m.group(1)] = m.group(2)
                        continue
                    m = re.match(r"^(CH\$LINK|AC\$MASS_SPECTROMETRY|MS\$FOCUSED_ION|AC\$CHROMATOGRAPHY|MS\$DATA_PROCESSING): (\S+) ?(.*)$", ln)
                    if m:
                        d[m.group(1) + ":" + m.group(2)] = m.group(3)
                        continue
                    m = re.match(r"^(AC\$INSTRUMENT|AC\$INSTRUMENT_TYPE|CH\$SMILES|CH\$IUPAC|CH\$FORMULA|CH\$EXACT_MASS|CH\$NAME): ?(.*)$", ln)
                    if m:
                        d[m.group(1)] = m.group(2)
    return recs, shas, meta


def parse_title(t):
    out = {"title_name": None, "title_ce": None, "title_R": None, "title_adduct": None,
           "title_first_mass": None, "title_other": []}
    if not isinstance(t, str):
        return out
    parts = [p.strip() for p in t.split(";")]
    names = []
    for p in parts:
        if p.startswith("CE:"):
            out["title_ce"] = p[3:].strip()
        elif p.startswith("R="):
            out["title_R"] = p[2:].strip()
        elif p.startswith("[") and ("]+" in p or "]-" in p or re.search(r"\][0-9]*[+-]", p)):
            out["title_adduct"] = p
        elif p.lower().startswith("first mass"):
            out["title_first_mass"] = p.split(":")[-1].strip()
        elif p in ("MS2", "LC-ESI-QFT", "LC-ESI-ITFT", "LC-ESI-QTOF") or p.startswith("LC-") or p == "MS":
            out["title_other"].append(p)
        else:
            names.append(p)
    out["title_name"] = "; ".join(names) if names else None
    out["title_other"] = "|".join(out["title_other"])
    return out


def ce_number(s):
    if not isinstance(s, str):
        return None
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)", s)
    return float(m.group(1)) if m else None


def mass_range(s):
    if not isinstance(s, str):
        return (None, None)
    m = re.match(r"^\s*([0-9.]+)\s*-\s*([0-9.]+)", s)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"rdkit": rdBase.rdkitVersion}

    # ---------------- trees ----------------
    tag = {t["path"]: t["sha"] for t in json.load(open(DL / "massbank_data_Eawag_tree_tag_2026.03.json"))["tree"]}
    dev = {t["path"]: t["sha"] for t in json.load(open(DL / "massbank_data_Eawag_tree_branch_dev.json"))["tree"]}
    files = sorted(p for p in tag if NAME_RE.fullmatch(p))
    summary["tree"] = {
        "n_record_files_tag_2026.03": len(files),
        "by_series_tag": dict(collections.Counter(re.sub(r"\d+\.txt$", "", p) for p in files)),
        "n_record_files_dev": sum(1 for p in dev if NAME_RE.fullmatch(p)),
        "n_blob_changed_tag_to_dev": sum(1 for p in files if dev.get(p) != tag[p]),
    }

    # ---------------- fragments ----------------
    recs, shas, meta = parse_fragments()
    summary["codesearch"] = {
        "n_query_partitions": len(meta),
        "n_partitions_total_count_ne_expected": sum(1 for m in meta if m["total_count"] != m["expected_files_in_tag_tree"]),
        "n_partitions_items_ne_total": sum(1 for m in meta if m["n_items"] != m["total_count"]),
        "n_incomplete_results": sum(1 for m in meta if m["incomplete_results"]),
        "n_record_files_seen": len(recs),
        "n_tag_files_not_seen": len(set(files) - set(recs)),
        "n_seen_not_in_tag": len(set(recs) - set(files)),
    }
    rows = []
    for fn in files:
        d = recs.get(fn, {})
        sha_seen = shas.get(fn, set())
        r = {
            "file": fn, "accession": fn[:-4], "series": re.sub(r"\d+$", "", fn[:-4]),
            "stem": fn[:-4][:-2], "spec_index": int(fn[:-4][-2:]),
            "queries_seen": "|".join(sorted(d.get("_queries", []))),
            "blob_sha_tag": tag[fn], "blob_sha_dev": dev.get(fn),
            "fragment_blob_shas": "|".join(sorted(sha_seen)),
            "fragment_matches_tag_blob": tag[fn] in sha_seen and len(sha_seen) == 1,
            "record_title": d.get("RECORD_TITLE"), "date": d.get("DATE"),
            "inchikey_record": d.get("CH$LINK:INCHIKEY"),
            "instrument": d.get("AC$INSTRUMENT"), "instrument_type": d.get("AC$INSTRUMENT_TYPE"),
            "ms_type": d.get("AC$MASS_SPECTROMETRY:MS_TYPE"),
            "fragmentation_mode": d.get("AC$MASS_SPECTROMETRY:FRAGMENTATION_MODE"),
            "collision_energy_str": d.get("AC$MASS_SPECTROMETRY:COLLISION_ENERGY"),
            "resolution": d.get("AC$MASS_SPECTROMETRY:RESOLUTION"),
            "mass_range": d.get("AC$MASS_SPECTROMETRY:MASS_RANGE_M/Z"),
            "precursor_mz": d.get("MS$FOCUSED_ION:PRECURSOR_M/Z"),
            "precursor_type": d.get("MS$FOCUSED_ION:PRECURSOR_TYPE"),
        }
        r.update(parse_title(r["record_title"]))
        r["ce_nce_title"] = ce_number(r["title_ce"])
        r["ce_nce_field"] = ce_number(r["collision_energy_str"])
        lo, hi = mass_range(r["mass_range"])
        r["mass_range_lo"], r["mass_range_hi"] = lo, hi
        try:
            r["precursor_mz"] = float(r["precursor_mz"]) if r["precursor_mz"] is not None else None
        except ValueError:
            pass
        rows.append(r)
    R = pd.DataFrame(rows)

    def vc(s):
        return {str(k): int(v) for k, v in s.value_counts(dropna=False).items()}

    R["precursor_mz"] = pd.to_numeric(R["precursor_mz"], errors="coerce")
    R["muru_window_ok"] = (R["mass_range_lo"] <= 40) & (R["mass_range_hi"] >= R["precursor_mz"] + 1)
    wr = R[R["mass_range"].notna()]
    summary["scan_window_sample"] = {
        "n_records_with_scan_range": int(len(wr)),
        "by_series_firstmass": {f"{s_}|{fm}": {"n": int(len(g)), "lo_values": vc(g["mass_range_lo"]),
                                              "n_muru_window_ok": int(g["muru_window_ok"].sum()) if "muru_window_ok" in g else None}
                                for (s_, fm), g in wr.groupby(["series", wr["title_first_mass"].fillna("none")])},
    }
    summary["records"] = {
        "instrument_by_series": {s: vc(g["instrument"]) for s, g in R.groupby("series")},
        "instrument_type": vc(R["instrument_type"]),
        "fragmentation_mode": vc(R["fragmentation_mode"]),
        "ce_string_forms": vc(R["collision_energy_str"].fillna("NA").str.replace(r"^[0-9.]+", "<n>", regex=True)),
        "title_ce_forms": vc(R["title_ce"].fillna("NA").str.replace(r"^[0-9.]+", "<n>", regex=True)),
        "title_vs_field_ce_disagree": int(((R["ce_nce_title"] != R["ce_nce_field"]) & R["ce_nce_title"].notna() & R["ce_nce_field"].notna()).sum()),
        "resolution_by_series": {s: vc(g["resolution"]) for s, g in R.groupby("series")},
        "title_R_by_series": {s: vc(g["title_R"]) for s, g in R.groupby("series")},
        "precursor_type": vc(R["precursor_type"]),
        "title_adduct": vc(R["title_adduct"]),
        "precursor_type_vs_title_disagree": int(((R["precursor_type"] != R["title_adduct"]) & R["precursor_type"].notna() & R["title_adduct"].notna()).sum()),
        "title_first_mass_by_series": {s: vc(g["title_first_mass"]) for s, g in R.groupby("series")},
        "mass_range_lo_by_series_first_mass": {f"{s}|{fm}": {"n": len(g), "lo_min": g["mass_range_lo"].min(), "lo_max": g["mass_range_lo"].max()}
                                               for (s, fm), g in R.groupby(["series", R["title_first_mass"].fillna("none")])},
        "date_by_series": {s: vc(g["date"].str[:7]) for s, g in R.groupby("series")},
        "title_other": vc(R["title_other"]),
        "ce_nce_values_by_series_adduct": {f"{s}|{im}": vc(g["ce_nce_title"]) for (s, im), g in R.groupby(["series", R["precursor_type"].fillna("NA")])},
        "n_fragment_matches_tag_blob": int(R["fragment_matches_tag_blob"].sum()),
        "n_missing_title": int(R["record_title"].isna().sum()),
        "n_missing_inchikey_line": int(R["inchikey_record"].isna().sum()),
        "n_missing_instrument": int(R["instrument"].isna().sum()),
        "n_missing_precursor": int(R["precursor_mz"].isna().sum()),
        "n_missing_ce_field": int(R["collision_energy_str"].isna().sum()),
        "n_title_tentative": int(R["record_title"].fillna("").str.contains("TENTATIVE", case=False).sum()),
        "n_title_tentative_by_series": {s: int(g["record_title"].fillna("").str.contains("TENTATIVE", case=False).sum()) for s, g in R.groupby("series")},
    }

    # ---------------- Table S4 ----------------
    s4 = pd.read_excel(DL / "np6c00107_si_002.xlsx", header=0)
    s4.columns = ["id", "name", "formula", "n_m2h", "n_mh_auto", "n_mh_40", "n_mmh_auto", "n_mmh_40", "n_total",
                  "level", "source", "purity", "doi", "smiles", "inchikey", "stems", "stems_etc", "accessions", "extra"]
    si_txt = subprocess.run(["pdftotext", "-layout", str(DL / "np6c00107_si_001.pdf"), "-"],
                            capture_output=True, text=True).stdout
    hash_ids = sorted(set(re.findall(r"^\s*(\d+)\s+#\s", si_txt, flags=re.M)), key=int)
    summary["s4"] = {"rows": len(s4), "hash_marked_previously_in_massbank_ids_from_si_pdf": hash_ids}

    comp_rows = []
    unit = None  # current S4 row with spectra (compound or isomer group)
    acc2unit = {}
    for i, r in s4.iterrows():
        idv = str(r["id"]).strip()
        acc = ",".join(str(x) for x in (r["accessions"], r["extra"]) if isinstance(x, str))
        accs = [a.strip() for a in acc.split(",") if a.strip()]
        is_group = idv.startswith("Isomer Group")
        if accs:
            unit = {"unit_id": f"{idv}@row{i}" if is_group else f"CMDB{idv}", "is_group": is_group, "level": str(r["level"]),
                    "purity": r["purity"], "source": r["source"], "accessions": accs,
                    "s4_counts": {k: r[k] for k in ["n_m2h", "n_mh_auto", "n_mh_40", "n_mmh_auto", "n_mmh_40", "n_total"]}}
            for a in accs:
                acc2unit[a] = unit["unit_id"]
        if is_group:
            continue
        if unit is None:
            continue
        comp_rows.append({"s4_row": i, "cyanometdb_id": idv, "name": r["name"], "formula": r["formula"],
                          "smiles": r["smiles"], "inchikey_s4": r["inchikey"], "unit_id": unit["unit_id"],
                          "unit_is_group": unit["is_group"], "level": unit["level"], "purity": unit["purity"],
                          "source": unit["source"], "hash_prev_massbank": idv in hash_ids})
    C = pd.DataFrame(comp_rows)
    summary["s4"].update({
        "n_units_with_accessions": len({v for v in acc2unit.values()}),
        "n_units_groups": int(sum(1 for u in set(acc2unit.values()) if u.startswith("Isomer"))),
        "n_accessions_listed": len(acc2unit),
        "n_compound_rows_incl_group_members": len(C),
        "level_counts_units": vc(s4.loc[s4["accessions"].notna(), "level"].astype(str)),
        "purity_counts_units": vc(s4.loc[s4["accessions"].notna(), "purity"].astype(str).str.lower()),
    })
    R["s4_unit"] = R["accession"].map(acc2unit)
    summary["s4"]["n_tag_records_not_in_s4"] = int(R["s4_unit"].isna().sum())
    summary["s4"]["n_s4_accessions_not_in_tag"] = len(set(acc2unit) - set(R["accession"]))
    summary["s4"]["records_not_in_s4_by_series_adduct"] = vc(R.loc[R["s4_unit"].isna(), "series"] + "|" + R.loc[R["s4_unit"].isna(), "title_adduct"].fillna("NA"))
    # map records not in S4 via stem to a unit that shares the stem
    stem2unit = {}
    for a, u in acc2unit.items():
        stem2unit.setdefault(a[:-2], set()).add(u)
    R["unit_via_stem"] = R["stem"].map(lambda s: "|".join(sorted(stem2unit.get(s, []))) or None)
    # records of other isomer-group member names: stem digits = CyanoMetDB ID of that member (INFERRED convention,
    # checked below against the record title name)
    id2unit = dict(zip(C["cyanometdb_id"].astype(str), C["unit_id"]))
    id2name = dict(zip(C["cyanometdb_id"].astype(str), C["name"].astype(str)))
    R["stem_cmdb_id"] = R["stem"].str[-4:].str.lstrip("0")
    R["unit_via_member_id"] = R["stem_cmdb_id"].map(id2unit)
    R["member_name_via_id"] = R["stem_cmdb_id"].map(id2name)
    R["unit"] = R["s4_unit"].fillna(R["unit_via_stem"]).fillna(R["unit_via_member_id"])
    R["record_listed_in_s4"] = R["s4_unit"].notna()
    nn = R[~R["record_listed_in_s4"]]
    summary["s4"]["n_not_listed_mapped_via_member_id"] = int(nn["unit_via_member_id"].notna().sum())
    summary["s4"]["n_not_listed_title_name_eq_member_name"] = int((nn["title_name"].astype(str).str.strip() == nn["member_name_via_id"].astype(str).str.strip()).sum())
    summary["s4"]["not_listed_units"] = vc(nn["unit"])
    summary["s4"]["n_records_unmapped_after_stem"] = int(R["unit"].isna().sum())
    summary["s4"]["unmapped_stems"] = sorted(R.loc[R["unit"].isna(), "stem"].unique().tolist())

    # ---------------- identity ----------------
    def keys_for(smi):
        k, g = SK.key_and_group(smi)
        return k, g

    C["muru_key"], C["scaffold_group"] = zip(*C["smiles"].map(keys_for))
    C["ik_s4_valid_format"] = C["inchikey_s4"].fillna("").str.fullmatch(r"[A-Z]{14}-[A-Z]{10}-[A-Z]")
    C["ik14_s4"] = C["inchikey_s4"].map(lambda x: SK.first_block(x.upper()) if isinstance(x, str) else None)

    def mh(smi):
        m = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
        if m is None:
            return None, None, None, None
        pm = SK.parent_mol(smi)
        ik = Chem.MolToInchiKey(m)
        return (Descriptors.ExactMolWt(pm) + PROTON, rdMolDescriptors.CalcMolFormula(pm), ik,
                pm.GetNumHeavyAtoms())

    C["mh_theor"], C["formula_rdkit"], C["inchikey_rdkit_raw"], C["heavy_atoms"] = zip(*C["smiles"].map(mh))
    C["formula_match"] = C["formula"].astype(str).str.replace(" ", "") == C["formula_rdkit"].astype(str)
    C["ik14_rdkit_eq_s4"] = C["inchikey_rdkit_raw"].map(SK.first_block) == C["ik14_s4"]

    # record-level inchikey per unit (from MassBank records)
    unit_rec_ik = R.groupby("unit")["inchikey_record"].agg(lambda s: "|".join(sorted(set(x for x in s if isinstance(x, str)))))
    C["inchikeys_in_records"] = C["unit_id"].map(unit_rec_ik)
    C["record_ik14_contains_s4_ik14"] = [
        (isinstance(a, str) and isinstance(b, str) and b in {x.split("-")[0] for x in a.split("|")})
        for a, b in zip(C["inchikeys_in_records"], C["ik14_s4"])]

    # ---------------- exclusion sets ----------------
    S = {
        "msg15_recorded_all": readset("msg15_keys_all.txt"),
        "msg15_parent_all": readset("msg15_parent_keys_all.txt"),
        "msg15_simchallenge_all": readset("msg15_simchallenge_keys_all.txt"),
        "muru_registry_keys": readset("muru_exposure_registry_keys.txt"),
        "muru_registry_scaffolds": readset("muru_exposure_registry_scaffold_groups.txt"),
        "study2_keys": readset("msnlib_study2_population_keys.txt"),
        "study2_scaffolds": readset("msnlib_study2_population_scaffold_groups.txt"),
        "comparator_keys": readset("comparator_common_population_keys.txt"),
        "comparator_scaffolds": readset("comparator_common_population_scaffold_groups.txt"),
        "msg15_scaffolds_all": readset("msg15_scaffold_groups_all.txt"),
        "muru_exposed_union_keys": readset("muru_exposed_union_keys.txt"),
        "msnlib_9lib_keys": readset("msnlib_9lib_keys.txt"),
    }
    pops = {}
    for p in sorted(EX.glob("muru_exposure_registry_population_*_keys.txt")):
        pops[p.name.replace("muru_exposure_registry_population_", "").replace("_keys.txt", "")] = readset(p.name)
    S["muru_exposed_populations_union"] = set().union(*pops.values())
    summary["exclusion_set_sizes"] = {k: len(v) for k, v in S.items()}

    msgp = pd.read_parquet(W / "artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet", columns=["precursor_mz"])
    summary["msg15_precursor_mz_max_reverified"] = float(msgp["precursor_mz"].max())

    def anyhit(keys, s):
        return any(k in s for k in keys if isinstance(k, str))

    C["in_msg15_any_route"] = [anyhit([a, b], S["msg15_recorded_all"]) or anyhit([a, b], S["msg15_parent_all"])
                               for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["in_msg15_simchallenge"] = [anyhit([a, b], S["msg15_simchallenge_all"]) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["in_muru_registry"] = [anyhit([a, b], S["muru_registry_keys"]) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["in_muru_exposed_populations"] = [anyhit([a, b], S["muru_exposed_populations_union"]) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["muru_population_hits"] = ["|".join(sorted(n for n, s in pops.items() if anyhit([a, b], s))) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["in_study2"] = [anyhit([a, b], S["study2_keys"]) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["in_comparator"] = [anyhit([a, b], S["comparator_keys"]) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    C["in_msnlib_9lib"] = [anyhit([a, b], S["msnlib_9lib_keys"]) for a, b in zip(C["muru_key"], C["ik14_s4"])]
    # hidden-inclusion probe: MassSpecGym molecules with the same neutral formula but a different key
    msgj = pd.read_parquet(W / "artifacts/ce_interface_adjudication/massspecgym15_identity_metadata_joined.parquet",
                           columns=["inchikey", "formula", "fold", "simulation_challenge"])
    f2keys = msgj.groupby("formula")["inchikey"].agg(lambda x: sorted(set(x)))
    C["msg15_same_formula_keys"] = C["formula_rdkit"].map(lambda f: "|".join(f2keys.get(f, [])) if isinstance(f, str) else "")
    C["n_msg15_same_formula_other_key"] = [len([k for k in (ks.split("|") if ks else []) if k not in {a, b}])
                                           for ks, a, b in zip(C["msg15_same_formula_keys"], C["muru_key"], C["ik14_s4"])]
    C["scaf_in_muru_registry"] = C["scaffold_group"].isin(S["muru_registry_scaffolds"])
    C["scaf_in_study2"] = C["scaffold_group"].isin(S["study2_scaffolds"])
    C["scaf_in_comparator"] = C["scaffold_group"].isin(S["comparator_scaffolds"])
    C["scaf_in_msg15"] = C["scaffold_group"].isin(S["msg15_scaffolds_all"])

    # ---------------- per-unit spectral availability ([M+H]+) ----------------
    R["is_mh"] = (R["precursor_type"].fillna(R["title_adduct"]) == "[M+H]+")
    R["scan_mode"] = R["title_first_mass"].map(lambda x: "first_mass_40" if x == "40" else "auto")
    R["muru_window_ok"] = (R["mass_range_lo"] <= 40) & (R["mass_range_hi"] >= R["precursor_mz"] + 1)
    per_unit = {}
    for u, g in R[R["is_mh"] & R["record_listed_in_s4"]].groupby("unit"):
        ces_all = sorted(set(g["ce_nce_title"].dropna()))
        g40 = g[g["scan_mode"] == "first_mass_40"]
        gw = g[g["muru_window_ok"] == True]  # noqa: E712
        per_unit[u] = {
            "n_mh_records": len(g),
            "mh_nce_set": ",".join(f"{x:g}" for x in ces_all),
            "n_mh_distinct_nce": len(ces_all),
            "n_mh_distinct_nce_first_mass_40": g40["ce_nce_title"].nunique(),
            "n_mh_distinct_nce_muru_window_ok": gw["ce_nce_title"].nunique(),
            "has_nce20_and_nce60": {20.0, 60.0} <= set(ces_all),
            "has_nce20_and_nce60_muru_window_ok": {20.0, 60.0} <= set(gw["ce_nce_title"].dropna()),
            "has_nce20_and_nce60_first_mass_40": {20.0, 60.0} <= set(g40["ce_nce_title"].dropna()),
            "n_mh_records_with_scan_range": int(g["mass_range"].notna().sum()),
            "mh_precursor_mz_median": float(g["precursor_mz"].median()) if g["precursor_mz"].notna().any() else None,
            "mh_instruments": "|".join(sorted(set(g["instrument"].dropna()))),
            "mh_series": "|".join(sorted(set(g["series"]))),
            "mh_fragmentation": "|".join(sorted(set(g["fragmentation_mode"].dropna()))),
        }
    PU = pd.DataFrame.from_dict(per_unit, orient="index")
    C = C.merge(PU, left_on="unit_id", right_index=True, how="left")
    C["has_mh"] = C["n_mh_records"].fillna(0) > 0
    C["mh_record_vs_theor_da"] = (C["mh_precursor_mz_median"] - C["mh_theor"]).abs()

    # ---------------- tiers ----------------
    base = C["has_mh"] & (C["n_mh_distinct_nce"] >= 3)
    clean = (~C["in_msg15_any_route"]) & (~C["in_muru_registry"]) & (~C["in_study2"]) & (~C["in_comparator"])
    scaf_clean = (~C["scaf_in_muru_registry"]) & (~C["scaf_in_study2"]) & (~C["scaf_in_comparator"])
    single_identity = ~C["unit_is_group"]
    lvl1 = C["level"] == "1"
    lvl12a = C["level"].isin(["1", "2a"])
    in_msg_range = C["mh_theor"] <= MSG_MAX_PRECURSOR
    in_muru_range = C["mh_theor"].between(*MURU_MH_RANGE)
    ref_material = C["purity"].astype(str).str.lower().isin(["reference material", "bioreagent"])

    def tier(mask, label):
        sub = C[mask]
        # a group counts once; keys and scaffolds are compound-level
        return {
            "label": label,
            "n_compound_rows": int(len(sub)),
            "n_units": int(sub["unit_id"].nunique()),
            "n_distinct_muru_keys": int(sub["muru_key"].nunique()),
            "n_distinct_scaffold_groups": int(sub["scaffold_group"].nunique()),
            "n_scaffold_groups_also_in_msg15": int(sub.loc[sub["scaf_in_msg15"], "scaffold_group"].nunique()),
            "n_distinct_scaffold_groups_not_in_msg15": int(sub.loc[~sub["scaf_in_msg15"], "scaffold_group"].nunique()),
            "precursor_mh_theor_quantiles": {q: round(float(sub["mh_theor"].quantile(q)), 2) for q in (0, .1, .5, .9, 1)} if len(sub) else {},
            "n_has_nce20_and_nce60": int(sub["has_nce20_and_nce60"].fillna(False).astype(bool).sum()),
            "n_has_nce20_and_nce60_muru_window_ok_VERIFIED_subset": int(sub["has_nce20_and_nce60_muru_window_ok"].fillna(False).astype(bool).sum()),
            "n_has_nce20_and_nce60_first_mass_40": int(sub["has_nce20_and_nce60_first_mass_40"].fillna(False).astype(bool).sum()),
            "n_ge3nce_first_mass_40": int((sub["n_mh_distinct_nce_first_mass_40"].fillna(0) >= 3).sum()),
            "scaffold_groups_with_first_mass_40_nce20_60": int(sub.loc[sub["has_nce20_and_nce60_first_mass_40"].fillna(False).astype(bool), "scaffold_group"].nunique()),
            "level_counts": vc(sub["level"]),
        }

    T = {}
    T["A_all_mh_ge3nce"] = tier(base, "S4 compound rows with [M+H]+ at >=3 NCE (group members included)")
    T["B_single_identity"] = tier(base & single_identity, "A minus Level-3 isomer-group members")
    T["C_clean_keys"] = tier(base & single_identity & clean, "B, key absent from MSG1.5 (both routes), MURU registry, study-2, comparator")
    T["D_clean_keys_and_scaffolds"] = tier(base & single_identity & clean & scaf_clean, "C, scaffold group absent from MURU registry, study-2 and comparator scaffold lists")
    T["E_D_msg_range"] = tier(base & single_identity & clean & scaf_clean & in_msg_range, "D with [M+H]+ <= 999.396 (MSG 1.5 max)")
    T["F_D_muru_range"] = tier(base & single_identity & clean & scaf_clean & in_muru_range, "D with [M+H]+ in MURU dev range 70-1042.6")
    T["G_E_level1"] = tier(base & single_identity & clean & scaf_clean & in_msg_range & lvl1, "E at confidence Level 1")
    T["H_E_level1_2a"] = tier(base & single_identity & clean & scaf_clean & in_msg_range & lvl12a, "E at Level 1 or 2a")
    T["I_E_refmaterial"] = tier(base & single_identity & clean & scaf_clean & in_msg_range & ref_material, "E recorded from reference material or bioreagent")
    T["J_E_nce20_60_first_mass_40"] = tier(base & single_identity & clean & scaf_clean & in_msg_range & C["has_nce20_and_nce60_first_mass_40"].fillna(False).astype(bool),
                                    "E with NCE20 and NCE60 [M+H]+ spectra in the first-mass-40 scan mode (EC series)")
    T["K_E_scaffold_new_vs_msg15"] = tier(base & single_identity & clean & scaf_clean & in_msg_range & ~C["scaf_in_msg15"], "E whose scaffold group is also absent from MSG 1.5 scaffolds")
    summary["tiers"] = T

    # overlap tallies
    summary["overlap"] = {
        "compound_rows_with_mh": int(C["has_mh"].sum()),
        "in_msg15_any_route": C.loc[C["has_mh"], ["cyanometdb_id", "name", "level", "mh_theor", "hash_prev_massbank", "in_msg15_simchallenge"]].loc[C["in_msg15_any_route"]].to_dict("records"),
        "in_muru_registry": C.loc[C["in_muru_registry"], ["cyanometdb_id", "name", "muru_population_hits"]].to_dict("records"),
        "in_study2": C.loc[C["in_study2"], ["cyanometdb_id", "name"]].to_dict("records"),
        "in_comparator": C.loc[C["in_comparator"], ["cyanometdb_id", "name"]].to_dict("records"),
        "scaf_in_muru_registry": C.loc[C["scaf_in_muru_registry"], ["cyanometdb_id", "name", "scaffold_group"]].to_dict("records"),
        "scaf_in_study2": int(C["scaf_in_study2"].sum()),
        "scaf_in_comparator": int(C["scaf_in_comparator"].sum()),
        "in_msnlib_9lib": C.loc[C["in_msnlib_9lib"], ["cyanometdb_id", "name"]].to_dict("records"),
        "same_formula_other_key_in_msg15": C.loc[C["n_msg15_same_formula_other_key"] > 0, ["cyanometdb_id", "name", "formula_rdkit", "level", "in_msg15_any_route", "msg15_same_formula_keys"]].to_dict("records"),
        "hash_prev_massbank_rows": C.loc[C["hash_prev_massbank"], ["cyanometdb_id", "name", "in_msg15_any_route", "mh_theor"]].to_dict("records"),
    }
    summary["identity_quality"] = {
        "n_compound_rows": len(C),
        "n_smiles_missing": int(C["smiles"].isna().sum()),
        "n_muru_key_unformable": int(C["muru_key"].isna().sum()),
        "n_s4_inchikey_bad_format": int((~C["ik_s4_valid_format"]).sum()),
        "s4_inchikey_bad_format_examples": C.loc[~C["ik_s4_valid_format"], ["cyanometdb_id", "name", "inchikey_s4"]].to_dict("records"),
        "n_rdkit_ik14_ne_s4_ik14": int((~C["ik14_rdkit_eq_s4"]).sum()),
        "rdkit_ik14_ne_s4_examples": C.loc[~C["ik14_rdkit_eq_s4"], ["cyanometdb_id", "name", "inchikey_s4", "inchikey_rdkit_raw"]].head(20).to_dict("records"),
        "n_formula_mismatch": int((~C["formula_match"]).sum()),
        "formula_mismatch_examples": C.loc[~C["formula_match"], ["cyanometdb_id", "name", "formula", "formula_rdkit"]].head(20).to_dict("records"),
        "n_record_ik14_not_matching_s4": int((C["has_mh"] & ~pd.Series(C["record_ik14_contains_s4_ik14"], index=C.index)).sum()),
        "record_ik_mismatch_examples": C.loc[C["has_mh"] & ~pd.Series(C["record_ik14_contains_s4_ik14"], index=C.index), ["cyanometdb_id", "name", "inchikey_s4", "inchikeys_in_records"]].head(20).to_dict("records"),
        "mh_record_minus_theor_abs_da_quantiles": {q: float(C["mh_record_vs_theor_da"].quantile(q)) for q in (.5, .9, .99, 1)} if C["mh_record_vs_theor_da"].notna().any() else {},
        "n_mh_record_vs_theor_gt_0p01": int((C["mh_record_vs_theor_da"] > 0.01).sum()),
        "mh_record_vs_theor_gt_0p01_examples": C.loc[C["mh_record_vs_theor_da"] > 0.01, ["cyanometdb_id", "name", "mh_theor", "mh_precursor_mz_median"]].head(20).to_dict("records"),
        "heavy_atoms_quantiles": {q: float(C["heavy_atoms"].quantile(q)) for q in (0, .5, .9, 1)},
        "n_heavy_atoms_gt_160": int((C["heavy_atoms"] > 160).sum()),
        "n_mh_theor_gt_glacier_upper_1500": int((C["mh_theor"] > GLACIER_UPPER_LIMIT).sum()),
    }

    # structural diversity for tier E (and G)
    def diversity(mask):
        sub = C[mask].drop_duplicates("muru_key")
        mols = [SK.parent_mol(s) for s in sub["smiles"]]
        fps = [AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048) for m in mols]
        n = len(fps)
        dists = []
        for i in range(1, n):
            sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
            dists.extend(1 - x for x in sims)
        out = {"n": n}
        for thr in (0.4, 0.6):
            cl = Butina.ClusterData(dists, n, thr, isDistData=True) if n > 1 else [(0,)] * n
            out[f"butina_clusters_tanimoto_ge_{1-thr:.1f}"] = len(cl)
        generic = set()
        for m in mols:
            mm = Chem.Mol(m)
            Chem.RemoveStereochemistry(mm)
            try:
                g = MurckoScaffold.MakeScaffoldGeneric(MurckoScaffold.GetScaffoldForMol(mm))
                generic.add(Chem.MolToSmiles(g))
            except Exception:
                generic.add("ERR")
        out["n_generic_frameworks"] = len(generic)
        fam = sub["name"].astype(str).str.replace(r"\[.*?\]", "", regex=True).str.strip().str.split().str[0].str.replace(r"[-0-9]+$", "", regex=True).str.lower()
        out["name_family_counts_INFERRED"] = {k: int(v) for k, v in fam.value_counts().items()}
        out["n_name_families_INFERRED"] = int(fam.nunique())
        out["n_macrocycle_ring_ge12"] = int(sum(any(len(r) >= 12 for r in m.GetRingInfo().AtomRings()) for m in mols))
        return out

    # nearest MassSpecGym 1.5 neighbour (Morgan r2 2048 Tanimoto on MURU parent molecules), all compound rows
    msg_smi = pd.read_parquet(W / "artifacts/ce_interface_adjudication/massspecgym15_identity_metadata_joined.parquet",
                              columns=["inchikey", "smiles"]).drop_duplicates("inchikey")
    msg_fps = []
    for smi in msg_smi["smiles"]:
        m = SK.parent_mol(smi)
        if m is not None:
            msg_fps.append(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048))
    nn = []
    for smi in C["smiles"]:
        m = SK.parent_mol(smi) if isinstance(smi, str) else None
        if m is None:
            nn.append(None)
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048)
        nn.append(max(DataStructs.BulkTanimotoSimilarity(fp, msg_fps)))
    C["msg15_nn_tanimoto"] = nn
    summary["msg15_nn_tanimoto"] = {"n_msg_molecules_fp": len(msg_fps)}
    for tname, mask in [("B", base & single_identity), ("E", base & single_identity & clean & scaf_clean & in_msg_range),
                        ("G", base & single_identity & clean & scaf_clean & in_msg_range & lvl1)]:
        v = C.loc[mask, "msg15_nn_tanimoto"].dropna()
        summary["msg15_nn_tanimoto"][tname] = {"n": int(len(v)), **{f"q{int(q*100)}": round(float(v.quantile(q)), 3) for q in (0, .1, .5, .9, 1)},
                                               "n_ge_0.7": int((v >= 0.7).sum()), "n_ge_0.5": int((v >= 0.5).sum())}

    summary["diversity"] = {
        "E": diversity(base & single_identity & clean & scaf_clean & in_msg_range),
        "G": diversity(base & single_identity & clean & scaf_clean & in_msg_range & lvl1),
        "D": diversity(base & single_identity & clean & scaf_clean),
    }

    # CE ladders
    mhC = C[C["has_mh"]].drop_duplicates("unit_id")
    summary["ce_ladders_per_unit_mh"] = vc(mhC["mh_nce_set"])
    summary["n_units_mh"] = int(len(mhC))
    summary["n_units_mh_ge3nce"] = int((mhC["n_mh_distinct_nce"] >= 3).sum())

    R.to_csv(OUT / "records.csv", index=False)
    C.to_csv(OUT / "compounds.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str)[:20000])


if __name__ == "__main__":
    main()
