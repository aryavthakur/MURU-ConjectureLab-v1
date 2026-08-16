"""E1 analysis: admissibility grid, lexicographic selection, CONFIRM check.

Pure post-hoc scoring of the persisted compound table -- no refitting.
MURU_V2_E1_PROTOCOL.md Sec 6-7.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS_DIR)
import e1_rules as e1r  # noqa: E402

ALPHA_LEVELS = (0.25, 0.5, 1.0, 2.0)
DETECTORS = ("M1", "M2", "M3")
WIN_RATIOS = (0.80, 0.90, 0.95, 0.98)
DEFAULT_MIN_EVALUABLE = e1r.DEFAULT_MIN_EVALUABLE


def wilson_interval(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    lo = (centre - adj) / denom
    hi = (centre + adj) / denom
    return max(0.0, lo), min(1.0, hi)


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------


def load_tables(out_dir: str, label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    comp_files = sorted(glob.glob(os.path.join(out_dir, f"compounds_{label}_*.parquet")))
    if not comp_files:
        comp_files = sorted(glob.glob(os.path.join(out_dir, f"compounds_{label}_*.csv")))
        comp = pd.concat([pd.read_csv(f) for f in comp_files], ignore_index=True)
    else:
        comp = pd.concat([pd.read_parquet(f) for f in comp_files], ignore_index=True)
    world_path = os.path.join(out_dir, f"worlds_{label}.parquet")
    if os.path.exists(world_path):
        world = pd.read_parquet(world_path)
    else:
        world = pd.read_csv(world_path.replace(".parquet", ".csv"))
    return comp, world


def precompute_win_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    valid = df["mae_m0"].notna() & df["mae_alt"].notna() & (df["mae_m0"] > 0)
    for ratio in WIN_RATIOS:
        col = f"win_r{int(ratio*100)}"
        df[col] = valid & (df["mae_alt"] <= ratio * df["mae_m0"])
    df["rel_reduction"] = np.where(valid, (df["mae_m0"] - df["mae_alt"]) / df["mae_m0"], np.nan)
    df["_mae_ok"] = df["mae_m0"].notna() & df["mae_alt"].notna()
    return df


# --------------------------------------------------------------------------
# Per-criterion case-level aggregation
# --------------------------------------------------------------------------


def case_stats_for_criterion(df: pd.DataFrame, cid: str, cparams: dict) -> pd.DataFrame:
    """One row per (world_id, detector): evaluable count, win counts per ratio,
    median relative reduction -- everything every rule needs."""
    unresolved = e1r.apply_criterion(df, cid, cparams)
    evaluable = df["_mae_ok"] & ~unresolved
    work = pd.DataFrame({"world_id": df["world_id"], "detector": df["detector"], "evaluable": evaluable})
    for ratio in WIN_RATIOS:
        col = f"win_r{int(ratio*100)}"
        work[col] = df[col] & evaluable
    work["rel_reduction"] = df["rel_reduction"].where(evaluable)

    g = work.groupby(["world_id", "detector"], sort=False)
    out = g["evaluable"].sum().rename("evaluable_count").to_frame()
    for ratio in WIN_RATIOS:
        col = f"win_r{int(ratio*100)}"
        out[f"wins_{int(ratio*100)}"] = g[col].sum()
    out["median_rel_reduction"] = g["rel_reduction"].median()
    return out.reset_index()


def apply_rules(case_stats: pd.DataFrame) -> pd.DataFrame:
    """Adds one boolean column per rule instance: fired."""
    out = case_stats.copy()
    ev = out["evaluable_count"]
    sufficient = ev >= DEFAULT_MIN_EVALUABLE
    out["evaluable_sufficient"] = sufficient

    # P0
    out["P0__"] = sufficient & (out["wins_90"] >= 20)
    # P1: ratio x win count grid (ratio already baked into wins_{ratio} columns)
    for ratio in (0.80, 0.90, 0.95, 0.98):
        wcol = f"wins_{int(ratio*100)}"
        for w in (15, 18, 20, 24):
            out[f"P1__ratio={ratio}_w={w}"] = sufficient & (out[wcol] >= w)
    # P2: sign test
    for q in (0.05, 0.01, 0.001):
        tail = out.apply(lambda r: e1r.directional_null_tail(int(r["wins_90"]), int(r["evaluable_count"])) if r["evaluable_count"] > 0 else 1.0, axis=1)
        out[f"P2__q={q}"] = sufficient & (tail <= q)
    # P3: conjunction
    frac90 = out["wins_90"] / out["evaluable_count"].replace(0, np.nan)
    for m in (0.05, 0.10):
        for f in (0.5, 0.6, 0.67):
            out[f"P3__m={m}_f={f}"] = sufficient & (out["median_rel_reduction"] >= m) & (frac90 >= f)
    return out


def rule_column_name(rid: str, params: dict) -> str:
    if rid == "P0":
        return "P0__"
    if rid == "P1":
        return f"P1__ratio={params['ratio']}_w={params['w']}"
    if rid == "P2":
        return f"P2__q={params['q']}"
    if rid == "P3":
        return f"P3__m={params['m']}_f={params['f']}"
    raise ValueError(rid)


# --------------------------------------------------------------------------
# World-level status for one (criterion, rule) pair
# --------------------------------------------------------------------------


def world_level_status(fired_df: pd.DataFrame, rule_col: str) -> pd.DataFrame:
    """One row per world_id: fired_detectors (frozenset), any_fired, indeterminate."""
    piv_fired = fired_df.pivot(index="world_id", columns="detector", values=rule_col)
    piv_suff = fired_df.pivot(index="world_id", columns="detector", values="evaluable_sufficient")
    for d in DETECTORS:
        if d not in piv_fired.columns:
            piv_fired[d] = False
        if d not in piv_suff.columns:
            piv_suff[d] = False
    fired_mask = piv_fired[list(DETECTORS)].fillna(False)
    suff_mask = piv_suff[list(DETECTORS)].fillna(False)
    n_fired = fired_mask.sum(axis=1)
    all_sufficient = suff_mask.all(axis=1)
    out = pd.DataFrame(index=piv_fired.index)
    out["any_fired"] = n_fired > 0
    out["n_fired"] = n_fired
    out["indeterminate"] = (~out["any_fired"]) & (~all_sufficient)
    for d in DETECTORS:
        out[f"fired_{d}"] = fired_mask[d]
    return out.reset_index()


# --------------------------------------------------------------------------
# Metrics for one (criterion, rule) pair, given world_status joined to world meta
# --------------------------------------------------------------------------


def compute_metrics(status: pd.DataFrame, world_meta: pd.DataFrame) -> dict:
    df = status.merge(world_meta, on="world_id", how="left")
    metrics: dict = {}

    # FRR + indeterminate_rate: pooled over all null worlds (all noise, all mu_ceil)
    null_df = df[df["is_null"]]
    n_null = len(null_df)
    k_frr = int(null_df["any_fired"].sum())
    k_indet = int(null_df["indeterminate"].sum())
    metrics["FRR"] = {"k": k_frr, "n": n_null, "rate": k_frr / n_null if n_null else None, "wilson": wilson_interval(k_frr, n_null)}
    metrics["indeterminate_rate"] = {"k": k_indet, "n": n_null, "rate": k_indet / n_null if n_null else None, "wilson": wilson_interval(k_indet, n_null)}

    # power_D at alpha=1.0, noise=0.02, pooled over mu_ceil
    power_primary = {}
    for d in DETECTORS:
        sub = df[(df["D"] == d) & (df["alpha"] == 1.0) & (df["noise_level"] == 0.02)]
        n = len(sub)
        k = int(sub[f"fired_{d}"].sum())
        power_primary[d] = {"k": k, "n": n, "rate": k / n if n else None, "wilson": wilson_interval(k, n)}
    metrics["power_primary"] = power_primary

    # misattribution at alpha=1.0, pooled over mu_ceil and noise, standalone D only
    misattr = {}
    for d in DETECTORS:
        sub = df[(df["D"] == d) & (df["alpha"] == 1.0)]
        n = len(sub)
        wrong = np.zeros(len(sub), dtype=bool)
        for other in DETECTORS:
            if other != d:
                wrong = wrong | sub[f"fired_{other}"].to_numpy()
        k = int(wrong.sum())
        misattr[d] = {"k": k, "n": n, "rate": k / n if n else None, "wilson": wilson_interval(k, n)}
    metrics["misattribution"] = misattr

    # power_D(alpha) full ladder (noise=0.02, pooled mu_ceil) for alpha_star + monotonicity
    power_curve = {}
    for d in DETECTORS:
        curve = {}
        for alpha in ALPHA_LEVELS:
            sub = df[(df["D"] == d) & (df["alpha"] == alpha) & (df["noise_level"] == 0.02)]
            n = len(sub)
            k = int(sub[f"fired_{d}"].sum())
            lo, hi = wilson_interval(k, n)
            curve[alpha] = {"k": k, "n": n, "rate": k / n if n else None, "wilson_lower": lo, "wilson_upper": hi}
        power_curve[d] = curve
    metrics["power_curve"] = power_curve

    # alpha_star_D: smallest alpha with rate>=0.80 and wilson_lower>=0.70
    alpha_star = {}
    monotone = {}
    for d in DETECTORS:
        curve = power_curve[d]
        star = None
        for alpha in ALPHA_LEVELS:
            c = curve[alpha]
            if c["rate"] is not None and c["rate"] >= 0.80 and c["wilson_lower"] >= 0.70:
                star = alpha
                break
        alpha_star[d] = star
        rates = [curve[a]["rate"] for a in ALPHA_LEVELS if curve[a]["rate"] is not None]
        monotone[d] = all(rates[i] <= rates[i + 1] + 1e-9 for i in range(len(rates) - 1))
    metrics["alpha_star"] = alpha_star
    metrics["monotone"] = monotone

    # combined family (M1M2M3): "correct" = any of M1/M2/M3 fires
    combined_curve = {}
    for alpha in ALPHA_LEVELS:
        sub = df[(df["D"] == "M1M2M3") & (df["alpha"] == alpha) & (df["noise_level"] == 0.02)]
        n = len(sub)
        k = int(sub["any_fired"].sum())
        lo, hi = wilson_interval(k, n)
        combined_curve[alpha] = {"k": k, "n": n, "rate": k / n if n else None, "wilson_lower": lo, "wilson_upper": hi}
    metrics["combined_power_curve"] = combined_curve

    return metrics


def check_admissibility(metrics: dict) -> dict:
    checks = {}
    frr = metrics["FRR"]
    checks["frr"] = frr["rate"] is not None and frr["rate"] <= 0.05 and frr["wilson"][1] <= 0.10
    indet = metrics["indeterminate_rate"]
    checks["indeterminate"] = indet["rate"] is not None and indet["rate"] <= 0.10 and indet["wilson"][1] <= 0.15
    power_ok = True
    for d in DETECTORS:
        p = metrics["power_primary"][d]
        if p["rate"] is None or p["rate"] < 0.80 or p["wilson"][0] < 0.70:
            power_ok = False
    checks["power"] = power_ok
    misattr_ok = True
    for d in DETECTORS:
        m = metrics["misattribution"][d]
        if m["rate"] is None or m["rate"] > 0.05:
            misattr_ok = False
    checks["misattribution"] = misattr_ok
    checks["monotone"] = all(metrics["monotone"].values())
    checks["admissible"] = all(checks.values())
    return checks


# --------------------------------------------------------------------------
# Full grid
# --------------------------------------------------------------------------


def run_grid(df: pd.DataFrame, world_meta: pd.DataFrame) -> list[dict]:
    results = []
    for cid, cparams in e1r.criterion_instances():
        case_stats = case_stats_for_criterion(df, cid, cparams)
        fired_df = apply_rules(case_stats)
        for rid, rparams in e1r.rule_instances():
            col = rule_column_name(rid, rparams)
            status = world_level_status(fired_df, col)
            metrics = compute_metrics(status, world_meta)
            adm = check_admissibility(metrics)
            results.append({
                "criterion": cid, "criterion_params": cparams,
                "rule": rid, "rule_params": rparams,
                "n_free_params": e1r.pair_free_params(cid, rid),
                "ladder_index": e1r.ladder_index(cid, cparams, rid, rparams),
                "metrics": metrics, "admissibility": adm,
            })
    return results


def select_pair(results: list[dict]) -> dict | None:
    admissible = [r for r in results if r["admissibility"]["admissible"]]
    if not admissible:
        return None

    def sort_key(r):
        min_power = min(r["metrics"]["power_primary"][d]["rate"] or 0 for d in DETECTORS)
        return (
            r["n_free_params"],
            r["metrics"]["indeterminate_rate"]["rate"] or 1.0,
            -min_power,
            r["ladder_index"],
        )

    admissible.sort(key=sort_key)
    return admissible[0]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="artifacts/e1")
    ap.add_argument("--label", default="full")
    ap.add_argument("--save", default=None)
    args = ap.parse_args()

    comp, world = load_tables(args.out_dir, args.label)
    comp = precompute_win_columns(comp)
    calib = comp[comp["split"] == "CALIBRATE"]
    calib_meta = world[world["split"] == "CALIBRATE"][["world_id", "D", "alpha", "noise_level", "mu_ceil_level", "is_null"]]

    print(f"compound rows: {len(comp)}, CALIBRATE rows: {len(calib)}, worlds: {len(world)}")
    results = run_grid(calib, calib_meta)
    print(f"scored {len(results)} (criterion, rule) pairs")
    n_admissible = sum(1 for r in results if r["admissibility"]["admissible"])
    print(f"admissible: {n_admissible}")

    selected = select_pair(results)
    if selected:
        print("SELECTED:", selected["criterion"], selected["criterion_params"], selected["rule"], selected["rule_params"])
    else:
        print("NO PAIR ADMISSIBLE")

    if args.save:
        with open(args.save, "w") as fh:
            json.dump({"results": results, "selected": selected}, fh, indent=2, default=str)
        print("saved to", args.save)


if __name__ == "__main__":
    main()
