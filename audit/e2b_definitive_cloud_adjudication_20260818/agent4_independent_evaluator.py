#!/usr/bin/env python3
"""AGENT_4: INDEPENDENT_ATTRIBUTION_REPLICATION.

A SEPARATE implementation of the E2b three-way attribution. It deliberately
does NOT import, read, or reuse scripts/e2b_direct_evaluator.py. It re-derives
every step from primary frozen authority, through a DIFFERENT code path:

  frozen evaluator (Agent 3)          this module (Agent 4)
  --------------------------------    -----------------------------------------
  hand-rolled argmax over row.score    rc5_selection.select_row_label -- the
                                       PRODUCTION retention rule, including its
                                       section 7.6 guards (missing score column,
                                       missing loss column, non-finite loss)
  representative READ from the         representative RECOMPUTED from scratch by
  replay report's                      rc5_selection.group_and_select over the
  representative_replayed field        30 retained candidates (production
                                       identity-contract grouping + voting)
  case list from evaluator's own       case list re-enumerated independently
  get_g2_case_ids()                    from registry.CASE_FAMILIES

Shared, and deliberately so: src/muru/paper_benchmark/g2_contract.py. That
module IS the frozen definition of G2-correctness (primary authority item 3);
re-implementing it would be inventing a second, unauthorised classifier rather
than replicating the frozen one. Only the ORCHESTRATION is independent.

Authority actually read to write this file:
  * v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.7
    (the four-way partition)
  * git show f4c1105:v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md
    sections 2 (A-E first-loss taxonomy) and 4 (Gate 1 trigger)
  * src/muru/paper_benchmark/g2_contract.py (G2 correctness contract)
  * src/muru/paper_benchmark/rc5_selection.py (retention + cross-seed voting)
  * src/muru/paper_benchmark/registry.py (case enumeration)

No timeout is applied anywhere: the frozen classification semantics contain no
authoritative timeout, so a performance timeout must never stand in for a class.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.g2_contract import (
    TRUTH_FAMILIES,
    G2Event,
    classify_discovered_family,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
    extract_effective_support,
    truth_support_for_case,
)
from muru.paper_benchmark.generator import generate_case
from muru.paper_benchmark.registry import CASE_FAMILIES, endpoint_applies_to_variant
from muru.paper_benchmark.rc5_selection import (
    RetainedCandidate,
    SeedSelection,
    SeedExecutionFailure,
    SeedNoCandidate,
    group_and_select,
    select_row_label,
)

REPLAY = ROOT / "results" / "e2b_macos_fullfront_replay_20260818"
FRONTS = REPLAY / "fronts"
OUTDIR = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
CKPT = OUTDIR / "_ckpt_independent"

SEEDS_PER_CASE = 30

# per-process memo of G2 correctness; pure function of its whole key
_G2_MEMO: dict = {}


def g2_correct(expr: str, truth_support: frozenset, truth_family: str) -> bool:
    """G2-correct iff the frozen contract's own event evaluation says SUCCESS.

    Composed here directly from g2_contract's five primitives, in the order the
    contract itself documents, rather than through any other module's helper.
    """
    key = (expr, truth_support, truth_family)
    hit = _G2_MEMO.get(key)
    if hit is not None:
        return hit
    support = extract_effective_support(expr)
    family = classify_discovered_family(expr)
    event = evaluate_g2_event(
        classify_support(support, truth_support),
        classify_family_match(family, truth_family),
    )
    result = event == G2Event.SUCCESS
    _G2_MEMO[key] = result
    return result


def enumerate_g2_cases() -> list[str]:
    """Re-derive the 144 held-out G2 case IDs straight from the registry."""
    out: list[str] = []
    for fam in CASE_FAMILIES:
        for r in range(fam.partition_counts.get("held_out", 0)):
            variant = fam.variant_for_replicate(r)
            if endpoint_applies_to_variant("family_recovery", variant):
                out.append(f"PB|held_out|{fam.code}|r{r:03d}")
    return out


def load_seed_fronts(case_id: str) -> dict[int, list[dict]]:
    """{seed_ordinal: [row, ...]} for one case, straight off disk."""
    case_dir = FRONTS / case_id.replace("|", "_")
    fronts: dict[int, list[dict]] = {}
    for path in sorted(case_dir.glob("*.jsonl")):
        rows = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
        if not rows:
            continue
        fronts[int(rows[0]["_seed_ordinal"])] = rows
    return fronts


def retained_row(rows: list[dict]) -> tuple[dict | None, str | None]:
    """The seed's single retained candidate, via the PRODUCTION rule.

    Builds the emitted frame back into a DataFrame and defers entirely to
    rc5_selection.select_row_label -- so this path inherits the frozen
    section 7.6 guards (absent score column, absent loss column, non-finite
    loss are EXECUTION_FAILURE, never a silent change of selection rule).
    """
    frame = pd.DataFrame(
        {
            "complexity": [r.get("complexity") for r in rows],
            "equation": [r.get("equation") for r in rows],
            "loss": [r.get("loss") for r in rows],
            "score": [r.get("score") for r in rows],
        }
    )
    try:
        label = select_row_label(frame)
    except (SeedExecutionFailure, SeedNoCandidate) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return rows[int(label)], None


def process_case(case_id: str) -> dict:
    ck = CKPT / (case_id.replace("|", "_") + ".json")
    if ck.exists():
        try:
            return json.loads(ck.read_text())
        except json.JSONDecodeError:
            ck.unlink()

    t0 = time.time()
    truth = generate_case(case_id).truth
    rec: dict = {"case_id": case_id}

    if truth.mathematical_family not in TRUTH_FAMILIES:
        rec.update(
            direct_class="NEVER_ON_FRONT", valid=False,
            invalid_reason=f"truth family {truth.mathematical_family!r} not in TRUTH_FAMILIES",
            seeds_with_correct_on_front=0, seeds_with_retained_correct=0,
            independent_selection_count=0, independent_representative_expression="",
            representative_correct=False, wall_seconds=time.time() - t0,
        )
        ck.write_text(json.dumps(rec))
        return rec

    truth_support = truth_support_for_case(truth)
    truth_family = truth.mathematical_family

    fronts = load_seed_fronts(case_id)
    if len(fronts) != SEEDS_PER_CASE:
        rec.update(
            direct_class="NEVER_ON_FRONT", valid=False,
            invalid_reason=f"expected {SEEDS_PER_CASE} seed fronts, found {len(fronts)}",
            seeds_with_correct_on_front=0, seeds_with_retained_correct=0,
            independent_selection_count=0, independent_representative_expression="",
            representative_correct=False, wall_seconds=time.time() - t0,
        )
        ck.write_text(json.dumps(rec))
        return rec

    seeds_correct_on_front = 0
    seeds_retained_correct = 0
    selections: list[SeedSelection] = []
    seed_errors: list[str] = []

    for k in range(SEEDS_PER_CASE):
        rows = fronts[k]
        seed_val = int(rows[0]["_seed"])

        # (1) stage-A/B evidence: does ANY row on this seed's front recover truth?
        if any(g2_correct(r.get("equation", ""), truth_support, truth_family)
               for r in rows if r.get("equation")):
            seeds_correct_on_front += 1

        # (2) the seed's retained candidate, by the production retention rule
        row, err = retained_row(rows)
        if row is None:
            seed_errors.append(f"seed_ordinal={k}: {err}")
            selections.append(SeedSelection(k=k, seed=seed_val,
                                            status=SeedStatus.COMPLETED_NO_CANDIDATE,
                                            error_message=err or ""))
            continue

        if g2_correct(row.get("equation", ""), truth_support, truth_family):
            seeds_retained_correct += 1

        selections.append(SeedSelection(
            k=k, seed=seed_val, status=SeedStatus.COMPLETED_WITH_CANDIDATES,
            candidate=RetainedCandidate(
                k=k, seed=seed_val,
                expression_string=str(row.get("equation", "")),
                complexity=int(row.get("complexity", 0)),
                # not used by group_and_select's bucketing / winner rule, which
                # keys only on parsed-expression template_key and seed ordinal
                valid_r2=float("nan"), invalid_fraction=float("nan"),
                candidate_test_r2=float("nan"),
            ),
        ))

    # (3) cross-seed voting, recomputed from scratch by the production selector
    cross = group_and_select(selections, selection_denominator=SEEDS_PER_CASE)
    rep_expr = cross.representative.expression_string if cross.representative else ""
    rep_correct = bool(rep_expr) and g2_correct(rep_expr, truth_support, truth_family)

    # (4) the four-way partition, section 2.7, in strict priority order
    if rep_correct:
        direct_class = "SUCCESS"
    elif seeds_correct_on_front == 0:
        direct_class = "NEVER_ON_FRONT"
    elif seeds_retained_correct >= 1:
        direct_class = "LOST_IN_CROSS_SEED"
    else:
        direct_class = "LOST_IN_RETENTION"

    rec.update(
        direct_class=direct_class,
        seeds_with_correct_on_front=seeds_correct_on_front,
        seeds_with_retained_correct=seeds_retained_correct,
        independent_selection_count=cross.selection_count,
        independent_representative_expression=rep_expr,
        representative_correct=rep_correct,
        voting_seeds=cross.voting_seeds,
        valid=True,
        invalid_reason="",
        seed_errors=seed_errors,
        wall_seconds=time.time() - t0,
    )
    ck.write_text(json.dumps(rec))
    print(f"[a4] {case_id} -> {direct_class} ({rec['wall_seconds']:.1f}s)", flush=True)
    return rec


def main() -> None:
    CKPT.mkdir(parents=True, exist_ok=True)
    case_ids = enumerate_g2_cases()
    assert len(case_ids) == 144, f"expected 144 G2 cases from registry, got {len(case_ids)}"

    t0 = time.time()
    with Pool(processes=12) as pool:
        results = pool.map(process_case, case_ids, chunksize=1)
    wall = time.time() - t0

    order = {c: i for i, c in enumerate(case_ids)}
    results.sort(key=lambda d: order[d["case_id"]])

    # cross-reference ONLY (never an input to classification above)
    report = json.loads((REPLAY / "E2B_FULLFRONT_REPLAY_REPORT.json").read_text())
    sealed = {
        d["case_id"]: (d["selection_count_replayed"], d["representative_replayed"])
        for d in report.get("comparison_details", [])
    }

    counts = {k: 0 for k in ("SUCCESS", "NEVER_ON_FRONT", "LOST_IN_RETENTION", "LOST_IN_CROSS_SEED")}
    sel_match = rep_match = 0
    for d in results:
        counts[d["direct_class"]] += 1
        s_count, s_rep = sealed.get(d["case_id"], (None, None))
        d["matches_sealed_selection_count"] = (d["independent_selection_count"] == s_count)
        d["matches_sealed_representative_expression"] = (
            d["independent_representative_expression"] == s_rep
        )
        sel_match += bool(d["matches_sealed_selection_count"])
        rep_match += bool(d["matches_sealed_representative_expression"])

    with open(OUTDIR / "INDEPENDENT_DIRECT_CLASSES.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "case_id", "direct_class", "seeds_with_correct_on_front",
            "seeds_with_retained_correct", "independent_selection_count",
            "independent_representative_expression", "representative_correct",
            "matches_sealed_selection_count", "matches_sealed_representative_expression",
            "valid", "invalid_reason",
        ])
        for d in results:
            w.writerow([
                d["case_id"], d["direct_class"], d["seeds_with_correct_on_front"],
                d["seeds_with_retained_correct"], d["independent_selection_count"],
                d["independent_representative_expression"], d["representative_correct"],
                d["matches_sealed_selection_count"],
                d["matches_sealed_representative_expression"],
                d["valid"], d["invalid_reason"],
            ])

    summary = {
        "schema": "muru-e2b-independent-replication-1.0.0",
        "agent": "AGENT_4_INDEPENDENT_ATTRIBUTION_REPLICATION",
        "implementation": "audit/e2b_definitive_cloud_adjudication_20260818/agent4_independent_evaluator.py",
        "shares_with_agent3": "src/muru/paper_benchmark/g2_contract.py only (the frozen G2 definition itself)",
        "independent_of_agent3": [
            "retention via rc5_selection.select_row_label (production, guarded)",
            "representative recomputed via rc5_selection.group_and_select (not read from the replay report)",
            "case enumeration re-derived from registry.CASE_FAMILIES",
            "own four-way classification chain",
        ],
        "timeout_applied": None,
        "cases": len(results),
        "counts": counts,
        "COUNT_SUM": sum(counts.values()),
        "DIRECT_RETENTION": counts["LOST_IN_RETENTION"],
        "DIRECT_GENERATION": counts["NEVER_ON_FRONT"],
        "DIRECT_THIRD_CLASS": counts["SUCCESS"] + counts["LOST_IN_CROSS_SEED"],
        "INVALID_CASES": sum(1 for d in results if not d["valid"]),
        "selection_count_matches_sealed": f"{sel_match}/{len(results)}",
        "representative_matches_sealed": f"{rep_match}/{len(results)}",
        "wall_seconds": wall,
        "seed_error_cases": [d["case_id"] for d in results if d.get("seed_errors")],
    }
    (OUTDIR / "INDEPENDENT_REPLICATION_SUMMARY.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
