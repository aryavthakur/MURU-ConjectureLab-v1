"""Regression checks for the additive A3.4 temporal provenance erratum."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRATUM_PATH = ROOT / "audit/muru_a3_4_temporal_provenance_erratum.json"
ERRATUM_MARKDOWN_PATH = ROOT / "audit/MURU_A3_4_TEMPORAL_PROVENANCE_ERRATUM.md"
A34_SHA = "c699230ab8995461b73a6db2b3fecab661f744e937f40ebe2db34fa8c8c11ada"
A34_COMMIT = "be23b80d63fbd30227f0ab8f200dddc2121f3bfe"
MERGE_COMMIT = "5055f69097aa0c6ce2ded6a3e57f0edfaea69faf"
ERRATUM_TAG = "a3-4-temporal-provenance-erratum"
FIRST_DURABLE_SEED_DEFINITION = (
    "The frozen execution definition is the first non-quarantined PB__NCAL__ "
    "durable seed record, durably written at 2026-08-14T10:08:31-04:00 "
    "(10:08:31 EDT). Preflight, manifest/directory setup, runner-sidecar start, "
    "and the inferred backend.search start interval are provenance stages, not "
    "durable seed records; the record identity may not be reselected from later "
    "outputs."
)
EXACT_EVENT_TIMESTAMPS = {
    "PREFLIGHT_CREATED": "2026-08-13T23:59:01-04:00",
    "CALIBRATION_DIRECTORY_AND_MANIFEST_SETUP": "2026-08-14T10:08:17-04:00",
    "RUNNER_SIDECAR_STARTED": "2026-08-14T10:08:17.932248-04:00",
    "FIRST_NON_QUARANTINED_DURABLE_PB_NCAL_RECORD": "2026-08-14T10:08:31-04:00",
    "A3_4_CREATED": "2026-08-14T11:56:17-04:00",
    "A3_4_FREEZE_COMMIT": "2026-08-14T11:56:23-04:00",
    "A3_4_FREEZE_TAG": "2026-08-14T11:56:26-04:00",
    "RUNNER_FINISHED": "2026-08-14T11:58:40.935600-04:00",
    "TERMINAL_SUMMARY_FILES": "2026-08-14T11:58:41-04:00",
    "A3_4_LINEAGE_MERGED": "2026-08-14T12:27:08-04:00",
}
INFERRED_BACKEND_SEARCH_START_INTERVAL = {
    "strictly_after": "2026-08-14T10:08:17.932248-04:00",
    "strictly_before": "2026-08-14T10:08:31-04:00",
    "epistemic_status": "INFERRED_OPEN_INTERVAL_NOT_AN_EXACT_TIMESTAMP",
    "source": "RUNNER_SIDECAR_STARTED_UTC_AND_FIRST_NON_QUARANTINED_DURABLE_RECORD",
}


def sha256_path(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def read_erratum() -> dict[str, object]:
    assert ERRATUM_PATH.is_file(), "the additive temporal provenance erratum is missing"
    return json.loads(ERRATUM_PATH.read_text(encoding="utf-8"))


def git_output(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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

    frozen_execution = ERRATUM["frozen_execution"]
    assert isinstance(frozen_execution, dict)
    assert frozen_execution == {
        "record_family": "PB__NCAL__",
        "quarantine_status": "NON_QUARANTINED",
        "first_durable_record_timestamp": EXACT_EVENT_TIMESTAMPS[
            "FIRST_NON_QUARANTINED_DURABLE_PB_NCAL_RECORD"
        ],
        "definition": FIRST_DURABLE_SEED_DEFINITION,
    }

    chronology = ERRATUM["chronology"]
    assert isinstance(chronology, dict)
    assert chronology["timezone"] == "EDT (UTC-04:00)"
    assert chronology["merge_commit"] == MERGE_COMMIT
    assert chronology["merge_commit_timestamp"] == "2026-08-14T12:27:08-04:00"
    assert chronology["event_timestamps"] == EXACT_EVENT_TIMESTAMPS
    assert chronology["first_backend_search_start"] == INFERRED_BACKEND_SEARCH_START_INTERVAL
    assert chronology["event_order"] == [
        "PREFLIGHT_CREATED",
        "CALIBRATION_DIRECTORY_AND_MANIFEST_SETUP",
        "RUNNER_SIDECAR_STARTED",
        "FIRST_BACKEND_SEARCH_START_INFERRED_INTERVAL",
        "FIRST_NON_QUARANTINED_DURABLE_PB_NCAL_RECORD",
        "A3_4_CREATED",
        "A3_4_FREEZE_COMMIT",
        "A3_4_FREEZE_TAG",
        "RUNNER_FINISHED",
        "TERMINAL_SUMMARY_FILES",
        "A3_4_LINEAGE_MERGED",
    ]
    for timestamp in chronology["event_timestamps"].values():
        parsed = datetime.fromisoformat(timestamp)
        assert parsed.utcoffset() is not None


def test_erratum_human_record_distinguishes_provenance_stages():
    """The review-facing erratum must expose the full outcome-blind chronology."""
    markdown = ERRATUM_MARKDOWN_PATH.read_text(encoding="utf-8")

    assert FIRST_DURABLE_SEED_DEFINITION in markdown
    assert "PB__NCAL__" in markdown
    assert "non-quarantined" in markdown
    assert "inferred open interval, not an exact timestamp" in markdown
    for timestamp in EXACT_EVENT_TIMESTAMPS.values():
        assert timestamp in markdown
    assert INFERRED_BACKEND_SEARCH_START_INTERVAL["strictly_after"] in markdown
    assert INFERRED_BACKEND_SEARCH_START_INTERVAL["strictly_before"] in markdown


def test_erratum_tag_is_annotated_and_freezes_the_current_erratum_commit():
    """A lightweight tag cannot silently replace the corrected erratum record."""
    assert git_output("cat-file", "-t", ERRATUM_TAG) == "tag"
    assert git_output("rev-parse", f"{ERRATUM_TAG}^{{}}") == git_output(
        "rev-parse", "HEAD"
    )
