"""Build the per-complexity null threshold table from the calibration worlds.

The statistic is the one the real protocol reports: the maximum over 30 seeds of
the best validation R² attainable at complexity <= c. Taking the max over seeds
is what prices in search multiplicity.

Calibration worlds are the NCAL block; they are disjoint from the 100 G4 worlds
that measure the false-positive rate, so the threshold is not fitted to the data
that tests it.

Writes `artifacts/p3_null_calibration.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.discovery import grammar, nulls, protocol      # noqa: E402
from muru.discovery.checkpoint import Store              # noqa: E402
from muru.synth import plan                              # noqa: E402

ART = ROOT / "artifacts"
CKPT = ART / "p3_ckpt"


def curve_from_units(units: dict) -> np.ndarray:
    """Max over seeds of best validation R^2 at complexity <= c."""
    per_seed = []
    for key, payload in units.items():
        if key == "_world":
            continue
        best = np.full(grammar.MAX_COMPLEXITY + 1, -np.inf)
        for c in payload["candidates"]:
            if not c["valid"] or c["valid_r2"] is None:
                continue
            r = float(c["valid_r2"])
            if not np.isfinite(r):
                continue
            cc = min(int(c["complexity"]), grammar.MAX_COMPLEXITY)
            best[cc] = max(best[cc], r)
        per_seed.append(np.maximum.accumulate(best))
    if not per_seed:
        return np.full(grammar.MAX_COMPLEXITY + 1, -np.inf)
    return np.max(np.vstack(per_seed), axis=0)


def block_curves(block: str, engine: str = "pysr") -> dict[str, np.ndarray]:
    store = Store(CKPT)
    out = {}
    for spec in plan.all_worlds():
        if spec.block != block:
            continue
        units = store.read_world(f"{block}_{engine}", spec.world_id)
        seeds = [k for k in units if k != "_world"]
        if len(seeds) < protocol.N_SEEDS:
            continue
        out[spec.world_id] = curve_from_units(units)
    return out


def main() -> int:
    curves = block_curves("NCAL")
    if not curves:
        print("[t3_30] no completed NCAL worlds; run scripts/t3_20_search.py first")
        return 1

    table = nulls.threshold_table(list(curves.values()))
    # construction-level breakdown, so a single pathological construction is
    # visible rather than buried in the pooled quantile
    by_con: dict[str, list] = {}
    for spec in plan.all_worlds():
        if spec.block == "NCAL" and spec.world_id in curves:
            by_con.setdefault(spec.null_construction, []).append(
                curves[spec.world_id])
    per_construction = {
        con: {"n_worlds": len(cs),
              "p95_by_complexity": [
                  float(np.percentile([c[k] for c in cs if np.isfinite(c[k])], 95))
                  if any(np.isfinite(c[k]) for c in cs) else None
                  for k in range(grammar.MAX_COMPLEXITY + 1)]}
        for con, cs in by_con.items()}

    out = {
        **table,
        "block": "NCAL",
        "engine": "pysr",
        "n_seeds_per_world": protocol.N_SEEDS,
        "worlds": sorted(curves),
        "per_construction": per_construction,
        "disjointness": ("calibration worlds are the NCAL block and are disjoint "
                         "from the 100 G4 worlds used to measure the "
                         "false-positive rate"),
        "frozen_for_phase4": True,
    }
    (ART / "p3_null_calibration.json").write_text(json.dumps(out, indent=1))
    thr = table["threshold_by_complexity"]
    print(f"[t3_30] {table['n_worlds']} calibration worlds; "
          f"threshold c=4 {thr[4]:.4f}, c=10 {thr[10]:.4f}, c=20 {thr[20]:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
