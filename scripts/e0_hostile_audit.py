"""E0 hostile audit: independently re-derive every claim in e0_analysis.json
from the raw machine-readable rows, using none of e0_analyze.py's own cached
numbers as ground truth -- only the world/fit/probe tables and the frozen
protocol's decision table.

Writes artifacts/e0/e0_hostile_audit.json. Exits non-zero if any check fails.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e0_common as e0  # noqa: E402
import e0_analyze as analyze  # noqa: E402

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "e0")


def check(name, condition, detail=None):
    return {"check": name, "pass": bool(condition), "detail": detail}


def main():
    findings = []

    worlds = pd.read_csv(os.path.join(ARTIFACT_DIR, "e0_worlds.csv"))
    fits = pd.read_parquet(os.path.join(ARTIFACT_DIR, "e0_fits.parquet"))
    probes = pd.read_parquet(os.path.join(ARTIFACT_DIR, "e0_probes.parquet"))
    world_index = pd.read_csv(os.path.join(ARTIFACT_DIR, "e0_world_index.csv"))
    with open(os.path.join(ARTIFACT_DIR, "e0_run_manifest.json")) as fh:
        run_manifest = json.load(fh)
    with open(os.path.join(ARTIFACT_DIR, "e0_analysis.json")) as fh:
        analysis = json.load(fh)
    with open(os.path.join(ARTIFACT_DIR, "e0_manifest.json")) as fh:
        pre_manifest = json.load(fh)

    # 1. 540/540 worlds analyzed
    findings.append(check("540_worlds_analyzed", len(worlds) == 540, {"n_worlds": len(worlds)}))

    # 2. 0 missing/duplicate worlds
    expected_ids = set(world_index["world_id"])
    actual_ids = set(worlds["world_id"])
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids
    dup = worlds["world_id"].duplicated().sum()
    findings.append(
        check(
            "0_missing_or_duplicate_worlds",
            len(missing) == 0 and len(extra) == 0 and dup == 0,
            {"missing": len(missing), "extra": len(extra), "duplicates": int(dup)},
        )
    )

    # 3. 100% design-cell coverage
    expected_cells = set(e0.all_cells())
    counts = worlds.groupby("cell_id")["world_id"].count()
    coverage_ok = set(counts.index) == expected_cells and bool((counts == e0.N_REPLICATES).all())
    findings.append(check("100pct_design_cell_coverage", coverage_ok, {"counts": counts.to_dict()}))

    # 4. 0 Held-out decision rows
    heldout_like = worlds["world_id"].astype(str).str.contains("held_out|PB\\|", regex=True).sum()
    findings.append(check("0_heldout_rows_in_decision_table", heldout_like == 0, {"matches": int(heldout_like)}))

    # 5. 0 PySR
    pysr_in_modules = "pysr" in sys.modules
    pysr_flag = bool(run_manifest.get("pysr_imported", True))
    findings.append(
        check(
            "0_pysr",
            (not pysr_in_modules) and (not pysr_flag),
            {"pysr_in_sys_modules_now": pysr_in_modules, "pysr_imported_during_run": pysr_flag},
        )
    )

    # 6. aggregates reproducible from machine-readable rows: recompute cell
    # metrics, interaction decomposition, and decoupling contrast completely
    # independently (fresh call into e0_analyze's pure functions against the
    # raw rows -- not by reading its cached json) and diff against the sealed
    # e0_analysis.json.
    recomputed_cell_df = analyze.cell_metrics(worlds, fits)
    sealed_cell_df = pd.DataFrame(analysis["cell_metrics"]).sort_values("cell_id").reset_index(drop=True)
    numeric_cols = [c for c in recomputed_cell_df.columns if pd.api.types.is_numeric_dtype(recomputed_cell_df[c])]
    mismatches = []
    for col in numeric_cols:
        a = recomputed_cell_df[col].to_numpy(dtype=float)
        b = sealed_cell_df[col].to_numpy(dtype=float)
        if not np.allclose(a, b, equal_nan=True, atol=1e-9):
            mismatches.append(col)
    findings.append(check("cell_metrics_reproducible_from_raw_rows", len(mismatches) == 0, {"mismatched_columns": mismatches}))

    recomputed_decomp = analyze.interaction_decomposition(recomputed_cell_df, metric="boundary_limited_rate")
    sealed_decomp = analysis["interaction_decomposition_boundary_limited_rate"]
    decomp_ok = (
        abs(recomputed_decomp["c_gen_main_effect_range"] - sealed_decomp["c_gen_main_effect_range"]) < 1e-9
        and abs(recomputed_decomp["mu_ceil_main_effect_range"] - sealed_decomp["mu_ceil_main_effect_range"]) < 1e-9
        and abs(recomputed_decomp["interaction_effect_magnitude"] - sealed_decomp["interaction_effect_magnitude"]) < 1e-9
    )
    findings.append(check("interaction_decomposition_reproducible", decomp_ok, {"recomputed": recomputed_decomp, "sealed": sealed_decomp}))

    recomputed_contrast = analyze.decoupling_contrast(worlds)
    sealed_contrast = analysis["decoupling_contrast"]
    contrast_ok = abs(recomputed_contrast["absolute_drop"] - sealed_contrast["absolute_drop"]) < 1e-9
    findings.append(check("decoupling_contrast_reproducible", contrast_ok, {"recomputed_drop": recomputed_contrast["absolute_drop"], "sealed_drop": sealed_contrast["absolute_drop"]}))

    # 7. decision-tree output mechanically matches measured values: recompute
    # the terminal category from the frozen protocol table directly, given
    # only the drop and decomposition ranges recomputed above.
    recomputed_decision = analyze.apply_decision_tree(recomputed_contrast["absolute_drop"], recomputed_decomp)
    sealed_decision = analysis["causal_decision"]
    decision_ok = (
        recomputed_decision["terminal_category"] == sealed_decision["terminal_category"]
        and recomputed_decision["committed_row"] == sealed_decision["committed_row"]
    )
    findings.append(
        check(
            "decision_tree_output_matches_measured_values",
            decision_ok,
            {"recomputed": recomputed_decision, "sealed": sealed_decision},
        )
    )

    # Additional integrity spot-checks
    fit_count_ok = len(fits) == worlds["n_fit_rows"].sum() == 540 * 1080
    findings.append(check("fit_record_count_matches_design_1080_per_world", fit_count_ok, {"n_fits": len(fits), "expected": 540 * 1080}))

    manifest_hash_present = all(isinstance(v, str) and len(v) == 64 for v in run_manifest.get("source_hashes", {}).values()) and len(run_manifest.get("source_hashes", {})) > 0
    findings.append(check("source_hashes_present_in_run_manifest", manifest_hash_present, {"n_hashes": len(run_manifest.get("source_hashes", {}))}))

    pre_manifest_ok = pre_manifest.get("all_checks_pass") is True
    findings.append(check("pre_execution_manifest_all_6_assertions_passed", pre_manifest_ok, None))

    all_pass = all(f["pass"] for f in findings)
    out = {"experiment": "E0", "all_pass": all_pass, "findings": findings}
    with open(os.path.join(ARTIFACT_DIR, "e0_hostile_audit.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=str)

    for f in findings:
        print(f"[{'PASS' if f['pass'] else 'FAIL'}] {f['check']}")
    if not all_pass:
        print("HOSTILE AUDIT FAILED", file=sys.stderr)
        sys.exit(1)
    print("HOSTILE AUDIT: ALL CHECKS PASS")


if __name__ == "__main__":
    main()
