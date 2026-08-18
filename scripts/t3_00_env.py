"""Engine validation: environment, determinism, checkpointability, smoke test.

Master plan 10: verify installation, the Julia runtime, deterministic seeding as
far as the library permits, checkpointability, operator definitions, complexity
scoring, and a trivial smoke test on a known synthetic equation.

Successful installation is not scientific validation and this script does not
claim otherwise. It establishes only that the engine does what the protocol
assumes it does.

Writes `artifacts/p3_engine_validation.json`.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import numpy as np                                        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"


def versions() -> dict:
    import gplearn, pysr, sklearn, scipy, sympy       # noqa: E401
    import pandas as pd
    out = {
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "cpu_count": os.cpu_count(),
        "pysr": pysr.__version__,
        "gplearn": gplearn.__version__,
        "sympy": sympy.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "scipy": scipy.__version__,
    }
    try:
        from juliacall import Main as jl
        out["julia"] = str(jl.seval("string(VERSION)"))
        out["SymbolicRegression_jl"] = str(jl.seval(
            'string(pkgversion(Base.loaded_modules[Base.PkgId('
            'Base.UUID("8254be44-1295-4e6a-a16d-46603ac705cb"), '
            '"SymbolicRegression")]))'))
    except Exception as e:                                  # pragma: no cover
        out["julia"] = f"unavailable: {type(e).__name__}"
    return out


def smoke_test() -> dict:
    """A trivial planted equation the engine must recover.

    y = 1.5*x0 + 0.5*x1^2 on clean data. If this fails, nothing downstream is
    interpretable.
    """
    from muru.discovery import engine, equivalence, grammar

    rng = np.random.default_rng(0)
    V = ["x0", "x1"]
    X = rng.uniform(0.3, 1.9, size=(400, 2))
    y = 1.5 * X[:, 0] + 0.5 * X[:, 1] ** 2
    w = np.ones(len(y))
    tr, va = slice(0, 300), slice(300, 400)

    t0 = time.time()
    cands = engine.run_pysr(X[tr], y[tr], w[tr], X[va], y[va], w[va], V, seed=1)
    dt = time.time() - t0

    truth = grammar.parse("1.5*x0 + 0.5*x1**2", V)
    D = equivalence.latin_hypercube({"x0": (0.3, 1.9), "x1": (0.3, 1.9)}, V,
                                    2000, seed=5)
    best, eq = None, None
    for c in sorted(cands, key=lambda c: c.complexity):
        e = equivalence.equivalence(c.expr, truth, V, D)
        if e["functionally_equivalent"]:
            best, eq = c, e
            break
    return {
        "planted": "1.5*x0 + 0.5*x1**2",
        "n_pareto": len(cands),
        "seconds": round(dt, 2),
        "recovered": best is not None,
        "recovered_expr": best.expr_str if best else None,
        "recovered_complexity": best.complexity if best else None,
        "exact_equivalent": bool(eq["exact_equivalent"]) if eq else False,
        "best_valid_r2": max((c.valid_r2 for c in cands), default=None),
    }


def determinism() -> dict:
    """Two runs at the same seed must agree; different seeds may not."""
    from muru.discovery import engine

    rng = np.random.default_rng(7)
    V = ["x0", "x1"]
    X = rng.uniform(0.3, 1.9, size=(300, 2))
    y = 2.0 * np.sqrt(X[:, 0]) + 0.3 * X[:, 1]
    w = np.ones(len(y))
    tr, va = slice(0, 220), slice(220, 300)

    def front(seed):
        return [(c.expr_str, c.complexity)
                for c in engine.run_pysr(X[tr], y[tr], w[tr], X[va], y[va],
                                         w[va], V, seed=seed)]
    a, b, c = front(11), front(11), front(12)
    return {
        "same_seed_identical": a == b,
        "same_seed_n_equations": len(a),
        "different_seed_differs": a != c,
        "note": ("PySR is run with deterministic=True and parallelism='serial'; "
                 "reproducibility is asserted at that setting, which is the one "
                 "every governed run uses"),
    }


def operator_and_complexity_definitions() -> dict:
    from muru.discovery import grammar
    return {
        "binary_operators": grammar.BINARY_OPERATORS,
        "unary_operators": grammar.UNARY_OPERATORS,
        "excluded": ["exp", "trigonometric functions", "free-exponent ^"],
        "max_complexity": grammar.MAX_COMPLEXITY,
        "nested_constraints": grammar.NESTED_CONSTRAINTS,
        "protected_semantics": grammar.PROTECTED_SEMANTICS,
        "complexity_metric": ("node count over the parsed tree: variable 1, "
                              "constant 1, binary op 1, unary op 1; an integer "
                              "or half-integer power is one unary op over its "
                              "base"),
        "complexity_examples": {
            s: grammar.complexity(grammar.parse(s, ["a", "b"]))
            for s in ("a", "a + b", "sqrt(a)", "a**2", "square(a)",
                      "sqrt(a*b)", "a*b + 1.0")},
    }


def checkpointability() -> dict:
    import tempfile
    from muru.discovery.checkpoint import Store
    with tempfile.TemporaryDirectory() as td:
        s = Store(Path(td))
        s.write("B", "W", 1, {"seed": 1})
        pending_before = s.pending("B", "W", [1, 2, 3])
        s.write("B", "W", 2, {"seed": 2})
        pending_after = s.pending("B", "W", [1, 2, 3])
        p = s.path("B", "W", 9)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"trunc')
        truncated_is_incomplete = not s.done("B", "W", 9)
    return {
        "unit": "(block, world, seed)",
        "resume_skips_completed": pending_before == [2, 3],
        "resume_advances": pending_after == [3],
        "truncated_file_treated_as_incomplete": truncated_is_incomplete,
        "atomic_write": "tmp file then os.replace",
    }


def main() -> int:
    out = {
        "versions": versions(),
        "operators_and_complexity": operator_and_complexity_definitions(),
        "checkpointability": checkpointability(),
        "determinism": determinism(),
        "smoke_test": smoke_test(),
        "disclaimer": ("successful installation is not scientific validation; "
                       "this file records only that the engine behaves as the "
                       "protocol assumes"),
    }
    (ART / "p3_engine_validation.json").write_text(json.dumps(out, indent=1))
    s, d = out["smoke_test"], out["determinism"]
    print(f"[t3_00] PySR {out['versions']['pysr']} julia "
          f"{out['versions'].get('julia')} | smoke recovered={s['recovered']} "
          f"({s['recovered_expr']}) | determinism same_seed={d['same_seed_identical']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
