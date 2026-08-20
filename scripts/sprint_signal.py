"""FINAL ACCURACY SPRINT — how much ranking information does each candidate-side
feature actually carry?

Within each positive world, among usable band members, label = family-correct.
Report the mean within-world ROC AUC of every predeclared feature. A feature
that carries no ranking information sits at 0.5.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S
import sprint_arch as A

OUT = WT / "artifacts" / "sprint"

FEATS = [
    ("valid_r2", lambda m: m["valid_r2"], +1),
    ("refit_valid_r2_eff", lambda m: A.q_refit(m), +1),
    ("refit_minus_orig_r2", lambda m: (A.q_refit(m) - m["valid_r2"]), +1),
    ("strat_median_r2", lambda m: m["strat_median_r2"], +1),
    ("strat_min_r2", lambda m: m["strat_min_r2"], +1),
    ("strat_sd_r2", lambda m: m["strat_sd_r2"], -1),
    ("strat_worst_norm_rmse", lambda m: m["strat_worst_norm_rmse"], -1),
    ("resid_max_abs_spearman", lambda m: m["resid_max_abs_spearman"], -1),
    ("resid_med_abs_spearman", lambda m: m["resid_med_abs_spearman"], -1),
    ("resid_interaction_spearman", lambda m: m["resid_interaction_spearman"], -1),
    ("complexity", lambda m: m["complexity"], -1),
]


def main():
    worlds = A.load_worlds()
    res = {}
    for scope, blocks in [("all_positive", S.POSITIVE_BLOCKS), ("G1B", {"G1B"}),
                          ("G1C", {"G1C"})]:
        per = {name: [] for name, _, _ in FEATS}
        nw = 0
        for w in worlds:
            if w["block"] not in blocks or not w["scorable"]:
                continue
            mem = [m for m in w["members"] if m["usable"] and m["cluster"] >= 0]
            y = [1 if m.get("t_family") else 0 for m in mem]
            if not mem or sum(y) == 0 or sum(y) == len(y):
                continue
            nw += 1
            for name, fn, sgn in FEATS:
                v = []
                for m in mem:
                    x = fn(m)
                    v.append(float("nan") if x is None else sgn * float(x))
                a = S.auc_roc(v, y)
                if np.isfinite(a):
                    per[name].append(a)
        res[scope] = {"n_worlds_with_both_classes": nw,
                      **{name: {"mean_auc": float(np.mean(per[name])),
                                "median_auc": float(np.median(per[name])),
                                "n": len(per[name])}
                         for name, _, _ in FEATS}}
    # refit deltas
    d = []
    for w in worlds:
        if w["block"] not in S.POSITIVE_BLOCKS:
            continue
        for m in w["members"]:
            if m["refit_ok"] and m["refit_valid_r2"] is not None:
                d.append(m["refit_valid_r2"] - m["valid_r2"])
    d = np.asarray(d, float)
    res["refit_delta_valid_r2"] = {
        "n": int(d.size), "mean": float(d.mean()), "median": float(np.median(d)),
        "p05": float(np.percentile(d, 5)), "p95": float(np.percentile(d, 95)),
        "frac_improved": float(np.mean(d > 0)),
        "frac_worse": float(np.mean(d < 0)),
        "frac_abs_gt_0.001": float(np.mean(np.abs(d) > 1e-3))}
    (OUT / "feature_signal.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
