"""S11 screen, candidate C11: ExpoLib 1.0 (Zenodo 20715576). Step 2: independent re-verification + criteria 1-11.

Runs AFTER screen_c11_expolib.py. It does three things the first pass did not:

  (A) Re-derives every exclusion overlap from the raw downloaded tables, independently of
      c11_compounds_screen.csv, and asserts agreement with the first pass (any disagreement is reported,
      never smoothed over).
  (B) Tautomer- and skeleton-aware re-check of the compound-level exclusions, same method as
      screen_c01_eawag_eq_tautomer.py: the MURU compound key is the first InChIKey block of the parent, which
      is tautomer SENSITIVE, so a key-only exclusion can miss a compound present in a comparison population as
      another tautomer. Candidate matches are accepted only when the molecular FORMULA is identical too.
  (C) Machine-extracts the load-bearing collision-energy / instrument / license / timing evidence from the
      downloaded files, so criteria 5, 7, 10 and 11 rest on parsed strings and not on prose.

Inputs (all already downloaded and registered; no spectra, no model output, no MURU result):
  screen/c11_expolib/downloads/Library_Overview_-_ESI+.xlsx
  screen/c11_expolib/downloads/mzmine_files_extracted/Database_File_mzmine_ESI+.csv
  screen/c11_expolib/downloads/mzmine_files_extracted/20260521_mzmine_batch_ExpoLib1.0_ESI{+,-}_All.mzbatch
  screen/c11_expolib/downloads/mzmine_files_extracted/20260521_mzmine_presets_ExpoLib1.0_ESI+_All.mzmwizard
  screen/c11_expolib/downloads/11306_2026_2481_MOESM1_ESM.xlsx      (paper SI: S1, S2, S5)
  screen/c11_expolib/downloads/zenodo_20715576_record.json, zenodo_18186810_versions.json
  screen/c11_expolib/c11_compounds_screen.csv                       (first pass, for the agreement check)
  exclusion/*                                                       (P5)
  massspecgym15_metadata_columns.parquet, wur_v2/data/compounds.csv,
  wur_v2_confirmation_v2/freeze/validation_population.csv, comparator_benchmark/population/common_population.csv

Outputs in artifacts/ce_interface_adjudication/screen/c11_expolib/:
  c11_tautomer_recheck.csv
  c11_criteria.json
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import inchi, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

RDLogger.DisableLog("rdApp.*")

ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
EXC = ADJ / "exclusion"
OUT = ADJ / "screen" / "c11_expolib"
DL = OUT / "downloads"
MZ = DL / "mzmine_files_extracted"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def norm(s) -> str:
    s = unicodedata.normalize("NFKC", str(s)).lower().replace("′", "'").replace("’", "'")
    return re.sub(r"[^a-z0-9]", "", s)


def read_set(name: str) -> set[str]:
    return {x.strip() for x in (EXC / name).read_text().splitlines() if x.strip()}


def keys_for(smiles, enum):
    """(parent_key, taut_key, skel_key, formula) of the MURU parent molecule."""
    pm = SK.parent_mol(smiles) if isinstance(smiles, str) else None
    if pm is None:
        return None, None, None, None
    pk = SK.first_block(inchi.MolToInchiKey(pm) or "") or None
    formula = rdMolDescriptors.CalcMolFormula(pm)
    try:
        tk = SK.first_block(inchi.MolToInchiKey(enum.Canonicalize(pm)) or "") or None
    except Exception:
        tk = None
    try:
        sm = Chem.RWMol(pm)
        for at in sm.GetAtoms():
            at.SetFormalCharge(0)
            at.SetNumExplicitHs(0)
            at.SetNoImplicit(False)
            at.SetIsAromatic(False)
        for bd in sm.GetBonds():
            bd.SetBondType(Chem.BondType.SINGLE)
            bd.SetIsAromatic(False)
        skel = sm.GetMol()
        Chem.SanitizeMol(skel)
        Chem.RemoveStereochemistry(skel)
        sk = SK.first_block(inchi.MolToInchiKey(skel) or "") or None
    except Exception:
        sk = None
    return pk, tk, sk, formula


# ---------------------------------------------------------------- (C) evidence extraction
def extract_evidence() -> dict:
    ev = {}
    rec = json.loads((DL / "zenodo_20715576_record.json").read_text())
    ev["zenodo"] = {
        "record_id": rec.get("id"), "doi": rec.get("doi"), "concept_doi": rec["metadata"].get("conceptdoi"),
        "title": rec["metadata"].get("title"), "publication_date": rec["metadata"].get("publication_date"),
        "created": rec.get("created"), "modified": rec.get("modified"),
        "license": rec["metadata"].get("license"),
        "access_right": rec["metadata"].get("access_right"),
        "n_files": len(rec.get("files", [])),
        "file_names": sorted(f.get("key") for f in rec.get("files", [])),
        "description_ce_sentence": next(
            (s.strip() for s in re.split(r"(?<=\.)\s", re.sub(r"<[^>]+>", " ", rec["metadata"].get("description", "")))
             if "collision energ" in s.lower()), None),
    }
    ver = json.loads((DL / "zenodo_18186810_versions.json").read_text())
    ev["zenodo_versions"] = [
        {"id": h.get("id"), "doi": h.get("doi"), "publication_date": h["metadata"].get("publication_date"),
         "created": h.get("created"), "license": (h["metadata"].get("license") or {}).get("id")}
        for h in sorted(ver.get("hits", {}).get("hits", []), key=lambda x: x.get("created", ""))]

    pres = (MZ / "20260521_mzmine_presets_ExpoLib1.0_ESI+_All.mzmwizard").read_text(errors="replace")
    bat_pos = (MZ / "20260521_mzmine_batch_ExpoLib1.0_ESI+_All.mzbatch").read_text(errors="replace")
    bat_neg = (MZ / "20260521_mzmine_batch_ExpoLib1.0_ESI-_All.mzbatch").read_text(errors="replace")
    ev["instrument_strings"] = {
        "presets_INSTRUMENT_NAME": sorted(set(re.findall(r'INSTRUMENT_NAME">([^<]+)<', pres))),
        "presets_INSTRUMENT": sorted(set(re.findall(r'(?<!_)INSTRUMENT">([^<]+)<', pres))),
        "batch_pos_INSTRUMENT_NAME": sorted(set(re.findall(r'INSTRUMENT_NAME">([^<]+)<', bat_pos))),
        "batch_pos_INSTRUMENT": sorted(set(re.findall(r'(?<!_)INSTRUMENT">([^<]+)<', bat_pos))),
    }

    def wiffs(text):
        return sorted(set(re.findall(r"[0-9A-Za-z_+\-. ]*\.wiff", text)))

    def ce_tokens(names):
        single, spread = set(), set()
        for n in names:
            m = re.search(r"_CES(\d+)-(\d+)_", n)
            if m:
                spread.add(f"{int(m.group(1))}+-{int(m.group(2))}")
                continue
            m = re.search(r"_CE(\d+)_", n)
            if m:
                single.add(int(m.group(1)))
        return sorted(single), sorted(spread)

    pos_files, neg_files = wiffs(bat_pos), wiffs(bat_neg)
    ps, pspread = ce_tokens(pos_files)
    ns, nspread = ce_tokens(neg_files)
    ev["mzmine_imported_raw_files"] = {
        "esi_pos_files": pos_files, "esi_pos_single_ce": ps, "esi_pos_ce_spread": pspread,
        "esi_neg_n_files": len(neg_files), "esi_neg_single_ce": ns, "esi_neg_ce_spread": nspread,
    }

    si = pd.read_excel(DL / "11306_2026_2481_MOESM1_ESM.xlsx", sheet_name=None, header=None)
    s2 = si["S2 - Data Acquisition"]
    flat = ["" if pd.isna(v) else str(v) for v in s2.to_numpy().ravel(order="C")]
    ev["si_s2"] = {
        "sheet_names": sorted(si.keys()),
        "ces_definition_note": next((t for t in flat if "collision energy spread" in t.lower()
                                     and "example" in t.lower()), None),
        "ms_method_ce_cells": [f"{flat[i - 1]} = {flat[i]}" for i in range(1, len(flat))
                               if re.fullmatch(r"\s*(Collision energy ?[+/\-]*\s*\(V\)|Collision energy spread \(V\)|"
                                               r"Declustering potential ?[+/\-]*\s*\(V\)|Spray voltage ?[+/\-]*\s*\(V\))\s*",
                                               flat[i - 1] or "")],
        "acquisition_pos_datafiles": sorted({t for t in flat if re.search(r"_CE[S0-9\-]+_POS", t)}),
    }
    acq = ev["si_s2"]["acquisition_pos_datafiles"]
    acq_single = sorted({int(m.group(1)) for t in acq for m in [re.search(r"_CE(\d+)_POS", t)] if m})
    ev["si_s2"]["acquisition_pos_single_ce"] = acq_single
    ev["si_s2"]["acquisition_pos_single_ce_nonzero_count"] = len([x for x in acq_single if x != 0])
    return ev


# ---------------------------------------------------------------- main
def main() -> None:
    enum = rdMolStandardize.TautomerEnumerator()
    S = {"script": "scripts/ce_interface_adjudication/screen_c11_expolib_criteria.py",
         "generated_utc": datetime.now(timezone.utc).isoformat(), "rdkit": rdBase.rdkitVersion,
         "candidate": "C11 ExpoLib 1.0 (Zenodo 20715576)"}
    S["evidence"] = extract_evidence()

    prev = pd.read_csv(OUT / "c11_compounds_screen.csv")
    S["inputs"] = {"c11_compounds_screen.csv": {"sha256": sha256(OUT / "c11_compounds_screen.csv"),
                                                "rows": int(len(prev))}}

    # ---------- (A) independent re-derivation of identity and overlaps
    ov_raw = pd.read_excel(DL / "Library_Overview_-_ESI+.xlsx", header=None)
    hdr = int(ov_raw.index[ov_raw.iloc[:, 1].astype(str).eq("Compound")][0])
    ov = []
    for i in range(hdr + 1, ov_raw.shape[0]):
        nm = ov_raw.iat[i, 1]
        if isinstance(nm, str) and nm.strip() and not nm.startswith("*"):
            ov.append({"compound": nm, "ce_list": ov_raw.iat[i, 2], "adducts": ov_raw.iat[i, 3],
                       "total_spectra": ov_raw.iat[i, 4], "chimeric": ov_raw.iat[i, 5]})
    ov = pd.DataFrame(ov)
    db = pd.read_csv(MZ / "Database_File_mzmine_ESI+.csv")
    dbn = {}
    for r in db.to_dict("records"):
        dbn.setdefault(norm(r["Compound"]), []).append(r)

    reg = read_set("muru_exposure_registry_keys.txt")
    reg_groups = read_set("muru_exposure_registry_scaffold_groups.txt")
    pr7 = read_set("msnlib_study2_population_keys.txt")
    pr7_groups = read_set("msnlib_study2_population_scaffold_groups.txt")
    comp = read_set("comparator_common_population_keys.txt")
    comp_groups = read_set("comparator_common_population_scaffold_groups.txt")
    msg_all = read_set("msg15_keys_all.txt") | read_set("msg15_parent_keys_all.txt")
    msg_groups = read_set("msg15_scaffold_groups_all.txt")

    rows = []
    for r in ov.itertuples(index=False):
        d = dbn.get(norm(r.compound), [None])[0]
        smi = None
        if d:
            for cand in (d.get("SMILES"), d.get("Isomeric Smiles"), d.get("Canonical Smiles")):
                if isinstance(cand, str) and cand.strip() not in ("", "-", "nan"):
                    smi = cand.strip()
                    break
        pk, tk, sk, formula = keys_for(smi, enum)
        grp = SK.scaffold_group(smi, pk) if (smi and pk) else None
        nmh = sum(int(n) for a, n in re.findall(r"(\[[^\]]+\][+-])\s*\((\d+)\)", str(r.adducts)) if a == "[M+H]+")
        ce_txt = re.sub(r"\d+\s*±\s*\d+\s*\(\d+\)", " ", str(r.ce_list))
        ces = sorted({int(x) for x in re.findall(r"(\d+)\s*\(", ce_txt)})
        rows.append({"compound": r.compound, "smiles": smi, "formula_calc": formula, "parent_key": pk,
                     "taut_key": tk, "skel_key": sk, "scaffold_group": grp, "n_mh_spectra": nmh,
                     "single_ce": ";".join(map(str, ces)), "n_single_ce": len(ces),
                     "chimeric_flag": r.chimeric,
                     "in_muru_registry": bool(pk and pk in reg),
                     "group_in_muru_registry_groups": bool(grp and grp in reg_groups),
                     "in_pr7": bool(pk and pk in pr7), "group_in_pr7": bool(grp and grp in pr7_groups),
                     "in_comparator": bool(pk and pk in comp), "group_in_comparator": bool(grp and grp in comp_groups),
                     "in_msg15": bool(pk and pk in msg_all), "group_in_msg15": bool(grp and grp in msg_groups)})
    c = pd.DataFrame(rows)

    p = prev.set_index("compound")
    agree, dis = {}, []
    for mine, theirs in (("parent_key", "parent_key"), ("scaffold_group", "scaffold_group"),
                         ("n_mh_spectra", "n_mh_spectra"), ("in_muru_registry", "in_muru_registry"),
                         ("in_pr7", "in_pr7_population"), ("in_comparator", "in_comparator_population"),
                         ("in_msg15", "in_msg15_any_fold"), ("group_in_msg15", "group_in_msg15_groups")):
        n_ok = 0
        for _i, row in c.iterrows():
            a, b = row[mine], p.at[row["compound"], theirs]
            same = (pd.isna(a) and pd.isna(b)) or (a == b)
            n_ok += bool(same)
            if not same:
                dis.append({"compound": row["compound"], "field": mine, "pass2": a, "pass1": b})
        agree[mine] = f"{n_ok}/{len(c)}"
    S["pass1_vs_pass2_agreement"] = agree
    S["pass1_vs_pass2_disagreements"] = dis

    # ---------- (B) tautomer / skeleton recheck
    formulas = set(c["formula_calc"].dropna())
    pops, pop_meta = {}, {}
    mm = pd.read_parquet(ADJ / "massspecgym15_metadata_columns.parquet", columns=["smiles"]).drop_duplicates("smiles")
    pop_meta["msg15"] = {"path": "artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet",
                         "unique_smiles": int(len(mm))}
    keep = []
    for s in mm["smiles"]:
        pm = SK.parent_mol(s)
        if pm is not None and rdMolDescriptors.CalcMolFormula(pm) in formulas:
            keep.append(s)
    pops["msg15"] = keep
    for name, rel, col in (("muru_dev_pop", "artifacts/wur_v2/data/compounds.csv", "smiles"),
                           ("pr7", "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv", "smiles"),
                           ("comparator", "artifacts/comparator_benchmark/population/common_population.csv",
                            "model_smiles")):
        df = pd.read_csv(ROOT / rel, usecols=[col]).drop_duplicates(col)
        pop_meta[name] = {"path": rel, "column_read": col, "unique_smiles": int(len(df)),
                          "sha256": sha256(ROOT / rel)}
        keep = []
        for s in df[col]:
            pm = SK.parent_mol(s)
            if pm is not None and rdMolDescriptors.CalcMolFormula(pm) in formulas:
                keep.append(s)
        pops[name] = keep
    for k in pops:
        pop_meta[k]["structures_sharing_a_c11_formula"] = len(pops[k])
    S["tautomer_recheck_populations"] = pop_meta

    idx = {}
    for name, smis in pops.items():
        pk_i, tk_i, sk_i = (collections.defaultdict(set) for _ in range(3))
        for s in smis:
            a, b, d2, f = keys_for(s, enum)
            if a:
                pk_i[(f, a)].add(s)
            if b:
                tk_i[(f, b)].add(s)
            if d2:
                sk_i[(f, d2)].add(s)
        idx[name] = (pk_i, tk_i, sk_i)
    for name, (pk_i, tk_i, sk_i) in idx.items():
        c[name + "_pk_hit"] = [bool(k) and (f, k) in pk_i for f, k in zip(c.formula_calc, c.parent_key)]
        c[name + "_taut_hit"] = [bool(k) and (f, k) in tk_i for f, k in zip(c.formula_calc, c.taut_key)]
        c[name + "_skel_hit"] = [bool(k) and (f, k) in sk_i for f, k in zip(c.formula_calc, c.skel_key)]
        c[name + "_new_hit_smiles"] = [
            ";".join(sorted((tk_i.get((f, t), set()) | sk_i.get((f, s2), set())) - pk_i.get((f, p2), set()))[:3])
            for f, p2, t, s2 in zip(c.formula_calc, c.parent_key, c.taut_key, c.skel_key)]
    c["taut_or_skel_new_hit"] = False
    for name in pops:
        c["taut_or_skel_new_hit"] |= (c[name + "_taut_hit"] | c[name + "_skel_hit"]) & ~c[name + "_pk_hit"]
    c.to_csv(OUT / "c11_tautomer_recheck.csv", index=False)
    S["tautomer_recheck"] = {
        "n_compounds": int(len(c)),
        "n_taut_key_differs_from_parent_key": int((c.taut_key != c.parent_key).sum()),
        "n_new_exclusions_any_population": int(c.taut_or_skel_new_hit.sum()),
        "new_exclusions": [{"compound": r.compound, "parent_key": r.parent_key, "taut_key": r.taut_key,
                            "populations": [n for n in pops
                                            if (getattr(r, n + "_taut_hit") or getattr(r, n + "_skel_hit"))
                                            and not getattr(r, n + "_pk_hit")],
                            "matched_smiles": next((getattr(r, n + "_new_hit_smiles") for n in pops
                                                    if getattr(r, n + "_new_hit_smiles")), "")}
                           for r in c[c.taut_or_skel_new_hit].itertuples()],
    }

    # ---------- post-exclusion inventories
    base = c[c.n_mh_spectra.gt(0) & c.parent_key.notna()].copy()
    tiers = {
        "T0_all_mh_with_key": pd.Series(True, index=base.index),
        "T1_minus_muru_registry_key": ~base.in_muru_registry,
        "T2_T1_minus_pr7_comparator_key": ~base.in_muru_registry & ~base.in_pr7 & ~base.in_comparator,
        "T3_T2_minus_msg15_key": ~base.in_muru_registry & ~base.in_pr7 & ~base.in_comparator & ~base.in_msg15,
        "T4_T3_minus_all_scaffold_groups": (~base.in_muru_registry & ~base.in_pr7 & ~base.in_comparator
                                            & ~base.in_msg15 & ~base.group_in_muru_registry_groups
                                            & ~base.group_in_pr7 & ~base.group_in_comparator
                                            & ~base.group_in_msg15),
        "T5_T3_minus_tautomer_skeleton_hits": (~base.in_muru_registry & ~base.in_pr7 & ~base.in_comparator
                                               & ~base.in_msg15 & ~base.taut_or_skel_new_hit),
        "M_msg15_key_only": ~base.in_msg15,
        "M_msg15_key_and_scaffold": ~base.in_msg15 & ~base.group_in_msg15,
    }
    S["tiers"] = {}
    for name, m in tiers.items():
        t = base[m]
        S["tiers"][name] = {"n_compounds": int(len(t)), "n_scaffold_groups": int(t.scaffold_group.nunique()),
                            "n_with_ge11_mh_spectra": int((t.n_mh_spectra >= 11).sum()),
                            "n_with_ge5_mh_spectra": int((t.n_mh_spectra >= 5).sum()),
                            "compounds": sorted(t.compound.tolist())}

    (OUT / "c11_criteria.json").write_text(json.dumps(S, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: v for k, v in S.items() if k != "evidence"}, indent=1, ensure_ascii=False, default=str))
    print("\n=== EVIDENCE ===")
    print(json.dumps(S["evidence"], indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
