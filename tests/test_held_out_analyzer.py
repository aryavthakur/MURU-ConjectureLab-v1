"""Unit tests for the frozen Held-out primary analyzer and independent recomputation on synthetic fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from muru.paper_benchmark.held_out_analyzer import (
    MetricInterval,
    analyze_held_out_records,
)
from muru.paper_benchmark.independent_recomputation import (
    compare_analysis_reports,
    recompute_held_out_metrics,
)
from muru.paper_benchmark.post_execution_sealer import (
    verify_held_out_completeness,
    write_execution_seal_receipt,
)
from muru.paper_benchmark.rc3_record import canonical_json
from muru.paper_benchmark.rc5_manifest import manifest_digest
from muru.paper_benchmark.rc5_seeds import case_search_seeds
from muru.paper_benchmark.rc5_store import case_slug


@pytest.fixture
def synthetic_held_out_fixture(tmp_path: Path) -> tuple[Path, list[str]]:
    root = tmp_path / "synthetic_run"
    records_dir = root / "records"
    seed_records_dir = root / "seed_records"
    records_dir.mkdir(parents=True)
    seed_records_dir.mkdir(parents=True)

    cases = [
        "PB|held_out|F01|r000",
        "PB|held_out|F01|r001",
        "PB|held_out|F02|r000",
        "PB|held_out|F02|r001",
    ]

    manifest_payload = {
        "schema_version": "muru-rc5-partition-execution-manifest-1.0.0",
        "science": {"case_ids": cases},
        "run": {"run_commit": "8d87143d4280602323aa33ee0b5481aaef0fb4a8"},
    }
    manifest_payload["digest"] = manifest_digest(manifest_payload)
    (root / "execution_manifest.json").write_text(canonical_json(manifest_payload), encoding="utf-8")

    for i, case_id in enumerate(cases):
        slug = case_slug(case_id)
        # Give case 0 and 2 full passes, case 1 G1 only, case 3 failure
        case_rec = {
            "schema_version": "muru-rc3-case-record-1.0.0",
            "case_id": case_id,
            "adequate": (i != 3),
            "status": "COMPLETED" if i != 3 else "EXECUTION_FAILURE",
            "g1_wilson_lower": 0.85 if i != 3 else 0.40,
            "g2_recovered": (i in (0, 2)),
            "g3_event": "CONJECTURE_CONFIRMED" if (i in (0, 2)) else "INCONCLUSIVE",
            "gate7_pass": (i != 3),
            "gate8_pass": (i != 3),
            "f9_pass": (i == 0),
            "stability_score": 0.95 if i != 3 else 0.10,
        }
        (records_dir / f"{slug}.json").write_text(canonical_json(case_rec), encoding="utf-8")

        seeds = list(case_search_seeds(case_id))
        lines = [json.dumps({"seed": s, "status": "COMPLETED"}) for s in seeds]
        (seed_records_dir / f"{slug}.jsonl").write_text("\n".join(lines) + "\n")

    report = verify_held_out_completeness(root, expected_case_ids=cases)
    write_execution_seal_receipt(root, report, run_commit="8d87143d4280602323aa33ee0b5481aaef0fb4a8")

    return root, cases


def test_primary_analysis_and_independent_recomputation(synthetic_held_out_fixture):
    root, cases = synthetic_held_out_fixture

    primary = analyze_held_out_records(root, expected_case_ids=cases)
    assert primary.total_cases == 4
    assert primary.g1.successes == 3
    assert primary.g2.successes == 2
    assert primary.g3.successes == 2
    assert primary.gate7.successes == 3
    assert primary.gate8.successes == 3
    assert primary.poisoned_cases == 1
    assert primary.decision_passed is True

    independent = recompute_held_out_metrics(root, expected_case_ids=cases)
    assert independent.case_count == 4
    assert independent.g1_interval.k == 3
    assert independent.g2_interval.k == 2
    assert independent.g3_interval.k == 2
    assert independent.gate7_interval.k == 3
    assert independent.gate8_interval.k == 3
    assert independent.unevaluable_count == 1
    assert independent.benchmark_pass is True

    comparison = compare_analysis_reports(primary, independent)
    assert comparison.is_identical
    comparison.assert_identical()
