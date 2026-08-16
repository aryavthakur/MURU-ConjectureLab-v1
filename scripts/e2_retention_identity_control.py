#!/usr/bin/env python
"""E2 Control 1: retention-identity regression.

For a control set of (world, seed) pairs, run the bare production
single-candidate path (`rc5_runner.PySRCaseBackend` + `select_row_label` +
`row_position`, structured exactly as `rc5_runner._run_one_seed` calls them)
as an independent second fit, and assert it reproduces the SAME retained
expression/complexity/valid_r2 that `e2_search.run_seed_search`'s full-front
capture flags `retained_by_argmax_score=True` on. If this control fails, E2's
persisted fronts are unusable per the design's own gate
(MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.5, control 1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.paper_benchmark.rc5_adapter import candidate_r2_on, row_position  # noqa: E402
from muru.paper_benchmark.rc5_runner import PySRCaseBackend  # noqa: E402
from muru.paper_benchmark.rc5_selection import select_row_label  # noqa: E402
from muru.v2_calibration import e2_search as e2s  # noqa: E402
from muru.v2_calibration import e2_worlds as e2w  # noqa: E402

CONTROL_WORLDS = [
    ("mass_affine_descriptor", "mid", "default", 0),
    ("mass_power", "low", "noiseless", 1),
    ("mass_interaction", "high", "strong", 2),
]
SEED_BASE = 2_104_500_000
K_TO_CHECK = (0, 1)


def main() -> None:
    results = []
    all_pass = True
    for family, regime, noise, replicate in CONTROL_WORLDS:
        world = e2w.build_world(family, regime, noise, replicate)
        world_design = e2s.build_world_design(world.compounds, world.trajectories, world.world_id)

        for k in K_TO_CHECK:
            seed = SEED_BASE + world.world_ordinal * 30 + k

            # Path A: E2's full-front capture.
            e2_result = e2s.run_seed_search(world_design, k=k, seed=seed)
            e2_retained = next((r for r in e2_result.rows if r.retained_by_argmax_score), None)

            # Path B: bare production single-candidate path, independent fit.
            backend = PySRCaseBackend()
            outcome = backend.search(world_design.design, seed)
            label = select_row_label(outcome.equations)
            position = row_position(outcome.equations, label)
            prod_expr = str(outcome.equations["equation"].iloc[position])
            prod_complexity = int(outcome.equations["complexity"].iloc[position])
            prod_valid_r2 = candidate_r2_on(
                outcome.model, outcome.equations, label,
                world_design.design.design, world_design.design.target,
                world_design.design.validation_mask,
            )

            match = (
                e2_retained is not None
                and e2_retained.expression_string == prod_expr
                and e2_retained.engine_complexity == prod_complexity
                and e2_retained.valid_r2 == prod_valid_r2
            )
            all_pass = all_pass and match
            results.append({
                "world_id": world.world_id, "seed_ordinal_k": k, "seed": seed,
                "match": match,
                "e2_expression": e2_retained.expression_string if e2_retained else None,
                "prod_expression": prod_expr,
                "e2_complexity": e2_retained.engine_complexity if e2_retained else None,
                "prod_complexity": prod_complexity,
                "e2_valid_r2": e2_retained.valid_r2 if e2_retained else None,
                "prod_valid_r2": prod_valid_r2,
            })
            print(f"{world.world_id} k={k}: match={match}")

    out_path = REPO_ROOT / "results" / "e2" / "retention_identity_control.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"all_pass": all_pass, "checks": results}, indent=2))
    print(f"\nALL_PASS={all_pass}  ({len(results)} checks)  -> {out_path}")
    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
