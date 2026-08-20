"""ACCURACY OPTIMIZATION — Stage 2: selector architectures + CV + refusal gate.

Every architecture and every gate feature below is DEFINED HERE, before any
cross-validated result is compared. Selectors read only outcome-independent
candidate statistics. Truth fields in the cache are used exclusively to SCORE a
selection after it is made.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

WT = Path(__file__).resolve().parents[1]
CACHE = WT / "artifacts" / "accopt" / "candidate_cache.json"

POSITIVE_BLOCKS = {"G1A", "G1B", "G1C"}
NULL_BLOCKS = {"G4", "G4M", "NCAL"}
REFUSAL_BLOCKS = {"G2", "G3", "G5", "GC", "GRT"}
NO_LAW_BLOCKS = {"NCAL", "G4", "GC"}
MASS_ONLY_BLOCKS = {"G3", "G4M"}
CONFOUNDED_BLOCKS = {"G5", "GRT", "G2"}

N_FOLDS = 5
BAND_TOL = 0.01               # frozen; identical to the production band tolerance
STAB_SUBSETS = 200            # deterministic seed-subsets for the stability vote
STAB_SUBSET_SIZE = 15


def category(block):
    if block in POSITIVE_BLOCKS:
        return "positive"
    if block in NULL_BLOCKS:
        return "null"
    return "refusal"


# ---------------------------------------------------------------- CV folds --
def assign_folds(worlds):
    """Deterministic stratified 5-fold BY WORLD. All 30 seeds of a world stay
    together, because a world is the unit the selector acts on."""
    strata = {}
    for w in worlds:
        key = (w["block"], w["noise_regime"], category(w["block"]))
        strata.setdefault(key, []).append(w["world_id"])
    fold = {}
    for key in sorted(strata):
        ids = sorted(strata[key],
                     key=lambda x: hashlib.sha256(x.encode()).hexdigest())
        for i, wid in enumerate(ids):
            fold[wid] = i % N_FOLDS
    return fold


# ------------------------------------------------------- selector helpers --
def _rep_lowcomplexity(members, idxs):
    """The production representative rule: lowest complexity, then highest
    validation R^2, then lexicographic expression."""
    return min(idxs, key=lambda i: (members[i]["complexity"],
                                    -members[i]["valid_r2"], members[i]["expr"]))


def _rep_bestr2(members, idxs):
    """Highest validation R^2, then lowest complexity, then lexicographic."""
    return min(idxs, key=lambda i: (-members[i]["valid_r2"],
                                    members[i]["complexity"], members[i]["expr"]))


def _rep_nearbest_simplest(members, idxs, tol=BAND_TOL):
    """Within `tol` absolute validation R^2 of the group best, lowest
    complexity. Scale-aware check: valid_r2 is already an R^2 on [-inf, 1], so
    0.01 absolute is the same unit the production band uses."""
    best = max(members[i]["valid_r2"] for i in idxs)
    near = [i for i in idxs if members[i]["valid_r2"] >= best - tol]
    return _rep_lowcomplexity(members, near)


def _seedfrac(members, idxs, n_seeds):
    return len({members[i]["seed"] for i in idxs}) / max(1, n_seeds)


def _stability_scores(members, groups, n_seeds, world_id):
    """Fraction of deterministic 15-seed subsets in which a group is the modal
    group by distinct-seed count. World-seeded RNG, never truth-seeded."""
    seeds = sorted({m["seed"] for m in members})
    if len(seeds) <= STAB_SUBSET_SIZE or not groups:
        return {g: _seedfrac(members, idxs, n_seeds) for g, idxs in groups.items()}
    rng = np.random.default_rng(
        int.from_bytes(hashlib.sha256(world_id.encode()).digest()[:4], "big"))
    gseeds = {g: {members[i]["seed"] for i in idxs} for g, idxs in groups.items()}
    wins = {g: 0 for g in groups}
    for _ in range(STAB_SUBSETS):
        sub = set(rng.choice(seeds, size=STAB_SUBSET_SIZE, replace=False).tolist())
        best_g, best_n = None, -1
        for g in sorted(groups):
            n = len(gseeds[g] & sub)
            if n > best_n:
                best_g, best_n = g, n
        if best_n > 0:
            wins[best_g] += 1
    return {g: wins[g] / STAB_SUBSETS for g in groups}


# ------------------------------------------------------------ architectures --
def select_world(world, arch, fam_vote="B1", rep_rule="R2"):
    """Return (rep_index or None, diagnostics dict). Reads no truth field."""
    members = world["members"]
    n_seeds = max(1, world["n_seeds"])
    usable = [i for i, m in enumerate(members) if m["usable"] and m["cluster"] >= 0]
    diag = {"n_members": len(members), "n_usable": len(usable)}
    if not usable:
        return None, diag

    # cluster -> member indices (production family object)
    clusters = {}
    for i in usable:
        clusters.setdefault(members[i]["cluster"], []).append(i)

    if arch == "BASELINE_30":
        # exactly muru.objval.select: max selection_fraction, tie -> rep
        # complexity, then rep expression string.
        def key(c):
            r = _rep_lowcomplexity(members, clusters[c])
            return (-_seedfrac(members, clusters[c], n_seeds),
                    members[r]["complexity"], members[r]["expr"])
        c = min(sorted(clusters), key=key)
        rep = _rep_lowcomplexity(members, clusters[c])
        diag.update(sel_frac=_seedfrac(members, clusters[c], n_seeds),
                    support=members[rep]["eff_blocks"], support_freq=None,
                    cluster=c)
        return rep, diag

    # ---- SUPPORT CONSENSUS (shared by A/B/C/D) --------------------------
    supports = {}
    for i in usable:
        supports.setdefault(tuple(members[i]["eff_blocks"]), []).append(i)
    sup_stats = {}
    for S, idxs in supports.items():
        sup_stats[S] = {
            "seedfrac": _seedfrac(members, idxs, n_seeds),
            "med_r2": float(np.median([members[i]["valid_r2"] for i in idxs])),
            "med_cx": float(np.median([members[i]["complexity"] for i in idxs])),
        }
    Sstar = min(sorted(supports),
                key=lambda S: (-sup_stats[S]["seedfrac"], -sup_stats[S]["med_r2"],
                               sup_stats[S]["med_cx"], S))
    pool = supports[Sstar]
    diag["support"] = list(Sstar)
    diag["support_freq"] = sup_stats[Sstar]["seedfrac"]

    groups = {}
    for i in pool:
        groups.setdefault(members[i]["cluster"], []).append(i)

    if arch == "SUPPORT_CONSENSUS":
        c = min(sorted(groups), key=lambda g: (-_seedfrac(members, groups[g], n_seeds),
                                               members[_rep_lowcomplexity(members, groups[g])]["complexity"]))
        rep = _rep_lowcomplexity(members, groups[c])
        diag.update(sel_frac=_seedfrac(members, groups[c], n_seeds), cluster=c)
        return rep, diag

    # ---- FAMILY CONSENSUS vote ------------------------------------------
    if fam_vote == "B1":          # unweighted majority of distinct seeds
        score = {g: _seedfrac(members, idxs, n_seeds) for g, idxs in groups.items()}
    elif fam_vote == "B2":        # validation-quality-weighted vote
        score = {}
        for g, idxs in groups.items():
            per_seed = {}
            for i in idxs:
                s = members[i]["seed"]
                per_seed[s] = max(per_seed.get(s, -9e9), members[i]["valid_r2"])
            score[g] = sum(max(0.0, v) for v in per_seed.values()) / n_seeds
    elif fam_vote == "B3":        # stability-weighted vote
        score = _stability_scores(members, groups, n_seeds, world["world_id"])
    else:
        raise ValueError(fam_vote)

    c = min(sorted(groups), key=lambda g: (
        -score[g], members[_rep_lowcomplexity(members, groups[g])]["complexity"],
        members[_rep_lowcomplexity(members, groups[g])]["expr"]))
    gidx = groups[c]
    diag.update(sel_frac=_seedfrac(members, gidx, n_seeds), cluster=c,
                fam_score=score[c])

    if arch == "SUPPORT_PLUS_FAMILY_CONSENSUS":
        return _rep_lowcomplexity(members, gidx), diag
    # CONSENSUS_PLUS_SIMPLE_REPRESENTATIVE and the gated architecture
    rep = _rep_bestr2(members, gidx) if rep_rule == "R1" else \
        _rep_nearbest_simplest(members, gidx)
    return rep, diag


# --------------------------------------------------------- gate features --
def gate_features(world, diag):
    br = [s["best_valid_r2"] for s in world["seeds"]
          if s["best_valid_r2"] == s["best_valid_r2"]]
    f = {"median_seed_best_r2": float(np.median(br)) if br else float("nan"),
         "uq_seed_best_r2": float(np.percentile(br, 75)) if br else float("nan"),
         "selection_fraction": float(diag.get("sel_frac") or 0.0),
         "modal_support_freq": float(diag.get("support_freq") or 0.0)}
    return f


T1_GRID = np.round(np.arange(-0.10, 1.001, 0.005), 4)
T2_GRID = np.round(np.arange(0.0, 1.0001, 1.0 / 30.0), 6)
MAX_NULL_FPR = 0.05


def fit_gate(rows):
    """REPORT iff median-seed-best-R2 >= t1 AND reported-family
    selection-fraction >= t2. Maximize positive sensitivity subject to
    null FPR <= 5% on the TRAINING fold only."""
    pos = [r for r in rows if r["category"] == "positive"]
    nul = [r for r in rows if r["category"] == "null"]
    if not pos or not nul:
        return {"t1": 0.5, "t2": 0.0, "train_sens": float("nan"),
                "train_fpr": float("nan")}
    P1 = np.array([r["gate"]["median_seed_best_r2"] for r in pos])
    P2 = np.array([r["gate"]["selection_fraction"] for r in pos])
    N1 = np.array([r["gate"]["median_seed_best_r2"] for r in nul])
    N2 = np.array([r["gate"]["selection_fraction"] for r in nul])
    best = None
    for t1 in T1_GRID:
        for t2 in T2_GRID:
            fpr = float(np.mean((N1 >= t1) & (N2 >= t2)))
            if fpr > MAX_NULL_FPR:
                continue
            sens = float(np.mean((P1 >= t1) & (P2 >= t2)))
            k = (-sens, fpr, -t1, -t2)
            if best is None or k < best[0]:
                best = (k, {"t1": float(t1), "t2": float(t2),
                            "train_sens": sens, "train_fpr": fpr})
    return best[1] if best else {"t1": 1.1, "t2": 1.1, "train_sens": 0.0,
                                 "train_fpr": 0.0}


def apply_gate(g, feats):
    return bool(feats["median_seed_best_r2"] >= g["t1"]
                and feats["selection_fraction"] >= g["t2"])


# ------------------------------------------------------------------ AUCs --
def auc_roc(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    m = np.isfinite(s)
    s, y = s[m], y[m]
    if y.sum() == 0 or y.sum() == len(y):
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    sv = s[order]
    i = 0
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    n1, n0 = y.sum(), len(y) - y.sum()
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def auc_pr(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    m = np.isfinite(s); s, y = s[m], y[m]
    if y.sum() == 0:
        return float("nan")
    order = np.argsort(-s, kind="mergesort")
    y = y[order]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / y.sum()
    ap, prev = 0.0, 0.0
    for p, r in zip(prec, rec):
        ap += p * (r - prev); prev = r
    return float(ap)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load():
    return json.loads(CACHE.read_text())
