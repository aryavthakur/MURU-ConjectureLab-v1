"""FINAL ACCURACY SPRINT — nested world-level CV over architectures A-D."""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S      # noqa: E402
import sprint_arch as A          # noqa: E402

OUT = WT / "artifacts" / "sprint"
OUT.mkdir(parents=True, exist_ok=True)


def score_selection(P, rep):
    m = P["members"][rep] if rep is not None else None
    return {"rep": rep, "expr": m["expr"] if m else None,
            "complexity": m["complexity"] if m else None,
            "valid_r2": m["valid_r2"] if m else None,
            "refit_valid_r2": m["refit_valid_r2"] if m else None,
            "support": m["eff_blocks"] if m else None,
            "cluster": m["cluster"] if m else None,
            "t_support": bool(m.get("t_support")) if m else None,
            "t_family": bool(m.get("t_family")) if m else None,
            "t_exact": bool(m.get("t_exact")) if m else None,
            "t_rel_rmse": m.get("t_rel_rmse") if m else None}


def run_selection(preps, worlds_by_id, wids, arch, z=None, abg=None, dmodel=None):
    out = {}
    for wid in wids:
        P = preps[wid]
        if arch == "D_SMALL_FAMILY_RANKER":
            rep, diag = A.select_D(P, dmodel)
        else:
            rep, diag = A.select_ABC(P, arch, z=z, abg=abg)
        r = score_selection(P, rep)
        r["diag"] = diag
        r["gate"] = A.gate_feats(worlds_by_id[wid], diag)
        out[wid] = r
    return out


def fam_rate(sel, worlds_by_id, wids, key="t_family", blocks=None):
    n = k = 0
    for wid in wids:
        w = worlds_by_id[wid]
        if not w["scorable"]:
            continue
        if blocks and w["block"] not in blocks:
            continue
        r = sel.get(wid)
        if r is None or r[key] is None:
            continue
        n += 1
        k += bool(r[key])
    return k, n


def main():
    t0 = time.time()
    worlds = A.load_worlds()
    W = {w["world_id"]: w for w in worlds}
    preps = {w["world_id"]: A.prep(w) for w in worlds}
    fold = S.assign_folds(worlds)
    all_ids = sorted(W)
    POS = S.POSITIVE_BLOCKS
    print(f"loaded {len(worlds)} worlds  {time.time()-t0:.0f}s", flush=True)

    nested = {"outer_folds": {}, "architectures": {}}
    held = {a: {} for a in A.ARCHS}
    gate_choice = {}

    for f in range(S.N_FOLDS):
        tr = [w for w in all_ids if fold[w] != f]
        te = [w for w in all_ids if fold[w] == f]
        tr_worlds = [W[w] for w in tr]
        inner = A.inner_folds(worlds, set(tr))
        rec = {"n_train": len(tr), "n_test": len(te)}

        # ---------- C: inner CV over (alpha, beta, gamma) ----------------
        best_abg, best_key = None, None
        inner_scores = {}
        for g_i in range(S.N_FOLDS):
            itr = [w for w in tr if inner[w] != g_i]
            ite = [w for w in tr if inner[w] == g_i]
            z = A.fit_zstats([W[w] for w in itr])
            for a_ in A.ALPHA_GRID:
                for b_ in A.BETA_GRID:
                    for c_ in A.GAMMA_GRID:
                        sel = run_selection(preps, W, ite,
                                            "C_ROBUST_GENERALIZATION",
                                            z=z, abg=(a_, b_, c_))
                        k, n = fam_rate(sel, W, ite, "t_family", POS)
                        ks, ns = fam_rate(sel, W, ite, "t_support", POS)
                        acc = inner_scores.setdefault((a_, b_, c_), [0, 0, 0, 0])
                        acc[0] += k; acc[1] += n; acc[2] += ks; acc[3] += ns
        for abg, (k, n, ks, ns) in sorted(inner_scores.items()):
            key = (-(k / max(n, 1)), -(ks / max(ns, 1)), abg)
            if best_key is None or key < best_key:
                best_key, best_abg = key, abg
        rec["C_abg"] = list(best_abg)
        rec["C_inner"] = {str(k2): v for k2, v in sorted(inner_scores.items())}

        # ---------- D: inner CV over regularization C --------------------
        best_creg, bk = None, None
        d_inner = {}
        for g_i in range(S.N_FOLDS):
            itr = [w for w in tr if inner[w] != g_i]
            ite = [w for w in tr if inner[w] == g_i]
            Xtr, ytr = A.d_training_matrix(preps, W, set(itr))
            for creg in A.C_GRID:
                model = A.fit_d(Xtr, ytr, creg)
                sel = run_selection(preps, W, ite, "D_SMALL_FAMILY_RANKER",
                                    dmodel=model)
                k, n = fam_rate(sel, W, ite, "t_family", POS)
                ks, ns = fam_rate(sel, W, ite, "t_support", POS)
                acc = d_inner.setdefault(creg, [0, 0, 0, 0])
                acc[0] += k; acc[1] += n; acc[2] += ks; acc[3] += ns
        for creg, (k, n, ks, ns) in sorted(d_inner.items()):
            key = (-(k / max(n, 1)), -(ks / max(ns, 1)), creg)
            if bk is None or key < bk:
                bk, best_creg = key, creg
        rec["D_C"] = best_creg
        rec["D_inner"] = {str(k2): v for k2, v in sorted(d_inner.items())}

        # ---------- fit final per-architecture params on the whole train --
        z_full = A.fit_zstats(tr_worlds)
        Xtr, ytr = A.d_training_matrix(preps, W, set(tr))
        dmodel = A.fit_d(Xtr, ytr, best_creg)
        rec["D_n_train_rows"] = int(len(ytr))
        rec["D_pos_rate"] = float(ytr.mean()) if len(ytr) else float("nan")
        rec["D_coef"] = dict(zip(A.D_FEATURES, dmodel["coef"])) if dmodel["coef"] else None

        for arch in A.ARCHS:
            kw = {}
            if arch == "C_ROBUST_GENERALIZATION":
                kw = {"z": z_full, "abg": best_abg}
            if arch == "D_SMALL_FAMILY_RANKER":
                kw = {"dmodel": dmodel}
            sel_tr = run_selection(preps, W, tr, arch, **kw)
            sel_te = run_selection(preps, W, te, arch, **kw)

            # ---- gate: inner CV chooses the FORM, train fold fits it -----
            form_score = {}
            for g_i in range(S.N_FOLDS):
                itr = [w for w in tr if inner[w] != g_i]
                ite = [w for w in tr if inner[w] == g_i]
                rows_tr = [{"world_id": w, "category": S.category(W[w]["block"]),
                            "gate": sel_tr[w]["gate"]} for w in itr]
                g1 = A.fit_gate1(rows_tr); g1["form"] = "CURRENT_GATE"
                g2 = A.fit_gate2(rows_tr)
                for name, g in (("CURRENT_GATE", g1), ("MONOTONIC_LINEAR_GATE", g2)):
                    tp = fp = npos = nnul = 0
                    for w in ite:
                        cat = S.category(W[w]["block"])
                        rep = A.apply_gate(g, sel_tr[w]["gate"])
                        if cat == "positive":
                            npos += 1; tp += rep
                        elif cat == "null":
                            nnul += 1; fp += rep
                    acc = form_score.setdefault(name, [0, 0, 0, 0])
                    acc[0] += tp; acc[1] += npos; acc[2] += fp; acc[3] += nnul
            chosen = None
            for name in A.GATE_FORMS:
                tp, npos, fp, nnul = form_score[name]
                sens = tp / max(npos, 1); fpr = fp / max(nnul, 1)
                ok = fpr <= A.MAX_NULL_FPR
                key = (0 if ok else 1, -sens, fpr, A.GATE_FORMS.index(name))
                if chosen is None or key < chosen[0]:
                    chosen = (key, name)
            gform = chosen[1]
            rows_tr = [{"world_id": w, "category": S.category(W[w]["block"]),
                        "gate": sel_tr[w]["gate"]} for w in tr]
            gfit = A.fit_gate1(rows_tr) if gform == "CURRENT_GATE" else A.fit_gate2(rows_tr)
            gfit["form"] = gform
            gate_choice.setdefault(arch, {})[f] = {
                "form": gform, "params": gfit,
                "inner": {k2: v for k2, v in form_score.items()}}

            for w in te:
                r = dict(sel_te[w])
                r["fold"] = f
                r["report"] = A.apply_gate(gfit, r["gate"])
                r["gate_form"] = gform
                held[arch][w] = r
        nested["outer_folds"][str(f)] = rec
        print(f"  fold {f} done  C={best_abg} D_C={best_creg}  "
              f"{time.time()-t0:.0f}s", flush=True)

    # ------------------------------------------------------ metrics -------
    def metrics(arch):
        h = held[arch]
        res = {}
        groups = [("all", POS, None), ("G1A", {"G1A"}, None), ("G1B", {"G1B"}, None),
                  ("G1C", {"G1C"}, None),
                  ("G1B_low", {"G1B"}, "low"), ("G1B_moderate", {"G1B"}, "moderate"),
                  ("G1B_adverse", {"G1B"}, "adverse"),
                  ("G3", {"G3"}, None), ("G4M", {"G4M"}, None)]
        for lbl, blocks, noise in groups:
            ids = [w for w in h if W[w]["block"] in blocks and W[w]["scorable"]
                   and (noise is None or W[w]["noise_regime"] == noise)]
            row = {"n": len(ids)}
            for met in ("t_support", "t_family", "t_exact"):
                row[met] = sum(1 for w in ids if h[w][met])
                row[met + "_gated"] = sum(1 for w in ids
                                          if h[w][met] and h[w]["report"])
            res[lbl] = row
        pos = [w for w in h if S.category(W[w]["block"]) == "positive"]
        nul = [w for w in h if S.category(W[w]["block"]) == "null"]
        ref = [w for w in h if S.category(W[w]["block"]) == "refusal"]
        tp = sum(h[w]["report"] for w in pos)
        fp = sum(h[w]["report"] for w in nul)
        sens = tp / len(pos); fpr = fp / len(nul)
        sc = [h[w]["gate"]["median_seed_best_r2"] for w in pos + nul]
        lab = [1] * len(pos) + [0] * len(nul)
        res["gate"] = {
            "sensitivity": sens, "sensitivity_ci": A.wilson(tp, len(pos)),
            "specificity": 1 - fpr, "false_positive_rate": fpr,
            "fpr_ci": A.wilson(fp, len(nul)), "false_negative_rate": 1 - sens,
            "balanced_accuracy": 0.5 * (sens + 1 - fpr),
            "roc_auc": S.auc_roc(sc, lab), "pr_auc": S.auc_pr(sc, lab),
            "n_positive": len(pos), "n_null": len(nul), "n_refusal": len(ref),
            "forms": {str(k): v["form"] for k, v in gate_choice[arch].items()},
            "by_block": {b: {"n": sum(1 for w in h if W[w]["block"] == b),
                             "reported": sum(h[w]["report"] for w in h
                                             if W[w]["block"] == b)}
                         for b in sorted({W[w]["block"] for w in h})},
        }
        for name, blocks in [("no_law", S.NO_LAW_BLOCKS),
                             ("mass_only", S.MASS_ONLY_BLOCKS),
                             ("confounded", S.CONFOUNDED_BLOCKS)]:
            ids = [w for w in h if W[w]["block"] in blocks]
            res["gate"]["by_block"][f"__{name}__"] = {
                "n": len(ids), "reported": sum(h[w]["report"] for w in ids),
                "reported_with_non_mass_structure": sum(
                    1 for w in ids if h[w]["report"] and h[w]["support"]
                    and set(h[w]["support"]) - {"MASS"})}
        k, n = res["all"]["t_family"], res["all"]["n"]
        res["family_ci"] = A.wilson(k, n)
        res["support_ci"] = A.wilson(res["all"]["t_support"], n)
        return res

    for arch in A.ARCHS:
        nested["architectures"][arch] = metrics(arch)
        r = nested["architectures"][arch]
        print(f"{arch:26s} sup {r['all']['t_support']}/{r['all']['n']} "
              f"(gated {r['all']['t_support_gated']}) fam {r['all']['t_family']} "
              f"(gated {r['all']['t_family_gated']}) exact {r['all']['t_exact']} "
              f"| G1A {r['G1A']['t_family']}/{r['G1A']['n']} "
              f"G1B {r['G1B']['t_family']}/{r['G1B']['n']} "
              f"G1C {r['G1C']['t_family']}/{r['G1C']['n']} "
              f"| FPR {r['gate']['false_positive_rate']:.4f} "
              f"sens {r['gate']['sensitivity']:.4f} AUC {r['gate']['roc_auc']:.4f} "
              f"form {sorted(set(r['gate']['forms'].values()))}", flush=True)

    (OUT / "nested_cv_results.json").write_text(json.dumps(nested, indent=1, default=str))
    (OUT / "outer_fold_predictions.json").write_text(json.dumps(
        {a: {w: {k: v for k, v in r.items() if k != "diag"}
             for w, r in held[a].items()} for a in A.ARCHS}, indent=1, default=str))
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
