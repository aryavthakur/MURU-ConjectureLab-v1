"""Amendment A2.1 integrity tests: the GENERATOR_VERSION bump is metadata-only.

Amendment A2 changed the F16 generator's scientific behavior while leaving
`GENERATOR_VERSION` at `1.0.0`. A2.1 bumps the version and proves the bump
changes nothing scientific: every one of the 380 cases' `content_hash` moves
(the version string is part of its hash pre-image), but every case's actual
payload -- covariates, scaffolds, partitions, seeds, energies, generated
responses, and truth values -- is byte-identical to Amendment A2.

No Development or Held-out scientific outcome is scored, summarised, or
inspected here. Content hashing and whole-object equality are mechanical.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.paper_benchmark.generator import GENERATOR_VERSION, generate_case, scientific_payload_hash  # noqa: E402

ARTIFACTS = ROOT / "artifacts"
SCRIPT = ROOT / "scripts" / "pb_32_amendment_a2_1_integrity.py"
AMENDMENT_A2_FREEZE = "03cc4d3"

#: content_hash values under GENERATOR_VERSION = 1.1.0 (A2.1), for the same
#: case sample already used for the version-independent payload pins in
#: `test_paper_benchmark_amendment_a2_integrity.py`.
CONTENT_HASHES_A2_1 = {
    "PB|development|F01|r000": "065b251a2f9d0c0e04328fcebcb5f6397361ec56a072228434b3285d51a531be",
    "PB|development|F13|r000": "6e238fe050dd46d81cb49ce3bde8e63cd2e3bf354646c6e0963aedf890293586",
    "PB|development|F14|r000": "2bf3cf180cf832f6d5d8f5abb86eb75340b24ca8c68acecc852c7159dfbe3ed7",
    "PB|development|F15|r000": "9d4f9f8617326ea64e38ef6b3f6e6a5605971d042f4936d08fb0feb0d252c1ed",
    "PB|held_out|F06|r005": "a6e40cbb2165193bb3fa83c208dc32566627e4a0a982892742fc19dfe165a3b0",
    "PB|held_out|F07|r003": "57b11996bc7410f15303565d25dacabe9040a0e563340b282ddcc31d13d6c512",
    "PB|held_out|F15|r011": "1e6a04dd23939b60c86cc84869bf1939a59b0489d32f5f39b31bac1ecf478730",
    "PB|held_out|F19|r008": "b60113c223b03ed07ffdf660b984ef992f2d6ef83e69e89ed3e6e87eaf9d4942",
    "PB|challenge|F20|r002": "3d3a3c008f5d274abe0578cc202d1b528fad6e89c861cb3dce2de510833b7cca",
    "PB|development|F16|r000": "8e594ea658c71a3cfedb0d12c0a237ce677499bbc18c7c18f8299755e93bb531",
    "PB|development|F16|r003": "9772c35a9820c805f597ce7c82c24c8018da27c431e5fbcd485d918ea8f1f9b0",
    "PB|held_out|F16|r000": "911d3d07ee065596220d23ec0c46cc29e5216a3f8cdf375932323570a752694f",
    "PB|held_out|F16|r011": "1205837e907fcb43ef434c82d7927dabf729d7013bc9c774a72da52549503205",
    "PB|challenge|F16|r002": "6df63970e4acc1c33939a03c6bd377552ae7506bd0ad70ef8fc37e666582ca0e",
}


def _git_available() -> bool:
    probe = subprocess.run(["git", "cat-file", "-e", f"{AMENDMENT_A2_FREEZE}^{{commit}}"], cwd=ROOT, capture_output=True)
    return probe.returncode == 0


pytestmark = pytest.mark.skipif(not _git_available(), reason="amendment A2 freeze 03cc4d3 is not reachable")


def _run(tmp_path: Path) -> tuple[subprocess.CompletedProcess, dict]:
    output = tmp_path / "paper_benchmark_amendment_a2_1.json"
    process = subprocess.run(["python3", str(SCRIPT), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
    payload = json.loads(output.read_text()) if output.exists() else {}
    return process, payload


# --------------------------------------------------------------------------
# 1-2: generator version changed; truth schema version unchanged
# --------------------------------------------------------------------------


def test_generator_version_bumped_to_1_1_0():
    assert GENERATOR_VERSION == "paper-benchmark-generator-1.1.0"


def test_truth_schema_version_unchanged_because_the_schema_is_unchanged():
    """`truth_version` names the `TruthRecord` field set, not generator
    behavior. A2.1 does not touch a single field on `TruthRecord`, so it stays
    at its A1/A2 value."""
    truth = generate_case("PB|development|F01|r000").truth
    assert truth.truth_version == "paper-benchmark-truth-1.0.0"


# --------------------------------------------------------------------------
# 3: 361 non-F16 and 19 F16 scientific payloads are unchanged relative to A2
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case_id", sorted(k for k in CONTENT_HASHES_A2_1 if not k.split("|")[2] == "F16"))
def test_non_f16_content_hash_matches_the_shipped_a2_1_artifact(case_id):
    assert generate_case(case_id).content_hash == CONTENT_HASHES_A2_1[case_id]


@pytest.mark.parametrize("case_id", sorted(k for k in CONTENT_HASHES_A2_1 if k.split("|")[2] == "F16"))
def test_f16_content_hash_matches_the_shipped_a2_1_artifact(case_id):
    assert generate_case(case_id).content_hash == CONTENT_HASHES_A2_1[case_id]


@pytest.mark.parametrize("case_id", sorted(CONTENT_HASHES_A2_1))
def test_content_hash_and_payload_hash_are_genuinely_different_quantities(case_id):
    """`content_hash` moved (asserted above) precisely because it includes
    `GENERATOR_VERSION`; the payload-only hash it is built from did not -- it
    is the same value pinned in `test_paper_benchmark_amendment_a2_integrity.py`
    as `NON_F16_PAYLOAD_HASHES` / `F16_PAYLOAD_HASHES` for this case sample."""
    generated = generate_case(case_id)
    payload_hash = scientific_payload_hash(generated.inputs, generated.truth, generator_version=None)
    versioned_hash = scientific_payload_hash(generated.inputs, generated.truth, generator_version=GENERATOR_VERSION)

    assert versioned_hash == generated.content_hash == CONTENT_HASHES_A2_1[case_id]
    assert payload_hash != generated.content_hash


def test_the_repair_running_script_proves_zero_payload_changes_across_all_380_cases(tmp_path):
    process, manifest = _run(tmp_path)

    assert process.returncode == 0, process.stdout + process.stderr
    rows = manifest["generated_row_comparison"]
    assert rows["case_records_total"] == 380
    assert rows["case_records_payload_changed"] == 0
    assert rows["case_records_content_hash_changed"] == 380
    for stream in rows["row_streams"].values():
        assert stream["payload_changed"] == 0


# --------------------------------------------------------------------------
# General integrity: only the declared version-bump paths differ from A2
# --------------------------------------------------------------------------


def test_only_declared_version_bump_paths_differ_from_amendment_a2(tmp_path):
    process, manifest = _run(tmp_path)

    assert process.returncode == 0, process.stdout + process.stderr
    assert manifest["amendment_a2_freeze"] == AMENDMENT_A2_FREEZE
    assert manifest["old_generator_version"] == "paper-benchmark-generator-1.0.0"
    assert manifest["new_generator_version"] == "paper-benchmark-generator-1.1.0"
    assert manifest["generator_version_bumped"] is True
    assert manifest["unexpected_changed_paths"] == []
    assert manifest["removed_paths"] == []
    assert manifest["scientific_change"] == "NONE"
    assert manifest["integrity_verified"] is True


# --------------------------------------------------------------------------
# 6-9: everything A2.1 must not touch
# --------------------------------------------------------------------------


def test_a1_adequacy_constants_are_unchanged():
    from muru.paper_benchmark import adequacy

    assert adequacy.MU_FLOOR == 1e-4
    assert adequacy.MU_CEIL == 1 - 1e-4
    assert adequacy.MIN_VERTICAL_AMPLITUDE == 0.05
    assert set(adequacy.ADEQUACY_MODELS) == {"M0", "M1", "M2", "M3"}


def test_a2_f16_constants_are_unchanged():
    from muru.paper_benchmark.generator import (
        COMBINED_M1_AMPLITUDE,
        COMBINED_M2_AMPLITUDE,
        COMBINED_M3_AMPLITUDE,
        COMBINED_M3_ATTENUATION_DENOMINATOR,
        COMBINED_M3_ATTENUATION_NUMERATOR,
        M3_CEILING_CLIP,
    )

    assert COMBINED_M1_AMPLITUDE == 0.15
    assert COMBINED_M2_AMPLITUDE == 0.05
    assert COMBINED_M3_ATTENUATION_NUMERATOR == 5
    assert COMBINED_M3_ATTENUATION_DENOMINATOR == 18
    assert COMBINED_M3_AMPLITUDE == 11 / 180
    assert M3_CEILING_CLIP == (0.6, 0.99)


def test_m1_m2_m3_denominators_are_unchanged():
    from muru.paper_benchmark.analysis import endpoint_denominator

    assert endpoint_denominator("m1_sensitivity") == 36
    assert endpoint_denominator("m2_sensitivity") == 24
    assert endpoint_denominator("m3_sensitivity") == 24
    assert endpoint_denominator("m0_specificity") == 164


def test_case_counts_and_population_are_unchanged():
    from muru.paper_benchmark.registry import CASE_FAMILIES, PARTITION_CASE_COUNTS, ROOT_SEED

    assert len(CASE_FAMILIES) == 20
    assert ROOT_SEED == 20260813
    f16 = next(family for family in CASE_FAMILIES if family.code == "F16")
    assert f16.partition_counts == PARTITION_CASE_COUNTS == {"development": 4, "held_out": 12, "challenge": 3}


def test_held_out_remains_unexecuted():
    freeze = json.loads((ARTIFACTS / "paper_benchmark_content_freeze.json").read_text())

    assert freeze["status"] == "WAITING_FOR_LOCKED_IMPLEMENTATION"
    assert freeze["final_executable_freeze"] is False
