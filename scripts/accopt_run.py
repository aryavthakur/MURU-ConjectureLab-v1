"""ACCURACY OPTIMIZATION — Stage 3: baseline, cross-validated model selection,
refusal gate, failure taxonomy, oracle ceilings."""
from __future__ import annotations

import json, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S

OUT = WT / "artifacts" / "accopt"
ARCHS = ["BASELINE_30", "SUPPORT_CONSENSUS", "SUPPORT_PLUS_FAMILY_CONSENSUS",
         "CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE",
         "CONSENSUS_PLUS_REPRESENTATIVE_PLUS_REFUSAL_GATE"]
FAM_VOTES = ["B1", "B2", "B3"]
REP_RULES = ["R1", "R2"]


def run_arch(worlds, arch, fam_vote, rep_rule):
    out = {}
    for w in worlds:
        rep, diag = S.select_world(w, arch if arch != ARCHS[4] else ARCHS[3],
                                   fam_vote, rep_rule)
        m = w["members"][rep] if rep is not None else None
        out[w["world_id"]] = {
            "rep": rep, "diag": diag,
            "gate": S.gate_features(w, diag),
            "expr": m["expr"] if m else None,
            "complexity": m["complexity"] if m else None,
            "valid_r2": m["valid_r2"] if m else None,
            "support": m["eff_blocks"] if m else None,
            "t_support": bool(m.get("t_support")) if m and w["scorable"] else None,
            "t_family": bool(m.get("t_family")) if m and w["scorable"] else None,
            "t_exact": bool(m.get("t_exact")) if m and w["scorable"] else None,
            "t_rel_rmse": m.get("t_rel_rmse") if m and w["scorable"] else None,
        }
    return out


def rates(worlds, sel, wids, key, blocks=None):
    n = k = 0
    for w in worlds:
        if w["world_id"] not in wids or not w["scorable"]:
            continue
        if blocks and w["block"] not in blocks:
            continue
        r = sel[w["world_id"]]
        if r[key] is None:
            continue
        n += 1; k += bool(r[key])
    return k, n


def main():
    worlds = S.load()
    W = {w["world_id"]: w for w in worlds}
    fold = S.assign_folds(worlds)
    pos_ids = [w["world_id"] for w in worlds if w["block"] in S.POSITIVE_BLOCKS]
    all_ids = set(W)

    # ---------------- ORACLE CEILINGS -----------------------------------
    oracle = {}
    for w in worlds:
        if not w["scorable"]:
            continue
        oracle[w["world_id"]] = {
            "support": any(m.get("t_support") for m in w["members"]),
            "family": any(m.get("t_family") for m in w["members"]),
            "exact": any(m.get("t_exact") for m in w["members"]),
        }

    # ---------------- run every predefined variant on every world -------
    runs = {}
    runs[("BASELINE_30", "-", "-")] = run_arch(worlds, "BASELINE_30", "B1", "R2")
    runs[("SUPPORT_CONSENSUS", "-", "-")] = run_arch(worlds, "SUPPORT_CONSENSUS", "B1", "R2")
    for fv in FAM_VOTES:
        runs[("SUPPORT_PLUS_FAMILY_CONSENSUS", fv, "-")] = run_arch(
            worlds, "SUPPORT_PLUS_FAMILY_CONSENSUS", fv, "R2")
        for rr in REP_RULES:
            runs[("CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE", fv, rr)] = run_arch(
                worlds, "CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE", fv, rr)
    print("variants run:", len(runs), flush=True)

    # ---------------- full-data (all 30 seeds) summary per variant ------
    variant_summary = {}
    for k, sel in runs.items():
        row = {}
        for lbl, blocks in [("all", S.POSITIVE_BLOCKS), ("G1A", {"G1A"}),
                            ("G1B", {"G1B"}), ("G1C", {"G1C"}), ("G3", {"G3"}),
                            ("G4M", {"G4M"})]:
            for metric in ("t_support", "t_family", "t_exact"):
                a, b = rates(worlds, sel, all_ids, metric, blocks)
                row[f"{lbl}_{metric}"] = [a, b]
        variant_summary["|".join(k)] = row
    (OUT / "variant_summary.json").write_text(json.dumps(variant_summary, indent=1))

    # ---------------- nested CV: choose variant on TRAIN, score on TEST -
    cv_choice, held = {}, {}
    for f in range(S.N_FOLDS):
        tr = {wid for wid in all_ids if fold[wid] != f}
        te = {wid for wid in all_ids if fold[wid] == f}
        # family recovery on training positives picks the family vote and rep rule
        best = None
        for fv in FAM_VOTES:
            for rr in REP_RULES:
                sel = runs[("CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE", fv, rr)]
                fk, fn = rates(worlds, sel, tr, "t_family", S.POSITIVE_BLOCKS)
                sk, sn = rates(worlds, sel, tr, "t_support", S.POSITIVE_BLOCKS)
                key = (-(fk / max(fn, 1)), -(sk / max(sn, 1)), fv, rr)
                if best is None or key < best[0]:
                    best = (key, fv, rr)
        _, fv, rr = best
        sel = runs[("CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE", fv, rr)]
        rows = [{"world_id": wid, "category": S.category(W[wid]["block"]),
                 "gate": sel[wid]["gate"]} for wid in sorted(tr)]
        g = S.fit_gate(rows)
        cv_choice[f] = {"fam_vote": fv, "rep_rule": rr, "gate": g,
                        "n_train": len(tr), "n_test": len(te)}
        for wid in te:
            held[wid] = {"fold": f, "fam_vote": fv, "rep_rule": rr, "gate": g,
                         "report": S.apply_gate(g, sel[wid]["gate"]),
                         **{k2: sel[wid][k2] for k2 in
                            ("t_support", "t_family", "t_exact", "expr",
                             "complexity", "valid_r2", "support", "rep",
                             "t_rel_rmse")},
                         "gate_feats": sel[wid]["gate"], "diag": sel[wid]["diag"]}
    print("cv folds fitted", flush=True)

    # pooled held-out selector accuracy (identical across gate, gate only
    # changes whether a world is reported)
    def held_rate(metric, blocks, gated=False):
        n = k = 0
        for wid, r in held.items():
            w = W[wid]
            if not w["scorable"] or w["block"] not in blocks:
                continue
            if r[metric] is None:
                continue
            n += 1
            v = bool(r[metric]) and (r["report"] if gated else True)
            k += v
        return k, n

    result = {"n_worlds": len(worlds), "folds": {str(k): v for k, v in cv_choice.items()},
              "oracle": {}, "baseline_30": {}, "held_out": {}, "gate": {}}

    for lbl, blocks in [("all", S.POSITIVE_BLOCKS), ("G1A", {"G1A"}),
                        ("G1B", {"G1B"}), ("G1C", {"G1C"}), ("G3", {"G3"}),
                        ("G4M", {"G4M"})]:
        ids = [w["world_id"] for w in worlds
               if w["block"] in blocks and w["scorable"]]
        result["oracle"][lbl] = {
            "n": len(ids),
            "support": sum(oracle[i]["support"] for i in ids),
            "family": sum(oracle[i]["family"] for i in ids),
            "exact": sum(oracle[i]["exact"] for i in ids)}
        base = runs[("BASELINE_30", "-", "-")]
        result["baseline_30"][lbl] = {
            m: rates(worlds, base, all_ids, m, blocks)
            for m in ("t_support", "t_family", "t_exact")}
        result["held_out"][lbl] = {
            m: held_rate(m, blocks) for m in ("t_support", "t_family", "t_exact")}
        result["held_out"][lbl].update({
            m + "_gated": held_rate(m, blocks, True)
            for m in ("t_support", "t_family", "t_exact")})

    # ---------------- gate performance, pooled held-out -----------------
    def cat_ids(cats):
        return [wid for wid in held if S.category(W[wid]["block"]) in cats]

    pos = cat_ids({"positive"}); nul = cat_ids({"null"}); ref = cat_ids({"refusal"})
    tp = sum(held[i]["report"] for i in pos)
    fp = sum(held[i]["report"] for i in nul)
    sens = tp / len(pos); fpr = fp / len(nul)
    scores1 = [held[i]["gate_feats"]["median_seed_best_r2"] for i in pos + nul]
    scores2 = [held[i]["gate_feats"]["selection_fraction"] for i in pos + nul]
    labels = [1] * len(pos) + [0] * len(nul)
    result["gate"] = {
        "rule": "REPORT iff median_seed_best_r2 >= t1 AND selection_fraction >= t2",
        "per_fold_thresholds": {str(k): v["gate"] for k, v in cv_choice.items()},
        "n_positive": len(pos), "n_null": len(nul), "n_refusal": len(ref),
        "sensitivity": sens, "sensitivity_ci": S.wilson(tp, len(pos)),
        "specificity": 1 - fpr, "false_positive_rate": fpr,
        "fpr_ci": S.wilson(fp, len(nul)),
        "false_negative_rate": 1 - sens,
        "balanced_accuracy": 0.5 * (sens + (1 - fpr)),
        "roc_auc_median_seed_best_r2": S.auc_roc(scores1, labels),
        "pr_auc_median_seed_best_r2": S.auc_pr(scores1, labels),
        "roc_auc_selection_fraction": S.auc_roc(scores2, labels),
        "pr_auc_selection_fraction": S.auc_pr(scores2, labels),
        "by_block": {},
    }
    for b in sorted({w["block"] for w in worlds}):
        ids = [wid for wid in held if W[wid]["block"] == b]
        result["gate"]["by_block"][b] = {
            "n": len(ids), "reported": sum(held[i]["report"] for i in ids)}
    # finer semantics
    for name, blocks in [("no_law", S.NO_LAW_BLOCKS), ("mass_only", S.MASS_ONLY_BLOCKS),
                         ("confounded", S.CONFOUNDED_BLOCKS)]:
        ids = [wid for wid in held if W[wid]["block"] in blocks]
        rep_n = sum(held[i]["report"] for i in ids)
        nonmass = sum(1 for i in ids if held[i]["report"] and held[i]["support"]
                      and set(held[i]["support"]) - {"MASS"})
        result["gate"]["by_block"][f"__{name}__"] = {
            "n": len(ids), "reported": rep_n,
            "reported_with_non_mass_structure": nonmass}

    # ---------------- baseline gate behaviour (no gate = always reports)
    result["baseline_report_rates"] = {
        "positive": [len(pos), len(pos)], "null": [len(nul), len(nul)],
        "refusal": [len(ref), len(ref)]}

    # ---------------- failure taxonomy on positives ---------------------
    tax = Counter(); tax_rows = []
    for wid in pos:
        w = W[wid]; r = held[wid]
        oc = oracle[wid]
        pb = set(w.get("planted_blocks", []))
        chosen = set(r["support"] or [])
        cl = w["members"][r["rep"]]["cluster"] if r["rep"] is not None else -1
        fam_in_cluster = any(m.get("t_family") for m in w["members"]
                             if m["cluster"] == cl)
        code = None
        if not r["report"]:
            code = "NULL_GATE_FAILURE"
        elif not r["t_support"]:
            code = "SEARCH_FAILURE_SUPPORT" if not oc["support"] else "SUPPORT_SELECTION_FAILURE"
        elif not r["t_family"]:
            if not oc["family"]:
                code = "SEARCH_FAILURE_FAMILY"
            elif fam_in_cluster:
                code = "REPRESENTATIVE_FAILURE"
            else:
                code = "FAMILY_SELECTION_FAILURE"
            if (r["t_rel_rmse"] is not None and np.isfinite(r["t_rel_rmse"])
                    and r["t_rel_rmse"] <= 0.10 and code != "SEARCH_FAILURE_FAMILY"):
                code += "|NUMERICALLY_CLOSE"
        else:
            code = "OK"
        tax[code] += 1
        if code != "OK":
            tax_rows.append({"world_id": wid, "block": w["block"],
                             "noise": w["noise_regime"], "code": code,
                             "planted_blocks": sorted(pb),
                             "chosen_blocks": sorted(chosen),
                             "oracle_support": oc["support"],
                             "oracle_family": oc["family"],
                             "expr": r["expr"], "valid_r2": r["valid_r2"],
                             "rel_rmse": r["t_rel_rmse"],
                             "gate_feats": r["gate_feats"]})
    result["failure_taxonomy"] = dict(tax)
    result["failure_rows"] = tax_rows

    # ---------------- per-seed availability of correct structure --------
    avail = []
    for w in worlds:
        if w["block"] not in S.POSITIVE_BLOCKS or not w["scorable"]:
            continue
        seeds_sup = len({m["seed"] for m in w["members"] if m.get("t_support")})
        seeds_fam = len({m["seed"] for m in w["members"] if m.get("t_family")})
        avail.append({"world_id": w["world_id"], "block": w["block"],
                      "n_seeds": w["n_seeds"], "seeds_with_correct_support": seeds_sup,
                      "seeds_with_correct_family": seeds_fam,
                      "n_members": len(w["members"])})
    result["seed_availability"] = avail

    result["variant_summary"] = variant_summary
    (OUT / "run_result.json").write_text(json.dumps(result, indent=1, default=str))
    json.dump({wid: {k: v for k, v in r.items() if k != "diag"}
               for wid, r in held.items()},
              open(OUT / "held_out_selections.json", "w"), indent=1, default=str)
    print(json.dumps({k: result[k] for k in
                      ("oracle", "baseline_30", "held_out", "failure_taxonomy")},
                     indent=1, default=str))
    print("\nGATE:", json.dumps(result["gate"], indent=1, default=str)[:2500])


if __name__ == "__main__":
    main()
