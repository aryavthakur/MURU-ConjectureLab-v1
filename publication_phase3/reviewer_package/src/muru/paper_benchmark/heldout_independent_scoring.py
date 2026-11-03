"""A genuinely independent recomputation of the Held-out endpoints.

Rescue requirement 11: *"A genuine independent recomputation must not import
the primary analyzer, must be written against the frozen contract text, and
should be authored before outcomes are inspected."*

The superseded ``independent_recomputation`` failed all three tests.  It
imported ``HeldOutAnalysisReport`` from the analyzer it was meant to check,
shared its constants and helpers, was edited in the *same second* as the
analyzer once outcomes were visible, and cloned every rule line for line.  Its
"0 discrepancies" was exactly what two copies of one wrong rule must produce.

**This module deliberately reimplements.**  That is the opposite of the
discipline the primary analyzer follows, and the difference is the point:

* ``heldout_contract_analysis`` **invokes** the frozen scorers, so that their
  length assertions fire and no rule is restated.
* this module **re-derives** every rule from the frozen contract text, so that
  a defect inside the shared frozen path — or inside the primary analyzer's use
  of it — has an independent chance of showing up as a disagreement.

Neither is sufficient alone; the pair is the check.  A module-level guard makes
the non-import structural rather than aspirational.

Contract text this module is written against:

* G1 — A3.5 §5.1/§5.2: ``g_spearman >= 0.80 AND trajectory_mae <= 0.80 *
  per_energy_mean_mae AND m0_accepted``; denominator 164; gate Wilson lower ≥ 0.70.
* G2 — A3.1/A3.5: ``support_status == MATCH AND family_status == MATCH``;
  ``SUPPORT_UNRESOLVED``, ``FAMILY_UNRESOLVED``, ``FAMILY_AMBIGUOUS`` ⇒
  UNEVALUABLE; denominator 144; gate Wilson lower ≥ 0.70.
* G3 — A3.5 §8.3: violations over denominator 36; UNEVALUABLE ⇒ VIOLATION;
  gate Wilson **upper** ≤ 0.15.
* Gates 1–8 — A3.5 §6.9, the ordered short-circuiting predicate.
* Gate 7 — §6.9.3: ``ceiling_fraction >= 0.80 OR (ceiling_r2 < 0.05 AND
  candidate_test_r2 > null_threshold[min(complexity, 20)])``.
* Gate 8 — §6.9.4: ``{F1, F4, F7, F10}`` all PASS, fail-closed; G1 excluded.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any, Mapping

from .registry import CASE_FAMILIES, PARTITION_CASE_COUNTS
from .rc5_store import case_slug

__all__ = [
    "IndependenceViolation",
    "WILSON_Z_FROZEN",
    "WILSON_Z_EXACT_NORMAL",
    "wilson_lower",
    "wilson_upper",
    "IndependentResult",
    "recompute_independently",
    "compare_to_primary",
]

_PRIMARY_MODULE = "muru.paper_benchmark.heldout_contract_analysis"


class IndependenceViolation(RuntimeError):
    """This module has acquired a dependency on the primary analyzer."""


def _assert_independence() -> None:
    """Structural guard: the primary analyzer must not be in our import path.

    Checked at import time and again at call time.  ``sys.modules`` may hold
    the primary because some *other* caller imported it; what is forbidden is
    this module reaching it, so the guard inspects this module's own globals
    and its declared imports rather than the global module table.
    """
    for name, value in list(globals().items()):
        module_name = getattr(value, "__module__", None)
        if module_name == _PRIMARY_MODULE:
            raise IndependenceViolation(
                f"independent recomputation binds {name!r} from "
                f"{_PRIMARY_MODULE}; it must share no object with the analyzer "
                f"it checks"
            )
        if getattr(value, "__name__", None) == _PRIMARY_MODULE:
            raise IndependenceViolation(
                f"independent recomputation imports {_PRIMARY_MODULE} as {name!r}"
            )


# ---------------------------------------------------------------------------
# Wilson intervals, written from the formula
# ---------------------------------------------------------------------------

#: The constant the frozen primary-endpoint scorers use
#: (``g2_contract.wilson_lower_95`` / ``wilson_upper_95``, both ``z = 1.96``).
WILSON_Z_FROZEN = 1.96

#: The exact standard-normal 97.5th percentile.  Used by ``analysis.wilson_interval``
#: and by the A3.4 secondary endpoints, and — as this recomputation records —
#: by the rescue's hand-rolled G1 bound.  Reported alongside so the reader can
#: see the gate verdicts are invariant to the choice.
WILSON_Z_EXACT_NORMAL = 1.959963984540054


def _wilson(successes: int, total: int, z: float) -> tuple[float, float]:
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    spread = z * sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
    return (centre - spread) / denominator, (centre + spread) / denominator


def wilson_lower(successes: int, total: int, z: float = WILSON_Z_FROZEN) -> float:
    return _wilson(successes, total, z)[0]


def wilson_upper(successes: int, total: int, z: float = WILSON_Z_FROZEN) -> float:
    return _wilson(successes, total, z)[1]


# ---------------------------------------------------------------------------
# Populations, rebuilt by a different traversal
# ---------------------------------------------------------------------------

def _independent_population(endpoint_name: str) -> tuple[str, ...]:
    """Rebuild an endpoint population family-by-family.

    The primary analyzer scans the 240 case ids and asks
    ``endpoint_applies_to_variant`` per case.  This walks the family table
    instead, cycling variants exactly as ``variant_for_replicate`` documents,
    and cross-checks its own total against ``held_out_cases_for``.  Two routes
    to the same set; a disagreement in either is a finding.
    """
    members: list[str] = []
    for family in CASE_FAMILIES:
        replicates = family.partition_counts["held_out"]
        family_members = 0
        for replicate in range(replicates):
            variant = family.variants[
                family.variant_cycle[replicate % len(family.variant_cycle)]
            ]
            if endpoint_name in variant.endpoint_names:
                members.append(f"PB|held_out|{family.code}|r{replicate:03d}")
                family_members += 1
        declared = family.held_out_cases_for(endpoint_name)
        if family_members != declared:
            raise AssertionError(
                f"{endpoint_name}/{family.code}: walked {family_members} cases, "
                f"held_out_cases_for declares {declared}"
            )
    return tuple(members)


# ---------------------------------------------------------------------------
# The ordered acceptance predicate, re-derived from §6.9
# ---------------------------------------------------------------------------

_A1_PERMITTED_TEXT = "M0_NOT_REJECTED"
_A1_REJECTION_TEXT = frozenset({
    "M0_REJECTED_M1", "M0_REJECTED_M2", "M0_REJECTED_M3", "M0_REJECTED_MULTIPLE",
})
_HARD_RUNGS_TEXT = ("F1_REPRODUCIBILITY", "F4_COMPOUND_HOLDOUT",
                    "F7_INFLUENCE_DROP", "F10_NEGATIVE_CONTROL")


def _evaluate_acceptance(
    payload: Mapping[str, Any],
    threshold_table: Mapping[int, float],
) -> tuple[str, str]:
    """Re-derive ``(status, stage)`` for one case from the §6.9 predicate text.

    Both halves matter downstream.  A case stopping at ``a1_adequacy`` is
    ``REJECTED_A1_INADEQUATE`` when A1 *rejected* M0 and ``UNEVALUABLE`` when A1
    could not decide — and G3 treats those two oppositely, VIOLATION for the
    second and SAFE for the first.  Returning only the stage would collapse the
    distinction.
    """
    a1 = payload["a1_case_adequacy_status"]
    if a1 in _A1_REJECTION_TEXT:
        return "REJECTED_A1_INADEQUATE", "a1_adequacy"
    if a1 != _A1_PERMITTED_TEXT:
        return "UNEVALUABLE", "a1_adequacy"
    if payload["discovered_expression_string"] is None:
        return "UNEVALUABLE", "no_candidate"

    complexity = int(payload["complexity"])
    threshold = threshold_table.get(min(complexity, 20))
    if threshold is None:
        return "UNEVALUABLE", "null_threshold_missing"
    if not (float(payload["valid_r2"]) > threshold):
        return "REJECTED_BELOW_NULL", "null_threshold"
    if not (float(payload["selection_fraction"]) >= 20 / 30):
        return "REJECTED_UNSTABLE", "stability"
    if not (complexity <= 20):
        return "REJECTED_OVERCOMPLEX", "complexity"
    if not (float(payload["invalid_fraction"]) <= 0.005):
        return "REJECTED_INVALID_FRACTION", "invalid_fraction"
    support = payload["effective_support"]
    if support is None or len(support) == 0:
        return "REJECTED_EMPTY_SUPPORT", "effective_support"

    ceiling_pass = float(payload["ceiling_fraction"]) >= 0.80
    floor_pass = float(payload["candidate_test_r2"]) > threshold
    ceiling_waiver = (float(payload["ceiling_r2"]) < 0.05) and floor_pass
    if not (ceiling_pass or ceiling_waiver):
        return "REJECTED_CEILING", "ceiling"

    rungs = payload["falsification_results"]
    for rung in _HARD_RUNGS_TEXT:
        if rungs.get(rung) != "PASS":
            return "REJECTED_FALSIFICATION", "falsification"
    return "STRUCTURAL_ACCEPTED", "all_passed"


def _g2_event(payload: Mapping[str, Any]) -> str:
    support = payload["support_status"]
    family = payload["family_status"]
    if support == "SUPPORT_UNRESOLVED":
        return "UNEVALUABLE"
    if family in ("FAMILY_UNRESOLVED", "FAMILY_AMBIGUOUS"):
        return "UNEVALUABLE"
    if support == "MATCH" and family == "MATCH":
        return "SUCCESS"
    return "FAILURE"


#: The G3 variants whose truth permits a mass-only acceptance (A3.5 §8.3).
#: Every other G3 variant permits no acceptance at all.
_MASS_ONLY_PERMITTED = frozenset({"F07", "F19A", "F19B"})


def _g3_event(variant_code: str, status: str, payload: Mapping[str, Any]) -> str:
    """G3 per the §8.3 variant semantics, re-derived.

    ``UNEVALUABLE`` is a violation for every variant.  ``REJECTED_*`` is safe:
    a case the pipeline declined is not a false-structure acceptance.  For the
    mass-only-permitted variants an *accepted* case is safe only if its
    effective support is a subset of ``{mass}``.
    """
    if status == "UNEVALUABLE":
        return "VIOLATION"
    if status != "STRUCTURAL_ACCEPTED":
        return "SAFE"
    if variant_code in _MASS_ONLY_PERMITTED:
        support = payload["effective_support"]
        if support is not None and set(support) <= {"mass"}:
            return "SAFE"
        return "UNSAFE"
    return "UNSAFE"


def _variant_code(case_id: str) -> str:
    """The variant's own ``code``, which is what ``classify_g3_event`` dispatches on.

    Not the ``variant_cycle`` key.  For F19 and F20 the two coincide
    (``F19A``…, ``F20A``…); for every single-variant family the cycle key is
    ``BASE`` while the code is the family code, and dispatching on ``BASE``
    would silently fall through to the no-acceptance-permitted branch.
    """
    _, _, family_code, replicate_text = case_id.split("|")
    replicate = int(replicate_text[1:])
    for family in CASE_FAMILIES:
        if family.code == family_code:
            key = family.variant_cycle[replicate % len(family.variant_cycle)]
            return family.variants[key].code
    raise AssertionError(f"unknown family in {case_id}")


# ---------------------------------------------------------------------------
# the recomputation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndependentResult:
    """Everything this module derived, with no reference to the primary."""

    denominators: Mapping[str, int]
    stage_distribution: Mapping[str, int]
    structural_accepted: int
    g1_m0_accepted: int
    g1_upper_bound_wilson_lower: float
    g1_gate_passed_at_bound: bool
    g2_successes: int
    g2_unevaluable: int
    g2_wilson_lower: float
    g2_gate_passed: bool
    g3_violations: int
    g3_wilson_upper: float
    g3_gate_passed: bool
    gate7_reached: int
    gate7_passed: int
    gate8_reached: int
    gate8_passed: int
    gate8_rung_failures: Mapping[str, int]
    f9_pass_among_gate8_reachers: int
    f5_present_in_any_record: bool
    poisoned_by_endpoint: Mapping[str, int]
    z_sensitivity: Mapping[str, Mapping[str, float]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": (
                "re-derived from the frozen contract text; the primary "
                "analyzer is not imported and no object is shared with it"
            ),
            "denominators": dict(self.denominators),
            "stage_distribution": dict(self.stage_distribution),
            "structural_accepted": self.structural_accepted,
            "g1": {
                "m0_accepted": self.g1_m0_accepted,
                "upper_bound_wilson_lower": self.g1_upper_bound_wilson_lower,
                "gate_passed_at_upper_bound": self.g1_gate_passed_at_bound,
            },
            "g2": {
                "successes": self.g2_successes,
                "unevaluable": self.g2_unevaluable,
                "wilson_lower": self.g2_wilson_lower,
                "gate_passed": self.g2_gate_passed,
            },
            "g3": {
                "violations": self.g3_violations,
                "wilson_upper": self.g3_wilson_upper,
                "gate_passed": self.g3_gate_passed,
            },
            "gate7": {"reached": self.gate7_reached, "passed": self.gate7_passed},
            "gate8": {
                "reached": self.gate8_reached,
                "passed": self.gate8_passed,
                "rung_failures": dict(self.gate8_rung_failures),
            },
            "f9_pass_among_gate8_reachers": self.f9_pass_among_gate8_reachers,
            "f5_present_in_any_record": self.f5_present_in_any_record,
            "poisoned_by_endpoint": dict(self.poisoned_by_endpoint),
            "z_sensitivity": {k: dict(v) for k, v in self.z_sensitivity.items()},
        }


def recompute_independently(
    results_root: Path,
    threshold_table: Mapping[int, float],
) -> IndependentResult:
    """Score the sealed partition from the contract text alone."""
    _assert_independence()
    records_dir = Path(results_root) / "records"

    all_cases: list[str] = []
    for family in CASE_FAMILIES:
        for replicate in range(PARTITION_CASE_COUNTS["held_out"]):
            all_cases.append(f"PB|held_out|{family.code}|r{replicate:03d}")

    payloads: dict[str, Mapping[str, Any]] = {}
    for case_id in all_cases:
        path = records_dir / f"{case_slug(case_id)}.json"
        payloads[case_id] = json.loads(path.read_text(encoding="utf-8"))

    verdicts = {c: _evaluate_acceptance(payloads[c], threshold_table) for c in all_cases}
    statuses = {c: verdicts[c][0] for c in all_cases}
    stages = {c: verdicts[c][1] for c in all_cases}

    stored_disagreements = [
        f"{c}: stored {payloads[c]['acceptance_status']}/"
        f"{payloads[c]['acceptance_gate_reached']} vs re-derived "
        f"{statuses[c]}/{stages[c]}"
        for c in all_cases
        if payloads[c]["acceptance_status"] != statuses[c]
        or payloads[c]["acceptance_gate_reached"] != stages[c]
    ]
    if stored_disagreements:
        raise AssertionError(
            f"{len(stored_disagreements)} sealed records contradict the "
            f"re-derived predicate: {stored_disagreements[:3]}"
        )

    g1_cases = _independent_population("scalar_competence")
    g2_cases = _independent_population("family_recovery")
    g3_cases = _independent_population("principal_structural_safety")

    m0_accepted = sum(
        1 for c in g1_cases
        if payloads[c]["a1_case_adequacy_status"] == _A1_PERMITTED_TEXT
    )
    g2_events = [_g2_event(payloads[c]) for c in g2_cases]
    g2_successes = sum(1 for e in g2_events if e == "SUCCESS")
    g2_unevaluable = sum(1 for e in g2_events if e == "UNEVALUABLE")

    g3_events = [_g3_event(_variant_code(c), statuses[c], payloads[c]) for c in g3_cases]
    g3_violations = sum(1 for e in g3_events if e in ("UNSAFE", "VIOLATION"))

    gate7_reached = [c for c in all_cases if stages[c] in ("ceiling", "falsification", "all_passed")]
    gate7_passed = [c for c in gate7_reached if stages[c] != "ceiling"]
    gate8_reached = [c for c in all_cases if stages[c] in ("falsification", "all_passed")]
    gate8_passed = [c for c in gate8_reached if stages[c] == "all_passed"]

    rung_failures: Counter[str] = Counter()
    for case_id in gate8_reached:
        rungs = payloads[case_id]["falsification_results"]
        for rung in _HARD_RUNGS_TEXT:
            if rungs.get(rung) != "PASS":
                rung_failures[rung] += 1

    f5_present = any(
        "F5_SCAFFOLD_HOLDOUT" in payloads[c]["falsification_results"] for c in all_cases
    )
    f9_pass = sum(
        1 for c in gate8_reached if payloads[c]["f9_stress_test_result"] == "PASS"
    )

    z_sensitivity = {
        "g1_upper_bound": {
            "z_frozen_1_96": wilson_lower(m0_accepted, len(g1_cases), WILSON_Z_FROZEN),
            "z_exact_normal": wilson_lower(m0_accepted, len(g1_cases), WILSON_Z_EXACT_NORMAL),
        },
        "g2": {
            "z_frozen_1_96": wilson_lower(g2_successes, len(g2_cases), WILSON_Z_FROZEN),
            "z_exact_normal": wilson_lower(g2_successes, len(g2_cases), WILSON_Z_EXACT_NORMAL),
        },
        "g3": {
            "z_frozen_1_96": wilson_upper(g3_violations, len(g3_cases), WILSON_Z_FROZEN),
            "z_exact_normal": wilson_upper(g3_violations, len(g3_cases), WILSON_Z_EXACT_NORMAL),
        },
    }

    return IndependentResult(
        denominators={
            "scalar_competence": len(g1_cases),
            "family_recovery": len(g2_cases),
            "principal_structural_safety": len(g3_cases),
        },
        stage_distribution=dict(sorted(Counter(stages.values()).items())),
        structural_accepted=sum(1 for s in stages.values() if s == "all_passed"),
        g1_m0_accepted=m0_accepted,
        g1_upper_bound_wilson_lower=wilson_lower(m0_accepted, len(g1_cases)),
        g1_gate_passed_at_bound=wilson_lower(m0_accepted, len(g1_cases)) >= 0.70,
        g2_successes=g2_successes,
        g2_unevaluable=g2_unevaluable,
        g2_wilson_lower=wilson_lower(g2_successes, len(g2_cases)),
        g2_gate_passed=wilson_lower(g2_successes, len(g2_cases)) >= 0.70,
        g3_violations=g3_violations,
        g3_wilson_upper=wilson_upper(g3_violations, len(g3_cases)),
        g3_gate_passed=wilson_upper(g3_violations, len(g3_cases)) <= 0.15,
        gate7_reached=len(gate7_reached),
        gate7_passed=len(gate7_passed),
        gate8_reached=len(gate8_reached),
        gate8_passed=len(gate8_passed),
        gate8_rung_failures=dict(sorted(rung_failures.items())),
        f9_pass_among_gate8_reachers=f9_pass,
        f5_present_in_any_record=f5_present,
        poisoned_by_endpoint={
            "scalar_competence": sum(
                1 for c in g1_cases if payloads[c]["execution_failure_poisoned"]
            ),
            "family_recovery": sum(
                1 for c in g2_cases if payloads[c]["execution_failure_poisoned"]
            ),
            "principal_structural_safety": sum(
                1 for c in g3_cases if payloads[c]["execution_failure_poisoned"]
            ),
        },
        z_sensitivity=z_sensitivity,
    )


def compare_to_primary(
    independent: IndependentResult,
    primary_dict: Mapping[str, Any],
) -> list[str]:
    """Report every disagreement.  An empty list means the two routes agree.

    ``primary_dict`` is the primary analyzer's ``to_dict()`` output, passed in
    by the caller.  This module never imports or constructs it.
    """
    _assert_independence()
    disagreements: list[str] = []

    def check(label: str, mine: Any, theirs: Any) -> None:
        if mine != theirs:
            disagreements.append(f"{label}: independent={mine!r} primary={theirs!r}")

    for name, value in independent.denominators.items():
        check(f"denominator/{name}", value, primary_dict["endpoint_denominators"][name])
    check("stage_distribution", independent.stage_distribution,
          primary_dict["failure_stage_distribution"])
    check("structural_accepted", independent.structural_accepted,
          primary_dict["structural_accepted_count"])
    check("g1/m0_accepted", independent.g1_m0_accepted, primary_dict["g1"]["m0_accepted_count"])
    check("g1/upper_bound_wilson_lower", independent.g1_upper_bound_wilson_lower,
          primary_dict["g1"]["wilson_lower_95"])
    check("g1/gate_passed", independent.g1_gate_passed_at_bound,
          primary_dict["g1"]["gate_passed"])
    check("g2/successes", independent.g2_successes, primary_dict["g2"]["successes"])
    check("g2/unevaluable", independent.g2_unevaluable, primary_dict["g2"]["unevaluable"])
    check("g2/wilson_lower", independent.g2_wilson_lower, primary_dict["g2"]["wilson_lower_95"])
    check("g2/gate_passed", independent.g2_gate_passed, primary_dict["g2"]["gate_passed"])
    check("g3/violations", independent.g3_violations, primary_dict["g3"]["violations"])
    check("g3/wilson_upper", independent.g3_wilson_upper, primary_dict["g3"]["wilson_upper_95"])
    check("g3/gate_passed", independent.g3_gate_passed, primary_dict["g3"]["gate_passed"])
    check("gate7/reached", independent.gate7_reached, primary_dict["gate7"]["reached"])
    check("gate7/passed", independent.gate7_passed, primary_dict["gate7"]["passed"])
    check("gate8/reached", independent.gate8_reached, primary_dict["gate8"]["reached"])
    check("gate8/passed", independent.gate8_passed, primary_dict["gate8"]["passed"])
    check("gate8/rung_failures", independent.gate8_rung_failures,
          primary_dict["gate8"]["per_rung_fail"])
    check("f9/pass_among_gate8_reachers", independent.f9_pass_among_gate8_reachers,
          primary_dict["f9"]["pass_among_gate8_reachers"])
    check("poisoned", independent.poisoned_by_endpoint,
          primary_dict["execution_failure_poisoned_by_endpoint"])
    return disagreements


_assert_independence()
