"""Candidate equivalence must merge known reparameterizations and separate
known-distinct expressions (master plan, Phase 3 Tests).

String equality is not the criterion, and neither is raw correlation: a
candidate that merely correlates with the truth is not the truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery import equivalence, grammar  # noqa: E402

V = ["m", "h"]
BOUNDS = {"m": (0.25, 1.7), "h": (0.2, 2.7)}


def D(n=2000, seed=3):
    return equivalence.latin_hypercube(BOUNDS, V, n, seed)


def eq(a: str, b: str, d=None):
    return equivalence.equivalence(grammar.parse(a, V), grammar.parse(b, V), V,
                                   D() if d is None else d)


def test_algebraic_reparameterization_is_merged():
    r = eq("sqrt(m)*sqrt(m)", "m")
    assert r["exact_equivalent"] and r["functionally_equivalent"]


def test_expanded_and_factored_forms_are_merged():
    r = eq("m*h + m", "m*(h + 1)")
    assert r["exact_equivalent"]


def test_equivalence_is_judged_up_to_a_positive_scale():
    """The collapse model identifies g only up to a positive constant, so a
    rescaled expression is the SAME candidate."""
    r = eq("3.7*sqrt(m)", "sqrt(m)")
    assert r["exact_equivalent"], "scale-only difference must not split a family"
    assert abs(r["numeric"]["scale"] - 3.7) < 1e-6


def test_known_distinct_expressions_are_separated():
    r = eq("sqrt(m)", "m*m")
    assert not r["exact_equivalent"] and not r["functionally_equivalent"]


def test_a_merely_correlated_expression_is_not_equivalent():
    """Over this domain sqrt(m) and m correlate strongly; that is not identity."""
    r = eq("sqrt(m)", "m")
    assert r["numeric"]["r"] > 0.95
    assert not r["functionally_equivalent"]


def test_support_difference_is_reported_even_when_shapes_are_close():
    r = eq("sqrt(m)", "sqrt(m)*(1 + 0.0001*h)")
    assert set(r["support_b"]) == {"m", "h"}
    assert not r["support_match"]


def test_latin_hypercube_is_independent_of_the_training_points():
    a, b = D(500, 1), D(500, 2)
    assert not np.allclose(a, b)
    for i, v in enumerate(V):
        lo, hi = BOUNDS[v]
        assert a[:, i].min() >= lo and a[:, i].max() <= hi


def test_fingerprint_clustering_groups_reparameterizations():
    class C:
        def __init__(self, s):
            self.expr = grammar.parse(s, V)
            self.expr_str, self.complexity, self.valid_r2 = s, 1, 0.5
    # m/sqrt(m) IS sqrt(m), written differently; m*m is a different object.
    cands = [C("sqrt(m)"), C("2*sqrt(m)"), C("m*m"), C("m/sqrt(m)")]
    clusters = equivalence.cluster_by_fingerprint(cands, V, D())
    sizes = sorted(len(c) for c in clusters)
    assert sizes == [1, 3], f"expected sqrt-family merged, got {clusters}"


def test_selection_frequency_counts_families_not_strings():
    class C:
        def __init__(self, s):
            self.expr = grammar.parse(s, V)
            self.expr_str, self.complexity, self.valid_r2 = s, 1, 0.5
    seeds = [C("sqrt(m)"), C("1.5*sqrt(m)"), C("0.9*sqrt(m)"), C("m*h")]
    s = equivalence.selection_frequency(seeds, V, D())
    assert s["top_count"] == 3 and s["n_seeds"] == 4
    assert abs(s["fraction"] - 0.75) < 1e-9


def test_a_complex_interpolant_is_not_scored_as_recovery():
    """High-order polynomial noise fitting must not read as the planted law."""
    r = eq("sqrt(m)", "0.1*m*m*m - 0.5*m*m + 1.3*m + 0.2")
    assert not r["exact_equivalent"]
    assert r["complexity_b"] > r["complexity_a"]
