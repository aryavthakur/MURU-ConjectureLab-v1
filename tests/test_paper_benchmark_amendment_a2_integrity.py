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
from muru.paper_benchmark.generator import generate_case
from muru.paper_benchmark.registry import (
    CASE_FAMILIES,
    ENERGY_GRID,
    PARTITION_CASE_COUNTS,
    PARTITIONS,
    ROOT_SEED,
    iter_case_ids,
)

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

#: Frozen at A1 and required to be byte-identical after the F16 repair.
NON_F16_CONTENT_HASHES = {
    "PB|development|F01|r000": "5ef1a0beb75e73a2244710212fc48a8210ac73d33a51d2b0ca2ff5150a24ba90",
    "PB|development|F13|r000": "65960205c52b448a2e40e54ac6f0b034162f923bb97ea8eacf3464ae9704380c",
    "PB|development|F14|r000": "9d3f5f1210de340835afb17d57de30db690d476492c25b11528826bc0507d784",
    "PB|development|F15|r000": "c46805ba5529ba55423ad5563090ff870d5be79d61cf445c196ea400acf1d8a7",
    "PB|held_out|F06|r005": "6f2943d4748c23ff9a2513de2fa0c30e4a1f55b0a3ca18bbd7a9edad7391f694",
    "PB|held_out|F07|r003": "4b3f71e98493bd56b379c815e6beb3a296098afc6d80d67b2b67db63ac3a8198",
    "PB|held_out|F15|r011": "d468f19558850dcc68dd469383ae55224ad565b445d2448f52dd92bcca3d637b",
    "PB|held_out|F19|r008": "7f7b1adc64c8687e9eaf0f0b3c2e65b58ddefe70a36c3d2c1d5a38cae27788f3",
    "PB|challenge|F20|r002": "0bc94d2cae97c71494ebcf4bbff5a6caf3086db7d9793ff15123f283bd6afb9b",
}

#: Post-repair F16 values.
F16_CONTENT_HASHES = {
    "PB|development|F16|r000": "47fb8f24a2f3b3699b41c655245fbf213d2d3bbd7a7f126e707b196482cdcd9a",
    "PB|development|F16|r003": "6667754bd0a0547ee50712d86a6d98c337ee4d86553c0f7cdb8a40e078e53517",
    "PB|held_out|F16|r000": "b295e0b7afcdde14acf67eb2aa31b9dc1081efcbfb2f2037b80a9949adab95b5",
    "PB|held_out|F16|r011": "4e2f019fdbc5a1bd6bb34d048e635a7d8b2b120e6e5a38d4e872af519f7f1ef6",
    "PB|challenge|F16|r002": "ac33f7a759f6c1822c289e777b0785e8cf8102e857f0a479da45c10199b3c09e",
}


# --------------------------------------------------------------------------
# 10: non-F16 deterministic generation is unchanged
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case_id,expected", sorted(NON_F16_CONTENT_HASHES.items()))
def test_non_f16_generation_is_byte_identical_to_amendment_a1(case_id, expected):
    assert generate_case(case_id).content_hash == expected


@pytest.mark.parametrize("case_id,expected", sorted(F16_CONTENT_HASHES.items()))
def test_repaired_f16_generation_is_pinned(case_id, expected):
    assert generate_case(case_id).content_hash == expected


def test_case_manifest_changed_only_on_f16_rows():
    manifest = json.loads((ARTIFACTS / "paper_benchmark_case_manifest.json").read_text())
    cases = manifest["cases"]

    assert manifest["case_count"] == 380
    assert len(cases) == 380
    for case_id, expected in NON_F16_CONTENT_HASHES.items():
        assert next(c for c in cases if c["case_id"] == case_id)["content_hash"] == expected
    for case_id, expected in F16_CONTENT_HASHES.items():
        assert next(c for c in cases if c["case_id"] == case_id)["content_hash"] == expected


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
