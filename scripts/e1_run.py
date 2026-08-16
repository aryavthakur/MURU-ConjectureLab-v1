"""E1 production/pilot runner.

Usage:
    python3 scripts/e1_run.py --pilot                 # 5-fit-unit pilot (protocol Sec 8)
    python3 scripts/e1_run.py --full --workers 8       # full 11,475-fit-unit run
    python3 scripts/e1_run.py --cells CELL1,CELL2 ...  # ad hoc subset (diagnostics only)

Writes one parquet (or csv fallback) file per shard of compound-level
records (e1_fit.aggregate_compound output) plus one world-level manifest
row per fit unit (for the control-arm / abort-gate sanity checks). No PySR
import anywhere in this process.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from multiprocessing import get_context

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS_DIR)
_SRC_DIR = os.path.join(os.path.dirname(_THIS_DIR), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import e1_common as e1c  # noqa: E402
import e1_fit as e1f  # noqa: E402

assert "pysr" not in sys.modules, "E1 must never import PySR"


def run_fit_unit(cell_row: dict) -> tuple[dict, list[dict]]:
    """Run one (D, alpha, noise, mu_ceil_level, replicate) fit unit.

    Returns (world_summary_row, [compound_row, ...]) -- 3 detectors x 30 test
    compounds = 90 compound rows.
    """
    from muru.paper_benchmark import adequacy, rc5_adequacy, rc5_estimate

    replicate = int(cell_row["replicate"])
    noise = float(cell_row["noise_level"])
    draw = e1c.generate_shared_draw(replicate, noise)
    traj = e1c.build_trajectories(draw, cell_row["D"], float(cell_row["alpha"]))
    frozen_phi = rc5_estimate.fit_case_phi(draw.compounds, traj)
    shape = rc5_adequacy.ProfileShape.from_phi(frozen_phi)

    prev_ceil = rc5_adequacy.MU_CEIL
    rc5_adequacy.MU_CEIL = float(cell_row["mu_ceil_value"])
    compound_rows: list[dict] = []
    try:
        test_ids = draw.compounds.loc[draw.compounds["split"] == "test", "compound_id"].tolist()
        contrast_records: dict[str, list] = {d: [] for d in adequacy.DETECTORS}
        for detector in ("M1", "M2", "M3"):
            for cid in test_ids:
                sub = traj[traj["compound_id"] == cid]
                energies = sub["energy"].to_numpy()
                mu = sub["mu"].to_numpy()
                rec, folds = e1f.instrumented_compound_contrast(cid, detector, energies, mu, shape)
                contrast_records[detector].append(rec)
                agg = e1f.aggregate_compound(rec, folds)
                agg.update(
                    world_id=cell_row["world_id"], cell_id=cell_row["cell_id"],
                    D=cell_row["D"], alpha=cell_row["alpha"], noise_level=noise,
                    mu_ceil_level=cell_row["mu_ceil_level"], replicate=replicate,
                    split=cell_row["split"], is_null=cell_row["is_null"],
                )
                compound_rows.append(agg)
        case_result = adequacy.decide_case_adequacy(cell_row["world_id"], contrast_records)
    finally:
        rc5_adequacy.MU_CEIL = prev_ceil

    world_row = {
        "world_id": cell_row["world_id"], "cell_id": cell_row["cell_id"],
        "D": cell_row["D"], "alpha": cell_row["alpha"], "noise_level": noise,
        "mu_ceil_level": cell_row["mu_ceil_level"], "replicate": replicate,
        "split": cell_row["split"], "is_null": cell_row["is_null"],
        "c0_case_status": case_result.status.value,
        "c0_fired": ",".join(case_result.fired),
        "c0_false_m0_rejection": case_result.status.value.startswith("M0_REJECTED"),
        "mu_inf": draw.mu_inf, "phi_p": draw.phi_p,
        "content_hash": e1c.world_content_hash(draw.compounds, traj),
    }
    return world_row, compound_rows


def _worker(args):
    idx, cell_row = args
    try:
        return run_fit_unit(cell_row)
    except Exception as exc:  # pragma: no cover - surfaced to caller
        return {"world_id": cell_row["world_id"], "ERROR": repr(exc)}, []


def run_batch(manifest: pd.DataFrame, workers: int, out_dir: str, shard_size: int = 500, label: str = "run"):
    os.makedirs(out_dir, exist_ok=True)
    rows = manifest.to_dict("records")
    n = len(rows)
    t0 = time.time()
    world_rows: list[dict] = []
    compound_rows: list[dict] = []
    errors: list[dict] = []
    shard_idx = 0

    def flush():
        nonlocal compound_rows, shard_idx
        if not compound_rows:
            return
        df = pd.DataFrame(compound_rows)
        path = os.path.join(out_dir, f"compounds_{label}_{shard_idx:05d}.parquet")
        try:
            df.to_parquet(path, index=False)
        except Exception:
            df.to_csv(path.replace(".parquet", ".csv"), index=False)
        shard_idx += 1
        compound_rows = []

    ctx = get_context("spawn")
    with ctx.Pool(processes=workers) as pool:
        for i, (world_row, comp_rows) in enumerate(pool.imap_unordered(_worker, enumerate(rows), chunksize=4)):
            if "ERROR" in world_row:
                errors.append(world_row)
                continue
            world_rows.append(world_row)
            compound_rows.extend(comp_rows)
            if len(compound_rows) >= shard_size * 90:
                flush()
            if (i + 1) % max(1, n // 20) == 0 or (i + 1) == n:
                elapsed = time.time() - t0
                print(f"[{label}] {i+1}/{n} fit units, {elapsed:.1f}s elapsed, "
                      f"{elapsed/(i+1):.4f}s/unit, ETA {(elapsed/(i+1))*(n-i-1):.1f}s", flush=True)
    flush()

    world_df = pd.DataFrame(world_rows)
    world_path = os.path.join(out_dir, f"worlds_{label}.parquet")
    try:
        world_df.to_parquet(world_path, index=False)
    except Exception:
        world_df.to_csv(world_path.replace(".parquet", ".csv"), index=False)

    elapsed = time.time() - t0
    manifest_out = {
        "label": label, "n_fit_units": n, "n_errors": len(errors),
        "elapsed_seconds": elapsed, "seconds_per_fit_unit": elapsed / max(n, 1),
        "workers": workers, "pysr_imported": "pysr" in sys.modules,
        "errors": errors[:20],
    }
    with open(os.path.join(out_dir, f"run_manifest_{label}.json"), "w") as fh:
        json.dump(manifest_out, fh, indent=2, default=str)
    print(json.dumps(manifest_out, indent=2, default=str))
    return manifest_out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--n-replicates", type=int, default=e1c.N_REPLICATES)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out-dir", type=str, default="artifacts/e1")
    ap.add_argument("--label", type=str, default=None)
    args = ap.parse_args()

    assert "pysr" not in sys.modules

    if args.pilot:
        # Protocol Sec 8: 5 diverse fit units, one MU_CEIL level each.
        cells = e1c.full_grid_cells()
        by_id = {c["cell_id"]: c for c in cells}
        picks = [
            "M0_a000_n002_c1e4",       # control-analogue (null, default noise, v1 ceiling)
            "M3_a025_n000_c1e4",       # small alpha extreme
            "M1M2M3_a200_n006_copen",  # large alpha extreme, high noise, open ceiling
            "M2_a100_n000_c1e3",       # mid alpha, middle ceiling
            "M1_a050_n006_c1e4",       # different D, high noise
        ]
        pilot_rows = []
        for cid in picks:
            c = by_id[cid]
            pilot_rows.append({
                "world_id": f"V2C|E1|{cid}|r000", "cell_id": cid,
                "D": c["D"], "alpha": c["alpha"], "noise_level": c["noise"],
                "is_null": c["is_null"], "mu_ceil_level": c["mu_ceil_level"],
                "mu_ceil_value": c["mu_ceil_value"], "replicate": 0, "split": "CALIBRATE",
            })
        manifest = pd.DataFrame(pilot_rows)
        run_batch(manifest, workers=min(args.workers, 5), out_dir=args.out_dir, label=args.label or "pilot")
    elif args.full:
        manifest = e1c.build_world_manifest(n_replicates=args.n_replicates)
        run_batch(manifest, workers=args.workers, out_dir=args.out_dir, label=args.label or "full")
    else:
        raise SystemExit("pass --pilot or --full")


if __name__ == "__main__":
    main()
