"""Engine validation for the objective-validation study.

Re-verifies, on this machine and at this commit, that the engine does what the
protocol assumes: versions, determinism at the settings every governed run uses,
the complexity metric, protected numerics, checkpointability, and a smoke test on
a known equation. It additionally checks the two things that are NEW here — the
Type 2 signature's agreement with the frozen evaluator, and the mass-block
exponent's invariance to which size proxy an expression is written on.

**Successful installation is not scientific validation** and nothing here claims
otherwise.

Writes `artifacts/ov_engine_validation.json`.
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

import numpy as np                                          # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"


def versions() -> dict:
    import gplearn, pysr, sklearn, scipy, sympy             # noqa: E401
    import pandas as pd
    out = {"python": platform.python_version(),
           "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
           "cpu_count": os.cpu_count(), "pysr": pysr.__version__,
           "gplearn": gplearn.__version__, "sympy": sympy.__version__,
           "numpy": np.__version__, "pandas": pd.__version__,
           "scikit_learn": sklearn.__version__, "scipy": scipy.__version__}
    try:
        from juliacall import Main as jl
        out["julia"] = str(jl.seval("string(VERSION)"))
        out["SymbolicRegression_jl"] = str(jl.seval(
            'string(pkgversion(Base.loaded_modules[Base.PkgId('
            'Base.UUID("8254be44-1295-4e6a-a16d-46603ac705cb"), '
            '"SymbolicRegression")]))'))
    except Exception as e:
        out["julia"] = f"unavailable: {type(e).__name__}"
    return out


def smoke_and_determinism() -> dict:
    from muru.discovery import engine, equivalence, grammar
    import sympy as sp
    rng = np.random.default_rng(4)
    X = rng.uniform(0.3, 1.7, size=(240, 2))
    y = 1.5 * X[:, 0] + 0.5 * X[:, 1] ** 2
    w = np.ones(len(y))
    V = ["x0", "x1"]
    seed = 1_700_000_000

    t = time.time()
    front = engine.run_pysr(X[:180], y[:180], w[:180], X[180:], y[180:],
                            w[180:], V, seed)
    wall = time.time() - t
    again = engine.run_pysr(X[:180], y[:180], w[:180], X[180:], y[180:],
                            w[180:], V, seed)
    other = engine.run_pysr(X[:180], y[:180], w[:180], X[180:], y[180:],
                            w[180:], V, seed + 1)

    planted = sp.sympify("1.5*x0 + 0.5*x1**2")
    D = equivalence.latin_hypercube(equivalence.domain_bounds(X, V), V,
                                    2000, seed=3)
    best, hit = None, False
    for c in front:
        eq = equivalence.equivalence(c.expr, planted, V, D)
        if eq["functionally_equivalent"]:
            hit = True
            if best is None or c.complexity < best[1]:
                best = (c.expr_str, c.complexity, eq["exact_equivalent"])
    return {
        "planted": "1.5*x0 + 0.5*x1**2",
        "front_size": len(front), "wall_s": wall,
        "recovered": hit,
        "recovered_expression": None if best is None else best[0],
        "recovered_complexity": None if best is None else best[1],
        "symbolically_equivalent": None if best is None else best[2],
        "best_valid_r2": max((c.valid_r2 for c in front), default=float("nan")),
        "identical_front_at_same_seed":
            [c.expr_str for c in front] == [c.expr_str for c in again],
        "different_front_at_different_seed":
            [c.expr_str for c in front] != [c.expr_str for c in other],
        "settings": {"deterministic": True, "parallelism": "serial"},
    }


def type2_checks() -> dict:
    """The two properties this study adds on top of Phase 3's engine checks."""
    import sympy as sp
    from muru.discovery import grammar
    from muru.objval import signature
    V = list(__import__("muru.discovery.protocol", fromlist=["FEATURES"]).FEATURES)
    Z = np.random.default_rng(5).uniform(0.25, 1.75, size=(1500, len(V)))

    e = sp.sympify("sqrt(precursor_mz*(heteroatom_fraction + 0.8))")
    v1, o1 = signature._eval(e, V, Z)
    v2, o2 = grammar.evaluate(e, V, Z)
    agree = bool(np.array_equal(o1, o2) and np.allclose(v1[o1], v2[o2],
                                                        rtol=0, atol=0))

    proxies = {p: signature.mass_exponent(
        signature.signature(sp.sympify(f"sqrt({p})"), V, Z))
        for p in ("precursor_mz", "total_atom_count", "rdbe")}

    worked = {s: grammar.complexity(sp.sympify(s))
              for s in ("a", "a + b", "sqrt(a)", "a**2", "sqrt(a*b)",
                        "a*b + 1.0")}
    bad = {}
    for s in ("1/(a-a)", "log(a-b)"):
        val, ok = grammar.evaluate(sp.sympify(s), ["a", "b"],
                                  np.tile(np.array([[0.5, 0.9]]), (10, 1)))
        bad[s] = {"invalid_fraction": float(1 - ok.mean())}

    return {"compiled_evaluator_matches_frozen_evaluator": agree,
            "mass_block_exponent_by_proxy": proxies,
            "mass_block_exponent_is_proxy_invariant":
                bool(max(proxies.values()) - min(proxies.values()) < 1e-3),
            "complexity_worked_examples": worked,
            "protected_numerics": bad,
            "protected_semantics": grammar.PROTECTED_SEMANTICS}


def checkpointability() -> dict:
    import tempfile
    from muru.discovery.checkpoint import Store
    from muru.objval.plan2 import seed_list2
    with tempfile.TemporaryDirectory() as td:
        st = Store(Path(td))
        seeds = seed_list2("OV|G1B|r000|moderate")
        for s in seeds[:5]:
            st.write("G1B", "OV|G1B|r000|moderate", s, {"seed": s})
        skips = st.pending("G1B", "OV|G1B|r000|moderate", seeds) == seeds[5:]
        p = st.path("G1B", "OV|G1B|r000|moderate", seeds[0])
        p.write_text('{"seed":')
        truncated = not st.done("G1B", "OV|G1B|r000|moderate", seeds[0])
    return {"unit": "(block, world, seed)", "resume_skips_completed": bool(skips),
            "truncated_file_counts_as_incomplete": bool(truncated),
            "write": "tmp file then os.replace"}


def main() -> int:
    out = {"purpose": ("engine validation for the objective-alignment "
                       "validation study; installation is not validation"),
           "versions": versions(),
           "smoke_test": smoke_and_determinism(),
           "type2_checks": type2_checks(),
           "checkpointability": checkpointability()}
    (ART / "ov_engine_validation.json").write_text(json.dumps(out, indent=1,
                                                              default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "type2_checks"},
                     indent=1, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
