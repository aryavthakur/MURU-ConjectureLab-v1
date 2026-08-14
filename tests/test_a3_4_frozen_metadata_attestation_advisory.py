"""Regression checks for the additive A3.4 frozen-metadata advisory."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADVISORY_JSON = ROOT / "audit/muru_a3_4_frozen_metadata_attestation_advisory.json"
ADVISORY_MARKDOWN = ROOT / "audit/MURU_A3_4_FROZEN_METADATA_ATTESTATION_ADVISORY.md"

A34_FREEZE_COMMIT = "be23b80d63fbd30227f0ab8f200dddc2121f3bfe"
A34_CREATION_COMMIT = "d0ea5d4b0309e4e95dcab4035b9be66e166765b1"
A34_FREEZE_TAG = "benchmark-content-freeze-a3-4"
A34_FREEZE_TAG_OBJECT = "326727d5f17943b22f014262dcf42f5cf043ba42"
A33_TAG = "benchmark-content-freeze-a3-3"
A33_TAG_OBJECT = "363e1c5a64cdf235712900fc2a14409fa6ec3e1e"
FROZEN_PARENT_LITERAL = "71f53697e8894df6469ad0ff7150a049fa531b74"
ACTUAL_A33_COMMIT = "71f5369c8aa9e5c47f951bd894d744af70956616"

A34_DOCUMENT_PATH = "MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md"
A34_ARTIFACT_PATH = "artifacts/paper_benchmark_amendment_a3_4.json"
A34_DOCUMENT_SHA256 = "c699230ab8995461b73a6db2b3fecab661f744e937f40ebe2db34fa8c8c11ada"
A34_REFERENCE_DIGEST = "4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44"
RECORDED_PROTECTED_AGGREGATE = (
    "d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8"
)
STANDARD_PROTECTED_AGGREGATE = (
    "55ebd0b92ba07ad828983f4e7add5163f49377255dfcf47bdd9f1af98174f16a"
)


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def git_bytes(revision: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ("git", "show", f"{revision}:{relative_path}"),
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return result.stdout


def git_text(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def frozen_a34_artifact() -> dict[str, Any]:
    artifact = json.loads(git_bytes(A34_FREEZE_COMMIT, A34_ARTIFACT_PATH))
    assert isinstance(artifact, dict)
    return artifact


def read_advisory() -> dict[str, Any]:
    assert ADVISORY_JSON.is_file(), "the additive frozen-metadata advisory is missing"
    ledger = json.loads(ADVISORY_JSON.read_text(encoding="utf-8"))
    assert isinstance(ledger, dict)
    return ledger


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def test_advisory_is_canonically_bound_additive_and_outcome_blind():
    """Unbound advisory content or a science amendment must be rejected."""
    ledger = read_advisory()

    assert ADVISORY_MARKDOWN.is_file(), "the human-readable advisory is missing"
    assert set(ledger) == {"canonical_attestation", "canonical_binding"}

    attestation = ledger["canonical_attestation"]
    binding = ledger["canonical_binding"]
    assert isinstance(attestation, dict)
    assert binding == {
        "algorithm": "SHA-256",
        "canonicalization": (
            "UTF-8 JSON; recursive lexicographic object-key ordering; compact "
            "separators ',' and ':'; ensure_ascii=false; allow_nan=false; no "
            "trailing newline"
        ),
        "content_pointer": "/canonical_attestation",
        "content_sha256": sha256(canonical_json_bytes(attestation)),
    }
    assert attestation["schema_version"] == (
        "muru-a3-4-frozen-metadata-attestation-advisory-1.0.0"
    )
    assert attestation["classification"] == (
        "IMMUTABLE_HISTORICAL_PROVENANCE_ATTESTATION_DISCREPANCY"
    )
    assert attestation["status"] == (
        "IMMUTABLE_HISTORICAL_PROVENANCE_ATTESTATION_DISCREPANCY"
    )
    assert attestation["scope"] == "ADDITIVE_OUTCOME_BLIND_ADVISORY_NOT_A_SCIENCE_AMENDMENT"
    assert attestation["scientific_change"] == "NONE"
    assert attestation["outcome_inspection"] == "NONE"
    assert attestation["scientific_amendment"] is False
    assert attestation["frozen_content_changed"] is False

    projection = attestation["human_readable_projection"]
    assert projection == {
        "path": "audit/MURU_A3_4_FROZEN_METADATA_ATTESTATION_ADVISORY.md",
        "sha256": sha256(ADVISORY_MARKDOWN.read_bytes()),
    }
    markdown = ADVISORY_MARKDOWN.read_text(encoding="utf-8")
    assert "immutable historical provenance-attestation discrepancy" in markdown
    assert "not a science amendment" in markdown
    assert "outcome-blind" in markdown


def test_advisory_attests_the_parent_literal_against_frozen_git_provenance():
    """A different parent literal or tag/parent relationship must fail the attestation."""
    ledger = read_advisory()
    attestation = ledger["canonical_attestation"]
    assert isinstance(attestation, dict)
    finding = attestation["findings"]["parent_a3_3_commit"]

    artifact = frozen_a34_artifact()
    frozen_markdown = git_bytes(A34_FREEZE_COMMIT, A34_DOCUMENT_PATH).decode("utf-8")
    assert artifact["parent_a3_3_commit"] == FROZEN_PARENT_LITERAL
    assert FROZEN_PARENT_LITERAL in frozen_markdown

    nonobject = subprocess.run(
        ("git", "cat-file", "-e", f"{FROZEN_PARENT_LITERAL}^{{commit}}"),
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    assert nonobject.returncode != 0
    assert git_text("cat-file", "-t", A33_TAG) == "tag"
    assert git_text("rev-parse", A33_TAG) == A33_TAG_OBJECT
    assert git_text("rev-parse", f"{A33_TAG}^{{}}") == ACTUAL_A33_COMMIT
    assert git_text("rev-parse", f"{A34_CREATION_COMMIT}^") == ACTUAL_A33_COMMIT

    assert finding == {
        "a3_4_creation_commit": A34_CREATION_COMMIT,
        "a3_4_creation_commit_git_parent": ACTUAL_A33_COMMIT,
        "actual_a3_3_tag": {
            "name": A33_TAG,
            "tag_object": A33_TAG_OBJECT,
            "target_commit": ACTUAL_A33_COMMIT,
        },
        "frozen_locations": [A34_DOCUMENT_PATH, A34_ARTIFACT_PATH],
        "frozen_recorded_literal": FROZEN_PARENT_LITERAL,
        "git_commit_object_check": {
            "algorithm": "git cat-file -e <literal>^{commit}",
            "literal_resolves_to_commit": False,
        },
    }


def test_advisory_attests_all_frozen_path_hashes_and_the_aggregate_difference():
    """Missing per-path validation, hash drift, or a changed digest algorithm must fail."""
    ledger = read_advisory()
    attestation = ledger["canonical_attestation"]
    assert isinstance(attestation, dict)
    finding = attestation["findings"]["protected_path_digest"]

    artifact = frozen_a34_artifact()
    protected_paths = artifact["protected_paths"]
    protected_sha256 = artifact["protected_sha256"]
    assert isinstance(protected_paths, list)
    assert isinstance(protected_sha256, dict)
    assert artifact["protected_path_count"] == 31
    assert len(protected_paths) == 31
    assert len(set(protected_paths)) == 31
    assert set(protected_paths) == set(protected_sha256)

    for relative_path in protected_paths:
        frozen = git_bytes(A34_FREEZE_COMMIT, relative_path)
        assert sha256(frozen) == protected_sha256[relative_path]
        assert (ROOT / relative_path).read_bytes() == frozen

    frozen_document = git_bytes(A34_FREEZE_COMMIT, A34_DOCUMENT_PATH)
    frozen_artifact = git_bytes(A34_FREEZE_COMMIT, A34_ARTIFACT_PATH)
    assert sha256(frozen_document) == A34_DOCUMENT_SHA256
    assert (ROOT / A34_DOCUMENT_PATH).read_bytes() == frozen_document
    assert (ROOT / A34_ARTIFACT_PATH).read_bytes() == frozen_artifact

    standard_payload = "".join(
        f"{relative_path}:{protected_sha256[relative_path]}\n"
        for relative_path in sorted(protected_sha256)
    ).encode("utf-8")
    no_terminal_newline_payload = "\n".join(
        f"{relative_path}:{protected_sha256[relative_path]}"
        for relative_path in sorted(protected_sha256)
    ).encode("utf-8")
    assert artifact["protected_path_digest"] == RECORDED_PROTECTED_AGGREGATE
    assert sha256(standard_payload) == STANDARD_PROTECTED_AGGREGATE
    assert sha256(no_terminal_newline_payload) == RECORDED_PROTECTED_AGGREGATE

    assert finding == {
        "a3_4_freeze_commit": A34_FREEZE_COMMIT,
        "all_31_individual_sha256_entries_validate_at_freeze": True,
        "protected_path_count": 31,
        "recorded_aggregate_sha256": RECORDED_PROTECTED_AGGREGATE,
        "recorded_value_matches_no_terminal_newline_variant": True,
        "standard_path_sha256_newline_algorithm": {
            "digest": "SHA-256",
            "encoding": "UTF-8",
            "entry_format": "{relative_path}:{sha256}\\n",
            "ordering": "LEXICOGRAPHIC_ASCENDING_RELATIVE_PATH",
            "terminal_newline": True,
        },
        "standard_recomputed_aggregate_sha256": STANDARD_PROTECTED_AGGREGATE,
    }
    assert attestation["frozen_a3_4"] == {
        "artifact_path": A34_ARTIFACT_PATH,
        "creation_commit": A34_CREATION_COMMIT,
        "document_path": A34_DOCUMENT_PATH,
        "document_sha256": A34_DOCUMENT_SHA256,
        "freeze_commit": A34_FREEZE_COMMIT,
        "freeze_tag": {
            "name": A34_FREEZE_TAG,
            "tag_object": A34_FREEZE_TAG_OBJECT,
            "target_commit": A34_FREEZE_COMMIT,
        },
        "reference_covariates_sha256": A34_REFERENCE_DIGEST,
    }
    assert attestation["scientific_impact"] == {
        "a3_4_scientific_definitions_changed": False,
        "a3_4_reference_digest_changed": False,
        "frozen_content_changed": False,
        "reference_covariates_sha256": A34_REFERENCE_DIGEST,
    }
