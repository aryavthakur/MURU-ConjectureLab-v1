"""Engineering RC3: acceptance wiring.

A :class:`~.rc3_record.CaseExecutionRecord` carries both the acceptance
*inputs* and the acceptance *verdict*.  Nothing stops a caller writing a
verdict that contradicts its own inputs - a record claiming
``STRUCTURAL_ACCEPTED`` while recording ``ceiling_fraction = 0.4``.

This module closes that gap by re-deriving the verdict from the record's own
inputs through the frozen predicate and comparing.  It adds no rule: every
gate, threshold and inequality comes from
``structural_acceptance.evaluate_structural_acceptance``, which RC3 does not
reimplement.

Truth-blindness is enforced structurally: :func:`candidate_from_record`
projects out only the acceptance inputs, so planted truth cannot reach the
predicate even though the record holds it.  ``truth_family`` and
``truth_support`` are read nowhere in this module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

from .rc3_record import CaseExecutionRecord
from .structural_acceptance import (
    AcceptanceResult,
    AcceptanceStatus,
    StructuralCandidate,
    evaluate_structural_acceptance,
)

__all__ = [
    "TRUTH_BLIND_FIELDS",
    "null_threshold_digest",
    "candidate_from_record",
    "derive_acceptance",
    "AcceptanceMismatch",
    "verify_record_acceptance",
]

#: The record fields the acceptance predicate is allowed to see.  Planted
#: truth is deliberately absent.
TRUTH_BLIND_FIELDS: frozenset[str] = frozenset({
    "valid_r2", "complexity", "selection_count", "selection_denominator",
    "invalid_fraction", "effective_support", "ceiling_fraction", "ceiling_r2",
    "falsification_results", "a1_case_adequacy_status",
})


def null_threshold_digest(null_threshold: Mapping[int, float]) -> str:
    """Stable identity for a null threshold table.

    Recorded on each case so that gate 2 - the only gate depending on
    calibration output - can be reproduced from the record alone.
    """
    canonical = json.dumps(
        {str(int(c)): repr(float(v)) for c, v in sorted(null_threshold.items())},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def candidate_from_record(record: CaseExecutionRecord) -> StructuralCandidate | None:
    """Project a record's acceptance inputs, and nothing else.

    Returns ``None`` when the record carries no discovered candidate, which
    the frozen predicate maps to ``UNEVALUABLE`` at the ``no_candidate`` gate.
    """
    if record.discovered_expression_string is None:
        return None
    return StructuralCandidate(
        valid_r2=record.valid_r2,
        complexity=record.complexity,
        selection_fraction=record.selection_fraction,
        invalid_fraction=record.invalid_fraction,
        effective_support=record.effective_support,
        ceiling_fraction=record.ceiling_fraction,
        ceiling_r2=record.ceiling_r2,
        falsification_results=record.falsification_results,
    )


def derive_acceptance(
    record: CaseExecutionRecord,
    null_threshold: Mapping[int, float],
) -> AcceptanceResult:
    """Re-derive the acceptance verdict from the record's own inputs."""
    return evaluate_structural_acceptance(
        a1_status=record.a1_case_adequacy_status,
        candidate=candidate_from_record(record),
        null_threshold=null_threshold,
    )


class AcceptanceMismatch(RuntimeError):
    """A record's stored verdict contradicts its own inputs."""


@dataclass(frozen=True)
class AcceptanceCheck:
    case_id: str
    recorded_status: AcceptanceStatus
    derived_status: AcceptanceStatus
    recorded_gate: str
    derived_gate: str

    @property
    def agrees(self) -> bool:
        return (
            self.recorded_status == self.derived_status
            and self.recorded_gate == self.derived_gate
        )


def verify_record_acceptance(
    record: CaseExecutionRecord,
    null_threshold: Mapping[int, float],
    strict: bool = True,
) -> AcceptanceCheck:
    """Check that a record's stored verdict matches its own inputs.

    Also verifies that the record was scored against *this* threshold table,
    when the record carries a threshold digest.

    Raises
    ------
    AcceptanceMismatch
        With ``strict=True`` (the default) on any disagreement.
    """
    expected_digest = null_threshold_digest(null_threshold)
    if record.null_threshold_digest and record.null_threshold_digest != expected_digest:
        raise AcceptanceMismatch(
            f"{record.case_id}: recorded against threshold table "
            f"{record.null_threshold_digest}, verified against {expected_digest}"
        )

    derived = derive_acceptance(record, null_threshold)
    check = AcceptanceCheck(
        case_id=record.case_id,
        recorded_status=record.acceptance_status,
        derived_status=derived.status,
        recorded_gate=record.acceptance_gate_reached,
        derived_gate=derived.gate_reached,
    )
    if strict and not check.agrees:
        raise AcceptanceMismatch(
            f"{record.case_id}: recorded {check.recorded_status.value} at "
            f"{check.recorded_gate!r}, but its own inputs derive "
            f"{check.derived_status.value} at {check.derived_gate!r}"
        )
    return check
