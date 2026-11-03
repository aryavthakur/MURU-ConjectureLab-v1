"""E2: the downstream, truth-joined scoring pass.

Everything here consumes a `WorldTruth` (`e2_worlds.WorldTruth`) and a
already-searched `FrontRow` (`e2_search.FrontRow`). Nothing in this module is
ever called from `e2_search.py`, and no function in `e2_search.py` or
`e2_classify.py` accepts a `WorldTruth` argument -- the search-time /
truth-joined boundary `rc3_acceptance`/`g2_contract` maintain in production is
preserved by the two modules' non-overlapping call graphs, not merely by
convention.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from muru.discovery.equivalence import algebraically_equivalent
from muru.paper_benchmark.g2_contract import (
    FamilyStatus,
    G2Event,
    SupportStatus,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
)
from muru.paper_benchmark.rc5_selection import parse_production_candidate

from . import e2_classify
from .e2_search import FrontRow
from .e2_worlds import WorldTruth

__all__ = ["ScoredRow", "score_row", "truth_expression_symbols"]


@dataclass(frozen=True)
class ScoredRow:
    front: FrontRow
    discovered_family: Optional[str]
    truth_family: str
    truth_support: frozenset[str]
    coefficient_regime: str
    support_status_vs_truth: str
    family_status_vs_truth: str
    g2_correct: bool
    g2_event: str
    truth_equivalent: Optional[bool]   # algebraic equivalence to the planted law, up to positive scale; None = undetermined


_TRUTH_EXPR_CACHE: dict[str, object] = {}


def _parse_truth(law_string: str):
    cached = _TRUTH_EXPR_CACHE.get(law_string)
    if cached is not None:
        return cached
    from muru.paper_benchmark.g2_contract import _safe_parse

    parsed = _safe_parse(law_string)
    _TRUTH_EXPR_CACHE[law_string] = parsed
    return parsed


def truth_expression_symbols():  # pragma: no cover - documentation helper
    """Both the candidate and the truth law are parsed through
    `g2_contract`'s own symbol table (`_safe_parse` / `parse_production_candidate`,
    which alias PySR's `x{i}` naming onto the SAME Symbol objects
    `_safe_parse` uses), so an algebraic-equivalence comparison between them
    is never confounded by two different Symbol instances sharing a name."""


def score_row(front: FrontRow, truth: WorldTruth) -> ScoredRow:
    classification = e2_classify.classify_expression(front.expression_string)
    discovered_family = classification.discovered_family

    effective_support = (
        frozenset(classification.effective_support) if classification.effective_support is not None else None
    )
    support_status = classify_support(effective_support, truth.support)
    family_status = classify_family_match(discovered_family, truth.family)
    event = evaluate_g2_event(support_status, family_status)
    g2_correct = event == G2Event.SUCCESS

    truth_equivalent: Optional[bool] = None
    if front.parse_ok and classification.canonicalization_status == "OK":
        try:
            candidate_expr = parse_production_candidate(front.expression_string)
            truth_expr = _parse_truth(truth.law_string)
            if truth_expr is not None:
                truth_equivalent = algebraically_equivalent(candidate_expr, truth_expr)
        except Exception:
            truth_equivalent = None

    return ScoredRow(
        front=front,
        discovered_family=discovered_family,
        truth_family=truth.family,
        truth_support=truth.support,
        coefficient_regime=truth.regime,
        support_status_vs_truth=support_status.value,
        family_status_vs_truth=family_status.value,
        g2_correct=g2_correct,
        g2_event=event.value,
        truth_equivalent=truth_equivalent,
    )
