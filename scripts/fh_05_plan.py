"""FRESH HOLDOUT — Phase B: predeclare the plan BEFORE any search runs."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import fh_lib as fh  # noqa: E402


def main() -> int:
    freeze = json.loads((ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json").read_text())
    specs = fh.all_worlds()
    by_block: dict[str, int] = {}
    by_cat: dict[str, int] = {}
    for s in specs:
        by_block[s.block] = by_block.get(s.block, 0) + 1
        by_cat[fh.category(s.block)] = by_cat.get(fh.category(s.block), 0) + 1

    plan = {
        "plan_version": fh.FH_PLAN_VERSION,
        "phase": "B_PREDECLARED_PLAN",
        "declared_before": "any fresh-holdout world data or search output exists",
        "frozen_architecture_identity": freeze["frozen_architecture"],
        "deployment_gate": freeze["deployment_gate"],
        "method_freeze_sha256": hashlib.sha256(
            (ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json").read_bytes()).hexdigest(),
        "sample_composition": {
            "n_worlds": len(specs),
            "by_category": by_cat,
            "by_block": by_block,
            "positive_detail": {
                "G1A": {"low": 2, "moderate": 2, "adverse": 2},
                "G1B": dict(fh.G1B_REPLICATES),
                "G1C": {"moderate": fh.N_G1C},
            },
            "null_detail": {"NCAL_per_construction": fh.N_NCAL_PER_CONSTRUCTION,
                            "NCAL_constructions": list(fh.NULL_CONSTRUCTIONS),
                            "G4": fh.N_G4, "G4M": fh.N_G4M},
            "refusal_detail": {"G2": fh.N_G2, "G3": fh.N_G3, "G5": fh.N_G5,
                               "GC_cutoffs_da": list(fh.GC_CUTOFFS),
                               "GC_per_cutoff": fh.N_GC_PER_CUTOFF,
                               "GRT": fh.N_GRT},
        },
        "generation_namespace": {
            "world_id_prefix": "FH|",
            "replicate_base": fh.FH_REP_BASE,
            "generator": "muru.objval.generators2 (ov-gen-1.0.0), UNCHANGED",
            "truth": "muru.objval.truth2, UNCHANGED",
            "note": ("Fresh generator seeds arise because world_seed2 hashes "
                     "the replicate index; the FH replicate namespace has never "
                     "been used."),
        },
        "search_seed_policy": {
            "derivation": ("FH_SEED_BASE + (sha256(world_id)[:4] mod "
                           "FH_SEED_SPREAD) * 100 + k, k = 0..5"),
            "base": fh.FH_SEED_BASE, "spread": fh.FH_SEED_SPREAD,
            "n_seeds_per_world": fh.N_SEEDS,
            "band_min": fh.FH_SEED_BASE,
            "band_theoretical_max": fh.FH_SEED_BASE
            + (fh.FH_SEED_SPREAD - 1) * 100 + fh.N_SEEDS - 1,
            "ov_band_theoretical_max": fh.OV_SEED_THEORETICAL_MAX,
            "p3_band_theoretical_max": fh.P3_SEED_THEORETICAL_MAX,
            "int32_max": fh.INT32_MAX,
        },
        "searches_per_world": fh.N_SEEDS,
        "total_planned_searches": len(specs) * fh.N_SEEDS,
        "search_configuration": "frozen PYSR_CONFIG, unmodified",
        "primary_metrics": [
            "positive support recovery — ungated",
            "positive support recovery — end-to-end after report gate",
            "positive family recovery — ungated",
            "positive family recovery — end-to-end",
            "G1A family recovery", "G1B family recovery", "G1C family recovery",
            "null false-positive rate", "sensitivity", "specificity",
            "balanced accuracy", "positive-vs-null ROC AUC",
            "computational failure rate",
        ],
        "secondary_metrics": [
            "G1B low / moderate / adverse family recovery",
            "exact / form recovery", "refusal-challenge behaviour",
            "representative validation R2 distributions",
            "positive vs null R2 distributions", "recovered equations",
            "failure taxonomy",
        ],
        "success_rubric": {
            "STRONG_GENERALIZATION_EVIDENCE": {
                "support_end_to_end_ge": 0.90, "family_recovery_ge": 0.70,
                "G1B_family_ge": 0.75, "null_fpr_le": 0.05, "roc_auc_ge": 0.95,
                "computational_failure_rate_le": 0.02,
                "and": ("no major unexplained catastrophic collapse in a "
                        "scientifically important stratum"),
            },
            "MODERATE_GENERALIZATION_EVIDENCE": (
                "broad signal and general discrimination clearly remain but at "
                "least one strong criterion fails"),
            "WEAK_UNSTABLE_GENERALIZATION_EVIDENCE": (
                "performance becomes strongly regime-dependent or deteriorates "
                "substantially relative to development"),
            "NO_EVIDENCE_OF_GENERALIZATION": (
                "both symbolic recovery and null discrimination materially "
                "collapse"),
            "status": "descriptive exploratory labels, not confirmatory criteria",
        },
        "no_post_holdout_tuning_rule": (
            "Once any holdout scientific outcome is visible: no model, selector, "
            "gate, threshold, tolerance, grammar, operator or search-budget "
            "change; no special handling of failed worlds; no second holdout; no "
            "rerun of poor-looking worlds. The only permissible rerun is a same "
            "world/seed identity that failed for an objective computational "
            "reason."),
        "time_budget_fallback": (
            "If, BEFORE any scoring, 96x6 cannot finish inside the 120-minute "
            "ceiling, reduce the WORLD population to 84 then 72 using "
            "fh_lib.reduction_rank (sha256 of the frozen world id) within each "
            "block, preserving all 6 seeds per retained world and the block "
            "proportions. Never driven by any scientific output."),
        "truth_quarantine": (
            "fresh_holdout_truth_manifest.json is written at generation time and "
            "is not opened by any discovery, selection, gating or prediction "
            "code. It is opened once, after "
            "fresh_holdout_predictions_frozen.json is written and hashed."),
    }
    text = json.dumps(plan, indent=1, sort_keys=True)
    (ROOT / "FRESH_HOLDOUT_PLAN.json").write_text(text)
    print(json.dumps({"n_worlds": len(specs), "by_category": by_cat,
                      "by_block": by_block,
                      "total_searches": len(specs) * fh.N_SEEDS,
                      "plan_sha256": hashlib.sha256(text.encode()).hexdigest()},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
