"""Control C-1b: search-equivalence check between e2c_search and the sealed e2_search.

DELIBERATELY A SEPARATE MODULE from e2c_search.py (CRITIC_SCIENCE NEW-C1).

`control_c1b` function-locally imports `muru.v2_calibration.e2_search`, which calls
`e2_classify.classify_expression` -- one of section 16's BANNED symbols. When this
function lived inside `e2c_search.py`, that import put it in the same module as the
actual per-world search entry point (`run_calibration_seed_search`), so a
module-scoped or even a naive call-graph scan could not cleanly distinguish "the
search path itself calls a banned symbol" from "a validation control, never invoked
during Stage 1 world search, happens to live in the same file". Moving it here makes
the distinction structural rather than argued: `e2c_search.py`'s own transitive call
graph (the thing sections 12/16 actually govern) no longer contains this import at
all, and this module is never imported by `e2c_search.py`, `e2c_classify.py`, or the
Stage 1 driver's per-world path (`scripts/v2_stage1_calibration_run.py:run_world`).

This module IS ALLOWED to call e2_search / e2_classify: control C-1b's whole job is
to compare the new truth-blind path against the module that produced the SEALED E2a
corpus, and that module legitimately uses the sealed E2a instrument. The truth-blind
boundary (P8a) governs the SEARCH ENTRY POINT, not every diagnostic that ever touches
search output for comparison purposes.
"""
from __future__ import annotations

from muru.paper_benchmark.rc5_adapter import build_case_design
from muru.paper_benchmark.rc5_estimate import fit_case_scalars
from . import e2c_search


def control_c1b(n_worlds: int = 3, n_seeds: int = 3) -> dict:
    """Control `C-1`, evaluated between this module and `e2_search`.

    Duplicating a search path is a risk. It is discharged EXHAUSTIVELY on the control
    set rather than argued: the `argmax(score)`-retained candidate, its complexity and
    its valid_r2 must be BYTE-IDENTICAL between the two modules on the same E2a world
    and seed. Only canonicalisation may differ, and only in the direction section 25
    requires.
    """
    from . import e2_search, e2_worlds
    mismatches, compared = [], 0
    for fi, fam in enumerate(e2_worlds.FAMILIES[:n_worlds]):
        w = e2_worlds.build_world(fam, "low", "default", 6)
        wid = e2_worlds.world_id(fam, "low", "default", 6)
        theirs_wd = e2_search.build_world_design(w.compounds, w.trajectories, wid)
        mine_design = build_case_design(w.compounds, fit_case_scalars(w.compounds, w.trajectories))
        for k in range(n_seeds):
            seed = 2_100_011_400 + fi * 100 + k
            a = e2_search.run_seed_search(theirs_wd, k, seed)
            wd = e2c_search.CalWorldDesign(wid, wid, theirs_wd.scalars, mine_design,
                                {"cell_id": wid, "replicate": 6, "partition": "calibration",
                                 "case_id": wid, "family_code": fam, "variant": fam,
                                 "condition_kind": fam, "coefficient_value": None,
                                 "noise_sd": None})
            b = e2c_search.run_calibration_seed_search(wd, k, seed)
            compared += 1
            ra = next((r for r in a.rows if r.retained_by_argmax_score), None)
            rb = next((r for r in b.rows if r.retained_by_argmax_score), None)
            if (a.status != b.status
                    or (ra is None) != (rb is None)
                    or (ra is not None and (
                        ra.expression_string != rb.expression_string
                        or ra.engine_complexity != rb.engine_complexity
                        or f"{ra.valid_r2:.12g}" != f"{rb.valid_r2:.12g}"
                        or f"{ra.score:.12g}" != f"{rb.score:.12g}"))):
                mismatches.append({"world": wid, "k": k,
                                   "theirs": (a.status, ra.expression_string if ra else None),
                                   "mine": (b.status, rb.expression_string if rb else None)})
    return {"control": "C-1b", "compared": compared, "n_mismatched": len(mismatches),
            "mismatches": mismatches[:10], "passed": compared > 0 and not mismatches}
