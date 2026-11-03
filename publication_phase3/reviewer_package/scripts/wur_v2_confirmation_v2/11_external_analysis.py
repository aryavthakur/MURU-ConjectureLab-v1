"""MSnLib confirmation study 2, protocol V2 section 2: the frozen external analysis, run after the one look.

Identical rules to study 1 (scripts/wur_v2_confirmation/12_external_analysis.py): A0 map, frozen models, support
exclusion, P1 and summaries, whole-scaffold-group bootstrap (B=10,000, seed 20261011), AF tail override, per-rung
and novelty-bin secondaries, four-way decision. Existing tested code only (metrics.py, candidate.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import candidate as CA            # noqa: E402
from muru.wur_v2 import decode_authority as DA     # noqa: E402
from muru.wur_v2 import metrics as M               # noqa: E402

A0 = (-5.95552603907965, 0.8618030610784555)
NCE_RUNGS = (20.0, 60.0)
BOOT_B, BOOT_SEED = 10_000, 20261011
AF_TOLERANCE_UPPER95 = 0.03
V2 = ROOT / "artifacts/wur_v2_confirmation_v2"


def main() -> int:
    mu = pd.read_csv(V2 / "result/measured_mu.csv")
    pop = pd.read_csv(ROOT / DA.POPULATION_CSV)
    W = mu.pivot(index="key", columns="energy", values="mu").reindex(columns=list(NCE_RUNGS))
    p = pop.set_index("key").loc[W.index]
    E = (np.array(NCE_RUNGS) - A0[0]) / A0[1]
    candidate = json.loads((ROOT / DA.CANDIDATE_JSON).read_text())
    ta_ridge = json.loads((ROOT / DA.COMPARATOR_JSON).read_text())
    pred_c = CA.predict_mu(candidate, p.smiles, p.mh, E)
    pred_r = CA.predict_mu(ta_ridge, p.smiles, p.mh, E)
    sup = CA.supported(candidate, p.smiles, p.mh, E).all(1) & CA.supported(ta_ridge, p.smiles, p.mh, E).all(1)
    complete = np.isfinite(W.to_numpy()).all(1)
    keep = complete & sup
    Y = W.to_numpy()[keep]
    groups = p.scaffold_group.to_numpy()[keep]
    sizes = pd.Series(groups).value_counts()
    out = {
        "n_population_compounds": int(len(pop)), "n_measured_compounds": int(len(W)),
        "n_incomplete_rung": int((~complete).sum()), "n_excluded_unsupported": int((complete & ~sup).sum()),
        "n_scored": int(keep.sum()), "n_scaffold_groups_scored": int(len(sizes)), "largest_group": int(sizes.max()),
        "group_size_distribution": {str(k): int(v) for k, v in sizes.value_counts().sort_index().items()},
        "candidate": M.summary(pred_c[keep], Y), "ta_ridge": M.summary(pred_r[keep], Y),
        "per_rung_candidate": M.per_rung(pred_c[keep], Y, NCE_RUNGS), "per_rung_ta_ridge": M.per_rung(pred_r[keep], Y, NCE_RUNGS),
    }
    Ec, Er = M.errors(pred_c[keep], Y), M.errors(pred_r[keep], Y)
    out["per_rung_detail"] = {str(e): {"ratio": float(np.sqrt(np.nanmean(Ec[:, j] ** 2)) / np.sqrt(np.nanmean(Er[:, j] ** 2))),
                                       "mean_signed_residual_candidate": float(np.nanmean(Ec[:, j])),
                                       "mean_signed_residual_ta_ridge": float(np.nanmean(Er[:, j])),
                                       "median_abs_residual_candidate": float(np.nanmedian(np.abs(Ec[:, j]))),
                                       "median_abs_residual_ta_ridge": float(np.nanmedian(np.abs(Er[:, j])))}
                              for j, e in enumerate(NCE_RUNGS)}
    out["bootstrap"] = M.cluster_bootstrap(pred_c[keep], pred_r[keep], Y, groups, n=BOOT_B, seed=BOOT_SEED)
    k2 = complete
    out["sensitivity_including_unsupported"] = {"n": int(k2.sum()), "P1_candidate": M.p1(M.errors(pred_c[k2], W.to_numpy()[k2])),
                                                "P1_ta": M.p1(M.errors(pred_r[k2], W.to_numpy()[k2]))}
    nov = pd.read_csv(V2 / "freeze/novelty_bins_per_compound.csv").set_index("key")
    labels = nov.reindex(p.index[keep]).novelty_bin
    by_bin = {}
    for lab in labels.dropna().unique():
        m = (labels == lab).to_numpy()
        if m.sum() >= 5:
            b = {"n": int(m.sum()), "P1_candidate": M.p1(M.errors(pred_c[keep][m], Y[m])), "P1_ta": M.p1(M.errors(pred_r[keep][m], Y[m]))}
            b["ratio"] = b["P1_candidate"] / b["P1_ta"]
            by_bin[str(lab)] = b
    out["novelty_bins"] = by_bin
    c = out["bootstrap"]
    af_adverse = c["AF_diff_ci"][1] > AF_TOLERANCE_UPPER95
    out["af_tail_risk"] = {"AF_diff": c["AF_diff"], "AF_diff_ci95": c["AF_diff_ci"],
                           "tolerance_upper95": AF_TOLERANCE_UPPER95, "materially_adverse": bool(af_adverse)}
    if c["P1_ratio"] >= 1.0 or af_adverse:
        decision = "FAILED TO TRANSFER"
    elif c["P1_ratio_ci"][1] < 1.0:
        decision = "PRACTICALLY MEANINGFUL EXTERNAL CONFIRMATION" if c["P1_ratio"] <= 0.95 else "MODEST EXTERNAL CONFIRMATION"
    else:
        decision = "DIRECTIONALLY FAVORABLE BUT INCONCLUSIVE"
    out["decision"] = decision
    (V2 / "result/external_analysis.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps(out, indent=2, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
