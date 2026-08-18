"""DEVELOPMENT ONLY — Type 2 selector study on already-seen Phase 3 worlds.

This script is part of the bounded method-development stage of the prospective
objective-alignment validation study. It runs candidate Type 2 selection rules
over the Phase 3 checkpoint store, which holds every seed's complete Pareto
front for all 240 governed worlds.

NOTHING here counts toward the study's verdict. Phase 3's worlds have been seen;
using them to score a rule that was designed on them would be circular. They are
used only to choose the rule, exactly as `OBJECTIVE_ALIGNMENT_AMENDMENT.md` §8
permits. The governed evidence comes from fresh worlds generated after the
preregistration is committed.

    python scripts/ov_dev_01_selector_study.py [--blocks G1,G4] [--out FILE]
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

import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

CKPT = ROOT / "artifacts" / "p3_ckpt"
ART = ROOT / "artifacts"


class Cand:
    """A checkpointed Phase 3 candidate, rehydrated."""

    __slots__ = ("expr_str", "expr", "complexity", "support", "engine", "seed",
                 "train_r2", "valid_r2", "invalid_fraction", "valid")

    def __init__(self, d: dict):
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


def load_world(block_dir: Path, world: str) -> tuple[dict, dict]:
    per_seed: dict[int, list] = {}
    meta: dict = {}
    for p in sorted((block_dir / world).glob("*.json")):
        d = json.loads(p.read_text())
        if p.stem == "_world":
            meta = d
            continue
        cands = []
        for c in d["candidates"]:
            try:
                cands.append(Cand(c))
            except Exception:
                continue
        per_seed[int(d["seed"])] = cands
    return per_seed, meta


def main() -> int:
    from muru.discovery import protocol
    from muru.objval import select as sel
    from muru.synth.generators import load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="G1,G2,G3,G4,G4M,G5,GA,GC,GRT,NCAL")
    ap.add_argument("--engine", default="pysr")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=str(ART / "ov_dev_selector_study.json"))
    a = ap.parse_args()

    cov = load_dev_covariates()
    variables = list(protocol.FEATURES)
    Xreal = np.column_stack([cov[c].to_numpy(float) / protocol.SCALE[c]
                             for c in variables])

    rows = []
    t0 = time.time()
    for block in a.blocks.split(","):
        bd = CKPT / f"{block}_{a.engine}"
        if not bd.exists():
            print(f"[dev] missing {bd}", flush=True)
            continue
        worlds = sorted(p.name for p in bd.iterdir() if p.is_dir())
        if a.limit:
            worlds = worlds[:a.limit]
        for wi, w in enumerate(worlds, 1):
            per_seed, meta = load_world(bd, w)
            if not per_seed:
                continue
            # GA is fully synthetic: its descriptor domain is uniform on
            # [0.2, 1.8] in every dimensionless variable, by construction.
            X = Xreal
            if block == "GA":
                X = np.random.default_rng(0).uniform(
                    0.2, 1.8, size=(len(Xreal), len(variables)))
            r = sel.select(w, per_seed, variables, X, engine=a.engine)
            rep = r.reported
            rows.append({
                "block": block, "world": w,
                "n_seeds": r.n_seeds,
                "median_band_size": float(np.median(r.band_sizes)) if r.band_sizes else 0.0,
                "max_band_size": int(max(r.band_sizes)) if r.band_sizes else 0,
                "n_families": len(r.families),
                "reported": None if rep is None else {
                    "expr": rep["representative"]["expr"],
                    "complexity": rep["representative"]["complexity"],
                    "valid_r2": rep["representative"]["valid_r2"],
                    "selection_fraction": rep["selection_fraction"],
                    "effective_support": rep["effective_support"],
                    "effective_support_blocks": rep["effective_support_blocks"],
                    "block_exponents": rep["block_exponents"],
                    "block_signs": rep["block_signs"],
                    "symbolic_support": rep["symbolic_support"],
                    "exponents": rep["exponents"],
                    "signs": rep["signs"],
                    "n_distinct_algebraic_forms": rep["n_distinct_algebraic_forms"],
                    "member_complexities": rep["member_complexities"],
                    "exponent_spread": rep["exponent_spread_across_members"],
                },
                "runner_up_fraction": (r.families[1]["selection_fraction"]
                                       if len(r.families) > 1 else 0.0),
            })
            el = time.time() - t0
            print(f"[dev {block} {wi:3d}/{len(worlds)}] {w:40s} "
                  f"fam={len(r.families):3d} "
                  f"frac={0.0 if rep is None else rep['selection_fraction']:.2f} "
                  f"c={0 if rep is None else rep['representative']['complexity']:2d} "
                  f"supp={[] if rep is None else rep['effective_support']} "
                  f"[{el/60:.1f}m]", flush=True)

    Path(a.out).write_text(json.dumps({
        "purpose": "DEVELOPMENT ONLY — not evidence for the Type 2 verdict",
        "source": "Phase 3 checkpoint store (already-seen worlds)",
        "band_tol": sel.BAND_TOL, "lattice_n": sel.N_LATTICE,
        "rows": rows}, indent=1, default=str))
    print(f"[dev] wrote {a.out} ({len(rows)} worlds, "
          f"{(time.time()-t0)/60:.1f} min)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
