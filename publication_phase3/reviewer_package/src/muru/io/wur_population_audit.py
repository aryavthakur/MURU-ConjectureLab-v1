"""Identity-only correctness audit of the Stage 0 population definition.

`build_qualifying_trajectories` calls a connectivity key qualifying when the
UNION of its accepted rows covers the six-point ladder, then picks the modal
adduct. That union is doing real work only if ladders are ever completed by
mixing adducts or by mixing source deposits. This module measures whether
they are, before any mu exists, so that a population-definition defect is
caught as a Stage 0 issue rather than silently absorbed by the Stage 1 mu
builder.

Reads identity columns only. No peak data.
"""
from datetime import datetime, timezone

import pandas as pd

from muru.io.wur_identity import LADDER_ENERGIES


def audit_population(accepted: pd.DataFrame) -> dict:
    """The three population-definition questions, over one polarity's
    accepted-row table."""
    ladder = set(LADDER_ENERGIES)
    qualifying = sorted(
        key for key, grp in accepted.groupby("connectivity_key")
        if set(grp["energy"]) == ladder
    )
    q = accepted[accepted["connectivity_key"].isin(qualifying)]

    multi_adduct = sorted(
        key for key, grp in q.groupby("connectivity_key")
        if grp["adduct"].nunique() > 1
    )
    only_across_adducts = sorted(
        key for key, grp in q.groupby("connectivity_key")
        if not any(set(sub["energy"]) == ladder
                   for _, sub in grp.groupby("adduct"))
    )
    only_across_libraries = sorted(
        key for key, grp in q.groupby("connectivity_key")
        if not any(set(sub["energy"]) == ladder
                   for _, sub in grp.groupby("source_library"))
    )
    return {
        "n_accepted_rows": int(len(accepted)),
        "n_qualifying_keys": len(qualifying),
        "n_keys_multi_adduct": len(multi_adduct),
        "keys_multi_adduct": multi_adduct,
        "n_keys_complete_only_across_adducts": len(only_across_adducts),
        "keys_complete_only_across_adducts": only_across_adducts,
        "n_keys_complete_only_across_libraries": len(only_across_libraries),
        "keys_complete_only_across_libraries": only_across_libraries,
        "is_clean": not (multi_adduct or only_across_adducts
                         or only_across_libraries),
    }


def build_population_audit(accepted: dict[str, pd.DataFrame]) -> dict:
    """The audit over both polarities, as a writable artifact."""
    polarities = {pf: audit_population(df) for pf, df in accepted.items()}
    return {
        "purpose": "Identity-only correctness audit of the Stage 0 "
                   "population definition. Run before any mu exists.",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "questions": {
            "multi_adduct": "qualifying keys carrying more than one inferred "
                            "adduct across accepted rows",
            "complete_only_across_adducts": "six-energy ladders that stop "
                                            "being complete when completeness "
                                            "is required within one adduct",
            "complete_only_across_libraries": "six-energy ladders that exist "
                                              "only because rows from "
                                              "different source deposits were "
                                              "unioned",
        },
        "polarities": polarities,
        "is_clean": all(p["is_clean"] for p in polarities.values()),
    }
