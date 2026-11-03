"""Fresh validation-world construction for the objective-alignment study.

Every world here is NEW: a fresh generator-seed namespace, freshly drawn
constants, freshly drawn nuisance values, fresh noise and fresh split
assignments. No Phase 3 world is reused, and `tests/test_ov_freshness.py`
asserts that the realized seed sets are disjoint from Phase 3's.

Blind truth handling (`TYPE2_VALIDATION_PREREGISTRATION.md` §8): `build_world2`
returns a `World2` whose `long`/`cov` frames are the ONLY thing the search side
receives. The planted law, its parameters and its support live in `truth`, which
is written to a separate manifest artifact and is never read by
`objval.select`, `objval.signature`, `objval.equiv` or `muru.discovery`.

This module is allowed to read `truth2`. It is not importable from the
discovery side.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from muru.objval import truth2
from muru.objval.truth2 import PlantedLaw2, planted2
from muru.synth.generators import (CELL_DROPOUT_RATE, ENERGY_GRID, ENERGY_SCALE,
                                   FEATURES, MIN_ENERGIES_PER_COMPOUND, MU_CEIL,
                                   MU_FLOOR, SCALE, load_dev_covariates,
                                   scale_frame)

GENERATOR2_VERSION = "ov-gen-1.0.0"

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"

# Fresh noise regimes. The moderate level is UNCHANGED from Phase 3 because it
# is the Phase 1 conservative inter-mixture variability estimate, a measured
# quantity rather than a tuning knob (MASTER_PLAN_CLARIFICATIONS C4). Changing
# it would change what "moderate noise" means relative to the real instrument.
NOISE_REGIMES2 = {"low": 0.010, "moderate": 0.0295, "adverse": 0.060}

N_FRAGMENTS = 24


def world_seed2(family: str, replicate: int, tag: str) -> int:
    """Generator seed in a namespace disjoint from Phase 3's.

    Phase 3 hashed `p3-gen-1.0.0|family|replicate|regime`. The version prefix
    differs here, and the realized seed sets are asserted disjoint by test.
    """
    key = f"{GENERATOR2_VERSION}|{family}|{replicate}|{tag}"
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big")


@dataclass
class World2:
    world_id: str
    family: str
    replicate: int
    noise_regime: str
    seed: int
    generator_version: str
    truth_version: str
    covariate_source: str
    long: pd.DataFrame
    cov: pd.DataFrame
    output_sha256: str
    truth: dict          # QUARANTINED: never handed to the search side

    def search_inputs(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Exactly what the discovery side is allowed to see."""
        return self.long, self.cov

    def manifest(self) -> dict:
        """World identity WITHOUT the planted law. Safe for search-side logs."""
        return {"world_id": self.world_id, "family": self.family,
                "replicate": self.replicate, "noise_regime": self.noise_regime,
                "seed": self.seed, "generator_version": self.generator_version,
                "truth_version": self.truth_version,
                "covariate_source": self.covariate_source,
                "n_compounds": int(self.cov.group_key.nunique()),
                "n_rows": int(len(self.long)),
                "output_sha256": self.output_sha256}

    def truth_record(self) -> dict:
        """The quarantined planted truth, for the separate truth manifest."""
        return {"world_id": self.world_id, **self.truth}


def _apply_noise(mu: np.ndarray, sd: float, rng: np.random.Generator) -> np.ndarray:
    return np.clip(mu + rng.normal(0.0, sd, mu.shape), MU_FLOOR, MU_CEIL)


def _drop_cells(long: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    keep = rng.random(len(long)) >= CELL_DROPOUT_RATE
    out = long[keep]
    n = out.groupby("group_key").ce_numeric.transform("size")
    short = out[n < MIN_ENERGIES_PER_COMPOUND].group_key.unique()
    if len(short):
        out = pd.concat([out, long[long.group_key.isin(short)]]).drop_duplicates(
            subset=["group_key", "ce_numeric"])
    return out.sort_values(["group_key", "ce_numeric"]).reset_index(drop=True)


def _long(cov: pd.DataFrame, mu_mat: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "group_key": np.repeat(cov.group_key.to_numpy(), len(ENERGY_GRID)),
        "ce_numeric": np.tile(ENERGY_GRID, len(cov)),
        "mu": mu_mat.ravel()})


def _hash_world(long: pd.DataFrame, cov: pd.DataFrame) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(long.mu.to_numpy(float)).tobytes())
    h.update(np.ascontiguousarray(long.ce_numeric.to_numpy(float)).tobytes())
    h.update("|".join(long.group_key.astype(str)).encode())
    h.update(np.ascontiguousarray(cov[list(FEATURES)].to_numpy(float)).tobytes())
    return h.hexdigest()


def _collapse_mu(g: np.ndarray, mu_inf: float, p: float) -> np.ndarray:
    u = (ENERGY_GRID / ENERGY_SCALE)[None, :] / np.clip(g, 1e-6, None)[:, None]
    return truth2.phi(u, mu_inf, p)


def _latent(z: dict, rho: float, rng: np.random.Generator) -> np.ndarray:
    proxy = np.column_stack([z["heteroatom_fraction"], z["tpsa"], z["rotatable_bonds"]])
    proxy = (proxy - proxy.mean(0)) / proxy.std(0)
    base = proxy.mean(1)
    base = (base - base.mean()) / base.std()
    lat = rho * base + np.sqrt(max(1e-9, 1 - rho ** 2)) * rng.normal(0, 1, len(base))
    return (lat - lat.mean()) / lat.std()


def _analytic_covariates(rng: np.random.Generator, n: int = 439
                         ) -> tuple[pd.DataFrame, dict]:
    """G1A: covariates independent of real chemistry.

    Stored columns are pre-multiplied by `SCALE` so the discovery side's
    dimensionless division recovers exactly the frame the law is planted on —
    the failure `DEVIATIONS_P3.md` D9 recorded, avoided here by construction.
    """
    v = rng.uniform(0.2, 1.8, size=(n, len(FEATURES)))
    cov = pd.DataFrame({c: v[:, i] * SCALE[c] for i, c in enumerate(FEATURES)})
    cov.insert(0, "group_key", [f"OVA{i:04d}" for i in range(n)])
    cov["scaffold_group"] = [f"OVAS{i % 60:03d}" for i in range(n)]
    cov["cluster_group"] = cov["scaffold_group"]
    cov["mix"] = 0
    z = {c: v[:, i] for i, c in enumerate(FEATURES)}
    z["v0"], z["v1"] = z["precursor_mz"], z["heteroatom_fraction"]
    return cov, z


def _coupling_world(cov: pd.DataFrame, rng: np.random.Generator,
                    cutoff_da: float) -> tuple[np.ndarray, dict]:
    """The measurement-coupling adversary, reconstructed with fresh draws.

    Fractional fragmentation is held FIXED as a law across mass; an absolute
    low-mass cutoff is applied and `mu` is computed exactly as the real pipeline
    computes it. Per-compound realizations are independent of every descriptor,
    so any descriptor structure found here is spurious by construction.

    The cutoff is stipulated, never tuned to reproduce an observed correlation,
    and nothing here identifies how much of the real association is artifactual.
    """
    M = cov.precursor_mz.to_numpy(float)
    n = len(M)
    f = np.sort(rng.uniform(0.05, 0.95, size=(n, N_FRAGMENTS)), axis=1)
    inten0 = rng.uniform(0.2, 1.0, size=(n, N_FRAGMENTS))
    sy_i = rng.uniform(0.85, 1.15, size=n)

    mu = np.empty((n, len(ENERGY_GRID)))
    for j, E in enumerate(ENERGY_GRID):
        sy = np.clip(sy_i / (1.0 + (E / 33.0) ** 2.1), 0.0, 1.0)
        w = inten0 * np.exp(-1.15 * (E / 90.0) * f)
        alive = (f * M[:, None]) >= cutoff_da
        wt = np.where(alive, w, 0.0)
        denom = wt.sum(1)
        phi_frag = np.where(denom > 0, (wt * f).sum(1) / np.maximum(denom, 1e-12), 1.0)
        mu[:, j] = sy + (1.0 - sy) * phi_frag

    rho = [float(pd.Series(mu[:, j]).corr(pd.Series(M), method="spearman"))
           for j in range(len(ENERGY_GRID))]
    return mu, {"cutoff_da": float(cutoff_da), "n_fragments": N_FRAGMENTS,
                "rho_mu_mass_by_energy": rho}


def build_world2(family: str, replicate: int, noise_regime: str,
                 cov: pd.DataFrame | None = None,
                 cutoff_da: float | None = None) -> World2:
    """Construct one fresh validation world.

    Deterministic in (family, replicate, noise_regime, cutoff_da) under the
    `ov-gen-1.0.0` namespace.
    """
    law: PlantedLaw2 = planted2(family)
    tag = noise_regime if cutoff_da is None else f"{noise_regime}|cut{cutoff_da:g}"
    seed = world_seed2(family, replicate, tag)
    rng = np.random.default_rng(seed)
    sd = NOISE_REGIMES2[noise_regime]
    params = truth2.draw_params(family, rng, replicate)
    params.update({"noise_sd": sd, "cell_dropout_rate": CELL_DROPOUT_RATE})
    src = "real_dev_covariates"
    diagnostics: dict = {}

    if family == "G1A":
        cov, z = _analytic_covariates(rng)
        src = "fully_synthetic"
    else:
        cov = load_dev_covariates() if cov is None else cov.copy()
        z = scale_frame(cov)

    extra_cols: dict[str, np.ndarray] = {}
    g = None

    if family == "G2":
        g = law.g_of(z, params)
        p_i = law.extra["p_of_z"](z, params)
        u = (ENERGY_GRID / ENERGY_SCALE)[None, :] / np.clip(g, 1e-6, None)[:, None]
        mu = truth2.phi_shape_varying(u, p_i[:, None], params["mu_inf"])
        diagnostics["p_i_range"] = [float(p_i.min()), float(p_i.max())]

    elif family in ("G4", "G4M"):
        offs = rng.normal(0.0, params["sigma_g"], len(cov))
        g = law.g_of(z, params) * np.exp(offs)
        mu = _collapse_mu(g, params["mu_inf"], params["phi_p"])
        diagnostics["max_abs_corr_offset_descriptor"] = float(max(
            abs(np.corrcoef(offs, z[c])[0, 1]) for c in FEATURES))

    elif family == "G5":
        lat = _latent(z, params["latent_rho"], rng)
        g = law.g_of({**z, "__latent__": lat}, params)
        mu = _collapse_mu(g, params["mu_inf"], params["phi_p"])
        diagnostics["latent_max_abs_corr_observed"] = float(max(
            abs(np.corrcoef(lat, z[c])[0, 1]) for c in FEATURES))

    elif family == "GRT":
        lipo = _latent(z, 0.55, rng)
        g = law.g_of({**z, "__lipo__": lipo}, params)
        mu = _collapse_mu(g, params["mu_inf"], params["phi_p"])
        extra_cols["retention_time_min"] = (
            8.0 + 4.0 * lipo + rng.normal(0, params["rt_noise"] * 4.0, len(cov)))

    elif family == "GC":
        mu, gc = _coupling_world(cov, rng, float(cutoff_da))
        params["cutoff_da"] = float(cutoff_da)
        diagnostics.update(gc)

    else:  # G1A, G1B, G1C, G3
        g = law.g_of(z, params)
        mu = _collapse_mu(g, params["mu_inf"], params["phi_p"])

    if g is not None:
        diagnostics["g_range"] = [float(np.min(g)), float(np.max(g))]
    if family in ("G1B", "G1C", "G2", "G3"):
        diagnostics["carrier_mass_spearman"] = {
            c: float(pd.Series(z[c]).corr(pd.Series(z["precursor_mz"]),
                                          method="spearman"))
            for c in truth2.NON_MASS_CARRIERS}

    mu = _apply_noise(mu, sd, rng)
    long = _long(cov, mu)
    for name, vals in extra_cols.items():
        long[name] = np.repeat(vals, len(ENERGY_GRID))
    long = _drop_cells(long, rng)

    wid = (f"OV|{family}|r{replicate:03d}|{noise_regime}"
           + (f"|cut{cutoff_da:g}" if cutoff_da is not None else ""))
    return World2(
        world_id=wid, family=family, replicate=replicate,
        noise_regime=noise_regime, seed=seed,
        generator_version=GENERATOR2_VERSION, truth_version=truth2.TRUTH2_VERSION,
        covariate_source=src, long=long, cov=cov,
        output_sha256=_hash_world(long, cov),
        truth={"family": family, "role": law.role,
               "planted_expr": law.expr_of(params),
               "planted_support": list(law.support_of(params)),
               "collapses": law.collapses,
               "structural_beyond_mass": law.structural_beyond_mass,
               "exactly_representable": law.exactly_representable,
               "params": params, "diagnostics": diagnostics,
               "notes": law.notes})


# --------------------------------------------------------------------------
# null calibration worlds
# --------------------------------------------------------------------------
NULL_CONSTRUCTIONS2 = (
    "target_permuted_across_compounds",
    "target_permuted_across_energy_within_compound",
    "descriptors_permuted_across_compounds",
    "gaussian_targets_with_observed_variance",
)


def build_null_world2(index: int, construction: str, cov: pd.DataFrame,
                      base_family: str = "G1B",
                      noise_regime: str = "moderate") -> World2:
    """A calibration world in which no valid descriptor-level conjecture exists.

    A realistic structured world is built first and then the descriptor-response
    link is destroyed by one of the master plan's four §13.6 constructions, so
    the null keeps as much of the marginal structure as the construction allows
    and is not trivially easy to reject.
    """
    if construction not in NULL_CONSTRUCTIONS2:
        raise ValueError(f"unknown null construction: {construction}")
    base = build_world2(base_family, 50_000 + index, noise_regime, cov=cov)
    seed = world_seed2(f"NULL|{construction}", index, noise_regime)
    rng = np.random.default_rng(seed)

    long = base.long.copy()
    cov_out = base.cov.copy()

    if construction == "target_permuted_across_compounds":
        keys = long.group_key.unique()
        mapping = dict(zip(keys, rng.permutation(keys)))
        src = {k: gdf.set_index("ce_numeric").mu
               for k, gdf in long.groupby("group_key")}
        long["mu"] = [src[mapping[k]].get(e, np.nan)
                      for k, e in zip(long.group_key, long.ce_numeric)]
        long["mu"] = long.mu.fillna(float(base.long.mu.mean()))
    elif construction == "target_permuted_across_energy_within_compound":
        long["mu"] = long.groupby("group_key").mu.transform(
            lambda s: rng.permutation(s.to_numpy()))
    elif construction == "descriptors_permuted_across_compounds":
        feats = list(FEATURES)
        cov_out[feats] = cov_out[feats].to_numpy()[rng.permutation(len(cov_out))]
    else:
        stats = base.long.groupby("ce_numeric").mu.agg(["mean", "std"])
        m = long.ce_numeric.map(stats["mean"]).to_numpy(float)
        s = long.ce_numeric.map(stats["std"]).to_numpy(float)
        long["mu"] = np.clip(rng.normal(m, s), MU_FLOOR, MU_CEIL)

    wid = f"OV|NULL|{construction}|r{index:03d}"
    return World2(
        world_id=wid, family="NULL", replicate=index, noise_regime=noise_regime,
        seed=seed, generator_version=GENERATOR2_VERSION,
        truth_version=truth2.TRUTH2_VERSION,
        covariate_source="real_dev_covariates",
        long=long.reset_index(drop=True), cov=cov_out,
        output_sha256=_hash_world(long, cov_out),
        truth={"family": "NULL", "role": "null calibration",
               "planted_expr": "NO DESCRIPTOR-LEVEL CONJECTURE EXISTS",
               "planted_support": [], "collapses": False,
               "structural_beyond_mass": False, "exactly_representable": False,
               "params": {"construction": construction,
                          "base_family": base_family,
                          "noise_regime": noise_regime},
               "diagnostics": {}, "notes": ""})


def truth_manifest_path() -> Path:
    return ART / "ov_truth_manifest.json"


def write_truth_manifest(records: list[dict]) -> str:
    """Write the quarantined truth manifest and return its sha256.

    The search side never opens this file. `tests/test_ov_blinding.py` asserts
    that no discovery-side module references it.
    """
    p = truth_manifest_path()
    payload = {"truth_version": truth2.TRUTH2_VERSION,
               "generator_version": GENERATOR2_VERSION,
               "n_worlds": len(records), "worlds": records}
    text = json.dumps(payload, indent=1, sort_keys=True, default=str)
    p.write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()
