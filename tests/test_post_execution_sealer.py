"""Unit tests for post-execution sealing, completeness, duplicate detection, and boundary guards."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from muru.paper_benchmark.post_execution_sealer import (
    SealingError,
    build_canonical_hash_inventory,
    guard_analysis_boundary,
    verify_held_out_completeness,
    verify_sealed_integrity,
    write_execution_seal_receipt,
)
from muru.paper_benchmark.rc3_record import canonical_json
from muru.paper_benchmark.rc5_manifest import manifest_digest
from muru.paper_benchmark.rc5_seeds import case_search_seeds
from muru.paper_benchmark.rc5_store import case_slug


@pytest.fixture
def mock_results_dir(tmp_path: Path) -> Path:
    """Create a fully valid mock 2-case partition directory with manifest and records."""
    root = tmp_path / "mock_held_out"
    records_dir = root / "records"
    seed_records_dir = root / "seed_records"
    records_dir.mkdir(parents=True)
    seed_records_dir.mkdir(parents=True)

    cases = ["PB|held_out|F01|r000", "PB|held_out|F01|r001"]

    # Create valid manifest
    manifest_payload = {
        "schema_version": "muru-rc5-partition-execution-manifest-1.0.0",
        "science": {"case_ids": cases},
        "run": {"run_commit": "8d87143d4280602323aa33ee0b5481aaef0fb4a8"},
    }
    manifest_payload["digest"] = manifest_digest(manifest_payload)
    (root / "execution_manifest.json").write_text(canonical_json(manifest_payload), encoding="utf-8")

    # Create valid case records & seed records
    for case_id in cases:
        slug = case_slug(case_id)
        case_rec = {
            "schema_version": "muru-rc3-case-record-1.0.0",
            "case_id": case_id,
            "adequate": True,
            "g1_wilson_lower": 0.85,
            "g2_recovered": True,
            "g3_event": "CONJECTURE_CONFIRMED",
            "gate7_pass": True,
            "gate8_pass": True,
        }
        (records_dir / f"{slug}.json").write_text(canonical_json(case_rec), encoding="utf-8")

        seeds = list(case_search_seeds(case_id))
        lines = []
        for s in seeds:
            lines.append(json.dumps({"seed": s, "status": "COMPLETED", "score": 0.1}))
        (seed_records_dir / f"{slug}.jsonl").write_text("\n".join(lines) + "\n")

    return root


def test_completeness_and_sealing_happy_path(mock_results_dir: Path):
    cases = ["PB|held_out|F01|r000", "PB|held_out|F01|r001"]
    report = verify_held_out_completeness(mock_results_dir, expected_case_ids=cases)
    assert report.is_complete
    assert report.found_case_records == 2
    assert report.found_seed_record_files == 2
    assert report.total_seeds_recorded == 60
    assert len(report.missing_cases) == 0
    assert len(report.duplicate_seeds) == 0

    # Guard should fail before sealing
    with pytest.raises(SealingError, match="Cannot analyze unsealed"):
        guard_analysis_boundary(mock_results_dir)

    # Seal execution
    receipt = write_execution_seal_receipt(
        mock_results_dir,
        report,
        run_commit="8d87143d4280602323aa33ee0b5481aaef0fb4a8",
    )
    assert receipt["sealed"] is True
    assert receipt["declaration"] == "CURRENT-CONTRACT HELD-OUT RAW EXECUTION SEALED"

    # Guard should pass after sealing
    guard_analysis_boundary(mock_results_dir)
    assert verify_sealed_integrity(mock_results_dir) is True


def test_tamper_detection_after_sealing(mock_results_dir: Path):
    cases = ["PB|held_out|F01|r000", "PB|held_out|F01|r001"]
    report = verify_held_out_completeness(mock_results_dir, expected_case_ids=cases)
    write_execution_seal_receipt(mock_results_dir, report, run_commit="8d87143d")

    # Tamper with a file
    case_path = mock_results_dir / "records" / f"{case_slug(cases[0])}.json"
    case_path.write_bytes(b'{"tampered": true}')

    with pytest.raises(SealingError, match="Tamper detected"):
        guard_analysis_boundary(mock_results_dir)


def test_duplicate_seed_detection(mock_results_dir: Path):
    cases = ["PB|held_out|F01|r000", "PB|held_out|F01|r001"]
    # Append duplicate seed in first file
    seed_path = mock_results_dir / "seed_records" / f"{case_slug(cases[0])}.jsonl"
    first_seed = list(case_search_seeds(cases[0]))[0]
    with open(seed_path, "a") as f:
        f.write(json.dumps({"seed": first_seed, "status": "COMPLETED"}) + "\n")

    report = verify_held_out_completeness(mock_results_dir, expected_case_ids=cases)
    assert len(report.duplicate_seeds) > 0
    with pytest.raises(SealingError):
        report.assert_valid()
