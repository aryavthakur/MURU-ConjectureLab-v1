"""CE interface adjudication, P5 step 1: identity-only exclusion sets (InChIKey first-block key lists).

Reads identity/key/structure columns only. Never opens any benchmark result, prediction, measured-mu or analysis file.
No model of any kind is run (the MURU support rule needs model predictions and is therefore NOT evaluated here).

Outputs (artifacts/ce_interface_adjudication/exclusion/):
  msg15_keys_{all,train,val,test}.txt                      MassSpecGym 1.5 recorded `inchikey` (already 14 chars)
  msg15_simchallenge_keys_{all,train,val,test}.txt         rows with simulation_challenge == True (ICEBERG msg_simulation)
  msg15_parent_keys_{all,train,val,test}.txt               MURU parent_connectivity_key of the MSG SMILES (if SMILES
                                                           available; see msg_smiles_source in the manifest)
  muru_exposure_registry_keys.txt / _scaffold_groups.txt   verbatim registry sets (sha256-verified)
  muru_exposure_registry_population_<NAME>_keys.txt        EXPOSED_POPULATION:<NAME> members, per population
  msnlib_study2_population_keys.txt / _scaffold_groups.txt PR #7 frozen validation population (1,794)
  comparator_common_population_keys.txt / _scaffold_groups.txt
  msnlib_v1_0_4lib_keys.txt                                FIORA-OS v0.1.0 training universe proxy (MCEBIO, NIHNP,
                                                           MCESCAF, OTAVAPEP plated compounds, 2025 cleaned tables)
  msnlib_9lib_keys.txt                                     all nine MSnLib libraries (FIORA-OS v1.0.0 universe proxy)
  msnlib_key_libraries.csv                                 key -> libraries, and which key route matched
  multims2_reserved_validation_secondary_keys.txt          informational: reserved, never decoded, not exposed
  muru_exposed_union_keys.txt                              registry | study-2 population | comparator population
  exclusion_manifest.json                                  counts, sha256, overlaps, provenance
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from rdkit import rdBase

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scaffold_key as SK  # noqa: E402

OUT = ROOT / "artifacts/ce_interface_adjudication/exclusion"
REG = ROOT / "artifacts/wur_v2_confirmation_v2/exposure_registry"
MSG_ID = ROOT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
MSG_META = ROOT / "artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet"   # P4 output, optional
MSPRED_LABELS = Path("/Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv")
MERLIN = Path("/Users/aryav/muru-msnlib/merlin_metadata")
DESIGN_CACHE = Path("/Users/aryav/muru-msnlib/cache/confirmation_v2")
CENSUS = ROOT / "artifacts/wur_v2/external_census/msnlib_census.json"
LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]
LIB_LABEL = {"mcebio": "MCEBIO", "mcescaf": "MCESCAF", "nihnp": "NIHNP", "otavapep": "OTAVAPEP", "enamdisc": "ENAMDISC",
             "enammol": "ENAMMOL", "mcedrug": "MCEDRUG", "mcediv_50k_sub": "MCEDIV", "targetmolhtsnp": "TARGETMOL"}
MSNLIB_V1_0 = {"MCEBIO", "NIHNP", "MCESCAF", "OTAVAPEP"}   # Zenodo 11163381 file names (p3_downloads record)
ID_COLS = ["plate_id", "well_location", "unique_sample_id", "smiles", "inchikey", "split_inchikey", "compound_name",
           "monoisotopic_mass", "structure_source"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_lines(items) -> str:
    return hashlib.sha256("\n".join(sorted(items)).encode()).hexdigest()


def write_list(name: str, items) -> dict:
    items = sorted({x for x in items if isinstance(x, str) and x})
    p = OUT / name
    p.write_text("\n".join(items) + ("\n" if items else ""))
    return {"file": f"exclusion/{name}", "n": len(items), "sha256_sorted_newline_joined": sha256_lines(items),
            "file_sha256": sha256_file(p)}


def load_design() -> tuple[pd.DataFrame, str]:
    """MERLIN plated-compound rows with MURU identity. Uses the study-2 design cache only if its content tag
    (MERLIN sha256 + identity.py sha256 + rdkit version, msnlib_design.load_design lines 90-102) reproduces."""
    census = json.loads(CENSUS.read_text())
    tables = census["inputs"]["design_tables"]
    hashes = {}
    for lib in LIBS:
        p = MERLIN / f"compounds__{lib}_cleaned.tsv"
        got = sha256_file(p)
        if got != tables[LIB_LABEL[lib]]["sha256"]:
            raise SystemExit(f"MERLIN table {p.name} sha256 mismatch")
        hashes[p.name] = got
    id_sha = sha256_file(ROOT / "src/muru/wur_v2/identity.py")
    tag = hashlib.sha256(json.dumps([hashes, id_sha, rdBase.rdkitVersion], sort_keys=True).encode()).hexdigest()[:16]
    cp = DESIGN_CACHE / f"design_identity_{tag}.pkl"
    if cp.is_file():
        d = pd.read_pickle(cp)
        src = f"cache {cp} (tag reproduced from MERLIN sha256, identity.py sha256 {id_sha[:12]}, rdkit {rdBase.rdkitVersion})"
    else:
        parts = []
        for lib in LIBS:
            p = MERLIN / f"compounds__{lib}_cleaned.tsv"
            cols = pd.read_csv(p, sep="\t", nrows=0).columns
            x = pd.read_csv(p, sep="\t", usecols=[c for c in ID_COLS if c in cols], dtype=str, low_memory=False)
            x["library"] = LIB_LABEL[lib]
            parts.append(x)
        d = pd.concat(parts, ignore_index=True)
        kg = [SK.key_and_group(s) for s in d.smiles]
        d["parent_key"] = [k for k, _ in kg]
        d["scaffold"] = [g for _, g in kg]
        d["key"] = d.parent_key
        src = "recomputed with scripts/ce_interface_adjudication/scaffold_key.py"
    # spot-check 300 rows against the standalone reimplementation
    chk = d.dropna(subset=["smiles"]).sample(300, random_state=0)
    n_ok = sum(SK.key_and_group(s)[0] == k for s, k in zip(chk.smiles, chk.parent_key))
    if n_ok != len(chk):
        raise SystemExit(f"design identity spot-check failed {n_ok}/{len(chk)}")
    return d, src + f"; spot-check 300/300 parent keys reproduced"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    man: dict = {"script": "scripts/ce_interface_adjudication/p5_01_build_exclusion_sets.py", "rdkit": rdBase.rdkitVersion,
                 "key_definition": "MURU parent_connectivity_key (src/muru/wur_v2/identity.py:45-50) unless a set says "
                                   "it holds a RECORDED first block", "sets": {}, "notes": []}
    S = man["sets"]
    sets: dict[str, set] = {}

    # (a) MassSpecGym 1.5 -----------------------------------------------------------------------------------------
    msg = pd.read_parquet(MSG_ID, columns=["identifier", "inchikey", "fold", "simulation_challenge"])
    assert len(msg) == 231_104 and (msg.inchikey.str.len() == 14).all()
    man["msg_identity_parquet_sha256"] = sha256_file(MSG_ID)
    for fold in ("all", "train", "val", "test"):
        sub = msg if fold == "all" else msg[msg.fold == fold]
        S[f"msg15_{fold}"] = write_list(f"msg15_keys_{fold}.txt", sub.inchikey)
        S[f"msg15_{fold}"]["n_rows"] = int(len(sub))
        S[f"msg15_{fold}"]["key_kind"] = "MassSpecGym recorded inchikey column (14-char first block as released)"
        sc = sub[sub.simulation_challenge]
        S[f"msg15_simchallenge_{fold}"] = write_list(f"msg15_simchallenge_keys_{fold}.txt", sc.inchikey)
        S[f"msg15_simchallenge_{fold}"]["n_rows"] = int(len(sc))
        sets[f"msg15_{fold}"] = set(sub.inchikey)
    man["msg15_keys_in_more_than_one_fold"] = int((msg.groupby("inchikey").fold.nunique() > 1).sum())

    # MURU-definition parent keys of MassSpecGym SMILES
    if MSG_META.exists():
        meta = pd.read_parquet(MSG_META, columns=["identifier", "smiles"])
        smi = msg.merge(meta, on="identifier", how="left", validate="1:1")
        man["msg_smiles_source"] = f"{MSG_META.relative_to(ROOT)} (P4 range read), sha256 {sha256_file(MSG_META)}"
    else:
        lab = pd.read_csv(MSPRED_LABELS, sep="\t", usecols=["spec", "smiles"]).rename(columns={"spec": "identifier"})
        smi = msg.merge(lab, on="identifier", how="left", validate="1:1")
        man["msg_smiles_source"] = (f"{MSPRED_LABELS} (ms-pred ed8311f committed labels; simulation_challenge rows only, "
                                    f"{int(smi.smiles.notna().sum())} of {len(smi)} rows)")
    uniq = smi.dropna(subset=["smiles"]).smiles.unique()
    pk = {s: SK.key_and_group(s) for s in uniq}
    smi["parent_key"] = smi.smiles.map(lambda s: pk[s][0] if isinstance(s, str) else None)
    smi["scaffold_group"] = smi.smiles.map(lambda s: pk[s][1] if isinstance(s, str) else None)
    has = smi.smiles.notna()
    for fold in ("all", "train", "val", "test"):
        sub = smi[has] if fold == "all" else smi[has & (smi.fold == fold)]
        S[f"msg15_parent_{fold}"] = write_list(f"msg15_parent_keys_{fold}.txt", sub.parent_key)
        S[f"msg15_parent_{fold}"]["n_rows_with_smiles"] = int(len(sub))
        sets[f"msg15_parent_{fold}"] = set(sub.parent_key.dropna())
    dis = smi[has & smi.parent_key.notna() & (smi.parent_key != smi.inchikey)]
    man["msg15_recorded_vs_parent_key"] = {
        "rows_with_smiles": int(has.sum()), "rows_parent_key_unformable": int((has & smi.parent_key.isna()).sum()),
        "rows_recorded_ne_parent": int(len(dis)), "distinct_recorded_keys_ne_parent": int(dis.inchikey.nunique()),
        "examples": dis.drop_duplicates("inchikey").head(8)[["inchikey", "parent_key", "smiles"]].values.tolist()}
    smi[["identifier", "inchikey", "parent_key", "scaffold_group"]].to_parquet(OUT / "msg15_row_keys.parquet", index=False)
    S["msg15_row_keys_parquet"] = {"file": "exclusion/msg15_row_keys.parquet", "file_sha256": sha256_file(OUT / "msg15_row_keys.parquet")}
    sets["msg15_scaffold_groups_all"] = set(smi.scaffold_group.dropna())
    S["msg15_scaffold_groups_all"] = write_list("msg15_scaffold_groups_all.txt", smi.scaffold_group)

    # (b) MURU exposure registry ----------------------------------------------------------------------------------
    rm = json.loads((REG / "registry_manifest.json").read_text())
    for fn in ("excluded_compound_keys.txt", "excluded_scaffold_groups.txt", "excluded_compounds.csv"):
        if sha256_file(REG / fn) != rm["output_file_sha256"][fn]:
            raise SystemExit(f"registry file {fn} sha256 does not match registry_manifest.json")
    rkeys = set((REG / "excluded_compound_keys.txt").read_text().split())
    rgroups = set((REG / "excluded_scaffold_groups.txt").read_text().splitlines()) - {""}
    assert sha256_lines(rkeys) == rm["hashes_sorted_newline_joined"]["excluded_compound_keys_sha256"]
    assert sha256_lines(rgroups) == rm["hashes_sorted_newline_joined"]["excluded_scaffold_groups_sha256"]
    S["muru_exposure_registry"] = write_list("muru_exposure_registry_keys.txt", rkeys)
    S["muru_exposure_registry_scaffold_groups"] = write_list("muru_exposure_registry_scaffold_groups.txt", rgroups)
    sets["muru_exposure_registry"] = rkeys
    ec = pd.read_csv(REG / "excluded_compounds.csv", usecols=["key", "reasons"])
    reasons = ec.assign(r=ec.reasons.str.split(";")).explode("r")
    per_reason = reasons.r.value_counts().to_dict()
    man["registry_per_reason_recount_matches_manifest"] = {k: int(v) for k, v in per_reason.items()} == rm["counts"]["per_reason_compounds"]
    man["registry_covers"] = {"study_id": rm["study_id"], "utc": rm["utc"], "rule": rm["rule"],
                              "exposed_populations": rm["inputs"]["population_key_counts"],
                              "other_reasons": {k: v for k, v in rm["counts"]["per_reason_compounds"].items()
                                                if not k.startswith("EXPOSED_POPULATION:")},
                              "not_excluded_disclosures": rm["not_excluded_disclosures"]}
    for name in sorted(r for r in per_reason if r.startswith("EXPOSED_POPULATION:")):
        tag = name.split(":", 1)[1]
        S[f"registry_pop_{tag}"] = write_list(f"muru_exposure_registry_population_{tag}_keys.txt",
                                              reasons[reasons.r == name].key)
    direct = set(reasons[reasons.r != "SCAFFOLD_GROUP_EXCLUDED"].key)
    S["muru_exposure_registry_direct_reason"] = write_list("muru_exposure_registry_keys_direct_reason.txt", direct)
    S["muru_exposure_registry_direct_reason"]["note"] = ("registry keys with at least one reason other than "
                                                         "SCAFFOLD_GROUP_EXCLUDED (the rest are excluded only because "
                                                         "their MSnLib census scaffold group was excluded)")
    sets["muru_exposure_registry_direct_reason"] = direct
    anc = reasons[reasons.r == "MULTIMS2_ANCHOR_CALIBRATION"].key
    S["registry_pop_MultiMS2-ANCHOR"] = write_list("muru_exposure_registry_population_MultiMS2-ANCHOR_keys.txt", anc)

    # (c) MSnLib confirmation study 2 (PR #7) frozen population ----------------------------------------------------
    vp = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv", usecols=["key", "scaffold_group"])
    fm = json.loads((ROOT / "artifacts/wur_v2_confirmation_v2/freeze/freeze_manifest.json").read_text())
    assert sha256_lines(set(vp.key)) == fm["population_key_hash"] and sha256_lines(set(vp.scaffold_group)) == fm["scaffold_group_hash"]
    S["msnlib_study2_population"] = write_list("msnlib_study2_population_keys.txt", vp.key)
    S["msnlib_study2_population_scaffold_groups"] = write_list("msnlib_study2_population_scaffold_groups.txt", vp.scaffold_group)
    S["msnlib_study2_population"]["note"] = ("frozen validation population (freeze_manifest population_key_hash reproduced). "
                                             "The subset actually scored is only in the result directory, which is not "
                                             "read; the frozen superset is the conservative exclusion.")
    sets["msnlib_study2_population"] = set(vp.key)
    s1 = set((ROOT / "artifacts/wur_v2_confirmation_v2/population/sampled_scaffold_groups.txt").read_text().splitlines()) - {""}
    man["study2_sampled_groups_n"] = len(s1)

    # (d) comparator benchmark common population --------------------------------------------------------------------
    cp = pd.read_csv(ROOT / "artifacts/comparator_benchmark/population/common_population.csv", usecols=["key", "scaffold_group"])
    ck = set((ROOT / "artifacts/comparator_benchmark/population/common_population_keys.txt").read_text().split())
    assert ck == set(cp.key)
    S["comparator_common_population"] = write_list("comparator_common_population_keys.txt", ck)
    S["comparator_common_population_scaffold_groups"] = write_list("comparator_common_population_scaffold_groups.txt", cp.scaffold_group)
    sets["comparator_common_population"] = ck

    # (e) MSnLib library universes (FIORA-OS v0.1.0 = MSnLib v1.0; v1.0.0 = all 9) ----------------------------------
    design, dsrc = load_design()
    man["msnlib_design_identity_source"] = dsrc
    design["recorded_fb"] = design.split_inchikey.map(SK.first_block)
    rec = design.dropna(subset=["recorded_fb"])[["recorded_fb", "library"]].rename(columns={"recorded_fb": "k"}).assign(route="recorded")
    par = design.dropna(subset=["parent_key"])[["parent_key", "library"]].rename(columns={"parent_key": "k"}).assign(route="parent")
    kl = pd.concat([rec, par])
    agg = kl.groupby("k").agg(libraries=("library", lambda s: ";".join(sorted(set(s)))),
                              routes=("route", lambda s: ";".join(sorted(set(s))))).reset_index().rename(columns={"k": "key"})
    agg["in_msnlib_v1_0"] = agg.libraries.str.split(";").map(lambda L: bool(set(L) & MSNLIB_V1_0))
    agg.to_csv(OUT / "msnlib_key_libraries.csv", index=False)
    S["msnlib_key_libraries_csv"] = {"file": "exclusion/msnlib_key_libraries.csv", "n": int(len(agg)),
                                     "file_sha256": sha256_file(OUT / "msnlib_key_libraries.csv")}
    v1 = set(kl[kl.library.isin(MSNLIB_V1_0)].k)
    all9 = set(kl.k)
    S["msnlib_v1_0_4lib"] = write_list("msnlib_v1_0_4lib_keys.txt", v1)
    S["msnlib_v1_0_4lib"]["note"] = ("union of recorded split_inchikey first blocks and MURU parent keys of plated rows in "
                                     "the 2025 MERLIN cleaned tables of MCEBIO, NIHNP, MCESCAF, OTAVAPEP; a proxy for "
                                     "the 2024 MSnLib v1.0 MGF compound set (not verified against v1.0 MGF headers)")
    S["msnlib_9lib"] = write_list("msnlib_9lib_keys.txt", all9)
    sets["msnlib_v1_0_4lib"], sets["msnlib_9lib"] = v1, all9
    man["msnlib_key_route_counts"] = {
        "v1_0_parent_only": len(set(par[par.library.isin(MSNLIB_V1_0)].k) - set(rec[rec.library.isin(MSNLIB_V1_0)].k)),
        "v1_0_recorded_only": len(set(rec[rec.library.isin(MSNLIB_V1_0)].k) - set(par[par.library.isin(MSNLIB_V1_0)].k)),
        "per_library_keys": {lib: int(kl[kl.library == lib].k.nunique()) for lib in sorted(kl.library.unique())}}

    # cross-check against the feasibility audit's per-compound flags (identity columns only)
    ov = pd.read_csv(ROOT / "artifacts/comparator_feasibility/overlap_support_per_compound.csv",
                     usecols=["key", "in_msnlib_v1_0", "in_msnlib_16984129", "msg_folds"])
    ov["mine_v1"] = ov.key.isin(v1)
    ov["mine_msg"] = ov.key.isin(sets["msg15_all"])
    man["crosscheck_feasibility_audit_1794"] = {
        "audit_in_msnlib_v1_0": int(ov.in_msnlib_v1_0.sum()), "this_in_msnlib_v1_0": int(ov.mine_v1.sum()),
        "audit_true_this_false": int((ov.in_msnlib_v1_0 & ~ov.mine_v1).sum()),
        "audit_false_this_true": int((~ov.in_msnlib_v1_0 & ov.mine_v1).sum()),
        "audit_in_msg_any": int(ov.msg_folds.notna().sum()), "this_in_msg_any": int(ov.mine_msg.sum()),
        "audit_in_msnlib_16984129": int(ov.in_msnlib_16984129.sum())}

    # informational: MultiMS2 reserved populations (never decoded, not exposed, not in registry)
    pj = json.loads((ROOT / "artifacts/wur_v2/external/populations.json").read_text())["populations"]
    res = {r["key"] for pop in ("VALIDATION", "SECONDARY") for r in pj[pop]}
    S["multims2_reserved_validation_secondary"] = write_list("multims2_reserved_validation_secondary_keys.txt", res)
    S["multims2_reserved_validation_secondary"]["note"] = "not exposed; listed so a future study does not burn them silently"
    sets["multims2_reserved"] = res

    union = sets["muru_exposure_registry"] | sets["msnlib_study2_population"] | sets["comparator_common_population"]
    S["muru_exposed_union"] = write_list("muru_exposed_union_keys.txt", union)
    sets["muru_exposed_union"] = union

    names = ["muru_exposure_registry", "muru_exposure_registry_direct_reason", "msnlib_study2_population", "comparator_common_population", "msnlib_v1_0_4lib",
             "msnlib_9lib", "multims2_reserved", "msg15_all", "msg15_train", "msg15_val", "msg15_test", "msg15_parent_all"]
    man["pairwise_overlap_counts"] = {a: {b: len(sets[a] & sets[b]) for b in names} for a in names}
    man["checks"] = {"comparator_subset_of_study2": sets["comparator_common_population"] <= sets["msnlib_study2_population"],
                     "study2_disjoint_from_registry": not (sets["msnlib_study2_population"] & sets["muru_exposure_registry"]),
                     "study2_subset_of_msnlib_9lib": sets["msnlib_study2_population"] <= sets["msnlib_9lib"]}
    (OUT / "exclusion_manifest.json").write_text(json.dumps(man, indent=1, default=str) + "\n")
    print(json.dumps({k: v.get("n") for k, v in S.items()}, indent=1))
    print(json.dumps({k: man[k] for k in ("checks", "crosscheck_feasibility_audit_1794", "msg15_recorded_vs_parent_key",
                                          "msnlib_key_route_counts", "registry_per_reason_recount_matches_manifest",
                                          "msg_smiles_source")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
