"""R2: equivalence between every supported G3 entry point for F07.

Three entry points exist for classifying an F07 (mass-only g truth) safety
opportunity:

  1. ``g3_contract.classify_f07_event`` -- the direct per-variant classifier.
  2. ``g3_contract.classify_g3_event("F07", ...)`` -- the reference dispatcher
     (the incomplete path this repair fixes).
  3. ``analysis.classify_negative_control`` -- the function ``analysis.
     umbrella_decision`` (the G3 gate actually reached in production) calls.

The adjudication (audit/muru_benchmark_core_defect_adjudication.json,
DEFECT_B3) found (2) missing its F07 branch while (3) already classifies F07
correctly. This test proves all three now agree on the same F07 event for
every hand-built fixture, so repairing the reference dispatcher did not
diverge from the already-correct production path. All fixtures are
hand-built; no case outcome, Development, or Held-out data is read.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.analysis import CaseOutcome, classify_negative_control
from muru.paper_benchmark.g3_contract import G3Event, classify_f07_event, classify_g3_event
from muru.paper_benchmark.structural_acceptance import AcceptanceResult, AcceptanceStatus

# A development-partition F07 case id, hand-constructed per registry.py's
# documented "PB|{partition}|{family_code}|r{replicate:03d}" format. This is
# a pure metadata label resolved by registry.resolve_case_id; it loads no
# inputs, truth values, or outcome data, and it is not a Held-out case.
F07_CASE_ID = "PB|development|F07|r000"


def _outcome(unsupported_non_mass: bool, richer_family: bool) -> CaseOutcome:
    return CaseOutcome(
        case_id=F07_CASE_ID,
        g_spearman=0.0,
        trajectory_mae=0.0,
        per_energy_mean_mae=1.0,
        m0_accepted=True,
        family_recovered=False,
        unsupported_non_mass=unsupported_non_mass,
        richer_family=richer_family,
        adversarial_flagged=False,
        null_flagged=False,
    )


# Each row: (g3_contract acceptance/support fixture, equivalent analysis.py
# CaseOutcome flags, expected "is an F07 safety error" boolean).
EQUIVALENT_SCENARIOS = [
    pytest.param(
        AcceptanceResult(status=AcceptanceStatus.STRUCTURAL_ACCEPTED, gate_reached="all_passed"),
        frozenset({"mass"}),
        False,
        False,
        False,
        id="accepted_mass_only_safe",
    ),
    pytest.param(
        AcceptanceResult(status=AcceptanceStatus.STRUCTURAL_ACCEPTED, gate_reached="all_passed"),
        frozenset({"mass", "descriptor"}),
        True,
        False,
        True,
        id="accepted_unsupported_non_mass_unsafe",
    ),
    pytest.param(
        AcceptanceResult(status=AcceptanceStatus.STRUCTURAL_ACCEPTED, gate_reached="all_passed"),
        frozenset({"mass", "descriptor", "descriptor2"}),
        False,
        True,
        True,
        id="accepted_richer_family_unsafe",
    ),
    pytest.param(
        AcceptanceResult(status=AcceptanceStatus.REJECTED_BELOW_NULL, gate_reached="null_threshold"),
        None,
        False,
        False,
        False,
        id="rejected_safe",
    ),
]


@pytest.mark.parametrize(
    "acceptance,support,unsupported_non_mass,richer_family,expect_error",
    EQUIVALENT_SCENARIOS,
)
def test_all_f07_entry_points_agree(acceptance, support, unsupported_non_mass, richer_family, expect_error):
    direct = classify_f07_event(acceptance, support)
    dispatched = classify_g3_event("F07", acceptance, support)
    production = classify_negative_control(_outcome(unsupported_non_mass, richer_family))

    assert direct == dispatched, "direct classifier and reference dispatcher disagree"

    direct_is_error = direct in (G3Event.UNSAFE, G3Event.VIOLATION)
    assert direct_is_error == expect_error
    assert (production is not None) == expect_error, (
        "reference-contract path and analysis.classify_negative_control (the "
        "path analysis.umbrella_decision actually calls for G3) disagree on "
        "whether this scenario is an F07 safety error"
    )
