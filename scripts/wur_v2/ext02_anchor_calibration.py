"""External step 2: anchor calibration under the ANCHOR_CALIBRATION guard (anchor spectra only)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import external_multims2 as E
from muru.wur_v2.external_guard import AccessGuard
ROOT = Path(__file__).resolve().parents[2]; OUT = E.OUT
FREEZE = ROOT / "MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md"
P = json.loads((OUT / "populations.json").read_text())
pop = pd.DataFrame(P["populations"]["ANCHOR"])
sp = pd.DataFrame(P["spectra"]["ANCHOR"])
allowed = {tuple(x) for x in P["allowed_spectra"]["ANCHOR"]}
guard = AccessGuard("ANCHOR_CALIBRATION", OUT / "anchor_calibration_access.json", FREEZE, allowed)
mu, info = E.measured_mu(sp, pop, guard)
models = E.load_models()
res = {"access": guard.record, "decode_info": info, "n_anchor_cells": int(len(mu))}
a1 = E.fit_adapter(mu, pop, models["CANDIDATE"], gammas=(1.0,))
g1 = E.gate(a1["cells"])
res["A1"] = {"k": a1["k"], "gamma": 1.0, "sse": a1["sse"], "gate": g1}
chosen = None
if g1["passes"]:
    chosen = ("A1", a1)
else:
    a2 = E.fit_adapter(mu, pop, models["CANDIDATE"], gammas=tuple(E.GAMMA_GRID))
    g2 = E.gate(a2["cells"])
    res["A2"] = {"k": a2["k"], "gamma": a2["gamma"], "sse": a2["sse"], "gate": g2}
    if g2["passes"]:
        chosen = ("A2", a2)
res["qualified"] = chosen is not None
if chosen:
    name, fit = chosen
    res["adapter"] = {"family": name, "k": fit["k"], "gamma": fit["gamma"]}
    # anchor-cluster bootstrap of the adapter (scaffold groups of anchors)
    rng = np.random.default_rng(20261002)
    groups = pop.set_index("key").scaffold_group
    ug = groups.unique(); ks = []
    rows_by_group = {g: mu[mu.key.isin(groups.index[groups == g])] for g in ug}
    for b in range(2000):
        pick = rng.choice(ug, size=len(ug), replace=True)
        sub = pd.concat([rows_by_group[g] for g in pick], ignore_index=True)
        fb = E.fit_adapter(sub, pop.drop_duplicates("key"), models["CANDIDATE"], gammas=(fit["gamma"],))
        ks.append(fb["k"])
    res["adapter"]["k_bootstrap_2.5_97.5"] = np.percentile(ks, [2.5, 97.5]).tolist()
    fit["cells"].to_csv(OUT / "anchor_cells.csv", index=False)
(OUT / "anchor_calibration.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "access"}, indent=1, default=float))
