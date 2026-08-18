"""Strict projection from a sealed case-record payload to the frozen typed inputs.

Rescue requirement 10: *"Branch on no field absent from the record schema."*

The superseded analyzer read eleven fields that do not exist in
``muru-rc5-case-record-2.0.0`` (``gate7_pass``, ``gate8_pass``, ``g1_pass``,
``g1_wilson_lower``, ``g2_recovered``, ``g3_pass``, ``g3_event``, ``f9_pass``,
``adequate``, ``status``, ``stability_score``).  Every one of them returned its
``dict.get`` default on all 240 records, and the reported numbers were produced
entirely by those fallback arms.  A missing field must therefore be an error,
never a default.

This module supplies the only accessor the restoration layer is permitted to
use: :meth:`SealedRecord.require`, which raises on an absent key.  It reads no
truth, applies no rule, and decides no endpoint.  Every scientific decision is
delegated to a frozen scorer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .adequacy import CaseAdequacyStatus
from .g2_contract import FamilyStatus, G2Event, SupportStatus
from .rc3_acceptance import candidate_from_record  # noqa: F401  (documented authority)
from .rc3_record import RECORD_SCHEMA_VERSION
from .rc5_store import case_slug
from .structural_acceptance import (
    AcceptanceResult,
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
    StructuralCandidate,
)

__all__ = [
    "SEALED_RECORD_KEYS",
    "MissingRecordField",
    "SchemaConformanceError",
    "SealedRecord",
    "load_sealed_record",
    "load_sealed_partition",
]


class MissingRecordField(KeyError):
    """A field the analyzer tried to read is absent from the sealed record."""


class SchemaConformanceError(RuntimeError):
    """A sealed record does not conform to the frozen record schema."""


#: The exact key set of ``muru-rc5-case-record-2.0.0`` as sealed.  Verified
#: uniform across all 240 Held-out records: one distinct key set, 35 keys.
SEALED_RECORD_KEYS: frozenset[str] = frozenset({
    "a1_case_adequacy_status",
    "acceptance_gate_reached",
    "acceptance_status",
    "candidate_test_r2",
    "case_id",
    "ceiling_fraction",
    "ceiling_r2",
    "complexity",
    "discovered_expression_string",
    "discovered_family",
    "effective_support",
    "engine_versions",
    "execution_failure_poisoned",
    "f9_acceptance_calibration_status",
    "f9_stress_test_metric",
    "f9_stress_test_result",
    "falsification_results",
    "family_id",
    "family_status",
    "g2_event",
    "invalid_fraction",
    "null_threshold_digest",
    "partition_label",
    "per_seed_status",
    "schema_version",
    "seeds_used",
    "selection_count",
    "selection_denominator",
    "selection_fraction",
    "support_status",
    "truth_family",
    "truth_support",
    "valid_r2",
    "winning_class_distinct_coefficient_vectors",
    "winning_class_distinct_expression_strings",
})


@dataclass(frozen=True)
class SealedRecord:
    """One sealed case record, read strictly.

    ``payload`` is the sealed JSON exactly as written.  Nothing in this class
    mutates it, and nothing writes back to the evidence root.
    """

    case_id: str
    payload: Mapping[str, Any]

    # ------------------------------------------------------------------
    # the only permitted accessor
    # ------------------------------------------------------------------

    def require(self, key: str) -> Any:
        """Return ``payload[key]``, raising if the key is absent.

        There is deliberately no ``default`` parameter.  A field the frozen
        contract needs and the record does not carry is a contract failure, not
        a zero.
        """
        if key not in self.payload:
            raise MissingRecordField(
                f"{self.case_id}: sealed record has no field {key!r}; the "
                f"restoration layer may not branch on a field absent from "
                f"{RECORD_SCHEMA_VERSION}"
            )
        return self.payload[key]

    def assert_schema_conformance(self) -> None:
        """Reject any record whose key set is not exactly the frozen schema."""
        version = self.require("schema_version")
        if version != RECORD_SCHEMA_VERSION:
            raise SchemaConformanceError(
                f"{self.case_id}: schema_version {version!r}, expected "
                f"{RECORD_SCHEMA_VERSION!r}"
            )
        actual = frozenset(self.payload)
        if actual != SEALED_RECORD_KEYS:
            missing = sorted(SEALED_RECORD_KEYS - actual)
            extra = sorted(actual - SEALED_RECORD_KEYS)
            raise SchemaConformanceError(
                f"{self.case_id}: record key set differs from the frozen "
                f"schema; missing={missing} extra={extra}"
            )

    # ------------------------------------------------------------------
    # typed projections — total, no defaults, no rules
    # ------------------------------------------------------------------

    @property
    def a1_status(self) -> CaseAdequacyStatus:
        return CaseAdequacyStatus(self.require("a1_case_adequacy_status"))

    @property
    def effective_support(self) -> frozenset[str] | None:
        raw = self.require("effective_support")
        if raw is None:
            return None
        return frozenset(str(item) for item in raw)

    @property
    def falsification_results(
        self,
    ) -> Mapping[FalsificationRung, FalsificationResult]:
        """Project the stored rung map, rejecting any unknown rung key.

        A stringly-typed rung name that is not a member of
        ``FalsificationRung`` would be silently dropped by a permissive
        projection, and a dropped required rung makes ``check_gate8``
        fail-closed for the wrong reason.  Both directions are errors here.
        """
        raw = self.require("falsification_results")
        projected: dict[FalsificationRung, FalsificationResult] = {}
        for rung_name, result_name in raw.items():
            try:
                rung = FalsificationRung(rung_name)
            except ValueError as exc:
                raise SchemaConformanceError(
                    f"{self.case_id}: falsification_results carries unknown "
                    f"rung {rung_name!r}; F5_SCAFFOLD_HOLDOUT is superseded and "
                    f"no rung outside FalsificationRung may be emitted"
                ) from exc
            projected[rung] = FalsificationResult(result_name)
        return projected

    @property
    def structural_candidate(self) -> StructuralCandidate | None:
        """Mirror :func:`rc3_acceptance.candidate_from_record` over a payload.

        The frozen projection takes a ``CaseExecutionRecord``; the sealed
        evidence is payload JSON with no inverse constructor.  This property is
        a field-for-field transcription of that frozen projection and adds no
        term: ``None`` exactly when ``discovered_expression_string`` is null,
        and otherwise the identical nine acceptance inputs.  It reads no truth
        field.
        """
        if self.require("discovered_expression_string") is None:
            return None
        return StructuralCandidate(
            valid_r2=float(self.require("valid_r2")),
            complexity=int(self.require("complexity")),
            selection_fraction=float(self.require("selection_fraction")),
            invalid_fraction=float(self.require("invalid_fraction")),
            effective_support=self.effective_support,
            ceiling_fraction=float(self.require("ceiling_fraction")),
            ceiling_r2=float(self.require("ceiling_r2")),
            falsification_results=self.falsification_results,
            candidate_test_r2=float(self.require("candidate_test_r2")),
        )

    @property
    def stored_acceptance(self) -> AcceptanceResult:
        """The verdict as sealed — used only to check the recomputation."""
        return AcceptanceResult(
            status=AcceptanceStatus(self.require("acceptance_status")),
            gate_reached=str(self.require("acceptance_gate_reached")),
        )

    @property
    def stored_g2_event(self) -> G2Event:
        return G2Event(self.require("g2_event"))

    @property
    def support_status(self) -> SupportStatus:
        return SupportStatus(self.require("support_status"))

    @property
    def family_status(self) -> FamilyStatus:
        return FamilyStatus(self.require("family_status"))

    @property
    def execution_failure_poisoned(self) -> bool:
        return bool(self.require("execution_failure_poisoned"))

    @property
    def f9_stress_test_result(self) -> FalsificationResult | None:
        raw = self.require("f9_stress_test_result")
        return None if raw is None else FalsificationResult(raw)

    @property
    def f9_stress_test_metric(self) -> float | None:
        raw = self.require("f9_stress_test_metric")
        return None if raw is None else float(raw)

    @property
    def f9_acceptance_calibration_status(self) -> str:
        return str(self.require("f9_acceptance_calibration_status"))

    @property
    def null_threshold_digest(self) -> str:
        return str(self.require("null_threshold_digest"))


def load_sealed_record(records_dir: Path, case_id: str) -> SealedRecord:
    """Read one sealed record, enforcing schema conformance immediately."""
    path = Path(records_dir) / f"{case_slug(case_id)}.json"
    if not path.exists():
        raise SchemaConformanceError(
            f"{case_id}: sealed record missing at {path}; a missing record may "
            f"not be silently skipped, it would shrink an endpoint population"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("case_id") != case_id:
        raise SchemaConformanceError(
            f"{case_id}: record at {path} declares case_id "
            f"{payload.get('case_id')!r}"
        )
    record = SealedRecord(case_id=case_id, payload=payload)
    record.assert_schema_conformance()
    return record


def load_sealed_partition(
    results_root: Path,
    case_ids: tuple[str, ...],
) -> dict[str, SealedRecord]:
    """Read every named case record.  Any absence is fatal, never skipped."""
    records_dir = Path(results_root) / "records"
    return {case_id: load_sealed_record(records_dir, case_id) for case_id in case_ids}
