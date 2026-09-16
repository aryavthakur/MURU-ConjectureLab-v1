"""Task C (completeness critic) re-check of document-level numeric claims.

Read-only. Recomputes the specific numbers that the three deliverable documents state but that are
NOT directly present as a named field in the counts artifacts, so that a critic can confirm or refute
them without trusting the prose.

No model is loaded and no inference is run. Inputs are the same metadata parquets the Q classifier used.
Writes one JSON: artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json
"""
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ART = ROOT / "artifacts" / "ce_interface_adjudication"
IDENT = ROOT / "artifacts" / "comparator_feasibility" / "massspecgym15_identity.parquet"
META = ART / "massspecgym15_metadata_columns.parquet"
P3 = ART / "p3_msg15_row_source_attribution.parquet"
LONG = ART / "counts" / "ce_convention_counts_long.csv"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


ident = pd.read_parquet(IDENT)
meta = pd.read_parquet(META)
p3 = pd.read_parquet(P3)

print("ident cols", ident.columns.tolist())
print("meta cols", meta.columns.tolist())
print("p3 cols", p3.columns.tolist())

df = ident.merge(meta[["identifier","precursor_mz"]], on="identifier", how="left").merge(
    p3[["identifier", "source_label"]], on="identifier", how="left")
sim = df[df.simulation_challenge.astype(bool)].copy()
assert len(sim) == 119029, len(sim)

ce = sim.collision_energy.to_numpy(dtype=float)
mz = sim.precursor_mz.to_numpy(dtype=float)
orb = (sim.instrument_type == "Orbitrap").to_numpy()
is_int = ce == np.floor(ce)
src = sim.source_label.to_numpy()
mbmona = src == "MassBank_or_MoNA"

fold = sim.fold.to_numpy()
split = np.where(fold == "train", "train", np.where(fold == "val", "val", "test"))

U4_LADDER = [15.0, 30.0, 35.0, 45.0, 60.0, 75.0, 90.0, 120.0, 150.0, 180.0]
MSNLIB_LADDER = [15.0, 20.0, 30.0, 45.0, 60.0, 75.0]

mult5 = mbmona & orb & is_int & (ce != 0) & (np.mod(ce, 5) == 0)
on_u4 = mult5 & np.isin(ce, U4_LADDER)

out = {"inputs": {str(p): sha256(p) for p in [IDENT, META, P3]}}

out["C1_mbmona_integer_mult5"] = {
    "claim_in_docs": "18,340 MassBank or MoNA integer Orbitrap rows on the {15,30,35,45,60,75,90,120,150,180} ladder",
    "mbmona_orbitrap_integer_rows": int((mbmona & orb & is_int).sum()),
    "subreason_mult5_rows_recomputed": int(mult5.sum()),
    "of_which_on_the_named_10_value_ladder": int(on_u4.sum()),
    "off_ladder_multiples_of_5": int((mult5 & ~on_u4).sum()),
    "off_ladder_value_counts": {str(k): int(v) for k, v in
                                pd.Series(ce[mult5 & ~on_u4]).value_counts().sort_index().items()},
}

lng = pd.read_csv(LONG)
print("long cols", lng.columns.tolist())
g = lng[(lng.checkpoint == "iceberg21_msg_simulation_gen") & (lng.split_scope == "train") &
        (lng.status == "retained") & (lng.category == "CAT4_UNKNOWN_AMBIGUOUS")]
by_sub = g.groupby("subreason").n_rows.sum().to_dict()
mb_subs = [s for s in by_sub if s.startswith("mbmona")]
out["C2_train_CAT4_by_source"] = {
    "claim_in_docs": "Phase0 4.2B row G4 (MassBank or MoNA, Orbitrap) quotes 'Unresolved arm (n = 23,689)'",
    "gen_train_CAT4_all_sources": int(g.n_rows.sum()),
    "gen_train_CAT4_by_subreason": {k: int(v) for k, v in by_sub.items()},
    "gen_train_unresolved_mbmona_only": int(sum(by_sub[s] for s in mb_subs)),
    "gen_train_unresolved_probable_msnlib": int(by_sub.get("msnlib_probable_integer_ladder", 0)),
    "gen_train_unresolved_blockB_anomalous": int(by_sub.get("msnlib_order_nonladder_or_anomalous", 0)),
}

# exact CAT4 set for MassBank_or_MoNA Orbitrap train: every integer row plus the 12 CE 80.205 rows
cat4_mb = mbmona & orb & (split == "train") & (is_int | (np.abs(ce - 80.205) < 1e-9))
v = np.floor(ce[cat4_mb])
out["C3_mbmona_unresolved_presented_values_gen_train"] = {
    "n": int(cat4_mb.sum()),
    "n_distinct": int(len(np.unique(v))),
    "min": float(v.min()), "max": float(v.max()),
    "q05": float(np.quantile(v, 0.05)), "q50": float(np.quantile(v, 0.50)), "q95": float(np.quantile(v, 0.95)),
}
# plus the 12 non-integer CAT4 MassBank rows (CE 80.205) which belong to the same arm
cat4_mb_nonint = mbmona & orb & (split == "train") & (~is_int) & (np.abs(ce - 80.205) < 1e-9)
out["C3_mbmona_unresolved_nonint_rows_gen_train"] = int(cat4_mb_nonint.sum())

lad = np.isin(ce, MSNLIB_LADDER)
out["C4_orbitrap_integer_ladder_bracket"] = {
    "ladder_used": MSNLIB_LADDER,
    "orbitrap_integer_ladder_rows_T_sim": int((orb & is_int & lad).sum()),
    "block_B_of_those": int((orb & is_int & lad & (src == "MSnLib_v1")).sum()),
    "probable_of_those": int((orb & is_int & lad & (src == "MSnLib_v1_probable")).sum()),
    "mbmona_of_those": int((orb & is_int & lad & mbmona).sum()),
}

out["C5_instrument_composition_T_sim"] = {
    "Orbitrap": int(orb.sum()), "QTOF": int((sim.instrument_type == "QTOF").sum()),
    "other_or_missing": int(len(sim) - int(orb.sum()) - int((sim.instrument_type == "QTOF").sum())),
}

for scope in ["train", "val"]:
    sel = orb & (split == scope)
    n = int(sel.sum())
    sub = lng[(lng.checkpoint == "iceberg21_msg_simulation_gen") & (lng.split_scope == scope) &
              (lng.status == "retained")]
    cat1 = int(sub[sub.category == "CAT1_RAW_NCE"].n_rows.sum())
    conv = int(sub[sub.category.isin(["CAT2_NCE_x_mz_over_500", "CAT3_OTHER_CONVERSION"])].n_rows.sum())
    unk = int(sub[sub.category == "CAT4_UNKNOWN_AMBIGUOUS"].n_rows.sum())
    out[f"C6_orbitrap_{scope}_composition"] = {
        "orbitrap_rows": n, "raw_nce": cat1, "converted": conv, "unknown": unk,
        "pct_raw": round(100.0 * cat1 / n, 1), "pct_conv": round(100.0 * conv / n, 1),
        "pct_unknown": round(100.0 * unk / n, 1),
    }

# precursor support of the C01-relevant claim: MassSpecGym max precursor and ICEBERG label max
out["C7_precursor_support"] = {
    "msg15_all_rows_max_precursor_mz": float(np.nanmax(meta.precursor_mz.to_numpy(dtype=float))),
    "T_sim_max_precursor_mz": float(np.nanmax(mz)),
}

dest = ART / "counts" / "c_taskc_recheck.json"
dest.write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
print("WROTE", dest)
