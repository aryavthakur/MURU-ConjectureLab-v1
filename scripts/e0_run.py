"""E0 execution driver.

Usage:
    python scripts/e0_run.py --pilot   # 1 replicate x 9 cells = 9 worlds, timing only
    python scripts/e0_run.py --full    # 60 replicates x 9 cells = 540 worlds, the run

Writes artifacts/e0/e0_worlds.csv, e0_fits.parquet, e0_probes.parquet, and
(full run only) e0_run_manifest.json with environment/cost provenance.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e0_common as e0  # noqa: E402

import numpy as np
import pandas as pd

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e0")


def run(n_replicates: int, label: str) -> dict:
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    manifest = e0.build_world_manifest(n_replicates=n_replicates)

    world_rows = []
    fit_rows = []
    probe_rows = []

    t_start = time.time()
    draws_cache: dict[int, "e0.SharedDraw"] = {}
    for _, row in manifest.sort_values(["replicate", "cell_id"]).iterrows():
        r = int(row["replicate"])
        if r not in draws_cache:
            draws_cache[r] = e0.generate_shared_draw(r, None)
        draw = draws_cache[r]
        wr, frs, prs = e0.run_world(row, draw)
        world_rows.append(wr)
        fit_rows.extend(frs)
        probe_rows.extend(prs)
    wall = time.time() - t_start

    worlds_df = pd.DataFrame(world_rows)
    fits_df = pd.DataFrame(fit_rows)
    probes_df = pd.DataFrame(probe_rows)

    worlds_df.to_csv(os.path.join(ARTIFACT_DIR, f"e0_worlds{'_pilot' if label=='pilot' else ''}.csv"), index=False)
    fits_df.to_parquet(os.path.join(ARTIFACT_DIR, f"e0_fits{'_pilot' if label=='pilot' else ''}.parquet"), index=False)
    probes_df.to_parquet(os.path.join(ARTIFACT_DIR, f"e0_probes{'_pilot' if label=='pilot' else ''}.parquet"), index=False)

    assert "pysr" not in sys.modules, "PySR was imported during E0 execution"

    summary = {
        "label": label,
        "n_worlds": len(worlds_df),
        "n_replicates": n_replicates,
        "n_fit_records": len(fits_df),
        "n_probe_records": len(probes_df),
        "wall_clock_seconds": wall,
        "seconds_per_world": wall / len(worlds_df) if len(worlds_df) else None,
        "cpu_hours_projected_540_worlds": (wall / len(worlds_df) * 540 / 3600.0) if len(worlds_df) else None,
        "pysr_imported": "pysr" in sys.modules,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "platform": platform.platform(),
        "boundary_limited_count": int(worlds_df["boundary_limited"].sum()) if len(worlds_df) else 0,
        "control_cell_worlds": int((worlds_df["cell_id"] == e0.CONTROL_CELL).sum()) if len(worlds_df) else 0,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pilot", action="store_true")
    mode.add_argument("--full", action="store_true")
    args = parser.parse_args()

    if args.pilot:
        summary = run(n_replicates=1, label="pilot")
    else:
        summary = run(n_replicates=e0.N_REPLICATES, label="full")
        summary["source_hashes"] = e0.source_hashes()
        summary["seed_namespace_prefix"] = e0.SEED_NAMESPACE_PREFIX
        summary["control_cell"] = e0.CONTROL_CELL
        summary["decoupled_cell"] = e0.DECOUPLED_CELL
        with open(os.path.join(ARTIFACT_DIR, "e0_run_manifest.json"), "w") as fh:
            json.dump(summary, fh, indent=2, default=str)

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
