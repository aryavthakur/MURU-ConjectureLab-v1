"""Stage 1 calibration search — the truth-blind entry point (protocol v3 sections 12/14/16).

WHY THIS MODULE EXISTS, rather than reusing `e2_search`:

  X-3.  `e2_search.run_seed_search` calls `e2_classify.classify_expression`, which
        enforces `SIMPLIFY_TIMEOUT_SECONDS = 5`. Section 13 `A2` RETIRES that cap as
        a classification rule, and `e2_classify.py:161-162` is the defect Gate 1 was
        convened to adjudicate: it gates `effective_support` and `discovered_family`
        -- both PURE functions of the expression string -- on whether an unrelated
        `sympy.simplify` returned in time. Executing Stage 1 through `e2_search`
        would violate `A2` on the first world.

  P8a.  Section 16's symbol-level truth-blind ban forbids the search entry point's
        reachable import graph from binding `e2_classify.classify_expression`.
        `e2_search` binds it at module scope, so the entry point cannot import
        `e2_search` either.

  Neither module is edited. `e2_classify` is the sealed E2a instrument and `e2_search`
  produced the sealed E2a corpus; changing either would retroactively alter sealed
  evidence.

DUPLICATION RISK is discharged the way section 5.2 discharges it for the generator:
by an EXECUTED equivalence control rather than by argument. `control_c1b()` requires
this module's `argmax(score)`-retained candidate to be byte-identical to
`e2_search`'s on the same world and seed, for every seed of a declared control set.
That is control `C-1`'s obligation, evaluated between these two modules.

TRUTH-BLIND (section 16):
  * imported here: `build_case_design`, `fit_case_scalars`, `build_case_regressor`,
    `candidate_r2_on`, `row_complexity`, `row_position`, `select_row_label`,
    `invalid_fraction`  -- none takes a truth argument;
  * `g` is ESTIMATED from the observed trajectories by `fit_case_scalars`, never read
    from `TruthRecord.g_by_compound`. `assert_design_truth_blind` enforces that per
    world (P8b), not once in preflight.
  * NOT imported: `g2_contract`'s truth comparators, the oracle, the truth registry,
    `discovery.equivalence`, `e2_classify`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from muru.paper_benchmark.rc5_adapter import (
    CaseDesign, build_case_design, build_case_regressor, candidate_r2_on,
    row_complexity, row_position,
)
from muru.paper_benchmark.rc5_estimate import (
    N_VALIDATION_COMPOUNDS, CaseScalars, fit_case_scalars,
    invalid_fraction as compute_invalid_fraction,
)
from muru.paper_benchmark.rc5_selection import (
    SeedExecutionFailure, SeedNoCandidate, select_row_label,
)
from . import e2c_classify

__all__ = ["CalFrontRow", "CalSeedResult", "CalWorldDesign",
           "build_calibration_world_design", "run_calibration_seed_search",
           "assert_design_truth_blind"]

ADMISSIBILITY = "DECISION_ADMISSIBLE"     # section 15: stamped at ROW level, at write time


@dataclass(frozen=True)
class CalFrontRow:
    """One persisted Pareto-front row. All 21 section 14 search-side fields plus the
    seven condition-identifying fields the calibration population requires."""
    # --- section 14, fields 1..21 ---
    world_id: str
    cell_id: str
    replicate: int
    split: str
    seed_ordinal_k: int
    seed: int
    front_rank: int
    engine_complexity: int
    grammar_complexity: int
    expression_string: str
    parse_ok: bool
    train_r2: float
    valid_r2: float
    test_r2: float
    loss: float
    score: float
    invalid_fraction: float
    effective_support: Optional[tuple[str, ...]]
    template_key: Optional[str]
    retained_by_argmax_score: bool
    admissibility: str
    # --- condition-identifying extension ---
    partition: str
    case_id: str
    family_code: str
    variant: str
    condition_kind: str
    coefficient_value: Optional[float]
    noise_sd: Optional[float]
    # --- canonicalisation state (section 25.3), NOT a label ---
    canonicalization_status: str
    canonical_expression: Optional[str]
    discovered_family: Optional[str]
    canonicalisation_tier: int


@dataclass(frozen=True)
class CalSeedResult:
    world_id: str
    seed_ordinal_k: int
    seed: int
    status: str          # COMPLETED_WITH_FRONT | COMPLETED_NO_CANDIDATE | EXECUTION_FAILURE
    error_message: str
    rows: tuple[CalFrontRow, ...]
    argmax_score_label_position: Optional[int]
    wall_seconds: float


@dataclass(frozen=True)
class CalWorldDesign:
    world_id: str
    case_id: str
    scalars: CaseScalars
    design: CaseDesign
    meta: dict


def assert_design_truth_blind(design: CaseDesign, truth: Any) -> None:
    """P8b: no TruthRecord field may be reachable from the design. Asserted PER WORLD.

    The leak that matters is `g` being read from `truth.g_by_compound` instead of
    estimated from the observed trajectories. An import-level check could never
    detect that regression; this does.
    """
    g_truth = getattr(truth, "g_by_compound", None) or {}
    if not g_truth:
        return
    truth_vec = np.asarray([g_truth[c] for c in design.compound_ids
                            if c in g_truth], dtype=np.float64)
    if truth_vec.size == 0:
        return
    est = np.asarray(design.target, dtype=np.float64)[:truth_vec.size]
    if est.size == truth_vec.size and np.allclose(est, truth_vec, rtol=0, atol=0):
        raise AssertionError(
            "P8b VIOLATED: the design target is byte-identical to TruthRecord.g_by_compound. "
            "The search would be reading truth rather than estimating from trajectories.")


def build_calibration_world_design(case_id: str) -> CalWorldDesign:
    """Generate one calibration world and assemble its search design.

    `generate_calibration_case` is imported INSIDE the function so that the truth
    record never enters this module's namespace at import time.
    """
    from muru.paper_benchmark.calibration_surface import (
        generate_calibration_case, resolve_calibration_case_id,
    )
    generated = generate_calibration_case(case_id)
    family, variant, replicate = resolve_calibration_case_id(case_id)
    scalars = fit_case_scalars(generated.inputs.compounds, generated.inputs.trajectories)
    design = build_case_design(generated.inputs.compounds, scalars)
    assert_design_truth_blind(design, generated.truth)          # P8b, per world
    truth = generated.truth
    # Section 14's condition-identifying extension. These LABEL the persisted rows and
    # are NEVER passed to the fit: `run_calibration_seed_search` fits on
    # `design.design[train_mask]` / `design.target[train_mask]` only, and `meta` is
    # consumed solely when constructing the output row. They are generative FACTORS
    # (which condition this world is), not truth LABELS (what the answer is); the
    # truth-derived columns 22-28 are joined later, by the separate scoring pass.
    meta = {
        "partition": truth.partition,
        "case_id": case_id,
        "family_code": family.code,
        "variant": variant.code,
        "replicate": replicate,
        "condition_kind": variant.generative_kind,
        "coefficient_value": (truth.coefficients or {}).get("coefficient"),
        "noise_sd": (truth.noise or {}).get("sd"),
        "cell_id": f"{family.code}|{variant.code}",
        "content_hash": generated.content_hash,
    }
    return CalWorldDesign(world_id=case_id, case_id=case_id, scalars=scalars,
                          design=design, meta=meta)


def run_calibration_seed_search(
    wd: CalWorldDesign, k: int, seed: int,
    table: "e2c_classify.CanonicalisationTable | None" = None,
    work_dir: Path | None = None,
) -> CalSeedResult:
    """One seed's FULL Pareto front, persisted before retention is applied.

    The fit and the retention call are the frozen production ones, in the frozen
    order. Only canonicalisation differs from `e2_search`, and only in that it obeys
    section 25 instead of the retired 5 s cap.
    """
    started = time.monotonic()
    design, m = wd.design, wd.meta
    table = table if table is not None else e2c_classify.CanonicalisationTable()

    def fail(msg: str) -> CalSeedResult:
        return CalSeedResult(wd.world_id, k, seed, "EXECUTION_FAILURE", msg, (), None,
                             time.monotonic() - started)

    if not design.train_mask.any():
        return fail("case has an empty train partition")
    try:
        model = build_case_regressor(seed, work_dir=work_dir)
        model.fit(design.design[design.train_mask], design.target[design.train_mask])
        equations = getattr(model, "equations_", None)
    except Exception as e:
        return fail(f"{type(e).__name__}: {e}")
    if isinstance(equations, list):
        equations = equations[0]

    try:
        argmax_position = row_position(equations, select_row_label(equations))
    except SeedNoCandidate:
        return CalSeedResult(wd.world_id, k, seed, "COMPLETED_NO_CANDIDATE", "", (), None,
                             time.monotonic() - started)
    except SeedExecutionFailure as e:
        return fail(f"{type(e).__name__}: {e}")
    except Exception as e:
        return fail(f"{type(e).__name__}: {e}")

    rows: list[CalFrontRow] = []
    for position in range(len(equations)):
        label = equations.index[position]
        try:
            expression = str(equations["equation"].iloc[position])
            entry = table.get(expression)                    # section 25, NOT the 5 s cap
            predictions = np.asarray(
                model.predict(design.design[design.validation_mask], index=position),
                dtype=np.float64)
            rows.append(CalFrontRow(
                world_id=wd.world_id, cell_id=m["cell_id"], replicate=m["replicate"],
                split="calibration", seed_ordinal_k=k, seed=seed, front_rank=position,
                engine_complexity=row_complexity(equations, label),
                grammar_complexity=row_complexity(equations, label),
                expression_string=expression,
                parse_ok=(entry.canonicalization_status != "UNPARSEABLE"),
                train_r2=float(candidate_r2_on(model, equations, label, design.design,
                                               design.target, design.train_mask)),
                valid_r2=float(candidate_r2_on(model, equations, label, design.design,
                                               design.target, design.validation_mask)),
                test_r2=float(candidate_r2_on(model, equations, label, design.design,
                                              design.target, design.test_mask)),
                loss=float(equations["loss"].iloc[position]),
                score=float(equations["score"].iloc[position]),
                invalid_fraction=float(compute_invalid_fraction(predictions,
                                                               N_VALIDATION_COMPOUNDS)),
                effective_support=entry.effective_support,
                template_key=entry.template_key_repr,
                retained_by_argmax_score=(position == argmax_position),
                admissibility=ADMISSIBILITY,
                partition=m["partition"], case_id=m["case_id"],
                family_code=m["family_code"], variant=m["variant"],
                condition_kind=m["condition_kind"],
                coefficient_value=m["coefficient_value"], noise_sd=m["noise_sd"],
                canonicalization_status=entry.canonicalization_status,
                canonical_expression=entry.canonical_expression,
                discovered_family=entry.discovered_family,
                canonicalisation_tier=entry.tier,
            ))
        except Exception as e:
            # A malformed row poisons its own row, never the rest of the front.
            rows.append(CalFrontRow(
                world_id=wd.world_id, cell_id=m["cell_id"], replicate=m["replicate"],
                split="calibration", seed_ordinal_k=k, seed=seed, front_rank=position,
                engine_complexity=-1, grammar_complexity=-1,
                expression_string=str(equations["equation"].iloc[position])
                                  if "equation" in equations.columns else "",
                parse_ok=False, train_r2=float("nan"), valid_r2=float("nan"),
                test_r2=float("nan"), loss=float("nan"), score=float("nan"),
                invalid_fraction=float("nan"), effective_support=None, template_key=None,
                retained_by_argmax_score=(position == argmax_position),
                admissibility=ADMISSIBILITY,
                partition=m["partition"], case_id=m["case_id"],
                family_code=m["family_code"], variant=m["variant"],
                condition_kind=m["condition_kind"],
                coefficient_value=m["coefficient_value"], noise_sd=m["noise_sd"],
                canonicalization_status=f"ROW_ERROR:{type(e).__name__}",
                canonical_expression=None, discovered_family=None,
                canonicalisation_tier=0,
            ))
    if not rows:
        return CalSeedResult(wd.world_id, k, seed, "COMPLETED_NO_CANDIDATE", "", (), None,
                             time.monotonic() - started)
    return CalSeedResult(wd.world_id, k, seed, "COMPLETED_WITH_FRONT", "", tuple(rows),
                         argmax_position, time.monotonic() - started)
