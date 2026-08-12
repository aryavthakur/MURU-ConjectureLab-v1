"""Type 2 structural signature of a candidate expression.

A Type 2 claim is not a claim about an algebraic string. It is a claim about
*which molecular variables matter, in which direction, and with what scaling*.
This module turns any candidate expression — from any engine — into that
claim-relevant object, so that two syntactically different expressions can be
compared on the thing the claim is actually about.

Every quantity here is invariant to multiplying the candidate by a positive
constant, which is exactly the freedom the collapse model leaves in `g`
(`muru.discovery.estimate`: `g` is identified only up to positive scale).

This module reads data and candidates. It never reads a planted law.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from muru.discovery import grammar

SIGNATURE_VERSION = "ov-signature-1.0.0"

# Relative step for the central log-difference. Small enough to approximate the
# derivative, large enough to stay clear of float cancellation on the protected
# evaluator.
ELASTICITY_STEP = 1e-3

# A variable is in the EFFECTIVE support only if it moves the candidate by more
# than this in elasticity terms. A variable that appears in the string but
# changes the prediction by ~0 is not part of the scientific claim and must not
# be reported as structure.
EFFECTIVE_SUPPORT_MIN_ELASTICITY = 0.02

# Points where the candidate is non-positive cannot carry a scale
# interpretation: `g` is a positive energy scale. A candidate that is
# non-positive on more than this fraction of the domain has no Type 2 signature.
MAX_NONPOSITIVE_FRACTION = 0.05

# A variable whose value is zero on a point admits no multiplicative
# perturbation, so its elasticity is undefined there. `n_S` and `n_halogen` have
# median 0 in the development corpus and are affected; their SIGN is still
# recoverable from the additive partial derivative.
MIN_POSITIVE_VALUE = 1e-9

# --- structural blocks -------------------------------------------------------
# `precursor_mz`, `total_atom_count` and `rdbe` are near-collinear measures of
# molecular size. `muru.discovery.protocol.MASS_BLOCK` already treats them as one
# block that must be ablated together, because "dropping the named mass variable
# alone leaves its proxies in place and understates how much of the effect mass
# carries" (`DESCRIPTORS.md`). The same logic applies to a structural CLAIM: two
# expressions that put the same scaling on two different mass proxies are making
# one empirical claim about molecular size, not two different ones, and this
# corpus cannot distinguish which proxy carries it.
#
# So a Type 2 claim is made at BLOCK level. Variable-level support is computed,
# reported and never discarded — it is simply not what the claim is stated on.
MASS_BLOCK = ("precursor_mz", "total_atom_count", "rdbe")
MASS_BLOCK_NAME = "MASS"


def block_of(v: str) -> str:
    return MASS_BLOCK_NAME if v in MASS_BLOCK else v


def blocks_of(variables) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for v in variables:
        out.setdefault(block_of(v), []).append(v)
    return out


_COMPILED: dict[tuple, object] = {}


def compiled(expr: sp.Expr, variables: list[str]):
    """`sp.lambdify` once per (expression, variable order).

    `grammar.evaluate` lambdifies on every call, which is correct but costs
    milliseconds. The signature needs ~50 evaluations of the same expression, so
    the compile is cached here. The numerical result is identical — the same
    protected mask from `grammar.finite_mask` is applied — and
    `tests/test_ov_signature.py` asserts agreement with `grammar.evaluate`.
    """
    key = (sp.srepr(expr), tuple(variables))
    fn = _COMPILED.get(key)
    if fn is None:
        syms = [sp.Symbol(v) for v in variables]
        try:
            fn = sp.lambdify(syms, expr, modules=["numpy"])
        except Exception:
            fn = False
        if len(_COMPILED) > 20_000:
            _COMPILED.clear()
        _COMPILED[key] = fn
    return fn


def _eval(expr: sp.Expr, variables: list[str], Z: np.ndarray
          ) -> tuple[np.ndarray, np.ndarray]:
    fn = compiled(expr, variables)
    if fn is False:
        return np.zeros(len(Z)), np.zeros(len(Z), dtype=bool)
    with np.errstate(all="ignore"):
        try:
            out = np.asarray(fn(*[Z[:, i] for i in range(Z.shape[1])]), float)
        except Exception:
            return np.zeros(len(Z)), np.zeros(len(Z), dtype=bool)
    if out.ndim == 0:
        out = np.full(len(Z), float(out))
    return out, grammar.finite_mask(out)


def elasticities_from(evalfn, variables: list[str], Z: np.ndarray,
                      step: float = ELASTICITY_STEP) -> dict:
    """Point-wise log-log slope of the candidate in each variable.

        e_j(z) = (d f / d z_j) * z_j / f(z)

    computed by a central multiplicative perturbation. `e_j` is the local
    scaling exponent in `z_j`: for `f = c * m**0.5 * (1 + a*h)` it is exactly
    0.5 in `m` everywhere, for any `c > 0`. That invariance is why the exponent,
    and not the expression, is the reportable quantity.

    Returns the per-variable summary plus the additive partial-derivative sign,
    which stays defined where a variable can be zero.
    """
    f0, ok0 = evalfn(Z)
    positive = ok0 & np.isfinite(f0) & (f0 > MIN_POSITIVE_VALUE)
    out: dict[str, dict] = {}
    for j, v in enumerate(variables):
        zj = Z[:, j]
        Zp, Zm = Z.copy(), Z.copy()
        Zp[:, j] = zj * (1.0 + step)
        Zm[:, j] = zj * (1.0 - step)
        fp, okp = evalfn(Zp)
        fm, okm = evalfn(Zm)

        usable = positive & okp & okm & (zj > MIN_POSITIVE_VALUE)
        if usable.sum() >= 20:
            e = (fp[usable] - fm[usable]) / (2.0 * step * f0[usable])
            e = e[np.isfinite(e)]
        else:
            e = np.array([])

        # additive partial derivative: defined even where z_j == 0, and used for
        # the SIGN of an effect when the elasticity is not available
        Zap, Zam = Z.copy(), Z.copy()
        h_abs = step * max(float(np.nanstd(zj)), 1e-6)
        Zap[:, j] = zj + h_abs
        Zam[:, j] = zj - h_abs
        gp, okgp = evalfn(Zap)
        gm, okgm = evalfn(Zam)
        du = positive & okgp & okgm
        d = ((gp[du] - gm[du]) / (2.0 * h_abs)) if du.sum() >= 20 else np.array([])
        d = d[np.isfinite(d)]

        out[v] = {
            "elasticity_median": float(np.median(e)) if e.size else float("nan"),
            "elasticity_iqr": float(np.subtract(*np.percentile(e, [75, 25])))
            if e.size else float("nan"),
            "elasticity_n": int(e.size),
            "d_median": float(np.median(d)) if d.size else float("nan"),
            "monotone_increasing_fraction": float(np.mean(d > 0)) if d.size else float("nan"),
        }
    # --- block-level elasticity ---------------------------------------------
    # All members of a block are perturbed together, so the exponent measured is
    # the response to a proportional change in molecular size rather than to one
    # arbitrarily chosen proxy. For a law written on any single mass proxy this
    # returns exactly the planted exponent, which is what makes it comparable
    # across engines and across expressions.
    per_block: dict[str, dict] = {}
    for bname, members in blocks_of(variables).items():
        cols = [variables.index(m) for m in members]
        Zp, Zm = Z.copy(), Z.copy()
        for c in cols:
            Zp[:, c] = Z[:, c] * (1.0 + step)
            Zm[:, c] = Z[:, c] * (1.0 - step)
        fp, okp = evalfn(Zp)
        fm, okm = evalfn(Zm)
        anypos = np.any(Z[:, cols] > MIN_POSITIVE_VALUE, axis=1)
        usable = positive & okp & okm & anypos
        if usable.sum() >= 20:
            e = (fp[usable] - fm[usable]) / (2.0 * step * f0[usable])
            e = e[np.isfinite(e)]
        else:
            e = np.array([])
        per_block[bname] = {
            "members": members,
            "elasticity_median": float(np.median(e)) if e.size else float("nan"),
            "elasticity_n": int(e.size),
            "monotone_increasing_fraction": float(np.mean(e > 0)) if e.size else float("nan"),
        }

    return {"per_variable": out, "per_block": per_block,
            "positive_fraction": float(positive.mean()),
            "valid_fraction": float(ok0.mean())}


def _sign(x: float, dead: float) -> int:
    if not np.isfinite(x):
        return 0
    if x > dead:
        return 1
    if x < -dead:
        return -1
    return 0


def signature_from(evalfn, variables: list[str], Z: np.ndarray,
                   symbolic_support: tuple[str, ...] | list[str],
                   min_elasticity: float = EFFECTIVE_SUPPORT_MIN_ELASTICITY) -> dict:
    """The claim-relevant Type 2 signature of any evaluable scale function.

    Used for candidate expressions and — after candidates are frozen — for the
    planted law itself, so the two are described by the *same* procedure and can
    be compared without either side being privileged.

    * `symbolic_support` — variables the expression contains. Reported, never
      used alone: a variable can appear and do nothing.
    * `effective_support` — variables whose |median elasticity| (or, where the
      variable can be zero, whose normalized additive effect) exceeds
      `min_elasticity`. THIS is what a structural claim is made of.
    * `exponents` — median elasticity per effective variable; the mass exponent
      is the quantity the master plan's ±0.15 tolerance applies to.
    * `signs` — direction of each effect.
    * `monotone` — whether the effect keeps one sign across the domain.
    """
    el = elasticities_from(evalfn, variables, Z)
    per = el["per_variable"]
    sym = tuple(symbolic_support)

    scale = {}
    for v in variables:
        zj = Z[:, list(variables).index(v)]
        sd = float(np.nanstd(zj))
        d = per[v]["d_median"]
        # normalized additive effect: how much f moves, in units of f, over one
        # SD of the variable. Comparable to an elasticity and defined at z=0.
        scale[v] = abs(d) * sd if np.isfinite(d) else float("nan")

    f0, ok0 = evalfn(Z)
    fbar = float(np.median(np.abs(f0[ok0]))) if ok0.any() else float("nan")

    effective, exponents, signs, monotone = [], {}, {}, {}
    for v in variables:
        e = per[v]["elasticity_median"]
        norm = scale[v] / fbar if (np.isfinite(scale[v]) and fbar > 0) else float("nan")
        strength = abs(e) if np.isfinite(e) else (norm if np.isfinite(norm) else 0.0)
        if v in sym and strength > min_elasticity:
            effective.append(v)
            exponents[v] = e
            signs[v] = _sign(e if np.isfinite(e) else per[v]["d_median"], 0.0)
            mi = per[v]["monotone_increasing_fraction"]
            monotone[v] = bool(np.isfinite(mi) and (mi > 0.95 or mi < 0.05))

    # --- block level: what the Type 2 claim is actually stated on ------------
    pb = el["per_block"]
    eff_blocks = sorted({block_of(v) for v in effective})
    block_exponents, block_signs, block_monotone = {}, {}, {}
    for b in eff_blocks:
        e = pb[b]["elasticity_median"]
        if not np.isfinite(e):
            # fall back to the sum of the member elasticities that ARE defined
            vals = [exponents[v] for v in effective
                    if block_of(v) == b and np.isfinite(exponents.get(v, np.nan))]
            e = float(np.sum(vals)) if vals else float("nan")
        block_exponents[b] = e
        mi = pb[b]["monotone_increasing_fraction"]
        block_signs[b] = _sign(e, 0.0) if np.isfinite(e) else _sign(
            float(np.mean([signs[v] for v in effective if block_of(v) == b])), 0.0)
        block_monotone[b] = bool(np.isfinite(mi) and (mi > 0.95 or mi < 0.05))

    return {
        "signature_version": SIGNATURE_VERSION,
        "symbolic_support": list(sym),
        "effective_support": effective,
        "exponents": exponents,
        "signs": signs,
        "monotone": monotone,
        "effective_support_blocks": eff_blocks,
        "block_exponents": block_exponents,
        "block_signs": block_signs,
        "block_monotone": block_monotone,
        "positive_fraction": el["positive_fraction"],
        "valid_fraction": el["valid_fraction"],
        "usable": bool(el["positive_fraction"] >= 1.0 - MAX_NONPOSITIVE_FRACTION),
        "per_variable": per,
        "per_block": pb,
    }


def signature(expr: sp.Expr, variables: list[str], Z: np.ndarray,
              min_elasticity: float = EFFECTIVE_SUPPORT_MIN_ELASTICITY) -> dict:
    """Type 2 signature of a candidate expression."""
    return signature_from(lambda Zx: _eval(expr, variables, Zx), variables, Z,
                          grammar.variable_support(expr, variables),
                          min_elasticity)


def mass_exponent(sig: dict) -> float:
    """The scaling exponent the master plan's ±0.15 tolerance is stated on.

    Measured on the mass BLOCK, so it is the same number whether an expression
    writes the size dependence on `precursor_mz`, `total_atom_count` or `rdbe`.
    `nan` when the candidate carries no mass-block dependence at all, which is
    itself a reportable outcome and not a missing value to be filled in.
    """
    return float(sig["block_exponents"].get(MASS_BLOCK_NAME, float("nan")))


def mass_exponent_named(sig: dict, mass_variable: str = "precursor_mz") -> float:
    """Variable-level mass exponent, reported alongside the block-level one."""
    return float(sig["exponents"].get(mass_variable, float("nan")))
