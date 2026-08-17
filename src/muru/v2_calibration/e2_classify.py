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

EXECUTION-SAFETY NOTE (see E2_EXECUTION_DEVIATION.md): the per-expression
wall-clock cap this module has always declared was originally enforced with
a single in-process `signal.alarm`/SIGALRM around only the `sympy.simplify`
call. Live diagnosis of the 2026-08-16 E2a rescue found that cap defeated in
practice -- sympy's own internal simplification fallbacks wrap broad
`except Exception` blocks that can catch and discard the alarm-raised
exception before it ever reaches this module, letting the call resume and
run unbounded. `classify_expression` below now enforces the *same*,
*unchanged* `SIMPLIFY_TIMEOUT_SECONDS` cap and the *same* `SIMPLIFY_TIMEOUT`
status at a process boundary instead, via a single persistent forked worker
(`_get_worker`) that services every call for the life of this process --
`Process.kill()` from the parent on a timeout is un-catchable by any
in-worker `except Exception`. A fresh-fork-per-call design was tried first
and rejected: it discarded sympy's own internal `@cacheit` memoization
(the process-lifetime cache backing `sympy.simplify` itself, distinct from
this module's `_CACHE`) between calls, which a same-sample before/after
parity check showed measurably slows still-successful classifications and
manufactures new near-boundary SIMPLIFY_TIMEOUTs that do not occur in the
original in-process code -- a real behavioral drift, not just enforcement
relocation. The persistent worker keeps that cache warm across calls
exactly as the original single-process design did; only an actual timeout
(expected to be rare) pays a cold-restart cost, by discarding and
respawning the worker.

A second, independent source of the same drift was `ClassificationResult.
template_key_value`: `template_key()` (`identity_contract.py`) can return a
tuple holding live sympy objects (e.g. a numerator/denominator with huge
integer coefficients for a heavily-nested candidate), and pickling that
across the worker's pipe re-triggers close to the same expensive
`Basic.__new__`/assumptions machinery paid to build it in the first place --
sometimes costing more than the computation it is reporting the result of.
This field is verified dead for E2 (grepped clean across e2_search.py,
e2_scoring.py, e2_aggregate.py, rc5_selection.py, scripts/, and tests/):
nothing downstream ever reads `classification.template_key_value` --
`FrontRow` carries only the already-cheap-to-pickle `template_key_repr`
string, and `rc5_selection.py`'s own cross-seed equivalence classing (the
actual scientific consumer of template keys) independently recomputes
`template_key(parse_production_candidate(...))` from the raw expression
string, never from anything `classify_expression` returns. The worker
therefore sends `template_key_value=None` across the wire; `_classify_compute`
itself is unchanged and still computes and briefly holds the real tuple
(so a `TEMPLATE_KEY_FAILED` status downgrade still fires exactly as before),
it is only never marshalled back. This changes only where and how the
pre-declared cap is enforced, not its value, not which status name reports
a cap-out, and not the classification/equivalence computation itself.
"""
from __future__ import annotations

import multiprocessing
import signal
from dataclasses import dataclass, replace
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
#: into an explicit, distinguishable status instead of a hang. Unchanged by
#: the 2026-08-16 rescue -- only its enforcement mechanism moved (see the
#: module docstring's EXECUTION-SAFETY NOTE).
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


def _classify_compute(expression_string: str) -> ClassificationResult:
    """The per-expression computation, unchanged from the pre-rescue
    `classify_expression` body (module-level only so it can run inside a
    forked child process -- see `classify_expression`). `grammar_parse_ok`
    is filled in by the parent afterward; the placeholder here is never
    observed by a caller."""
    parsed = _safe_parse(expression_string)
    if parsed is None:
        return ClassificationResult(
            expression_string=expression_string, parse_ok=False,
            canonicalization_status="UNPARSEABLE", canonical_expression=None,
            effective_support=None, discovered_family=None,
            template_key_value=None, template_key_repr=None,
            coefficient_estimates=None, grammar_parse_ok=False,
        )

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

    return ClassificationResult(
        expression_string=expression_string, parse_ok=True,
        canonicalization_status=canonicalization_status,
        canonical_expression=canonical_expression,
        effective_support=effective_support, discovered_family=discovered_family,
        template_key_value=template_key_value, template_key_repr=template_key_repr,
        coefficient_estimates=coefficient_estimates, grammar_parse_ok=False,
    )


def _worker_loop(conn) -> None:  # pragma: no cover - runs in child process
    """Persistent classify worker body: receive one expression string, send
    back its computed `ClassificationResult`, repeat, for the process's
    whole life. Running many calls in one long-lived process (rather than
    forking fresh per call) is what preserves sympy's own internal
    `@cacheit` memoization across calls -- see the module docstring's
    EXECUTION-SAFETY NOTE. Never raises back across the pipe; a broken pipe
    or closed connection just ends the loop, since that only happens when
    the parent has already given up on (and is about to kill) this worker."""
    while True:
        try:
            expression_string = conn.recv()
        except (EOFError, OSError):
            return
        try:
            result = _classify_compute(expression_string)
        except Exception:
            result = ClassificationResult(
                expression_string=expression_string, parse_ok=False,
                canonicalization_status="UNPARSEABLE", canonical_expression=None,
                effective_support=None, discovered_family=None,
                template_key_value=None, template_key_repr=None,
                coefficient_estimates=None, grammar_parse_ok=False,
            )
        # Never marshal template_key_value across the pipe -- see the module
        # docstring's EXECUTION-SAFETY NOTE (dead field for E2, and pickling
        # a large sympy tree is itself expensive enough to manufacture a
        # false timeout). template_key_repr (the string form, and the only
        # form anything downstream reads) is sent in full.
        if result.template_key_value is not None:
            result = replace(result, template_key_value=None)
        try:
            conn.send(result)
        except (EOFError, OSError, BrokenPipeError):
            return


_WORKER_PROC = None
_WORKER_CONN = None


def _kill_worker() -> None:
    """Hard-terminate the current persistent worker (if any) and clear the
    module-level handle so the next call lazily respawns a fresh one. Called
    whenever a call times out (the worker may be wedged on that exact call
    and must not be reused) or the worker is otherwise found dead."""
    global _WORKER_PROC, _WORKER_CONN
    if _WORKER_CONN is not None:
        try:
            _WORKER_CONN.close()
        except Exception:
            pass
        _WORKER_CONN = None
    if _WORKER_PROC is not None:
        if _WORKER_PROC.is_alive():
            _WORKER_PROC.kill()
            _WORKER_PROC.join(2.0)
        _WORKER_PROC = None


def _get_worker():
    """Return (conn, proc) for the persistent worker, spawning one if it
    doesn't exist yet or died since the last call."""
    global _WORKER_PROC, _WORKER_CONN
    if _WORKER_PROC is not None and _WORKER_PROC.is_alive():
        return _WORKER_CONN, _WORKER_PROC
    ctx = multiprocessing.get_context("fork")
    parent_conn, child_conn = ctx.Pipe(duplex=True)
    proc = ctx.Process(target=_worker_loop, args=(child_conn,), daemon=True)
    proc.start()
    child_conn.close()
    _WORKER_PROC = proc
    _WORKER_CONN = parent_conn
    return parent_conn, proc


def classify_expression(expression_string: str) -> ClassificationResult:
    """Truth-blind classification of one as-emitted expression string,
    memoized process-locally by exact string (fronts repeat heavily across
    seeds within a world, per the design doc's own observation).

    The computation runs in a persistent forked worker so the pre-declared
    `SIMPLIFY_TIMEOUT_SECONDS` cap is enforced by a hard `Process.kill()`
    from the parent -- see the module docstring's EXECUTION-SAFETY NOTE.
    """
    cached = _CACHE.get(expression_string)
    if cached is not None:
        return cached

    # Secondary, independent parse check via discovery.grammar (the search's
    # own protected-semantics parser), reported but not load-bearing for
    # classification -- g2_contract._safe_parse is the classification parser
    # of record (rc5_selection.parse_production_candidate's docstring). Kept
    # in the parent: cheap, and not implicated in the sympy hang this cap
    # exists for.
    try:
        discovery_grammar.parse(expression_string, list(discovery_grammar_variables()))
        grammar_parse_ok = True
    except Exception:
        grammar_parse_ok = False

    result: Optional[ClassificationResult] = None
    try:
        conn, proc = _get_worker()
        conn.send(expression_string)
        if conn.poll(SIMPLIFY_TIMEOUT_SECONDS):
            try:
                result = conn.recv()
            except (EOFError, OSError):
                result = None
        else:
            result = None
    except (BrokenPipeError, EOFError, OSError):
        result = None

    if result is None:
        # Either the timeout fired (the worker may be wedged on exactly this
        # call and is killed outright -- SIGKILL, no in-worker except can
        # defeat this) or the pipe/worker otherwise failed. Both collapse to
        # the design doc's pre-declared cap-out status, and either way the
        # worker must not be reused for the next call.
        _kill_worker()
        result = ClassificationResult(
            expression_string=expression_string, parse_ok=True,
            canonicalization_status="SIMPLIFY_TIMEOUT", canonical_expression=None,
            effective_support=None, discovered_family=None,
            template_key_value=None, template_key_repr=None,
            coefficient_estimates=None, grammar_parse_ok=grammar_parse_ok,
        )
    else:
        result = replace(result, grammar_parse_ok=grammar_parse_ok)

    _CACHE[expression_string] = result
    return result


def discovery_grammar_variables() -> tuple[str, ...]:
    from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES

    return tuple(f"x{i}" for i in range(len(GRAMMAR_PRIMITIVES)))


def cache_size() -> int:
    return len(_CACHE)
