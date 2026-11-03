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

from .truth import TruthRecord

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

# Frozen unary-operator numeric semantics, reproduced verbatim from the
# sibling frozen module src/muru/discovery/grammar.py::_SYMPY_LOCALS
# (square=x**2, cube=x**3, inv=1/x). sympy's default sympify namespace already
# resolves "sqrt" and "log" as builtin functions, so only these three need
# explicit binding; without them sympify treats "square"/"cube"/"inv" as
# opaque undefined functions, which blocks the algebraic cancellation and
# reordering-invariance rules below from ever firing.
_UNARY_LOCALS: dict[str, object] = {
    "square": lambda x: x**2,
    "cube": lambda x: x**3,
    "inv": lambda x: 1 / x,
}

# Deterministic PySR-default-naming alias: x{i} maps positionally to
# GRAMMAR_PRIMITIVES[i], the same covariate order already frozen as the
# design-matrix column order for calibration worlds and the ceiling
# estimator (rc3_calibration_worlds.py::CALIBRATION_COVARIATE_ORDER,
# rc3_ceiling.py::CEILING_COVARIATE_ORDER, both literally `= GRAMMAR_PRIMITIVES`).
# Aliasing "x{i}" to the *same* Symbol object as GRAMMAR_PRIMITIVES[i] (rather
# than a separate symbol) makes every downstream free-symbol check treat them
# identically for free.
_FEATURE_NAME_ALIASES: dict[str, Symbol] = {
    f"x{index}": _PRIMITIVE_SYMBOLS[name] for index, name in enumerate(GRAMMAR_PRIMITIVES)
}

_KNOWN_SYMBOLS: frozenset[Symbol] = frozenset(_PRIMITIVE_SYMBOLS.values())


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
        local_dict: dict[str, object] = {**_PRIMITIVE_SYMBOLS, **_UNARY_LOCALS, **_FEATURE_NAME_ALIASES}
        parsed = sympify(expr_str, locals=local_dict)
        if parsed is None or not isinstance(parsed, sympy.Basic):
            return None
        return parsed
    except (sympy.SympifyError, SyntaxError, TypeError, ValueError):
        return None


def _resolved_support(simplified: sympy.Expr) -> frozenset[str] | None:
    """Effective support of an already-simplified expression, or None
    (fail closed) if it references any symbol outside the protected grammar
    primitives and their x{i} aliases.  A symbol reaching this point that is
    not in ``_KNOWN_SYMBOLS`` was never bound in ``_safe_parse``'s locals, so
    sympify auto-created it as an unmapped identifier: it must not be
    silently reported as absent from support."""
    free = simplified.free_symbols
    if not free <= _KNOWN_SYMBOLS:
        return None
    return frozenset(
        name for name, sym in _PRIMITIVE_SYMBOLS.items()
        if sym in free
    )


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

    return _resolved_support(simplified)


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

    support = _resolved_support(simplified)

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
# Truth-side support production (R4 repair: DEFECT_D)
#
# classify_support(discovered_support, truth_support) has always required a
# truth_support operand; nothing in the repository produced one. The single
# source of truth is generator.py::_law's active_variables, already written
# for every case. This module only maps its block labels onto
# GRAMMAR_PRIMITIVES names -- it invents no new label.
# -----------------------------------------------------------------------

# generator.py's single interaction-law branch returns, in the same call,
# both the law string "... * descriptor * descriptor2 ..." and
# active_variables=["mass", "interaction_left", "interaction_right"]. The
# block labels are therefore forced 1:1, in the order they already appear in
# that one call, onto descriptor/descriptor2 -- a mechanical reading of
# existing frozen source, not a new naming choice.
_BLOCK_LABEL_TO_PRIMITIVE: dict[str, str] = {
    "interaction_left": "descriptor",
    "interaction_right": "descriptor2",
}


def truth_support_for_case(truth: TruthRecord) -> frozenset[str]:
    """Mechanically derive G2 truth support from a case's ``TruthRecord``.

    Defined only for G2-applicable families -- ``TruthRecord.
    symbolic_truth_kind == "defined"``, the frozen per-variant metadata
    (registry.py's ``VariantSpec.symbolic_truth_kind``, already carried onto
    every generated ``TruthRecord`` by generator.py) that distinguishes the
    12 family_recovery-endpoint families (F01-F05, F08-F12, F17, F18) from
    every other family. Reading it directly off the record -- rather than
    importing registry.py here to re-resolve it -- keeps this module's A3.4
    sealed-boundary import closure unchanged (scripts/pb_35_a3_4_integrity.py
    statically forbids any registry/generator/partition reference reachable
    from the a34_*.py secondary-scorer roots, which import this module).
    Callers must not invoke this for a case outside that set; it raises
    rather than returning an arbitrary label, mirroring
    rc3_acceptance.py's truth-blind-by-design boundary for the acceptance
    predicate itself.
    """
    if truth.symbolic_truth_kind != "defined":
        raise ValueError(
            f"case {truth.case_id!r} (variant {truth.variant!r}, symbolic_truth_kind="
            f"{truth.symbolic_truth_kind!r}) is not G2-applicable; truth support is undefined"
        )
    if truth.mathematical_family not in TRUTH_FAMILIES:
        raise ValueError(
            f"case {truth.case_id!r} has no recognized truth family {truth.mathematical_family!r}"
        )

    mapped: set[str] = set()
    for label in truth.active_variables:
        if label in GRAMMAR_PRIMITIVES:
            mapped.add(label)
        elif label in _BLOCK_LABEL_TO_PRIMITIVE:
            mapped.add(_BLOCK_LABEL_TO_PRIMITIVE[label])
        else:
            raise ValueError(
                f"case {truth.case_id!r} has unmapped active_variable block label {label!r}"
            )
    return frozenset(mapped)


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
