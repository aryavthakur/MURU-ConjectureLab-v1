"""Atomic benchmark artifact construction and SHA-256 verification."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .generator import GeneratedCase, generate_partition
from .registry import CASE_FAMILIES, PARTITIONS


@dataclass(frozen=True)
class BuildReceipt:
    partition: str
    case_count: int
    hashes: dict[str, str]


def _canonical_bytes(record: object) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _write_atomic(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def _case_input_record(generated: GeneratedCase) -> dict[str, object]:
    return {"case_id": generated.case_id, "inputs": generated.inputs.canonical_dict(), "content_hash": generated.content_hash}


def _case_truth_record(generated: GeneratedCase) -> dict[str, object]:
    return {"case_id": generated.case_id, "truth": generated.truth.to_dict(), "content_hash": generated.content_hash}


def _manifest_records(generated_cases: Iterable[GeneratedCase]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    cases, inputs, truths = [], [], []
    for generated in generated_cases:
        case_record = {
            "case_id": generated.case_id,
            "partition": generated.truth.partition,
            "family": generated.truth.family,
            "variant": generated.truth.variant,
            "content_hash": generated.content_hash,
            "applicable_endpoints": generated.truth.applicable_endpoints,
        }
        cases.append(case_record)
        inputs.append(_case_input_record(generated))
        truths.append(_case_truth_record(generated))
    return cases, inputs, truths


def _write_partition_files(partition: str, output_dir: Path, generated_cases: list[GeneratedCase]) -> dict[str, str]:
    cases, inputs, truths = _manifest_records(generated_cases)
    input_payload = b"".join(_canonical_bytes(record) for record in inputs)
    truth_payload = b"".join(_canonical_bytes(record) for record in truths)
    hashes = {
        f"inputs/{partition}.jsonl": _write_atomic(output_dir / "inputs" / f"{partition}.jsonl", input_payload),
        f"truth/{partition}.jsonl": _write_atomic(output_dir / "truth" / f"{partition}.jsonl", truth_payload),
    }
    return hashes


def _write_global_manifests(output_dir: Path, all_cases: list[dict[str, object]], counts: dict[str, int], hashes: dict[str, str]) -> dict[str, str]:
    partition_manifest = {"version": "paper-benchmark-manifest-1.0.0", "partitions": {partition: {"case_count": counts.get(partition, 0)} for partition in PARTITIONS}}
    case_manifest = {"version": "paper-benchmark-case-manifest-1.0.0", "case_count": len(all_cases), "cases": all_cases}
    truth_manifest = {"version": "paper-benchmark-truth-manifest-1.0.0", "case_count": len(all_cases), "truth_paths": {partition: f"truth/{partition}.jsonl" for partition in counts}}
    hashes["paper_benchmark_partition_manifest.json"] = _write_atomic(output_dir / "paper_benchmark_partition_manifest.json", _canonical_bytes(partition_manifest))
    hashes["paper_benchmark_case_manifest.json"] = _write_atomic(output_dir / "paper_benchmark_case_manifest.json", _canonical_bytes(case_manifest))
    hashes["paper_benchmark_truth_manifest.json"] = _write_atomic(output_dir / "paper_benchmark_truth_manifest.json", _canonical_bytes(truth_manifest))
    inventory = {"version": "paper-benchmark-hash-inventory-1.0.0", "hashes": dict(sorted(hashes.items()))}
    hashes["paper_benchmark_hash_inventory.json"] = _write_atomic(output_dir / "paper_benchmark_hash_inventory.json", _canonical_bytes(inventory))
    return hashes


def build_partition(partition: str, output_dir: Path) -> BuildReceipt:
    """Build one partition; Development never requests any other partition."""
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    generated_cases = list(generate_partition(partition))
    hashes = _write_partition_files(partition, output_dir, generated_cases)
    all_cases, _, _ = _manifest_records(generated_cases)
    _write_global_manifests(output_dir, all_cases, {partition: len(generated_cases)}, hashes)
    return BuildReceipt(partition=partition, case_count=len(generated_cases), hashes=verify_hash_inventory(output_dir))


def build_all(output_dir: Path) -> dict[str, BuildReceipt]:
    """Generate all content without loading a generated artifact after writing it."""
    all_cases: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    receipts: dict[str, BuildReceipt] = {}
    for partition in PARTITIONS:
        generated_cases = list(generate_partition(partition))
        hashes.update(_write_partition_files(partition, output_dir, generated_cases))
        case_records, _, _ = _manifest_records(generated_cases)
        all_cases.extend(case_records)
        receipts[partition] = BuildReceipt(partition, len(generated_cases), {})
    _write_global_manifests(output_dir, all_cases, {partition: receipt.case_count for partition, receipt in receipts.items()}, hashes)
    verified = verify_hash_inventory(output_dir)
    return {partition: BuildReceipt(partition, receipt.case_count, verified) for partition, receipt in receipts.items()}


def verify_hash_inventory(output_dir: Path) -> dict[str, str]:
    """Reconstruct hashes from the public inventory without parsing sealed rows."""
    inventory = json.loads((output_dir / "paper_benchmark_hash_inventory.json").read_text())
    verified: dict[str, str] = {}
    for relative, expected in inventory["hashes"].items():
        path = output_dir / relative
        if not path.exists():
            raise ValueError(f"artifact absent: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"artifact hash mismatch: {relative}")
        verified[relative] = actual
    return verified
