"""The fresh validation worlds must be genuinely fresh.

`OBJECTIVE_ALIGNMENT_AMENDMENT.md` §8 makes the Phase 3 worlds development
evidence only. If a Phase 3 seed, world id or world could leak into this study's
plan, the separation would be decorative.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from muru.objval.generators2 import GENERATOR2_VERSION, world_seed2
from muru.objval.plan2 import (OV_SEED_BASE, P3_SEED_THEORETICAL_MAX,
                               all_worlds2, seed_list2)
from muru.synth.generators import GENERATOR_VERSION
from muru.synth.plan import all_worlds as p3_worlds

ART = Path(__file__).resolve().parents[1] / "artifacts"


def _ov_seeds() -> list[int]:
    return [s for w in all_worlds2() for s in seed_list2(w.world_id)]


def test_seed_band_is_disjoint_from_phase3_by_construction():
    assert OV_SEED_BASE > P3_SEED_THEORETICAL_MAX
    assert min(_ov_seeds()) > P3_SEED_THEORETICAL_MAX


def test_seeds_stay_inside_the_engine_s_accepted_integer_range():
    assert max(_ov_seeds()) < 2 ** 31 - 1


def test_realized_seed_sets_do_not_intersect():
    p3 = ART / "p3_seed_manifest.json"
    if not p3.exists():
        pytest.skip("Phase 3 seed manifest not present in this checkout")
    old = {s for v in json.loads(p3.read_text())["seeds"].values() for s in v}
    assert not (old & set(_ov_seeds()))


def test_world_ids_are_unique_and_cannot_collide_with_phase3():
    ids = [w.world_id for w in all_worlds2()]
    assert len(set(ids)) == len(ids)
    assert all(i.startswith("OV|") for i in ids)
    assert not (set(ids) & {w.world_id for w in p3_worlds()})


def test_generator_namespace_differs_so_world_data_cannot_be_reused():
    assert GENERATOR2_VERSION != GENERATOR_VERSION
    # the same (family, replicate, regime) draws a different generator seed
    from muru.synth.generators import world_seed as p3_world_seed
    assert world_seed2("G1B", 0, "moderate") != p3_world_seed("G1B", 0, "moderate")


def test_an_old_phase3_world_cannot_be_counted_as_new_validation():
    """A Phase 3 checkpoint directory name can never satisfy this study's plan."""
    plan_ids = {w.world_id for w in all_worlds2()}
    for w in p3_worlds():
        assert w.world_id not in plan_ids
        assert w.world_id.replace("|", "~") not in {i.replace("|", "~")
                                                    for i in plan_ids}


def test_seed_manifest_if_present_matches_the_plan():
    p = ART / "ov_seed_manifest.json"
    if not p.exists():
        pytest.skip("fresh seed manifest not yet written")
    m = json.loads(p.read_text())
    for w in all_worlds2():
        assert m["seeds"][w.world_id] == seed_list2(w.world_id)
