"""Frozen symbolic grammar, protected numerics, and the complexity metric.

Frozen by `PHASE3_PREREGISTRATION.md` before any governed run. Changing any of
it after seeing recovery performance is a deviation and must be recorded in
`DEVIATIONS_P3.md`.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

GRAMMAR_VERSION = "p3-grammar-1.0.0"

BINARY_OPERATORS = ["+", "-", "*", "/"]
UNARY_OPERATORS = ["sqrt", "log", "square", "cube", "inv"]

# `exp` is deliberately excluded (DEVIATIONS_P3 D1). The search target is a
# positive energy SCALE; the logistic shape lives in Phi, which is fitted
# nonparametrically rather than searched, so exp buys no planted structure while
# adding overflow pathologies. Trigonometric functions are excluded because
# nothing in this physics oscillates (master plan 13.4).
MAX_COMPLEXITY = 20

# Nested-operator limits block exp(exp(x))-style pathologies (master plan 13.3).
NESTED_CONSTRAINTS = {
    "sqrt": {"sqrt": 0, "log": 0},
    "log": {"log": 0, "sqrt": 0},
    "inv": {"inv": 0},
    "square": {"square": 0, "cube": 0},
    "cube": {"cube": 0, "square": 0},
}

EPS = 1e-12
OVERFLOW = 1e12


# --------------------------------------------------------------------------
# protected numerics
# --------------------------------------------------------------------------
def _invalid_like(a: np.ndarray) -> np.ndarray:
    return np.zeros(np.shape(a), dtype=bool)


def safe_div(a, b):
    """Division guarded off zero. Returns (value, invalid_mask)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    bad = np.abs(b) < EPS
    out = np.divide(a, np.where(bad, 1.0, b))
    return out, bad


def safe_inv(a):
    a = np.asarray(a, float)
    bad = np.abs(a) < EPS
    return np.divide(1.0, np.where(bad, 1.0, a)), bad


def safe_log(a):
    a = np.asarray(a, float)
    bad = a <= 0
    return np.log(np.where(bad, 1.0, a)), bad


def safe_sqrt(a):
    a = np.asarray(a, float)
    bad = a < 0
    return np.sqrt(np.where(bad, 0.0, a)), bad


def finite_mask(y: np.ndarray) -> np.ndarray:
    """Overflow, underflow-to-nonfinite and NaN are all invalidity."""
    y = np.asarray(y, float)
    return np.isfinite(y) & (np.abs(y) < OVERFLOW)


# Fraction of evaluation points allowed to be invalid before the candidate is
# rejected outright. Invalidity NEVER improves a score: invalid points are
# excluded from the fit statistic and counted against the candidate here.
MAX_INVALID_FRACTION = 0.005


# --------------------------------------------------------------------------
# sympy evaluation with protected semantics
# --------------------------------------------------------------------------
_SYMPY_LOCALS = {
    "square": lambda x: x ** 2,
    "cube": lambda x: x ** 3,
    "inv": lambda x: 1 / x,
    "sqrt": sp.sqrt,
    "log": sp.log,
}


def parse(expr: str, variables: list[str]) -> sp.Expr:
    """Parse an engine-emitted expression string into a sympy expression.

    Symbols carry NO positivity assumption. Assuming positivity makes sympy
    restructure expressions on sight — `sqrt(a*b)` becomes `sqrt(a)*sqrt(b)` —
    which would inflate the node count relative to the tree the engine actually
    searched and break the stated goal of keeping PySR and gplearn on one
    complexity scale. Positivity is asserted only inside
    `equivalence.algebraically_equivalent`, where it is a proof aid rather than
    a representation change.
    """
    loc = dict(_SYMPY_LOCALS)
    loc.update({v: sp.Symbol(v) for v in variables})
    return sp.sympify(expr, locals=loc)


def evaluate(expr: sp.Expr, variables: list[str],
             X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate a candidate on a design matrix under protected semantics.

    Returns `(values, valid_mask)`. Points that divide by zero, take a log or
    square root outside the domain, overflow, or produce NaN are marked invalid
    and their values are not trusted.
    """
    syms = [sp.Symbol(v) for v in variables]
    with np.errstate(all="ignore"):
        try:
            # lambdify itself raises on degenerate expressions such as the
            # ComplexInfinity that `1/(a-a)` collapses to. That is invalidity,
            # not an error to propagate — and it must never become a good score.
            fn = sp.lambdify(syms, expr, modules=["numpy"])
            out = np.asarray(fn(*[X[:, i] for i in range(X.shape[1])]), float)
        except Exception:
            return np.zeros(len(X)), np.zeros(len(X), dtype=bool)
    if out.ndim == 0:
        out = np.full(len(X), float(out))
    return out, finite_mask(out)


# --------------------------------------------------------------------------
# complexity
# --------------------------------------------------------------------------
def complexity(expr: sp.Expr) -> int:
    """Node count over the canonical expression tree.

    One metric, applied identically to PySR and gplearn output, used for
    candidate ranking, the Pareto front, null calibration and the Phase 4
    thresholds. A variable costs 1, a constant costs 1, each binary operation
    costs 1, each unary operation costs 1.

    An integer or half-integer power counts as ONE unary operation over its
    base, so `x**2` costs 2 exactly as PySR's `square(x)` does; this keeps the
    two engines on the same scale.
    """
    if expr.is_Symbol or expr.is_Number or expr.is_NumberSymbol:
        return 1
    if expr.is_Add or expr.is_Mul:
        return (len(expr.args) - 1) + sum(complexity(a) for a in expr.args)
    if expr.is_Pow:
        e = expr.exp
        if e.is_Number:
            return 1 + complexity(expr.base)
        return 1 + complexity(expr.base) + complexity(e)
    return 1 + sum(complexity(a) for a in expr.args)


def variable_support(expr: sp.Expr, variables: list[str]) -> tuple[str, ...]:
    """Variables the SIMPLIFIED expression genuinely depends on."""
    try:
        e = sp.cancel(sp.together(expr))
    except Exception:
        e = expr
    free = {str(s) for s in e.free_symbols}
    return tuple(v for v in variables if v in free)


PROTECTED_SEMANTICS = {
    "division": "|denominator| < 1e-12 -> invalid",
    "inv": "|argument| < 1e-12 -> invalid",
    "log": "argument <= 0 -> invalid",
    "sqrt": "argument < 0 -> invalid",
    "overflow": "|value| >= 1e12 -> invalid",
    "nan": "NaN or non-finite -> invalid",
    "scoring": ("invalid points are excluded from the fit statistic and counted "
                "against the candidate; a candidate with more than 0.5% invalid "
                "points on the evaluation domain is rejected outright. "
                "Invalidity can never improve a score."),
}
