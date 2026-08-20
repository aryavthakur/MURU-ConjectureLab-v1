"""FRESH HOLDOUT — deterministic equation-example selection policy.

Declared before the reveal is scored. Selection depends only on the frozen
world identity (sha256 tie-break) and on the stratum, never on how pretty an
equation looks.

SUCCESSES: one world from each stratum in the fixed order
    [G1A, G1B_low, G1B_moderate, G1B_adverse, G1C]
qualifying = positive, scorable, t_family True, report True. Within a stratum,
the qualifying world with the smallest sha256("fh-example|" + world_id). If a
stratum has no qualifying world it contributes none, and the shortfall is made
up by continuing round-robin through the same stratum order.

FAILURES: 3 rows, one per distinct failure class in alphabetical class order,
smallest sha256 within class; if fewer than 3 classes exist, continue
round-robin through the classes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "fresh_holdout"

STRATA = [("G1A", {"G1A"}, None), ("G1B_low", {"G1B"}, "low"),
          ("G1B_moderate", {"G1B"}, "moderate"),
          ("G1B_adverse", {"G1B"}, "adverse"), ("G1C", {"G1C"}, None)]
N_SUCCESS = 5
N_FAILURE = 3


def rank(wid):
    return hashlib.sha256(("fh-example|" + wid).encode()).hexdigest()


def main() -> int:
    import sympy as sp
    sys.path.insert(0, str(ROOT / "src"))
    from muru.discovery import grammar, protocol
    variables = list(protocol.FEATURES)

    sc = json.loads((OUT / "fresh_holdout_scored.json").read_text())
    per = sc["per_world"]

    pools = []
    for name, blocks, noise in STRATA:
        ids = sorted([w for w, r in per.items()
                      if r["block"] in blocks and r["scorable"]
                      and (noise is None or r["noise_regime"] == noise)
                      and r["t_family"] and r["report"]], key=rank)
        pools.append((name, ids))
    picks, i = [], 0
    while len(picks) < N_SUCCESS and any(p[1] for p in pools):
        name, ids = pools[i % len(pools)]
        if ids:
            picks.append((name, ids.pop(0)))
        i += 1
        if i > 200:
            break

    fails = sc["failure_rows"]
    byclass = {}
    for f in fails:
        byclass.setdefault(f["class"], []).append(f)
    for k in byclass:
        byclass[k].sort(key=lambda f: rank(f["world_id"]))
    fpicks, j = [], 0
    classes = sorted(byclass)
    while len(fpicks) < N_FAILURE and any(byclass[c] for c in classes):
        c = classes[j % len(classes)]
        if byclass[c]:
            fpicks.append(byclass[c].pop(0))
        j += 1
        if j > 200:
            break

    def canon(e):
        if not e:
            return None
        try:
            return str(sp.simplify(sp.nsimplify(grammar.parse(e, variables),
                                                rational=False)))
        except Exception:
            try:
                return str(sp.simplify(grammar.parse(e, variables)))
            except Exception:
                return "(canonicalisation failed)"

    rows = []
    for stratum, wid in picks:
        r = per[wid]
        rows.append({"kind": "success", "stratum": stratum, "world_id": wid,
                     "block": r["block"], "noise_regime": r["noise_regime"],
                     "planted_expr": r["planted_expr"],
                     "planted_support": r["planted_support"],
                     "planted_blocks": r["planted_blocks"],
                     "discovered_raw": r["expr"],
                     "discovered_canonical": canon(r["expr"]),
                     "recovered_support": r["eff_blocks"],
                     "recovered_variables": r["eff_support"],
                     "t_support": r["t_support"], "t_family": r["t_family"],
                     "t_exact": r["t_exact"], "t_rel_rmse": r["t_rel_rmse"],
                     "valid_r2": r["valid_r2"],
                     "median_seed_best_r2": r["gate"]["median_seed_best_r2"],
                     "selection_fraction": r["gate"]["selection_fraction"],
                     "complexity": r["complexity"], "reported": r["report"]})
    for f in fpicks:
        r = per[f["world_id"]]
        rows.append({"kind": "failure", "failure_class": f["class"],
                     "world_id": f["world_id"], "block": r["block"],
                     "noise_regime": r["noise_regime"],
                     "planted_expr": r["planted_expr"],
                     "planted_support": r["planted_support"],
                     "planted_blocks": r["planted_blocks"],
                     "discovered_raw": r["expr"],
                     "discovered_canonical": canon(r["expr"]),
                     "recovered_support": r["eff_blocks"],
                     "recovered_variables": r["eff_support"],
                     "t_support": r["t_support"], "t_family": r["t_family"],
                     "t_exact": r["t_exact"], "t_rel_rmse": r["t_rel_rmse"],
                     "valid_r2": r["valid_r2"],
                     "median_seed_best_r2": r["gate"]["median_seed_best_r2"],
                     "selection_fraction": r["gate"]["selection_fraction"],
                     "complexity": r["complexity"], "reported": r["report"]})

    (OUT / "equation_examples.json").write_text(json.dumps(
        {"policy": __doc__, "rows": rows}, indent=1, default=str))
    print(json.dumps(rows, indent=1, default=str)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
