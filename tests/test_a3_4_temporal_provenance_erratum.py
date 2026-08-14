"""Regression checks for the additive A3.4 temporal provenance erratum."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRATUM_PATH = ROOT / "audit/muru_a3_4_temporal_provenance_erratum.json"
ERRATUM_MARKDOWN_PATH = ROOT / "audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md"
A34_SHA = "c699230ab8995461b73a6db2b3fecab661f744e937f40ebe2db34fa8c8c11ada"
A34_COMMIT = "be23b80d63fbd30227f0ab8f200dddc2121f3bfe"
MERGE_COMMIT = "5055f69097aa0c6ce2ded6a3e57f0edfaea69faf"
FIRST_DURABLE_SEED_DEFINITION = (
    "The first durable seed is the first seed record persisted in version control "
    "before any outcome inspection; its identity is frozen at that commit and may "
    "not be reselected from later outputs."
)


def sha256_path(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def read_erratum() -> dict[str, object]:
    assert ERRATUM_PATH.is_file(), "the additive temporal provenance erratum is missing"
    return json.loads(ERRATUM_PATH.read_text(encoding="utf-8"))


def test_erratum_is_additive_and_leaves_a34_bytes_unchanged():
    """Changing the frozen A3.4 source or replacing the erratum breaks the audit."""
    ERRATUM = read_erratum()

    assert ERRATUM_MARKDOWN_PATH.is_file(), "the human-readable erratum is missing"
    assert ERRATUM["classification"] == "TEMPORAL_PROVENANCE_ERRATUM_REQUIRED_OUTCOME_BLIND"
    assert sha256_path("MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md") == A34_SHA
    assert ERRATUM["a3_4_source_commit"] == A34_COMMIT
    assert ERRATUM["a3_4_document_sha256"] == A34_SHA
    assert ERRATUM["scientific_change"] == "NONE"
    assert ERRATUM["outcome_inspection"] == "NONE"
    assert ERRATUM["frozen_first_durable_seed_definition"] == FIRST_DURABLE_SEED_DEFINITION

    chronology = ERRATUM["chronology"]
    assert isinstance(chronology, dict)
    assert chronology["date"] == "2026-08-14"
    assert chronology["timezone"] == "EDT (UTC-04:00)"
    assert chronology["a3_4_commit_timestamp"] == "2026-08-14T11:56:23-04:00"
    assert chronology["merge_commit"] == MERGE_COMMIT
    assert chronology["merge_commit_timestamp"] == "2026-08-14T12:27:08-04:00"
    assert chronology["event_order"] == [
        "A3_4_FROZEN",
        "A3_4_LINEAGE_MERGED",
    ]
    for timestamp in chronology["event_timestamps"].values():
        parsed = datetime.fromisoformat(timestamp)
        assert parsed.date().isoformat() == chronology["date"]
        assert parsed.utcoffset() is not None
