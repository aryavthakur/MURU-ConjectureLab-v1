"""Task M: independent recount of the D1-staged MassBank post-2023.11 Eawag-family record metadata.

Identity and metadata only (no peaks, no model output, no MURU outcome). Inputs:
  --d1-csv    D1 staged d1_eawag_new_record_metadata.csv (13 header-derived columns, no peak data)
  --d1-keys   D1 staged d1_clean_ik14_eawag_new_MH_ge3nce.json
  --d3-eq5    D3 staged eawag_eq5_path_to_inchikey.json (only its keys, i.e. record file paths, are used)
  --exclusion artifacts/ce_interface_adjudication/exclusion
  --msg-meta  artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet (precursor_mz only)
Writes one JSON summary to --out.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

CYANO_PREFIXES = {"EAWAG-EC", "EAWAG-ED", "MLU-ED"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def keys(p):
    return set(Path(p).read_text().split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d1-csv", required=True)
    ap.add_argument("--d1-keys", required=True)
    ap.add_argument("--d3-eq5", required=True)
    ap.add_argument("--exclusion", required=True)
    ap.add_argument("--msg-meta", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ex = Path(a.exclusion)
    msg = keys(ex / "msg15_keys_all.txt")
    muru = keys(ex / "muru_exposure_registry_keys.txt")
    msn9 = keys(ex / "msnlib_9lib_keys.txt")
    common = keys(ex / "comparator_common_population_keys.txt")
    msg_mz_max = float(pd.read_parquet(a.msg_meta, columns=["precursor_mz"])["precursor_mz"].max())

    d = pd.read_csv(a.d1_csv)
    d["release"] = d["first_release"].map(lambda x: f"{float(x):.2f}")
    d["grp"] = d["pre"].map(
        lambda p: "CyanoMetDB" if p in CYANO_PREFIXES else ("EawagEQ" if p == "Eawag-EQ" else "other"))
    out = {
        "inputs": {k: {"path": str(v), "sha256": sha256(v)} for k, v in
                   {"d1_csv": a.d1_csv, "d1_keys": a.d1_keys, "d3_eq5": a.d3_eq5, "msg_meta": a.msg_meta}.items()},
        "key_definition_note": "recorded 14-char InChIKey first block from the MassBank record; MURU registry keys are "
                               "parent connectivity keys, so MURU overlap is approximate; scaffold groups not applied",
        "n_records": int(len(d)),
        "records_by_group_prefix_ptype": {"|".join(map(str, k)): int(v)
                                          for k, v in d.groupby(["grp", "pre", "ptype"]).size().items()},
        "records_by_group_instrument": {"|".join(map(str, k)): int(v)
                                        for k, v in d.groupby(["grp", "inst"]).size().items()},
        "fraction_ce_string_with_percent": float(d["ce"].astype(str).str.contains("%").mean()),
        "msg15_precursor_mz_max": msg_mz_max,
        "groups": {},
    }
    clean_all = set()
    mh = d[(d["ptype"] == "[M+H]+") & d["nce"].notna()]
    for grp, x in mh.groupby("grp"):
        g = x.groupby("ik").agg(
            n_nce=("nce", "nunique"), pmz=("pmz", "median"), rel=("release", "min"),
            ladder=("nce", lambda s: ",".join(f"{v:g}" for v in sorted(set(s))))).reset_index()
        ge3 = g[g["n_nce"] >= 3].copy()
        ge3["in_msg"] = ge3["ik"].isin(msg)
        ge3["in_muru"] = ge3["ik"].isin(muru)
        clean = ge3[~ge3["in_msg"] & ~ge3["in_muru"]]
        clean_all |= set(clean["ik"])
        out["groups"][grp] = {
            "mh_records_by_instrument": {str(k): int(v) for k, v in x["inst"].value_counts().items()},
            "mh_compounds": int(g["ik"].nunique()),
            "mh_compounds_by_first_release": {str(k): int(v) for k, v in g["rel"].value_counts().items()},
            "mh_compounds_ge3_nce": int(len(ge3)),
            "ge3_in_msg15": int(ge3["in_msg"].sum()),
            "ge3_in_muru_registry": int(ge3["in_muru"].sum()),
            "ge3_clean": int(len(clean)),
            "clean_in_msnlib9": int(clean["ik"].isin(msn9).sum()),
            "clean_in_comparator_common_population": int(clean["ik"].isin(common).sum()),
            "clean_by_first_release": {str(k): int(v) for k, v in clean["rel"].value_counts().items()},
            "clean_pmz_median": round(float(clean["pmz"].median()), 1),
            "clean_pmz_q10_q90": [round(float(v), 1) for v in clean["pmz"].quantile([0.1, 0.9])],
            "clean_pmz_max": round(float(clean["pmz"].max()), 1),
            "clean_above_msg15_max_pmz": int((clean["pmz"] > msg_mz_max).sum()),
            "clean_below_500": int((clean["pmz"] < 500).sum()),
            "top_ladders_all_mh_compounds": {k: int(v) for k, v in g["ladder"].value_counts().head(4).items()},
        }
    staged = set(json.loads(Path(a.d1_keys).read_text()))
    out["d1_staged_clean_key_list"] = {"n": len(staged), "recomputed_n": len(clean_all),
                                       "identical": staged == clean_all}
    eq5 = json.loads(Path(a.d3_eq5).read_text())
    eq5_names = {p.split("/")[-1] for p in (eq5.keys() if isinstance(eq5, dict) else eq5)}
    out["d3_eq5_sample"] = {"n_files": len(eq5_names),
                            "n_in_d1_post_2023_11_set": len(eq5_names & set(d["f"])),
                            "example_files": sorted(eq5_names)[:3]}
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
