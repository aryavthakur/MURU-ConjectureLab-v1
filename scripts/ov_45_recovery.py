"""Truth-based recovery scoring — the FIRST script that opens the planted law.

Preconditions, asserted before anything is read: every world in scope has a
frozen selection result and a frozen adjudication verdict. Recovery cannot
influence either, because both are already written to disk.

Reports Type 2 and Type 3 quantities side by side and never merges them:
support recovery, exponent recovery, shape-family recovery and family recovery
are Type 2; exact functional-form recovery is a Type 3 diagnostic, reported with
`search_found_the_law` beside it so that a search failure and a reporting
failure stay distinguishable.

    python scripts/ov_45_recovery.py [--blocks G1B]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"
SEL = ART / "ov_sel"
ADJ = ART / "ov_adj"


def main() -> int:
    import numpy as np
    import sympy as sp
    from muru.discovery import protocol
    from muru.discovery.checkpoint import Store
    from muru.objval import recovery, select as selmod
    from muru.objval.plan2 import all_worlds2
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="")
    ap.add_argument("--engine", default="pysr")
    ap.add_argument("--out", default=str(ART / "ov_recovery.json"))
    a = ap.parse_args()

    specs = all_worlds2()
    if a.blocks:
        want = set(a.blocks.split(","))
        specs = [s for s in specs if s.block in want]

    selstore, adjstore = Store(SEL), Store(ADJ)
    missing = [s.world_id for s in specs
               if not (selstore.done(s.block, s.world_id, a.engine)
                       and adjstore.done(s.block, s.world_id, a.engine))]
    if missing:
        raise SystemExit(
            f"refusing to open the truth manifest: {len(missing)} world(s) have "
            f"no frozen selection or adjudication result, e.g. {missing[:3]}")

    truth = {w["world_id"]: w for w in
             json.loads((ART / "ov_truth_manifest.json").read_text())["worlds"]}

    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8,
                                              size=(len(Xreal), len(variables)))

    rows, t0 = [], time.time()
    for i, s in enumerate(specs, 1):
        res = selstore.read(s.block, s.world_id, a.engine)
        ver = adjstore.read(s.block, s.world_id, a.engine)
        tr = truth[s.world_id]
        X = Xsynth if s.family == "G1A" else Xreal
        Z = selmod.lattice(X, variables)

        rep = res["reported"]
        rep_expr = (sp.sympify(rep["representative"]["expr"].replace("^", "**"))
                    if rep else None)
        band = []
        for e in res.get("all_band_exprs", []):
            try:
                band.append(sp.sympify(e.replace("^", "**")))
            except Exception:
                continue
        col = res.get("collapse", {})
        sc = recovery.score_world(
            tr["family"], tr["params"], variables, Z, rep, rep_expr, band,
            phi_u=col.get("phi_u"), phi_v=col.get("phi_v"))
        rows.append({
            "world_id": s.world_id, "block": s.block, "family": s.family,
            "noise_regime": s.noise_regime, "replicate": s.replicate,
            "cutoff_da": s.cutoff_da,
            "carrier": tr["params"].get("carrier"),
            "accepted": ver["verdict"]["accepted"],
            "claims_non_mass_structure": ver["verdict"].get("claims_non_mass_structure"),
            "selection_fraction": (rep or {}).get("selection_fraction", 0.0),
            "complexity": (rep or {}).get("representative", {}).get("complexity"),
            "planted_expr": tr["planted_expr"],
            "recovery": sc})
        if i % 25 == 0 or i == len(specs):
            print(f"[ov45] {i:4d}/{len(specs)} [{(time.time()-t0)/60:.1f}m]",
                  flush=True)

    Path(a.out).write_text(json.dumps(
        {"n": len(rows), "engine": a.engine,
         "recovery_version": recovery.RECOVERY_VERSION, "rows": rows},
        indent=1, default=str))
    print(f"[ov45] wrote {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
