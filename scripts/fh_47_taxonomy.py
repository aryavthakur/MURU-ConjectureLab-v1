"""FRESH HOLDOUT — post-reveal failure decomposition (DIAGNOSTIC ONLY).

Scores EVERY Pareto-band member against the planted law so the holdout failure
codes are computed by the same rule the development error decomposition used
(scripts/sprint_gate.py). The two architecture-specific branches of that rule
(CONSTANT_ESTIMATION_FAILURE, CROSS_STRATUM_GENERALIZATION_FAILURE) belong to
architectures B and C, which are NOT the frozen architecture, and are omitted.

Nothing here changes any prediction, threshold or tolerance.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "artifacts" / "fresh_holdout"
POSITIVE = {"G1A", "G1B", "G1C"}

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
    _G.update(variables=variables, Zreal=selmod.lattice(Xreal, variables),
              Zsynth=selmod.lattice(Xsynth, variables),
              truth={w["world_id"]: w for w in json.loads(
                  (ROOT / "fresh_holdout_truth_manifest.json").read_text())["worlds"]},
              cache={r["world_id"]: r for r in json.loads(
                  (OUT / "fh_candidate_cache.json").read_text())})


def oracle(wid):
    from muru.discovery import grammar
    from muru.objval import equiv, recovery as recmod, signature
    if not _G:
        _init()
    w = _G["cache"][wid]
    tr = _G["truth"][wid]
    V = _G["variables"]
    Z = _G["Zsynth"] if w["family"] == "G1A" else _G["Zreal"]
    params = recmod.freeze_constants(tr["family"], tr["params"], V, Z)
    psig = recmod.planted_signature(tr["family"], params, V, Z)
    if psig is None:
        return None
    ev, _ = recmod.planted_evaluator(tr["family"], params, V)
    pv, pok = ev(Z)
    pb = set(psig["effective_support_blocks"])
    out = []
    for m in w["members"]:
        if not m["usable"]:
            out.append({"t_support": False, "t_family": False,
                        "cluster": m["cluster"], "rel": float("nan")})
            continue
        e = grammar.parse(m["expr"], V)
        sg = signature.signature(e, V, Z)
        v, ok0 = signature._eval(e, V, Z)
        ok = pok & ok0
        fc = equiv.functional_class(pv, v, ok)
        out.append({
            "t_support": bool(pb == set(sg["effective_support_blocks"])),
            "t_family": bool(equiv.same_family(sg, psig, v, pv, ok)["same_family"]),
            "cluster": m["cluster"],
            "rel": float(fc["numeric"]["rel_rmse"])})
    return out


def main() -> int:
    _init()
    sc = json.loads((OUT / "fresh_holdout_scored.json").read_text())
    per = sc["per_world"]
    tax, rows = Counter(), []
    for wid in sorted(per):
        r = per[wid]
        if r["block"] not in POSITIVE or not r["scorable"]:
            continue
        oc = oracle(wid) or []
        oc_sup = any(m["t_support"] for m in oc)
        oc_fam = any(m["t_family"] for m in oc)
        cl = r["cluster"]
        fam_in_cluster = any(m["t_family"] for m in oc if m["cluster"] == cl)
        rel = r["t_rel_rmse"]
        if not r["report"]:
            code = "NULL_GATE_FALSE_NEGATIVE"
        elif not r["t_support"]:
            code = "SEARCH_FAILURE" if not oc_sup else "FAMILY_AGGREGATION_FAILURE"
        elif not r["t_family"]:
            if not oc_fam:
                code = "SEARCH_FAILURE"
            elif fam_in_cluster:
                code = "REPRESENTATIVE_SELECTION_FAILURE"
            else:
                code = "FAMILY_AGGREGATION_FAILURE"
            if rel is not None and np.isfinite(rel) and rel <= 0.115 \
                    and code != "SEARCH_FAILURE":
                code = "FAMILY_TOLERANCE_BOUNDARY"
        else:
            code = "OK"
        tax[code] += 1
        if code != "OK":
            rows.append({
                "world_id": wid, "block": r["block"], "noise": r["noise_regime"],
                "code": code, "expr": r["expr"], "complexity": r["complexity"],
                "valid_r2": r["valid_r2"], "rel_rmse_vs_truth": rel,
                "planted_expr": r["planted_expr"],
                "planted_blocks": r["planted_blocks"],
                "recovered_blocks": r["eff_blocks"],
                "oracle_support_in_pool": oc_sup,
                "oracle_family_in_pool": oc_fam,
                "family_correct_members_in_chosen_cluster":
                    sum(1 for m in oc if m["cluster"] == cl and m["t_family"]),
                "family_correct_members_in_pool":
                    sum(1 for m in oc if m["t_family"]),
                "best_rel_rmse_in_pool": float(np.nanmin(
                    [m["rel"] for m in oc])) if oc else None,
                "n_members": len(oc), "n_clusters": r["n_clusters"]})
    payload = {"scope": "positive worlds only, diagnostic",
               "rule": "scripts/sprint_gate.py decomposition, arch-A branches only",
               "counts": dict(tax), "rows": rows}
    (OUT / "failure_decomposition.json").write_text(
        json.dumps(payload, indent=1, default=str))
    print(json.dumps({"counts": dict(tax)}, indent=1))
    for r in rows:
        print(f"  {r['code']:32s} {r['world_id']:34s} rel={r['rel_rmse_vs_truth']:.4f} "
              f"oc_fam={r['oracle_family_in_pool']} in_cluster="
              f"{r['family_correct_members_in_chosen_cluster']} "
              f"pool={r['family_correct_members_in_pool']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
