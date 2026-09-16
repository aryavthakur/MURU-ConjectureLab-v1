"""C07 screen (CE interface adjudication, task S7): metadata-only overlap and feasibility screen of the mFam consortium
MassBank contribution (MassBank release 2025.10, contributor mFam; Metabolomics 2026 22:114, PMC13328316).

Inputs (metadata only, fetched by screen_c07_mfam_fetch.py; every object is in downloads_register.jsonl):
  downloads/massbank_api/search_mFam__<INSTRUMENT_TYPE>__<ION_MODE>.json   accession partition (MassBank3 API)
  downloads/massbank_export_jsonld/export_metadata_jsonld.jsonl.gz          record title + compound identity per accession
  downloads/github_codesearch/*.json                                        GitHub code-search header FRAGMENTS
                                                                            (AC$INSTRUMENT, COLLISION_ENERGY lines)
  downloads/mfam_contributions_repo/mFam_master_raw.csv                     paper Fig. 3 accession/SMILES table (cross-check)
No record file, spectrum or peak list is read. No model is run.

Exclusion sets and the MURU key/scaffold definition come from task P5
(artifacts/ce_interface_adjudication/exclusion/, scripts/ce_interface_adjudication/scaffold_key.py).

"Sub-collection" = accession lab code MCxx (MSBNK-mFam-MCxx_nnnnnn). The paper's 47 datasets are not exposed per record.

Outputs in artifacts/ce_interface_adjudication/screen/c07_mfam/:
  c07_records.csv            one row per accession: partition, title fields, CE parse, instrument model, key, group
  c07_lab_profile.csv        one row per lab x instrument_type x ion_mode: models, CE strings, adducts, counts
  c07_orbitrap_pos_mh_compounds.csv  one row per (key) in the Orbitrap positive [M+H]+ subset with exclusion flags
  c07_all_compounds.csv      one row per key over all mFam records with exclusion flags
  c07_screen_summary.json    counts per criterion
"""
from __future__ import annotations

import glob
import gzip
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors, inchi, rdMolDescriptors

W = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
sys.path.insert(0, str(W / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

A = W / "artifacts/ce_interface_adjudication"
E = A / "exclusion"
OUT = A / "screen/c07_mfam"
DL = OUT / "downloads"
PROTON = 1.007276
DEV_MH_RANGE = (70.0, 1042.6)  # P5 note section 4
ORBI_TYPES = {"LC-ESI-ITFT", "LC-ESI-QFT", "APCI-ITFT"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def keys(name: str) -> set[str]:
    return {l.strip() for l in (E / name).read_text().splitlines() if l.strip()}


TITLE_RE = re.compile(r"^(?P<name>.*); (?P<itype>[A-Za-z0-9-]+); (?P<mstype>MS\d?); (?P<rest>.*)$")


def parse_title(t: str) -> dict:
    m = TITLE_RE.match(t)
    if not m:
        return {"t_name": None, "t_itype": None, "t_ce": None, "t_res": None, "t_adduct": None}
    fields = [f.strip() for f in m.group("rest").split(";")]
    ce = next((f[3:].strip() for f in fields if f.startswith("CE:")), None)
    res = next((f[2:].strip() for f in fields if f.startswith("R=")), None)
    other = [f for f in fields if f and not f.startswith("CE:") and not f.startswith("R=")]
    return {"t_name": m.group("name"), "t_itype": m.group("itype"), "t_ce": ce, "t_res": res,
            "t_adduct": other[-1] if other else None}


NUM = r"-?\d+(?:\.\d+)?"


def classify_ce(s: str | None) -> tuple[str, str]:
    """Return (form, values) for a MassBank COLLISION_ENERGY string. Pure string classification, no unit inference."""
    if not isinstance(s, str) or not s.strip():
        return "missing", ""
    x = s.strip()
    nums = re.findall(NUM, x)
    low = x.lower()
    unit = ("nce" if "nce" in low else "percent" if "%" in x else "eV" if "ev" in low else
            "V" if re.search(r"\dv\b|\d\s*v$", low) else "none")
    prefix = "HCD" if low.startswith("hcd") else "CID" if low.startswith("cid") else ""
    if len(nums) == 1:
        form = "single"
    elif re.search(NUM + r"\s*[-:]\s*" + NUM, x.replace("-10", "m10")) or "ramp" in low:
        form = "range_or_ramp"
    else:
        form = "list_or_stepped"
    return f"{form}|unit={unit}|prefix={prefix or 'none'}", ",".join(nums)


def main() -> int:
    # ---------------------------------------------------------------- partition from MassBank3 API search responses
    part = {}
    part_files = sorted(glob.glob(str(DL / "massbank_api/search_mFam__*.json")))
    for f in part_files:
        _, it, mode = os.path.basename(f)[:-5].split("__")
        for r in json.load(open(f))["data"]:
            assert r["accession"] not in part, r["accession"]
            part[r["accession"]] = (it, mode)
    browse = json.load(open(DL / "massbank_api/browse_mFam.json"))

    # ---------------------------------------------------------------- JSON-LD
    jl = DL / "massbank_export_jsonld/export_metadata_jsonld.jsonl.gz"
    recs = []
    for line in gzip.open(jl, "rt"):
        r = json.loads(line)
        if r["status"] != 200:
            recs.append({"accession": r["accession"], "jsonld_status": r["status"]})
            continue
        body = r["body"]
        ds = next(x for x in body if x.get("@type") == "Dataset")
        cs = next(x for x in body if x.get("@type") == "ChemicalSubstance")
        me = (cs.get("hasBioChemEntityPart") or [{}])[0]
        d = {"accession": r["accession"], "jsonld_status": 200, "title": ds.get("name"),
             "date_published": ds.get("datePublished"), "license": ds.get("license"),
             "smiles": me.get("smiles"), "inchi": me.get("inChI"), "recorded_inchikey": me.get("inChIKey"),
             "recorded_formula": me.get("molecularFormula"), "recorded_mono": me.get("monoisotopicMolecularWeight")}
        d.update(parse_title(ds.get("name") or ""))
        recs.append(d)
    df = pd.DataFrame(recs)
    df["lab"] = df.accession.str.extract(r"MSBNK-mFam-(MC\d+)_")[0]
    df["instrument_type"] = df.accession.map(lambda a: part.get(a, (None, None))[0])
    df["ion_mode"] = df.accession.map(lambda a: part.get(a, (None, None))[1])
    cls = df.t_ce.map(classify_ce)
    df["ce_form"] = [c[0] for c in cls]
    df["ce_numbers"] = [c[1] for c in cls]

    # ---------------------------------------------------------------- code-search fragments (instrument model, CE line)
    model, ce_line, frag_mode, frag_src = {}, {}, {}, Counter()
    cs_files = sorted(glob.glob(str(DL / "github_codesearch/*.json")))
    for f in cs_files:
        o = json.load(open(f))
        for h in o["hits"]:
            acc = h["path"].split("/")[-1][:-4]
            for fr in h["fragments"]:
                for ln in fr.splitlines():
                    if ln.startswith("AC$INSTRUMENT: "):
                        model[acc] = ln[len("AC$INSTRUMENT: "):].strip()
                    elif ln.startswith("AC$MASS_SPECTROMETRY: COLLISION_ENERGY "):
                        ce_line[acc] = ln[len("AC$MASS_SPECTROMETRY: COLLISION_ENERGY "):].strip()
                    elif ln.startswith("AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE "):
                        frag_mode[acc] = ln[len("AC$MASS_SPECTROMETRY: FRAGMENTATION_MODE "):].strip()
        frag_src[os.path.basename(f)] = o["n_hits"]
    df["instrument_model_codesearch"] = df.accession.map(model)
    df["ce_line_codesearch"] = df.accession.map(ce_line)
    df["fragmentation_mode_codesearch"] = df.accession.map(frag_mode)
    df["ce_title_equals_line"] = [(a == b) if isinstance(b, str) else None for a, b in zip(df.t_ce, df.ce_line_codesearch)]

    # ---------------------------------------------------------------- identity
    ids = {}
    for smi in df.smiles.dropna().unique():
        key, grp = SK.key_and_group(smi)
        m = SK.parent_mol(smi)
        m0 = Chem.MolFromSmiles(smi)
        ids[smi] = {"key": key, "scaffold_group": grp,
                    "parent_formula": rdMolDescriptors.CalcMolFormula(m) if m is not None else None,
                    "parent_mono": Descriptors.ExactMolWt(m) if m is not None else None,
                    "parent_formal_charge": Chem.GetFormalCharge(m) if m is not None else None,
                    "n_fragments_raw": len(Chem.GetMolFrags(m0)) if m0 is not None else None,
                    "elements": ";".join(sorted({a.GetSymbol() for a in m.GetAtoms()})) if m is not None else ""}
    for col in ("key", "scaffold_group", "parent_formula", "parent_mono", "parent_formal_charge", "n_fragments_raw",
                "elements"):
        df[col] = df.smiles.map(lambda s: ids.get(s, {}).get(col) if isinstance(s, str) else None)
    df["recorded_block"] = df.recorded_inchikey.map(SK.first_block)

    def inchi_block(s):
        if not isinstance(s, str) or not s.startswith("InChI="):
            return None
        k = inchi.InchiToInchiKey(s)
        return k.split("-")[0] if k else None

    df["inchi_block"] = df.inchi.map(inchi_block)
    df["mh_mz"] = df.parent_mono + PROTON
    df["mh_in_dev_range"] = df.mh_mz.between(*DEV_MH_RANGE)

    # cross-check against the paper's accession/SMILES table
    xc = pd.read_csv(DL / "mfam_contributions_repo/mFam_master_raw.csv", header=None, dtype=str,
                     names=["accession", "smiles_fig3", "name_fig3", "ion_mode_fig3"])
    df = df.merge(xc, on="accession", how="left")
    df["fig3_smiles_key"] = df.smiles_fig3.map(lambda s: SK.key_and_group(s)[0] if isinstance(s, str) else None)
    df["fig3_key_agrees"] = [(a == b) if isinstance(b, str) else None for a, b in zip(df.key, df.fig3_smiles_key)]

    # ---------------------------------------------------------------- exclusion sets
    msg_all = keys("msg15_keys_all.txt") | keys("msg15_parent_keys_all.txt")
    msg_fold = {f: keys(f"msg15_keys_{f}.txt") | keys(f"msg15_parent_keys_{f}.txt") for f in ("train", "val", "test")}
    msg_sim = keys("msg15_simchallenge_keys_all.txt")
    msg_groups = keys("msg15_scaffold_groups_all.txt")
    reg = keys("muru_exposure_registry_keys.txt")
    reg_direct = keys("muru_exposure_registry_keys_direct_reason.txt")
    reg_groups = keys("muru_exposure_registry_scaffold_groups.txt")
    pops = {p.name[len("muru_exposure_registry_population_"):-len("_keys.txt")]: keys(p.name)
            for p in sorted(E.glob("muru_exposure_registry_population_*_keys.txt"))}
    s2, s2_groups = keys("msnlib_study2_population_keys.txt"), keys("msnlib_study2_population_scaffold_groups.txt")
    cmp_, cmp_groups = keys("comparator_common_population_keys.txt"), keys("comparator_common_population_scaffold_groups.txt")
    msn9, msn4 = keys("msnlib_9lib_keys.txt"), keys("msnlib_v1_0_4lib_keys.txt")
    mm2 = keys("multims2_reserved_validation_secondary_keys.txt")

    def cand_of(r):
        return {k for k in (r.key, r.recorded_block, r.inchi_block) if isinstance(k, str)}

    flags = []
    for r in df.itertuples(index=False):
        c = cand_of(r)
        g = r.scaffold_group if isinstance(r.scaffold_group, str) else None
        flags.append({
            "in_msg15_any": bool(c & msg_all), "msg15_folds": ";".join(sorted(f for f, s in msg_fold.items() if c & s)),
            "in_msg15_simchallenge": bool(c & msg_sim), "scaffold_in_msg15": (g in msg_groups) if g else None,
            "in_muru_registry": bool(c & reg), "in_muru_registry_direct": bool(c & reg_direct),
            "muru_exposed_populations": ";".join(sorted(n for n, s in pops.items() if c & s)),
            "scaffold_in_muru_registry": (g in reg_groups) if g else None,
            "in_study2_pop": bool(c & s2), "scaffold_in_study2_pop": (g in s2_groups) if g else None,
            "in_comparator_pop": bool(c & cmp_), "scaffold_in_comparator_pop": (g in cmp_groups) if g else None,
            "in_msnlib_9lib": bool(c & msn9), "in_msnlib_v1_0": bool(c & msn4), "in_multims2_reserved": bool(c & mm2),
        })
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(flags)], axis=1)

    # hidden-identity proxy: MSG 1.5 distinct parent keys with the same parent formula (and same scaffold group)
    j = pd.read_parquet(A / "massspecgym15_identity_metadata_joined.parquet", columns=["identifier", "formula"])
    rk = pd.read_parquet(E / "msg15_row_keys.parquet", columns=["identifier", "parent_key", "scaffold_group"])
    fk = j.merge(rk, on="identifier").dropna(subset=["parent_key"]).drop_duplicates(["parent_key"])
    by_f = fk.groupby("formula").parent_key.nunique()
    by_fg = fk.groupby(["formula", "scaffold_group"]).parent_key.nunique()
    df["msg15_keys_same_formula"] = [int(by_f.get(f, 0)) if isinstance(f, str) else 0 for f in df.parent_formula]
    df["msg15_keys_same_formula_and_scaffold"] = [int(by_fg.get((f, g), 0)) if isinstance(f, str) else 0
                                                  for f, g in zip(df.parent_formula, df.scaffold_group)]

    # ---------------------------------------------------------------- subsets
    df["is_orbitrap_type"] = df.instrument_type.isin(ORBI_TYPES)
    df["is_pos"] = df.ion_mode.eq("POSITIVE")
    df["is_mh"] = df.t_adduct.eq("[M+H]+")
    df["is_esi"] = ~df.instrument_type.fillna("").str.startswith("APCI")
    df["ce_single_numeric"] = df.ce_form.str.startswith("single|")

    lab_rows = []
    for (lab, it, mode), s in df.groupby(["lab", "instrument_type", "ion_mode"]):
        per_key_ce = s[s.key.notna()].groupby(["key", "t_adduct"]).t_ce.nunique()
        lab_rows.append({
            "lab": lab, "instrument_type": it, "ion_mode": mode, "n_records": len(s), "n_keys": s.key.nunique(),
            "n_mh_records": int(s.is_mh.sum()), "n_mh_keys": s[s.is_mh].key.nunique(),
            "instrument_models": json.dumps(dict(Counter(s.instrument_model_codesearch.fillna("NOT_FETCHED")))),
            "ce_strings_top": json.dumps(dict(Counter(s.t_ce.fillna("NA")).most_common(12))),
            "n_distinct_ce_strings": s.t_ce.nunique(),
            "ce_forms": json.dumps(dict(Counter(s.ce_form))),
            "adducts_top": json.dumps(dict(Counter(s.t_adduct.fillna("NA")).most_common(6))),
            "max_distinct_ce_per_key_adduct": int(per_key_ce.max()) if len(per_key_ce) else 0,
            "n_key_adduct_with_ge3_distinct_ce": int((per_key_ce >= 3).sum()),
            "n_key_adduct_with_ge2_distinct_ce": int((per_key_ce >= 2).sum()),
            "resolution_strings": json.dumps(dict(Counter(s.t_res.fillna("NA")).most_common(4))),
            "date_published_range": f"{s.date_published.min()}..{s.date_published.max()}",
            "licenses": json.dumps(dict(Counter(s.license.fillna("NA")))),
            "codesearch_ce_line_coverage": int(s.ce_line_codesearch.notna().sum()),
            "codesearch_fragmentation_mode": json.dumps(dict(Counter(s.fragmentation_mode_codesearch.dropna()))),
        })
    labp = pd.DataFrame(lab_rows)

    orb = df[df.is_orbitrap_type & df.is_pos & df.is_mh & df.key.notna()]
    per = []
    for key, s in orb.groupby("key"):
        by_lab = s.groupby("lab").t_ce.apply(lambda x: sorted(set(x.fillna("NA"))))
        single_by_lab = s[s.ce_single_numeric].groupby("lab").ce_numbers.apply(lambda x: sorted(set(x)))
        r0 = s.iloc[0]
        per.append({
            "key": key, "scaffold_group": r0.scaffold_group, "name": r0.t_name, "smiles": r0.smiles,
            "labs": ";".join(sorted(s.lab.unique())), "instrument_types": ";".join(sorted(s.instrument_type.unique())),
            "instrument_models": ";".join(sorted(s.instrument_model_codesearch.fillna("NOT_FETCHED").unique())),
            "n_records": len(s), "ce_strings_by_lab": json.dumps({k: v for k, v in by_lab.items()}),
            "max_distinct_ce_strings_within_one_lab": int(max(len(v) for v in by_lab.values)),
            "max_distinct_single_numeric_ce_within_one_lab": int(max((len(v) for v in single_by_lab.values), default=0)),
            "mh_in_dev_range": bool(r0.mh_in_dev_range), "parent_formal_charge": r0.parent_formal_charge,
            "n_fragments_raw": r0.n_fragments_raw,
            **{c: r0[c] for c in ("in_msg15_any", "msg15_folds", "in_msg15_simchallenge", "scaffold_in_msg15",
                                  "in_muru_registry", "in_muru_registry_direct", "muru_exposed_populations",
                                  "scaffold_in_muru_registry", "in_study2_pop", "scaffold_in_study2_pop",
                                  "in_comparator_pop", "scaffold_in_comparator_pop", "in_msnlib_9lib",
                                  "in_msnlib_v1_0", "in_multims2_reserved", "msg15_keys_same_formula",
                                  "msg15_keys_same_formula_and_scaffold")},
        })
    oc = pd.DataFrame(per)

    allc = df[df.key.notna()].sort_values("accession").drop_duplicates("key").copy()
    allc["labs"] = allc.key.map(df[df.key.notna()].groupby("key").lab.apply(lambda x: ";".join(sorted(set(x)))))

    def ladder(t: pd.DataFrame) -> dict:
        f = lambda c: t[c].fillna(False).astype(bool)  # noqa: E731
        A_ = ~f("in_muru_registry") & ~f("in_study2_pop") & ~f("in_comparator_pop")
        B_ = A_ & ~f("in_msg15_any")
        C_ = B_ & ~f("scaffold_in_muru_registry") & ~f("scaffold_in_study2_pop") & ~f("scaffold_in_comparator_pop")
        D_ = C_ & ~f("scaffold_in_msg15")
        L1 = t.muru_exposed_populations.fillna("").eq("") & ~f("in_study2_pop") & ~f("in_comparator_pop")
        L2 = L1 & ~f("in_msg15_any")
        L3 = L2 & ~f("scaffold_in_study2_pop") & ~f("scaffold_in_comparator_pop")

        def cnt(m):
            s = t[m]
            return {"keys": int(s.key.nunique()), "scaffold_groups": int(s.scaffold_group.nunique()),
                    "acyclic_groups": int(s.scaffold_group.fillna("").str.startswith("__ACYCLIC__").sum()),
                    "groups_with_ge2_keys": int((s.groupby("scaffold_group").key.nunique() >= 2).sum())}
        return {"all": cnt(pd.Series(True, index=t.index)), "A_keys_not_in_registry_pr7_cmp": cnt(A_),
                "B_A_and_not_in_msg15": cnt(B_), "C_B_and_scaffold_not_in_registry_pr7_cmp": cnt(C_),
                "D_C_and_scaffold_not_in_msg15": cnt(D_), "L1_keys_not_in_exposed_pop_union_pr7_cmp": cnt(L1),
                "L2_L1_and_not_in_msg15": cnt(L2), "L3_L2_and_scaffold_not_in_pr7_cmp": cnt(L3),
                "overlap_keys": {
                    "muru_registry_full": int(t[f("in_muru_registry")].key.nunique()),
                    "muru_registry_direct_reason": int(t[f("in_muru_registry_direct")].key.nunique()),
                    "muru_exposed_population_union": int(t[t.muru_exposed_populations.fillna("").ne("")].key.nunique()),
                    "muru_exposed_populations_hit": dict(Counter(p for s in t.muru_exposed_populations.fillna("")
                                                                 for p in s.split(";") if p)),
                    "pr7_study2": int(t[f("in_study2_pop")].key.nunique()),
                    "comparator_common": int(t[f("in_comparator_pop")].key.nunique()),
                    "msg15_any": int(t[f("in_msg15_any")].key.nunique()),
                    "msg15_by_fold": dict(Counter(x for s in t.msg15_folds.fillna("") for x in s.split(";") if x)),
                    "msg15_simchallenge": int(t[f("in_msg15_simchallenge")].key.nunique()),
                    "msnlib_9lib": int(t[f("in_msnlib_9lib")].key.nunique()),
                    "msnlib_v1_0": int(t[f("in_msnlib_v1_0")].key.nunique()),
                    "multims2_reserved": int(t[f("in_multims2_reserved")].key.nunique())},
                "B_hidden_identity_proxy": {
                    "B_keys_msg15_same_formula": int((t[B_].msg15_keys_same_formula > 0).sum()),
                    "B_keys_msg15_same_formula_and_scaffold": int((t[B_].msg15_keys_same_formula_and_scaffold > 0).sum())},
                "_masks": {"B": B_, "C": C_, "L2": L2}}

    lad_all = ladder(allc)
    lad_orb = ladder(oc) if len(oc) else {}
    # multi-energy subset of the Orbitrap positive [M+H]+ compounds
    me3 = oc[oc.max_distinct_single_numeric_ce_within_one_lab >= 3] if len(oc) else oc
    lad_me3 = ladder(me3) if len(me3) else {}
    me3_detail = {}
    if len(me3):
        mm = ladder(me3)["_masks"]
        me3_detail = {
            "labs": dict(Counter(l for x in me3.labs for l in x.split(";"))),
            "instrument_models": dict(Counter(me3.instrument_models)),
            "ce_strings_by_lab_examples": dict(Counter(me3.ce_strings_by_lab)),
            "C_pass": me3[mm["C"]][["key", "name", "scaffold_group", "labs", "ce_strings_by_lab",
                                    "msg15_keys_same_formula", "msg15_keys_same_formula_and_scaffold"]].to_dict("records"),
            "L2_pass": me3[mm["L2"]][["key", "name", "scaffold_group", "labs", "in_muru_registry",
                                      "scaffold_in_muru_registry"]].to_dict("records"),
        }
    # MSG 1.5 acquisition-signature check for the multi-energy lab ladder (metadata only)
    mem = pd.read_parquet(E / "msg_row_msnlib_membership.parquet",
                          columns=["inchikey14", "parent_key14", "adduct", "instrument_type", "collision_energy"])
    sig = {}
    if len(me3):
        # energies only from the lab list(s) that supply >= 3 distinct values for the compound
        ladder_vals = sorted({float(v) for x in me3.ce_strings_by_lab for vs in json.loads(x).values()
                              if len(vs) >= 3 for v in vs if re.fullmatch(NUM, v)})
        me3_detail["labs_supplying_ge3_energies"] = dict(Counter(lab for x in me3.ce_strings_by_lab
                                                                 for lab, vs in json.loads(x).items() if len(vs) >= 3))
        me3_detail["labs_co_occurring_any"] = me3_detail.pop("labs")
        o = mem[(mem.instrument_type == "Orbitrap") & (mem.adduct == "[M+H]+") & mem.collision_energy.notna()]
        kset = o.groupby("parent_key14").collision_energy.apply(lambda x: frozenset(x.round(4)))
        full = kset[kset.apply(lambda z: set(ladder_vals) <= z)]
        me3keys = set(me3.key)
        allo = mem[(mem.instrument_type == "Orbitrap") & mem.collision_energy.notna()].collision_energy
        sig = {"ladder_values": ladder_vals,
               "msg15_orbitrap_rows_ce_gt_90": int((allo > 90).sum()), "msg15_orbitrap_ce_max": float(allo.max()),
               "msg15_orbitrap_mh_keys_with_full_ladder": int(len(full)),
               "of_which_multi_energy_mfam_keys": int(len(set(full.index) & me3keys)),
               "msg15_orbitrap_mh_rows_ce_100": int((o.collision_energy == 100).sum()),
               "msg15_orbitrap_any_adduct_rows_ce_100": int(((mem.instrument_type == "Orbitrap") &
                                                             (mem.collision_energy == 100)).sum()),
               "multi_energy_mfam_keys_in_msg15_with_orbitrap_mh_rows": int(len(me3keys & set(o.parent_key14))),
               "multi_energy_mfam_keys_in_msg15_orbitrap_mh_ce_hist_top": dict(Counter(
                   o[o.parent_key14.isin(me3keys)].collision_energy.round(3)).most_common(15))}
    for d in (lad_all, lad_orb, lad_me3):
        d.pop("_masks", None)
    if len(oc):
        mC = ladder(oc)["_masks"]["C"]
        oc["pass_C"] = mC
        oc["pass_B"] = ladder(oc)["_masks"]["B"]

    summary = {
        "script": "scripts/ce_interface_adjudication/screen_c07_mfam.py", "rdkit": rdBase.rdkitVersion,
        "frozen_rdkit": SK.FROZEN_RDKIT,
        "inputs": {"jsonld_gz_sha256": sha(jl), "partition_files": len(part_files),
                   "codesearch_files": {os.path.basename(f): sha(Path(f)) for f in cs_files},
                   "fig3_table_sha256": sha(DL / "mfam_contributions_repo/mFam_master_raw.csv"),
                   "exclusion_manifest_sha256": sha(E / "exclusion_manifest.json")},
        "browse_counts": {k: {x["value"]: x["count"] for x in v if x.get("count")} for k, v in browse.items()},
        "n_records_partition": len(part), "n_records_jsonld": int(len(df)),
        "jsonld_status": dict(Counter(map(str, df.jsonld_status))),
        "title_parse_failures": int(df.t_itype.isna().sum()),
        "title_itype_vs_partition_disagree": int((df.t_itype.notna() & (df.t_itype != df.instrument_type)).sum()),
        "n_key_formed_records": int(df.key.notna().sum()), "n_distinct_keys_all": int(df.key.nunique()),
        "n_scaffold_groups_all": int(df.scaffold_group.nunique()),
        "key_vs_recorded_inchikey_block": dict(Counter(map(str, (df.key == df.recorded_block)))),
        "key_vs_inchi_block": dict(Counter(map(str, (df.key == df.inchi_block)))),
        "fig3_key_agrees": dict(Counter(map(str, df.fig3_key_agrees))),
        "codesearch_hits_per_file": dict(frag_src),
        "codesearch_ce_line_vs_title": dict(Counter(map(str, df.ce_title_equals_line))),
        "codesearch_fragmentation_mode_values": dict(Counter(df.fragmentation_mode_codesearch.dropna())),
        "date_published_by_lab": {k: [v.min(), v.max()] for k, v in df.groupby("lab").date_published},
        "licenses": dict(Counter(df.license.fillna("NA"))),
        "orbitrap_type_records": int(df.is_orbitrap_type.sum()),
        "orbitrap_pos_records": int((df.is_orbitrap_type & df.is_pos).sum()),
        "orbitrap_pos_mh_records": int((df.is_orbitrap_type & df.is_pos & df.is_mh).sum()),
        "orbitrap_pos_mh_esi_records": int((df.is_orbitrap_type & df.is_pos & df.is_mh & df.is_esi).sum()),
        "orbitrap_pos_mh_keys": int(oc.key.nunique()) if len(oc) else 0,
        "orbitrap_pos_mh_by_lab_records": dict(Counter(df[df.is_orbitrap_type & df.is_pos & df.is_mh].lab)),
        "orbitrap_pos_mh_max_distinct_single_numeric_ce_within_lab_hist":
            dict(Counter(map(int, oc.max_distinct_single_numeric_ce_within_one_lab))) if len(oc) else {},
        "orbitrap_pos_mh_max_distinct_ce_strings_within_lab_hist":
            dict(Counter(map(int, oc.max_distinct_ce_strings_within_one_lab))) if len(oc) else {},
        "all_mfam_records_pos_mh_max_distinct_ce_per_key_lab_hist": dict(Counter(map(int, df[df.is_pos & df.is_mh & df.key.notna()]
                                                                                   .groupby(["key", "lab"]).t_ce.nunique()))),
        "ladder_all_mfam_compounds": lad_all,
        "ladder_orbitrap_pos_mh_compounds": lad_orb,
        "ladder_orbitrap_pos_mh_ge3_single_numeric_ce_within_lab": lad_me3,
        "multi_energy_subset_detail": me3_detail,
        "msg15_signature_check_multi_energy_ladder": sig,
        "orbitrap_pos_mh_pass_C_by_lab": dict(Counter(l for s in oc[oc.pass_C].labs for l in s.split(";"))) if len(oc) else {},
        "orbitrap_pos_mh_pass_C_mh_dev_range_neutral_single":
            int((oc.pass_C & oc.mh_in_dev_range & oc.parent_formal_charge.eq(0) & oc.n_fragments_raw.eq(1)).sum()) if len(oc) else 0,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "c07_records.csv", index=False)
    labp.to_csv(OUT / "c07_lab_profile.csv", index=False)
    oc.to_csv(OUT / "c07_orbitrap_pos_mh_compounds.csv", index=False)
    allc.drop(columns=[c for c in allc.columns if c.startswith("t_") and c not in ("t_name",)]).to_csv(
        OUT / "c07_all_compounds.csv", index=False)
    (OUT / "c07_screen_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
