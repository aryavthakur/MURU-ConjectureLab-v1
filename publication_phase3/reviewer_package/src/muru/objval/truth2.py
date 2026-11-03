"""Planted ground truth for the FRESH objective-validation worlds.

QUARANTINE. Imported by `objval.generators2` and by adjudication code that
scores recovery *after* candidate selection has finished. It must never appear
in the import closure of `muru.discovery` or of the `objval` discovery side
(`signature`, `select`, `equiv`). `tests/test_ov_import_graph.py` enforces this.

Differences from `muru.synth.truth`, and why each exists
--------------------------------------------------------
* **Parameters are drawn, not fixed.** Phase 3 froze every constant
  (`c1 = 1.7017`, mass exponent 0.5, `0.35 * hetfrac`, `Phi` exponent 1.4874).
  A rule developed by looking at Phase 3's fronts could be tuned to those exact
  numbers. Here each replicate draws its own constants from pre-registered
  ranges, and the shared shape `Phi` draws its own exponent and asymptote, so
  the study tests generalization across the family rather than across noise
  draws of one instance.
* **The non-mass carrier rotates.** Phase 3's structured worlds always put the
  non-mass dependence on `heteroatom_fraction`. Here it cycles over three
  descriptors with materially different mass coupling, declared in advance.
* **A near-degenerate family (G1C) is planted deliberately**, using a form the
  frozen grammar cannot represent exactly, so that "the family is identified but
  the algebraic form is not" is a reachable and testable outcome.

Dimensional discipline is unchanged: every law is written in the dimensionless
frame (`muru.synth.generators.SCALE`). Identifiability is unchanged: in
`mu = Phi(E/g(z))`, `g` is identified only up to a positive multiplicative
constant, so recovery is adjudicated up to positive scaling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

TRUTH2_VERSION = "ov-truth-1.0.0"

# --- shared trajectory shape -------------------------------------------------
# Phi(u) = mu_inf + (1 - mu_inf) / (1 + u**p). Phase 3 froze
# (mu_inf, p) = (0.2414, 1.4874), calibrated once to the development corpus
# marginal means. Here those two are DRAWN per replicate from ranges bracketing
# the Phase 3 values, so shape-family recovery is a real test rather than a
# recovery of one memorized curve.
PHI_RANGES = {"mu_inf": (0.18, 0.30), "p": (1.20, 1.80)}

# Overall scale of g. Identified only up to positive scaling, so its value can
# never be recovered and is drawn purely to keep u in a sensible range.
G_SCALE_RANGE = (1.40, 2.00)

# Non-mass structural carriers, cycled across replicates. Chosen for materially
# different mass coupling in the development corpus; the measured correlations
# are recorded in the world manifest so the difficulty of each is declared in
# advance rather than discovered afterwards.
NON_MASS_CARRIERS = ("heteroatom_fraction", "rotatable_bonds", "n_O")

# Strength of the non-mass term.
STRUCT_COEF_RANGE = (0.25, 0.55)

# G3 mass-only exponent. Phase 3 fixed 0.6; drawn here.
G3_EXPONENT_RANGE = (0.45, 0.75)

# Null dispersion of the compound-level offset.
G4_SIGMA_RANGE = (0.18, 0.28)
G4M_SIGMA_RANGE = (0.14, 0.24)

# G5 latent correlation with the supplied proxies.
G5_LATENT_RHO_RANGE = (0.50, 0.70)
G5_COEF_RANGE = (0.30, 0.55)

# GRT latent-to-retention-time coupling.
GRT_COEF_RANGE = (0.22, 0.42)
GRT_RT_NOISE_RANGE = (0.25, 0.45)

# GC absolute low-mass cutoffs, stipulated at interpretable instrument settings
# and never tuned to reproduce any observed correlation.
GC_CUTOFFS_DA = (30.0, 50.0, 80.0)

# G2 regime switch and shape modulation.
G2_SWITCH_VARIABLES = ("aromatic_ring_count", "ring_count")
G2_SHAPE_MODULATION_RANGE = (0.35, 0.60)


def draw_params(family: str, rng: np.random.Generator, replicate: int) -> dict:
    """Every constant a world needs, drawn once from the ranges above."""
    p: dict = {
        "mu_inf": float(rng.uniform(*PHI_RANGES["mu_inf"])),
        "phi_p": float(rng.uniform(*PHI_RANGES["p"])),
        "g_scale": float(rng.uniform(*G_SCALE_RANGE)),
    }
    if family in ("G1B", "G1C", "G5", "GRT", "G2"):
        p["carrier"] = NON_MASS_CARRIERS[replicate % len(NON_MASS_CARRIERS)]
        p["struct_coef"] = float(rng.uniform(*STRUCT_COEF_RANGE))
    if family == "G1A":
        p["a0"] = float(rng.uniform(1.10, 1.90))
        p["a1"] = float(rng.uniform(0.30, 0.80))
    if family == "G3":
        p["mass_exponent"] = float(rng.uniform(*G3_EXPONENT_RANGE))
    if family == "G4":
        p["sigma_g"] = float(rng.uniform(*G4_SIGMA_RANGE))
    if family == "G4M":
        p["sigma_g"] = float(rng.uniform(*G4M_SIGMA_RANGE))
    if family == "G5":
        p["latent_rho"] = float(rng.uniform(*G5_LATENT_RHO_RANGE))
        p["struct_coef"] = float(rng.uniform(*G5_COEF_RANGE))
    if family == "GRT":
        p["struct_coef"] = float(rng.uniform(*GRT_COEF_RANGE))
        p["rt_noise"] = float(rng.uniform(*GRT_RT_NOISE_RANGE))
    if family == "G2":
        p["switch_variable"] = G2_SWITCH_VARIABLES[replicate % len(G2_SWITCH_VARIABLES)]
        p["shape_modulation"] = float(rng.uniform(*G2_SHAPE_MODULATION_RANGE))
        p["second_carrier"] = "rotatable_bonds" if p["carrier"] != "rotatable_bonds" \
            else "heteroatom_fraction"
    return p


def phi(u: np.ndarray, mu_inf: float, p: float) -> np.ndarray:
    u = np.clip(np.asarray(u, float), 1e-9, 1e9)
    return mu_inf + (1.0 - mu_inf) / (1.0 + u ** p)


def phi_shape_varying(u: np.ndarray, p_i: np.ndarray, mu_inf: float) -> np.ndarray:
    u = np.clip(np.asarray(u, float), 1e-9, 1e9)
    return mu_inf + (1.0 - mu_inf) / (1.0 + u ** p_i)


@dataclass(frozen=True)
class PlantedLaw2:
    """One fresh world family.

    `g_of` maps a dimensionless descriptor dict plus the world's drawn
    parameters to the energy scale. `expr_of` renders the planted expression as
    a sympy-parseable string, used only to score recovery afterwards.
    `support_of` names the descriptors the law genuinely depends on.
    """

    name: str
    role: str
    g_of: Callable[[dict, dict], np.ndarray]
    expr_of: Callable[[dict], str]
    support_of: Callable[[dict], tuple[str, ...]]
    collapses: bool
    structural_beyond_mass: bool
    exactly_representable: bool
    notes: str = ""
    extra: dict = field(default_factory=dict)


# --- G1A: analytic sanity, no real chemistry ---------------------------------
G1A = PlantedLaw2(
    name="G1A", role="positive control — analytically simple conditional law",
    g_of=lambda z, p: p["a0"] * z["v0"] + p["a1"] * z["v1"] ** 2,
    expr_of=lambda p: f"{p['a0']:.6f}*v0 + {p['a1']:.6f}*v1**2",
    support_of=lambda p: ("v0", "v1"),
    collapses=True, structural_beyond_mass=True, exactly_representable=True,
    notes=("i.i.d. covariates, transparent law, low complexity. Proves the "
           "complete pipeline works and isolates it from any property of the "
           "real descriptor matrix. Constants are drawn, not the Phase 3 GA "
           "literals."),
)

# --- G1B: the realistic molecule-conditional law -----------------------------
G1B = PlantedLaw2(
    name="G1B", role="positive control — realistic molecule-conditional law",
    g_of=lambda z, p: (p["g_scale"] * np.sqrt(z["precursor_mz"])
                       * (1.0 + p["struct_coef"] * z[p["carrier"]])),
    expr_of=lambda p: (f"{p['g_scale']:.6f}*sqrt(precursor_mz)"
                       f"*(1 + {p['struct_coef']:.6f}*{p['carrier']})"),
    support_of=lambda p: ("precursor_mz", p["carrier"]),
    collapses=True, structural_beyond_mass=True, exactly_representable=True,
    notes=("shared trajectory family with molecule-specific scaling predicted "
           "by more than mass alone; the actual MURU claim. Mass exponent is "
           "exactly 0.5, the master plan 18.3 target."),
)

# --- G1C: the near-degenerate family challenge -------------------------------
# The true law is OUTSIDE the frozen grammar: `exp` is not an available operator
# (DEVIATIONS_P3 D1), so no candidate can represent this exactly. Its
# first-order expansion, `sqrt(m)*(1 + a*(h - hbar))`, is far simpler and nearly
# prediction-equivalent over the observed domain. The Type 2 signature — mass
# exponent 0.5, one positive monotone non-mass effect — is unchanged.
#
# The degeneracy is created by placing the truth outside the hypothesis space,
# NOT by tuning constants to reproduce Phase 3's observed failure numerically.
#
# `carrier_center` is the centering constant `X̄`. It is a CONSTANT of the world,
# fixed when the world is generated. Generation passes no `carrier_center`, so
# the fallback reproduces the world exactly as built. Truth-side scoring passes
# the frozen value, because a constant that is recomputed from whatever matrix
# it is handed stops being a constant under differentiation: perturbing the
# carrier column moves the mean with it, the two shifts cancel, and the
# elasticity collapses to zero. See DEVIATIONS_OBJECTIVE_VALIDATION.md D2.
G1C = PlantedLaw2(
    name="G1C", role="positive control — near-degenerate family challenge",
    g_of=lambda z, p: (p["g_scale"] * np.sqrt(z["precursor_mz"])
                       * np.exp(p["struct_coef"]
                                * (z[p["carrier"]]
                                   - float(p.get("carrier_center",
                                                 np.mean(z[p["carrier"]])))))),
    expr_of=lambda p: (f"{p['g_scale']:.6f}*sqrt(precursor_mz)"
                       f"*exp({p['struct_coef']:.6f}*({p['carrier']} - cbar))"),
    support_of=lambda p: ("precursor_mz", p["carrier"]),
    collapses=True, structural_beyond_mass=True, exactly_representable=False,
    notes=("the generating form is not representable in the frozen grammar, so "
           "several simpler forms are near-equivalent on the observed domain. "
           "The correct output may be: family and scaling identified, exact "
           "algebraic form NOT identified."),
)

# --- G2: predictable, not compressible ---------------------------------------
G2 = PlantedLaw2(
    name="G2", role="refusal — predictable but no compact universal collapse",
    g_of=lambda z, p: (p["g_scale"] * np.sqrt(z["precursor_mz"])
                       * (1.0 + p["struct_coef"] * z[p["carrier"]]
                          + 0.25 * np.where(z[p["switch_variable"]] > 1.0,
                                            z[p["second_carrier"]], 0.0))),
    expr_of=lambda p: "NO COMPACT UNIVERSAL LAW EXISTS",
    support_of=lambda p: ("precursor_mz", p["carrier"], p["switch_variable"],
                          p["second_carrier"]),
    collapses=False, structural_beyond_mass=True, exactly_representable=False,
    notes=("scale AND shape depend on descriptors, with a regime switch, so "
           "H-MAIN is false. Refusal, or a restricted regime-specific "
           "conclusion, is the correct behaviour."),
    extra={"p_of_z": lambda z, p: p["phi_p"] * (
        1.0 + p["shape_modulation"] * np.tanh(2.0 * (z[p["switch_variable"]] - 1.0))
        - 0.30 * np.tanh(1.5 * (z[p["carrier"]] - 1.0)))},
)

# --- G3: mass-only -----------------------------------------------------------
G3 = PlantedLaw2(
    name="G3", role="refusal — mass-only world",
    g_of=lambda z, p: p["g_scale"] * np.clip(z["precursor_mz"], 1e-9, None) ** p["mass_exponent"],
    expr_of=lambda p: f"{p['g_scale']:.6f}*precursor_mz**{p['mass_exponent']:.6f}",
    support_of=lambda p: ("precursor_mz",),
    collapses=True, structural_beyond_mass=False, exactly_representable=False,
    notes=("energy and precursor mass only; other descriptors stay "
           "mass-correlated because the covariates are real. Any accepted "
           "non-mass structural claim here is the K5 threat realized."),
)

# --- G4: pure null -----------------------------------------------------------
G4 = PlantedLaw2(
    name="G4", role="refusal — pure null; the false-positive basis",
    g_of=lambda z, p: np.full(len(next(iter(z.values()))), p["g_scale"]),
    expr_of=lambda p: "g = c * exp(sigma * eps_i), eps_i independent of all descriptors",
    support_of=lambda p: (),
    collapses=True, structural_beyond_mass=False, exactly_representable=False,
    notes="no descriptor-level conjecture exists; the offsets are added by the generator.",
)

# --- G4M: mass-conditional null ----------------------------------------------
G4M = PlantedLaw2(
    name="G4M", role="refusal — mass-conditional null",
    g_of=lambda z, p: p["g_scale"] * np.sqrt(z["precursor_mz"]),
    expr_of=lambda p: f"{p['g_scale']:.6f}*sqrt(precursor_mz) * exp(sigma*eps_i)",
    support_of=lambda p: ("precursor_mz",),
    collapses=True, structural_beyond_mass=False, exactly_representable=False,
    notes="mass dependence is real; structure beyond mass must not be invented.",
)

# --- G5: confounded ----------------------------------------------------------
G5 = PlantedLaw2(
    name="G5", role="refusal — confounded, true driver unobserved",
    g_of=lambda z, p: (p["g_scale"] * np.sqrt(z["precursor_mz"])
                       * (1.0 + p["struct_coef"] * z["__latent__"])),
    expr_of=lambda p: (f"{p['g_scale']:.6f}*sqrt(precursor_mz)"
                       f"*(1 + {p['struct_coef']:.6f}*LATENT)   [LATENT never supplied]"),
    support_of=lambda p: ("precursor_mz", "__latent__"),
    collapses=True, structural_beyond_mass=True, exactly_representable=False,
    notes="observed descriptors are proxies; a proxy expression must not be promoted.",
)

# --- GC: measurement-coupling adversary --------------------------------------
GC = PlantedLaw2(
    name="GC", role="refusal — measurement-coupling adversary",
    g_of=lambda z, p: np.full(len(next(iter(z.values()))), p["g_scale"]),
    expr_of=lambda p: "NO DESCRIPTOR LAW; mass association induced by an absolute m/z cutoff",
    support_of=lambda p: (),
    collapses=True, structural_beyond_mass=False, exactly_representable=False,
    notes=("fractional fragmentation held fixed as a law; an absolute low-mass "
           "cutoff manufactures a mass association with no chemistry. Does NOT "
           "identify the mechanism of the real association."),
)

# --- GRT: retention-time surrogate -------------------------------------------
GRT = PlantedLaw2(
    name="GRT", role="refusal — retention-time surrogate",
    g_of=lambda z, p: (p["g_scale"] * np.sqrt(z["precursor_mz"])
                       * (1.0 + p["struct_coef"] * z["__lipo__"])),
    expr_of=lambda p: (f"{p['g_scale']:.6f}*sqrt(precursor_mz)"
                       f"*(1 + {p['struct_coef']:.6f}*LIPO);  RT = f(LIPO) + noise"),
    support_of=lambda p: ("precursor_mz", "__lipo__"),
    collapses=True, structural_beyond_mass=True, exactly_representable=False,
    notes=("RT is a downstream marker of a latent property, never the cause. "
           "Bounded stress test; does not resolve the real NC7 finding causally."),
)

REGISTRY2: dict[str, PlantedLaw2] = {
    law.name: law for law in (G1A, G1B, G1C, G2, G3, G4, G4M, G5, GC, GRT)
}


def planted2(name: str) -> PlantedLaw2:
    return REGISTRY2[name]
