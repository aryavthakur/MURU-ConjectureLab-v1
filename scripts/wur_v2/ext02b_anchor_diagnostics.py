"""Diagnostics of the failed anchor gate (anchors only; they are calibration data already accessed).

Re-decodes the same 1,292 anchor spectra under a separately logged ANCHOR_CALIBRATION guard
(`anchor_diagnostics_access.json`). No validation or secondary spectrum is touched. Nothing here
changes the frozen gate outcome: MultiMS2 is not qualified.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from muru.wur_v2 import external_multims2 as E, external_mzml as X
from muru.wur_v2.external_guard import AccessGuard
ROOT = Path(__file__).resolve().parents[2]; OUT = E.OUT
P = json.loads((OUT / "populations.json").read_text())
pop = pd.DataFrame(P["populations"]["ANCHOR"]); sp = pd.DataFrame(P["spectra"]["ANCHOR"])
allowed = {tuple(x) for x in P["allowed_spectra"]["ANCHOR"]}
guard = AccessGuard("ANCHOR_CALIBRATION", OUT / "anchor_diagnostics_access.json", ROOT / "MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md", allowed)
files = E.file_index().set_index("file"); mh = pop.set_index("key").mh
rows = []
for fn, g in sp.groupby("file"):
    peaks = X.decode_selected(ROOT / files.loc[fn, "path"], g.spectrum_id.tolist(), guard)
    for r in g.itertuples(index=False):
        mz, it = peaks[r.spectrum_id]; m = mh.loc[r.key]
        keep1 = it >= 0.01 * it.max()
        below = mz < m + 1.5
        rows.append({"key": r.key, "energy": r.energy, "mu": E.spectrum_mu(mz, it, m), "mu_cut1pct": E.spectrum_mu(mz[keep1], it[keep1], m),
                     "mu_no_above_precursor": E.spectrum_mu(mz[below], it[below], m), "n_peaks": int(mz.size),
                     "precursor_fraction": float(it[np.abs(mz - m) <= 0.02].sum() / it.sum()),
                     "intensity_above_precursor_fraction": float(it[mz > m + 1.5].sum() / it.sum())})
s = pd.DataFrame(rows)
cell = s.groupby(["key", "energy"]).agg(mu=("mu", "median"), mu_cut1pct=("mu_cut1pct", "median"), mu_no_above=("mu_no_above_precursor", "median"),
                                        within_cell_sd=("mu", "std"), n=("mu", "size"), n_peaks=("n_peaks", "median"),
                                        prec_frac=("precursor_fraction", "median"), above_frac=("intensity_above_precursor_fraction", "median")).reset_index()
W = cell.pivot(index="key", columns="energy", values="mu")
long = pd.read_csv(ROOT / "artifacts/wur_v2/data/long_aligned.csv").pivot(index="group_key", columns="ce_numeric", values="mu").loc[W.index]
out = {"n_anchor_spectra": len(s), "within_cell_scan_sd_pooled": float(np.sqrt((cell.within_cell_sd.dropna() ** 2).mean())),
       "median_n_peaks_per_energy": cell.groupby("energy").n_peaks.median().to_dict(),
       "median_precursor_fraction_per_energy": cell.groupby("energy").prec_frac.median().to_dict(),
       "median_intensity_above_precursor_per_energy": cell.groupby("energy").above_frac.median().to_dict(),
       "mu_obs_quantiles_per_energy": {str(e): W[e].quantile([.1, .5, .9]).round(3).tolist() for e in W.columns},
       "exposed_mu_quantiles_per_rung": {str(e): long[e].quantile([.1, .5, .9]).round(3).tolist() for e in long.columns},
       "monotone_fraction_20_40_60": float(((W[20.0] >= W[40.0]) & (W[40.0] >= W[60.0])).mean()),
       "spearman_mu_obs_vs_exposed_rung": {f"{e}eV_vs_NCE{int(r)}": float(spearmanr(W[e], long[r], nan_policy='omit').statistic) for e in W.columns for r in long.columns},
       "spearman_variants_vs_best_rung": {}}
for col in ("mu_cut1pct", "mu_no_above"):
    Wv = cell.pivot(index="key", columns="energy", values=col)
    out["spearman_variants_vs_best_rung"][col] = {str(e): float(max(spearmanr(Wv[e], long[r], nan_policy='omit').statistic for r in long.columns)) for e in Wv.columns}
cell.to_csv(OUT / "anchor_diagnostic_cells.csv", index=False)
(OUT / "anchor_diagnostics.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(json.dumps(out, indent=1, default=float))
