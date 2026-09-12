"""The frozen selector and gate, applied to one real-data world.

This is `scripts/fh_30_predict.py`'s deployed sequence, factored so a
module can call it: Pareto band per seed, structural signature on a lattice
over the world's own descriptor domain, Type 2 family clustering, then
`sprint_arch.select_ABC(P, "A_CURRENT_FINAL")` (modal support consensus,
B2 validation-quality-weighted family vote, R1 highest-validation-R2
representative) and the two-quantity gate at the thresholds read from
FRESH_HOLDOUT_METHOD_FREEZE.json. The selector code itself is imported from
its historical location in scripts/ and is not rewritten.

Held-out scoring on the test part is added here as reporting only; nothing
in selection reads it.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from muru.discovery import engine, grammar, protocol
from muru.objval import equiv, select as selmod, signature

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
FREEZE = ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json"


def _load_script(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


def frozen_gate() -> dict:
    g = json.loads(FREEZE.read_text())["deployment_gate"]
    return {"t1": float(g["t1"]), "t2": float(g["t2"]), "form": g["form"]}


def candidate_cache(world_id: str, wd: protocol.WorldData,
                    per_seed: dict[int, list[engine.Candidate]],
                    planned_seeds: list[int]) -> dict:
    """Blind per-world candidate cache, mirroring fh_30_predict.process."""
    variables = list(wd.variables)
    Z = selmod.lattice(wd.X, variables)
    members, seed_rows = [], []
    for s in sorted(per_seed):
        cands = per_seed[s]
        ok = [c for c in cands if c.valid and np.isfinite(c.valid_r2)
              and c.complexity <= grammar.MAX_COMPLEXITY]
        seed_best = float(max((c.valid_r2 for c in ok), default=float("nan")))
        band = selmod.pareto_band(cands)
        seed_rows.append({"seed": int(s), "n_cands": len(cands), "n_valid": len(ok),
                          "best_valid_r2": seed_best, "n_band": len(band)})
        for k, c in enumerate(band):
            members.append((s, k, c))
    members.sort(key=lambda t: (t[0], t[2].complexity, t[2].expr_str))

    rec = {"world_id": world_id, "block": "REAL", "family": "REAL",
           "noise_regime": "real", "index": 0,
           "n_seeds": len(per_seed), "n_seeds_planned": len(planned_seeds),
           "missing_seeds": [int(s) for s in planned_seeds if s not in per_seed],
           "seeds": seed_rows, "members": [], "clusters": [], "lattice_n": int(len(Z))}
    if not members:
        return rec
    sigs, vals, oks = [], [], []
    for (_s, _k, c) in members:
        sg = signature.signature(c.expr, variables, Z)
        v, o = signature._eval(c.expr, variables, Z)
        sigs.append(sg); vals.append(v); oks.append(o)
    usable = [i for i in range(len(members)) if sigs[i]["usable"]]
    cluster_of = [-1] * len(members)
    clusters = []
    if usable:
        cl = equiv.cluster_families([sigs[i] for i in usable],
                                    [vals[i] for i in usable],
                                    [oks[i] for i in usable])
        clusters = [[usable[j] for j in c] for c in cl]
        for ci, c in enumerate(clusters):
            for i in c:
                cluster_of[i] = ci
    for i, (s, k, c) in enumerate(members):
        sg = sigs[i]
        rec["members"].append({
            "seed": int(s), "band_index": int(k), "expr": c.expr_str,
            "complexity": int(c.complexity), "valid_r2": float(c.valid_r2),
            "train_r2": float(c.train_r2),
            "invalid_fraction": float(c.invalid_fraction),
            "usable": bool(sg["usable"]),
            "eff_support": sorted(sg["effective_support"]),
            "eff_blocks": sorted(sg["effective_support_blocks"]),
            "cluster": int(cluster_of[i])})
    for ci, c in enumerate(clusters):
        cseeds = sorted({members[i][0] for i in c})
        rec["clusters"].append({"id": ci, "n_members": len(c), "n_seeds": len(cseeds),
                                "selection_fraction": len(cseeds) / max(1, len(per_seed)),
                                "seeds": [int(x) for x in cseeds]})
    return rec


def select_and_gate(cache: dict) -> dict:
    """The frozen A_CURRENT_FINAL selection and CURRENT_GATE decision."""
    A = _load_script("sprint_arch")
    S = _load_script("accopt_selectors")
    gate = frozen_gate()
    P = A.prep(cache)
    rep, diag = A.select_ABC(P, "A_CURRENT_FINAL")
    g = S.gate_features(cache, diag)
    report = bool(g["median_seed_best_r2"] >= gate["t1"]
                  and g["selection_fraction"] >= gate["t2"])
    m = cache["members"][rep] if rep is not None else None
    return {
        "architecture": "A_CURRENT_FINAL (B2 family vote + R1 representative)",
        "gate": {**gate, "features": g}, "report": report,
        "rep_index": rep,
        "expr": m["expr"] if m else None,
        "complexity": m["complexity"] if m else None,
        "valid_r2": m["valid_r2"] if m else None,
        "train_r2": m["train_r2"] if m else None,
        "eff_support": m["eff_support"] if m else None,
        "eff_blocks": m["eff_blocks"] if m else None,
        "cluster": diag.get("cluster"), "modal_support": diag.get("support"),
        "n_usable": diag.get("n_usable", 0), "n_members": len(cache["members"]),
        "n_clusters": len(cache["clusters"]),
        "computational_failure": bool(rep is None
                                      or cache["n_seeds"] < cache["n_seeds_planned"]),
        "seed_best_valid_r2": [s["best_valid_r2"] for s in cache["seeds"]],
    }


def score_on_part(expr_str: str, wd: protocol.WorldData, part: str) -> dict:
    """Reporting only: the expression against the held-out part."""
    X, y, w = wd.part(part)
    expr = grammar.parse(expr_str, list(wd.variables))
    pred, ok = grammar.evaluate(expr, list(wd.variables), X)
    frac_invalid = float(1.0 - ok.mean()) if len(ok) else float("nan")
    r2w = engine.weighted_r2(y, pred, w, ok)
    r2u = engine.weighted_r2(y, pred, np.ones_like(w), ok)
    rho = float(spearmanr(pred[ok], y[ok]).statistic) if ok.sum() >= 3 else float("nan")
    return {"part": part, "n": int(len(y)), "n_valid": int(ok.sum()),
            "invalid_fraction": frac_invalid,
            "r2_weighted": float(r2w), "r2_unweighted": float(r2u),
            "spearman": rho}
