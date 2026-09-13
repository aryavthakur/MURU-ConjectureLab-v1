"""Experiment 2: empirical repeatability and scale identifiability.

Repeat structures: (R1) LCSB raw inter-preparation duplicates, mixes 499 and
503 (30 non-confirmation compounds, full rungs 30-90); (R2) the 124 compounds
measured on both instruments (LCSB vs WUR read at the frozen map); (R3) WUR
isomer acquisitions under one connectivity key (diagnostic, not repeats).
Every scale fit uses the PRIMARY-fold profile trained without the compound.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, engine as EN, scale as SC, metrics as M, ledger as LG
from muru.wur_v2.exposure import lcsb_confirmation_keys
from muru.wur_bridge import apply_energy_map

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp02"
E = EN.POOLED_ENERGIES
d = RU.load_data(False)
a = RU.assignment("PRIMARY")
fits = {f: EN.collapse_for(d, sorted(a.index[a != f])) for f in range(5)}
ta = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")

def fold_fit(key):
    return fits[int(a.loc[key])]

def icc(x, y):
    """One-way random-effects ICC(1,1) for paired measurements."""
    X = np.column_stack([x, y]); n = len(X)
    gm = X.mean(); msb = 2 * ((X.mean(1) - gm) ** 2).sum() / (n - 1); msw = ((X - X.mean(1, keepdims=True)) ** 2).sum() / n
    return float((msb - msw) / (msb + msw)), float(np.sqrt(msw))

def scale_block(keys, YA, YB):
    """Fit log g on A and on B with each compound's out-of-fold profile; A->B prediction."""
    lgA, lgB, predAB, predBB, oracleB = [], [], [], [], []
    for i, k in enumerate(keys):
        f = fold_fit(k)
        ga = SC.fit_scale(f, E, YA[i:i + 1])[0]; gb = SC.fit_scale(f, E, YB[i:i + 1])[0]
        lgA.append(ga); lgB.append(gb)
        predAB.append(EN.mu_from_log_g(f, np.array([ga]))[0]); oracleB.append(EN.mu_from_log_g(f, np.array([gb]))[0])
    lgA, lgB = np.array(lgA), np.array(lgB)
    r_icc, sd_w = icc(lgA, lgB)
    return {"n": len(keys), "logg_icc": r_icc, "logg_within_sd": sd_w, "logg_sd_of_difference": float(np.std(lgA - lgB, ddof=1)),
            "logg_between_sd": float(np.std((lgA + lgB) / 2, ddof=1)), "mean_difference_A_minus_B": float(np.mean(lgA - lgB)),
            "trajectory_P1_repeat_A_to_B": M.p1(M.errors(np.array(predAB), YB)),
            "trajectory_P1_oracle_B_on_B": M.p1(M.errors(np.array(oracleB), YB)),
            "mu_rmsd_A_vs_B_direct": M.p1(M.errors(YA, YB)), "_lgA": lgA, "_lgB": lgB}

res = {}
# ---------- R1: LCSB raw inter-preparation duplicates ----------
conf = lcsb_confirmation_keys()
raw = pd.read_parquet(ROOT / "artifacts/raw_branch_merged.parquet")
raw = raw[~raw.inchikey_first_block.isin(conf) & raw.ce_numeric.isin(E)]
W = raw.pivot_table(index="inchikey_first_block", columns=["mix", "ce_numeric"], values="mu")
keys = [k for k in W.index if k in d.cov.index and W.loc[k, 499].notna().all() and W.loc[k, 503].notna().all()]
YA, YB = W.loc[keys, 499][E].to_numpy(), W.loc[keys, 503][E].to_numpy()
r1 = scale_block(keys, YA, YB)
# ICC of mu per rung
r1["mu_icc_per_rung"] = {str(e): icc(YA[:, j], YB[:, j])[0] for j, e in enumerate(E)}
r1["mu_within_sd_per_rung"] = {str(e): icc(YA[:, j], YB[:, j])[1] for j, e in enumerate(E)}
Yc = d.Y.loc[keys].to_numpy()
r1["ta_ridge_oof_P1_same_compounds"] = M.p1(M.errors(ta.pred.loc[keys].to_numpy(), Yc))
r1["curated_vs_raw_mu_rmsd"] = M.p1(M.errors(Yc, (YA + YB) / 2))
# curvature-based variance for the same compounds (what v1 called reliability), vs empirical
fit_pop = EN.collapse_for(d, list(d.cov.index))
gvar = pd.Series(fit_pop.g_var, index=fit_pop.compounds)
r1["curvature_logg_sd_median_same_compounds"] = float(np.sqrt(gvar.loc[keys].median()))
res["R1_LCSB_inter_preparation"] = r1

# ---------- R2: cross-instrument pairs ----------
both = d.cov.index[d.cov.measured_lcsb & d.cov.measured_wur]
walign = pd.read_csv(ROOT / "artifacts/wur_v2/data/wur_aligned_all.csv")
WW = walign.pivot(index="group_key", columns="ce_numeric", values="mu").reindex(index=both, columns=E)
YL, YW = d.Y.loc[both].to_numpy(), WW.to_numpy()
ok = np.isfinite(YL).sum(1) >= 4
r2 = scale_block(list(both[ok]), YL[ok], YW[ok])
r2["ta_ridge_oof_P1_same_compounds_on_LCSB_copy"] = M.p1(M.errors(ta.pred.loc[both[ok]].to_numpy(), YL[ok]))
r2["ta_ridge_oof_P1_same_compounds_on_WUR_copy"] = M.p1(M.errors(ta.pred.loc[both[ok]].to_numpy(), YW[ok]))
r2["note"] = "the frozen map was fitted on these 124 compounds (population B); cross-instrument agreement is optimistic by construction"
res["R2_cross_instrument"] = r2

# ---------- R3: WUR isomer acquisitions ----------
spec = pd.read_parquet(ROOT / "artifacts/wur_v2/data/wur_pos_spectra.parquet")
from muru.wur_v2.spectra import acquisition_id
spec["acq"] = acquisition_id(spec)
distinct = spec.drop_duplicates(["connectivity_key", "ce_numeric", "acq"])
multi = distinct.groupby("connectivity_key").smiles.nunique(); multi = multi[multi > 1].index
iso_rows = []
bridge = RU.json.loads((ROOT / "artifacts/wur_bridge_gate.json").read_text())["alignment"] if hasattr(RU, "json") else json.loads((ROOT / "artifacts/wur_bridge_gate.json").read_text())["alignment"]
for k in multi:
    g = distinct[distinct.connectivity_key == k]
    for smi, gg in g.groupby("smiles"):
        if set(gg.ce_numeric) != {15., 30., 45., 60., 75., 90.}:
            continue
        cells = gg.groupby("ce_numeric").mu.median().reset_index().assign(connectivity_key=k)
        mapped, _ = apply_energy_map(cells, bridge["a"], bridge["b"])
        y = mapped.set_index("ce_numeric").mu.reindex(E).to_numpy()
        f = fold_fit(k) if k in a.index else fit_pop
        iso_rows.append({"key": k, "smiles": smi, "log_g": float(SC.fit_scale(f, E, y[None, :])[0]), **{str(e): v for e, v in zip(E, y)}})
iso = pd.DataFrame(iso_rows)
sp = iso.groupby("key").agg(n=("smiles", "size"), logg_sd=("log_g", "std"), **{f"mu_sd_{e}": (str(e), "std") for e in E})
res["R3_wur_isomer_groups"] = {"n_keys": int(len(sp)), "n_isomer_trajectories": int(len(iso)),
                               "logg_within_key_sd_pooled": float(np.sqrt((sp.logg_sd ** 2).mean())),
                               "mu_within_key_sd_pooled_per_rung": {str(e): float(np.sqrt((sp[f'mu_sd_{e}'] ** 2).mean())) for e in E},
                               "note": "stereoisomers/E-Z isomers acquired separately; spread includes real stereo effects, so this is not repeatability"}

# ---------- identifiability across the population (out-of-fold profiles) ----------
sigma = float(r1["logg_within_sd"]) if False else 0.0295       # mu repeatability scale (inter-mixture, REPEATABILITY.md)
rows = []
for f in range(5):
    ks = sorted(a.index[a == f]); Y = d.Y.loc[ks].to_numpy()
    idf = SC.identifiability(fits[f], E, Y, sigma)
    for i, k in enumerate(ks):
        rows.append({"group_key": k, **{kk: (v[i] if hasattr(v, "__len__") else v) for kk, v in idf.items()}})
ident = pd.DataFrame(rows).set_index("group_key")
err = pd.Series(M.compound_rmse(M.errors(ta.pred.loc[ident.index].to_numpy(), d.Y.loc[ident.index].to_numpy())), index=ident.index)
ident["ta_oof_rmse"] = err
ident["ta_logg_error"] = ta.log_g_pred.loc[ident.index] - ident["log_g"]
ident["precursor_mz"] = d.cov.loc[ident.index, "precursor_mz"]
ident["weak"] = ident.interval_width > 0.5
ident.to_csv(OUT / "identifiability_primary_oof.csv")
cv = ident["precursor_mz"]
res["identifiability"] = {"sigma_used": sigma, "delta_rule": "SSE <= min + chi2_1(0.95) sigma^2",
    "n": int(len(ident)), "boundary_low": int(ident.boundary_low.sum()), "boundary_high": int(ident.boundary_high.sum()),
    "interval_width_quantiles": ident.interval_width.quantile([.1, .25, .5, .75, .9]).round(3).tolist(),
    "frac_weak_width_gt_0.5": float(ident.weak.mean()), "frac_interval_touches_edge": float(ident.interval_touches_edge.mean()),
    "median_mz_boundary": float(cv[ident.boundary_low | ident.boundary_high].median()) if (ident.boundary_low | ident.boundary_high).any() else None,
    "median_mz_all": float(cv.median()),
    "ta_oof_P1_weak": M.p1(M.errors(ta.pred.loc[ident.index[ident.weak]].to_numpy(), d.Y.loc[ident.index[ident.weak]].to_numpy())),
    "ta_oof_P1_identified": M.p1(M.errors(ta.pred.loc[ident.index[~ident.weak]].to_numpy(), d.Y.loc[ident.index[~ident.weak]].to_numpy())),
    "ta_oof_AF_weak": float((ident.loc[ident.weak, "ta_oof_rmse"] > 0.2).mean()), "ta_oof_AF_identified": float((ident.loc[~ident.weak, "ta_oof_rmse"] > 0.2).mean()),
    "var_logg_label": float(ident.log_g.var()), "var_ta_logg_error": float(ident.ta_logg_error.var()),
    "var_ta_logg_error_identified_only": float(ident.loc[~ident.weak & ~ident.interval_touches_edge, "ta_logg_error"].var())}
# variance budget: empirical repeat variance of log g vs residual variance beyond Tier A
res["variance_budget"] = {
    "var_logg_within_repeat_R1": r1["logg_within_sd"] ** 2, "var_logg_within_crossinstrument_R2": r2["logg_within_sd"] ** 2,
    "var_ta_logg_error": res["identifiability"]["var_ta_logg_error"],
    "share_of_ta_error_variance_explained_by_R1_repeat_noise": r1["logg_sd_of_difference"] ** 2 / 2 / res["identifiability"]["var_ta_logg_error"],
    "share_by_R2_cross_instrument": r2["logg_sd_of_difference"] ** 2 / 2 / res["identifiability"]["var_ta_logg_error"],
    "note": "within-compound variance of a single measurement's log g = SD(A-B)^2/2"}
for blk in ("R1_LCSB_inter_preparation", "R2_cross_instrument"):
    for kk in ("_lgA", "_lgB"):
        res[blk].pop(kk)
(OUT / "exp02_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps(res, indent=1, default=lambda o: round(float(o), 4)))
