"""The preserved A3.2 calibration evidence, and the guard that now admits it.

Engineering only.  These tests read the calibration evidence as data: they
verify its identity and reconstruct its published aggregate.  Nothing here
touches Development, Held-out, Challenge or Confirmation, and nothing
re-executes, refits or alters the calibration.

pb_34's calibration check was written when the calibration had not run and
treated any record store as a breach.  The calibration has since been executed
once and audited VALID, so the check was redirected to "is every record here
part of the one authorized run".  These tests exist so that redirection is not
a quiet weakening: they prove the guard still refuses a foreign store and a
tampered manifest.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "calibration" / "a3_2"

MANIFEST_SHA256 = "9950b964346581d104bf3069c992eec2599c88235f6598b2aed1bb31ac58fe0f"
MAX_COMPLEXITY = 20

pytestmark = pytest.mark.skipif(
    not CALIBRATION.exists(),
    reason="A3.2 calibration evidence is not present on this branch",
)


def _pb_34():
    spec = importlib.util.spec_from_file_location(
        "pb_34_rc3_integrity_under_test",
        ROOT / "scripts" / "pb_34_rc3_integrity.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_execution_manifest_canonicalizes_to_the_governance_digest():
    manifest = json.loads((CALIBRATION / "execution_manifest.json").read_text())
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == MANIFEST_SHA256


def test_the_threshold_table_is_bound_to_that_manifest_and_valid():
    table = json.loads((CALIBRATION / "threshold_table.json").read_text())
    assert table["execution_manifest_sha256"] == MANIFEST_SHA256
    assert table["validity"] == "VALID"
    assert sorted(int(c) for c in table["thresholds"]) == list(
        range(1, MAX_COMPLEXITY + 1)
    )


def test_the_manifest_records_the_dependency_lock_this_closure_adopted():
    """The repository evidence that the 50-pin lock is not a version choice."""
    manifest = json.loads((CALIBRATION / "execution_manifest.json").read_text())
    assert manifest["dependency_lock_commit"] == (
        "c7c23324d40cd432bdd14bf9d3292b5a2867ef9e"
    )
    assert manifest["dependency_lock_sha256"] == hashlib.sha256(
        (ROOT / "requirements.lock.txt").read_bytes()
    ).hexdigest()
    assert manifest["python_version"] == "3.13.12"


def test_the_raw_records_are_complete_and_undisturbed():
    files = sorted((CALIBRATION / "seed_records").glob("*.jsonl"))
    assert len(files) == 100
    total = 0
    statuses: dict[str, int] = {}
    for path in files:
        seeds = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            assert record["seed"] not in seeds, "duplicate seed"
            seeds.add(record["seed"])
            statuses[record["status"]] = statuses.get(record["status"], 0) + 1
            total += 1
        assert len(seeds) == 30
    assert total == 3000
    assert statuses == {"COMPLETED_WITH_CANDIDATES": 3000}


def test_the_frozen_threshold_table_reconstructs_from_the_raw_records():
    """Independent of the frozen contract code, straight from the amendment.

    S(w,c) = max over seeds of the prefix-max validation R2; Q95 across worlds
    per complexity by numpy.quantile linear; maximum.accumulate over c.
    """
    def parse(value):
        if isinstance(value, str):
            return {"NaN": math.nan, "Infinity": math.inf,
                    "-Infinity": -math.inf}[value]
        return float(value)

    statistics: dict[str, dict[int, float]] = {}
    for path in sorted((CALIBRATION / "seed_records").glob("*.jsonl")):
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        world_id = records[0]["world_id"]
        if any(r["status"] == "EXECUTION_FAILURE" for r in records):
            statistics[world_id] = {c: 1.0 for c in range(1, MAX_COMPLEXITY + 1)}
            continue
        row = {c: -math.inf for c in range(1, MAX_COMPLEXITY + 1)}
        for record in records:
            curve = record.get("best_valid_r2_by_complexity")
            values = (
                {} if curve is None
                else {int(k): parse(v) for k, v in curve.items()}
            )
            running = -math.inf
            for complexity in range(1, MAX_COMPLEXITY + 1):
                running = max(running, values.get(complexity, -math.inf))
                row[complexity] = max(row[complexity], running)
        statistics[world_id] = row

    assert len(statistics) == 100
    per_complexity = [
        float(np.quantile(
            np.array([statistics[w][c] for w in sorted(statistics)], dtype=float),
            0.95, method="linear",
        ))
        for c in range(1, MAX_COMPLEXITY + 1)
    ]
    accumulated = np.maximum.accumulate(per_complexity)
    reconstructed = {
        str(c): float(accumulated[c - 1]) for c in range(1, MAX_COMPLEXITY + 1)
    }

    frozen = json.loads((CALIBRATION / "threshold_table.json").read_text())
    assert reconstructed == frozen["thresholds"]


def test_the_guard_admits_the_authorized_store():
    module = _pb_34()
    status, errors = module.check_calibration_execution_status()
    assert errors == []
    assert status == "EXECUTED (AUTHORIZED A3.2, VERIFIED)"


def test_the_guard_still_refuses_a_store_outside_the_authorized_directory(
    monkeypatch, tmp_path
):
    """Redirecting the check must not have made it blind."""
    module = _pb_34()
    monkeypatch.setattr(module, "AUTHORIZED_CALIBRATION_DIR", "calibration/somewhere_else")
    status, errors = module.check_calibration_execution_status()
    assert any(e.startswith("UNAUTHORIZED_CALIBRATION_RECORDS") for e in errors)
    assert status == "EXECUTED"


def test_the_guard_refuses_a_tampered_execution_manifest(monkeypatch):
    module = _pb_34()
    monkeypatch.setattr(
        module, "AUTHORIZED_CALIBRATION_MANIFEST_SHA256", "0" * 64
    )
    _, errors = module.check_calibration_execution_status()
    assert any(e.startswith("CALIBRATION_MANIFEST_DIGEST") for e in errors)


def test_the_guard_refuses_a_short_store(monkeypatch):
    module = _pb_34()
    monkeypatch.setattr(module, "AUTHORIZED_CALIBRATION_RECORDS", 3001)
    monkeypatch.setattr(module, "AUTHORIZED_CALIBRATION_WORLDS", 101)
    _, errors = module.check_calibration_execution_status()
    assert any(e.startswith("CALIBRATION_RECORD_COUNT") for e in errors)
    assert any(e.startswith("CALIBRATION_WORLD_COUNT") for e in errors)
