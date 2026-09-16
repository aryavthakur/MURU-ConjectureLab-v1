"""S10-C10 verification, part 2: is the BAFG ladder literally inside MassSpecGym 1.5, and what adducts exist.

Local metadata only; no network, no spectra.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "screen/c10_bafg"

df = pd.read_csv(OUT / "c10_records_identity.csv", low_memory=False)
pos = df[df["ion_mode"] == "POSITIVE"]
msg = pd.read_parquet(ADJ.parent / "comparator_feasibility/massspecgym15_identity.parquet")

out = {}

# ---- A. precursor-type evidence actually present in the records table
pt = pos["precursor_type_codesearch"]
out["precursor_type_sample"] = {
    "positive_records_with_precursor_type_evidence": int(pt.notna().sum()),
    "positive_records_total": int(len(pos)),
    "distribution": {str(k): int(v) for k, v in pt.value_counts(dropna=True).items()},
}
kpt = pos[pt.notna()].groupby("key")["precursor_type_codesearch"].agg(lambda s: ";".join(sorted(set(s))))
out["precursor_type_sample"]["keys_with_evidence"] = int(len(kpt))
out["precursor_type_sample"]["keys_by_type"] = {str(k): int(v) for k, v in kpt.value_counts().items()}
# cross-check against parent charge: permanent cations should be [M]+
pc = pos.groupby("key")["parent_charge"].first()
j = pd.DataFrame({"pt": kpt, "charge": pc.reindex(kpt.index)})
out["precursor_type_sample"]["cross_tab_charge_vs_type"] = {
    f"charge={int(c)} type={t}": int(n) for (c, t), n in j.groupby(["charge", "pt"]).size().items()
}
out["positive_keys_by_parent_charge"] = {str(int(k)): int(v) for k, v in pc.value_counts().items()}

# ---- B. is the BAFG ladder literally in MassSpecGym (row-level fingerprint, not just compound overlap)?
q = msg[msg["instrument_type"] == "QTOF"].copy()
ladder = [float(x) for x in range(10, 160, 10)]
bafg_keys = set(pos["key"])
qb = q[q["inchikey"].isin(bafg_keys)]
out["msg_qtof_vs_bafg"] = {
    "msg_qtof_rows": int(len(q)),
    "msg_qtof_rows_with_a_bafg_positive_key": int(len(qb)),
    "msg_qtof_rows_on_ladder": int(q["collision_energy"].isin(ladder).sum()),
    "msg_qtof_rows_on_ladder_with_bafg_key": int(qb["collision_energy"].isin(ladder).sum()),
    "msg_qtof_max_ce": float(q["collision_energy"].max()),
    "msg_orbitrap_max_ce": float(msg[msg["instrument_type"] == "Orbitrap"]["collision_energy"].max()),
    "msg_qtof_rows_ce_gt_100": int((q["collision_energy"] > 100).sum()),
    "msg_qtof_rows_ce_gt_100_with_bafg_key": int((qb["collision_energy"] > 100).sum()),
}
# per key: BAFG positive-mode record count on the ladder vs MSG QTOF row count on the ladder
bl = pos[pos["ce_value"].isin(ladder)].groupby("key").size().rename("bafg_records")
ml = qb[qb["collision_energy"].isin(ladder)].groupby("inchikey").size().rename("msg_qtof_rows")
cmp_ = pd.concat([bl, ml], axis=1).dropna()
cmp_["ratio"] = cmp_["msg_qtof_rows"] / cmp_["bafg_records"]
out["per_key_row_count_comparison"] = {
    "keys_compared": int(len(cmp_)),
    "keys_msg_rows_eq_bafg_records": int((cmp_["msg_qtof_rows"] == cmp_["bafg_records"]).sum()),
    "keys_msg_rows_ge_bafg_records": int((cmp_["msg_qtof_rows"] >= cmp_["bafg_records"]).sum()),
    "median_ratio": float(cmp_["ratio"].median()),
    "examples": cmp_.head(8).reset_index().to_dict("records"),
}
# CE-value-set fingerprint: BAFG 15-point ladder keys, do MSG QTOF rows carry the same 15 values?
full = pos.groupby("key")["ce_value"].apply(lambda s: tuple(sorted(set(s))))
full15 = full[full == tuple(ladder)]
mset = qb.groupby("inchikey")["collision_energy"].apply(lambda s: tuple(sorted(set(s))))
both = [k for k in full15.index if k in mset.index]
exact = [k for k in both if mset[k] == tuple(ladder)]
superset = [k for k in both if set(ladder).issubset(set(mset[k]))]
out["ce_value_set_fingerprint"] = {
    "bafg_keys_with_exact_10_150_step10_ladder": int(len(full15)),
    "of_those_present_in_msg_qtof": int(len(both)),
    "msg_qtof_ce_set_exactly_equals_the_ladder": int(len(exact)),
    "msg_qtof_ce_set_contains_the_whole_ladder": int(len(superset)),
}

# ---- C. what the surviving post-exclusion pool looks like
ver = json.loads((OUT / "s10_verification_record.json").read_text())
v6 = set(ver["checks"]["v6_keys"])
sub = pos[pos["key"].isin(v6)]
per = sub.groupby("key").agg(
    n_records=("accession", "size"),
    n_ce=("ce_value", "nunique"),
    ce_min=("ce_value", "min"),
    ce_max=("ce_value", "max"),
    name=("compound_name", "first"),
    formula=("parent_formula", "first"),
    mh=("mh_mz_from_parent", "first"),
    in2023=("in_tree_2023_11", "any"),
)
out["v6_pool_detail"] = per.reset_index().to_dict("records")
out["v6_pool_totals"] = {
    "keys": int(len(per)),
    "records": int(per["n_records"].sum()),
    "keys_with_full_15_point_ladder": int((per["n_ce"] >= 15).sum()),
    "records_in_massbank_2023_11": int(sub["in_tree_2023_11"].sum()),
}

(OUT / "s10_verification_part2.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str)[:9000])
