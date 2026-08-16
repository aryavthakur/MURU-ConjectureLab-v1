"""The preregistered E3 cell/world manifest.

MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md section 3.6 / MURU_V2_REMEDIATION_
EXPERIMENT_PLAN.json `E3.case_count`: 5 families x 5 coefficients x 4 noise
levels x 2 energy grids x 50 replicates = 10,000 worlds, no search.

This module only enumerates the Cartesian product and assigns each world a
unique, deterministic `world_id`. It performs no generation and no fitting.
"""
from __future__ import annotations

import _bootstrap  # noqa: F401  (puts the frozen src tree + this dir on sys.path)
from v2c_generator import TRUTH_FAMILIES

FAMILIES = TRUTH_FAMILIES  # ("mass_power", "mass_affine_descriptor", "mass_saturating_descriptor", "mass_interaction", "mass_exponential_descriptor")
COEFFICIENTS = (0.25, 0.40, 0.55, 1.1, 2.2)
NOISE_LEVELS = (0.0, 0.02, 0.0295, 0.06)
GRID_POINTS = (6, 12)
N_REPLICATES = 50

EXPECTED_TOTAL = len(FAMILIES) * len(COEFFICIENTS) * len(NOISE_LEVELS) * len(GRID_POINTS) * N_REPLICATES
assert EXPECTED_TOTAL == 10_000, EXPECTED_TOTAL


def cell_id(family: str, c: float, noise_sd: float, grid_points: int) -> str:
    return f"{family}|c{c:g}|noise{noise_sd:g}|grid{grid_points}"


def world_id(family: str, c: float, noise_sd: float, grid_points: int, replicate: int) -> str:
    return f"V2C|E3|{family}|c{c:g}|noise{noise_sd:g}|grid{grid_points}|r{replicate:03d}"


def build_manifest() -> list[dict]:
    rows = []
    for family in FAMILIES:
        for c in COEFFICIENTS:
            for noise_sd in NOISE_LEVELS:
                for grid_points in GRID_POINTS:
                    for replicate in range(N_REPLICATES):
                        rows.append({
                            "world_id": world_id(family, c, noise_sd, grid_points, replicate),
                            "cell_id": cell_id(family, c, noise_sd, grid_points),
                            "family": family,
                            "c": c,
                            "noise_sd": noise_sd,
                            "grid_points": grid_points,
                            "replicate": replicate,
                        })
    return rows


def verify_manifest(rows: list[dict]) -> dict:
    """0 missing cells, 0 duplicate IDs, exact Cartesian-product coverage."""
    ids = [r["world_id"] for r in rows]
    unique_ids = set(ids)
    expected_cells = {
        cell_id(family, c, noise_sd, grid_points)
        for family in FAMILIES for c in COEFFICIENTS
        for noise_sd in NOISE_LEVELS for grid_points in GRID_POINTS
    }
    observed_cells = {r["cell_id"] for r in rows}
    cell_replicate_counts = {}
    for r in rows:
        cell_replicate_counts.setdefault(r["cell_id"], set()).add(r["replicate"])

    missing_cells = expected_cells - observed_cells
    extra_cells = observed_cells - expected_cells
    cells_wrong_replicate_count = {
        cid: sorted(reps) for cid, reps in cell_replicate_counts.items()
        if reps != set(range(N_REPLICATES))
    }

    return {
        "total_rows": len(rows),
        "expected_total": EXPECTED_TOTAL,
        "total_matches_expected": len(rows) == EXPECTED_TOTAL,
        "unique_world_ids": len(unique_ids),
        "duplicate_world_id_count": len(ids) - len(unique_ids),
        "expected_cell_count": len(expected_cells),
        "observed_cell_count": len(observed_cells),
        "missing_cells": sorted(missing_cells),
        "extra_cells": sorted(extra_cells),
        "cells_wrong_replicate_count": cells_wrong_replicate_count,
        "zero_missing": len(missing_cells) == 0,
        "zero_duplicates": len(ids) == len(unique_ids),
        "zero_extra": len(extra_cells) == 0,
        "all_cells_full_replicate_set": len(cells_wrong_replicate_count) == 0,
    }


if __name__ == "__main__":
    import json
    manifest_rows = build_manifest()
    report = verify_manifest(manifest_rows)
    print(json.dumps(report, indent=2, default=str))
