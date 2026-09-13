"""Step 11 (frozen external analysis), run only AFTER the one-look decode produces
`artifacts/wur_v2_confirmation/measured_mu.csv` (key, energy in {20,60}, mu).
Reuses the repo's existing, already-tested estimand/bootstrap code (metrics.py) and
model-prediction code (candidate.py) verbatim -- no new statistics are invented here.
Fixed A0 map only (no adapter fitting): E_LCSB = (NCE - a_WUR) / b_WUR.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
sys.path.insert(0, str(REPO / "src"))
from muru.wur_v2 import candidate as CA   # noqa: E402
from muru.wur_v2 import metrics as M      # noqa: E402

A0 = (-5.95552603907965, 0.8618030610784555)   # a_WUR, b_WUR (frozen Stage 1 bridge; zero MSnLib-fitted parameters)
NCE_RUNGS = (20.0, 60.0)
BOOT_B = 10_000
BOOT_SEED = 20261011


def e_lcsb(nce: np.ndarray) -> np.ndarray:
    return (nce - A0[0]) / A0[1]


def main():
    mu = pd.read_csv(REPO / "artifacts/wur_v2_confirmation/measured_mu.csv")  # key, energy, mu
    pop = pd.read_csv(REPO / "artifacts/wur_v2_confirmation/eligible_population.csv")  # key, smiles, mh, scaffold_group

    W = mu.pivot(index="key", columns="energy", values="mu").reindex(columns=list(NCE_RUNGS))
    p = pop.set_index("key").loc[W.index]
    # A0 is zero-parameter: the same map for every compound. predict_mu/supported broadcast a
    # 1-D energies_lcsb across all compounds identically (candidate.py:128-129, 138-139).
    E = e_lcsb(np.array(NCE_RUNGS))

    candidate = json.loads((REPO / "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json").read_text())
    ta_ridge = json.loads((REPO / "artifacts/wur_v2/candidate/V2_REF_TA_RIDGE.json").read_text())
    pred_c = CA.predict_mu(candidate, p.smiles, p.mh, E)
    pred_r = CA.predict_mu(ta_ridge, p.smiles, p.mh, E)
    sup_c = CA.supported(candidate, p.smiles, p.mh, E)
    sup_r = CA.supported(ta_ridge, p.smiles, p.mh, E)

    complete = np.isfinite(W.to_numpy()).all(1)
    supported = sup_c.all(1) & sup_r.all(1)
    keep = complete & supported
    Y = W.to_numpy()[keep]
    groups = p.scaffold_group.to_numpy()[keep]

    out = {
        "n_measured_compounds": int(len(W)), "n_incomplete_rung": int((~complete).sum()),
        "n_excluded_unsupported": int((complete & ~supported).sum()), "n_scored": int(keep.sum()),
        "n_scaffold_groups_scored": int(len(set(groups))),
        "candidate": M.summary(pred_c[keep], Y), "ta_ridge": M.summary(pred_r[keep], Y),
        "per_rung_candidate": M.per_rung(pred_c[keep], Y, NCE_RUNGS),
        "per_rung_ta_ridge": M.per_rung(pred_r[keep], Y, NCE_RUNGS),
    }
    out["bootstrap"] = M.cluster_bootstrap(pred_c[keep], pred_r[keep], Y, groups, n=BOOT_B, seed=BOOT_SEED)

    # sensitivity including profile-unsupported cells (never the primary)
    k2 = complete
    out["sensitivity_including_unsupported"] = {
        "n": int(k2.sum()), "P1_candidate": M.p1(M.errors(pred_c[k2], W.to_numpy()[k2])),
        "P1_ta": M.p1(M.errors(pred_r[k2], W.to_numpy()[k2]))}

    # novelty-bin cross-tab (secondary, descriptive, only interpreted strongly if primary supported)
    nov = pd.read_csv(REPO / "artifacts/wur_v2_confirmation/novelty_bins_per_compound.csv")
    nov = nov.set_index("key")
    keys_kept = p.index[keep]
    bin_labels = nov.reindex(keys_kept).novelty_bin
    by_bin = {}
    for label in bin_labels.dropna().unique():
        m = (bin_labels == label).to_numpy()
        if m.sum() >= 5:
            by_bin[str(label)] = {"n": int(m.sum()), "P1_candidate": M.p1(M.errors(pred_c[keep][m], Y[m])),
                                   "P1_ta": M.p1(M.errors(pred_r[keep][m], Y[m]))}
            by_bin[str(label)]["ratio"] = by_bin[str(label)]["P1_candidate"] / by_bin[str(label)]["P1_ta"]
    out["novelty_bins"] = by_bin

    # Frozen rule (protocol/freeze §9) is a disjunction: point ratio >= 1.00 OR a materially
    # adverse tail effect under the secondary AF rule both force FAILED_TO_TRANSFER, even when
    # the point-estimate ratio looks good. AF_TOLERANCE_UPPER95 = +0.03 noninferiority tolerance
    # (protocol §9's "key secondary ... AF difference upper 95 percent limit at most +0.03").
    AF_TOLERANCE_UPPER95 = 0.03
    c = out["bootstrap"]
    af_adverse = c["AF_diff_ci"][1] > AF_TOLERANCE_UPPER95
    out["af_tail_risk"] = {"AF_diff": c["AF_diff"], "AF_diff_ci95": c["AF_diff_ci"],
                           "tolerance_upper95": AF_TOLERANCE_UPPER95, "materially_adverse": bool(af_adverse)}
    if c["P1_ratio"] >= 1.0 or af_adverse:
        decision = "FAILED_TO_TRANSFER"
    elif c["P1_ratio_ci"][1] < 1.0:
        decision = "PRACTICALLY_MEANINGFUL" if c["P1_ratio"] <= 0.95 else "MODEST"
    else:
        decision = "DIRECTIONALLY_FAVORABLE_BUT_INCONCLUSIVE"
    out["decision"] = decision

    (REPO / "artifacts/wur_v2_confirmation/external_analysis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
