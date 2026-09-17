#!/usr/bin/env python3
"""S2 screen C02 (CyanoMetDB in MassBank 2026.03): criteria evaluation on top of the harvest.

Inputs (all already on disk, metadata only):
  screen/c02_cyanometdb/{records.csv,compounds.csv,summary.json}  (screen_c02_cyanometdb.py,
      re-run in this task and reproduced bit for bit)
  screen/c02_cyanometdb/downloads_s2/*                            (screen_c02_cyanometdb_s2_fetch.py,
      screen_c02_cyanometdb_s2_counts.py)
  artifacts/ce_interface_adjudication/massspecgym15_identity_metadata_joined.parquet
  /Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv
  /Users/aryav/muru-comparators/repos/ms-pred/src/ms_pred/common/chem_utils.py (constants, read not imported)

Outputs (screen/c02_cyanometdb/):
  s2_design_sets.csv      per compound row, the design-set membership flags used below
  s2_msg_overlap_rows.csv MassSpecGym 1.5 row metadata for every overlapping compound key
  s2_criteria.json        criterion-by-criterion status and the counts behind each

No model is run; no spectra file is read.
"""
import collections
import json
import re
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
W = Path(__file__).resolve().parents[2]
OUT = W / "artifacts/ce_interface_adjudication/screen/c02_cyanometdb"
DL2 = OUT / "downloads_s2"
MSPRED = Path("/Users/aryav/muru-comparators/repos/ms-pred")

MSG_MAX_PRECURSOR = 999.396          # MassSpecGym 1.5 max precursor_mz (re-verified in the harvest)
MURU_MH_RANGE = (70.0, 1042.6)       # src/muru/wur_v2/msnlib_design.py:27 DEV_MH_RANGE
GLACIER_UPPER_LIMIT = 1500           # glacier_msg/best.ckpt hyper_parameters.upper_limit
MAX_ATOM_CT = 160                    # ms-pred common/chem_utils.py:132
# ms-pred common/chem_utils.py:131 NORM_VEC, in the element order of VALID_ELEMENTS
NORM_VEC_ELEMENTS = ["C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se",
                     "Fe", "Co", "As", "Na", "K"]
NORM_VEC = [81, 19, 6, 34, 6, 6, 6, 158, 10, 17, 3, 1, 2, 1, 1, 2, 1, 1]


def vc(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).items()}


def main():
    C = pd.read_csv(OUT / "compounds.csv")
    R = pd.read_csv(OUT / "records.csv")
    summ = json.load(open(OUT / "summary.json"))
    res = {}

    # ---------------------------------------------------------------- 1. design sets
    base = C["has_mh"].fillna(False) & (C["n_mh_distinct_nce"].fillna(0) >= 3)
    single = ~C["unit_is_group"].fillna(False)
    key_clean = (~C["in_msg15_any_route"]) & (~C["in_muru_registry"]) & (~C["in_study2"]) & (~C["in_comparator"])
    scaf_clean = (~C["scaf_in_muru_registry"]) & (~C["scaf_in_study2"]) & (~C["scaf_in_comparator"])
    in_msg_range = C["mh_theor"] <= MSG_MAX_PRECURSOR
    in_muru_range = C["mh_theor"].between(*MURU_MH_RANGE)
    lvl1 = C["level"].astype(str) == "1"
    lvl12a = C["level"].astype(str).isin(["1", "2a"])
    nce2060 = C["has_nce20_and_nce60"].fillna(False).astype(bool)
    fm40_2060 = C["has_nce20_and_nce60_first_mass_40"].fillna(False).astype(bool)

    sets = {
        "P0_all_mh_ge3nce": base,
        "P1_single_identity": base & single,
        "P2_key_clean": base & single & key_clean,
        "P3_key_and_scaffold_clean": base & single & key_clean & scaf_clean,
        "P4_P3_nce20_60": base & single & key_clean & scaf_clean & nce2060,
        "P5_P4_msg_range": base & single & key_clean & scaf_clean & nce2060 & in_msg_range,
        "P6_P4_muru_range": base & single & key_clean & scaf_clean & nce2060 & in_muru_range,
        "P7_P5_level1_2a": base & single & key_clean & scaf_clean & nce2060 & in_msg_range & lvl12a,
        "P8_P5_level1": base & single & key_clean & scaf_clean & nce2060 & in_msg_range & lvl1,
        "P9_P5_first_mass_40": base & single & key_clean & scaf_clean & in_msg_range & fm40_2060,
        "P10_P9_level1_2a": base & single & key_clean & scaf_clean & in_msg_range & fm40_2060 & lvl12a,
    }
    flags = pd.DataFrame({k: v for k, v in sets.items()})
    keep = ["cyanometdb_id", "name", "level", "purity", "unit_id", "unit_is_group", "muru_key",
            "scaffold_group", "mh_theor", "formula_rdkit", "heavy_atoms", "mh_nce_set",
            "n_mh_distinct_nce", "n_mh_distinct_nce_first_mass_40", "has_nce20_and_nce60",
            "has_nce20_and_nce60_first_mass_40", "mh_series", "mh_instruments",
            "in_msg15_any_route", "in_msg15_simchallenge", "in_muru_registry", "in_study2",
            "in_comparator", "scaf_in_msg15", "msg15_nn_tanimoto"]
    D = pd.concat([C[keep], flags], axis=1)

    def describe(mask):
        sub = C[mask]
        g = sub.groupby("scaffold_group")["muru_key"].nunique()
        return {
            "n_compounds": int(sub["muru_key"].nunique()),
            "n_compound_rows": int(len(sub)),
            "n_scaffold_groups": int(sub["scaffold_group"].nunique()),
            "n_scaffold_groups_singleton": int((g == 1).sum()),
            "max_compounds_in_one_scaffold_group": int(g.max()) if len(g) else 0,
            "n_scaffold_groups_also_in_msg15": int(sub.loc[sub["scaf_in_msg15"], "scaffold_group"].nunique()),
            "mh_min": round(float(sub["mh_theor"].min()), 2) if len(sub) else None,
            "mh_median": round(float(sub["mh_theor"].median()), 2) if len(sub) else None,
            "mh_max": round(float(sub["mh_theor"].max()), 2) if len(sub) else None,
            "n_mh_gt_msg_label_max_995_556": int((sub["mh_theor"] > 995.556).sum()),
            "n_mh_gt_msg15_max": int((sub["mh_theor"] > MSG_MAX_PRECURSOR).sum()),
            "n_mh_gt_muru_dev_max": int((sub["mh_theor"] > MURU_MH_RANGE[1]).sum()),
            "n_mh_gt_glacier_upper": int((sub["mh_theor"] > GLACIER_UPPER_LIMIT).sum()),
            "level_counts": vc(sub["level"].astype(str)),
            "series": vc(sub["mh_series"].astype(str)),
        }

    res["design_sets"] = {k: describe(v) for k, v in sets.items()}

    # ---------------------------------------------------------------- 2. element/atom domain
    def counts(smi):
        m = Chem.MolFromSmiles(smi) if isinstance(smi, str) else None
        if m is None:
            return None
        m = Chem.AddHs(m)
        c = collections.Counter(a.GetSymbol() for a in m.GetAtoms())
        return c

    over = collections.Counter()
    unknown_el = collections.Counter()
    n_over_rows = 0
    for smi in C.loc[base & single, "smiles"]:
        c = counts(smi)
        if c is None:
            continue
        hit = False
        for el, n in c.items():
            if el not in NORM_VEC_ELEMENTS:
                unknown_el[el] += 1
                continue
            if n > NORM_VEC[NORM_VEC_ELEMENTS.index(el)]:
                over[el] += 1
                hit = True
        n_over_rows += hit
    res["ms_pred_element_domain"] = {
        "reference": "ms-pred src/ms_pred/common/chem_utils.py:131 NORM_VEC (normalisation, not a hard cap), :132 MAX_ATOM_CT=160",
        "n_compounds_checked": int((base & single).sum()),
        "n_compounds_with_any_element_count_above_NORM_VEC": int(n_over_rows),
        "per_element_n_compounds_above_NORM_VEC": {k: int(v) for k, v in over.items()},
        "elements_not_in_ms_pred_valid_list": {k: int(v) for k, v in unknown_el.items()},
        "n_compounds_heavy_atoms_gt_MAX_ATOM_CT": int((C.loc[base & single, "heavy_atoms"] > MAX_ATOM_CT).sum()),
        "heavy_atoms_max": float(C.loc[base & single, "heavy_atoms"].max()),
    }

    # ---------------------------------------------------------------- 3. MassSpecGym rows of overlapping keys
    msg = pd.read_parquet(W / "artifacts/ce_interface_adjudication/massspecgym15_identity_metadata_joined.parquet")
    ov_keys = set()
    for a, b in zip(C.loc[C["in_msg15_any_route"], "muru_key"], C.loc[C["in_msg15_any_route"], "ik14_s4"]):
        for k in (a, b):
            if isinstance(k, str):
                ov_keys.add(k)
    msg_ov = msg[msg["inchikey"].isin(ov_keys)].copy()
    name_by_key = {}
    for _, r in C[C["in_msg15_any_route"]].iterrows():
        for k in (r["muru_key"], r["ik14_s4"]):
            if isinstance(k, str):
                name_by_key.setdefault(k, r["name"])
    msg_ov["cyanometdb_name"] = msg_ov["inchikey"].map(name_by_key)
    msg_ov.to_csv(OUT / "s2_msg_overlap_rows.csv", index=False)
    per_key = []
    for k, g in msg_ov.groupby("inchikey"):
        per_key.append({
            "inchikey14": k, "cyanometdb_name": name_by_key.get(k),
            "n_msg_rows": int(len(g)), "folds": "|".join(sorted(set(g["fold"].astype(str)))),
            "n_simulation_challenge_rows": int(g["simulation_challenge"].fillna(False).astype(bool).sum()),
            "adducts": "|".join(sorted(set(g["adduct"].astype(str)))),
            "instruments": "|".join(sorted(set(g["instrument_type"].astype(str)))),
            "ce_values": "|".join(sorted(set(f"{x:g}" for x in g["collision_energy"].dropna()))),
            "precursor_mz_min": round(float(g["precursor_mz"].min()), 4),
            "precursor_mz_max": round(float(g["precursor_mz"].max()), 4),
        })
    res["msg15_overlap_rows_per_key"] = sorted(per_key, key=lambda d: -d["n_msg_rows"])

    lab = pd.read_csv(MSPRED / "data/spec_datasets/msg/labels.tsv", sep="\t")
    res["ms_pred_msg_labels"] = {
        "path": "repos/ms-pred/data/spec_datasets/msg/labels.tsv",
        "n_rows": int(len(lab)),
        "precursor_min": float(lab["precursor"].min()),
        "precursor_max": float(lab["precursor"].max()),
        "instrument_counts": vc(lab["instrument"]),
        "ionization_counts": vc(lab["ionization"]),
        "n_rows_with_overlap_key": int(lab["inchikey"].isin(ov_keys).sum()),
        "overlap_keys_in_labels": sorted(set(lab.loc[lab["inchikey"].isin(ov_keys), "inchikey"])),
    }

    # ---------------------------------------------------------------- 4. record-level evidence
    res["record_level"] = {
        "n_records_tag_2026.03": int(len(R)),
        "series_counts": vc(R["series"]),
        "instrument_by_series": summ["records"]["instrument_by_series"],
        "instrument_type": summ["records"]["instrument_type"],
        "fragmentation_mode_sampled": summ["records"]["fragmentation_mode"],
        "ce_field_string_forms_sampled": summ["records"]["ce_string_forms"],
        "title_ce_forms_all_records": summ["records"]["title_ce_forms"],
        "title_vs_field_ce_disagree": summ["records"]["title_vs_field_ce_disagree"],
        "n_records_with_TENTATIVE_in_title": int(R["record_title"].fillna("").str.contains("TENTATIVE", case=False).sum()),
        "precursor_type_counts": summ["records"]["precursor_type"],
        "first_mass_by_series": summ["records"]["title_first_mass_by_series"],
        "scan_window_sample": summ["scan_window_sample"],
        "n_mh_records": int((R["precursor_type"].fillna(R["title_adduct"]) == "[M+H]+").sum()),
    }

    # per-record header sample from the LICENSE/COPYRIGHT fragments (300 records)
    conf, cmdb, lic, pub = collections.Counter(), 0, collections.Counter(), collections.Counter()
    sample_map = {}
    p = DL2 / "codesearch_license_tentative.jsonl"
    n_frag_records = 0
    for line in p.open():
        j = json.loads(line)
        for it in j["items"]:
            n_frag_records += 1
            acc = it["path"].split("/")[-1][:-4]
            txt = "\n".join(it["fragments"])
            for ln in txt.split("\n"):
                ln = ln.strip()
                m = re.match(r"^COMMENT: (?:CONFIDENCE )?(?:Level )?([123][ab]?)$", ln)
                if m:
                    conf[m.group(1)] += 1
                    sample_map.setdefault(acc, {})["level_record"] = m.group(1)
                m = re.match(r"^COMMENT: CyanoMetDB_ID (\d+)$", ln)
                if m:
                    cmdb += 1
                    sample_map.setdefault(acc, {})["cyanometdb_id_record"] = m.group(1)
                m = re.match(r"^(LICENSE|PUBLICATION): (.*)$", ln)
                if m:
                    (lic if m.group(1) == "LICENSE" else pub)[m.group(2)] += 1
    # cross-check the record-carried level and CyanoMetDB id against Table S4
    acc2unit = dict(zip(R["accession"], R["unit"]))
    unit_level = dict(zip(C["unit_id"], C["level"].astype(str)))
    id2unit = {str(i): u for i, u in zip(C["cyanometdb_id"].astype(str), C["unit_id"])}
    agree_lvl = dis_lvl = agree_id = dis_id = 0
    dis_examples = []
    for acc, d in sample_map.items():
        u = acc2unit.get(acc)
        if "level_record" in d and u in unit_level:
            if unit_level[u] == d["level_record"]:
                agree_lvl += 1
            else:
                dis_lvl += 1
                if len(dis_examples) < 10:
                    dis_examples.append({"accession": acc, "unit": u, "level_s4": unit_level[u],
                                         "level_record": d["level_record"]})
        if "cyanometdb_id_record" in d:
            u2 = id2unit.get(d["cyanometdb_id_record"])
            if u2 is not None and u2 == u:
                agree_id += 1
            else:
                dis_id += 1
                if len(dis_examples) < 20:
                    dis_examples.append({"accession": acc, "unit_from_stem_mapping": u,
                                         "cyanometdb_id_record": d["cyanometdb_id_record"],
                                         "unit_of_that_id": u2})
    res["record_header_sample"] = {
        "n_records_in_sample": n_frag_records,
        "license_values": {k: int(v) for k, v in lic.items()},
        "publication_values": {k: int(v) for k, v in pub.items()},
        "confidence_level_values": {k: int(v) for k, v in conf.items()},
        "n_records_with_cyanometdb_id_comment": cmdb,
        "level_agreement_with_table_s4": {"agree": agree_lvl, "disagree": dis_lvl},
        "cyanometdb_id_unit_agreement": {"agree": agree_id, "disagree": dis_id},
        "disagreement_examples": dis_examples,
    }

    # ---------------------------------------------------------------- 5. timing evidence
    name_re = re.compile(r"MSBNK-(EAWAG-E[CD]|MLU-ED)\d+\.txt")
    tim = {}
    for tagname, fn in [("2023.11", DL2 / "massbank_data_Eawag_tree_tag_2023.11.json"),
                        ("2025.10", DL2 / "massbank_data_Eawag_tree_tag_2025.10.json"),
                        ("2026.03", OUT / "downloads/massbank_data_Eawag_tree_tag_2026.03.json"),
                        ("dev", OUT / "downloads/massbank_data_Eawag_tree_branch_dev.json")]:
        names = [t["path"] for t in json.load(open(fn))["tree"]]
        tim[tagname] = {"n_eawag_dir_files": len(names),
                        "n_cyanometdb_named": sum(1 for p_ in names if name_re.fullmatch(p_))}
    for tagname in ("2023.11", "2025.10"):
        root = json.load(open(DL2 / f"massbank_data_root_tree_tag_{tagname}.json"))
        tim[tagname]["root_has_MLU_dir"] = any(t["path"] == "MLU" for t in root["tree"])
    res["timing"] = {
        "cyanometdb_record_files_in_Eawag_dir_by_ref": tim,
        "record_DATE_by_series": summ["records"]["date_by_series"],
        "massbank_pr_366": {"created_at": "2026-01-12T18:35:31Z", "merged_at": "2026-02-02T08:15:18Z",
                            "changed_files": 3126, "base": "dev", "user": "chufz",
                            "source": "gh api repos/MassBank/MassBank-data/pulls/366"},
    }
    res["codesearch_count_probe_caveat"] = json.load(open(DL2 / "codesearch_counts_only.json"))["counts"]

    # ------------------------------------------------- 6. CE-interface geometry and spectrum counts
    R["is_mh"] = (R["precursor_type"].fillna(R["title_adduct"]) == "[M+H]+")
    unit2n = R[R["is_mh"]].groupby("unit").size()
    ladder = {}
    for name, mask in sets.items():
        sub = C[mask]
        ratios = (sub["mh_theor"] / 500.0).dropna()
        nce = collections.Counter()
        for s_ in sub["mh_nce_set"].dropna():
            for v in str(s_).split(","):
                nce[v] += 1
        ladder[name] = {
            "precursor_over_500_q10": round(float(ratios.quantile(0.1)), 3) if len(ratios) else None,
            "precursor_over_500_median": round(float(ratios.median()), 3) if len(ratios) else None,
            "precursor_over_500_q90": round(float(ratios.quantile(0.9)), 3) if len(ratios) else None,
            "n_compounds_ratio_gt_1": int((ratios > 1).sum()),
            "n_mh_records_total": int(unit2n.reindex(sub["unit_id"].unique()).fillna(0).sum()),
            "nce_value_coverage_n_compounds": {k: int(v) for k, v in sorted(nce.items(), key=lambda kv: float(kv[0]))},
            "distinct_nce_per_compound_median": float(sub["n_mh_distinct_nce"].median()) if len(sub) else None,
        }
    res["ce_geometry"] = ladder

    # scan-window coverage, on the records that carry a MASS_RANGE line (QC-sampled partitions only)
    wr = R[R["is_mh"] & R["mass_range"].notna()].copy()
    wr["hi_minus_prec"] = wr["mass_range_hi"] - wr["precursor_mz"]
    res["scan_window_mh_sampled"] = {
        "n_mh_records_with_mass_range": int(len(wr)),
        "n_mh_records_total": int(R["is_mh"].sum()),
        "by_series": {s: {"n": int(len(g)),
                          "lo_le_40": int((g["mass_range_lo"] <= 40).sum()),
                          "hi_ge_prec_plus_1": int((g["hi_minus_prec"] >= 1).sum()),
                          "lo_min": float(g["mass_range_lo"].min()), "lo_max": float(g["mass_range_lo"].max()),
                          "hi_min": float(g["mass_range_hi"].min()), "hi_max": float(g["mass_range_hi"].max())}
                      for s, g in wr.groupby("series")},
    }

    # ------------------------------------------------- 7. criterion table (statuses are this screen's judgement)
    res["criteria"] = [
        {"id": 1, "criterion": "absent from MURU development", "status": "MET",
         "evidence": ("git grep -l over the MURU worktree finds no file under src/, scripts/ or *.md "
                      "containing CyanoMetDB, MSBNK-EAWAG, MSBNK-MLU or Eawag; MURU's only MassBank cohort "
                      "is LCSB and MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md:35 lists non-LCSB MassBank/MoNA "
                      "cohorts as not outcome-accessed. Compound level: 4 of 136 [M+H]+ compound keys are in "
                      "the MURU exposure registry (Nodularin-R, MC-LA, MC-LY, 7-Deoxy-Cylindrospermopsin) and "
                      "30 of the 142 [M+H]+ >=3-NCE compound rows share a registry scaffold group (9 groups, mostly the microcystin macrocycle); removed in P2/P3.")},
        {"id": 2, "criterion": "absent from the PR #7 (MSnLib confirmation study 2) population", "status": "MET",
         "evidence": "0 of 136 keys in msnlib_study2_population_keys.txt (1,794) and 0 shared scaffold groups."},
        {"id": 3, "criterion": "absent from the comparator benchmark population", "status": "MET",
         "evidence": "0 of 136 keys in comparator_common_population_keys.txt (1,327) and 0 shared scaffold groups."},
        {"id": 4, "criterion": "absent from ICEBERG/GLACIER training at compound level (MassSpecGym 1.5, all folds)",
         "status": "PARTIAL",
         "evidence": ("14 of 136 [M+H]+ compound keys are in MassSpecGym 1.5 by recorded or MURU parent key; 7 of "
                      "them are in the [M+H]+ simulation-challenge subset and appear in ms-pred "
                      "data/spec_datasets/msg/labels.tsv with 138 rows. All 14 are removed in design set P2, so "
                      "the post-exclusion sets are MET by construction.")},
        {"id": 5, "criterion": "known CE semantics", "status": "MET",
         "evidence": ("Record titles of all 3,126 records carry CE: <n>% (single value, never stepped); the "
                      "AC$MASS_SPECTROMETRY COLLISION_ENERGY field reads '<n> % (nominal)' and FRAGMENTATION_MODE "
                      "HCD in the 1,147 records whose headers were harvested with the QC query, with 0 "
                      "title-vs-field disagreements; the paper states 9 NCE per mode (15,20,25,30,40,50,60,70,80 %), "
                      "1.0 Da isolation, MS2 R=15,000. The field-level check covers 1,147 of 3,126 records because "
                      "of the harvest's query sampling, not because the field is missing.")},
        {"id": 6, "criterion": "[M+H]+ positive mode available", "status": "MET",
         "evidence": ("1,888 [M+H]+ records (plus 1,211 [M-H]- and 27 [M+2H]2+); 130 compound units have an "
                      "[M+H]+ ladder and all 130 have >= 3 distinct NCE.")},
        {"id": 7, "criterion": "compatible fragmentation / instrument metadata", "status": "PARTIAL",
         "evidence": ("Compatible: HCD beam-type on Orbitrap (Exploris 240 2,546 records, Q Exactive Plus 580), "
                      "instrument_type LC-ESI-QFT maps to the ms-pred token 'Orbitrap' "
                      "(ms-pred src/ms_pred/common/chem_utils.py:277-282); NCE 20 and 60 both present for 78 of the "
                      "84 P3 compound rows; heavy atoms <= 122 vs MAX_ATOM_CT 160. Not compatible: MURU's external "
                      "scan-window rule (lower <= 40, external_msnlib.py:59-62) is met only by the EC series "
                      "(290 of 326 sampled EC [M+H]+ records), 0 of 281 ED and 0 of 69 MLU sampled records; 27 of "
                      "81 P3 compounds exceed the MassSpecGym 1.5 precursor max 999.396 and the ICEBERG msg label "
                      "max 995.556, 18 exceed the MURU development max 1042.6, 4 exceed the GLACIER checkpoint "
                      "upper_limit 1500; negative mode and [M+2H]2+ records are outside MURU claim scope.")},
        {"id": 8, "criterion": "multiple energies per compound", "status": "MET",
         "evidence": ("Median 9 distinct NCE per [M+H]+ compound in every design set; the modal ladder "
                      "15,20,25,30,40,50,60,70,80 covers 97 of 130 units; 9 units stop at 60 and 11 use a "
                      "15-70 ladder with an extra 35.")},
        {"id": 9, "criterion": "structural diversity and scaffold count after all exclusions", "status": "NOT_MET",
         "evidence": ("P3 (key and scaffold clean) = 81 compounds in 45 MURU scaffold groups, 28 of them "
                      "singletons; intersecting the models' precursor domain and requiring NCE 20 and 60 gives "
                      "P5 = 53 compounds / 33 groups; Level 1 only gives 13 compounds / 12 groups. All are "
                      "cyanobacterial peptides and peptide-like natural products: Butina clustering at Tanimoto "
                      "0.4 gives 20 clusters for the 81-compound set and 16 for the 57-compound in-range set, "
                      "with 40 and 28 name families, 54 and 31 macrocycles; Bemis-Murcko groups of macrocyclic "
                      "peptides are nearly compound-specific, so the group count overstates independence. "
                      "Nearest-MassSpecGym-neighbour Tanimoto for the 57 in-range compounds: median 0.59, "
                      "18 of 57 at >= 0.7, so key-level novelty does not imply structural novelty.")},
        {"id": 10, "criterion": "license and access", "status": "MET",
         "evidence": ("Every one of the 300 sampled records carries 'LICENSE: CC BY-SA' (COPYRIGHT Eawag 2023); "
                      "the repository MassBank/MassBank-data is public (tag 2026.03) and releases are archived "
                      "under Zenodo 10.5281/zenodo.3378723; the paper is CC-BY 4.0. Share-alike constrains "
                      "redistribution of derived spectral sets. The peak lists themselves were not downloaded "
                      "(this study's download policy forbids spectra).")},
        {"id": 11, "criterion": "hidden MassSpecGym inclusion under a different identifier", "status": "MET",
         "evidence": ("0 of the 3,126 record files exist in the MassBank tags 2023.11 (the release MassSpecGym 1.0 "
                      "ingested) or 2025.10; they entered through PR #366 (opened 2026-01-12, merged 2026-02-02, "
                      "3,126 changed files) and first appear at tag 2026.03. MassSpecGym 1.5 added no spectra "
                      "(only smiles re-canonicalisation). Residual compound-level route: 14 keys are already in "
                      "MassSpecGym from earlier independent depositions (SI Table S4 marks 11 compounds as "
                      "previously in MassBank; SI Table S1 lists 14 compounds deposited before 2025), and 13 "
                      "compound rows share a neutral formula with a different MassSpecGym key; all are excluded "
                      "in P2.")},
    ]
    res["verdict"] = {
        "verdict": "PARTIAL_OR_SUPPORTING_ONLY",
        "reason": ("Criteria 1-6, 8, 10 and 11 hold for the post-exclusion design sets and the CE quantity is "
                   "unambiguous, but criterion 9 fails (one chemical class, 45 scaffold groups at P3, 33 inside "
                   "the models' precursor domain, 12 at Level 1) and criterion 7 is only partly met (two scan "
                   "modes, only the EC series satisfies MURU's scan-window rule, and a quarter to a third of the "
                   "clean compounds sit above the models' precursor range). Useful as a dedicated high-m/z arm "
                   "(precursor/500 median 1.59-1.82), not as a stand-alone Design A dataset.")}
    res["access_notes"] = {
        "peak_data_not_downloaded": True,
        "aborted_probe": ("One GitHub code-search text-match probe (term TENTATIVE, series MSBNK-EAWAG-EC) "
                          "returned a fragment containing peak-like lines; the fetch script's own guard aborted "
                          "and that response was discarded in memory and never stored. The probe was re-run "
                          "count-only."),
        "codesearch_count_probe_unusable": ("With a filename: filter the code-search totals do not track the "
                                            "search term: LICENSE (present in every record) and TENTATIVE return "
                                            "identical totals (950/1408/654), and those totals also differ from "
                                            "the true per-series file counts 1010/1536/580. No TENTATIVE "
                                            "prevalence claim can be derived from them."),
    }

    D.to_csv(OUT / "s2_design_sets.csv", index=False)
    (OUT / "s2_criteria.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ("design_sets", "ms_pred_element_domain", "record_header_sample",
                                          "timing", "ms_pred_msg_labels")}, indent=1, default=str)[:12000])


if __name__ == "__main__":
    main()
