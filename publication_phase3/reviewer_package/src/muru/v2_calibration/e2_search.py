"""E2: full per-seed Pareto front capture.

Removes `WITHIN_SEED_PARETO_NOT_OBSERVABLE` by persisting every row of
`equations_`, not just the `argmax(score)` retained row -- and by changing
NOTHING else. Every function this module calls to build the design, build
the regressor, and score a row is imported unmodified from
`rc5_adapter`/`rc5_estimate`/`rc5_selection`, the same modules the production
Held-out runner used. The single-candidate retention path
(`rc5_selection.select_row_label`) is *also* called here, on the identical
`equations_` frame, so `retained_by_argmax_score` is computed by the same
function production uses -- not re-derived by inspecting scores independently
-- which is what makes the retention-identity regression in
`e2_preflight.py` meaningful rather than circular.

Truth-blind throughout: no function here accepts or reads a `WorldTruth`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES
from muru.paper_benchmark.rc5_adapter import (
    CaseDesign,
    build_case_design,
    build_case_regressor,
    candidate_r2_on,
    row_complexity,
    row_position,
)
from muru.paper_benchmark.rc5_estimate import (
    N_VALIDATION_COMPOUNDS,
    CaseScalars,
    fit_case_scalars,
    invalid_fraction as compute_invalid_fraction,
)
from muru.paper_benchmark.rc5_selection import (
    SeedExecutionFailure,
    SeedNoCandidate,
    select_row_label,
)
from muru.paper_benchmark.structural_acceptance import MAX_COMPLEXITY

from . import e2_classify

__all__ = [
    "FrontRow", "SeedFrontResult", "WorldDesign",
    "build_world_design", "run_seed_search",
]


@dataclass(frozen=True)
class FrontRow:
    """One row of one seed's persisted Pareto front. Truth-blind."""

    front_rank: int
    engine_complexity: int
    grammar_complexity: int          # == engine_complexity here (row_complexity IS PySR's own column; kept as a distinct field name matching front_record_fields)
    expression_string: str
    parse_ok: bool
    canonicalization_status: str
    canonical_expression: Optional[str]
    train_r2: float
    valid_r2: float
    test_r2: float
    loss: float
    score: float
    invalid_fraction: float
    effective_support: Optional[tuple[str, ...]]
    template_key_repr: Optional[str]
    coefficient_estimates: Optional[tuple[float, ...]]
    retained_by_argmax_score: bool
    admissibility: str = "DECISION_ADMISSIBLE"   # E2a; E2b rows would carry DECISION_INADMISSIBLE


@dataclass(frozen=True)
class SeedFrontResult:
    seed_ordinal_k: int
    seed: int
    status: str                       # COMPLETED_WITH_FRONT | COMPLETED_NO_CANDIDATE | EXECUTION_FAILURE
    error_message: str
    rows: tuple[FrontRow, ...]
    argmax_score_label_position: Optional[int]
    wall_seconds: float


@dataclass(frozen=True)
class WorldDesign:
    world_id: str
    scalars: CaseScalars
    design: CaseDesign


def build_world_design(compounds: pd.DataFrame, trajectories: pd.DataFrame, world_id: str) -> WorldDesign:
    """The frozen A3.5-section-4 two-stage fit (Phi on train, g for all
    compounds against the frozen Phi), then the frozen design assembly.
    Identical call sequence to what the production runner does per real case
    -- `fit_case_scalars` and `build_case_design` do not know or care whether
    the compounds/trajectories came from `generator.generate_case` or from
    `e2_worlds.build_world`; the schema is all either one requires."""
    scalars = fit_case_scalars(compounds, trajectories)
    design = build_case_design(compounds, scalars)
    return WorldDesign(world_id=world_id, scalars=scalars, design=design)


def run_seed_search(
    world_design: WorldDesign, k: int, seed: int, work_dir: Path | None = None,
) -> SeedFrontResult:
    """One seed's full front, captured without disturbing what production
    would have retained from the identical fit.

    Fitted exactly as `PySRCaseBackend.search` does: `build_case_regressor`
    under the frozen `SEARCH_SETTINGS`, fitted on `design.design[train_mask]`,
    `design.target[train_mask]` -- no sample weights (rc5_adapter binds
    "Weights: none"), no `variable_names` override (PySR's default `x0..x4`
    naming, which `g2_contract`/`rc5_selection` are built to consume).
    """
    started = time.monotonic()
    design = world_design.design
    train = design.train_mask
    if not train.any():
        return SeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message="case has an empty train partition", rows=(),
            argmax_score_label_position=None, wall_seconds=time.monotonic() - started,
        )

    try:
        model = build_case_regressor(seed, work_dir=work_dir)
        model.fit(design.design[train], design.target[train])
        equations = getattr(model, "equations_", None)
    except Exception as error:
        return SeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message=f"{type(error).__name__}: {error}", rows=(),
            argmax_score_label_position=None, wall_seconds=time.monotonic() - started,
        )

    if isinstance(equations, list):  # multi-output guard; single-target here so take [0] defensively
        equations = equations[0]

    # The SAME retention call production makes, on the SAME frame. Whatever
    # exception class it raises is preserved as the seed's status, exactly as
    # `rc5_runner._run_one_seed` does -- E2 does not invent a softer failure
    # mode for the retention step.
    argmax_position: Optional[int] = None
    try:
        label = select_row_label(equations)
        argmax_position = row_position(equations, label)
    except SeedNoCandidate:
        return SeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="COMPLETED_NO_CANDIDATE",
            error_message="", rows=(), argmax_score_label_position=None,
            wall_seconds=time.monotonic() - started,
        )
    except SeedExecutionFailure as error:
        return SeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message=f"{type(error).__name__}: {error}", rows=(),
            argmax_score_label_position=None, wall_seconds=time.monotonic() - started,
        )
    except Exception as error:
        return SeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="EXECUTION_FAILURE",
            error_message=f"{type(error).__name__}: {error}", rows=(),
            argmax_score_label_position=None, wall_seconds=time.monotonic() - started,
        )

    rows: list[FrontRow] = []
    for position in range(len(equations)):
        label = equations.index[position]
        try:
            complexity = row_complexity(equations, label)
            expression = str(equations["equation"].iloc[position])
            loss = float(equations["loss"].iloc[position])
            score = float(equations["score"].iloc[position])

            train_r2 = candidate_r2_on(model, equations, label, design.design, design.target, design.train_mask)
            valid_r2 = candidate_r2_on(model, equations, label, design.design, design.target, design.validation_mask)
            test_r2 = candidate_r2_on(model, equations, label, design.design, design.target, design.test_mask)

            predictions = np.asarray(
                model.predict(design.design[design.validation_mask], index=position), dtype=np.float64,
            )
            frac_invalid = compute_invalid_fraction(predictions, N_VALIDATION_COMPOUNDS)

            classification = e2_classify.classify_expression(expression)

            rows.append(FrontRow(
                front_rank=position,
                engine_complexity=complexity,
                grammar_complexity=complexity,
                expression_string=expression,
                parse_ok=classification.parse_ok,
                canonicalization_status=classification.canonicalization_status,
                canonical_expression=classification.canonical_expression,
                train_r2=float(train_r2), valid_r2=float(valid_r2), test_r2=float(test_r2),
                loss=loss, score=score, invalid_fraction=float(frac_invalid),
                effective_support=(
                    tuple(sorted(classification.effective_support))
                    if classification.effective_support is not None else None
                ),
                template_key_repr=classification.template_key_repr,
                coefficient_estimates=classification.coefficient_estimates,
                retained_by_argmax_score=(position == argmax_position),
            ))
        except Exception as error:
            # One malformed row must not poison the rest of the front (E2's
            # own persistence contract goes further than production's
            # single-row contract precisely so a row-level defect is visible
            # rather than aborting the whole seed).
            rows.append(FrontRow(
                front_rank=position, engine_complexity=-1, grammar_complexity=-1,
                expression_string=str(equations["equation"].iloc[position]) if "equation" in equations.columns else "",
                parse_ok=False, canonicalization_status=f"ROW_ERROR:{type(error).__name__}",
                canonical_expression=None, train_r2=float("nan"), valid_r2=float("nan"),
                test_r2=float("nan"), loss=float("nan"), score=float("nan"),
                invalid_fraction=float("nan"), effective_support=None, template_key_repr=None,
                coefficient_estimates=None, retained_by_argmax_score=(position == argmax_position),
            ))

    if not rows:
        return SeedFrontResult(
            seed_ordinal_k=k, seed=seed, status="COMPLETED_NO_CANDIDATE",
            error_message="", rows=(), argmax_score_label_position=None,
            wall_seconds=time.monotonic() - started,
        )

    return SeedFrontResult(
        seed_ordinal_k=k, seed=seed, status="COMPLETED_WITH_FRONT",
        error_message="", rows=tuple(rows),
        argmax_score_label_position=argmax_position,
        wall_seconds=time.monotonic() - started,
    )
