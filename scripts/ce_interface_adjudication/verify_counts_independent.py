#!/usr/bin/env python3
"""
Task V (v_counts): independent count reproduction for the MURU collision-energy
interface adjudication.

Written from scratch against Part 1 of
artifacts/ce_interface_adjudication/notes/q_counts.md (the predeclared
classification rule). It does NOT import or exec
scripts/ce_interface_adjudication/03_classify_ce_conventions.py, and it does not
read that script's source while classifying; it only reads its OUTPUT tables at
the end, to diff counts.

Inputs (all identity / training metadata, no model output, no benchmark result):
  artifacts/comparator_feasibility/massspecgym15_identity.parquet
  artifacts/ce_interface_adjudication/massspecgym15_metadata_columns.parquet
  artifacts/ce_interface_adjudication/p3_msg15_row_source_attribution.parquet   (labels compared, not used)
  artifacts/ce_interface_adjudication/exclusion/msg_row_msnlib_membership.parquet (compound membership)
  /Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv
  artifacts/ce_interface_adjudication/counts/ce_convention_counts{.csv,_long.csv}  (diff target)

Outputs:
  artifacts/ce_interface_adjudication/counts/v_independent_counts.csv
  artifacts/ce_interface_adjudication/counts/v_independent_counts.json
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ART = WT / "artifacts/ce_interface_adjudication"
COUNTS = ART / "counts"
MSPRED = Path("/Users/aryav/muru-comparators/repos/ms-pred")

LADDER = {15.0, 20.0, 30.0, 45.0, 60.0, 75.0}
SUBLIBS = ("MCEBIO", "MCESCAF", "NIHNP", "OTAVAPEP")

report: dict = {"checks": {}, "counts": {}, "diffs": {}, "notes": []}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def check(name: str, ok: bool, detail=None) -> None:
    report["checks"][name] = {"pass": bool(ok), "detail": detail}
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail is not None else ""))


# ---------------------------------------------------------------- load inputs
ident_p = WT / "artifacts/comparator_feasibility/massspecgym15_identity.parquet"
meta_p = ART / "massspecgym15_metadata_columns.parquet"
p3_p = ART / "p3_msg15_row_source_attribution.parquet"
p5_p = ART / "exclusion/msg_row_msnlib_membership.parquet"
labels_p = MSPRED / "data/spec_datasets/msg/labels.tsv"

report["inputs"] = {str(p.relative_to(WT)) if str(p).startswith(str(WT)) else str(p):
                    {"sha256": sha256(p), "bytes": p.stat().st_size}
                    for p in (ident_p, meta_p, p3_p, p5_p, labels_p)}

ident = pd.read_parquet(ident_p)
meta = pd.read_parquet(meta_p, columns=["identifier", "precursor_mz"])
df = ident.merge(meta, on="identifier", how="inner", validate="1:1")
check("join_identity_metadata_231104", len(df) == 231104 == len(ident) == len(meta), len(df))

df["idnum"] = df["identifier"].str.extract(r"(\d+)$").astype(np.int64)
df = df.sort_values("idnum", kind="mergesort").reset_index(drop=True)
check("identifiers_unique_and_monotonic",
      df["idnum"].is_unique and df["idnum"].is_monotonic_increasing,
      {"min": int(df["idnum"].min()), "max": int(df["idnum"].max())})

ce = df["collision_energy"].to_numpy(dtype=float)
mz = df["precursor_mz"].to_numpy(dtype=float)
instr = df["instrument_type"].astype("object").where(df["instrument_type"].notna(), None).to_numpy()
ce_present = ~np.isnan(ce)

# simulation_challenge, independently re-derived (MassSpecGym nb6 cell 5 rule:
# no NaN in any column, adduct [M+H]+)
sim_flag = df["simulation_challenge"].to_numpy(dtype=bool)
sim_rule = ce_present & df["instrument_type"].notna().to_numpy() & (df["adduct"].to_numpy() == "[M+H]+")
check("simulation_challenge_rule_reproduced", bool((sim_rule == sim_flag).all()),
      {"flag_true": int(sim_flag.sum()), "rule_true": int(sim_rule.sum()),
       "disagree": int((sim_rule != sim_flag).sum())})

# ------------------------------------------------ blocks from scratch (rule 1.1)
key = df["inchikey"].to_numpy()
new_run = np.empty(len(df), dtype=bool)
new_run[0] = True
new_run[1:] = key[1:] != key[:-1]
run_id = np.cumsum(new_run) - 1
run_start_idx = np.flatnonzero(new_run)
run_start_idnum = df["idnum"].to_numpy()[run_start_idx]
n_runs = len(run_start_idx)

first_ce_present = ce_present[run_start_idx]
# C_start: first run start after which EVERY row has missing CE.
last_ce_row = np.flatnonzero(ce_present)[-1]
last_ce_run = run_id[last_ce_row]
c_run = last_ce_run + 1
C_start = int(run_start_idnum[c_run])

# B_start: earliest run start before C_start such that <= 0.5% of run first rows
# from it up to C_start are not (Orbitrap and CE in ladder).
first_orb = np.array([instr[i] == "Orbitrap" for i in run_start_idx])
first_ladder = np.array([ce_present[i] and (ce[i] in LADDER) for i in run_start_idx])
good = first_orb & first_ladder  # per run-start, "is an Orbitrap ladder first row"
# suffix counts over runs [r, c_run)
bad = (~good[:c_run]).astype(np.int64)
suffix_bad = np.concatenate([np.cumsum(bad[::-1])[::-1], [0]])
total_runs_from = np.arange(c_run, -1, -1)[::-1]  # runs from r to c_run-1 = c_run - r
cands = []
for r in range(c_run):
    n = c_run - r
    if suffix_bad[r] <= 0.005 * n:
        cands.append(r)
        break
B_run = cands[0]
B_start = int(run_start_idnum[B_run])
check("block_boundaries_B202862_C239029", (B_start, C_start) == (202862, 239029),
      {"B_start": B_start, "C_start": C_start, "n_runs": int(n_runs)})

idnum = df["idnum"].to_numpy()
run_first_idnum = run_start_idnum[run_id]
block = np.where(run_first_idnum >= C_start, "C",
                 np.where(run_first_idnum >= B_start, "B", "A"))

# ------------------------------------------- P5 compound membership (naming only)
p5 = pd.read_parquet(p5_p, columns=["identifier", "in_msnlib_v1_compound", "msnlib_v1_sublibraries"])
p5 = df[["identifier"]].merge(p5, on="identifier", how="left", validate="1:1")
in_msnlib_cmpd = p5["in_msnlib_v1_compound"].fillna(False).to_numpy(dtype=bool)
sublibs = p5["msnlib_v1_sublibraries"].fillna("").to_numpy()

# --------------------------------------------- source labels (rule 1.1)
is_orb = np.array([x == "Orbitrap" for x in instr])
is_ladder = np.array([bool(p) and (v in LADDER) for p, v in zip(ce_present, ce)])

src = np.full(len(df), "GNPS", dtype=object)
src[(block == "B") & ce_present] = "MSnLib_v1.0"
src[(block == "A") & ce_present] = "MassBank_or_MoNA"
# probable heuristic: block A trailing rows (before trailing CE-missing rows)
# that are Orbitrap ladder rows of an MSnLib v1.0 compound.
probable = np.zeros(len(df), dtype=bool)
order = np.arange(len(df))
for r in range(n_runs):
    lo = run_start_idx[r]
    hi = run_start_idx[r + 1] if r + 1 < n_runs else len(df)
    if run_first_idnum[lo] >= B_start:
        continue  # block B or C
    if not in_msnlib_cmpd[lo]:
        continue
    j = hi - 1
    while j >= lo and not ce_present[j]:
        j -= 1  # skip trailing CE-missing rows
    k = j
    while k >= lo and is_orb[k] and is_ladder[k]:
        k -= 1
    if k < j:
        probable[k + 1: j + 1] = True
src[probable] = "MSnLib_v1.0_probable"

lab_counts = Counter(src.tolist())
report["counts"]["source_label_all_msg"] = dict(lab_counts)

# compare with P3 (data comparison, not an import)
p3 = pd.read_parquet(p3_p, columns=["identifier", "source_label", "block"])
p3 = df[["identifier"]].merge(p3, on="identifier", how="left", validate="1:1")
p3_lab = p3["source_label"].to_numpy()
mine_as_p3 = np.where(src == "MSnLib_v1.0", "MSnLib_v1",
                      np.where(src == "MSnLib_v1.0_probable", "MSnLib_v1_probable",
                               np.where(src == "GNPS",
                                        np.where(block == "C", "GNPS", "GNPS_or_MoNA_missing_ce"),
                                        src)))
agree = (mine_as_p3 == p3_lab)
check("p3_row_labels_reproduced_on_CE_present_rows", bool(agree[ce_present].all()),
      {"ce_present_rows": int(ce_present.sum()),
       "disagree_rows": int((~agree[ce_present]).sum())})
check("p3_labels_of_CE_missing_rows_match_rule_prose", bool(agree[~ce_present].all()),
      {"ce_missing_rows": int((~ce_present).sum()),
       "disagree_rows": int((~agree[~ce_present]).sum()),
       "by_pair_p3_vs_v": {f"{a}|{b}": int(n) for (a, b), n in
                           Counter(zip(p3_lab[~agree].tolist(), mine_as_p3[~agree].tolist())).items()},
       "rows_in_T_sim": int((~agree & sim_flag).sum())})
check("p3_disagreements_never_touch_T_sim", int((~agree & sim_flag).sum()) == 0,
      int((~agree & sim_flag).sum()))

# ------------------------------------------------------- T_sim + labels.tsv
T = sim_flag
n_T = int(T.sum())
labels = pd.read_csv(labels_p, sep="\t")
lab_specs = set(labels["spec"].astype(str))
T_specs = set(df.loc[T, "identifier"].astype(str))
check("T_sim_equals_labels_tsv_spec_set",
      lab_specs == T_specs, {"T_sim": n_T, "labels_rows": len(labels),
                             "labels_minus_T": len(lab_specs - T_specs),
                             "T_minus_labels": len(T_specs - lab_specs)})

lj = labels.merge(df.loc[T, ["identifier", "instrument_type", "precursor_mz", "collision_energy"]],
                  left_on=labels["spec"].astype(str), right_on="identifier", how="inner")
lab_ce = lj["collision_energies"].astype(str).str.strip("[]'").astype(float).to_numpy()
check("labels_ce_equals_floor_msg_ce",
      bool((lab_ce == np.floor(lj["collision_energy"].to_numpy())).all()),
      {"rows": len(lj),
       "equal_floor": int((lab_ce == np.floor(lj["collision_energy"].to_numpy())).sum())})
check("labels_instrument_and_precursor_match",
      bool((lj["instrument"].to_numpy() == lj["instrument_type"].to_numpy()).all()
           and (lj["precursor"].to_numpy() == lj["precursor_mz"].to_numpy()).all()),
      {"instr_mismatch": int((lj["instrument"].to_numpy() != lj["instrument_type"].to_numpy()).sum()),
       "prec_mismatch": int((lj["precursor"].to_numpy() != lj["precursor_mz"].to_numpy()).sum())})


# ------------------------------------------------ ms-pred label/key functions
def format_collision_energy(value):
    """Reimplementation of create_msg_simulation_dataset.py:67-80."""
    try:
        val = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(val):
        return None
    label = str(int(val)) if val.is_integer() else f"{val:g}"
    if "[imputed]" in label:
        return None
    return f"['{label}']"


def collision_key(value):
    """Reimplementation of create_msg_simulation_dataset.py:202-206."""
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return None


ce_T = ce[T]
mz_T = mz[T]
instr_T = instr[T]
src_T = src[T]
sub_T = sublibs[T]
memb_T = in_msnlib_cmpd[T]
block_T = block[T]
id_T = idnum[T]
fold_T = df.loc[T, "fold"].to_numpy()


def normalize_fold(v):
    s = str(v).strip().lower()
    if s == "train":
        return "train"
    if s in {"val", "valid", "validation"}:
        return "val"
    return "test"


split_T = np.array([normalize_fold(v) for v in fold_T])
check("split_sizes_99341_9734_9954",
      dict(Counter(split_T.tolist())) == {"train": 99341, "val": 9734, "test": 9954},
      dict(Counter(split_T.tolist())))

# format_collision_energy drops nothing on T_sim (imputed energies = 0 rows)
lab_str = [format_collision_energy(v) for v in ce_T]
check("format_collision_energy_drops_0_rows_on_T_sim",
      all(s is not None for s in lab_str) and not any("[imputed]" in str(s) for s in lab_str),
      {"none_count": sum(1 for s in lab_str if s is None)})


# ------------------------------------------------------- numeric tests (rule 1.2)
def decimals(x: float) -> int:
    s = repr(float(x))
    if "e" in s or "E" in s:
        return 12
    return min(len(s.split(".")[1].rstrip("0")) if "." in s else 0, 12)


is_int = ce_T == np.floor(ce_T)
d_arr = np.array([decimals(v) for v in ce_T])
tol = np.maximum(0.5 * 10.0 ** (-d_arr), 1e-9 * ce_T)
r_arr = ce_T * 500.0 / mz_T
n_arr = np.round(r_arr)
T500 = (n_arr >= 1) & (np.abs(ce_T - n_arr * mz_T / 500.0) <= tol)
chance_p = 2.0 * tol * 500.0 / mz_T

r2 = np.round(r_arr, 2)
frac_ok = np.abs(r_arr - r2) <= (tol * 500.0 / mz_T)
# "shared by at least 2 rows with different precursor_mz"
cand = (~is_int) & (~T500) & frac_ok
shared = defaultdict(set)
for v, m in zip(r2[cand], mz_T[cand]):
    shared[round(float(v), 2)].add(float(m))
T500_frac = np.array([bool(c and len(shared.get(round(float(v), 2), ())) >= 2)
                      for c, v in zip(cand, r2)])

is_orb_T = np.array([x == "Orbitrap" for x in instr_T])
is_qtof_T = np.array([x == "QTOF" for x in instr_T])
ladder_T = np.array([v in LADDER for v in ce_T])
half_T = (~is_int) & ((2 * ce_T) == np.floor(2 * ce_T))

# ------------------------------------------------------ categories (rule 1.3)
CAT = np.empty(len(ce_T), dtype=object)
SUB = np.empty(len(ce_T), dtype=object)
BASIS = np.empty(len(ce_T), dtype=object)
for i in range(len(ce_T)):
    if is_qtof_T[i]:
        CAT[i] = "NATIVE_EV_NOT_NCE"
        BASIS[i] = "instrument_semantics"
        SUB[i] = ("qtof_integer" if is_int[i] else
                  "qtof_half_integer" if half_T[i] else "qtof_other_fractional")
    elif is_orb_T[i] and (not is_int[i]) and T500[i]:
        CAT[i], SUB[i], BASIS[i] = "CAT2_NCE_x_mz_over_500", "nonint_T500_pass", "numeric_test"
    elif is_orb_T[i] and src_T[i] == "MSnLib_v1.0" and is_int[i] and ladder_T[i]:
        CAT[i], SUB[i], BASIS[i] = "CAT1_RAW_NCE", "msnlib_order_integer_ladder", "code_provenance"
    elif is_orb_T[i] and (not is_int[i]) and (not T500[i]) and T500_frac[i]:
        CAT[i], SUB[i], BASIS[i] = ("CAT3_OTHER_CONVERSION", "pct_conversion_of_noninteger_nce",
                                    "numeric_test")
    elif is_orb_T[i]:
        CAT[i], BASIS[i] = "CAT4_UNKNOWN_AMBIGUOUS", "unresolved"
        if src_T[i] == "MSnLib_v1.0":
            SUB[i] = "msnlib_order_nonladder_or_anomalous"
        elif src_T[i] == "MSnLib_v1.0_probable":
            SUB[i] = "msnlib_probable_integer_ladder"
        elif is_int[i] and ce_T[i] == 0.0:
            SUB[i] = "mbmona_integer_ce0"
        elif is_int[i] and (ce_T[i] % 5 == 0):
            SUB[i] = "mbmona_integer_mult5"
        elif is_int[i]:
            SUB[i] = "mbmona_integer_other"
        elif half_T[i]:
            SUB[i] = "mbmona_half_integer"
        else:
            SUB[i] = "mbmona_nonint_not_mz_proportional"
    else:
        CAT[i], SUB[i], BASIS[i] = "CAT4_UNKNOWN_AMBIGUOUS", "instrument_missing", "unresolved"

# ---------------------------------------------- inten_contr exclusion (rule 1.0)
label_key = np.array([collision_key(str(s.strip("[]'")).split()[0]) for s in lab_str])
base_key = np.array([f"{int(math.floor(v))}" for v in ce_T])
excluded = label_key != base_key
check("inten_contr_presented_value_equals_floor_on_retained",
      bool((label_key[~excluded].astype(float) == np.floor(ce_T[~excluded])).all()),
      {"retained": int((~excluded).sum())})

# ------------------------------------------------------------ aggregation
CATCOL = {"CAT1_RAW_NCE": "raw_nce", "CAT2_NCE_x_mz_over_500": "nce_times_mz_over_500",
          "CAT3_OTHER_CONVERSION": "other_conversion", "CAT4_UNKNOWN_AMBIGUOUS": "unknown_ambiguous",
          "NATIVE_EV_NOT_NCE": "native_ev_not_nce"}


def sublabel(i):
    s = src_T[i]
    if s in ("MSnLib_v1.0", "MSnLib_v1.0_probable"):
        raw = sub_T[i]
        parts = [p for p in str(raw).split(";") if p]
        if len(parts) == 1 and parts[0] in SUBLIBS:
            return f"{s}:{parts[0]}"
        if len(parts) > 1:
            return f"{s}:multiple({';'.join(parts)})"
        return f"{s}:unmatched"
    return s


srclabel = np.array([sublabel(i) for i in range(len(ce_T))], dtype=object)

base = pd.DataFrame({
    "split": split_T, "instrument": [x if x is not None else "MISSING" for x in instr_T],
    "source_library": srclabel, "category": CAT, "subreason": SUB, "basis": BASIS,
    "excluded": excluded,
    "s1_cat1": np.where((CAT == "CAT4_UNKNOWN_AMBIGUOUS") & (SUB == "msnlib_probable_integer_ladder"),
                        "CAT1_RAW_NCE", CAT),
})

rows = []
for ckpt in ("iceberg21_msg_simulation_gen", "iceberg21_msg_simulation_inten_contr", "glacier_msg"):
    b = base.copy()
    b["excl"] = b["excluded"] if ckpt.endswith("inten_contr") else False
    for split in ("train", "val", "test", "all"):
        s = b if split == "all" else b[b["split"] == split]
        for srcl in ["ALL"] + sorted(s["source_library"].unique()):
            ss = s if srcl == "ALL" else s[s["source_library"] == srcl]
            for inst in ["ALL"] + sorted(ss["instrument"].unique()):
                t = ss if inst == "ALL" else ss[ss["instrument"] == inst]
                if len(t) == 0:
                    continue
                kept = t[~t["excl"]]
                cc = kept["category"].value_counts()
                rows.append({
                    "checkpoint": ckpt, "split_scope": split, "source_library": srcl,
                    "instrument": inst,
                    "raw_nce": int(cc.get("CAT1_RAW_NCE", 0)),
                    "nce_times_mz_over_500": int(cc.get("CAT2_NCE_x_mz_over_500", 0)),
                    "other_conversion": int(cc.get("CAT3_OTHER_CONVERSION", 0)),
                    "unknown_ambiguous": int(cc.get("CAT4_UNKNOWN_AMBIGUOUS", 0)),
                    "native_ev_not_nce": int(cc.get("NATIVE_EV_NOT_NCE", 0)),
                    "excluded_or_missing": int(t["excl"].sum()),
                    "total_rows": int(len(t)),
                    "resolved_by_code_provenance": int((kept["basis"] == "code_provenance").sum()),
                    "resolved_by_numeric_test": int((kept["basis"] == "numeric_test").sum()),
                    "resolved_by_instrument_semantics": int((kept["basis"] == "instrument_semantics").sum()),
                    "unresolved": int((kept["basis"] == "unresolved").sum()),
                    "s1_raw_nce_if_msnlib_probable_accepted":
                        int((kept["s1_cat1"] == "CAT1_RAW_NCE").sum()),
                })
mine = pd.DataFrame(rows)
mine.to_csv(COUNTS / "v_independent_counts.csv", index=False)

# --------------------------------------------------- internal reconciliations
cat_cols = ["raw_nce", "nce_times_mz_over_500", "other_conversion", "unknown_ambiguous",
            "native_ev_not_nce", "excluded_or_missing"]
check("category_columns_sum_to_total_every_row",
      bool((mine[cat_cols].sum(axis=1) == mine["total_rows"]).all()),
      int((mine[cat_cols].sum(axis=1) != mine["total_rows"]).sum()))
res_cols = ["resolved_by_code_provenance", "resolved_by_numeric_test",
            "resolved_by_instrument_semantics", "unresolved"]
check("resolution_columns_sum_to_retained_every_row",
      bool((mine[res_cols].sum(axis=1) == mine["total_rows"] - mine["excluded_or_missing"]).all()),
      int((mine[res_cols].sum(axis=1) != mine["total_rows"] - mine["excluded_or_missing"]).sum()))
allrow = mine[(mine.checkpoint == "iceberg21_msg_simulation_gen") & (mine.split_scope == "all")
              & (mine.source_library == "ALL") & (mine.instrument == "ALL")].iloc[0]
check("T_sim_total_119029", int(allrow["total_rows"]) == 119029, int(allrow["total_rows"]))
sp = mine[(mine.checkpoint == "iceberg21_msg_simulation_gen") & (mine.source_library == "ALL")
          & (mine.instrument == "ALL")].set_index("split_scope")["total_rows"]
check("split_totals_sum_to_T_sim",
      int(sp["train"] + sp["val"] + sp["test"]) == int(sp["all"]) == 119029,
      {k: int(v) for k, v in sp.items()})

# ----------------------- audit A: compound membership not used as row provenance
cat1 = CAT == "CAT1_RAW_NCE"
cat1_nomemb = is_orb_T & (block_T == "B") & ce_present[T] & is_int & ladder_T
check("A1_cat1_independent_of_compound_membership",
      bool((cat1 == cat1_nomemb).all()),
      {"cat1": int(cat1.sum()), "cat1_block_rule_only": int(cat1_nomemb.sum()),
       "differ": int((cat1 != cat1_nomemb).sum())})
check("A2_cat1_rows_that_are_NOT_msnlib_compounds_still_counted",
      int((cat1 & ~memb_T).sum()) > 0,
      {"cat1_not_msnlib_compound": int((cat1 & ~memb_T).sum()),
       "cat1_msnlib_compound": int((cat1 & memb_T).sum())})
check("A3_msnlib_compound_rows_outside_block_B_never_cat1",
      int((memb_T & (block_T != "B") & cat1).sum()) == 0,
      {"msnlib_compound_rows_in_T_sim": int(memb_T.sum()),
       "of_which_block_B": int((memb_T & (block_T == "B")).sum()),
       "of_which_cat1": int((memb_T & cat1).sum())})
# membership is used by the probable heuristic only, and probable is CAT4 in the primary rule
prob_T = src_T == "MSnLib_v1.0_probable"
check("A4_probable_rows_all_CAT4_in_primary_rule",
      bool((CAT[prob_T] == "CAT4_UNKNOWN_AMBIGUOUS").all()),
      {"probable_rows": int(prob_T.sum()),
       "categories": dict(Counter(CAT[prob_T].tolist()))})
# sub-library naming only partitions; it never changes a category
sub_partition_ok = True
for ckpt in mine["checkpoint"].unique():
    m = mine[(mine.checkpoint == ckpt) & (mine.split_scope == "all") & (mine.instrument == "ALL")]
    tot = m[m.source_library == "ALL"][cat_cols].to_numpy()[0]
    parts = m[m.source_library != "ALL"][cat_cols].to_numpy().sum(axis=0)
    sub_partition_ok &= bool((tot == parts).all())
check("A5_source_library_partition_is_exact", sub_partition_ok)

# ---------------- audit B: ambiguous integer rows were not silently assigned
int_orb = is_orb_T & is_int
check("B1_integer_orbitrap_rows_only_in_CAT1_or_CAT4",
      set(Counter(CAT[int_orb].tolist())) <= {"CAT1_RAW_NCE", "CAT4_UNKNOWN_AMBIGUOUS"},
      dict(Counter(CAT[int_orb].tolist())))
int_orb_T500 = int_orb & T500
check("B2_integer_orbitrap_rows_passing_T500_not_assigned_CAT2",
      int((int_orb_T500 & (CAT == "CAT2_NCE_x_mz_over_500")).sum()) == 0,
      {"integer_orbitrap_passing_T500": int(int_orb_T500.sum()),
       "their_categories": dict(Counter(CAT[int_orb_T500].tolist()))})
check("B3_cat4_is_the_only_unresolved_basis",
      bool((BASIS[CAT == "CAT4_UNKNOWN_AMBIGUOUS"] == "unresolved").all()
           and (CAT[BASIS == "unresolved"] == "CAT4_UNKNOWN_AMBIGUOUS").all()))
check("B4_every_cat4_row_has_a_named_subreason",
      bool(all(isinstance(s, str) and s for s in SUB[CAT == "CAT4_UNKNOWN_AMBIGUOUS"])),
      dict(Counter(SUB[CAT == "CAT4_UNKNOWN_AMBIGUOUS"].tolist())))
mb_int = (src_T == "MassBank_or_MoNA") & is_orb_T & is_int
check("B5_mbmona_integer_orbitrap_all_CAT4",
      bool((CAT[mb_int] == "CAT4_UNKNOWN_AMBIGUOUS").all()),
      {"rows": int(mb_int.sum()), "cats": dict(Counter(CAT[mb_int].tolist()))})

report["counts"]["numeric_test_diagnostics"] = {
    "nonint_orbitrap_rows": int((is_orb_T & ~is_int).sum()),
    "nonint_orbitrap_T500_pass": int((is_orb_T & ~is_int & T500).sum()),
    "nonint_orbitrap_T500_expected_by_chance": float(chance_p[is_orb_T & ~is_int].sum()),
    "nonint_qtof_rows": int((is_qtof_T & ~is_int).sum()),
    "nonint_qtof_T500_pass": int((is_qtof_T & ~is_int & T500).sum()),
    "nonint_qtof_T500_expected_by_chance": float(chance_p[is_qtof_T & ~is_int].sum()),
    "implied_nce_multiple_of_5": int(((is_orb_T & ~is_int & T500) &
                                      (np.mod(n_arr, 5) == 0)).sum()),
    "implied_nce_top": dict(Counter(n_arr[is_orb_T & ~is_int & T500].astype(int).tolist()).most_common(10)),
    "integer_orbitrap_rows": int(int_orb.sum()),
    "integer_orbitrap_T500_pass_uninformative": int(int_orb_T500.sum()),
    "exact_vs_isclose_integer_disagreement":
        int((is_orb_T & ~is_int & np.isclose(ce_T, np.round(ce_T))).sum()),
}
report["counts"]["inten_contr_exclusions"] = {
    "total": int(excluded.sum()),
    "by_split": {k: int(v) for k, v in Counter(split_T[excluded].tolist()).items()},
    "by_category": {k: int(v) for k, v in Counter(CAT[excluded].tolist()).items()},
    "kept_train": int(((~excluded) & (split_T == "train")).sum()),
}
report["counts"]["subreason_all_splits"] = {
    f"{c}|{s}": int(n) for (c, s), n in
    Counter(zip(CAT.tolist(), SUB.tolist())).items()}

# ------------------------------------------------------------- diff vs Task Q
q = pd.read_csv(COUNTS / "ce_convention_counts.csv")
keys = ["checkpoint", "split_scope", "source_library", "instrument"]
cmp_cols = cat_cols + ["total_rows"] + res_cols + ["s1_raw_nce_if_msnlib_probable_accepted"]
mm = mine.merge(q, on=keys, how="outer", suffixes=("_v", "_q"), indicator=True)
only_v = mm[mm["_merge"] == "left_only"][keys].to_dict("records")
only_q = mm[mm["_merge"] == "right_only"][keys].to_dict("records")
both = mm[mm["_merge"] == "both"]
diffs = []
for c in cmp_cols:
    bad = both[both[f"{c}_v"].fillna(-1) != both[f"{c}_q"].fillna(-1)]
    for _, r in bad.iterrows():
        diffs.append({**{k: r[k] for k in keys}, "column": c,
                      "v": int(r[f"{c}_v"]), "q": int(r[f"{c}_q"]),
                      "delta": int(r[f"{c}_v"]) - int(r[f"{c}_q"])})
report["diffs"]["wide_table"] = {"rows_compared": int(len(both)),
                                 "cells_compared": int(len(both) * len(cmp_cols)),
                                 "cell_disagreements": len(diffs),
                                 "rows_only_in_v": only_v, "rows_only_in_q": only_q,
                                 "detail": diffs[:200]}
check("diff_vs_Q_wide_table_zero_disagreements",
      len(diffs) == 0 and not only_v and not only_q,
      {"cells": int(len(both) * len(cmp_cols)), "disagreements": len(diffs),
       "rows_only_in_v": len(only_v), "rows_only_in_q": len(only_q)})

# long table: subreason-level comparison (all splits, ALL margins are not in the long table,
# so compare the full subreason x status totals)
ql = pd.read_csv(COUNTS / "ce_convention_counts_long.csv")
qg = (ql[(ql.checkpoint == "iceberg21_msg_simulation_gen")]
      .groupby(["split_scope", "category", "subreason"])["n_rows"].sum())
vc = Counter(zip(split_T.tolist(), CAT.tolist(), SUB.tolist()))
for (sp, c, s), n in list(vc.items()):
    vc[("all", c, s)] += n
vg = pd.Series(vc).rename("n_rows")
vg.index = pd.MultiIndex.from_tuples(vg.index, names=["split_scope", "category", "subreason"])
cmp_long = pd.concat([vg.rename("v"), qg.rename("q")], axis=1).fillna(0).astype(int)
long_bad = cmp_long[cmp_long["v"] != cmp_long["q"]]
report["diffs"]["long_table_gen"] = {
    "groups": int(len(cmp_long)), "disagreements": int(len(long_bad)),
    "detail": long_bad.reset_index().to_dict("records")}
check("diff_vs_Q_long_table_gen_subreasons",
      len(long_bad) == 0, {"groups": int(len(cmp_long)), "disagreements": int(len(long_bad))})

# inten_contr excluded rows, by split / category / subreason
qe = (ql[(ql.checkpoint == "iceberg21_msg_simulation_inten_contr")
         & (ql.status == "excluded_ce_key_filter")]
      .groupby(["split_scope", "category", "subreason"])["n_rows"].sum())
ve = Counter(zip(split_T[excluded].tolist(), CAT[excluded].tolist(), SUB[excluded].tolist()))
for (sp, c, s), n in list(ve.items()):
    ve[("all", c, s)] += n
vse = pd.Series(ve).rename("n_rows")
vse.index = pd.MultiIndex.from_tuples(vse.index, names=["split_scope", "category", "subreason"])
cmp_e = pd.concat([vse.rename("v"), qe.rename("q")], axis=1).fillna(0).astype(int)
e_bad = cmp_e[cmp_e["v"] != cmp_e["q"]]
report["diffs"]["long_table_inten_contr_excluded"] = {
    "groups": int(len(cmp_e)), "disagreements": int(len(e_bad)),
    "detail": e_bad.reset_index().to_dict("records")}
check("diff_vs_Q_inten_contr_excluded_subreasons", len(e_bad) == 0,
      {"groups": int(len(cmp_e)), "disagreements": int(len(e_bad)),
       "excluded_total": int(excluded.sum())})


# ------------- conservatism diagnostics for the CAT1 / CAT4 boundary (not a rule change)
blockA_orb_int_ladder = int((is_orb_T & is_int & ladder_T & (block_T == "A")).sum())
report["counts"]["cat1_boundary_diagnostics"] = {
    "orbitrap_integer_ladder_rows_in_T_sim": int((is_orb_T & is_int & ladder_T).sum()),
    "of_which_block_B_(CAT1)": int(cat1.sum()),
    "of_which_block_A_(stay_CAT4)": blockA_orb_int_ladder,
    "block_A_ladder_rows_labelled_probable": int((probable[T] & is_orb_T & is_int & ladder_T).sum()),
    "block_A_ladder_rows_labelled_MassBank_or_MoNA":
        int(((src_T == "MassBank_or_MoNA") & is_orb_T & is_int & ladder_T).sum()),
    "block_B_rows_in_T_sim": int((block_T == "B").sum()),
    "block_B_orbitrap_nonladder_rows": int((is_orb_T & (block_T == "B") & ~ladder_T).sum()),
    "block_B_qtof_rows": int((is_qtof_T & (block_T == "B")).sum()),
    "T_sim_rows_with_missing_instrument": int((~is_orb_T & ~is_qtof_T).sum()),
}
check("C1_no_T_sim_row_has_missing_instrument",
      int((~is_orb_T & ~is_qtof_T).sum()) == 0, int((~is_orb_T & ~is_qtof_T).sum()))
check("C2_block_A_ladder_rows_all_stay_CAT4",
      bool((CAT[is_orb_T & is_int & ladder_T & (block_T == "A")] == "CAT4_UNKNOWN_AMBIGUOUS").all()),
      blockA_orb_int_ladder)

# -------------------------------- extra reconciliations against Q section 2.2/2.3
notsim = ~sim_flag
instr_missing = df["instrument_type"].isna().to_numpy()
adduct = df["adduct"].to_numpy()
stage = {
    "msg15_rows": int(len(df)),
    "notsim_ce_missing_instrument_present": int((notsim & ~ce_present & ~instr_missing).sum()),
    "notsim_ce_and_instrument_missing": int((notsim & ~ce_present & instr_missing).sum()),
    "notsim_adduct_not_MH_ce_instr_present": int((notsim & ce_present & ~instr_missing
                                                  & (adduct != "[M+H]+")).sum()),
    "notsim_instrument_missing_only": int((notsim & ce_present & instr_missing).sum()),
    "T_sim": n_T,
}
report["counts"]["stage_table"] = stage
check("stage_table_matches_Q_2_2",
      stage == {"msg15_rows": 231104, "notsim_ce_missing_instrument_present": 104174,
                "notsim_ce_and_instrument_missing": 5184,
                "notsim_adduct_not_MH_ce_instr_present": 2678,
                "notsim_instrument_missing_only": 39, "T_sim": 119029}, stage)
check("stage_table_sums_to_231104",
      sum(v for k, v in stage.items() if k not in ("msg15_rows",)) == 231104,
      sum(v for k, v in stage.items() if k not in ("msg15_rows",)))

kept_train = int(((~excluded) & (split_T == "train")).sum())
check("inten_contr_kept_train_88178_in_step_window",
      kept_train == 88178 and 88129 <= kept_train <= 88192, kept_train)
# S2 sensitivity: base keys = round-half-even (= the label key) drops 0 rows
s2_excluded = label_key != np.array([collision_key(v) for v in ce_T])
check("S2_round_keyed_base_drops_0_rows", int(s2_excluded.sum()) == 0, int(s2_excluded.sum()))

chance_orb = float(chance_p[is_orb_T & ~is_int].sum())
chance_qtof = float(chance_p[is_qtof_T & ~is_int].sum())
check("chance_expectations_match_Q_2_4",
      round(chance_orb, 2) == 0.41 and round(chance_qtof, 1) == 182.6,
      {"orbitrap_nonint_expected": chance_orb, "qtof_nonint_expected": chance_qtof,
       "qtof_nonint_T500_pass": int((is_qtof_T & ~is_int & T500).sum())})
check("exact_vs_isclose_integer_15_rows",
      int((is_orb_T & ~is_int & np.isclose(ce_T, np.round(ce_T))).sum()) == 15,
      int((is_orb_T & ~is_int & np.isclose(ce_T, np.round(ce_T))).sum()))

# ----------------------- presented-value spot check vs network_ce_value_quantiles
qq = pd.read_csv(COUNTS / "network_ce_value_quantiles.csv")
qq = qq[(qq.checkpoint == "iceberg21_msg_simulation_gen") & (qq.value_hypothesis == "as_trained")
        & (qq.split_scope == "train") & (qq.quantity == "presented_value (eV if read as eV)")]
pv = np.floor(ce_T)
tr = split_T == "train"
pv_rows = []
for inst in ["ALL", "Orbitrap", "QTOF"]:
    for cat in ["ALL"] + sorted(set(CAT.tolist())):
        m = tr.copy()
        if inst != "ALL":
            m &= np.array([x == inst for x in instr_T])
        if cat != "ALL":
            m &= (CAT == cat)
        if m.sum() == 0:
            continue
        v = pv[m]
        pv_rows.append({"instrument": inst, "category": cat, "n": int(m.sum()),
                        "n_distinct": int(len(np.unique(v))), "min": float(v.min()),
                        "q50": float(np.quantile(v, 0.5)), "max": float(v.max())})
pv_mine = pd.DataFrame(pv_rows)
pv_cmp = pv_mine.merge(qq[["instrument", "category", "n", "n_distinct", "min", "q50", "max"]],
                       on=["instrument", "category"], how="inner", suffixes=("_v", "_q"))
pv_bad = pv_cmp[(pv_cmp.n_v != pv_cmp.n_q) | (pv_cmp.n_distinct_v != pv_cmp.n_distinct_q)
                | (pv_cmp.min_v != pv_cmp.min_q) | (pv_cmp.q50_v != pv_cmp.q50_q)
                | (pv_cmp.max_v != pv_cmp.max_q)]
report["diffs"]["presented_value_spot_check_gen_train"] = {
    "cells_compared": int(len(pv_cmp)), "disagreements": int(len(pv_bad)),
    "detail": pv_bad.to_dict("records"), "mine": pv_rows}
check("presented_value_gen_train_spot_check", len(pv_bad) == 0 and len(pv_cmp) >= 6,
      {"cells": int(len(pv_cmp)), "disagreements": int(len(pv_bad))})

report["boundaries"] = {"B_start": B_start, "C_start": C_start, "n_runs": int(n_runs)}


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


with open(COUNTS / "v_independent_counts.json", "w") as fh:
    json.dump(jsonable(report), fh, indent=1, sort_keys=False, default=str)

n_fail = sum(1 for v in report["checks"].values() if not v["pass"])
print(f"\nchecks: {len(report['checks'])}, failures: {n_fail}")
print("wrote", COUNTS / "v_independent_counts.csv", "and", COUNTS / "v_independent_counts.json")
sys.exit(0)
