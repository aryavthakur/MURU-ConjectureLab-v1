"""Rescue-v2: raw (classification-free) per-seed front capture.

`e2_search.run_seed_search` (the frozen-lineage E2 search module) calls
`e2_classify.classify_expression` INLINE, once per front row, while
building each row -- this is exactly why the exhaustive path pays full
classification cost during search itself, before `evaluate_world` ever
gets a chance to determine how much of it was actually needed (see
`MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md` section 1). To realize the lazy
witness order in production, search and classification must be decoupled:
this module is a TRANSCRIPTION of `run_seed_search`'s structural
(non-classification) logic -- same imports, same call sequence, same
frozen `rc5_adapter`/`rc5_estimate`/`rc5_selection` functions, same
retention call (`select_row_label`) -- with the
`classification = e2_classify.classify_expression(expression)` line and
every classification-derived `FrontRow` field removed, replaced by a
`lazy_classify.RawFrontRow` (only the fields `lazy_evaluate_world` and
`RetainedCandidate` actually need).

Per this project's own transcription discipline (`MURU_V2_E2_PREDECLARATION.md`
section 1: "any function that IS transcribed line-for-line is checked
against the original by an executable identity test before use"): see
`tests/test_raw_search_identity.py`, which runs BOTH this module's
`run_seed_search_raw` and the real `e2_search.run_seed_search` on the same
world/seed and asserts every structural field (front_rank, complexity,
expression_string, valid_r2, invalid_fraction, test_r2, retained flag) is
byte-identical -- the only permitted difference is the classification-
derived fields this module never computes.

Nothing here changes model fitting, the grammar, the objective, or the
retention rule. `PySRCaseBackend`/`build_case_regressor`/`select_row_label`
are imported unmodified from the same frozen modules.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from muru.paper_benchmark.rc5_adapter import (
    build_case_regressor,
    candidate_r2_on,
    row_complexity,
    row_position,
)
from muru.paper_benchmark.rc5_estimate import N_VALIDATION_COMPOUNDS, invalid_fraction as compute_invalid_fraction
from muru.paper_benchmark.rc5_selection import SeedExecutionFailure, SeedNoCandidate, select_row_label

from muru.v2_calibration.e2_search import WorldDesign  # reused, not copied -- same lightweight container
from muru.v2_calibration.e2_rescue_v2.lazy_classify import RawFrontRow

__all__ = ["RawSeedFrontResult", "run_seed_search_raw"]


@dataclass(frozen=True)
class RawSeedFrontResult:
    seed_ordinal_k: int
    seed: int
    status: str  # COMPLETED_WITH_FRONT | COMPLETED_NO_CANDIDATE | EXECUTION_FAILURE -- identical vocabulary to e2_search.SeedFrontResult
    error_message: str
    rows: tuple[RawFrontRow, ...]
    wall_seconds: float


def run_seed_search_raw(world_design: WorldDesign, k: int, seed: int, work_dir: Path | None = None) -> RawSeedFrontResult:
    """Structural transcription of `e2_search.run_seed_search` -- see this
    module's docstring. Every call below is the SAME frozen function that
    module calls, in the SAME order, on the SAME arguments."""
    started = time.monotonic()
    design = world_design.design
    train = design.train_mask
    if not train.any():
        return RawSeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message="case has an empty train partition", rows=(),
            wall_seconds=time.monotonic() - started,
        )

    try:
        model = build_case_regressor(seed, work_dir=work_dir)
        model.fit(design.design[train], design.target[train])
        equations = getattr(model, "equations_", None)
    except Exception as error:
        return RawSeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message=f"{type(error).__name__}: {error}", rows=(),
            wall_seconds=time.monotonic() - started,
        )

    if isinstance(equations, list):
        equations = equations[0]

    argmax_position: Optional[int] = None
    try:
        label = select_row_label(equations)
        argmax_position = row_position(equations, label)
    except SeedNoCandidate:
        return RawSeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="COMPLETED_NO_CANDIDATE",
            error_message="", rows=(), wall_seconds=time.monotonic() - started,
        )
    except SeedExecutionFailure as error:
        return RawSeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message=f"{type(error).__name__}: {error}", rows=(),
            wall_seconds=time.monotonic() - started,
        )
    except Exception as error:
        return RawSeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message=f"{type(error).__name__}: {error}", rows=(),
            wall_seconds=time.monotonic() - started,
        )

    rows: list[RawFrontRow] = []
    for position in range(len(equations)):
        label = equations.index[position]
        try:
            complexity = row_complexity(equations, label)
            expression = str(equations["equation"].iloc[position])

            valid_r2 = candidate_r2_on(model, equations, label, design.design, design.target, design.validation_mask)
            test_r2 = candidate_r2_on(model, equations, label, design.design, design.target, design.test_mask)

            predictions = np.asarray(
                model.predict(design.design[design.validation_mask], index=position), dtype=np.float64,
            )
            frac_invalid = compute_invalid_fraction(predictions, N_VALIDATION_COMPOUNDS)

            rows.append(RawFrontRow(
                seed_ordinal_k=k, seed=seed, front_rank=position,
                expression_string=expression, complexity=complexity,
                valid_r2=float(valid_r2), invalid_fraction=float(frac_invalid),
                candidate_test_r2=float(test_r2),
                retained_by_argmax_score=(position == argmax_position),
            ))
        except Exception:
            # Mirrors e2_search.py's own row-level exception discipline: one
            # malformed row must not poison the rest of the front. A raw row
            # with parse-hostile placeholder values is still schema-valid
            # input to lazy_evaluate_world (classify_expression will itself
            # report UNPARSEABLE for it, exactly as production would).
            rows.append(RawFrontRow(
                seed_ordinal_k=k, seed=seed, front_rank=position,
                expression_string=(str(equations["equation"].iloc[position]) if "equation" in equations.columns else ""),
                complexity=-1, valid_r2=float("nan"), invalid_fraction=float("nan"),
                candidate_test_r2=float("nan"), retained_by_argmax_score=(position == argmax_position),
            ))

    if not rows:
        return RawSeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="COMPLETED_NO_CANDIDATE",
            error_message="", rows=(), wall_seconds=time.monotonic() - started,
        )

    return RawSeedFrontResult(
        seed_ordinal_k=k, seed=seed, status="COMPLETED_WITH_FRONT",
        error_message="", rows=tuple(rows), wall_seconds=time.monotonic() - started,
    )
