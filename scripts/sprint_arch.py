"""FINAL ACCURACY SPRINT — architectures A-D, gates 1-2, nested world-level CV.

Everything here implements MURU_FINAL_ACCURACY_SPRINT_FREEZE.md, which was
written and committed before any number below was computed.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S            # noqa: E402  (frozen baseline machinery)

FEATCACHE = WT / "artifacts" / "sprint" / "candidate_feature_cache.json"

ARCHS = ["A_CURRENT_FINAL", "B_CONSTANT_REFIT", "C_ROBUST_GENERALIZATION",
         "D_SMALL_FAMILY_RANKER"]
ALPHA_GRID = [0.25, 0.5, 1.0]
BETA_GRID = [0.25, 0.5, 1.0]
GAMMA_GRID = [0.25, 0.5, 1.0]
C_GRID = [0.1, 1.0, 10.0]
GATE_FORMS = ["CURRENT_GATE", "MONOTONIC_LINEAR_GATE"]
LIN_COEF_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
MAX_NULL_FPR = 0.05

SCORABLE_BLOCKS = {"G1A", "G1B", "G1C", "G3", "G4M"}


# ------------------------------------------------------------------ load --
def load_worlds():
    worlds = S.load()
    feats = {r["world_id"]: r for r in json.loads(FEATCACHE.read_text())}
    for w in worlds:
        fr = feats[w["world_id"]]
        by = {(f["seed"], f["band_index"]): f for f in fr["features"]}
        for m in w["members"]:
            f = by[(m["seed"], m["band_index"])]
            m["refit_ok"] = bool(f.get("refit_ok"))
            m["refit_valid_r2"] = f.get("refit_valid_r2")
            m["refit_valid_rmse"] = f.get("refit_valid_rmse")
            m["orig_valid_rmse"] = f.get("orig_valid_rmse")
            m["n_params"] = f.get("n_params")
            m["strat_median_r2"] = f.get("strat_median_r2")
            m["strat_min_r2"] = f.get("strat_min_r2")
            m["strat_sd_r2"] = f.get("strat_sd_r2")
            m["strat_worst_norm_rmse"] = f.get("strat_worst_norm_rmse")
            m["n_strata"] = f.get("n_strata")
            m["resid_max_abs_spearman"] = f.get("resid_max_abs_spearman")
            m["resid_med_abs_spearman"] = f.get("resid_med_abs_spearman")
            m["resid_interaction_spearman"] = f.get("resid_interaction_spearman")
            m["computational_failure"] = bool(f.get("computational_failure"))
    return worlds


def q_refit(m):
    """Quality under the deterministic-refit substitution, fail-closed."""
    if m["refit_ok"] and m["refit_valid_r2"] is not None \
            and np.isfinite(m["refit_valid_r2"]):
        return float(m["refit_valid_r2"])
    return float(m["valid_r2"])


# -------------------------------------------------- per-world static prep --
def prep(world):
    """Architecture-independent structures, computed once per world."""
    members = world["members"]
    n_seeds = max(1, world["n_seeds"])
    usable = [i for i, m in enumerate(members) if m["usable"] and m["cluster"] >= 0]
    clusters = {}
    for i in usable:
        clusters.setdefault(members[i]["cluster"], []).append(i)
    supports = {}
    for i in usable:
        supports.setdefault(tuple(members[i]["eff_blocks"]), []).append(i)
    return {"members": members, "n_seeds": n_seeds, "usable": usable,
            "clusters": clusters, "supports": supports,
            "world_id": world["world_id"], "block": world["block"]}


def _seedfrac(members, idxs, n_seeds):
    return len({members[i]["seed"] for i in idxs}) / max(1, n_seeds)


# --------------------------------------------------------- SCORE_C stats --
SCORE_C_FIELDS = ["refit_valid_r2_eff", "strat_median_r2", "strat_sd_r2",
                  "resid_max_abs_spearman"]


def raw_score_fields(m):
    return (q_refit(m), m["strat_median_r2"], m["strat_sd_r2"],
            m["resid_max_abs_spearman"])


def fit_zstats(worlds_subset):
    cols = [[], [], [], []]
    for w in worlds_subset:
        for m in w["members"]:
            if not (m["usable"] and m["cluster"] >= 0):
                continue
            v = raw_score_fields(m)
            for k in range(4):
                if v[k] is not None and np.isfinite(v[k]):
                    cols[k].append(float(v[k]))
    out = []
    for k in range(4):
        a = np.asarray(cols[k], float)
        mu = float(np.mean(a)) if a.size else 0.0
        sd = float(np.std(a)) if a.size else 0.0
        out.append((mu, sd))
    return out


def score_c_array(P, z, abg):
    """SCORE_C for every usable member of a prepared world."""
    a, b, g = abg
    members = P["members"]
    out = {}
    for i in P["usable"]:
        m = members[i]
        v = raw_score_fields(m)
        terms = []
        for k in range(4):
            mu, sd = z[k]
            if v[k] is None or not np.isfinite(v[k]) or sd <= 0:
                terms.append(0.0)
            else:
                terms.append((float(v[k]) - mu) / sd)
        out[i] = terms[0] + a * terms[1] - b * terms[2] - g * terms[3]
    return out


# ------------------------------------------------------------- selection --
def select_ABC(P, arch, z=None, abg=None):
    members, n_seeds = P["members"], P["n_seeds"]
    if not P["usable"]:
        return None, {"n_usable": 0}
    if arch == "A_CURRENT_FINAL":
        q = {i: float(members[i]["valid_r2"]) for i in P["usable"]}
    elif arch == "B_CONSTANT_REFIT":
        q = {i: q_refit(members[i]) for i in P["usable"]}
    else:
        q = score_c_array(P, z, abg)

    # ---- modal support consensus (tie-break on the architecture's quality)
    sup_stats = {}
    for Ssup, idxs in P["supports"].items():
        sup_stats[Ssup] = (_seedfrac(members, idxs, n_seeds),
                           float(np.median([q[i] for i in idxs])),
                           float(np.median([members[i]["complexity"] for i in idxs])))
    Sstar = min(sorted(P["supports"]),
                key=lambda Ss: (-sup_stats[Ss][0], -sup_stats[Ss][1],
                                sup_stats[Ss][2], Ss))
    pool = P["supports"][Sstar]
    groups = {}
    for i in pool:
        groups.setdefault(members[i]["cluster"], []).append(i)

    # ---- family vote -------------------------------------------------
    fam_score = {}
    for gid, idxs in groups.items():
        per_seed = {}
        for i in idxs:
            s = members[i]["seed"]
            per_seed[s] = max(per_seed.get(s, -9e18), q[i])
        if arch == "C_ROBUST_GENERALIZATION":
            fam_score[gid] = float(sum(per_seed.values()))
        else:
            fam_score[gid] = float(sum(max(0.0, v) for v in per_seed.values()) / n_seeds)

    def _repidx(idxs):
        return min(idxs, key=lambda i: (-q[i], members[i]["complexity"],
                                        members[i]["expr"]))

    def _lowcx(idxs):
        # frozen baseline's family tie-break representative
        return min(idxs, key=lambda i: (members[i]["complexity"],
                                        -members[i]["valid_r2"],
                                        members[i]["expr"]))

    c = min(sorted(groups), key=lambda gid: (
        -fam_score[gid], members[_lowcx(groups[gid])]["complexity"],
        members[_lowcx(groups[gid])]["expr"]))
    if arch == "A_CURRENT_FINAL":
        rep = min(groups[c], key=lambda i: (-members[i]["valid_r2"],
                                            members[i]["complexity"],
                                            members[i]["expr"]))
    else:
        rep = _repidx(groups[c])
    ordered = sorted(fam_score.values(), reverse=True)
    runner = ordered[1] if len(ordered) > 1 else 0.0
    diag = {"n_usable": len(P["usable"]), "support": list(Sstar), "cluster": c,
            "support_freq": sup_stats[Sstar][0],
            "sel_frac": _seedfrac(members, groups[c], n_seeds),
            "fam_score": fam_score[c], "margin": float(fam_score[c] - runner)}
    return rep, diag


# ------------------------------------------------------- D: family ranker --
D_FEATURES = ["n_seeds_f", "selection_fraction", "sum_seed_best_raw_r2",
              "median_raw_r2", "sd_raw_r2", "sum_seed_best_refit_r2",
              "median_refit_r2", "median_strat_median_r2",
              "median_strat_min_r2", "median_strat_sd_r2",
              "median_resid_max_abs_spearman", "min_complexity",
              "median_complexity"]


def _med(vals):
    v = [float(x) for x in vals if x is not None and np.isfinite(x)]
    return float(np.median(v)) if v else float("nan")


def d_family_rows(P):
    """One feature row per Type 2 cluster in the world, plus its rep index."""
    members, n_seeds = P["members"], P["n_seeds"]
    rows = []
    for gid in sorted(P["clusters"]):
        idxs = P["clusters"][gid]
        seeds = {members[i]["seed"] for i in idxs}
        raw = [float(members[i]["valid_r2"]) for i in idxs]
        ref = [q_refit(members[i]) for i in idxs]
        per_seed_raw, per_seed_ref = {}, {}
        for i in idxs:
            s = members[i]["seed"]
            per_seed_raw[s] = max(per_seed_raw.get(s, -9e18), float(members[i]["valid_r2"]))
            per_seed_ref[s] = max(per_seed_ref.get(s, -9e18), q_refit(members[i]))
        rep = min(idxs, key=lambda i: (-q_refit(members[i]),
                                       members[i]["complexity"], members[i]["expr"]))
        f = {
            "n_seeds_f": float(len(seeds)),
            "selection_fraction": len(seeds) / max(1, n_seeds),
            "sum_seed_best_raw_r2": float(sum(max(0.0, v) for v in per_seed_raw.values())),
            "median_raw_r2": float(np.median(raw)),
            "sd_raw_r2": float(np.std(raw, ddof=1)) if len(raw) > 1 else 0.0,
            "sum_seed_best_refit_r2": float(sum(max(0.0, v) for v in per_seed_ref.values())),
            "median_refit_r2": float(np.median(ref)),
            "median_strat_median_r2": _med([members[i]["strat_median_r2"] for i in idxs]),
            "median_strat_min_r2": _med([members[i]["strat_min_r2"] for i in idxs]),
            "median_strat_sd_r2": _med([members[i]["strat_sd_r2"] for i in idxs]),
            "median_resid_max_abs_spearman":
                _med([members[i]["resid_max_abs_spearman"] for i in idxs]),
            "min_complexity": float(min(members[i]["complexity"] for i in idxs)),
            "median_complexity": float(np.median([members[i]["complexity"] for i in idxs])),
        }
        rows.append({"cluster": gid, "rep": rep, "x": [f[k] for k in D_FEATURES],
                     "sel_frac": f["selection_fraction"],
                     "min_cx": f["min_complexity"],
                     "expr": members[rep]["expr"]})
    return rows


def d_training_matrix(preps, worlds_by_id, wids):
    X, y = [], []
    for wid in sorted(wids):
        w = worlds_by_id[wid]
        if w["block"] not in SCORABLE_BLOCKS or not w["scorable"]:
            continue
        P = preps[wid]
        for r in d_family_rows(P):
            X.append(r["x"])
            y.append(1 if bool(P["members"][r["rep"]].get("t_family")) else 0)
    return np.asarray(X, float), np.asarray(y, int)


def fit_d(X, y, creg):
    from sklearn.linear_model import LogisticRegression
    med = np.nanmedian(np.where(np.isfinite(X), X, np.nan), axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    Xi = np.where(np.isfinite(X), X, med)
    mu, sd = Xi.mean(axis=0), Xi.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (Xi - mu) / sd
    if y.sum() == 0 or y.sum() == len(y):
        return {"trivial": int(y[0]) if len(y) else 0, "med": med.tolist(),
                "mu": mu.tolist(), "sd": sd.tolist(), "coef": None, "b": None}
    m = LogisticRegression(C=creg, penalty="l2", solver="lbfgs", max_iter=5000)
    m.fit(Z, y)
    return {"trivial": None, "med": med.tolist(), "mu": mu.tolist(),
            "sd": sd.tolist(), "coef": m.coef_[0].tolist(),
            "b": float(m.intercept_[0])}


def d_predict(model, x):
    x = np.asarray(x, float)
    med = np.asarray(model["med"], float)
    x = np.where(np.isfinite(x), x, med)
    z = (x - np.asarray(model["mu"], float)) / np.asarray(model["sd"], float)
    if model["coef"] is None:
        return float(model["trivial"])
    t = float(np.dot(z, np.asarray(model["coef"], float)) + model["b"])
    return 1.0 / (1.0 + math.exp(-max(-500.0, min(500.0, -t))))


def select_D(P, model):
    if not P["usable"]:
        return None, {"n_usable": 0}
    rows = d_family_rows(P)
    for r in rows:
        r["p"] = d_predict(model, r["x"])
    best = min(rows, key=lambda r: (-r["p"], -r["sel_frac"], r["min_cx"], r["expr"]))
    ordered = sorted((r["p"] for r in rows), reverse=True)
    runner = ordered[1] if len(ordered) > 1 else 0.0
    return best["rep"], {"n_usable": len(P["usable"]),
                         "support": P["members"][best["rep"]]["eff_blocks"],
                         "cluster": best["cluster"],
                         "support_freq": best["sel_frac"],
                         "sel_frac": best["sel_frac"], "fam_score": best["p"],
                         "margin": float(best["p"] - runner)}


# ------------------------------------------------------------------ gates --
def gate_feats(world, diag):
    br = [s["best_valid_r2"] for s in world["seeds"]
          if s["best_valid_r2"] == s["best_valid_r2"]]
    return {"median_seed_best_r2": float(np.median(br)) if br else float("nan"),
            "selection_fraction": float(diag.get("sel_frac") or 0.0),
            "family_quality_margin": float(diag.get("margin") or 0.0)}


def fit_gate1(rows):
    return S.fit_gate(rows)


def apply_gate1(g, f):
    return bool(f["median_seed_best_r2"] >= g["t1"]
                and f["selection_fraction"] >= g["t2"])


def _gate2_z(rows):
    A = np.array([[r["gate"]["median_seed_best_r2"], r["gate"]["selection_fraction"],
                   r["gate"]["family_quality_margin"]] for r in rows], float)
    A = np.where(np.isfinite(A), A, 0.0)
    mu, sd = A.mean(axis=0), A.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return mu, sd


def fit_gate2(rows):
    pos = [r for r in rows if r["category"] == "positive"]
    nul = [r for r in rows if r["category"] == "null"]
    if not pos or not nul:
        return {"form": "MONOTONIC_LINEAR_GATE", "a": 1.0, "b": 0.0, "c": 0.0,
                "thr": 0.0, "mu": [0, 0, 0], "sd": [1, 1, 1],
                "train_sens": float("nan"), "train_fpr": float("nan")}
    mu, sd = _gate2_z(rows)

    def Z(rs):
        A = np.array([[r["gate"]["median_seed_best_r2"],
                       r["gate"]["selection_fraction"],
                       r["gate"]["family_quality_margin"]] for r in rs], float)
        A = np.where(np.isfinite(A), A, 0.0)
        return (A - mu) / sd

    Zp, Zn = Z(pos), Z(nul)
    best = None
    for a in LIN_COEF_GRID:
        for b in LIN_COEF_GRID:
            for c in LIN_COEF_GRID:
                t = a + b + c
                if t <= 0:
                    continue
                wv = np.array([a, b, c]) / t
                sp_, sn_ = Zp @ wv, Zn @ wv
                cand = np.unique(np.concatenate([sp_, sn_]))
                for thr in cand:
                    fpr = float(np.mean(sn_ >= thr))
                    if fpr > MAX_NULL_FPR:
                        continue
                    sens = float(np.mean(sp_ >= thr))
                    k = (-sens, fpr, -float(a), -float(b), -float(c), -float(thr))
                    if best is None or k < best[0]:
                        best = (k, {"form": "MONOTONIC_LINEAR_GATE",
                                    "a": float(wv[0]), "b": float(wv[1]),
                                    "c": float(wv[2]), "thr": float(thr),
                                    "mu": mu.tolist(), "sd": sd.tolist(),
                                    "train_sens": sens, "train_fpr": fpr})
    if best is None:
        return {"form": "MONOTONIC_LINEAR_GATE", "a": 1.0, "b": 0.0, "c": 0.0,
                "thr": 1e9, "mu": mu.tolist(), "sd": sd.tolist(),
                "train_sens": 0.0, "train_fpr": 0.0}
    return best[1]


def apply_gate2(g, f):
    v = np.array([f["median_seed_best_r2"], f["selection_fraction"],
                  f["family_quality_margin"]], float)
    v = np.where(np.isfinite(v), v, 0.0)
    z = (v - np.asarray(g["mu"], float)) / np.asarray(g["sd"], float)
    return bool(float(np.dot(z, [g["a"], g["b"], g["c"]])) >= g["thr"])


def apply_gate(g, f):
    return apply_gate1(g, f) if g.get("form", "CURRENT_GATE") == "CURRENT_GATE" \
        else apply_gate2(g, f)


# ------------------------------------------------------------------ folds --
def inner_folds(worlds, wids):
    sub = [w for w in worlds if w["world_id"] in wids]
    return S.assign_folds(sub)


def wilson(k, n):
    return S.wilson(k, n)
