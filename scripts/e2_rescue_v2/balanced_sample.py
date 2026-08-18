#!/usr/bin/env python
"""Part VII: balanced probability-sample design over the original 540-world
E2a manifest (5 families x 3 regimes x 3 noise levels x 12 replicates = 45
cells x 12).

Selection is OUTCOME-BLIND and RUNTIME-BLIND by construction: each cell's r
replicate indices (out of its 12) are drawn by a `numpy.random.Generator`
seeded from a FIXED, disclosed string
(`MURU_V2_E2_BALANCED_SAMPLE_SEED_V1|cell_id`) -- computed from the cell's
own identity alone, before any world is run and before this script ever
reads a single outcome file. Changing which worlds happen to be complete,
or what their stages turn out to be, cannot change the selection (verified
by `tests/test_balanced_sample.py`, which asserts the selection is
identical whether or not any completion data exists).

This script only DESIGNS the sample and reports its design-based
properties (variance/MOE) and how much of it is already reusable from the
live run's currently-completed world set (world_id membership only --
never touches first_loss_stage or any other outcome field). It does not
decide or lock the E4a routing gate (see routing_lock.py for that, and
MURU_V2_E2_ROUTING_LOCK_THEORY.md section on why the two must stay
separate).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402

from muru.v2_calibration import e2_worlds  # noqa: E402

SEED_TAG = "MURU_V2_E2_BALANCED_SAMPLE_SEED_V1"
CANDIDATE_R_VALUES = (4, 5, 6, 7, 8)  # -> n = 180, 225, 270, 315, 360 (45 cells x r)
N_CELLS = 45
N_PER_CELL = 12  # e2_worlds.N_REPLICATES
N_FAMILY_CELLS = 9  # 3 regimes x 3 noise levels, per family


def _cell_seed(cell_id: str) -> int:
    digest = hashlib.sha256(f"{SEED_TAG}|{cell_id}".encode()).hexdigest()
    return int(digest[:8], 16)  # 32-bit, well within numpy's accepted range


def full_preference_order(cell_id: str) -> list[int]:
    """ALL 12 replicate indices for a cell, in a single deterministic
    RNG-shuffled preference order -- the seed depends only on cell_id, so
    this is computed once, before any outcome or execution-health signal
    exists, and never revisited. `select_replicates_for_r(r)` is exactly
    the first `r` elements of this order; the remaining `12-r` are the
    PRECOMMITTED fallback sequence for that cell (see
    `select_replicates_with_fallback`, and Part X's poison-world handling
    in MURU_V2_E2_BALANCED_SAMPLE_DESIGN.md section 7) -- a permanently
    unresolvable replicate is swapped for the next name in THIS SAME
    order, never for whichever remaining replicate turns out easiest."""
    rng = np.random.default_rng(_cell_seed(cell_id))
    return rng.permutation(N_PER_CELL).tolist()


def select_replicates_for_r(r: int) -> dict[str, list[int]]:
    """cell_id -> sorted list of r selected replicate indices (0..11),
    deterministic given r alone -- the first r of `full_preference_order`."""
    selection: dict[str, list[int]] = {}
    for family, regime, noise in e2_worlds.iter_cells():
        cell_id = e2_worlds.cell_id(family, regime, noise)
        chosen = sorted(full_preference_order(cell_id)[:r])
        selection[cell_id] = chosen
    return selection


def select_replicates_with_fallback(r: int, permanently_unresolvable: set[str]) -> dict[str, list[int]]:
    """Same as `select_replicates_for_r`, except any selected world_id
    found in `permanently_unresolvable` (e.g. the poison world, after
    every isolated-retry avenue in Part X is exhausted) is swapped for the
    next replicate in that cell's OWN precommitted `full_preference_order`
    -- mechanical, no discretion, and identical for every caller given the
    same `permanently_unresolvable` set. An empty set reproduces
    `select_replicates_for_r` exactly."""
    selection: dict[str, list[int]] = {}
    for family, regime, noise in e2_worlds.iter_cells():
        cell_id = e2_worlds.cell_id(family, regime, noise)
        order = full_preference_order(cell_id)
        chosen: list[int] = []
        for replicate in order:
            if len(chosen) == r:
                break
            wid = e2_worlds.world_id(family, regime, noise, replicate)
            if wid in permanently_unresolvable:
                continue
            chosen.append(replicate)
        selection[cell_id] = sorted(chosen)
    return selection


def world_ids_for_selection(selection: dict[str, list[int]]) -> list[str]:
    ids = []
    for family, regime, noise in e2_worlds.iter_cells():
        cell_id = e2_worlds.cell_id(family, regime, noise)
        for replicate in selection[cell_id]:
            ids.append(e2_worlds.world_id(family, regime, noise, replicate))
    return sorted(ids)


def design_based_moe(r: int, worst_case_p: float = 0.5, z: float = 1.96) -> dict:
    """Stratified SRSWOR, 45 (or 9, for family-level) equal-size strata,
    proportionate allocation (constant sampling fraction r/12 in every
    stratum -- so the stratified mean-of-proportions estimator applies
    directly). See MURU_V2_E2_BALANCED_SAMPLE_DESIGN.md section 2 for the
    derivation. worst_case_p=0.5 maximizes per-stratum variance
    (conservative -- reports the widest MOE consistent with any true
    proportion)."""
    fpc = (N_PER_CELL - r) / (N_PER_CELL - 1)
    per_stratum_var = fpc * worst_case_p * (1 - worst_case_p) / r

    overall_var = (1.0 / N_CELLS) ** 2 * N_CELLS * per_stratum_var  # = per_stratum_var / N_CELLS
    overall_moe = z * overall_var ** 0.5

    family_var = (1.0 / N_FAMILY_CELLS) ** 2 * N_FAMILY_CELLS * per_stratum_var  # = per_stratum_var / N_FAMILY_CELLS
    family_moe = z * family_var ** 0.5

    return {
        "r_per_cell": r, "n_total": r * N_CELLS, "sampling_fraction": r / N_PER_CELL,
        "overall_moe_95": overall_moe, "family_level_moe_95": family_moe,
        "finite_population_correction": fpc,
    }


def _completed_world_ids(dirs: list[Path]) -> set[str]:
    """world_id membership only -- deliberately reads no other field."""
    done = set()
    for d in dirs:
        for path in sorted(d.glob("worlds_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        wid = json.loads(line).get("world_id")
                    except json.JSONDecodeError:
                        continue
                    if wid:
                        done.add(wid)
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", action="append", default=[], dest="dirs",
                         help="live run output dirs, for the 'already completed and reusable' count (world_id only)")
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    completed = _completed_world_ids([Path(d) for d in args.dirs]) if args.dirs else set()

    designs = []
    for r in CANDIDATE_R_VALUES:
        selection = select_replicates_for_r(r)
        wids = world_ids_for_selection(selection)
        moe = design_based_moe(r)
        n_reusable = sum(1 for w in wids if w in completed)
        designs.append({
            **moe,
            "n_already_completed_reusable": n_reusable,
            "n_additional_worlds_required": len(wids) - n_reusable,
        })

    out = {
        "seed_tag": SEED_TAG,
        "n_cells": N_CELLS, "n_per_cell_population": N_PER_CELL,
        "candidate_designs": designs,
        "n_currently_completed_overall": len(completed) if args.dirs else None,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    for d in designs:
        print(f"r={d['r_per_cell']:2d} n={d['n_total']:3d}  overall_MOE95={d['overall_moe_95']*100:5.2f}%  "
              f"family_MOE95={d['family_level_moe_95']*100:5.2f}%  reusable={d['n_already_completed_reusable']:3d}  "
              f"additional_needed={d['n_additional_worlds_required']:3d}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
