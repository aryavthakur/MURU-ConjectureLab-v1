"""Experiment 13: attempt to disprove the leading development candidate TA_MORGAN_JOINT.

Pre-stated sensitivity set: compound weighting, per-rung, per-fold, alternative
cluster unit, leverage extremes, novel-chemistry decile, native WUR energies,
source transfer (train on one source, predict the other), historical v1 on the
formerly sealed compounds (descriptive), and the chemical content of the Morgan
coefficients.
"""
import json, os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from ast import literal_eval
from pathlib import Path
import numpy as np, pandas as pd
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from muru.wur_v2 import runner as RU, models as MO, engine as EN, metrics as M, ledger as LG
from muru.wur_v2.population import bridge

ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/exp13"
d = RU.load_data(); E = EN.POOLED_ENERGIES
J = RU.run(MO.JointRidge("MORGAN", "TA_MORGAN_JOINT"), d, "PRIMARY"); T = RU.run(MO.RidgeModel("TIER_A", model_id="TA_RIDGE"), d, "PRIMARY")
a = RU.assignment("PRIMARY"); keys = d.cov.index; Y = d.Y.loc[keys].to_numpy()
pj, pt = J.pred.loc[keys].to_numpy(), T.pred.loc[keys].to_numpy()
res = {}
sj, st = M.summary(pj, Y), M.summary(pt, Y)
res["weighting"] = {"P1_cw_joint": sj["P1_cw"], "P1_cw_TA": st["P1_cw"], "ratio_cw": sj["P1_cw"] / st["P1_cw"], "ratio_cells": sj["P1"] / st["P1"]}
res["per_rung"] = {"joint": M.per_rung(pj, Y, E), "TA": M.per_rung(pt, Y, E)}
res["per_fold"] = {int(f): M.p1(M.errors(pj[(a.loc[keys] == f).to_numpy()], Y[(a.loc[keys] == f).to_numpy()])) / M.p1(M.errors(pt[(a.loc[keys] == f).to_numpy()], Y[(a.loc[keys] == f).to_numpy()])) for f in range(5)}
res["bootstrap_strict_cluster_unit"] = M.cluster_bootstrap(pj, pt, Y, d.cov.loc[keys, "strict_cluster"].to_numpy())
tt = pd.read_csv(ROOT / "artifacts/wur_v2/exp10/trust_table_PRIMARY.csv", index_col=0).loc[keys]
def sub_ratio(mask):
    return {"n": int(mask.sum()), "P1_joint": M.p1(M.errors(pj[mask], Y[mask])), "P1_TA": M.p1(M.errors(pt[mask], Y[mask])),
            "ratio": M.p1(M.errors(pj[mask], Y[mask])) / M.p1(M.errors(pt[mask], Y[mask])),
            "AF_joint": float((M.compound_rmse(M.errors(pj[mask], Y[mask])) > 0.2).mean()), "AF_TA": float((M.compound_rmse(M.errors(pt[mask], Y[mask])) > 0.2).mean())}
res["leverage_top_decile"] = sub_ratio((tt.leverage >= tt.leverage.quantile(0.9)).to_numpy())
res["novel_chemistry_bottom_similarity_decile"] = sub_ratio((tt.dist_1_minus_maxsim >= tt.dist_1_minus_maxsim.quantile(0.9)).to_numpy())
res["max_similarity_below_0.5"] = sub_ratio((tt.dist_1_minus_maxsim > 0.5).to_numpy())
# native WUR energies via the inverse map
A, B = bridge(); nat = pd.read_csv(ROOT / "artifacts/wur_v2/data/native_cells.csv")
wk = keys[d.cov.primary_source == "WUR"]
nw = nat[(nat.source == "WUR") & nat.connectivity_key.isin(wk)].pivot(index="connectivity_key", columns="ce_numeric", values="mu").reindex(index=wk)
fits = {f: EN.collapse_for(d, sorted(a.index[a != f])) for f in range(5)}
NE = np.array([30.0, 45.0, 60.0, 75.0, 90.0])
def native(run):
    return np.vstack([EN.mu_from_log_g(fits[int(a.loc[k])], np.array([run.log_g_pred.loc[k]]), (NE - A) / B)[0] for k in wk])
Yn = nw[NE].to_numpy()
res["native_WUR"] = {"P1_joint": M.p1(M.errors(native(J), Yn)), "P1_TA": M.p1(M.errors(native(T), Yn))}
res["native_WUR"]["ratio"] = res["native_WUR"]["P1_joint"] / res["native_WUR"]["P1_TA"]
# source transfer
cfg_modal = (0.3, 0.1)
class FixedJoint(MO.JointRidge):
    def grid(self):
        return [cfg_modal]
tr_res = {}
for src_train, src_test in (("LCSB", "WUR"), ("WUR", "LCSB")):
    trk = np.array(sorted(keys[d.cov.primary_source == src_train])); tek = np.array(sorted(keys[d.cov.primary_source == src_test]))
    out = {}
    for name, m in (("joint", MO.JointRidge("MORGAN", "TA_MORGAN_JOINT")), ("TA", MO.RidgeModel("TIER_A", model_id="TA_RIDGE"))):
        fr = EN.run_fold(m, d, trk, tek, "scaffold_group", 0)
        out[name] = M.p1(M.errors(fr.pred, d.Y.loc[tek].to_numpy()))
    out["ratio"] = out["joint"] / out["TA"]; out["n_train"], out["n_test"] = len(trk), len(tek)
    out["test_scaffold_groups_seen_in_train"] = float(d.cov.loc[tek, "scaffold_group"].isin(set(d.cov.loc[trk, "scaffold_group"])).mean())
    tr_res[f"train_{src_train}_test_{src_test}"] = out
res["source_transfer"] = tr_res
# historical v1 on formerly sealed (descriptive: different training sets)
npz = np.load(ROOT / "artifacts/wur_v2/exp01/stage3_reproduced_predictions.npz", allow_pickle=True)
sk = list(npz["keys"]); v1 = npz["V1B_RIDGE_TIERA"]; Ys = d.Y.loc[sk].to_numpy()
res["formerly_sealed_descriptive"] = {"n": len(sk), "V1_FROZEN_P1": M.p1(M.errors(v1, Ys)),
    "TA_RIDGE_OOF_P1": M.p1(M.errors(T.pred.loc[sk].to_numpy(), Ys)), "JOINT_OOF_P1": M.p1(M.errors(J.pred.loc[sk].to_numpy(), Ys)),
    "note": "V1_FROZEN trained on 921 DEV2B+HOLD compounds with v1 aggregation; OOF models trained on ~1,060 v2 compounds that include other formerly sealed compounds; the sealed aligned table differs from v2 D-AGG in 10 cells; descriptive only"}
# chemical content of the Morgan block: full-population fit at the modal configuration
fit = EN.collapse_for(d, list(keys)); ts = EN.trainset(d, list(keys), "scaffold_group", 0)
m, stats, bw = MO.JointRidge("MORGAN", "_").fit(ts, cfg_modal)
coef_fp = m.coef_[12:] * bw; Xm = d.features["MORGAN"].loc[ts.keys].to_numpy()
contrib = coef_fp * Xm.std(0)
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
def bit_examples(bit, n=3):
    ex = []
    for k in keys:
        mol = Chem.MolFromSmiles(d.cov.loc[k, "smiles"]); ao = rdFingerprintGenerator.AdditionalOutput(); ao.AllocateBitInfoMap()
        gen.GetFingerprint(mol, additionalOutput=ao); info = ao.GetBitInfoMap()
        if bit in info:
            atom, rad = info[bit][0]
            env = Chem.FindAtomEnvironmentOfRadiusN(mol, rad, atom); amap = {}
            sub = Chem.PathToSubmol(mol, env, atomMap=amap) if rad > 0 else None
            ex.append(Chem.MolToSmiles(sub) if sub is not None and sub.GetNumAtoms() else mol.GetAtomWithIdx(atom).GetSymbol())
            if len(ex) >= n:
                break
    return ex
order = np.argsort(contrib)
top_neg = [(int(b), float(contrib[b]), float((Xm[:, b] > 0).mean()), bit_examples(int(b))) for b in order[:12]]
top_pos = [(int(b), float(contrib[b]), float((Xm[:, b] > 0).mean()), bit_examples(int(b))) for b in order[::-1][:12]]
ta_coef = dict(zip(d.features["TIER_A"].columns, (m.coef_[:12]).round(4).tolist()))
res["morgan_content"] = {"note": "log g coefficient x feature SD; negative lowers g (fragments at lower energy)", "top_lowering_g": top_neg, "top_raising_g": top_pos,
                         "tier_a_standardized_coefficients": ta_coef,
                         "variance_share_fp_block_in_fitted_logg": float(np.var(Xm @ coef_fp) / np.var(m.predict(np.hstack([(ts.X("TIER_A") - stats[0]) / stats[1], bw * Xm]))))}
(OUT / "exp13_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "morgan_content"}, indent=1, default=lambda o: round(float(o), 4)))
for lab in ("top_lowering_g", "top_raising_g"):
    print(lab); [print("  ", r[0], round(r[1], 4), round(r[2], 3), r[3]) for r in res["morgan_content"][lab]]
print(res["morgan_content"]["tier_a_standardized_coefficients"], res["morgan_content"]["variance_share_fp_block_in_fitted_logg"])
LG.append({"experiment_id": "V2-EXP13-CANDIDATE-STRESS", "generation": "v2-G1", "parent_model": "TA_MORGAN_JOINT",
 "hypothesis": "The joint model's gain over TA_RIDGE depends on weighting, one fold, the cluster unit, leverage extremes, novel chemistry, the energy coordinate or one source.",
 "population_sha256": json.loads((ROOT / "artifacts/wur_v2/data/population_manifest.json").read_text())["keys_sha256"],
 "partition": RU.folds()["partitions"]["PRIMARY"]["assignment_sha256"], "representation": "Tier A + Morgan joint ridge", "endpoint": "aligned and native mu",
 "hyperparameters_and_space": "as nested runs; source transfer nested; Morgan content at modal cfg (0.3, 0.1)", "tuning_process": "nested",
 "results": {k: v for k, v in res.items() if k != "morgan_content"}, "uncertainty": res["bootstrap_strict_cluster_unit"],
 "tail_metrics": {"leverage_top_decile": res["leverage_top_decile"], "novel": res["novel_chemistry_bottom_similarity_decile"]},
 "interpretation": "see exp13_results.json and the decision-gate document", "decision": "diagnostic", "reason": "pre-selection falsification set",
 "informed_later_decisions": "candidate selection matrix"})
