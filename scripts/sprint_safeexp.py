"""FINAL ACCURACY SPRINT — conditional SAFE_EXP grammar experiment (G1C only).

BASE_GRAMMAR    the 30 existing frozen-grammar seeds per world (already run)
PORTFOLIO       15 of those base seeds + 15 NEW SAFE_EXP-enabled seeds

K = 8.0 and the SAFE_EXP complexity cost = 5 were chosen before any recovery
number from this experiment was seen (MURU_FINAL_ACCURACY_SPRINT_FREEZE.md 8).
Every other search setting is the frozen PYSR_CONFIG, unchanged.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                   # noqa: E402
import sympy as sp                                   # noqa: E402

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "src"))
sys.path.insert(0, str(WT / "scripts"))
OUT = WT / "artifacts" / "sprint"
OUT.mkdir(parents=True, exist_ok=True)

K_CLIP = 8.0
SEXP_COMPLEXITY = 5
N_PORTFOLIO_EXP_SEEDS = 15


def sexp_sympy(x):
    return sp.exp(sp.Min(sp.Max(x, -K_CLIP), K_CLIP))


def parse_sexp(expr_str, variables):
    from muru.discovery import grammar
    loc = {"square": lambda x: x ** 2, "cube": lambda x: x ** 3,
           "inv": lambda x: 1 / x, "sqrt": sp.sqrt, "log": sp.log,
           "sexp": sexp_sympy}
    loc.update({v: sp.Symbol(v) for v in variables})
    return sp.sympify(expr_str, locals=loc)


def complexity_sexp(expr):
    """Frozen node count, with SAFE_EXP charged SEXP_COMPLEXITY instead of 1."""
    from muru.discovery import grammar
    if expr.is_Symbol or expr.is_Number or expr.is_NumberSymbol:
        return 1
    if expr.func is sp.exp:
        return SEXP_COMPLEXITY + complexity_sexp(expr.args[0])
    if isinstance(expr, (sp.Min, sp.Max)):
        # the clip wrapper is part of the operator, not extra structure
        return max(complexity_sexp(a) for a in expr.args
                   if not a.is_Number) if any(not a.is_Number for a in expr.args) else 1
    if expr.is_Add or expr.is_Mul:
        return (len(expr.args) - 1) + sum(complexity_sexp(a) for a in expr.args)
    if expr.is_Pow:
        if expr.exp.is_Number:
            return 1 + complexity_sexp(expr.base)
        return 1 + complexity_sexp(expr.base) + complexity_sexp(expr.exp)
    return 1 + sum(complexity_sexp(a) for a in expr.args)


def uses_sexp(expr):
    return bool(expr.atoms(sp.exp))


def run_pysr_sexp(Xtr, ytr, wtr, Xva, yva, wva, variables, seed):
    from pysr import PySRRegressor
    from muru.discovery import engine, grammar
    cfg = dict(engine.PYSR_CONFIG)
    cfg["unary_operators"] = list(grammar.UNARY_OPERATORS) + [
        f"sexp(x) = exp(clamp(x, -{K_CLIP}f0, {K_CLIP}f0))"]
    nc = dict(grammar.NESTED_CONSTRAINTS)
    nc["sexp"] = {"sexp": 0}
    cfg["nested_constraints"] = nc
    cfg["complexity_of_operators"] = {"sexp": SEXP_COMPLEXITY}
    cfg["extra_sympy_mappings"] = {"sexp": sexp_sympy}
    out = []
    with tempfile.TemporaryDirectory() as td:
        model = PySRRegressor(random_state=seed, output_directory=td,
                              run_id=f"x{seed}", **cfg)
        model.fit(Xtr, ytr, weights=wtr, variable_names=list(variables))
        eqs = model.equations_
        if isinstance(eqs, list):
            eqs = eqs[0]
        rows = [] if eqs is None else list(eqs.itertuples())
    for r in rows:
        raw = str(getattr(r, "equation"))
        try:
            expr = parse_sexp(raw, variables)
        except Exception:
            continue
        cx = complexity_sexp(expr)
        if cx > grammar.MAX_COMPLEXITY:
            continue
        tr_r2, _, _ = engine.score_candidate(expr, variables, Xtr, ytr, wtr)
        va_r2, frac, usable = engine.score_candidate(expr, variables, Xva, yva, wva)
        out.append({"expr_str": raw, "complexity": int(cx),
                    "train_r2": float(tr_r2), "valid_r2": float(va_r2),
                    "invalid_fraction": float(frac), "valid": bool(usable),
                    "uses_sexp": uses_sexp(expr), "seed": int(seed)})
    return out


def world_job(args):
    wid, n_seeds = args
    from muru.discovery import protocol
    from muru.objval.plan2 import all_worlds2, seed_list2
    from muru.synth.generators import load_dev_covariates
    from ov_20_search import build_search_world
    specs = {s.world_id: s for s in all_worlds2()}
    spec = specs[wid]
    cov = load_dev_covariates()
    w = build_search_world(spec, cov)
    long, covw = w.search_inputs()
    wd = protocol.build_world_data(wid, long, covw)
    Xtr, ytr, wtr = wd.part("train")
    Xva, yva, wva = wd.part("valid")
    seeds = seed_list2(wid)[:n_seeds]
    t0 = time.time()
    res = []
    for s in seeds:
        c = run_pysr_sexp(Xtr, ytr, wtr, Xva, yva, wva, wd.variables, s)
        res.append({"seed": int(s), "candidates": c})
    return {"world_id": wid, "n_seeds": len(seeds),
            "sec": time.time() - t0, "runs": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=N_PORTFOLIO_EXP_SEEDS)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--procs", type=int, default=5)
    a = ap.parse_args()
    import multiprocessing as mp
    cache = json.loads((WT / "artifacts" / "accopt" / "candidate_cache.json").read_text())
    g1c = sorted(w["world_id"] for w in cache if w["block"] == "G1C")
    if a.limit:
        g1c = g1c[:a.limit]
    print(f"SAFE_EXP search over {len(g1c)} G1C worlds x {a.seeds} seeds", flush=True)
    t0 = time.time()
    ctx = mp.get_context("spawn")
    out = []
    with ctx.Pool(a.procs) as pool:
        for n, r in enumerate(pool.imap_unordered(
                world_job, [(w, a.seeds) for w in g1c]), 1):
            out.append(r)
            print(f"  [{n}/{len(g1c)}] {r['world_id']} {r['sec']:.0f}s "
                  f"total {time.time()-t0:.0f}s", flush=True)
    out.sort(key=lambda r: r["world_id"])
    (OUT / "safeexp_runs.json").write_text(json.dumps(out))
    print(f"wrote safeexp_runs.json  {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
