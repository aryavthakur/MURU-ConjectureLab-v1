"""FINAL ACCURACY SPRINT — assemble the frozen outputs."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

WT = Path(__file__).resolve().parents[1]
OUT = WT / "artifacts" / "sprint"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    nested = json.loads((OUT / "nested_cv_results.json").read_text())
    gate = json.loads((OUT / "gate_comparison.json").read_text())
    head = json.loads((OUT / "headroom_summary.json").read_text())
    err = json.loads((OUT / "error_decomposition.json").read_text())
    sig = json.loads((OUT / "feature_signal.json").read_text())
    dd = json.loads((OUT / "d_diagnostic.json").read_text())
    rep = json.loads((OUT / "development_replay.json").read_text())
    sx = json.loads((OUT / "safeexp_score.json").read_text())

    A = nested["architectures"]
    base_fam = A["A_CURRENT_FINAL"]["all"]["t_family"]
    n = A["A_CURRENT_FINAL"]["all"]["n"]
    ship = []
    for arch, r in A.items():
        if arch == "A_CURRENT_FINAL":
            continue
        gain = (r["all"]["t_family"] - base_fam) / n
        ship.append({"architecture": arch,
                     "family": [r["all"]["t_family"], n],
                     "family_gain_pp": round(100 * gain, 2),
                     "meets_3pp": bool(gain >= 0.03)})

    freeze = {
        "sprint": "MURU_FINAL_ACCURACY_SPRINT",
        "decision": "RETAIN_CURRENT_FINAL",
        "frozen_architecture": {
            "family_aggregation": "B2 validation-quality-weighted family vote",
            "representative": "R1 highest-validation-R2 representative",
            "null_gate": "CURRENT_GATE — median_seed_best_r2 >= t1 AND selection_fraction >= t2",
            "recovery": "corrected production parser (unchanged)",
            "grammar": "frozen p3-grammar-1.0.0, SAFE_EXP NOT adopted",
            "cas": "SymPy only (unchanged)",
            "constant_refit": "NOT adopted as a runtime quality signal",
            "cross_stratum_score": "NOT adopted",
            "family_ranker": "NOT adopted",
            "code": "muru.objval.select + scripts/accopt_selectors.py "
                    "(CONSENSUS_PLUS_REPRESENTATIVE_PLUS_REFUSAL_GATE, B2, R1)",
        },
        "unchanged_frozen_constants": {
            "EXPONENT_TOL": 0.15, "BAND_TOL": 0.01, "MAX_COMPLEXITY": 20,
            "MAX_INVALID_FRACTION": 0.005, "MIN_SELECTION_FRACTION": "20/30",
            "SHAPE_REL_RMSE_TOL": 0.05,
        },
        "ship_criterion": {
            "required_family_gain_pp": 3.0,
            "baseline_family": [base_fam, n],
            "candidates": ship,
            "met_by_any": bool(any(c["meets_3pp"] for c in ship)),
        },
        "gate_head_to_head": {
            f: {k: gate["gates"][f][k] for k in
                ("sensitivity", "false_positive_rate", "specificity",
                 "balanced_accuracy", "roc_auc", "pr_auc")}
            for f in gate["gates"]},
        "selected_gate": gate["selected_gate"],
        "held_out_cv": {
            "support_ungated": [A["A_CURRENT_FINAL"]["all"]["t_support"], n],
            "support_end_to_end": [A["A_CURRENT_FINAL"]["all"]["t_support_gated"], n],
            "family_ungated": [A["A_CURRENT_FINAL"]["all"]["t_family"], n],
            "family_end_to_end": [A["A_CURRENT_FINAL"]["all"]["t_family_gated"], n],
            "family_ci": A["A_CURRENT_FINAL"]["family_ci"],
            "support_ci": A["A_CURRENT_FINAL"]["support_ci"],
            **{k: gate["gates"]["CURRENT_GATE"][k] for k in
               ("sensitivity", "specificity", "false_positive_rate",
                "false_negative_rate", "balanced_accuracy", "roc_auc", "pr_auc")},
        },
        "computational_failure_rate": 0.0,
        "artifact_hashes": {p.name: sha(p) for p in sorted(OUT.glob("*.json"))},
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=WT,
                                   capture_output=True, text=True).stdout.strip(),
    }
    (OUT / "architecture_freeze.json").write_text(json.dumps(freeze, indent=1))

    payload = {
        "freeze": freeze,
        "phase0_baseline_parity": {
            "reproduced": True,
            "support_ungated": [55, 56], "support_end_to_end": [54, 56],
            "family": [47, 56], "G1A_family": [6, 6], "G1B_family": [35, 40],
            "G1C_family": [6, 10], "null_fpr": 0.030434782608695653,
            "roc_auc": 0.9990683229813665,
            "note": "scripts/accopt_run.py re-run on the copied cache is "
                    "bit-identical to the frozen baseline artifact; "
                    "architecture A reproduces the baseline selector on "
                    "323/323 worlds",
        },
        "nested_cv": nested,
        "gate_comparison": gate,
        "headroom": head,
        "error_decomposition": err,
        "feature_signal": sig,
        "d_diagnostic": dd,
        "development_replay": rep,
        "safe_exp": sx["summary"],
    }
    (WT / "MURU_FINAL_ACCURACY_SPRINT.json").write_text(
        json.dumps(payload, indent=1, default=str))
    print("wrote architecture_freeze.json and MURU_FINAL_ACCURACY_SPRINT.json")
    print(json.dumps(freeze["ship_criterion"], indent=1))


if __name__ == "__main__":
    main()
