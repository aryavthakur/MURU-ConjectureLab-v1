"""Prospective objective-alignment validation of the Type 2 claim.

This package is NOT a sixth phase and does not modify Phase 3. It implements a
separate prospective study asking whether the MURU machinery is valid for the
*original* master-plan objective — a compact, interpretable, molecule-conditional
empirical equation FAMILY with correct structural support and scaling behaviour —
rather than for the stricter exact-functional-form criterion that
`PHASE3_PREREGISTRATION.md` §19 introduced.

Layout mirrors the Phase 3 quarantine discipline:

* `signature`, `select`, `equiv`, `adjudicate` are the discovery side. They read
  data and candidates. They never read a planted law.
* `truth2` holds the planted laws for the fresh validation worlds and must not
  appear in the import closure of the discovery side.
* `generators2` builds the fresh worlds and is allowed to read `truth2`.
"""

OBJVAL_VERSION = "ov-1.0.0"
