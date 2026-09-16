"""S11 screen, candidate C11: ExpoLib 1.0 (Zenodo 20715576). ANALYSIS of metadata only.

Inputs (all fetched by screen_c11_expolib_fetch.py plus two manual register-recorded steps; no spectra):
  downloads/Library_Overview_-_ESI+.xlsx                      per-compound CE list, adducts, chimeric flag, RT
  downloads/mzmine_files_extracted/Database_File_mzmine_ESI+.csv  compound table (name, precursor m/z, InChIKey, SMILES)
  downloads/11306_2026_2481_MOESM1_ESM.xlsx                   paper SI: S1 compound info (229), S5 ESI+ overview
Exclusion sets from P5 (artifacts/ce_interface_adjudication/exclusion/), keys and scaffold groups by
scripts/ce_interface_adjudication/scaffold_key.py (MURU parent connectivity key and scaffold_group_v2).
Outputs in artifacts/ce_interface_adjudication/screen/c11_expolib/:
  c11_compounds_screen.csv   one row per ESI+ library compound
  c11_screen_summary.json    counts used in the screen verdict
No model of any kind is run. No spectra are read.
(Authored in the session scratchpad and copied into the adjudication worktree; the session Write guard binds to
another worktree.)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402

ADJ = ROOT / "artifacts" / "ce_interface_adjudication"
EXC = ADJ / "exclusion"
OUT = ADJ / "screen" / "c11_expolib"
DL = OUT / "downloads"
PROTON = 1.007276
DEV_MH_RANGE = (70.0, 1042.6)  # P5 note section 4, msnlib_design.py:27
SINGLE_CE = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70]
CES = ["30±10", "30±20", "40±10", "40±20"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = s.replace("′", "'").replace("’", "'")
    return re.sub(r"[^a-z0-9]", "", s)


def read_set(name: str) -> set[str]:
    return {x.strip() for x in (EXC / name).read_text().splitlines() if x.strip()}


def parse_overview(df: pd.DataFrame, header_row: int, cols: dict) -> pd.DataFrame:
    rows = []
    for i in range(header_row + 1, df.shape[0]):
        name = df.iat[i, cols["compound"]]
        if not isinstance(name, str) or name.startswith("*") or not name.strip():
            continue
        rows.append({k: df.iat[i, c] for k, c in cols.items()})
    return pd.DataFrame(rows)


def parse_ce(ce_str: str) -> dict:
    s = str(ce_str).replace("±", "±").replace("+-", "±")
    # remove parenthesised counts "(2)" before tokenising
    s2 = re.sub(r"\(\s*\d+\s*\)", " ", s)
    single, ces = set(), set()
    for a, b, c in re.findall(r"(\d+)\s*±\s*(\d+)|(\d+)", s2):
        if a:
            ces.add(f"{a}±{b}")
        else:
            single.add(int(c))
    return {"single_ce": sorted(single), "ces": sorted(ces)}


def parse_adducts(s: str) -> dict:
    out = {}
    for ad, n in re.findall(r"(\[[^\]]+\][+-])\s*\((\d+)\)", str(s)):
        out[ad] = out.get(ad, 0) + int(n)
    return out


def main() -> None:
    ov_raw = pd.read_excel(DL / "Library_Overview_-_ESI+.xlsx", header=None)
    hdr = int(ov_raw.index[ov_raw.iloc[:, 1].astype(str).eq("Compound")][0])
    ov = parse_overview(ov_raw, hdr, {"compound": 1, "ce_list": 2, "adducts": 3, "total_spectra": 4,
                                      "chimeric": 5, "rt_min": 6})
    si = pd.read_excel(DL / "11306_2026_2481_MOESM1_ESM.xlsx", sheet_name=None, header=None)
    s5_raw = si["S5 - Libraries overview - ESI+"]
    h5 = int(s5_raw.index[s5_raw.iloc[:, 1].astype(str).eq("Compound")][0])
    s5 = parse_overview(s5_raw, h5, {"compound": 1, "ce_list": 2, "adducts": 3, "total_spectra": 4, "noisy": 5,
                                     "chimeric": 6, "rt_min": 7})
    s1_raw = si["S1 - Compound Info"]
    h1 = int(s1_raw.index[s1_raw.iloc[:, 1].astype(str).eq("Compound ID#")][0])
    s1 = s1_raw.iloc[h1 + 1:, 1:19].copy()
    s1.columns = [str(c).replace("\n", " ") for c in s1_raw.iloc[h1, 1:19]]
    s1 = s1[pd.to_numeric(s1["Compound ID#"], errors="coerce").notna()]
    db = pd.read_csv(DL / "mzmine_files_extracted" / "Database_File_mzmine_ESI+.csv")

    # cross-check Zenodo overview vs SI S5
    ov_names, s5_names = set(map(norm, ov.compound)), set(map(norm, s5.compound))
    s5n = {norm(r.compound): r for r in s5.itertuples()}
    ce_mismatch = [r.compound for r in ov.itertuples()
                   if norm(r.compound) in s5n and (str(r.ce_list).strip() != str(s5n[norm(r.compound)].ce_list).strip()
                                                  or str(r.adducts).strip() != str(s5n[norm(r.compound)].adducts).strip())]

    dbn = {}
    for r in db.to_dict("records"):
        dbn.setdefault(norm(r["Compound"]), []).append(r)
    s1n = {}
    for r in s1.to_dict("records"):
        s1n.setdefault(norm(r["Compound name"]), []).append(r)

    # exclusion sets
    reg = read_set("muru_exposure_registry_keys.txt")
    reg_direct = read_set("muru_exposure_registry_keys_direct_reason.txt")
    reg_groups = read_set("muru_exposure_registry_scaffold_groups.txt")
    pops = {p.name.replace("muru_exposure_registry_population_", "").replace("_keys.txt", ""): read_set(p.name)
            for p in sorted(EXC.glob("muru_exposure_registry_population_*_keys.txt"))}
    pop_union = set().union(*pops.values())
    pr7 = read_set("msnlib_study2_population_keys.txt")
    pr7_groups = read_set("msnlib_study2_population_scaffold_groups.txt")
    comp = read_set("comparator_common_population_keys.txt")
    comp_groups = read_set("comparator_common_population_scaffold_groups.txt")
    msg_all = read_set("msg15_keys_all.txt")
    msg_parent_all = read_set("msg15_parent_keys_all.txt")
    msg_fold = {f: read_set(f"msg15_keys_{f}.txt") | read_set(f"msg15_parent_keys_{f}.txt")
                for f in ("train", "val", "test")}
    msg_sim = read_set("msg15_simchallenge_keys_all.txt")
    msg_groups = read_set("msg15_scaffold_groups_all.txt")
    msn9 = read_set("msnlib_9lib_keys.txt")
    msnv1 = read_set("msnlib_v1_0_4lib_keys.txt")
    mrow = pd.read_parquet(EXC / "msg_row_msnlib_membership.parquet",
                           columns=["inchikey14", "parent_key14", "fold", "adduct", "instrument_type",
                                    "simulation_challenge"])

    # co-injected mixture: S1 compounds #1-#223 were one working solution; #224-#229 acquired separately (paper,
    # Materials and methods). Ion list mirrors the MURU isolation-purity rule (P5 note section 4, 0.7 m/z).
    ION_SHIFTS = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
                  "[M-H2O+H]+": PROTON - 18.010565}
    mix = []
    for r1 in s1.to_dict("records"):
        cid = int(r1["Compound ID#"])
        mass = None
        for c in (r1.get("SMILES"), r1.get("Canonical SMILES"), r1.get("Isomeric SMILES")):
            if isinstance(c, str) and c.strip() not in ("", "-") and Chem.MolFromSmiles(c.strip()) is not None:
                mm = Chem.MolFromSmiles(c.strip())
                if CalcMolFormula(mm) == str(r1["Formula"]).strip():
                    mass = Descriptors.ExactMolWt(SK.parent_mol(c.strip()))
                    break
        if mass is None:
            try:
                mass = float(r1["Monoisotopic Mass1"])
            except (TypeError, ValueError):
                mass = None
        mix.append({"id": cid, "name": r1["Compound name"], "mass": mass, "in_mix": cid <= 223})

    recs = []
    for r in ov.itertuples(index=False):
        n = norm(r.compound)
        d_db = dbn.get(n, [None])[0]
        d_s1 = s1n.get(n, [None])[0]
        formula = str((d_db or d_s1 or {}).get("Formula", "")).strip() or None
        prec_mz = d_db.get("Precursor m/z") if d_db else None
        cands = []
        if d_db:
            cands += [("db_SMILES", d_db.get("SMILES")), ("db_Isomeric_Smiles", d_db.get("Isomeric Smiles")),
                      ("db_Canonical_Smiles", d_db.get("Canonical Smiles"))]
        if d_s1:
            cands += [("s1_SMILES", d_s1.get("SMILES")), ("s1_Isomeric_SMILES", d_s1.get("Isomeric SMILES")),
                      ("s1_Canonical_SMILES", d_s1.get("Canonical SMILES"))]
        parsed = []
        for lab, c in cands:
            if isinstance(c, str) and c.strip() not in ("", "-") and Chem.MolFromSmiles(c.strip()) is not None:
                mol = Chem.MolFromSmiles(c.strip())
                parsed.append((lab, c.strip(), CalcMolFormula(mol) == formula))
        chosen = next((x for x in parsed if x[2]), parsed[0] if parsed else (None, None, False))
        src, smi, formula_ok = chosen
        key, group = SK.key_and_group(smi) if isinstance(smi, str) else (None, None)
        alt_keys = {lab: SK.parent_connectivity_key(c) for lab, c, _ in parsed}
        rec_db = SK.first_block(d_db.get("InChI Key")) if d_db else None
        rec_s1 = SK.first_block(d_s1.get("InChIKey")) if d_s1 else None
        ik = d_db.get("InChI Key") if d_db else (d_s1.get("InChIKey") if d_s1 else None)
        rec_block = rec_db or rec_s1
        route_keys = {k for k in [rec_db, rec_s1, *alt_keys.values()] if k}
        conflicting = sorted(k for k in route_keys if k != key)
        m = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
        charge = sum(a.GetFormalCharge() for a in m.GetAtoms()) if m is not None else None
        pm = SK.parent_mol(smi) if isinstance(smi, str) else None
        mono = Descriptors.ExactMolWt(pm) if pm is not None else None
        mh = mono + PROTON if mono is not None else None
        elements = sorted({a.GetSymbol() for a in pm.GetAtoms()}) if pm is not None else []
        ce = parse_ce(r.ce_list)
        ad = parse_adducts(r.adducts)
        keys = {key} if key else set()
        anyk = keys | route_keys
        in_msg = bool(keys & (msg_all | msg_parent_all))
        rows_msg = mrow[mrow.inchikey14.isin(keys) | mrow.parent_key14.isin(keys)]
        self_ids = [m1["id"] for m1 in mix if norm(m1["name"]) == n]
        neigh = []
        if mh is not None and self_ids and self_ids[0] <= 223:
            for m1 in mix:
                if not m1["in_mix"] or m1["id"] in self_ids or m1["mass"] is None:
                    continue
                for ion, sh in ION_SHIFTS.items():
                    if abs(m1["mass"] + sh - mh) <= 0.7:
                        neigh.append(f"{m1['name']}{ion}")
        rec = {
            "compound": r.compound, "identity_source": src, "smiles": smi, "recorded_inchikey": ik,
            "db_precursor_mz": prec_mz, "formula": formula, "parent_key": key, "recorded_first_block": rec_block,
            "smiles_formula_matches_recorded_formula": formula_ok, "other_route_keys_conflicting": ";".join(conflicting),
            "key_route_disagree": bool(conflicting), "scaffold_group": group,
            "net_formal_charge_raw": charge, "parent_mh_mz": round(mh, 5) if mh else None,
            "mh_in_dev_range": bool(mh and DEV_MH_RANGE[0] <= mh <= DEV_MH_RANGE[1]),
            "elements": ";".join(elements), "has_F": "F" in elements,
            "single_ce_listed": ";".join(map(str, ce["single_ce"])), "n_single_ce_listed": len(ce["single_ce"]),
            "ces_listed": ";".join(ce["ces"]), "n_ces_listed": len(ce["ces"]),
            "adducts": json.dumps(ad), "n_mh_spectra": ad.get("[M+H]+", 0), "has_mh": ad.get("[M+H]+", 0) > 0,
            "total_spectra": r.total_spectra, "chimeric_flag": r.chimeric, "rt_min": r.rt_min,
            "s1_compound_id": self_ids[0] if self_ids else None,
            "coinjected_ions_within_0p7_mz_of_mh": ";".join(neigh), "n_coinjected_ions_within_0p7": len(neigh),
            "in_muru_registry": bool(keys & reg), "in_muru_registry_direct_reason": bool(keys & reg_direct),
            "muru_exposed_populations": ";".join(p for p, s in pops.items() if keys & s),
            "in_muru_exposed_population_union": bool(keys & pop_union),
            "group_in_muru_registry_groups": bool(group and group in reg_groups),
            "in_pr7_population": bool(keys & pr7), "group_in_pr7_groups": bool(group and group in pr7_groups),
            "in_comparator_population": bool(keys & comp),
            "group_in_comparator_groups": bool(group and group in comp_groups),
            "in_msg15_any_fold": in_msg,
            "msg15_folds": ";".join(f for f, s in msg_fold.items() if keys & s),
            "in_msg15_simchallenge": bool(keys & msg_sim),
            "msg15_rows": len(rows_msg),
            "msg15_instrument_types": ";".join(f"{k}:{v}" for k, v in rows_msg.instrument_type.value_counts().items()),
            "msg15_mh_qtof_rows": int(((rows_msg.instrument_type == "QTOF") & (rows_msg.adduct == "[M+H]+")).sum()),
            "group_in_msg15_groups": bool(group and group in msg_groups),
            "in_msnlib_9lib": bool(keys & msn9), "in_msnlib_v1_0": bool(keys & msnv1),
            "anyroute_in_muru_registry": bool(anyk & reg), "anyroute_in_muru_exposed_population_union": bool(anyk & pop_union),
            "anyroute_in_pr7_population": bool(anyk & pr7), "anyroute_in_comparator_population": bool(anyk & comp),
            "anyroute_in_msg15_any_fold": bool(anyk & (msg_all | msg_parent_all)),
        }
        recs.append(rec)
    t = pd.DataFrame(recs)
    t.to_csv(OUT / "c11_compounds_screen.csv", index=False)

    def cnt(mask):
        return int(mask.sum())

    base = t[t.has_mh & t.parent_key.notna()]
    c1 = base[~base.in_muru_registry]
    c1g = c1[~c1.group_in_muru_registry_groups]
    c2 = c1g[~c1g.in_pr7_population & ~c1g.group_in_pr7_groups]
    c3 = c2[~c2.in_comparator_population & ~c2.group_in_comparator_groups]
    c4 = c3[~c3.in_msg15_any_fold]
    c4g = c4[~c4.group_in_msg15_groups]
    c5 = c4[c4.mh_in_dev_range & (c4.net_formal_charge_raw == 0)]
    lenient = base[~base.in_muru_exposed_population_union & ~base.in_pr7_population & ~base.in_comparator_population
                   & ~base.in_msg15_any_fold]

    def ce_profile(df):
        return {"n": len(df), "n_scaffold_groups": int(df.scaffold_group.nunique()),
                "n_mh_spectra_ge_11": cnt(df.n_mh_spectra >= 11), "n_mh_spectra_ge_5": cnt(df.n_mh_spectra >= 5),
                "n_mh_spectra_ge_2": cnt(df.n_mh_spectra >= 2),
                "n_acyclic_groups": cnt(df.scaffold_group.astype(str).str.startswith("__ACYCLIC__")),
                "n_chimeric_flag_yes": cnt(df.chimeric_flag.astype(str).str.lower().eq("yes")),
                "n_coinjected_ion_within_0p7": cnt(df.n_coinjected_ions_within_0p7 > 0),
                "n_clean_no_chimeric_no_coinjected": cnt(~df.chimeric_flag.astype(str).str.lower().eq("yes")
                                                         & (df.n_coinjected_ions_within_0p7 == 0)),
                "compounds": sorted(df.compound.tolist())}

    summary = {
        "script": "scripts/ce_interface_adjudication/screen_c11_expolib.py",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "rdkit": rdBase.rdkitVersion,
        "input_sha256": {p.name: sha(p) for p in [DL / "Library_Overview_-_ESI+.xlsx",
                                                  DL / "mzmine_files_extracted" / "Database_File_mzmine_ESI+.csv",
                                                  DL / "11306_2026_2481_MOESM1_ESM.xlsx"]},
        "overview_esi_plus_compounds": len(ov), "si_s5_compounds": len(s5),
        "overview_vs_s5_name_sets_equal": ov_names == s5_names,
        "overview_minus_s5": sorted(ov_names - s5_names), "s5_minus_overview": sorted(s5_names - ov_names),
        "overview_vs_s5_ce_or_adduct_string_mismatch": ce_mismatch,
        "database_file_esi_plus_rows": len(db), "si_s1_rows": len(s1),
        "identity_source_counts": t.identity_source.fillna("UNMATCHED").value_counts().to_dict(),
        "unmatched_compounds": t.loc[t.identity_source.isna(), "compound"].tolist(),
        "with_parent_key": cnt(t.parent_key.notna()), "unique_parent_keys": int(t.parent_key.nunique()),
        "duplicate_parent_keys": t.loc[t.parent_key.duplicated(keep=False) & t.parent_key.notna(),
                                       ["compound", "parent_key"]].values.tolist(),
        "key_route_disagreements": t.loc[t.key_route_disagree, ["compound", "identity_source", "parent_key",
                                                                 "other_route_keys_conflicting"]].values.tolist(),
        "smiles_formula_mismatch": t.loc[t.parent_key.notna() & ~t.smiles_formula_matches_recorded_formula,
                                         ["compound", "formula"]].values.tolist(),
        "no_structure": t.loc[t.parent_key.isna(), "compound"].tolist(),
        "charged_raw_smiles": t.loc[t.net_formal_charge_raw.fillna(0) != 0, "compound"].tolist(),
        "mh_outside_dev_range": t.loc[~t.mh_in_dev_range, ["compound", "parent_mh_mz"]].values.tolist(),
        "has_mh": cnt(t.has_mh), "no_mh": t.loc[~t.has_mh, "compound"].tolist(),
        "n_mh_spectra_distribution": t.n_mh_spectra.value_counts().sort_index().to_dict(),
        "n_single_ce_listed_distribution": t.n_single_ce_listed.value_counts().sort_index().to_dict(),
        "single_ce_values_seen": sorted({int(x) for s in t.single_ce_listed for x in str(s).split(";") if x}),
        "ces_values_seen": sorted({x for s in t.ces_listed.fillna("") for x in str(s).split(";") if x}),
        "chimeric_yes": cnt(t.chimeric_flag.astype(str).str.lower().eq("yes")),
        "s1_id_matched": cnt(t.s1_compound_id.notna()),
        "with_any_coinjected_ion_within_0p7_mz": cnt(t.n_coinjected_ions_within_0p7 > 0),
        "overlap_of_mh_compounds": {
            "base_mh_with_key": len(base),
            "muru_registry_key": cnt(base.in_muru_registry),
            "muru_registry_direct_reason": cnt(base.in_muru_registry_direct_reason),
            "muru_exposed_population_union_key": cnt(base.in_muru_exposed_population_union),
            "muru_registry_scaffold_group": cnt(base.group_in_muru_registry_groups),
            "muru_populations_hit": pd.Series([p for s in base.muru_exposed_populations for p in s.split(";") if p])
            .value_counts().to_dict(),
            "pr7_key": cnt(base.in_pr7_population), "pr7_group": cnt(base.group_in_pr7_groups),
            "comparator_key": cnt(base.in_comparator_population), "comparator_group": cnt(base.group_in_comparator_groups),
            "msg15_any_fold_key": cnt(base.in_msg15_any_fold),
            "msg15_train_key": cnt(base.msg15_folds.str.contains("train")),
            "msg15_simchallenge_key": cnt(base.in_msg15_simchallenge),
            "msg15_key_with_mh_qtof_rows": cnt(base.msg15_mh_qtof_rows > 0),
            "msg15_scaffold_group": cnt(base.group_in_msg15_groups),
            "msnlib_9lib_key": cnt(base.in_msnlib_9lib), "msnlib_v1_0_key": cnt(base.in_msnlib_v1_0),
            "anyroute_muru_registry": cnt(base.anyroute_in_muru_registry),
            "anyroute_muru_exposed_population_union": cnt(base.anyroute_in_muru_exposed_population_union),
            "anyroute_pr7": cnt(base.anyroute_in_pr7_population), "anyroute_comparator": cnt(base.anyroute_in_comparator_population),
            "anyroute_msg15_any_fold": cnt(base.anyroute_in_msg15_any_fold),
        },
        "cascade_mh": {
            "0_mh_with_key": ce_profile(base),
            "1_minus_muru_registry_key": len(c1),
            "1g_minus_muru_registry_scaffold_group": len(c1g),
            "2_minus_pr7_key_and_group": len(c2),
            "3_minus_comparator_key_and_group": len(c3),
            "4_minus_msg15_all_folds_key": ce_profile(c4),
            "4g_also_minus_msg15_scaffold_group": ce_profile(c4g),
            "5_c4_and_mh_in_dev_range_and_neutral": ce_profile(c5),
        },
        "lenient_mh_key_only_exposed_populations_pr7_comparator_msg15": ce_profile(lenient),
        "msg15_only_mh_absent_key": ce_profile(base[~base.in_msg15_any_fold]),
        "msg15_only_mh_absent_key_and_scaffold_group": ce_profile(base[~base.in_msg15_any_fold
                                                                       & ~base.group_in_msg15_groups]),
        "msg15_only_mh_absent_key_ge11_mh_spectra": ce_profile(base[~base.in_msg15_any_fold
                                                                    & (base.n_mh_spectra >= 11)]),
    }
    (OUT / "c11_screen_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("input_sha256",)}, indent=1,
                     ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
