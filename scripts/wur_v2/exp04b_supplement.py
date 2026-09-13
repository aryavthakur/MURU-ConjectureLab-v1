"""EXP04 supplement: variance of the out-of-fold error explained by (s, d) beyond total mu, per source and rung.
Mechanically dominated by total mu (statistical review S-03); not mechanistic evidence."""
import json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
t = pd.read_parquet(ROOT / "artifacts/wur_v2/exp04/cells.parquet")
rows = []
for (src, e), g in t[t.d.notna()].groupby(["source", "E_native"]):
    y = g.e.to_numpy()
    def r2(X):
        X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
        return 1 - ((y - X @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    rows.append({"source": src, "E": e, "R2_mu": r2(g.mu), "R2_s_d": r2(np.column_stack([g.s, g.d])),
                 "R2_mu_s_d": r2(np.column_stack([g.mu, g.s, g.d])), "gain_s_d_beyond_mu": r2(np.column_stack([g.mu, g.s, g.d])) - r2(g.mu)})
json.dump(rows, open(ROOT / "artifacts/wur_v2/exp04/supplement_beyond_total_mu.json", "w"), indent=1)
print(pd.DataFrame(rows).round(3).to_string())
