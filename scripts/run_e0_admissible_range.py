#!/usr/bin/env python
"""Execute E0, `A1_ADMISSIBLE_RANGE_PROVENANCE`.

Generates the 3 x 3 x 60 corpus of fresh true-M0 `V2C` worlds, runs the frozen
A1 adequacy pass on each under that cell's injected `MU_CEIL`, and persists
fit-level records.  Runs no symbolic search and imports no search engine.

Usage
-----
    python scripts/run_e0_admissible_range.py --pilot 5      # cost measurement
    python scripts/run_e0_admissible_range.py                # full 540 worlds

Analysis is a separate entry point (`scripts/analyse_e0.py`) so that generation
cannot be re-run after a result is seen without that being visible in the
manifest.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from muru.paper_benchmark.rc5_estimate import fit_case_phi  # noqa: E402
from muru.v2_calibration import e0_cells  # noqa: E402
from muru.v2_calibration.e0_instrument import (  # noqa: E402
    assert_pysr_absent,
    block_pysr_imports,
    mu_ceil_injected,
    run_case_adequacy_instrumented,
)
from muru.v2_calibration.e0_seeds import assert_namespace_disjoint, e0_seed, e0_world_id  # noqa: E402
from muru.v2_calibration.e0_worlds import E0_LAW_KIND, E0_NOISE_SD, draw_base, render  # noqa: E402

OUT = REPO / "artifacts" / "e0"


def run_world(base, cell: e0_cells.Cell) -> tuple[dict, list[dict], list[dict]]:
    world_id = e0_world_id(cell.cell_id, base.replicate)
    world = render(base, cell.cell_id, world_id, cell.generator_clip)

    phi = fit_case_phi(world.compounds, world.trajectories)
    context = {
        "world_id": world_id,
        "cell_id": cell.cell_id,
        "replicate": base.replicate,
    }
    with mu_ceil_injected(cell.fitter_mu_ceil):
        result, fits, contrasts = run_case_adequacy_instrumented(
            world_id, world.compounds, world.trajectories, phi, context
        )

    # Test-compound response geometry, measured on the rendered world.
    test_mask = (world.compounds["split"] == "test").to_numpy()
    mu_test = world.mu[test_mask]
    mu_max_per_compound = mu_test.max(axis=1)
    at_clip = (
        0 if cell.generator_clip is None
        else int(np.count_nonzero(mu_max_per_compound == cell.generator_clip))
    )
    at_v1 = int(np.count_nonzero(mu_max_per_compound == 1.0 - 1e-4))

    unresolved = [f for f in fits if f["unresolved_boundary"] and f["dominant_bound_hit"]]
    dominant = (
        pd.Series([f["dominant_bound_hit"] for f in unresolved]).value_counts().index[0]
        if unresolved else None
    )

    row = {
        **context,
        "generator_clip": cell.generator_clip,
        "fitter_mu_ceil": cell.fitter_mu_ceil,
        "coupled": cell.coupled,
        "case_status": result.status.value,
        "fired": ",".join(result.fired),
        "n_fired": len(result.fired),
        "dominant_bound_hit": dominant,
        "ceiling_clip_activations": world.ceiling_clip_activations,
        "floor_clip_activations": world.floor_clip_activations,
        "test_compounds_mu_max_at_clip": at_clip,
        "test_compounds_mu_max_at_v1_constant": at_v1,
        "mu_max_test": float(mu_max_per_compound.max()),
        "mu_inf": base.mu_inf,
        "phi_p": base.phi_p,
        "shape_a_lo": float(phi.values[0]),
        "shape_a_hi": float(phi.values[-1]),
        "base_fingerprint": world.base_fingerprint,
        "content_hash": world.content_hash,
    }
    for detector in ("M1", "M2", "M3"):
        contrast = result.contrasts[detector]
        row[f"evaluable_{detector}"] = contrast.evaluable
        row[f"wins_{detector}"] = contrast.practical_wins
        row[f"fired_{detector}"] = contrast.fired
        row[f"boundary_limited_compounds_{detector}"] = contrast.status_counts["BOUNDARY_LIMITED"]
    return row, fits, contrasts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=int, default=0, help="run N replicates and stop")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    namespace = assert_namespace_disjoint()
    n_replicates = args.pilot if args.pilot else e0_cells.N_REPLICATES
    label = "pilot" if args.pilot else "full"
    args.out.mkdir(parents=True, exist_ok=True)

    world_rows: list[dict] = []
    fit_rows: list[dict] = []
    contrast_rows: list[dict] = []

    start = time.time()
    with block_pysr_imports():
        for replicate in range(n_replicates):
            base = draw_base(replicate, e0_seed)
            for cell in e0_cells.CELLS:
                row, fits, contrasts = run_world(base, cell)
                world_rows.append(row)
                fit_rows.extend(fits)
                contrast_rows.extend(contrasts)
            done = replicate + 1
            elapsed = time.time() - start
            print(
                f"[{label}] replicate {done}/{n_replicates}  "
                f"worlds={len(world_rows)}  {elapsed:.1f}s  "
                f"{elapsed / (done * len(e0_cells.CELLS)):.3f}s/world",
                flush=True,
            )
    elapsed = time.time() - start
    assert_pysr_absent()

    worlds = pd.DataFrame(world_rows)
    fits_df = pd.DataFrame(fit_rows)
    contrasts_df = pd.DataFrame(contrast_rows)

    suffix = f"_{label}" if args.pilot else ""
    worlds.to_csv(args.out / f"e0_worlds{suffix}.csv", index=False)
    fits_df.to_parquet(args.out / f"e0_fits{suffix}.parquet", index=False)
    contrasts_df.to_parquet(args.out / f"e0_contrasts{suffix}.parquet", index=False)

    manifest = {
        "experiment": "E0",
        "name": "A1_ADMISSIBLE_RANGE_PROVENANCE",
        "run_label": label,
        "n_replicates": n_replicates,
        "n_cells": len(e0_cells.CELLS),
        "n_worlds": len(worlds),
        "fits_per_world": len(fits_df) // max(len(worlds), 1),
        "n_fit_records": len(fits_df),
        "n_contrast_records": len(contrasts_df),
        "world_configuration": {
            "law": E0_LAW_KIND,
            "noise_sd": E0_NOISE_SD,
            "truth": "M0",
            "compounds": 180,
            "test_compounds": 30,
            "energies": 6,
        },
        "namespace": namespace,
        "wall_clock_seconds": elapsed,
        "seconds_per_world": elapsed / max(len(worlds), 1),
        "cpu_hours_measured": elapsed / 3600.0,
        "cpu_hours_projected_540_worlds": (elapsed / max(len(worlds), 1)) * 540 / 3600.0,
        "symbolic_search_runs": 0,
        "pysr_imported": False,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "platform": platform.platform(),
    }
    (args.out / f"e0_run_manifest{suffix}.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps({k: manifest[k] for k in (
        "n_worlds", "n_fit_records", "wall_clock_seconds",
        "seconds_per_world", "cpu_hours_projected_540_worlds")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
