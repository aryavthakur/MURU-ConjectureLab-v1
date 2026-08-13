"""Fully synthetic prospective benchmark generation.

This module only depends on the paper benchmark registry and standard numerical
libraries.  It is deliberately independent of all historic and real-data code.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd

from .registry import ENERGY_GRID, iter_case_ids, resolve_case_id
from .truth import TruthRecord

GENERATOR_VERSION = "paper-benchmark-generator-1.0.0"
N_COMPOUNDS = 180
N_SCAFFOLDS = 30


@dataclass(frozen=True)
class CaseInputs:
    compounds: pd.DataFrame
    trajectories: pd.DataFrame

    def canonical_dict(self) -> dict[str, list[dict[str, object]]]:
        return {
            "compounds": self.compounds.sort_index(axis=1).sort_values("compound_id").to_dict("records"),
            "trajectories": self.trajectories.sort_index(axis=1).sort_values(["compound_id", "energy"]).to_dict("records"),
        }


@dataclass(frozen=True)
class GeneratedCase:
    case_id: str
    inputs: CaseInputs
    truth: TruthRecord
    content_hash: str


def derive_seed(*parts: str) -> int:
    payload = "paper-benchmark-v1|" + "|".join(parts)
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def _rng(case_id: str, stage: str) -> tuple[np.random.Generator, int]:
    seed = derive_seed(case_id, stage)
    return np.random.default_rng(seed), seed


def _synthetic_compounds(case_id: str) -> tuple[pd.DataFrame, dict[str, int]]:
    rng, seed = _rng(case_id, "compounds")
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


def _law(kind: str, compounds: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray | None, str | None, list[str], str | None, dict[str, float], dict[str, float]]:
    mass = compounds.mass.to_numpy()
    descriptor = compounds.descriptor.to_numpy()
    descriptor2 = compounds.descriptor2.to_numpy()
    scale, coefficient = float(rng.uniform(1.1, 1.8)), float(rng.uniform(0.25, 0.55))
    if kind in {"scalar_noiseless", "scalar_moderate", "scalar_strong", "missing_one_energy", "boundary_scale", "simple_descriptor", "irrelevant_distractors", "correlated_distractors", "equivalent_forms"}:
        return scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor), "mass_affine_descriptor", ["mass", "descriptor"], "sqrt(mass) * (1 + coefficient * descriptor)", {"scale": scale, "coefficient": coefficient}, {"mass": 0.5}
    if kind == "mass_only":
        exponent = float(rng.uniform(0.45, 0.75))
        return scale * (mass / 250.0) ** exponent, "mass_power", ["mass"], "scale * mass**exponent", {"scale": scale}, {"mass": exponent}
    if kind == "nonlinear_descriptor":
        return scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor / (1 + descriptor)), "mass_saturating_descriptor", ["mass", "descriptor"], "sqrt(mass) * (1 + coefficient * descriptor/(1+descriptor))", {"scale": scale, "coefficient": coefficient}, {"mass": 0.5}
    if kind == "interaction":
        return scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor * descriptor2), "mass_interaction", ["mass", "interaction_left", "interaction_right"], "sqrt(mass) * (1 + coefficient * descriptor * descriptor2)", {"scale": scale, "coefficient": coefficient}, {"mass": 0.5}
    if kind == "difficult_algebra":
        return scale * np.sqrt(mass / 250.0) * np.exp(coefficient * descriptor / 3), "mass_exponential_descriptor", ["mass", "descriptor"], "sqrt(mass) * exp(coefficient * descriptor / 3)", {"scale": scale, "coefficient": coefficient}, {"mass": 0.5}
    if kind == "descriptor_link_permutation":
        return scale * np.exp(rng.normal(0, 0.25, len(compounds))), None, [], None, {"scale": scale}, {}
    if kind == "mass_preserving_null":
        exponent = float(rng.uniform(0.45, 0.75))
        return scale * (mass / 250.0) ** exponent, "mass_power", ["mass"], "scale * mass**exponent", {"scale": scale}, {"mass": exponent}
    return None, None, [], None, {}, {}


def _response_matrix(kind: str, g: np.ndarray | None, compounds: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, dict[str, float | str], dict[str, float | str], dict[str, float], str]:
    energy = np.asarray(ENERGY_GRID, dtype=float)
    mu_inf, phi_p = float(rng.uniform(0.15, 0.30)), float(rng.uniform(1.20, 1.70))
    if g is None:
        g = 1.4 * np.exp(rng.normal(0, 0.28, len(compounds)))
    u = (energy[None, :] / 45.0) / g[:, None]
    mu = mu_inf + (1 - mu_inf) * np.exp(-(u**phi_p))
    adequacy = "M0"
    if kind in {"no_scalar", "m1_horizontal"}:
        shape = 1 + 0.45 * np.tanh(compounds.descriptor.to_numpy())
        mu = mu_inf + (1 - mu_inf) * np.exp(-(u**(phi_p * shape[:, None])))
        adequacy = "M1"
    elif kind == "m2_high_energy":
        floor = np.clip(mu_inf + 0.18 * (compounds.descriptor.to_numpy() - 0.5), 0.03, 0.55)
        mu = floor[:, None] + (1 - floor[:, None]) * np.exp(-(u**phi_p))
        adequacy = "M2"
    elif kind == "m3_low_energy":
        ceiling = np.clip(1 - 0.22 * compounds.descriptor.to_numpy(), 0.6, 0.99)
        mu = mu_inf + (ceiling[:, None] - mu_inf) * np.exp(-(u**phi_p))
        adequacy = "M3"
    elif kind == "combined_violation":
        shape = 1 + 0.15 * np.tanh(compounds.descriptor.to_numpy())
        floor = np.clip(mu_inf + 0.05 * (compounds.descriptor2.to_numpy() - 0.5), 0.03, 0.55)
        mu = floor[:, None] + (1 - floor[:, None]) * np.exp(-(u**(phi_p * shape[:, None])))
        adequacy = "M1+M2+M3"
    elif kind == "response_cell_resampling":
        mu = rng.uniform(0.08, 0.95, mu.shape)
        adequacy = "not_applicable"
    elif kind in {"latent_driver", "measurement_coupling", "out_of_grammar"}:
        driver = rng.normal(0, 1, len(compounds))
        if kind == "measurement_coupling":
            driver = (compounds.mass.to_numpy() - compounds.mass.mean()) / compounds.mass.std()
        if kind == "out_of_grammar":
            driver = np.sin(compounds.mass.to_numpy() / 47.0)
        mu = np.clip(mu + 0.12 * np.tanh(driver)[:, None] * (energy[None, :] / energy.max()), 1e-4, 1 - 1e-4)
        adequacy = "not_applicable"
    noise_sd = {"scalar_noiseless": 0.0, "scalar_moderate": 0.0295, "scalar_strong": 0.06}.get(kind, 0.02)
    if noise_sd:
        mu = mu + rng.normal(0, noise_sd, mu.shape)
    mu = np.clip(mu, 1e-4, 1 - 1e-4)
    missingness: dict[str, float | str] = {"mechanism": "none", "rate": 0.0}
    if kind == "missing_one_energy":
        missingness = {"mechanism": "one_energy_per_compound", "rate": 1 / len(energy)}
    return mu, {"mechanism": "additive_gaussian", "sd": noise_sd}, missingness, {"mu_inf": mu_inf, "phi_p": phi_p}, adequacy


def generate_case(case_id: str) -> GeneratedCase:
    family, variant, _ = resolve_case_id(case_id)
    compounds, seeds = _synthetic_compounds(case_id)
    law_rng, law_seed = _rng(case_id, "law")
    response_rng, response_seed = _rng(case_id, "response")
    g, mathematical_family, active, relationship, coefficients, exponents = _law(variant.generative_kind, compounds, law_rng)
    mu, noise, missingness, phi, generated_adequacy = _response_matrix(variant.generative_kind, g, compounds, response_rng)
    rows: list[dict[str, object]] = []
    for i, compound_id in enumerate(compounds.compound_id):
        omitted = (i + derive_seed(case_id, "missing")) % len(ENERGY_GRID) if missingness["mechanism"] != "none" else None
        for j, energy in enumerate(ENERGY_GRID):
            if j == omitted:
                continue
            rows.append({"compound_id": compound_id, "energy": energy, "mu": float(mu[i, j])})
    trajectories = pd.DataFrame(rows)
    seeds.update({"law": law_seed, "response": response_seed, "missingness": derive_seed(case_id, "missing")})
    truth = TruthRecord(
        case_id=case_id,
        partition=case_id.split("|")[1],
        family=family.code,
        variant=variant.code,
        seeds=seeds,
        phi={"family": "stretched_exponential", **phi},
        g_definition=relationship,
        g_by_compound={} if not variant.scalar_truth_defined or g is None else {key: float(value) for key, value in zip(compounds.compound_id, g)},
        descriptor_relationship=relationship,
        active_variables=active,
        mathematical_family=mathematical_family,
        coefficients=coefficients,
        exponents=exponents,
        noise=noise,
        missingness=missingness,
        scalar_truth_defined=variant.scalar_truth_defined,
        m0_adequacy_truth=variant.m0_adequacy_truth if variant.m0_adequacy_truth != "M0" else generated_adequacy,
        symbolic_truth_kind=variant.symbolic_truth_kind,
        applicable_endpoints=sorted(variant.endpoint_names),
        expected_behavior=variant.expected_behavior,
    )
    inputs = CaseInputs(compounds=compounds, trajectories=trajectories)
    payload = {"inputs": inputs.canonical_dict(), "truth": truth.to_dict(), "generator_version": GENERATOR_VERSION}
    content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return GeneratedCase(case_id=case_id, inputs=inputs, truth=truth, content_hash=content_hash)


def generate_partition(partition: str) -> Iterator[GeneratedCase]:
    for case_id in iter_case_ids(partition):
        yield generate_case(case_id)
