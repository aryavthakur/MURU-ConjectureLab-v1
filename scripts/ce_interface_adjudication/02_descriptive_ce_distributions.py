"""CE interface adjudication, P4 steps 2-3: join + cross-check + descriptive CE distributions.

Descriptive only. No convention is classified here.

Inputs (metadata only, no spectra, no model outputs):
  artifacts/comparator_feasibility/massspecgym15_identity.parquet        (identity columns, 231,104 rows)
  artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet  (scalar metadata, from script 01)
  /Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv   (ms-pred HEAD ed8311f)

Outputs: artifacts/ce_interface_adjudication/descriptive/*.csv, *.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "descriptive"
IDENTITY = ROOT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
METADATA = ADJ / "massspecgym15_metadata_columns.parquet"
MSPRED = Path("/Users/aryav/muru-comparators/repos/ms-pred")
LABELS = MSPRED / "data/spec_datasets/msg/labels.tsv"
EXPECTED_ROWS = 231_104
NA = "<NA>"
# Reference NCE sets used ONLY as descriptive landmarks (not as a convention rule):
#  - MSNLIB_AUDIT_SET: the integer values the pre-benchmark feasibility audit reported for MSnLib-library Orbitrap rows
#    (MURU_COMPARATOR_FEASIBILITY_AUDIT.md:106-107: 60, 20, 30, 45, 15, 75).
#  - MULT5: multiples of 5 in [5, 200].
MSNLIB_AUDIT_SET = {15, 20, 30, 45, 60, 75}
MULT5 = set(range(5, 201, 5))
QS = [0.0, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999, 1.0]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def shortest_repr(x: float) -> str:
    return np.format_float_positional(x, unique=True, trim="-")


def decimals_of(s: str) -> int:
    s = s.strip()
    if "e" in s.lower():
        raise ValueError(s)
    return len(s.split(".")[1]) if "." in s else 0


def qtable(series: pd.Series) -> dict:
    s = series.dropna().astype(float)
    d = {"n": int(len(s)), "n_unique": int(s.nunique()), "mean": float(s.mean()) if len(s) else None}
    for q in QS:
        d[f"q{q:g}"] = float(s.quantile(q)) if len(s) else None
    return d


def corr_row(df: pd.DataFrame, label: dict) -> dict:
    n = len(df)
    out = dict(label, n_rows=n, n_unique_ce=int(df.collision_energy.nunique()) if n else 0,
               n_unique_inchikey=int(df.inchikey.nunique()) if n else 0)
    if n >= 3 and df.collision_energy.nunique() > 1 and df.precursor_mz.nunique() > 1:
        out["pearson_ce_precursor_mz"] = float(df.collision_energy.corr(df.precursor_mz))
        out["spearman_ce_precursor_mz"] = float(df.collision_energy.rank().corr(df.precursor_mz.rank()))
    else:
        out["pearson_ce_precursor_mz"] = None
        out["spearman_ce_precursor_mz"] = None
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ident = pd.read_parquet(IDENTITY)
    meta = pd.read_parquet(METADATA)
    lab = pd.read_csv(LABELS, sep="\t", dtype=str, keep_default_na=False)
    summary: dict = {
        "inputs": {
            "identity_parquet": {"path": str(IDENTITY.relative_to(ROOT)), "sha256": sha256(IDENTITY)},
            "metadata_parquet": {"path": str(METADATA.relative_to(ROOT)), "sha256": sha256(METADATA)},
            "mspred_labels_tsv": {"path": str(LABELS), "sha256": sha256(LABELS),
                                  "mspred_head": subprocess.run(["git", "-C", str(MSPRED), "rev-parse", "HEAD"],
                                                                capture_output=True, text=True).stdout.strip(),
                                  "last_commit_touching_file": subprocess.run(
                                      ["git", "-C", str(MSPRED), "log", "-1", "--format=%H %ad %s", "--",
                                       "data/spec_datasets/msg/labels.tsv"], capture_output=True, text=True
                                  ).stdout.strip()},
        }
    }

    # ---------------------------------------------------------------- step 2: join and cross-check
    assert len(ident) == EXPECTED_ROWS and len(meta) == EXPECTED_ROWS
    assert ident.identifier.is_unique and meta.identifier.is_unique
    df = ident.merge(meta, on="identifier", how="inner", validate="one_to_one")
    same_order = bool((ident.identifier.values == meta.identifier.values).all())
    join = {"identity_rows": len(ident), "metadata_rows": len(meta), "inner_join_rows": len(df),
            "identifiers_only_in_identity": int((~ident.identifier.isin(meta.identifier)).sum()),
            "identifiers_only_in_metadata": int((~meta.identifier.isin(ident.identifier)).sum()),
            "row_order_identical": same_order, "join_exact": len(df) == EXPECTED_ROWS}
    assert join["join_exact"]
    df["instrument_type"] = df.instrument_type.fillna(NA)
    df["adduct"] = df.adduct.fillna(NA)
    df["ce_missing"] = df.collision_energy.isna()
    join["null_counts"] = {c: int(df[c].isna().sum()) for c in
                           ["precursor_mz", "parent_mass", "formula", "precursor_formula", "smiles", "inchikey"]}
    join["null_counts"]["collision_energy"] = int(df.ce_missing.sum())
    join["null_counts"]["instrument_type_NA"] = int((df.instrument_type == NA).sum())
    join["null_counts"]["adduct_NA"] = int((df.adduct == NA).sum())
    df.to_parquet(ADJ / "massspecgym15_identity_metadata_joined.parquet", index=False)
    join["joined_parquet_sha256"] = sha256(ADJ / "massspecgym15_identity_metadata_joined.parquet")
    summary["join"] = join

    # labels.tsv vs parquet
    lab_ids = set(lab.spec)
    sim = df[df.simulation_challenge]
    sim_ids = set(sim.identifier)
    all_ids = set(df.identifier)
    x = lab.merge(df, left_on="spec", right_on="identifier", how="left", indicator=True)
    x_in = x[x._merge == "both"].copy()
    prec_lab = x_in.precursor.astype(float)
    ce_lab_str = x_in.collision_energies.str.extract(r"^\['([^']*)'\]$")[0]
    x_in["ce_label_str"] = ce_lab_str
    x_in["ce_label"] = pd.to_numeric(ce_lab_str, errors="coerce")
    x_in["precursor_label"] = prec_lab
    x_in["precursor_abs_diff"] = (prec_lab - x_in.precursor_mz).abs()
    x_in["precursor_label_str_eq_parquet_shortest_repr"] = x_in.precursor == x_in.precursor_mz.map(shortest_repr)
    canon = {}
    for smi in pd.unique(pd.concat([x_in.smiles_x, x_in.smiles_y])):
        mol = Chem.MolFromSmiles(smi)
        canon[smi] = Chem.MolToSmiles(mol) if mol is not None else None
    x_in["smiles_canon_label"] = x_in.smiles_x.map(canon)
    x_in["smiles_canon_parquet"] = x_in.smiles_y.map(canon)
    x_in["smiles_canon_equal"] = (x_in.smiles_canon_label == x_in.smiles_canon_parquet) & x_in.smiles_canon_label.notna()
    x_in["parquet_ce_is_integer"] = x_in.collision_energy == np.round(x_in.collision_energy)
    lab_cmp = {
        "labels_rows": len(lab), "labels_unique_spec": int(lab.spec.nunique()),
        "labels_columns": lab.columns.tolist(),
        "labels_unnamed0_equals_rownumber": bool((lab["Unnamed: 0"].astype(int).values == np.arange(len(lab))).all()),
        "labels_dataset_values": lab.dataset.value_counts().to_dict(),
        "labels_ionization_values": lab.ionization.value_counts().to_dict(),
        "labels_instrument_values": lab.instrument.value_counts().to_dict(),
        "labels_collision_energies_single_value_list_format": int(ce_lab_str.notna().sum()),
        "parquet_simulation_challenge_rows": len(sim),
        "parquet_simulation_challenge_ce_missing": int(sim.ce_missing.sum()),
        "labels_spec_in_parquet": int(len(x_in)),
        "labels_spec_not_in_parquet": sorted(lab_ids - all_ids)[:50],
        "n_labels_spec_not_in_parquet": len(lab_ids - all_ids),
        "n_labels_minus_sim": len(lab_ids - sim_ids),
        "n_sim_minus_labels": len(sim_ids - lab_ids),
        "n_labels_and_sim": len(lab_ids & sim_ids),
        "labels_minus_sim_examples": sorted(lab_ids - sim_ids)[:50],
        "sim_minus_labels_examples": sorted(sim_ids - lab_ids)[:50],
        "sim_minus_labels_ce_missing": int(sim[~sim.identifier.isin(lab_ids)].ce_missing.sum()),
        "labels_rows_whose_parquet_ce_missing": int(x_in.ce_missing.sum()),
        "precursor_exact_float_equal": int((prec_lab == x_in.precursor_mz).sum()),
        "precursor_label_string_equals_parquet_shortest_repr": int(x_in.precursor_label_str_eq_parquet_shortest_repr.sum()),
        "precursor_abs_diff_le_1e-9": int((x_in.precursor_abs_diff <= 1e-9).sum()),
        "precursor_abs_diff_le_1e-4": int((x_in.precursor_abs_diff <= 1e-4).sum()),
        "precursor_mismatch_rows": int((prec_lab != x_in.precursor_mz).sum()),
        "precursor_abs_diff_max": float(x_in.precursor_abs_diff.max()),
        "ce_exact_float_equal": int((x_in.ce_label == x_in.collision_energy).sum()),
        "ce_mismatch_rows": int((x_in.ce_label != x_in.collision_energy).sum()),
        "ce_label_unparseable": int(x_in.ce_label.isna().sum()),
        "instrument_equal": int((x_in.instrument == x_in.instrument_type).sum()),
        "adduct_equal": int((x_in.ionization == x_in.adduct).sum()),
        "inchikey_equal": int((x_in.inchikey_x == x_in.inchikey_y).sum()),
        "formula_equal": int((x_in.formula_x == x_in.formula_y).sum()),
        "smiles_string_equal": int((x_in.smiles_x == x_in.smiles_y).sum()),
        "smiles_rdkit_canonical_equal": int(x_in.smiles_canon_equal.sum()),
        "smiles_rdkit_parse_failures": int(x_in.smiles_canon_label.isna().sum() + x_in.smiles_canon_parquet.isna().sum()),
        "ce_mismatch_rows_that_are_parquet_non_integer": int(((x_in.ce_label != x_in.collision_energy)
                                                              & ~x_in.parquet_ce_is_integer).sum()),
        "parquet_non_integer_ce_rows_in_labels": int((~x_in.parquet_ce_is_integer).sum()),
        "labels_ce_equals_trunc_of_parquet_ce_all_rows": bool((x_in.ce_label == np.trunc(x_in.collision_energy)).all()),
        "labels_ce_equals_python_round_of_parquet_ce_non_integer_rows": int(
            (x_in.ce_label[~x_in.parquet_ce_is_integer] == np.round(x_in.collision_energy[~x_in.parquet_ce_is_integer])).sum()),
        "labels_ce_minus_parquet_ce_non_integer_rows_quantiles": {f"q{q:g}": float(
            (x_in.ce_label - x_in.collision_energy)[~x_in.parquet_ce_is_integer].quantile(q)) for q in (0, 0.5, 1)},
        "ce_mismatch_by_instrument": x_in[x_in.ce_label != x_in.collision_energy].instrument.value_counts().to_dict(),
        "labels_fold_of_matched_rows": x_in.fold.value_counts().to_dict(),
        "sim_subset_fold": sim.fold.value_counts().to_dict(),
        "mspred_msg_split_files_present_locally": sorted(
            str(p.relative_to(MSPRED)) for p in (MSPRED / "data/spec_datasets/msg").rglob("*") if p.is_file()),
    }
    summary["labels_vs_parquet"] = lab_cmp
    mm_cols = ["spec", "instrument", "instrument_type", "ionization", "adduct", "precursor", "precursor_mz",
               "precursor_abs_diff", "collision_energies", "collision_energy", "fold", "simulation_challenge"]
    mm = x_in[(x_in.precursor_label != x_in.precursor_mz) | (x_in.ce_label != x_in.collision_energy)
              | (x_in.instrument != x_in.instrument_type) | (x_in.ionization != x_in.adduct)
              | (x_in.inchikey_x != x_in.inchikey_y) | (x_in.formula_x != x_in.formula_y)
              | ~x_in.smiles_canon_equal]
    mm = mm.assign(precursor_mismatch=mm.precursor_label != mm.precursor_mz,
                   ce_mismatch=mm.ce_label != mm.collision_energy,
                   instrument_mismatch=mm.instrument != mm.instrument_type,
                   adduct_mismatch=mm.ionization != mm.adduct,
                   inchikey_mismatch=mm.inchikey_x != mm.inchikey_y,
                   formula_mismatch=mm.formula_x != mm.formula_y,
                   smiles_canonical_mismatch=~mm.smiles_canon_equal)
    # raw SMILES strings differ in form for most rows (labels.tsv Kekule vs parquet aromatic) but are RDKit-canonically
    # identical; string-level SMILES differences are counted in the summary, not listed row by row.
    mm = mm.assign(labels_ce_is_trunc_of_parquet=mm.ce_label == np.trunc(mm.collision_energy))
    mm[mm_cols + ["labels_ce_is_trunc_of_parquet"] + [c for c in mm.columns if c.endswith("_mismatch")]].to_csv(
        OUT / "labels_vs_parquet_mismatches.csv", index=False)
    lab_cmp["mismatch_rows_any_field"] = int(len(mm))
    lab_cmp["mismatch_counts_by_field"] = {c: int(mm[c].sum()) for c in mm.columns if c.endswith("_mismatch")}
    setdiff = pd.DataFrame(
        [{"identifier": i, "side": "labels_not_in_sim_subset"} for i in sorted(lab_ids - sim_ids)]
        + [{"identifier": i, "side": "sim_subset_not_in_labels"} for i in sorted(sim_ids - lab_ids)],
        columns=["identifier", "side"])
    setdiff = setdiff.merge(df[["identifier", "instrument_type", "adduct", "fold", "simulation_challenge",
                                "collision_energy", "ce_missing"]], on="identifier", how="left")
    setdiff.to_csv(OUT / "labels_vs_sim_subset_setdiff.csv", index=False)

    # ---------------------------------------------------------------- step 3a: cross-tab counts
    ct = (df.groupby(["instrument_type", "adduct", "simulation_challenge", "fold", "ce_missing"], dropna=False)
          .agg(n_rows=("identifier", "size"), n_unique_inchikey=("inchikey", "nunique")).reset_index())
    ct.to_csv(OUT / "counts_instrument_adduct_simchallenge_fold_cemissing.csv", index=False)
    ct2 = (df.groupby(["instrument_type", "simulation_challenge", "ce_missing"], dropna=False)
           .agg(n_rows=("identifier", "size"), n_unique_inchikey=("inchikey", "nunique")).reset_index())
    ct2.to_csv(OUT / "counts_instrument_simchallenge_cemissing.csv", index=False)

    # ---------------------------------------------------------------- step 3b: CE value frequency per instrument
    nm = df[~df.ce_missing].copy()
    nm["ce_repr"] = nm.collision_energy.map(shortest_repr)
    nm["ce_decimals"] = nm.ce_repr.map(decimals_of)
    nm["ce_is_integer"] = np.isclose(nm.collision_energy, np.round(nm.collision_energy), rtol=0, atol=0)
    freq = (nm.groupby(["instrument_type", "collision_energy"])
            .agg(ce_repr=("ce_repr", "first"), ce_decimals=("ce_decimals", "first"),
                 n_rows=("identifier", "size"), n_simulation_challenge=("simulation_challenge", "sum"),
                 n_unique_inchikey=("inchikey", "nunique"),
                 n_adduct_MH=("adduct", lambda s: int((s == "[M+H]+").sum())),
                 precursor_mz_min=("precursor_mz", "min"), precursor_mz_median=("precursor_mz", "median"),
                 precursor_mz_max=("precursor_mz", "max"))
            .reset_index().sort_values(["instrument_type", "n_rows"], ascending=[True, False]))
    freq["frac_of_instrument_nonmissing"] = freq.n_rows / freq.groupby("instrument_type").n_rows.transform("sum")
    freq.to_csv(OUT / "ce_value_frequency_by_instrument.csv", index=False)
    miss = df.groupby("instrument_type").agg(n_rows=("identifier", "size"), n_ce_missing=("ce_missing", "sum"),
                                              n_unique_ce=("collision_energy", "nunique")).reset_index()
    miss.to_csv(OUT / "ce_missing_and_unique_by_instrument.csv", index=False)

    # ---------------------------------------------------------------- step 3c: integer / decimals per instrument
    dec_rows = []
    for (inst, simflag), g in list(nm.groupby(["instrument_type", "simulation_challenge"])) + [
            ((i, "all"), g) for i, g in nm.groupby("instrument_type")]:
        r = {"instrument_type": inst, "simulation_challenge": simflag, "n_nonmissing": len(g),
             "n_integer": int(g.ce_is_integer.sum()), "n_non_integer": int((~g.ce_is_integer).sum())}
        for d in range(0, 7):
            r[f"n_decimals_{d}"] = int((g.ce_decimals == d).sum())
        r["n_decimals_7plus"] = int((g.ce_decimals >= 7).sum())
        r["n_unique_values"] = int(g.collision_energy.nunique())
        r["n_unique_integer_values"] = int(g[g.ce_is_integer].collision_energy.nunique())
        r["n_unique_non_integer_values"] = int(g[~g.ce_is_integer].collision_energy.nunique())
        dec_rows.append(r)
    pd.DataFrame(dec_rows).to_csv(OUT / "ce_integer_decimal_counts_by_instrument.csv", index=False)

    # Caveat check on decimal counts: the HF parquet stores float64, not the TSV text. A repr with >= 13 decimals can be
    # either literal long text in the TSV or a non-correctly-rounded text->double parse of a short decimal. For each
    # such value, find the fewest decimals k <= 12 whose decimal rounding lies within n ULPs of the stored double.
    long_rows = []
    for (inst, v), grp in nm[nm.ce_decimals >= 13].groupby(["instrument_type", "collision_energy"]):
        ulp = float(np.spacing(v))
        best_k, best_ulps = None, None
        for k in range(0, 13):
            dist = abs(round(v, k) - v) / ulp
            if dist <= 4:
                best_k, best_ulps = k, dist
                break
        long_rows.append({"instrument_type": inst, "ce_repr": shortest_repr(v), "n_rows": len(grp),
                          "fewest_decimals_within_4ulp": best_k, "ulps_from_that_rounding": best_ulps})
    lr_df = pd.DataFrame(long_rows)
    lr_df.to_csv(OUT / "ce_long_repr_ulp_check.csv", index=False)
    summary["long_repr_ulp_check"] = {
        f"{i}|k={k}": int(n) for (i, k), n in
        lr_df.groupby(["instrument_type", "fewest_decimals_within_4ulp"], dropna=False).n_rows.sum().items()}
    summary["long_repr_ulp_distance_rows"] = {
        f"ulps={u}": int(n) for u, n in
        lr_df.assign(u=lr_df.ulps_from_that_rounding.round(3)).groupby("u", dropna=False).n_rows.sum().items()}

    # ---------------------------------------------------------------- step 3d: CE*500/precursor_mz
    # If a stored CE were round(NCE * m / 500, d) for integer NCE and the same m as stored precursor_mz, then
    # |CE*500/m - NCE| <= 0.5*10^-d * 500/m = 250*10^-d / m. A precursor rounding slack of 5e-5 in m adds
    # <= r*5e-5/m. tol_d = 250*10^-d/m + r*5e-5/m + 1e-9. Chance baseline under a uniform fractional part is
    # min(1, 2*tol_d) per row (reported as its mean). d=0 tolerance is large (>= 0.25 for m <= 1000).
    nm["ratio"] = nm.collision_energy * 500.0 / nm.precursor_mz
    nm["ratio_nearest_int"] = np.round(nm.ratio).astype("Int64")
    nm["ratio_dist"] = (nm.ratio - np.round(nm.ratio)).abs()
    for d in (0, 1, 2):
        tol = 250.0 * 10.0 ** (-d) / nm.precursor_mz + nm.ratio * 5e-5 / nm.precursor_mz + 1e-9
        nm[f"tol_d{d}"] = tol
        nm[f"near_int_d{d}"] = nm.ratio_dist <= tol
        nm[f"chance_d{d}"] = np.minimum(1.0, 2 * tol)
    # additional descriptive levels: "tight" = the stored CE is reproduced by (integer * stored precursor_mz / 500) up to
    # float noise (|r - round(r)| <= 1e-6); "own" = tolerance from the row's own stored decimal count k (k capped at 12,
    # since reprs with >= 13 decimals are float noise of an unrounded product), no precursor slack.
    nm["tol_tight"] = 1e-6
    nm["near_int_tight"] = nm.ratio_dist <= 1e-6
    nm["chance_tight"] = 2e-6
    own_k = nm.ce_decimals.clip(upper=12)
    nm["tol_own"] = 250.0 * 10.0 ** (-own_k.astype(float)) / nm.precursor_mz + 1e-9
    nm["near_int_own"] = nm.ratio_dist <= nm.tol_own
    nm["chance_own"] = np.minimum(1.0, 2 * nm.tol_own)
    nm["nearest_int_in_msnlib_audit_set"] = nm.ratio_nearest_int.isin(list(MSNLIB_AUDIT_SET))
    nm["nearest_int_multiple_of_5"] = nm.ratio_nearest_int.isin(list(MULT5))
    nm["ce_in_msnlib_audit_set"] = nm.ce_is_integer & nm.collision_energy.isin(list(MSNLIB_AUDIT_SET))

    ratio_rows = []
    groups = [("all", lambda g: g), ("ce_integer", lambda g: g[g.ce_is_integer]),
              ("ce_non_integer", lambda g: g[~g.ce_is_integer])]
    groups += [(f"ce_decimals_{k}", (lambda k: (lambda g: g[g.ce_decimals == k]))(k)) for k in range(0, 5)]
    groups += [("ce_decimals_5plus", lambda g: g[g.ce_decimals >= 5])]
    for inst, gi in nm.groupby("instrument_type"):
        for simflag in ("all", True, False):
            gs = gi if simflag == "all" else gi[gi.simulation_challenge == simflag]
            for gname, fn in groups:
                g = fn(gs)
                r = {"instrument_type": inst, "simulation_challenge": simflag, "subset": gname, "n_rows": len(g)}
                if len(g):
                    for key in ("d0", "d1", "d2", "tight", "own"):
                        r[f"n_near_int_{key}"] = int(g[f"near_int_{key}"].sum())
                        r[f"frac_near_int_{key}"] = float(g[f"near_int_{key}"].mean())
                        r[f"chance_baseline_mean_{key}"] = float(g[f"chance_{key}"].mean())
                        r[f"n_near_int_{key}_nearest_in_msnlib_audit_set"] = int(
                            (g[f"near_int_{key}"] & g.nearest_int_in_msnlib_audit_set).sum())
                        r[f"n_near_int_{key}_nearest_multiple_of_5"] = int(
                            (g[f"near_int_{key}"] & g.nearest_int_multiple_of_5).sum())
                    r["n_ce_integer_in_msnlib_audit_set"] = int(g.ce_in_msnlib_audit_set.sum())
                    for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99):
                        r[f"ratio_q{q:g}"] = float(g.ratio.quantile(q))
                        r[f"ratio_dist_q{q:g}"] = float(g.ratio_dist.quantile(q))
                ratio_rows.append(r)
    pd.DataFrame(ratio_rows).to_csv(OUT / "ratio_ce500_over_mz_near_integer_tests.csv", index=False)

    # histogram of the fractional distance, per instrument x CE-integer flag (0.01 bins on [0, 0.5])
    bins = np.linspace(0, 0.5, 51)
    hist_rows = []
    for (inst, isint), g in nm.groupby(["instrument_type", "ce_is_integer"]):
        h, _ = np.histogram(g.ratio_dist.clip(0, 0.5), bins=bins)
        for lo, hi, c in zip(bins[:-1], bins[1:], h):
            hist_rows.append({"instrument_type": inst, "ce_is_integer": bool(isint), "dist_lo": round(lo, 3),
                              "dist_hi": round(hi, 3), "n_rows": int(c)})
    pd.DataFrame(hist_rows).to_csv(OUT / "ratio_distance_to_nearest_integer_histogram.csv", index=False)

    # nearest-integer ratio value frequency for near-integer rows (d=2 and tight tolerances), all instruments
    for key in ("d2", "tight"):
        near = nm[nm[f"near_int_{key}"]]
        nfreq = (near.groupby(["instrument_type", "ce_is_integer", "ratio_nearest_int"])
                 .agg(n_rows=("identifier", "size"), n_unique_ce=("collision_energy", "nunique"),
                      n_unique_inchikey=("inchikey", "nunique"),
                      n_simulation_challenge=("simulation_challenge", "sum"),
                      pearson_ce_mz=("collision_energy",
                                     lambda v, near=near: float(v.corr(near.loc[v.index, "precursor_mz"]))
                                     if len(v) > 2 and v.nunique() > 1 else np.nan))
                 .reset_index())
        nfreq["in_msnlib_audit_set"] = nfreq.ratio_nearest_int.isin(list(MSNLIB_AUDIT_SET))
        nfreq["multiple_of_5"] = nfreq.ratio_nearest_int.isin(list(MULT5))
        nfreq = nfreq.sort_values(["instrument_type", "ce_is_integer", "n_rows"], ascending=[True, True, False])
        nfreq.to_csv(OUT / f"ratio_nearest_integer_frequency_near_int_{key}.csv", index=False)

    # Orbitrap-only full per-row ratio table (identifier + scalar metadata + ratio tests), for later phases
    orb = nm[nm.instrument_type == "Orbitrap"]
    orb[["identifier", "inchikey", "fold", "simulation_challenge", "adduct", "precursor_mz", "collision_energy",
         "ce_repr", "ce_decimals", "ce_is_integer", "ratio", "ratio_nearest_int", "ratio_dist", "tol_d0", "tol_d1",
         "tol_d2", "tol_own", "near_int_d0", "near_int_d1", "near_int_d2", "near_int_tight", "near_int_own",
         "nearest_int_in_msnlib_audit_set",
         "ce_in_msnlib_audit_set"]].to_csv(OUT / "orbitrap_rows_ratio_tests.csv.gz", index=False)

    # ---------------------------------------------------------------- step 3e: CE vs precursor_mz correlation
    cr = []
    for inst, gi in nm.groupby("instrument_type"):
        for simflag in ("all", True, False):
            gs = gi if simflag == "all" else gi[gi.simulation_challenge == simflag]
            sets = {"all_nonmissing": gs, "ce_integer": gs[gs.ce_is_integer], "ce_non_integer": gs[~gs.ce_is_integer],
                    "ce_integer_in_msnlib_audit_set": gs[gs.ce_in_msnlib_audit_set],
                    "ce_integer_not_in_msnlib_audit_set": gs[gs.ce_is_integer & ~gs.ce_in_msnlib_audit_set],
                    "ratio_near_int_d2": gs[gs.near_int_d2], "ratio_not_near_int_d2": gs[~gs.near_int_d2],
                    "ce_non_integer_ratio_near_int_d2": gs[~gs.ce_is_integer & gs.near_int_d2],
                    "ce_non_integer_ratio_not_near_int_d2": gs[~gs.ce_is_integer & ~gs.near_int_d2],
                    "ce_integer_ratio_near_int_d2": gs[gs.ce_is_integer & gs.near_int_d2],
                    "ce_integer_ratio_not_near_int_d2": gs[gs.ce_is_integer & ~gs.near_int_d2],
                    "ratio_near_int_tight": gs[gs.near_int_tight], "ratio_not_near_int_tight": gs[~gs.near_int_tight],
                    "ce_non_integer_ratio_near_int_tight": gs[~gs.ce_is_integer & gs.near_int_tight],
                    "ce_non_integer_ratio_not_near_int_tight": gs[~gs.ce_is_integer & ~gs.near_int_tight],
                    "ce_integer_ratio_near_int_tight": gs[gs.ce_is_integer & gs.near_int_tight],
                    "ce_integer_ratio_not_near_int_tight": gs[gs.ce_is_integer & ~gs.near_int_tight]}
            for k in range(0, 5):
                sets[f"ce_decimals_{k}"] = gs[gs.ce_decimals == k]
            for name, g in sets.items():
                cr.append(corr_row(g, {"instrument_type": inst, "simulation_challenge": simflag, "ce_value_set": name}))
    pd.DataFrame(cr).to_csv(OUT / "ce_precursor_mz_correlation_by_value_set.csv", index=False)

    # Within one stored CE value the CE is constant, so the per-value association with precursor_mz is reported as the
    # precursor_mz min/median/max per value in ce_value_frequency_by_instrument.csv, not as a correlation.
    # Descriptive OLS of CE on precursor_mz per instrument x decimals class x integer flag (no model implied).
    fits = []
    nm["dec_class"] = nm.ce_decimals.clip(upper=5).astype(str).replace({"5": "5plus"})
    for (inst, dc, tight), g in nm.groupby(["instrument_type", "dec_class", "near_int_tight"]):
        row = {"instrument_type": inst, "ce_decimals_class": dc, "ratio_near_int_tight": bool(tight), "n_rows": len(g),
               "n_unique_ce": int(g.collision_energy.nunique())}
        if len(g) >= 3 and g.precursor_mz.nunique() > 1:
            A = np.vstack([g.precursor_mz.values, np.ones(len(g))]).T
            coef = np.linalg.lstsq(A, g.collision_energy.values, rcond=None)[0]
            row.update(slope=float(coef[0]), intercept=float(coef[1]),
                       resid_sd=float(np.std(g.collision_energy.values - A @ coef)),
                       ce_over_mz_q05=float((g.collision_energy / g.precursor_mz).quantile(0.05)),
                       ce_over_mz_q50=float((g.collision_energy / g.precursor_mz).quantile(0.5)),
                       ce_over_mz_q95=float((g.collision_energy / g.precursor_mz).quantile(0.95)))
        fits.append(row)
    pd.DataFrame(fits).to_csv(OUT / "ce_linear_fit_on_precursor_mz_by_decimals.csv", index=False)

    # ---------------------------------------------------------------- step 3f: labels.tsv CE quantiles per instrument
    labq = []
    lce = pd.to_numeric(lab.collision_energies.str.extract(r"^\['([^']*)'\]$")[0], errors="coerce")
    lab = lab.assign(ce=lce, ce_str=lab.collision_energies.str.extract(r"^\['([^']*)'\]$")[0])
    for inst, g in list(lab.groupby("instrument")) + [("all", lab)]:
        r = {"instrument": inst, **qtable(g.ce)}
        r["n_unparseable"] = int(g.ce.isna().sum())
        r["n_integer"] = int((g.ce == np.round(g.ce)).sum())
        r["n_non_integer"] = int((g.ce != np.round(g.ce)).sum())
        decs = g.ce_str.dropna().map(decimals_of)
        for d in range(0, 5):
            r[f"n_string_decimals_{d}"] = int((decs == d).sum())
        r["n_string_decimals_5plus"] = int((decs >= 5).sum())
        gm = pd.to_numeric(g.precursor, errors="coerce")
        lr = g.ce * 500.0 / gm
        ld = (lr - np.round(lr)).abs()
        r["n_labels_ratio_near_int_tight"] = int((ld <= 1e-6).sum())
        r["n_labels_ratio_near_int_d2"] = int((ld <= 250.0 * 0.01 / gm + lr * 5e-5 / gm + 1e-9).sum())
        pq_ = qtable(gm)
        r.update({f"precursor_{k}": v for k, v in pq_.items()})
        labq.append(r)
    pd.DataFrame(labq).to_csv(OUT / "mspred_msg_labels_ce_quantiles_by_instrument.csv", index=False)
    lfreq = (lab.groupby(["instrument", "ce_str"]).size().rename("n_rows").reset_index()
             .assign(ce=lambda t: pd.to_numeric(t.ce_str, errors="coerce"))
             .sort_values(["instrument", "n_rows"], ascending=[True, False]))
    lfreq.to_csv(OUT / "mspred_msg_labels_ce_value_frequency_by_instrument.csv", index=False)

    # ---------------------------------------------------------------- headline numbers
    def pick(inst):
        g = nm[nm.instrument_type == inst]
        return {"n_nonmissing": len(g), "n_integer": int(g.ce_is_integer.sum()),
                "n_non_integer": int((~g.ce_is_integer).sum()),
                "decimals": {str(k): int(v) for k, v in g.ce_decimals.value_counts().sort_index().items()},
                "n_unique_values": int(g.collision_energy.nunique()),
                "top10_values": {shortest_repr(k): int(v) for k, v in g.collision_energy.value_counts().head(10).items()},
                "near_int_d2_all": int(g.near_int_d2.sum()), "near_int_d1_all": int(g.near_int_d1.sum()),
                "near_int_tight_all": int(g.near_int_tight.sum()),
                "near_int_tight_non_integer": int((g.near_int_tight & ~g.ce_is_integer).sum()),
                "near_int_tight_integer": int((g.near_int_tight & g.ce_is_integer).sum()),
                "near_int_own_non_integer": int((g.near_int_own & ~g.ce_is_integer).sum()),
                "chance_own_expected_non_integer": float(g[~g.ce_is_integer].chance_own.sum()),
                "non_integer_simulation_challenge": int((~g.ce_is_integer & g.simulation_challenge).sum()),
                "near_int_d2_non_integer": int((g.near_int_d2 & ~g.ce_is_integer).sum()),
                "near_int_d2_integer": int((g.near_int_d2 & g.ce_is_integer).sum()),
                "chance_d2_expected_non_integer": float(g[~g.ce_is_integer].chance_d2.sum()),
                "chance_d2_expected_integer": float(g[g.ce_is_integer].chance_d2.sum()),
                "ce_integer_in_msnlib_audit_set": int(g.ce_in_msnlib_audit_set.sum())}
    summary["headline"] = {inst: pick(inst) for inst in sorted(nm.instrument_type.unique())}
    summary["headline"]["ce_missing_by_instrument"] = miss.set_index("instrument_type").n_ce_missing.astype(int).to_dict()
    (OUT / "p4_summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "inputs"}, indent=1, default=str)[:12000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
