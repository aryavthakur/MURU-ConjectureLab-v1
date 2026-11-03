"""Engineering RC5: case-scoped record store, atomic writes, resume.

Three mechanical components, all generalisations of already-frozen patterns:

1. :class:`CaseSeedRecordStore` -- the case-scoped analogue of
   ``rc3_calibration_runner.SeedRecordStore``.  One append-only JSONL file per
   *case* instead of per *world*, holding one record per completed search
   seed, so an interrupted partition resumes without re-executing a finished
   seed.
2. :func:`write_case_record` / :func:`append_provenance` -- atomic case-record
   writes over ``artifacts._write_atomic``'s tmp-then-rename pattern, with the
   scientific record and the non-scientific provenance sidecar kept in
   separate files.
3. :func:`completed_case_ids` / :func:`resume_plan` -- deterministic
   case-scoped resume.

**Append-only is a durability property, not a permission to revise.**  A3.5
section 8.2 forbids any retry that erases or supersedes a prior
``EXECUTION_FAILURE``, and section 12 forbids re-running a case, seed or rung
whose result already exists.  Both are enforced structurally here: a second
record for an already-recorded seed is rejected on load, and a case record is
never overwritten in place.

**Nothing here is scientific.**  This module computes no gate, reads no truth,
and branches on no partition label: ``case_id`` is a filename and a record
key, exactly the two uses A3.5 section 6.0 permits.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .calibration_contract import SeedStatus
from .rc3_calibration_runner import FROZEN_SETTINGS_DIGEST
from .rc3_record import (
    RECORD_SCHEMA_VERSION,
    CaseExecutionRecord,
    PerSeedStatusEntry,
    ProvenanceSidecar,
    canonical_json,
    record_schema_generation,
)

__all__ = [
    "CaseRecordExists",
    "SchemaGenerationRefused",
    "StoredSeedOutcome",
    "CaseSeedRecordStore",
    "case_slug",
    "write_atomic",
    "write_case_record",
    "append_provenance",
    "load_case_record_payload",
    "completed_case_ids",
    "ResumePlan",
    "resume_plan",
]

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def case_slug(case_id: str) -> str:
    """Filesystem-safe, collision-free rendering of a case ID.

    ``PB|development|F01|r000`` -> ``PB_development_F01_r000``.  Injective over
    the frozen 380-case enumeration because the registry's IDs differ only in
    characters this mapping preserves.
    """
    return _UNSAFE.sub("_", case_id)


def write_atomic(path: Path, payload: bytes) -> str:
    """Write bytes via tmp-then-rename and return their SHA-256.

    Same mechanism as ``artifacts._write_atomic``: a reader never observes a
    partially written file, because ``Path.replace`` is atomic within a
    filesystem.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


class CaseRecordExists(RuntimeError):
    """A completed case record is already on disk and must not be rewritten."""


class SchemaGenerationRefused(RuntimeError):
    """A record on disk is not of the current schema generation."""


@dataclass(frozen=True)
class StoredSeedOutcome:
    """One recorded seed, complete enough to resume from without recomputing.

    The record carries the retained candidate's **own decided values** --
    complexity, ``valid_r2`` and ``invalid_fraction`` -- not merely its
    expression string.  Without them a resumed run would have to recompute a
    number the original run already decided, which is the very thing A3.5
    sections 8.2 and 12 forbid.  They are absent exactly when the seed retained
    nothing.
    """

    entry: PerSeedStatusEntry
    complexity: int | None = None
    valid_r2: float | None = None
    invalid_fraction: float | None = None

    @property
    def retained(self) -> bool:
        return self.entry.status is SeedStatus.COMPLETED_WITH_CANDIDATES


# -----------------------------------------------------------------------
# Per-seed store, case-scoped
# -----------------------------------------------------------------------

class CaseSeedRecordStore:
    """Append-only per-seed record store, one JSONL file per case.

    ``settings_digest`` is the digest this store EXPECTS; what a record is
    stamped with is supplied per-append by the caller from the backend that
    actually ran, so a record cannot claim settings it did not run under.
    ``case_content_hash`` plays the same role ``world_construction_digest``
    plays for calibration: a record produced against different case content is
    refused rather than adopted.

    Resume is **seed-granular**: :meth:`load` returns enough to rebuild each
    recorded seed's outcome exactly, so an interruption partway through a case
    never re-executes a finished seed and never lets a fresh result supersede a
    recorded ``EXECUTION_FAILURE``.
    """

    def __init__(
        self,
        root: Path,
        settings_digest: str = FROZEN_SETTINGS_DIGEST,
        plan_digest: str = "",
    ):
        self.root = Path(root)
        self.settings_digest = settings_digest
        self.plan_digest = plan_digest
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, case_id: str) -> Path:
        return self.root / f"{case_slug(case_id)}.jsonl"

    def recorded_seeds(self, case_id: str) -> frozenset[int]:
        """Seed values already present in this case's file, cheaply.

        Read without the full verification :meth:`load` performs, because
        :meth:`append` needs it on every write and a malformed line must not be
        able to make a duplicate look absent.
        """
        path = self.path_for(case_id)
        if not path.exists():
            return frozenset()
        seeds: set[int] = set()
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                seeds.add(int(json.loads(raw)["seed"]))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
        return frozenset(seeds)

    def append(
        self,
        case_id: str,
        entry: PerSeedStatusEntry,
        case_content_hash: str,
        settings_digest: str | None = None,
        complexity: int | None = None,
        valid_r2: float | None = None,
        invalid_fraction: float | None = None,
    ) -> None:
        # Refuse the duplicate HERE, not only on load.  A guard that fires only
        # on read lets the writer commit the violation and continue, and once
        # written the file becomes unreadable by its only reader -- so even an
        # auditor cannot enumerate the seed history without destroying
        # evidence.  A seed is decided once (A3.5 sections 8.2, 12).
        if int(entry.seed) in self.recorded_seeds(case_id):
            raise RuntimeError(
                f"seed {entry.seed} already has a record for {case_id}; records "
                f"are append-only and a seed is decided once - a second record "
                f"would be a selective retry that supersedes a prior result"
            )
        payload = {
            "case_id": case_id,
            "seed": int(entry.seed),
            "status": entry.status.value,
            "selected_expression_string": entry.selected_expression_string,
            "error_message": entry.error_message,
            "search_settings_digest": (
                self.settings_digest if settings_digest is None else settings_digest
            ),
            "case_content_hash": case_content_hash,
            "global_plan_digest": self.plan_digest,
            "complexity": None if complexity is None else int(complexity),
            "valid_r2": None if valid_r2 is None else float(valid_r2),
            "invalid_fraction": (
                None if invalid_fraction is None else float(invalid_fraction)
            ),
        }
        if entry.status is SeedStatus.COMPLETED_WITH_CANDIDATES and (
            complexity is None or valid_r2 is None or invalid_fraction is None
        ):
            raise ValueError(
                f"seed {entry.seed} retained a candidate but its decided values "
                f"were not supplied; a record that cannot be resumed from without "
                f"recomputation is not a usable record"
            )
        line = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        with self.path_for(case_id).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()

    def load(
        self,
        case_id: str,
        case_content_hash: str | None = None,
    ) -> dict[int, StoredSeedOutcome]:
        """Load completed seeds for a case.

        A truncated final line (an interrupted write) is discarded, so a
        half-written record can never be mistaken for a completed seed.
        Everything else is verified rather than trusted; any mismatch raises
        and none is repaired.
        """
        path = self.path_for(case_id)
        if not path.exists():
            return {}
        results: dict[int, PerSeedStatusEntry] = {}
        lines = path.read_text(encoding="utf-8").splitlines()
        last_index = len(lines) - 1
        for index, raw in enumerate(lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                if index == last_index:
                    continue  # a genuinely truncated final line, mid-write
                # Anywhere else, a corrupt line is evidence being lost: it
                # could be hiding a recorded EXECUTION_FAILURE that a later
                # clean record would then appear to supersede.
                raise RuntimeError(
                    f"{path} line {index + 1} of {len(lines)} is unparseable and "
                    f"is not the final line; a corrupt interior record must not "
                    f"be silently dropped"
                ) from None
            recorded_case = payload.get("case_id")
            if recorded_case != case_id:
                raise RuntimeError(
                    f"{path} contains a record for {recorded_case!r} but was read "
                    f"as {case_id!r}; a renamed or copied record file must not be "
                    f"adopted as another case's completed seeds"
                )
            recorded_settings = payload.get("search_settings_digest")
            if recorded_settings != self.settings_digest:
                raise RuntimeError(
                    f"{path} seed {payload.get('seed')} was produced under search "
                    f"settings {recorded_settings} but this store expects "
                    f"{self.settings_digest}; a record produced under different "
                    f"settings must not be adopted"
                )
            if self.plan_digest:
                recorded_plan = payload.get("global_plan_digest")
                if recorded_plan != self.plan_digest:
                    raise RuntimeError(
                        f"{path} seed {payload.get('seed')} was produced under "
                        f"global science plan {recorded_plan!r}, but this run's "
                        f"plan is {self.plan_digest!r}"
                    )
            if case_content_hash is not None:
                recorded_content = payload.get("case_content_hash")
                if recorded_content != case_content_hash:
                    raise RuntimeError(
                        f"{path} seed {payload.get('seed')} was produced on case "
                        f"content {recorded_content!r}, but this case's content "
                        f"hash is {case_content_hash!r}; the inputs differ, so the "
                        f"recorded result must not be adopted"
                    )
            seed = int(payload["seed"])
            if seed in results:
                raise RuntimeError(
                    f"{path} contains a duplicate record for seed {seed}; records "
                    f"are append-only and a seed is decided once - a second record "
                    f"would be a selective retry"
                )
            results[seed] = StoredSeedOutcome(
                entry=PerSeedStatusEntry(
                    seed=seed,
                    status=SeedStatus(payload["status"]),
                    selected_expression_string=payload.get(
                        "selected_expression_string"
                    ),
                    error_message=payload.get("error_message", ""),
                ),
                complexity=payload.get("complexity"),
                valid_r2=payload.get("valid_r2"),
                invalid_fraction=payload.get("invalid_fraction"),
            )
        return results


# -----------------------------------------------------------------------
# Case-record atomic write, provenance append
# -----------------------------------------------------------------------

def _record_path(out_dir: Path, case_id: str) -> Path:
    return Path(out_dir) / "records" / f"{case_slug(case_id)}.json"


def _provenance_path(out_dir: Path) -> Path:
    return Path(out_dir) / "provenance" / "case_provenance.jsonl"


def write_case_record(
    record: CaseExecutionRecord,
    out_dir: Path,
    overwrite: bool = False,
) -> str:
    """Write one case's scientific record atomically; return its digest.

    Refuses to rewrite an existing record unless ``overwrite=True``, which the
    RC5 runner never passes: re-running a case whose result already exists is
    forbidden by A3.5 section 12, and silently overwriting is exactly how that
    prohibition would be violated by accident.
    """
    path = _record_path(out_dir, record.case_id)
    if path.exists() and not overwrite:
        raise CaseRecordExists(
            f"{path} already exists; re-running a case whose result already "
            f"exists is forbidden (A3.5 section 12). Resume skips completed cases."
        )
    payload = record.to_canonical_json().encode("utf-8")
    write_atomic(path, payload)
    return record.scientific_digest()


def append_provenance(sidecar: ProvenanceSidecar, out_dir: Path) -> None:
    """Append one case's non-scientific provenance.

    A3.5 section 8.4: post-execution provenance is a **separate, append-only**
    record.  It lives in its own file and is never merged into the scientific
    record or into the pre-execution manifest.
    """
    path = _provenance_path(out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(sidecar.to_json() + "\n")
        handle.flush()


def load_case_record_payload(out_dir: Path, case_id: str) -> Mapping[str, object]:
    """Read back one case's scientific payload, refusing any other generation.

    A3.5's schema bump is only meaningful if something enforces it.  A
    ``muru-rc3-case-record-1.0.0`` payload carries a six-rung
    ``falsification_results`` mapping scored under the superseded Gate 8 --
    where F5 gated, F9 gated, and ``NOT_APPLICABLE`` fell through to passing --
    so reading one as current-generation would adopt a verdict the amended
    rules never produced.
    """
    payload = json.loads(_record_path(out_dir, case_id).read_text(encoding="utf-8"))
    generation = record_schema_generation(payload)
    if generation != "current":
        raise SchemaGenerationRefused(
            f"{_record_path(out_dir, case_id)} is a {generation} record "
            f"({payload.get('schema_version')!r}); the current generation is "
            f"{RECORD_SCHEMA_VERSION!r}. The two are not interchangeable and an "
            f"old record is never reinterpreted as a new one."
        )
    return payload


def completed_case_ids(out_dir: Path) -> frozenset[str]:
    """Case IDs whose **current-generation** scientific record is on disk.

    A record of any other generation raises rather than counting as complete:
    counting it would make the resume contract skip that case permanently, so
    its superseded verdict would stand and never be re-executed under the
    amended rules.
    """
    root = Path(out_dir) / "records"
    if not root.exists():
        return frozenset()
    found: set[str] = set()
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        generation = record_schema_generation(payload)
        if generation != "current":
            raise SchemaGenerationRefused(
                f"{path} is a {generation} record "
                f"({payload.get('schema_version')!r}); it must not be counted as "
                f"a completed case under {RECORD_SCHEMA_VERSION!r}"
            )
        found.add(str(payload["case_id"]))
    return frozenset(found)


@dataclass(frozen=True)
class ResumePlan:
    """What a resumed run will and will not execute."""

    requested: tuple[str, ...]
    already_complete: tuple[str, ...]
    to_execute: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "requested": list(self.requested),
            "already_complete": list(self.already_complete),
            "to_execute": list(self.to_execute),
        }


def resume_plan(out_dir: Path, case_ids: Sequence[str]) -> ResumePlan:
    """Deterministic case-scoped resume.

    Order is the caller's (the frozen manifest's) order, never filesystem
    order, so two resumes of the same interrupted run execute the same cases in
    the same sequence.
    """
    done = completed_case_ids(out_dir)
    requested = tuple(case_ids)
    return ResumePlan(
        requested=requested,
        already_complete=tuple(c for c in requested if c in done),
        to_execute=tuple(c for c in requested if c not in done),
    )


def payload_digest(payload: Mapping[str, object]) -> str:
    """SHA-256 over the pinned canonical JSON serialisation."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
