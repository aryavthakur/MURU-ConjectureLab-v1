"""E0 required analysis: rates by cell, interaction effect, effect sizes with
uncertainty, and the causal conclusion via the frozen MURU_V2_E0_PROTOCOL.md
Sec 4 decision table only.

Reads artifacts/e0/e0_worlds.csv, e0_fits.parquet, e0_probes.parquet
(produced by e0_run.py --full). Writes artifacts/e0/e0_analysis.json and
artifacts/e0/e0_cell_metrics.csv.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e0_common as e0  # noqa: E402

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e0")

Z_975 = 1.959963984540054  # scipy.stats.norm.ppf(0.975), transcribed as a literal to avoid a scipy dependency here


def wilson_ci(successes: int, n: int, z: float = Z_975) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, center - margin), min(1.0, center + margin)


def bootstrap_median_ci(values: np.ndarray, n_resamples: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    med = float(np.median(values))
    if values.size == 1:
        return (med, med, med)
    idx = rng.integers(0, values.size, size=(n_resamples, values.size))
    boots = np.median(values[idx], axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return med, float(lo), float(hi)


def cell_metrics(worlds: pd.DataFrame, fits: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cell_id, wg in worlds.groupby("cell_id"):
        n = len(wg)
        fg = fits[fits["cell_id"] == cell_id]
        n_fits = len(fg)
        contact_n = int(fg["boundary_contact"].sum())
        unresolved_n = int(fg["unresolved_boundary"].sum())
        bl_p, bl_lo, bl_hi = wilson_ci(int(wg["boundary_limited"].sum()), n)
        fm0_p, fm0_lo, fm0_hi = wilson_ci(int(wg["false_m0_rejection"].sum()), n)
        contact_p, contact_lo, contact_hi = wilson_ci(contact_n, n_fits)
        unresolved_p, unresolved_lo, unresolved_hi = wilson_ci(unresolved_n, n_fits)
        rows.append(
            {
                "cell_id": cell_id,
                "c_gen_level": wg["c_gen_level"].iloc[0],
                "mu_ceil_level": wg["mu_ceil_level"].iloc[0],
                "n_worlds": n,
                "n_fits": n_fits,
                "contact_rate": contact_p,
                "contact_rate_wilson_lo": contact_lo,
                "contact_rate_wilson_hi": contact_hi,
                "unresolved_rate": unresolved_p,
                "unresolved_rate_wilson_lo": unresolved_lo,
                "unresolved_rate_wilson_hi": unresolved_hi,
                "boundary_limited_rate": bl_p,
                "boundary_limited_rate_wilson_lo": bl_lo,
                "boundary_limited_rate_wilson_hi": bl_hi,
                "false_m0_rejection_rate": fm0_p,
                "false_m0_rejection_rate_wilson_lo": fm0_lo,
                "false_m0_rejection_rate_wilson_hi": fm0_hi,
                "evaluable_M3_mean": float(wg["evaluable_m3"].mean()),
                "evaluable_M3_median": float(wg["evaluable_m3"].median()),
                "mu_max_at_clip_share_mean": float(wg["mu_max_at_clip_share"].mean()),
                "pin_at_ceiling_share_mean": float(wg["pin_at_ceiling_share"].dropna().mean()) if wg["pin_at_ceiling_share"].notna().any() else None,
            }
        )
    return pd.DataFrame(rows).sort_values("cell_id").reset_index(drop=True)


def interaction_decomposition(cell_df: pd.DataFrame, metric: str = "boundary_limited_rate") -> dict:
    """Saturated 3x3 cell-mean decomposition: grand mean + row + col + residual."""
    pivot = cell_df.pivot(index="c_gen_level", columns="mu_ceil_level", values=metric)
    pivot = pivot.reindex(index=list(e0.C_GEN_LEVELS.keys()), columns=list(e0.MU_CEIL_LEVELS.keys()))
    grand_mean = float(pivot.values.mean())
    row_effect = (pivot.mean(axis=1) - grand_mean).to_dict()
    col_effect = (pivot.mean(axis=0) - grand_mean).to_dict()
    residual = pivot.copy()
    for r in pivot.index:
        for c in pivot.columns:
            residual.loc[r, c] = pivot.loc[r, c] - grand_mean - row_effect[r] - col_effect[c]
    row_ss = float(sum(v * v for v in row_effect.values()) * len(col_effect))
    col_ss = float(sum(v * v for v in col_effect.values()) * len(row_effect))
    interaction_ss = float((residual.values ** 2).sum())
    total_ss = row_ss + col_ss + interaction_ss
    return {
        "metric": metric,
        "grand_mean": grand_mean,
        "c_gen_main_effect": {k: float(v) for k, v in row_effect.items()},
        "mu_ceil_main_effect": {k: float(v) for k, v in col_effect.items()},
        "interaction_residual_by_cell": {f"{r}_{c}": float(residual.loc[r, c]) for r in pivot.index for c in pivot.columns},
        "c_gen_main_effect_range": float(max(row_effect.values()) - min(row_effect.values())),
        "mu_ceil_main_effect_range": float(max(col_effect.values()) - min(col_effect.values())),
        "interaction_effect_magnitude": float(np.sqrt((residual.values ** 2).mean())),
        "sum_of_squares": {"c_gen_main": row_ss, "mu_ceil_main": col_ss, "interaction": interaction_ss, "total": total_ss},
        "variance_share": {
            "c_gen_main": row_ss / total_ss if total_ss > 0 else None,
            "mu_ceil_main": col_ss / total_ss if total_ss > 0 else None,
            "interaction": interaction_ss / total_ss if total_ss > 0 else None,
        },
    }


def decoupling_contrast(worlds: pd.DataFrame) -> dict:
    control = worlds[worlds["cell_id"] == e0.CONTROL_CELL]
    decoupled = worlds[worlds["cell_id"] == e0.DECOUPLED_CELL]
    c_p, c_lo, c_hi = wilson_ci(int(control["boundary_limited"].sum()), len(control))
    d_p, d_lo, d_hi = wilson_ci(int(decoupled["boundary_limited"].sum()), len(decoupled))
    drop = c_p - d_p
    se_diff = float(np.sqrt((c_hi - c_lo) ** 2 / (4 * Z_975 ** 2) + (d_hi - d_lo) ** 2 / (4 * Z_975 ** 2)))
    return {
        "control_cell": e0.CONTROL_CELL,
        "decoupled_cell": e0.DECOUPLED_CELL,
        "control_boundary_limited_rate": c_p,
        "control_wilson_ci": [c_lo, c_hi],
        "decoupled_boundary_limited_rate": d_p,
        "decoupled_wilson_ci": [d_lo, d_hi],
        "n_per_cell": len(control),
        "absolute_drop": drop,
        "absolute_drop_approx_95ci": [drop - Z_975 * se_diff, drop + Z_975 * se_diff],
    }


def apply_decision_tree(drop: float, decomposition: dict) -> dict:
    """MURU_V2_E0_PROTOCOL.md Sec 4, mechanically, no post-result addition."""
    row_range = decomposition["c_gen_main_effect_range"]
    col_range = decomposition["mu_ceil_main_effect_range"]
    interaction_mag = decomposition["interaction_effect_magnitude"]

    if drop > 0.50:
        committed = "H_clip confirmed"
        if row_range > col_range and row_range > interaction_mag:
            category = "GENERATOR_CLIP_DOMINANT"
        elif col_range > row_range and col_range > interaction_mag:
            category = "FITTER_RANGE_DOMINANT"
        else:
            category = "COUPLING_INTERACTION_DOMINANT"
    elif drop >= 0.10:
        committed = "H_clip and H_alias both contribute"
        category = "COUPLING_INTERACTION_DOMINANT"
    else:
        committed = "H_null; MU_CEIL exonerated"
        category = "NEITHER_SUFFICIENT"

    return {
        "decoupling_drop": drop,
        "committed_row": committed,
        "terminal_category": category,
        "decomposition_used": {
            "c_gen_main_effect_range": row_range,
            "mu_ceil_main_effect_range": col_range,
            "interaction_effect_magnitude": interaction_mag,
        },
    }


def abort_gate_check(worlds: pd.DataFrame, fits: pd.DataFrame) -> dict:
    control = worlds[worlds["cell_id"] == e0.CONTROL_CELL]
    cfits = fits[fits["cell_id"] == e0.CONTROL_CELL]
    contact_rate = float(cfits["boundary_contact"].mean())
    mu_max_share = float(control["mu_max_at_clip_share"].mean())
    bl_rate = float(control["boundary_limited"].mean())
    checks = {
        "contact_rate_gt_0": {"value": contact_rate, "pass": contact_rate > 0},
        "mu_max_at_clip_share_in_band": {"value": mu_max_share, "band": [0.20, 0.90], "pass": 0.20 <= mu_max_share <= 0.90},
        "boundary_limited_rate_in_band": {"value": bl_rate, "band": [0.30, 0.90], "pass": 0.30 <= bl_rate <= 0.90},
    }
    checks["all_pass"] = all(c["pass"] for c in checks.values() if isinstance(c, dict))
    return checks


def main():
    worlds = pd.read_csv(os.path.join(ARTIFACT_DIR, "e0_worlds.csv"))
    fits = pd.read_parquet(os.path.join(ARTIFACT_DIR, "e0_fits.parquet"))
    probes = pd.read_parquet(os.path.join(ARTIFACT_DIR, "e0_probes.parquet"))

    cell_df = cell_metrics(worlds, fits)
    cell_df.to_csv(os.path.join(ARTIFACT_DIR, "e0_cell_metrics.csv"), index=False)

    decomposition = interaction_decomposition(cell_df, metric="boundary_limited_rate")
    contrast = decoupling_contrast(worlds)
    decision = apply_decision_tree(contrast["absolute_drop"], decomposition)
    abort_gate = abort_gate_check(worlds, fits)

    probe_gain = probes["probe_gain_rel"].dropna().to_numpy()
    probe_median, probe_lo, probe_hi = bootstrap_median_ci(probe_gain)

    overall_fm0 = wilson_ci(int(worlds["false_m0_rejection"].sum()), len(worlds))

    out = {
        "experiment": "E0",
        "name": "A1_ADMISSIBLE_RANGE_PROVENANCE",
        "n_worlds": len(worlds),
        "n_fit_records": len(fits),
        "n_probe_records": len(probes),
        "abort_gate": abort_gate,
        "cell_metrics": json.loads(cell_df.to_json(orient="records")),
        "interaction_decomposition_boundary_limited_rate": decomposition,
        "decoupling_contrast": contrast,
        "causal_decision": decision,
        "probe_gain_rel_overall": {"median": probe_median, "bootstrap_95ci": [probe_lo, probe_hi], "n_triggering_probes": int(probe_gain.size)},
        "false_m0_rejection_rate_overall": {"rate": overall_fm0[0], "wilson_ci": [overall_fm0[1], overall_fm0[2]]},
    }
    with open(os.path.join(ARTIFACT_DIR, "e0_analysis.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)

    print(json.dumps({"abort_gate": abort_gate, "decoupling_contrast": contrast, "causal_decision": decision}, indent=2, default=str))


if __name__ == "__main__":
    main()
