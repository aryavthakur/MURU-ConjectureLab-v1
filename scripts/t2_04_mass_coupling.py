"""Denominator-coupling audit for mu (Phase 2 instruction 10).

Precursor mass appears in the definition of mu:

    mu = (sum_k I_k * mz_k) / (sum_k I_k) / mz_precursor

so an apparent association between mu and precursor mass may be produced
mechanically by the normalization rather than by chemistry. This audit asks one
question:

    Can mu manufacture an association with precursor mass even when the
    underlying FRACTIONAL fragmentation behaviour is held exactly constant?

The diagnostic is deterministic and analytically transparent. It is a Phase 2
response-variable audit, NOT the Phase 3 synthetic discovery system: there is no
search, no hidden ground-truth equation, no discovery engine.

Writes artifacts/p2_mass_coupling.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
ENERGIES = [15, 30, 45, 60, 75, 90]
SEED = 20260811

R: dict = {}

# Real precursor masses, so the diagnostic spans the corpus's actual range.
dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")
masses = (dev.groupby("group_key").precursor_mz.first().to_numpy(float))
R["n_synthetic_compounds"] = int(len(masses))
R["mass_range"] = [float(masses.min()), float(masses.max())]


def mu_from_spectrum(mz: np.ndarray, inten: np.ndarray, mz_prec: float) -> float:
    """mu exactly as Phase 1 defines it."""
    return float((inten * mz).sum() / inten.sum() / mz_prec)


def spearman(a, b):
    return float(stats.spearmanr(a, b).statistic)


# ---------------------------------------------------------------------------
# Analytic statement
# ---------------------------------------------------------------------------
# Writing SY for survival yield and phi for the intensity-weighted mean FRAGMENT
# mass expressed as a fraction of the precursor mass,
#
#     mu = SY + (1 - SY) * phi
#
# (exactly, up to the observed/declared precursor mass ratio that Phase 1
# deviation D1 quantified at ~9 ppm). Both SY and phi are dimensionless. So if
# fragmentation is genuinely FRACTIONAL -- every fragment's m/z a fixed
# proportion of its precursor, with fixed relative intensities -- mu is
# independent of precursor mass by construction, and no coupling exists.
#
# Coupling appears exactly when fragment masses are set on an ABSOLUTE scale
# rather than a proportional one. Then phi = <mz_frag> / mz_prec falls as
# 1/mz_prec, and mu inherits a negative mass dependence with no chemistry
# whatsoever.
R["analytic"] = {
    "identity": "mu = SY + (1 - SY) * phi, with phi = <mz_fragment> / mz_precursor",
    "fractional_regime": ("if fragment m/z scales proportionally with precursor "
                          "m/z and relative intensities are fixed, phi is "
                          "mass-invariant and mu carries NO mass dependence"),
    "absolute_regime": ("if fragment m/z is drawn on an absolute scale, "
                        "phi ~ 1/mz_precursor, so mu acquires a negative mass "
                        "association mechanically, with no chemistry"),
}

rng = np.random.default_rng(SEED)

# A fixed fractional fragmentation programme, identical for every compound:
# survival yield falls with energy, and fragments sit at fixed FRACTIONS of the
# precursor mass. Nothing here depends on the molecule.
SY_BY_E = {15: 0.66, 30: 0.15, 45: 0.02, 60: 0.005, 75: 0.002, 90: 0.001}
FRAG_FRACTIONS = np.array([0.25, 0.40, 0.55, 0.70, 0.85])
FRAG_WEIGHTS = np.array([0.10, 0.20, 0.30, 0.25, 0.15])

# An absolute-scale fragment programme: the same number of fragments at the same
# relative intensities, but placed at fixed m/z values that do not know the
# precursor mass. Values chosen to sit inside the corpus's observed fragment
# range.
FRAG_ABSOLUTE = np.array([70.0, 105.0, 140.0, 180.0, 230.0])


def build(regime: str, blend: float = 0.5) -> pd.DataFrame:
    rows = []
    for i, mp in enumerate(masses):
        for e in ENERGIES:
            sy = SY_BY_E[e]
            if regime == "fractional":
                fmz = FRAG_FRACTIONS * mp
            elif regime == "absolute":
                fmz = np.minimum(FRAG_ABSOLUTE, mp * 0.95)
            elif regime == "blend":
                fmz = np.minimum(blend * FRAG_ABSOLUTE
                                 + (1 - blend) * FRAG_FRACTIONS * mp, mp * 0.95)
            elif regime == "absolute_floor":
                # proportional fragments, but nothing may fall below a fixed
                # low-mass cutoff -- the realistic instrument behaviour
                fmz = np.maximum(FRAG_FRACTIONS * mp, 50.0)
                fmz = np.minimum(fmz, mp * 0.95)
            else:
                raise ValueError(regime)

            mz = np.concatenate([[mp], fmz])
            inten = np.concatenate([[sy], (1 - sy) * FRAG_WEIGHTS])
            rows.append({"cid": i, "precursor_mz": mp, "ce_numeric": e,
                         "mu": mu_from_spectrum(mz, inten, mp), "sy": sy})
    return pd.DataFrame(rows)


REGIMES = {
    "A_fractional": ("Purely fractional fragmentation: fragment m/z proportional "
                     "to precursor m/z. Fractional behaviour held exactly "
                     "constant across mass."),
    "B_absolute": ("Absolute-scale fragmentation: fragments at fixed m/z, "
                   "independent of precursor. Fractional behaviour NOT constant."),
    "C_blend": ("50/50 blend of the two, the realistic middle case."),
    "D_absolute_floor": ("Proportional fragments with a fixed 50 Da low-mass "
                         "cutoff -- proportional chemistry plus one absolute "
                         "instrument limit."),
}

R["regimes"] = {}
for key, desc in REGIMES.items():
    regime = key.split("_", 1)[1]
    df = build(regime)
    per_e = {}
    for e in ENERGIES:
        g = df[df.ce_numeric == e]
        per_e[int(e)] = round(spearman(g.mu, g.precursor_mz), 4)
    R["regimes"][key] = {
        "description": desc,
        "rho_mu_vs_precursor_mz_by_energy": per_e,
        "max_abs_rho": round(max(abs(v) for v in per_e.values()), 4),
        "mu_range": [round(float(df.mu.min()), 4), round(float(df.mu.max()), 4)],
    }

# ---------------------------------------------------------------------------
# Observed comparison
# ---------------------------------------------------------------------------
obs = {}
for e in ENERGIES:
    g = dev[dev.ce_numeric == e]
    obs[int(e)] = round(spearman(g.mu, g.precursor_mz), 4)
R["observed_rho_by_energy"] = obs
R["observed_max_abs_rho"] = round(max(abs(v) for v in obs.values()), 4)

# How much of the observed high-energy association could regime D reproduce?
R["comparison"] = {
    "observed_at_NCE90": obs[90],
    "fractional_at_NCE90": R["regimes"]["A_fractional"][
        "rho_mu_vs_precursor_mz_by_energy"][90],
    "absolute_at_NCE90": R["regimes"]["B_absolute"][
        "rho_mu_vs_precursor_mz_by_energy"][90],
    "absolute_floor_at_NCE90": R["regimes"]["D_absolute_floor"][
        "rho_mu_vs_precursor_mz_by_energy"][90],
}

# ---------------------------------------------------------------------------
# Empirical check on the real data: is the observed mass association carried by
# phi (the fragment term, where the denominator lives) or by SY?
# ---------------------------------------------------------------------------
real = {}
for e in ENERGIES:
    g = dev[dev.ce_numeric == e]
    real[int(e)] = {
        "rho_mu_mass": round(spearman(g.mu, g.precursor_mz), 4),
        "rho_phi_mass": round(spearman(g.fragment_depth.dropna(),
                                       g.loc[g.fragment_depth.notna(),
                                             "precursor_mz"]), 4),
        "rho_sy_mass": round(spearman(g.survival_yield, g.precursor_mz), 4),
    }
R["decomposition_of_the_association"] = real

(ART / "p2_mass_coupling.json").write_text(json.dumps(R, indent=2))
print(json.dumps(R, indent=2))
