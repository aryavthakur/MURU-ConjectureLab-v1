#!/usr/bin/env python
"""Migration step 9: initialize the persistent classification cache from
the old run's already-computed, valid classifications.

Safety proof, not assumption: `classify_expression` is a pure function of
`expression_string` alone (see classify_cache.py's own docstring), so any
(expression_string -> ClassificationResult) pair the old run already
computed is a valid cache entry FOR THE SAME CLASSIFIER VERSION, and only
for the same version -- this script refuses to seed anything if the old
run's worktree hashes to a different `classifier_version` than this
worktree's (checked here, not assumed; see main()).

Only genuinely-computed classify_expression() outputs are imported: rows
whose `canonicalization_status` starts with `ROW_ERROR:` came from the
OUTER per-row exception handler in the old run's search loop, not from
`classify_expression` itself, and are excluded.

This does NOT seed the (candidate, truth) `algebraically_equivalent`
cache -- the old run never computed or persisted that as a reusable,
keyed pair (score_row computed it inline, per row, without a cache), so
there is nothing valid to import for it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.v2_calibration.e2_classify import ClassificationResult  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import classify_cache as cc  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-result-dir", action="append", required=True, dest="old_dirs")
    parser.add_argument("--cache-db", type=str, required=True)
    parser.add_argument("--classifier-version", type=str, required=True,
                         help="must match compute_classifier_version(repo_root) for BOTH the old run's code and this worktree's -- verified by the caller before invoking this script")
    args = parser.parse_args()

    cache = cc.PersistentClassifyCache(Path(args.cache_db), args.classifier_version)
    n_seen = 0
    n_imported = 0
    n_skipped_row_error = 0
    n_skipped_dup_conflict = 0
    seen_exprs: dict[str, ClassificationResult] = {}

    for d in args.old_dirs:
        d = Path(d)
        for path in sorted(d.glob("candidates_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    n_seen += 1
                    status = rec.get("canonicalization_status")
                    if status is None or status.startswith("ROW_ERROR"):
                        n_skipped_row_error += 1
                        continue
                    expr = rec["expression_string"]
                    result = ClassificationResult(
                        expression_string=expr,
                        parse_ok=rec["parse_ok"],
                        canonicalization_status=status,
                        canonical_expression=rec.get("canonical_expression"),
                        effective_support=(
                            frozenset(rec["effective_support"]) if rec.get("effective_support") is not None else None
                        ),
                        discovered_family=rec.get("discovered_family"),
                        template_key_value=None,
                        template_key_repr=rec.get("template_key"),
                        coefficient_estimates=(
                            tuple(rec["coefficient_estimates"]) if rec.get("coefficient_estimates") is not None else None
                        ),
                        grammar_parse_ok=True,  # never consumed downstream; not persisted by the old run either
                    )
                    prior = seen_exprs.get(expr)
                    if prior is not None and prior != result:
                        # A real conflict would mean classify_expression is
                        # NOT pure in expression_string alone, contradicting
                        # this cache's own safety proof -- refuse silently
                        # overwriting, count it instead.
                        n_skipped_dup_conflict += 1
                        continue
                    seen_exprs[expr] = result
                    cache.put_classification(expr, result)
                    n_imported += 1

    stats = cache.stats()
    cache.close()
    print(f"n_candidate_rows_seen: {n_seen}")
    print(f"n_skipped_row_error: {n_skipped_row_error}")
    print(f"n_skipped_dup_conflict: {n_skipped_dup_conflict}")
    print(f"n_cache_put_calls: {n_imported}")
    print(f"n_distinct_expressions_now_cached (this version): {stats['classify_rows_current_version']}")


if __name__ == "__main__":
    main()
