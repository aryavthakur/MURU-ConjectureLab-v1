"""Stage 7: scaffold and data geometry for every Held-out case.

The failure taxonomies need to be able to answer "was this case harder by
construction?" -- how many scaffolds and compounds the case carries, how much
of the energy grid was actually observed, how much missingness it suffered, and
how much spread the covariates the search sees actually have.

All quantities are read off regenerated case content; nothing is fitted and no
search runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    install_frozen_src,
    load_case_manifest,
    load_truth,
    write_json,
)

install_frozen_src()

import numpy as np  # noqa: E402

from muru.paper_benchmark.registry import ENERGY_GRID  # noqa: E402
from muru.paper_benchmark.rc5_runner import materialize_case  # noqa: E402

COVARIATES = ("mass", "descriptor", "descriptor2", "distractor", "correlated_distractor")


def _spread(values: np.ndarray) -> dict:
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
    }


def main() -> int:
    manifest = load_case_manifest()
    truth = load_truth()
    rows = []

    for index, case_id in enumerate(manifest, start=1):
        content = materialize_case(case_id)
        compounds = content.compounds
        trajectories = content.trajectories
        planted = truth[case_id]

        train = compounds[compounds["split"] == "train"]
        test = compounds[compounds["split"] == "test"]

        observed = trajectories.groupby("compound_id")["energy"].nunique()
        expected_cells = len(compounds) * len(ENERGY_GRID)
        observed_cells = len(trajectories)

        row = {
            "case_id": case_id,
            "family_id": case_id.split("|")[2],
            "variant": manifest[case_id]["variant"],
            "truth_family": planted.get("mathematical_family"),
            "scaffolds_total": int(compounds["scaffold_id"].nunique()),
            "scaffolds_train": int(train["scaffold_id"].nunique()),
            "scaffolds_test": int(test["scaffold_id"].nunique()),
            "compounds_total": int(len(compounds)),
            "compounds_train": int(len(train)),
            "compounds_test": int(len(test)),
            "energy_grid_size": len(ENERGY_GRID),
            "observed_cells": int(observed_cells),
            "expected_cells": int(expected_cells),
            "missing_cell_fraction": float(1.0 - observed_cells / expected_cells),
            "observed_energies_min": int(observed.min()),
            "observed_energies_median": float(observed.median()),
            "observed_energies_max": int(observed.max()),
            "compounds_below_5_energies": int((observed < 5).sum()),
            "mu_min": float(trajectories["mu"].min()),
            "mu_max": float(trajectories["mu"].max()),
            "noise_spec": planted.get("noise"),
            "missingness_spec": planted.get("missingness"),
        }
        for name in COVARIATES:
            stats = _spread(compounds[name].to_numpy(dtype=float))
            for key, value in stats.items():
                row[f"{name}_{key}"] = value
        row["mass_range_ratio"] = (
            row["mass_max"] / row["mass_min"] if row["mass_min"] > 0 else None
        )
        rows.append(row)

        if index % 20 == 0 or index == len(manifest):
            print(f"  geometry: {index}/{len(manifest)}", flush=True)

    write_json(OUT_DIR / "case_geometry.json", {"cases": len(rows), "per_case": rows})
    print(f"  wrote {OUT_DIR / 'case_geometry.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
