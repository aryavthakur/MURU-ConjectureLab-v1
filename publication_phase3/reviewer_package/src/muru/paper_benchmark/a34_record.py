"""Deterministic A3.4 predictive-equivalence candidate-binding sidecar."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import InitVar, dataclass, field
from typing import Any, Mapping

from .a34_contract import EXPECTED_REFERENCE_DIGEST
from .a34_predictive_equivalence import PredictiveEquivalenceResult
from .truth import TruthRecord

__all__ = [
    "A34_RECORD_SCHEMA_VERSION",
    "A34_CONTRACT_IDENTITY",
    "CandidateBindingSidecar",
    "PredictiveEquivalenceSidecar",
    "candidate_expression_grammar_digest",
    "candidate_binding_digest",
    "truth_record_snapshot_payload",
    "truth_record_snapshot_digest",
    "canonical_json",
    "scientific_payload_digest",
]


A34_RECORD_SCHEMA_VERSION = "muru-a34-predictive-equivalence-record-1.0.0"
A34_CONTRACT_IDENTITY = "paper-benchmark-secondary-endpoints-1.1.0"
_ENDPOINT_NAME = "predictive_equivalence"


def _encode_float(value: float) -> float | str:
    value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0.0 else "-Infinity"
    return 0.0 if value == 0.0 else value


def _encode(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return _encode_float(value)
    if isinstance(value, (tuple, list)):
        return [_encode(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): _encode(item)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
        }
    raise TypeError(f"cannot canonically encode {type(value).__name__}")


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Serialize a scientific payload with deterministic strict JSON."""
    return json.dumps(
        _encode(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def scientific_payload_digest(payload: Mapping[str, Any]) -> str:
    """SHA-256 over a canonical endpoint scientific payload."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def candidate_expression_grammar_digest(
    expression: str | None,
    grammar_version: str,
) -> str:
    """Bind the exact supplied expression to the grammar version that parsed it."""
    if expression is not None and not isinstance(expression, str):
        raise ValueError("candidate expression must be a string or None")
    if not isinstance(grammar_version, str) or not grammar_version:
        raise ValueError("grammar version must be a non-empty string")
    return scientific_payload_digest(
        {
            "candidate_expression": expression,
            "grammar_version": grammar_version,
        }
    )


# The shorter spelling is useful at handoff sites while retaining one digest
# calculation and one canonical payload definition.
candidate_binding_digest = candidate_expression_grammar_digest


def truth_record_snapshot_payload(truth: TruthRecord) -> dict[str, object]:
    """Return the canonical scalar-law projection of a supplied truth record.

    The endpoint reconstructs its planted values from exactly these immutable
    law fields.  Row-level generated values are intentionally not part of this
    projection, so the binding stays prospective and row-value independent.
    """
    if not isinstance(truth, TruthRecord):
        raise ValueError("truth must be a TruthRecord")
    if not isinstance(truth.coefficients, Mapping) or not isinstance(
        truth.exponents, Mapping
    ):
        raise ValueError("truth coefficients and exponents must be mappings")
    return {
        "case_id": truth.case_id,
        "family": truth.family,
        "variant": truth.variant,
        "scalar_truth_defined": truth.scalar_truth_defined,
        "mathematical_family": truth.mathematical_family,
        "coefficients": dict(truth.coefficients),
        "exponents": dict(truth.exponents),
        "truth_version": truth.truth_version,
    }


def truth_record_snapshot_digest(truth: TruthRecord) -> str:
    """SHA-256 binding for the frozen scalar-law truth projection."""
    return scientific_payload_digest(truth_record_snapshot_payload(truth))


def _normalized_sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be a SHA-256 hexadecimal digest")
    normalized = value.lower()
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field} must be a SHA-256 hexadecimal digest")
    return normalized


@dataclass(frozen=True)
class CandidateBindingSidecar:
    """Canonical record that binds one score to its immutable scientific inputs."""

    case_id: str
    source_case_record_digest: str
    candidate_expression: str | None
    grammar_version: str
    truth: InitVar[TruthRecord]
    result: PredictiveEquivalenceResult
    contract_identity: str = A34_CONTRACT_IDENTITY
    reference_digest: str = EXPECTED_REFERENCE_DIGEST
    schema_version: str = A34_RECORD_SCHEMA_VERSION
    _truth_snapshot_json: str = field(init=False, repr=False)
    _truth_snapshot_digest: str = field(init=False, repr=False)

    def __post_init__(self, truth: TruthRecord) -> None:
        if not isinstance(self.case_id, str) or not self.case_id:
            raise ValueError("case ID must be a non-empty string")
        object.__setattr__(
            self,
            "source_case_record_digest",
            _normalized_sha256(self.source_case_record_digest, "source case-record digest"),
        )
        object.__setattr__(
            self,
            "reference_digest",
            _normalized_sha256(self.reference_digest, "reference digest"),
        )
        if self.candidate_expression is not None and not isinstance(
            self.candidate_expression, str
        ):
            raise ValueError("candidate expression must be a string or None")
        if not isinstance(self.grammar_version, str) or not self.grammar_version:
            raise ValueError("grammar version must be a non-empty string")
        if not isinstance(truth, TruthRecord):
            raise ValueError("truth must be a TruthRecord")
        truth_snapshot = truth_record_snapshot_payload(truth)
        if self.case_id != truth_snapshot["case_id"]:
            raise ValueError("case ID must match truth case ID")
        snapshot_json = canonical_json(truth_snapshot)
        object.__setattr__(self, "_truth_snapshot_json", snapshot_json)
        object.__setattr__(
            self,
            "_truth_snapshot_digest",
            hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest(),
        )
        if not isinstance(self.contract_identity, str) or not self.contract_identity:
            raise ValueError("contract identity must be a non-empty string")
        if not isinstance(self.schema_version, str) or not self.schema_version:
            raise ValueError("schema version must be a non-empty string")
        if not isinstance(self.result, PredictiveEquivalenceResult):
            raise ValueError("result must be a PredictiveEquivalenceResult")

    @property
    def candidate_expression_grammar_digest(self) -> str:
        return candidate_expression_grammar_digest(
            self.candidate_expression,
            self.grammar_version,
        )

    @property
    def truth_record_snapshot_digest(self) -> str:
        return self._truth_snapshot_digest

    def scientific_payload(self) -> dict[str, object]:
        """Return the deterministic endpoint projection, without free text."""
        return {
            "schema_version": self.schema_version,
            "endpoint": _ENDPOINT_NAME,
            "case_id": self.case_id,
            "source_case_record_digest": self.source_case_record_digest,
            "candidate_expression_grammar_digest": self.candidate_expression_grammar_digest,
            "truth_record_snapshot_digest": self.truth_record_snapshot_digest,
            "contract_identity": self.contract_identity,
            "reference_digest": self.reference_digest,
            "result": self.result.scientific_payload(),
        }

    def to_canonical_json(self) -> str:
        return canonical_json(self.scientific_payload())

    def to_json(self) -> str:
        return self.to_canonical_json()

    def scientific_digest(self) -> str:
        return scientific_payload_digest(self.scientific_payload())


# Both names identify the same endpoint record.  The first is the binding
# terminology used in A3.4; the second reads naturally at reporting sites.
PredictiveEquivalenceSidecar = CandidateBindingSidecar
