"""FRESH HOLDOUT — assemble MURU_FRESH_HOLDOUT_RESULT.{json,md}."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "fresh_holdout"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    sc = json.loads((OUT / "fresh_holdout_scored.json").read_text())
    fz = json.loads((ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json").read_text())
    pl = json.loads((ROOT / "FRESH_HOLDOUT_PLAN.json").read_text())
    dj = json.loads((ROOT / "fresh_holdout_disjointness.json").read_text())
    cp = json.loads((OUT / "search_completeness.json").read_text())
    fd = json.loads((OUT / "failure_decomposition.json").read_text())
    ex = json.loads((OUT / "equation_examples.json").read_text())
    ph = json.loads((OUT / "predictions_frozen_hash.json").read_text())

    P, S, C = sc["primary_metrics"], sc["strata"], sc["development_vs_holdout"]
    rub = sc["strong_rubric"]

    payload = {
        "experiment": "MURU_FRESH_HOLDOUT",
        "verdict": "STRONG_GENERALIZATION_EVIDENCE" if rub["all_numeric_criteria_met"]
                   else "SEE_RUBRIC",
        "revealed_at_utc": sc["revealed_at_utc"],
        "method_freeze": {
            "git_head": fz["git"]["head"], "git_branch": fz["git"]["branch"],
            "architecture": fz["frozen_architecture"],
            "deployment_gate": fz["deployment_gate"],
            "versions": fz["versions"],
            "file_sha256": fz["file_sha256"],
            "method_freeze_sha256": sha(ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json"),
            "plan_sha256": sha(ROOT / "FRESH_HOLDOUT_PLAN.json"),
        },
        "freshness": {
            "verdict": dj["VERDICT"],
            "checks": {k: v for k, v in dj["checks"].items()
                       if not isinstance(v, list)},
            "n_historical_world_ids_compared": dj["n_historical_world_ids_compared"],
            "n_historical_symbolic_seeds_compared":
                dj["n_historical_symbolic_seeds_compared"],
            "world_manifest_sha256": dj["world_manifest_sha256"],
            "truth_manifest_sha256": dj["truth_manifest_sha256"],
        },
        "population": pl["sample_composition"],
        "search_completeness": {k: v for k, v in cp.items()
                                if k not in ("per_world", "missing_units",
                                             "torn_or_corrupt_units")},
        "prediction_freeze": ph,
        "primary_metrics": P,
        "development_vs_holdout": C,
        "strata": S,
        "nulls": sc["nulls"],
        "refusal": sc["refusal"],
        "failure_decomposition": fd["counts"],
        "failure_rows": fd["rows"],
        "equation_examples": ex["rows"],
        "r2_summary": {
            k: {"n": len(v), "min": min(v), "median": float(np.median(v)),
                "max": max(v)}
            for k, v in sc["r2_distributions"].items()},
        "strong_rubric": rub,
    }
    (ROOT / "MURU_FRESH_HOLDOUT_RESULT.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str))
    print("wrote MURU_FRESH_HOLDOUT_RESULT.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
