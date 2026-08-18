"""Engineering RC5: per-case scoring wiring for already-frozen scorers.

Pure call-site wiring.  Every quantity below is computed by an already-frozen
module; this one only decides *which* frozen path is called, *when*, and with
*what*.  It defines no threshold, no denominator, and no gate.

Three bindings it enforces structurally:

1. **G3 goes through ``g3_contract`` only.**  A3.5 section 8.3:
   ``analysis.classify_negative_control`` MUST NOT be used to score G3, because
   it disagrees with the frozen rule on 20 of the 36 Held-out G3 opportunities
   and **grants them safety credit** -- drift in the permissive,
   safety-understating direction.  ``analysis`` is not imported here at all, so
   the wrong path is not merely unused, it is unreachable.

2. **Truth is read strictly after the truth-blind verdict exists.**
   :func:`case_acceptance` derives the acceptance verdict from truth-blind
   inputs only; the A3.4 secondaries and G3 are then scored from an
   :class:`~.structural_acceptance.AcceptanceResult` that already exists.
   Ordering is enforced by the function signatures: the truth-reading scorers
   cannot be called without one.

3. **The threshold table's identity travels with the verdict.**  Gate 2 is the
   only gate depending on calibration output, so the table digest is stamped
   alongside the verdict rather than recomputed later.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .a34_parameter_recovery import ParameterRecoveryResult, score_parameter_recovery
from .a34_predictive_equivalence import (
    PredictiveEquivalenceResult,
    score_predictive_equivalence,
)
from .g2_contract import G2Event
from .g3_contract import G3Event, G3Score, classify_g3_event, score_g3
from .rc3_scoring import G2Score, score_g2
from .rc3_acceptance import derive_acceptance, null_threshold_digest
from .registry import resolve_case_id
from .structural_acceptance import (
    AcceptanceResult,
    StructuralCandidate,
    evaluate_structural_acceptance,
)
from .truth import TruthRecord

__all__ = [
    "PoisonedDisclosure",
    "execution_failure_poisoned_counts",
    "CaseAcceptance",
    "case_acceptance",
    "CaseSecondaries",
    "score_case_secondaries",
    "case_g3_event",
    "score_partition_g2",
    "score_partition_g3",
    "G3_AUTHORITY",
]

#: The sole authorised G3 scoring path, named so a reviewer can grep for it.
G3_AUTHORITY = (
    "muru.paper_benchmark.g3_contract.classify_g3_event",
    "muru.paper_benchmark.g3_contract.score_g3",
)


@dataclass(frozen=True)
class PoisonedDisclosure:
    """A3.5 obligation 16: execution-failure-poisoned counts, per endpoint.

    Section 8.2 binds the per-endpoint consequences explicitly *because they
    differ*: G1 gives no credit while the case stays in the fixed 164
    denominator, G2 gives no credit within the fixed 144, and G3 counts the
    case as a **violation** within the fixed 36.  The conservative rule is only
    costless if the count it hides is disclosed, so this is a mandatory
    separate disclosure, never a correction to a denominator.
    """

    scalar_competence: int
    family_recovery: int
    principal_structural_safety: int
    total_poisoned_cases: int
    poisoned_case_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "scalar_competence": self.scalar_competence,
            "family_recovery": self.family_recovery,
            "principal_structural_safety": self.principal_structural_safety,
            "total_poisoned_cases": self.total_poisoned_cases,
            "poisoned_case_ids": list(self.poisoned_case_ids),
            "note": (
                "A3.5 section 8.2 / obligation 16: an execution-failure-poisoned "
                "case is UNEVALUABLE. It receives no G1 or G2 credit and counts "
                "as a G3 violation, and every endpoint denominator stays fixed. "
                "These counts are disclosed, never subtracted."
            ),
        }


def execution_failure_poisoned_counts(
    records: Sequence[Any],
) -> PoisonedDisclosure:
    """Count poisoned cases per primary endpoint, from the records themselves.

    Endpoint applicability comes from the frozen registry variant, so a case is
    counted against exactly the endpoints it was ever eligible for.
    """
    poisoned = [r for r in records if r.execution_failure_poisoned]
    counts = {"scalar_competence": 0, "family_recovery": 0,
              "principal_structural_safety": 0}
    for record in poisoned:
        _family, variant, _replicate = resolve_case_id(record.case_id)
        for endpoint in counts:
            if endpoint in variant.endpoint_names:
                counts[endpoint] += 1
    return PoisonedDisclosure(
        scalar_competence=counts["scalar_competence"],
        family_recovery=counts["family_recovery"],
        principal_structural_safety=counts["principal_structural_safety"],
        total_poisoned_cases=len(poisoned),
        poisoned_case_ids=tuple(r.case_id for r in poisoned),
    )


@dataclass(frozen=True)
class CaseAcceptance:
    """One case's truth-blind acceptance verdict plus the table it used."""

    result: AcceptanceResult
    null_threshold_digest: str


def case_acceptance(
    a1_status,
    candidate: StructuralCandidate | None,
    null_threshold: Mapping[int, float],
) -> CaseAcceptance:
    """Evaluate the frozen predicate and stamp the threshold table's identity.

    ``candidate`` carries only truth-blind fields by construction
    (:class:`StructuralCandidate` has no truth slot), so this call cannot see
    planted truth even accidentally.
    """
    return CaseAcceptance(
        result=evaluate_structural_acceptance(
            a1_status=a1_status,
            candidate=candidate,
            null_threshold=null_threshold,
        ),
        null_threshold_digest=null_threshold_digest(null_threshold),
    )


@dataclass(frozen=True)
class CaseSecondaries:
    """A3.4's two secondary endpoint results for one case."""

    case_id: str
    parameter_recovery: ParameterRecoveryResult
    predictive_equivalence: PredictiveEquivalenceResult


def score_case_secondaries(
    case_id: str,
    discovered_expression_string: str | None,
    truth: TruthRecord,
    acceptance: AcceptanceResult,
) -> CaseSecondaries:
    """Score A3.4's secondaries for one case, after acceptance is decided.

    ``acceptance`` is required but deliberately not read: its presence in the
    signature is what forces the caller to have completed the truth-blind
    predicate before any truth-reading scorer runs.  A3.3/A3.4 already fix
    every rule these two scorers apply; RC5 adds none.
    """
    if truth.case_id != case_id:
        raise ValueError(
            f"truth record is for {truth.case_id!r}, not {case_id!r}"
        )
    return CaseSecondaries(
        case_id=case_id,
        parameter_recovery=score_parameter_recovery(discovered_expression_string, truth),
        predictive_equivalence=score_predictive_equivalence(
            discovered_expression_string, truth
        ),
    )


def case_g3_event(
    case_id: str,
    acceptance: AcceptanceResult,
    effective_support: frozenset[str] | None,
) -> G3Event:
    """Classify one case's G3 event through the sole frozen authority.

    The variant code comes from the registry's own ``resolve_case_id``, so the
    dispatcher receives exactly the variant the frozen registry assigns.
    """
    _, variant, _ = resolve_case_id(case_id)
    return classify_g3_event(variant.code, acceptance, effective_support)


def score_partition_g2(events: Sequence[G2Event]) -> G2Score:
    """G2 over its frozen 144 denominator, via ``rc3_scoring.score_g2``."""
    return score_g2(events)


def score_partition_g3(events: Sequence[G3Event]) -> G3Score:
    """G3 over its frozen 36 denominator, via ``g3_contract.score_g3``."""
    return score_g3(events)
