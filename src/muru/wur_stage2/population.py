"""Stage 2 populations, identity-asserted before any spectrum is decoded.

Three populations, defined in MURU_WUR_STAGE2A_EXECUTION_PROTOCOL.md section
3: WUR-DEV-HOLD (never decoded here), WUR-DEV-ANALYSIS, and LCSB-DEV. Every
loader asserts, from the frozen artifacts, that what it returns is disjoint
from the WUR sealed keys, the LCSB sealed keys and (for WUR) the internal
holdout, and that the key hashes match the committed manifests.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from muru.discovery.protocol import FEATURES
from muru.io import wur_raw
from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_identity import accepted_rows
from muru.io.wur_partition import apply_d6, partition, sealed_scaffold_groups
from muru.io.wur_provenance import canonical_key_hash
from muru.io.wur_spectra import build_mu_table
from muru.molecules import scaffold_group, tier_a_descriptors
from muru.synth.generators import load_dev_covariates, sealed_keys
from muru.wur_bridge_constants import BASE_CELL

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts"

WUR_SEALED_SHA256 = "6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52"


class PopulationError(RuntimeError):
    """A population failed an identity assertion. Nothing is decoded."""


# ----------------------------------------------------------------- LCSB --
def lcsb_dev_mu_table() -> pd.DataFrame:
    """LCSB development trajectories at the base cell, sealed keys removed.

    Lineage is asserted the way Stage 1 asserted it, then the LCSB
    confirmation keys are subtracted and their absence asserted.
    """
    dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")
    dev = dev.rename(columns={"inchikey_first_block": "connectivity_key"})
    counts = dev.groupby(["connectivity_key", "ce_numeric"]).size()
    if counts.max() != 1:
        raise PopulationError("LCSB corpus has duplicated (compound, energy) cells")

    traj = pd.read_parquet(ART / "trajectories.parquet")
    base = traj[traj["is_base_cell"]]
    for col, val in (("cell_relative_cutoff", BASE_CELL["relative_cutoff"]),
                     ("cell_include_precursor", BASE_CELL["include_precursor"]),
                     ("cell_intensity_transform", BASE_CELL["intensity_transform"])):
        if not (base[col] == val).all():
            raise PopulationError(f"trajectories.parquet base cell differs on {col}")
    lineage = base[base["ion_mode_raw"].str.upper() == "POSITIVE"].groupby(
        ["inchikey_first_block", "ce_numeric"])["mu"].mean()
    check = dev.set_index(["connectivity_key", "ce_numeric"])["mu"]
    shared = check.index.intersection(lineage.index)
    if len(shared) != len(check):
        raise PopulationError("an LCSB corpus row has no base-cell ancestor")
    if (check.loc[shared] - lineage.loc[shared]).abs().max() >= 1e-9:
        raise PopulationError("LCSB corpus mu does not reproduce the base-cell value")

    sealed = sealed_keys()
    out = dev[~dev["connectivity_key"].isin(sealed)]
    if set(out["connectivity_key"]) & sealed:
        raise PopulationError("an LCSB sealed key survived subtraction")
    return out[["connectivity_key", "ce_numeric", "mu"]].reset_index(drop=True)


def lcsb_dev_covariates() -> pd.DataFrame:
    """Tier A descriptors and scaffold group for LCSB-DEV, keyed by bare key."""
    cov = load_dev_covariates()          # already drops confirmation keys, asserted
    out = cov.rename(columns={"inchikey_first_block": "connectivity_key"})
    out = out[["connectivity_key", "scaffold_group", *FEATURES]].copy()
    out["source"] = "LCSB"
    return out.reset_index(drop=True)


# ------------------------------------------------------------------ WUR --
def load_internal_holdout() -> dict:
    return json.loads((ART / "wur_dev_internal_holdout.json").read_text())


def wur_dev_partition(data_dir: Path) -> pd.DataFrame:
    """The WUR-DEV positive-mode identity table, sealed hash asserted."""
    pre = partition(load_annotated_trajectories(data_dir))
    part = apply_d6(pre, sealed_scaffold_groups(pre["POS"]))
    pos = part["POS"]
    sealed = sorted(pos.loc[pos["side"] == "WUR-SEALED", "connectivity_key"])
    recorded = json.loads((ART / "wur_sealed_partition.json").read_text())
    if not (canonical_key_hash(sealed) == WUR_SEALED_SHA256
            == recorded["connectivity_keys_sha256"]):
        raise PopulationError("sealed partition does not reproduce the frozen hash")
    dev = pos[pos["side"] == "WUR-DEV"].reset_index(drop=True)
    if set(dev["connectivity_key"]) & set(sealed):
        raise PopulationError("a sealed key is on the WUR-DEV side")
    if set(dev["connectivity_key"]) & sealed_keys():
        raise PopulationError("an LCSB sealed key is on the WUR-DEV side")
    return dev


def wur_analysis_keys(dev: pd.DataFrame) -> list[str]:
    """WUR-DEV-ANALYSIS keys, checked against the committed holdout manifest."""
    hold = load_internal_holdout()
    hold_keys = set(hold["hold"]["connectivity_keys"])
    ana_keys = set(hold["analysis"]["connectivity_keys"])
    if canonical_key_hash(sorted(hold_keys)) != hold["hold"]["connectivity_keys_sha256"]:
        raise PopulationError("holdout manifest hash mismatch (hold)")
    if canonical_key_hash(sorted(ana_keys)) != hold["analysis"]["connectivity_keys_sha256"]:
        raise PopulationError("holdout manifest hash mismatch (analysis)")
    dev_keys = set(dev["connectivity_key"])
    if hold_keys | ana_keys != dev_keys or hold_keys & ana_keys:
        raise PopulationError("holdout manifest does not partition WUR-DEV")
    return sorted(ana_keys)


def wur_analysis_accepted(data_dir: Path,
                          dev: pd.DataFrame | None = None
                          ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Accepted spectra of WUR-DEV-ANALYSIS only, plus the identity rows.

    The accepted-row table is filtered to the analysis keys BEFORE it is
    handed to any peak reader, so neither a sealed nor a held-out blob can be
    decoded by anything downstream of this function.
    """
    if dev is None:
        dev = wur_dev_partition(data_dir)
    keys = set(wur_analysis_keys(dev))
    accepted = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    acc = accepted[accepted["connectivity_key"].isin(keys)].reset_index(drop=True)
    if set(acc["connectivity_key"]) != keys:
        raise PopulationError("accepted rows do not cover exactly the analysis keys")
    forbidden = set(json.loads((ART / "wur_sealed_partition.json").read_text())
                    ["connectivity_keys"]) | set(load_internal_holdout()["hold"]["connectivity_keys"])
    if set(acc["connectivity_key"]) & forbidden:
        raise PopulationError("a forbidden key reached the accepted table")
    ident = dev[dev["connectivity_key"].isin(keys)].reset_index(drop=True)
    return acc, ident


def wur_mu(accepted: pd.DataFrame, data_dir: Path) -> pd.DataFrame:
    """Base-cell mu for the accepted spectra; a peak defect halts."""
    hold = set(load_internal_holdout()["hold"]["connectivity_keys"])
    table, census = build_mu_table(accepted, data_dir, forbidden=hold)
    if census:
        raise PopulationError(f"{len(census)} analysis spectra carry a peak defect: "
                              f"{census[:5]}")
    return table


def wur_covariates(accepted: pd.DataFrame, ident: pd.DataFrame
                   ) -> tuple[pd.DataFrame, list[dict]]:
    """Tier A descriptors for WUR keys from the deposited SMILES.

    `precursor_mz` is the median declared precursor mass over the key's
    accepted spectra. A key whose descriptors cannot be computed is returned
    in the failure list, never silently dropped.
    """
    pm = accepted.groupby("connectivity_key")["precursor_mass"].median()
    rows, failures = [], []
    for r in ident.itertuples(index=False):
        d = tier_a_descriptors(r.smiles)
        if not d:
            failures.append({"connectivity_key": r.connectivity_key,
                             "reason": "RDKit could not parse the deposited SMILES"})
            continue
        d["precursor_mz"] = float(pm.loc[r.connectivity_key])
        if not all(np.isfinite(d[f]) for f in FEATURES):
            failures.append({"connectivity_key": r.connectivity_key,
                             "reason": "non-finite descriptor"})
            continue
        rows.append({"connectivity_key": r.connectivity_key,
                     "scaffold_group": scaffold_group(r.smiles, r.connectivity_key),
                     **{f: float(d[f]) for f in FEATURES}, "source": "WUR"})
    cov = pd.DataFrame(rows, columns=["connectivity_key", "scaffold_group",
                                      *FEATURES, "source"])
    return cov.reset_index(drop=True), failures
