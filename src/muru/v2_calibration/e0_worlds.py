"""E0 world construction: the v1 generator arithmetic with two injected knobs.

The only two things E0 is permitted to vary on the generator side are the seed
payload prefix (so the worlds live in the `V2C` namespace) and the **response
ceiling** (factor 1 of the design's 3 x 3).  Everything else -- the covariate
construction, the affine law, the M0 response, the noise draw, and the order in
which every one of those consumes its generator -- is the frozen v1 arithmetic,
transcribed line for line from `paper_benchmark/generator.py`.

That transcription is not trusted on inspection.  `build_case_inputs` is written
so that driving it with the benchmark's own seed function and the benchmark's
own ceiling must reproduce `generator.generate_case` exactly;
`tests/test_e0_generator_identity.py` asserts that on real v1 case ids and fails
closed on any drift.

The two-stage split below is structural, not stylistic.  :func:`draw_base`
consumes every random draw and takes **no cell argument**, and :func:`render`
applies a ceiling and consumes **no randomness at all**.  The design's
requirement that all nine cells share covariates, `mu_inf`, `phi_p`, `g` and the
noise draws is therefore a property of the call graph rather than a promise.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from muru.paper_benchmark.generator import N_COMPOUNDS, N_SCAFFOLDS
from muru.paper_benchmark.registry import ENERGY_GRID

__all__ = [
    "E0_LAW_KIND",
    "E0_NOISE_SD",
    "RESPONSE_FLOOR_CLIP",
    "BaseDraw",
    "RenderedWorld",
    "build_case_inputs",
    "draw_base",
    "render",
    "world_content_hash",
]

#: `MURU_V2_E0_PROTOCOL.md` section 2: the modal v1 true-M0 generative cell.
#: The `mass_affine_descriptor` law branch of `generator._law`, shared verbatim
#: by v1 variants F05, F08, F11, F12 and F17.
E0_LAW_KIND = "mass_affine_descriptor"

#: `generator._response_matrix`'s default response noise, carried by every G1
#: variant that is not `scalar_noiseless` / `scalar_moderate` / `scalar_strong`.
E0_NOISE_SD = 0.02

#: The lower half of the v1 two-sided clip.  E0 manipulates the **ceiling**;
#: this floor is held at the v1 value wherever a clip is applied at all, and
#: every activation of it is counted so that the claim "the manipulation is
#: purely on the ceiling" is measured rather than assumed.
RESPONSE_FLOOR_CLIP = 1e-4


@dataclass(frozen=True)
class BaseDraw:
    """Everything random about one replicate, drawn once and shared by all cells."""

    replicate: int
    compounds: pd.DataFrame
    energies: np.ndarray
    g: np.ndarray
    mu_inf: float
    phi_p: float
    scale: float
    coefficient: float
    noise: np.ndarray
    mu_preclip: np.ndarray
    seeds: dict[str, int]

    def draw_fingerprint(self) -> str:
        """A hash of the shared random content, cell-independent by construction.

        Used to prove that the nine cells of a replicate really did receive the
        same draws, rather than merely being intended to.
        """
        payload = {
            "compounds": self.compounds.sort_index(axis=1).sort_values("compound_id").to_dict("records"),
            "energies": [float(e) for e in self.energies],
            "g": [float(v) for v in self.g],
            "mu_inf": float(self.mu_inf),
            "phi_p": float(self.phi_p),
            "scale": float(self.scale),
            "coefficient": float(self.coefficient),
            "noise": [float(v) for v in self.noise.ravel()],
            "mu_preclip": [float(v) for v in self.mu_preclip.ravel()],
            "seeds": dict(self.seeds),
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RenderedWorld:
    """One replicate rendered at one generator-clip level."""

    world_id: str
    cell_id: str
    replicate: int
    response_ceiling: float | None
    compounds: pd.DataFrame
    trajectories: pd.DataFrame
    mu: np.ndarray
    ceiling_clip_activations: int
    floor_clip_activations: int
    base_fingerprint: str
    content_hash: str


def build_case_inputs(
    seed_for: Callable[[str], int],
    response_ceiling: float | None,
    *,
    noise_sd: float = E0_NOISE_SD,
    response_floor: float | None = RESPONSE_FLOOR_CLIP,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """The v1 generator's affine-law true-M0 path, with the ceiling injected.

    ``seed_for(stage)`` supplies the integer seed for each of the generator's
    three stages, in the generator's own order: ``compounds``, ``law``,
    ``response``.  Passing ``lambda stage: generator.derive_seed(case_id, stage)``
    and ``response_ceiling=1 - 1e-4`` reproduces ``generator.generate_case`` for
    any affine-law true-M0 case exactly; that is the identity test's contract.

    ``response_ceiling=None`` applies no clip at all -- neither the ceiling nor
    the floor -- which is the design's "no clip" level.
    """
    # --- generator._synthetic_compounds, transcribed -----------------------
    rng = np.random.default_rng(seed_for("compounds"))
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
    compounds = pd.DataFrame({
        "compound_id": [f"C{i:03d}" for i in range(N_COMPOUNDS)],
        "scaffold_id": [f"S{i:02d}" for i in scaffold],
        "split": split_by_group[scaffold],
        "mass": mass,
        "descriptor": descriptor,
        "descriptor2": descriptor2,
        "distractor": distractor,
        "correlated_distractor": correlated,
    })

    # --- generator._law, mass_affine_descriptor branch, transcribed --------
    law_rng = np.random.default_rng(seed_for("law"))
    scale, coefficient = float(law_rng.uniform(1.1, 1.8)), float(law_rng.uniform(0.25, 0.55))
    g = scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor)

    # --- generator._response_matrix, shared M0 branch, transcribed ---------
    response_rng = np.random.default_rng(seed_for("response"))
    energy = np.asarray(ENERGY_GRID, dtype=float)
    mu_inf, phi_p = float(response_rng.uniform(0.15, 0.30)), float(response_rng.uniform(1.20, 1.70))
    u = (energy[None, :] / 45.0) / g[:, None]
    mu = mu_inf + (1 - mu_inf) * np.exp(-(u**phi_p))
    noise = response_rng.normal(0, noise_sd, mu.shape) if noise_sd else np.zeros_like(mu)
    mu_preclip = mu + noise

    # --- the one injected knob: generator.py line 221 ----------------------
    if response_ceiling is None:
        mu_out = mu_preclip.copy()
        ceiling_hits = floor_hits = 0
    else:
        lower = RESPONSE_FLOOR_CLIP if response_floor is None else response_floor
        mu_out = np.clip(mu_preclip, lower, response_ceiling)
        ceiling_hits = int(np.count_nonzero(mu_preclip > response_ceiling))
        floor_hits = int(np.count_nonzero(mu_preclip < lower))

    rows: list[dict[str, object]] = []
    for i, compound_id in enumerate(compounds.compound_id):
        for j, energy_value in enumerate(ENERGY_GRID):
            rows.append({"compound_id": compound_id, "energy": energy_value, "mu": float(mu_out[i, j])})
    trajectories = pd.DataFrame(rows)

    diagnostics: dict[str, object] = {
        "energies": energy,
        "g": g,
        "mu_inf": mu_inf,
        "phi_p": phi_p,
        "scale": scale,
        "coefficient": coefficient,
        "noise": noise,
        "mu_preclip": mu_preclip,
        "mu": mu_out,
        "ceiling_clip_activations": ceiling_hits,
        "floor_clip_activations": floor_hits,
    }
    return compounds, trajectories, diagnostics


def draw_base(replicate: int, seed_for: Callable[[int, str], int]) -> BaseDraw:
    """Consume every random draw for one replicate.  Takes no cell argument."""
    compounds, _, diag = build_case_inputs(
        lambda stage: seed_for(replicate, stage), response_ceiling=None
    )
    return BaseDraw(
        replicate=replicate,
        compounds=compounds,
        energies=diag["energies"],
        g=diag["g"],
        mu_inf=float(diag["mu_inf"]),
        phi_p=float(diag["phi_p"]),
        scale=float(diag["scale"]),
        coefficient=float(diag["coefficient"]),
        noise=diag["noise"],
        mu_preclip=diag["mu_preclip"],
        seeds={stage: seed_for(replicate, stage) for stage in ("compounds", "law", "response")},
    )


def render(base: BaseDraw, cell_id: str, world_id: str, response_ceiling: float | None) -> RenderedWorld:
    """Apply one generator-clip level.  Consumes no randomness."""
    if response_ceiling is None:
        mu_out = base.mu_preclip.copy()
        ceiling_hits = floor_hits = 0
    else:
        mu_out = np.clip(base.mu_preclip, RESPONSE_FLOOR_CLIP, response_ceiling)
        ceiling_hits = int(np.count_nonzero(base.mu_preclip > response_ceiling))
        floor_hits = int(np.count_nonzero(base.mu_preclip < RESPONSE_FLOOR_CLIP))

    rows: list[dict[str, object]] = []
    for i, compound_id in enumerate(base.compounds.compound_id):
        for j, energy_value in enumerate(ENERGY_GRID):
            rows.append({"compound_id": compound_id, "energy": energy_value, "mu": float(mu_out[i, j])})
    trajectories = pd.DataFrame(rows)

    return RenderedWorld(
        world_id=world_id,
        cell_id=cell_id,
        replicate=base.replicate,
        response_ceiling=response_ceiling,
        compounds=base.compounds,
        trajectories=trajectories,
        mu=mu_out,
        ceiling_clip_activations=ceiling_hits,
        floor_clip_activations=floor_hits,
        base_fingerprint=base.draw_fingerprint(),
        content_hash=world_content_hash(base.compounds, trajectories, world_id),
    )


def world_content_hash(compounds: pd.DataFrame, trajectories: pd.DataFrame, world_id: str) -> str:
    """SHA-256 over the world's canonical inputs, in the v2 namespace."""
    payload = {
        "world_id": world_id,
        "namespace": "muru-v2-calibration",
        "compounds": compounds.sort_index(axis=1).sort_values("compound_id").to_dict("records"),
        "trajectories": trajectories.sort_index(axis=1).sort_values(["compound_id", "energy"]).to_dict("records"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
