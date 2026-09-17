"""P3: attribute MassSpecGym 1.5 rows to source libraries from identifier order (identity/metadata columns only).

Mechanism (VERIFIED in pluskal-lab/MassSpecGym notebooks, see artifacts/ce_interface_adjudication/notes/p3_msg_curation.md):
  - notebook 1 cell 12 merges libraries in the fixed order MassBank_NIST.msp, MoNA-export-LC-MS_Spectra.msp,
    ms2_spectra_corinna.mgf (MSnLib v1.0, Zenodo 11163381), then 46 GNPS library MGFs;
  - notebook 3 cell 2 groups spectra by full InChIKey in first-appearance order and appends each group's
    spectra in their original (source) order; cell 13 then numbers spectra MassSpecGymID0000001..0414174;
  - later filters drop rows but never renumber.
  Therefore identifiers are grouped by molecule, molecules are ordered by the source of their first appearance,
  and inside a molecule the rows follow MassBank < MoNA < MSnLib < GNPS.

Blocks (by the identifier of a run's first row; a run = maximal consecutive rows sharing the 14-char key):
  A  molecules first seen in MassBank or MoNA (not separable from each other here)
  B  molecules first seen in MSnLib v1.0
  C  molecules first seen in GNPS
  C start = first run after which every row has a missing collision_energy (GNPS library MGFs carry no CE field).
  B start = earliest run start such that, over all runs from it up to C start, at most 0.5% of run first rows
            are NOT Orbitrap with CE in the MSnLib MS2 ladder {15,20,30,45,60,75}.

Row labels (INFERRED; heuristic in block A):
  C rows                                  -> GNPS
  B rows, CE present                      -> MSnLib_v1
  B rows, CE missing                      -> GNPS (appended to an MSnLib-first molecule)
  A rows: trailing CE-missing rows        -> GNPS_or_MoNA_missing_ce
          trailing Orbitrap-ladder rows (before those) of a molecule in an MSnLib v1.0 sub-library
                                          -> MSnLib_v1_probable
          all other rows                  -> MassBank_or_MoNA

Inputs: artifacts/comparator_feasibility/massspecgym15_identity.parquet (identity columns),
        optional artifacts/ce_interface_adjudication/exclusion/msg_row_msnlib_membership.parquet (P5 membership),
        optional artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet (P4; precursor_mz).
No spectrum column is read. Outputs under artifacts/ce_interface_adjudication/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/ce_interface_adjudication"
IDENTITY = ROOT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
MEMBERSHIP = OUT / "exclusion/msg_row_msnlib_membership.parquet"
METADATA = OUT / "massspecgym15_metadata_columns.parquet"
LADDER = [15.0, 20.0, 30.0, 45.0, 60.0, 75.0]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    inputs = {"identity": {"path": str(IDENTITY.relative_to(ROOT)), "sha256": sha256(IDENTITY)}}
    df = pd.read_parquet(IDENTITY)
    df["identifier_num"] = df.identifier.str[len("MassSpecGymID"):].astype(int)
    df = df.sort_values("identifier_num").reset_index(drop=True)
    assert df.identifier_num.is_monotonic_increasing and df.identifier_num.is_unique

    have_membership = MEMBERSHIP.exists()
    if have_membership:
        inputs["membership"] = {"path": str(MEMBERSHIP.relative_to(ROOT)), "sha256": sha256(MEMBERSHIP)}
        m = pd.read_parquet(MEMBERSHIP, columns=["identifier", "in_msnlib_v1_compound"])
        df = df.merge(m, on="identifier", how="left", validate="one_to_one")
        df["in_msnlib_v1_compound"] = df["in_msnlib_v1_compound"].fillna(False).astype(bool)
    else:
        df["in_msnlib_v1_compound"] = False

    have_mz = METADATA.exists()
    if have_mz:
        inputs["metadata"] = {"path": str(METADATA.relative_to(ROOT)), "sha256": sha256(METADATA)}
        mz = pd.read_parquet(METADATA, columns=["identifier", "precursor_mz"])
        df = df.merge(mz, on="identifier", how="left", validate="one_to_one")

    ce = df.collision_energy
    df["ce_missing"] = ce.isna()
    df["orbi_ladder"] = (df.instrument_type == "Orbitrap") & ce.isin(LADDER)
    df["run"] = (df.inchikey != df.inchikey.shift()).cumsum()
    df["pos"] = df.groupby("run").cumcount()
    runs = df.groupby("run").agg(first_id=("identifier_num", "min"), n=("identifier_num", "size"),
                                 all_missing=("ce_missing", "all"))
    runs["first_ladder"] = df[df.pos == 0].set_index("run").orbi_ladder.astype(bool)

    suffix_all_missing = runs.all_missing[::-1].cumprod()[::-1].astype(bool)
    c_start_run = runs.index[suffix_all_missing].min()
    c_start = int(runs.loc[c_start_run, "first_id"])

    pre = runs[runs.first_id < c_start]
    exc = (~pre.first_ladder)[::-1].cumsum()[::-1]
    cnt = pd.Series(np.arange(len(pre), 0, -1), index=pre.index)
    rate = exc / cnt
    b_start_run = rate[rate <= 0.005].index.min()
    b_start = int(runs.loc[b_start_run, "first_id"])

    run_first = df.run.map(runs.first_id)
    df["block"] = np.where(run_first >= c_start, "C_GNPS_first",
                           np.where(run_first >= b_start, "B_MSnLib_first", "A_MassBank_or_MoNA_first"))

    label = np.full(len(df), "MassBank_or_MoNA", dtype=object)
    label[(df.block == "C_GNPS_first").to_numpy()] = "GNPS"
    isB = (df.block == "B_MSnLib_first").to_numpy()
    miss = df.ce_missing.to_numpy()
    label[isB & ~miss] = "MSnLib_v1"
    label[isB & miss] = "GNPS"
    ladder = df.orbi_ladder.to_numpy()
    member = df.in_msnlib_v1_compound.to_numpy()
    a_idx = df.index[df.block == "A_MassBank_or_MoNA_first"].to_numpy()
    a_runs = df.run.to_numpy()[a_idx]
    bounds = np.flatnonzero(np.diff(a_runs)) + 1
    for seg in np.split(a_idx, bounds):
        k = len(seg) - 1
        while k >= 0 and miss[seg[k]]:
            label[seg[k]] = "GNPS_or_MoNA_missing_ce"
            k -= 1
        while k >= 0 and ladder[seg[k]] and member[seg[k]]:
            label[seg[k]] = "MSnLib_v1_probable"
            k -= 1
    df["source_label"] = label

    c0 = ce.fillna(0.0)
    is_int = np.isclose(c0, np.round(c0))
    is_half = np.isclose(c0 * 2, np.round(c0 * 2))
    df["ce_class"] = np.select([df.ce_missing, is_int, is_half], ["missing", "integer", "half_integer"],
                               "other_fractional")

    summary: dict = {
        "script": "scripts/ce_interface_adjudication/p3_msg_source_attribution.py",
        "inputs": inputs,
        "n_rows": int(len(df)), "n_runs": int(len(runs)),
        "block_boundaries": {"B_start_identifier_num": b_start, "C_start_identifier_num": c_start,
                             "B_first_row_exceptions": int(exc.loc[b_start_run]),
                             "B_runs": int(cnt.loc[b_start_run])},
        "rows_by_block": {k: int(v) for k, v in df.block.value_counts().items()},
        "rows_by_label": {k: int(v) for k, v in df.source_label.value_counts().items()},
    }
    tabs = {}
    for name, sub in [("all", df), ("simulation_challenge", df[df.simulation_challenge])]:
        t = pd.crosstab([sub.source_label, sub.instrument_type.fillna("NA")], sub.ce_class)
        tabs[name] = t
        summary[f"label_x_instrument_x_ce_class_{name}"] = {
            f"{i[0]}|{i[1]}": {k: int(v) for k, v in row.items()} for i, row in t.iterrows()}
        summary[f"label_by_fold_{name}"] = {
            str(i): {k: int(v) for k, v in row.items()}
            for i, row in pd.crosstab(sub.source_label, sub.fold).iterrows()}
    summary["top_ce_values_simulation_challenge_by_label"] = {
        lab: {str(k): int(v) for k, v in g.collision_energy.value_counts().head(15).items()}
        for lab, g in df[df.simulation_challenge].groupby("source_label")}

    if have_mz:
        x = df[(df.ce_class == "other_fractional") & df.precursor_mz.notna()].copy()
        x["implied_nce"] = x.collision_energy * 500.0 / x.precursor_mz
        x["resid"] = (x.implied_nce - np.round(x.implied_nce)).abs()
        summary["fractional_ce_back_conversion"] = {
            "definition": "implied_nce = collision_energy * 500 / precursor_mz; resid = |implied_nce - round|",
            "n_other_fractional_rows": int(len(x)),
            "share_resid_lt_0.01": float((x.resid < 0.01).mean()),
            "share_resid_lt_0.05": float((x.resid < 0.05).mean()),
            "implied_integer_nce_top_resid_lt_0.01": {
                str(int(k)): int(v) for k, v in np.round(x[x.resid < 0.01].implied_nce).value_counts().head(20).items()},
            "share_resid_lt_0.01_by_label": {lab: float((g.resid < 0.01).mean()) for lab, g in
                                             x.groupby("source_label")},
            "share_resid_lt_0.01_by_instrument": {str(k): float((g.resid < 0.01).mean()) for k, g in
                                                  x.groupby(x.instrument_type.fillna("NA"))},
            "n_by_label_x_instrument": {f"{i[0]}|{i[1]}": int(v) for i, v in
                                        x.groupby(["source_label", x.instrument_type.fillna("NA")]).size().items()},
        }

    cols = ["identifier", "identifier_num", "inchikey", "fold", "simulation_challenge", "adduct", "instrument_type",
            "collision_energy", "ce_class", "block", "source_label", "in_msnlib_v1_compound"]
    out_parquet = OUT / "p3_msg15_row_source_attribution.parquet"
    df[cols].to_parquet(out_parquet, index=False)
    summary["output_parquet"] = {"path": str(out_parquet.relative_to(ROOT)), "sha256": sha256(out_parquet)}
    (OUT / "p3_msg15_row_source_attribution_summary.json").write_text(json.dumps(summary, indent=1))
    pd.set_option("display.width", 220)
    print(json.dumps({k: summary[k] for k in ["inputs", "block_boundaries", "rows_by_block", "rows_by_label"]},
                     indent=1))
    for name, t in tabs.items():
        print("==", name)
        print(t.to_string())
    print(json.dumps(summary["top_ce_values_simulation_challenge_by_label"], indent=1))
    if have_mz:
        print(json.dumps(summary["fractional_ce_back_conversion"], indent=1))


if __name__ == "__main__":
    main()
