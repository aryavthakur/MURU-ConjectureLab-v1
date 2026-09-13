"""Experiment 7 preparation: build and audit the ION_ENV block on exposed structures (no outcomes)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import ion_env as IE, models as MO
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp07"
cov = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv").set_index("group_key")
blk = IE.table(cov.smiles)
keep, rep = IE.prune(blk, MO.tier_a_scaled(cov))
rng = np.random.default_rng(7)
audit = {"n": len(blk), "features": {}}
for c in blk.columns:
    nz = blk.index[blk[c] > 0]
    ex = list(cov.loc[rng.choice(nz, size=min(6, len(nz)), replace=False), "smiles"]) if len(nz) else []
    audit["features"][c] = {"prevalence_nonzero": float((blk[c] > 0).mean()), "mean": float(blk[c].mean()), "max": float(blk[c].max()),
                            "pruning": rep.get(c, ""), "examples": ex}
audit["kept"] = keep
audit["corr_with_tier_a_max_abs"] = {c: float(max(abs(np.corrcoef(blk[c], MO.tier_a_scaled(cov)[t])[0, 1]) for t in MO.tier_a_scaled(cov).columns)) for c in keep}
blk.to_csv(OUT / "ion_env_block.csv")
(OUT / "ion_env_audit.json").write_text(json.dumps(audit, indent=1) + "\n")
for c, v in audit["features"].items():
    print(c, round(v["prevalence_nonzero"], 3), v["pruning"]); [print("    ", e) for e in v["examples"][:4]]
print("kept", keep); print(audit["corr_with_tier_a_max_abs"])
