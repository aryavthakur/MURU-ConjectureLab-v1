"""Development-only cost measurement with a hard held-out quarantine.

RC5 generalisation (engineering only, no scientific behaviour changed).
``run_preflight`` was hard-wired to ``inputs/development.jsonl`` and to a
literal case count of 80.  RC5's production runner needs the same measurement
for whichever partition it is authorised to execute, so the partition is now a
parameter that **defaults to** ``"development"`` and the expected case count is
read from the frozen registry instead of being restated as a literal.

Nothing scientific moves:

* the default call ``run_preflight(dir, lock)`` measures exactly what it
  measured before, against exactly the same expected count (the registry
  computes 80 for development), and returns the same field values;
* the check performed is still line framing plus the presence of ``case_id``
  -- no scientific outcome is interpreted, for any partition;
* ``held_out_accessed`` now reports the truth rather than a constant, so a
  report can never claim held-out was untouched while naming it.

Authorisation to run a partition at all is **not** this module's job and is
deliberately not added here: it belongs to
``governance.assert_held_out_execution_allowed`` and to the RC5 runner, which
refuses every partition A3.5 section 14.2 does not authorise.
"""
from __future__ import annotations

import json
import platform
import resource
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .governance import ImplementationLock
from .registry import PARTITIONS, iter_case_ids

#: The frozen per-partition case population, computed from the registry.
#: development 80, held_out 240, challenge 60.
PARTITION_EXPECTED_CASES: dict[str, int] = {
    partition: len(list(iter_case_ids(partition))) for partition in PARTITIONS
}

DEFAULT_PREFLIGHT_PARTITION = "development"


@dataclass(frozen=True)
class PreflightReport:
    partition: str
    case_count: int
    wall_seconds: float
    cpu_seconds: float
    peak_rss_bytes: int
    artifact_bytes: int
    engine_status: str
    engine_failures: int
    candidate_count: int
    held_out_accessed: bool
    complete: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_preflight(
    artifact_dir: Path,
    lock: ImplementationLock,
    partition: str = DEFAULT_PREFLIGHT_PARTITION,
) -> PreflightReport:
    """Measure one partition's artifact size and parse cost.

    Only line framing and the presence of ``case_id`` are validated.  No
    scientific outcome is interpreted and no truth artifact is opened, for any
    partition.
    """
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    expected = PARTITION_EXPECTED_CASES[partition]

    start_wall, start_cpu = time.perf_counter(), time.process_time()
    input_path = artifact_dir / "inputs" / f"{partition}.jsonl"
    if not input_path.exists():
        raise ValueError(f"{partition} inputs are required for preflight")
    lines = input_path.read_bytes().splitlines()
    case_count = len(lines)
    if case_count != expected:
        raise ValueError(f"expected {expected} {partition} cases, found {case_count}")
    # Validate line framing only. This rejects accidental corrupted content without
    # reading a held-out artifact or interpreting development scientific outcomes.
    for line in lines:
        if "case_id" not in json.loads(line):
            raise ValueError(f"{partition} input record is malformed")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss_bytes = int(usage.ru_maxrss)
    if platform.system() != "Darwin":
        peak_rss_bytes *= 1024
    pending = lock.status == "PENDING_LOCK"
    return PreflightReport(
        partition=partition,
        case_count=case_count,
        wall_seconds=time.perf_counter() - start_wall,
        cpu_seconds=time.process_time() - start_cpu,
        peak_rss_bytes=peak_rss_bytes,
        artifact_bytes=input_path.stat().st_size,
        engine_status="not_run_pending_lock" if pending else "ready_for_locked_engine_preflight",
        engine_failures=0,
        candidate_count=0,
        held_out_accessed=(partition == "held_out"),
        complete=not pending,
    )
