"""Build the v2 spectrum-level tables (WUR positive mode, LCSB dev) and the
aggregated cell table. Identity plus exposed outcomes only."""
import json, sys, time
from pathlib import Path
import pandas as pd
from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import apply_d6, partition, sealed_scaffold_groups
from muru.wur_v2 import spectra as SP
from muru.wur_v2.exposure import lcsb_confirmation_keys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "wur_v2" / "data"
OUT.mkdir(parents=True, exist_ok=True)
data_dir = ROOT / "data" / "external" / "wur"
t0 = time.time()
pre = partition(load_annotated_trajectories(data_dir))
part = apply_d6(pre, sealed_scaffold_groups(pre["POS"]))
pos = part["POS"]
pos[["connectivity_key", "smiles", "adduct", "scaffold_group", "in_lcsb_dev", "in_lcsb_sealed", "side",
     "n_source_rows"]].assign(source_libraries=pos["source_libraries"].map(lambda t: ";".join(t))).to_csv(
    OUT / "wur_pos_identity.csv", index=False)
spec = SP.wur_pos_spectra(data_dir, set(pos["connectivity_key"]))
spec.to_parquet(OUT / "wur_pos_spectra.parquet", index=False)
cells = SP.aggregate_cells(spec)
cells.to_csv(OUT / "wur_pos_cells.csv", index=False)
lc = SP.lcsb_dev_spectra(lcsb_confirmation_keys())
lc.to_parquet(OUT / "lcsb_pos_spectra.parquet", index=False)
print(json.dumps({"n_wur_keys": int(pos.connectivity_key.nunique()), "n_wur_spectra": len(spec),
                  "defects": int((spec.defect != "").sum()), "n_cells": len(cells),
                  "n_lcsb_spectra": len(lc), "seconds": round(time.time() - t0, 1)}, indent=1))
