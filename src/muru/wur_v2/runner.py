"""Cached out-of-fold runs and standard comparisons for v2 experiments."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from muru.wur_v2 import engine as EN
from muru.wur_v2 import metrics as M
from muru.wur_v2.models import b0_predictions

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "artifacts/wur_v2/data"
RUNS = ROOT / "artifacts/wur_v2/runs"
GROUP_COL = {"PRIMARY": "scaffold_group", "PARTITION_S1": "scaffold_group", "PARTITION_S2": "scaffold_group",
             "GIANT": "scaffold_group", "STRICT": "strict_cluster", "RANDOM": "compound_group"}
TEST_FOLDS = {"GIANT": [0]}
BENZENE = "c1ccccc1"


def load_data(with_representations: bool = True) -> EN.Data:
    d = EN.Data.load(ROOT)
    d.cov["compound_group"] = d.cov.index
    if with_representations:
        rep = DATA / "representations"
        for p in rep.glob("*.parquet"):
            d.features[p.stem] = pd.read_parquet(p).loc[d.cov.index]
        for p in rep.glob("*.npy"):
            d.kernels[p.stem] = (d.cov.index, np.load(p))
    return d


def folds() -> dict:
    return json.loads((ROOT / "artifacts/wur_v2/folds.json").read_text())


def assignment(name: str) -> pd.Series:
    return pd.Series(folds()["partitions"][name]["assignment"])


def run(model: EN.ScaleModel, data: EN.Data, partition: str, keys_subset=None, tag: str = "",
        use_cache: bool = True) -> EN.CVRun:
    a = assignment(partition)
    sha = folds()["partitions"][partition]["assignment_sha256"][:12]
    path = RUNS / partition / f"{model.id}{tag}__{sha}.parquet"
    meta_path = path.with_suffix(".json")
    if use_cache and path.exists() and keys_subset is None:
        pred = pd.read_parquet(path)
        meta = json.loads(meta_path.read_text())
        return EN.CVRun(model_id=model.id, partition=partition, pred=pred[list(EN.POOLED_ENERGIES.astype(str))].set_axis(EN.POOLED_ENERGIES, axis=1),
                        log_g_pred=pred["log_g_pred"], fold_of=pred["fold"], cfgs=meta["cfgs"],
                        inner_oof=pd.read_parquet(path.with_suffix(".inner.parquet")) if path.with_suffix(".inner.parquet").exists() else pd.DataFrame(),
                        seconds=meta["seconds"])
    test_folds = TEST_FOLDS.get(partition)
    if test_folds is not None:
        r = _run_selected_folds(model, data, a, partition, test_folds)
    else:
        r = EN.run_cv(model, data, a, partition, GROUP_COL[partition], keys_subset=keys_subset)
    if keys_subset is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        out = r.pred.copy(); out.columns = [str(c) for c in out.columns]
        out["log_g_pred"] = r.log_g_pred; out["fold"] = r.fold_of
        out.to_parquet(path)
        if len(r.inner_oof):
            io = r.inner_oof.copy(); io.columns = [str(c) for c in io.columns]
            io.to_parquet(path.with_suffix(".inner.parquet"))
        meta_path.write_text(json.dumps({"model_id": model.id, "partition": partition, "assignment_sha256": sha,
                                         "cfgs": r.cfgs, "seconds": r.seconds,
                                         "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1))
    return r


def _run_selected_folds(model, data, a, partition, test_folds):
    t0 = time.time()
    preds, lgs, cfgs, inner = [], [], {}, []
    for f in test_folds:
        test = np.array(sorted(a.index[a == f])); train = np.array(sorted(a.index[a != f]))
        fr = EN.run_fold(model, data, train, test, GROUP_COL[partition], int(f))
        preds.append(pd.DataFrame(fr.pred, index=fr.test_keys, columns=EN.POOLED_ENERGIES))
        lgs.append(pd.Series(fr.log_g_pred, index=fr.test_keys)); cfgs[int(f)] = str(fr.cfg)
        if len(fr.inner_oof):
            inner.append(fr.inner_oof.assign(outer_fold=int(f)))
    pred = pd.concat(preds).sort_index()
    return EN.CVRun(model_id=model.id, partition=partition, pred=pred, log_g_pred=pd.concat(lgs).sort_index(),
                    fold_of=a.loc[pred.index], cfgs=cfgs, inner_oof=pd.concat(inner) if inner else pd.DataFrame(),
                    seconds=time.time() - t0)


def b0(data: EN.Data, partition: str) -> pd.DataFrame:
    a = assignment(partition)
    if partition in TEST_FOLDS:
        tf = TEST_FOLDS[partition]
        out = []
        for f in tf:
            test = sorted(a.index[a == f]); train = sorted(a.index[a != f])
            m = data.Y.loc[train].mean(0)
            out.append(pd.DataFrame(np.tile(m.to_numpy(), (len(test), 1)), index=test, columns=data.Y.columns))
        return pd.concat(out).sort_index()
    return b0_predictions(data, a)


def compare(data: EN.Data, cand: pd.DataFrame, ref: pd.DataFrame, partition: str, b0pred: pd.DataFrame | None = None,
            boot: bool = True, keys=None) -> dict:
    keys = sorted(set(cand.index) & set(ref.index)) if keys is None else sorted(keys)
    Y = data.Y.loc[keys].to_numpy()
    pc, pr = cand.loc[keys].to_numpy(), ref.loc[keys].to_numpy()
    pb = b0pred.loc[keys].to_numpy() if b0pred is not None else None
    out = {"partition": partition, "n": len(keys), "cand": M.summary(pc, Y, pb), "ref": M.summary(pr, Y, pb),
           "cand_per_rung": M.per_rung(pc, Y, EN.POOLED_ENERGIES)}
    out["P1_ratio"] = out["cand"]["P1"] / out["ref"]["P1"]
    if boot:
        col = GROUP_COL.get(partition, "scaffold_group")
        col = "scaffold_group" if col == "compound_group" else col
        out["bootstrap"] = M.cluster_bootstrap(pc, pr, Y, data.cov.loc[keys, col].to_numpy())
    return out


def strata(data: EN.Data, cand: pd.DataFrame, ref: pd.DataFrame) -> dict:
    cov = data.cov.loc[cand.index]
    groups = {"LCSB_primary": cov.index[cov.primary_source == "LCSB"], "WUR_primary": cov.index[cov.primary_source == "WUR"],
              "non_benzene": cov.index[cov.scaffold_group != BENZENE], "benzene": cov.index[cov.scaffold_group == BENZENE],
              "MH_adduct": cov.index[cov.adduct == "[M+H]+"], "non_MH_adduct": cov.index[cov.adduct != "[M+H]+"],
              "mass_low_tercile": cov.index[cov.precursor_mz <= cov.precursor_mz.quantile(1 / 3)],
              "mass_mid_tercile": cov.index[(cov.precursor_mz > cov.precursor_mz.quantile(1 / 3)) & (cov.precursor_mz <= cov.precursor_mz.quantile(2 / 3))],
              "mass_high_tercile": cov.index[cov.precursor_mz > cov.precursor_mz.quantile(2 / 3)],
              "formerly_sealed": cov.index[cov.historical_class == "WUR-SEALED"]}
    out = {}
    for name, ks in groups.items():
        ks = list(ks)
        if len(ks) < 5:
            continue
        Y = data.Y.loc[ks].to_numpy()
        c, r = M.summary(cand.loc[ks].to_numpy(), Y), M.summary(ref.loc[ks].to_numpy(), Y)
        out[name] = {"n": len(ks), "P1_cand": c["P1"], "P1_ref": r["P1"], "P1_ratio": c["P1"] / r["P1"],
                     "AF_cand": c["AF"], "AF_ref": r["AF"], "MRMSE_cand": c["MRMSE"], "MRMSE_ref": r["MRMSE"]}
    return out
