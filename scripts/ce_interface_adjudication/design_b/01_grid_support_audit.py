"""Design B planning: metadata-only training-support audit of candidate NCE grids.

Reads only the reconstructed MassSpecGym 1.5 CE metadata (Phase 0/P3 artifacts). Runs no model,
reads no spectrum, touches no Design A outcome. Design cells are (stratum, NCE, m/z) with m/z on a
0.5 Da grid across each window, strata weighted equally.
"""
import json
import numpy as np
import pandas as pd

A = "artifacts/ce_interface_adjudication"
rows = pd.read_parquet(f"{A}/p3_msg15_row_source_attribution.parquet")
meta = pd.read_parquet(f"{A}/massspecgym15_metadata_columns.parquet")
t = rows[rows.simulation_challenge & rows.collision_energy.notna()].merge(
    meta[["identifier", "precursor_mz"]], on="identifier", how="left")
assert len(t) == 119029 and t.precursor_mz.notna().all()
ce, mz = t.collision_energy.to_numpy(), t.precursor_mz.to_numpy()
q = {k: float(np.quantile(ce, p)) for k, p in [("q01", .01), ("q05", .05), ("q95", .95), ("q99", .99)]}
q.update(min=float(ce.min()), max=float(ce.max()))

STRATA = {"L": (130.0, 300.0), "N": (485.0, 515.0), "H": (700.0, 900.0)}
GRIDS = {"G6_15_90": [15, 30, 45, 60, 75, 90], "G5_15_75": [15, 30, 45, 60, 75]}
ALIAS = [5.95, 11.95, 18.15]  # Phase 0 section 6 near-alias differences


def local_support(c0, c1, lo, hi):
    """Training rows in the same mass window whose CE lies in [c0 - 5, c1 + 5]."""
    return int(((mz >= lo) & (mz <= hi) & (ce >= c0 - 5) & (ce <= c1 + 5)).sum())


out = {"training_numeric_ce": q, "training_rows_per_window": {s: int(((mz >= lo) & (mz <= hi)).sum()) for s, (lo, hi) in STRATA.items()}, "n_training_rows": len(t), "grids": {}}
for g, grid in GRIDS.items():
    res = {"per_mapping": {}, "cells": []}
    for K in ("K1", "K2"):
        vals, w = [], []
        for s, (lo, hi) in STRATA.items():
            m = np.arange(lo, hi + 1e-9, 0.5)
            for n in grid:
                v = np.full_like(m, n) if K == "K1" else n * m / 500.0
                vals.append(v); w.append(np.full_like(m, 1.0 / (len(m) * len(grid) * 3)))
                res["cells"].append(dict(mapping=K, stratum=s, nce=n, ce_min=round(float(v.min()), 2),
                                         ce_max=round(float(v.max()), 2),
                                         frac_above_q95=round(float((v > q["q95"]).mean()), 3),
                                         frac_above_q99=round(float((v > q["q99"]).mean()), 3),
                                         support_rows_in_window=local_support(float(v.min()), float(v.max()), lo, hi),
                                         support_rows_at_ce_max=local_support(float(v.max()), float(v.max()), lo, hi)))
        v, w = np.concatenate(vals), np.concatenate(w)
        res["per_mapping"][K] = dict(ce_min=round(float(v.min()), 2), ce_max=round(float(v.max()), 2),
                                     frac_above_q95=round(float(w[v > q["q95"]].sum()), 4),
                                     frac_above_q99=round(float(w[v > q["q99"]].sum()), 4),
                                     frac_outside_min_max=round(float(w[(v < q["min"]) | (v > q["max"])].sum()), 4))
    # K1-K2 numerical separation in the divergent strata
    d = np.concatenate([np.abs(n - n * np.arange(lo, hi + 1e-9, 0.5) / 500.0)
                        for s, (lo, hi) in STRATA.items() if s != "N" for n in grid])
    res["divergent_abs_K1_minus_K2"] = dict(min=round(float(d.min()), 2), max=round(float(d.max()), 2),
                                            frac_within_0p5_of_near_alias=round(float(
                                                np.any([np.abs(d - a) <= 0.5 for a in ALIAS], axis=0).mean()), 4))
    dn = np.concatenate([np.abs(n - n * np.arange(485, 515.01, 0.5) / 500.0) for n in grid])
    res["null_abs_K1_minus_K2_max"] = round(float(dn.max()), 2)
    out["grids"][g] = res

json.dump(out, open(f"{A}/design_b/grid_support_audit.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("training_numeric_ce",)}, indent=0))
for g, r in out["grids"].items():
    print(g, json.dumps(r["per_mapping"]), r["divergent_abs_K1_minus_K2"], "null max", r["null_abs_K1_minus_K2_max"])
    for c in r["cells"]:
        if c["frac_above_q95"] > 0 or c["support_rows_in_window"] < 200:
            print("  ", c)
