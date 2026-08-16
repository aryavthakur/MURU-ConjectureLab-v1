"""INDEPENDENT recomputation of every E3 headline statistic.

Written from scratch for the hostile audit. Reads ONLY the raw
e3_worlds.jsonl per-world records (written by run_e3.py). Does NOT import
aggregate_e3.py, does NOT read e3_aggregate.json or e3_per_world_table.csv
(both are outputs of the primary aggregator / its main()), and re-implements
every rate, Wilson interval, confusion matrix, and classification rule from
scratch against the frozen design document's own stated definitions.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

WORLDS_PATH = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b/results/e3_identifiability/e3_worlds.jsonl")
OUT_DIR = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/results/audit_e3")

FAMILY_TO_MODEL = {
    "mass_power": "M_mass",
    "mass_affine_descriptor": "M_affine",
    "mass_saturating_descriptor": "M_sat",
    "mass_exponential_descriptor": "M_exp",
    "mass_interaction": "M_inter",
}
MODEL_TO_FAMILY = {v: k for k, v in FAMILY_TO_MODEL.items()}
IDENTIFIABLE = 0.80
MARGINAL = 0.50


def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - adj) / denom, (centre + adj) / denom)


def classify(rate):
    if rate >= IDENTIFIABLE:
        return "IDENTIFIABLE"
    if rate >= MARGINAL:
        return "MARGINAL"
    return "WEAKLY_IDENTIFIABLE"


def load():
    rows = []
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            assert r["status"] == "OK"
            rows.append({
                "world_id": r["world_id"],
                "family": r["family"],
                "c": r["c"],
                "noise_sd": r["noise_sd"],
                "grid_points": r["grid_points"],
                "replicate": r["replicate"],
                "bic_selected_model": r["bic_selected_model"],
                "val_r2_selected_model": r["val_r2_selected_model"],
                "true_model_id": r["true_model_id"],
                "delta_r2_vs_mass": r["delta_r2_vs_mass"],
                "delta_r2_vs_rival": r["delta_r2_vs_rival"],
            })
    df = pd.DataFrame(rows)
    df["oracle_correct_bic"] = df["bic_selected_model"] == df["true_model_id"]
    df["oracle_correct_r2"] = df["val_r2_selected_model"] == df["true_model_id"]
    df["is_control"] = df["family"] == "mass_power"
    df["false_structure_bic"] = df["is_control"] & (df["bic_selected_model"] != "M_mass")
    df["false_structure_r2"] = df["is_control"] & (df["val_r2_selected_model"] != "M_mass")
    return df


def rate(df, correct_col):
    n = len(df)
    k = int(df[correct_col].sum())
    r = k / n if n else float("nan")
    lo, hi = wilson(k, n)
    return {"n": n, "k": k, "rate": r, "wilson_lo": lo, "wilson_hi": hi}


def main():
    df = load()
    assert len(df) == 10_000
    report = {}

    # ================================================================
    # 1. STUDY VALIDITY GATE
    # ================================================================
    control = df[df["is_control"]]
    assert len(control) == 2000
    k_bic = int(control["false_structure_bic"].sum())
    k_r2 = int(control["false_structure_r2"].sum())
    lo_bic, hi_bic = wilson(k_bic, 2000)
    lo_r2, hi_r2 = wilson(k_r2, 2000)
    report["study_validity"] = {
        "bic": {"k": k_bic, "n": 2000, "rate": k_bic / 2000, "wilson_upper": hi_bic, "valid": (k_bic / 2000) <= 0.10},
        "r2": {"k": k_r2, "n": 2000, "rate": k_r2 / 2000, "wilson_upper": hi_r2, "valid": (k_r2 / 2000) <= 0.10},
    }
    print("=== STUDY VALIDITY (independent) ===")
    print(f"BIC: {k_bic}/2000 = {k_bic/2000:.4f}, Wilson upper = {hi_bic:.4f}  (reported: 0.095, 0.109)")
    print(f"R2:  {k_r2}/2000 = {k_r2/2000:.4f}, Wilson upper = {hi_r2:.4f}  (reported: 0.685, 0.705)")

    # ================================================================
    # 2. OVERALL RECOVERY
    # ================================================================
    overall_all5 = rate(df, "oracle_correct_bic")
    overall_all5_r2 = rate(df, "oracle_correct_r2")
    descriptor_df = df[~df["is_control"]]
    overall_desc = rate(descriptor_df, "oracle_correct_bic")
    report["overall_recovery"] = {
        "all5_bic": overall_all5, "all5_r2": overall_all5_r2, "descriptor_only_bic": overall_desc,
    }
    print("\n=== OVERALL RECOVERY (independent) ===")
    print(f"All 5 families, BIC: n={overall_all5['n']} rate={overall_all5['rate']:.4f} (reported: 0.8264)")
    print(f"Descriptor only, BIC: n={overall_desc['n']} rate={overall_desc['rate']:.4f} (reported: 0.8068)")

    # ================================================================
    # 3. RECOVERY BY FAMILY
    # ================================================================
    print("\n=== RECOVERY BY FAMILY (independent, pooled over whole grid) ===")
    by_family = {}
    reported_by_family = {
        "mass_interaction": (0.9855, 0.9325), "mass_power": (0.9050, 0.3150),
        "mass_saturating_descriptor": (0.8430, 0.7410), "mass_affine_descriptor": (0.7300, 0.6065),
        "mass_exponential_descriptor": (0.6685, 0.5610),
    }
    for fam, sub in df.groupby("family"):
        if fam == "mass_power":
            bic_r = 1 - sub["false_structure_bic"].mean()
            r2_r = 1 - sub["false_structure_r2"].mean()
        else:
            bic_r = sub["oracle_correct_bic"].mean()
            r2_r = sub["oracle_correct_r2"].mean()
        by_family[fam] = {"n": len(sub), "bic_rate": bic_r, "r2_rate": r2_r}
        rep_bic, rep_r2 = reported_by_family[fam]
        flag = "OK" if abs(bic_r - rep_bic) < 1e-4 and abs(r2_r - rep_r2) < 1e-4 else "MISMATCH"
        print(f"  {fam:32s} n={len(sub):5d} bic={bic_r:.4f} (reported {rep_bic}) r2={r2_r:.4f} (reported {rep_r2})  [{flag}]")
    report["recovery_by_family"] = by_family

    # ================================================================
    # 4. RECOVERY BY COEFFICIENT (pooled over 4 descriptor families)
    # ================================================================
    print("\n=== RECOVERY BY COEFFICIENT, pooled descriptor families (independent) ===")
    reported_by_c = {0.25: (0.6681, 0.5769), 0.40: (0.7569, 0.6581), 0.55: (0.8094, 0.6944), 1.1: (0.8813, 0.7856), 2.2: (0.9181, 0.8363)}
    by_c = {}
    for c, sub in descriptor_df.groupby("c"):
        bic_r = sub["oracle_correct_bic"].mean()
        r2_r = sub["oracle_correct_r2"].mean()
        by_c[c] = {"n": len(sub), "bic_rate": bic_r, "r2_rate": r2_r}
        rep_bic, rep_r2 = reported_by_c[c]
        flag = "OK" if abs(bic_r - rep_bic) < 1e-4 and abs(r2_r - rep_r2) < 1e-4 else "MISMATCH"
        print(f"  c={c:5.2f} n={len(sub):5d} bic={bic_r:.4f} (reported {rep_bic}) r2={r2_r:.4f} (reported {rep_r2})  [{flag}]")
    report["recovery_by_coefficient"] = by_c

    # ================================================================
    # 5. FROZEN OPERATING POINT HEADLINE TABLE
    # ================================================================
    print("\n=== FROZEN OPERATING POINT (c in {0.25,0.40,0.55}, noise=0.02, grid=6) ===")
    FROZEN_C = {0.25, 0.40, 0.55}
    frozen = df[(df["c"].isin(FROZEN_C)) & (df["noise_sd"] == 0.02) & (df["grid_points"] == 6)]
    reported_frozen = {
        "mass_interaction": (1.000, 0.975, "IDENTIFIABLE", 0.25),
        "mass_saturating_descriptor": (0.820, 0.751, "IDENTIFIABLE", 0.40),
        "mass_affine_descriptor": (0.553, 0.473, "MARGINAL", 1.1),
        "mass_exponential_descriptor": (0.527, 0.447, "MARGINAL", 1.1),
    }
    headline = {}
    for fam in ["mass_interaction", "mass_saturating_descriptor", "mass_affine_descriptor", "mass_exponential_descriptor"]:
        sub = frozen[frozen["family"] == fam]
        k = int(sub["oracle_correct_bic"].sum())
        n = len(sub)
        r = k / n
        lo, hi = wilson(k, n)
        cls = classify(r)
        headline[fam] = {"n": n, "k": k, "rate": r, "wilson_lo": lo, "classification": cls}
        rep_rate, rep_lo, rep_cls, rep_cstar = reported_frozen[fam]
        flag = "OK" if abs(r - rep_rate) < 1e-3 and abs(lo - rep_lo) < 1e-3 and cls == rep_cls else "MISMATCH"
        print(f"  {fam:32s} n={n} k={k} rate={r:.4f} (reported {rep_rate}) wilson_lo={lo:.4f} (reported {rep_lo}) class={cls} (reported {rep_cls}) [{flag}]")
    report["frozen_operating_point"] = headline

    # ================================================================
    # 6. c_star per family at native noise=0.02, grid=6
    # ================================================================
    print("\n=== c* (native noise 0.02, grid 6) ===")
    c_star = {}
    for fam in ["mass_interaction", "mass_saturating_descriptor", "mass_affine_descriptor", "mass_exponential_descriptor"]:
        sub = df[(df["family"] == fam) & (df["noise_sd"] == 0.02) & (df["grid_points"] == 6)]
        curve = sub.groupby("c")["oracle_correct_bic"].mean().sort_index()
        reached = curve[curve >= IDENTIFIABLE]
        cstar = float(reached.index.min()) if len(reached) else None
        c_star[fam] = {"curve": curve.to_dict(), "c_star": cstar}
        print(f"  {fam:32s} curve={dict(curve.round(3))} c*={cstar}")
    report["c_star"] = c_star

    # ================================================================
    # 7. CONFUSION MATRIX at frozen operating point (BIC), 750 worlds
    # ================================================================
    print("\n=== CONFUSION MATRIX at frozen operating point, BIC (independent) ===")
    fam_order = ["mass_power", "mass_affine_descriptor", "mass_saturating_descriptor", "mass_exponential_descriptor", "mass_interaction"]
    frozen["selected_family"] = frozen["bic_selected_model"].map(MODEL_TO_FAMILY)
    cm = {}
    for truth in fam_order:
        row = {}
        sub = frozen[frozen["family"] == truth]
        assert len(sub) == 150, f"{truth}: {len(sub)}"
        for sel in fam_order:
            row[sel] = int((sub["selected_family"] == sel).sum())
        assert sum(row.values()) == 150
        cm[truth] = row
        print(f"  {truth:28s} -> {row}")
    report["confusion_matrix_frozen_bic"] = cm
    reported_cm = {
        "mass_power": {"mass_power": 132, "mass_affine_descriptor": 0, "mass_saturating_descriptor": 0, "mass_exponential_descriptor": 3, "mass_interaction": 15},
        "mass_affine_descriptor": {"mass_power": 0, "mass_affine_descriptor": 83, "mass_saturating_descriptor": 7, "mass_exponential_descriptor": 60, "mass_interaction": 0},
        "mass_saturating_descriptor": {"mass_power": 0, "mass_affine_descriptor": 20, "mass_saturating_descriptor": 123, "mass_exponential_descriptor": 6, "mass_interaction": 1},
        "mass_exponential_descriptor": {"mass_power": 2, "mass_affine_descriptor": 38, "mass_saturating_descriptor": 23, "mass_exponential_descriptor": 79, "mass_interaction": 8},
        "mass_interaction": {"mass_power": 0, "mass_affine_descriptor": 0, "mass_saturating_descriptor": 0, "mass_exponential_descriptor": 0, "mass_interaction": 150},
    }
    cm_match = cm == reported_cm
    print(f"  CONFUSION MATRIX EXACT MATCH TO E3_RESULTS.md TABLE: {cm_match}")
    report["confusion_matrix_matches_reported"] = cm_match

    # ================================================================
    # 8. F02/F03/F09/F18 special analysis
    # ================================================================
    print("\n=== F02/F03/F09/F18 special analysis (independent) ===")
    special_spec = {
        "F02": ("mass_affine_descriptor", 0.0295, 48.7),
        "F03": ("mass_affine_descriptor", 0.06, 36.0),
        "F09": ("mass_saturating_descriptor", 0.02, 82.0),
        "F18": ("mass_exponential_descriptor", 0.02, 52.7),
    }
    special = {}
    for tag, (fam, noise, rep_pct) in special_spec.items():
        sub = df[(df["family"] == fam) & (df["noise_sd"] == noise) & (df["c"].isin(FROZEN_C)) & (df["grid_points"] == 6)]
        n = len(sub)
        r = sub["oracle_correct_bic"].mean()
        special[tag] = {"n": n, "rate_pct": r * 100}
        flag = "OK" if abs(r * 100 - rep_pct) < 0.1 else "MISMATCH"
        print(f"  {tag} ({fam}, noise={noise}): n={n} rate={r*100:.1f}% (reported {rep_pct}%) [{flag}]")
    report["special_F02_F03_F09_F18"] = special

    # ================================================================
    # 9. F18 intended geometry (section 10)
    # ================================================================
    print("\n=== F18 intended geometry (independent) ===")
    f18_6 = df[(df["family"] == "mass_exponential_descriptor") & (df["noise_sd"] == 0.02) & (df["c"].isin(FROZEN_C)) & (df["grid_points"] == 6)]
    f18_12 = df[(df["family"] == "mass_exponential_descriptor") & (df["noise_sd"] == 0.02) & (df["c"].isin(FROZEN_C)) & (df["grid_points"] == 12)]
    r6 = f18_6["oracle_correct_bic"].mean()
    r12 = f18_12["oracle_correct_bic"].mean()
    print(f"  grid=6:  n={len(f18_6)} rate={r6:.4f} (reported 0.527)")
    print(f"  grid=12: n={len(f18_12)} rate={r12:.4f} (reported 0.540)")
    report["f18_intended_geometry"] = {"grid6": {"n": len(f18_6), "rate": r6}, "grid12": {"n": len(f18_12), "rate": r12}}

    # ================================================================
    # 10. Noise-free arm (H_id_noise) at c=0.25, grid=6 -- section 8.2
    # ================================================================
    print("\n=== NOISE-FREE ARM (H_id_noise), grid=6 (independent) ===")
    reported_noise0 = {0.25: {"affine": 1.00, "exponential": 0.98, "saturating": 1.00, "interaction": 1.00}}
    fam_short = {"mass_affine_descriptor": "affine", "mass_exponential_descriptor": "exponential", "mass_saturating_descriptor": "saturating", "mass_interaction": "interaction"}
    noise0 = df[(df["noise_sd"] == 0.0) & (df["grid_points"] == 6) & (~df["is_control"])]
    for c in [0.25, 0.40, 0.55, 1.1, 2.2]:
        sub = noise0[noise0["c"] == c]
        rates = sub.groupby("family")["oracle_correct_bic"].mean()
        row = {fam_short[f]: round(v, 3) for f, v in rates.items()}
        print(f"  c={c}: {row}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "independent_recompute.json"
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
            return None
        return o
    out_path.write_text(json.dumps(clean(report), indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
