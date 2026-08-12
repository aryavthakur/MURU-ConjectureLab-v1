"""Operator safety, protected numerics, and the complexity metric.

The rule these tests exist to defend: candidate invalidity must never be
silently converted into a favourable score.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery import grammar  # noqa: E402

V = ["a", "b"]


def test_protected_division_flags_zero_denominators():
    out, bad = grammar.safe_div(np.array([1.0, 2.0]), np.array([2.0, 0.0]))
    assert bad.tolist() == [False, True]
    assert out[0] == 0.5
    assert np.isfinite(out).all(), "a protected op must not emit inf/nan itself"


def test_protected_log_and_sqrt_flag_out_of_domain():
    _, badl = grammar.safe_log(np.array([1.0, 0.0, -3.0]))
    _, bads = grammar.safe_sqrt(np.array([4.0, -1.0]))
    assert badl.tolist() == [False, True, True]
    assert bads.tolist() == [False, True]


def test_overflow_and_nan_are_invalidity():
    assert grammar.finite_mask(np.array([1.0, np.nan, np.inf, 1e13])).tolist() \
        == [True, False, False, False]


def test_division_by_zero_is_invalid_not_a_free_win():
    """1/(a-a) is undefined everywhere; it must be marked invalid, and the
    invalid fraction must exceed the rejection limit."""
    e = grammar.parse("1/(a - a)", V)
    X = np.column_stack([np.linspace(1, 2, 50), np.linspace(1, 2, 50)])
    _, ok = grammar.evaluate(e, V, X)
    assert ok.mean() == 0.0
    assert (1 - ok.mean()) > grammar.MAX_INVALID_FRACTION


def test_log_of_a_negative_subexpression_is_invalid_where_it_should_be():
    e = grammar.parse("log(a - b)", V)
    X = np.column_stack([np.array([2.0, 1.0, 3.0]), np.array([1.0, 2.0, 1.0])])
    _, ok = grammar.evaluate(e, V, X)
    assert ok.tolist() == [True, False, True]


@pytest.mark.parametrize("expr,expected", [
    ("a", 1),
    ("a + b", 3),               # a, b, +
    ("a*b + 1.0", 5),           # a, b, *, const, +
    ("sqrt(a)", 2),             # a, sqrt
    ("a**2", 2),                # counted as one unary over the base
    ("a**3", 2),
    ("sqrt(a*b)", 4),          # a, b, *, sqrt — the tree the engine searched
    ("a + b + 1.0", 5),
])
def test_complexity_counts_nodes(expr, expected):
    assert grammar.complexity(grammar.parse(expr, V)) == expected


def test_parsing_does_not_restructure_the_engines_tree():
    """Positivity assumptions would split sqrt(a*b) into sqrt(a)*sqrt(b) and
    inflate the node count above what the engine actually searched."""
    e = grammar.parse("sqrt(a*b)", V)
    assert e.is_Pow and grammar.complexity(e) == 4


def test_square_and_power_agree_so_engines_share_one_scale():
    """`square(x)` and `x**2` are the same object and must cost the same."""
    assert (grammar.complexity(grammar.parse("square(a)", V))
            == grammar.complexity(grammar.parse("a**2", V)))


def test_complexity_is_monotone_under_wrapping():
    inner = grammar.parse("a*b", V)
    outer = grammar.parse("sqrt(a*b)", V)
    assert grammar.complexity(outer) > grammar.complexity(inner)


def test_variable_support_ignores_variables_that_cancel():
    assert grammar.variable_support(grammar.parse("a + b - b", V), V) == ("a",)


def test_grammar_excludes_trigonometric_and_exponential_operators():
    assert "exp" not in grammar.UNARY_OPERATORS
    assert not any(t in grammar.UNARY_OPERATORS
                   for t in ("sin", "cos", "tan", "atan"))


def test_max_complexity_is_the_master_plan_budget():
    assert grammar.MAX_COMPLEXITY == 20
