#!/usr/bin/env python3
"""Recompute the decomposition's root-cause ranking from the DIRECT E2b
attribution, and cross-tabulate it against the v1 taxonomy that Gate 1 falsified.

Reads only sealed evidence + the adjudicated case-level output. Invents no class,
moves no case, changes no historical number.
"""
from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audit" / "e2b_definitive_cloud_adjudication_20260818"
V1 = ROOT / "v2_design_reference" / "MURU_V1_G2_FAILURE_TAXONOMY.csv"

DENOM = 144


def main() -> None:
    gate = json.loads((OUT / "GATE_1_DEFINITIVE.json").read_text())
    direct = {r["CASE_ID"]: r["FROZEN_CLASS"]
              for r in csv.DictReader(open(OUT / "FROZEN_DIRECT_CLASSES.csv"))}
    v1rows = list(csv.DictReader(open(V1)))
    v1 = {r["case_id"]: r for r in v1rows}

    counts = collections.Counter(direct.values())
    ranking = []
    for rank, (cls, n) in enumerate(counts.most_common(), start=1):
        ranking.append({
            "rank": rank, "class": cls, "count": n,
            "percentage": round(100.0 * n / DENOM, 2),
        })

    # cross-tab: direct class x v1 root_cause_class
    xtab = collections.defaultdict(collections.Counter)
    for cid, dc in direct.items():
        rc = v1.get(cid, {}).get("root_cause_class", "<NOT_IN_V1>")
        xtab[dc][rc] += 1

    # v1's own oracle statistic vs the direct partition
    v1_oracle_true = sum(1 for r in v1rows if r["oracle_any_seed_correct"] == "True")
    v1_oracle_false = sum(1 for r in v1rows if r["oracle_any_seed_correct"] == "False")
    direct_retained_ever = counts["SUCCESS"] + counts["LOST_IN_CROSS_SEED"]
    direct_retained_never = counts["NEVER_ON_FRONT"] + counts["LOST_IN_RETENTION"]

    # per-case agreement of the oracle statistic (case level, not just totals)
    oracle_case_agree = 0
    oracle_case_disagree = []
    for cid, dc in direct.items():
        v1_flag = v1.get(cid, {}).get("oracle_any_seed_correct")
        direct_flag = "True" if dc in ("SUCCESS", "LOST_IN_CROSS_SEED") else "False"
        if v1_flag == direct_flag:
            oracle_case_agree += 1
        else:
            oracle_case_disagree.append({"case_id": cid, "v1_oracle": v1_flag,
                                         "direct_class": dc, "direct_implies": direct_flag})

    v1_counts = collections.Counter(r["root_cause_class"] for r in v1rows)

    revision = {
        "schema": "muru-e2b-attribution-revision-1.0.0",
        "denominator": DENOM,
        "trigger": "GATE_1 = FAIL (E2B_69_57_HOOK = FAIL). The v1 decomposition's "
                   "root-cause ranking is falsified and must be republished from the "
                   "direct measurement before any E4 arm may be re-authorised.",
        "direct_root_cause_ranking": ranking,
        "RANK_1": ranking[0]["class"] if len(ranking) > 0 else None,
        "RANK_2": ranking[1]["class"] if len(ranking) > 1 else None,
        "RANK_3": ranking[2]["class"] if len(ranking) > 2 else None,
        "RANK_4": ranking[3]["class"] if len(ranking) > 3 else None,
        "v1_root_cause_ranking_superseded": dict(v1_counts),
        "cross_tabulation_direct_x_v1": {k: dict(v) for k, v in xtab.items()},
        "oracle_cross_check": {
            "meaning": "v1's oracle_any_seed_correct records whether ANY of the 30 "
                       "per-seed RETAINED candidates was correct. The direct partition "
                       "implies the same predicate: True iff SUCCESS or LOST_IN_CROSS_SEED.",
            "v1_oracle_true": v1_oracle_true,
            "v1_oracle_false": v1_oracle_false,
            "direct_retained_correct_ever": direct_retained_ever,
            "direct_retained_correct_never": direct_retained_never,
            "totals_match": (v1_oracle_true == direct_retained_ever
                             and v1_oracle_false == direct_retained_never),
            "case_level_agreement": f"{oracle_case_agree}/{DENOM}",
            "case_level_disagreements": oracle_case_disagree,
        },
        "gate_1_summary": {
            "DIRECT_RETENTION": gate["DIRECT_RETENTION"],
            "DIRECT_GENERATION": gate["DIRECT_GENERATION"],
            "DIRECT_THIRD_CLASS": gate["DIRECT_THIRD_CLASS"],
            "HISTORICAL_RETENTION": gate["HISTORICAL_RETENTION"],
            "HISTORICAL_GENERATION": gate["HISTORICAL_GENERATION"],
            "RETENTION_DEVIATION": gate["RETENTION_DEVIATION"],
            "GENERATION_DEVIATION": gate["GENERATION_DEVIATION"],
            "E2B_69_57_HOOK": gate["E2B_69_57_HOOK"],
            "GATE_1": gate["GATE_1"],
        },
        "robustness_of_the_FAIL": {
            "concern": "v1 carries a separate 12-case GRAMMAR_REPRESENTABILITY class "
                       "(F18, 'exp' absent from the grammar) which also implies the truth "
                       "could never appear on a front. A critic may ask whether the "
                       "generation comparison should be 57+12=69 rather than the frozen 57.",
            "frozen_answer": "The frozen authority states 69/57 literally and may not be "
                             "reinterpreted after seeing results.",
            "robustness": "The FAIL verdict is invariant to that reinterpretation: against "
                          "57 the generation deviation is |DIRECT_GENERATION-57|; against 69 "
                          "it would be even larger. Both exceed the 10-case tolerance.",
        },
    }
    (OUT / "ATTRIBUTION_REVISION.json").write_text(json.dumps(revision, indent=2))
    print(json.dumps({k: v for k, v in revision.items()
                      if k not in ("cross_tabulation_direct_x_v1",)}, indent=2)[:4000])
    print("\nCROSS-TAB direct x v1:")
    for dc, ctr in xtab.items():
        print(f"  {dc}: {dict(ctr)}")


if __name__ == "__main__":
    main()
