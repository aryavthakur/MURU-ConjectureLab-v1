"""Type 2 candidate selection and null calibration.

Runs the frozen Type 2 selection rule (`muru.objval.select`) over every world's
30 seeds, writes one result per world, and builds the null threshold table from
the `NCAL` block.

Selection reads candidates only. It never opens the truth manifest — recovery
scoring is a separate script that runs afterwards, on frozen output.

Null statistic (unchanged from Phase 3 §15, and deliberately so): the maximum
over the 30 seeds of the best validation R^2 attainable at complexity <= c. It
prices in search multiplicity, and it UPPER-BOUNDS whatever any selection rule
can report at complexity c inside the same world — so a threshold built from it
is conservative under the new rule as well as the old one. What changed is the
calibration size: 100 worlds instead of 40 (`BACKLOG.md` I8).

    python scripts/ov_30_select.py [--blocks G1B,G4] [--shard 0 --nshards 4]
    python scripts/ov_30_select.py --calibrate      # after selection completes
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
CKPT = ART / "ov_ckpt"
SEL = ART / "ov_sel"

NULL_QUANTILE = 0.95
N_BOOT_THRESHOLD = 2000


class Cand:
    __slots__ = ("expr_str", "expr", "complexity", "support", "engine", "seed",
                 "train_r2", "valid_r2", "invalid_fraction", "valid")

    def __init__(self, d: dict):
        import sympy as sp
        self.expr_str = d["expr_str"]
        self.expr = sp.sympify(d["expr"])
        self.complexity = int(d["complexity"])
        self.support = tuple(d["support"])
        self.engine = d["engine"]
        self.seed = int(d["seed"])
        self.train_r2 = float(d["train_r2"])
        self.valid_r2 = float(d["valid_r2"])
        self.invalid_fraction = float(d["invalid_fraction"])
        self.valid = bool(d["valid"])


def load_world_units(block_engine: str, world: str) -> tuple[dict, dict]:
    from muru.discovery.checkpoint import Store
    st = Store(CKPT)
    units = st.read_world(block_engine, world)
    meta = units.pop("_world", {})
    per_seed = {}
    for u in units.values():
        cands = []
        for c in u["candidates"]:
            try:
                cands.append(Cand(c))
            except Exception:
                continue
        per_seed[int(u["seed"])] = cands
    return per_seed, meta


def select_world(spec, engine: str, X, variables) -> dict:
    from muru.objval import select as sel
    from muru.objval.select import BAND_TOL
    per_seed, meta = load_world_units(f"{spec.block}_{engine}", spec.world_id)
    if not per_seed:
        return {}
    r = sel.select(spec.world_id, per_seed, variables, X, engine=engine)
    rep = r.reported
    slim = None
    if rep is not None:
        slim = {k: v for k, v in rep.items() if not k.startswith("_")}
    return {
        "world_id": spec.world_id, "block": spec.block, "family": spec.family,
        "replicate": spec.replicate, "noise_regime": spec.noise_regime,
        "cutoff_da": spec.cutoff_da, "null_construction": spec.null_construction,
        "engine": engine, "n_seeds": r.n_seeds, "band_tol": BAND_TOL,
        "band_sizes": r.band_sizes, "lattice_n": r.lattice_n,
        "n_families": len(r.families),
        "reported": slim,
        "runner_up": ({k: v for k, v in r.families[1].items()
                       if not k.startswith("_")} if len(r.families) > 1 else None),
        "r2_by_complexity_max": _curve(per_seed),
        "collapse": meta.get("collapse", {}),
        "split_counts": meta.get("split_counts", {}),
        "band_exprs": sorted({m.expr_str for m in rep["_members"]}) if rep else [],
        "all_band_exprs": sorted({c.expr_str for s in per_seed
                                  for c in sel.pareto_band(per_seed[s])}),
    }


def _curve(per_seed: dict) -> list:
    import numpy as np
    from muru.discovery.protocol import best_r2_by_complexity
    curves = [best_r2_by_complexity(c) for c in per_seed.values()]
    if not curves:
        return []
    m = np.max(np.vstack(curves), axis=0)
    return [None if not np.isfinite(x) else float(x) for x in m]


def calibrate() -> dict:
    """Per-complexity null threshold table from the NCAL block."""
    import numpy as np
    from muru.discovery.checkpoint import Store
    from muru.discovery.grammar import MAX_COMPLEXITY

    st = Store(SEL)
    rows = []
    for p in sorted((SEL / "NCAL").glob("*/*.json")) if (SEL / "NCAL").exists() else []:
        d = json.loads(p.read_text())
        if d.get("r2_by_complexity_max"):
            rows.append(d)
    if not rows:
        raise SystemExit("no NCAL selection results found; run selection first")

    from muru.objval.calibration import threshold_table

    M = np.array([[(-np.inf if x is None else x)
                   for x in r["r2_by_complexity_max"]] for r in rows])
    tab = threshold_table(M)

    # Per-construction reporting uses the same floor `threshold_table` applies,
    # so a world where the search produced nothing usable at some complexity is
    # kept in the sample rather than turning the quantile into -inf.
    from muru.objval.calibration import NEG_INF_FILL
    by_constr: dict[str, list] = {}
    for r in rows:
        by_constr.setdefault(r["null_construction"] or "unknown", []).append(
            [(NEG_INF_FILL if (x is None or not np.isfinite(x)) else x)
             for x in r["r2_by_complexity_max"]])

    out = {
        "statistic": ("max over the 30 seeds of the best validation R^2 "
                      "attainable at complexity <= c"),
        "why_unchanged": ("the statistic upper-bounds what ANY selection rule "
                          "can report at complexity c within a world, so a "
                          "threshold built from it stays conservative under the "
                          "Type 2 rule; only the calibration SIZE changed"),
        "max_complexity": MAX_COMPLEXITY,
        **tab,
        "per_construction_p95": {
            k: {"n": len(v),
                "p95_c10": float(np.quantile([r[10] for r in v], NULL_QUANTILE)),
                "p95_c20": float(np.quantile([r[20] for r in v], NULL_QUANTILE))}
            for k, v in by_constr.items()},
    }
    (ART / "ov_null_calibration.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items()
                      if k in ("n_calibration_worlds", "threshold")}, indent=1))
    return out


def main() -> int:
    import numpy as np
    from muru.discovery import protocol
    from muru.discovery.checkpoint import Store
    from muru.objval.plan2 import all_worlds2
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="")
    ap.add_argument("--engine", default="pysr")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()

    if a.calibrate:
        calibrate()
        return 0

    specs = all_worlds2()
    if a.blocks:
        want = set(a.blocks.split(","))
        specs = [s for s in specs if s.block in want]
    if a.collect:
        rows = []
        for s in specs:
            p = SEL / s.block / s.world_id.replace("|", "~") / f"{a.engine}.json"
            if p.exists():
                rows.append(json.loads(p.read_text()))
        (ART / "ov_selection.json").write_text(json.dumps(
            {"n": len(rows), "engine": a.engine, "rows": rows}, indent=1))
        print(f"[ov30] collected {len(rows)} worlds", flush=True)
        return 0

    if a.nshards > 1:
        specs = [s for i, s in enumerate(specs) if i % a.nshards == a.shard]

    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])
    Xsynth = np.random.default_rng(0).uniform(0.2, 1.8,
                                              size=(len(Xreal), len(variables)))
    store = Store(SEL)
    t0 = time.time()
    for i, s in enumerate(specs, 1):
        if store.done(s.block, s.world_id, a.engine):
            continue
        X = Xsynth if s.family == "G1A" else Xreal
        res = select_world(s, a.engine, X, variables)
        if not res:
            continue
        store.write(s.block, s.world_id, a.engine, res)
        rep = res["reported"]
        print(f"[s{a.shard} {i:4d}/{len(specs)}] {s.world_id:46s} "
              f"fam={res['n_families']:3d} "
              f"frac={0.0 if not rep else rep['selection_fraction']:.2f} "
              f"c={0 if not rep else rep['representative']['complexity']:2d} "
              f"supp={[] if not rep else rep['effective_support']} "
              f"[{(time.time()-t0)/60:.1f}m]", flush=True)
    print(f"[ov30] shard {a.shard} done in {(time.time()-t0)/60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
