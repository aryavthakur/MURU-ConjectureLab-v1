"""Fold-specific optimism: rerun LIN / V1A / V1C on three FRESH repeats (new seeds)
and compare to the ledgered results on the frozen folds."""
import sys, json, os, time
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ[v] = "1"
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path('/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-reconciliation-f69f63')
SP = Path('/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/review_leakage')
sys.path.insert(0, str(ROOT / 'src'))
from muru.wur_stage2 import cv as CV, folds as FO, arms_v1 as AV
from muru.splits import grouped_folds

long, cov, frame = CV.load_dev2b()
fresh = {"k": 5, "repeats": []}
for r, seed in enumerate((30260913, 30260914, 30260915)):
    f = grouped_folds(frame["scaffold_group"], n_folds=5, seed=seed)
    fresh["repeats"].append({"repeat": r, "seed": seed, "assignment": dict(zip(frame["group_key"], (int(x) for x in f.to_numpy())))})
frozen = FO.load_folds()
out = {}
for label, folds in (("fresh", fresh), ("frozen", frozen)):
    t0 = time.time()
    b0p = CV.b0_predictions(long, cov, frame, folds)
    res = {}
    for name, mk in (("B0", CV.B0NullProfile), ("B1", CV.B1MassOnly), ("LIN", CV.LinRidge), ("V1A", AV.StableLaw), ("V1C", AV.RichRidge)):
        res[name] = CV.run_cv(mk, long, cov, frame, folds, b0p, with_loeo=False)
        print(label, name, f"P1 {res[name].p1_vector().mean():.4f} sd {res[name].p1_vector().std(ddof=1):.4f} {time.time()-t0:.0f}s", flush=True)
    out[label] = {n: r.p1_vector().tolist() for n, r in res.items()}
    out[label + "_cmp"] = {"V1C_vs_LIN": CV.compare(res["V1C"], res["LIN"]), "V1C_vs_V1A": CV.compare(res["V1C"], res["V1A"]),
                           "V1A_vs_LIN": CV.compare(res["V1A"], res["LIN"]), "V1C_vs_B1": CV.compare(res["V1C"], res["B1"])}
    out[label + "_boot"] = {"V1C_vs_LIN": CV.paired_bootstrap(res["V1C"], res["LIN"])}
json.dump(out, open(SP / "refit_fresh_folds.json", "w"), indent=1)
for label in ("frozen", "fresh"):
    print(label, {k: (round(v["mean_diff"], 5), v["wins"], round(v["se_diff"], 5)) for k, v in out[label + "_cmp"].items()})
print("DONE")
