"""FINAL ACCURACY SPRINT — score BASE_GRAMMAR vs PORTFOLIO_GRAMMAR on G1C.

Both arms go through IDENTICAL downstream code: per-seed Pareto band (frozen
BAND_TOL), structural signature on the frozen lattice, Type 2 family clustering,
architecture A selection, then truth scoring. 30 search runs per world in both
arms (BASE: 30 frozen-grammar seeds; PORTFOLIO: 15 frozen-grammar seeds +
15 SAFE_EXP seeds).
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                    # noqa: E402
import sympy as sp                                    # noqa: E402

WT = Path(__file__).resolve().parents[1]
MAIN = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1")
sys.path.insert(0, str(WT / "src"))
sys.path.insert(0, str(WT / "scripts"))
OUT = WT / "artifacts" / "sprint"
CKPT = MAIN / "artifacts" / "ov_ckpt"

_G = {}


def _init():
    from muru.discovery import protocol
    from muru.discovery.checkpoint import Store
    from muru.objval import select as selmod
    from muru.objval.plan2 import all_worlds2
    from muru.synth.generators import load_dev_covariates
    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    _G["variables"] = variables
    _G["Z"] = selmod.lattice(Xreal, variables)
    _G["store"] = Store(CKPT)
    _G["specs"] = {s.world_id: s for s in all_worlds2()}
    _G["truth"] = {w["world_id"]: w for w in json.loads(
        (WT / "artifacts" / "ov_truth_manifest.json").read_text())["worlds"]}


def band(cands):
    """Frozen per-seed Pareto band on plain dicts."""
    from muru.discovery import grammar
    ok = [c for c in cands if c["valid"] and np.isfinite(c["valid_r2"])
          and c["complexity"] <= grammar.MAX_COMPLEXITY]
    if not ok:
        return []
    best = max(c["valid_r2"] for c in ok)
    return [c for c in ok if c["valid_r2"] >= best - 0.01]


def build_record(wid, per_seed, parse_fn):
    """Same object accopt_build_cache produces, from arbitrary per-seed lists."""
    from muru.objval import equiv, signature
    from muru.objval import recovery as recmod
    variables, Z = _G["variables"], _G["Z"]
    members = []
    seed_rows = []
    for s in sorted(per_seed):
        cands = per_seed[s]
        okc = [c for c in cands if c["valid"] and np.isfinite(c["valid_r2"])]
        seed_rows.append({"seed": int(s),
                          "best_valid_r2": float(max((c["valid_r2"] for c in okc),
                                                     default=float("nan")))})
        for k, c in enumerate(band(cands)):
            members.append((s, k, c))
    members.sort(key=lambda t: (t[0], t[2]["complexity"], t[2]["expr_str"]))
    if not members:
        return None
    sigs, vals, oks, exprs = [], [], [], []
    for (_s, _k, c) in members:
        e = parse_fn(c["expr_str"])
        exprs.append(e)
        sigs.append(signature.signature(e, variables, Z))
        v, o = signature._eval(e, variables, Z)
        vals.append(v); oks.append(o)
    usable = [i for i in range(len(members)) if sigs[i]["usable"]]
    cluster_of = [-1] * len(members)
    if usable:
        cl = equiv.cluster_families([sigs[i] for i in usable],
                                    [vals[i] for i in usable],
                                    [oks[i] for i in usable])
        for ci, c in enumerate([[usable[j] for j in cc] for cc in cl]):
            for i in c:
                cluster_of[i] = ci
    tr = _G["truth"][wid]
    params = recmod.freeze_constants(tr["family"], tr["params"], variables, Z)
    psig = recmod.planted_signature(tr["family"], params, variables, Z)
    ev, _ = recmod.planted_evaluator(tr["family"], params, variables)
    pv, pok = ev(Z)
    pb = set(psig["effective_support_blocks"])
    rec_members = []
    for i, (s, k, c) in enumerate(members):
        sg = sigs[i]
        row = {"seed": int(s), "band_index": int(k), "expr": c["expr_str"],
               "complexity": int(c["complexity"]),
               "valid_r2": float(c["valid_r2"]), "train_r2": float(c["train_r2"]),
               "invalid_fraction": float(c["invalid_fraction"]),
               "usable": bool(sg["usable"]),
               "eff_support": sorted(sg["effective_support"]),
               "eff_blocks": sorted(sg["effective_support_blocks"]),
               "cluster": int(cluster_of[i]),
               "uses_sexp": bool(c.get("uses_sexp", False)),
               "refit_ok": False, "refit_valid_r2": None}
        if sg["usable"]:
            ok = pok & oks[i]
            row["t_support"] = bool(pb == set(sg["effective_support_blocks"]))
            row["t_family"] = bool(equiv.same_family(sg, psig, vals[i], pv, ok)["same_family"])
            fc = equiv.functional_class(pv, vals[i], ok)
            row["t_exact"] = bool(fc["functionally_equivalent"])
            row["t_rel_rmse"] = float(fc["numeric"]["rel_rmse"])
        else:
            row.update({"t_support": False, "t_family": False, "t_exact": False,
                        "t_rel_rmse": float("nan")})
        rec_members.append(row)
    return {"world_id": wid, "block": "G1C", "family": "G1C",
            "noise_regime": "moderate", "n_seeds": len(per_seed),
            "members": rec_members, "seeds": seed_rows, "scorable": True}


def load_base(wid, seeds):
    from muru.discovery import grammar
    store = _G["store"]
    per = {}
    for s in seeds:
        if not store.done("G1C_pysr", wid, s):
            continue
        d = store.read("G1C_pysr", wid, s)
        cands = []
        for c in d.get("candidates", []):
            try:
                e = grammar.parse(c["expr_str"], _G["variables"])
            except Exception:
                continue
            cands.append({"expr_str": c["expr_str"],
                          "complexity": grammar.complexity(e),
                          "valid_r2": float(c["valid_r2"]),
                          "train_r2": float(c["train_r2"]),
                          "invalid_fraction": float(c["invalid_fraction"]),
                          "valid": bool(c["valid"]), "uses_sexp": False})
        per[int(s)] = cands
    return per


def job(wid):
    if not _G:
        _init()
    import sprint_arch as A
    import sprint_safeexp as SE
    from muru.discovery import grammar
    from muru.objval.plan2 import seed_list2
    seeds = seed_list2(wid)
    runs = {r["world_id"]: r for r in
            json.loads((OUT / "safeexp_runs.json").read_text())}[wid]
    exp_per = {}
    for r in runs["runs"]:
        exp_per[int(r["seed"]) + 10 ** 7] = [
            {**c, "expr_str": c["expr_str"]} for c in r["candidates"]]

    def parse_mixed(s):
        try:
            return grammar.parse(s, _G["variables"])
        except Exception:
            return SE.parse_sexp(s, _G["variables"])

    def parse_any(s):
        if "sexp" in s:
            return SE.parse_sexp(s, _G["variables"])
        return grammar.parse(s, _G["variables"])

    base_per = load_base(wid, seeds)
    port_per = dict(load_base(wid, seeds[15:30]))
    port_per.update(exp_per)

    out = {"world_id": wid}
    for arm, per in (("BASE_GRAMMAR", base_per), ("PORTFOLIO_GRAMMAR", port_per)):
        rec = build_record(wid, per, parse_any)
        if rec is None:
            out[arm] = None
            continue
        P = A.prep(rec)
        rep, diag = A.select_ABC(P, "A_CURRENT_FINAL")
        m = rec["members"][rep] if rep is not None else None
        out[arm] = {
            "n_search_runs": len(per),
            "n_members": len(rec["members"]),
            "oracle_support": any(x["t_support"] for x in rec["members"]),
            "oracle_family": any(x["t_family"] for x in rec["members"]),
            "oracle_exact": any(x["t_exact"] for x in rec["members"]),
            "best_rel_rmse": float(np.nanmin([x["t_rel_rmse"] for x in rec["members"]])),
            "n_family_correct_members": sum(1 for x in rec["members"] if x["t_family"]),
            "n_sexp_members": sum(1 for x in rec["members"] if x["uses_sexp"]),
            "n_sexp_family_correct": sum(1 for x in rec["members"]
                                         if x["uses_sexp"] and x["t_family"]),
            "selected_expr": m["expr"] if m else None,
            "selected_uses_sexp": bool(m["uses_sexp"]) if m else None,
            "selected_t_support": bool(m["t_support"]) if m else None,
            "selected_t_family": bool(m["t_family"]) if m else None,
            "selected_t_exact": bool(m["t_exact"]) if m else None,
            "selected_rel_rmse": float(m["t_rel_rmse"]) if m else None,
            "median_seed_best_r2": float(np.median(
                [s["best_valid_r2"] for s in rec["seeds"]
                 if np.isfinite(s["best_valid_r2"])])),
            "selection_fraction": float(diag.get("sel_frac") or 0.0),
        }
    return out


def main():
    import multiprocessing as mp
    _init()
    cache = json.loads((WT / "artifacts" / "accopt" / "candidate_cache.json").read_text())
    g1c = sorted(w["world_id"] for w in cache if w["block"] == "G1C")
    t0 = time.time()
    ctx = mp.get_context("fork")
    out = []
    with ctx.Pool(5) as pool:
        for n, r in enumerate(pool.imap_unordered(job, g1c), 1):
            out.append(r)
            print(f"  [{n}/{len(g1c)}] {r['world_id']} {time.time()-t0:.0f}s", flush=True)
    out.sort(key=lambda r: r["world_id"])
    summ = {}
    for arm in ("BASE_GRAMMAR", "PORTFOLIO_GRAMMAR"):
        rs = [r[arm] for r in out if r[arm]]
        summ[arm] = {
            "n_worlds": len(rs),
            "oracle_family": sum(r["oracle_family"] for r in rs),
            "oracle_support": sum(r["oracle_support"] for r in rs),
            "oracle_exact": sum(r["oracle_exact"] for r in rs),
            "selected_family": sum(bool(r["selected_t_family"]) for r in rs),
            "selected_support": sum(bool(r["selected_t_support"]) for r in rs),
            "selected_exact": sum(bool(r["selected_t_exact"]) for r in rs),
            "median_best_rel_rmse": float(np.median([r["best_rel_rmse"] for r in rs])),
            "worlds_selecting_sexp": sum(bool(r["selected_uses_sexp"]) for r in rs),
            "total_sexp_members": sum(r["n_sexp_members"] for r in rs),
            "median_valid_r2": float(np.median([r["median_seed_best_r2"] for r in rs])),
        }
    payload = {"summary": summ, "per_world": out}
    (OUT / "safeexp_score.json").write_text(json.dumps(payload, indent=1, default=str))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
