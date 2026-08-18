"""Separate two questions that the G1 recovery rate conflates.

1. **Is the search capable?** Does ANY candidate, anywhere on the 30 seeds'
   Pareto fronts, match the planted law?
2. **Does the system report it?** Is the candidate the frozen ranking rule
   actually SELECTS the matching one?

The distinction matters for the Phase 3 verdict. A system that never finds the
law is broken in one way; a system that finds it and then discards it in favour
of a simpler near-equivalent is broken in a different way, with a different and
specific remedy.

This changes no threshold and no rule. It characterizes a result.

Writes `artifacts/p3_recovery_diagnosis.json`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                        # noqa: E402
import sympy as sp                                        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"

TRUTH = {
    "G1B": "1.7017*sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)",
    "G3": "1.7017*precursor_mz**0.6",
    "GA": "1.5*precursor_mz + 0.5*heteroatom_fraction**2",
}


def diagnose(spec) -> dict:
    from muru.discovery import equivalence, grammar, protocol
    from muru.discovery.checkpoint import Store
    from muru.synth.generators import build_world, load_dev_covariates

    cov = None if spec.family == "GA" else load_dev_covariates()
    world = build_world(spec.family, spec.replicate, spec.noise_regime, cov=cov)
    wd = protocol.build_world_data(spec.world_id, world.long, world.cov)
    V = wd.variables
    D = equivalence.latin_hypercube(equivalence.domain_bounds(wd.X, V), V,
                                    equivalence.N_LHC_ADJUDICATE, seed=99)
    truth = grammar.parse(TRUTH[spec.family], V)
    tv, tok = grammar.evaluate(truth, V, D)

    units = Store(ART / "p3_ckpt").read_world(f"{spec.block}_pysr", spec.world_id)
    seen: dict[str, dict] = {}
    for k, payload in units.items():
        if k == "_world":
            continue
        for c in payload["candidates"]:
            if not c["valid"] or c["expr_str"] in seen:
                continue
            try:
                e = sp.sympify(c["expr"])
            except Exception:
                continue
            v, ok = grammar.evaluate(e, V, D)
            rel = equivalence.numeric_relation(tv, v, ok & tok)
            seen[c["expr_str"]] = {
                "complexity": c["complexity"], "valid_r2": c["valid_r2"],
                "rel_rmse": rel["rel_rmse"], "r": rel["r"],
                "match": bool(rel["r"] > equivalence.FUNC_MIN_R
                              and rel["rel_rmse"] < equivalence.FUNC_REL_RMSE)}

    matches = {k: v for k, v in seen.items() if v["match"]}
    best = min(seen.values(), key=lambda d: d["rel_rmse"]) if seen else None
    cheapest_match = (min(matches.values(), key=lambda d: d["complexity"])
                      if matches else None)
    return {
        "world_id": spec.world_id, "block": spec.block, "family": spec.family,
        "noise_regime": spec.noise_regime,
        "n_distinct_candidates": len(seen),
        "search_found_the_law": bool(matches),
        "n_matching_candidates": len(matches),
        "cheapest_matching_complexity":
            cheapest_match["complexity"] if cheapest_match else None,
        "cheapest_matching_r2": cheapest_match["valid_r2"] if cheapest_match else None,
        "best_rel_rmse_anywhere": best["rel_rmse"] if best else None,
        "best_rel_rmse_complexity": best["complexity"] if best else None,
        "tolerance": equivalence.FUNC_REL_RMSE,
    }


def main() -> int:
    import multiprocessing as mp
    from muru.synth import plan

    specs = [s for s in plan.all_worlds() if s.block in ("G1", "G3", "GA")]
    ctx = mp.get_context("spawn")
    with ctx.Pool(4) as pool:
        recs = list(pool.imap_unordered(diagnose, specs))
    recs.sort(key=lambda r: r["world_id"])

    worlds = {w["world_id"]: w for w in json.loads((ART / "p3_worlds.json").read_text())
              if w.get("status") == "ok"}
    for r in recs:
        w = worlds.get(r["world_id"], {})
        r["system_selected_a_match"] = bool(
            (w.get("recovery") or {}).get("functionally_equivalent"))
        r["selected_complexity"] = (w.get("candidate") or {}).get("complexity")
        r["selected_r2"] = (w.get("candidate") or {}).get("valid_r2")
        r["accepted"] = (w.get("acceptance") or {}).get("accepted")

    summary = {}
    for block in ("G1", "G3", "GA"):
        for regime in ("low", "moderate", "adverse"):
            sub = [r for r in recs
                   if r["block"] == block and r["noise_regime"] == regime]
            if not sub:
                continue
            found = sum(r["search_found_the_law"] for r in sub)
            sel = sum(r["system_selected_a_match"] for r in sub)
            gaps = [r["cheapest_matching_complexity"] - r["selected_complexity"]
                    for r in sub
                    if r["cheapest_matching_complexity"] and r["selected_complexity"]]
            summary[f"{block}/{regime}"] = {
                "n": len(sub),
                "search_capability_rate": found / len(sub),
                "system_report_rate": sel / len(sub),
                "median_complexity_gap": float(np.median(gaps)) if gaps else None,
                "median_best_rel_rmse": float(np.median(
                    [r["best_rel_rmse_anywhere"] for r in sub
                     if r["best_rel_rmse_anywhere"] is not None])),
            }

    out = {
        "question": ("does the search FIND the planted law, and does the frozen "
                     "ranking rule SELECT it?"),
        "changes_no_threshold": True,
        "summary": summary,
        "worlds": recs,
    }
    (ART / "p3_recovery_diagnosis.json").write_text(json.dumps(out, indent=1))
    for k, v in summary.items():
        print(f"[t3_45] {k:16s} search finds {v['search_capability_rate']:.0%}, "
              f"system reports {v['system_report_rate']:.0%}, "
              f"complexity gap {v['median_complexity_gap']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
