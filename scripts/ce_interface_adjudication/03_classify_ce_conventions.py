"""Q: count training rows of the frozen ICEBERG 2.1 msg_simulation (gen, inten_contr) and GLACIER msg checkpoints
by collision-energy (CE) convention.

The classification rule is predeclared in artifacts/ce_interface_adjudication/notes/q_counts.md (Part 1, frozen
before this script computed any category count; its sha256 at freeze time is recorded in the JSON output).

Inputs (identity / metadata / code only; no spectra, no model output, no model is run):
  artifacts/comparator_feasibility/massspecgym15_identity.parquet            MSG 1.5 CE, instrument, fold, sim flag
  artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet P4 range read: precursor_mz
  artifacts/ce_interface_adjudication/exclusion/msg_row_msnlib_membership.parquet  P5: sub-library membership
  artifacts/ce_interface_adjudication/p3_msg15_row_source_attribution.parquet      P3: cross-check of block labels
  artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl     epoch / global_step only
  ms-pred ed8311f: data/spec_datasets/msg/labels.tsv, data_scripts/create_msg_simulation_dataset.py (functions
  extracted verbatim with ast and executed on the MSG 1.5 values)

Outputs under artifacts/ce_interface_adjudication/counts/.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ADJ = ROOT / "artifacts/ce_interface_adjudication"
OUT = ADJ / "counts"
IDENTITY = ROOT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
METADATA = ADJ / "massspecgym15_metadata_columns.parquet"
MEMBERSHIP = ADJ / "exclusion/msg_row_msnlib_membership.parquet"
P3_ATTR = ADJ / "p3_msg15_row_source_attribution.parquet"
RULE_NOTE = ADJ / "notes/q_counts.md"
T1 = ROOT / "artifacts/comparator_benchmark/technical/t1/checkpoint_hyperparameters.jsonl"
MSPRED = Path("/Users/aryav/muru-comparators/repos/ms-pred")
LABELS = MSPRED / "data/spec_datasets/msg/labels.tsv"
BUILDER = MSPRED / "data_scripts/create_msg_simulation_dataset.py"

RULE_SHA256_AT_FREEZE = "c5ab93af9bbddff93a957676a77e93275130295c59707726427c33bfdd9a671b"
RULE_FROZEN_UTC = "2026-09-15T03:18:59Z"

LADDER = (15.0, 20.0, 30.0, 45.0, 60.0, 75.0)
V1_SUBLIBS = ("MCEBIO", "MCESCAF", "NIHNP", "OTAVAPEP")
CATS = ["CAT1_RAW_NCE", "CAT2_NCE_x_mz_over_500", "CAT3_OTHER_CONVERSION", "CAT4_UNKNOWN_AMBIGUOUS",
        "NATIVE_EV_NOT_NCE"]
CAT_COL = {"CAT1_RAW_NCE": "raw_nce", "CAT2_NCE_x_mz_over_500": "nce_times_mz_over_500",
           "CAT3_OTHER_CONVERSION": "other_conversion", "CAT4_UNKNOWN_AMBIGUOUS": "unknown_ambiguous",
           "NATIVE_EV_NOT_NCE": "native_ev_not_nce"}
BASIS = {"CAT1_RAW_NCE": "code_provenance", "CAT2_NCE_x_mz_over_500": "numeric_test",
         "CAT3_OTHER_CONVERSION": "numeric_test", "CAT4_UNKNOWN_AMBIGUOUS": "unresolved",
         "NATIVE_EV_NOT_NCE": "instrument_semantics"}
SPLIT_ROLE = {"train": "gradient_updates", "val": "early_stopping_and_best_checkpoint_selection",
              "test": "not_used_for_fitting", "all": "all_splits"}
CHECKPOINTS = ["iceberg21_msg_simulation_gen", "iceberg21_msg_simulation_inten_contr", "glacier_msg"]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_functions(path: Path, names: list[str]) -> dict:
    """Execute the named top-level functions of an ms-pred script verbatim, without running the script."""
    src = path.read_text()
    tree = ast.parse(src)
    ns: dict = {"pd": pd, "ast": ast, "re": re, "__builtins__": __builtins__}
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            seg = ast.get_source_segment(src, node)
            exec(compile("from __future__ import annotations\n" + seg, str(path), "exec"), ns)
            found[node.name] = {"lineno": node.lineno, "end_lineno": node.end_lineno}
    missing = set(names) - set(found)
    assert not missing, missing
    return ns, found


def repr_decimals(x: float) -> int:
    s = repr(float(x))
    if "e" in s or "E" in s:
        mant, exp = s.lower().split("e")
        dec = len(mant.split(".")[1]) if "." in mant else 0
        return max(0, dec - int(exp))
    return len(s.split(".")[1]) if "." in s and s.split(".")[1] != "0" else 0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = {p.name if p != LABELS else "mspred_msg_labels.tsv": {"path": str(p), "sha256": sha256(p)}
              for p in [IDENTITY, METADATA, MEMBERSHIP, P3_ATTR, T1, LABELS, BUILDER]}
    rule_sha_now = sha256(RULE_NOTE)

    # ------------------------------------------------------------------ load and join MSG 1.5
    ident = pd.read_parquet(IDENTITY)
    meta = pd.read_parquet(METADATA, columns=["identifier", "precursor_mz"])
    memb = pd.read_parquet(MEMBERSHIP, columns=["identifier", "in_msnlib_v1_compound", "msnlib_v1_sublibraries",
                                               "precursor_mz_decimals", "msnlib_like_row_signature"])
    df = ident.merge(meta, on="identifier", how="inner", validate="one_to_one")
    df = df.merge(memb, on="identifier", how="left", validate="one_to_one")
    assert len(df) == len(ident) == 231104
    df["identifier_num"] = df.identifier.str[len("MassSpecGymID"):].astype(int)
    df = df.sort_values("identifier_num").reset_index(drop=True)
    assert df.identifier_num.is_unique and df.identifier_num.is_monotonic_increasing
    df["in_msnlib_v1_compound"] = df["in_msnlib_v1_compound"].fillna(False).astype(bool)
    df["msnlib_like_row_signature"] = df["msnlib_like_row_signature"].fillna(False).astype(bool)

    # ------------------------------------------------------------------ full MSG 1.5 -> T_sim reconciliation
    ce = df.collision_energy
    not_sim_reason = np.select(
        [ce.isna() & df.instrument_type.isna(), ce.isna(), df.instrument_type.isna(), df.adduct != "[M+H]+"],
        ["ce_missing_and_instrument_missing", "ce_missing", "instrument_missing", "adduct_not_MH"], "in_sim")
    derived_sim = not_sim_reason == "in_sim"
    assert (derived_sim == df.simulation_challenge.to_numpy()).all(), "nb6 cell 5 rule not reproduced"
    full_recon = {
        "msg15_rows": int(len(df)),
        "simulation_challenge_rows": int(derived_sim.sum()),
        "non_simulation_rows_by_first_failing_reason": {k: int(v) for k, v in
                                                        pd.Series(not_sim_reason).value_counts().items()
                                                        if k != "in_sim"},
        "rule": "MassSpecGym nb6 cell 5: simulation_challenge = no NaN in any column and adduct == [M+H]+",
    }

    # ------------------------------------------------------------------ source blocks (P3 criteria, reimplemented)
    df["ce_missing"] = ce.isna()
    df["orbi_ladder"] = (df.instrument_type == "Orbitrap") & ce.isin(LADDER)
    df["run"] = (df.inchikey != df.inchikey.shift()).cumsum()
    df["pos"] = df.groupby("run").cumcount()
    runs = df.groupby("run").agg(first_id=("identifier_num", "min"), all_missing=("ce_missing", "all"))
    runs["first_ladder"] = df[df.pos == 0].set_index("run").orbi_ladder.astype(bool)
    suffix_all_missing = runs.all_missing[::-1].cumprod()[::-1].astype(bool)
    c_start = int(runs.loc[runs.index[suffix_all_missing].min(), "first_id"])
    pre = runs[runs.first_id < c_start]
    exc = (~pre.first_ladder)[::-1].cumsum()[::-1]
    cnt = pd.Series(np.arange(len(pre), 0, -1), index=pre.index)
    b_start_run = (exc / cnt)[(exc / cnt) <= 0.005].index.min()
    b_start = int(runs.loc[b_start_run, "first_id"])
    assert (b_start, c_start) == (202862, 239029), (b_start, c_start)
    run_first = df.run.map(runs.first_id)
    df["block"] = np.where(run_first >= c_start, "C", np.where(run_first >= b_start, "B", "A"))

    label = np.full(len(df), "MassBank_or_MoNA", dtype=object)
    label[(df.block == "C").to_numpy()] = "GNPS"
    isB = (df.block == "B").to_numpy()
    miss = df.ce_missing.to_numpy()
    label[isB & ~miss] = "MSnLib_v1"
    label[isB & miss] = "GNPS"
    ladder = df.orbi_ladder.to_numpy()
    member = df.in_msnlib_v1_compound.to_numpy()
    a_idx = df.index[df.block == "A"].to_numpy()
    bounds = np.flatnonzero(np.diff(df.run.to_numpy()[a_idx])) + 1
    for seg in np.split(a_idx, bounds):
        k = len(seg) - 1
        while k >= 0 and miss[seg[k]]:
            label[seg[k]] = "GNPS_or_MoNA_missing_ce"
            k -= 1
        while k >= 0 and ladder[seg[k]] and member[seg[k]]:
            label[seg[k]] = "MSnLib_v1_probable"
            k -= 1
    df["p3_label"] = label
    p3 = pd.read_parquet(P3_ATTR, columns=["identifier", "source_label", "block"])
    chk = df[["identifier", "p3_label"]].merge(p3, on="identifier", validate="one_to_one")
    assert (chk.p3_label == chk.source_label).all(), "P3 labels not reproduced"

    def src_name(row_label: str, subl) -> str:
        if row_label in ("MSnLib_v1", "MSnLib_v1_probable"):
            base = "MSnLib_v1.0" if row_label == "MSnLib_v1" else "MSnLib_v1.0_probable"
            parts = [s for s in str(subl or "").split(";") if s]
            if len(parts) == 1:
                return f"{base}:{parts[0]}"
            if len(parts) > 1:
                return f"{base}:multiple({';'.join(parts)})"
            return f"{base}:unmatched"
        if row_label in ("GNPS", "GNPS_or_MoNA_missing_ce"):
            return "GNPS_or_missing_ce"
        return "MassBank_or_MoNA"

    df["source_library"] = [src_name(l, s) for l, s in zip(df.p3_label, df.msnlib_v1_sublibraries)]

    # ------------------------------------------------------------------ T_sim and ms-pred builder, verbatim functions
    ns, fn_lines = extract_functions(BUILDER, ["truthy", "format_collision_energy", "normalize_fold",
                                               "collision_key", "iter_label_collision_pairs",
                                               "parse_subformula_key"])
    sim = df[ns["truthy"](df.simulation_challenge)].copy()
    sim["collision_energies"] = sim.collision_energy.map(ns["format_collision_energy"])
    n_before = len(sim)
    sim = sim.dropna(subset=["collision_energies"])
    sim = sim[~sim["collision_energies"].astype(str).str.contains(r"\[imputed\]", regex=True)]
    assert len(sim) == n_before == 119029
    sim["split"] = sim.fold.map(ns["normalize_fold"])
    sim["spec"] = sim.identifier.astype(str)
    assert sim.spec.is_unique

    labels = pd.read_csv(LABELS, sep="\t")
    lab = labels.set_index("spec")
    assert set(lab.index) == set(sim.spec) and len(lab) == len(sim)
    s_ix = sim.set_index("spec")
    assert (lab.loc[s_ix.index, "instrument"].to_numpy() == s_ix.instrument_type.to_numpy()).all()
    assert (lab.loc[s_ix.index, "precursor"].to_numpy() == s_ix.precursor_mz.to_numpy()).all()
    lab_ce = lab.loc[s_ix.index, "collision_energies"].map(lambda x: float(ast.literal_eval(x)[0]))
    assert (lab_ce.to_numpy() == np.floor(s_ix.collision_energy.to_numpy())).all()
    committed_labels_check = {"spec_set_equal": True, "instrument_equal": True, "precursor_exact_equal": True,
                              "ce_equals_floor_msg15_ce": True, "rows": int(len(lab))}

    # inten_contr filter (verbatim label pair construction and subformula key parser)
    label_pairs = ns["iter_label_collision_pairs"](sim[["spec", "collision_energies"]])
    ce_arr = sim.collision_energy.to_numpy()
    floor_keys = [ns["parse_subformula_key"](f"{s}_collision {int(math.floor(c))}.json")
                  for s, c in zip(sim.spec, ce_arr)]
    sim["inten_kept_floor_base"] = [k in label_pairs for k in floor_keys]
    round_keys = [ns["parse_subformula_key"](f"{s}_collision {float(f'{float(c):.0f}'):.0f}.json")
                  for s, c in zip(sim.spec, ce_arr)]
    sim["inten_kept_round_base"] = [k in label_pairs for k in round_keys]
    sim["label_key"] = [float(ns["collision_key"](ast.literal_eval(x)[0])) for x in sim.collision_energies]
    kept = sim.inten_kept_floor_base.to_numpy()
    assert (sim.label_key.to_numpy()[kept] == np.floor(ce_arr[kept])).all()

    # ------------------------------------------------------------------ numeric tests
    mz = sim.precursor_mz.to_numpy()
    orbi = (sim.instrument_type == "Orbitrap").to_numpy()
    qtof = (sim.instrument_type == "QTOF").to_numpy()
    assert (orbi | qtof).all(), "instrument missing rows in T_sim"
    is_int = ce_arr == np.floor(ce_arr)
    dec = np.array([min(repr_decimals(c), 12) for c in ce_arr])
    tol = np.maximum(0.5 * 10.0 ** (-dec), 1e-9 * ce_arr)
    r = ce_arr * 500.0 / mz
    n_near = np.round(r)
    t500 = (n_near >= 1) & (np.abs(ce_arr - n_near * mz / 500.0) <= tol)
    chance_t500 = np.minimum(1.0, 2.0 * tol * 500.0 / mz)
    half = (~is_int) & (ce_arr * 2 == np.floor(ce_arr * 2))
    r2 = np.round(r, 2)
    frac_close = (~is_int) & (~t500) & (np.abs(ce_arr - r2 * mz / 500.0) <= tol) & (r2 != np.round(r2))
    sim["r2"] = np.where(frac_close, r2, np.nan)
    grp = sim[frac_close & orbi].groupby("r2").precursor_mz.nunique()
    shared = set(grp[grp >= 2].index)
    t500_frac = frac_close & sim.r2.isin(shared).to_numpy()
    sim["is_int"], sim["decimals"], sim["t500"], sim["n_nce"] = is_int, dec, t500, n_near
    sim["t500_frac"], sim["half"] = t500_frac, half
    sim["t500_chance_p"] = chance_t500

    # ------------------------------------------------------------------ categories (first match wins)
    lab_s = sim.p3_label.to_numpy()
    msn_order = lab_s == "MSnLib_v1"
    msn_prob = lab_s == "MSnLib_v1_probable"
    in_ladder = sim.collision_energy.isin(LADDER).to_numpy()
    cat = np.full(len(sim), "", dtype=object)
    sub = np.full(len(sim), "", dtype=object)

    def assign(mask, c, s):
        m = mask & (cat == "")
        cat[m] = c
        sub[m] = s

    q_sub = np.where(is_int, "qtof_integer", np.where(half, "qtof_half_integer", "qtof_other_fractional"))
    for s_ in ["qtof_integer", "qtof_half_integer", "qtof_other_fractional"]:
        assign(qtof & (q_sub == s_), "NATIVE_EV_NOT_NCE", s_)
    assign(orbi & ~is_int & t500, "CAT2_NCE_x_mz_over_500", "nonint_T500_pass")
    assign(orbi & msn_order & is_int & in_ladder, "CAT1_RAW_NCE", "msnlib_order_integer_ladder")
    assign(orbi & ~is_int & ~t500 & t500_frac, "CAT3_OTHER_CONVERSION", "pct_conversion_of_noninteger_nce")
    assign(orbi & msn_order, "CAT4_UNKNOWN_AMBIGUOUS", "msnlib_order_nonladder_or_anomalous")
    assign(orbi & msn_prob & is_int & in_ladder, "CAT4_UNKNOWN_AMBIGUOUS", "msnlib_probable_integer_ladder")
    assign(orbi & msn_prob, "CAT4_UNKNOWN_AMBIGUOUS", "msnlib_probable_other")
    assign(orbi & is_int & (ce_arr == 0), "CAT4_UNKNOWN_AMBIGUOUS", "mbmona_integer_ce0")
    assign(orbi & is_int & (ce_arr % 5 == 0), "CAT4_UNKNOWN_AMBIGUOUS", "mbmona_integer_mult5")
    assign(orbi & is_int, "CAT4_UNKNOWN_AMBIGUOUS", "mbmona_integer_other")
    assign(orbi & half, "CAT4_UNKNOWN_AMBIGUOUS", "mbmona_half_integer")
    assign(orbi, "CAT4_UNKNOWN_AMBIGUOUS", "mbmona_nonint_not_mz_proportional")
    assert (cat != "").all()
    sim["category"], sim["subreason"] = cat, sub
    sim["resolution_basis"] = sim.category.map(BASIS)
    sim["instrument"] = sim.instrument_type
    sim["flag_qtof_t500_pass"] = qtof & ~is_int & t500
    sim["flag_qtof_in_block_B"] = qtof & (sim.block.to_numpy() == "B")
    sim["flag_msnlib_signature_unlabelled"] = (sim.msnlib_like_row_signature.to_numpy() & (lab_s == "MassBank_or_MoNA"))

    # ------------------------------------------------------------------ post-hoc diagnostics (added after the first
    # run; they do not change any category): is the MSnLib fixed energy 20 present in a probable sub-run, and what CE
    # values carry P5's signature without the probable label (MassBank Eawag-style HCD ladders have no 20).
    prob = sim[sim.p3_label == "MSnLib_v1_probable"]
    run_has20 = prob.groupby("run").collision_energy.apply(lambda s: bool((s == 20.0).any()))
    run_has20_60 = prob.groupby("run").collision_energy.apply(lambda s: bool((s == 20.0).any() and (s == 60.0).any()))
    post_hoc = {
        "msnlib_probable_rows_T_sim": int(len(prob)),
        "msnlib_probable_rows_in_subrun_with_ce20": int(prob.run.map(run_has20).sum()),
        "msnlib_probable_rows_in_subrun_with_ce20_and_ce60": int(prob.run.map(run_has20_60).sum()),
        "msnlib_probable_ce_values": {str(k): int(v) for k, v in prob.collision_energy.value_counts().items()},
        "msnlib_probable_rows_by_identifier_region": {str(k): int(v) for k, v in pd.cut(
            prob.identifier_num, [0, 184000, 203000, 10 ** 6], right=False,
            labels=["<184000", "184000-202999", ">=203000"]).value_counts().items()},
        "signature_unlabelled_ce_values": {str(k): int(v) for k, v in
                                           sim[sim.flag_msnlib_signature_unlabelled].collision_energy.value_counts().items()},
        "signature_unlabelled_in_msnlib_v1_compound": int(
            (sim.flag_msnlib_signature_unlabelled & sim.in_msnlib_v1_compound).sum()),
        "msnlib_order_ce_values": {str(k): int(v) for k, v in
                                   sim[sim.p3_label == "MSnLib_v1"].collision_energy.value_counts().items()},
    }

    # ------------------------------------------------------------------ per-checkpoint tables
    def ckpt_frame(ck: str) -> pd.DataFrame:
        f = sim.copy()
        f["checkpoint"] = ck
        f["status"] = "retained"
        if ck == "iceberg21_msg_simulation_inten_contr":
            f.loc[~f.inten_kept_floor_base, "status"] = "excluded_ce_key_filter"
        f["value_floor"] = np.floor(f.collision_energy).astype(np.float32)
        f["value_raw"] = f.collision_energy.astype(np.float32)
        return f

    frames = {ck: ckpt_frame(ck) for ck in CHECKPOINTS}
    allf = pd.concat(frames.values(), ignore_index=True)
    rounding = {"iceberg21_msg_simulation_gen": "floor (INFERRED int-truncated spectrum-header CE keys)",
                "iceberg21_msg_simulation_inten_contr": "round-half-even of the :g label; equals floor on retained rows",
                "glacier_msg": "UNRESOLVED; primary H_floor floor, sensitivity H_raw unrounded float32"}

    # long table (subreason granularity)
    long_rows = []
    for split in ["train", "val", "test", "all"]:
        g = allf if split == "all" else allf[allf.split == split]
        t = g.groupby(["checkpoint", "source_library", "instrument", "category", "subreason", "resolution_basis",
                       "status"]).size().reset_index(name="n_rows")
        t.insert(1, "split_scope", split)
        t.insert(2, "split_role", SPLIT_ROLE[split])
        long_rows.append(t)
    long_df = pd.concat(long_rows, ignore_index=True)
    long_df.to_csv(OUT / "ce_convention_counts_long.csv", index=False)

    # wide table matching the per_checkpoint_counts schema, with margins
    wide_rows = []
    for ck in CHECKPOINTS:
        f = frames[ck]
        for split in ["train", "val", "test", "all"]:
            g0 = f if split == "all" else f[f.split == split]
            for srcv in ["ALL"] + sorted(f.source_library.unique()):
                g1 = g0 if srcv == "ALL" else g0[g0.source_library == srcv]
                for inst in ["ALL", "Orbitrap", "QTOF"]:
                    g = g1 if inst == "ALL" else g1[g1.instrument == inst]
                    if len(g) == 0:
                        continue
                    ret = g[g.status == "retained"]
                    row = {"checkpoint": ck, "split_scope": split, "split_role": SPLIT_ROLE[split],
                           "source_library": srcv, "instrument": inst}
                    for c in CATS:
                        row[CAT_COL[c]] = int((ret.category == c).sum())
                    row["excluded_or_missing"] = int((g.status != "retained").sum())
                    row["total_rows"] = int(len(g))
                    row["resolved_by_code_provenance"] = row["raw_nce"]
                    row["resolved_by_numeric_test"] = row["nce_times_mz_over_500"] + row["other_conversion"]
                    row["resolved_by_instrument_semantics"] = row["native_ev_not_nce"]
                    row["unresolved"] = row["unknown_ambiguous"]
                    row["s1_raw_nce_if_msnlib_probable_accepted"] = int(
                        row["raw_nce"] + ((ret.subreason == "msnlib_probable_integer_ladder")).sum())
                    row["presented_value_rounding"] = rounding[ck]
                    assert sum(row[CAT_COL[c]] for c in CATS) + row["excluded_or_missing"] == row["total_rows"]
                    wide_rows.append(row)
    wide = pd.DataFrame(wide_rows)
    wide.to_csv(OUT / "ce_convention_counts.csv", index=False)

    # ------------------------------------------------------------------ network value quantiles
    qs = [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0]
    qrows = []

    def qrow(base: dict, quantity: str, x: np.ndarray):
        x = np.asarray(x, dtype=float)
        x = x[~np.isnan(x)]
        if len(x) == 0:
            return
        qv = np.quantile(x, qs)
        d = dict(base, quantity=quantity, n=int(len(x)), n_distinct=int(len(np.unique(x))), mean=float(x.mean()))
        for q, v in zip(qs, qv):
            d[{0.0: "min", 1.0: "max"}.get(q, f"q{int(round(q * 100)):02d}")] = float(v)
        qrows.append(d)

    for ck in CHECKPOINTS:
        hyps = [("H_floor", "value_floor"), ("H_raw", "value_raw")] if ck == "glacier_msg" else [("as_trained", "value_floor")]
        f = frames[ck]
        f = f[f.status == "retained"]
        for hname, vcol in hyps:
            for split in ["train", "val", "test", "all"]:
                g0 = f if split == "all" else f[f.split == split]
                for inst in ["ALL", "Orbitrap", "QTOF"]:
                    g1 = g0 if inst == "ALL" else g0[g0.instrument == inst]
                    for c in ["ALL"] + CATS:
                        g = g1 if c == "ALL" else g1[g1.category == c]
                        if len(g) == 0:
                            continue
                        base = {"checkpoint": ck, "value_hypothesis": hname, "split_scope": split,
                                "instrument": inst, "category": c}
                        v = g[vcol].to_numpy(dtype=float)
                        m_ = g.precursor_mz.to_numpy()
                        qrow(base, "presented_value (eV if read as eV)", v)
                        qrow(base, "presented_value*mz/500 (eV if read as NCE)", v * m_ / 500.0)
                        qrow(base, "presented_value*500/mz (NCE if read as eV)", v * 500.0 / m_)
                        if c in ("CAT1_RAW_NCE",):
                            qrow(base, "source_NCE (MSnLib setting)", g.collision_energy.to_numpy())
                            qrow(base, "source_NCE*mz/500 (lab-frame eV equivalent)",
                                 g.collision_energy.to_numpy() * m_ / 500.0)
                        if c == "CAT2_NCE_x_mz_over_500":
                            qrow(base, "source_NCE (integer n)", g.n_nce.to_numpy())
                            qrow(base, "source_eV_unrounded (MSG value)", g.collision_energy.to_numpy())
                            qrow(base, "source_eV_minus_presented (rounding loss)",
                                 g.collision_energy.to_numpy() - v)
                        if c == "NATIVE_EV_NOT_NCE":
                            qrow(base, "source_eV_unrounded (MSG value)", g.collision_energy.to_numpy())
                        qrow(base, "precursor_mz", m_)
    qdf = pd.DataFrame(qrows)
    qdf.to_csv(OUT / "network_ce_value_quantiles.csv", index=False)

    # ------------------------------------------------------------------ step arithmetic bounds (P1 C14)
    t1 = {json.loads(l)["path"]: json.loads(l) for l in T1.read_text().splitlines() if l.strip()}

    def window_1gpu(steps):
        return [32 * (steps - 1) + 1, 32 * steps]

    def window_ddp2(steps):
        return [2 * (32 * (steps - 1) + 1) - 1, 2 * 32 * steps]

    tr = frames["iceberg21_msg_simulation_gen"]
    n_train = int((tr.split == "train").sum())
    n_inten_train = int(((frames["iceberg21_msg_simulation_inten_contr"].split == "train")
                         & (frames["iceberg21_msg_simulation_inten_contr"].status == "retained")).sum())
    step = {}
    for key, ck, mode, n_rows in [("/ckpt/iceberg21_msg_simulation/gen/best.ckpt", "gen", "1gpu", n_train),
                                  ("/ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt", "inten_contr", "ddp2",
                                   n_inten_train),
                                  ("/ckpt/glacier_msg/best.ckpt", "glacier", "1gpu", n_train)]:
        e = t1[key]
        spe = e["global_step"] / (e["epoch"] + 1)
        assert spe == int(spe)
        w = window_1gpu(int(spe)) if mode == "1gpu" else window_ddp2(int(spe))
        step[ck] = {"epoch": e["epoch"], "global_step": e["global_step"], "steps_per_epoch": int(spe),
                    "mode": mode, "implied_train_items_window": w, "row_identifiable_train_rows": n_rows,
                    "unallocated_loss_bound": [max(0, n_rows - w[1]), n_rows - w[0]]}

    # ------------------------------------------------------------------ JSON summary
    def tab(frame, by):
        return {" | ".join(map(str, k)) if isinstance(k, tuple) else str(k): int(v)
                for k, v in frame.groupby(by).size().items()}

    summary = {
        "script": "scripts/ce_interface_adjudication/03_classify_ce_conventions.py",
        "rule_note": {"path": str(RULE_NOTE.relative_to(ROOT)), "sha256_at_freeze": RULE_SHA256_AT_FREEZE,
                      "frozen_utc": RULE_FROZEN_UTC,
                      "note": "file later extended with Part 2 results; Part 1 text unchanged"},
        "inputs": inputs,
        "mspred_functions_executed_verbatim": {k: f"create_msg_simulation_dataset.py:{v['lineno']}-{v['end_lineno']}"
                                               for k, v in fn_lines.items()},
        "full_msg15_to_T_sim_reconciliation": full_recon,
        "block_boundaries": {"B_start": b_start, "C_start": c_start, "p3_labels_reproduced": True},
        "committed_msg_labels_check": committed_labels_check,
        "T_sim_rows_by_split": tab(sim, "split"),
        "imputed_rows": 0,
        "inten_contr_ce_key_filter": {
            "base_key_hypothesis_primary": "floor (int) of MSG CE",
            "dropped_by_split_floor_base": tab(sim[~sim.inten_kept_floor_base], "split"),
            "kept_by_split_floor_base": tab(sim[sim.inten_kept_floor_base], "split"),
            "dropped_by_split_S2_round_base": tab(sim[~sim.inten_kept_round_base], "split") or {"train": 0},
            "dropped_by_instrument_x_category_floor_base": tab(sim[~sim.inten_kept_floor_base],
                                                               ["instrument", "category"]),
        },
        "step_arithmetic": step,
        "category_counts_T_sim_all_splits": tab(sim, "category"),
        "category_x_subreason_T_sim_all_splits": tab(sim, ["category", "subreason"]),
        "category_x_subreason_x_instrument_x_split": tab(sim, ["category", "subreason", "instrument", "split"]),
        "source_label_x_category_T_sim": tab(sim, ["source_library", "category"]),
        "numeric_test_diagnostics": {
            "orbitrap_nonint_rows": int((orbi & ~is_int).sum()),
            "orbitrap_nonint_T500_pass": int((orbi & ~is_int & t500).sum()),
            "orbitrap_nonint_T500_expected_by_chance": float(chance_t500[orbi & ~is_int].sum()),
            "orbitrap_nonint_T500_pass_by_decimals": {str(k): int(v) for k, v in
                                                      pd.Series(dec[orbi & ~is_int & t500]).value_counts().sort_index().items()},
            "orbitrap_nonint_T500_fail": int((orbi & ~is_int & ~t500).sum()),
            "orbitrap_T500_frac_values": {str(k): int(v) for k, v in
                                          sim[orbi & t500_frac].r2.value_counts().items()},
            "cat2_n_nce_top": {str(int(k)): int(v) for k, v in
                               sim[sim.category == "CAT2_NCE_x_mz_over_500"].n_nce.value_counts().head(25).items()},
            "cat2_n_nce_multiple_of_5": int((sim[sim.category == "CAT2_NCE_x_mz_over_500"].n_nce % 5 == 0).sum()),
            "qtof_nonint_rows": int((qtof & ~is_int).sum()),
            "qtof_nonint_T500_pass": int(sim.flag_qtof_t500_pass.sum()),
            "qtof_nonint_T500_expected_by_chance": float(chance_t500[qtof & ~is_int].sum()),
            "qtof_rows_in_block_B": int(sim.flag_qtof_in_block_B.sum()),
            "mbmona_rows_with_msnlib_like_signature_not_labelled_probable": int(sim.flag_msnlib_signature_unlabelled.sum()),
            "mbmona_signature_unlabelled_by_category_subreason": tab(sim[sim.flag_msnlib_signature_unlabelled],
                                                                    ["category", "subreason"]),
            "mbmona_integer_orbitrap_top_values": {str(k): int(v) for k, v in sim[
                sim.subreason.isin(["mbmona_integer_mult5", "mbmona_integer_other", "mbmona_integer_ce0"])
            ].collision_energy.value_counts().head(25).items()},
            "msnlib_order_nonladder_rows": sim[sim.subreason == "msnlib_order_nonladder_or_anomalous"][
                ["identifier", "instrument", "collision_energy"]].to_dict(orient="records"),
            "cat4_nonint_not_mz_proportional_values": {str(k): int(v) for k, v in sim[
                sim.subreason == "mbmona_nonint_not_mz_proportional"].collision_energy.value_counts().head(20).items()},
            "exact_vs_isclose_integer_disagreement_rows": int((np.isclose(ce_arr, np.round(ce_arr)) & ~is_int).sum()),
        },
        "post_hoc_diagnostics_not_used_for_categories": post_hoc,
        "wide_counts_top_level": wide[(wide.source_library == "ALL") & (wide.instrument == "ALL")].to_dict(orient="records"),
        "wide_counts_by_source_and_instrument": wide[(wide.source_library != "ALL") & (wide.instrument != "ALL")].to_dict(orient="records"),
        "outputs": {},
    }
    for p in ["ce_convention_counts.csv", "ce_convention_counts_long.csv", "network_ce_value_quantiles.csv"]:
        summary["outputs"][p] = {"path": str((OUT / p).relative_to(ROOT)), "sha256": sha256(OUT / p)}
    (OUT / "ce_convention_counts.json").write_text(json.dumps(summary, indent=1, default=str))

    pd.set_option("display.width", 250)
    print("rule sha now", rule_sha_now, "at freeze", RULE_SHA256_AT_FREEZE)
    print(json.dumps({k: summary[k] for k in ["full_msg15_to_T_sim_reconciliation", "block_boundaries",
                                              "T_sim_rows_by_split", "inten_contr_ce_key_filter", "step_arithmetic",
                                              "category_counts_T_sim_all_splits",
                                              "category_x_subreason_T_sim_all_splits",
                                              "numeric_test_diagnostics"]}, indent=1, default=str))
    top = wide[(wide.source_library == "ALL")]
    print(top[["checkpoint", "split_scope", "instrument", "raw_nce", "nce_times_mz_over_500", "other_conversion",
               "unknown_ambiguous", "native_ev_not_nce", "excluded_or_missing", "total_rows",
               "s1_raw_nce_if_msnlib_probable_accepted"]].to_string(index=False))
    t = wide[(wide.checkpoint == "iceberg21_msg_simulation_gen") & (wide.split_scope == "train") &
             (wide.instrument != "ALL") & (wide.source_library != "ALL")]
    print(t[["source_library", "instrument", "raw_nce", "nce_times_mz_over_500", "other_conversion",
             "unknown_ambiguous", "native_ev_not_nce", "total_rows"]].to_string(index=False))


if __name__ == "__main__":
    main()
