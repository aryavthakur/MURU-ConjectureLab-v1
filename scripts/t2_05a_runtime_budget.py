"""Runtime budget and determinism check for the Phase 2 baseline ladder.

Answers, before the expensive job is launched (BACKLOG I4):

  1. does capping thread counts change the FITTED RESULT?  (it must not)
  2. what does one representative expensive fit cost at each thread setting?
  3. what does one complete inner-CV unit cost?
  4. how many fits does the full ladder imply, and what is the projected wall
     time and peak memory?

Nothing here touches the pre-registered experiment. It measures cost and
verifies that the execution changes are inert.
"""
from __future__ import annotations

import os

# Thread caps must be set before numpy / sklearn import to take effect.
THREADS = os.environ.get("MURU_THREADS", "1")
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
          "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = THREADS

import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import resource  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.models import FlexibleBenchmark, MassFlex, Spec, TierAModel  # noqa: E402
from muru.molecules import TIER_A  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
MIN_BIT_COUNT = 5

d = pd.read_parquet(ART / "p2_splits.parquet")
tA = pd.read_parquet(ART / "p2_tierA.parquet").drop(columns=["precursor_mz"])
tB = pd.read_parquet(ART / "p2_tierB.parquet")
fp = [c for c in tB.columns if c.startswith("fp_")]
on = tB[fp].sum(axis=0)
TIER_B_FEATS = ([c for c in fp if on[c] >= MIN_BIT_COUNT]
                + [c for c in tB.columns if c.startswith("rdk_")])
df = d.merge(tA, on="group_key").merge(tB[["group_key", *TIER_B_FEATS]],
                                       on="group_key")

tr = df[df.fold_S2 != 0]
te = df[df.fold_S2 == 0]

# The most expensive grid point in the frozen grid.
WORST = {"max_depth": None, "learning_rate": 0.05, "max_iter": 500,
         "min_samples_leaf": 20, "l2_regularization": 0.0}
CHEAP = {"max_depth": 3, "learning_rate": 0.1, "max_iter": 200,
         "min_samples_leaf": 20, "l2_regularization": 0.0}

out: dict = {"threads_env": THREADS, "n_features": len(TIER_B_FEATS),
             "train_rows": int(len(tr)), "test_rows": int(len(te))}

t0 = time.perf_counter()
m = FlexibleBenchmark(**WORST).fit(tr, TIER_B_FEATS)
pred_worst = m.predict(te)
out["worst_fit_seconds"] = round(time.perf_counter() - t0, 3)

t0 = time.perf_counter()
m2 = FlexibleBenchmark(**CHEAP).fit(tr, TIER_B_FEATS)
out["cheap_fit_seconds"] = round(time.perf_counter() - t0, 3)

# One complete inner-CV unit: 12 grid points on one inner training split.
from muru.splits import grouped_folds  # noqa: E402

inner = grouped_folds(tr["scaffold_group"], n_folds=4, seed=20260811)
i_tr, i_te = tr[inner != 0], tr[inner == 0]
GRID = [{"max_depth": md, "learning_rate": lr, "max_iter": mi,
         "min_samples_leaf": 20, "l2_regularization": 0.0}
        for md in (3, 6, None) for lr in (0.05, 0.1) for mi in (200, 500)]
t0 = time.perf_counter()
for hp in GRID:
    FlexibleBenchmark(**hp).fit(i_tr, TIER_B_FEATS).predict(i_te)
out["one_inner_fold_full_grid_seconds"] = round(time.perf_counter() - t0, 3)
out["grid_points"] = len(GRID)

# Cheap models, for completeness
t0 = time.perf_counter()
MassFlex(alpha=1.0).fit(tr)
out["massflex_fit_seconds"] = round(time.perf_counter() - t0, 4)
t0 = time.perf_counter()
mm = TierAModel(alpha=1.0).fit(tr, list(TIER_A))
mm.feats_ = list(TIER_A)
out["tiera_fit_seconds"] = round(time.perf_counter() - t0, 4)

out["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                           / (1024 * 1024), 1)

np.save(f"/tmp/claude-502/pred_worst_{THREADS}.npy", pred_worst)
print(json.dumps(out, indent=2))
