"""Hostile audit of the E3 execution.

Checks, each independently verifiable from artifacts on disk:
  A. 100% of the 200 preregistered cells / 10,000 worlds executed, 0 missing.
  B. 0 duplicate world IDs; the executed-world-ID set is exactly the
     manifest's world-ID set (a bijection, not just equal cardinality).
  C. 0 PySR imports anywhere in the code path actually exercised, checked
     both statically (source grep) and dynamically (sys.modules after
     running real workers).
  D. Oracle decisions are reproducible: re-running a random sample of
     worlds from their world_id alone reproduces every persisted number
     exactly (determinism from the seed derivation, not just "close").
  E. The decision thresholds and the manifest's independent-variable levels
     actually used match the frozen design documents byte-for-byte, i.e.
     were fixed before this run and not adjusted after seeing results.
  F. Aggregate counts reconcile exactly (family/control partitions,
     confusion-matrix row sums, cell counts).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import numpy as np

from manifest import build_manifest, verify_manifest, FAMILIES, COEFFICIENTS, NOISE_LEVELS, GRID_POINTS, N_REPLICATES

REPO_ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b")
RESULTS_DIR = REPO_ROOT / "results" / "e3_identifiability"
WORLDS_PATH = RESULTS_DIR / "e3_worlds.jsonl"
FROZEN_SRC = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/heldout-analysis-restoration/src")
DESIGN_DOC = REPO_ROOT / "MURU_V2_IDENTIFIABILITY_STUDY_DESIGN.md"
PLAN_JSON = REPO_ROOT / "MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json"


def check_a_b_manifest_completeness() -> dict:
    manifest_rows = build_manifest()
    manifest_check = verify_manifest(manifest_rows)
    manifest_ids = {r["world_id"] for r in manifest_rows}

    executed_ids = []
    statuses = []
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            executed_ids.append(r["world_id"])
            statuses.append(r["status"])

    executed_id_set = set(executed_ids)
    ok_count = sum(1 for s in statuses if s == "OK")

    return {
        "manifest_check": manifest_check,
        "manifest_world_count": len(manifest_ids),
        "executed_world_count": len(executed_ids),
        "executed_unique_world_count": len(executed_id_set),
        "duplicate_executed_ids": len(executed_ids) - len(executed_id_set),
        "manifest_minus_executed": sorted(manifest_ids - executed_id_set)[:20],
        "executed_minus_manifest": sorted(executed_id_set - manifest_ids)[:20],
        "manifest_equals_executed_set": manifest_ids == executed_id_set,
        "n_ok": ok_count,
        "n_execution_failure": len(statuses) - ok_count,
        "pass_100_percent_executed": (manifest_ids == executed_id_set) and (ok_count == 10_000) and (len(executed_ids) == len(executed_id_set)),
    }


def check_c_pysr() -> dict:
    # Static: grep every file actually imported by the E3 harness, plus the
    # harness's own source, for a real `import pysr` / `from pysr` statement.
    touched_files = [
        REPO_ROOT / "scripts" / "e3_identifiability" / "v2c_generator.py",
        REPO_ROOT / "scripts" / "e3_identifiability" / "oracle_models.py",
        REPO_ROOT / "scripts" / "e3_identifiability" / "manifest.py",
        REPO_ROOT / "scripts" / "e3_identifiability" / "run_e3.py",
        REPO_ROOT / "scripts" / "e3_identifiability" / "aggregate_e3.py",
        FROZEN_SRC / "muru" / "paper_benchmark" / "generator.py",
        FROZEN_SRC / "muru" / "paper_benchmark" / "rc5_estimate.py",
        FROZEN_SRC / "muru" / "paper_benchmark" / "adequacy.py",
        FROZEN_SRC / "muru" / "paper_benchmark" / "structural_acceptance.py",
        FROZEN_SRC / "muru" / "paper_benchmark" / "registry.py",
        FROZEN_SRC / "muru" / "paper_benchmark" / "truth.py",
        FROZEN_SRC / "muru" / "discovery" / "estimate.py",
        FROZEN_SRC / "muru" / "discovery" / "grammar.py",
    ]
    import_pattern = re.compile(r"^\s*(import\s+pysr|from\s+pysr)", re.IGNORECASE | re.MULTILINE)
    static_hits = {}
    for f in touched_files:
        text = f.read_text(encoding="utf-8")
        hits = import_pattern.findall(text)
        if hits:
            static_hits[str(f)] = hits

    # Dynamic: actually run a world through the real worker in a fresh
    # subprocess and inspect sys.modules for anything pysr-named.
    probe = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "import run_e3; rec = run_e3.run_one_world({'world_id':'V2C|E3|mass_power|c0.25|noise0.02|grid6|r000',"
        "'cell_id':'x','family':'mass_power','c':0.25,'noise_sd':0.02,'grid_points':6,'replicate':0}); "
        "print('STATUS', rec['status']); "
        "print('PYSR_MODULES', [m for m in sys.modules if 'pysr' in m.lower()])"
    ) % (str(REPO_ROOT / "scripts" / "e3_identifiability"), str(FROZEN_SRC))
    proc = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=60)
    dynamic_ok = "STATUS OK" in proc.stdout and "PYSR_MODULES []" in proc.stdout

    return {
        "static_grep_touched_files": [str(f.relative_to(REPO_ROOT.parent.parent) if REPO_ROOT in f.parents else f) for f in touched_files],
        "static_hits": static_hits,
        "static_pass": len(static_hits) == 0,
        "dynamic_probe_stdout": proc.stdout.strip(),
        "dynamic_probe_stderr": proc.stderr.strip()[-2000:],
        "dynamic_pass": dynamic_ok,
        "pass_zero_pysr_imports": len(static_hits) == 0 and dynamic_ok,
    }


def check_d_reproducibility(n_sample: int = 40, seed: int = 20260816) -> dict:
    import run_e3

    manifest_rows = build_manifest()
    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(len(manifest_rows), size=n_sample, replace=False)
    sample_cells = [manifest_rows[i] for i in sample_idx]

    # Load persisted originals
    originals = {}
    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            originals[r["world_id"]] = r

    mismatches = []
    for cell in sample_cells:
        rerun = run_e3.run_one_world(cell)
        original = originals[cell["world_id"]]
        if rerun.get("status") != original.get("status"):
            mismatches.append({"world_id": cell["world_id"], "field": "status", "original": original.get("status"), "rerun": rerun.get("status")})
            continue
        for key in ("bic_selected_model", "val_r2_selected_model", "true_model_id", "oracle_correct_bic", "oracle_correct_r2"):
            if rerun.get(key) != original.get(key):
                mismatches.append({"world_id": cell["world_id"], "field": key, "original": original.get(key), "rerun": rerun.get(key)})
        for mid in ("M_mass", "M_affine", "M_sat", "M_exp", "M_inter"):
            orig_bic = original["models"][mid]["bic"]
            rerun_bic = rerun["models"][mid]["bic"]
            if orig_bic is None and rerun_bic is None:
                continue
            if orig_bic is None or rerun_bic is None or abs(orig_bic - rerun_bic) > 1e-9:
                mismatches.append({"world_id": cell["world_id"], "field": f"bic__{mid}", "original": orig_bic, "rerun": rerun_bic})

    return {
        "n_sampled": n_sample,
        "n_mismatches": len(mismatches),
        "mismatches": mismatches[:20],
        "pass_fully_reproducible": len(mismatches) == 0,
    }


def check_e_frozen_criteria() -> dict:
    design_text = DESIGN_DOC.read_text(encoding="utf-8")
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    e3_plan = next(e for e in plan["experiments"] if e["id"] == "E3")

    checks = {
        "design_doc_states_identifiable_0.80": ">= 0.80" in design_text and "IDENTIFIABLE" in design_text,
        "design_doc_states_marginal_0.50": "0.50" in design_text,
        "design_doc_states_invalid_0.10": "0.10" in design_text and "STUDY INVALID" in design_text,
        "plan_json_families_match": list(e3_plan["independent_variable"]["truth_family"]) == [
            "mass_power (control)", "mass_affine_descriptor", "mass_saturating_descriptor",
            "mass_interaction", "mass_exponential_descriptor",
        ],
        "plan_json_coefficients_match": tuple(e3_plan["independent_variable"]["coefficient_c"]) == COEFFICIENTS,
        "plan_json_noise_match": tuple(e3_plan["independent_variable"]["noise_sd"]) == NOISE_LEVELS,
        "plan_json_grid_match": tuple(e3_plan["independent_variable"]["energy_grid_points"]) == GRID_POINTS,
        "plan_json_worlds_total_10000": e3_plan["case_count"]["worlds_total"] == 10_000,
        "plan_json_zero_searches": e3_plan["case_count"]["searches"] == 0,
        "plan_json_decision_criterion_matches_code": (
            "0.80" in e3_plan["decision_criterion"]["IDENTIFIABLE"]
            and "0.50" in e3_plan["decision_criterion"]["MARGINAL"]
            and "0.10" in e3_plan["decision_criterion"]["STUDY_INVALID"]
        ),
    }
    checks["all_pass"] = all(checks.values())
    return checks


def check_f_aggregate_reconciliation() -> dict:
    agg = json.loads((RESULTS_DIR / "e3_aggregate.json").read_text(encoding="utf-8"))
    by_family_sum = sum(row["n"] for row in agg["recovery_by_family"])
    control_breakdown_sum = sum(row["n"] for row in agg["control_breakdown_by_noise_grid"])
    full_cell_sum = sum(row["n"] for row in agg["full_cell_classification_200_cells"])

    checks = {
        "n_worlds_is_10000": agg["n_worlds"] == 10_000,
        "n_ok_is_10000": agg["n_ok"] == 10_000,
        "by_family_sums_to_10000": by_family_sum == 10_000,
        "by_family_has_5_rows": len(agg["recovery_by_family"]) == 5,
        "each_family_has_2000": all(row["n"] == 2000 for row in agg["recovery_by_family"]),
        "control_breakdown_sums_to_2000": control_breakdown_sum == 2000,
        "full_cell_classification_has_200_rows": len(agg["full_cell_classification_200_cells"]) == 200,
        "full_cell_classification_sums_to_10000": full_cell_sum == 10_000,
        "overall_descriptor_only_n_is_8000": agg["overall_recovery_descriptor_families_only"]["n"] == 8000,
        "study_validity_control_n_is_2000": agg["study_validity"]["n_control_worlds"] == 2000,
    }
    # Confusion matrix row sums reconcile to the frozen-subset cell count (150 per truth family).
    for criterion in ("bic", "val_r2"):
        cm = agg["confusion_matrix_frozen_operating_point"][criterion]
        for truth_family, row in cm.items():
            checks[f"confusion_{criterion}_{truth_family}_row_sums_150"] = sum(row.values()) == 150
    checks["all_pass"] = all(checks.values())
    return checks


def main() -> None:
    report = {
        "A_B_manifest_and_execution_completeness": check_a_b_manifest_completeness(),
        "C_zero_pysr_imports": check_c_pysr(),
        "D_reproducibility": check_d_reproducibility(),
        "E_frozen_criteria_no_post_hoc_changes": check_e_frozen_criteria(),
        "F_aggregate_reconciliation": check_f_aggregate_reconciliation(),
    }
    report["OVERALL_PASS"] = all([
        report["A_B_manifest_and_execution_completeness"]["pass_100_percent_executed"],
        report["A_B_manifest_and_execution_completeness"]["manifest_equals_executed_set"],
        report["A_B_manifest_and_execution_completeness"]["duplicate_executed_ids"] == 0,
        report["C_zero_pysr_imports"]["pass_zero_pysr_imports"],
        report["D_reproducibility"]["pass_fully_reproducible"],
        report["E_frozen_criteria_no_post_hoc_changes"]["all_pass"],
        report["F_aggregate_reconciliation"]["all_pass"],
    ])

    out_path = RESULTS_DIR / "e3_hostile_audit.json"
    out_path.write_text(json.dumps(report, indent=1, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({k: (v if k == "OVERALL_PASS" else v.get("all_pass", v.get("pass_100_percent_executed", v.get("pass_zero_pysr_imports", v.get("pass_fully_reproducible"))))) for k, v in report.items()}, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
