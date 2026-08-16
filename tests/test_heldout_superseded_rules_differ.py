"""Differential test: the superseded rules, run on the same sealed evidence.

A regression test that cannot fail is worse than no test.  The superseded
hostile review contained exactly that failure mode — its "Denominator
Reviewer" asserted every denominator equalled 240 and reported success, and
its "Gate 7 / Gate 8 Reviewer" branched on fields that do not exist so its
sole condition never fired.  Both passed without testing anything.

This module guards against the same emptiness in the *restoration*.  It
re-implements the superseded rules verbatim from the preserved artifact,
runs them on the identical sealed records, and asserts they reproduce the
documented wrong numbers — and that the restored analysis differs from every
one of them.  If the restoration were a relabelling rather than a repair,
every assertion below would fail.

Superseded numbers, from `MURU_HELDOUT_RESCUE_POSTRUN_DIFF.md` §5:

    G1 = 119   count(candidate_test_r2 >= 0.80)                over 240
    G2 =  23   count(g2_event == SUCCESS OR support == MATCH)  over 240
    G3 =   2   count(STRUCTURAL_ACCEPTED AND g2_pass)          over 240
    Gate 7 = 25  count(acceptance_status == STRUCTURAL_ACCEPTED)
    Gate 8 = 24  count(STRUCTURAL_ACCEPTED AND test_r2 >= 0.80)
    F9 = 0     count(f9_acceptance_calibration_status == "PROVEN_FOR_HARD_GATE")
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from muru.paper_benchmark.registry import iter_case_ids
from muru.paper_benchmark.rc5_store import case_slug

EVIDENCE_ROOT = Path(
    "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/"
    "muru-heldout-a3-6/results/held_out"
)
RESTORED = Path(__file__).resolve().parents[1] / "results" / "restored"

pytestmark = pytest.mark.skipif(
    not (EVIDENCE_ROOT / "records").is_dir()
    or not (RESTORED / "heldout_restored_analysis.json").exists(),
    reason="sealed evidence or restored analysis unavailable",
)

#: The superseded `is_adequate`, verbatim.  Note the fictitious
#: `M1_NOT_REJECTED`, which is not a member of `CaseAdequacyStatus` at all,
#: and `BOUNDARY_LIMITED`, which the frozen contract calls UNEVALUABLE.
_SUPERSEDED_ADEQUATE = ("M0_NOT_REJECTED", "M1_NOT_REJECTED", "BOUNDARY_LIMITED")


@pytest.fixture(scope="module")
def payloads() -> dict[str, dict]:
    records = EVIDENCE_ROOT / "records"
    return {
        case_id: json.loads(
            (records / f"{case_slug(case_id)}.json").read_text(encoding="utf-8")
        )
        for case_id in iter_case_ids("held_out")
    }


@pytest.fixture(scope="module")
def restored() -> dict:
    return json.loads((RESTORED / "heldout_restored_analysis.json").read_text())


def _superseded_counts(payloads: dict[str, dict]) -> dict[str, int]:
    """The superseded analyzer's arithmetic, reproduced exactly."""
    g1 = g2 = g3 = gate7 = gate8 = f9 = 0
    for data in payloads.values():
        is_poisoned = bool(data.get("execution_failure_poisoned", False)) or data.get(
            "status"
        ) == "EXECUTION_FAILURE"
        is_adequate = (
            data.get("a1_case_adequacy_status") in _SUPERSEDED_ADEQUATE
            or bool(data.get("adequate", False))
        ) and not is_poisoned

        gate7_pass = is_adequate and (
            data.get("acceptance_status") in ("STRUCTURAL_ACCEPTED", "ACCEPTED")
            or bool(data.get("gate7_pass", False))
        )
        test_r2 = float(data.get("candidate_test_r2", float("-inf")))
        g1_pass = is_adequate and (
            test_r2 >= 0.80
            or float(data.get("g1_wilson_lower", 0.0)) >= 0.80
            or bool(data.get("g1_pass", False))
        )
        g2_pass = is_adequate and (
            data.get("g2_event") == "SUCCESS"
            or data.get("support_status") == "MATCH"
            or bool(data.get("g2_recovered", False))
        )
        g3_pass = is_adequate and (
            str(data.get("g3_event", "")) == "CONJECTURE_CONFIRMED"
            or (gate7_pass and g2_pass)
            or bool(data.get("g3_pass", False))
        )
        gate8_pass = bool(data.get("gate8_pass", False)) or (gate7_pass and g1_pass)

        g1 += g1_pass
        g2 += g2_pass
        g3 += g3_pass
        gate7 += gate7_pass
        gate8 += gate8_pass
        f9 += bool(data.get("f9_pass", False)) or data.get(
            "f9_acceptance_calibration_status"
        ) == "PROVEN_FOR_HARD_GATE"
    return {
        "g1": g1, "g2": g2, "g3": g3,
        "gate7": gate7, "gate8": gate8, "f9": f9,
        "denominator": len(payloads),
    }


def test_superseded_rules_reproduce_their_documented_wrong_numbers(payloads):
    """Anchors the differential: these are the numbers that were reported."""
    counts = _superseded_counts(payloads)
    assert counts["denominator"] == 240
    assert counts["g1"] == 119
    assert counts["g2"] == 23
    assert counts["g3"] == 2
    assert counts["gate7"] == 25
    assert counts["gate8"] == 24
    assert counts["f9"] == 0


def test_superseded_is_adequate_was_true_for_every_case(payloads):
    """The load-bearing defect: BOUNDARY_LIMITED accepted as adequate."""
    adequate = sum(
        1 for d in payloads.values()
        if d["a1_case_adequacy_status"] in _SUPERSEDED_ADEQUATE
    )
    assert adequate == 240
    statuses = {d["a1_case_adequacy_status"] for d in payloads.values()}
    assert statuses == {"M0_NOT_REJECTED", "BOUNDARY_LIMITED"}


def test_superseded_fields_are_absent_from_every_sealed_record(payloads):
    """Every superseded branch on these fields took its default on all 240."""
    invented = (
        "gate7_pass", "gate8_pass", "g1_pass", "g1_wilson_lower", "g2_recovered",
        "g3_pass", "g3_event", "f9_pass", "adequate", "status", "stability_score",
    )
    for field in invented:
        present = sum(1 for d in payloads.values() if field in d)
        assert present == 0, f"{field} present in {present} records"


def test_restored_analysis_differs_from_every_superseded_quantity(payloads, restored):
    """The repair changes every primary number.  It is not a relabelling."""
    superseded = _superseded_counts(payloads)

    assert restored["g1"]["denominator"] == 164 != superseded["denominator"]
    assert restored["g1"]["competent"] != superseded["g1"]

    assert restored["g2"]["denominator"] == 144 != superseded["denominator"]
    assert restored["g2"]["successes"] != superseded["g2"]

    assert restored["g3"]["denominator"] == 36 != superseded["denominator"]
    assert restored["g3"]["violations"] != superseded["g3"]

    # Gate 7's superseded count numerically coincides with structural
    # acceptance (25).  The restored Gate 7 is a different quantity and a
    # different number.
    assert superseded["gate7"] == restored["structural_accepted_count"] == 25
    assert restored["gate7"]["passed"] == 26 != superseded["gate7"]

    assert restored["gate8"]["passed"] != superseded["gate8"]
    assert restored["f9"]["pass_among_gate8_reachers"] != superseded["f9"]


def test_the_verdict_itself_is_inverted(payloads, restored):
    """Superseded: `decision_passed: true`.  Restored: all three endpoints fail."""
    superseded = _superseded_counts(payloads)
    superseded_decision = (
        superseded["g1"] > 0 and superseded["g2"] > 0 and superseded["gate8"] > 0
    )
    assert superseded_decision is True
    assert restored["decision"]["all_primary_endpoints_pass"] is False
    assert restored["decision"]["g1_gate_passed"] is False
    assert restored["decision"]["g2_gate_passed"] is False
    assert restored["decision"]["g3_gate_passed"] is False


def test_ineligible_families_supplied_most_superseded_g2_successes(payloads):
    """16 of the 23 superseded G2 'successes' came from F07 and F19."""
    from muru.paper_benchmark.heldout_endpoint_populations import (
        build_endpoint_population,
    )

    eligible = build_endpoint_population("family_recovery").case_id_set
    credited = [
        case_id for case_id, d in payloads.items()
        if d["a1_case_adequacy_status"] in _SUPERSEDED_ADEQUATE
        and (d["g2_event"] == "SUCCESS" or d["support_status"] == "MATCH")
    ]
    assert len(credited) == 23
    ineligible = [c for c in credited if c not in eligible]
    assert len(ineligible) == 16
    assert {c.split("|")[2] for c in ineligible} == {"F07", "F19"}
