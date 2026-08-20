"""FRESH HOLDOUT — blind candidate processing, frozen selection, frozen gate.

TRUTH-BLIND. This script never opens fresh_holdout_truth_manifest.json and
imports nothing that does. It reproduces the production scientific pipeline
exactly:

    frozen candidate processing (Pareto band on the frozen BAND_TOL)
      -> frozen structural signature on the frozen selection lattice
      -> frozen Type 2 family clustering
      -> modal support consensus
      -> B2 validation-quality-weighted family vote
      -> R1 highest-validation-R2 representative
      -> calibrated two-quantity report gate at the frozen (t1, t2)

Output: fresh_holdout_predictions_frozen.json  (the one-way boundary artifact)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
CKPT = ROOT / "artifacts" / "fh_ckpt"
OUT = ROOT / "artifacts" / "fresh_holdout"

_G = {}


def _init():
    from muru.discovery import protocol
    from muru.objval import select as selmod
    from muru.synth.generators import load_dev_covariates
    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8,
                                              size=(len(Xreal), len(variables)))
    _G["variables"] = variables
    _G["Zreal"] = selmod.lattice(Xreal, variables)
    _G["Zsynth"] = selmod.lattice(Xsynth, variables)


def process(spec_tuple):
    """Blind per-world candidate cache. Mirrors accopt_build_cache.process with
    every truth-scoring branch removed."""
    from muru.discovery import grammar
    from muru.discovery.checkpoint import Store
    from muru.discovery.engine import Candidate
    from muru.objval import equiv, select as selmod, signature
    if not _G:
        _init()
    import fh_lib as fh
    block, world_id, family, noise_regime, index = spec_tuple
    variables = _G["variables"]
    Z = _G["Zsynth"] if family == "G1A" else _G["Zreal"]
    store = Store(CKPT)
    be = f"{block}_pysr"
    seeds = fh.fh_seed_list(world_id)

    per_seed_raw, missing = {}, []
    for s in seeds:
        if not store.done(be, world_id, s):
            missing.append(int(s))
            continue
        data = store.read(be, world_id, s)
        cands = []
        for c in data.get("candidates", []):
            try:
                expr = grammar.parse(c["expr_str"], variables)
            except Exception:
                continue
            cands.append(Candidate(
                expr_str=c["expr_str"], expr=expr,
                complexity=grammar.complexity(expr),
                support=tuple(c["support"]), engine=c["engine"], seed=c["seed"],
                train_r2=float(c["train_r2"]), valid_r2=float(c["valid_r2"]),
                invalid_fraction=float(c["invalid_fraction"]),
                valid=bool(c["valid"])))
        per_seed_raw[s] = cands

    members, seed_rows = [], []
    for s in sorted(per_seed_raw):
        cands = per_seed_raw[s]
        ok = [c for c in cands if c.valid and np.isfinite(c.valid_r2)
              and c.complexity <= grammar.MAX_COMPLEXITY]
        seed_best = float(max((c.valid_r2 for c in ok), default=float("nan")))
        band = selmod.pareto_band(cands)
        seed_rows.append({"seed": int(s), "n_cands": len(cands),
                          "n_valid": len(ok), "best_valid_r2": seed_best,
                          "n_band": len(band)})
        for k, c in enumerate(band):
            members.append((s, k, c))
    members.sort(key=lambda t: (t[0], t[2].complexity, t[2].expr_str))

    rec = {"world_id": world_id, "block": block, "family": family,
           "noise_regime": noise_regime, "index": index,
           "n_seeds": len(per_seed_raw), "n_seeds_planned": len(seeds),
           "missing_seeds": missing, "seeds": seed_rows,
           "members": [], "clusters": []}
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
        rec["clusters"].append({"id": ci, "n_members": len(c),
                                "n_seeds": len(cseeds),
                                "selection_fraction": len(cseeds)
                                / max(1, len(per_seed_raw)),
                                "seeds": [int(x) for x in cseeds]})
    return rec


def main() -> int:
    import accopt_selectors as S
    import fh_lib as fh
    import sprint_arch as A

    freeze = json.loads((ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json").read_text())
    t1 = freeze["deployment_gate"]["t1"]
    t2 = freeze["deployment_gate"]["t2"]

    specs = fh.all_worlds()
    retained = json.loads((OUT / "retained_worlds.json").read_text())["world_ids"] \
        if (OUT / "retained_worlds.json").exists() else [s.world_id for s in specs]
    specs = [s for s in specs if s.world_id in set(retained)]

    tasks = [(s.block, s.world_id, s.family, s.noise_regime, s.index)
             for s in specs]
    t0 = time.time()
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    cache = []
    with ctx.Pool(7) as pool:
        for n, r in enumerate(pool.imap_unordered(process, tasks, chunksize=1), 1):
            cache.append(r)
            if n % 12 == 0 or n == len(tasks):
                print(f"  [{n}/{len(tasks)}] {time.time()-t0:.0f}s", flush=True)
    cache.sort(key=lambda r: r["world_id"])
    (OUT / "fh_candidate_cache.json").write_text(json.dumps(cache))

    preds = {}
    for w in cache:
        P = A.prep(w)
        rep, diag = A.select_ABC(P, "A_CURRENT_FINAL")
        g = S.gate_features(w, diag)
        report = bool(g["median_seed_best_r2"] >= t1
                      and g["selection_fraction"] >= t2)
        m = w["members"][rep] if rep is not None else None
        preds[w["world_id"]] = {
            "block": w["block"], "family": w["family"],
            "noise_regime": w["noise_regime"],
            "category": fh.category(w["block"]),
            "n_seeds_completed": w["n_seeds"],
            "n_seeds_planned": w["n_seeds_planned"],
            "missing_seeds": w["missing_seeds"],
            "n_members": len(w["members"]),
            "n_usable": diag.get("n_usable", 0),
            "n_clusters": len(w["clusters"]),
            "rep_index": rep,
            "expr": m["expr"] if m else None,
            "complexity": m["complexity"] if m else None,
            "valid_r2": m["valid_r2"] if m else None,
            "eff_support": m["eff_support"] if m else None,
            "eff_blocks": m["eff_blocks"] if m else None,
            "cluster": diag.get("cluster"),
            "modal_support": diag.get("support"),
            "gate": g, "report": report,
            "computational_failure": bool(rep is None
                                          or w["n_seeds"] < w["n_seeds_planned"]),
            "seed_best_valid_r2": [s["best_valid_r2"] for s in w["seeds"]],
        }

    payload = {
        "phase": "PREDICTION_FREEZE",
        "boundary": ("Written BEFORE fresh_holdout_truth_manifest.json is "
                     "opened. Nothing downstream may change the algorithm."),
        "architecture": "A_CURRENT_FINAL (B2 family vote + R1 representative)",
        "gate": {"form": "CURRENT_GATE", "t1": t1, "t2": t2,
                 "source": "FRESH_HOLDOUT_METHOD_FREEZE.json"},
        "method_freeze_sha256": hashlib.sha256(
            (ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json").read_bytes()).hexdigest(),
        "world_manifest_sha256": hashlib.sha256(
            (ROOT / "fresh_holdout_world_manifest.json").read_bytes()).hexdigest(),
        "n_worlds": len(preds),
        "predictions": preds,
    }
    text = json.dumps(payload, indent=1, sort_keys=True)
    p = ROOT / "fresh_holdout_predictions_frozen.json"
    p.write_text(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    (OUT / "predictions_frozen_hash.json").write_text(json.dumps(
        {"file": "fresh_holdout_predictions_frozen.json", "sha256": sha,
         "n_worlds": len(preds),
         "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1))
    nrep = sum(v["report"] for v in preds.values())
    print(json.dumps({"n_worlds": len(preds), "n_report": nrep,
                      "n_comp_fail": sum(v["computational_failure"]
                                         for v in preds.values()),
                      "predictions_sha256": sha}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
