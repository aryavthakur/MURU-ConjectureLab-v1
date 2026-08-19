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
    """V3-C4 repair (CRITIC_SCIENCE). The v3 version of this function computed
    `extract_effective_support` and `classify_discovered_family` OUTSIDE the CPU
    budget, each wrapped in a bare `except Exception`. Both callees internally call
    `sympy.simplify` themselves (`g2_contract.py:163,207`) -- a SEPARATE, UNBUDGETED
    simplify from the one below -- so a MemoryError/RecursionError inside either one
    was silently swallowed into `None`, and the declared 60s tier-1 budget did not
    bound the dominant cost, since both unprotected calls ran to completion (or
    exhaustion) BEFORE the budget was ever entered.

    FIX: every call that can invoke `simplify` runs inside the SAME `_cpu_budget`
    context, in the SAME try block, with MemoryError/RecursionError/`_Cap` typed
    explicitly ahead of the generic handler -- exactly the discipline
    `e2a_instrument_diagnostic.py`'s `_PAYLOAD` already applies correctly. A
    resource event during EITHER extraction call now produces `UNRESOLVED` with a
    reason, never a silently nulled field next to `canonicalization_status: OK`.
    """
    t0 = time.process_time()

    # _safe_parse is typically cheap (tokenising), but it is not GUARANTEED cheap for
    # a pathological string, and a bare `except Exception` here would swallow a
    # MemoryError/RecursionError into UNPARSEABLE -- the same defect class as the main
    # fix below, just smaller in practice. Typed explicitly for the same reason.
    parsed = None
    try:
        with _cpu_budget(cpu_budget):
            parsed = _safe_parse(expression_string)
    except _Cap:
        return CanonicalEntry(expression_string, "UNRESOLVED", None, None, None, None,
                              time.process_time() - t0, tier)
    except (MemoryError, RecursionError):
        return CanonicalEntry(expression_string, "UNRESOLVED", None, None, None, None,
                              time.process_time() - t0, tier)
    except Exception:
        parsed = None
    if parsed is None:
        return CanonicalEntry(expression_string, "UNPARSEABLE", None, None, None, None,
                              time.process_time() - t0, tier)

    # ---- everything that can touch simplify, under ONE SHARED budget -------
    # FP-2 declares "60s PER DISTINCT EXPRESSION", not per call. Three independent
    # 60s windows would allow up to 180 CPU-seconds; instead the remaining budget
    # is recomputed before each block, so the THREE calls together never exceed
    # `cpu_budget` CPU-seconds (tier 1) or run forever together (tier 2, where
    # `cpu_budget is None` and every block is simply uncapped).
    def _remaining() -> Optional[float]:
        if cpu_budget is None:
            return None
        used = time.process_time() - t0
        return max(cpu_budget - used, 0.001)

    status, canonical = "OK", None
    effective_support: Optional[tuple[str, ...]] = None
    discovered_family: Optional[str] = None
    resource_event = False
    try:
        with _cpu_budget(_remaining()):
            canonical = str(sympy.simplify(parsed))
    except _Cap:
        status, resource_event = "UNRESOLVED", True
    except (MemoryError, RecursionError):
        status, resource_event = "UNRESOLVED", True
    except Exception:
        status = "UNPARSEABLE"

    if status == "OK":
        # section 25.3: pure syntactic functions of the expression ALONE, still
        # run under the SHARED budget because BOTH internally re-simplify (X-3's
        # own note -- "neither call reads `simplified`" -- was about DEPENDENCE,
        # not about cost: unconditional means "not gated on the main simplify's
        # OUTCOME", never "unbudgeted").
        try:
            with _cpu_budget(_remaining()):
                support = extract_effective_support(expression_string)
                effective_support = tuple(sorted(support)) if support is not None else None
        except _Cap:
            effective_support, resource_event = None, True
        except (MemoryError, RecursionError):
            effective_support, resource_event = None, True
        except Exception:
            effective_support = None
        try:
            with _cpu_budget(_remaining()):
                discovered_family = classify_discovered_family(expression_string)
        except _Cap:
            discovered_family, resource_event = None, True
        except (MemoryError, RecursionError):
            discovered_family, resource_event = None, True
        except Exception:
            discovered_family = None

    if resource_event and status == "OK":
        # the main simplify succeeded but a downstream extraction hit a resource
        # wall: the entry is UNRESOLVED, not a silently-nulled OK.
        status = "UNRESOLVED"

    # ---- template key --------------------------------------------------------
    template_repr = None
    try:
        with _cpu_budget(_remaining()):
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
