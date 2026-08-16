"""Aggregate the 10,000 E3 per-world records into every required output.

Required outputs (per the E3 execution goal):
  1. oracle family-recovery rate overall
  2. recovery by family
  3. recovery by coefficient/effect-size regime
  4. confusion matrix
  5. truth-vs-mass-only separation
  6. truth-vs-best-wrong-family separation
  7. identifiability curves
  8. special analysis of F02/F03/F09/F18
  9. F18 exponential distinguishability under intended geometry

Plus the preregistered per-cell decision-tree classification
(IDENTIFIABLE / MARGINAL / WEAKLY_IDENTIFIABLE / STUDY_INVALID), computed
separately -- never combined -- for the BIC and validation-R2 selection
criteria, exactly as MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md section 3.7
declares in advance of any result.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "e3_identifiability"
WORLDS_PATH = RESULTS_DIR / "e3_worlds.jsonl"

MODEL_IDS = ("M_mass", "M_affine", "M_sat", "M_exp", "M_inter")
FAMILY_TO_MODEL = {
    "mass_power": "M_mass",
    "mass_affine_descriptor": "M_affine",
    "mass_saturating_descriptor": "M_sat",
    "mass_exponential_descriptor": "M_exp",
    "mass_interaction": "M_inter",
}
MODEL_TO_FAMILY = {v: k for k, v in FAMILY_TO_MODEL.items()}

#: MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md section 3.7, stated before any world was run.
IDENTIFIABLE_THRESHOLD = 0.80
MARGINAL_THRESHOLD = 0.50
STUDY_INVALID_THRESHOLD = 0.10

#: v1's actual observed oracle recovery for these four families, from the frozen
#: evidence base (MURU_V1_ROOT_CAUSE_RANKING.md), reused here read-only for
#: side-by-side comparison against E3's oracle ceiling. Not derived by E3, not
#: modified by E3, and not used to select any E3 parameter.
V1_OBSERVED_RECOVERY = {
    "F02": {"family": "mass_affine_descriptor", "noise_sd": 0.0295, "correct": 3, "total": 12},
    "F03": {"family": "mass_affine_descriptor", "noise_sd": 0.06, "correct": 1, "total": 12},
    "F09": {"family": "mass_saturating_descriptor", "noise_sd": 0.02, "correct": 0, "total": 12},
    "F18": {"family": "mass_exponential_descriptor", "noise_sd": 0.02, "correct": 0, "total": 12},
}

#: The frozen benchmark's own planted coefficient support (generator.py:
#: rng.uniform(0.25, 0.55)) and default energy grid.
FROZEN_C_SUPPORT = (0.25, 0.40, 0.55)
FROZEN_GRID = 6
FROZEN_NOISE_DEFAULT = 0.02


def wilson_lower(k: int, n: int, z: float = 1.959963984540054) -> float:
    if n == 0:
        return float("nan")
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre - adj) / denom)


def wilson_upper(k: int, n: int, z: float = 1.959963984540054) -> float:
    if n == 0:
        return float("nan")
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre + adj) / denom)


def classify_cell(rate: float) -> str:
    if rate >= IDENTIFIABLE_THRESHOLD:
        return "IDENTIFIABLE"
    if rate >= MARGINAL_THRESHOLD:
        return "MARGINAL"
    return "WEAKLY_IDENTIFIABLE"


def load_worlds() -> pd.DataFrame:
    records = []
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            row = {
                "world_id": r["world_id"],
                "cell_id": r["cell_id"],
                "family": r["family"],
                "c": r["c"],
                "noise_sd": r["noise_sd"],
                "grid_points": r["grid_points"],
                "replicate": r["replicate"],
                "status": r["status"],
            }
            if r["status"] == "OK":
                row.update({
                    "true_model_id": r["true_model_id"],
                    "rival_model_id": r["rival_model_id"],
                    "bic_selected_model": r["bic_selected_model"],
                    "val_r2_selected_model": r["val_r2_selected_model"],
                    "oracle_correct_bic": r["oracle_correct_bic"],
                    "oracle_correct_r2": r["oracle_correct_r2"],
                    "is_control": r["is_control"],
                    "false_structure_bic": r["false_structure_bic"],
                    "false_structure_r2": r["false_structure_r2"],
                    "delta_r2_vs_mass": r["delta_r2_vs_mass"],
                    "delta_r2_vs_rival": r["delta_r2_vs_rival"],
                    "c_hat_over_se": r["c_hat_over_se"],
                    "lrt_p_true_vs_mass": r["lrt_p_true_vs_mass"],
                    "lrt_p_true_vs_rival": r["lrt_p_true_vs_rival"],
                })
                for mid in MODEL_IDS:
                    row[f"r2_val__{mid}"] = r["models"][mid]["r2_val"]
                    row[f"bic__{mid}"] = r["models"][mid]["bic"]
                    row[f"converged__{mid}"] = r["models"][mid]["converged"]
                true_r2 = row[f"r2_val__{row['true_model_id']}"]
                wrong_r2s = [row[f"r2_val__{m}"] for m in MODEL_IDS if m != row["true_model_id"] and row[f"r2_val__{m}"] is not None]
                row["best_wrong_r2"] = max(wrong_r2s) if wrong_r2s else None
                row["best_wrong_model"] = None
                if wrong_r2s:
                    best = max(
                        ((row[f"r2_val__{m}"], m) for m in MODEL_IDS if m != row["true_model_id"] and row[f"r2_val__{m}"] is not None),
                    )
                    row["best_wrong_model"] = best[1]
                row["delta_r2_vs_best_wrong"] = (
                    None if true_r2 is None or row["best_wrong_r2"] is None else true_r2 - row["best_wrong_r2"]
                )
            records.append(row)
    return pd.DataFrame.from_records(records)


def rate_table(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if not group_cols:
        out = pd.DataFrame([{
            "n": len(df),
            "bic_correct": int(df["oracle_correct_bic"].sum()),
            "r2_correct": int(df["oracle_correct_r2"].sum()),
        }])
    else:
        g = df.groupby(group_cols, dropna=False)
        out = g.agg(
            n=("world_id", "count"),
            bic_correct=("oracle_correct_bic", "sum"),
            r2_correct=("oracle_correct_r2", "sum"),
        ).reset_index()
    out["bic_rate"] = out["bic_correct"] / out["n"]
    out["r2_rate"] = out["r2_correct"] / out["n"]
    out["bic_wilson_lower"] = out.apply(lambda row: wilson_lower(int(row["bic_correct"]), int(row["n"])), axis=1)
    out["r2_wilson_lower"] = out.apply(lambda row: wilson_lower(int(row["r2_correct"]), int(row["n"])), axis=1)
    out["bic_classification"] = out["bic_rate"].apply(classify_cell)
    out["r2_classification"] = out["r2_rate"].apply(classify_cell)
    return out


def build_aggregate() -> dict:
    df = load_worlds()
    assert (df["status"] == "OK").all(), f"non-OK worlds present: {(df['status'] != 'OK').sum()}"
    assert len(df) == 10_000, len(df)

    descriptor_df = df[df["family"] != "mass_power"].copy()
    control_df = df[df["family"] == "mass_power"].copy()

    # -----------------------------------------------------------------
    # STUDY_INVALID gate, computed first, on the full 2,000-world control set.
    # -----------------------------------------------------------------
    n_control = len(control_df)
    false_structure_bic_rate = float(control_df["false_structure_bic"].mean())
    false_structure_r2_rate = float(control_df["false_structure_r2"].mean())
    k_bic = int(control_df["false_structure_bic"].sum())
    k_r2 = int(control_df["false_structure_r2"].sum())
    study_validity = {
        "n_control_worlds": n_control,
        "bic_criterion": {
            "false_structure_oracle_rate": false_structure_bic_rate,
            "wilson_upper": wilson_upper(k_bic, n_control),
            "count": k_bic,
            "study_invalid": false_structure_bic_rate > STUDY_INVALID_THRESHOLD,
        },
        "r2_criterion": {
            "false_structure_oracle_rate": false_structure_r2_rate,
            "wilson_upper": wilson_upper(k_r2, n_control),
            "count": k_r2,
            "study_invalid": false_structure_r2_rate > STUDY_INVALID_THRESHOLD,
        },
    }
    # Breakdown by noise/grid, diagnostic only -- the gate itself is the pooled figure above.
    control_breakdown = rate_table(
        control_df.assign(
            oracle_correct_bic=lambda d: ~d["false_structure_bic"],
            oracle_correct_r2=lambda d: ~d["false_structure_r2"],
        ),
        ["noise_sd", "grid_points"],
    )

    # -----------------------------------------------------------------
    # 1. Overall oracle family-recovery rate
    # -----------------------------------------------------------------
    overall_all5 = rate_table(df, [])  # single row
    overall_descriptor_only = rate_table(descriptor_df, [])

    # -----------------------------------------------------------------
    # 2. Recovery by family
    # -----------------------------------------------------------------
    by_family = rate_table(df, ["family"])

    # -----------------------------------------------------------------
    # 3. Recovery by coefficient regime
    # -----------------------------------------------------------------
    by_coefficient_pooled = rate_table(descriptor_df, ["c"])
    by_family_and_c = rate_table(descriptor_df, ["family", "c"])

    # Every one of the 200 preregistered (family, c, noise, grid) cells,
    # classified per the frozen decision criterion. The control family's
    # "correctness" is redefined as NOT selecting a descriptor model, so its
    # 40 cells are classified on the same IDENTIFIABLE/MARGINAL/WEAKLY scale
    # applied to specificity rather than recovery.
    full_cell_rows = rate_table(descriptor_df, ["family", "c", "noise_sd", "grid_points"]).to_dict(orient="records")
    control_cell_rows = rate_table(
        control_df.assign(
            oracle_correct_bic=lambda d: ~d["false_structure_bic"],
            oracle_correct_r2=lambda d: ~d["false_structure_r2"],
        ),
        ["family", "c", "noise_sd", "grid_points"],
    ).to_dict(orient="records")
    for row in control_cell_rows:
        row["bic_classification"] = "SPECIFICITY_" + row["bic_classification"]
        row["r2_classification"] = "SPECIFICITY_" + row["r2_classification"]
    full_cell_classification = full_cell_rows + control_cell_rows
    assert len(full_cell_classification) == 200, len(full_cell_classification)

    # c_star per (family, noise, grid)
    c_star_rows = []
    for (family, noise_sd, grid_points), sub in descriptor_df.groupby(["family", "noise_sd", "grid_points"]):
        curve = rate_table(sub, ["c"]).sort_values("c")
        for criterion in ("bic", "r2"):
            reached = curve[curve[f"{criterion}_rate"] >= IDENTIFIABLE_THRESHOLD]
            c_star = float(reached["c"].min()) if len(reached) else None
            c_star_rows.append({
                "family": family, "noise_sd": noise_sd, "grid_points": grid_points,
                "criterion": criterion, "c_star": c_star,
                "c_star_above_ladder": c_star is None,
            })
    c_star_table = pd.DataFrame(c_star_rows)

    # -----------------------------------------------------------------
    # 4. Confusion matrices (true family -> selected family)
    # -----------------------------------------------------------------
    def confusion(sub: pd.DataFrame, selection_col: str) -> dict:
        sel_family = sub[selection_col].map(MODEL_TO_FAMILY)
        ct = pd.crosstab(sub["family"], sel_family, dropna=False)
        for fam in FAMILY_TO_MODEL:
            if fam not in ct.index:
                ct.loc[fam] = 0
            if fam not in ct.columns:
                ct[fam] = 0
        ct = ct.reindex(index=list(FAMILY_TO_MODEL.keys()), columns=list(FAMILY_TO_MODEL.keys()), fill_value=0)
        # orient="index" -> {true_family: {selected_family: count}}, rows=truth / columns=prediction.
        return ct.astype(int).to_dict(orient="index")

    confusion_full_bic = confusion(df, "bic_selected_model")
    confusion_full_r2 = confusion(df, "val_r2_selected_model")

    frozen_subset = df[(df["c"].isin(FROZEN_C_SUPPORT)) & (df["grid_points"] == FROZEN_GRID) & (df["noise_sd"] == FROZEN_NOISE_DEFAULT)]
    confusion_frozen_bic = confusion(frozen_subset, "bic_selected_model")
    confusion_frozen_r2 = confusion(frozen_subset, "val_r2_selected_model")

    # -----------------------------------------------------------------
    # 5. Truth-vs-mass-only separation
    # -----------------------------------------------------------------
    sep_vs_mass = descriptor_df.groupby(["family", "c", "noise_sd", "grid_points"])["delta_r2_vs_mass"].agg(
        ["mean", "median", "min", "max", "count"]
    ).reset_index()

    # -----------------------------------------------------------------
    # 6. Truth-vs-best-wrong-family separation
    # -----------------------------------------------------------------
    sep_vs_best_wrong = descriptor_df.groupby(["family", "c", "noise_sd", "grid_points"])["delta_r2_vs_best_wrong"].agg(
        ["mean", "median", "min", "max", "count"]
    ).reset_index()
    best_wrong_model_freq = (
        descriptor_df.groupby(["family"])["best_wrong_model"].value_counts(normalize=True).rename("share").reset_index()
    )

    # -----------------------------------------------------------------
    # 7. Identifiability curves: rate vs c, at three reference slices
    # -----------------------------------------------------------------
    def curve_slice(noise_sd: float, grid_points: int) -> dict:
        sub = descriptor_df[(descriptor_df["noise_sd"] == noise_sd) & (descriptor_df["grid_points"] == grid_points)]
        t = rate_table(sub, ["family", "c"]).sort_values(["family", "c"])
        return t.to_dict(orient="records")

    identifiability_curves = {
        "default_noise_6pt_grid__noise0.02_grid6": curve_slice(0.02, 6),
        "noise_free__noise0.0_grid6": curve_slice(0.0, 6),
        "twelve_point_grid__noise0.02_grid12": curve_slice(0.02, 12),
    }

    # -----------------------------------------------------------------
    # 8. F02 / F03 / F09 / F18 special analysis
    # -----------------------------------------------------------------
    special = {}
    for tag, spec in V1_OBSERVED_RECOVERY.items():
        sub = descriptor_df[(descriptor_df["family"] == spec["family"]) & (descriptor_df["noise_sd"] == spec["noise_sd"])]
        curve = rate_table(sub, ["c", "grid_points"]).sort_values(["grid_points", "c"])
        frozen_range_sub = sub[sub["c"].isin(FROZEN_C_SUPPORT) & (sub["grid_points"] == FROZEN_GRID)]
        pooled = rate_table(frozen_range_sub, [])
        special[tag] = {
            "family": spec["family"],
            "noise_sd": spec["noise_sd"],
            "v1_observed_recovery": f"{spec['correct']}/{spec['total']}",
            "v1_observed_rate": spec["correct"] / spec["total"],
            "e3_oracle_rate_at_frozen_c_support_grid6": {
                "n": int(pooled["n"].iloc[0]) if len(pooled) else 0,
                "bic_rate": float(pooled["bic_rate"].iloc[0]) if len(pooled) else None,
                "r2_rate": float(pooled["r2_rate"].iloc[0]) if len(pooled) else None,
                "bic_classification": pooled["bic_classification"].iloc[0] if len(pooled) else None,
                "r2_classification": pooled["r2_classification"].iloc[0] if len(pooled) else None,
            },
            "full_c_and_grid_curve": curve.to_dict(orient="records"),
        }

    # -----------------------------------------------------------------
    # 9. F18 distinguishability under "intended geometry"
    #    (grid=6, noise=0.02, c in the frozen [0.25, 0.55] support --
    #    F18's actual production design point)
    # -----------------------------------------------------------------
    f18 = descriptor_df[(descriptor_df["family"] == "mass_exponential_descriptor") & (descriptor_df["noise_sd"] == 0.02)]
    f18_intended = f18[(f18["c"].isin(FROZEN_C_SUPPORT)) & (f18["grid_points"] == FROZEN_GRID)]
    f18_intended_rate = rate_table(f18_intended, [])
    f18_12pt = f18[(f18["c"].isin(FROZEN_C_SUPPORT)) & (f18["grid_points"] == 12)]
    f18_12pt_rate = rate_table(f18_12pt, [])
    f18_disposition = {
        "intended_geometry": {
            "description": "grid=6 (frozen ENERGY_GRID), noise=0.02 (F18's real noise level), c in {0.25,0.40,0.55} (frozen U(0.25,0.55) support)",
            "n": int(f18_intended_rate["n"].iloc[0]),
            "bic_rate": float(f18_intended_rate["bic_rate"].iloc[0]),
            "r2_rate": float(f18_intended_rate["r2_rate"].iloc[0]),
            "bic_wilson_lower": float(f18_intended_rate["bic_wilson_lower"].iloc[0]),
            "classification_bic": f18_intended_rate["bic_classification"].iloc[0],
            "classification_r2": f18_intended_rate["r2_classification"].iloc[0],
            "distinguishable": bool(f18_intended_rate["bic_rate"].iloc[0] >= IDENTIFIABLE_THRESHOLD),
        },
        "twelve_point_grid_same_c_and_noise": {
            "n": int(f18_12pt_rate["n"].iloc[0]),
            "bic_rate": float(f18_12pt_rate["bic_rate"].iloc[0]),
            "r2_rate": float(f18_12pt_rate["r2_rate"].iloc[0]),
            "classification_bic": f18_12pt_rate["bic_classification"].iloc[0],
        },
    }

    # -----------------------------------------------------------------
    # Per-family headline disposition at the frozen operating point
    # -----------------------------------------------------------------
    headline = {}
    for family in FAMILY_TO_MODEL:
        if family == "mass_power":
            continue
        native_noise = 0.02
        sub = descriptor_df[
            (descriptor_df["family"] == family)
            & (descriptor_df["noise_sd"] == native_noise)
            & (descriptor_df["grid_points"] == FROZEN_GRID)
            & (descriptor_df["c"].isin(FROZEN_C_SUPPORT))
        ]
        rt = rate_table(sub, [])
        c_star_bic = c_star_table[(c_star_table["family"] == family) & (c_star_table["noise_sd"] == native_noise) & (c_star_table["grid_points"] == FROZEN_GRID) & (c_star_table["criterion"] == "bic")]
        headline[family] = {
            "n": int(rt["n"].iloc[0]),
            "bic_rate": float(rt["bic_rate"].iloc[0]),
            "r2_rate": float(rt["r2_rate"].iloc[0]),
            "bic_wilson_lower": float(rt["bic_wilson_lower"].iloc[0]),
            "classification_bic": rt["bic_classification"].iloc[0],
            "classification_r2": rt["r2_classification"].iloc[0],
            "c_star_bic": None if c_star_bic.empty else c_star_bic["c_star"].iloc[0],
        }

    return {
        "n_worlds": len(df),
        "n_ok": int((df["status"] == "OK").sum()),
        "study_validity": study_validity,
        "control_breakdown_by_noise_grid": control_breakdown.to_dict(orient="records"),
        "overall_recovery_all_5_families": overall_all5.to_dict(orient="records")[0],
        "overall_recovery_descriptor_families_only": overall_descriptor_only.to_dict(orient="records")[0],
        "recovery_by_family": by_family.to_dict(orient="records"),
        "recovery_by_coefficient_pooled": by_coefficient_pooled.to_dict(orient="records"),
        "recovery_by_family_and_coefficient": by_family_and_c.to_dict(orient="records"),
        "full_cell_classification_200_cells": full_cell_classification,
        "c_star_table": c_star_table.to_dict(orient="records"),
        "confusion_matrix_full_grid": {"bic": confusion_full_bic, "val_r2": confusion_full_r2},
        "confusion_matrix_frozen_operating_point": {"bic": confusion_frozen_bic, "val_r2": confusion_frozen_r2,
                                                       "description": f"c in {FROZEN_C_SUPPORT}, grid={FROZEN_GRID}, noise={FROZEN_NOISE_DEFAULT}"},
        "truth_vs_mass_separation": sep_vs_mass.to_dict(orient="records"),
        "truth_vs_best_wrong_separation": sep_vs_best_wrong.to_dict(orient="records"),
        "best_wrong_model_frequency": best_wrong_model_freq.to_dict(orient="records"),
        "identifiability_curves": identifiability_curves,
        "special_analysis_F02_F03_F09_F18": special,
        "f18_intended_geometry_disposition": f18_disposition,
        "headline_disposition_by_family_frozen_operating_point": headline,
    }


def _sanitize(obj):
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return _sanitize(float(obj))
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def main() -> None:
    aggregate = build_aggregate()
    aggregate = _sanitize(aggregate)
    out_path = RESULTS_DIR / "e3_aggregate.json"
    out_path.write_text(json.dumps(aggregate, indent=1, sort_keys=True, allow_nan=False, default=str), encoding="utf-8")
    print(f"wrote {out_path}")

    # Also emit a flat per-world CSV for the "per-world table" deliverable.
    df = load_worlds()
    csv_cols = [
        "world_id", "cell_id", "family", "c", "noise_sd", "grid_points", "replicate", "status",
        "true_model_id", "bic_selected_model", "val_r2_selected_model",
        "oracle_correct_bic", "oracle_correct_r2", "is_control",
        "false_structure_bic", "false_structure_r2",
        "delta_r2_vs_mass", "delta_r2_vs_rival", "delta_r2_vs_best_wrong",
        "best_wrong_model", "c_hat_over_se", "lrt_p_true_vs_mass", "lrt_p_true_vs_rival",
    ] + [f"r2_val__{m}" for m in MODEL_IDS] + [f"bic__{m}" for m in MODEL_IDS]
    df[csv_cols].to_csv(RESULTS_DIR / "e3_per_world_table.csv", index=False)
    print(f"wrote {RESULTS_DIR / 'e3_per_world_table.csv'}")


if __name__ == "__main__":
    main()
