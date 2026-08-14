"""Regression checks for the MURU RC4 A3.4 engineering freeze record."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE_JSON_PATH = ROOT / "audit/muru_rc4_a3_4_engineering_freeze.json"
FREEZE_MD_PATH = ROOT / "audit/MURU_RC4_A3_4_ENGINEERING_FREEZE.md"

RC3_1_PARENT_COMMIT = "07c64c862cb32a306f5081582dacf73e09211c0a"
A34_SCIENCE_FREEZE_COMMIT = "be23b80d63fbd30227f0ab8f200dddc2121f3bfe"
A34_MERGE_COMMIT = "5055f69097aa0c6ce2ded6a3e57f0edfaea69faf"
TEMPORAL_ERRATUM_COMMIT = "220c9cb679e03865f1b2a02b975397de9f4c7b46"
REFERENCE_AGGREGATE_DIGEST = (
    "4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44"
)
RECORDED_PROTECTED_AGGREGATE = (
    "d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8"
)
TERMINAL_NEWLINE_PROTECTED_AGGREGATE = (
    "55ebd0b92ba07ad828983f4e7add5163f49377255dfcf47bdd9f1af98174f16a"
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_engineering_freeze_ledger_bindings():
    assert FREEZE_JSON_PATH.is_file()
    assert FREEZE_MD_PATH.is_file()

    payload = json.loads(FREEZE_JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)

    canonical = payload["canonical_freeze"]
    assert canonical["classification"] == "ENGINEERING_RELEASE_CANDIDATE_FREEZE"
    assert canonical["status"] == "FROZEN_VALID"
    assert canonical["tag"] == "engineering-rc4-a3-4"

    provenance = canonical["provenance_bindings"]
    assert provenance["rc3_1_parent_commit"] == RC3_1_PARENT_COMMIT
    assert provenance["a3_4_science_freeze_commit"] == A34_SCIENCE_FREEZE_COMMIT
    assert provenance["a3_4_merge_commit"] == A34_MERGE_COMMIT
    assert provenance["temporal_provenance_erratum_commit"] == TEMPORAL_ERRATUM_COMMIT

    digests = canonical["digests"]
    assert digests["reference_distribution_aggregate_sha256"] == REFERENCE_AGGREGATE_DIGEST
    assert digests["protected_paths_count"] == 31
    assert (
        digests["protected_paths_recorded_aggregate_sha256"]
        == RECORDED_PROTECTED_AGGREGATE
    )
    assert (
        digests["protected_paths_terminal_newline_aggregate_sha256"]
        == TERMINAL_NEWLINE_PROTECTED_AGGREGATE
    )

    canonical_bytes = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert sha256_bytes(canonical_bytes) == payload["canonical_binding"]["content_sha256"]

    md_content = FREEZE_MD_PATH.read_bytes()
    assert (
        sha256_bytes(md_content)
        == canonical["human_readable_projection"]["sha256"]
    )
