"""Hierarchical model, variance decomposition, and model-adequacy diagnostics.

Answers a different question from the baseline ladder: not "how well can mu be
predicted" but "where does the variance in mu live, and how much of the
between-compound part can structure account for".

The descriptor-explained share is reported BOTH in-sample and
cross-validated under the primary split. Only the cross-validated figure is
used for K5, because an in-sample R2 from 12 descriptors on 439 compounds is
optimistic by construction.

Writes artifacts/p2_variance.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.models import SEED
from muru.molecules import MASS_BLOCK, TIER_A
from muru.splits import grouped_folds

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
R: dict = {}

d = pd.read_parquet(ART / "p2_splits.parquet")
# precursor_mz lives in both frames and is the same record value; keep the split
# frame's copy so the join cannot introduce an _x/_y ambiguity.
tA = pd.read_parquet(ART / "p2_tierA.parquet").drop(columns=["precursor_mz"])
df = d.merge(tA, on="group_key")
assert not any(c.endswith(("_x", "_y")) for c in df.columns)
df["energy_c"] = (df.ce_numeric - df.ce_numeric.mean()) / 30.0
df["cid"] = df.inchikey_first_block

# ---------------------------------------------------------------------------
# Model adequacy, on the natural scale (DEVIATIONS D7, D8)
# ---------------------------------------------------------------------------
ols = smf.ols("mu ~ C(ce_numeric)", data=df).fit()
df["resid_b1"] = ols.resid
adq = {
    "response_scale": "natural (not logit); see DEVIATIONS D7",
    "mu_min": float(df.mu.min()), "mu_max": float(df.mu.max()),
    "n_mu_gt_1": int((df.mu > 1).sum()),
    "resid_sd_by_energy": {int(e): round(float(g.resid_b1.std(ddof=1)), 5)
                           for e, g in df.groupby("ce_numeric")},
    "resid_skew_by_energy": {int(e): round(float(g.resid_b1.skew()), 3)
                             for e, g in df.groupby("ce_numeric")},
}
adq["resid_sd_ratio_max_over_min"] = round(
    max(adq["resid_sd_by_energy"].values())
    / min(adq["resid_sd_by_energy"].values()), 3)
# Breusch-Pagan style check of residual spread against fitted value
fitted = ols.fittedvalues
adq["spearman_absresid_vs_fitted"] = round(float(
    pd.Series(np.abs(df.resid_b1)).corr(pd.Series(fitted), method="spearman")), 4)
R["model_adequacy"] = adq

# ---------------------------------------------------------------------------
# Hierarchical model: compound random intercept + random slope in energy
# ---------------------------------------------------------------------------
md = smf.mixedlm("mu ~ C(ce_numeric)", df, groups=df.cid,
                 re_formula="~energy_c")
mf = md.fit(method="lbfgs", maxiter=2000)

re = pd.DataFrame(mf.random_effects).T
re.columns = ["u_intercept", "u_slope"][:re.shape[1]]
re.index.name = "cid"
re = re.reset_index()

cov = mf.cov_re.to_numpy()
sig_e = float(mf.scale)
R["hierarchical"] = {
    "implementation": "statsmodels MixedLM (see DEVIATIONS D11 for why not PyMC)",
    "converged": bool(mf.converged),
    "n_obs": int(mf.nobs), "n_groups": int(df.cid.nunique()),
    "var_random_intercept": round(float(cov[0, 0]), 6),
    "var_random_slope": round(float(cov[1, 1]), 6) if cov.shape[0] > 1 else None,
    "cov_intercept_slope": round(float(cov[0, 1]), 6) if cov.shape[0] > 1 else None,
    "corr_intercept_slope": round(float(cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])), 4)
    if cov.shape[0] > 1 else None,
    "residual_var": round(sig_e, 6),
    "loglike": round(float(mf.llf), 2),
}

# ---------------------------------------------------------------------------
# Variance decomposition
# ---------------------------------------------------------------------------
total_var = float(df.mu.var(ddof=1))
per_e = df.groupby("ce_numeric").mu.transform("mean")
v_energy = float(per_e.var(ddof=1))

merged = df.merge(re, on="cid", how="left")
compound_component = (merged.u_intercept
                      + merged.u_slope * merged.energy_c
                      if "u_slope" in merged else merged.u_intercept)
v_compound = float(np.var(compound_component, ddof=1))

R["variance_decomposition"] = {
    "total_var_mu": round(total_var, 6),
    "energy_fixed": round(v_energy, 6),
    "energy_fixed_share": round(v_energy / total_var, 4),
    "compound_random": round(v_compound, 6),
    "compound_random_share": round(v_compound / total_var, 4),
    "residual": round(sig_e, 6),
    "residual_share": round(sig_e / total_var, 4),
    "icc_conditional_on_energy": round(
        float(cov[0, 0] / (cov[0, 0] + sig_e)), 4),
}

# ---------------------------------------------------------------------------
# Descriptor-explained share of BETWEEN-COMPOUND variance  (K5 input)
# ---------------------------------------------------------------------------
cmp_tbl = (df.drop_duplicates("cid")[["cid", "scaffold_group", *TIER_A]]
           .merge(re, on="cid"))
targets = ["u_intercept"] + (["u_slope"] if "u_slope" in re.columns else [])

ALPHAS = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]


def cv_r2(X: np.ndarray, y: np.ndarray, groups: pd.Series,
          n_folds: int = 5) -> float:
    """Out-of-fold R2, scaffold-grouped, ridge penalty chosen inside each fold."""
    folds = grouped_folds(groups, n_folds=n_folds, seed=SEED).to_numpy()
    oof = np.zeros_like(y, dtype=float)
    for f in np.unique(folds):
        tr, te = folds != f, folds == f
        inner = grouped_folds(groups[tr], n_folds=4, seed=SEED).to_numpy()
        best, best_e = ALPHAS[0], np.inf
        for a in ALPHAS:
            errs = []
            for g in np.unique(inner):
                i_tr, i_te = inner != g, inner == g
                Xi, yi = X[tr][i_tr], y[tr][i_tr]
                m = Ridge(alpha=a).fit((Xi - Xi.mean(0)) / (Xi.std(0) + 1e-12), yi)
                Xt = (X[tr][i_te] - Xi.mean(0)) / (Xi.std(0) + 1e-12)
                errs.append(np.mean((y[tr][i_te] - m.predict(Xt)) ** 2))
            if np.mean(errs) < best_e:
                best_e, best = np.mean(errs), a
        Xtr = X[tr]
        mu_, sd_ = Xtr.mean(0), Xtr.std(0) + 1e-12
        m = Ridge(alpha=best).fit((Xtr - mu_) / sd_, y[tr])
        oof[te] = m.predict((X[te] - mu_) / sd_)
    return float(1 - ((y - oof) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def in_sample_r2(X, y):
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
    m = Ridge(alpha=1.0).fit(Xs, y)
    p = m.predict(Xs)
    return float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


FEATSETS = {
    "tier_a_full": list(TIER_A),
    "tier_a_no_mass": [c for c in TIER_A if c not in MASS_BLOCK],
    "mass_block_only": list(MASS_BLOCK),
    "precursor_mz_only": ["precursor_mz"],
}

R["descriptor_explained_between_compound"] = {}
for tgt in targets:
    y = cmp_tbl[tgt].to_numpy(float)
    entry = {}
    for fname, feats in FEATSETS.items():
        X = cmp_tbl[feats].to_numpy(float)
        entry[fname] = {
            "cv_r2_scaffold_grouped": round(cv_r2(X, y, cmp_tbl.scaffold_group), 4),
            "in_sample_r2": round(in_sample_r2(X, y), 4),
            "n_features": len(feats),
        }
    R["descriptor_explained_between_compound"][tgt] = entry

# K5 headline: descriptor-driven share of between-compound variance, the master
# plan's >= 0.20 threshold, evaluated out of sample on the primary split.
share = R["descriptor_explained_between_compound"]["u_intercept"][
    "tier_a_full"]["cv_r2_scaffold_grouped"]
share_nm = R["descriptor_explained_between_compound"]["u_intercept"][
    "tier_a_no_mass"]["cv_r2_scaffold_grouped"]
R["K5_variance_share"] = {
    "metric": ("cross-validated R2 of Tier A predicting the compound random "
               "intercept, scaffold-grouped out-of-fold"),
    "threshold": 0.20,
    "tier_a_full": share,
    "tier_a_no_mass": share_nm,
    "meets_threshold_full": bool(share >= 0.20),
    "meets_threshold_without_mass": bool(share_nm >= 0.20),
}

(ART / "p2_variance.json").write_text(json.dumps(R, indent=2, default=str))
print(json.dumps(R, indent=2, default=str))
