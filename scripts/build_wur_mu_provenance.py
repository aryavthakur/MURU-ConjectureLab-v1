"""CLI: write artifacts/wur_mu_provenance.json, the per-cell provenance of
the Stage 1 WUR mu table.

Section 5.2 of the preregistration promises that the contributing spectrum
ids, source libraries and n_spectra are preserved for every cell.
`build_mu_table` preserves them, but the gate CLI writes only aggregates, so
this companion persists them.

This does NOT re-run the gate and does not touch artifacts/wur_bridge_gate.json.
It recomputes the same deterministic mu table from the same frozen release and
the same committed code, and records where each value came from. The mu values
it reports must equal the ones the gate used; that equality is the check this
artifact makes possible.
"""
import json
import sys
from pathlib import Path

import pandas as pd

from muru.io import wur_raw
from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_identity import accepted_rows
from muru.io.wur_partition import apply_d6, partition, sealed_scaffold_groups
from muru.io.wur_provenance import environment_provenance
from muru.io.wur_spectra import build_mu_table
from muru.synth.generators import sealed_keys
from muru.wur_bridge import build_population_b

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"

    pre_d6 = partition(load_annotated_trajectories(data_dir))
    partitioned = apply_d6(pre_d6, sealed_scaffold_groups(pre_d6["POS"]))
    pos = partitioned["POS"]
    wur_dev_keys = set(pos.loc[pos["side"] == "WUR-DEV", "connectivity_key"])

    wur_sealed = set(json.loads(
        (ART / "wur_sealed_partition.json").read_text())["connectivity_keys"])
    dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")
    population_b = build_population_b(
        wur_dev_keys, set(dev["inchikey_first_block"]), wur_sealed, sealed_keys())

    accepted = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    accepted_b = accepted[accepted["connectivity_key"].isin(set(population_b))]
    wur_mu, census = build_mu_table(accepted_b, data_dir)

    cells = [
        {
            "connectivity_key": row.connectivity_key,
            "ce_numeric": float(row.ce_numeric),
            "mu": float(row.mu),
            "n_spectra": int(row.n_spectra),
            "spectrum_ids": [list(t) for t in row.spectrum_ids],
            "source_libraries": list(row.source_libraries),
        }
        for row in wur_mu.sort_values(
            ["connectivity_key", "ce_numeric"]).itertuples(index=False)
    ]

    n_spectra = [c["n_spectra"] for c in cells]
    provenance = {
        "purpose": "Per-cell provenance of the Stage 1 WUR mu table, as "
                   "section 5.2 of the preregistration requires. Recomputed "
                   "after the gate run from the same frozen release and the "
                   "same code; it does not re-run the gate.",
        "preregistration": "wur-real-data-1.0, errata E-1, E-2 and E-3",
        "n_population_b": len(population_b),
        "n_cells": len(cells),
        "n_spectra_per_cell_min": min(n_spectra) if n_spectra else 0,
        "n_spectra_per_cell_max": max(n_spectra) if n_spectra else 0,
        "duplicate_aggregator": "median",
        "peak_defect_census": census,
        "environment": environment_provenance(ROOT),
        "cells": cells,
    }
    (ART / "wur_mu_provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n")

    print("Wrote wur_mu_provenance.json")
    print(f"  population B: {len(population_b)}, cells: {len(cells)}, "
          f"spectra per cell: {provenance['n_spectra_per_cell_min']} to "
          f"{provenance['n_spectra_per_cell_max']}")
    if census:
        print(f"  peak defects: {len(census)}", file=sys.stderr)
        sys.exit(1)
