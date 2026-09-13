"""Experiment 6: learning curves for B1 (mass), TA_RIDGE (Tier A) and MORGAN ridge.

Within every outer fold, a fraction p of the training structural groups
(scaffold groups for PRIMARY, strict clusters for STRICT, compounds for
RANDOM) is drawn at seeds 0-2; the full nested pipeline (collapse, inner
selection) runs on that subsample and predicts the whole outer test fold.
"""
import json, os, sys, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, engine as EN, metrics as M, ledger as LG

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp06"
FRACS = (0.25, 0.5, 0.75, 1.0); SEEDS = (0, 1, 2)
d = RU.load_data()
models = {"B1_MASS": MO.MassIsotonic, "TA_RIDGE": lambda: MO.RidgeModel("TIER_A", model_id="TA_RIDGE"),
          "MORGAN_RIDGE": lambda: MO.RidgeModel("MORGAN", alphas=MO.RIDGE_ALPHAS_FP, model_id="MORGAN_RIDGE")}
rows = []
path = OUT / "learning_curves.csv"
done = set()
if path.exists():
    old = pd.read_csv(path); rows = old.to_dict("records"); done = {(r["partition"], r["model"], r["frac"], r["seed"]) for r in rows}
for part in ("PRIMARY", "STRICT", "RANDOM"):
    a = RU.assignment(part); gcol = RU.GROUP_COL[part]
    for mname, make in models.items():
        for frac in FRACS:
            for seed in (SEEDS if frac < 1 else (0,)):
                if (part, mname, frac, seed) in done:
                    continue
                t0 = time.time(); preds = []; ntrain = []
                for f in range(5):
                    test = np.array(sorted(a.index[a == f])); train = np.array(sorted(a.index[a != f]))
                    if frac < 1:
                        groups = d.cov.loc[train, gcol]; ug = np.array(sorted(groups.unique()))
                        rng = np.random.default_rng(1000 * seed + f + int(frac * 100))
                        keep = set(rng.choice(ug, size=max(8, int(round(frac * len(ug)))), replace=False))
                        train = train[groups.isin(keep).to_numpy()]
                    ntrain.append(len(train))
                    r = EN.run_fold(make(), d, train, test, gcol, f)
                    preds.append(pd.DataFrame(r.pred, index=r.test_keys, columns=EN.POOLED_ENERGIES))
                P = pd.concat(preds).loc[d.cov.index]
                s = M.summary(P.to_numpy(), d.Y.to_numpy())
                rows.append({"partition": part, "model": mname, "frac": frac, "seed": seed, "mean_n_train": float(np.mean(ntrain)),
                             "P1": s["P1"], "MRMSE": s["MRMSE"], "AF": s["AF"], "seconds": time.time() - t0})
                pd.DataFrame(rows).to_csv(path, index=False)
                print(part, mname, frac, seed, round(s["P1"], 4), round(time.time() - t0, 1), flush=True)
df = pd.DataFrame(rows)
summ = df.groupby(["partition", "model", "frac"]).agg(P1_mean=("P1", "mean"), P1_sd=("P1", "std"), n_train=("mean_n_train", "mean"), AF=("AF", "mean")).reset_index()
summ.to_csv(OUT / "learning_curves_summary.csv", index=False)
print(summ.round(4).to_string())
slopes = {}
for (part, m), g in summ.groupby(["partition", "model"]):
    g = g.set_index("frac")
    slopes[f"{part}|{m}"] = {"P1_25": g.loc[0.25, "P1_mean"], "P1_50": g.loc[0.5, "P1_mean"], "P1_75": g.loc[0.75, "P1_mean"], "P1_100": g.loc[1.0, "P1_mean"],
                             "rel_gain_50_to_100": (g.loc[0.5, "P1_mean"] - g.loc[1.0, "P1_mean"]) / g.loc[0.5, "P1_mean"],
                             "rel_gain_75_to_100": (g.loc[0.75, "P1_mean"] - g.loc[1.0, "P1_mean"]) / g.loc[0.75, "P1_mean"]}
(OUT / "exp06_results.json").write_text(json.dumps({"slopes": slopes, "summary": summ.to_dict("records")}, indent=1, default=float) + "\n")
print(json.dumps(slopes, indent=1, default=lambda o: round(float(o), 4)))
