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
    F9_ACCEPTANCE_CALIBRATION_STATUS,
    REQUIRED_HARD_GATES,
    SECONDARY_REPORTED_RUNGS,
    STABILITY_DENOMINATOR,
    AcceptanceStatus,
    FalsificationResult,
    FalsificationRung,
)

__all__ = [
    "RECORD_SCHEMA_VERSION",
    "LEGACY_RECORD_SCHEMA_VERSIONS",
    "LEGACY_FALSIFICATION_RUNG_NAMES",
    "GATE8_REACHING_GATES",
    "HARD_GATE_ORDER",
    "F9_ACCEPTANCE_CALIBRATION_STATUS",
    "SchemaVersionError",
    "record_schema_generation",
    "PerSeedStatusEntry",
    "CaseExecutionRecord",
    "ProvenanceSidecar",
    "canonical_json",
    "scientific_payload_digest",
]

#: Bumped by A3.5 section 6.9.4 (RC5 obligations 14, 18, 19).  This is a
#: **breaking** change, and the major version says so: under 1.0.0 a record was
#: required to carry all six rungs, so a 2.0.0 record -- which legitimately
#: carries no ``F5_SCAFFOLD_HOLDOUT`` and separates F9 into its own reported
#: fields -- would have been rejected outright by the old ``__post_init__``.
#: The two generations are therefore not interchangeable in either direction,
#: and :func:`record_schema_generation` refuses to guess.
RECORD_SCHEMA_VERSION = "muru-rc5-case-record-2.0.0"

#: Record schema versions written before the A3.5 Gate-8 correction.  Kept so
#: an old serialized record stays *parseable and identifiable*; it is never
#: reinterpreted as a current-generation record.
LEGACY_RECORD_SCHEMA_VERSIONS: frozenset[str] = frozenset({
    "muru-rc3-case-record-1.0.0",
})

#: What a legacy record's ``falsification_results`` mapping contained.  Held as
#: plain strings because two of them are no longer members of
#: :class:`FalsificationRung`.
LEGACY_FALSIFICATION_RUNG_NAMES: tuple[str, ...] = (
    "F1_REPRODUCIBILITY",
    "F4_COMPOUND_HOLDOUT",
    "F5_SCAFFOLD_HOLDOUT",
    "F7_INFLUENCE_DROP",
    "F9_ENERGY_SUBSET",
    "F10_NEGATIVE_CONTROL",
)

#: Frozen emission order for the hard Gate-8 rungs.  Serialization never
#: depends on mapping iteration order.  The ORDER is RC3's (a tuple has one, a
#: frozenset does not); the MEMBERSHIP is the frozen contract's, and the
#: assertion below is what keeps the two from drifting apart.
HARD_GATE_ORDER: tuple[FalsificationRung, ...] = (
    FalsificationRung.F1_REPRODUCIBILITY,
    FalsificationRung.F4_COMPOUND_HOLDOUT,
    FalsificationRung.F7_INFLUENCE_DROP,
    FalsificationRung.F10_NEGATIVE_CONTROL,
)

#: There is deliberately NO ``FALSIFICATION_RUNG_ORDER`` alias.  An RC3-era
#: importer expecting six rungs must break loudly at import time: silently
#: handing it a four-member tuple under the old name would move exactly the
#: reinterpretation this MAJOR version bump exists to prevent from the data
#: layer to the code layer, and any six-rung completeness check it performs
#: would then pass vacuously.

if set(HARD_GATE_ORDER) != set(REQUIRED_HARD_GATES):
    raise ImportError(
        "RC5 hard-gate emission order has drifted from the frozen "
        f"REQUIRED_HARD_GATES: {set(HARD_GATE_ORDER)} != {set(REQUIRED_HARD_GATES)}"
    )

if set(HARD_GATE_ORDER) & SECONDARY_REPORTED_RUNGS:
    raise ImportError(
        "a secondary reported rung appears in the hard-gate emission order; "
        "A3.5 section 6.9.4 forbids F9 from ever gating"
    )

#: The two gates a case can report only after Gate 8 was actually evaluated.
#: A3.5 obligation 19 requires the F9 secondary fields on every such record.
GATE8_REACHING_GATES: frozenset[str] = frozenset({"falsification", "all_passed"})

#: A3.5 section 6.0: ``NOT_APPLICABLE`` is "never emitted" by any rung, and
#: ``EXECUTION_FAILURE`` "resolves to FAIL before entering the mapping Gate 8
#: consumes".  So the only two values that may ever reach a record are these.
_EMITTABLE_RESULTS: frozenset[FalsificationResult] = frozenset({
    FalsificationResult.PASS,
    FalsificationResult.FAIL,
})


class SchemaVersionError(ValueError):
    """A serialized record's schema version is unknown or mis-declared."""


def record_schema_generation(payload: Mapping[str, Any]) -> str:
    """Classify a serialized payload's schema generation, without guessing.

    Returns ``"current"`` or ``"legacy"``.  Raises on an absent or unrecognised
    ``schema_version``: a record whose generation cannot be established is
    never silently read as either one, because the two disagree about what the
    same ``falsification_results`` mapping *means*.
    """
    version = payload.get("schema_version")
    if not isinstance(version, str):
        raise SchemaVersionError(
            f"record schema_version must be a string, got {type(version).__name__}"
        )
    if version == RECORD_SCHEMA_VERSION:
        return "current"
    if version in LEGACY_RECORD_SCHEMA_VERSIONS:
        return "legacy"
    raise SchemaVersionError(
        f"unrecognised record schema_version {version!r}; known versions are "
        f"{RECORD_SCHEMA_VERSION!r} and {sorted(LEGACY_RECORD_SCHEMA_VERSIONS)}"
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

    #: The four hard Gate-8 rungs, and only those.  A3.5 section 6.9.4.
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

    #: A3.5 section 6.3(i) / 6.9.3: the single ``candidate_test_r2``
    #: computation, recorded so Gate 7's waiver branch is reproducible from
    #: the record alone.
    candidate_test_r2: float = float("-inf")

    #: A3.5 section 6.9.4 / obligation 19.  F9's secondary stress test:
    #: computed and reported for every case reaching Gate 8, and read by
    #: neither ``REQUIRED_HARD_GATES`` nor ``check_gate8``.  ``None`` exactly
    #: when the case never reached Gate 8.
    f9_stress_test_result: FalsificationResult | None = None
    f9_stress_test_metric: float | None = None
    f9_acceptance_calibration_status: str = F9_ACCEPTANCE_CALIBRATION_STATUS

    schema_version: str = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        # A record may only ever stamp itself with the current schema.  Without
        # this the writer could produce a record its own classifier calls
        # `legacy`, which is the reinterpretation the bump exists to prevent.
        if self.schema_version != RECORD_SCHEMA_VERSION:
            raise SchemaVersionError(
                f"a record may only be written under {RECORD_SCHEMA_VERSION!r}, "
                f"not {self.schema_version!r}; the two generations are not "
                f"interchangeable in either direction"
            )
        # A3.5 section 6.9.4 fixes this string; a record that self-declared
        # PROVEN would launder section 12's promotion prohibition into a report.
        if self.f9_acceptance_calibration_status != F9_ACCEPTANCE_CALIBRATION_STATUS:
            raise ValueError(
                f"f9_acceptance_calibration_status must be "
                f"{F9_ACCEPTANCE_CALIBRATION_STATUS!r}, not "
                f"{self.f9_acceptance_calibration_status!r}; promoting F9 requires "
                f"a new prospective amendment and a fresh F9-specific calibration"
            )
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
        reached_gate8 = self.acceptance_gate_reached in GATE8_REACHING_GATES
        stray = sorted(
            str(getattr(rung, "value", rung))
            for rung in self.falsification_results
            if rung not in REQUIRED_HARD_GATES
        )
        if stray:
            raise ValueError(
                f"falsification_results carries non-hard-gate rungs {stray}; "
                f"F5 is superseded and F9 is a reported secondary recorded in "
                f"f9_stress_test_result / f9_stress_test_metric, so neither may "
                f"enter the Gate-8 mapping"
            )
        if reached_gate8:
            missing = [
                rung.value for rung in HARD_GATE_ORDER
                if rung not in self.falsification_results
            ]
            if missing:
                raise ValueError(
                    f"falsification_results is missing required hard gates "
                    f"{missing}; a missing rung must fail loudly, not serialize "
                    f"as null"
                )
        elif self.falsification_results:
            # A3.5 section 6.9.4: a case that stopped before Gate 8 "never
            # reaches check_gate8 at all" and produced no rung results.  It
            # cannot carry PASS or FAIL (nothing was evaluated) and section 6.0
            # forbids NOT_APPLICABLE, so it must carry nothing.
            raise ValueError(
                f"{self.case_id} stopped at {self.acceptance_gate_reached!r}, "
                f"before Gate 8, but carries falsification results "
                f"{sorted(str(getattr(r, 'value', r)) for r in self.falsification_results)}; "
                f"a case that never reached Gate 8 produced no rung results"
            )
        has_f9 = self.f9_stress_test_result is not None
        if reached_gate8 and not has_f9:
            raise ValueError(
                f"{self.case_id} reached Gate 8 at "
                f"{self.acceptance_gate_reached!r} but records no "
                f"f9_stress_test_result; A3.5 obligation 19 requires it on "
                f"every case record reaching Gate 8"
            )
        if reached_gate8 and self.f9_stress_test_metric is None:
            raise ValueError(
                f"{self.case_id} records f9_stress_test_result without "
                f"f9_stress_test_metric; obligation 19 requires both"
            )
        # Section 6.0's emission prohibition, enforced by MEMBERSHIP rather than
        # identity, and on the hard gates too -- not only on F9.  The record is
        # the artifact that prohibition is about: it is the one place a
        # forbidden value would survive to disk.
        for rung, result in self.falsification_results.items():
            if result not in _EMITTABLE_RESULTS:
                raise ValueError(
                    f"{getattr(rung, 'value', rung)} carries "
                    f"{getattr(result, 'value', result)!r}; A3.5 section 6.0 "
                    f"permits only PASS or FAIL to be emitted by any rung"
                )
        if has_f9 and self.f9_stress_test_result not in _EMITTABLE_RESULTS:
            raise ValueError(
                f"f9_stress_test_result is "
                f"{getattr(self.f9_stress_test_result, 'value', self.f9_stress_test_result)!r}; "
                f"A3.5 section 6.0 forbids every rung from emitting anything but "
                f"PASS or FAIL, F9 included"
            )
        if not reached_gate8 and has_f9:
            raise ValueError(
                f"{self.case_id} did not reach Gate 8 (stopped at "
                f"{self.acceptance_gate_reached!r}) but records an F9 result; "
                f"F9 is computed only for cases reaching Gate 8"
            )

    # -------------------------------------------------------------------
    @property
    def execution_failure_poisoned(self) -> bool:
        """Whether any of this case's seeds ended in ``EXECUTION_FAILURE``.

        A3.5 section 8.2: one such seed makes the whole case ``UNEVALUABLE``,
        with no replacement seed and no 29/30 denominator.  Obligation 16 then
        requires the poisoned count to be disclosed **separately per endpoint**,
        which is what "makes the conservative rule cost no information".

        Derived from ``per_seed_status`` rather than stored, so it can never
        disagree with the per-seed record it summarises.
        """
        return any(
            entry.status is SeedStatus.EXECUTION_FAILURE
            for entry in self.per_seed_status
        )

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
            "candidate_test_r2": _encode_float(self.candidate_test_r2),
            "falsification_results": {
                # __post_init__ guarantees every hard gate is present when the
                # case reached Gate 8, that nothing else ever is, and that a
                # case which stopped earlier carries none.
                rung.value: self.falsification_results[rung].value
                for rung in HARD_GATE_ORDER
                if rung in self.falsification_results
            },
            "f9_stress_test_result": (
                None if self.f9_stress_test_result is None
                else self.f9_stress_test_result.value
            ),
            "f9_stress_test_metric": (
                None if self.f9_stress_test_metric is None
                else _encode_float(self.f9_stress_test_metric)
            ),
            "f9_acceptance_calibration_status": self.f9_acceptance_calibration_status,
            "execution_failure_poisoned": self.execution_failure_poisoned,
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
