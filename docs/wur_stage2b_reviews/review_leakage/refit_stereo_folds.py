"""Price the stereo-variant scaffold straddle: rebuild the three frozen repeats with
stereo-stripped scaffold groups (same seeds, same builder) and rerun LIN / V1A / V1C."""
import sys, json, os, time
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): os.environ[v] = "1"
from pathlib import Path
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger; RDLogger.DisableLog("rdApp.*")
ROOT = Path('/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-reconciliation-f69f63')
SP = Path('/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/review_leakage')
sys.path.insert(0, str(ROOT / 'src'))
from muru.wur_stage2 import cv as CV, folds as FO, arms_v1 as AV
from muru.splits import grouped_folds
long, cov, frame = CV.load_dev2b()
def strip(s):
    if s.startswith('__ACYCLIC__'): return s
    m = Chem.MolFromSmiles(s); Chem.RemoveStereochemistry(m); return Chem.MolToSmiles(m)
frame2 = frame.copy(); frame2['scaffold_group'] = frame2.scaffold_group.map(strip)
print('groups', frame.scaffold_group.nunique(), '->', frame2.scaffold_group.nunique())
merged = frame2.groupby('scaffold_group').group_key.apply(list)
affected = [k for g, ks in merged.items() if frame[frame.group_key.isin(ks)].scaffold_group.nunique() > 1 for k in ks]
print('affected compounds', len(affected))
st = {"k": 5, "repeats": []}
for r, seed in enumerate(FO.REPEAT_SEEDS):
    f = grouped_folds(frame2["scaffold_group"], n_folds=5, seed=seed)
    st["repeats"].append({"repeat": r, "seed": seed, "assignment": dict(zip(frame2["group_key"], (int(x) for x in f.to_numpy())))})
frozen = FO.load_folds()
# how much does the assignment change overall?
for r in range(3):
    a, b = frozen['repeats'][r]['assignment'], st['repeats'][r]['assignment']
    print('repeat', r, 'compounds whose fold changed:', sum(a[k] != b[k] for k in a))
out = {}
for label, folds in (("stereo_merged", st), ("frozen", frozen)):
    b0p = CV.b0_predictions(long, cov, frame, folds); res = {}
    for name, mk in (("B1", CV.B1MassOnly), ("LIN", CV.LinRidge), ("V1A", AV.StableLaw), ("V1C", AV.RichRidge)):
        res[name] = CV.run_cv(mk, long, cov, frame, folds, b0p, with_loeo=False)
    out[label] = {n: {"P1": r.p1_vector().tolist(), "per_compound": r.per_compound} for n, r in res.items()}
    out[label + "_cmp"] = {"V1C_vs_LIN": CV.compare(res["V1C"], res["LIN"]), "V1C_vs_V1A": CV.compare(res["V1C"], res["V1A"])}
    print(label, {n: round(float(np.mean(v["P1"])), 5) for n, v in out[label].items()}, {k: (round(v["mean_diff"], 5), v["wins"], round(v["se_diff"], 5)) for k, v in out[label + "_cmp"].items()})
    # RMSE of the affected (steroid) compounds
    for n in ("LIN", "V1C"):
        pc = res[n].per_compound
        aff = np.mean([np.mean(list(pc[k].values())) for k in affected]); rest = np.mean([np.mean(list(pc[k].values())) for k in pc if k not in set(affected)])
        print(f'   {n}: mean per-compound RMSE affected {aff:.4f} vs others {rest:.4f}')
json.dump({k: v for k, v in out.items() if k.endswith('_cmp')} | {"affected": affected}, open(SP / 'refit_stereo_folds.json', 'w'), indent=1)
print('DONE')
