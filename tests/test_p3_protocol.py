"""Grouped evaluation, leakage control, ranking and the acceptance rule."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery import grammar, protocol  # noqa: E402
from muru.discovery.protocol import WorldResult  # noqa: E402


class C:
    def __init__(self, s, cx, r2, support=("m",), invalid=0.0):
        self.expr_str, self.complexity, self.valid_r2 = s, cx, r2
        self.expr = grammar.parse(s, ["m"])
        self.support, self.invalid_fraction, self.valid = support, invalid, True
        self.train_r2, self.engine, self.seed = r2, "pysr", 0


def groups(n=400, k=60, seed=0):
    rng = np.random.default_rng(seed)
    return np.array([f"S{g:03d}" for g in rng.integers(0, k, n)])


# --- splits -----------------------------------------------------------------
def test_no_scaffold_group_straddles_a_split_boundary():
    g = groups()
    s = protocol.group_split(g, "W1")
    for grp in np.unique(g):
        assert len(set(s[g == grp])) == 1, f"group {grp} straddles the wall"


def test_all_three_partitions_are_populated():
    s = protocol.group_split(groups(), "W1")
    for part in ("train", "valid", "test"):
        assert (s == part).sum() > 20


def test_split_is_deterministic_for_a_given_world():
    g = groups()
    assert (protocol.group_split(g, "W1") == protocol.group_split(g, "W1")).all()


def test_different_worlds_get_different_splits():
    g = groups()
    assert not (protocol.group_split(g, "W1") == protocol.group_split(g, "W2")).all()


def test_one_huge_group_cannot_dominate_a_partition():
    """The 80-compound benzene group is the real case this guards."""
    g = np.array(["BIG"] * 80 + [f"S{i:03d}" for i in range(320)])
    s = protocol.group_split(g, "W1")
    frac = {p: (s == p).sum() / len(g) for p in ("train", "valid", "test")}
    assert 0.4 < frac["train"] < 0.8
    assert all(v > 0.05 for v in frac.values())


# --- seeds ------------------------------------------------------------------
def test_seed_list_is_frozen_and_thirty_long():
    a = protocol.seed_list("G1B|r000|moderate")
    assert len(a) == 30 == protocol.N_SEEDS
    assert a == protocol.seed_list("G1B|r000|moderate")
    assert len(set(a)) == 30


def test_different_worlds_get_different_seeds():
    assert set(protocol.seed_list("A")) != set(protocol.seed_list("B"))


# --- ranking ----------------------------------------------------------------
def test_elbow_prefers_the_simplest_expression_within_tolerance():
    cands = [C("m", 1, 0.50), C("sqrt(m)", 4, 0.943), C("m*m*m", 8, 0.9455)]
    assert protocol.elbow_pick(cands).complexity == 4, (
        "the elbow must not chase the last 0.002 of R^2 with 4 more nodes")


def test_elbow_rejects_candidates_outside_the_complexity_budget():
    assert protocol.elbow_pick([C("m", 25, 0.99)]) is None


def test_elbow_returns_none_when_nothing_is_valid():
    assert protocol.elbow_pick([]) is None


def test_best_r2_by_complexity_is_non_decreasing():
    curve = protocol.best_r2_by_complexity([C("m", 3, 0.4), C("sqrt(m)", 7, 0.8)])
    finite = curve[np.isfinite(curve)]
    assert all(finite[i] <= finite[i + 1] for i in range(len(finite) - 1))
    assert curve[3] == 0.4 and curve[7] == 0.8 and curve[20] == 0.8


# --- acceptance -------------------------------------------------------------
def result(cx=4, r2=0.9, frac=1.0, invalid=0.0, support=("m",)):
    c = C("sqrt(m)", cx, r2, support=support, invalid=invalid)
    return WorldResult("W", "pysr", c, {"fraction": frac, "top_count": 30,
                                        "n_seeds": 30, "n_families": 1,
                                        "top_index": 0}, [c],
                       np.zeros(21), 30)


THR = np.full(21, 0.30)


def test_acceptance_requires_every_condition():
    ok = protocol.accept(result(), THR, {"passed": True})
    assert ok["accepted"] and all(ok["conditions"].values())


@pytest.mark.parametrize("kw,failing", [
    (dict(r2=0.10), "exceeds_null_threshold"),
    (dict(frac=0.50), "seed_stability"),
    (dict(invalid=0.10), "numerically_valid"),
])
def test_each_condition_can_veto_on_its_own(kw, failing):
    a = protocol.accept(result(**kw), THR, {"passed": True})
    assert not a["accepted"] and a["conditions"][failing] is False


def test_a_failed_harness_vetoes_acceptance():
    a = protocol.accept(result(), THR, {"passed": False})
    assert not a["accepted"]


def test_a_missing_harness_is_not_treated_as_a_pass():
    a = protocol.accept(result(), THR, None)
    assert not a["accepted"]


def test_no_candidate_is_not_an_acceptance():
    r = WorldResult("W", "pysr", None, {"fraction": 0.0}, [], np.zeros(21), 30)
    assert not protocol.accept(r, THR, {"passed": True})["accepted"]


def test_stability_boundary_is_twenty_of_thirty():
    assert protocol.accept(result(frac=20 / 30), THR, {"passed": True})["accepted"]
    assert not protocol.accept(result(frac=19 / 30), THR,
                               {"passed": True})["accepted"]


# --- mass logic -------------------------------------------------------------
def test_mass_block_is_the_phase_2_block_removed_together():
    assert set(protocol.MASS_BLOCK) == {"precursor_mz", "total_atom_count", "rdbe"}


def test_mass_only_and_non_mass_support_are_distinguished():
    assert protocol.is_mass_only(("precursor_mz", "rdbe"))
    assert not protocol.is_mass_only(("precursor_mz", "tpsa"))
    assert protocol.has_non_mass_support(("precursor_mz", "tpsa"))
    assert not protocol.has_non_mass_support(("total_atom_count",))


def test_a_structural_claim_is_flagged_on_acceptance():
    a = protocol.accept(result(support=("precursor_mz", "heteroatom_fraction")),
                        THR, {"passed": True})
    assert a["claims_non_mass_structure"] and not a["mass_only"]
