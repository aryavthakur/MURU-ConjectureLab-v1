"""Amendment A3.1: G2 structural-family endpoint contract.

G2 asks whether the best accepted expression has:
  - correct effective structural support, AND
  - correct mathematical family.

This module is the REFERENCE CONTRACT implementation.  It does not integrate
into the production execution path; Engineering RC3 does that.

Scope:
  - effective-support extraction from symbolic expressions
  - truth-family taxonomy preservation
  - discovered-side family classification (structural, coefficient-agnostic)
  - G2 event evaluation

This module NEVER reads planted truth during acceptance.  It reads truth
only for post-hoc G2 scoring, which is separated from the acceptance
predicate by design.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Sequence

import sympy
from sympy import Symbol, simplify, symbols, sympify

# -----------------------------------------------------------------------
# Truth family taxonomy - frozen
# -----------------------------------------------------------------------

TRUTH_FAMILIES: frozenset[str] = frozenset({
    "mass_affine_descriptor",
    "mass_power",
    "mass_saturating_descriptor",
    "mass_interaction",
    "mass_exponential_descriptor",
})

# -----------------------------------------------------------------------
# Protected grammar primitives
# -----------------------------------------------------------------------

GRAMMAR_PRIMITIVES: tuple[str, ...] = (
    "mass",
    "descriptor",
    "descriptor2",
    "distractor",
    "correlated_distractor",
)

_PRIMITIVE_SYMBOLS: dict[str, Symbol] = {
    name: symbols(name) for name in GRAMMAR_PRIMITIVES
}


class SupportStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    SUPPORT_UNRESOLVED = "SUPPORT_UNRESOLVED"


class FamilyStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    FAMILY_AMBIGUOUS = "FAMILY_AMBIGUOUS"
    FAMILY_UNRESOLVED = "FAMILY_UNRESOLVED"


class G2Event(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNEVALUABLE = "UNEVALUABLE"


# -----------------------------------------------------------------------
# Effective support extraction
# -----------------------------------------------------------------------

def _safe_parse(expr_str: str) -> sympy.Expr | None:
    """Parse under protected grammar.  Returns None on failure."""
    try:
        local_dict = dict(_PRIMITIVE_SYMBOLS)
        parsed = sympify(expr_str, locals=local_dict)
        if parsed is None or not isinstance(parsed, sympy.Basic):
            return None
        return parsed
    except (sympy.SympifyError, SyntaxError, TypeError, ValueError):
        return None


def extract_effective_support(expr_str: str) -> frozenset[str] | None:
    """Extract the effective structural support of a symbolic expression.

    Returns a frozenset of primitive variable names, or None if the
    expression cannot be resolved deterministically (SUPPORT_UNRESOLVED).

    Rules (from the resolved Phase A contract):
    - parse under protected grammar
    - deterministic algebraic normalization/simplification
    - cancelled variables do not count
    - exact-zero terms do not count
    - constants contribute no support
    - duplicated primitive variables count once
    - nested transforms preserve primitive dependence
    - interactions contribute every primitive input
    - correlated proxy variables remain distinct variables
    - F12 proxy (correlated_distractor) is NOT interchangeable with
      the planted descriptor
    - no new magnitude threshold may be invented
    """
    parsed = _safe_parse(expr_str)
    if parsed is None:
        return None

    try:
        simplified = simplify(parsed)
    except Exception:
        return None

    if simplified.is_number:
        return frozenset()

    free = simplified.free_symbols
    support = frozenset(
        name for name, sym in _PRIMITIVE_SYMBOLS.items()
        if sym in free
    )
    return support


def classify_support(
    discovered_support: frozenset[str] | None,
    truth_support: frozenset[str],
) -> SupportStatus:
    """Compare discovered effective support against truth support."""
    if discovered_support is None:
        return SupportStatus.SUPPORT_UNRESOLVED
    if discovered_support == truth_support:
        return SupportStatus.MATCH
    return SupportStatus.MISMATCH


# -----------------------------------------------------------------------
# Discovered-side family classification
# -----------------------------------------------------------------------

def classify_discovered_family(expr_str: str) -> str | None:
    """Classify a discovered expression into the truth family taxonomy.

    Classification is structural and coefficient-agnostic: it examines the
    skeleton of the expression (which primitives appear, what operations
    combine them) rather than coefficient values.

    Algebraic reorderings must classify identically.

    Returns one of the TRUTH_FAMILIES strings, or None if unclassifiable.
    Returns "FAMILY_AMBIGUOUS" for degenerate exact family intersection.
    """
    parsed = _safe_parse(expr_str)
    if parsed is None:
        return None

    try:
        simplified = simplify(parsed)
    except Exception:
        return None

    if simplified.is_number:
        return None

    free = simplified.free_symbols
    support = frozenset(
        name for name, sym in _PRIMITIVE_SYMBOLS.items()
        if sym in free
    )

    if not support:
        return None

    mass_sym = _PRIMITIVE_SYMBOLS["mass"]
    desc_sym = _PRIMITIVE_SYMBOLS["descriptor"]
    desc2_sym = _PRIMITIVE_SYMBOLS["descriptor2"]

    has_mass = "mass" in support
    has_descriptor = "descriptor" in support
    has_descriptor2 = "descriptor2" in support

    if not has_mass:
        return None

    # mass_power: only mass in support
    if support == {"mass"}:
        return "mass_power"

    # mass_interaction: mass and both descriptors (interaction term)
    if has_mass and has_descriptor and has_descriptor2:
        if _contains_product(simplified, desc_sym, desc2_sym):
            return "mass_interaction"

    # For mass+descriptor (no descriptor2), collect all matching families.
    # If more than one matches, return FAMILY_AMBIGUOUS.
    if has_mass and has_descriptor and not has_descriptor2:
        candidates: list[str] = []

        if _contains_exp_of(simplified, desc_sym):
            candidates.append("mass_exponential_descriptor")

        if _contains_saturating(simplified, desc_sym):
            candidates.append("mass_saturating_descriptor")

        if _is_linear_in(simplified, desc_sym):
            candidates.append("mass_affine_descriptor")

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            return "FAMILY_AMBIGUOUS"

        # Fallback classification
        return _fallback_classify(simplified, desc_sym)

    return None


def _contains_product(expr: sympy.Expr, sym1: Symbol, sym2: Symbol) -> bool:
    """Check if expression contains a product of two symbols."""
    try:
        d2 = sympy.diff(sympy.diff(expr, sym1), sym2)
        return d2 != 0
    except Exception:
        return False


def _contains_exp_of(expr: sympy.Expr, sym: Symbol) -> bool:
    """Check if expression contains exp(f(sym)) where f depends on sym."""
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.exp):
            if sym in sub.free_symbols:
                return True
    return False


def _contains_saturating(expr: sympy.Expr, sym: Symbol) -> bool:
    """Check if expression contains sym/(c + sym) or equivalent saturation."""
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.Mul):
            # Look for 1/(1 + sym) pattern in factors
            for factor in sub.args:
                if isinstance(factor, sympy.Pow) and factor.exp == -1:
                    base = factor.base
                    if sym in base.free_symbols:
                        # Check if base is of form (c + sym) or (c + c*sym)
                        try:
                            coeff = base.coeff(sym)
                            if coeff != 0:
                                return True
                        except Exception:
                            pass
        if isinstance(sub, sympy.Pow) and sub.exp == -1:
            base = sub.base
            if sym in base.free_symbols:
                try:
                    coeff = base.coeff(sym)
                    if coeff != 0:
                        remainder = base - coeff * sym
                        if remainder.is_number and remainder != 0:
                            return True
                except Exception:
                    pass
    return False


def _is_linear_in(expr: sympy.Expr, sym: Symbol) -> bool:
    """Check if expression is linear (affine) in sym."""
    try:
        d1 = sympy.diff(expr, sym)
        d2 = sympy.diff(d1, sym)
        return d2 == 0 and d1 != 0
    except Exception:
        return False


def _fallback_classify(expr: sympy.Expr, desc_sym: Symbol) -> str | None:
    """Attempt classification when primary heuristics fail."""
    try:
        d1 = sympy.diff(expr, desc_sym)
        if d1 == 0:
            return None
        d2 = sympy.diff(d1, desc_sym)
        if d2 == 0:
            return "mass_affine_descriptor"
    except Exception:
        pass
    return None


# -----------------------------------------------------------------------
# G2 event evaluation
# -----------------------------------------------------------------------

def evaluate_g2_event(
    support_status: SupportStatus,
    family_status: FamilyStatus,
) -> G2Event:
    """Evaluate the G2 event for one case.

    G2 success requires:
      support_status == MATCH AND family_status == MATCH

    Unresolved support or family produces UNEVALUABLE.
    """
    if support_status == SupportStatus.SUPPORT_UNRESOLVED:
        return G2Event.UNEVALUABLE
    if family_status in (FamilyStatus.FAMILY_UNRESOLVED, FamilyStatus.FAMILY_AMBIGUOUS):
        return G2Event.UNEVALUABLE

    if (
        support_status == SupportStatus.MATCH
        and family_status == FamilyStatus.MATCH
    ):
        return G2Event.SUCCESS

    return G2Event.FAILURE


def classify_family_match(
    discovered_family: str | None,
    truth_family: str | None,
) -> FamilyStatus:
    """Compare discovered family against truth family.

    Truth family may be None for cases where no family truth is defined.
    """
    if truth_family is None or truth_family not in TRUTH_FAMILIES:
        return FamilyStatus.FAMILY_UNRESOLVED

    if discovered_family is None:
        return FamilyStatus.FAMILY_UNRESOLVED

    if discovered_family == "FAMILY_AMBIGUOUS":
        return FamilyStatus.FAMILY_AMBIGUOUS

    if discovered_family == truth_family:
        return FamilyStatus.MATCH

    return FamilyStatus.MISMATCH


def wilson_lower_95(successes: int, total: int) -> float:
    """Lower bound of 95% Wilson score interval."""
    if total == 0:
        return 0.0
    z = 1.96
    p_hat = successes / total
    denominator = 1 + z * z / total
    centre = p_hat + z * z / (2 * total)
    spread = z * (p_hat * (1 - p_hat) / total + z * z / (4 * total * total)) ** 0.5
    return (centre - spread) / denominator


def wilson_upper_95(successes: int, total: int) -> float:
    """Upper bound of 95% Wilson score interval."""
    if total == 0:
        return 1.0
    z = 1.96
    p_hat = successes / total
    denominator = 1 + z * z / total
    centre = p_hat + z * z / (2 * total)
    spread = z * (p_hat * (1 - p_hat) / total + z * z / (4 * total * total)) ** 0.5
    return (centre + spread) / denominator


# G2 frozen parameters
G2_HELD_OUT_DENOMINATOR = 144
G2_WILSON_LOWER_GATE = 0.70
