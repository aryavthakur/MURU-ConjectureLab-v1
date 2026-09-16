"""S1 screen C01, step 4: tautomer- and skeleton-aware re-check of the compound-level exclusions.

Motivation (found while reviewing step 3): MassBank Eawag re-deposited compound UCHEM 3178 in release 2024.11 with a
different structural representation than its pre-2023.11 records. The old records (in MassBank 2023.11, the release
MassSpecGym loaded) carry InChIKey IOYNQIMAUDJVEI (enol form of clethodim), the new ones PHXHZCIAPNNPTQ (diketone
form). The MURU compound key is the first InChIKey block of the parent molecule, which is tautomer SENSITIVE, so a
key-only exclusion can miss a compound that is in MassSpecGym as another tautomer; Morgan nearest-neighbour also
misses it (Tanimoto 0.54 for this pair).

Re-screens every C01 compound against the exclusion populations with two tautomer-insensitive keys:
  taut_key = first InChIKey block of the RDKit canonical tautomer of the parent molecule
             (rdMolStandardize.TautomerEnumerator().Canonicalize)
  skel_key = first InChIKey block of the parent after erasing bond orders, charges, explicit H and stereo
             (heavy-atom connectivity skeleton; catches pairs the canonicaliser does not unify)
Comparison populations (identity columns only): MassSpecGym 1.5 (all folds), MURU v2 development population,
MSnLib confirmation study 2 (PR #7) population, comparator benchmark common population. To keep the cost bounded,
each population is first restricted to structures whose molecular formula equals that of some C01 compound: a
tautomer or skeleton match implies an identical molecular formula, so this restriction is exact, not a heuristic.

Identity metadata only. No spectra, no model output, no MURU result.

Outputs (in --outdir): c01_tautomer_recheck.csv, c01_tautomer_recheck.json
"""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import inchi, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scaffold_key as SK  # noqa: E402

RDLogger.DisableLog("rdApp.*")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def keys_for(smiles, enum):
    """(parent_key, taut_key, skel_key, formula) for one SMILES; None where RDKit cannot build them."""
    pm = SK.parent_mol(smiles) if isinstance(smiles, str) else None
    if pm is None:
        return None, None, None, None
    pk = SK.first_block(inchi.MolToInchiKey(pm) or "") or None
    formula = rdMolDescriptors.CalcMolFormula(pm)
    try:
        tm = enum.Canonicalize(pm)
        tk = SK.first_block(inchi.MolToInchiKey(tm) or "") or None
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True, help="c01_compound_screen.csv from step 3")
    ap.add_argument("--msg-meta", required=True, help="massspecgym15_metadata_columns.parquet (smiles column)")
    ap.add_argument("--dev-compounds", required=True, help="artifacts/wur_v2/data/compounds.csv (smiles)")
    ap.add_argument("--pr7-population", required=True, help="wur_v2_confirmation_v2/freeze/validation_population.csv")
    ap.add_argument("--comparator-population", required=True,
                    help="comparator_benchmark/population/common_population.csv (model_smiles)")
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    enum = rdMolStandardize.TautomerEnumerator()
    S = {"rdkit": rdBase.rdkitVersion, "inputs": {}}

    c = pd.read_csv(a.screen)
    S["inputs"]["screen"] = {"path": a.screen, "sha256": sha256(a.screen), "rows": int(len(c))}
    rows = [keys_for(s, enum) for s in c["smiles"]]
    c["parent_key_recomputed"] = [r[0] for r in rows]
    c["taut_key"] = [r[1] for r in rows]
    c["skel_key"] = [r[2] for r in rows]
    c["formula_calc"] = [r[3] for r in rows]
    S["parent_key_recomputed_equals_cmp_key"] = int((c["parent_key_recomputed"] == c["cmp_key"]).sum())
    S["n_taut_key_differs_from_parent_key"] = int((c["taut_key"] != c["parent_key_recomputed"]).sum())
    formulas = set(c["formula_calc"].dropna())

    pops = {}
    mm = pd.read_parquet(a.msg_meta, columns=["smiles"]).drop_duplicates("smiles")
    S["inputs"]["msg_meta"] = {"path": a.msg_meta, "sha256": sha256(a.msg_meta), "unique_smiles": int(len(mm))}
    msg = []
    for s in mm["smiles"]:
        pm = SK.parent_mol(s)
        if pm is None:
            continue
        f = rdMolDescriptors.CalcMolFormula(pm)
        if f in formulas:
            msg.append((s, f))
    pops["msg15"] = pd.DataFrame(msg, columns=["smiles", "formula_calc"])
    S["msg15_structures_sharing_a_formula"] = len(msg)
    for name, path, col in (("muru_dev_pop", a.dev_compounds, "smiles"),
                            ("pr7", a.pr7_population, "smiles"),
                            ("comparator", a.comparator_population, "model_smiles")):
        df = pd.read_csv(path, usecols=[col]).rename(columns={col: "smiles"}).drop_duplicates("smiles")
        S["inputs"][name] = {"path": path, "sha256": sha256(path), "rows": int(len(df)), "column_read": col}
        keep = []
        for s in df["smiles"]:
            pm = SK.parent_mol(s)
            if pm is None:
                continue
            f = rdMolDescriptors.CalcMolFormula(pm)
            if f in formulas:
                keep.append((s, f))
        pops[name] = pd.DataFrame(keep, columns=["smiles", "formula_calc"])
        S[f"{name}_structures_sharing_a_formula"] = len(keep)

    # A skeleton key erases bond orders and hydrogen counts, so two molecules differing in oxidation state (e.g.
    # a flavanone and a flavone) share it. A tautomer or skeleton match is only accepted when the molecular
    # FORMULA is also identical, which is a necessary condition for the two records to be the same substance.
    idx = {}
    for name, df in pops.items():
        pk, tk, sk = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
        for s in df["smiles"]:
            p, t, k, f = keys_for(s, enum)
            if p:
                pk[(f, p)].add(s)
            if t:
                tk[(f, t)].add(s)
            if k:
                sk[(f, k)].add(s)
        idx[name] = (pk, tk, sk)

    for name in pops:
        pk, tk, sk = idx[name]
        c[name + "_parent_key_hit"] = [bool(k) and (f, k) in pk
                                       for f, k in zip(c["formula_calc"], c["parent_key_recomputed"])]
        c[name + "_taut_key_hit"] = [bool(k) and (f, k) in tk for f, k in zip(c["formula_calc"], c["taut_key"])]
        c[name + "_skel_key_hit"] = [bool(k) and (f, k) in sk for f, k in zip(c["formula_calc"], c["skel_key"])]
        c[name + "_new_hit_smiles"] = [
            ";".join(sorted((tk.get((f, t), set()) | sk.get((f, s), set())) - pk.get((f, p), set()))[:3])
            for f, p, t, s in zip(c["formula_calc"], c["parent_key_recomputed"], c["taut_key"], c["skel_key"])]

    c.to_csv(out / "c01_tautomer_recheck.csv", index=False)

    base = c[c["ge3_nce"]].copy()
    base["new_hit"] = (base["msg15_taut_key_hit"] | base["msg15_skel_key_hit"]
                       | base["muru_dev_pop_taut_key_hit"] | base["muru_dev_pop_skel_key_hit"]
                       | base["pr7_taut_key_hit"] | base["pr7_skel_key_hit"]
                       | base["comparator_taut_key_hit"] | base["comparator_skel_key_hit"])
    blocks = {}
    for scope, m in {"tagged": base["tagged_release"],
                     "all_including_dev": pd.Series(True, index=base.index)}.items():
        b = base[m]
        blk = {}
        for tier in ("clean_compound_level", "clean_primary", "clean_conservative", "clean_strict_msg_scaffold"):
            t = b[b[tier]]
            nh = t["new_hit"]
            blk[tier] = {
                "n_compounds_step3": int(len(t)),
                "n_new_exclusions_tautomer_or_skeleton": int(nh.sum()),
                "n_compounds_after": int((~nh).sum()),
                "n_scaffold_groups_after": int(t.loc[~nh, "scaffold_group"].nunique()),
                "new_exclusions": [
                    {"cmp_key": r["cmp_key"], "name": r["name"], "smiles": r["smiles"],
                     "msg15": bool(r["msg15_taut_key_hit"] or r["msg15_skel_key_hit"]),
                     "muru_dev_pop": bool(r["muru_dev_pop_taut_key_hit"] or r["muru_dev_pop_skel_key_hit"]),
                     "pr7": bool(r["pr7_taut_key_hit"] or r["pr7_skel_key_hit"]),
                     "comparator": bool(r["comparator_taut_key_hit"] or r["comparator_skel_key_hit"]),
                     "matched_smiles": (r["msg15_new_hit_smiles"] or r["muru_dev_pop_new_hit_smiles"]
                                        or r["pr7_new_hit_smiles"] or r["comparator_new_hit_smiles"])}
                    for _i, r in t[nh].iterrows()],
            }
        blocks[scope] = blk
    S["tiers"] = blocks
    (out / "c01_tautomer_recheck.json").write_text(json.dumps(S, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(S, indent=1, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
