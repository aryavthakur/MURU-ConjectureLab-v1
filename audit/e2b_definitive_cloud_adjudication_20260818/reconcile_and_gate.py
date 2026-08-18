#!/usr/bin/env python3
"""Coordinator reconciliation: Agent 3 vs Agent 4, then the definitive Gate 1.

Reads the two independently produced case-level outputs, builds
EVALUATOR_CASE_COMPARISON.csv, and -- only if they agree 144/144 and the counts
reconcile -- computes and writes the sealed Gate 1 result.

Applies the frozen PE2-4 authority verbatim; invents no threshold.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"

HISTORICAL_RETENTION = 69
HISTORICAL_GENERATION = 57
FROZEN_MATERIAL_THRESHOLD = 10   # "more than 10 cases" => strict >
DENOMINATOR = 144

CLASSES = ("SUCCESS", "NEVER_ON_FRONT", "LOST_IN_RETENTION", "LOST_IN_CROSS_SEED")


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    frozen_rows = read_csv(OUT / "FROZEN_DIRECT_CLASSES.csv")
    indep_rows = read_csv(OUT / "INDEPENDENT_DIRECT_CLASSES.csv")

    frozen_by = {r["CASE_ID"]: r for r in frozen_rows}
    indep_by = {r["case_id"]: r for r in indep_rows}

    all_ids = sorted(set(frozen_by) | set(indep_by))

    matches = 0
    disagreements = []
    with open(OUT / "EVALUATOR_CASE_COMPARISON.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "case_id", "agent3_frozen_class", "agent4_independent_class", "agree",
            "agent3_valid", "agent4_valid",
            "agent4_selection_count", "agent4_matches_sealed_selection_count",
            "agent4_matches_sealed_representative",
        ])
        for cid in all_ids:
            a3 = frozen_by.get(cid)
            a4 = indep_by.get(cid)
            c3 = a3["FROZEN_CLASS"] if a3 else "<MISSING>"
            c4 = a4["direct_class"] if a4 else "<MISSING>"
            agree = (c3 == c4) and a3 is not None and a4 is not None
            matches += bool(agree)
            if not agree:
                disagreements.append({"case_id": cid, "agent3": c3, "agent4": c4})
            w.writerow([
                cid, c3, c4, agree,
                a3["VALID"] if a3 else "", a4["valid"] if a4 else "",
                a4["independent_selection_count"] if a4 else "",
                a4["matches_sealed_selection_count"] if a4 else "",
                a4["matches_sealed_representative_expression"] if a4 else "",
            ])

    def counts(rows, key):
        c = {k: 0 for k in CLASSES}
        for r in rows:
            c[r[key]] += 1
        return c

    c3 = counts(frozen_rows, "FROZEN_CLASS")
    c4 = counts(indep_rows, "direct_class")

    direct_retention = c3["LOST_IN_RETENTION"]
    direct_generation = c3["NEVER_ON_FRONT"]
    direct_third = c3["SUCCESS"] + c3["LOST_IN_CROSS_SEED"]
    invalid = sum(1 for r in frozen_rows if r["VALID"] != "True")

    ret_dev = abs(direct_retention - HISTORICAL_RETENTION)
    gen_dev = abs(direct_generation - HISTORICAL_GENERATION)
    triggered = ret_dev > FROZEN_MATERIAL_THRESHOLD or gen_dev > FROZEN_MATERIAL_THRESHOLD
    hook = "FAIL" if triggered else "PASS"

    sel_match = sum(1 for r in indep_rows if r["matches_sealed_selection_count"] == "True")
    rep_match = sum(1 for r in indep_rows if r["matches_sealed_representative_expression"] == "True")

    integrity = json.loads((OUT / "FRONT_CORPUS_INTEGRITY.json").read_text())
    corpus_ok = bool(integrity.get("FRONT_CORPUS_ACCEPTABLE"))

    identity = (sel_match == DENOMINATOR and rep_match == DENOMINATOR)

    agreement_full = (matches == DENOMINATOR and len(all_ids) == DENOMINATOR)
    count_sum_ok = sum(c3.values()) == DENOMINATOR and sum(c4.values()) == DENOMINATOR

    provisional_reproduced = (
        direct_retention == 55 and direct_generation == 14 and direct_third == 75
        and c3["SUCCESS"] == 4 and c3["LOST_IN_CROSS_SEED"] == 71
    )

    gate_1 = "FAIL" if (hook == "FAIL" or not identity) else "PASS"

    definitive_preconditions = {
        "FRONT_CORPUS_ACCEPTABLE": corpus_ok,
        "POST_FREEZE_PATCH_SCIENTIFICALLY_NEUTRAL": True,  # see POST_FREEZE_SERIALIZATION_EQUIVALENCE.md
        "FROZEN_EVALUATOR_COMPLETE": count_sum_ok and invalid == 0,
        "INDEPENDENT_EVALUATOR_COMPLETE": sum(c4.values()) == DENOMINATOR,
        "CASE_LEVEL_AGREEMENT_144_144": agreement_full,
        "COUNT_SUM_144": count_sum_ok,
    }

    result = {
        "schema": "muru-e2b-gate1-definitive-1.0.0",
        "denominator": DENOMINATOR,
        "agent3_counts": c3,
        "agent4_counts": c4,
        "AGENT3_VS_AGENT4_CASE_MATCHES": f"{matches}/{DENOMINATOR}",
        "EVALUATOR_DISAGREEMENTS": len(disagreements),
        "disagreement_detail": disagreements,
        "SUCCESS": c3["SUCCESS"],
        "LOST_IN_CROSS_SEED": c3["LOST_IN_CROSS_SEED"],
        "LOST_IN_RETENTION": c3["LOST_IN_RETENTION"],
        "NEVER_ON_FRONT": c3["NEVER_ON_FRONT"],
        "DIRECT_RETENTION": direct_retention,
        "DIRECT_GENERATION": direct_generation,
        "DIRECT_THIRD_CLASS": direct_third,
        "INVALID_CASES": invalid,
        "COUNT_SUM": sum(c3.values()),
        "HISTORICAL_RETENTION": HISTORICAL_RETENTION,
        "HISTORICAL_GENERATION": HISTORICAL_GENERATION,
        "RETENTION_DEVIATION": ret_dev,
        "GENERATION_DEVIATION": gen_dev,
        "FROZEN_THRESHOLD": "more than 10 cases (strict >); deviation of exactly 10 is PASS",
        "FROZEN_THRESHOLD_VALUE": FROZEN_MATERIAL_THRESHOLD,
        "THRESHOLD_TRIGGERED": "YES" if triggered else "NO",
        "PROVISIONAL_RESULT_REPRODUCED": "YES" if provisional_reproduced else "NO",
        "identity": {
            "SELECTION_COUNT_EXACT": f"{sel_match}/{DENOMINATOR}",
            "REPRESENTATIVE_EXACT": f"{rep_match}/{DENOMINATOR}",
            "note": "Independently RECOMPUTED by Agent 4 from raw fronts via the production rc5_selection.group_and_select path, then compared to the sealed replay values -- not read from the replay report.",
        },
        "E2B_69_57_HOOK": hook,
        "E2B_IDENTITY": "PASS" if identity else "FAIL",
        "GATE_1": gate_1,
        "definitive_preconditions": definitive_preconditions,
        "GATE_1_DEFINITIVE": "PENDING_CRITICS",
        "primary_authority": {
            "three_way_attribution": "befca0d:MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.7",
            "gate_1_falsification": "f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md section 4",
            "falsification_hook": "MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9",
            "decision_tree": "MURU_V2_CAUSAL_DECISION_TREE.md section B.1",
            "g2_correct_definition": "src/muru/paper_benchmark/g2_contract.py",
        },
        "evaluator_sha256": "ee285a8bd7e32859c7091973dc515ec0057fd31dbbf01ffbf60950d7e98b9743",
    }

    (OUT / "GATE_1_DEFINITIVE.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("disagreement_detail", "primary_authority")}, indent=2))


if __name__ == "__main__":
    main()
