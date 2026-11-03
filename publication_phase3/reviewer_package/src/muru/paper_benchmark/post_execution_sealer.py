"""Post-execution sealing and tamper verification for MURU benchmark partitions.

Implements immutable sealing, 240-case / 7,200-seed inventory verification,
duplicate detection, raw record schema checks, canonical SHA-256 hashing,
and strict analysis boundary guards.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .rc3_record import canonical_json
from .rc5_manifest import manifest_digest, verify_partition_manifest
from .rc5_seeds import case_search_seeds
from .rc5_store import case_slug
from .registry import iter_case_ids

SEAL_RECEIPT_SCHEMA_VERSION = "muru-rc5-execution-seal-receipt-1.0.0"


class SealingError(RuntimeError):
    """Raised when post-execution sealing or integrity verification fails."""


@dataclass(frozen=True)
class CompletenessReport:
    """Detailed verification report for a benchmark partition's raw records."""

    partition: str
    expected_case_count: int
    found_case_records: int
    found_seed_record_files: int
    total_seeds_recorded: int
    expected_seeds_total: int
    is_complete: bool
    missing_cases: list[str] = field(default_factory=list)
    corrupt_records: list[str] = field(default_factory=list)
    duplicate_seeds: list[str] = field(default_factory=list)
    unexpected_cases: list[str] = field(default_factory=list)
    manifest_digest: str = ""

    def assert_valid(self) -> None:
        if not self.is_complete:
            raise SealingError(
                f"Partition {self.partition} is incomplete: "
                f"{self.found_case_records}/{self.expected_case_count} cases, "
                f"{self.total_seeds_recorded}/{self.expected_seeds_total} seeds. "
                f"Missing: {self.missing_cases[:5]}"
            )
        if self.corrupt_records:
            raise SealingError(f"Corrupt records found: {self.corrupt_records}")
        if self.duplicate_seeds:
            raise SealingError(f"Duplicate seeds found: {self.duplicate_seeds}")
        if self.unexpected_cases:
            raise SealingError(f"Unexpected cases found: {self.unexpected_cases}")


def verify_held_out_completeness(
    results_root: Path,
    expected_case_ids: Sequence[str] | None = None,
) -> CompletenessReport:
    """Verify all 240 case records and 7,200 seed records for Held-out partition."""
    results_root = Path(results_root)
    records_dir = results_root / "records"
    seed_records_dir = results_root / "seed_records"
    manifest_file = results_root / "execution_manifest.json"

    if not manifest_file.exists():
        raise SealingError(f"Execution manifest missing at {manifest_file}")

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    m_digest = manifest_digest(manifest_data)
    if manifest_data.get("digest") != m_digest:
        raise SealingError(
            f"Manifest digest mismatch: recorded {manifest_data.get('digest')}, computed {m_digest}"
        )

    if expected_case_ids is None:
        expected_case_ids = list(iter_case_ids("held_out"))
    expected_set = set(expected_case_ids)

    missing_cases: list[str] = []
    corrupt_records: list[str] = []
    duplicate_seeds: list[str] = []
    seen_seeds: set[int] = set()

    found_cases = 0
    found_seed_files = 0
    total_seeds = 0

    for case_id in expected_case_ids:
        slug = case_slug(case_id)
        case_path = records_dir / f"{slug}.json"
        seed_path = seed_records_dir / f"{slug}.jsonl"

        if not case_path.exists():
            missing_cases.append(case_id)
            continue
        found_cases += 1

        try:
            case_data = json.loads(case_path.read_text(encoding="utf-8"))
            if case_data.get("case_id") != case_id:
                corrupt_records.append(f"{case_path.name}: case_id mismatch")
        except Exception as exc:
            corrupt_records.append(f"{case_path.name}: json decode error {exc}")

        if not seed_path.exists():
            missing_cases.append(f"{case_id} (seed record)")
            continue
        found_seed_files += 1

        expected_seeds = list(case_search_seeds(case_id))
        case_seeds_found: list[int] = []

        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    seed_val = entry.get("seed")
                    if seed_val is None:
                        corrupt_records.append(f"{seed_path.name}: entry missing seed")
                        continue
                    if seed_val in seen_seeds:
                        duplicate_seeds.append(f"Global duplicate seed {seed_val} in {case_id}")
                    if seed_val in case_seeds_found:
                        duplicate_seeds.append(f"Case duplicate seed {seed_val} in {case_id}")
                    seen_seeds.add(seed_val)
                    case_seeds_found.append(seed_val)
                    total_seeds += 1

            if sorted(case_seeds_found) != sorted(expected_seeds):
                corrupt_records.append(
                    f"{seed_path.name}: seeds do not match derived seeds for {case_id}"
                )
        except Exception as exc:
            corrupt_records.append(f"{seed_path.name}: jsonl error {exc}")

    # Check for unexpected files
    unexpected_cases: list[str] = []
    if records_dir.exists():
        for path in records_dir.glob("*.json"):
            slug = path.stem
            # Verify slug corresponds to an expected case
            matched = any(case_slug(c) == slug for c in expected_case_ids)
            if not matched:
                unexpected_cases.append(str(path.name))

    expected_count = len(expected_case_ids)
    expected_total_seeds = expected_count * 30
    is_complete = (
        found_cases == expected_count
        and found_seed_files == expected_count
        and total_seeds == expected_total_seeds
        and not missing_cases
    )

    return CompletenessReport(
        partition="held_out",
        expected_case_count=expected_count,
        found_case_records=found_cases,
        found_seed_record_files=found_seed_files,
        total_seeds_recorded=total_seeds,
        expected_seeds_total=expected_total_seeds,
        is_complete=is_complete,
        missing_cases=missing_cases,
        corrupt_records=corrupt_records,
        duplicate_seeds=duplicate_seeds,
        unexpected_cases=unexpected_cases,
        manifest_digest=m_digest,
    )


def build_canonical_hash_inventory(results_root: Path) -> dict[str, str]:
    """Compute canonical SHA-256 digest for every file in the partition result."""
    results_root = Path(results_root)
    inventory: dict[str, str] = {}

    for path in sorted(results_root.rglob("*")):
        if path.is_file() and not path.name.endswith(".tmp") and path.name != "execution_seal_receipt.json":
            rel_path = str(path.relative_to(results_root))
            raw_bytes = path.read_bytes()
            inventory[rel_path] = hashlib.sha256(raw_bytes).hexdigest()

    return inventory


def write_execution_seal_receipt(
    results_root: Path,
    report: CompletenessReport,
    run_commit: str,
    sealed_by: str = "MURU-PostExecution-Sealer-v1",
) -> dict[str, Any]:
    """Write an immutable seal receipt asserting the partition raw execution is complete and sealed."""
    report.assert_valid()
    results_root = Path(results_root)
    receipt_path = results_root / "execution_seal_receipt.json"
    if receipt_path.exists():
        raise SealingError(f"Seal receipt already exists at {receipt_path}; never overwrite")

    file_hashes = build_canonical_hash_inventory(results_root)

    payload = {
        "schema_version": SEAL_RECEIPT_SCHEMA_VERSION,
        "sealed": True,
        "partition": report.partition,
        "sealed_by": sealed_by,
        "run_commit": run_commit,
        "manifest_digest": report.manifest_digest,
        "case_count": report.found_case_records,
        "seed_count": report.total_seeds_recorded,
        "file_count": len(file_hashes),
        "file_hashes": file_hashes,
        "declaration": "CURRENT-CONTRACT HELD-OUT RAW EXECUTION SEALED",
    }

    raw_str = canonical_json(payload)
    payload_digest = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
    payload["receipt_digest"] = payload_digest

    receipt_path.write_text(canonical_json(payload), encoding="utf-8")
    return payload


def verify_sealed_integrity(results_root: Path) -> bool:
    """Verify that all files match the hashes recorded in the seal receipt."""
    results_root = Path(results_root)
    receipt_path = results_root / "execution_seal_receipt.json"
    if not receipt_path.exists():
        return False

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    recorded_hashes: dict[str, str] = receipt.get("file_hashes", {})

    for rel_path, expected_hash in recorded_hashes.items():
        file_path = results_root / rel_path
        if not file_path.exists():
            raise SealingError(f"Sealed file missing: {rel_path}")
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise SealingError(
                f"Tamper detected in {rel_path}: recorded {expected_hash}, actual {actual_hash}"
            )

    return True


def guard_analysis_boundary(results_root: Path) -> None:
    """Hard boundary guard: analysis must NEVER run on an unsealed or modified run."""
    results_root = Path(results_root)
    receipt_path = results_root / "execution_seal_receipt.json"
    if not receipt_path.exists():
        raise SealingError(
            "ANALYSIS BOUNDARY VIOLATION: Cannot analyze unsealed raw execution. "
            "Raw execution must be verified and sealed first."
        )
    if not verify_sealed_integrity(results_root):
        raise SealingError(
            "ANALYSIS BOUNDARY VIOLATION: Seal integrity check failed."
        )
