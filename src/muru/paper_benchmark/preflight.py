"""Development-only cost measurement with a hard held-out quarantine."""
from __future__ import annotations

import json
import resource
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .governance import ImplementationLock


@dataclass(frozen=True)
class PreflightReport:
    partition: str
    case_count: int
    wall_seconds: float
    cpu_seconds: float
    peak_rss_kb: int
    artifact_bytes: int
    engine_status: str
    engine_failures: int
    candidate_count: int
    held_out_accessed: bool
    complete: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_preflight(artifact_dir: Path, lock: ImplementationLock) -> PreflightReport:
    """Measure only development artifact size and parse cost; never open held-out."""
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    input_path = artifact_dir / "inputs" / "development.jsonl"
    if not input_path.exists():
        raise ValueError("development inputs are required for preflight")
    lines = input_path.read_bytes().splitlines()
    case_count = len(lines)
    if case_count != 80:
        raise ValueError(f"expected 80 development cases, found {case_count}")
    # Validate line framing only. This rejects accidental corrupted content without
    # reading a held-out artifact or interpreting development scientific outcomes.
    for line in lines:
        if "case_id" not in json.loads(line):
            raise ValueError("development input record is malformed")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    pending = lock.status == "PENDING_LOCK"
    return PreflightReport(
        partition="development",
        case_count=case_count,
        wall_seconds=time.perf_counter() - start_wall,
        cpu_seconds=time.process_time() - start_cpu,
        peak_rss_kb=int(usage.ru_maxrss),
        artifact_bytes=input_path.stat().st_size,
        engine_status="not_run_pending_lock" if pending else "ready_for_locked_engine_preflight",
        engine_failures=0,
        candidate_count=0,
        held_out_accessed=False,
        complete=not pending,
    )
