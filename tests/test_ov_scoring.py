"""Type 2 signature, family equivalence and recovery scoring.

These are the definitions the whole study rests on, so each is tested against a
case whose answer is known analytically rather than against itself.
"""
from __future__ import annotations

import numpy as np
import pytest
import sympy as sp

from muru.discovery import grammar
from muru.objval import equiv, recovery, select, signature

V = ["precursor_mz", "total_atom_count", "rotatable_bonds", "ring_count",
     "aromatic_ring_count", "rdbe", "tpsa", "heteroatom_fraction",
     "n_N", "n_O", "n_S", "n_halogen"]


@pytest.fixture(scope="module")
def Z():
    rng = np.random.default_rng(11)
    return rng.uniform(0.25, 1.75, size=(1500, len(V)))


def _sig(expr, Z):
    return signature.signature(sp.sympify(expr), V, Z)


# --- elasticity is the planted exponent, and is scale-invariant -------------
@pytest.mark.parametrize("expr,expected", [
    ("sqrt(precursor_mz)", 0.5),
    ("precursor_mz", 1.0),
    ("precursor_mz**2", 2.0),
    ("1/precursor_mz", -1.0),
    ("2.7*sqrt(precursor_mz)", 0.5),       # positive scaling changes nothing
])
def test_scaling_exponent_matches_the_analytic_value(expr, expected, Z):
    assert _sig(expr, Z)["exponents"]["precursor_mz"] == pytest.approx(
        expected, abs=1e-3)


def test_exponent_is_invariant_to_positive_rescaling(Z):
    a = _sig("sqrt(precursor_mz)*(1 + 0.4*heteroatom_fraction)", Z)
    b = _sig("9.13*sqrt(precursor_mz)*(1 + 0.4*heteroatom_fraction)", Z)
    assert a["exponents"] == pytest.approx(b["exponents"], abs=1e-6)


def test_compiled_evaluation_agrees_with_the_frozen_grammar_evaluator(Z):
    e = sp.sympify("sqrt(precursor_mz*(heteroatom_fraction + 0.8))")
    v1, o1 = signature._eval(e, V, Z)
    v2, o2 = grammar.evaluate(e, V, Z)
    assert np.array_equal(o1, o2)
    assert np.allclose(v1[o1], v2[o2], rtol=0, atol=0)


# --- effective support ------------------------------------------------------
def test_a_variable_that_does_nothing_is_not_effective_support(Z):
    s = _sig("sqrt(precursor_mz) + 1e-9*tpsa", Z)
    assert "tpsa" in s["symbolic_support"]
    assert "tpsa" not in s["effective_support"]


def test_a_variable_that_matters_is_effective_support(Z):
    s = _sig("sqrt(precursor_mz)*(1 + 0.4*heteroatom_fraction)", Z)
    assert set(s["effective_support"]) == {"precursor_mz", "heteroatom_fraction"}
    assert s["signs"]["heteroatom_fraction"] == 1


def test_a_negative_effect_is_signed_negative(Z):
    s = _sig("sqrt(precursor_mz)/(1 + 0.4*tpsa)", Z)
    assert s["signs"]["tpsa"] == -1


def test_a_candidate_that_is_not_a_positive_scale_is_unusable(Z):
    assert not _sig("heteroatom_fraction - 1.0", Z)["usable"]


# --- block level ------------------------------------------------------------
def test_mass_block_exponent_is_the_same_for_every_size_proxy(Z):
    a = _sig("sqrt(precursor_mz)", Z)
    b = _sig("sqrt(total_atom_count)", Z)
    assert signature.mass_exponent(a) == pytest.approx(0.5, abs=1e-3)
    assert signature.mass_exponent(b) == pytest.approx(0.5, abs=1e-3)
    assert a["effective_support_blocks"] == b["effective_support_blocks"] == ["MASS"]
    # and the variable-level supports still differ, and are still reported
    assert a["effective_support"] != b["effective_support"]


# --- family equivalence -----------------------------------------------------
def _pair(e1, e2, Z):
    s1, s2 = _sig(e1, Z), _sig(e2, Z)
    v1, o1 = signature._eval(sp.sympify(e1), V, Z)
    v2, o2 = signature._eval(sp.sympify(e2), V, Z)
    return equiv.same_family(s1, s2, v1, v2, o1 & o2)


def test_a_proxy_substitution_passes_the_support_and_exponent_conditions(Z):
    """Block-level support and scaling treat two size proxies as one claim.

    The family predicate ALSO requires dense predictive agreement on an
    independently generated lattice (master plan 13.5), and that lattice
    deliberately destroys the corpus's correlation structure — so two proxies
    that happen to be collinear in the real corpus are still separated there.
    That is the conservative behaviour and it is kept. Support and exponent
    agreement is what the corroboration standard is stated on.
    """
    r = _pair("sqrt(precursor_mz)", "sqrt(total_atom_count)", Z)
    assert not any("support" in x for x in r["reasons"])
    assert not any("exponent" in x for x in r["reasons"])
    assert any("predictions disagree" in x for x in r["reasons"])
    a, b = _sig("sqrt(precursor_mz)", Z), _sig("sqrt(total_atom_count)", Z)
    assert a["effective_support_blocks"] == b["effective_support_blocks"]
    assert signature.mass_exponent(a) == pytest.approx(
        signature.mass_exponent(b), abs=1e-3)


def test_a_different_exponent_is_a_different_family(Z):
    r = _pair("sqrt(precursor_mz)", "precursor_mz", Z)
    assert not r["same_family"]
    assert any("exponent" in x for x in r["reasons"])


def test_an_extra_effective_variable_is_a_different_family(Z):
    r = _pair("sqrt(precursor_mz)",
              "sqrt(precursor_mz)*(1 + 0.5*heteroatom_fraction)", Z)
    assert not r["same_family"]
    assert any("support" in x for x in r["reasons"])


def test_an_opposite_sign_is_a_different_family(Z):
    r = _pair("sqrt(precursor_mz)*(1 + 0.5*tpsa)",
              "sqrt(precursor_mz)/(1 + 0.5*tpsa)", Z)
    assert not r["same_family"]


def test_family_equivalence_is_looser_than_functional_equivalence(Z):
    e1 = "sqrt(precursor_mz)*(1 + 0.30*heteroatom_fraction)"
    e2 = "sqrt(precursor_mz)*(1 + 0.36*heteroatom_fraction)"
    v1, o1 = signature._eval(sp.sympify(e1), V, Z)
    v2, o2 = signature._eval(sp.sympify(e2), V, Z)
    assert _pair(e1, e2, Z)["same_family"]
    fc = equiv.functional_class(v1, v2, o1 & o2)
    assert not fc["exact_equivalent"]


def test_clustering_is_deterministic_in_input_order(Z):
    exprs = ["sqrt(precursor_mz)", "1.9*sqrt(precursor_mz)",
             "precursor_mz", "sqrt(precursor_mz)*(1+0.5*tpsa)"]
    sigs, vals, oks = [], [], []
    for e in exprs:
        sigs.append(_sig(e, Z))
        v, o = signature._eval(sp.sympify(e), V, Z)
        vals.append(v), oks.append(o)
    c1 = equiv.cluster_families(sigs, vals, oks)
    c2 = equiv.cluster_families(sigs, vals, oks)
    assert c1 == c2
    # the two that differ only by a positive scale merge; the other two do not
    assert sorted(len(c) for c in c1) == [1, 1, 2]
    assert [0, 1] in c1


# --- the selection rule -----------------------------------------------------
class _C:
    def __init__(self, e, cx, r2, seed=1):
        self.expr_str, self.expr = e, sp.sympify(e)
        self.complexity, self.valid_r2, self.train_r2 = cx, r2, r2
        self.invalid_fraction, self.valid, self.seed = 0.0, True, seed
        self.engine = "pysr"


def test_the_band_retains_everything_within_tolerance_not_just_the_cheapest():
    cands = [_C("sqrt(precursor_mz)", 2, 0.900),
             _C("sqrt(precursor_mz*(heteroatom_fraction+0.8))", 6, 0.905),
             _C("precursor_mz", 1, 0.500)]
    band = select.pareto_band(cands)
    assert {c.complexity for c in band} == {2, 6}      # 0.500 is outside 0.01
    assert len(band) == 2, "Phase 3 kept only the cheapest of exactly this set"


def test_selection_reports_the_family_and_counts_its_algebraic_forms(Z):
    per_seed = {}
    for s in range(30):
        per_seed[s] = [
            _C("sqrt(precursor_mz*(heteroatom_fraction+0.80))", 6, 0.905, s),
            _C("sqrt(precursor_mz*(heteroatom_fraction+0.84))", 6, 0.902, s),
            _C("precursor_mz", 1, 0.10, s)]
    r = select.select("w", per_seed, V, Z)
    rep = r.reported
    assert rep["selection_fraction"] == 1.0
    assert set(rep["effective_support"]) == {"precursor_mz", "heteroatom_fraction"}
    assert rep["representative"]["complexity"] == 6


# --- recovery scoring -------------------------------------------------------
def test_shape_recovery_accepts_the_planted_shape_and_rejects_a_wrong_one():
    params = {"mu_inf": 0.24, "phi_p": 1.5}
    u = np.exp(np.linspace(-2.0, 2.0, 60))
    good = recovery.shape_recovery(np.log(u),
                                   recovery.phi(u, 0.24, 1.5), params)
    bad = recovery.shape_recovery(np.log(u),
                                  recovery.phi(u, 0.60, 4.0), params)
    assert good["shape_family_recovered"]
    assert not bad["shape_family_recovered"]


def test_exact_form_recovery_is_reported_separately_from_type2(Z):
    params = {"g_scale": 1.7, "struct_coef": 0.35, "carrier": "heteroatom_fraction",
              "mu_inf": 0.24, "phi_p": 1.5}
    approx = sp.sympify("sqrt(precursor_mz*(heteroatom_fraction + 0.80))")
    out = recovery.score_world(
        "G1B", params, V, Z,
        reported={"n_distinct_algebraic_forms": 3,
                  "algebraic_form_identified": False},
        rep_expr=approx, band_exprs=[approx])
    assert out["support_recovery"]["recovered"] is True
    assert out["exponent_recovery"]["per_block"]["MASS"]["within_tolerance"]
    # Type 2 succeeds; the Type 3 diagnostic is present and separate
    assert "system_reported_the_law" in out["exact_form"]
    assert out["exact_form"]["algebraic_form_identified"] is False


def test_exponent_recovery_fails_outside_the_master_plan_tolerance(Z):
    params = {"g_scale": 1.7, "struct_coef": 0.35, "carrier": "heteroatom_fraction",
              "mu_inf": 0.24, "phi_p": 1.5}
    wrong = sp.sympify("precursor_mz*(heteroatom_fraction + 0.80)")   # exponent 1
    out = recovery.score_world("G1B", params, V, Z,
                               reported={"n_distinct_algebraic_forms": 1,
                                         "algebraic_form_identified": True},
                               rep_expr=wrong, band_exprs=[wrong])
    assert not out["exponent_recovery"]["recovered"]
    assert out["exponent_recovery"]["tolerance"] == 0.15


def test_support_recovery_flags_an_unsupported_extra_block(Z):
    params = {"g_scale": 1.7, "struct_coef": 0.35, "carrier": "heteroatom_fraction",
              "mu_inf": 0.24, "phi_p": 1.5}
    extra = sp.sympify("sqrt(precursor_mz*(heteroatom_fraction + 0.8))*(1+0.6*n_N)")
    out = recovery.score_world("G1B", params, V, Z,
                               reported={"n_distinct_algebraic_forms": 1,
                                         "algebraic_form_identified": True},
                               rep_expr=extra, band_exprs=[extra])
    assert not out["support_recovery"]["recovered"]
    assert "n_N" in out["support_recovery"]["extra_blocks"]


def test_worlds_with_no_descriptor_law_score_as_not_applicable(Z):
    for fam in ("G4", "GC"):
        out = recovery.score_world(fam, {"mu_inf": 0.24, "phi_p": 1.5,
                                         "g_scale": 1.7}, V, Z, None, None, [])
        assert out["support_recovery"]["applicable"] is False


def test_a_latent_driver_world_is_not_scored_for_support_recovery(Z):
    out = recovery.score_world("G5", {"mu_inf": 0.24, "phi_p": 1.5,
                                      "g_scale": 1.7, "latent_rho": 0.6,
                                      "struct_coef": 0.4,
                                      "carrier": "heteroatom_fraction"},
                               V, Z, None, None, [])
    assert out["family_recovery"]["applicable"] is False
