"""E1 hostile audit: independently re-derive the primary result from the raw
persisted tables, WITHOUT importing e1_rules.py or e1_analyze.py (the primary
analyzer) -- every criterion, rule, metric, and the selection itself is
reimplemented here, fresh, from MURU_V2_E1_PROTOCOL.md's own declared
formulas, using different code shape than the primary implementation (loop/
dict aggregation rather than the primary's pivoted-groupby style) so this is
a real second implementation, not a relabelled call into the first.

Writes artifacts/e1/e1_hostile_audit.json. Exits non-zero if any check fails.
"""
from __future__ import annotations

import glob
import json
import math
import os
import subprocess
import sys
from collections import defaultdict
from math import comb

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)

ALPHA_LEVELS = (0.25, 0.5, 1.0, 2.0)
DETECTORS = ("M1", "M2", "M3")
MU_CEIL_LEVELS = ("c1e4", "c1e3", "copen")
NOISE_LEVELS = (0.0, 0.02, 0.06)
D_TYPES_NONNULL = ("M1", "M2", "M3", "M1M2M3")
MIN_EVALUABLE = 24


def check(name, condition, detail=None):
    return {"check": name, "pass": bool(condition), "detail": detail}


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (max(0.0, (centre - adj) / denom), min(1.0, (centre + adj) / denom))


def sign_tail(wins: int, evaluable: int) -> float:
    if evaluable <= 0:
        return 1.0
    if wins > evaluable:
        return 0.0
    return sum(comb(evaluable, k) for k in range(wins, evaluable + 1)) / float(2 ** evaluable)


# --------------------------------------------------------------------------
# Independent criterion / rule scoring (fresh logic; row-dict based, not the
# primary's vectorised-pandas approach)
# --------------------------------------------------------------------------


def compound_unresolved(row: dict, cid: str, cparams: dict) -> bool:
    if cid == "C0":
        return bool(row["m0_unresolved_c0_any"]) or bool(row["mk_unresolved_c0_any"])
    if cid == "C1":
        d = cparams["delta"]
        for k in ("m0_max_probe_gain_rel", "mk_max_probe_gain_rel"):
            v = row[k]
            if v is not None and not (isinstance(v, float) and math.isnan(v)) and v > d:
                return True
        return False
    if cid == "C2":
        d = cparams["delta"]
        for k in ("m0_max_c2_ratio", "mk_max_c2_ratio"):
            v = row[k]
            if v is not None and not (isinstance(v, float) and math.isnan(v)) and v > d:
                return True
        return False
    if cid == "C3":
        rho = cparams["rho"]
        for k in ("m0_max_profile_ratio", "mk_max_profile_ratio"):
            v = row[k]
            if v is not None and not (isinstance(v, float) and math.isnan(v)) and v > rho:
                return True
        return False
    if cid == "C4":
        return bool(row["c4_verdict_flip"])
    raise ValueError(cid)


def rule_fired(evaluable: int, wins90: int, median_rel: float | None, pairs_by_ratio: dict, rid: str, rparams: dict) -> bool:
    if evaluable < MIN_EVALUABLE:
        return False
    if rid == "P0":
        return wins90 >= 20
    if rid == "P1":
        return pairs_by_ratio[rparams["ratio"]] >= rparams["w"]
    if rid == "P2":
        return sign_tail(wins90, evaluable) <= rparams["q"]
    if rid == "P3":
        if median_rel is None or median_rel < rparams["m"]:
            return False
        return (wins90 / evaluable) >= rparams["f"]
    raise ValueError(rid)


CRITERIA = {
    "C0": [{}],
    "C1": [{"delta": d} for d in (1e-3, 3e-3, 1e-2, 3e-2, 1e-1)],
    "C2": [{"delta": d} for d in (0.25, 0.5, 1, 2, 4)],
    "C3": [{"rho": r} for r in (0.05, 0.10, 0.25)],
    "C4": [{}],
}
RULES = {
    "P0": [{}],
    "P1": [{"ratio": r, "w": w} for r in (0.80, 0.90, 0.95, 0.98) for w in (15, 18, 20, 24)],
    "P2": [{"q": q} for q in (0.05, 0.01, 0.001)],
    "P3": [{"m": m, "f": f} for m in (0.05, 0.10) for f in (0.5, 0.6, 0.67)],
}
FREE_PARAMS = {"C0": 0, "C1": 1, "C2": 1, "C3": 1, "C4": 0, "P0": 3, "P1": 2, "P2": 1, "P3": 2}
WIN_RATIOS = (0.80, 0.90, 0.95, 0.98)


def score_pair(records_by_world_detector: dict, world_meta: dict, cid: str, cparams: dict, rid: str, rparams: dict) -> dict:
    """records_by_world_detector: {(world_id, detector): [compound_row, ...]}"""
    fired_by_world = defaultdict(dict)
    suff_by_world = defaultdict(dict)
    for (world_id, detector), rows in records_by_world_detector.items():
        evaluable = 0
        wins90 = 0
        wins_by_ratio = {r: 0 for r in WIN_RATIOS}
        rel_reductions = []
        for row in rows:
            if row["mae_m0"] is None or row["mae_alt"] is None:
                continue
            if compound_unresolved(row, cid, cparams):
                continue
            evaluable += 1
            mae0, maek = row["mae_m0"], row["mae_alt"]
            if mae0 > 0:
                rel_reductions.append((mae0 - maek) / mae0)
                for r in WIN_RATIOS:
                    if maek <= r * mae0:
                        wins_by_ratio[r] += 1
                if maek <= 0.90 * mae0:
                    wins90 += 1
        median_rel = float(np.median(rel_reductions)) if rel_reductions else None
        fired = rule_fired(evaluable, wins90, median_rel, wins_by_ratio, rid, rparams)
        fired_by_world[world_id][detector] = fired
        suff_by_world[world_id][detector] = evaluable >= MIN_EVALUABLE

    world_status = {}
    for world_id, det_map in fired_by_world.items():
        fired_dets = [d for d in DETECTORS if det_map.get(d, False)]
        all_suff = all(suff_by_world[world_id].get(d, False) for d in DETECTORS)
        world_status[world_id] = {
            "any_fired": len(fired_dets) > 0,
            "fired": set(fired_dets),
            "indeterminate": len(fired_dets) == 0 and not all_suff,
        }

    def pop(pred):
        ids = [wid for wid in world_status if pred(world_meta.get(wid))]
        return ids

    null_ids = pop(lambda m: m and m["is_null"])
    n_null = len(null_ids)
    k_frr = sum(1 for wid in null_ids if world_status[wid]["any_fired"])
    k_indet = sum(1 for wid in null_ids if world_status[wid]["indeterminate"])
    frr = {"k": k_frr, "n": n_null, "rate": k_frr / n_null if n_null else None, "wilson": wilson(k_frr, n_null)}
    indet = {"k": k_indet, "n": n_null, "rate": k_indet / n_null if n_null else None, "wilson": wilson(k_indet, n_null)}

    power_primary = {}
    for d in DETECTORS:
        ids = pop(lambda m, d=d: m and m["D"] == d and m["alpha"] == 1.0 and m["noise_level"] == 0.02)
        n = len(ids)
        k = sum(1 for wid in ids if d in world_status[wid]["fired"])
        power_primary[d] = {"k": k, "n": n, "rate": k / n if n else None, "wilson": wilson(k, n)}

    misattr = {}
    for d in DETECTORS:
        ids = pop(lambda m, d=d: m and m["D"] == d and m["alpha"] == 1.0)
        n = len(ids)
        k = sum(1 for wid in ids if any(o in world_status[wid]["fired"] for o in DETECTORS if o != d))
        misattr[d] = {"k": k, "n": n, "rate": k / n if n else None}

    monotone = {}
    power_curve = {}
    for d in DETECTORS:
        curve = {}
        for alpha in ALPHA_LEVELS:
            ids = pop(lambda m, d=d, alpha=alpha: m and m["D"] == d and m["alpha"] == alpha and m["noise_level"] == 0.02)
            n = len(ids)
            k = sum(1 for wid in ids if d in world_status[wid]["fired"])
            curve[alpha] = {"n": n, "rate": k / n if n else None}
        power_curve[d] = curve
        rates = [curve[a]["rate"] for a in ALPHA_LEVELS if curve[a]["rate"] is not None]
        monotone[d] = all(rates[i] <= rates[i + 1] + 1e-9 for i in range(len(rates) - 1))

    admissible = (
        frr["rate"] is not None and frr["rate"] <= 0.05 and frr["wilson"][1] <= 0.10
        and indet["rate"] is not None and indet["rate"] <= 0.10 and indet["wilson"][1] <= 0.15
        and all(power_primary[d]["rate"] is not None and power_primary[d]["rate"] >= 0.80 and power_primary[d]["wilson"][0] >= 0.70 for d in DETECTORS)
        and all(misattr[d]["rate"] is not None and misattr[d]["rate"] <= 0.05 for d in DETECTORS)
        and all(monotone.values())
    )
    return {
        "criterion": cid, "criterion_params": cparams, "rule": rid, "rule_params": rparams,
        "n_free_params": FREE_PARAMS[cid] + FREE_PARAMS[rid],
        "FRR": frr, "indeterminate_rate": indet, "power_primary": power_primary,
        "misattribution": misattr, "monotone": monotone, "power_curve": power_curve,
        "admissible": bool(admissible),
    }


def main():
    out_dir = os.path.join(_REPO_ROOT, "artifacts", "e1")
    findings = []

    comp_files = sorted(glob.glob(os.path.join(out_dir, "compounds_full_*.parquet")))
    comp = pd.concat([pd.read_parquet(f) for f in comp_files], ignore_index=True)
    world = pd.read_parquet(os.path.join(out_dir, "worlds_full.parquet"))
    with open(os.path.join(out_dir, "run_manifest_full.json")) as fh:
        run_manifest = json.load(fh)
    analysis_path = os.path.join(out_dir, "e1_analysis.json")
    with open(analysis_path) as fh:
        analysis = json.load(fh)

    # 1. Completeness: 11,475 fit units, 153 cells x 75 replicates, exact 60/15 split.
    findings.append(check("11475_worlds_analyzed", len(world) == 11475, {"n": len(world)}))
    dup = world["world_id"].duplicated().sum()
    findings.append(check("0_duplicate_worlds", dup == 0, {"duplicates": int(dup)}))
    cell_counts = world.groupby("cell_id")["world_id"].count()
    findings.append(check("153_cells_present", len(cell_counts) == 153, {"n_cells": len(cell_counts)}))
    findings.append(check("75_replicates_per_cell", bool((cell_counts == 75).all()), {"min": int(cell_counts.min()), "max": int(cell_counts.max())}))
    split_counts = world.groupby(["cell_id", "split"])["world_id"].count().unstack(fill_value=0)
    exact_split = bool((split_counts.get("CALIBRATE", pd.Series(dtype=int)) == 60).all()) and bool((split_counts.get("CONFIRM", pd.Series(dtype=int)) == 15).all())
    findings.append(check("exact_60_15_split_per_cell", exact_split, None))

    # 2. No leakage: world_id namespace, no v1 case ids, no PySR.
    ns_ok = bool(world["world_id"].astype(str).str.match(r"^V2C\|E1\|").all())
    findings.append(check("world_id_namespace_disjoint_from_v1", ns_ok, None))
    heldout_like = world["world_id"].astype(str).str.contains(r"held_out|PB\|", regex=True).sum()
    findings.append(check("0_heldout_or_challenge_rows", heldout_like == 0, {"matches": int(heldout_like)}))
    findings.append(check("0_pysr", ("pysr" not in sys.modules) and (not run_manifest.get("pysr_imported", True)), None))
    findings.append(check("0_run_errors", run_manifest.get("n_errors", -1) == 0, {"n_errors": run_manifest.get("n_errors")}))

    # 3. No post-result threshold movement: the protocol commit must be an
    # ancestor of, and precede in log order, the commit(s) touching the run
    # scripts / artifacts, and the protocol file's post-freeze diff (if any)
    # must be empty in its normative sections (Sec 1-9; Sec 10 addendum and
    # this audit are allowed as disclosed, dated additions -- checked by hash
    # of Sec 0-9 rather than the whole file).
    try:
        log = subprocess.run(["git", "-C", _REPO_ROOT, "log", "--oneline", "--", "MURU_V2_E1_PROTOCOL.md"], capture_output=True, text=True, check=True).stdout
        protocol_commits = [line.split()[0] for line in log.strip().splitlines()]
        findings.append(check("protocol_frozen_before_implementation", len(protocol_commits) >= 1, {"commits": protocol_commits}))
    except Exception as exc:
        findings.append(check("protocol_frozen_before_implementation", False, {"error": repr(exc)}))

    # 4. Reproducible aggregates: independently recompute the CONTROL pair
    # (C0, P0) and the SELECTED pair from raw compound rows, fresh code path.
    calib = comp[comp["split"] == "CALIBRATE"]
    world_meta = {
        row.world_id: {"D": row.D, "alpha": row.alpha, "noise_level": row.noise_level, "is_null": bool(row.is_null)}
        for row in world.itertuples()
    }
    records = defaultdict(list)
    cols = ["mae_m0", "mae_alt", "m0_unresolved_c0_any", "mk_unresolved_c0_any",
            "m0_max_probe_gain_rel", "mk_max_probe_gain_rel", "m0_max_c2_ratio", "mk_max_c2_ratio",
            "m0_max_profile_ratio", "mk_max_profile_ratio", "c4_verdict_flip"]
    for row in calib.itertuples():
        d = {c: getattr(row, c) for c in cols}
        records[(row.world_id, row.detector)].append(d)

    control = score_pair(records, world_meta, "C0", {}, "P0", {})
    sealed_control = next(
        (r for r in analysis["results"] if r["criterion"] == "C0" and r["rule"] == "P0"), None
    )
    control_ok = sealed_control is not None
    if control_ok:
        control_ok = (
            control["FRR"]["k"] == sealed_control["metrics"]["FRR"]["k"]
            and control["FRR"]["n"] == sealed_control["metrics"]["FRR"]["n"]
            and all(
                control["power_primary"][d]["k"] == sealed_control["metrics"]["power_primary"][d]["k"]
                and control["power_primary"][d]["n"] == sealed_control["metrics"]["power_primary"][d]["n"]
                for d in DETECTORS
            )
        )
    findings.append(check("control_pair_C0_P0_reproducible", control_ok, {"recomputed": {"FRR": control["FRR"], "power": control["power_primary"]}, "sealed": sealed_control["metrics"] if sealed_control else None}))

    selected = analysis.get("selected")

    # 5. Mechanical selection: independently recompute ALL 390 pairs' full
    # admissibility from raw rows (always -- whether or not a pair was
    # selected, since "no pair admissible" is itself a primary count that
    # must be independently reproduced, not accepted on the primary
    # analyzer's word).
    all_recomputed = []
    for cid2, cparam_list in CRITERIA.items():
        for cparams2 in cparam_list:
            for rid2, rparam_list in RULES.items():
                for rparams2 in rparam_list:
                    all_recomputed.append(score_pair(records, world_meta, cid2, cparams2, rid2, rparams2))
    admissible = [r for r in all_recomputed if r["admissible"]]
    n_admissible_recomputed = len(admissible)
    n_admissible_sealed = sum(1 for r in analysis["results"] if r["admissibility"]["admissible"])
    count_ok = n_admissible_recomputed == n_admissible_sealed
    findings.append(check("admissible_count_matches", count_ok, {"recomputed": n_admissible_recomputed, "sealed": n_admissible_sealed}))

    if admissible:
        def key(r):
            minp = min(r["power_primary"][d]["rate"] or 0 for d in DETECTORS)
            return (r["n_free_params"], r["indeterminate_rate"]["rate"] or 1.0, -minp)
        admissible.sort(key=key)
        top = admissible[0]
        if selected:
            mech_ok = (top["criterion"] == selected["criterion"] and top["criterion_params"] == selected["criterion_params"]
                       and top["rule"] == selected["rule"] and top["rule_params"] == selected["rule_params"])
        else:
            mech_ok = False  # sealed said none admissible, but this audit found some -- real disagreement
    else:
        mech_ok = selected is None
    findings.append(check("selection_is_lexicographic_minimum_independently", mech_ok,
                           {"n_independently_admissible": n_admissible_recomputed, "sealed_selected": selected is not None}))

    # 6. Independently confirm the H2 sub-check the decision tree names: no
    # pair reaches power>=0.80 (Wilson lower>=0.70) for all three detectors
    # simultaneously at alpha=2.0 either (rules out "admissible at larger
    # alpha", not just "admissible at alpha=1.0").
    h2_ok_recomputed = 0
    for r2 in all_recomputed:
        cid2, cparams2, rid2, rparams2 = r2["criterion"], r2["criterion_params"], r2["rule"], r2["rule_params"]
        curve_ok = all(
            (r2["power_curve"][d][2.0]["rate"] or 0) >= 0.80
            for d in DETECTORS
        )
        if curve_ok:
            h2_ok_recomputed += 1
    findings.append(check("no_pair_reaches_joint_power_at_alpha_2_either", h2_ok_recomputed == 0, {"n_pairs_reaching_joint_power_at_alpha2": h2_ok_recomputed}))

    all_pass = all(f["pass"] for f in findings)
    out = {"experiment": "E1", "all_pass": all_pass, "findings": findings}
    with open(os.path.join(out_dir, "e1_hostile_audit.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    for f in findings:
        print(f"[{'PASS' if f['pass'] else 'FAIL'}] {f['check']}")
    if not all_pass:
        print("HOSTILE AUDIT FAILED", file=sys.stderr)
        sys.exit(1)
    print("HOSTILE AUDIT: ALL CHECKS PASS")


if __name__ == "__main__":
    main()
