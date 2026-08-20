"""ACCURACY OPTIMIZATION — Stage 1: build the candidate-level cache.

One expensive pass over 323 worlds x 30 seeds. For every Pareto-band member of
every seed we compute its structural signature ONCE on the frozen selection
lattice, cluster members into Type 2 families, and (for truth-scorable worlds)
score EVERY member against the planted law.

Scoring every member -- not just the one the selector picked -- is what makes
all downstream selector variants free to evaluate and makes the ORACLE CEILING
mechanically computable.

Truth fields are written to the cache but are NEVER inputs to any selector.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

WT = Path(__file__).resolve().parents[1]
MAIN = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1")
sys.path.insert(0, str(WT / "src"))
CKPT = MAIN / "artifacts" / "ov_ckpt"
OUT = WT / "artifacts" / "accopt"
OUT.mkdir(parents=True, exist_ok=True)

ENGINE = "pysr"

POSITIVE_BLOCKS = {"G1A", "G1B", "G1C"}
NULL_BLOCKS = {"G4", "G4M", "NCAL"}
REFUSAL_BLOCKS = {"G2", "G3", "G5", "GC", "GRT"}
# finer scientific semantics, reported alongside the owner's coarse split
NO_LAW_BLOCKS = {"NCAL", "G4", "GC"}          # no descriptor law exists at all
MASS_ONLY_BLOCKS = {"G3", "G4M"}              # mass law real, non-mass is the K5 threat
CONFOUNDED_BLOCKS = {"G5", "GRT", "G2"}       # driver unobserved / not compressible

_G = {}


def _init():
    from muru.discovery import grammar, protocol
    from muru.discovery.checkpoint import Store
    from muru.objval import select as selmod
    from muru.synth.generators import load_dev_covariates
    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8, size=(len(Xreal), len(variables)))
    _G["variables"] = variables
    _G["Zreal"] = selmod.lattice(Xreal, variables)
    _G["Zsynth"] = selmod.lattice(Xsynth, variables)
    _G["store"] = Store(CKPT)
    _G["truth"] = {w["world_id"]: w for w in
                   json.loads((MAIN / "artifacts" / "ov_truth_manifest.json").read_text())["worlds"]}
    _G["grammar"] = grammar


def process(spec_tuple):
    from muru.discovery import grammar
    from muru.discovery.engine import Candidate
    from muru.objval import equiv, select as selmod, signature
    from muru.objval import recovery as recmod
    from muru.objval.plan2 import seed_list2
    if not _G:
        _init()
    block, world_id, family, noise_regime, replicate = spec_tuple
    variables = _G["variables"]
    Z = _G["Zsynth"] if family == "G1A" else _G["Zreal"]
    store = _G["store"]
    be = f"{block}_{ENGINE}"
    seeds = seed_list2(world_id)

    per_seed_raw = {}
    for s in seeds:
        if not store.done(be, world_id, s):
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
                invalid_fraction=float(c["invalid_fraction"]), valid=bool(c["valid"])))
        per_seed_raw[s] = cands

    # ---- per-seed Pareto band (frozen BAND_TOL, unchanged) -----------------
    members = []
    seed_rows = []
    for s in sorted(per_seed_raw):
        cands = per_seed_raw[s]
        ok = [c for c in cands if c.valid and np.isfinite(c.valid_r2)
              and c.complexity <= grammar.MAX_COMPLEXITY]
        seed_best = float(max((c.valid_r2 for c in ok), default=float("nan")))
        band = selmod.pareto_band(cands)
        seed_rows.append({"seed": int(s), "n_cands": len(cands), "n_valid": len(ok),
                          "best_valid_r2": seed_best, "n_band": len(band),
                          "band_min_complexity": int(min((c.complexity for c in band),
                                                         default=-1))})
        for k, c in enumerate(band):
            members.append((s, k, c))
    members.sort(key=lambda t: (t[0], t[2].complexity, t[2].expr_str))

    n_seeds = len(per_seed_raw)
    rec = {"world_id": world_id, "block": block, "family": family,
           "noise_regime": noise_regime, "replicate": replicate,
           "n_seeds": n_seeds, "seeds": seed_rows,
           "members": [], "clusters": [], "scorable": False}

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

    # ---- truth scoring of EVERY member (evaluation only) -------------------
    truth_rec = _G["truth"].get(world_id)
    psig = pv = pok = None
    if truth_rec is not None:
        params = recmod.freeze_constants(truth_rec["family"], truth_rec["params"],
                                         variables, Z)
        psig = recmod.planted_signature(truth_rec["family"], params, variables, Z)
        if psig is not None:
            ev, _ = recmod.planted_evaluator(truth_rec["family"], params, variables)
            pv, pok = ev(Z)
    rec["scorable"] = psig is not None
    if psig is not None:
        rec["planted_blocks"] = sorted(set(psig["effective_support_blocks"]))
        rec["planted_variables"] = sorted(set(psig["effective_support"]))

    pb = set(psig["effective_support_blocks"]) if psig else set()

    for i, (s, k, c) in enumerate(members):
        sg = sigs[i]
        row = {"seed": int(s), "band_index": int(k), "expr": c.expr_str,
               "complexity": int(c.complexity), "valid_r2": float(c.valid_r2),
               "train_r2": float(c.train_r2),
               "invalid_fraction": float(c.invalid_fraction),
               "usable": bool(sg["usable"]),
               "eff_support": sorted(sg["effective_support"]),
               "eff_blocks": sorted(sg["effective_support_blocks"]),
               "cluster": int(cluster_of[i])}
        if psig is not None and sg["usable"]:
            rb = set(sg["effective_support_blocks"])
            row["t_support"] = bool(pb == rb)
            ok = pok & oks[i]
            fam = equiv.same_family(sg, psig, vals[i], pv, ok)
            row["t_family"] = bool(fam["same_family"])
            fc = equiv.functional_class(pv, vals[i], ok)
            row["t_exact"] = bool(fc["functionally_equivalent"])
            row["t_rel_rmse"] = float(fc["numeric"]["rel_rmse"])
        elif psig is not None:
            row["t_support"] = False; row["t_family"] = False
            row["t_exact"] = False; row["t_rel_rmse"] = float("nan")
        rec["members"].append(row)

    for ci, c in enumerate(clusters):
        cseeds = sorted({members[i][0] for i in c})
        rec["clusters"].append({
            "id": ci, "n_members": len(c), "n_seeds": len(cseeds),
            "selection_fraction": len(cseeds) / max(1, n_seeds),
            "member_indices": c,
            "seeds": [int(x) for x in cseeds],
        })
    return rec


def main():
    _init()
    from muru.objval.plan2 import all_worlds2
    specs = all_worlds2()
    tasks = [(s.block, s.world_id, s.family, s.noise_regime, s.replicate) for s in specs]
    t0 = time.time()
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    out = []
    with ctx.Pool(7) as pool:
        for n, r in enumerate(pool.imap_unordered(process, tasks, chunksize=2), 1):
            out.append(r)
            if n % 25 == 0 or n == len(tasks):
                print(f"  [{n}/{len(tasks)}] {time.time()-t0:.0f}s", flush=True)
    out.sort(key=lambda r: r["world_id"])
    p = OUT / "candidate_cache.json"
    p.write_text(json.dumps(out))
    nm = sum(len(r["members"]) for r in out)
    print(f"wrote {p} — {len(out)} worlds, {nm} band members, "
          f"{sum(r['n_seeds'] for r in out)} seed-runs, {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
