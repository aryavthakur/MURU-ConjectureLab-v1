"""Execute the preregistered E3 identifiability oracle over all 10,000 worlds.

No symbolic search anywhere (MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md section
3.3: "No symbolic search is run. No grammar is involved. No complexity
penalty is applied. The oracle is handed the answer set."). Per world:

  1. Generate the world under the V2C namespace (v2c_generator.build_world).
  2. Run the frozen, unmodified Phi/g estimation stage
     (rc5_estimate.fit_case_scalars) to obtain g_hat.
  3. Fit the five closed-form candidate models on the training split against
     g_hat (oracle_models.fit_all_models).
  4. Score every candidate on validation and test; select by BIC and,
     separately, by validation R2.
  5. Persist one record per world.

Usage:
    python3 run_e3.py [--workers N] [--limit N] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import _bootstrap  # noqa: F401
import numpy as np

from manifest import build_manifest, verify_manifest
import oracle_models as om

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results" / "e3_identifiability"


def _nan_to_none(value):
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _split_dict(compounds_with_g, split: str) -> dict:
    sub = compounds_with_g[compounds_with_g["split"] == split]
    return {col: sub[col].to_numpy(dtype=float) for col in ("mass", "descriptor", "descriptor2", "g")}


def _fit_summary(fit: om.ModelFit) -> dict:
    return {
        "converged": fit.converged,
        "params": {k: _nan_to_none(v) for k, v in fit.params.items()},
        "param_se": {k: _nan_to_none(v) for k, v in fit.param_se.items()},
        "rss_train": _nan_to_none(fit.rss_train),
        "n_train": fit.n_train,
        "k_params": fit.k_params,
        "bic": _nan_to_none(fit.bic),
        "r2_train": _nan_to_none(fit.r2_train),
        "r2_val": _nan_to_none(fit.r2_val),
        "r2_test": _nan_to_none(fit.r2_test),
        "n_val": fit.n_val,
        "n_test": fit.n_test,
    }


def run_one_world(cell: dict) -> dict:
    # Imported lazily inside the worker so ProcessPoolExecutor (spawn) workers
    # each perform their own sys.path bootstrap and frozen-module import.
    import _bootstrap  # noqa: F401
    from v2c_generator import build_world
    from muru.paper_benchmark.rc5_estimate import fit_case_scalars
    import oracle_models as om

    family = cell["family"]
    c = cell["c"]
    noise_sd = cell["noise_sd"]
    grid_points = cell["grid_points"]
    replicate = cell["replicate"]

    record = {
        "world_id": cell["world_id"],
        "cell_id": cell["cell_id"],
        "family": family,
        "c": c,
        "noise_sd": noise_sd,
        "grid_points": grid_points,
        "replicate": replicate,
    }

    try:
        world = build_world(family, c, noise_sd, grid_points, replicate)
        scalars = fit_case_scalars(world.compounds, world.trajectories)
        compounds_with_g = world.compounds.assign(g=scalars.g)

        train = _split_dict(compounds_with_g, "train")
        val = _split_dict(compounds_with_g, "validation")
        test = _split_dict(compounds_with_g, "test")

        fits = om.fit_all_models(train, val, test)
        bic_selected = om.select_by_bic(fits)
        r2_selected = om.select_by_val_r2(fits)

        true_model_id = om.FAMILY_TO_MODEL[family]
        rival_model_id = om.NEAREST_RIVAL.get(true_model_id)

        true_fit = fits[true_model_id]
        mass_fit = fits["M_mass"]
        rival_fit = fits.get(rival_model_id) if rival_model_id else None

        delta_r2_vs_mass = (
            None if true_model_id == "M_mass" or not (true_fit.converged and mass_fit.converged)
            else _nan_to_none(true_fit.r2_val - mass_fit.r2_val)
        )
        delta_r2_vs_rival = (
            None if rival_fit is None or not (true_fit.converged and rival_fit.converged)
            else _nan_to_none(true_fit.r2_val - rival_fit.r2_val)
        )

        c_hat = true_fit.params.get("c") if true_fit.converged else None
        c_se = true_fit.param_se.get("c") if true_fit.converged else None
        c_hat_over_se = (
            None if c_hat is None or c_se in (None, 0) or not math.isfinite(c_se)
            else _nan_to_none(c_hat / c_se)
        )

        record.update({
            "seeds": {
                "compounds": world.compounds_seed,
                "law": world.law_seed,
                "response": world.response_seed,
            },
            "law_params": world.law_params,
            "response_params": world.response_params,
            "models": {mid: _fit_summary(fits[mid]) for mid in om.MODEL_IDS},
            "true_model_id": true_model_id,
            "rival_model_id": rival_model_id,
            "bic_selected_model": bic_selected,
            "val_r2_selected_model": r2_selected,
            "oracle_correct_bic": bic_selected == true_model_id,
            "oracle_correct_r2": r2_selected == true_model_id,
            "is_control": family == "mass_power",
            "false_structure_bic": (family == "mass_power") and (bic_selected is not None) and (bic_selected != "M_mass"),
            "false_structure_r2": (family == "mass_power") and (r2_selected is not None) and (r2_selected != "M_mass"),
            "delta_r2_vs_mass": delta_r2_vs_mass,
            "delta_r2_vs_rival": delta_r2_vs_rival,
            "c_hat_over_se": c_hat_over_se,
            "lrt_p_true_vs_mass": _nan_to_none(om.true_vs_mass_lrt_p(true_model_id, fits)),
            "lrt_p_true_vs_rival": _nan_to_none(om.true_vs_rival_lrt_p(true_model_id, fits)),
            "status": "OK",
        })
    except Exception as exc:  # pragma: no cover - defensive; every failure is persisted, not swallowed
        record.update({"status": "EXECUTION_FAILURE", "error": f"{type(exc).__name__}: {exc}"})

    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None, help="run only the first N manifest rows (smoke test)")
    parser.add_argument("--out", type=str, default=str(RESULTS_DIR / "e3_worlds.jsonl"))
    args = parser.parse_args()

    manifest_rows = build_manifest()
    manifest_check = verify_manifest(manifest_rows)
    assert manifest_check["zero_missing"] and manifest_check["zero_duplicates"] and manifest_check["total_matches_expected"], manifest_check

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = RESULTS_DIR / "e3_manifest.json"
    manifest_path.write_text(json.dumps({"manifest_check": manifest_check, "rows": manifest_rows}, indent=1), encoding="utf-8")

    rows = manifest_rows if args.limit is None else manifest_rows[: args.limit]
    out_path = Path(args.out)

    t0 = time.time()
    n_done = 0
    n_failed = 0
    with out_path.open("w", encoding="utf-8") as fh:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_one_world, row): row["world_id"] for row in rows}
            for future in as_completed(futures):
                record = future.result()
                if record.get("status") != "OK":
                    n_failed += 1
                fh.write(json.dumps(record, sort_keys=True) + "\n")
                n_done += 1
                if n_done % 500 == 0 or n_done == len(rows):
                    elapsed = time.time() - t0
                    rate = n_done / elapsed if elapsed > 0 else 0.0
                    print(f"  {n_done}/{len(rows)} worlds done, {n_failed} failed, {elapsed:.1f}s elapsed, {rate:.1f} worlds/s", flush=True)

    print(f"DONE: {n_done} worlds, {n_failed} failures, {time.time()-t0:.1f}s total, written to {out_path}")


if __name__ == "__main__":
    main()
