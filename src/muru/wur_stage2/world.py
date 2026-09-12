"""Assembling one Stage 2 analysis world from mu tables and covariates."""
from __future__ import annotations

import numpy as np
import pandas as pd

from muru.discovery import protocol
from muru.splits import assert_group_disjoint
from muru.wur_bridge import apply_energy_map
from muru.wur_bridge_constants import LADDER_ENERGIES

POOLED_ENERGIES = (30.0, 45.0, 60.0, 75.0, 90.0)       # E = 15 excluded, E-3
SPLIT_SEED_TAG = "seed20260911"


def world_id(analysis: str) -> str:
    return f"WUR2A|{analysis}|{SPLIT_SEED_TAG}"


def aligned_wur_long(wur_mu: pd.DataFrame, a: float, b: float) -> pd.DataFrame:
    """WUR trajectories re-read at T(E) for E in the pooled rungs.

    Uses the Stage 1 code unchanged, then drops E = 15. Every clamped cell
    must be an E = 15 cell; anything else is a violation of erratum E-3's
    account of the map and halts.
    """
    mapped, n_clamped = apply_energy_map(wur_mu, a, b)
    n_keys = mapped["connectivity_key"].nunique()
    targets = a + b * np.asarray(LADDER_ENERGIES)
    inside = [(t >= LADDER_ENERGIES[0] - 1e-6) and (t <= LADDER_ENERGIES[-1] + 1e-6)
              for t in targets]
    expected_clamped = n_keys * int(sum(1 for i in inside if not i))
    if n_clamped != expected_clamped:
        raise ValueError(f"clamped cells {n_clamped} != expected {expected_clamped}")
    if not all(inside[i] for i, e in enumerate(LADDER_ENERGIES) if e in POOLED_ENERGIES):
        raise ValueError("a pooled rung maps outside the WUR ladder")
    out = mapped[mapped["ce_numeric"].isin(POOLED_ENERGIES)].copy()
    out = out.rename(columns={"connectivity_key": "group_key"})
    out["source"] = "WUR"
    return out.reset_index(drop=True)


def native_long(mu: pd.DataFrame, source: str) -> pd.DataFrame:
    out = mu[["connectivity_key", "ce_numeric", "mu"]].rename(
        columns={"connectivity_key": "group_key"}).copy()
    out["source"] = source
    return out.reset_index(drop=True)


def pooled_long(lcsb: pd.DataFrame, wur_aligned: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Union with one trajectory per key; a key on both sides keeps LCSB."""
    lcsb = lcsb[lcsb["ce_numeric"].isin(POOLED_ENERGIES)]
    both = set(lcsb["group_key"]) & set(wur_aligned["group_key"])
    wur_only = wur_aligned[~wur_aligned["group_key"].isin(both)]
    out = pd.concat([lcsb, wur_only], ignore_index=True)
    dup = out.groupby(["group_key", "ce_numeric"]).size()
    if dup.max() != 1:
        raise ValueError("pooled table has a duplicated (key, energy) cell")
    census = {"n_lcsb_keys": int(lcsb["group_key"].nunique()),
              "n_wur_keys": int(wur_aligned["group_key"].nunique()),
              "n_both_lcsb_kept": len(both),
              "n_pooled_keys": int(out["group_key"].nunique())}
    return out, census


def pooled_covariates(lcsb_cov: pd.DataFrame, wur_cov: pd.DataFrame,
                      keys: set[str]) -> pd.DataFrame:
    """Covariates for the pooled keys; a key on both sides keeps LCSB."""
    both = set(lcsb_cov["connectivity_key"]) & set(wur_cov["connectivity_key"])
    cov = pd.concat([lcsb_cov, wur_cov[~wur_cov["connectivity_key"].isin(both)]],
                    ignore_index=True)
    cov = cov[cov["connectivity_key"].isin(keys)]
    if cov["connectivity_key"].duplicated().any():
        raise ValueError("duplicate key in pooled covariates")
    return cov.reset_index(drop=True)


def build_world(analysis: str, long: pd.DataFrame, cov: pd.DataFrame
                ) -> tuple[protocol.WorldData, pd.DataFrame]:
    """The frozen world constructor, on keys present in both tables.

    Returns the WorldData and the compound frame (key, scaffold group,
    split, source) the ladder and the report use. Split disjointness by key
    and by scaffold group is asserted.
    """
    cov = cov.rename(columns={"connectivity_key": "group_key"})
    keys = sorted(set(long["group_key"]) & set(cov["group_key"]))
    long = long[long["group_key"].isin(keys)].reset_index(drop=True)
    cov = cov[cov["group_key"].isin(keys)].reset_index(drop=True)
    wd = protocol.build_world_data(world_id(analysis), long, cov)
    frame = pd.DataFrame({"group_key": wd.fit.compounds,
                          "scaffold_group": wd.groups, "split": wd.split})
    frame = frame.merge(cov[["group_key", "source"]], on="group_key", how="left")
    frame["inchikey_first_block"] = frame["group_key"]
    assert_group_disjoint(frame, "split", key_col="scaffold_group")
    assert_group_disjoint(frame, "split", key_col="inchikey_first_block")
    return wd, frame.drop(columns="inchikey_first_block")
