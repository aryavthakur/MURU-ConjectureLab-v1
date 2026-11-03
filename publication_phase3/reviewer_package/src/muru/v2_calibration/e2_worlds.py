"""E2a fresh V2C world construction.

Per `v2_design_reference/MURU_V2_E2_PREDECLARATION.md`. The covariate
construction and the M0 response mechanism are `generator.py`'s
`_synthetic_compounds` / `_law` / `_response_matrix` transcribed line for
line (same discipline `e0_worlds.py` used), varying only three things:

1. the seed payload prefix (`"muru-v2-calibration|"` instead of
   `"paper-benchmark-v1|"`, so no V2C world's construction seed can collide
   with any benchmark case's -- checked, not assumed, by
   `assert_seed_namespace_disjoint`);
2. `coefficient`, which the frozen law draws from `rng.uniform(0.25, 0.55)`,
   is instead fixed to one of three regime values (E2a's own controlled
   factor -- the entire reason this world set exists);
3. `noise_sd`, which the frozen response matrix keys off the case `kind`
   string, is instead fixed directly to one of three levels.

Everything else -- 180 compounds, 30 scaffold groups, the 20/5/5-per-group
train/validation/test split, the latent-scaffold covariate draw, `mu_inf`,
`phi_p`, the M0 profile shape, the `[1e-4, 1-1e-4]` response clip -- is the
identical arithmetic, identical call order, against a `numpy.random.Generator`
seeded the same way (via SHA-256 of a string payload). `tests/test_e2_worlds.py`
proves this by an executable identity check, not by inspection.

Nothing here reads planted truth for scoring purposes; the truth this module
returns alongside each world (`WorldTruth`) is consumed only by the
downstream, search-blind scoring pass in `e2_scoring.py`, exactly as
`generator.py`'s own `TruthRecord` is never read during acceptance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np
import pandas as pd

from muru.paper_benchmark.generator import N_COMPOUNDS, N_SCAFFOLDS
from muru.paper_benchmark.registry import ENERGY_GRID

__all__ = [
    "FAMILIES", "REGIMES", "COEFFICIENT_BY_REGIME", "NOISE_LEVELS",
    "NOISE_SD_BY_LEVEL", "N_REPLICATES", "N_WORLDS",
    "SEED_NAMESPACE_PREFIX", "TRUTH_SUPPORT_BY_FAMILY",
    "derive_seed_v2", "cell_id", "world_id", "world_ordinal",
    "iter_cells", "iter_worlds",
    "WorldTruth", "WorldContent",
    "build_world", "assert_seed_namespace_disjoint",
]

# ---------------------------------------------------------------------------
# E2a factor levels -- see MURU_V2_E2_PREDECLARATION.md sections 2-4.
# ---------------------------------------------------------------------------

#: generator._law's own dispatch order (mass_affine_descriptor first, then
#: mass_power, mass_saturating_descriptor, mass_interaction,
#: mass_exponential_descriptor).
FAMILIES: tuple[str, ...] = (
    "mass_affine_descriptor",
    "mass_power",
    "mass_saturating_descriptor",
    "mass_interaction",
    "mass_exponential_descriptor",
)

REGIMES: tuple[str, ...] = ("low", "mid", "high")
#: The frozen U(0.25, 0.55) support's own two endpoints and midpoint.
COEFFICIENT_BY_REGIME: dict[str, float] = {"low": 0.25, "mid": 0.40, "high": 0.55}

NOISE_LEVELS: tuple[str, ...] = ("noiseless", "default", "strong")
#: {0.0, 0.02, 0.06}: the three noise_sd values already literal in
#: generator._response_matrix's own dict that are not scalar_moderate's
#: family-specific 0.0295 -- and identical to E1's own noise-level list.
NOISE_SD_BY_LEVEL: dict[str, float] = {"noiseless": 0.0, "default": 0.02, "strong": 0.06}

N_REPLICATES = 12
N_WORLDS = len(FAMILIES) * len(REGIMES) * len(NOISE_LEVELS) * N_REPLICATES
assert N_WORLDS == 540

#: generator.py's active_variables label -> GRAMMAR_PRIMITIVES support set,
#: mechanically read off `_law`'s own return values (mass_interaction's
#: "interaction_left"/"interaction_right" block labels map onto
#: descriptor/descriptor2 exactly as g2_contract._BLOCK_LABEL_TO_PRIMITIVE
#: does for the real benchmark).
TRUTH_SUPPORT_BY_FAMILY: dict[str, frozenset[str]] = {
    "mass_affine_descriptor": frozenset({"mass", "descriptor"}),
    "mass_power": frozenset({"mass"}),
    "mass_saturating_descriptor": frozenset({"mass", "descriptor"}),
    "mass_interaction": frozenset({"mass", "descriptor", "descriptor2"}),
    "mass_exponential_descriptor": frozenset({"mass", "descriptor"}),
}

#: Disjoint from generator.derive_seed's "paper-benchmark-v1|" namespace,
#: per MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md section 2.2.
SEED_NAMESPACE_PREFIX = "muru-v2-calibration|"


def derive_seed_v2(*parts: str) -> int:
    payload = SEED_NAMESPACE_PREFIX + "|".join(parts)
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def assert_seed_namespace_disjoint() -> None:
    """The two prefixes cannot produce the same hash input for any parts
    tuple, because one is a strict, non-overlapping-in-content prefix of
    neither the other (checked structurally, not just "looks different")."""
    from muru.paper_benchmark.generator import derive_seed as derive_seed_v1

    v1_prefix = "paper-benchmark-v1|"
    v2_prefix = SEED_NAMESPACE_PREFIX
    if v1_prefix == v2_prefix:
        raise AssertionError("v1 and v2 seed namespace prefixes are identical")
    if v1_prefix.startswith(v2_prefix) or v2_prefix.startswith(v1_prefix):
        raise AssertionError("v1/v2 seed namespace prefixes are not mutually unambiguous")
    # Spot-check: no (v1 case_id-shaped, stage) pair collides with any
    # (v2 world_id-shaped, stage) pair over a real sample.
    probe_stages = ("compounds", "law", "response")
    v1_ids = [f"PB|development|F01_mass_affine_descriptor|v01|r{i:02d}" for i in range(5)]
    v2_ids = [world_id(*args) for args in list(iter_worlds())[:5]]
    v1_seeds = {derive_seed_v1(cid, stage) for cid in v1_ids for stage in probe_stages}
    v2_seeds = {derive_seed_v2(wid, stage) for wid in v2_ids for stage in probe_stages}
    overlap = v1_seeds & v2_seeds
    if overlap:
        raise AssertionError(f"v1/v2 world-content seed collision on spot check: {overlap}")


def cell_id(family: str, regime: str, noise: str) -> str:
    return f"{family}|c_{regime}|n_{noise}"


def world_id(family: str, regime: str, noise: str, replicate: int) -> str:
    return f"V2C|E2|{cell_id(family, regime, noise)}|r{replicate:03d}"


def world_ordinal(family: str, regime: str, noise: str, replicate: int) -> int:
    fi, ri, ni = FAMILIES.index(family), REGIMES.index(regime), NOISE_LEVELS.index(noise)
    if not (0 <= replicate < N_REPLICATES):
        raise ValueError(f"replicate {replicate} outside [0, {N_REPLICATES})")
    return ((fi * len(REGIMES) + ri) * len(NOISE_LEVELS) + ni) * N_REPLICATES + replicate


def iter_cells() -> Iterator[tuple[str, str, str]]:
    for family in FAMILIES:
        for regime in REGIMES:
            for noise in NOISE_LEVELS:
                yield family, regime, noise


def iter_worlds() -> Iterator[tuple[str, str, str, int]]:
    for family, regime, noise in iter_cells():
        for replicate in range(N_REPLICATES):
            yield family, regime, noise, replicate


def _rng_v2(wid: str, stage: str) -> tuple[np.random.Generator, int]:
    seed = derive_seed_v2(wid, stage)
    return np.random.default_rng(seed), seed


# ---------------------------------------------------------------------------
# Transcribed verbatim from generator.py, with only the seed source changed.
# ---------------------------------------------------------------------------

def _synthetic_compounds_v2(wid: str) -> tuple[pd.DataFrame, dict[str, int]]:
    rng, seed = _rng_v2(wid, "compounds")
    scaffold = np.repeat(np.arange(N_SCAFFOLDS), N_COMPOUNDS // N_SCAFFOLDS)
    split_by_group = np.array(["train"] * 20 + ["validation"] * 5 + ["test"] * 5)
    group_latent = rng.normal(0, 1, N_SCAFFOLDS)
    latent = group_latent[scaffold] + rng.normal(0, 0.35, N_COMPOUNDS)
    mass = np.exp(5.55 + 0.25 * latent + rng.normal(0, 0.18, N_COMPOUNDS))
    descriptor = (latent + rng.normal(0, 0.45, N_COMPOUNDS) - latent.min())
    descriptor /= descriptor.max()
    descriptor2 = (0.65 * latent + rng.normal(0, 0.65, N_COMPOUNDS))
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
    return frame, {"compounds": seed}


def _law_v2(
    family: str, coefficient_value: float, compounds: pd.DataFrame, rng: np.random.Generator,
) -> tuple[np.ndarray, list[str], dict[str, float], str]:
    """generator.py::_law, restructured to dispatch on family name directly
    and to accept `coefficient` as a controlled input rather than a draw.

    The unconditional `scale, coefficient = rng.uniform(1.1, 1.8),
    rng.uniform(0.25, 0.55)` draw at the top of the real `_law` is preserved
    exactly (same two calls, same order), so every family's RNG stream
    consumes identically to the real generator up to this point; only the
    *use* of the drawn `coefficient` is replaced by `coefficient_value` for
    the four descriptor-bearing families. `mass_power` never uses
    `coefficient` in the real generator either, so this substitution is a
    true no-op for it (MURU_V2_E2_PREDECLARATION.md section 2).
    """
    mass = compounds.mass.to_numpy()
    descriptor = compounds.descriptor.to_numpy()
    descriptor2 = compounds.descriptor2.to_numpy()
    scale, _drawn_coefficient = float(rng.uniform(1.1, 1.8)), float(rng.uniform(0.25, 0.55))
    coefficient = float(coefficient_value)

    if family == "mass_affine_descriptor":
        g = scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor)
        law_str = f"{scale!r} * sqrt(mass / 250.0) * (1 + {coefficient!r} * descriptor)"
        return g, ["mass", "descriptor"], {"scale": scale, "coefficient": coefficient}, law_str

    if family == "mass_power":
        exponent = float(rng.uniform(0.45, 0.75))
        g = scale * (mass / 250.0) ** exponent
        law_str = f"{scale!r} * (mass / 250.0) ** {exponent!r}"
        return g, ["mass"], {"scale": scale, "exponent": exponent}, law_str

    if family == "mass_saturating_descriptor":
        g = scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor / (1 + descriptor))
        law_str = (
            f"{scale!r} * sqrt(mass / 250.0) * "
            f"(1 + {coefficient!r} * descriptor / (1 + descriptor))"
        )
        return g, ["mass", "descriptor"], {"scale": scale, "coefficient": coefficient}, law_str

    if family == "mass_interaction":
        g = scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor * descriptor2)
        law_str = (
            f"{scale!r} * sqrt(mass / 250.0) * "
            f"(1 + {coefficient!r} * descriptor * descriptor2)"
        )
        return (
            g, ["mass", "descriptor", "descriptor2"],
            {"scale": scale, "coefficient": coefficient}, law_str,
        )

    if family == "mass_exponential_descriptor":
        g = scale * np.sqrt(mass / 250.0) * np.exp(coefficient * descriptor / 3)
        law_str = f"{scale!r} * sqrt(mass / 250.0) * exp({coefficient!r} * descriptor / 3)"
        return g, ["mass", "descriptor"], {"scale": scale, "coefficient": coefficient}, law_str

    raise ValueError(f"unknown E2a family {family!r}")


def _response_matrix_v2(
    g: np.ndarray, noise_sd: float, rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, float]]:
    """generator.py::_response_matrix's plain-M0 branch, transcribed exactly.

    No adequacy violation is planted (E2 is not an A1 study) and no
    missingness mechanism is applied (row filtering: none, matching
    rc5_estimate's own "Row filtering: none" binding).
    """
    energy = np.asarray(ENERGY_GRID, dtype=float)
    mu_inf, phi_p = float(rng.uniform(0.15, 0.30)), float(rng.uniform(1.20, 1.70))
    u = (energy[None, :] / 45.0) / g[:, None]
    mu = mu_inf + (1 - mu_inf) * np.exp(-(u ** phi_p))
    if noise_sd:
        mu = mu + rng.normal(0, noise_sd, mu.shape)
    mu = np.clip(mu, 1e-4, 1 - 1e-4)
    return mu, {"mu_inf": mu_inf, "phi_p": phi_p}


# ---------------------------------------------------------------------------
# Public world content
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorldTruth:
    family: str
    regime: str
    noise_level: str
    coefficient: float
    noise_sd: float
    active_variables: tuple[str, ...]
    support: frozenset[str]
    coefficients: dict[str, float]
    law_string: str          # concrete, sympy-parseable: g as a function of the primitives


@dataclass(frozen=True)
class WorldContent:
    world_id: str
    cell_id: str
    replicate: int
    world_ordinal: int
    compounds: pd.DataFrame
    trajectories: pd.DataFrame
    truth: WorldTruth
    seeds: dict[str, int]
    content_hash: str


def _canonical_dict(compounds: pd.DataFrame, trajectories: pd.DataFrame) -> dict:
    return {
        "compounds": compounds.sort_index(axis=1).sort_values("compound_id").to_dict("records"),
        "trajectories": trajectories.sort_index(axis=1).sort_values(["compound_id", "energy"]).to_dict("records"),
    }


def build_world(family: str, regime: str, noise: str, replicate: int) -> WorldContent:
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}")
    if regime not in REGIMES:
        raise ValueError(f"unknown regime {regime!r}")
    if noise not in NOISE_LEVELS:
        raise ValueError(f"unknown noise level {noise!r}")

    wid = world_id(family, regime, noise, replicate)
    compounds, seeds = _synthetic_compounds_v2(wid)
    law_rng, law_seed = _rng_v2(wid, "law")
    response_rng, response_seed = _rng_v2(wid, "response")

    coefficient_value = COEFFICIENT_BY_REGIME[regime]
    noise_sd = NOISE_SD_BY_LEVEL[noise]

    g, active_variables, coefficients, law_str = _law_v2(family, coefficient_value, compounds, law_rng)
    mu, phi = _response_matrix_v2(g, noise_sd, response_rng)

    rows: list[dict[str, object]] = []
    for i, compound_id in enumerate(compounds.compound_id):
        for j, energy in enumerate(ENERGY_GRID):
            rows.append({"compound_id": compound_id, "energy": energy, "mu": float(mu[i, j])})
    trajectories = pd.DataFrame(rows)

    seeds.update({"law": law_seed, "response": response_seed})

    truth = WorldTruth(
        family=family, regime=regime, noise_level=noise,
        coefficient=coefficient_value, noise_sd=noise_sd,
        active_variables=tuple(active_variables),
        support=TRUTH_SUPPORT_BY_FAMILY[family],
        coefficients=coefficients, law_string=law_str,
    )

    payload = {
        "world_id": wid,
        "inputs": _canonical_dict(compounds, trajectories),
        "truth": {
            "family": family, "regime": regime, "noise_level": noise,
            "coefficients": coefficients, "law_string": law_str,
        },
        "generator_transcription_version": "e2-worlds-1.0.0",
    }
    content_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return WorldContent(
        world_id=wid, cell_id=cell_id(family, regime, noise), replicate=replicate,
        world_ordinal=world_ordinal(family, regime, noise, replicate),
        compounds=compounds, trajectories=trajectories, truth=truth,
        seeds=seeds, content_hash=content_hash,
    )
