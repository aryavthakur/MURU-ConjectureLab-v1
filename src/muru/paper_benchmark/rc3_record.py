"""Engineering RC3: the single per-case execution record.

One frozen dataclass carries every field the A3.1 contracts consume, so a
scoring pass never has to reach back into intermediate pipeline state.

Two hard rules govern serialization:

1. **The scientific payload is deterministic.**  Sorted keys, fixed float
   formatting, canonical ordering of every set-valued field.  Two runs that
   computed the same science must produce byte-identical bytes.
2. **No timestamps, paths, hostnames, or durations live inside the
   scientific payload.**  They live in a separate provenance sidecar
   (:class:`ProvenanceSidecar`) which is written alongside and is explicitly
   excluded from the scientific hash.  This is why a failed seed contributes
   only its exception *type* to the payload: a full exception message
   routinely carries a temp-directory path or a PID, which would make two
   runs that computed identical science produce different digests.

Floats are emitted as JSON numbers, whose encoding is the shortest decimal
that round-trips the IEEE-754 binary64 value - identical on every platform
CPython supports.  ``-0.0`` is normalized to ``0.0`` so one numeric value
cannot take two digest-distinct forms.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .adequacy import CaseAdequacyStatus
from .calibration_contract import SeedStatus
from .g2_contract import FamilyStatus, G2Event, SupportStatus
from .structural_acceptance import (
    REQUIRED_FALSIFICATION_RUNGS,
    STABILITY_DENOMINATOR,
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
)

__all__ = [
    "RECORD_SCHEMA_VERSION",
    "FALSIFICATION_RUNG_ORDER",
    "PerSeedStatusEntry",
    "CaseExecutionRecord",
    "ProvenanceSidecar",
    "canonical_json",
    "scientific_payload_digest",
]

RECORD_SCHEMA_VERSION = "muru-rc3-case-record-1.0.0"

#: Frozen emission order for the reduced falsification harness.  Serialization
#: never depends on mapping iteration order.  The ORDER is RC3's (a tuple has
#: one, a frozenset does not); the MEMBERSHIP is the frozen contract's, and
#: the assertion below is what keeps the two from drifting apart.
FALSIFICATION_RUNG_ORDER: tuple[FalsificationRung, ...] = (
    FalsificationRung.F1_REPRODUCIBILITY,
    FalsificationRung.F4_COMPOUND_HOLDOUT,
    FalsificationRung.F5_SCAFFOLD_HOLDOUT,
    FalsificationRung.F7_INFLUENCE_DROP,
    FalsificationRung.F9_ENERGY_SUBSET,
    FalsificationRung.F10_NEGATIVE_CONTROL,
)

if set(FALSIFICATION_RUNG_ORDER) != set(REQUIRED_FALSIFICATION_RUNGS):
    raise ImportError(
        "RC3 falsification rung order has drifted from the frozen "
        f"REQUIRED_FALSIFICATION_RUNGS: {set(FALSIFICATION_RUNG_ORDER)} != "
        f"{set(REQUIRED_FALSIFICATION_RUNGS)}"
    )

#: The gate names the frozen acceptance predicate can report.
VALID_ACCEPTANCE_GATES: frozenset[str] = frozenset({
    "a1_adequacy", "no_candidate", "null_threshold_missing", "null_threshold",
    "stability", "complexity", "invalid_fraction", "effective_support",
    "ceiling", "falsification", "all_passed",
})


# -----------------------------------------------------------------------
# Deterministic scalar encoding
# -----------------------------------------------------------------------

def _encode_float(value: float) -> Any:
    """Encode a float deterministically and losslessly.

    ``nan``, ``inf`` and ``-inf`` are not representable in strict JSON, so
    they are emitted as their sentinel strings.  Every finite float is
    emitted as a Python float, whose ``json`` encoding is the shortest
    round-tripping decimal - stable across platforms for IEEE-754 binary64.
    """
    value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    if value == 0.0:
        return 0.0  # collapse -0.0, which would otherwise serialize distinctly
    return value


def _encode_key(key: Any) -> str:
    """Encode a mapping key.

    A ``str``-Enum key must encode as its ``.value``; plain ``str()`` would
    yield ``"FalsificationRung.F1_REPRODUCIBILITY"`` and silently differ from
    the explicit ``.value`` used elsewhere in the payload.
    """
    if hasattr(key, "value") and isinstance(key.value, str):
        return key.value
    return str(key)


def _encode(value: Any) -> Any:
    """Recursively encode a value into canonical JSON-ready form."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return _encode_float(value)
    if isinstance(value, (frozenset, set)):
        return sorted(_encode(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_encode(v) for v in value]
    if isinstance(value, Mapping):
        return {
            _encode_key(k): _encode(v)
            for k, v in sorted(value.items(), key=lambda kv: _encode_key(kv[0]))
        }
    # str-valued enums (every status enum in this package) encode as their value
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    raise TypeError(f"cannot canonically encode {type(value).__name__}")


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Serialize a payload deterministically.

    Sorted keys, no whitespace padding, no NaN literals, ASCII-escaped.
    """
    return json.dumps(
        _encode(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def scientific_payload_digest(payload: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical serialization of a scientific payload."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------
# Per-seed status
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class PerSeedStatusEntry:
    """One search seed's outcome, as recorded on a case.

    ``status`` is assigned from the actual execution outcome, never inferred
    from the finiteness of any number.
    """

    seed: int
    status: SeedStatus
    selected_expression_string: str | None = None
    error_message: str = ""

    @property
    def error_type(self) -> str:
        """The exception class name alone.

        ``error_message`` as produced by the runner is
        ``"{type}: {message}"``, and the message half routinely contains a
        temp-directory path or a PID.  Only the type is scientific; the free
        text goes to the provenance sidecar.
        """
        if not self.error_message:
            return ""
        return self.error_message.split(":", 1)[0].strip()

    def to_payload(self) -> dict[str, Any]:
        """The scientific projection: no free text, so no paths and no PIDs."""
        return {
            "seed": int(self.seed),
            "status": self.status.value,
            "selected_expression_string": self.selected_expression_string,
            "error_type": self.error_type,
        }

    def to_diagnostic_payload(self) -> dict[str, Any]:
        """The full record, for the provenance sidecar only."""
        return {**self.to_payload(), "error_message": self.error_message}


# -----------------------------------------------------------------------
# The per-case execution record
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseExecutionRecord:
    """Every field the A3.1 contracts consume, for exactly one case.

    Constructed once by the pipeline and never mutated.  Downstream scoring
    (:mod:`rc3_scoring`, ``structural_acceptance``, ``g2_contract``,
    ``g3_contract``) reads only from here.
    """

    # identity
    case_id: str
    family_id: str
    partition_label: str

    # planted truth, read ONLY for post-hoc G2 scoring, never by acceptance
    truth_family: str | None
    truth_support: frozenset[str]

    # discovered structure
    discovered_expression_string: str | None
    effective_support: frozenset[str] | None
    support_status: SupportStatus
    family_status: FamilyStatus
    discovered_family: str | None
    g2_event: G2Event

    # A1 adequacy prerequisite
    a1_case_adequacy_status: CaseAdequacyStatus

    # acceptance inputs
    valid_r2: float
    complexity: int
    selection_count: int          # k, out of 30
    selection_denominator: int    # always 30
    invalid_fraction: float

    # ceiling
    ceiling_r2: float
    ceiling_fraction: float

    # reduced falsification harness
    falsification_results: Mapping[FalsificationRung, FalsificationResult]

    # acceptance verdict
    acceptance_status: AcceptanceStatus
    acceptance_gate_reached: str

    # execution provenance that IS scientific (versions and seeds change results)
    per_seed_status: Sequence[PerSeedStatusEntry]
    seeds_used: Sequence[int]
    engine_versions: Mapping[str, str]

    #: Identity of the null threshold table acceptance gate 2 was evaluated
    #: against.  Without it, ``acceptance_status`` cannot be reproduced from
    #: the record alone.
    null_threshold_digest: str = ""

    schema_version: str = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.selection_denominator != STABILITY_DENOMINATOR:
            raise ValueError(
                f"selection_denominator must be the frozen "
                f"{STABILITY_DENOMINATOR}, got {self.selection_denominator}; "
                f"a different denominator would let k/{self.selection_denominator} "
                f"clear the frozen >= 20/30 stability gate that k/30 fails"
            )
        if not (0 <= self.selection_count <= STABILITY_DENOMINATOR):
            raise ValueError(
                f"selection_count {self.selection_count} outside "
                f"0..{STABILITY_DENOMINATOR}"
            )
        if self.acceptance_gate_reached not in VALID_ACCEPTANCE_GATES:
            raise ValueError(
                f"acceptance_gate_reached {self.acceptance_gate_reached!r} is not "
                f"a gate the frozen predicate reports; expected one of "
                f"{sorted(VALID_ACCEPTANCE_GATES)}"
            )
        missing = [
            rung.value for rung in FALSIFICATION_RUNG_ORDER
            if rung not in self.falsification_results
        ]
        if missing:
            raise ValueError(
                f"falsification_results is missing required rungs {missing}; "
                f"a missing rung must fail loudly, not serialize as null"
            )

    # -------------------------------------------------------------------
    @property
    def selection_fraction(self) -> float:
        """k/30, computed rather than stored, so the two cannot disagree."""
        return self.selection_count / STABILITY_DENOMINATOR

    def scientific_payload(self) -> dict[str, Any]:
        """The deterministic scientific payload.

        Contains no timestamp, no path, no hostname, no wall-clock duration.
        """
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "family_id": self.family_id,
            "partition_label": self.partition_label,
            "truth_family": self.truth_family,
            "truth_support": sorted(self.truth_support),
            "discovered_expression_string": self.discovered_expression_string,
            "effective_support": (
                None if self.effective_support is None
                else sorted(self.effective_support)
            ),
            "support_status": self.support_status.value,
            "family_status": self.family_status.value,
            "discovered_family": self.discovered_family,
            "g2_event": self.g2_event.value,
            "a1_case_adequacy_status": self.a1_case_adequacy_status.value,
            "valid_r2": _encode_float(self.valid_r2),
            "complexity": int(self.complexity),
            "selection_count": int(self.selection_count),
            "selection_denominator": int(self.selection_denominator),
            "selection_fraction": _encode_float(self.selection_fraction),
            "invalid_fraction": _encode_float(self.invalid_fraction),
            "ceiling_r2": _encode_float(self.ceiling_r2),
            "ceiling_fraction": _encode_float(self.ceiling_fraction),
            "falsification_results": {
                # __post_init__ guarantees every required rung is present.
                rung.value: self.falsification_results[rung].value
                for rung in FALSIFICATION_RUNG_ORDER
            },
            "acceptance_status": self.acceptance_status.value,
            "acceptance_gate_reached": self.acceptance_gate_reached,
            "null_threshold_digest": self.null_threshold_digest,
            "per_seed_status": [e.to_payload() for e in self.per_seed_status],
            "seeds_used": [int(s) for s in self.seeds_used],
            "engine_versions": {
                str(k): str(v) for k, v in sorted(self.engine_versions.items())
            },
        }

    def to_canonical_json(self) -> str:
        return canonical_json(self.scientific_payload())

    def scientific_digest(self) -> str:
        return scientific_payload_digest(self.scientific_payload())


# -----------------------------------------------------------------------
# Provenance sidecar - everything non-scientific
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class ProvenanceSidecar:
    """Non-scientific execution metadata for one case.

    Deliberately separate from :class:`CaseExecutionRecord` so that a
    timestamp can never perturb a scientific digest.
    """

    case_id: str
    scientific_digest: str
    started_utc: str
    finished_utc: str
    wall_seconds: float
    host_platform: str
    commit: str
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "scientific_digest": self.scientific_digest,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "wall_seconds": _encode_float(self.wall_seconds),
            "host_platform": self.host_platform,
            "commit": self.commit,
            "extra": _encode(dict(self.extra)),
        }

    def to_json(self) -> str:
        return canonical_json(self.to_payload())
