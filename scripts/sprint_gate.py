"""FINAL ACCURACY SPRINT — clean head-to-head of the two predefined gate forms,
under the architecture that wins the nested-CV comparison, plus the frozen
error decomposition and the development replay.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S      # noqa: E402
import sprint_arch as A          # noqa: E402
import sprint_run as R           # noqa: E402

OUT = WT / "artifacts" / "sprint"


def evaluate(held, W):
    pos = [w for w in held if S.category(W[w]["block"]) == "positive"]
    nul = [w for w in held if S.category(W[w]["block"]) == "null"]
    tp = sum(held[w]["report"] for w in pos)
    fp = sum(held[w]["report"] for w in nul)
    sens, fpr = tp / len(pos), fp / len(nul)
    sc = [held[w]["gate"]["median_seed_best_r2"] for w in pos + nul]
    lab = [1] * len(pos) + [0] * len(nul)
    out = {"sensitivity": sens, "sensitivity_ci": A.wilson(tp, len(pos)),
           "specificity": 1 - fpr, "false_positive_rate": fpr,
           "fpr_ci": A.wilson(fp, len(nul)), "false_negative_rate": 1 - sens,
           "balanced_accuracy": 0.5 * (sens + 1 - fpr),
           "roc_auc": S.auc_roc(sc, lab), "pr_auc": S.auc_pr(sc, lab),
           "n_positive": len(pos), "n_null": len(nul)}
    for lbl, blocks, noise in [("all", S.POSITIVE_BLOCKS, None),
                               ("G1A", {"G1A"}, None), ("G1B", {"G1B"}, None),
                               ("G1C", {"G1C"}, None),
                               ("G1B_low", {"G1B"}, "low"),
                               ("G1B_moderate", {"G1B"}, "moderate"),
                               ("G1B_adverse", {"G1B"}, "adverse")]:
        ids = [w for w in held if W[w]["block"] in blocks and W[w]["scorable"]
               and (noise is None or W[w]["noise_regime"] == noise)]
        out[lbl] = {"n": len(ids)}
        for met in ("t_support", "t_family", "t_exact"):
            out[lbl][met] = sum(1 for w in ids if held[w][met])
            out[lbl][met + "_gated"] = sum(1 for w in ids
                                           if held[w][met] and held[w]["report"])
    for name, blocks in [("no_law", S.NO_LAW_BLOCKS),
                         ("mass_only", S.MASS_ONLY_BLOCKS),
                         ("confounded", S.CONFOUNDED_BLOCKS)]:
        ids = [w for w in held if W[w]["block"] in blocks]
        out[name] = {"n": len(ids), "reported": sum(held[w]["report"] for w in ids),
                     "reported_with_non_mass_structure": sum(
                         1 for w in ids if held[w]["report"] and held[w]["support"]
                         and set(held[w]["support"]) - {"MASS"})}
    out["by_block"] = {b: {"n": sum(1 for w in held if W[w]["block"] == b),
                           "reported": sum(held[w]["report"] for w in held
                                           if W[w]["block"] == b)}
                       for b in sorted({W[w]["block"] for w in held})}
    return out


def main():
    arch = sys.argv[1] if len(sys.argv) > 1 else "A_CURRENT_FINAL"
    worlds = A.load_worlds()
    W = {w["world_id"]: w for w in worlds}
    preps = {w["world_id"]: A.prep(w) for w in worlds}
    fold = S.assign_folds(worlds)
    all_ids = sorted(W)

    res = {"architecture": arch, "gates": {}}
    held_by_form = {}
    for form in A.GATE_FORMS:
        held = {}
        params = {}
        for f in range(S.N_FOLDS):
            tr = [w for w in all_ids if fold[w] != f]
            te = [w for w in all_ids if fold[w] == f]
            sel_tr = R.run_selection(preps, W, tr, arch)
            sel_te = R.run_selection(preps, W, te, arch)
            rows = [{"world_id": w, "category": S.category(W[w]["block"]),
                     "gate": sel_tr[w]["gate"]} for w in tr]
            g = A.fit_gate1(rows) if form == "CURRENT_GATE" else A.fit_gate2(rows)
            g["form"] = form
            params[str(f)] = g
            for w in te:
                r = dict(sel_te[w])
                r["fold"] = f
                r["report"] = A.apply_gate(g, r["gate"])
                held[w] = r
        res["gates"][form] = {"per_fold_params": params, **evaluate(held, W)}
        held_by_form[form] = held
        e = res["gates"][form]
        print(f"{form:24s} sens {e['sensitivity']:.4f} FPR {e['false_positive_rate']:.4f} "
              f"bal {e['balanced_accuracy']:.4f} sup_e2e {e['all']['t_support_gated']}/{e['all']['n']} "
              f"fam {e['all']['t_family']} fam_e2e {e['all']['t_family_gated']}", flush=True)

    # frozen selection criterion: max sensitivity s.t. FPR <= 5%; ties -> lower FPR
    best = None
    for form in A.GATE_FORMS:
        e = res["gates"][form]
        ok = e["false_positive_rate"] <= A.MAX_NULL_FPR
        # frozen rule (freeze doc 5 and 9.5): FPR <= 5%, then MAXIMISE
        # sensitivity; ON A TIE THE INCUMBENT CURRENT_GATE IS RETAINED.
        key = (0 if ok else 1, -e["sensitivity"], A.GATE_FORMS.index(form))
        if best is None or key < best[0]:
            best = (key, form)
    res["selected_gate"] = best[1]
    print("SELECTED GATE:", best[1], flush=True)

    # ------------------------------------------------- error decomposition --
    held = held_by_form[best[1]]
    hr = {r["world_id"]: r for r in
          json.loads((OUT / "headroom_members.json").read_text())} \
        if (OUT / "headroom_members.json").exists() else {}
    tax, rows = Counter(), []
    for wid in sorted(held):
        w = W[wid]
        if w["block"] not in S.POSITIVE_BLOCKS or not w["scorable"]:
            continue
        r = held[wid]
        P = preps[wid]
        oc_sup = any(m.get("t_support") for m in w["members"])
        oc_fam = any(m.get("t_family") for m in w["members"])
        cl = w["members"][r["rep"]]["cluster"] if r["rep"] is not None else -1
        fam_in_cluster = any(m.get("t_family") for m in w["members"]
                             if m["cluster"] == cl)
        h = hr.get(wid, {})
        refit_rescues = bool(h.get("refit", {}).get("family")) and not oc_fam
        # cross-stratum evidence on the chosen representative
        mm = w["members"][r["rep"]] if r["rep"] is not None else {}
        strat_bad = (mm.get("strat_min_r2") is not None
                     and mm.get("strat_median_r2") is not None
                     and mm["strat_min_r2"] < 0.5 * mm["strat_median_r2"])
        rel = r["t_rel_rmse"]
        near = rel is not None and np.isfinite(rel) and 0.10 < rel <= 0.115
        if not r["report"] and r["t_family"]:
            code = "NULL_GATE_FALSE_NEGATIVE"
        elif not r["report"]:
            code = "NULL_GATE_FALSE_NEGATIVE"
        elif not r["t_support"]:
            code = "SEARCH_FAILURE" if not oc_sup else "FAMILY_AGGREGATION_FAILURE"
        elif not r["t_family"]:
            if not oc_fam and not refit_rescues:
                code = "SEARCH_FAILURE"
            elif refit_rescues:
                code = "CONSTANT_ESTIMATION_FAILURE"
            elif fam_in_cluster:
                code = "REPRESENTATIVE_SELECTION_FAILURE"
            else:
                code = "FAMILY_AGGREGATION_FAILURE"
            if rel is not None and np.isfinite(rel) and rel <= 0.115 \
                    and code != "SEARCH_FAILURE":
                code = "FAMILY_TOLERANCE_BOUNDARY"
            elif strat_bad and code != "SEARCH_FAILURE":
                code = "CROSS_STRATUM_GENERALIZATION_FAILURE"
        else:
            code = "OK"
        tax[code] += 1
        if code != "OK":
            rows.append({
                "world_id": wid, "block": w["block"], "noise": w["noise_regime"],
                "code": code, "expr": r["expr"], "complexity": r["complexity"],
                "valid_r2": r["valid_r2"], "refit_valid_r2": r["refit_valid_r2"],
                "rel_rmse_vs_truth": rel,
                "oracle_support_in_pool": oc_sup, "oracle_family_in_pool": oc_fam,
                "refit_oracle_family_in_pool": bool(h.get("refit", {}).get("family")),
                "family_correct_members_in_chosen_cluster": sum(
                    1 for m in w["members"] if m["cluster"] == cl and m.get("t_family")),
                "family_correct_members_in_pool": sum(
                    1 for m in w["members"] if m.get("t_family")),
                "best_rel_rmse_in_pool": h.get("raw", {}).get("best_rel_rmse"),
                "best_refit_rel_rmse_in_pool": h.get("refit", {}).get("best_rel_rmse"),
                "strat_min_r2": mm.get("strat_min_r2"),
                "strat_median_r2": mm.get("strat_median_r2"),
                "resid_max_abs_spearman": mm.get("resid_max_abs_spearman"),
                "gate_feats": r["gate"], "reported": r["report"]})
    res["error_decomposition"] = {"counts": dict(tax), "rows": rows}
    print(json.dumps(dict(tax), indent=1))

    (OUT / "gate_comparison.json").write_text(json.dumps(res, indent=1, default=str))
    (OUT / "error_decomposition.json").write_text(json.dumps(
        res["error_decomposition"], indent=1, default=str))
    (OUT / "final_held_out.json").write_text(json.dumps(
        {w: {k: v for k, v in r.items() if k != "diag"} for w, r in held.items()},
        indent=1, default=str))


if __name__ == "__main__":
    main()
