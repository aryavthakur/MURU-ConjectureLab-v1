"""Shared, memoized, truth-blind expression classification for E2.

One `sympy.simplify` per distinct expression string, exactly the cost
mitigation `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.10 pre-declares:
"memoise by expression string ... apply a per-expression wall-clock cap with
the timeout recorded as an explicit SIMPLIFY_TIMEOUT status rather than
silently becoming None". `effective_support` (search-time,
`front_record_fields`) and `discovered_family` (downstream,
`scoring_pass_fields`) both consume the same cached simplified form so the
two-pass field split the design doc specifies costs nothing extra to compute.

Every function here is truth-blind: none reads a `WorldTruth`. Truth is
joined only in `e2_scoring.py`.
"""
from __future__ import annotations

import signal
from dataclasses import dataclass
from typing import Optional

import sympy

from muru.discovery import grammar as discovery_grammar
from muru.paper_benchmark.g2_contract import (
    _safe_parse,
    classify_discovered_family,
    extract_effective_support,
)
from muru.paper_benchmark.identity_contract import template_key, template_key_string
from muru.paper_benchmark.rc5_selection import coefficient_vector, parse_production_candidate

__all__ = [
    "SIMPLIFY_TIMEOUT_SECONDS",
    "ClassificationResult",
    "classify_expression",
]

#: Per-expression wall-clock cap. Generous relative to the ~tens-of-ms typical
#: cost at maxsize=20; exists only to convert a pathological sympy blow-up
#: into an explicit, distinguishable status instead of a hang.
SIMPLIFY_TIMEOUT_SECONDS = 5


class _SimplifyTimeout(Exception):
    pass


def _alarm_handler(signum, frame):  # pragma: no cover - exercised via signal
    raise _SimplifyTimeout()


@dataclass(frozen=True)
class ClassificationResult:
    expression_string: str
    parse_ok: bool
    canonicalization_status: str          # OK | UNPARSEABLE | SIMPLIFY_TIMEOUT | TEMPLATE_KEY_FAILED
    canonical_expression: Optional[str]   # str(sympy.simplify(parsed)), or None
    effective_support: Optional[frozenset[str]]
    discovered_family: Optional[str]
    template_key_value: Optional[tuple]
    template_key_repr: Optional[str]
    coefficient_estimates: Optional[tuple[float, ...]]
    grammar_parse_ok: bool                # secondary check via discovery.grammar.parse


_CACHE: dict[str, ClassificationResult] = {}


def _with_timeout(fn, *args):
    """Run fn(*args) under a SIGALRM wall-clock cap. Main-thread only, POSIX
    only -- true of every worker process this experiment runs in. Falls back
    to no timeout if SIGALRM is unavailable (defensive; not expected here)."""
    if not hasattr(signal, "SIGALRM"):
        return fn(*args)
    previous = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(SIMPLIFY_TIMEOUT_SECONDS)
    try:
        return fn(*args)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def classify_expression(expression_string: str) -> ClassificationResult:
    """Truth-blind classification of one as-emitted expression string,
    memoized process-locally by exact string (fronts repeat heavily across
    seeds within a world, per the design doc's own observation)."""
    cached = _CACHE.get(expression_string)
    if cached is not None:
        return cached

    # Secondary, independent parse check via discovery.grammar (the search's
    # own protected-semantics parser), reported but not load-bearing for
    # classification -- g2_contract._safe_parse is the classification parser
    # of record (rc5_selection.parse_production_candidate's docstring).
    try:
        discovery_grammar.parse(expression_string, list(discovery_grammar_variables()))
        grammar_parse_ok = True
    except Exception:
        grammar_parse_ok = False

    parsed = _safe_parse(expression_string)
    if parsed is None:
        result = ClassificationResult(
            expression_string=expression_string, parse_ok=False,
            canonicalization_status="UNPARSEABLE", canonical_expression=None,
            effective_support=None, discovered_family=None,
            template_key_value=None, template_key_repr=None,
            coefficient_estimates=None, grammar_parse_ok=grammar_parse_ok,
        )
        _CACHE[expression_string] = result
        return result

    try:
        simplified = _with_timeout(sympy.simplify, parsed)
        canonicalization_status = "OK"
    except _SimplifyTimeout:
        simplified = None
        canonicalization_status = "SIMPLIFY_TIMEOUT"
    except Exception:
        simplified = None
        canonicalization_status = "UNPARSEABLE"

    effective_support = extract_effective_support(expression_string) if canonicalization_status == "OK" else None
    discovered_family = classify_discovered_family(expression_string) if canonicalization_status == "OK" else None
    canonical_expression = str(simplified) if simplified is not None else None

    template_key_value: Optional[tuple] = None
    template_key_repr: Optional[str] = None
    try:
        production_parsed = parse_production_candidate(expression_string)
        template_key_value = template_key(production_parsed)
        template_key_repr = template_key_string(production_parsed)
    except Exception:
        if canonicalization_status == "OK":
            canonicalization_status = "TEMPLATE_KEY_FAILED"

    coefficient_estimates = coefficient_vector(expression_string)

    result = ClassificationResult(
        expression_string=expression_string, parse_ok=True,
        canonicalization_status=canonicalization_status,
        canonical_expression=canonical_expression,
        effective_support=effective_support, discovered_family=discovered_family,
        template_key_value=template_key_value, template_key_repr=template_key_repr,
        coefficient_estimates=coefficient_estimates, grammar_parse_ok=grammar_parse_ok,
    )
    _CACHE[expression_string] = result
    return result


def discovery_grammar_variables() -> tuple[str, ...]:
    from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES

    return tuple(f"x{i}" for i in range(len(GRAMMAR_PRIMITIVES)))


def cache_size() -> int:
    return len(_CACHE)
