"""Type 2 acceptance: null threshold, ceiling, H-MAIN and the F1-F12 harness.

Runs after selection is complete and frozen. Uses the world's data only — the
planted law is not read here; truth-based recovery is scored separately by
`ov_45_recovery.py`.

    python scripts/ov_40_adjudicate.py [--blocks G4] [--shard 0 --nshards 4]
    python scripts/ov_40_adjudicate.py --collect
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
    from muru.discovery import falsify, protocol
    from muru.discovery.checkpoint import Store
    from muru.objval import adjudicate as adj
    from muru.objval.plan2 import all_worlds2
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="")
    ap.add_argument("--engine", default="pysr")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()

    specs = all_worlds2()
    if a.blocks:
        want = set(a.blocks.split(","))
        specs = [s for s in specs if s.block in want]

    if a.collect:
        rows = []
        for s in specs:
            p = ADJ / s.block / s.world_id.replace("|", "~") / f"{a.engine}.json"
            if p.exists():
                rows.append(json.loads(p.read_text()))
        (ART / "ov_adjudication.json").write_text(json.dumps(
            {"n": len(rows), "engine": a.engine, "rows": rows}, indent=1,
            default=str))
        print(f"[ov40] collected {len(rows)} worlds", flush=True)
        return 0

    cal = json.loads((ART / "ov_null_calibration.json").read_text())
    thr = np.array(cal["threshold"], float)

    if a.nshards > 1:
        specs = [s for i, s in enumerate(specs) if i % a.nshards == a.shard]

    sys.path.insert(0, str(ROOT / "scripts"))
    from ov_20_search import build_search_world

    cov = load_dev_covariates()
    store, selstore = Store(ADJ), Store(SEL)
    t0 = time.time()
    for i, s in enumerate(specs, 1):
        if store.done(s.block, s.world_id, a.engine):
            continue
        if not selstore.done(s.block, s.world_id, a.engine):
            continue
        res = selstore.read(s.block, s.world_id, a.engine)
        rep = res["reported"]

        world = build_search_world(s, None if s.family == "G1A" else cov)
        long, covw = world.search_inputs()
        wd = protocol.build_world_data(s.world_id, long, covw)
        ceiling = adj.flexible_ceiling(wd)

        harness, expr, cx = None, None, 0
        if rep is not None:
            expr = sp.sympify(rep["representative"]["expr"].replace("^", "**"))
            cx = int(rep["representative"]["complexity"])
            harness = falsify.run_harness(wd, expr, cx,
                                          tuple(rep["effective_support"]),
                                          thr, {"fraction": rep["selection_fraction"]})
        verdict = adj.accept_type2(wd, rep, expr, cx, thr, harness, ceiling)
        store.write(s.block, s.world_id, a.engine, {
            "world_id": s.world_id, "block": s.block, "family": s.family,
            "replicate": s.replicate, "noise_regime": s.noise_regime,
            "cutoff_da": s.cutoff_da,
            "null_construction": s.null_construction,
            "engine": a.engine, "verdict": verdict,
            "harness": harness, "ceiling_r2": float(ceiling),
            "collapse_resid_sd": float(wd.fit.resid_sd),
            "hmain": wd.fit.hmain})
        print(f"[s{a.shard} {i:4d}/{len(specs)}] {s.world_id:46s} "
              f"acc={verdict['accepted']} "
              f"nonmass={verdict.get('claims_non_mass_structure')} "
              f"fail={verdict.get('failed_conditions')} "
              f"[{(time.time()-t0)/60:.1f}m]", flush=True)
    print(f"[ov40] shard {a.shard} done in {(time.time()-t0)/60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
