"""FINAL ACCURACY SPRINT — exact headroom: three oracle ceilings.

RAW_CANDIDATE_ORACLE      best reachable over the band members as emitted
CONSTANT_REFIT_ORACLE     best reachable after the deterministic constant refit
CURRENT_GRAMMAR_ORACLE    union of the two, plus the representability verdict

Truth is used here ONLY to score, never to select.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                       # noqa: E402
import sympy as sp                                       # noqa: E402

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "src"))
sys.path.insert(0, str(WT / "scripts"))
OUT = WT / "artifacts" / "sprint"
CACHE = WT / "artifacts" / "accopt" / "candidate_cache.json"

SCORABLE = {"G1A", "G1B", "G1C", "G3", "G4M"}
_G = {}


def _init():
    from muru.discovery import protocol
    from muru.objval import select as selmod
    from muru.objval.plan2 import all_worlds2
    from muru.synth.generators import load_dev_covariates
    import sprint_features as sf
    sf._init()
    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8, size=(len(Xreal), len(variables)))
    _G["variables"] = variables
    _G["Zreal"] = selmod.lattice(Xreal, variables)
    _G["Zsynth"] = selmod.lattice(Xsynth, variables)
    _G["cov"] = cov
    _G["specs"] = {s.world_id: s for s in all_worlds2()}
    _G["truth"] = {w["world_id"]: w for w in json.loads(
        (WT / "artifacts" / "ov_truth_manifest.json").read_text())["worlds"]}
    _G["sf"] = sf


def process(world_cache):
    if not _G:
        _init()
    from muru.discovery import grammar, protocol
    from muru.objval import equiv, signature
    from muru.objval import recovery as recmod
    from ov_20_search import build_search_world
    sf = _G["sf"]
    variables = _G["variables"]
    wid = world_cache["world_id"]
    spec = _G["specs"][wid]
    Z = _G["Zsynth"] if spec.family == "G1A" else _G["Zreal"]

    w = build_search_world(spec, None if spec.family == "G1A" else _G["cov"])
    long, covw = w.search_inputs()
    wd = protocol.build_world_data(wid, long, covw)
    Xtr, ytr, wtr = wd.part("train")

    tr = _G["truth"][wid]
    params = recmod.freeze_constants(tr["family"], tr["params"], variables, Z)
    psig = recmod.planted_signature(tr["family"], params, variables, Z)
    if psig is None:
        return {"world_id": wid, "block": world_cache["block"], "scorable": False}
    ev, _ = recmod.planted_evaluator(tr["family"], params, variables)
    pv, pok = ev(Z)
    pb = set(psig["effective_support_blocks"])

    rows = []
    for m in world_cache["members"]:
        row = {"seed": m["seed"], "band_index": m["band_index"],
               "raw_support": bool(m.get("t_support")),
               "raw_family": bool(m.get("t_family")),
               "raw_exact": bool(m.get("t_exact")),
               "raw_rel_rmse": m.get("t_rel_rmse")}
        try:
            expr = grammar.parse(m["expr"], variables)
        except Exception:
            rows.append(row)
            continue
        rf = sf.refit_candidate(expr, variables, Xtr, ytr, wtr)
        rf.pop("_fn", None)
        row["refit_ok"] = bool(rf["refit_ok"])
        if not rf["refit_ok"]:
            rows.append(row)
            continue
        consts = sf.free_constants(expr)
        sub = {c: sp.Float(v) for c, v in zip(consts, rf["theta"])}
        rexpr = expr.xreplace(sub)
        sg = signature.signature(rexpr, variables, Z)
        if not sg["usable"]:
            row["refit_usable"] = False
            rows.append(row)
            continue
        v, o = signature._eval(rexpr, variables, Z)
        ok = pok & o
        row["refit_usable"] = True
        row["refit_support"] = bool(pb == set(sg["effective_support_blocks"]))
        fam = equiv.same_family(sg, psig, v, pv, ok)
        row["refit_family"] = bool(fam["same_family"])
        fc = equiv.functional_class(pv, v, ok)
        row["refit_exact"] = bool(fc["functionally_equivalent"])
        row["refit_rel_rmse"] = float(fc["numeric"]["rel_rmse"])
        row["refit_expr"] = sp.srepr(rexpr) if False else str(rexpr)
        rows.append(row)

    def anyk(k):
        return any(r.get(k) for r in rows)
    best_raw = min([r["raw_rel_rmse"] for r in rows
                    if r.get("raw_rel_rmse") is not None
                    and np.isfinite(r["raw_rel_rmse"])], default=float("nan"))
    best_ref = min([r["refit_rel_rmse"] for r in rows
                    if r.get("refit_rel_rmse") is not None
                    and np.isfinite(r["refit_rel_rmse"])], default=float("nan"))
    return {"world_id": wid, "block": world_cache["block"], "scorable": True,
            "n_members": len(rows),
            "raw": {"support": anyk("raw_support"), "family": anyk("raw_family"),
                    "exact": anyk("raw_exact"), "best_rel_rmse": best_raw},
            "refit": {"support": anyk("refit_support"), "family": anyk("refit_family"),
                      "exact": anyk("refit_exact"), "best_rel_rmse": best_ref},
            "union": {"support": anyk("raw_support") or anyk("refit_support"),
                      "family": anyk("raw_family") or anyk("refit_family"),
                      "exact": anyk("raw_exact") or anyk("refit_exact")},
            "n_rescued_family": sum(1 for r in rows if r.get("refit_family")
                                    and not r.get("raw_family")),
            "n_lost_family": sum(1 for r in rows if r.get("raw_family")
                                 and not r.get("refit_family")),
            "n_raw_family": sum(1 for r in rows if r.get("raw_family")),
            "n_refit_family": sum(1 for r in rows if r.get("refit_family")),
            "members": rows}


def main():
    import multiprocessing as mp
    cache = [w for w in json.loads(CACHE.read_text()) if w["block"] in SCORABLE]
    print(f"{len(cache)} scorable worlds", flush=True)
    t0 = time.time()
    ctx = mp.get_context("fork")
    out = []
    with ctx.Pool(7) as pool:
        for n, r in enumerate(pool.imap_unordered(process, cache, chunksize=1), 1):
            out.append(r)
            if n % 10 == 0 or n == len(cache):
                print(f"  [{n}/{len(cache)}] {time.time()-t0:.0f}s", flush=True)
    out.sort(key=lambda r: r["world_id"])
    (OUT / "headroom_members.json").write_text(json.dumps(out))

    summary = {}
    for lbl, blocks in [("all_positive", {"G1A", "G1B", "G1C"}), ("G1A", {"G1A"}),
                        ("G1B", {"G1B"}), ("G1C", {"G1C"}), ("G3", {"G3"}),
                        ("G4M", {"G4M"})]:
        ids = [r for r in out if r["block"] in blocks and r["scorable"]]
        summary[lbl] = {
            "n": len(ids),
            "RAW_CANDIDATE_ORACLE": {
                k: sum(1 for r in ids if r["raw"][k]) for k in ("support", "family", "exact")},
            "CONSTANT_REFIT_ORACLE": {
                k: sum(1 for r in ids if r["refit"][k]) for k in ("support", "family", "exact")},
            "CURRENT_GRAMMAR_ORACLE": {
                k: sum(1 for r in ids if r["union"][k]) for k in ("support", "family", "exact")},
            "worlds_where_refit_rescues_family": [
                r["world_id"] for r in ids if r["refit"]["family"] and not r["raw"]["family"]],
            "worlds_where_refit_loses_family": [
                r["world_id"] for r in ids if r["raw"]["family"] and not r["refit"]["family"]],
            "total_members_rescued": sum(r["n_rescued_family"] for r in ids),
            "total_members_lost": sum(r["n_lost_family"] for r in ids),
            "total_members_family_raw": sum(r["n_raw_family"] for r in ids),
            "total_members_family_refit": sum(r["n_refit_family"] for r in ids),
        }
    (OUT / "headroom_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
