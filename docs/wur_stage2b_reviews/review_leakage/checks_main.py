"""Leakage audit, part 1: identity, seal/HOLD scans, target recomputation."""
import sys, json, re, hashlib
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path('/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-reconciliation-f69f63')
SP = Path('/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-reconciliation-f69f63/7be686fa-90a5-447a-960d-089f68387c46/scratchpad')
sys.path.insert(0, str(ROOT / 'src'))
from muru.molecules import scaffold_group, tier_a_descriptors, murcko_scaffold
from muru.wur_stage2.descriptors2 import tier_a2_descriptors, TIER_A2
from muru.discovery.protocol import FEATURES
from muru.wur_bridge import apply_energy_map
from muru.io.wur_provenance import canonical_key_hash
from muru.splits import assert_group_disjoint
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

ART = ROOT / 'artifacts'; A = ART / 'wur_stage2a' / 'A_POOLED_ALIGNED'; B = ART / 'wur_stage2b'
comp = pd.read_csv(A / 'compounds.csv'); cov = pd.read_csv(A / 'covariates.csv'); long = pd.read_csv(A / 'long_mu.csv')
a2 = pd.read_csv(B / 'descriptors_a2.csv'); folds = json.load(open(B / 'folds.json'))
hold = json.load(open(ART / 'wur_dev_internal_holdout.json')); sealed = json.load(open(ART / 'wur_sealed_partition.json'))
HOLD = set(hold['hold']['connectivity_keys']); ANA = set(hold['analysis']['connectivity_keys']); SEALED = set(sealed['connectivity_keys'])
HOLD_G = set(hold['hold']['scaffold_groups'])
LSEALED = set(json.load(open(ART / 'confirmation_set_sealed.json'))['connectivity_keys']) if 'connectivity_keys' in json.load(open(ART / 'confirmation_set_sealed.json')) else None
if LSEALED is None:
    d = json.load(open(ART / 'confirmation_set_sealed.json')); print('confirmation_set_sealed keys:', list(d)[:10])
    for k, v in d.items():
        if isinstance(v, list) and v and isinstance(v[0], str) and len(v[0]) == 14: LSEALED = set(v); break
POPB = set(json.load(open(ART / 'wur_bridge_gate.json'))['population_b']['connectivity_keys'])
gate = json.load(open(ART / 'wur_bridge_gate.json'))['alignment']; a_, b_ = gate['a'], gate['b']
keys = set(comp.group_key); print('DEV2B n', len(keys), 'sha', canonical_key_hash(sorted(keys))[:16], '== folds', folds['population_keys_sha256'][:16])
R = {}
def rep(name, ok, detail=''):
    R[name] = (ok, detail); print(('CLEAN  ' if ok else 'FINDING'), name, detail)

# ---------------- 1. identity ----------------
rep('dev2b_vs_hold', not (keys & HOLD), f'{len(keys & HOLD)}')
rep('dev2b_vs_wur_sealed', not (keys & SEALED), f'{len(keys & SEALED)}')
rep('dev2b_vs_lcsb_sealed', not (keys & LSEALED), f'{len(keys & LSEALED)}')
rep('popB_in_dev2b_all_LCSB', set(comp[comp.group_key.isin(POPB)].source) == {'LCSB'} and POPB <= keys, f'{len(POPB & keys)}/{len(POPB)}')
rep('wur_keys_subset_of_analysis', set(comp[comp.source == 'WUR'].group_key) <= ANA, '')
rec = hashlib.sha256(json.dumps([r['assignment'] for r in folds['repeats']], sort_keys=True).encode()).hexdigest()
rep('folds_hash_recompute', rec == folds['folds_sha256'], rec[:16])
g_of = comp.set_index('group_key').scaffold_group
for r in folds['repeats']:
    asg = pd.Series(r['assignment']); ok = set(asg.index) == keys
    df = pd.DataFrame({'k': asg.index, 'fold': asg.values, 'g': g_of.loc[asg.index].values})
    ng = df.groupby('g').fold.nunique().max(); nk = df.groupby('k').fold.nunique().max()
    rep(f'fold_disjoint_repeat{r["repeat"]}', ok and ng == 1 and nk == 1, f'groups spanning >1 fold: {(df.groupby("g").fold.nunique()>1).sum()}')
sp = comp.groupby('scaffold_group').split.nunique().max()
rep('stage2a_split_group_disjoint', sp == 1, '')
rep('dev2b_groups_vs_hold_groups', not (set(comp.scaffold_group) & HOLD_G), f'{len(set(comp.scaffold_group) & HOLD_G)}')

# scaffold consistency from SMILES
p2 = pd.read_parquet(ART / 'p2_compounds.parquet'); p2 = p2[~p2.in_confirmation]
lsm = p2.set_index('inchikey_first_block').smiles
wid = pd.read_parquet(SP / 'wur_dev_pos_identity_full.parquet').set_index('connectivity_key')
wsm = wid.smiles
smiles = {}
for k, s in zip(comp.group_key, comp.source):
    smiles[k] = lsm.loc[k] if s == 'LCSB' else wsm.loc[k]
recg = {k: scaffold_group(smiles[k], k) for k in comp.group_key}
mism = [(k, recg[k], g_of.loc[k]) for k in comp.group_key if recg[k] != g_of.loc[k]]
rep('scaffold_group_recompute_matches_covariates', len(mism) == 0, f'{len(mism)} mismatches {mism[:3]}')
# pop B: WUR-side scaffold vs LCSB-side scaffold
popb_diff = []
for k in sorted(POPB & keys):
    gw = scaffold_group(wsm.loc[k], k) if k in wsm.index else None; gl = g_of.loc[k]
    if gw != gl: popb_diff.append((k, gl, gw))
rep('popB_wur_vs_lcsb_scaffold_agree', len(popb_diff) == 0, f'{len(popb_diff)} differ {popb_diff[:3]}')
# does any pop-B WUR-side scaffold match another DEV2B compound in a different fold?
straddle = []
for k, gl, gw in popb_diff:
    others = comp[(comp.scaffold_group == gw) & (comp.group_key != k)].group_key.tolist()
    for r in folds['repeats']:
        asg = r['assignment']
        for o in others:
            if asg[o] != asg[k]: straddle.append((r['repeat'], k, o))
rep('popB_alt_scaffold_straddles_fold', len(straddle) == 0, f'{len(straddle)} {straddle[:3]}')
# canonical SMILES duplicates across different keys; identical 24-descriptor vectors across keys
canon = {k: Chem.MolToSmiles(Chem.MolFromSmiles(smiles[k])) for k in comp.group_key}
dup = pd.Series(canon).reset_index(); dup.columns = ['k', 'c']; dd = dup.groupby('c').k.apply(list); dd = dd[dd.str.len() > 1]
rep('same_canonical_smiles_different_key', len(dd) == 0, f'{len(dd)} {dd.tolist()[:3]}')
X = cov.set_index('group_key')[list(FEATURES)].join(a2.set_index('group_key')[list(TIER_A2)])
X12 = X[[f for f in FEATURES if f != 'precursor_mz']]
key24 = X.round(6).astype(str).agg('|'.join, axis=1); key11 = X12.round(6).astype(str).agg('|'.join, axis=1)
def straddles(sig, label):
    grp = sig.groupby(sig).apply(lambda s: list(s.index)); grp = grp[grp.str.len() > 1]
    pairs = [(g[i], g[j]) for g in grp for i in range(len(g)) for j in range(i + 1, len(g))]
    st = 0; tot = 0; same_scaf = 0
    for r in folds['repeats']:
        asg = r['assignment']
        for x, y in pairs:
            tot += 1
            if asg[x] != asg[y]: st += 1
    same_scaf = sum(1 for x, y in pairs if g_of.loc[x] == g_of.loc[y])
    print(f'  {label}: {len(grp)} groups, {len(pairs)} pairs, same-scaffold pairs {same_scaf}, pair-repeats straddling folds {st}/{tot}')
    return pairs, st
p24, s24 = straddles(key24, 'identical 24-descriptor vectors'); p11, s11 = straddles(key11, 'identical 11 non-mass Tier A')
rep('near_duplicate_descriptor_twins_across_folds', s24 == 0, f'{s24} straddling pair-repeats; pairs {p24[:5]}')
# formula-isomers: same molecular formula different key
form = {k: rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(smiles[k])) for k in comp.group_key}
fs = pd.Series(form); fg = fs.groupby(fs).apply(lambda s: list(s.index)); fg = fg[fg.str.len() > 1]
n_iso_pairs = sum(len(g) * (len(g) - 1) // 2 for g in fg); n_iso_straddle = 0
for r in folds['repeats']:
    asg = r['assignment']
    for g in fg:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if asg[g[i]] != asg[g[j]]: n_iso_straddle += 1
print(f'  formula isomer groups {len(fg)}, pairs {n_iso_pairs}, pair-repeats straddling {n_iso_straddle}/{3*n_iso_pairs}')

# ---------------- 2. seal / HOLD scan of every artifact ----------------
pat = re.compile(r'\b[A-Z]{14}\b')
forbidden = HOLD | SEALED | LSEALED
hits = {}
for base in [ART / 'wur_stage2a', B, ROOT / 'docs' / 'wur_stage2b_failure_analysis']:
    for p in sorted(base.rglob('*')):
        if p.is_file() and p.suffix in ('.csv', '.json', '.md', '.py', '.txt'):
            found = set(pat.findall(p.read_text(errors='ignore'))) & forbidden
            if found: hits[str(p.relative_to(ROOT))] = (len(found & HOLD), len(found & SEALED), len(found & LSEALED))
rep('no_hold_or_sealed_key_in_any_stage2_artifact', not hits, f'{hits}')
# ckpt dirs (pickles / other)
other = [str(p.relative_to(ROOT)) for base in [ART / 'wur_stage2a', B] for p in base.rglob('*') if p.is_file() and p.suffix not in ('.csv', '.json', '.md', '.py', '.txt')]
print('  non-text artifact files:', len(other), other[:5])
for p in other:
    found = set(pat.findall((ROOT / p).read_bytes().decode('latin1'))) & forbidden
    if found: print('  FORBIDDEN KEY IN', p, len(found))
fw = pd.read_csv(B / 'features_wur.csv'); fl = pd.read_csv(B / 'features_lcsb.csv')
rep('features_wur_keys_subset_analysis', set(fw.connectivity_key) <= ANA and not (set(fw.connectivity_key) & (HOLD | SEALED)), f'{fw.connectivity_key.nunique()} keys')
rep('features_lcsb_keys_not_sealed', not (set(fl.connectivity_key) & LSEALED), f'{fl.connectivity_key.nunique()} keys')

# ---------------- 3. target recomputation ----------------
dev = pd.read_parquet(ART / 'p2_dev_corpus.parquet')
L = long[long.source == 'LCSB'].merge(dev[['inchikey_first_block', 'ce_numeric', 'mu']].rename(columns={'inchikey_first_block': 'group_key', 'mu': 'mu_src'}), on=['group_key', 'ce_numeric'], how='left')
rep('lcsb_long_mu_equals_p2_dev_corpus', L.mu_src.notna().all() and (L.mu - L.mu_src).abs().max() < 1e-9, f'max |d| {(L.mu - L.mu_src).abs().max():.2e}, n {len(L)}')
wn = fw[['connectivity_key', 'ce_numeric', 'mu']]
mapped, ncl = apply_energy_map(wn, a_, b_)
W = long[long.source == 'WUR'].merge(mapped.rename(columns={'connectivity_key': 'group_key', 'mu': 'mu_re'}), on=['group_key', 'ce_numeric'], how='left')
rep('wur_long_mu_equals_map_of_features_wur_native_mu', W.mu_re.notna().all() and (W.mu - W.mu_re).abs().max() < 1e-9, f'max |d| {(W.mu - W.mu_re).abs().max():.2e}, n {len(W)}, clamped {ncl}')
# is the WUR native mu of pop-B keys (features_wur) anywhere in DEV2B?  It must not be (LCSB copy kept)
rep('popB_wur_copy_absent_from_long', not (set(long[long.source == 'WUR'].group_key) & POPB), '')
# descriptors
bad = []
for k in comp.group_key:
    d = tier_a_descriptors(smiles[k]); row = cov.set_index('group_key').loc[k]
    for f in FEATURES:
        if f == 'precursor_mz': continue
        if abs(d[f] - row[f]) > 1e-6: bad.append((k, f, d[f], row[f]))
rep('tierA_descriptors_recompute_from_smiles', not bad, f'{len(bad)} {bad[:3]}')
bad2 = []
for k in comp.group_key:
    d = tier_a2_descriptors(smiles[k]); row = a2.set_index('group_key').loc[k]
    for f in TIER_A2:
        if abs(d[f] - row[f]) > 1e-6: bad2.append((k, f))
rep('tierA2_descriptors_recompute_from_smiles', not bad2, f'{len(bad2)}')
# precursor_mz offset vs exact [M+H]+ by source
ex = {k: Descriptors.ExactMolWt(Chem.MolFromSmiles(smiles[k])) + 1.007276 for k in comp.group_key}
cv2 = cov.set_index('group_key'); off = pd.Series({k: cv2.loc[k, 'precursor_mz'] - ex[k] for k in comp.group_key})
src = comp.set_index('group_key').source
print('  precursor_mz - exact [M+H]+ by source (Da):')
for s in ('LCSB', 'WUR'):
    o = off[src == s]; print(f'    {s}: n={len(o)} median={o.median():.5f} IQR=[{o.quantile(.25):.5f},{o.quantile(.75):.5f}] |off|>0.01: {(o.abs()>0.01).sum()} |off|>0.5: {(o.abs()>0.5).sum()}')
# can source be predicted from the 24 descriptors alone? (a model could exploit a source signature only if it exists)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
Xs = X.loc[comp.group_key].to_numpy(); ys = (src.loc[comp.group_key] == 'WUR').astype(int).to_numpy()
auc = cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), Xs, ys, cv=5, scoring='roc_auc').mean()
Xs2 = np.column_stack([Xs, off.loc[comp.group_key].to_numpy()])
auc2 = cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), Xs2, ys, cv=5, scoring='roc_auc').mean()
print(f'  source-from-descriptors AUC (24 desc): {auc:.3f}; with precursor offset feature: {auc2:.3f}')
# does the source residual survive?  log g residual after ridge on 24 vs source
json.dump({k: [bool(v[0]), v[1]] for k, v in R.items()}, open(SP / 'review_leakage' / 'checks_main.json', 'w'), indent=1)
print('\nSUMMARY findings:', [k for k, v in R.items() if not v[0]])
