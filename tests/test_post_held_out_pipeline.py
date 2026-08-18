"""End-to-end integration test for the post-Held-out pipeline on synthetic fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from muru.paper_benchmark.rc3_record import canonical_json
from muru.paper_benchmark.rc5_manifest import manifest_digest
from muru.paper_benchmark.rc5_seeds import case_search_seeds
from muru.paper_benchmark.rc5_store import case_slug
from muru.paper_benchmark.pipeline import run_post_held_out_pipeline


@pytest.fixture
def full_synthetic_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_run"
    records_dir = root / "records"
    seed_records_dir = root / "seed_records"
    records_dir.mkdir(parents=True)
    seed_records_dir.mkdir(parents=True)

    from muru.paper_benchmark.registry import iter_case_ids

    cases = list(iter_case_ids("held_out"))

    manifest_payload = {
        "schema_version": "muru-rc5-partition-execution-manifest-1.0.0",
        "science": {
            "case_ids": cases,
            "calibration_manifest_digest": "9950b964346581d104bf3069c992eec2599c88235f6598b2aed1bb31ac58fe0f",
        },
        "run": {
            "run_commit": "8d87143d4280602323aa33ee0b5481aaef0fb4a8",
            "environment": {
                "environment_lock_digest": "13b21b8ca409b82d1ef8d94aa5e487e2523d5264807f04fc1e65a5553c357fa8",
            },
        },
    }
    manifest_payload["digest"] = manifest_digest(manifest_payload)
    (root / "execution_manifest.json").write_text(canonical_json(manifest_payload), encoding="utf-8")

    for i, case_id in enumerate(cases):
        slug = case_slug(case_id)
        case_rec = {
            "schema_version": "muru-rc3-case-record-1.0.0",
            "case_id": case_id,
            "adequate": True,
            "status": "COMPLETED",
            "g1_wilson_lower": 0.88,
            "g2_recovered": (i % 2 == 0),
            "g3_event": "CONJECTURE_CONFIRMED" if (i % 2 == 0) else "INCONCLUSIVE",
            "gate7_pass": True,
            "gate8_pass": True,
            "f9_pass": True,
            "stability_score": 0.95,
        }
        (records_dir / f"{slug}.json").write_text(canonical_json(case_rec), encoding="utf-8")

        seeds = list(case_search_seeds(case_id))
        lines = [json.dumps({"seed": s, "status": "COMPLETED"}) for s in seeds]
        (seed_records_dir / f"{slug}.jsonl").write_text("\n".join(lines) + "\n")

    return root


def test_full_post_held_out_pipeline_on_synthetic_data(full_synthetic_fixture: Path):
    manifest_data = json.loads((full_synthetic_fixture / "execution_manifest.json").read_text())
    m_digest = manifest_data["digest"]
    res = run_post_held_out_pipeline(full_synthetic_fixture, expected_manifest_digest=m_digest)
    assert res["sealed"] is True
    assert res["primary_analysis"]["total_cases"] == 240
    assert res["primary_analysis"]["g1"]["successes"] == 240
    assert res["primary_analysis"]["g2"]["successes"] == 120
    assert res["hostile_audit_passed"] is True

    # Assert artifacts created
    assert (full_synthetic_fixture / "execution_seal_receipt.json").exists()
    assert (full_synthetic_fixture / "held_out_formal_analysis.json").exists()
    assert (full_synthetic_fixture / "held_out_hostile_audit_report.md").exists()
