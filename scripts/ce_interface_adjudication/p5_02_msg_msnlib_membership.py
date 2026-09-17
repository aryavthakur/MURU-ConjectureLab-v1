"""CE interface adjudication, P5 step 2: per-row MassSpecGym 1.5 -> MSnLib compound membership, plus row-order signals.

COMPOUND MEMBERSHIP IS NOT ROW PROVENANCE. A MassSpecGym row whose molecule is plated in an MSnLib v1.0 library may
still come from MassBank, MoNA or GNPS. This table gives compound membership and the raw row-order signals from which
row provenance can be inferred; it assigns no row to a source.

Row-order facts used (read in pluskal-lab/MassSpecGym notebooks/dataset_construction at commit 5a34ede, 2024-09-07):
  1_Load_data_from_repositories cell 12: sources concatenated in the order MassBank_NIST.msp, MoNA-export-LC-MS,
      ms2_spectra_corinna.mgf (MSnLib v1.0 MSn MGFs, non-merged spectra; cell 7 file order nihnp_neg, mcescaf_neg,
      otavapep_neg, mcebio_neg, nihnp_pos, mcescaf_pos, otavapep_pos, mcebio_pos), then 46 GNPS library MGFs.
  3_remove_duplicates_and_profiled_spectra cell 2: spectra grouped by full source InChIKey in first-appearance order;
      within a group the kept spectra stay in source order. Cell 13 assigns MassSpecGymID in that order.
  So each contiguous run of one InChIKey is [MassBank][MoNA][MSnLib][GNPS] in that order, and a run's position in the
  identifier sequence reflects the source that first contributed that InChIKey. Later notebooks filter rows; the
  released identifiers are monotonic but not consecutive (verified below). Whether MassSpecGym 1.5 kept the 1.0
  identifier order is INFERRED from the monotonic identifiers, not documented.

Reads: exclusion/msnlib_key_libraries.csv (P5 step 1), the MassSpecGym identity parquet (identifier, inchikey, fold,
simulation_challenge, adduct, instrument_type, collision_energy), exclusion/msg15_row_keys.parquet (MURU parent keys).
Writes: exclusion/msg_row_msnlib_membership.parquet, exclusion/msg_run_region_composition.csv,
        exclusion/msg_row_msnlib_membership_summary.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "artifacts/ce_interface_adjudication/exclusion"
MSG_ID = ROOT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
V1 = {"MCEBIO", "NIHNP", "MCESCAF", "OTAVAPEP"}
REGION_BIN = 2000
MSG_META = ROOT / "artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet"   # P4 range read
# the integer CE values the feasibility audit reported for MSnLib-member Orbitrap rows (audit section 1.2); used only
# as a descriptive signature, not asserted to be the MSnLib acquisition ladder
MSNLIB_CE_SET = [15.0, 20.0, 30.0, 45.0, 60.0, 75.0]


def n_decimals(x) -> int | None:
    if x is None or pd.isna(x):
        return None
    s = repr(float(x))
    if "e" in s or "." not in s:
        return 0 if "." not in s and "e" not in s else -1
    return len(s.split(".")[1].rstrip("0"))


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    msg = pd.read_parquet(MSG_ID)
    rk = pd.read_parquet(EX / "msg15_row_keys.parquet")
    msg = msg.merge(rk[["identifier", "parent_key"]], on="identifier", how="left", validate="1:1")
    kl = pd.read_csv(EX / "msnlib_key_libraries.csv")
    libs = kl.set_index("key").libraries.to_dict()

    def lib_of(row_keys):
        s = set()
        for k in row_keys:
            if isinstance(k, str) and k in libs:
                s |= set(libs[k].split(";"))
        return s

    msg["identifier_num"] = msg.identifier.str.slice(13).astype(int)
    assert msg.identifier_num.is_monotonic_increasing
    all_libs = [lib_of((a, b)) for a, b in zip(msg.inchikey, msg.parent_key)]
    rec_hit = msg.inchikey.isin(libs.keys())
    par_hit = msg.parent_key.isin(libs.keys())
    out = pd.DataFrame({
        "identifier": msg.identifier,
        "identifier_num": msg.identifier_num,
        "inchikey14": msg.inchikey,
        "parent_key14": msg.parent_key,
        "fold": msg.fold,
        "simulation_challenge": msg.simulation_challenge,
        "adduct": msg.adduct,
        "instrument_type": msg.instrument_type,
        "collision_energy": msg.collision_energy,
        "in_msnlib_v1_compound": [bool(s & V1) for s in all_libs],
        "msnlib_v1_sublibraries": [";".join(sorted(s & V1)) for s in all_libs],
        "in_msnlib_9lib_compound": [bool(s) for s in all_libs],
        "msnlib_9lib_libraries": [";".join(sorted(s)) for s in all_libs],
        "match_route": np.select([rec_hit & par_hit, rec_hit, par_hit], ["recorded_and_parent", "recorded_only", "parent_only"], ""),
    })
    # contiguous runs of one recorded key in identifier order (approximates the full-InChIKey dedupe groups)
    run = (out.inchikey14 != out.inchikey14.shift()).cumsum().astype(int)
    out["run_index"] = run
    g = out.groupby("run_index")
    out["run_first_identifier_num"] = g.identifier_num.transform("min")
    out["run_length"] = g.identifier_num.transform("size")
    out["position_in_run"] = g.cumcount()
    out["n_runs_for_key"] = out.groupby("inchikey14").run_index.transform("nunique")
    out["key_first_identifier_num"] = out.groupby("inchikey14").identifier_num.transform("min")

    # region composition: per key, the library set vs the identifier bin of the key's first row
    fk = out.drop_duplicates("inchikey14")[["inchikey14", "key_first_identifier_num", "msnlib_v1_sublibraries", "in_msnlib_9lib_compound"]]
    fk = fk.assign(bin_start=fk.key_first_identifier_num // REGION_BIN * REGION_BIN)
    comp = pd.crosstab(fk.bin_start, fk.msnlib_v1_sublibraries.replace("", "NOT_IN_MSNLIB_V1"))
    comp.insert(0, "n_keys", comp.sum(1))
    comp.insert(1, "frac_in_msnlib_v1", 1 - comp["NOT_IN_MSNLIB_V1"] / comp["n_keys"])
    comp.to_csv(EX / "msg_run_region_composition.csv")

    # descriptive: rows whose key first appears inside a region where >= 99% of first-appearing keys are v1 members
    dense = set(comp.index[(comp.frac_in_msnlib_v1 >= 0.99) & (comp.n_keys >= 100)])
    in_dense = (out.key_first_identifier_num // REGION_BIN * REGION_BIN).isin(dense)
    ce_int = out.collision_energy.notna() & (out.collision_energy % 1 == 0)

    # candidate row-level signals (descriptive; no row is assigned to a source)
    out["key_first_in_dense_msnlib_bin"] = in_dense
    out["ce_in_msnlib_observed_set"] = out.collision_energy.isin(MSNLIB_CE_SET)
    if MSG_META.exists():
        pmz = pd.read_parquet(MSG_META, columns=["identifier", "precursor_mz"]).set_index("identifier").precursor_mz
        out["precursor_mz_decimals"] = out.identifier.map(pmz).map(n_decimals).astype("Int64")
    else:
        out["precursor_mz_decimals"] = pd.array([pd.NA] * len(out), dtype="Int64")
    out["msnlib_like_row_signature"] = (out.instrument_type.eq("Orbitrap") & out.ce_in_msnlib_observed_set
                                        & out.precursor_mz_decimals.isin([4, 5]).fillna(False).astype(bool))
    p = EX / "msg_row_msnlib_membership.parquet"
    out.to_parquet(p, index=False)
    sig = out.msnlib_like_row_signature
    signature_counts = {
        "definition": "instrument_type == Orbitrap AND collision_energy in {15,20,30,45,60,75} AND precursor_mz has 4 or 5 "
                      "decimal digits (repr of the released double)",
        "rows_key_first_in_dense_bins": int(in_dense.sum()),
        "rows_key_first_in_dense_bins_ce_nonnull": int((in_dense & out.collision_energy.notna()).sum()),
        "signature_rows_key_first_in_dense_bins": int((sig & in_dense).sum()),
        "signature_rows_v1_compound_outside_dense": int((sig & out.in_msnlib_v1_compound & ~in_dense).sum()),
        "rows_v1_compound_outside_dense": int((out.in_msnlib_v1_compound & ~in_dense).sum()),
        "signature_rows_9lib_not_v1_compound": int((sig & out.in_msnlib_9lib_compound & ~out.in_msnlib_v1_compound).sum()),
        "signature_rows_not_in_any_msnlib_compound": int((sig & ~out.in_msnlib_9lib_compound).sum()),
        "rows_not_in_any_msnlib_compound": int((~out.in_msnlib_9lib_compound).sum()),
        "dense_bins_position_in_run_median_ce_nonnull": float(out[in_dense & out.collision_energy.notna()].position_in_run.median()),
        "dense_bins_position_in_run_median_ce_null": float(out[in_dense & out.collision_energy.isna()].position_in_run.median()),
        "dense_bins_ce_null_decimals": out[in_dense & out.collision_energy.isna()].precursor_mz_decimals.value_counts().sort_index().pipe(lambda v: {str(k): int(x) for k, x in v.items()}),
        "dense_bins_ce_nonnull_decimals": out[in_dense & out.collision_energy.notna()].precursor_mz_decimals.value_counts().sort_index().pipe(lambda v: {str(k): int(x) for k, x in v.items()}),
    }

    def ce_table(mask):
        sub = out[mask]
        return {"n_rows": int(len(sub)), "instrument": sub.instrument_type.fillna("NA").value_counts().to_dict(),
                "adduct": sub.adduct.value_counts().to_dict(),
                "ce_null": int(sub.collision_energy.isna().sum()),
                "ce_integer_share_of_nonnull": float((ce_int & mask).sum() / max(int(sub.collision_energy.notna().sum()), 1)),
                "top_ce_values": {str(k): int(v) for k, v in sub.collision_energy.value_counts().head(12).items()}}

    orb = out.instrument_type.eq("Orbitrap")
    summary = {
        "script": "scripts/ce_interface_adjudication/p5_02_msg_msnlib_membership.py",
        "output_sha256": sha256_file(p),
        "n_rows": int(len(out)), "n_keys": int(out.inchikey14.nunique()),
        "identifiers_monotonic": True, "identifiers_consecutive": bool((np.diff(out.identifier_num) == 1).all()),
        "max_identifier_num": int(out.identifier_num.max()),
        "rows_parent_key_available": int(out.parent_key14.notna().sum()),
        "compound_membership": {
            "rows_in_msnlib_v1_compound": int(out.in_msnlib_v1_compound.sum()),
            "keys_in_msnlib_v1_compound": int(out[out.in_msnlib_v1_compound].inchikey14.nunique()),
            "rows_in_msnlib_9lib_compound": int(out.in_msnlib_9lib_compound.sum()),
            "keys_in_msnlib_9lib_compound": int(out[out.in_msnlib_9lib_compound].inchikey14.nunique()),
            "match_route_rows": out.match_route.replace("", "none").value_counts().to_dict(),
            "rows_by_v1_sublibrary_set": out.msnlib_v1_sublibraries.replace("", "none").value_counts().to_dict(),
            "orbitrap_rows_in_v1_compound": int((orb & out.in_msnlib_v1_compound).sum()),
            "by_fold_rows_in_v1_compound": out[out.in_msnlib_v1_compound].fold.value_counts().to_dict(),
        },
        "runs": {"n_runs": int(out.run_index.nunique()),
                 "keys_with_1_run": int((out.drop_duplicates("inchikey14").n_runs_for_key == 1).sum()),
                 "keys_with_2plus_runs": int((out.drop_duplicates("inchikey14").n_runs_for_key > 1).sum())},
        "dense_msnlib_first_appearance_bins": sorted(int(b) for b in dense),
        "rows_with_key_first_in_dense_bins": ce_table(in_dense),
        "rows_v1_compound_key_first_outside_dense_bins": ce_table(out.in_msnlib_v1_compound & ~in_dense),
        "rows_not_v1_compound": ce_table(~out.in_msnlib_v1_compound),
        "row_signature": signature_counts,
    }
    (EX / "msg_row_msnlib_membership_summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
