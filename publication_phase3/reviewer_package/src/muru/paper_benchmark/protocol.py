"""Minimal fold-local scalar adapter boundary for the locked implementation."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FrozenScalarObjects:
    energy: tuple[float, ...]
    training_mean: tuple[float, ...]
    support: tuple[float, float]


@dataclass(frozen=True)
class ScalarEstimate:
    compound_id: str
    log_g: float
    boundary_hit: bool


def fit_training_scalar(training_rows: pd.DataFrame) -> FrozenScalarObjects:
    if training_rows.empty or set(training_rows.split) != {"train"}:
        raise ValueError("fit_training_scalar accepts training rows only")
    means = training_rows.groupby("energy", sort=True).mu.mean()
    return FrozenScalarObjects(tuple(float(value) for value in means.index), tuple(float(value) for value in means.values), (-2.0, 2.0))


def estimate_one(frozen: FrozenScalarObjects, compound_rows: pd.DataFrame) -> ScalarEstimate:
    if compound_rows.empty or compound_rows.compound_id.nunique() != 1:
        raise ValueError("estimate_one accepts exactly one held-out compound")
    observed = compound_rows.set_index("energy").mu.reindex(frozen.energy).to_numpy(dtype=float)
    baseline = np.asarray(frozen.training_mean)
    # Frozen M0 generator: u = (E/45)/g, mu = mu_inf + (1 - mu_inf) * exp(-(u**phi_p)).
    # For fixed E, mu is strictly increasing in g (larger g -> smaller u -> smaller
    # u**phi_p -> exp(-(.)) closer to 1 -> larger mu, since mu_inf < 1 always).
    # A held-out compound with mu observed above the training baseline therefore has
    # a larger g than the training population; the scalar estimate must move the same
    # direction as that residual, not against it.
    residual = float(np.nanmean(observed - baseline))
    log_g = float(np.clip(residual, *frozen.support))
    return ScalarEstimate(str(compound_rows.compound_id.iloc[0]), log_g, log_g in frozen.support)
