#!/usr/bin/env python3
"""Design A population construction, MURU collision-energy interface adjudication.

Outcome-blind. Metadata only. No record file, no peak list, no spectrum file, no model prediction is
opened or fetched by this script. The only inputs are the three frozen screen tables listed in INPUTS.

Rules are applied in a strict order R1..R9. Every one of the 5,051 input records gets exactly one
first_failed_rule (or PASS) in the exclusion ledger, so the attrition is fully reconstructible.

Frozen decisions made by this script are recorded in design_a_counts.json under "frozen_rules".

Usage:  /opt/miniconda3/bin/python3 scripts/ce_interface_adjudication/design_a/10_build_population.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1]))
import scaffold_key as SK  # noqa: E402

from rdkit import Chem, RDLogger  # noqa: E402
from rdkit.Chem import Descriptors  # noqa: E402

RDLogger.DisableLog("rdApp.*")

SCREEN_DIR = REPO / "artifacts/ce_interface_adjudication/screen/c01_eawag_eq"
IN_RECORDS = SCREEN_DIR / "c01_record_metadata.csv.gz"
IN_SCREEN = SCREEN_DIR / "c01_compound_screen.csv"
IN_TAUTOMER = SCREEN_DIR / "c01_tautomer_recheck.csv"
OUT_DIR = REPO / "artifacts/ce_interface_adjudication/design_a/population"

# ---------------------------------------------------------------------------
# Frozen constants
# ---------------------------------------------------------------------------
# Proton mass as used by the frozen C01 screen (screen_c01_eawag_eq.py line 34), so that the
# theoretical [M+H]+ recomputed here is on the same numerical axis as the cached mh_calc column.
PROTON_MASS = 1.00727646688
# Theoretical [M+H]+ = rdkit.Chem.Descriptors.ExactMolWt(parent_mol(smiles)) + PROTON_MASS, where
# parent_mol is the MURU LargestFragmentChooser(preferOrganic=True) + Uncharger normalisation
# (scaffold_key.parent_mol). ExactMolWt uses RDKit monoisotopic masses of the most common isotope.

TAGGED_RELEASES = ("2024.06", "2024.11", "2025.10")
DEV_RELEASE = "dev"
ACCEPTED_INSTRUMENT_TYPES = ("LC-ESI-QFT", "LC-ESI-ITFT")
NCE_CELLS = (30.0, 60.0)
CE_FORM_ACCEPTED = "N % (nominal)"

# R6 mass-integrity threshold, chosen from the data distribution; justification in JUSTIFY below.
MH_ERROR_TOL_DA = 0.01

# R7 model-support constants, read from /Users/aryav/muru-comparators/repos/ms-pred
# src/ms_pred/common/chem_utils.py: VALID_ELEMENTS (lines 38-57) and MAX_ATOM_CT (line 132).
MSPRED_VALID_ELEMENTS = frozenset(
    ["C", "N", "P", "O", "S", "Si", "I", "H", "Cl", "F", "Br", "B", "Se", "Fe", "Co", "As", "Na", "K"]
)
MSPRED_MAX_ATOM_CT = 160
# Precursor support bound. Two candidates are documented in
# MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md section 3.4:
#   ICEBERG training-label maximum   995.556
#   MassSpecGym maximum              999.396
# The tighter ICEBERG label maximum is APPLIED: it is the maximum precursor actually present in the
# label table the frozen checkpoints were trained on, so it is the true edge of trained support,
# while 999.396 is the maximum of the wider MassSpecGym release including rows the checkpoints never
# saw. Using the tighter bound cannot admit a compound outside either support.
PRECURSOR_BOUND_APPLIED = 995.556
PRECURSOR_BOUND_ALTERNATIVE = 999.396

JUSTIFY = {
    "R2_instrument_type": (
        "Orbitrap instrument-type strings accepted: LC-ESI-QFT and LC-ESI-ITFT. Only LC-ESI-QFT is "
        "present in C01 (5,051 of 5,051 records); LC-ESI-ITFT is accepted by the rule but contributes "
        "nothing here. QTOF is excluded by design constraint: MURU's claim scope is Orbitrap HCD "
        "fixed NCE, and the checkpoints' instrument vocabulary treats QTOF as a separate token."
    ),
    "R6_mh_error_threshold": (
        "mh_error_da = deposited PRECURSOR_M/Z minus theoretical [M+H]+ of the MURU parent structure "
        "(screen_c01_eawag_eq.py lines 188 and 207). It is therefore a SIGNED quantity on the [M+H]+ "
        "axis only: every [M-H]- record shows about -2.0146 Da by construction, which is the adduct "
        "sign artifact and not a defect. R1 removes all 1,756 negative-mode records before R6 runs, so "
        "no artifact reaches the threshold. Within the 3,295 [M+H]+ records the distribution is "
        "bimodal with a six-order-of-magnitude gap: max |error| in the clean mode is 5.0e-5 Da "
        "(q99 4.98e-5), then nothing until 82.0127 Da (9 records of one compound). A threshold of "
        "0.01 Da sits 200x above the clean maximum and 8,200x below the defect, and gives the same 9 "
        "records as 0.005 or 0.002 Da, so the result is insensitive to the exact choice inside the gap."
    ),
    "R7_precursor_bound": (
        "Applied bound 995.556 (ICEBERG training-label maximum, Phase 1-3 design section 3.4). The "
        "MassSpecGym maximum 999.396 is the looser alternative and is reported but not applied, "
        "because the label table is what the frozen checkpoints were trained on. No C01 record is "
        "between the two bounds, so the choice removes nothing either way."
    ),
    "R8_tautomer_recheck": (
        "The canonical-tautomer-key hidden-inclusion recheck is APPLIED as sub-rule R8m (it is what "
        "caught clethodim, PHXHZCIAPNNPTQ, at Morgan Tanimoto 0.54 to its MassSpecGym enol form "
        "IOYNQIMAUDJVEI). The formula-constrained heavy-atom SKELETON key from the same recheck table "
        "is computed and reported but NOT applied, because the task names only the tautomer route; it "
        "fires on no compound that the tautomer route does not already remove, so applying it would "
        "change nothing."
    ),
    "representative_structure": (
        "One parent_connectivity_key can carry several deposited SMILES strings. Frozen rule: the "
        "representative structure is the LEXICOGRAPHICALLY SMALLEST RDKit canonical SMILES "
        "(Chem.MolToSmiles of Chem.MolFromSmiles of the deposited CH$SMILES) among the compound's "
        "records that survive the record-level rules R1 through R7. Ties are impossible because the "
        "candidate set is a set of strings."
    ),
    "compound_identifier": (
        "parent_connectivity_key (column parent_key), the MURU compound identifier, frozen as THE "
        "compound identifier. The deposited recorded InChIKey first block is carried alongside for "
        "traceability but is never the grouping key."
    ),
}

RULES = [
    ("R1", "ion mode POSITIVE and precursor type exactly [M+H]+"),
    ("R2", "MS2, HCD, Orbitrap instrument type (LC-ESI-QFT or LC-ESI-ITFT)"),
    ("R3", "collision energy in single-value 'N % (nominal)' form and nce parses to a finite float"),
    ("R4", "nce exactly 30 or exactly 60"),
    ("R5", "release provenance: first_ref in a post-2023.11 tagged release"),
    ("R6", "structural integrity"),
    ("R7", "model support (elements, heavy atoms, precursor bound)"),
    ("R8", "compound-level identity exclusions"),
    ("R9", "cell completeness: at least one record at NCE 30 and one at NCE 60"),
]

R8_SUBRULES = [
    ("R8a", "in_msg15_recorded_route", "compound key in MassSpecGym 1.5 by the recorded InChIKey route"),
    ("R8b", "in_msg15_parent_route", "compound key in MassSpecGym 1.5 by the MURU parent key route"),
    ("R8c", "in_mspred_msg_labels", "compound in the ms-pred msg_simulation labels"),
    ("R8d", "in_muru_registry_keys", "compound in the MURU exposure registry"),
    ("R8e", "in_muru_exposed_pop_keys", "compound in a MURU exposed population"),
    ("R8f", "in_muru_dev_pop_keys", "compound in a MURU development population"),
    ("R8g", "in_pr7_keys", "compound in the PR #7 confirmation population"),
    ("R8h", "in_comparator_keys", "compound in the comparator benchmark population"),
    ("R8i", "sg_in_muru_registry", "scaffold group guard: group in the MURU exposure registry"),
    ("R8j", "sg_in_muru_dev_pop", "scaffold group guard: group in a MURU development population"),
    ("R8k", "sg_in_pr7", "scaffold group guard: group in the PR #7 population"),
    ("R8l", "sg_in_comparator", "scaffold group guard: group in the comparator population"),
]
R8M_TAUTOMER_COLUMNS = [
    "msg15_taut_key_hit",
    "muru_dev_pop_taut_key_hit",
    "pr7_taut_key_hit",
    "comparator_taut_key_hit",
]
R8_SKELETON_COLUMNS = [
    "msg15_skel_key_hit",
    "muru_dev_pop_skel_key_hit",
    "pr7_skel_key_hit",
    "comparator_skel_key_hit",
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(bool)


def jsonable(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return None if not math.isfinite(v) else v
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    return x


def theoretical_mh(smiles: str) -> float:
    pm = SK.parent_mol(smiles)
    if pm is None:
        return float("nan")
    return float(Descriptors.ExactMolWt(pm) + PROTON_MASS)


def canonical(smiles: str) -> str | None:
    m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    return Chem.MolToSmiles(m) if m is not None else None


def run_cascade(rec: pd.DataFrame, cflags: pd.DataFrame, releases: tuple[str, ...]):
    """Apply R1..R9 in order. Returns (population_df, ledger_series, step_counts, r8_detail)."""
    n = len(rec)
    failed = pd.Series([None] * n, index=rec.index, dtype=object)
    reason = pd.Series([None] * n, index=rec.index, dtype=object)

    def mark(mask_fail: pd.Series, rule: str, why: str | pd.Series):
        alive = failed.isna()
        hit = alive & mask_fail.reindex(rec.index).fillna(True)
        failed.loc[hit] = rule
        if isinstance(why, pd.Series):
            reason.loc[hit] = why.reindex(rec.index)[hit]
        else:
            reason.loc[hit] = why
        return hit

    steps = []

    def record_step(rule: str, desc: str):
        alive = failed.isna()
        steps.append(
            {
                "rule": rule,
                "description": desc,
                "records_surviving": int(alive.sum()),
                "compounds_surviving": int(rec.loc[alive, "parent_key"].nunique()),
                "scaffold_groups_surviving": int(rec.loc[alive, "scaffold_group"].nunique()),
            }
        )

    steps.append(
        {
            "rule": "R0",
            "description": "input records (C01 Eawag EQ, first released after MassBank 2023.11)",
            "records_surviving": n,
            "compounds_surviving": int(rec["parent_key"].nunique()),
            "scaffold_groups_surviving": int(rec["scaffold_group"].nunique()),
        }
    )

    # R1
    ok = (rec["ion_mode"] == "POSITIVE") & (rec["precursor_type"] == "[M+H]+")
    why = "ion_mode=" + rec["ion_mode"].astype(str) + " precursor_type=" + rec["precursor_type"].astype(str)
    mark(~ok, "R1", why)
    record_step("R1", RULES[0][1])

    # R2
    ok = (
        (rec["ms_type"] == "MS2")
        & (rec["frag_mode"] == "HCD")
        & (rec["instrument_type"].isin(ACCEPTED_INSTRUMENT_TYPES))
    )
    why = (
        "ms_type=" + rec["ms_type"].astype(str)
        + " frag_mode=" + rec["frag_mode"].astype(str)
        + " instrument_type=" + rec["instrument_type"].astype(str)
    )
    mark(~ok, "R2", why)
    record_step("R2", RULES[1][1])

    # R3
    ok = (rec["ce_form"] == CE_FORM_ACCEPTED) & np.isfinite(rec["nce"])
    why = "ce_form=" + rec["ce_form"].astype(str) + " ce=" + rec["ce"].astype(str)
    mark(~ok, "R3", why)
    record_step("R3", RULES[2][1])

    # R4
    ok = rec["nce"].isin(list(NCE_CELLS))
    why = "nce=" + rec["nce"].map(lambda v: f"{v:g}" if pd.notna(v) else "NA") + " not an adjudication cell (30 or 60)"
    mark(~ok, "R4", why)
    record_step("R4", RULES[3][1])

    # R5
    ok = rec["first_ref"].isin(list(releases))
    why = "first_ref=" + rec["first_ref"].astype(str) + " not a tagged release " + str(list(releases))
    mark(~ok, "R5", why)
    record_step("R5", RULES[4][1])

    # R6
    parts = []
    bad = pd.Series(False, index=rec.index)
    for col, label in [
        ("smiles_parse", "smiles_parse false"),
        ("smiles_ik_equals_recorded", "smiles InChIKey not equal to recorded"),
        ("inchi_ik_equals_recorded", "inchi InChIKey not equal to recorded"),
    ]:
        f = ~as_bool(rec[col])
        bad |= f
        parts.append((f, label))
    f = rec["formal_charge"].fillna(-999) != 0
    bad |= f
    parts.append((f, "formal_charge not 0"))
    f = ~(rec["mh_error_da"].abs() <= MH_ERROR_TOL_DA)
    bad |= f
    parts.append((f, f"abs(mh_error_da) > {MH_ERROR_TOL_DA} Da"))
    why = pd.Series("", index=rec.index, dtype=object)
    for f, label in parts:
        why = why.where(~f | (why != ""), label)
    why = why.where(why != "", "R6 fail")
    why = why + rec["mh_error_da"].map(lambda v: f" (mh_error_da={v:.6g})" if pd.notna(v) else " (mh_error_da=NA)")
    mark(bad, "R6", why)
    record_step("R6", RULES[5][1])

    # R7
    el_bad = rec["elements"].fillna("").map(lambda s: bool(set(x for x in s.split(",") if x) - MSPRED_VALID_ELEMENTS))
    ha_bad = ~(rec["heavy_atoms"] <= MSPRED_MAX_ATOM_CT)
    mz_bad = ~(rec["mh_calc"] <= PRECURSOR_BOUND_APPLIED)
    bad = el_bad | ha_bad | mz_bad
    why = pd.Series("R7 fail", index=rec.index, dtype=object)
    why = why.mask(mz_bad, rec["mh_calc"].map(lambda v: f"theoretical [M+H]+ {v:.4f} above {PRECURSOR_BOUND_APPLIED}"))
    why = why.mask(ha_bad, rec["heavy_atoms"].map(lambda v: f"heavy_atoms {v} above MAX_ATOM_CT {MSPRED_MAX_ATOM_CT}"))
    why = why.mask(el_bad, "elements outside ms-pred VALID_ELEMENTS: " + rec["elements"].fillna(""))
    mark(bad, "R7", why)
    record_step("R7", RULES[6][1])

    # R8, compound level, sub-rule by sub-rule so the ledger shows which one fired first
    alive = failed.isna()
    live_keys = sorted(rec.loc[alive, "parent_key"].unique())
    missing = [k for k in live_keys if k not in cflags.index]
    if missing:
        raise SystemExit(f"compound flags missing for {len(missing)} keys, e.g. {missing[:5]}")
    removed = {}
    r8_detail = []
    for rid, col, desc in R8_SUBRULES:
        fires = as_bool(cflags.loc[live_keys, col])
        new = [k for k in live_keys if fires[k] and k not in removed]
        r8_detail.append(
            {"sub_rule": rid, "column": col, "description": desc,
             "compounds_flagged": int(fires.sum()), "compounds_newly_removed": len(new), "applied": True}
        )
        for k in new:
            removed[k] = (rid, desc)
    taut = pd.Series(False, index=live_keys)
    for col in R8M_TAUTOMER_COLUMNS:
        taut |= as_bool(cflags.loc[live_keys, col])
    new = [k for k in live_keys if taut[k] and k not in removed]
    r8_detail.append(
        {"sub_rule": "R8m", "column": "|".join(R8M_TAUTOMER_COLUMNS),
         "description": "tautomer-key hidden-inclusion recheck (any of the four target populations)",
         "compounds_flagged": int(taut.sum()), "compounds_newly_removed": len(new), "applied": True}
    )
    for k in new:
        removed[k] = ("R8m", "tautomer-key hidden-inclusion recheck")
    skel = pd.Series(False, index=live_keys)
    for col in R8_SKELETON_COLUMNS:
        skel |= as_bool(cflags.loc[live_keys, col])
    r8_detail.append(
        {"sub_rule": "R8n-informational", "column": "|".join(R8_SKELETON_COLUMNS),
         "description": "formula-constrained skeleton-key recheck, REPORTED BUT NOT APPLIED",
         "compounds_flagged": int(skel.sum()),
         "compounds_newly_removed": len([k for k in live_keys if skel[k] and k not in removed]),
         "applied": False}
    )
    rem_rule = rec["parent_key"].map(lambda k: removed.get(k, (None, None))[0])
    rem_why = rec["parent_key"].map(
        lambda k: (f"{removed[k][0]}: {removed[k][1]}" if k in removed else None)
    )
    mark(rem_rule.notna(), "R8", rem_why.fillna("R8 fail"))
    record_step("R8", RULES[7][1])

    # R9
    alive = failed.isna()
    have = rec.loc[alive].groupby("parent_key")["nce"].agg(lambda s: set(s))
    incomplete = {k for k, v in have.items() if not set(NCE_CELLS) <= v}
    why = rec["parent_key"].map(
        lambda k: (
            "compound has NCE cells {" + ",".join(f"{v:g}" for v in sorted(have.get(k, set()))) + "}, needs both 30 and 60"
            if k in incomplete else None
        )
    )
    mark(rec["parent_key"].isin(incomplete), "R9", why.fillna("R9 fail"))
    record_step("R9", RULES[8][1])

    failed = failed.fillna("PASS")
    reason = reason.where(failed != "PASS", "eligible")
    pop = rec.loc[failed == "PASS"].copy()
    return pop, failed, reason, steps, r8_detail


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rec = pd.read_csv(IN_RECORDS)
    screen = pd.read_csv(IN_SCREEN)
    taut = pd.read_csv(IN_TAUTOMER)

    cflags = screen.set_index("cmp_key")
    tflags = taut.set_index("cmp_key")
    cflags = cflags.join(tflags[R8M_TAUTOMER_COLUMNS + R8_SKELETON_COLUMNS + ["parent_key_recomputed"]], how="left")

    # --------------------------------------------------------------- primary
    pop, failed, reason, steps, r8_detail = run_cascade(rec, cflags, TAGGED_RELEASES)
    # ------------------------------------------------- secondary, dev PR included
    pop_dev, failed_dev, _, steps_dev, r8_dev = run_cascade(rec, cflags, TAGGED_RELEASES + (DEV_RELEASE,))

    # ------------------------------------------------- representative structure
    eligible_for_rep = rec.loc[failed.isin(["PASS", "R8", "R9"])].copy()  # survived R1..R7
    canon = {s: canonical(s) for s in sorted(set(eligible_for_rep["smiles"].dropna()))}
    eligible_for_rep["canonical_smiles"] = eligible_for_rep["smiles"].map(canon)
    rep_smiles = (
        eligible_for_rep.dropna(subset=["canonical_smiles"])
        .groupby("parent_key")["canonical_smiles"]
        .agg(lambda s: sorted(set(s))[0])
    )
    multi_struct = (
        eligible_for_rep.groupby("parent_key")
        .agg(
            n_distinct_deposited_smiles=("smiles", "nunique"),
            n_distinct_canonical_smiles=("canonical_smiles", "nunique"),
            n_distinct_recorded_key14=("recorded_key14", "nunique"),
            n_distinct_scaffold_group=("scaffold_group", "nunique"),
        )
    )
    ambiguous = multi_struct[
        (multi_struct["n_distinct_canonical_smiles"] > 1) | (multi_struct["n_distinct_recorded_key14"] > 1)
    ]
    ambiguous_report = [
        {
            "compound_id": k,
            "n_distinct_deposited_smiles": int(r.n_distinct_deposited_smiles),
            "n_distinct_canonical_smiles": int(r.n_distinct_canonical_smiles),
            "n_distinct_recorded_key14": int(r.n_distinct_recorded_key14),
            "n_distinct_scaffold_group": int(r.n_distinct_scaffold_group),
            "representative_smiles": rep_smiles.get(k),
            "all_canonical_smiles": sorted(
                set(eligible_for_rep.loc[eligible_for_rep["parent_key"] == k, "canonical_smiles"].dropna())
            ),
            "all_recorded_key14": sorted(
                set(eligible_for_rep.loc[eligible_for_rep["parent_key"] == k, "recorded_key14"].dropna())
            ),
        }
        for k, r in ambiguous.iterrows()
    ]
    # the same check on the whole 5,051-record input, not just the eligible subset
    all_canon = {s: canonical(s) for s in sorted(set(rec["smiles"].dropna()))}
    whole = rec.assign(canonical_smiles=rec["smiles"].map(all_canon)).groupby("parent_key").agg(
        nc=("canonical_smiles", "nunique"), nk=("recorded_key14", "nunique"), nsg=("scaffold_group", "nunique")
    )
    whole_ambiguous = [
        {"compound_id": k, "n_distinct_canonical_smiles": int(r.nc),
         "n_distinct_recorded_key14": int(r.nk), "n_distinct_scaffold_group": int(r.nsg)}
        for k, r in whole[(whole.nc > 1) | (whole.nk > 1) | (whole.nsg > 1)].iterrows()
    ]

    # ------------------------------------------------- theoretical [M+H]+ and scaffolds
    rep = pd.DataFrame({"representative_smiles": rep_smiles})
    rep["theoretical_mh"] = rep["representative_smiles"].map(theoretical_mh)
    recomputed = {s: SK.key_and_group(s) for s in rep["representative_smiles"]}
    rep["key_recomputed"] = rep["representative_smiles"].map(lambda s: recomputed[s][0])
    rep["scaffold_group_recomputed"] = rep["representative_smiles"].map(lambda s: recomputed[s][1])

    pop = pop.join(rep, on="parent_key")
    pop["record_id"] = pop["file"].map(lambda s: Path(str(s)).stem)
    pop["blob_sha"] = pop["blob_2025_10"].where(pop["blob_2025_10"].notna(), pop["blob_dev"])
    pop = pop.sort_values(["parent_key", "nce", "record_id"], kind="mergesort").reset_index(drop=True)
    pop["order_index"] = np.arange(len(pop), dtype=int)

    # scaffold-group agreement (cached column vs recomputation from the representative structure)
    sg_cached = pop.groupby("parent_key")["scaffold_group"].agg(lambda s: sorted(set(s))[0])
    sg_agree = int((sg_cached == rep.loc[sg_cached.index, "scaffold_group_recomputed"]).sum())
    key_agree = int((pd.Series(sg_cached.index, index=sg_cached.index) == rep.loc[sg_cached.index, "key_recomputed"]).sum())
    sg_disagreements = [
        {"compound_id": k, "cached": sg_cached[k], "recomputed": rep.loc[k, "scaffold_group_recomputed"]}
        for k in sg_cached.index
        if sg_cached[k] != rep.loc[k, "scaffold_group_recomputed"]
    ]

    # theoretical [M+H]+ recomputation vs the cached per-record mh_calc
    mh_recompute_delta = (pop["theoretical_mh"] - pop["mh_calc"]).abs()

    # ------------------------------------------------- record table
    records_out = pd.DataFrame(
        {
            "record_id": pop["record_id"],
            "compound_id": pop["parent_key"],
            "recorded_key14": pop["recorded_key14"],
            "representative_smiles": pop["representative_smiles"],
            "formula": pop["formula"],
            "theoretical_mh": pop["theoretical_mh"],
            "deposited_precursor_mz": pop["precursor_mz_f"],
            "nce": pop["nce"],
            "instrument": pop["instrument"],
            "instrument_type": pop["instrument_type"],
            "resolution": pop["resolution"],
            "release": pop["first_ref"],
            "scaffold_group": pop["scaffold_group"],
            "source_file": pop["file"],
            "blob_sha": pop["blob_sha"],
            "order_index": pop["order_index"],
        }
    )

    # ------------------------------------------------- compound table
    def joinset(s):
        return ";".join(sorted(set(str(x) for x in s.dropna())))

    comp = (
        pop.groupby("parent_key")
        .agg(
            n_records=("record_id", "size"),
            n_records_nce30=("nce", lambda s: int((s == 30.0).sum())),
            n_records_nce60=("nce", lambda s: int((s == 60.0).sum())),
            instruments=("instrument", joinset),
            resolutions=("resolution", joinset),
            releases=("first_ref", joinset),
            theoretical_mh=("theoretical_mh", "first"),
            formula=("formula", joinset),
            scaffold_group=("scaffold_group", "first"),
            representative_smiles=("representative_smiles", "first"),
        )
        .reset_index()
        .rename(columns={"parent_key": "compound_id"})
        .sort_values("compound_id", kind="mergesort")
        .reset_index(drop=True)
    )

    # ------------------------------------------------- ledger
    ledger = pd.DataFrame(
        {
            "record_id": rec["file"].map(lambda s: Path(str(s)).stem),
            "source_file": rec["file"],
            "compound_id": rec["parent_key"],
            "recorded_key14": rec["recorded_key14"],
            "release": rec["first_ref"],
            "ion_mode": rec["ion_mode"],
            "precursor_type": rec["precursor_type"],
            "nce": rec["nce"],
            "first_failed_rule": failed,
            "reason": reason,
        }
    ).sort_values("record_id", kind="mergesort").reset_index(drop=True)

    # ------------------------------------------------- counts
    per_compound_records = Counter(comp["n_records"].tolist())
    sg_sizes = Counter(comp.groupby("scaffold_group").size().tolist())
    pos = rec[rec["precursor_type"] == "[M+H]+"]
    dep_minus_theo = pop["precursor_mz_f"] - pop["theoretical_mh"]

    def dist(a: pd.Series) -> dict:
        a = pd.Series(a).dropna().astype(float)
        if not len(a):
            return {}
        q = a.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
        return {
            "n": int(len(a)), "min": float(a.min()), "q05": float(q.loc[0.05]), "q25": float(q.loc[0.25]),
            "median": float(q.loc[0.5]), "q75": float(q.loc[0.75]), "q95": float(q.loc[0.95]),
            "max": float(a.max()), "mean": float(a.mean()), "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
        }

    dev_pop_comp = sorted(pop_dev["parent_key"].unique())
    primary_comp = sorted(pop["parent_key"].unique())
    counts = {
        "study": "MURU CE interface adjudication, Design A, outcome-blind population build",
        "generated_by": "scripts/ce_interface_adjudication/design_a/10_build_population.py",
        "rdkit_version": __import__("rdkit").__version__,
        "frozen_rules": {
            "compound_identifier": JUSTIFY["compound_identifier"],
            "representative_structure_rule": JUSTIFY["representative_structure"],
            "proton_mass": PROTON_MASS,
            "theoretical_mh_method": (
                "rdkit.Chem.Descriptors.ExactMolWt(parent_mol(representative_smiles)) + PROTON_MASS, where "
                "parent_mol = scaffold_key.parent_mol = LargestFragmentChooser(preferOrganic=True) then Uncharger"
            ),
            "nce_cells": list(NCE_CELLS),
            "tagged_releases": list(TAGGED_RELEASES),
            "accepted_instrument_types": list(ACCEPTED_INSTRUMENT_TYPES),
            "instrument_types_present_in_input": sorted(rec["instrument_type"].dropna().unique().tolist()),
            "qtof_note": "QTOF is excluded by design constraint; none is present in C01.",
            "mh_error_tolerance_da": MH_ERROR_TOL_DA,
            "mspred_valid_elements": sorted(MSPRED_VALID_ELEMENTS),
            "mspred_max_atom_ct": MSPRED_MAX_ATOM_CT,
            "precursor_bound_applied": PRECURSOR_BOUND_APPLIED,
            "precursor_bound_alternative_not_applied": PRECURSOR_BOUND_ALTERNATIVE,
            "justifications": JUSTIFY,
        },
        "rule_steps_primary": steps,
        "r8_sub_rules_primary": r8_detail,
        "final_primary": {
            "records": int(len(records_out)),
            "compounds": int(comp.shape[0]),
            "scaffold_groups": int(comp["scaffold_group"].nunique()),
            "records_by_nce_cell": {f"{k:g}": int(v) for k, v in sorted(Counter(records_out["nce"]).items())},
            "compounds_by_nce_cell": {
                "30": int((comp["n_records_nce30"] > 0).sum()),
                "60": int((comp["n_records_nce60"] > 0).sum()),
            },
            "records_per_compound_distribution": {str(k): int(v) for k, v in sorted(per_compound_records.items())},
            "compounds_per_scaffold_group_distribution": {str(k): int(v) for k, v in sorted(sg_sizes.items())},
            "n_singleton_scaffold_groups": int(sum(1 for _, s in comp.groupby("scaffold_group").size().items() if s == 1)),
            "n_distinct_scaffold_groups": int(comp["scaffold_group"].nunique()),
            "instrument_composition_records": {str(k): int(v) for k, v in sorted(Counter(records_out["instrument"]).items())},
            "instrument_composition_compounds": {
                str(k): int(v) for k, v in sorted(Counter(comp["instruments"]).items())
            },
            "resolution_composition_records": {str(k): int(v) for k, v in sorted(Counter(records_out["resolution"]).items())},
            "release_composition_records": {str(k): int(v) for k, v in sorted(Counter(records_out["release"]).items())},
            "theoretical_mh_distribution": dist(comp["theoretical_mh"]),
        },
        "secondary_dev_pr_figure_NOT_USED_BY_THE_PREREGISTRATION": {
            "label": (
                "Secondary, clearly labelled: the same cascade with R5 widened to admit the unreleased dev "
                "pull request. The preregistration does NOT use these numbers."
            ),
            "records": int(len(pop_dev)),
            "compounds": int(pop_dev["parent_key"].nunique()),
            "scaffold_groups": int(pop_dev["scaffold_group"].nunique()),
            "records_by_nce_cell": {f"{k:g}": int(v) for k, v in sorted(Counter(pop_dev["nce"]).items())},
            "records_by_release": {str(k): int(v) for k, v in sorted(Counter(pop_dev["first_ref"]).items())},
            "compounds_added_vs_primary": sorted(set(dev_pop_comp) - set(primary_comp)),
            "n_compounds_added_vs_primary": len(set(dev_pop_comp) - set(primary_comp)),
            "compounds_lost_vs_primary": sorted(set(primary_comp) - set(dev_pop_comp)),
            "rule_steps": steps_dev,
            "records_excluded_at_R5_as_dev_only": int((failed == "R5").sum()),
        },
        "structure_integrity_and_identity_diagnostics": {
            "compound_keys_spanning_multiple_structures_in_eligible_set": ambiguous_report,
            "compound_keys_spanning_multiple_structures_in_whole_input": whole_ambiguous,
            "scaffold_group_recomputation": {
                "compounds_checked": int(len(sg_cached)),
                "scaffold_group_agreements_with_cached_column": sg_agree,
                "parent_key_agreements_with_cached_column": key_agree,
                "disagreements": sg_disagreements,
            },
            "theoretical_mh_recomputation_vs_cached_mh_calc": {
                "max_abs_delta_da": float(mh_recompute_delta.max()) if len(mh_recompute_delta) else None,
                "n_records_delta_gt_1e_6": int((mh_recompute_delta > 1e-6).sum()),
            },
            "deposited_precursor_minus_theoretical_mh_CHECK_ONLY_NOT_A_FILTER": dist(dep_minus_theo),
            "abs_mh_error_da_all_MH_positive_input_records": dist(pos["mh_error_da"].abs()),
            "mh_error_da_negative_mode_input_records_ADDUCT_SIGN_ARTIFACT": dist(
                rec.loc[rec["precursor_type"] == "[M-H]-", "mh_error_da"]
            ),
            "records_failing_R6_on_mass": [
                {"record_id": Path(str(r.file)).stem, "compound_id": r.parent_key, "formula": r.formula,
                 "deposited_precursor_mz": float(r.precursor_mz_f), "theoretical_mh": float(r.mh_calc),
                 "mh_error_da": float(r.mh_error_da)}
                for r in rec.loc[
                    (rec["precursor_type"] == "[M+H]+") & (rec["mh_error_da"].abs() > MH_ERROR_TOL_DA)
                ].itertuples()
            ],
            "nce_values_present_in_MH_positive_input": {
                f"{k:g}": int(v) for k, v in sorted(Counter(pos["nce"].dropna()).items())
            },
            "nce_values_excluded_at_R4": {
                f"{k:g}": int(v)
                for k, v in sorted(Counter(rec.loc[failed == "R4", "nce"].dropna()).items())
            },
        },
        "exclusion_ledger_summary": {
            "records_total": int(len(ledger)),
            "by_first_failed_rule": {str(k): int(v) for k, v in sorted(Counter(ledger["first_failed_rule"]).items())},
        },
    }

    # ------------------------------------------------- write
    p_rec = OUT_DIR / "design_a_records.csv"
    p_cmp = OUT_DIR / "design_a_compounds.csv"
    p_led = OUT_DIR / "design_a_exclusion_ledger.csv"
    p_cnt = OUT_DIR / "design_a_counts.json"
    records_out.to_csv(p_rec, index=False)
    comp.to_csv(p_cmp, index=False)
    ledger.to_csv(p_led, index=False)
    p_cnt.write_text(json.dumps(jsonable(counts), indent=1, sort_keys=True) + "\n")

    manifest = {
        "inputs_read": {
            str(p.relative_to(REPO)): sha256_of(p) for p in [IN_RECORDS, IN_SCREEN, IN_TAUTOMER]
        },
        "outputs_written": {
            str(p.relative_to(REPO)): sha256_of(p) for p in [p_rec, p_cmp, p_led, p_cnt]
        },
        "script": str(HERE.relative_to(REPO)),
        "script_sha256": sha256_of(HERE),
    }
    p_man = OUT_DIR / "design_a_manifest_sha256.json"
    p_man.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")

    # ------------------------------------------------- print
    f = counts["final_primary"]
    print("Design A population build")
    print(f"  input records                  {len(rec)}")
    for s in steps:
        print(f"  {s['rule']:3s} surviving records {s['records_surviving']:5d}  compounds {s['compounds_surviving']:4d}"
              f"  scaffold groups {s['scaffold_groups_surviving']:4d}   {s['description']}")
    print(f"  FINAL  records {f['records']}  compounds {f['compounds']}  scaffold groups {f['scaffold_groups']}")
    print(f"  by NCE cell  {f['records_by_nce_cell']}")
    print(f"  records per compound  {f['records_per_compound_distribution']}")
    print(f"  compounds per scaffold group  {f['compounds_per_scaffold_group_distribution']}"
          f"  (singletons {f['n_singleton_scaffold_groups']})")
    print(f"  instruments (records)  {f['instrument_composition_records']}")
    print(f"  resolutions (records)  {f['resolution_composition_records']}")
    print(f"  releases (records)     {f['release_composition_records']}")
    print("  R8 sub-rule attrition (compounds newly removed):")
    for r in r8_detail:
        tag = "" if r["applied"] else "   [NOT APPLIED]"
        print(f"    {r['sub_rule']:18s} flagged {r['compounds_flagged']:4d}  newly removed {r['compounds_newly_removed']:4d}{tag}")
    sec = counts["secondary_dev_pr_figure_NOT_USED_BY_THE_PREREGISTRATION"]
    print(f"  SECONDARY (dev PR included, NOT used by the preregistration): records {sec['records']}, "
          f"compounds {sec['compounds']}, scaffold groups {sec['scaffold_groups']}, "
          f"+{sec['n_compounds_added_vs_primary']} compounds vs primary")
    print(f"  wrote {p_rec.name}, {p_cmp.name}, {p_led.name}, {p_cnt.name}, {p_man.name} in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
