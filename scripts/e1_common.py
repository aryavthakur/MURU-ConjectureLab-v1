"""E1 (A1_JOINT_EVALUABILITY_POWER): world generation.

New code, written for this experiment only. Reads and calls the frozen
production module ``generator`` (``combined_response``, the amplitude
constants) but modifies none of it on disk. See ``MURU_V2_E1_PROTOCOL.md``
Sec 2-3 for the derivation of every formula and seed below.

Seed namespace disjoint from v1 and from E0: parts are prefixed ``"E1"``
under the same V2C seed function E0 used.
"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(os.path.dirname(_THIS_DIR), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from muru.paper_benchmark import adequacy  # noqa: E402
from muru.paper_benchmark import generator  # noqa: E402
from muru.paper_benchmark import rc5_adequacy  # noqa: E402
from muru.paper_benchmark import registry  # noqa: E402

assert "pysr" not in sys.modules, "E1 must never import PySR"

ENERGY_GRID = tuple(float(e) for e in registry.ENERGY_GRID)
N_COMPOUNDS = 180
N_SCAFFOLDS = 30
E_REF = adequacy.E_REF
MU_FLOOR = adequacy.MU_FLOOR
V1_MU_CEIL_DEFAULT = adequacy.MU_CEIL

SEED_NAMESPACE_PREFIX = "muru-v2-calibration|"


def derive_seed(*parts: str) -> int:
    payload = SEED_NAMESPACE_PREFIX + "|".join(parts)
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


# --------------------------------------------------------------------------
# Design grid (MURU_V2_E1_PROTOCOL.md Sec 1-4)
# --------------------------------------------------------------------------
D_TYPES = ("M1", "M2", "M3", "M1M2M3")  # non-null deviation types
ALPHA_LEVELS = (0.25, 0.5, 1.0, 2.0)
NOISE_LEVELS = (0.0, 0.02, 0.06)
MU_CEIL_LEVELS = {
    "c1e4": 1.0 - 1e-4,
    "c1e3": 1.0 - 1e-3,
    "copen": 1.0 + 1e-2,
}
N_REPLICATES = 75
N_CALIBRATE = 60
N_CONFIRM = 15

# Amplitude constants read by reference from the frozen generator module,
# not retyped as new literals.
M1_AMPLITUDE = generator.M1_HORIZONTAL_AMPLITUDE
M2_AMPLITUDE = generator.M2_HIGH_ENERGY_AMPLITUDE
M3_AMPLITUDE = generator.M3_LOW_ENERGY_AMPLITUDE
M3_CEILING_CLIP = generator.M3_CEILING_CLIP
COMBINED_M1_AMPLITUDE = generator.COMBINED_M1_AMPLITUDE
COMBINED_M2_AMPLITUDE = generator.COMBINED_M2_AMPLITUDE
COMBINED_M3_AMPLITUDE = generator.COMBINED_M3_AMPLITUDE


def noise_token(noise: float) -> str:
    return f"n{noise:.2f}".replace(".", "")


_SPLIT_ASSIGNMENT_CACHE: dict[float, set[int]] = {}


def confirm_replicate_set(noise_level: float, n_replicates: int = N_REPLICATES) -> set[int]:
    """Exactly the CONFIRM-assigned replicate indices for one noise level.

    Design Sec 3.7 / E1_PROTOCOL.md Sec 3-4 require an *exact* 60/15 split per
    cell, not merely an expected 80/20 rate, so this is a seeded permutation
    (dedicated seed, independent of D/alpha/mu_ceil_level), not a per-replicate
    Bernoulli draw.
    """
    key = (noise_level, n_replicates)
    if key in _SPLIT_ASSIGNMENT_CACHE:
        return _SPLIT_ASSIGNMENT_CACHE[key]
    n_confirm = round(n_replicates * 0.20)
    seed = derive_seed("E1", noise_token(noise_level), "split_assignment")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n_replicates)
    confirm_set = set(int(i) for i in perm[:n_confirm])
    _SPLIT_ASSIGNMENT_CACHE[key] = confirm_set
    return confirm_set


def split_for(noise_level: float, replicate: int, n_replicates: int = N_REPLICATES) -> str:
    return "CONFIRM" if replicate in confirm_replicate_set(noise_level, n_replicates) else "CALIBRATE"


def alpha_token(alpha: float) -> str:
    return f"a{round(alpha * 100):03d}"


def design_cells() -> list[dict]:
    """The 51 (D, alpha, noise) design cells (MURU_V2_A1_STUDY_DESIGN.md Sec 3.2)."""
    cells = []
    for noise in NOISE_LEVELS:
        cells.append({"D": "M0", "alpha": 0.0, "noise": noise, "is_null": True})
        for d in D_TYPES:
            for alpha in ALPHA_LEVELS:
                cells.append({"D": d, "alpha": alpha, "noise": noise, "is_null": False})
    assert len(cells) == 51, len(cells)
    return cells


def full_grid_cells() -> list[dict]:
    """The 153 (D, alpha, noise, mu_ceil_level) fit-unit cells (E1_PROTOCOL Sec 1)."""
    out = []
    for base in design_cells():
        for mc_level in MU_CEIL_LEVELS:
            row = dict(base)
            row["mu_ceil_level"] = mc_level
            row["mu_ceil_value"] = MU_CEIL_LEVELS[mc_level]
            row["cell_id"] = (
                f"{base['D']}_{alpha_token(base['alpha'])}_{noise_token(base['noise'])}_{mc_level}"
            )
            out.append(row)
    assert len(out) == 153, len(out)
    return out


def build_world_manifest(n_replicates: int = N_REPLICATES) -> pd.DataFrame:
    """153 cells x n_replicates fit-unit index rows. No random draw here."""
    rows = []
    for cell in full_grid_cells():
        for r in range(n_replicates):
            split = split_for(cell["noise"], r, n_replicates)
            world_id = f"V2C|E1|{cell['cell_id']}|r{r:03d}"
            rows.append(
                {
                    "world_id": world_id,
                    "cell_id": cell["cell_id"],
                    "D": cell["D"],
                    "alpha": cell["alpha"],
                    "noise_level": cell["noise"],
                    "is_null": cell["is_null"],
                    "mu_ceil_level": cell["mu_ceil_level"],
                    "mu_ceil_value": cell["mu_ceil_value"],
                    "replicate": r,
                    "split": split,
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Shared draw: one per (noise_level, replicate), independent of D, alpha,
# and mu_ceil_level. MU_CEIL never touches generation.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SharedDraw:
    replicate: int
    noise_level: float
    compounds: pd.DataFrame
    g: np.ndarray  # (180,)
    mu_inf: float
    phi_p: float
    scale: float
    coefficient: float
    noise_array: np.ndarray  # (180, 6)
    split: str


def _synthetic_compounds(seed: int) -> pd.DataFrame:
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
    frame = pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N_COMPOUNDS)],
            "scaffold_id": [f"S{i:02d}" for i in scaffold],
            "split": split_by_group[scaffold],
            "mass": mass,
            "descriptor": descriptor,
            "descriptor2": descriptor2,
        }
    )
    return frame


def generate_shared_draw(replicate: int, noise_level: float) -> SharedDraw:
    ntok = noise_token(noise_level)
    seed_compounds = derive_seed("E1", ntok, f"r{replicate:03d}", "compounds")
    seed_law = derive_seed("E1", ntok, f"r{replicate:03d}", "law")
    seed_response = derive_seed("E1", ntok, f"r{replicate:03d}", "response")
    split = split_for(noise_level, replicate)

    compounds = _synthetic_compounds(seed_compounds)
    mass = compounds["mass"].to_numpy()
    descriptor = compounds["descriptor"].to_numpy()

    law_rng = np.random.default_rng(seed_law)
    scale = float(law_rng.uniform(1.1, 1.8))
    coefficient = float(law_rng.uniform(0.25, 0.55))
    g = scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor)

    response_rng = np.random.default_rng(seed_response)
    mu_inf = float(response_rng.uniform(0.15, 0.30))
    phi_p = float(response_rng.uniform(1.20, 1.70))
    if noise_level:
        noise_array = response_rng.normal(0, noise_level, (N_COMPOUNDS, len(ENERGY_GRID)))
    else:
        noise_array = np.zeros((N_COMPOUNDS, len(ENERGY_GRID)))

    return SharedDraw(
        replicate=replicate,
        noise_level=noise_level,
        compounds=compounds,
        g=g,
        mu_inf=mu_inf,
        phi_p=phi_p,
        scale=scale,
        coefficient=coefficient,
        noise_array=noise_array,
        split=split,
    )


def deviation_arrays(d: str, alpha: float, compounds: pd.DataFrame, mu_inf: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(shape, floor, ceiling) per MURU_V2_E1_PROTOCOL.md Sec 2's table."""
    descriptor = compounds["descriptor"].to_numpy()
    descriptor2 = compounds["descriptor2"].to_numpy()
    n = len(compounds)
    shape = np.ones(n)
    floor = np.full(n, mu_inf)
    ceiling = np.ones(n)
    if d == "M0":
        return shape, floor, ceiling
    if d == "M1":
        shape = 1 + alpha * M1_AMPLITUDE * np.tanh(descriptor)
    elif d == "M2":
        floor = np.clip(mu_inf + alpha * M2_AMPLITUDE * (descriptor - 0.5), 0.03, 0.55)
    elif d == "M3":
        ceiling = np.clip(1 - alpha * M3_AMPLITUDE * descriptor, *M3_CEILING_CLIP)
    elif d == "M1M2M3":
        shape = 1 + alpha * COMBINED_M1_AMPLITUDE * np.tanh(descriptor)
        floor = np.clip(mu_inf + alpha * COMBINED_M2_AMPLITUDE * (descriptor2 - 0.5), 0.03, 0.55)
        ceiling = np.clip(1 - alpha * COMBINED_M3_AMPLITUDE * descriptor, *M3_CEILING_CLIP)
    else:
        raise ValueError(f"unknown D: {d}")
    return shape, floor, ceiling


def build_trajectories(draw: SharedDraw, d: str, alpha: float) -> pd.DataFrame:
    """Apply deviation (d, alpha) to the shared draw; fixed v1 clip."""
    energy = np.asarray(ENERGY_GRID, dtype=float)
    u = (energy[None, :] / E_REF) / draw.g[:, None]
    shape, floor, ceiling = deviation_arrays(d, alpha, draw.compounds, draw.mu_inf)
    mu = generator.combined_response(u, draw.phi_p, shape, floor, ceiling)
    mu = mu + draw.noise_array
    mu = np.clip(mu, MU_FLOOR, V1_MU_CEIL_DEFAULT)
    rows = []
    compound_ids = draw.compounds["compound_id"].to_numpy()
    for i, cid in enumerate(compound_ids):
        for j, e in enumerate(ENERGY_GRID):
            rows.append({"compound_id": cid, "energy": e, "mu": float(mu[i, j])})
    return pd.DataFrame(rows)


def world_content_hash(compounds: pd.DataFrame, trajectories: pd.DataFrame) -> str:
    payload = (
        compounds.sort_values("compound_id").to_csv(index=False)
        + "|"
        + trajectories.sort_values(["compound_id", "energy"]).to_csv(index=False)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_hashes() -> dict:
    files = [
        "src/muru/paper_benchmark/generator.py",
        "src/muru/paper_benchmark/adequacy.py",
        "src/muru/paper_benchmark/rc5_adequacy.py",
        "src/muru/paper_benchmark/rc5_estimate.py",
        "src/muru/paper_benchmark/registry.py",
        "src/muru/discovery/estimate.py",
        "scripts/e1_common.py",
    ]
    repo_root = os.path.dirname(_THIS_DIR)
    out = {}
    for rel in files:
        path = os.path.join(repo_root, rel)
        with open(path, "rb") as fh:
            out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out
