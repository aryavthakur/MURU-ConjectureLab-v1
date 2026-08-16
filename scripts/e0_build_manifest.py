"""E0 pre-execution manifest and the six preregistered assertions.

Run before any world is fitted. Writes artifacts/e0/e0_manifest.json and
artifacts/e0/e0_world_index.csv. Exits non-zero (aborting the run) if any
assertion fails.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e0_common as e0  # noqa: E402

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e0")


def assert_world_count(manifest, n) -> dict:
    ok = len(manifest) == n
    return {"check": "world_count_540", "expected": n, "actual": len(manifest), "pass": ok}


def assert_cells_present(manifest) -> dict:
    expected_cells = set(e0.all_cells())
    actual_cells = set(manifest["cell_id"].unique())
    ok = expected_cells == actual_cells and len(expected_cells) == 9
    return {
        "check": "all_9_design_cells_present",
        "expected": sorted(expected_cells),
        "actual": sorted(actual_cells),
        "pass": ok,
    }


def assert_replicates_per_cell(manifest, n_replicates) -> dict:
    counts = manifest.groupby("cell_id")["replicate"].count().to_dict()
    ok = all(v == n_replicates for v in counts.values()) and len(counts) == 9
    return {"check": "exact_replicates_per_cell", "expected": n_replicates, "actual": counts, "pass": ok}


def assert_no_duplicates(manifest) -> dict:
    dup_world = manifest["world_id"].duplicated().sum()
    seed_triples = list(zip(manifest["seed_compounds"], manifest["seed_law"], manifest["seed_response"], manifest["cell_id"]))
    dup_seed_cell = len(seed_triples) - len(set(seed_triples))
    # Seeds are shared by design across cells at fixed replicate (that's the point);
    # duplication would only be a defect within one cell (same cell, same seed twice).
    per_cell_seed_dupe = 0
    for cell_id, group in manifest.groupby("cell_id"):
        per_cell_seed_dupe += group["seed_compounds"].duplicated().sum()
    ok = dup_world == 0 and per_cell_seed_dupe == 0
    return {
        "check": "no_duplicate_world_or_within_cell_seed_ids",
        "duplicate_world_ids": int(dup_world),
        "duplicate_seeds_within_a_cell": int(per_cell_seed_dupe),
        "pass": bool(ok),
    }


def assert_factor_assignment(manifest) -> dict:
    import pandas as pd

    problems = []
    for g_level, g_value in e0.C_GEN_LEVELS.items():
        rows = manifest[manifest["c_gen_level"] == g_level]
        vals = rows["c_gen_value"].tolist()
        if g_value is None:
            bad = [v for v in vals if not pd.isna(v)]
        else:
            bad = [v for v in vals if pd.isna(v) or v != g_value]
        if bad:
            problems.append({"factor": "c_gen", "level": g_level, "expected": g_value, "bad_values": bad[:5]})
    for c_level, c_value in e0.MU_CEIL_LEVELS.items():
        rows = manifest[manifest["mu_ceil_level"] == c_level]
        vals = rows["mu_ceil_value"].tolist()
        bad = [v for v in vals if v != c_value]
        if bad:
            problems.append({"factor": "mu_ceil", "level": c_level, "expected": c_value, "bad_values": bad[:5]})
    return {"check": "generator_fitter_factor_assignment_matches_design", "problems": problems, "pass": len(problems) == 0}


def assert_source_hashes() -> dict:
    hashes = e0.source_hashes()
    ok = all(isinstance(v, str) and len(v) == 64 for v in hashes.values())
    return {"check": "source_config_hashes_recorded", "hashes": hashes, "pass": ok}


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    manifest = e0.build_world_manifest()

    checks = [
        assert_world_count(manifest, 540),
        assert_cells_present(manifest),
        assert_replicates_per_cell(manifest, e0.N_REPLICATES),
        assert_no_duplicates(manifest),
        assert_factor_assignment(manifest),
        assert_source_hashes(),
    ]

    manifest.to_csv(os.path.join(ARTIFACT_DIR, "e0_world_index.csv"), index=False)

    all_pass = all(c["pass"] for c in checks)
    out = {
        "experiment": "E0",
        "name": "A1_ADMISSIBLE_RANGE_PROVENANCE",
        "n_worlds": len(manifest),
        "n_cells": manifest["cell_id"].nunique(),
        "n_replicates": e0.N_REPLICATES,
        "control_cell": e0.CONTROL_CELL,
        "decoupled_cell": e0.DECOUPLED_CELL,
        "checks": checks,
        "all_checks_pass": all_pass,
    }
    with open(os.path.join(ARTIFACT_DIR, "e0_manifest.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)

    for c in checks:
        status = "PASS" if c["pass"] else "FAIL"
        print(f"[{status}] {c['check']}")
    if not all_pass:
        print("MANIFEST ASSERTIONS FAILED -- ABORTING BEFORE ANY WORLD IS FITTED", file=sys.stderr)
        sys.exit(1)
    print(f"All 6 manifest assertions pass. {len(manifest)} worlds ready.")


if __name__ == "__main__":
    main()
