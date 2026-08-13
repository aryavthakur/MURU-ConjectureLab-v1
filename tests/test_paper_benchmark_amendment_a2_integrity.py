"""Amendment A2 integrity tests: what the F16 repair was not allowed to touch.

Every hash below is a byte-level pin.  The non-F16 pins are the values frozen at
Amendment A1 (`2ac86c5`) and must survive the repair unchanged; the F16 pins are
the post-repair values and lock the repaired generator against silent drift.

No Development or Held-out scientific outcome is scored, summarised, or
inspected here.  Content hashing is mechanical.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from muru.paper_benchmark import adequacy
from muru.paper_benchmark.analysis import endpoint_denominator, umbrella_decision
from muru.paper_benchmark.generator import generate_case, scientific_payload_hash
from muru.paper_benchmark.registry import (
    CASE_FAMILIES,
    ENERGY_GRID,
    PARTITION_CASE_COUNTS,
    PARTITIONS,
    ROOT_SEED,
    iter_case_ids,
)

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

#: Amendment A1 scientific payload (covariates, scaffolds, partitions, seeds,
#: energies, generated responses, truth), excluding `generator_version`. Pinned
#: this way rather than as full `content_hash` values so the pin survives a
#: future version-metadata-only bump (Amendment A2.1 is the first one) without
#: drifting for a reason unrelated to what this test certifies: that A2 left
#: every non-F16 case's science untouched.
NON_F16_PAYLOAD_HASHES = {
    "PB|development|F01|r000": "661e965f6e32517443089744ffb93a2a922655495b6144d3959c63eead409905",
    "PB|development|F13|r000": "cba1226a743615c79108d7a906ed07cf7d242cbe6aeba03d5bc5736d74f81bc6",
    "PB|development|F14|r000": "40ae529c00ef051d4fe90b95fed7404fc70b3c0f3f7727589508272eabd6a6d7",
    "PB|development|F15|r000": "ca5957d98da298e3e154fcfa9d54339dde73d5bfab9d42b3b06b40d077c5c29f",
    "PB|held_out|F06|r005": "4d1515f5d503b90d2b1fb9b6fd9e7fce5f3294a02f8c1c96bfa09ff49551af7f",
    "PB|held_out|F07|r003": "6292c418c0decf3f6ab67439daa0f75e6ca93c42c4ce67dfc67c01df9c7c5125",
    "PB|held_out|F15|r011": "3d59ead75ddd6254e8326f80c0a3cdf031311379e8e87f50a133288d076973b7",
    "PB|held_out|F19|r008": "b24bd8b9ec5b9389476e0bbc13ac988e6b2c1df2f6b806d3d58e4971d79ab527",
    "PB|challenge|F20|r002": "c6bbf51853c1206fec7584ecb631fb36a53767d04d2dc7433de7186bd6df735b",
}

#: Post-repair F16 scientific payload, same construction.
F16_PAYLOAD_HASHES = {
    "PB|development|F16|r000": "50c36bd36682e68ec8c30b184b1397d8afb2f14abf0abaa7a5b4ca90d61bbeec",
    "PB|development|F16|r003": "d539ad6f38a6726906a394b63dd709325978d865287b9e0f213af7670cbd719e",
    "PB|held_out|F16|r000": "789b44e932aaf68e851dac2ec2d90ffbd021b88a0d9c1a4fee43879b5b367688",
    "PB|held_out|F16|r011": "c85af13359e676d9497cb5f3922458b5cf9f3df4e872f64b2a6e17153676be7d",
    "PB|challenge|F16|r002": "a4dedd02a52016f670db13b381641458f72e17888dade03d0cff87e2fbd59de2",
}


def _payload_hash(case_id: str) -> str:
    generated = generate_case(case_id)
    return scientific_payload_hash(generated.inputs, generated.truth, generator_version=None)


# --------------------------------------------------------------------------
# 10: non-F16 deterministic generation is unchanged
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case_id,expected", sorted(NON_F16_PAYLOAD_HASHES.items()))
def test_non_f16_generation_is_byte_identical_to_amendment_a1(case_id, expected):
    assert _payload_hash(case_id) == expected


@pytest.mark.parametrize("case_id,expected", sorted(F16_PAYLOAD_HASHES.items()))
def test_repaired_f16_generation_is_pinned(case_id, expected):
    assert _payload_hash(case_id) == expected


def test_case_manifest_has_380_cases_with_f16_payload_matching_the_repair():
    """Full `content_hash` pins for the shipped manifest live in the Amendment
    A2.1 test module, since `content_hash` is version-stamped and A2.1 legitimately
    changes it for every case. This test checks what A2 owns: shape and the
    F16 scientific payload, independent of `GENERATOR_VERSION`.
    """
    manifest = json.loads((ARTIFACTS / "paper_benchmark_case_manifest.json").read_text())
    cases = manifest["cases"]

    assert manifest["case_count"] == 380
    assert len(cases) == 380
    ids_in_manifest = {c["case_id"] for c in cases}
    for case_id in NON_F16_PAYLOAD_HASHES:
        assert case_id in ids_in_manifest
    for case_id, expected in F16_PAYLOAD_HASHES.items():
        assert case_id in ids_in_manifest
        assert _payload_hash(case_id) == expected


# --------------------------------------------------------------------------
# Population, partition and seed invariants
# --------------------------------------------------------------------------


def test_registry_population_is_unchanged():
    assert len(CASE_FAMILIES) == 20
    assert ROOT_SEED == 20260813
    assert ENERGY_GRID == (15, 30, 45, 60, 75, 90)
    assert PARTITIONS == ("development", "held_out", "challenge")
    assert PARTITION_CASE_COUNTS == {"development": 4, "held_out": 12, "challenge": 3}
    assert sum(len(list(iter_case_ids(partition))) for partition in PARTITIONS) == 380


def test_partition_counts_are_unchanged():
    manifest = json.loads((ARTIFACTS / "paper_benchmark_partition_manifest.json").read_text())

    assert manifest["partitions"] == {
        "development": {"case_count": 80},
        "held_out": {"case_count": 240},
        "challenge": {"case_count": 60},
    }


def test_every_endpoint_denominator_is_unchanged():
    assert endpoint_denominator("scalar_competence") == 164
    assert endpoint_denominator("family_recovery") == 144
    assert endpoint_denominator("principal_structural_safety") == 36
    assert endpoint_denominator("m0_specificity") == 164
    assert endpoint_denominator("m1_sensitivity") == 36
    assert endpoint_denominator("m2_sensitivity") == 24
    assert endpoint_denominator("m3_sensitivity") == 24


# --------------------------------------------------------------------------
# 11: A1 adequacy decision constants and G1/G2/G3 thresholds
# --------------------------------------------------------------------------


def test_a1_adequacy_constants_are_unchanged():
    assert adequacy.MU_FLOOR == 1e-4
    assert adequacy.MU_CEIL == 1 - 1e-4
    assert adequacy.MIN_VERTICAL_AMPLITUDE == 0.05
    assert set(adequacy.ADEQUACY_MODELS) == {"M0", "M1", "M2", "M3"}
    assert adequacy.ADEQUACY_MODELS["M1"].reduces_to_m0_when == "s_i = 1 (log_shape = 0)"
    assert adequacy.ADEQUACY_MODELS["M2"].reduces_to_m0_when == "a_i = A_HI"
    assert adequacy.ADEQUACY_MODELS["M3"].reduces_to_m0_when == "b_i = A_LO"


def test_g1_g2_g3_thresholds_are_unchanged():
    body = inspect.getsource(umbrella_decision)

    assert '_gate_lower("G1"' in body
    assert '_gate_lower("G2"' in body
    assert '_gate_upper("G3"' in body
    # G1 and G2 are lower-bound gates at 0.70; G3 is an upper-bound gate at 0.15.
    assert body.count(", 0.70)") == 2
    assert body.count(", 0.15)") == 1


def test_content_freeze_remains_blocked_on_the_pending_implementation_lock():
    freeze = json.loads((ARTIFACTS / "paper_benchmark_content_freeze.json").read_text())

    assert freeze["status"] == "WAITING_FOR_LOCKED_IMPLEMENTATION"
    assert freeze["final_executable_freeze"] is False
    assert freeze["hashes_verified"] is True
