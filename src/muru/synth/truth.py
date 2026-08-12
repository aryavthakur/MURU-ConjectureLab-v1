"""Planted ground-truth laws for the Phase 3 synthetic worlds.

QUARANTINE. This module is imported by the generator and by reporting code that
scores recovery *after* a search has finished. It must never appear in the
import closure of `muru.discovery`, which is the code path the search itself
runs through. `tests/test_p3_import_graph.py` walks that closure and fails if it
does.

Everything here is frozen by `PHASE3_PREREGISTRATION.md`. The constants in
`PHI` were calibrated once, before any governed run, against the *marginal*
mu-by-energy means of the development corpus (0.8414 -> 0.4133); they reproduce
those six means to within 0.011. No response value of any individual compound
enters this module, and no confirmation compound is reachable from it.

Dimensional discipline
----------------------
Every law below is written in **dimensionless** variables (`SCALE` in
`generators.py`): energy in NCE/30, mass in Da/500, counts divided by their
development-corpus median. A recovered law is therefore a statement about
dimensionless quantities and must never be reported as a physical law in raw
units.

Identifiability
---------------
In the collapse form `mu = Phi(E / g(z))`, `g` is identified only up to a
positive multiplicative constant: `(g, Phi(u))` and `(a*g, Phi(u/a))` generate
identical data. Recovery is therefore adjudicated **up to positive scaling**,
which `muru.discovery.equivalence` implements without knowing what was planted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

TRUTH_VERSION = "p3-truth-1.0.0"

# --- shared trajectory shape -------------------------------------------------
# Phi(u) = muinf + (1 - muinf) / (1 + u**p), a logistic in log-energy
# (master plan 18.1). Calibrated to the development corpus marginal means.
PHI = {"mu_inf": 0.2414, "p": 1.4874, "c1": 1.7017}


def phi(u: np.ndarray, mu_inf: float = PHI["mu_inf"], p: float = PHI["p"]) -> np.ndarray:
    """Shared monotone decreasing shape, bounded in (mu_inf, 1]."""
    u = np.clip(np.asarray(u, float), 1e-9, 1e9)
    return mu_inf + (1.0 - mu_inf) / (1.0 + u ** p)


def phi_shape_varying(u: np.ndarray, p_i: np.ndarray,
                      mu_inf: float = PHI["mu_inf"]) -> np.ndarray:
    """G2 only: the exponent itself varies by compound, so no single rescaling
    of the energy axis collapses the family onto one curve."""
    u = np.clip(np.asarray(u, float), 1e-9, 1e9)
    return mu_inf + (1.0 - mu_inf) / (1.0 + u ** p_i)


@dataclass(frozen=True)
class PlantedLaw:
    """One planted world family.

    `g` maps the dimensionless descriptor frame to the energy scale. `expr` is
    the sympy-parseable string form used only to score recovery afterwards.
    `support` is the set of descriptor names the law genuinely depends on.
    """

    name: str
    expr: str
    support: tuple[str, ...]
    g: Callable[[dict[str, np.ndarray]], np.ndarray]
    collapses: bool  # is H-MAIN (a single shared Phi with one scale) true here?
    structural_beyond_mass: bool  # is there real non-mass descriptor dependence?
    notes: str = ""
    extra: dict = field(default_factory=dict)


C1 = PHI["c1"]


# --- G1: clean recoverable collapse ------------------------------------------
# Master plan 18.1: g = c1 * m**0.5, Phi a logistic in log-energy.
G1 = PlantedLaw(
    name="G1",
    expr=f"{C1}*sqrt(precursor_mz)",
    support=("precursor_mz",),
    g=lambda z: C1 * np.sqrt(z["precursor_mz"]),
    collapses=True,
    structural_beyond_mass=False,
    notes="positive control; exponent 0.5 is the 18.3 recovery target (+/-0.15)",
)

# G1B adds genuine non-mass structural dependence, so that 'recovered the
# planted law' is not satisfiable by a mass-only expression. Same family.
G1B = PlantedLaw(
    name="G1B",
    expr=f"{C1}*sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)",
    support=("precursor_mz", "heteroatom_fraction"),
    g=lambda z: C1 * np.sqrt(z["precursor_mz"]) * (1.0 + 0.35 * z["heteroatom_fraction"]),
    collapses=True,
    structural_beyond_mass=True,
    notes="clean collapse WITH non-mass structure; the Phase 2 K4B analogue",
)

# --- G2: predictable, but no single compact universal collapse ---------------
# Scale and shape both depend on descriptors, and a regime switch on aromatic
# ring count changes the family. Genuinely predictable, genuinely not
# compressible into one compact law for a single energy scale.
G2 = PlantedLaw(
    name="G2",
    expr="NO COMPACT UNIVERSAL LAW EXISTS",
    support=("precursor_mz", "heteroatom_fraction", "aromatic_ring_count", "rotatable_bonds"),
    g=lambda z: C1 * np.sqrt(z["precursor_mz"]) * (
        1.0 + 0.30 * z["heteroatom_fraction"]
        + 0.25 * np.where(z["aromatic_ring_count"] > 1.0, z["rotatable_bonds"], 0.0)),
    collapses=False,
    structural_beyond_mass=True,
    notes=("regime-dependent shape exponent p_i as well as scale; H-MAIN is FALSE. "
           "The correct Phase 3 outcome is that no compact conjecture survives."),
    extra={"p_of_z": lambda z: PHI["p"] * (
        1.0 + 0.45 * np.tanh(2.0 * (z["aromatic_ring_count"] - 1.0))
        - 0.30 * np.tanh(1.5 * (z["heteroatom_fraction"] - 1.0)))},
)

# --- G3: mass-only world -----------------------------------------------------
G3 = PlantedLaw(
    name="G3",
    expr=f"{C1}*precursor_mz**0.6",
    support=("precursor_mz",),
    g=lambda z: C1 * np.clip(z["precursor_mz"], 1e-9, None) ** 0.6,
    collapses=True,
    structural_beyond_mass=False,
    notes=("energy and precursor mass only. Other descriptors stay correlated with "
           "mass because the covariates are real. Any accepted NON-MASS structural "
           "conjecture here is the Phase 2 K5 threat realised."),
)

# --- G4: pure null -----------------------------------------------------------
# Master plan 18.1: 'mu depends on energy only, with compound-level random
# offsets'. The offset is independent of every descriptor.
G4 = PlantedLaw(
    name="G4",
    expr="c1 * exp(sigma_g * eps_i),  eps_i independent of all descriptors",
    support=(),
    g=lambda z: np.full(len(next(iter(z.values()))), C1),  # offsets added by generator
    collapses=True,
    structural_beyond_mass=False,
    notes="K6 false-positive basis. No descriptor-level conjecture exists.",
    extra={"sigma_g": 0.22},
)

# G4M: mass-conditional null. Mass dependence is REAL; non-mass structure is
# absent. This is the null matched to the actual Phase 2 question -- structure
# beyond energy and mass -- and is reported alongside, not instead of, G4.
G4M = PlantedLaw(
    name="G4M",
    expr=f"{C1}*sqrt(precursor_mz) * exp(sigma_g * eps_i)",
    support=("precursor_mz",),
    g=lambda z: C1 * np.sqrt(z["precursor_mz"]),
    collapses=True,
    structural_beyond_mass=False,
    notes="mass-conditional null; supplementary to the master plan's G4.",
    extra={"sigma_g": 0.18},
)

# --- G5: confounded ----------------------------------------------------------
# The true driver is a latent variable correlated with the supplied descriptors
# but not equal to any of them, and it is never handed to the search.
G5 = PlantedLaw(
    name="G5",
    expr=f"{C1}*sqrt(precursor_mz)*(1 + 0.40*LATENT)   [LATENT is not observed]",
    support=("precursor_mz", "__latent__"),
    g=lambda z: C1 * np.sqrt(z["precursor_mz"]) * (1.0 + 0.40 * z["__latent__"]),
    collapses=True,
    structural_beyond_mass=True,
    notes=("the driver is unobserved; observed descriptors are proxies at rho ~ 0.6. "
           "The system must not promote a proxy expression to a mechanistic law."),
    extra={"latent_rho": 0.60},
)

# --- GC: measurement-coupling adversary (Phase 2 restriction 1) --------------
# Fractional fragmentation behaviour is held FIXED across mass; an absolute
# low-mass cutoff is then applied and mu is recomputed exactly as the real
# pipeline computes it. Any mass association that appears is manufactured by
# the measurement construction, not by chemistry.
#
# The cutoffs are stipulated at three interpretable instrument settings and are
# NOT tuned to reproduce the observed rho = -0.676.
GC = PlantedLaw(
    name="GC",
    expr="NO DESCRIPTOR LAW; mass association is induced by an absolute m/z cutoff",
    support=(),
    g=lambda z: np.full(len(next(iter(z.values()))), C1),
    collapses=True,
    structural_beyond_mass=False,
    notes=("fractional fragmentation constant across mass; a fixed absolute low-mass "
           "cutoff manufactures a negative mu-mass association with no chemistry. "
           "This tests robustness of the discovery system. It does NOT identify the "
           "mechanism of the real association."),
    extra={"cutoffs_da": (30.0, 50.0, 80.0)},
)

# --- GRT: retention-time surrogate stress test -------------------------------
# A latent molecular property drives BOTH the descriptors and retention time.
# RT predicts the response observationally but is not the planted cause.
GRT = PlantedLaw(
    name="GRT",
    expr=f"{C1}*sqrt(precursor_mz)*(1 + 0.30*LIPO);  RT = f(LIPO) + noise",
    support=("precursor_mz", "__lipo__"),
    g=lambda z: C1 * np.sqrt(z["precursor_mz"]) * (1.0 + 0.30 * z["__lipo__"]),
    collapses=True,
    structural_beyond_mass=True,
    notes=("RT is a downstream marker of the latent property, never the cause. "
           "Bounded stress test only -- this is not chromatography modelling, and "
           "it does not resolve the real NC7 finding causally."),
    extra={"rt_noise": 0.35},
)

# --- GA: fully synthetic analytic sanity case --------------------------------
# Independent of real chemistry: descriptors drawn i.i.d. uniform, law
# analytically transparent. Guards against the possibility that recovery in the
# real-covariate worlds depends on some property of the real descriptor matrix.
GA = PlantedLaw(
    name="GA",
    expr="1.5*v0 + 0.5*v1*v1",
    support=("v0", "v1"),
    g=lambda z: 1.5 * z["v0"] + 0.5 * z["v1"] ** 2,
    collapses=True,
    structural_beyond_mass=True,
    notes="analytically transparent, no real chemistry involved",
)

REGISTRY: dict[str, PlantedLaw] = {
    law.name: law for law in (G1, G1B, G2, G3, G4, G4M, G5, GC, GRT, GA)
}


def planted(name: str) -> PlantedLaw:
    return REGISTRY[name]
