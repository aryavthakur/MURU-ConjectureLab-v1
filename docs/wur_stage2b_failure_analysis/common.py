import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-reconciliation-f69f63/src')
ROOT = '/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-reconciliation-f69f63'
S = '/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/failure_analysis'
A2 = f'{ROOT}/artifacts/wur_stage2a'; B2 = f'{ROOT}/artifacts/wur_stage2b'
FEATURES = ("precursor_mz", "total_atom_count", "rotatable_bonds", "ring_count",
            "aromatic_ring_count", "rdbe", "tpsa", "heteroatom_fraction",
            "n_N", "n_O", "n_S", "n_halogen")
SCALE = {"precursor_mz": 500.0, "total_atom_count": 37.0, "rotatable_bonds": 4.0,
         "ring_count": 2.0, "aromatic_ring_count": 2.0, "rdbe": 8.5,
         "tpsa": 54.5, "heteroatom_fraction": 0.25, "n_N": 2.0, "n_O": 2.0,
         "n_S": 1.0, "n_halogen": 1.0}
MASS_BLOCK = ("precursor_mz", "total_atom_count", "rdbe")
REPEAT_SD = 0.0295
def load(an):
    d = f'{A2}/{an}'
    return dict(long=pd.read_csv(f'{d}/long_mu.csv'), cov=pd.read_csv(f'{d}/covariates.csv'),
                comp=pd.read_csv(f'{d}/compounds.csv'), g=pd.read_csv(f'{d}/collapse_g.csv'),
                collapse=json.load(open(f'{d}/collapse.json')), ladder=json.load(open(f'{d}/ladder.json')),
                sel=json.load(open(f'{d}/selection.json')))
def phi_eval(knots, vals, u):
    return np.interp(np.log(np.clip(u, 1e-9, 1e9)), knots, vals, left=vals[0], right=vals[-1])
def folds():
    return json.load(open(f'{B2}/folds.json'))
def X_of(cov):
    return np.column_stack([cov[c].to_numpy(float)/SCALE[c] for c in FEATURES])
def sp(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b, nan_policy='omit')[0])
