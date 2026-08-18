#!/usr/bin/env python
"""Count SIMPLIFY_TIMEOUT outcomes from their ACTUAL source: the classify cache.

WHY THIS EXISTS. `seal_x86_e2a.py` counts SIMPLIFY_TIMEOUT by reading
`canonicalization_status` off candidate rows:

    if r.get("canonicalization_status") == "SIMPLIFY_TIMEOUT":

but `e2_run_shard_lazy.py` writes NO classification-derived column to any
candidate row -- that is a deliberate, documented property of the rescue-v2
candidate schema ("structural fields only ... since lazy_evaluate_world does
not report back which specific rows it visited"). The key is therefore always
absent and the seal's counter is structurally dead: it can only ever report 0.
Reporting that 0 as "no scientific timeouts occurred" would be false. This
script reports the real number instead, without modifying the seal.

WHERE THE TRUTH LIVES. `PersistentClassifyCache` stores the whole
`ClassificationResult` as JSON, including `canonicalization_status`, keyed by
(classifier_version, expression_string). Every classification this run
performed went through that cache.

DENOMINATOR CAVEAT, stated rather than glossed: the cache is keyed by
EXPRESSION STRING, so these are counts of DISTINCT EXPRESSIONS, not of
candidate rows and not of worlds. Under the lazy path an expression is only
classified if the minimal-witness order actually reaches it, so this counts
what this run genuinely evaluated -- neither the number of front rows that
would time out under full reclassification, nor the number of worlds affected.
Those are different quantities and are not claimed here.

Opens the DB READ-ONLY so it is safe to run while shards are still writing.
"""
from __future__ import annotations
import argparse, collections, json, sqlite3, sys
from pathlib import Path

DEFAULT_DB = "/home/aryav_thakur/e2_x86_cache/classify_cache.sqlite3"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-db", default=DEFAULT_DB)
    ap.add_argument("--classifier-version", default=None,
                    help="restrict to one classifier version (default: report every version present)")
    ap.add_argument("--out", default=None, help="write JSON here as well as stdout")
    args = ap.parse_args()

    db = Path(args.cache_db)
    if not db.exists():
        sys.exit(f"cache db not found: {db}")

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

    q = "SELECT version, result_json FROM classify_cache"
    params: tuple = ()
    if args.classifier_version:
        q += " WHERE version=?"
        params = (args.classifier_version,)

    by_version: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    unparseable = 0
    for version, payload in conn.execute(q, params):
        try:
            status = json.loads(payload).get("canonicalization_status")
        except Exception:
            unparseable += 1
            continue
        by_version[version][status] += 1
    conn.close()

    report = {
        "schema_version": "v2_e2a_x86_simplify_timeout_audit_v1",
        "cache_db": str(db),
        "integrity_check": integrity,
        "unit_of_count": "DISTINCT EXPRESSION STRINGS classified by this run -- NOT candidate rows, NOT worlds",
        "why_not_from_candidate_rows": (
            "candidates_shard_*.jsonl carries structural fields only and never a "
            "canonicalization_status column, so seal_x86_e2a.py's own SIMPLIFY_TIMEOUT "
            "counter is structurally dead and always reports 0"
        ),
        "unparseable_cache_rows": unparseable,
        "by_classifier_version": {
            v: {
                "total_distinct_expressions": sum(c.values()),
                "status_counts": dict(sorted(c.items(), key=lambda kv: -kv[1])),
                "simplify_timeout": c.get("SIMPLIFY_TIMEOUT", 0),
                "simplify_timeout_fraction": (
                    c.get("SIMPLIFY_TIMEOUT", 0) / sum(c.values()) if sum(c.values()) else 0.0
                ),
            }
            for v, c in by_version.items()
        },
    }
    text = json.dumps(report, indent=1)
    print(text)
    if args.out:
        Path(args.out).write_text(text)


if __name__ == "__main__":
    main()
