"""E2 rescue v2: persistent exact classification cache.

`e2_classify.py` already memoizes `classify_expression` by expression
string in a process-local dict (`_CACHE`) -- its own module docstring cites
this as the design doc's own pre-declared mitigation ("memoise by
expression string ... fronts repeat heavily across seeds"). That cache is
lost every time a shard process restarts (and this rescue's own history
shows shard restarts are frequent: SIGKILL-class deaths, the staleness
watchdog, supervisor retries -- see E2_EXECUTION_DEVIATION.md). This module
extends the SAME memoization discipline to a disk-backed store that
survives process restarts and is shared across shards, without changing
what is cached or how it is computed.

WHAT IS CACHED, and why each key is exactly what it is (not more, not
less):

1. `classify_expression(expression_string) -> ClassificationResult`.
   `e2_classify.py`'s own module docstring states this function is
   "truth-blind: none reads a WorldTruth" -- it is a PURE function of
   `expression_string` alone (verified: no other argument exists in its
   signature, and its full call graph -- `_safe_parse`,
   `classify_discovered_family`, `extract_effective_support`,
   `parse_production_candidate`, `template_key`, `template_key_string`,
   `coefficient_vector` -- takes no other input). Keying on
   `expression_string` alone is therefore CORRECT, not under-keyed.

2. `algebraically_equivalent(candidate_expr, truth_expr) -> bool | None`,
   called via `e2_scoring.score_row`'s guarded block, keyed on
   `(candidate_expression_string, truth_law_string)` as an ORDERED pair
   (argument order is not assumed commutative -- the implementation
   computes `a/b` and `a-b`, not a symmetrized quantity, so this cache
   never assumes `f(a,b) == f(b,a)` even though it may often be true).
   This call is NOT currently cached at all in production (`score_row`
   calls it fresh every time, even for a repeated candidate string against
   the same truth) -- unlike `classify_expression`, this is new caching,
   not an extension of an existing one. It is licensed by the same
   purity argument: `algebraically_equivalent` reads only its two
   argument expressions, and E2a's own truth construction (see
   `MURU_V2_E2_PREDECLARATION.md` section 2) fixes the truth `coefficient`
   per (family, regime) cell -- shared identically across all 3 noise
   levels and all 12 replicates for the four descriptor families -- so
   the SAME (candidate, truth) pair can recur across as many as 36 worlds,
   not just across seeds within one world.

BOTH keys are additionally namespaced by `classifier_version` (section
"Versioning" below) -- a cache hit under a stale version is never returned;
it is treated as a miss and recomputed (safe default: silent staleness is
never possible, at the cost of a wasted disk row, not a wrong answer).

WHAT IS NOT CACHED: nothing about world identity, seed, family, regime, or
noise level enters either key, because none of those can affect either
function's output (both are pure in their stated arguments only) -- adding
them would not create a wrong answer, only a strictly worse hit rate, so
they are correctly left out, not overlooked.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from muru.v2_calibration.e2_classify import ClassificationResult

__all__ = [
    "compute_classifier_version", "PersistentClassifyCache",
]

# Every file whose content can change classify_expression's or
# algebraically_equivalent's output. Includes files NOT on E2's own
# 17-file frozen-hash manifest (e2_classify.py, e2_scoring.py) precisely
# BECAUSE those are exactly the orchestration files most likely to be
# touched by a future rescue -- the manifest's 17 files matter here too
# (g2_contract, identity_contract, rc5_selection, discovery.equivalence,
# discovery.grammar) since classify_expression's and score_row's full call
# graphs run through them.
_VERSIONED_RELATIVE_PATHS = (
    "src/muru/v2_calibration/e2_classify.py",
    "src/muru/v2_calibration/e2_scoring.py",
    "src/muru/paper_benchmark/g2_contract.py",
    "src/muru/paper_benchmark/identity_contract.py",
    "src/muru/paper_benchmark/rc5_selection.py",
    "src/muru/discovery/equivalence.py",
    "src/muru/discovery/grammar.py",
)


def compute_classifier_version(repo_root: Path) -> str:
    """SHA-256 of the sorted (relative_path, sha256(content)) pairs of
    every file that can affect classify_expression's or
    algebraically_equivalent's output. Deterministic, no git dependency
    (works identically whether or not the tree is committed) -- a stricter
    invalidation trigger than the git-blob-hash manifest E2 itself uses,
    not a replacement for it."""
    parts = []
    for rel in _VERSIONED_RELATIVE_PATHS:
        path = repo_root / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "MISSING"
        parts.append(f"{rel}:{digest}")
    composite = "\n".join(sorted(parts))
    return hashlib.sha256(composite.encode()).hexdigest()


def _classification_to_json(result: ClassificationResult) -> str:
    d = asdict(result)
    # effective_support: frozenset -> sorted list (JSON has no set type).
    # template_key_value is already always None by e2_classify's own
    # design (never marshalled across its worker pipe -- see that
    # module's EXECUTION-SAFETY NOTE); asserted, not silently trusted.
    assert d["template_key_value"] is None, (
        "classify_expression returned a non-None template_key_value -- this cache "
        "assumed that field is always None (e2_classify.py's own documented "
        "invariant) and never serializes live sympy objects; refusing to cache "
        "silently rather than risk a lossy round-trip"
    )
    if d["effective_support"] is not None:
        d["effective_support"] = sorted(d["effective_support"])
    if d["coefficient_estimates"] is not None:
        d["coefficient_estimates"] = list(d["coefficient_estimates"])
    return json.dumps(d, sort_keys=True)


def _classification_from_json(s: str) -> ClassificationResult:
    d = json.loads(s)
    if d["effective_support"] is not None:
        d["effective_support"] = frozenset(d["effective_support"])
    if d["coefficient_estimates"] is not None:
        d["coefficient_estimates"] = tuple(d["coefficient_estimates"])
    return ClassificationResult(**d)


_MISSING = object()  # sentinel distinct from a cached None (algebraically_equivalent can legitimately return None)


class PersistentClassifyCache:
    """SQLite-backed (WAL mode, safe for multiple shard processes),
    keyed and versioned as described in this module's docstring.

    Every write is `INSERT OR IGNORE` -- concurrent shards racing to cache
    the same key is harmless (classify_expression/algebraically_equivalent
    are deterministic pure functions of their keyed arguments, so whichever
    write wins is correct) and is never treated as a conflict.
    """

    def __init__(self, db_path: Path, classifier_version: str):
        self.classifier_version = classifier_version
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), timeout=30, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS classify_cache (
                    version TEXT NOT NULL,
                    expression_string TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    PRIMARY KEY (version, expression_string)
                )"""
            )
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS equivalence_cache (
                    version TEXT NOT NULL,
                    candidate_expression_string TEXT NOT NULL,
                    truth_law_string TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    PRIMARY KEY (version, candidate_expression_string, truth_law_string)
                )"""
            )
            self._conn.commit()

    # --- classify_expression cache -------------------------------------

    def get_classification(self, expression_string: str) -> Optional[ClassificationResult] | object:
        with self._lock:
            row = self._conn.execute(
                "SELECT result_json FROM classify_cache WHERE version=? AND expression_string=?",
                (self.classifier_version, expression_string),
            ).fetchone()
        if row is None:
            return _MISSING
        return _classification_from_json(row[0])

    def put_classification(self, expression_string: str, result: ClassificationResult) -> None:
        payload = _classification_to_json(result)
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO classify_cache (version, expression_string, result_json) VALUES (?,?,?)",
                (self.classifier_version, expression_string, payload),
            )
            self._conn.commit()

    # --- algebraically_equivalent cache ---------------------------------

    def get_equivalence(self, candidate_expression_string: str, truth_law_string: str):
        with self._lock:
            row = self._conn.execute(
                "SELECT value_json FROM equivalence_cache WHERE version=? AND candidate_expression_string=? AND truth_law_string=?",
                (self.classifier_version, candidate_expression_string, truth_law_string),
            ).fetchone()
        if row is None:
            return _MISSING
        return json.loads(row[0])["value"]

    def put_equivalence(self, candidate_expression_string: str, truth_law_string: str, value: Optional[bool]) -> None:
        payload = json.dumps({"value": value})
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO equivalence_cache "
                "(version, candidate_expression_string, truth_law_string, value_json) VALUES (?,?,?,?)",
                (self.classifier_version, candidate_expression_string, truth_law_string, payload),
            )
            self._conn.commit()

    # --- introspection (diagnostic only) --------------------------------

    def stats(self) -> dict:
        with self._lock:
            n_classify_current = self._conn.execute(
                "SELECT COUNT(*) FROM classify_cache WHERE version=?", (self.classifier_version,)
            ).fetchone()[0]
            n_classify_stale = self._conn.execute(
                "SELECT COUNT(*) FROM classify_cache WHERE version!=?", (self.classifier_version,)
            ).fetchone()[0]
            n_equiv_current = self._conn.execute(
                "SELECT COUNT(*) FROM equivalence_cache WHERE version=?", (self.classifier_version,)
            ).fetchone()[0]
            n_equiv_stale = self._conn.execute(
                "SELECT COUNT(*) FROM equivalence_cache WHERE version!=?", (self.classifier_version,)
            ).fetchone()[0]
        return {
            "classifier_version": self.classifier_version,
            "classify_rows_current_version": n_classify_current,
            "classify_rows_stale_version": n_classify_stale,
            "equivalence_rows_current_version": n_equiv_current,
            "equivalence_rows_stale_version": n_equiv_stale,
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def cached_classify_expression(cache: PersistentClassifyCache, expression_string: str):
    """Drop-in wrapper around `e2_classify.classify_expression`: checks the
    persistent cache first (any version-current hit is reused verbatim,
    no recomputation), falls back to the real, unmodified frozen function
    on a miss, and writes the result back. Import this where a script would
    otherwise call `e2_classify.classify_expression` directly."""
    from muru.v2_calibration import e2_classify

    cached = cache.get_classification(expression_string)
    if cached is not _MISSING:
        return cached
    result = e2_classify.classify_expression(expression_string)
    cache.put_classification(expression_string, result)
    return result


def cached_algebraically_equivalent(cache: PersistentClassifyCache, candidate_expr, truth_expr,
                                     candidate_expression_string: str, truth_law_string: str):
    """Drop-in wrapper around `discovery.equivalence.algebraically_equivalent`.
    Takes both the already-parsed sympy expressions (needed for the real
    call on a miss) and their source strings (the cache key) separately,
    since the parsed forms are not the cache key -- see this module's
    docstring for why keying on the raw strings is the safe choice."""
    from muru.discovery.equivalence import algebraically_equivalent

    cached = cache.get_equivalence(candidate_expression_string, truth_law_string)
    if cached is not _MISSING:
        return cached
    value = algebraically_equivalent(candidate_expr, truth_expr)
    cache.put_equivalence(candidate_expression_string, truth_law_string, value)
    return value
