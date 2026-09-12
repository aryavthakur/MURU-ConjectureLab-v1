from common import *
out = {}
for an in ['A_POOLED_ALIGNED', 'B_WUR_NATIVE', 'C_LCSB_NATIVE']:
    D = load(an); g = D['g'].merge(D['cov'], on='group_key'); lg = np.log(g.g_hat)
    W = D['long'].pivot_table(index='group_key', columns='ce_numeric', values='mu')
    r = {}
    edge = np.abs(lg) > 1.59; lo = lg < -1.59; hi = lg > 1.59
    r['n'] = int(len(g)); r['n_edge_low'] = int(lo.sum()); r['n_edge_high'] = int(hi.sum())
    r['sd_log_g'] = float(lg.std()); r['frac_|logg|>1.2'] = float((np.abs(lg) > 1.2).mean())
    def traj(mask):
        w = W.loc[g.group_key[mask]]; return w.median().round(3).to_dict(), w.min(1).median(), w.max(1).median()
    for nm, m in [('edge_low', lo), ('edge_high', hi), ('interior', ~edge)]:
        if m.sum() == 0: continue
        med, mn, mx = traj(m)
        sub = g[m]
        r[nm] = dict(n=int(m.sum()), median_traj=med, median_min_mu=float(mn), median_max_mu=float(mx),
                     frac_all_mu_gt_0p9=float((W.loc[sub.group_key].min(1) > 0.9).mean()),
                     frac_all_mu_gt_0p8=float((W.loc[sub.group_key].min(1) > 0.8).mean()),
                     frac_range_lt_0p1=float(((W.loc[sub.group_key].max(1) - W.loc[sub.group_key].min(1)) < 0.1).mean()),
                     median_mz=float(sub.precursor_mz.median()), median_atoms=float(sub.total_atom_count.median()),
                     median_arom=float(sub.aromatic_ring_count.median()), median_hetfrac=float(sub.heteroatom_fraction.median()),
                     source=sub.source.value_counts().to_dict())
    # ladder unresolved boundary compounds
    lad = D['ladder']; rec = {d: pd.DataFrame(lad['records'][d]) for d in ['M1', 'M2', 'M3']}
    r['ladder'] = {}
    for d, df in rec.items():
        ub = df[df.unresolved_boundary]; 
        w = W.loc[ub.compound_id]
        r['ladder'][d] = dict(n_test=int(len(df)), n_unresolved=int(len(ub)), n_contact=int(df.boundary_contact.sum()),
                              median_traj_unresolved=w.median().round(3).to_dict(), median_traj_resolved=W.loc[df[~df.unresolved_boundary].compound_id].median().round(3).to_dict(),
                              frac_unres_min_mu_gt_0p8=float((w.min(1) > 0.8).mean()), frac_unres_max_mu_lt_0p5=float((w.max(1) < 0.5).mean()),
                              frac_unres_range_lt_0p15=float(((w.max(1)-w.min(1)) < 0.15).mean()),
                              median_range_unres=float((w.max(1)-w.min(1)).median()), median_range_res=float((W.loc[df[~df.unresolved_boundary].compound_id].max(1)-W.loc[df[~df.unresolved_boundary].compound_id].min(1)).median()),
                              collapse_logg_unres_median=float(np.log(D['g'].set_index('group_key').loc[ub.compound_id].g_hat).median()),
                              collapse_logg_unres_frac_edge=float((np.abs(np.log(D['g'].set_index('group_key').loc[ub.compound_id].g_hat)) > 1.59).mean()),
                              source_unres=D['comp'].set_index('group_key').loc[ub.compound_id].source.value_counts().to_dict())
    # any-detector unresolved
    anyu = set().union(*[set(df[df.unresolved_boundary].compound_id) for df in rec.values()])
    allu = set.intersection(*[set(df[df.unresolved_boundary].compound_id) for df in rec.values()])
    r['ladder']['n_unresolved_any'] = len(anyu); r['ladder']['n_unresolved_all3'] = len(allu)
    # Phi of ladder: a_lo, a_hi
    pv = lad['phi']['values']; r['ladder']['phi_a_lo'] = pv[0]; r['ladder']['phi_a_hi'] = pv[-1]; r['ladder']['phi_knot_range_log_u'] = [lad['phi']['knots'][0], lad['phi']['knots'][-1]]
    # what fraction of compounds have mu(E_min) > a_lo (above the shared plateau)? and mu(E_max) < a_hi?
    r['ladder']['frac_test_mu_lowE_above_phi_alo'] = float((W.loc[rec['M1'].compound_id].iloc[:, 0] > pv[0]).mean())
    r['ladder']['frac_test_mu_highE_below_phi_ahi'] = float((W.loc[rec['M1'].compound_id].iloc[:, -1] < pv[-1]).mean())
    r['ladder']['frac_all_mu_lowE_above_phi_alo'] = float((W.iloc[:, 0] > pv[0]).mean()); r['ladder']['frac_all_mu_highE_below_phi_ahi'] = float((W.iloc[:, -1] < pv[-1]).mean())
    # collapse Phi ends
    r['collapse_phi_ends'] = [D['collapse']['phi_v'][0], D['collapse']['phi_v'][-1]]
    # ---- T7 noise floor ----
    m0 = rec['M1'].mae_m0.dropna()
    r['noise'] = dict(n_test=int(len(m0)), median_mae_m0=float(m0.median()), q25=float(m0.quantile(.25)), q75=float(m0.quantile(.75)),
                      frac_lt_0p03=float((m0 < 0.03).mean()), frac_lt_0p0295=float((m0 < REPEAT_SD).mean()), frac_lt_0p05=float((m0 < 0.05).mean()),
                      repeat_sd=REPEAT_SD, median_over_repeat=float(m0.median()/REPEAT_SD))
    out[an] = r
# S3 from percompound S2A (all 791, 3 repeats)
p = json.load(open(f'{B2}/percompound_S2A_FROZEN_PIPELINE.json'))['loeo']
v = np.array([np.mean(list(d.values())) for d in p.values()])
out['A_S3_loeo_all791'] = dict(median=float(np.median(v)), frac_lt_0p03=float((v < 0.03).mean()), frac_lt_0p05=float((v < 0.05).mean()), q25=float(np.quantile(v,.25)), q75=float(np.quantile(v,.75)))
# mae_m0 vs source and vs descriptors in A
D = load('A_POOLED_ALIGNED'); df = pd.DataFrame(D['ladder']['records']['M1']).merge(D['cov'], left_on='compound_id', right_on='group_key')
out['A_mae_m0_by_source'] = df.groupby('source').mae_m0.median().round(4).to_dict()
out['A_spearman_mae_m0_vs'] = {c: round(sp(df.mae_m0, df[c]), 3) for c in FEATURES}
W = D['long'].pivot_table(index='group_key', columns='ce_numeric', values='mu'); rng = (W.max(1)-W.min(1))
out['A_spearman_mae_m0_vs_range'] = round(sp(df.mae_m0, rng.loc[df.compound_id]), 3)
json.dump(out, open(f'{S}/t2_t7_results.json', 'w'), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
