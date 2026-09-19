"""Design B sourcing screen, step 2: mechanical eligibility census of the purchasable candidate universe.

Catalogue identity metadata only (output of 10_fetch_catalogues.py) plus the frozen Phase 0 identity exclusion
key sets. No spectrum, no MS/MS outcome, no model. This is a feasibility census, NOT the final random draw.

Chemical = MURU parent connectivity key (scaffold_key.parent_connectivity_key: largest organic fragment,
Uncharger, first InChIKey block). Vendor listings of the same chemical (including salt forms) are merged.
Rules, in binding order, at chemical level (a chemical passes a listing-level rule if ANY listing passes):
  S1 structure: standardized PubChem CID with a parseable structure and a parent key
  S2 mass window: theoretical [M+H]+ (parent ExactMolWt + proton) in L 130-300, N 485-515 or H 700-900
  S3 single covalent unit: the catalogue structure has exactly one component (no salt, solvate or mixture)
  S4 no permanent charge: after Uncharger, net charge 0 and every charged atom bonded to an opposite charge
  S5 no isotope labels (the model input is the unlabelled structure)
  S6 model input limits: elements in ms-pred VALID_ELEMENTS, heavy atoms <= 160, [M+H]+ <= 995.556
  S7 absent from MassSpecGym 1.5 / ms-pred msg labels: recorded key, parent key, ms-pred labels (recorded and
     parent), and the canonical-tautomer key restricted to identical formulae (Design A rule R8m)
  S8 absent from the Design A population
  S9 absent from the PR #8 comparator population
  S10 purity >= 95% where catalogue purity is available (PubChem deposits carry none: no exclusion possible here)
Then at most one chemical per scaffold group (scaffold_key.scaffold_group): usable count = distinct groups.
"""
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, inchi
from rdkit.Chem.MolStandardize import rdMolStandardize

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1]))
import scaffold_key as SK  # noqa: E402

RDLogger.DisableLog("rdApp.*")
A = REPO / "artifacts/ce_interface_adjudication"
DL = A / "design_b/sourcing/downloads"
OUT = A / "design_b/sourcing"
EX = A / "exclusion"
MSPRED_LABELS = Path("/Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv")
DESIGN_A = A / "design_a/population/design_a_compounds.csv"

PROTON_MASS = 1.00727646688  # as Design A
STRATA = {"L": (130.0, 300.0), "N": (485.0, 515.0), "H": (700.0, 900.0)}
VALID_ELEMENTS = frozenset(["C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se", "Fe", "Co",
                            "As", "Na", "K"])
MAX_ATOM_CT = 160
PRECURSOR_BOUND = 995.556
SOURCE_ORDER = ["MedChemexpress MCE", "TargetMol", "Selleck Chemicals"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stratum(mh):
    for s, (lo, hi) in STRATA.items():
        if lo <= mh <= hi:
            return s
    return None


def per_structure(smi):
    """Everything computed from one catalogue structure (CID-level SMILES)."""
    m0 = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
    if m0 is None:
        return dict(parse_ok=False)
    pk = SK.parent_connectivity_key(smi)
    pm = SK.parent_mol(smi)
    if pk is None or pm is None:
        return dict(parse_ok=False)
    mh = float(Descriptors.ExactMolWt(pm) + PROTON_MASS)
    n_comp = len(Chem.GetMolFrags(m0))
    single = m0 if n_comp == 1 else None
    perm = True
    if single is not None:
        u = rdMolStandardize.Uncharger().uncharge(Chem.Mol(single))
        net = sum(a.GetFormalCharge() for a in u.GetAtoms())
        ok = net == 0 and all(a.GetFormalCharge() == 0 or any(n.GetFormalCharge() * a.GetFormalCharge() < 0
                                                               for n in a.GetNeighbors()) for a in u.GetAtoms())
        perm = not ok
    iso = any(a.GetIsotope() for a in m0.GetAtoms())
    elems = {a.GetSymbol() for a in Chem.AddHs(pm).GetAtoms()}
    return dict(parse_ok=True, parent_key=pk, mh=mh, stratum=stratum(mh), single_unit=n_comp == 1,
                permanent_charge=perm, isotope_labelled=iso, elements=",".join(sorted(elems)),
                elements_ok=elems <= VALID_ELEMENTS, heavy_atoms=pm.GetNumHeavyAtoms(),
                parent_smiles=Chem.MolToSmiles(pm), formula=Chem.rdMolDescriptors.CalcMolFormula(pm))


def taut_key(smi):
    try:
        pm = SK.parent_mol(smi)
        if pm is None:
            return None
        t = rdMolStandardize.TautomerEnumerator().Canonicalize(pm)
        k = inchi.MolToInchiKey(t)
        return k.split("-")[0] if k else None
    except Exception:  # noqa: BLE001
        return None


def main():
    import _scope_gate  # project-scope closure 2026-09-19: Design B cancelled, never executes
    _scope_gate.refuse()
    lst = pd.concat([pd.read_csv(DL / f"{s.split()[0].lower()}_sid_registry_cid.csv") for s in SOURCE_ORDER],
                    ignore_index=True)
    props = pd.read_csv(DL / "cid_properties.csv").rename(columns={"CID": "cid"})
    lst = lst.merge(props, on="cid", how="left")
    counts = {"raw_listings_screened": int(len(lst)),
              "raw_listings_by_source": lst["source"].value_counts().to_dict()}

    uniq = lst["SMILES"].dropna().unique().tolist()
    with ProcessPoolExecutor() as ex:
        res = dict(zip(uniq, ex.map(per_structure, uniq, chunksize=500)))
    st = pd.DataFrame([dict(SMILES=k, **v) for k, v in res.items()])
    lst = lst.merge(st, on="SMILES", how="left")
    lst["parse_ok"] = lst["parse_ok"].fillna(False).astype(bool)
    counts["listings_with_structure"] = int(lst["parse_ok"].sum())
    L = lst[lst["parse_ok"]].copy()
    for c in ("single_unit", "permanent_charge", "isotope_labelled", "elements_ok"):
        L[c] = L[c].astype(bool)
    counts["S1_unique_chemicals_after_vendor_dedup"] = int(L["parent_key"].nunique())

    # chemical-level table: listing-level rules pass if ANY listing passes
    L["listing_ok_S3"] = L["single_unit"]
    L["listing_ok_S4"] = L["single_unit"] & ~L["permanent_charge"]
    L["listing_ok_S5"] = L["listing_ok_S4"] & ~L["isotope_labelled"]
    L["src_rank"] = L["source"].map({s: i for i, s in enumerate(SOURCE_ORDER)})
    L = L.sort_values(["parent_key", "listing_ok_S5", "listing_ok_S4", "listing_ok_S3", "src_rank", "cid"],
                      ascending=[True, False, False, False, True, True])
    g = L.groupby("parent_key", sort=False)
    chem = g.first()[["parent_smiles", "mh", "stratum", "formula", "elements", "elements_ok", "heavy_atoms",
                      "InChIKey", "Title", "source", "catalogue_id", "cid"]].rename(
        columns={"source": "primary_source", "catalogue_id": "primary_catalogue_id", "cid": "primary_cid",
                 "InChIKey": "primary_listing_inchikey", "Title": "compound_name"})
    chem["n_listings"] = g.size()
    chem["vendors"] = g["source"].agg(lambda s: ";".join(sorted(set(s))))
    chem["catalogue_ids"] = g.apply(lambda d: ";".join(sorted({f"{a}:{b}" for a, b in zip(d["source"], d["catalogue_id"])})))
    for r in ("S3", "S4", "S5"):
        chem[f"any_{r}"] = g[f"listing_ok_{r}"].any()
    chem = chem.reset_index()

    E = {n: set(Path(EX / f).read_text().split()) for n, f in {
        "msg_recorded": "msg15_keys_all.txt", "msg_parent": "msg15_parent_keys_all.txt",
        "comparator": "comparator_common_population_keys.txt"}.items()}
    lab = pd.read_csv(MSPRED_LABELS, sep="\t", usecols=["smiles", "inchikey"])
    E["mspred_recorded"] = set(lab["inchikey"].dropna().map(lambda k: k.split("-")[0]))
    with ProcessPoolExecutor() as ex:
        E["mspred_parent"] = {k for k in ex.map(SK.parent_connectivity_key, lab["smiles"].dropna().unique().tolist(),
                                                chunksize=500) if k}
    E["design_a"] = set(pd.read_csv(DESIGN_A)["compound_id"])

    reason = pd.Series(None, index=chem.index, dtype=object)

    def mark(mask, text):
        nonlocal reason
        reason = reason.where(reason.notna() | ~mask, text)
        return int((reason.isna()).sum())

    steps = {}
    steps["S2_in_a_mass_window"] = mark(chem["stratum"].isna(), "S2 theoretical [M+H]+ outside all three windows")
    steps["S3_single_covalent_unit"] = mark(~chem["any_S3"], "S3 not a single covalent unit (salt, solvate or mixture) in any listing")
    steps["S4_no_permanent_charge"] = mark(~chem["any_S4"], "S4 permanent or net charge in every single-unit listing")
    steps["S5_no_isotope_label"] = mark(~chem["any_S5"], "S5 isotope-labelled in every eligible listing")
    s6 = ~chem["elements_ok"].astype(bool) | (chem["heavy_atoms"] > MAX_ATOM_CT) | (chem["mh"] > PRECURSOR_BOUND)
    steps["S6_model_input_limits"] = mark(s6, "S6 outside ms-pred element set, heavy-atom or precursor limits")
    k = chem["parent_key"]
    rk = chem["primary_listing_inchikey"].fillna("").str.split("-").str[0]
    msg_direct = (k.isin(E["msg_recorded"] | E["msg_parent"] | E["mspred_recorded"] | E["mspred_parent"])
                  | rk.isin(E["msg_recorded"] | E["mspred_recorded"]))
    steps["S7a_absent_from_msg15_by_key"] = mark(msg_direct, "S7a in MassSpecGym 1.5 / ms-pred msg labels (key routes)")

    # S7b tautomer route, restricted to identical formulae (exact restriction, as Design A R8m)
    alive = reason.isna()
    forms = set(chem.loc[alive, "formula"])
    mm = pd.read_parquet(A / "massspecgym15_metadata_columns.parquet", columns=["smiles", "formula"]).drop_duplicates("smiles")
    ref = pd.concat([mm[["smiles", "formula"]], pd.DataFrame({"smiles": lab["smiles"].dropna().unique()})])
    ref = ref.drop_duplicates("smiles")
    ref["pformula"] = [Chem.rdMolDescriptors.CalcMolFormula(SK.parent_mol(s)) if SK.parent_mol(s) is not None else None
                       for s in ref["smiles"]]
    ref = ref[ref["pformula"].isin(forms)]
    with ProcessPoolExecutor() as ex:
        msg_taut = {t for t in ex.map(taut_key, ref["smiles"].tolist(), chunksize=50) if t}
        cand_taut = dict(zip(chem.loc[alive, "parent_key"],
                             ex.map(taut_key, chem.loc[alive, "parent_smiles"].tolist(), chunksize=50)))
    chem["taut_key"] = chem["parent_key"].map(cand_taut)
    steps["S7b_absent_from_msg15_by_tautomer"] = mark(chem["taut_key"].isin(msg_taut) & chem["taut_key"].notna(),
                                                       "S7b in MassSpecGym 1.5 by canonical-tautomer key")
    steps["S8_absent_from_design_a"] = mark(k.isin(E["design_a"]), "S8 in the Design A population")
    steps["S9_absent_from_pr8"] = mark(k.isin(E["comparator"]), "S9 in the PR #8 comparator population")
    steps["S10_purity_ge_95_where_stated"] = int(reason.isna().sum())  # no purity field in the deposits
    chem["exclusion_reason"] = reason
    chem["eligible"] = reason.isna()
    chem["purity_stated"] = None
    chem["stock_status"] = None

    el = chem[chem["eligible"]].copy()
    el["scaffold_group"] = [SK.scaffold_group(s, kk) for s, kk in zip(el["parent_smiles"], el["parent_key"])]
    chem = chem.merge(el[["parent_key", "scaffold_group"]], on="parent_key", how="left")

    # window-level attrition (chemicals whose [M+H]+ is in the stratum window)
    order = ["S3", "S4", "S5", "S6", "S7a", "S7b", "S8", "S9"]
    per = {}
    for s in STRATA:
        c = chem[chem["stratum"] == s]
        row = {"in_window": int(len(c))}
        left = len(c)
        for r in order:
            left -= int(c["exclusion_reason"].fillna("").str.startswith(r + " ").sum())
            row[f"after_{r}"] = left
        row["eligible_chemicals"] = int(c["eligible"].sum())
        row["distinct_scaffold_groups"] = int(c.loc[c["eligible"], "scaffold_group"].nunique())
        per[s] = row
    # one chemical per scaffold group across the whole design; shared groups go to the scarcer stratum
    grp = {s: set(chem.loc[(chem["stratum"] == s) & chem["eligible"], "scaffold_group"]) for s in STRATA}
    usable, taken = {}, set()
    for s in sorted(STRATA, key=lambda x: len(grp[x])):
        usable[s] = len(grp[s] - taken)
        taken |= grp[s]
    nL, nH, nN = usable["L"], usable["H"], usable["N"]
    n_eff = 4 / (1 / nL + 1 / nH) if nL and nH else 0.0

    chem["mh"] = chem["mh"].round(5)
    cols = ["parent_key", "stratum", "mh", "compound_name", "parent_smiles", "formula", "primary_source",
            "primary_catalogue_id", "primary_cid", "vendors", "catalogue_ids", "n_listings", "purity_stated",
            "stock_status", "scaffold_group", "eligible", "exclusion_reason"]
    win = chem[chem["stratum"].notna()][cols].sort_values(["stratum", "parent_key"])
    win.to_csv(OUT / "candidate_ledger_in_windows.csv.gz", index=False)
    eu = win[win["eligible"]].drop(columns=["eligible", "exclusion_reason"])
    eu.to_csv(OUT / "eligible_universe.csv", index=False)
    summ = {
        "study": "muru-ce-interface-adjudication-design-b-sourcing-screen",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "catalogues": SOURCE_ORDER,
        "provenance": "PubChem PUG REST vendor deposits (substance/sourceall/<source>/sids; sid xrefs RegistryID; "
                      "standardized CIDs; CID properties). Retrieval recorded in downloads_register.jsonl.",
        "counts": counts, "chemical_level_cascade_remaining": steps, "per_stratum": per,
        "usable_after_one_per_scaffold_group_across_design": usable,
        "N_eff_LH": round(n_eff, 2),
        "go_rule": {"N_eff>=120": n_eff >= 120, "nL>=50": nL >= 50, "nH>=50": nH >= 50, "nN>=60": nN >= 60},
        "procurement_66_66_66_possible": all(usable[s] >= 66 for s in STRATA),
        "purity_and_stock": "not present in PubChem vendor deposits; no purity exclusion applied (rule S10 applies "
                            "only where purity is stated); see spot check",
        "exclusion_sets_sha256": {f: sha(EX / f) for f in ["msg15_keys_all.txt", "msg15_parent_keys_all.txt",
                                                           "comparator_common_population_keys.txt"]}
        | {"mspred_labels.tsv": sha(MSPRED_LABELS), "design_a_compounds.csv": sha(DESIGN_A)},
        "eligible_universe_sha256": sha(OUT / "eligible_universe.csv"),
        "candidate_ledger_sha256": sha(OUT / "candidate_ledger_in_windows.csv.gz"),
        "rdkit": Chem.rdBase.rdkitVersion,
    }
    (OUT / "sourcing_screen_summary.json").write_text(json.dumps(summ, indent=1, default=int) + "\n")
    print(json.dumps({k: summ[k] for k in ("counts", "chemical_level_cascade_remaining", "per_stratum",
                                           "usable_after_one_per_scaffold_group_across_design", "N_eff_LH",
                                           "go_rule", "procurement_66_66_66_possible")}, indent=1, default=int))


if __name__ == "__main__":
    main()
