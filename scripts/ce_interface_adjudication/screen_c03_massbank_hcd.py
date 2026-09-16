"""S3 screen C03: MassBank 2023.11 in-training Orbitrap HCD contributors. Metadata-only overlap and feasibility screen.

Inputs (all metadata; produced by screen_c03_massbank_hcd_fetch.py and screen_c03_massbank_hcd_codesearch.py, plus
the study's exclusion inventory built by P5 and the MassSpecGym 1.5 identity/metadata parquets built by P3/P4):
  downloads/github_trees/tree_{2023.11,dev}_<dir>.json      accessions and blob sha at tag 2023.11 and dev HEAD
  downloads/github_commits/commits_since_2023.11_<dir>.json commit messages touching each directory since the tag
  downloads/massbank_api/search_<dir>__<instrument_type>__<ion_mode>.json  per-accession instrument type, ion mode
  downloads/massbank_export_jsonld/export_metadata_jsonld.jsonl.gz  per-accession title and compound identity
  downloads/github_codesearch/codesearch_ac_lines.jsonl     AC$ lines (HEAD) for a sample of records per directory
No model output, no spectrum and no MURU measurement is read.

Outputs (OUT): records.parquet, compounds.parquet, msg_linkage_records.parquet, summary.json, plus CSV tables.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "screen/c03_massbank_hcd"
import os as _os
WRITE_OUT = Path(_os.environ["C03_DEBUG_OUT"]) if _os.environ.get("C03_DEBUG_OUT") else OUT
DL = OUT / "downloads"
EXC = ADJ / "exclusion"
sys.path.insert(0, str(ROOT / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402
from rdkit import rdBase  # noqa: E402

CONTRIBUTORS = ["AAFC", "Eawag", "Eawag_Additional_Specs", "HBM4EU", "NaToxAq", "UFZ"]
PROTON = 1.007276466812
ORBI_TYPES = {"LC-ESI-ITFT", "LC-ESI-QFT", "ESI-ITFT", "ESI-QFT"}  # ESI Orbitrap-class MassBank instrument types
MSG_ORBI_MAP = {"LC-ESI-ITFT", "LC-ESI-QFT", "ESI-ITFT", "ESI-QFT", "LC-APCI-ITFT", "APCI-ITFT"}


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_keys(name: str) -> set[str]:
    return {l.strip() for l in (EXC / name).read_text().splitlines() if l.strip()}


def load_trees():
    rows = []
    for c in CONTRIBUTORS:
        a = {e["path"][:-4]: e["sha"] for e in json.loads((DL / f"github_trees/tree_2023.11_{c}.json").read_text())["tree"]
             if e["type"] == "blob" and e["path"].endswith(".txt")}
        b = {e["path"][:-4]: e["sha"] for e in json.loads((DL / f"github_trees/tree_dev_{c}.json").read_text())["tree"]
             if e["type"] == "blob" and e["path"].endswith(".txt")}
        for acc, sha in a.items():
            rows.append({"accession": acc, "dir": c, "blob_2023_11": sha,
                         "dev_status": "same_blob" if b.get(acc) == sha else ("changed_blob" if acc in b else "removed_at_dev")})
        added = collections.Counter(re.sub(r"\d+(_\d+)?$", "", acc) for acc in b if acc not in a)
        yield_added = {"dir": c, "n_2023_11": len(a), "n_dev": len(b), "n_added_after_2023_11": sum(added.values()),
                       "added_prefixes": dict(added)}
        rows_added.append(yield_added)
    return pd.DataFrame(rows)


rows_added: list[dict] = []


def load_api():
    m = {}
    for p in sorted((DL / "massbank_api").glob("search_*.json")):
        _, rest = p.stem.split("_", 1)
        c, it, mode = rest.split("__")
        for x in json.loads(p.read_text()).get("data") or []:
            if x["accession"] in m:
                raise RuntimeError(f"duplicate accession across partitions {x['accession']}")
            m[x["accession"]] = {"api_dir": c, "api_instrument_type": it, "api_ion_mode": mode}
    return pd.DataFrame.from_dict(m, orient="index").rename_axis("accession").reset_index()


TITLE_RE = re.compile(r"^(?P<name>.*?);\s*(?P<itype>[A-Z]+(?:-[A-Za-z]+)+);\s*(?P<mstype>MS\d?);\s*(?P<rest>.*)$")


def parse_title(t: str) -> dict:
    out = {"title_name": None, "title_instrument_type": None, "title_ms_type": None, "title_ce_text": None,
           "title_resolution": None, "title_adduct": None, "title_parse": "fail"}
    if not isinstance(t, str):
        return out
    m = TITLE_RE.match(t)
    if not m:
        return out
    out["title_name"], out["title_instrument_type"], out["title_ms_type"] = m["name"], m["itype"], m["mstype"]
    parts = [s.strip() for s in m["rest"].split(";")]
    for s in parts:
        if s.startswith("CE:"):
            out["title_ce_text"] = s[3:].strip()
        elif s.startswith("R="):
            out["title_resolution"] = s[2:].strip()
        elif s.startswith("[") or s.startswith("M"):
            out["title_adduct"] = s
    out["title_parse"] = "ok"
    return out


def first_number(s):
    if not isinstance(s, str):
        return None
    m = re.search(r"\d+(\.\d+)?", s)
    return float(m.group(0)) if m else None


def load_jsonld():
    rows = []
    import os
    src = DL / "massbank_export_jsonld/export_metadata_jsonld.jsonl.gz"
    opener = (lambda: gzip.open(src, "rt"))
    if os.environ.get("C03_DEBUG_PARTIAL"):
        opener = (lambda: open(DL / "massbank_export_jsonld/export_metadata_jsonld.partial.jsonl"))
    with opener() as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = {"accession": r["accession"], "http_status": r["status"]}
            if r["body"]:
                ds = next(x for x in r["body"] if x.get("@type") == "Dataset")
                cs = next(x for x in r["body"] if x.get("@type") == "ChemicalSubstance")
                me = (cs.get("hasBioChemEntityPart") or [{}])[0]
                d.update({"title": ds.get("name"), "license": ds.get("license"), "date_published": ds.get("datePublished"),
                          "citation": ds.get("citation"), "compound_name": cs.get("name"), "formula": me.get("molecularFormula"),
                          "mono_mass": me.get("monoisotopicMolecularWeight"), "smiles": me.get("smiles"),
                          "inchi": me.get("inChI"), "inchikey": me.get("inChIKey"),
                          "ms_type_desc": re.search(r"contains the (\S+) mass spectrum", ds.get("description") or "").group(1)
                          if re.search(r"contains the (\S+) mass spectrum", ds.get("description") or "") else None})
            rows.append(d)
    return pd.DataFrame(rows)


def main():
    WRITE_OUT.mkdir(parents=True, exist_ok=True)
    summary: dict = {"rdkit": rdBase.rdkitVersion, "inputs": {}}

    trees = load_trees()
    api = load_api()
    jl = load_jsonld()
    rec = trees.merge(api, on="accession", how="left").merge(jl, on="accession", how="left")
    tp = rec["title"].map(parse_title).apply(pd.Series)
    rec = pd.concat([rec, tp], axis=1)
    rec["nce_first_number"] = rec["title_ce_text"].map(first_number)
    rec["title_ce_has_percent"] = rec["title_ce_text"].fillna("").str.contains("%")
    rec["title_ce_n_numbers"] = rec["title_ce_text"].fillna("").map(lambda s: len(re.findall(r"\d+(?:\.\d+)?", s)))
    rec["recorded_key14"] = rec["inchikey"].map(SK.first_block)
    kg = rec["smiles"].map(SK.key_and_group)
    rec["parent_key"] = kg.map(lambda x: x[0])
    rec["scaffold_group"] = kg.map(lambda x: x[1])
    rec["mono_mass"] = pd.to_numeric(rec["mono_mass"], errors="coerce")
    rec["mz_MH_theoretical"] = rec["mono_mass"] + PROTON
    rec["is_positive"] = rec["api_ion_mode"].eq("POSITIVE")
    rec["is_esi_orbitrap"] = rec["api_instrument_type"].isin(ORBI_TYPES)
    rec["is_MH"] = rec["title_adduct"].eq("[M+H]+")
    rec["design_row_any_structure"] = rec["is_positive"] & rec["is_esi_orbitrap"] & rec["is_MH"] & rec["api_instrument_type"].notna()
    rec["has_structure"] = rec["parent_key"].notna()
    # design row = positive-mode ESI Orbitrap-class [M+H]+ record WITH a usable structure (records without a parseable
    # structure, e.g. Eawag_Additional_Specs unknown features and HBM4EU "(TENTATIVE)" metabolites, cannot be keyed)
    rec["design_row"] = rec["design_row_any_structure"] & rec["has_structure"]

    # ---------------- exclusion sets ----------------
    S = {
        "msg15_all_recorded": read_keys("msg15_keys_all.txt"),
        "msg15_all_parent": read_keys("msg15_parent_keys_all.txt"),
        "msg15_train_recorded": read_keys("msg15_keys_train.txt"),
        "msg15_val_recorded": read_keys("msg15_keys_val.txt"),
        "msg15_test_recorded": read_keys("msg15_keys_test.txt"),
        "msg15_simchallenge_all": read_keys("msg15_simchallenge_keys_all.txt"),
        "muru_v2_development_population": read_keys("muru_exposure_registry_population_V2-DEVELOPMENT-POPULATION_keys.txt"),
        "muru_exposed_populations_union": set().union(*[read_keys(p.name) for p in EXC.glob("muru_exposure_registry_population_*_keys.txt")]),
        "muru_exposure_registry_full": read_keys("muru_exposure_registry_keys.txt"),
        "pr7_msnlib_study2_population": read_keys("msnlib_study2_population_keys.txt"),
        "comparator_common_population": read_keys("comparator_common_population_keys.txt"),
    }
    G = {
        "msg15_scaffold_groups_all": read_keys("msg15_scaffold_groups_all.txt"),
        "muru_exposure_registry_scaffold_groups": read_keys("muru_exposure_registry_scaffold_groups.txt"),
        "pr7_scaffold_groups": read_keys("msnlib_study2_population_scaffold_groups.txt"),
        "comparator_scaffold_groups": read_keys("comparator_common_population_scaffold_groups.txt"),
    }
    summary["exclusion_set_sizes"] = {k: len(v) for k, v in S.items()} | {k: len(v) for k, v in G.items()}
    summary["inputs"]["exclusion_manifest_sha256"] = sha_file(EXC / "exclusion_manifest.json")

    def in_set(keys_rec, keys_par, s):
        return keys_rec.isin(s) | keys_par.isin(s)

    for k, s in S.items():
        rec[f"in_{k}"] = in_set(rec["recorded_key14"], rec["parent_key"], s)
    rec["in_msg15_any"] = rec["in_msg15_all_recorded"] | rec["in_msg15_all_parent"]
    rec["excluded_any_key"] = rec[["in_msg15_any", "in_muru_exposure_registry_full", "in_pr7_msnlib_study2_population",
                                   "in_comparator_common_population"]].any(axis=1)
    rec["excluded_scaffold"] = rec["scaffold_group"].isin(set().union(*G.values()))

    # ---------------- compound table ----------------
    rec["compound_id"] = rec["parent_key"].fillna("NOKEY:" + rec["recorded_key14"].fillna(rec["accession"]))

    def comp_summary(df):
        g = df.groupby("compound_id")
        c = g.agg(dirs=("dir", lambda x: ";".join(sorted(set(x)))), n_records=("accession", "size"),
                  recorded_key14=("recorded_key14", "first"), parent_key=("parent_key", "first"),
                  scaffold_group=("scaffold_group", "first"), smiles=("smiles", "first"),
                  n_distinct_nce=("nce_first_number", lambda x: x.dropna().nunique()),
                  nce_values=("nce_first_number", lambda x: ";".join(f"{v:g}" for v in sorted(x.dropna().unique()))))
        for k in S:
            c[f"in_{k}"] = g[f"in_{k}"].any()
        c["in_msg15_any"] = g["in_msg15_any"].any()
        c["excluded_any_key"] = g["excluded_any_key"].any()
        c["excluded_scaffold"] = g["excluded_scaffold"].any()
        return c.reset_index()

    comps_all = comp_summary(rec[rec["http_status"].eq(200)])
    comps_design = comp_summary(rec[rec["design_row"]])
    comps_all.to_parquet(WRITE_OUT / "compounds_all_records.parquet", index=False)
    comps_design.to_parquet(WRITE_OUT / "compounds_design_rows.parquet", index=False)

    # ---------------- per-directory tables ----------------
    per_dir = []
    for c in CONTRIBUTORS + ["ALL"]:
        r = rec if c == "ALL" else rec[rec["dir"] == c]
        d = {"dir": c, "records_2023_11": len(r),
             "records_blob_same_at_dev": int(r["dev_status"].eq("same_blob").sum()),
             "records_blob_changed_at_dev": int(r["dev_status"].eq("changed_blob").sum()),
             "records_removed_at_dev": int(r["dev_status"].eq("removed_at_dev").sum()),
             "records_in_current_api": int(r["api_ion_mode"].notna().sum()),
             "records_jsonld_200": int(r["http_status"].eq(200).sum()),
             "records_positive": int(r["is_positive"].sum()),
             "records_instrument_types": r["api_instrument_type"].value_counts(dropna=False).to_dict(),
             "records_adducts_positive": r.loc[r["is_positive"], "title_adduct"].value_counts(dropna=False).head(12).to_dict(),
             "records_design_rows_any_structure": int(r["design_row_any_structure"].sum()),
             "records_design_rows_without_structure": int((r["design_row_any_structure"] & ~r["has_structure"]).sum()),
             "records_design_rows": int(r["design_row"].sum()),
             "records_title_ce_percent": int(r["title_ce_has_percent"].sum()),
             "records_title_ce_multi_number": int((r["title_ce_n_numbers"] > 1).sum()),
             "licenses": r["license"].value_counts(dropna=False).to_dict(),
             "date_published_range": [r["date_published"].min(), r["date_published"].max()]}
        cd = comps_design if c == "ALL" else comp_summary(r[r["design_row"]]) if r["design_row"].any() else comps_design.iloc[0:0]
        ca = comps_all if c == "ALL" else comp_summary(r[r["http_status"].eq(200)])
        d["compounds_all_records"] = int(len(ca))
        d["compounds_design"] = int(len(cd))
        for k in list(S) + ["in_msg15_any"]:
            kk = k if k.startswith("in_") else f"in_{k}"
            d[f"design_compounds_{kk}"] = int(cd[kk].sum()) if len(cd) else 0
        rem = cd[~cd["excluded_any_key"]] if len(cd) else cd
        d["design_compounds_after_key_exclusion"] = int(len(rem))
        d["design_scaffold_groups_after_key_exclusion"] = int(rem["scaffold_group"].nunique()) if len(rem) else 0
        rem2 = rem[~rem["excluded_scaffold"]] if len(rem) else rem
        d["design_compounds_after_key_and_scaffold_exclusion"] = int(len(rem2))
        d["design_scaffold_groups_after_key_and_scaffold_exclusion"] = int(rem2["scaffold_group"].nunique()) if len(rem2) else 0
        d["design_nce_values_per_compound_median"] = float(cd["n_distinct_nce"].median()) if len(cd) else None
        d["design_nce_value_set"] = sorted({float(v) for v in r.loc[r["design_row"], "nce_first_number"].dropna()})
        ca_rem = ca[~ca["excluded_any_key"]]
        d["all_compounds_after_key_exclusion"] = int(len(ca_rem))
        per_dir.append(d)
    summary["per_dir"] = per_dir
    summary["added_after_2023_11"] = rows_added
    pd.DataFrame(per_dir).to_csv(WRITE_OUT / "per_dir_summary.csv", index=False)

    # ---------------- MassSpecGym 1.5 row linkage (CE arm test) ----------------
    msg = pd.read_parquet(ADJ / "massspecgym15_identity_metadata_joined.parquet",
                          columns=["identifier", "inchikey", "fold", "simulation_challenge", "adduct", "instrument_type",
                                   "collision_energy", "precursor_mz"])
    attr = pd.read_parquet(ADJ / "p3_msg15_row_source_attribution.parquet", columns=["identifier", "block", "source_label"])
    msg = msg.merge(attr, on="identifier", how="left")
    summary["inputs"]["msg_joined_sha256"] = sha_file(ADJ / "massspecgym15_identity_metadata_joined.parquet")
    summary["inputs"]["p3_attribution_sha256"] = sha_file(ADJ / "p3_msg15_row_source_attribution.parquet")
    mo = msg[msg["instrument_type"].eq("Orbitrap") & msg["collision_energy"].notna()].copy()
    by_key = {k: g for k, g in mo.groupby("inchikey")}

    link = []
    cand = rec[rec["is_positive"] & rec["api_instrument_type"].isin(MSG_ORBI_MAP) & rec["recorded_key14"].notna()
               & rec["nce_first_number"].notna() & rec["title_adduct"].isin(["[M+H]+", "[M+Na]+"])]
    for r in cand.itertuples(index=False):
        g = by_key.get(r.recorded_key14)
        nce = r.nce_first_number
        out = {"accession": r.accession, "dir": r.dir, "recorded_key14": r.recorded_key14, "title_adduct": r.title_adduct,
               "nce": nce, "title_ce_text": r.title_ce_text, "mz_theor": None,
               "n_msg_rows_key": 0, "n_msg_rows_prec": 0, "n_conv_match": 0, "n_raw_match": 0, "conv_ids": "", "raw_ids": "",
               "conv_sim_rows": 0, "raw_sim_rows": 0}
        if g is None:
            link.append(out)
            continue
        ion_mass = r.mono_mass + (PROTON if r.title_adduct == "[M+H]+" else 22.989218)
        out["mz_theor"] = ion_mass
        out["n_msg_rows_key"] = len(g)
        gg = g[(g["adduct"] == r.title_adduct) & ((g["precursor_mz"] - ion_mass).abs() <= 0.02)]
        out["n_msg_rows_prec"] = len(gg)
        conv = gg[(gg["collision_energy"] - nce * gg["precursor_mz"] / 500.0).abs() <= 1e-6 * np.maximum(1.0, gg["collision_energy"])]
        raw = gg[(gg["collision_energy"] - nce).abs() <= 1e-9]
        # rows with precursor_mz == 500 would match both; they are counted in both and flagged via overlap
        out["n_conv_match"], out["n_raw_match"] = len(conv), len(raw)
        out["conv_ids"], out["raw_ids"] = ";".join(conv["identifier"]), ";".join(raw["identifier"])
        out["conv_sim_rows"], out["raw_sim_rows"] = int(conv["simulation_challenge"].sum()), int(raw["simulation_challenge"].sum())
        out["conv_blocks"] = ";".join(sorted(set(conv["source_label"].astype(str))))
        out["raw_blocks"] = ";".join(sorted(set(raw["source_label"].astype(str))))
        link.append(out)
    lk = pd.DataFrame(link)
    lk["arm"] = np.select([(lk.n_conv_match > 0) & (lk.n_raw_match == 0), (lk.n_raw_match > 0) & (lk.n_conv_match == 0),
                           (lk.n_raw_match > 0) & (lk.n_conv_match > 0), lk.n_msg_rows_key == 0],
                          ["percent_converted_only", "raw_only", "both_arms_present", "key_not_in_msg_orbitrap_ce_rows"],
                          default="key_present_no_ce_match")
    lk.to_parquet(WRITE_OUT / "msg_linkage_records.parquet", index=False)
    arm_tab = lk.groupby(["dir", "title_adduct", "arm"]).size().unstack(fill_value=0)
    arm_tab.to_csv(WRITE_OUT / "msg_linkage_arm_by_dir.csv")
    summary["msg_linkage_arm_by_dir"] = {f"{a}|{b}": v for (a, b), v in arm_tab.to_dict(orient="index").items()}
    # distinct MSG rows linked per dir and arm
    lr = {}
    for c in CONTRIBUTORS:
        s = lk[lk.dir == c]
        conv_ids = {i for x in s.loc[s.arm == "percent_converted_only", "conv_ids"] for i in x.split(";") if i}
        raw_ids = {i for x in s.loc[s.arm == "raw_only", "raw_ids"] for i in x.split(";") if i}
        sub_c = msg[msg.identifier.isin(conv_ids)]
        sub_r = msg[msg.identifier.isin(raw_ids)]
        lr[c] = {"msg_rows_linked_converted_only": len(conv_ids), "msg_rows_linked_raw_only": len(raw_ids),
                 "converted_sim_rows": int(sub_c.simulation_challenge.sum()), "raw_sim_rows": int(sub_r.simulation_challenge.sum()),
                 "converted_folds": sub_c.fold.value_counts().to_dict(), "raw_folds": sub_r.fold.value_counts().to_dict(),
                 "converted_ce_quantiles_eV_like": sub_c.collision_energy.quantile([0.05, 0.5, 0.95]).round(3).tolist() if len(sub_c) else None,
                 "raw_ce_values_top": sub_r.collision_energy.value_counts().head(12).to_dict(),
                 "converted_source_labels": sub_c.source_label.value_counts().to_dict(),
                 "raw_source_labels": sub_r.source_label.value_counts().to_dict()}
    summary["msg_rows_linked_per_dir"] = lr
    dsh = {}
    for c in CONTRIBUTORS:
        s_ = lk[(lk.dir == c) & (lk.title_adduct == "[M+H]+")]
        vc = s_["arm"].value_counts().to_dict()
        conv, raw = vc.get("percent_converted_only", 0), vc.get("raw_only", 0)
        dsh[c] = {"MH_records_tested": int(len(s_)), "arm_counts": vc,
                  "converted_share_of_resolvable": round(conv / (conv + raw), 4) if conv + raw else None}
    summary["msg_arm_share_MH"] = dsh
    # title "%" (record title CE text, current export) against the arm observed in MassSpecGym 1.5, per series
    tx = lk.merge(rec[["accession", "title_ce_has_percent", "api_instrument_type"]], on="accession", how="left")
    tx = tx[tx["title_adduct"] == "[M+H]+"].copy()
    tx["series"] = tx["accession"].str.replace(r"^MSBNK-", "", regex=True).str.replace(r"(\D+\d).*$", r"\1", regex=True)
    ct = tx.groupby(["dir", "series", "api_instrument_type", "title_ce_has_percent", "arm"]).size().unstack(fill_value=0)
    ct.to_csv(WRITE_OUT / "msg_arm_by_series_instrument_titlepercent.csv")
    ct2 = tx.groupby(["dir", "title_ce_has_percent", "arm"]).size().unstack(fill_value=0)
    ct2.to_csv(WRITE_OUT / "msg_arm_by_dir_titlepercent.csv")
    rawnce = tx[tx["arm"] == "raw_only"].groupby(["dir", "nce"]).size().rename("n").reset_index()
    rawnce.to_csv(WRITE_OUT / "msg_raw_arm_nce_values_by_dir.csv", index=False)
    # union over the six directories of MSG 1.5 rows linked under exactly one arm (a row can be linked from two
    # directories that share a compound and an NCE; the union counts it once; rows linked under both arms are reported)
    conv_all = {i for x in lk.loc[lk.arm == "percent_converted_only", "conv_ids"] for i in x.split(";") if i}
    raw_all = {i for x in lk.loc[lk.arm == "raw_only", "raw_ids"] for i in x.split(";") if i}
    both = conv_all & raw_all
    mm = msg.set_index("identifier")
    summary["msg_rows_linked_union"] = {
        "converted_only_rows": len(conv_all - both), "raw_only_rows": len(raw_all - both), "rows_in_both_sets": len(both),
        "converted_sim_rows": int(mm.loc[sorted(conv_all - both), "simulation_challenge"].sum()),
        "raw_sim_rows": int(mm.loc[sorted(raw_all - both), "simulation_challenge"].sum()),
        "converted_sim_rows_by_fold": mm.loc[sorted(conv_all - both)].query("simulation_challenge").fold.value_counts().to_dict(),
        "raw_sim_rows_by_fold": mm.loc[sorted(raw_all - both)].query("simulation_challenge").fold.value_counts().to_dict(),
        "converted_sim_rows_by_p3_source_label": mm.loc[sorted(conv_all - both)].query("simulation_challenge").source_label.value_counts().to_dict(),
        "raw_sim_rows_by_p3_source_label": mm.loc[sorted(raw_all - both)].query("simulation_challenge").source_label.value_counts().to_dict(),
        "context_p3_massbank_or_mona_orbitrap_sim_rows": {"converted_noninteger": 23894, "raw_integer": 18380}}
    pr7 = rec[rec["design_row"] & rec["in_pr7_msnlib_study2_population"]][["dir", "accession", "compound_name", "parent_key"]]
    summary["design_records_in_pr7_population"] = pr7.groupby(["dir", "parent_key", "compound_name"]).size().rename("n").reset_index().to_dict(orient="records")
    # NCE 20 and 60 availability per design compound (MURU external deployment uses fixed NCE 20 and 60)
    dr = rec[rec["design_row"]]
    has = dr.groupby(["dir", "compound_id"])["nce_first_number"].agg(lambda x: (20.0 in set(x), 60.0 in set(x)))
    h = has.map(lambda t: "both" if all(t) else ("20_only" if t[0] else ("60_only" if t[1] else "neither"))).rename("nce20_60").reset_index()
    summary["design_compounds_nce20_nce60"] = h.groupby("dir")["nce20_60"].value_counts().unstack(fill_value=0).to_dict(orient="index")

    # ---------------- title CE text forms per dir ----------------
    forms = rec.assign(ce_form=rec["title_ce_text"].fillna("<none>").str.replace(r"\d+(\.\d+)?", "N", regex=True))
    ft = forms.groupby(["dir", "ce_form"]).size().rename("n").reset_index().sort_values(["dir", "n"], ascending=[True, False])
    ft.to_csv(WRITE_OUT / "title_ce_forms_by_dir.csv", index=False)
    summary["title_ce_forms_by_dir"] = {c: ft[ft.dir == c].head(10).set_index("ce_form")["n"].to_dict() for c in CONTRIBUTORS}

    # ---------------- code-search AC$ lines (HEAD) ----------------
    cs_path = DL / "github_codesearch/codesearch_ac_lines.jsonl"
    if cs_path.exists():
        cs = [json.loads(l) for l in cs_path.read_text().splitlines() if l.strip()]
        blob23 = dict(zip(rec["accession"], rec["blob_2023_11"]))
        csum = {}
        for c in CONTRIBUTORS:
            items = [x for x in cs if x["contributor_dir"] == c]
            seen = {}
            for x in items:
                seen[x["path"]] = x
            ce_forms = collections.Counter()
            frag = collections.Counter()
            instr = collections.Counter()
            same = 0
            for pth, x in seen.items():
                acc = Path(pth).stem
                if blob23.get(acc) == x["blob_sha"]:
                    same += 1
                for ln in x["kept_lines"]:
                    if ln.startswith("AC$MASS_SPECTROMETRY: COLLISION_ENERGY"):
                        ce_forms[re.sub(r"\d+(\.\d+)?", "N", ln.split("COLLISION_ENERGY", 1)[1].strip())] += 1
                    elif ln.startswith("AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE"):
                        frag[ln.split("FRAGMENTATION_MODE", 1)[1].strip()] += 1
                    elif ln.startswith("AC$INSTRUMENT:"):
                        instr[ln.split(":", 1)[1].strip()] += 1
            csum[c] = {"distinct_files_sampled": len(seen), "files_blob_identical_to_2023_11": same,
                       "ce_string_forms": dict(ce_forms.most_common(12)), "fragmentation_mode": dict(frag),
                       "instrument": dict(instr.most_common(8))}
        summary["codesearch_head_sample"] = csum
        # cross-check: HEAD AC$ CE string form vs the parser arm observed in MassSpecGym 1.5 (built from 2023.11)
        cs_rows = []
        for c in CONTRIBUTORS:
            seen = {}
            for x in cs:
                if x["contributor_dir"] == c:
                    seen[x["path"]] = x
            for pth, x in seen.items():
                ce_line = next((ln for ln in x["kept_lines"] if ln.startswith("AC$MASS_SPECTROMETRY: COLLISION_ENERGY")), None)
                fm_line = next((ln for ln in x["kept_lines"] if ln.startswith("AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE")), None)
                cs_rows.append({"accession": Path(pth).stem, "cs_dir": c, "cs_blob_sha": x["blob_sha"],
                                "head_ce_string": ce_line.split("COLLISION_ENERGY", 1)[1].strip() if ce_line else None,
                                "head_frag_mode": fm_line.split("FRAGMENTATION_MODE", 1)[1].strip() if fm_line else None})
        csdf = pd.DataFrame(cs_rows)
        csdf["head_ce_has_percent"] = csdf["head_ce_string"].fillna("").str.contains("%")
        csdf["head_ce_form"] = csdf["head_ce_string"].fillna("<none>").str.replace(r"\d+(\.\d+)?", "N", regex=True)
        csdf = csdf.merge(rec[["accession", "blob_2023_11", "title", "title_ce_text", "title_adduct", "api_instrument_type",
                               "api_ion_mode", "design_row"]], on="accession", how="left")
        csdf["in_2023_11_tree"] = csdf["blob_2023_11"].notna()
        csdf["blob_identical_2023_11"] = csdf["cs_blob_sha"] == csdf["blob_2023_11"]
        csdf = csdf.merge(lk[["accession", "arm", "n_conv_match", "n_raw_match"]], on="accession", how="left")
        csdf.to_csv(WRITE_OUT / "codesearch_head_ce_vs_msg_arm.csv", index=False)
        xt = csdf[csdf["in_2023_11_tree"]].groupby(["cs_dir", "head_ce_form", "head_frag_mode", "arm"], dropna=False).size()
        xt.rename("n").reset_index().to_csv(WRITE_OUT / "codesearch_head_ce_form_x_msg_arm.csv", index=False)
        agree = csdf[csdf["in_2023_11_tree"] & csdf["arm"].isin(["percent_converted_only", "raw_only"])]
        summary["codesearch_head_percent_vs_msg_arm"] = {
            c: {"n_resolvable": int((agree.cs_dir == c).sum()),
                "head_percent_and_converted": int(((agree.cs_dir == c) & agree.head_ce_has_percent & (agree.arm == "percent_converted_only")).sum()),
                "head_nopercent_and_raw": int(((agree.cs_dir == c) & ~agree.head_ce_has_percent & (agree.arm == "raw_only")).sum()),
                "head_percent_but_raw": int(((agree.cs_dir == c) & agree.head_ce_has_percent & (agree.arm == "raw_only")).sum()),
                "head_nopercent_but_converted": int(((agree.cs_dir == c) & ~agree.head_ce_has_percent & (agree.arm == "percent_converted_only")).sum()),
                "sampled_in_2023_11_tree": int(((csdf.cs_dir == c) & csdf.in_2023_11_tree).sum()),
                "sampled_not_in_2023_11_tree": int(((csdf.cs_dir == c) & ~csdf.in_2023_11_tree).sum()),
                "sampled_blob_identical": int(((csdf.cs_dir == c) & csdf.blob_identical_2023_11).sum()),
                "frag_mode_in_2023_11_sample": csdf.loc[(csdf.cs_dir == c) & csdf.in_2023_11_tree, "head_frag_mode"].value_counts(dropna=False).to_dict(),
                "frag_mode_by_instrument_type": {f"{a}|{b}": int(v) for (a, b), v in csdf[(csdf.cs_dir == c) & csdf.in_2023_11_tree].groupby(["api_instrument_type", "head_frag_mode"]).size().items()},
                } for c in CONTRIBUTORS}

    # ---------------- commits ----------------
    summary["commits_since_2023_11"] = {
        c: [(x["sha"][:7], x["date"][:10], x["message"].splitlines()[0]) for x in
            json.loads((DL / f"github_commits/commits_since_2023.11_{c}.json").read_text())] for c in CONTRIBUTORS}

    # ---------------- hidden-inclusion probes for design compounds not in MSG by key ----------------
    notmsg = comps_design[~comps_design["in_msg15_any"]]
    msg_formula = pd.read_parquet(ADJ / "massspecgym15_identity_metadata_joined.parquet", columns=["inchikey", "formula"])
    msg_formulas = set(msg_formula["formula"].dropna())
    rec_formula = rec.groupby("compound_id")["formula"].first()
    notmsg = notmsg.assign(formula=notmsg["compound_id"].map(rec_formula))
    notmsg = notmsg.assign(formula_in_msg=notmsg["formula"].isin(msg_formulas))
    notmsg.to_csv(WRITE_OUT / "design_compounds_not_in_msg_by_key.csv", index=False)
    summary["design_compounds_not_in_msg_by_key"] = {"n": int(len(notmsg)), "formula_also_in_msg": int(notmsg["formula_in_msg"].sum()),
                                                     "n_scaffold_groups": int(notmsg["scaffold_group"].nunique())}
    remaining = comps_design[~comps_design["excluded_any_key"]].copy()
    # tautomer / representation probe (criterion 11): canonical tautomer of the parent vs every MassSpecGym 1.5 SMILES
    # with the same molecular formula
    from rdkit import Chem
    from rdkit.Chem import inchi as _inchi
    from rdkit.Chem.MolStandardize import rdMolStandardize
    te = rdMolStandardize.TautomerEnumerator()

    def canon_taut_key(smi):
        m = SK.parent_mol(smi) if isinstance(smi, str) else None
        if m is None:
            return None
        try:
            t = te.Canonicalize(m)
            return _inchi.MolToInchiKey(t).split("-")[0]
        except Exception:  # noqa: BLE001
            return None

    msgf = pd.read_parquet(ADJ / "massspecgym15_identity_metadata_joined.parquet", columns=["inchikey", "formula", "smiles"]).drop_duplicates("inchikey")
    remaining["formula"] = remaining["compound_id"].map(rec_formula)
    probes = []
    for rr in remaining.itertuples(index=False):
        tk = canon_taut_key(rr.smiles)
        same_f = msgf[msgf["formula"] == rr.formula]
        hits = [row.inchikey for row in same_f.itertuples(index=False) if canon_taut_key(row.smiles) == tk] if tk else []
        probes.append({"compound_id": rr.compound_id, "formula": rr.formula, "canonical_tautomer_key": tk,
                       "msg_same_formula_keys": int(len(same_f)), "msg_tautomer_equal_keys": ";".join(hits)})
    pr = pd.DataFrame(probes)
    remaining = remaining.merge(pr, on=["compound_id", "formula"], how="left")
    rec_mass = rec.groupby("compound_id")["mono_mass"].first()
    remaining["mono_mass"] = remaining["compound_id"].map(rec_mass)
    remaining["MH_mz"] = remaining["mono_mass"] + PROTON
    remaining["MH_above_msg_1000_cap"] = remaining["MH_mz"] > 1000
    remaining["in_muru_dev_range_70_1042.6"] = remaining["MH_mz"].between(70.0, 1042.6)
    remaining.to_csv(WRITE_OUT / "design_compounds_after_all_key_exclusions.csv", index=False)
    summary["design_compounds_after_all_key_exclusions"] = {
        "n": int(len(remaining)), "n_scaffold_groups": int(remaining["scaffold_group"].nunique()),
        "n_not_in_any_exclusion_scaffold_set": int((~remaining["excluded_scaffold"]).sum()),
        "n_scaffold_groups_not_in_any_exclusion_scaffold_set": int(remaining.loc[~remaining["excluded_scaffold"], "scaffold_group"].nunique()),
        "n_with_msg_tautomer_equal_key": int(remaining["msg_tautomer_equal_keys"].fillna("").ne("").sum()),
        "n_MH_above_1000": int(remaining["MH_above_msg_1000_cap"].sum())}

    rec.drop(columns=["inchi"]).to_parquet(WRITE_OUT / "records.parquet", index=False)
    summary["n_records"] = int(len(rec))
    (WRITE_OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: summary[k] for k in ("exclusion_set_sizes",)}, indent=1))
    print(pd.DataFrame(per_dir).T.to_string())


if __name__ == "__main__":
    main()
