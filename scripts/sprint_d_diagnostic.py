"""DIAGNOSTIC ONLY — why did architecture D collapse?

This changes nothing. D is scored exactly as frozen; this script only asks
which part of the frozen D specification produced the failure. Nothing here is
adopted, and no architecture is created from it.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S
import sprint_arch as A
import sprint_run as R

OUT = WT / "artifacts" / "sprint"


def main():
    worlds = A.load_worlds()
    W = {w["world_id"]: w for w in worlds}
    preps = {w["world_id"]: A.prep(w) for w in worlds}
    fold = S.assign_folds(worlds)
    all_ids = sorted(W)
    POS = S.POSITIVE_BLOCKS
    out = {}

    # 1. how many clusters per world does D rank over, and how often is the
    #    label-positive cluster even present?
    n_cl, has_pos = [], 0
    for w in worlds:
        if w["block"] not in POS:
            continue
        P = preps[w["world_id"]]
        rows = A.d_family_rows(P)
        n_cl.append(len(rows))
        has_pos += any(bool(P["members"][r["rep"]].get("t_family")) for r in rows)
    out["positives_n_clusters"] = {"median": float(np.median(n_cl)),
                                   "min": int(min(n_cl)), "max": int(max(n_cl))}
    out["positives_with_a_label_positive_cluster"] = [has_pos, len(n_cl)]

    # 2. is the collapse caused by the G3/G4M training rows (38 of 94 scorable
    #    worlds, whose planted law is a simple mass power law)?
    for label, blocks in [("as_frozen_all_scorable", A.SCORABLE_BLOCKS),
                          ("diagnostic_positives_only", {"G1A", "G1B", "G1C"})]:
        held = {}
        for f in range(S.N_FOLDS):
            tr = [w for w in all_ids if fold[w] != f]
            te = [w for w in all_ids if fold[w] == f]
            X, y = [], []
            for wid in sorted(tr):
                w = W[wid]
                if w["block"] not in blocks or not w["scorable"]:
                    continue
                P = preps[wid]
                for r in A.d_family_rows(P):
                    X.append(r["x"])
                    y.append(1 if bool(P["members"][r["rep"]].get("t_family")) else 0)
            model = A.fit_d(np.asarray(X, float), np.asarray(y, int), 0.1)
            sel = R.run_selection(preps, W, te, "D_SMALL_FAMILY_RANKER", dmodel=model)
            held.update(sel)
        k, n = R.fam_rate(held, W, list(held), "t_family", POS)
        ks, ns = R.fam_rate(held, W, list(held), "t_support", POS)
        out[label] = {"family": [k, n], "support": [ks, ns]}
        print(label, "family", k, "/", n, " support", ks, "/", ns, flush=True)

    # 3. what does the frozen-D ranker actually prefer?
    X, y = A.d_training_matrix(preps, W, set(all_ids))
    m = A.fit_d(X, y, 0.1)
    out["full_data_coefficients"] = dict(zip(A.D_FEATURES, m["coef"]))
    out["training_rows"] = int(len(y))
    out["training_positive_rate"] = float(y.mean())
    (OUT / "d_diagnostic.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
