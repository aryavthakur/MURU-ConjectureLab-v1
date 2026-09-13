"""Compute and cache structure-only representations and kernels."""
import time, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2.engine import Data
from muru.wur_v2 import representations as R
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/wur_v2/data/representations"; OUT.mkdir(parents=True, exist_ok=True)
t = time.time()
d = Data.load(ROOT)
feats, kernels = R.build_all(d.cov)
for k, v in feats.items():
    v.to_parquet(OUT / f"{k}.parquet")
    print(k, v.shape, hashlib.sha256(np.ascontiguousarray(v.to_numpy()).tobytes()).hexdigest()[:16])
for k, (idx, K) in kernels.items():
    np.save(OUT / f"{k}.npy", K)
    print(k, K.shape, hashlib.sha256(K.tobytes()).hexdigest()[:16])
print("seconds", round(time.time() - t, 1))
