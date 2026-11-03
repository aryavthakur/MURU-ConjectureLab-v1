"""Phase 3 synthetic world construction.

Two kinds of world:

* **real-covariate, synthetic-response** — the descriptor matrix, mass
  distribution, energy grid and scaffold grouping are the real development
  corpus, so mass-descriptor correlation and chemical support stay realistic.
  The response is generated entirely by a planted law in `truth.py`. No
  observed `mu` value is read, ever.
* **fully synthetic** (`GA`) — descriptors drawn i.i.d., law analytically
  transparent, no real chemistry involved.

The sealed confirmation compounds are excluded by connectivity key before any
covariate is touched, and only their identifiers are read.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

from muru.synth import truth
from muru.synth.truth import PHI, PlantedLaw, phi, phi_shape_varying, planted

GENERATOR_VERSION = "p3-gen-1.0.0"

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"

ENERGY_GRID = np.array([15.0, 30.0, 45.0, 60.0, 75.0, 90.0])

# Tier A descriptors handed to the search, in frozen order.
FEATURES = ("precursor_mz", "total_atom_count", "rotatable_bonds", "ring_count",
            "aromatic_ring_count", "rdbe", "tpsa", "heteroatom_fraction",
            "n_N", "n_O", "n_S", "n_halogen")

# Dimensionless scaling (master plan 13.4): energy in NCE/30, mass in Da/500,
# counts divided by their development-corpus median. Frozen literals, computed
# once from the 439 development compounds before any governed run.
SCALE = {
    "precursor_mz": 500.0,
    "total_atom_count": 37.0,
    "rotatable_bonds": 4.0,
    "ring_count": 2.0,
    "aromatic_ring_count": 2.0,
    "rdbe": 8.5,
    "tpsa": 54.5,
    "heteroatom_fraction": 0.25,
    "n_N": 2.0,
    "n_O": 2.0,
    "n_S": 1.0,       # median is 0; a unit scale keeps the variable dimensionless
    "n_halogen": 1.0,  # median is 0; same
}
ENERGY_SCALE = 30.0

# Noise regimes, frozen. The moderate level is the Phase 1 CONSERVATIVE
# INTER-MIXTURE VARIABILITY estimate -- an upper bound on technical
# repeatability, NOT an instrument noise floor and NOT pure Gaussian technical
# error (MASTER_PLAN_CLARIFICATIONS C4). It is used here only as a scale
# reference for an additive synthetic perturbation.
NOISE_REGIMES = {
    "low": 0.010,
    "moderate": 0.0295,
    "adverse": 0.060,
}

# Measured, not assumed: 517 of 549 compounds have all six energies and 32 have
# five, i.e. 99.03% cell coverage. The master plan 18.2 figure of 15% missing
# does not describe this corpus and is not used (DEVIATIONS_P3 D3).
CELL_DROPOUT_RATE = 0.0097
MIN_ENERGIES_PER_COMPOUND = 5

MU_FLOOR = 1e-3
MU_CEIL = 1.0


# --------------------------------------------------------------------------
# covariates
# --------------------------------------------------------------------------
def sealed_keys() -> set[str]:
    """Identifiers only. The confirmation response values are never read."""
    seal = json.loads((ART / "confirmation_set_sealed.json").read_text())
    return set(seal["connectivity_keys"])


def load_dev_covariates() -> pd.DataFrame:
    """Development-corpus Tier A descriptors, scaffold group, and cluster.

    Reads no response column. Confirmation compounds are dropped by
    connectivity key and their absence is asserted, not assumed.
    """
    cm = pd.read_parquet(ART / "p2_compounds.parquet")
    tA = pd.read_parquet(ART / "p2_descriptors_tierA.parquet")
    keys = sealed_keys()

    dev = cm[~cm.in_confirmation].copy()
    assert not (set(dev.inchikey_first_block) & keys), \
        "a sealed confirmation compound reached the Phase 3 covariate matrix"

    out = dev[["group_key", "inchikey_first_block", "scaffold_group",
               "cluster_group", "mix"]].merge(
        tA[["group_key", *FEATURES]], on="group_key", how="inner")
    assert len(out) == len(dev), "descriptor join lost development compounds"
    assert not out[list(FEATURES)].isna().any().any()
    return out.sort_values("group_key").reset_index(drop=True)


def scale_frame(cov: pd.DataFrame) -> dict[str, np.ndarray]:
    """Dimensionless descriptor frame, the only frame the search ever sees."""
    return {c: cov[c].to_numpy(float) / SCALE[c] for c in FEATURES}


# --------------------------------------------------------------------------
# world container
# --------------------------------------------------------------------------
@dataclass
class World:
    world_id: str
    family: str
    replicate: int
    noise_regime: str
    seed: int
    generator_version: str
    truth_version: str
    covariate_source: str
    planted_expr: str
    planted_support: tuple[str, ...]
    collapses: bool
    structural_beyond_mass: bool
    params: dict
    long: pd.DataFrame        # group_key, ce_numeric, mu  (+ retention_time for GRT)
    cov: pd.DataFrame         # group_key, features, scaffold_group, cluster_group
    output_sha256: str

    def manifest(self) -> dict:
        d = asdict(self)
        d.pop("long"), d.pop("cov")
        d["n_compounds"] = int(self.cov.group_key.nunique())
        d["n_rows"] = int(len(self.long))
        d["planted_support"] = list(self.planted_support)
        return d


def _hash_world(long: pd.DataFrame, cov: pd.DataFrame) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(long.mu.to_numpy(float)).tobytes())
    h.update(np.ascontiguousarray(long.ce_numeric.to_numpy(float)).tobytes())
    h.update("|".join(long.group_key.astype(str)).encode())
    h.update(np.ascontiguousarray(
        cov[list(FEATURES)].to_numpy(float)).tobytes())
    return h.hexdigest()


def world_seed(family: str, replicate: int, noise_regime: str) -> int:
    """Deterministic seed from the world's identity, so a clean rerun of any
    single world reproduces it without replaying the ones before it."""
    key = f"{GENERATOR_VERSION}|{family}|{replicate}|{noise_regime}"
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big")


# --------------------------------------------------------------------------
# noise and censoring
# --------------------------------------------------------------------------
def _apply_noise(mu: np.ndarray, sd: float, rng: np.random.Generator) -> np.ndarray:
    """Additive perturbation on the natural scale, then the pipeline's own
    bounds. mu is a mass fraction in (0, 1]; it is clipped, not transformed,
    because Phase 2 D7 established that the logit link is undefined here."""
    return np.clip(mu + rng.normal(0.0, sd, mu.shape), MU_FLOOR, MU_CEIL)


def _drop_cells(long: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Missing (compound, energy) cells at the measured 0.97% rate, never
    taking a compound below five energies."""
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
        "mu": mu_mat.ravel(),
    })


# --------------------------------------------------------------------------
# families
# --------------------------------------------------------------------------
def _collapse_mu(g: np.ndarray) -> np.ndarray:
    """mu_ij = Phi(E_j / g_i) on the frozen energy grid."""
    u = (ENERGY_GRID / ENERGY_SCALE)[None, :] / np.clip(g, 1e-6, None)[:, None]
    return phi(u)


def _latent(cov: pd.DataFrame, z: dict, rho: float,
            rng: np.random.Generator) -> np.ndarray:
    """A standardized latent variable correlated with the observed descriptors
    at approximately `rho` but not equal to any of them."""
    proxy = np.column_stack([z["heteroatom_fraction"], z["tpsa"], z["rotatable_bonds"]])
    proxy = (proxy - proxy.mean(0)) / proxy.std(0)
    base = proxy.mean(1)
    base = (base - base.mean()) / base.std()
    noise = rng.normal(0, 1, len(base))
    lat = rho * base + np.sqrt(max(1e-9, 1 - rho ** 2)) * noise
    return (lat - lat.mean()) / lat.std()


def build_world(family: str, replicate: int, noise_regime: str,
                cov: pd.DataFrame | None = None,
                cutoff_da: float | None = None) -> World:
    """Construct one synthetic world. Deterministic in (family, replicate,
    noise_regime, cutoff_da)."""
    law: PlantedLaw = planted(family)
    seed = world_seed(family, replicate, noise_regime if cutoff_da is None
                      else f"{noise_regime}|cut{cutoff_da:g}")
    rng = np.random.default_rng(seed)
    sd = NOISE_REGIMES[noise_regime]
    params: dict = {"noise_sd": sd, "cell_dropout_rate": CELL_DROPOUT_RATE}
    src = "real_dev_covariates"

    if family == "GA":
        cov, z = _analytic_covariates(rng)
        src = "fully_synthetic"
    else:
        cov = load_dev_covariates() if cov is None else cov.copy()
        z = scale_frame(cov)

    extra_cols: dict[str, np.ndarray] = {}

    if family == "G2":
        g = law.g(z)
        p_i = law.extra["p_of_z"](z)
        u = (ENERGY_GRID / ENERGY_SCALE)[None, :] / np.clip(g, 1e-6, None)[:, None]
        mu = phi_shape_varying(u, p_i[:, None])
        params["p_i_range"] = [float(p_i.min()), float(p_i.max())]

    elif family in ("G4", "G4M"):
        sigma = law.extra["sigma_g"]
        offs = rng.normal(0.0, sigma, len(cov))
        g = law.g(z) * np.exp(offs)
        mu = _collapse_mu(g)
        params["sigma_g"] = sigma
        # the offsets are independent of every descriptor by construction
        params["max_abs_corr_offset_descriptor"] = float(max(
            abs(np.corrcoef(offs, z[c])[0, 1]) for c in FEATURES))

    elif family == "G5":
        lat = _latent(cov, z, law.extra["latent_rho"], rng)
        g = law.g({**z, "__latent__": lat})
        mu = _collapse_mu(g)
        params["latent_rho_target"] = law.extra["latent_rho"]
        params["latent_max_abs_corr_observed"] = float(max(
            abs(np.corrcoef(lat, z[c])[0, 1]) for c in FEATURES))

    elif family == "GRT":
        lipo = _latent(cov, z, 0.55, rng)
        g = law.g({**z, "__lipo__": lipo})
        mu = _collapse_mu(g)
        rt = 8.0 + 4.0 * lipo + rng.normal(0, law.extra["rt_noise"] * 4.0, len(cov))
        extra_cols["retention_time_min"] = rt
        params["rt_noise"] = law.extra["rt_noise"]

    elif family == "GC":
        mu, gc_params = _coupling_world(cov, rng, cutoff_da)
        params.update(gc_params)
        g = None

    else:  # G1, G1B, G3, GA
        g = law.g(z)
        mu = _collapse_mu(g)

    mu = _apply_noise(mu, sd, rng)
    long = _long(cov, mu)
    for name, vals in extra_cols.items():
        long[name] = np.repeat(vals, len(ENERGY_GRID))
    long = _drop_cells(long, rng)

    wid = (f"{family}|r{replicate:03d}|{noise_regime}"
           + (f"|cut{cutoff_da:g}" if cutoff_da is not None else ""))
    return World(
        world_id=wid, family=family, replicate=replicate,
        noise_regime=noise_regime, seed=seed,
        generator_version=GENERATOR_VERSION, truth_version=truth.TRUTH_VERSION,
        covariate_source=src, planted_expr=law.expr,
        planted_support=law.support, collapses=law.collapses,
        structural_beyond_mass=law.structural_beyond_mass, params=params,
        long=long, cov=cov, output_sha256=_hash_world(long, cov))


# --------------------------------------------------------------------------
# the four master-plan 13.6 null constructions
# --------------------------------------------------------------------------
NULL_CONSTRUCTIONS = (
    "target_permuted_across_compounds",
    "target_permuted_across_energy_within_compound",
    "descriptors_permuted_across_compounds",
    "gaussian_targets_with_observed_variance",
)


def build_null_world(index: int, construction: str, cov: pd.DataFrame,
                     base_family: str = "G1B",
                     noise_regime: str = "moderate") -> World:
    """A calibration world in which no valid descriptor-level conjecture exists.

    A realistic base world is built first, then the descriptor-response link is
    destroyed by one of the master plan's four constructions. The marginal
    structure of the response is preserved as far as the construction allows, so
    the null is not trivially easy to reject.
    """
    if construction not in NULL_CONSTRUCTIONS:
        raise ValueError(f"unknown null construction: {construction}")
    base = build_world(base_family, 10_000 + index, noise_regime, cov=cov)
    seed = world_seed(f"NULL|{construction}", index, noise_regime)
    rng = np.random.default_rng(seed)

    long = base.long.copy()
    cov_out = base.cov.copy()

    if construction == "target_permuted_across_compounds":
        # whole trajectories move against descriptors, preserving trajectory shape
        keys = long.group_key.unique()
        mapping = dict(zip(keys, rng.permutation(keys)))
        src = {k: g.set_index("ce_numeric").mu for k, g in long.groupby("group_key")}
        long["mu"] = [
            src[mapping[k]].get(e, np.nan)
            for k, e in zip(long.group_key, long.ce_numeric)]
        long["mu"] = long.mu.fillna(float(base.long.mu.mean()))

    elif construction == "target_permuted_across_energy_within_compound":
        long["mu"] = long.groupby("group_key").mu.transform(
            lambda s: rng.permutation(s.to_numpy()))

    elif construction == "descriptors_permuted_across_compounds":
        feats = list(FEATURES)
        cov_out[feats] = cov_out[feats].to_numpy()[rng.permutation(len(cov_out))]

    else:  # gaussian_targets_with_observed_variance
        stats = base.long.groupby("ce_numeric").mu.agg(["mean", "std"])
        m = long.ce_numeric.map(stats["mean"]).to_numpy(float)
        s = long.ce_numeric.map(stats["std"]).to_numpy(float)
        long["mu"] = np.clip(rng.normal(m, s), MU_FLOOR, MU_CEIL)

    wid = f"NULL|{construction}|r{index:03d}"
    return World(
        world_id=wid, family="NULL", replicate=index,
        noise_regime=noise_regime, seed=seed,
        generator_version=GENERATOR_VERSION, truth_version=truth.TRUTH_VERSION,
        covariate_source="real_dev_covariates",
        planted_expr="NO DESCRIPTOR-LEVEL CONJECTURE EXISTS",
        planted_support=(), collapses=False, structural_beyond_mass=False,
        params={"construction": construction, "base_family": base_family,
                "noise_regime": noise_regime},
        long=long.reset_index(drop=True), cov=cov_out,
        output_sha256=_hash_world(long, cov_out))


def _analytic_covariates(rng: np.random.Generator, n: int = 439
                         ) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """GA: descriptors independent of real chemistry, law transparent.

    The stored columns are pre-multiplied by `SCALE` so that the discovery
    side's dimensionless division recovers exactly the values the law is
    planted on. Without that, the law would be planted in one frame and
    searched for in another, and GA would be unrecoverable by construction
    rather than by any property of the engine.
    """
    v = rng.uniform(0.2, 1.8, size=(n, len(FEATURES)))
    cov = pd.DataFrame({c: v[:, i] * SCALE[c] for i, c in enumerate(FEATURES)})
    cov.insert(0, "group_key", [f"GA{i:04d}" for i in range(n)])
    cov["scaffold_group"] = [f"GAS{i % 60:03d}" for i in range(n)]
    cov["cluster_group"] = cov["scaffold_group"]
    cov["mix"] = 0
    # the law is planted on the DIMENSIONLESS values, which is what the search
    # will see after `protocol.build_world_data` divides by SCALE
    z = {c: v[:, i] for i, c in enumerate(FEATURES)}
    z["v0"], z["v1"] = z["precursor_mz"], z["heteroatom_fraction"]
    return cov, z


# --------------------------------------------------------------------------
# GC: the Phase 2 measurement-coupling adversary
# --------------------------------------------------------------------------
N_FRAGMENTS = 24


def _coupling_world(cov: pd.DataFrame, rng: np.random.Generator,
                    cutoff_da: float | None) -> tuple[np.ndarray, dict]:
    """Fractional fragmentation held FIXED across mass; an absolute low-mass
    cutoff is then applied and mu is computed exactly as the real pipeline
    computes it:

        mu = SY + (1 - SY) * phi,     phi = <m/z fragment> / m/z precursor

    With proportional fragments and no cutoff, phi is mass-invariant and mu
    carries no mass dependence. With a fixed absolute cutoff at c Da, a
    fragment survives only if f_k * M >= c, so light precursors lose their
    low-f fragments and phi rises for them: a negative mu-mass association
    appears with no chemistry anywhere in the construction.

    The cutoff is stipulated at an interpretable instrument setting. It is not
    fitted, and nothing here identifies how much of the REAL association is
    artifactual.
    """
    M = cov.precursor_mz.to_numpy(float)
    cut = 0.0 if cutoff_da is None else float(cutoff_da)
    n = len(M)

    # Fractional fragmentation is held fixed as a LAW: every compound draws its
    # fragment positions and intensities from one common, mass-independent
    # distribution. The realization varies per compound -- otherwise mu would be
    # a deterministic function of mass and no search could be tempted to explain
    # the scatter with descriptors. The draws are independent of every
    # descriptor, so ANY descriptor structure found here is spurious.
    f = np.sort(rng.uniform(0.05, 0.95, size=(n, N_FRAGMENTS)), axis=1)
    inten0 = rng.uniform(0.2, 1.0, size=(n, N_FRAGMENTS))
    sy_i = rng.uniform(0.85, 1.15, size=n)  # per-compound survival scale, mass-free

    mu = np.empty((n, len(ENERGY_GRID)))
    for j, E in enumerate(ENERGY_GRID):
        # survival yield falls with energy; mass-invariant by construction
        sy = np.clip(sy_i / (1.0 + (E / 33.0) ** 2.1), 0.0, 1.0)
        # higher energy shifts intensity toward lighter fragments, by the same
        # fractional rule for every precursor
        w = inten0 * np.exp(-1.15 * (E / 90.0) * f)
        mz = f * M[:, None]                        # absolute fragment m/z
        alive = mz >= cut                          # the one absolute rule
        wt = np.where(alive, w, 0.0)
        denom = wt.sum(1)
        # a precursor whose fragments all fall below the cutoff has no fragment
        # term; phi falls back to the precursor itself
        phi_frag = np.where(denom > 0,
                            (wt * f).sum(1) / np.maximum(denom, 1e-12), 1.0)
        mu[:, j] = sy + (1.0 - sy) * phi_frag

    rho = [float(pd.Series(mu[:, j]).corr(pd.Series(M), method="spearman"))
           for j in range(len(ENERGY_GRID))]
    return mu, {"cutoff_da": cut, "n_fragments": N_FRAGMENTS,
                "fractional_behaviour":
                    "fixed mass-independent fractional law; per-compound "
                    "realizations independent of all descriptors",
                "rho_mu_mass_by_energy": rho}
