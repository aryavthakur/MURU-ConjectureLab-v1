"""Experiment 10: trust / error prediction for the leading point model (TA_MORGAN_JOINT).

Test-compound signals are computed against the outer training set; trust-model
training rows are the outer-training compounds' inner cross-fitted errors with
signals computed against their inner training sets. Nothing from a held-out
compound's spectra enters a signal.
"""
import json, os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from pathlib import Path
import numpy as np, pandas as pd
from muru.wur_v2 import runner as RU, models as MO, engine as EN, folds as FO, metrics as M, trust as TR, ledger as LG

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp10"
d = RU.load_data()
E = EN.POOLED_ENERGIES; ECOL = [str(e) for e in E]
rng = np.random.default_rng(20260927)
results = {}
for part in ("PRIMARY", "STRICT"):
    a = RU.assignment(part); gcol = RU.GROUP_COL[part]
    P = RU.run(MO.JointRidge("MORGAN", "TA_MORGAN_JOINT"), d, part)
    T = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, part)
    test_rows, train_models = [], {}
    for f in range(5):
        tr = np.array(sorted(a.index[a != f])); te = np.array(sorted(a.index[a == f]))
        fitT = EN.collapse_for(d, tr)
        sig_te = TR.signals(d, fitT.compounds, te, T.log_g_pred.loc[te].to_numpy(), P.log_g_pred.loc[te].to_numpy(), fitT)
        # training rows from inner cross-fitting
        keys = fitT.compounds
        inner = FO.inner_folds(d.cov.loc[keys].reset_index(), gcol, f)
        Pin = P.inner_oof[P.inner_oof.outer_fold == f]; Tin = T.inner_oof[T.inner_oof.outer_fold == f]
        rows = []
        for k in range(FO.INNER_K):
            trk, vak = keys[inner != k], keys[inner == k]
            fk = EN.collapse_for(d, trk)
            s = TR.signals(d, fk.compounds, vak, Tin.loc[vak, "log_g_pred"].to_numpy(), Pin.loc[vak, "log_g_pred"].to_numpy(), fk)
            s["rmse"] = M.compound_rmse(M.errors(Pin.loc[vak, ECOL].to_numpy(), d.Y.loc[vak].to_numpy()))
            rows.append(s)
        trn = pd.concat(rows)
        lt = TR.LearnedTrust().fit(trn[list(TR.SIGNALS)], trn["rmse"].to_numpy())
        pr = lt.predict(sig_te)
        thr = {"learned_q80": float(np.quantile(lt.predict(trn[list(TR.SIGNALS)])["pred_log_rmse"], 0.8)),
               "learned_q90": float(np.quantile(lt.predict(trn[list(TR.SIGNALS)])["pred_log_rmse"], 0.9)),
               "dist_q80": float(np.quantile(trn["dist_1_minus_maxsim"], 0.8)), "dist_q90": float(np.quantile(trn["dist_1_minus_maxsim"], 0.9))}
        te_df = pd.concat([sig_te, pr], axis=1).assign(fold=f, **{f"thr_{k}": v for k, v in thr.items()})
        test_rows.append(te_df)
        train_models[f] = {"coef_log_rmse": dict(zip(TR.SIGNALS, lt.reg.coef_.round(4).tolist())),
                           "coef_af": dict(zip(TR.SIGNALS, lt.clf.coef_[0].round(4).tolist())) if lt.clf is not None else None,
                           "n_train_rows": int(len(trn)), "train_af_rate": float((trn.rmse > M.AF_RMSE).mean())}
    te = pd.concat(test_rows).loc[d.cov.index]
    Yv = d.Y.loc[te.index].to_numpy(); pv = P.pred.loc[te.index].to_numpy()
    rmse = M.compound_rmse(M.errors(pv, Yv)); af = (rmse > M.AF_RMSE).astype(int)
    te["rmse"] = rmse; te["af"] = af
    te.to_csv(OUT / f"trust_table_{part}.csv")
    rankers = {"learned_log_rmse": te.pred_log_rmse.to_numpy(), "learned_p_af": te.p_af.to_numpy(),
               **{s: te[s].to_numpy() for s in TR.SIGNALS if s != "domain_flag"},
               "domain_flag_then_distance": te.domain_flag.to_numpy() * 10 + te.dist_1_minus_maxsim.to_numpy()}
    full = M.summary(pv, Yv)
    res = {"n": len(te), "full_population": {k: full[k] for k in ("P1", "MRMSE", "AF", "AF_max")}, "af_prevalence": float(af.mean()),
           "rankers": {}, "fold_models": train_models}
    from scipy.stats import spearmanr
    for name, sc in rankers.items():
        res["rankers"][name] = {"spearman_with_rmse": float(spearmanr(sc, rmse).statistic), "af_pr_auc": TR.pr_auc(sc, af),
                                "selective": TR.selective(pv, Yv, sc)}
    res["random_rejection_expected"] = {"AF": float(af.mean()), "P1": full["P1"], "af_pr_auc": float(af.mean())}
    res["calibration_learned_p_af"] = TR.calibration(te.p_af.to_numpy(), af)
    # frozen-threshold (training-quantile) selection
    for q in ("80", "90"):
        keep_l = te.pred_log_rmse <= te[f"thr_learned_q{q}"]; keep_d = te.dist_1_minus_maxsim <= te[f"thr_dist_q{q}"]
        res[f"threshold_q{q}"] = {"learned": {"coverage": float(keep_l.mean()), "AF": float(te.af[keep_l].mean()), **{k: v for k, v in M.summary(pv[keep_l.to_numpy()], Yv[keep_l.to_numpy()]).items() if k in ("P1", "MRMSE")}},
                                  "distance": {"coverage": float(keep_d.mean()), "AF": float(te.af[keep_d].mean()), **{k: v for k, v in M.summary(pv[keep_d.to_numpy()], Yv[keep_d.to_numpy()]).items() if k in ("P1", "MRMSE")}}}
    # bootstrap of retained-AF reduction, learned vs distance-only, ranking-based, membership fixed
    groups = d.cov.loc[te.index, "scaffold_group"].to_numpy(); uniq, codes = np.unique(groups.astype(str), return_inverse=True); G = len(uniq)
    boot = {}
    for c in (0.9, 0.8, 0.7):
        n_keep = int(round(c * len(te)))
        kl = np.zeros(len(te), bool); kl[np.argsort(te.pred_log_rmse.to_numpy(), kind="stable")[:n_keep]] = True
        kd = np.zeros(len(te), bool); kd[np.argsort(te.dist_1_minus_maxsim.to_numpy(), kind="stable")[:n_keep]] = True
        W = rng.multinomial(G, np.full(G, 1 / G), size=2000)
        al = (W @ np.bincount(codes, af * kl, G)) / np.maximum(W @ np.bincount(codes, kl.astype(float), G), 1)
        ad = (W @ np.bincount(codes, af * kd, G)) / np.maximum(W @ np.bincount(codes, kd.astype(float), G), 1)
        rel = 1 - al / np.maximum(ad, 1e-9)
        boot[str(c)] = {"AF_learned": float(af[kl].mean()), "AF_distance": float(af[kd].mean()),
                        "relative_reduction": float(1 - af[kl].mean() / max(af[kd].mean(), 1e-9)),
                        "relative_reduction_ci95": np.percentile(rel, [2.5, 97.5]).tolist(),
                        "AF_random": float(af.mean())}
    res["learned_vs_distance_bootstrap"] = boot
    results[part] = res
    print(part, "AF prevalence %.3f" % af.mean(), {k: (round(v["spearman_with_rmse"], 3), round(v["af_pr_auc"], 3), round(v["selective"]["0.8"]["AF"], 3)) for k, v in res["rankers"].items()})
    print("  boot", json.dumps(boot, default=lambda o: round(float(o), 3)))
    print("  thresholds", json.dumps({q: res[f"threshold_q{q}"] for q in ("80", "90")}, default=lambda o: round(float(o), 3)))
    print("  calibration", json.dumps(res["calibration_learned_p_af"], default=lambda o: round(float(o), 3)))
# source strata for PRIMARY ranking (learned) at 80 percent coverage within stratum
te = pd.read_csv(OUT / "trust_table_PRIMARY.csv").set_index("group_key") if "group_key" in pd.read_csv(OUT / "trust_table_PRIMARY.csv", nrows=1).columns else pd.read_csv(OUT / "trust_table_PRIMARY.csv", index_col=0)
strat = {}
for src in ("LCSB", "WUR"):
    ks = te.index[d.cov.loc[te.index, "primary_source"] == src]
    sub = te.loc[ks]; n_keep = int(round(0.8 * len(sub)))
    kl = sub.pred_log_rmse.sort_values(kind="stable").index[:n_keep]; kd = sub.dist_1_minus_maxsim.sort_values(kind="stable").index[:n_keep]
    strat[src] = {"n": len(sub), "AF_all": float(sub.af.mean()), "AF_learned_80": float(sub.loc[kl, "af"].mean()), "AF_distance_80": float(sub.loc[kd, "af"].mean())}
results["PRIMARY"]["source_strata_80"] = strat
(OUT / "exp10_results.json").write_text(json.dumps(results, indent=1, default=float) + "\n")
print(json.dumps(strat, indent=1))
