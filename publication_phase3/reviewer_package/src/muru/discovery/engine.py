"""Symbolic search: PySR (primary) and gplearn (comparison arm).

PySR is the primary engine per master plan 13.3 and stays primary unless
`DEVIATIONS_P3.md` records a justified deviation. gplearn's role is
methodological comparison on T2, not a tournament, and it cannot rescue a
failing PySR calibration.

This module reads data and returns candidates. It never reads a planted law.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

import numpy as np
import sympy as sp

from muru.discovery import grammar

ENGINE_VERSION = "p3-engine-1.0.0"

# Frozen search configuration. Benchmarked at 2.3 s per run serial on the
# development covariate matrix; see RUNTIME_BUDGET_P3.md.
PYSR_CONFIG = dict(
    niterations=40,
    populations=15,
    population_size=33,
    maxsize=grammar.MAX_COMPLEXITY,
    binary_operators=list(grammar.BINARY_OPERATORS),
    unary_operators=list(grammar.UNARY_OPERATORS),
    nested_constraints=dict(grammar.NESTED_CONSTRAINTS),
    parsimony=0.0032,
    adaptive_parsimony_scaling=20.0,
    deterministic=True,
    parallelism="serial",
    verbosity=0,
    progress=False,
)

GPLEARN_CONFIG = dict(
    population_size=1000,
    generations=20,
    function_set=("add", "sub", "mul", "div", "sqrt", "log", "inv"),
    parsimony_coefficient=0.005,
    n_jobs=1,
    verbose=0,
)


@dataclass
class Candidate:
    expr_str: str
    expr: sp.Expr
    complexity: int
    support: tuple[str, ...]
    engine: str
    seed: int
    train_r2: float
    valid_r2: float
    invalid_fraction: float
    valid: bool
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"expr_str": self.expr_str, "expr": sp.srepr(self.expr),
                "complexity": self.complexity, "support": list(self.support),
                "engine": self.engine, "seed": self.seed,
                "train_r2": self.train_r2, "valid_r2": self.valid_r2,
                "invalid_fraction": self.invalid_fraction, "valid": self.valid,
                "meta": self.meta}


def weighted_r2(y: np.ndarray, pred: np.ndarray, w: np.ndarray,
                mask: np.ndarray | None = None) -> float:
    """Weighted R^2. Invalid points are excluded from the numerator's benefit
    and their absence is charged separately by `invalid_fraction`."""
    if mask is None:
        mask = np.ones(len(y), dtype=bool)
    if mask.sum() < 3:
        return -np.inf
    yy, pp, ww = y[mask], pred[mask], w[mask]
    mean = np.average(yy, weights=ww)
    ss_res = float(np.sum(ww * (yy - pp) ** 2))
    ss_tot = float(np.sum(ww * (yy - mean) ** 2))
    if ss_tot <= 0:
        return -np.inf
    return 1.0 - ss_res / ss_tot


def score_candidate(expr: sp.Expr, variables: list[str], X: np.ndarray,
                    y: np.ndarray, w: np.ndarray) -> tuple[float, float, bool]:
    """(r2, invalid_fraction, usable) under protected semantics."""
    pred, ok = grammar.evaluate(expr, variables, X)
    frac_invalid = float(1.0 - ok.mean())
    if frac_invalid > grammar.MAX_INVALID_FRACTION:
        return -np.inf, frac_invalid, False
    return weighted_r2(y, pred, w, ok), frac_invalid, True


# --------------------------------------------------------------------------
# PySR
# --------------------------------------------------------------------------
def run_pysr(Xtr: np.ndarray, ytr: np.ndarray, wtr: np.ndarray,
             Xva: np.ndarray, yva: np.ndarray, wva: np.ndarray,
             variables: list[str], seed: int) -> list[Candidate]:
    """One PySR run. Returns the whole Pareto front as scored candidates."""
    from pysr import PySRRegressor

    with tempfile.TemporaryDirectory() as td:
        model = PySRRegressor(random_state=seed, output_directory=td,
                              run_id=f"s{seed}", **PYSR_CONFIG)
        model.fit(Xtr, ytr, weights=wtr, variable_names=list(variables))
        eqs = model.equations_
        if isinstance(eqs, list):
            eqs = eqs[0]
        rows = [] if eqs is None else list(eqs.itertuples())

    out: list[Candidate] = []
    for r in rows:
        raw = str(getattr(r, "equation"))
        try:
            expr = grammar.parse(raw, variables)
        except Exception:
            continue
        cx = grammar.complexity(expr)
        if cx > grammar.MAX_COMPLEXITY:
            continue
        tr_r2, _, _ = score_candidate(expr, variables, Xtr, ytr, wtr)
        va_r2, frac, usable = score_candidate(expr, variables, Xva, yva, wva)
        out.append(Candidate(
            expr_str=raw, expr=expr, complexity=cx,
            support=grammar.variable_support(expr, variables),
            engine="pysr", seed=seed, train_r2=tr_r2, valid_r2=va_r2,
            invalid_fraction=frac, valid=usable,
            meta={"engine_complexity": int(getattr(r, "complexity", cx))}))
    return out


# --------------------------------------------------------------------------
# gplearn comparison arm
# --------------------------------------------------------------------------
_GPLEARN_TO_SYMPY = {
    "add": "({} + {})", "sub": "({} - {})", "mul": "({}*{})",
    "div": "({}/{})", "sqrt": "sqrt({})", "log": "log({})", "inv": "inv({})",
    "neg": "(-{})",
}


def _gplearn_to_str(program, variables: list[str]) -> str:
    """Render a gplearn program as an infix string sympy can parse."""
    def walk(idx: int) -> tuple[str, int]:
        node = program.program[idx]
        if isinstance(node, int):
            return variables[node], idx + 1
        if isinstance(node, float):
            return repr(node), idx + 1
        tmpl = _GPLEARN_TO_SYMPY[node.name]
        i = idx + 1
        args = []
        for _ in range(node.arity):
            a, i = walk(i)
            args.append(a)
        return tmpl.format(*args), i
    return walk(0)[0]


def run_gplearn(Xtr: np.ndarray, ytr: np.ndarray, wtr: np.ndarray,
                Xva: np.ndarray, yva: np.ndarray, wva: np.ndarray,
                variables: list[str], seed: int) -> list[Candidate]:
    from gplearn.genetic import SymbolicRegressor

    m = SymbolicRegressor(random_state=seed, **GPLEARN_CONFIG)
    m.fit(Xtr, ytr, sample_weight=wtr)
    raw = _gplearn_to_str(m._program, list(variables))
    try:
        expr = grammar.parse(raw, variables)
    except Exception:
        return []
    cx = grammar.complexity(expr)
    tr_r2, _, _ = score_candidate(expr, variables, Xtr, ytr, wtr)
    va_r2, frac, usable = score_candidate(expr, variables, Xva, yva, wva)
    return [Candidate(expr_str=raw, expr=expr, complexity=cx,
                      support=grammar.variable_support(expr, variables),
                      engine="gplearn", seed=seed, train_r2=tr_r2,
                      valid_r2=va_r2, invalid_fraction=frac,
                      valid=usable and cx <= grammar.MAX_COMPLEXITY)]


def cap_threads() -> None:
    """Numerical-library threading must be pinned before numpy is imported by a
    worker; the runner calls this at process entry."""
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[v] = "1"
