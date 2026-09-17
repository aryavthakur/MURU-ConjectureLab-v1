"""TASK V: independent hidden-inclusion recheck for C01 survivors.

Builds, from scratch, three identity keys for every MassSpecGym 1.5 structure and for the C01
survivors, and tests the survivors against all of them:
  parent key            (MURU rule)
  canonical tautomer key  (RDKit TautomerEnumerator.Canonicalize -> InChIKey14 of the parent)
  formula + heavy-atom skeleton key (bond orders and charges erased, atoms kept)
and additionally reports same-formula nearest neighbours by Morgan/Tanimoto.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem import inchi

RDLogger.DisableLog("rdApp.*")
WT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ART = WT / "artifacts/ce_interface_adjudication"
sys.path.insert(0, str(WT / "scripts/ce_interface_adjudication"))
from scaffold_key import parent_mol, key_and_group  # noqa: E402

TE = rdMolStandardize.TautomerEnumerator()
MGEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def taut_key(smiles: str):
    m = parent_mol(smiles)
    if m is None:
        return None
    try:
        m = TE.Canonicalize(m)
    except Exception:
        return None
    k = inchi.MolToInchiKey(m)
    return k.split("-")[0] if k else None


def skel_key(smiles: str):
    """Formula + heavy-atom skeleton: all bonds single, no charges, no H counts, no stereo."""
    m = parent_mol(smiles)
    if m is None:
        return None
    em = Chem.RWMol(m)
    for b in em.GetBonds():
        b.SetBondType(Chem.BondType.SINGLE)
        b.SetIsAromatic(False)
    for a in em.GetAtoms():
        a.SetFormalCharge(0)
        a.SetNoImplicit(True)
        a.SetNumExplicitHs(0)
        a.SetIsAromatic(False)
    try:
        s = Chem.MolToSmiles(em.GetMol())
    except Exception:
        return None
    f = rdMolDescriptors.CalcMolFormula(m)
    return f"{f}|{s}" if s else None


def fp(smiles: str):
    m = parent_mol(smiles)
    return MGEN.GetFingerprint(m) if m is not None else None


def formula(smiles: str):
    m = parent_mol(smiles)
    return rdMolDescriptors.CalcMolFormula(m) if m is not None else None


print("loading MassSpecGym structures ...")
msg = pd.read_parquet(ART / "massspecgym15_metadata_columns.parquet", columns=["identifier", "smiles"])
msg_smi = sorted(set(msg["smiles"].dropna().astype(str)))
print("  unique MSG smiles:", len(msg_smi))

msg_taut, msg_skel, msg_by_formula = set(), set(), {}
for s in msg_smi:
    tk = taut_key(s)
    if tk:
        msg_taut.add(tk)
    sk = skel_key(s)
    if sk:
        msg_skel.add(sk)
    f = formula(s)
    if f:
        msg_by_formula.setdefault(f, []).append(s)
print("  msg taut keys:", len(msg_taut), " skel keys:", len(msg_skel), " formulas:", len(msg_by_formula))

# the same three keys for the MURU dev population, PR#7 and comparator populations
extra = {}
for lab, path, col in (
    ("muru_dev_pop", WT / "artifacts/wur_v2/data/compounds.csv", "smiles"),
    ("pr7", WT / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv", "smiles"),
    ("comparator", WT / "artifacts/comparator_benchmark/population/common_population.csv", "model_smiles"),
):
    d = pd.read_csv(path, usecols=[col])
    ss = sorted(set(d[col].dropna().astype(str)))
    extra[lab] = {"taut": {taut_key(s) for s in ss} - {None},
                  "skel": {skel_key(s) for s in ss} - {None},
                  "n": len(ss)}
    print(f"  {lab}: {len(ss)} smiles, {len(extra[lab]['taut'])} taut keys")

res = {"msg_unique_smiles": len(msg_smi), "msg_taut_keys": len(msg_taut), "msg_skel_keys": len(msg_skel),
       "extra_sizes": {k: {"n_smiles": v["n"], "taut": len(v["taut"]), "skel": len(v["skel"])} for k, v in extra.items()}}

cand = pd.read_csv("/tmp/v_c01_cand.csv")
key_clean = ~(cand["in_msg15"] | cand["in_registry"] | cand["in_pr7"] | cand["in_comparator"])
sur = cand[key_clean].copy()
print("\nsurvivors (key-clean, before tautomer step):", len(sur))

rows = []
for r in sur.itertuples(index=False):
    tk, sk, f = taut_key(r.smiles), skel_key(r.smiles), formula(r.smiles)
    mine = fp(r.smiles)
    nn, nn_smi = 0.0, None
    for s in msg_by_formula.get(f, []):
        o = fp(s)
        if o is None:
            continue
        t = DataStructs.TanimotoSimilarity(mine, o)
        if t > nn:
            nn, nn_smi = t, s
    rows.append({
        "key": r.key, "name": r.name, "smiles": r.smiles, "sg": r.sg, "formula": f,
        "taut_key": tk, "skel_key": sk,
        "taut_in_msg": tk in msg_taut, "skel_in_msg": sk in msg_skel,
        "taut_in_dev": tk in extra["muru_dev_pop"]["taut"], "skel_in_dev": sk in extra["muru_dev_pop"]["skel"],
        "taut_in_pr7": tk in extra["pr7"]["taut"], "skel_in_pr7": sk in extra["pr7"]["skel"],
        "taut_in_cmp": tk in extra["comparator"]["taut"], "skel_in_cmp": sk in extra["comparator"]["skel"],
        "msg_same_formula_n": len(msg_by_formula.get(f, [])),
        "msg_same_formula_max_tanimoto": round(nn, 4), "msg_nn_smiles": nn_smi,
        "in_msnlib9": r.in_msnlib9,
        "sg_in_registry": r.sg_in_registry, "sg_in_pr7": r.sg_in_pr7,
        "sg_in_comparator": r.sg_in_comparator, "sg_in_msg15": r.sg_in_msg15,
        "n_nce": r.n_nce, "nce_ladder": r.nce_ladder, "mh_calc": r.mh_calc, "releases": r.releases,
        "uchem_ids": r.uchem_ids,
    })
t = pd.DataFrame(rows)
t.to_csv("/tmp/v_c01_survivors_hidden.csv", index=False)

hit = t[t["taut_in_msg"] | t["skel_in_msg"] | t["taut_in_dev"] | t["skel_in_dev"]
        | t["taut_in_pr7"] | t["skel_in_pr7"] | t["taut_in_cmp"] | t["skel_in_cmp"]]
res["survivors_key_clean"] = int(len(t))
res["survivors_flagged_by_taut_or_skel"] = int(len(hit))
res["flagged"] = hit[["key", "name", "taut_in_msg", "skel_in_msg", "taut_in_dev", "skel_in_dev",
                      "taut_in_pr7", "taut_in_cmp", "msg_nn_smiles",
                      "msg_same_formula_max_tanimoto"]].to_dict("records")
res["max_same_formula_tanimoto_over_survivors"] = float(t["msg_same_formula_max_tanimoto"].max())
res["n_survivors_with_same_formula_msg_structure"] = int((t["msg_same_formula_n"] > 0).sum())
res["n_survivors_tanimoto_ge_0.7"] = int((t["msg_same_formula_max_tanimoto"] >= 0.7).sum())
res["n_survivors_tanimoto_ge_0.5"] = int((t["msg_same_formula_max_tanimoto"] >= 0.5).sum())
res["survivors_in_msnlib9"] = int(t["in_msnlib9"].sum())

# tiers after removing every taut/skel hit (my own version of the screen's step 4)
bad = set(hit["key"])
t["clean4"] = ~t["key"].isin(bad)
prim = t["clean4"] & ~(t["sg_in_registry"] | t["sg_in_pr7"] | t["sg_in_comparator"])
# primary as the verdict defines it uses the dev-population scaffold list, not the full registry
devpop_sg = set(pd.read_csv(WT / "artifacts/wur_v2/data/compounds.csv", usecols=["scaffold_group"])["scaffold_group"].dropna())
t["sg_in_devpop_file"] = t["sg"].isin(devpop_sg)
prim_v = t["clean4"] & ~(t["sg_in_devpop_file"] | t["sg_in_pr7"] | t["sg_in_comparator"])
cons = t["clean4"] & ~(t["sg_in_registry"] | t["sg_in_pr7"] | t["sg_in_comparator"])
strict = cons & ~t["sg_in_msg15"]
res["my_tiers_after_step4"] = {
    "compound_level": int(t["clean4"].sum()),
    "primary": int(prim_v.sum()), "primary_groups": int(t.loc[prim_v, "sg"].nunique()),
    "conservative": int(cons.sum()), "conservative_groups": int(t.loc[cons, "sg"].nunique()),
    "strict": int(strict.sum()), "strict_groups": int(t.loc[strict, "sg"].nunique()),
    "msnlib9_in_primary": int(t.loc[prim_v, "in_msnlib9"].sum()),
    "msnlib9_in_conservative": int(t.loc[cons, "in_msnlib9"].sum()),
}
print(json.dumps(res, indent=1, default=str))
Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-stability-study-6537d5/c50bb7b0-c2aa-4e0b-bd11-bc34c1ea3cbc/scratchpad/vscreen/v_hidden.json").write_text(
    json.dumps(res, indent=1, default=str))
