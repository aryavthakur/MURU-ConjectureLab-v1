import sys, json, os
sys.path.insert(0, 'src')
import numpy as np, pandas as pd
ROOT = 'artifacts/wur_stage2a'
OUT = '/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad/failure_analysis'
ANALYSES = ['A_POOLED_ALIGNED', 'B_WUR_NATIVE', 'C_LCSB_NATIVE']
DESC = ['precursor_mz','total_atom_count','rotatable_bonds','ring_count','aromatic_ring_count','rdbe','tpsa','heteroatom_fraction','n_N','n_O','n_S','n_halogen']
ENERGY_SCALE = 30.0

def load(a):
    d = f'{ROOT}/{a}'
    long = pd.read_csv(f'{d}/long_mu.csv')
    g = pd.read_csv(f'{d}/collapse_g.csv')
    cov = pd.read_csv(f'{d}/covariates.csv')
    comp = pd.read_csv(f'{d}/compounds.csv')
    col = json.load(open(f'{d}/collapse.json'))
    lad = json.load(open(f'{d}/ladder.json'))
    sel = json.load(open(f'{d}/selection.json'))
    cache = json.load(open(f'{d}/candidate_cache.json'))
    return dict(long=long, g=g, cov=cov, comp=comp, col=col, lad=lad, sel=sel, cache=cache)

def wide(long):
    p = long.pivot_table(index='group_key', columns='ce_numeric', values='mu').sort_index()
    return p.index.to_numpy(), p.columns.to_numpy(float), p.to_numpy(float)

def phi_eval(knots, vals, u):
    return np.interp(np.log(np.clip(u, 1e-9, 1e9)), knots, vals, left=vals[0], right=vals[-1])
