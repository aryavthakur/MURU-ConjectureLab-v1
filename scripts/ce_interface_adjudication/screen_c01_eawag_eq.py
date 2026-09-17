"""S1 screen C01 (MassBank Eawag EQ HCD NCE ladders first released after 2023.11), step 3: analysis.

Identity and acquisition METADATA only. No spectra, no peaks, no model output, no MURU outcome.

Inputs
  --tree       step 1 output eawag_eq_tree_blobs.csv (git trees of MassBank-data, blob SHAs per tag)
  --harvest    directory with step 2 outputs codesearch_{S,C,E,P,I}.json (header lines only)
  --exclusion  artifacts/ce_interface_adjudication/exclusion (P5 key/scaffold lists)
  --registry   artifacts/wur_v2_confirmation_v2/exposure_registry (excluded_compounds.csv: keys, census scaffold
               group, reasons; identity only)
  --msg-meta   artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet (smiles, formula only)
  --mspred-labels /Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv (smiles, inchikey)
  --outdir     artifacts/ce_interface_adjudication/screen/c01_eawag_eq
Key and scaffold definitions: scripts/ce_interface_adjudication/scaffold_key.py (MURU parent connectivity key and
scaffold_group_v2).
"""
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger, rdBase
from rdkit.Chem import Descriptors, inchi, rdFingerprintGenerator, rdMolDescriptors

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scaffold_key as SK  # noqa: E402

RDLogger.DisableLog("rdApp.*")
PROTON = 1.00727646688
RELEASE_ORDER = ["2024.06", "2024.11", "2025.10", "dev"]
CE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*%\s*\(nominal\)$")

TAGS = {
    "smiles": "CH$SMILES: ", "inchi": "CH$IUPAC: ", "inchikey": "CH$LINK: INCHIKEY ", "formula": "CH$FORMULA: ",
    "exact_mass": "CH$EXACT_MASS: ", "pubchem": "CH$LINK: PUBCHEM ", "cas": "CH$LINK: CAS ",
    "title": "RECORD_TITLE: ", "date": "DATE: ", "license": "LICENSE: ", "copyright": "COPYRIGHT: ",
    "authors": "AUTHORS: ", "publication": "PUBLICATION: ", "compound_class": "CH$COMPOUND_CLASS: ",
    "ch_name": "CH$NAME: ", "confidence": "COMMENT: CONFIDENCE ", "uchem_comment": "COMMENT: UCHEM_ID ",
    "instrument": "AC$INSTRUMENT: ", "instrument_type": "AC$INSTRUMENT_TYPE: ",
    "ce": "AC$MASS_SPECTROMETRY: COLLISION_ENERGY ", "frag_mode": "AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE ",
    "ion_mode": "AC$MASS_SPECTROMETRY: ION_MODE ", "ms_type": "AC$MASS_SPECTROMETRY: MS_TYPE ",
    "resolution": "AC$MASS_SPECTROMETRY: RESOLUTION ", "precursor_type": "MS$FOCUSED_ION: PRECURSOR_TYPE ",
    "precursor_mz": "MS$FOCUSED_ION: PRECURSOR_M/Z ",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def lines_set(p):
    return set(Path(p).read_text().split("\n")) - {""}


def main():
    ap = argparse.ArgumentParser()
    for k in ("tree", "harvest", "exclusion", "registry", "msg-meta", "mspred-labels", "outdir"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--dev-compounds", required=True,
                    help="artifacts/wur_v2/data/compounds.csv; only parent_key, smiles, scaffold_group are read")
    ap.add_argument("--d1-blocks", nargs="*", default=[],
                    help="task D1 code-search header blocks (same method, harvested 2026-09-15 at dev befc8a1); used "
                         "only for records not covered by this task's E/P/I passes")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    S = {"rdkit": rdBase.rdkitVersion, "inputs": {}}

    # ---------------- records ----------------
    tree = pd.read_csv(a.tree)
    S["inputs"]["tree"] = {"path": a.tree, "sha256": sha256(a.tree)}
    vals = collections.defaultdict(lambda: collections.defaultdict(set))
    shas = collections.defaultdict(dict)
    harvest_meta = {}
    for ps in "SCEPI":
        fn = Path(a.harvest) / f"codesearch_{ps}.json"
        if not fn.exists():
            continue
        S["inputs"][f"codesearch_{ps}"] = {"path": str(fn), "sha256": sha256(fn)}
        doc = json.loads(fn.read_text())
        harvest_meta[ps] = {"n_targets": doc["n_targets"], "n_harvested": doc["n_harvested"],
                            "retrieved_utc": doc["retrieved_utc"],
                            "n_queries": len(doc["queries"]),
                            "any_incomplete_results": any(q["incomplete_results"] for q in doc["queries"])}
        for f, r in doc["records"].items():
            shas[f][ps] = r["sha"]
            for ln in r["lines"]:
                for k, t in TAGS.items():
                    if ln.startswith(t):
                        vals[f][k].add(ln[len(t):].strip())
    own_epi = set()
    for ps in "EPI":
        fn = Path(a.harvest) / f"codesearch_{ps}.json"
        if fn.exists():
            own_epi |= set(json.loads(fn.read_text())["records"])
    d1_used = collections.Counter()
    for fn in a.d1_blocks:
        S["inputs"]["d1/" + Path(fn).name] = {"path": fn, "sha256": sha256(fn)}
        doc = json.loads(Path(fn).read_text())
        for f, lines in doc["records"].items():
            if f in own_epi:
                continue
            d1_used[Path(fn).name] += 1
            shas[f].setdefault("d1", None)
            for ln in lines:
                for k, t in TAGS.items():
                    if ln.startswith(t):
                        vals[f][k].add(ln[len(t):].strip())
    S["d1_block_records_used_as_fallback"] = dict(d1_used)
    S["harvest"] = harvest_meta
    targets = tree[tree["first_ref"].isin(RELEASE_ORDER)].copy()
    rows, conflicts = [], collections.Counter()
    for rd in targets.to_dict("records"):
        r = argparse.Namespace(**{k.replace(".", "_"): v for k, v in rd.items()})
        d = {"file": r.file, "first_ref": r.first_ref, "uchem_id_filename": r.uchem_id, "spec_idx": r.spec_idx,
             "suffix": r.suffix if isinstance(r.suffix, str) else "", "blob_dev": r.blob_dev,
             "blob_2025_10": r.blob_2025_10}
        for k in TAGS:
            v = vals[r.file].get(k, set())
            if k in ("pubchem", "cas", "ch_name"):
                d[k] = ";".join(sorted(v)) if v else None
                continue
            if len(v) > 1:
                conflicts[k] += 1
            d[k] = sorted(v)[0] if v else None
        s = {k: v for k, v in shas.get(r.file, {}).items() if k != "d1"}
        d["passes_found"] = "".join(sorted(s)) + ("+d1" if "d1" in shas.get(r.file, {}) else "")
        d["index_sha_matches_dev_blob"] = all(v == r.blob_dev for v in s.values()) if s else None
        rows.append(d)
    rec = pd.DataFrame(rows)
    S["n_target_records"] = int(len(rec))
    S["tag_value_conflicts_within_record"] = dict(conflicts)
    S["records_found_by_pass"] = {ps: int(rec["passes_found"].str.contains(ps).sum()) for ps in "SCEPI"}
    S["records_found_in_no_pass"] = int((rec["passes_found"] == "").sum())
    S["records_with_d1_fallback"] = int(rec["passes_found"].str.contains("d1").sum())
    S["records_missing_by_field"] = {k: int(rec[k].isna().sum()) for k in
                                     ("smiles", "inchi", "inchikey", "ce", "frag_mode", "ion_mode", "ms_type",
                                      "precursor_type", "precursor_mz", "instrument", "instrument_type", "license",
                                      "confidence")}
    S["records_missing_by_field_by_first_ref"] = {
        str(fr): {k: int(g[k].isna().sum()) for k in ("smiles", "ce", "precursor_type", "instrument_type", "frag_mode")}
        for fr, g in rec.groupby("first_ref")}
    S["index_sha_equals_dev_blob"] = {str(k): int(v) for k, v in rec["index_sha_matches_dev_blob"].value_counts(dropna=False).items()}
    rel_tagged = rec["first_ref"] != "dev"
    S["tagged_release_records_blob_2025_10_equals_dev"] = int((rec.loc[rel_tagged, "blob_2025_10"] == rec.loc[rel_tagged, "blob_dev"]).sum())
    S["tagged_release_records"] = int(rel_tagged.sum())

    # parse CE, precursor m/z
    rec["nce"] = rec["ce"].map(lambda s: float(CE_RE.match(s).group(1)) if isinstance(s, str) and CE_RE.match(s) else np.nan)
    rec["ce_form"] = rec["ce"].map(lambda s: "missing" if not isinstance(s, str) else
                                   ("N % (nominal)" if CE_RE.match(s) else ("contains %" if "%" in s else "other")))
    rec["precursor_mz_f"] = pd.to_numeric(rec["precursor_mz"], errors="coerce")
    rec["uchem_comment_int"] = pd.to_numeric(rec["uchem_comment"], errors="coerce")
    rec["name"] = rec["title"].map(lambda t: t.split(";")[0].strip() if isinstance(t, str) else None)
    rec["name"] = rec["name"].fillna(rec["ch_name"].map(lambda t: t.split(";")[0] if isinstance(t, str) else None))
    S["ce_string_forms_all_records"] = {str(k): int(v) for k, v in rec["ce_form"].value_counts(dropna=False).items()}
    S["ce_strings_other_examples"] = sorted(set(rec.loc[rec["ce_form"].isin(["contains %", "other"]), "ce"]))[:20]
    S["uchem_comment_equals_filename_id"] = {str(k): int(v) for k, v in
                                             (rec["uchem_comment_int"] == rec["uchem_id_filename"]).where(rec["uchem_comment_int"].notna()).value_counts(dropna=False).items()}

    # ---------------- structure per record ----------------
    cache = {}

    def chem(smi, inchi_s):
        kk = (smi, inchi_s)
        if kk in cache:
            return cache[kk]
        res = {"smiles_parse": False, "smiles_inchikey": None, "inchi_inchikey": None, "parent_key": None,
               "scaffold_group": None, "mh_calc": None, "heavy_atoms": None, "elements": None, "n_frag": None,
               "formal_charge": None}
        m = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
        if m is not None:
            res["smiles_parse"] = True
            res["smiles_inchikey"] = inchi.MolToInchiKey(m) or None
            pk, sg = SK.key_and_group(smi)
            res["parent_key"], res["scaffold_group"] = pk, sg
            pm = SK.parent_mol(smi)
            if pm is not None:
                res["mh_calc"] = Descriptors.ExactMolWt(pm) + PROTON
                res["heavy_atoms"] = pm.GetNumHeavyAtoms()
                res["elements"] = ",".join(sorted({x.GetSymbol() for x in Chem.AddHs(pm).GetAtoms()}))
                res["formal_charge"] = Chem.GetFormalCharge(pm)
            res["n_frag"] = len(Chem.GetMolFrags(m))
        if isinstance(inchi_s, str):
            mi = Chem.MolFromInchi(inchi_s)
            if mi is not None:
                res["inchi_inchikey"] = inchi.MolToInchiKey(mi) or None
        cache[kk] = res
        return res

    chem_rows = [chem(s, i) for s, i in zip(rec["smiles"], rec["inchi"])]
    rec = pd.concat([rec, pd.DataFrame(chem_rows)], axis=1)
    rec["recorded_key14"] = rec["inchikey"].map(SK.first_block)
    rec["smiles_ik_equals_recorded"] = np.where(rec["smiles_inchikey"].notna() & rec["inchikey"].notna(),
                                               rec["smiles_inchikey"] == rec["inchikey"], None)
    rec["inchi_ik_equals_recorded"] = np.where(rec["inchi_inchikey"].notna() & rec["inchikey"].notna(),
                                              rec["inchi_inchikey"] == rec["inchikey"], None)
    rec["mh_error_da"] = rec["precursor_mz_f"] - rec["mh_calc"]
    S["structure_qc_records"] = {
        "with_smiles": int(rec["smiles"].notna().sum()), "smiles_parse": int(rec["smiles_parse"].sum()),
        "with_inchikey": int(rec["inchikey"].notna().sum()),
        "smiles_inchikey_equals_recorded": {str(k): int(v) for k, v in rec["smiles_ik_equals_recorded"].value_counts(dropna=False).items()},
        "inchi_inchikey_equals_recorded": {str(k): int(v) for k, v in rec["inchi_ik_equals_recorded"].value_counts(dropna=False).items()},
    }
    rec.to_csv(out / "c01_record_metadata.csv.gz", index=False)

    # ---------------- population filter ----------------
    pos = rec[(rec["precursor_type"] == "[M+H]+")].copy()
    S["record_filter_counts"] = {
        "all_target_records": int(len(rec)),
        "precursor_type_counts": {str(k): int(v) for k, v in rec["precursor_type"].value_counts(dropna=False).items()},
        "ion_mode_counts": {str(k): int(v) for k, v in rec["ion_mode"].value_counts(dropna=False).items()},
        "MH_records": int(len(pos)),
        "MH_frag_mode": {str(k): int(v) for k, v in pos["frag_mode"].value_counts(dropna=False).items()},
        "MH_ms_type": {str(k): int(v) for k, v in pos["ms_type"].value_counts(dropna=False).items()},
        "MH_instrument_type": {str(k): int(v) for k, v in pos["instrument_type"].value_counts(dropna=False).items()},
        "MH_instrument": {str(k): int(v) for k, v in pos["instrument"].value_counts(dropna=False).items()},
        "MH_ce_form": {str(k): int(v) for k, v in pos["ce_form"].value_counts(dropna=False).items()},
        "MH_resolution": {str(k): int(v) for k, v in pos["resolution"].value_counts(dropna=False).items()},
        "MH_by_first_ref": {str(k): int(v) for k, v in pos["first_ref"].value_counts(dropna=False).items()},
        "MH_license": {str(k): int(v) for k, v in pos["license"].value_counts(dropna=False).items()},
        "MH_confidence": {str(k): int(v) for k, v in pos["confidence"].value_counts(dropna=False).items()},
        "MH_copyright": {str(k): int(v) for k, v in pos["copyright"].value_counts(dropna=False).items()},
        "MH_mh_abs_error_gt_0p01": int((pos["mh_error_da"].abs() > 0.01).sum()),
        "MH_mh_error_missing": int(pos["mh_error_da"].isna().sum()),
    }
    ok = pos[(pos["ion_mode"] == "POSITIVE") & (pos["ms_type"] == "MS2") & (pos["frag_mode"] == "HCD")
             & (pos["instrument_type"] == "LC-ESI-QFT") & pos["nce"].notna()].copy()
    S["record_filter_counts"]["MH_pos_MS2_HCD_QFT_single_nominal_pct"] = int(len(ok))

    # compound identity: MURU parent key; fall back to recorded first block if no SMILES in any record
    ok["cmp_key"] = ok["parent_key"].fillna("REC:" + ok["recorded_key14"].fillna("NA"))
    key_by_rec14 = ok.dropna(subset=["parent_key"]).groupby("recorded_key14")["parent_key"].agg(lambda s: sorted(set(s)))
    ok.loc[ok["parent_key"].isna() & ok["recorded_key14"].isin(key_by_rec14.index), "cmp_key"] = \
        ok.loc[ok["parent_key"].isna() & ok["recorded_key14"].isin(key_by_rec14.index), "recorded_key14"].map(
            lambda k: key_by_rec14[k][0] if len(key_by_rec14[k]) == 1 else "AMBIG:" + k)
    rank = {r: i for i, r in enumerate(RELEASE_ORDER)}

    def agg(g):
        sm = g.dropna(subset=["smiles"])
        first = sorted(g["first_ref"], key=rank.get)[0]
        return pd.Series({
            "recorded_key14s": ";".join(sorted(set(g["recorded_key14"].dropna()))),
            "parent_keys": ";".join(sorted(set(g["parent_key"].dropna()))),
            "scaffold_groups": ";".join(sorted(set(g["scaffold_group"].dropna()))),
            "n_distinct_smiles": sm["smiles"].nunique(),
            "smiles": sm["smiles"].iloc[0] if len(sm) else None,
            "name": g["name"].dropna().iloc[0] if g["name"].notna().any() else None,
            "uchem_ids": ";".join(str(int(x)) for x in sorted(set(g["uchem_id_filename"]))),
            "first_release": first,
            "releases": ";".join(sorted(set(g["first_ref"]), key=rank.get)),
            "n_records": len(g),
            "nce_ladder": ",".join(f"{v:g}" for v in sorted(set(g["nce"]))),
            "n_nce": g["nce"].nunique(),
            "instruments": ";".join(sorted(set(g["instrument"].dropna()))),
            "n_instruments": g["instrument"].nunique(),
            "precursor_mz": float(g["precursor_mz_f"].median()),
            "mh_calc": float(g["mh_calc"].dropna().median()) if g["mh_calc"].notna().any() else np.nan,
            "heavy_atoms": float(g["heavy_atoms"].dropna().median()) if g["heavy_atoms"].notna().any() else np.nan,
            "elements": g["elements"].dropna().iloc[0] if g["elements"].notna().any() else None,
            "n_frag_raw": g["n_frag"].dropna().max() if g["n_frag"].notna().any() else np.nan,
            "formula": g["formula"].dropna().iloc[0] if g["formula"].notna().any() else None,
            "confidence": ";".join(sorted(set(g["confidence"].dropna()))),
            "publication": ";".join(sorted(set(g["publication"].dropna()))),
            "authors": ";".join(sorted(set(g["authors"].dropna()))),
            "license": ";".join(sorted(set(g["license"].dropna()))),
            "any_smiles_ik_mismatch": bool((g["smiles_ik_equals_recorded"] == False).any()),  # noqa: E712
            "max_abs_mh_error_da": float(g["mh_error_da"].abs().max()) if g["mh_error_da"].notna().any() else np.nan,
        })

    cmp_ = ok.groupby("cmp_key").apply(agg).reset_index()
    cmp_["scaffold_group"] = cmp_["scaffold_groups"].map(lambda s: s.split(";")[0] if s else None)
    cmp_["n_scaffold_groups_in_records"] = cmp_["scaffold_groups"].map(lambda s: len(s.split(";")) if s else 0)
    cmp_["recorded_key14_list"] = cmp_["recorded_key14s"].map(lambda s: s.split(";") if s else [])

    # old Eawag uchem ids (present at <= 2023.11)
    old_ids = set(tree.loc[tree["blob_2023.11"].notna(), "uchem_id"])
    cmp_["uchem_id_in_2023_11_tree"] = cmp_["uchem_ids"].map(lambda s: any(int(x) in old_ids for x in s.split(";")))

    # records present at <= 2023.11 that share a UCHEM id with a screened compound (harvested with --extra-uchem)
    old_tree = tree[tree["blob_2023.11"].notna()]
    old_rows = []
    for rr in cmp_[cmp_["uchem_id_in_2023_11_tree"]].itertuples(index=False):
        for u in rr.uchem_ids.split(";"):
            for f in old_tree.loc[old_tree["uchem_id"] == int(u), "file"]:
                v = vals.get(f, {})
                old_rows.append({"cmp_key": rr.cmp_key, "uchem_id": int(u), "old_file": f,
                                 "old_recorded_inchikey": ";".join(sorted(v.get("inchikey", []))) or None,
                                 "old_ce": ";".join(sorted(v.get("ce", []))) or None,
                                 "old_precursor_type": ";".join(sorted(v.get("precursor_type", []))) or None,
                                 "old_instrument": ";".join(sorted(v.get("instrument", []))) or None,
                                 "blob_2023_11_equals_dev": bool(tree.set_index("file").loc[f, "blob_2023.11"] == tree.set_index("file").loc[f, "blob_dev"])})
    pd.DataFrame(old_rows).to_csv(out / "c01_shared_uchem_id_pre_2023_11_records.csv", index=False)
    S["shared_uchem_id_pre_2023_11_records"] = old_rows

    # ---------------- exclusion sets ----------------
    ex = Path(a.exclusion)
    E = {}
    for name, f in {"msg15_recorded": "msg15_keys_all.txt", "msg15_parent": "msg15_parent_keys_all.txt",
                    "msg15_scaffold_groups": "msg15_scaffold_groups_all.txt",
                    "msg15_sim_recorded": "msg15_simchallenge_keys_all.txt",
                    "muru_registry_keys": "muru_exposure_registry_keys.txt",
                    "muru_registry_scaffold_groups": "muru_exposure_registry_scaffold_groups.txt",
                    "pr7_keys": "msnlib_study2_population_keys.txt",
                    "pr7_scaffold_groups": "msnlib_study2_population_scaffold_groups.txt",
                    "comparator_keys": "comparator_common_population_keys.txt",
                    "comparator_scaffold_groups": "comparator_common_population_scaffold_groups.txt",
                    "msnlib_9lib_keys": "msnlib_9lib_keys.txt", "msnlib_v1_4lib_keys": "msnlib_v1_0_4lib_keys.txt",
                    "multims2_reserved_keys": "multims2_reserved_validation_secondary_keys.txt"}.items():
        E[name] = lines_set(ex / f)
        S["inputs"]["exclusion/" + f] = {"sha256": sha256(ex / f), "n": len(E[name])}
    reg = pd.read_csv(Path(a.registry) / "excluded_compounds.csv")
    S["inputs"]["registry/excluded_compounds.csv"] = {"sha256": sha256(Path(a.registry) / "excluded_compounds.csv")}
    exp = reg[reg["reasons"].str.contains("EXPOSED_POPULATION:")]
    E["muru_exposed_pop_keys"] = set(exp["key"])
    dc = pd.read_csv(a.dev_compounds, usecols=["parent_key", "smiles", "scaffold_group"])
    S["inputs"]["dev_compounds"] = {"path": a.dev_compounds, "sha256": sha256(a.dev_compounds), "rows": int(len(dc)),
                                    "columns_read": ["parent_key", "smiles", "scaffold_group"]}
    rec_ok = sum(SK.key_and_group(s_) == (k_, g_) for s_, k_, g_ in zip(dc["smiles"], dc["parent_key"], dc["scaffold_group"]))
    S["inputs"]["dev_compounds"]["key_and_group_recomputed_match"] = int(rec_ok)
    E["muru_dev_pop_keys"] = set(dc["parent_key"])
    E["muru_dev_pop_scaffold_groups"] = set(dc["scaffold_group"])
    S["derived_exclusion_set_sizes"] = {k: len(E[k]) for k in ("muru_exposed_pop_keys", "muru_dev_pop_keys",
                                                               "muru_dev_pop_scaffold_groups")}
    S["derived_exclusion_set_sizes"]["dev_pop_keys_equal_registry_population_list"] = (
        E["muru_dev_pop_keys"] == set(reg.loc[reg["reasons"].str.contains("V2-DEVELOPMENT-POPULATION"), "key"]))
    S["derived_exclusion_set_sizes"]["dev_pop_scaffold_groups_inside_registry_groups"] = len(
        E["muru_dev_pop_scaffold_groups"] & E["muru_registry_scaffold_groups"])
    lab = pd.read_csv(a.mspred_labels, sep="\t", usecols=["smiles", "inchikey"])
    S["inputs"]["mspred_labels"] = {"path": a.mspred_labels, "sha256": sha256(a.mspred_labels), "rows": int(len(lab))}
    E["mspred_labels_recorded"] = set(lab["inchikey"].dropna().map(lambda k: k.split("-")[0]))
    lab_parent = {}
    for s in lab["smiles"].dropna().unique():
        lab_parent[s] = SK.key_and_group(s)[0]
    E["mspred_labels_parent"] = set(v for v in lab_parent.values() if v)
    S["derived_exclusion_set_sizes"].update({"mspred_labels_recorded": len(E["mspred_labels_recorded"]),
                                             "mspred_labels_parent": len(E["mspred_labels_parent"])})

    def anyin(keys, s):
        return any(k in s for k in keys)

    cmp_["keys_all"] = cmp_.apply(lambda r: set(r["recorded_key14_list"]) | set(r["parent_keys"].split(";") if r["parent_keys"] else []), axis=1)
    flag = {
        "in_msg15_any_route": lambda r: anyin(r["keys_all"], E["msg15_recorded"] | E["msg15_parent"]),
        "in_msg15_recorded_route": lambda r: anyin(r["keys_all"], E["msg15_recorded"]),
        "in_msg15_parent_route": lambda r: anyin(r["keys_all"], E["msg15_parent"]),
        "in_msg15_simchallenge": lambda r: anyin(r["keys_all"], E["msg15_sim_recorded"]),
        "in_mspred_msg_labels": lambda r: anyin(r["keys_all"], E["mspred_labels_recorded"] | E["mspred_labels_parent"]),
        "in_muru_registry_keys": lambda r: anyin(r["keys_all"], E["muru_registry_keys"]),
        "in_muru_exposed_pop_keys": lambda r: anyin(r["keys_all"], E["muru_exposed_pop_keys"]),
        "in_muru_dev_pop_keys": lambda r: anyin(r["keys_all"], E["muru_dev_pop_keys"]),
        "in_pr7_keys": lambda r: anyin(r["keys_all"], E["pr7_keys"]),
        "in_comparator_keys": lambda r: anyin(r["keys_all"], E["comparator_keys"]),
        "in_msnlib_9lib_keys": lambda r: anyin(r["keys_all"], E["msnlib_9lib_keys"]),
        "in_msnlib_v1_4lib_keys": lambda r: anyin(r["keys_all"], E["msnlib_v1_4lib_keys"]),
        "in_multims2_reserved": lambda r: anyin(r["keys_all"], E["multims2_reserved_keys"]),
        "sg_in_muru_registry": lambda r: r["scaffold_group"] in E["muru_registry_scaffold_groups"],
        "sg_in_muru_dev_pop": lambda r: r["scaffold_group"] in E["muru_dev_pop_scaffold_groups"],
        "sg_in_pr7": lambda r: r["scaffold_group"] in E["pr7_scaffold_groups"],
        "sg_in_comparator": lambda r: r["scaffold_group"] in E["comparator_scaffold_groups"],
        "sg_in_msg15": lambda r: r["scaffold_group"] in E["msg15_scaffold_groups"],
    }
    for k, fnc in flag.items():
        cmp_[k] = cmp_.apply(fnc, axis=1)
    cmp_["acyclic"] = cmp_["scaffold_group"].fillna("").str.startswith("__ACYCLIC__")

    # ---------------- nearest MSG neighbours (structure novelty and hidden-inclusion screen) ----------------
    mm = pd.read_parquet(a.msg_meta, columns=["smiles", "formula"]).drop_duplicates("smiles")
    S["inputs"]["msg_meta"] = {"path": a.msg_meta, "sha256": sha256(a.msg_meta)}
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    msg_fps, msg_formula, msg_smiles = [], [], []
    for s, f in zip(mm["smiles"], mm["formula"]):
        pm = SK.parent_mol(s)
        if pm is None:
            continue
        msg_fps.append(gen.GetFingerprint(pm))
        msg_formula.append(rdMolDescriptors.CalcMolFormula(pm))
        msg_smiles.append(s)
    msg_formula = np.array(msg_formula)
    by_formula = collections.defaultdict(list)
    for i, f in enumerate(msg_formula):
        by_formula[f].append(i)
    nn_sim, nn_smi, same_formula_n, same_formula_maxsim = [], [], [], []
    for s in cmp_["smiles"]:
        pm = SK.parent_mol(s) if isinstance(s, str) else None
        if pm is None:
            nn_sim.append(np.nan); nn_smi.append(None); same_formula_n.append(np.nan); same_formula_maxsim.append(np.nan)
            continue
        fp = gen.GetFingerprint(pm)
        sims = np.array(DataStructs.BulkTanimotoSimilarity(fp, msg_fps))
        j = int(sims.argmax())
        nn_sim.append(float(sims[j])); nn_smi.append(msg_smiles[j])
        idx = by_formula.get(rdMolDescriptors.CalcMolFormula(pm), [])
        same_formula_n.append(len(idx))
        same_formula_maxsim.append(float(sims[idx].max()) if idx else np.nan)
    cmp_["msg15_nn_tanimoto"] = nn_sim
    cmp_["msg15_nn_smiles"] = nn_smi
    cmp_["msg15_same_formula_n_structures"] = same_formula_n
    cmp_["msg15_same_formula_max_tanimoto"] = same_formula_maxsim
    S["inputs"]["msg_meta"]["n_unique_parent_structures_fp"] = len(msg_fps)

    # ---------------- tiers ----------------
    cmp_["tagged_release"] = cmp_["first_release"] != "dev"
    cmp_["ge3_nce"] = cmp_["n_nce"] >= 3
    excl_compound = (cmp_["in_msg15_any_route"] | cmp_["in_mspred_msg_labels"] | cmp_["in_muru_registry_keys"]
                     | cmp_["in_pr7_keys"] | cmp_["in_comparator_keys"])
    excl_scaffold_primary = cmp_["sg_in_muru_dev_pop"] | cmp_["sg_in_pr7"] | cmp_["sg_in_comparator"]
    excl_scaffold_conservative = excl_scaffold_primary | cmp_["sg_in_muru_registry"]
    cmp_["clean_compound_level"] = ~excl_compound
    cmp_["clean_primary"] = ~excl_compound & ~excl_scaffold_primary
    cmp_["clean_conservative"] = ~excl_compound & ~excl_scaffold_conservative
    cmp_["clean_strict_msg_scaffold"] = cmp_["clean_conservative"] & ~cmp_["sg_in_msg15"]
    cmp_.drop(columns=["keys_all", "recorded_key14_list"]).to_csv(out / "c01_compound_screen.csv", index=False)

    def butina_clusters(df, dist=0.6):
        from rdkit.ML.Cluster import Butina
        if len(df) == 0:
            return np.array([], int), 0
        fps = [gen.GetFingerprint(SK.parent_mol(x)) for x in df["smiles"]]
        dd = []
        for i in range(1, len(fps)):
            dd.extend([1 - v for v in DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])])
        cl = Butina.ClusterData(dd, len(fps), dist, isDistData=True)
        lab = np.zeros(len(df), int)
        for k, q in enumerate(cl):
            for i in q:
                lab[i] = k
        return lab, len(cl)

    def summarize(df):
        df = df.reset_index(drop=True)
        sg = df["scaffold_group"]
        vc = sg.value_counts()
        lab, ncl = butina_clusters(df)
        bands = {"lt300": df["precursor_mz"] < 300, "300_500": (df["precursor_mz"] >= 300) & (df["precursor_mz"] < 500),
                 "ge500": df["precursor_mz"] >= 500}
        return {
            "butina_clusters_morgan2_tanimoto_distance_0p6": int(ncl),
            "by_precursor_mz_band_compounds_scaffold_groups_clusters": {
                k: [int(m.sum()), int(sg[m].nunique()), int(len(set(lab[m.values])))] for k, m in bands.items()},
            "n_spectra_records": int(df["n_records"].sum()) if len(df) else 0,
            "n_compounds": int(len(df)), "n_scaffold_groups": int(sg.nunique()),
            "n_ring_scaffold_groups": int(sg[~sg.fillna("").str.startswith("__ACYCLIC__")].nunique()),
            "n_acyclic_compounds": int(df["acyclic"].astype(bool).sum()),
            "largest_scaffold_group_size": int(vc.max()) if len(vc) else 0,
            "largest_scaffold_groups": {str(k): int(v) for k, v in vc.head(5).items()},
            "singleton_scaffold_groups": int((vc == 1).sum()),
            "by_first_release": {str(k): int(v) for k, v in df["first_release"].value_counts().items()},
            "precursor_mz_median": round(float(df["precursor_mz"].median()), 1) if len(df) else None,
            "precursor_mz_q10_q90": [round(float(x), 1) for x in df["precursor_mz"].quantile([0.1, 0.9])] if len(df) else None,
            "precursor_mz_min_max": [round(float(df["precursor_mz"].min()), 1), round(float(df["precursor_mz"].max()), 1)] if len(df) else None,
            "n_precursor_mz_ge_500": int((df["precursor_mz"] >= 500).sum()),
            "n_precursor_mz_gt_1000": int((df["precursor_mz"] > 1000).sum()),
            "n_outside_muru_dev_mh_range_70_1042p6": int(((df["precursor_mz"] < 70.0) | (df["precursor_mz"] > 1042.594)).sum()),
            "heavy_atoms_max": float(df["heavy_atoms"].max()) if len(df) else None,
            "n_heavy_atoms_gt_160": int((df["heavy_atoms"] > 160).sum()),
            "nce_ladders": {str(k): int(v) for k, v in df["nce_ladder"].value_counts().head(8).items()},
            "n_with_nce60": sum(1 for s in df["nce_ladder"] if "60" in s.split(",")),
            "n_with_nce15_and_30": sum(1 for s in df["nce_ladder"] if {"15", "30"} <= set(s.split(","))),
            "n_with_nce20": sum(1 for s in df["nce_ladder"] if "20" in s.split(",")),
            "n_nce_distribution": {str(k): int(v) for k, v in df["n_nce"].value_counts().sort_index().items()},
            "instruments": {str(k): int(v) for k, v in df["instruments"].value_counts().items()},
            "n_multi_instrument": int((df["n_instruments"] > 1).sum()),
            "confidence": {str(k): int(v) for k, v in df["confidence"].value_counts().items()},
            "license": {str(k): int(v) for k, v in df["license"].value_counts().items()},
            "elements_non_CHNOPS_halogen": sum(1 for e in df["elements"].fillna("") if set(e.split(",")) - {"C", "H", "N", "O", "P", "S", "F", "Cl", "Br", "I", ""}),
            "n_uchem_id_in_2023_11_tree": int(df["uchem_id_in_2023_11_tree"].astype(bool).sum()),
            "msg15_nn_tanimoto_median": round(float(df["msg15_nn_tanimoto"].median()), 3) if len(df) else None,
            "n_msg15_nn_tanimoto_ge_0p9": int((df["msg15_nn_tanimoto"] >= 0.9).sum()),
            "n_msg15_same_formula_tanimoto_ge_0p9": int((df["msg15_same_formula_max_tanimoto"] >= 0.9).sum()),
            "n_any_smiles_inchikey_mismatch": int(df["any_smiles_ik_mismatch"].astype(bool).sum()),
            "n_max_abs_mh_error_gt_0p01": int((df["max_abs_mh_error_da"] > 0.01).sum()),
            "n_multiple_smiles": int((df["n_distinct_smiles"] > 1).sum()),
        }

    base = cmp_[cmp_["ge3_nce"]]
    S["compounds"] = {
        "MH_HCD_QFT_nominal_pct_all_compounds": int(len(cmp_)),
        "cmp_key_without_parent_key": int(cmp_["parent_keys"].eq("").sum()),
        "compounds_with_multiple_parent_keys": int(cmp_["parent_keys"].str.contains(";").sum()),
        "compounds_with_multiple_recorded_key14": int(cmp_["recorded_key14s"].str.contains(";").sum()),
        "compounds_with_multiple_scaffold_groups": int((cmp_["n_scaffold_groups_in_records"] > 1).sum()),
        "ge3_nce": int(len(base)),
    }
    for scope, m in {"tagged_2024.06_2024.11_2025.10": base["tagged_release"], "dev_only_PR398": ~base["tagged_release"],
                     "all_including_dev": base["tagged_release"] | ~base["tagged_release"]}.items():
        b = base[m]
        blk = {"ge3_nce_compounds": int(len(b))}
        for k in flag:
            blk[k] = int(b[k].sum())
        blk["excluded_compound_level_union"] = int((~b["clean_compound_level"]).sum())
        blk["clean_compound_level"] = summarize(b[b["clean_compound_level"]])
        blk["clean_primary"] = summarize(b[b["clean_primary"]])
        blk["clean_conservative"] = summarize(b[b["clean_conservative"]])
        blk["clean_strict_msg_scaffold"] = summarize(b[b["clean_strict_msg_scaffold"]])
        blk["recorded_key_only_clean_count_for_M_comparison"] = int(
            (~b["in_msg15_recorded_route"] & ~b["recorded_key14s"].map(lambda s: any(k in E["muru_registry_keys"] for k in s.split(";")))).sum())
        S[scope] = blk
    # compare with task M staged clean list (recorded-key route) if present
    (out / "c01_screen_summary.json").write_text(json.dumps(S, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(S, indent=1, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
