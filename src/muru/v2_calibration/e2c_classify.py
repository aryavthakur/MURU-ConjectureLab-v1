"""Calibration-surface canonicalisation, under protocol v2 section 25.

This module exists because Stage 1 may NOT use `e2_classify.classify_expression`.
That function enforces `SIMPLIFY_TIMEOUT_SECONDS = 5`, which protocol v2 section 13
`A2` retires as a classification rule, and it contains the defect Gate 1 was
convened to adjudicate (`e2_classify.py:161-162`):

    effective_support = extract_effective_support(s) if canonicalization_status == "OK" else None
    discovered_family = classify_discovered_family(s) if canonicalization_status == "OK" else None

Both callees take `expression_string` and nothing else. Neither consumes the
simplified form. Gating them on whether `sympy.simplify` returned within five
seconds makes two PURE SYNTACTIC properties into functions of host speed, and a
nulled `effective_support` propagates to SUPPORT_UNRESOLVED -> `g2_correct=False`.
Section 25.3 states the correct contract directly: the canonicalisation table's
three values are "each a function of the expression ALONE".

`e2_classify.py` is NOT edited. It is the sealed E2a instrument and altering it
would retroactively change sealed E2a semantics.

Section 25.2, implemented here:

  Tier 1  `TIER1_CPU_SECONDS = 60` of CPU time (`ITIMER_PROF`, so the budget is not
          a function of host load or co-tenancy) per DISTINCT expression. Exceeding
          it yields `UNRESOLVED`, never a label.
  Tier 2  uncapped, for expressions that are unresolved AND decisive.
  The cap exception derives from `BaseException`, DELIBERATELY, so that
  `g2_contract`'s `except Exception: return None` handlers cannot swallow it and
  silently turn a cap into SUPPORT_UNRESOLVED -> not-correct.
"""
from __future__ import annotations

import signal
import time
from dataclasses import dataclass
from typing import Optional

import sympy

from muru.paper_benchmark.g2_contract import (
    _safe_parse, classify_discovered_family, extract_effective_support,
)
from muru.paper_benchmark.identity_contract import (
    parse_candidate as parse_production_candidate, template_key, template_key_string,
)

__all__ = [
    "TIER1_CPU_SECONDS", "CanonicalEntry", "canonicalise", "CanonicalisationTable",
]

TIER1_CPU_SECONDS = 60          # FP-2, DECLARED (12x the retired 5 s), CPU time


class _Cap(BaseException):
    """Derived from BaseException DELIBERATELY (section 25.2).

    `g2_contract` wraps work in `except Exception: return None` in seven places.
    A cap derived from `Exception` would be swallowed there and silently become
    "not-correct" -- the exact behaviour this protocol forbids.
    """


def _cap_handler(signum, frame):    # pragma: no cover - delivered by the kernel
    raise _Cap(f"tier-1 CPU budget of {TIER1_CPU_SECONDS}s exhausted")


class _cpu_budget:
    """CPU-time bound via ITIMER_PROF. `seconds=None` means tier 2: uncapped."""

    def __init__(self, seconds: Optional[float]):
        self.seconds = seconds

    def __enter__(self):
        if self.seconds is None:
            return self
        self._prev = signal.signal(signal.SIGPROF, _cap_handler)
        signal.setitimer(signal.ITIMER_PROF, self.seconds)
        return self

    def __exit__(self, *exc):
        if self.seconds is not None:
            signal.setitimer(signal.ITIMER_PROF, 0)
            signal.signal(signal.SIGPROF, self._prev)
        return False


@dataclass(frozen=True)
class CanonicalEntry:
    """One row of the section 25.3 canonicalisation table.

    `canonicalization_status` is one of
        OK | UNPARSEABLE | TEMPLATE_KEY_FAILED | UNRESOLVED
    `UNRESOLVED` means only "the budget was exhausted"; it is NOT a label and it
    does NOT null `effective_support` or `discovered_family`.
    """

    expression_string: str
    canonicalization_status: str
    canonical_expression: Optional[str]
    effective_support: Optional[tuple[str, ...]]
    discovered_family: Optional[str]
    template_key_repr: Optional[str]
    cpu_seconds: float
    tier: int


def canonicalise(expression_string: str, cpu_budget: Optional[float] = TIER1_CPU_SECONDS,
                 tier: int = 1) -> CanonicalEntry:
    t0 = time.process_time()

    # ---- the two PURE SYNTACTIC properties, computed UNCONDITIONALLY -------
    # This is the section 25.3 contract and the X-3 repair. Neither call reads
    # `simplified`; neither may be gated on a canonicalisation budget.
    try:
        support = extract_effective_support(expression_string)
        effective_support = tuple(sorted(support)) if support is not None else None
    except Exception:
        effective_support = None
    try:
        discovered_family = classify_discovered_family(expression_string)
    except Exception:
        discovered_family = None

    parsed = None
    try:
        parsed = _safe_parse(expression_string)
    except Exception:
        parsed = None
    if parsed is None:
        return CanonicalEntry(expression_string, "UNPARSEABLE", None,
                              effective_support, discovered_family, None,
                              time.process_time() - t0, tier)

    # ---- canonicalisation, under the section 25.2 budget -------------------
    status, canonical = "OK", None
    try:
        with _cpu_budget(cpu_budget):
            canonical = str(sympy.simplify(parsed))
    except _Cap:
        status, canonical = "UNRESOLVED", None
    except (MemoryError, RecursionError):
        status, canonical = "UNRESOLVED", None
    except Exception:
        status, canonical = "UNPARSEABLE", None

    # ---- template key ------------------------------------------------------
    template_repr = None
    try:
        with _cpu_budget(cpu_budget):
            production_parsed = parse_production_candidate(expression_string)
            template_key(production_parsed)
            template_repr = template_key_string(production_parsed)
    except _Cap:
        if status == "OK":
            status = "UNRESOLVED"
    except Exception:
        if status == "OK":
            status = "TEMPLATE_KEY_FAILED"

    return CanonicalEntry(expression_string, status, canonical, effective_support,
                          discovered_family, template_repr,
                          time.process_time() - t0, tier)


class CanonicalisationTable:
    """Memoised expression -> CanonicalEntry, with tier-2 escalation.

    Keyed by expression string alone (section 25.3). `escalate` re-runs a
    previously UNRESOLVED expression with NO cap; it is called only for
    expressions the determinacy bound has shown to be DECISIVE.
    """

    def __init__(self) -> None:
        self._table: dict[str, CanonicalEntry] = {}

    def get(self, expression_string: str) -> CanonicalEntry:
        hit = self._table.get(expression_string)
        if hit is None:
            hit = canonicalise(expression_string, TIER1_CPU_SECONDS, tier=1)
            self._table[expression_string] = hit
        return hit

    def escalate(self, expression_string: str) -> CanonicalEntry:
        entry = canonicalise(expression_string, None, tier=2)   # tier 2: uncapped
        self._table[expression_string] = entry
        return entry

    def unresolved(self) -> list[str]:
        return [e for e, v in self._table.items() if v.canonicalization_status == "UNRESOLVED"]

    def __len__(self) -> int:
        return len(self._table)

    def as_rows(self) -> list[dict]:
        return [{"expression_string": e, "canonicalization_status": v.canonicalization_status,
                 "canonical_expression": v.canonical_expression,
                 "effective_support": list(v.effective_support) if v.effective_support else None,
                 "discovered_family": v.discovered_family,
                 "template_key_repr": v.template_key_repr,
                 "cpu_seconds": round(v.cpu_seconds, 3), "tier": v.tier}
                for e, v in sorted(self._table.items())]
