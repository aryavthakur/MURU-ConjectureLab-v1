"""T(E) map exposure: the frozen map was fitted on population B (124 keys whose LCSB
copies are DEV2B targets).  For each outer fold of repeat 0, refit the map on the
TRAINING-side B keys only, re-align the WUR-only training compounds with it, and
rerun LIN and V1C.  Held-out targets stay as frozen (they are LCSB copies for B,
frozen-map reads for other WUR keys)."""
import sys, json, os, time
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ[v] = "1"
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path('/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-reconciliation-f69f63')
SP = Path('/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/review_leakage')
sys.path.insert(0, str(ROOT / 'src'))
from muru.wur_stage2 import cv as CV, folds as FO, arms_v1 as AV
from muru.wur_bridge import fit_energy_map, apply_energy_map
from muru.wur_stage2.world import POOLED_ENERGIES
ART = ROOT / 'artifacts'
long, cov, frame = CV.load_dev2b()
gate = json.load(open(ART / 'wur_bridge_gate.json')); a0, b0 = gate['alignment']['a'], gate['alignment']['b']
POPB = sorted(gate['population_b']['connectivity_keys'])
fw = pd.read_csv(ART / 'wur_stage2b' / 'features_wur.csv')[['connectivity_key', 'ce_numeric', 'mu']]
dev = pd.read_parquet(ART / 'p2_dev_corpus.parquet').rename(columns={'inchikey_first_block': 'connectivity_key'})[['connectivity_key', 'ce_numeric', 'mu']]
t0 = time.time()
full = fit_energy_map(fw, dev, POPB)
print(f"reproduce frozen map: a {full['a']:.6f} (frozen {a0:.6f}) b {full['b']:.6f} (frozen {b0:.6f}) obj {full['objective']:.5f} {time.time()-t0:.0f}s", flush=True)
folds = FO.load_folds(); rep0 = folds['repeats'][0]; asg = pd.Series(rep0['assignment'])
wur_only = sorted(set(frame[frame.source == 'WUR'].group_key))
led = {n: json.load(open(CV.LEDGER / f'{n}.json'))['folds'] for n in ('LIN_RIDGE_TIERA', 'V1C_RICH_RIDGE_24')}
rows = []
for k in range(5):
    held = sorted(asg.index[asg == k]); train = sorted(asg.index[asg != k])
    b_train = [x for x in POPB if x not in set(held)]
    fit = fit_energy_map(fw, dev, b_train); a_k, b_k = fit['a'], fit['b']
    mapped, _ = apply_energy_map(fw[fw.connectivity_key.isin(set(wur_only) & set(train))], a_k, b_k)
    mapped = mapped[mapped.ce_numeric.isin(POOLED_ENERGIES)].rename(columns={'connectivity_key': 'group_key'}); mapped['source'] = 'WUR'
    long_k = pd.concat([long[~(long.group_key.isin(set(mapped.group_key)))], mapped], ignore_index=True)
    assert long_k.groupby(['group_key', 'ce_numeric']).size().max() == 1 and len(long_k) == len(long)
    fold1 = {"k": 5, "repeats": [{"repeat": 0, "assignment": rep0['assignment']}]}
    b0p = CV.b0_predictions(long_k, cov, frame, fold1)
    r = {"fold": k, "n_b_train": len(b_train), "a": a_k, "b": b_k, "d_mu_train_max": float((mapped.merge(long, on=['group_key', 'ce_numeric'], suffixes=('_k', '')).eval('mu_k - mu')).abs().max())}
    for name, mk in (("LIN_RIDGE_TIERA", CV.LinRidge), ("V1C_RICH_RIDGE_24", AV.RichRidge)):
        arm = mk(); arm.fit(long_k[long_k.group_key.isin(train)], cov[cov.group_key.isin(train)], {"repeat": 0, "outer_fold": k})
        cov_h = cov.set_index('group_key').loc[held].reset_index(); Y = CV.wide(long, held)
        m = CV.fold_metrics(arm.predict_mu(cov_h), Y, b0p[(0, k)], frame.set_index('group_key').source.loc[held].to_numpy())
        r[name] = m['P1']; r[name + '_ledger'] = [f['P1'] for f in led[name] if f['repeat'] == 0 and f['fold'] == k][0]
    rows.append(r); print(r, f"{time.time()-t0:.0f}s", flush=True)
json.dump({"full_refit": full, "per_fold": rows}, open(SP / 'refit_map_leaveout.json', 'w'), indent=1)
R = pd.DataFrame(rows); print(R[['fold', 'a', 'b', 'd_mu_train_max', 'LIN_RIDGE_TIERA', 'LIN_RIDGE_TIERA_ledger', 'V1C_RICH_RIDGE_24', 'V1C_RICH_RIDGE_24_ledger']].to_string())
print("DONE")
