"""DEVELOPMENT ONLY — cost of the two acceptance conditions Phase 3 did not use.

The Type 2 acceptance rule reinstates two master-plan conditions that Phase 3's
acceptance rule omitted:

* **ceiling fraction** — L4 requires >= 80% of the Tier B ceiling (§16.2, §14.4);
  `PHASE3_PREREGISTRATION.md` §20 explicitly waived it;
* **H-MAIN adequacy** — the Type 2 claim is the collapse itself.

Both make acceptance strictly harder, so neither can inflate a false-positive
rate. What has to be checked before freezing is the opposite risk: that they do
not destroy recovery in worlds where a real relationship exists. This script
measures them on already-seen Phase 3 worlds. It is development evidence and
counts toward nothing.

    python scripts/ov_dev_02_new_conditions.py [--blocks G1,G3] [--per-block N]
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

ART = ROOT / "artifacts"


def main() -> int:
    from muru.discovery import falsify, protocol
    from muru.objval import adjudicate
    from muru.synth.generators import build_world, load_dev_covariates

    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", default="G1,G3")
    ap.add_argument("--per-block", type=int, default=9)
    ap.add_argument("--out", default=str(ART / "ov_dev_new_conditions.json"))
    a = ap.parse_args()

    dev = json.loads((ART / "ov_dev_selector_study.json").read_text())["rows"]
    want = set(a.blocks.split(","))
    rows_in = [r for r in dev if r["block"] in want and r["reported"]]

    cov = load_dev_covariates()
    out, t0 = [], time.time()
    seen: dict[str, int] = {}
    for r in rows_in:
        b = r["block"]
        if seen.get(b, 0) >= a.per_block:
            continue
        seen[b] = seen.get(b, 0) + 1

        fam, rep, regime = r["world"].split("~")
        world = build_world(fam, int(rep[1:]), regime, cov=cov)
        wd = protocol.build_world_data(r["world"].replace("~", "|"),
                                       world.long, world.cov)
        expr = sp.sympify(r["reported"]["expr"].replace("^", "**"))
        Xtr, ytr, wtr = wd.part("train")
        Xte, yte, wte = wd.part("test")
        test_r2 = falsify.r2_after_refit(expr, wd.variables, Xtr, ytr, wtr,
                                         Xte, yte, wte)
        ceil = adjudicate.flexible_ceiling(wd)
        frac = test_r2 / ceil if ceil > adjudicate.CEILING_MIN_R2 else float("nan")
        hm = wd.fit.hmain
        rec = {"block": b, "world": r["world"],
               "complexity": r["reported"]["complexity"],
               "valid_r2": r["reported"]["valid_r2"],
               "test_r2": float(test_r2), "ceiling_r2": float(ceil),
               "ceiling_fraction": float(frac),
               # mirrors adjudicate.accept_type2: the condition is waived only
               # when the CEILING carries no signal, never when the candidate's
               # own held-out R^2 is degenerate
               "passes_ceiling": bool(
                   ceil <= adjudicate.CEILING_MIN_R2
                   or (np.isfinite(frac) and frac >= adjudicate.MIN_CEILING_FRACTION)),
               "h_main_rejected": bool(hm["h_main_rejected"]),
               "h_main_ratio": hm["ratio"], "h_main_ci": hm["ci"]}
        out.append(rec)
        print(f"[dev2 {b} {r['world']:36s}] test_r2={test_r2:.3f} "
              f"ceil={ceil:.3f} frac={frac:.3f} pass={rec['passes_ceiling']} "
              f"hmain_rej={rec['h_main_rejected']} [{(time.time()-t0)/60:.1f}m]",
              flush=True)

    Path(a.out).write_text(json.dumps(
        {"purpose": "DEVELOPMENT ONLY — not evidence for the Type 2 verdict",
         "min_ceiling_fraction": adjudicate.MIN_CEILING_FRACTION,
         "rows": out}, indent=1))
    print(f"[dev2] wrote {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
