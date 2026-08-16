"""E3 world generation under the V2C (fresh, disjoint) seed namespace.

MURU_V2_A1_STUDY_DESIGN.md section 5 fixes the convention:

    world_id     = "V2C|<experiment>|<cell_id>|r<replicate:03d>"
    seed payload = "muru-v2-calibration|" + "|".join(parts)

`generator.derive_seed` (the frozen production module, imported read-only
below) prefixes every seed payload with `"paper-benchmark-v1|"`. The two
prefixes are asserted distinct at import time so no V2C world can ever
collide with a real benchmark case's seed stream or content hash.

This module does not modify, monkeypatch, or import-time-alter the frozen
`generator.py` in any way. It reuses exactly two things from it, unmodified,
both administrative constants, not scientific behaviour:

  * `N_COMPOUNDS`, `N_SCAFFOLDS` -- the population geometry constants.

Everything that must vary per E3 cell (the truth coefficient `c`, the
response noise sd, the energy grid) is re-expressed here as an explicit
function parameter rather than reused from the frozen `_law` /
`_response_matrix`, because those two functions sample `coefficient` and
select `noise_sd` internally with no override hook. The covariate-generation
algorithm (`_synthetic_compounds`) and the M0 collapse-response algorithm
(the non-M1/M2/M3 branch of `_response_matrix`) are transcribed here
line-for-line from the frozen source, with only the seed source and the two
override parameters (`c`, `noise_sd`) changed. E3 never touches M1/M2/M3;
only the M0 branch is relevant to this study.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401  (puts the frozen src tree on sys.path)
from muru.paper_benchmark import generator as frozen_generator

# ---------------------------------------------------------------------------
# Namespace discipline (MURU_V2_A1_STUDY_DESIGN.md section 5)
# ---------------------------------------------------------------------------

V2C_SEED_PREFIX = "muru-v2-calibration|"
BENCHMARK_SEED_PREFIX = "paper-benchmark-v1|"
assert V2C_SEED_PREFIX != BENCHMARK_SEED_PREFIX, "V2C namespace must be disjoint from the benchmark namespace"
assert not V2C_SEED_PREFIX.startswith(BENCHMARK_SEED_PREFIX)
assert not BENCHMARK_SEED_PREFIX.startswith(V2C_SEED_PREFIX)


def derive_seed_v2(*parts: str) -> int:
    """`muru-v2-calibration|`-namespaced twin of `generator.derive_seed`."""
    payload = V2C_SEED_PREFIX + "|".join(parts)
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


N_COMPOUNDS = frozen_generator.N_COMPOUNDS   # 180, reused unmodified
N_SCAFFOLDS = frozen_generator.N_SCAFFOLDS   # 30, reused unmodified

ENERGY_GRID_6 = (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)  # frozen ENERGY_GRID, restated as float
#: H_id_geometry's "12 points" arm. Not specified numerically anywhere in the
#: design docs beyond "doubling the energy grid from 6 to 12 points"; the
#: disclosed, stated implementation choice is 12 points evenly spaced over
#: the same [15, 90] range the frozen 6-point grid covers, so the comparison
#: isolates resolution from range.
ENERGY_GRID_12 = tuple(float(v) for v in np.linspace(15.0, 90.0, 12))

TRUTH_FAMILIES = (
    "mass_power",
    "mass_affine_descriptor",
    "mass_saturating_descriptor",
    "mass_interaction",
    "mass_exponential_descriptor",
)


def energy_grid_for(points: int) -> tuple[float, ...]:
    if points == 6:
        return ENERGY_GRID_6
    if points == 12:
        return ENERGY_GRID_12
    raise ValueError(f"unsupported energy grid point count: {points}")


# ---------------------------------------------------------------------------
# Covariates -- transcribed verbatim from generator._synthetic_compounds,
# seeded under the V2C namespace instead of the benchmark one.
# ---------------------------------------------------------------------------


def synthetic_compounds_v2(geometry_id: str) -> tuple[pd.DataFrame, int]:
    seed = derive_seed_v2(geometry_id, "compounds")
    rng = np.random.default_rng(seed)
    scaffold = np.repeat(np.arange(N_SCAFFOLDS), N_COMPOUNDS // N_SCAFFOLDS)
    split_by_group = np.array(["train"] * 20 + ["validation"] * 5 + ["test"] * 5)
    group_latent = rng.normal(0, 1, N_SCAFFOLDS)
    latent = group_latent[scaffold] + rng.normal(0, 0.35, N_COMPOUNDS)
    mass = np.exp(5.55 + 0.25 * latent + rng.normal(0, 0.18, N_COMPOUNDS))
    descriptor = latent + rng.normal(0, 0.45, N_COMPOUNDS) - latent.min()
    descriptor /= descriptor.max()
    descriptor2 = 0.65 * latent + rng.normal(0, 0.65, N_COMPOUNDS)
    descriptor2 = (descriptor2 - descriptor2.min()) / (descriptor2.max() - descriptor2.min())
    distractor = rng.normal(0, 1, N_COMPOUNDS)
    correlated = 0.85 * descriptor + 0.15 * rng.normal(0, 1, N_COMPOUNDS)
    frame = pd.DataFrame({
        "compound_id": [f"C{i:03d}" for i in range(N_COMPOUNDS)],
        "scaffold_id": [f"S{i:02d}" for i in scaffold],
        "split": split_by_group[scaffold],
        "mass": mass,
        "descriptor": descriptor,
        "descriptor2": descriptor2,
        "distractor": distractor,
        "correlated_distractor": correlated,
    })
    return frame, seed


# ---------------------------------------------------------------------------
# Truth law -- same five closed forms as generator._law, with `coefficient`
# taken as an explicit E3-cell parameter `c` instead of drawn from
# rng.uniform(0.25, 0.55). The RNG draw sequence is otherwise preserved
# exactly (scale, then a dummy coefficient draw matching the frozen
# unconditional draw at the top of `_law`, then, for mass_power only, the
# exponent draw) so the stream shape matches the frozen generator's even
# though the sampled "coefficient" value itself is discarded.
# ---------------------------------------------------------------------------


def law_v2(family: str, compounds: pd.DataFrame, rng: np.random.Generator, c: float) -> tuple[np.ndarray, dict]:
    mass = compounds["mass"].to_numpy()
    descriptor = compounds["descriptor"].to_numpy()
    descriptor2 = compounds["descriptor2"].to_numpy()
    scale = float(rng.uniform(1.1, 1.8))
    _unused_coefficient_draw = float(rng.uniform(0.25, 0.55))  # stream-shape parity with frozen generator._law
    if family == "mass_power":
        exponent = float(rng.uniform(0.45, 0.75))
        g = scale * (mass / 250.0) ** exponent
        return g, {"scale": scale, "exponent": exponent}
    if family == "mass_affine_descriptor":
        g = scale * np.sqrt(mass / 250.0) * (1 + c * descriptor)
        return g, {"scale": scale, "coefficient": c}
    if family == "mass_saturating_descriptor":
        g = scale * np.sqrt(mass / 250.0) * (1 + c * descriptor / (1 + descriptor))
        return g, {"scale": scale, "coefficient": c}
    if family == "mass_interaction":
        g = scale * np.sqrt(mass / 250.0) * (1 + c * descriptor * descriptor2)
        return g, {"scale": scale, "coefficient": c}
    if family == "mass_exponential_descriptor":
        g = scale * np.sqrt(mass / 250.0) * np.exp(c * descriptor / 3)
        return g, {"scale": scale, "coefficient": c}
    raise ValueError(f"unknown E3 truth family: {family}")


# ---------------------------------------------------------------------------
# Response -- the M0 (pure scalar-collapse) branch of
# generator._response_matrix, transcribed verbatim, with `noise_sd` and the
# energy grid taken as explicit parameters instead of a kind-keyed lookup
# and the frozen module constant. E3 never generates M1/M2/M3 adequacy
# deviations or missingness; every E3 world is true M0.
# ---------------------------------------------------------------------------


def response_v2(
    g: np.ndarray,
    rng: np.random.Generator,
    energy_grid: tuple[float, ...],
    noise_sd: float,
) -> tuple[np.ndarray, dict]:
    energy = np.asarray(energy_grid, dtype=float)
    mu_inf = float(rng.uniform(0.15, 0.30))
    phi_p = float(rng.uniform(1.20, 1.70))
    u = (energy[None, :] / 45.0) / g[:, None]
    mu = mu_inf + (1 - mu_inf) * np.exp(-(u ** phi_p))
    if noise_sd:
        mu = mu + rng.normal(0, noise_sd, mu.shape)
    mu = np.clip(mu, 1e-4, 1 - 1e-4)
    return mu, {"mu_inf": mu_inf, "phi_p": phi_p}


@dataclass(frozen=True)
class E3World:
    world_id: str
    geometry_id: str
    family: str
    c: float
    noise_sd: float
    grid_points: int
    replicate: int
    compounds: pd.DataFrame
    trajectories: pd.DataFrame
    true_g: np.ndarray
    law_params: dict
    response_params: dict
    compounds_seed: int
    law_seed: int
    response_seed: int


def build_world(family: str, c: float, noise_sd: float, grid_points: int, replicate: int) -> E3World:
    """One E3 world.

    Seeds derive from `geometry_id`, which deliberately excludes `c`: within
    a (family, noise, grid) cell, all five `c` levels share covariate,
    scale, and response-noise seeds across replicates (MURU_V2_IDENTIFIABILITY_
    STUDY_DESIGN.md section 3.4, control 3, "paired seeds"). For the
    mass_power control this makes all five `c` labels within a
    (noise, grid, replicate) triple byte-identical by construction, since
    mass_power's law does not consume `c` at all -- disclosed, not a defect;
    the 10,000-world count is the pre-registered Cartesian product and is
    generated exactly as declared.
    """
    geometry_id = f"E3|{family}|noise{noise_sd:g}|grid{grid_points}|r{replicate:03d}"
    world_id = f"V2C|E3|{family}|c{c:g}|noise{noise_sd:g}|grid{grid_points}|r{replicate:03d}"

    compounds, compounds_seed = synthetic_compounds_v2(geometry_id)

    law_seed = derive_seed_v2(geometry_id, "law")
    law_rng = np.random.default_rng(law_seed)
    g, law_params = law_v2(family, compounds, law_rng, c)

    response_seed = derive_seed_v2(geometry_id, "response")
    response_rng = np.random.default_rng(response_seed)
    energy_grid = energy_grid_for(grid_points)
    mu, response_params = response_v2(g, response_rng, energy_grid, noise_sd)

    rows = []
    for i, compound_id in enumerate(compounds["compound_id"]):
        for j, energy in enumerate(energy_grid):
            rows.append({"compound_id": compound_id, "energy": energy, "mu": float(mu[i, j])})
    trajectories = pd.DataFrame(rows)

    return E3World(
        world_id=world_id,
        geometry_id=geometry_id,
        family=family,
        c=c,
        noise_sd=noise_sd,
        grid_points=grid_points,
        replicate=replicate,
        compounds=compounds,
        trajectories=trajectories,
        true_g=g,
        law_params=law_params,
        response_params=response_params,
        compounds_seed=compounds_seed,
        law_seed=law_seed,
        response_seed=response_seed,
    )
