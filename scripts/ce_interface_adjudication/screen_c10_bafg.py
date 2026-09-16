"""S10 screen C10 (MassBank contributor BAFG, SCIEX TripleTOF LC-ESI-QTOF CE ladders): metadata-only overlap and
feasibility screen.

Inputs (all metadata; fetched by screen_c10_bafg_fetch.py and screen_c10_bafg_codesearch.py):
  downloads/massbank_export_jsonld/bafg_export_metadata_jsonld.jsonl.gz  per-accession JSON-LD (title with CE, license,
      datePublished, InChI, SMILES, InChIKey, formula, monoisotopic mass; no peaks)
  downloads/massbank_api/search_BAFG__{POSITIVE,NEGATIVE}.json            ion mode per accession
  downloads/github_trees/tree_{2023.11,2025.05,2025.05.1}_BAFG.json.gz    file names + blob sha per release
  downloads/github_codesearch/*.json                                      header-line fragments (instrument, precursor type)
Exclusion sets from P5 (artifacts/ce_interface_adjudication/exclusion/), MURU key/scaffold from scaffold_key.py,
development population identity columns (parent_key, scaffold_group) of artifacts/wur_v2/data/compounds.csv, MassSpecGym
1.5 identity/metadata columns (no spectra) from P4/P5/P3 parquet files.

No model is run; no spectra, measured-mu, result, or prediction file is read.
Outputs: artifacts/ce_interface_adjudication/screen/c10_bafg/{c10_records_identity.csv, c10_compounds_screen.csv,
  c10_msg_mass_linkage.csv, c10_screen_summary.json, output_manifest_sha256.json}
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import Descriptors, inchi
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

RDLogger.DisableLog("rdApp.*")
ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
sys.path.insert(0, str(ROOT / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

ADJ = ROOT / "artifacts/ce_interface_adjudication"
EXC = ADJ / "exclusion"
OUT = ADJ / "screen/c10_bafg"
DL = OUT / "downloads"
PROTON = 1.007276466812
LADDER = set(range(10, 151, 10))


def read_keys(p):
    return {x.strip() for x in open(p) if x.strip()}


def counts(it):
    return dict(Counter(it).most_common())


def parse_title(t):
    """BAFG title: '<name>; LC-ESI-QTOF; MS2; 50 V'. Returns instrument_type, ms_type, ce_value, ce_unit, ce_raw."""
    parts = [p.strip() for p in t.split(";")]
    ce_raw = parts[-1] if parts else ""
    m = re.fullmatch(r"(?:CE:\s*)?([0-9]+(?:\.[0-9]+)?)\s*(V|eV|%|)", ce_raw)
    inst = next((p for p in parts if re.fullmatch(r"[A-Z]+(-[A-Z]+)+", p)), None)
    mst = next((p for p in parts if re.fullmatch(r"MS[0-9n]?", p)), None)
    return inst, mst, (float(m.group(1)) if m else None), (m.group(2) if m else None), ce_raw


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"rdkit": rdBase.rdkitVersion, "frozen_rdkit_for_keys": SK.FROZEN_RDKIT}

    # ------------------------------------------------------------ record table
    mode = {}
    for m in ("POSITIVE", "NEGATIVE"):
        for x in json.loads((DL / f"massbank_api/search_BAFG__{m}.json").read_text())["data"]:
            mode[x["accession"]] = m
    trees = {}
    for lab in ("2023.11", "2025.05", "2025.05.1"):
        t = json.loads(gzip.decompress((DL / f"github_trees/tree_{lab}_BAFG.json.gz").read_bytes()))
        trees[lab] = {e["path"][:-4]: e["sha"] for e in t if e["type"] == "blob" and e["path"].endswith(".txt")}
    rows = []
    with gzip.open(DL / "massbank_export_jsonld/bafg_export_metadata_jsonld.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line)
            acc = r["accession"]
            rec = {"accession": acc, "http_status": r["status"], "ion_mode": mode.get(acc),
                   "in_tree_2023_11": acc in trees["2023.11"], "in_tree_2025_05_1": acc in trees["2025.05.1"],
                   "blob_changed_2023_11_to_2025_05_1": (acc in trees["2023.11"] and acc in trees["2025.05.1"]
                                                         and trees["2023.11"][acc] != trees["2025.05.1"][acc])}
            if r["body"]:
                ds = next(b for b in r["body"] if b.get("@type") == "Dataset")
                cs = next((b for b in r["body"] if b.get("@type") == "ChemicalSubstance"), {})
                me = (cs.get("hasBioChemEntityPart") or [{}])[0]
                inst, mst, cev, ceu, ceraw = parse_title(ds.get("name", ""))
                rec.update({"title": ds.get("name"), "license": ds.get("license"), "date_published": ds.get("datePublished"),
                            "title_instrument_type": inst, "title_ms_type": mst, "ce_value": cev, "ce_unit": ceu,
                            "ce_raw": ceraw, "compound_name": cs.get("name"), "formula_recorded": me.get("molecularFormula"),
                            "inchi": me.get("inChI"), "smiles": me.get("smiles"), "inchikey_recorded": me.get("inChIKey"),
                            "monoisotopic_recorded": me.get("monoisotopicMolecularWeight")})
            rows.append(rec)
    df = pd.DataFrame(rows)
    summary["records"] = {"n": int(len(df)), "http_status": counts(df["http_status"].astype(str)),
                          "ion_mode": counts(df["ion_mode"].fillna("NA")),
                          "in_tree_2023_11": int(df["in_tree_2023_11"].sum()),
                          "new_after_2023_11": int((~df["in_tree_2023_11"]).sum()),
                          "blob_changed_2023_11_to_2025_05_1": int(df["blob_changed_2023_11_to_2025_05_1"].sum()),
                          "title_instrument_type": counts(df["title_instrument_type"].fillna("NA")),
                          "title_ms_type": counts(df["title_ms_type"].fillna("NA")),
                          "ce_unit": counts(df["ce_unit"].fillna("UNPARSED")),
                          "ce_value": {str(k): v for k, v in counts(df["ce_value"].fillna(-1)).items()},
                          "ce_unparsed_examples": df.loc[df["ce_value"].isna(), "ce_raw"].dropna().head(10).tolist(),
                          "license": counts(df["license"].fillna("NA")),
                          "date_published": counts(df["date_published"].fillna("NA")),
                          "date_published_by_2023_11_membership": {
                              str(k): counts(g["date_published"].fillna("NA"))
                              for k, g in df.groupby("in_tree_2023_11")},
                          "accession_prefix_by_2023_11_membership": {
                              str(k): counts(g["accession"].str[:17]) for k, g in df.groupby("in_tree_2023_11")}}

    # ------------------------------------------------------------ identity
    cache = {}

    def ident(smiles, inchi_s):
        ck = (smiles, inchi_s)
        if ck in cache:
            return cache[ck]
        route = "smiles"
        k, g = SK.key_and_group(smiles) if isinstance(smiles, str) and smiles else (None, None)
        smi_used = smiles
        if k is None and isinstance(inchi_s, str) and inchi_s:
            mi = inchi.MolFromInchi(inchi_s)
            if mi is not None:
                smi_used = Chem.MolToSmiles(mi)
                k, g = SK.key_and_group(smi_used)
                route = "inchi"
        out = {"key": k, "scaffold_group": g, "key_route": route if k else None}
        pm = SK.parent_mol(smi_used) if k else None
        if pm is not None:
            out["parent_formula"] = CalcMolFormula(pm)
            out["parent_charge"] = sum(a.GetFormalCharge() for a in pm.GetAtoms())
            out["parent_monoisotopic"] = Descriptors.ExactMolWt(pm)
            out["elements"] = ";".join(sorted({a.GetSymbol() for a in pm.GetAtoms()}))
            out["n_fragments_raw"] = len(Chem.GetMolFrags(Chem.MolFromSmiles(smi_used)))
        # does the recorded SMILES agree with the recorded InChI (first block)?
        if isinstance(inchi_s, str) and inchi_s and isinstance(smiles, str) and smiles:
            ms = Chem.MolFromSmiles(smiles)
            kk = inchi.MolToInchiKey(ms) if ms is not None else ""
            ki = inchi.InchiToInchiKey(inchi_s) or ""
            out["smiles_inchi_block1_agree"] = bool(kk and ki and kk[:14] == ki[:14])
        cache[ck] = out
        return out

    idf = pd.DataFrame([ident(s, i) for s, i in zip(df["smiles"], df["inchi"])])
    df = pd.concat([df, idf], axis=1)
    df["recorded_block1"] = df["inchikey_recorded"].map(SK.first_block)
    df["recorded_charged"] = df["formula_recorded"].fillna("").str.contains(r"[+\-]$|\]\+|\]-", regex=True)
    df["mh_mz_from_parent"] = df["parent_monoisotopic"] + PROTON
    summary["identity"] = {"records_with_key": int(df["key"].notna().sum()),
                           "key_route": counts(df["key_route"].fillna("NONE")),
                           "recorded_block1_eq_parent_key": int((df["recorded_block1"] == df["key"]).sum()),
                           "recorded_block1_ne_parent_key": int((df["key"].notna() & (df["recorded_block1"] != df["key"])).sum()),
                           "smiles_inchi_block1_disagree_records": int((df["smiles_inchi_block1_agree"] == False).sum()),  # noqa: E712
                           "recorded_charged_formula_records": int(df["recorded_charged"].sum()),
                           "parent_charge_nonzero_records": int((df["parent_charge"].fillna(0) != 0).sum()),
                           "multi_fragment_raw_records": int((df["n_fragments_raw"].fillna(1) > 1).sum()),
                           "keys_all": int(df["key"].nunique()), "scaffold_groups_all": int(df["scaffold_group"].nunique())}

    # ------------------------------------------------------------ code-search fragments (precursor type, instrument)
    def frag_lines(label, prefix):
        p = DL / f"github_codesearch/{label}.json"
        if not p.exists():
            return None, {}
        d = json.loads(p.read_text())
        per = {}
        for pg in d["pages"]:
            for h in pg["hits"]:
                acc = Path(h["path"]).stem
                for fr in h["fragments"]:
                    for ln in fr.split("\n"):
                        if prefix in ln:
                            per[acc] = ln.split(prefix, 1)[1].strip()
        return d, per

    cs = {}
    for lab in sorted(p.stem for p in (DL / "github_codesearch").glob("*.json")):
        d = json.loads((DL / f"github_codesearch/{lab}.json").read_text())
        cs[lab] = {"total_count": d["total_count"], "incomplete_results": d["incomplete_results"],
                   "hits_kept": sum(pg["n_items"] for pg in d["pages"]), "dropped_pk_lines": d["dropped_pk_lines"]}
    summary["codesearch_counts_dev_branch"] = cs
    _, prec = frag_lines("prec_any", "PRECURSOR_TYPE")
    for lab in ("prec_NH4", "prec_Na", "prec_K", "prec_H2O"):
        _, extra = frag_lines(lab, "PRECURSOR_TYPE")
        prec.update(extra)
    _, inst = frag_lines("inst_line", "AC$INSTRUMENT:")
    _, fragm = frag_lines("frag_any", "FRAGMENTATION_MODE")
    df["precursor_type_codesearch"] = df["accession"].map(prec)
    df["instrument_codesearch"] = df["accession"].map(inst)
    sm = df[df["precursor_type_codesearch"].notna()]
    summary["precursor_type_codesearch_sample"] = {
        "n_records": int(len(sm)),
        "by_ion_mode": {m: counts(g["precursor_type_codesearch"]) for m, g in sm.groupby("ion_mode")},
        "positive_neutral_parent_recorded_uncharged": counts(
            sm[(sm["ion_mode"] == "POSITIVE") & ~sm["recorded_charged"]]["precursor_type_codesearch"]),
        "positive_recorded_charged": counts(sm[(sm["ion_mode"] == "POSITIVE") & sm["recorded_charged"]]["precursor_type_codesearch"]),
        "note": "non-random sample: GitHub best-match order, dev branch; exact adduct per record is otherwise not in the "
                "allowed metadata"}
    si = df[df["instrument_codesearch"].notna()]
    summary["instrument_codesearch_sample"] = {"n_records": int(len(si)), "instrument": counts(si["instrument_codesearch"]),
                                               "by_2023_11_membership": {str(k): counts(g["instrument_codesearch"])
                                                                         for k, g in si.groupby("in_tree_2023_11")}}

    # ------------------------------------------------------------ exclusion sets
    sets = {
        "msg15_recorded_all": read_keys(EXC / "msg15_keys_all.txt"),
        "msg15_parent_all": read_keys(EXC / "msg15_parent_keys_all.txt"),
        "msg15_simchallenge_all": read_keys(EXC / "msg15_simchallenge_keys_all.txt"),
        "msg15_recorded_train": read_keys(EXC / "msg15_keys_train.txt"),
        "muru_registry_all": read_keys(EXC / "muru_exposure_registry_keys.txt"),
        "muru_exposed_union": read_keys(EXC / "muru_exposed_union_keys.txt"),
        "pr7_study2_population": read_keys(EXC / "msnlib_study2_population_keys.txt"),
        "comparator_common_population": read_keys(EXC / "comparator_common_population_keys.txt"),
        "msnlib_9lib": read_keys(EXC / "msnlib_9lib_keys.txt"),
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
    summary["exclusion_set_sizes"] = {k: len(v) for k, v in {**sets, **groups}.items()}
    for k, v in sets.items():
        df[f"in_{k}"] = df["key"].isin(v)
    for k, v in groups.items():
        df[f"sg_in_{k}"] = df["scaffold_group"].isin(v)
    df["in_msg15_any_route"] = (df["in_msg15_recorded_all"] | df["in_msg15_parent_all"]
                                | df["recorded_block1"].isin(sets["msg15_recorded_all"] | sets["msg15_parent_all"]))
    df.to_csv(OUT / "c10_records_identity.csv", index=False)

    # ------------------------------------------------------------ compound table (positive mode)
    pos = df[(df["ion_mode"] == "POSITIVE") & df["key"].notna()].copy()
    agg = pos.groupby("key").agg(
        scaffold_group=("scaffold_group", "first"), parent_formula=("parent_formula", "first"),
        parent_charge=("parent_charge", "first"), mh_mz=("mh_mz_from_parent", "first"),
        compound_name=("compound_name", "first"), n_records=("accession", "size"),
        ce_values=("ce_value", lambda x: ";".join(str(int(v)) if float(v).is_integer() else str(v)
                                                  for v in sorted(set(x.dropna())))),
        n_distinct_ce=("ce_value", lambda x: int(x.dropna().nunique())),
        ce_units=("ce_unit", lambda x: ";".join(sorted(set(x.dropna())))),
        any_record_in_2023_11=("in_tree_2023_11", "any"), all_records_in_2023_11=("in_tree_2023_11", "all"),
        recorded_charged=("recorded_charged", "any"),
        recorded_block1s=("recorded_block1", lambda x: ";".join(sorted(set(x.dropna())))),
        date_published=("date_published", lambda x: ";".join(sorted(set(x.dropna())))),
        in_msg15_any_route=("in_msg15_any_route", "any"),
        in_msg15_simchallenge=("in_msg15_simchallenge_all", "any"),
        in_muru_registry=("in_muru_registry_all", "any"), in_muru_exposed_union=("in_muru_exposed_union", "any"),
        in_muru_exposed_populations=("in_muru_exposed_populations_union", "any"),
        in_muru_dev=("in_muru_dev_compounds_csv_keys", "any"), in_pr7=("in_pr7_study2_population", "any"),
        in_comparator=("in_comparator_common_population", "any"), in_msnlib_9lib=("in_msnlib_9lib", "any"),
        sg_in_msg15=("sg_in_msg15_scaffold_groups", "any"), sg_in_muru_registry=("sg_in_muru_registry_scaffold_groups", "any"),
        sg_in_muru_dev=("sg_in_muru_dev_scaffold_groups", "any"), sg_in_pr7=("sg_in_pr7_scaffold_groups", "any"),
        sg_in_comparator=("sg_in_comparator_scaffold_groups", "any"),
    ).reset_index()
    agg["in_range_70_1042_6"] = (agg["mh_mz"] >= 70.0) & (agg["mh_mz"] <= 1042.6)
    agg["charge_neutral_parent"] = (agg["parent_charge"] == 0) & ~agg["recorded_charged"]

    # ------------------------------------------------------------ MSG rows for BAFG keys, and mass-based linkage
    msg = pd.read_parquet(ADJ / "massspecgym15_identity_metadata_joined.parquet",
                          columns=["identifier", "inchikey", "fold", "simulation_challenge", "adduct", "instrument_type",
                                   "collision_energy", "precursor_mz", "formula"])
    mk = pd.read_parquet(EXC / "msg15_row_keys.parquet", columns=["identifier", "parent_key", "scaffold_group"])
    src = pd.read_parquet(ADJ / "p3_msg15_row_source_attribution.parquet", columns=["identifier", "source_label"])
    msg = msg.merge(mk, on="identifier", how="left").merge(src, on="identifier", how="left")
    bk = set(agg["key"])
    mrows = msg[msg["inchikey"].isin(bk) | msg["parent_key"].isin(bk)].copy()
    mrows["k"] = [b if b in bk else a for a, b in zip(mrows["inchikey"], mrows["parent_key"])]
    ce_int = mrows["collision_energy"].round(6)
    mrows["ce_in_bafg_ladder"] = ce_int.isin(LADDER)
    mq = mrows[(mrows["instrument_type"] == "QTOF")]
    summary["msg_rows_for_bafg_positive_keys"] = {
        "rows": int(len(mrows)), "keys": int(mrows["k"].nunique()),
        "instrument_type": counts(mrows["instrument_type"].fillna("NA")), "adduct": counts(mrows["adduct"]),
        "fold_rows": counts(mrows["fold"]), "source_label_rows": counts(mrows["source_label"].fillna("NA")),
        "qtof_rows": int(len(mq)), "qtof_rows_ce_in_ladder_10_150_step10": int(mq["ce_in_bafg_ladder"].sum()),
        "qtof_ce_values": {str(k): v for k, v in counts(mq["collision_energy"].round(2)).items()},
        "keys_with_qtof_ce_ge_110": int(mq.loc[mq["collision_energy"] >= 110, "k"].nunique()),
    }
    # all MSG QTOF rows at CE 110..150 (BAFG-like high rungs) and how many belong to BAFG keys
    hq = msg[(msg["instrument_type"] == "QTOF") & msg["collision_energy"].round(6).isin({110, 120, 130, 140, 150})]
    hq_bafg = hq["inchikey"].isin(bk) | hq["parent_key"].isin(bk)
    summary["msg_qtof_rows_ce_110_150"] = {"rows": int(len(hq)), "rows_with_bafg_positive_key": int(hq_bafg.sum()),
                                           "keys": int(hq["inchikey"].nunique()),
                                           "keys_that_are_bafg_positive_keys": int(hq.loc[hq_bafg, "inchikey"].nunique()),
                                           "non_bafg_key_rows_source_label": counts(hq.loc[~hq_bafg, "source_label"].fillna("NA"))}
    per_key = mq.groupby("k").agg(msg_qtof_rows=("identifier", "size"),
                                  msg_qtof_ladder_ce=("collision_energy", lambda x: int(x.round(6).isin(LADDER).sum())),
                                  msg_qtof_max_ce=("collision_energy", "max"),
                                  msg_folds=("fold", lambda x: ";".join(sorted(set(x))))).reset_index().rename(columns={"k": "key"})
    agg = agg.merge(per_key, on="key", how="left")

    # mass-based hidden-inclusion linkage: MSG QTOF [M+H]+ rows with CE >= 70 on the 10-step ladder and precursor m/z
    # within 10 ppm of the BAFG parent [M+H]+, whose key differs from the BAFG key.
    sig = msg[(msg["instrument_type"] == "QTOF") & (msg["adduct"] == "[M+H]+")
              & msg["collision_energy"].round(6).isin({70, 80, 90, 100, 110, 120, 130, 140, 150})].copy()
    sig = sig.sort_values("precursor_mz").reset_index(drop=True)
    import numpy as np
    mzs = sig["precursor_mz"].to_numpy()
    link = []
    for r in agg.itertuples(index=False):
        if not np.isfinite(r.mh_mz):
            continue
        tol = r.mh_mz * 10e-6
        lo, hi = np.searchsorted(mzs, r.mh_mz - tol), np.searchsorted(mzs, r.mh_mz + tol, side="right")
        if hi <= lo:
            continue
        s = sig.iloc[lo:hi]
        for k2, g in s.groupby("parent_key"):
            if k2 == r.key:
                continue
            link.append({"bafg_key": r.key, "bafg_formula": r.parent_formula, "bafg_in_msg15_any_route": r.in_msg15_any_route,
                         "bafg_any_record_in_2023_11": r.any_record_in_2023_11, "msg_parent_key": k2,
                         "msg_formula": g["formula"].iloc[0], "msg_rows_ce70_150": int(len(g)),
                         "msg_distinct_ce70_150": int(g["collision_energy"].round(6).nunique()),
                         "same_formula": g["formula"].iloc[0] == r.parent_formula,
                         "msg_key_is_other_bafg_key": k2 in bk, "msg_folds": ";".join(sorted(set(g["fold"])))})
    ldf = pd.DataFrame(link)
    ldf.to_csv(OUT / "c10_msg_mass_linkage.csv", index=False)
    if len(ldf):
        strong = ldf[(ldf["msg_distinct_ce70_150"] >= 5) & ldf["same_formula"] & ~ldf["msg_key_is_other_bafg_key"]]
        agg["hidden_msg_candidate_strong"] = agg["key"].isin(set(strong["bafg_key"]))
        any_same = ldf[ldf["same_formula"] & ~ldf["msg_key_is_other_bafg_key"]]
        agg["hidden_msg_candidate_any_same_formula"] = agg["key"].isin(set(any_same["bafg_key"]))
    else:
        agg["hidden_msg_candidate_strong"] = False
        agg["hidden_msg_candidate_any_same_formula"] = False
    summary["mass_linkage"] = {
        "rule": "MSG1.5 rows with instrument QTOF, adduct [M+H]+, CE in {70..150 step 10}, precursor_mz within 10 ppm of "
                "BAFG parent [M+H]+, MSG parent key != BAFG key; 'strong' = same parent formula, >= 5 distinct such CE "
                "values, and the MSG key is not itself a BAFG positive key",
        "msg_signature_rows": int(len(sig)), "links": int(len(ldf)),
        "bafg_keys_with_strong_candidate": int(agg["hidden_msg_candidate_strong"].sum()),
        "bafg_keys_with_strong_candidate_not_in_msg_by_key": int((agg["hidden_msg_candidate_strong"] & ~agg["in_msg15_any_route"]).sum()),
        "bafg_keys_with_same_formula_any": int(agg["hidden_msg_candidate_any_same_formula"].sum()),
        "bafg_keys_with_same_formula_any_not_in_msg_by_key": int((agg["hidden_msg_candidate_any_same_formula"] & ~agg["in_msg15_any_route"]).sum()),
    }
    agg.to_csv(OUT / "c10_compounds_screen.csv", index=False)

    # ------------------------------------------------------------ coverage of BAFG 2023.11 compounds by MSG
    a23 = agg[agg["any_record_in_2023_11"]]
    new = agg[~agg["any_record_in_2023_11"]]
    summary["positive_compounds"] = {
        "keys": int(len(agg)), "scaffold_groups": int(agg["scaffold_group"].nunique()),
        "keys_any_record_in_2023_11": int(len(a23)), "keys_only_post_2023_11": int(len(new)),
        "keys_mixed_2023_11_and_new_records": int((agg["any_record_in_2023_11"] & ~agg["all_records_in_2023_11"]).sum()),
        "in_msg15_any_route__2023_11_keys": int(a23["in_msg15_any_route"].sum()),
        "in_msg15_any_route__post_2023_11_only_keys": int(new["in_msg15_any_route"].sum()),
        "n_distinct_ce_distribution": {str(k): v for k, v in counts(agg["n_distinct_ce"]).items()},
        "ce_value_sets_top": counts(agg["ce_values"]) if agg["ce_values"].nunique() < 30 else
        dict(Counter(agg["ce_values"]).most_common(15)),
        "charge_neutral_parent_keys": int(agg["charge_neutral_parent"].sum()),
        "in_range_keys": int(agg["in_range_70_1042_6"].sum()),
    }

    # ------------------------------------------------------------ exclusion cascade and pools
    def pool(mask, label):
        s = agg[mask]
        sgc = s.groupby("scaffold_group")["key"].nunique().sort_values(ascending=False)
        return {"label": label, "keys": int(len(s)), "scaffold_groups": int(s["scaffold_group"].nunique()),
                "acyclic_keys": int(s["scaffold_group"].str.startswith("__ACYCLIC__").sum()),
                "singleton_scaffold_groups": int((sgc == 1).sum()),
                "largest_scaffold_group_key_counts": [int(x) for x in sgc.head(8).values],
                "largest_scaffold_groups": [str(x) for x in sgc.head(5).index],
                "records": int(s["n_records"].sum()),
                "keys_ge_2_ce": int((s["n_distinct_ce"] >= 2).sum()), "keys_ge_10_ce": int((s["n_distinct_ce"] >= 10).sum()),
                "keys_any_record_in_2023_11": int(s["any_record_in_2023_11"].sum()),
                "keys_charge_neutral": int(s["charge_neutral_parent"].sum()),
                "keys_in_range": int(s["in_range_70_1042_6"].sum()),
                "keys_hidden_msg_candidate_strong": int(s["hidden_msg_candidate_strong"].sum()),
                "keys_hidden_msg_candidate_same_formula": int(s["hidden_msg_candidate_any_same_formula"].sum()),
                "mh_mz_min_max": [float(s["mh_mz"].min()), float(s["mh_mz"].max())] if len(s) else None}

    k_msg = agg["in_msg15_any_route"]
    k_muru_min = agg["in_muru_exposed_populations"] | agg["in_muru_dev"]
    k_muru_full = k_muru_min | agg["in_muru_registry"] | agg["in_muru_exposed_union"]
    k_pr7, k_cmp = agg["in_pr7"], agg["in_comparator"]
    sg_mpc = agg["sg_in_muru_registry"] | agg["sg_in_muru_dev"] | agg["sg_in_pr7"] | agg["sg_in_comparator"]
    base = agg["charge_neutral_parent"]
    q = base & agg["in_range_70_1042_6"] & (agg["n_distinct_ce"] >= 2)
    summary["criterion_key_overlap_positive_keys"] = {
        "n_keys": int(len(agg)),
        "in_muru_exposed_populations_or_dev": int(k_muru_min.sum()), "in_muru_full_registry_or_union": int(k_muru_full.sum()),
        "in_pr7": int(k_pr7.sum()), "in_comparator": int(k_cmp.sum()), "in_msg15_any_route": int(k_msg.sum()),
        "in_msg15_simchallenge": int(agg["in_msg15_simchallenge"].sum()),
        "sg_in_muru_registry_or_dev": int((agg["sg_in_muru_registry"] | agg["sg_in_muru_dev"]).sum()),
        "sg_in_pr7": int(agg["sg_in_pr7"].sum()), "sg_in_comparator": int(agg["sg_in_comparator"].sum()),
        "sg_in_msg15": int(agg["sg_in_msg15"].sum()),
    }
    summary["pools"] = [
        pool(agg["key"].notna(), "Q0 all positive-mode BAFG keys"),
        pool(base, "Q1 charge-neutral parent (recorded formula uncharged, parent charge 0)"),
        pool(base & ~k_msg, "Q1b = Q1 and key not in MassSpecGym 1.5 (either key route)"),
        pool(base & ~k_msg & ~k_muru_min & ~k_pr7 & ~k_cmp,
             "Q2 = Q1, key not in MSG1.5, MURU exposed populations/dev, PR7, comparator"),
        pool(base & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp, "Q3 = Q2 and key not in the full MURU exposure registry"),
        pool(base & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp & ~sg_mpc,
             "Q4 = Q3 and scaffold group not in MURU registry/dev, PR7, comparator groups"),
        pool(base & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp & ~sg_mpc & ~agg["sg_in_msg15"],
             "Q5 = Q4 and scaffold group not in any MSG1.5 scaffold group (strict)"),
        pool(q & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp & ~sg_mpc, "Q6 = Q4 with [M+H]+ 70-1042.6 and >= 2 CE"),
        pool(q & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp & ~sg_mpc & ~agg["hidden_msg_candidate_any_same_formula"],
             "Q7 = Q6 and no same-formula MSG QTOF [M+H]+ CE-ladder mass link (hidden-inclusion screen)"),
        pool(q & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp & ~sg_mpc & ~agg["sg_in_msg15"],
             "Q8 = Q5 with [M+H]+ 70-1042.6 and >= 2 CE"),
    ]
    # element census of Q6
    q6 = agg[q & ~k_msg & ~k_muru_full & ~k_pr7 & ~k_cmp & ~sg_mpc]
    el = pos.drop_duplicates("key").set_index("key")["elements"]
    summary["q6_elements_keys"] = counts(e for k in q6["key"] for e in str(el.get(k, "")).split(";") if e)
    summary["q6_any_record_in_2023_11"] = int(q6["any_record_in_2023_11"].sum())

    # negative mode for completeness
    neg = df[(df["ion_mode"] == "NEGATIVE") & df["key"].notna()]
    summary["negative_mode"] = {"records": int(len(neg)), "keys": int(neg["key"].nunique()),
                                "keys_also_positive": int(len(set(neg["key"]) & bk))}

    (OUT / "c10_screen_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("c10_*"))}
    (OUT / "output_manifest_sha256.json").write_text(json.dumps(man, indent=1))
    print(json.dumps(summary, indent=1, default=str)[:20000])


if __name__ == "__main__":
    main()
