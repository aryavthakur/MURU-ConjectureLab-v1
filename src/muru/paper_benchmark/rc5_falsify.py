"""Engineering RC5 (D7): the per-case falsification executor under final A3.5.

Five procedures are built: **F1**, **F4**, **F7**, **F9**, **F10**.  There is no
sixth.  ``F5_SCAFFOLD_HOLDOUT`` was superseded at section 6.9.2 -- "never again
independently evaluated as a Gate-8 rung" -- and its one non-redundant
contribution, the ``candidate_test_r2`` quantity, is computed exactly once by
:func:`candidate_test_r2` and consumed by Gate 7's amended waiver branch (D1/D2),
not by any rung here.

Gating, per section 6.9.4::

    REQUIRED_HARD_GATES = {F1_REPRODUCIBILITY, F4_COMPOUND_HOLDOUT,
                           F7_INFLUENCE_DROP, F10_NEGATIVE_CONTROL}

``F9_ENERGY_SUBSET`` is computed and reported for every case reaching Gate 8,
exactly per section 6.5's construction -- nothing about how it is computed
changes -- and recorded as ``f9_stress_test_result`` /
``f9_stress_test_metric``.  Neither field is read by ``check_gate8``, and
``f9_stress_test_result`` cannot by itself or in combination produce
``REJECTED_FALSIFICATION``.  Its calibration status is
``NOT_PROVEN_FOR_HARD_GATE``.

Conventions common to all rungs (section 6.0)
----------------------------------------------
* **Affine refit.**  ``y ~ a + b*E(x)`` by ordinary least squares **on the
  designated training rows only, never on the rows being evaluated**, then R2
  on the evaluation rows under the frozen ``_r2``.  **Exactly two** free
  parameters.  The structural form is never altered by any rung except F1.
* **Truth-blindness.**  No rung reads ``TruthRecord``, ``truth.g_by_compound``,
  ``truth.active_variables``, ``truth.mathematical_family``,
  ``truth.m0_adequacy_truth``, ``scalar_truth_defined``, ``symbolic_truth_kind``,
  the family or variant code, **or the partition name**.  ``case_id`` is used
  only as a ``derive_seed`` namespace component (F10) and as a record key --
  never to branch rung behaviour.
* **No validity floors.**  No minimum-row, minimum-compound or minimum-energy
  floor exists, and no rung skips a fold, subset, construction or evaluation
  for insufficient data.  Degeneracy is handled by the already-frozen
  sentinels: a singular refit design matrix, an undefined target
  reconstruction, or a zero-variance evaluation target yields ``R2 = -inf``,
  which participates normally in the rung's own statistic.
* **Outcome states.**  ``NOT_APPLICABLE`` is **never emitted**.
  ``EXECUTION_FAILURE`` resolves to ``FAIL`` before entering the mapping Gate 8
  consumes.

Numeric ledger (section 6.8) -- every constant this contract introduces
------------------------------------------------------------------------
F1 rerun count 1; F4 one held-out compound per training scaffold at
within-scaffold index 5; F4 pass bar ``R2 > 0.0``; F7 20 LOSO folds; F9 6 folds;
F10 3 constructions; F5/F7/F9/F10 bar ``null_threshold[min(complexity, 20)]``.
No other number appears.  Phase 3's ``INFLUENCE_DROP_FRACTION = 0.05``,
``N_PERMUTATIONS_F10 = 20``, a bare ``MIN_TEST_R2``, and the three hard-coded
energy subsets are all rejected and are not imported.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from muru.discovery.grammar import evaluate as grammar_evaluate

from .calibration_contract import (
    CONSTRUCTION_ALLOCATION,
    EXCLUDED_CONSTRUCTIONS,
    MAX_COMPLEXITY,
)
from .g2_contract import GRAMMAR_PRIMITIVES, _safe_parse
from .generator import N_COMPOUNDS, N_SCAFFOLDS, derive_seed
from .identity_contract import parse_candidate, positive_scale_equivalent
from .rc3_calibration_runner import _r2
from .registry import ENERGY_GRID
from .rc5_estimate import TEST_SPLIT, TRAIN_SPLIT, fit_case_scalars
from .structural_acceptance import FalsificationResult, FalsificationRung

__all__ = [
    "REQUIRED_HARD_GATES",
    "F9_CALIBRATION_STATUS",
    "F1_RERUN_COUNT",
    "F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX",
    "F4_PASS_BAR",
    "F7_LOSO_FOLDS",
    "F9_FOLDS",
    "F10_CONSTRUCTIONS",
    "FalsificationInputs",
    "RungOutcome",
    "CaseFalsification",
    "affine_refit_r2",
    "candidate_test_r2",
    "run_f1_reproducibility",
    "run_f4_compound_holdout",
    "run_f7_influence_drop",
    "run_f9_energy_subset",
    "run_f10_negative_control",
    "run_falsification",
]

#: Section 6.9.4, verbatim.  F5 is absent because it is no longer a rung; F9 is
#: absent because it is reported, never gating.
REQUIRED_HARD_GATES: frozenset[FalsificationRung] = frozenset({
    FalsificationRung.F1_REPRODUCIBILITY,
    FalsificationRung.F4_COMPOUND_HOLDOUT,
    FalsificationRung.F7_INFLUENCE_DROP,
    FalsificationRung.F10_NEGATIVE_CONTROL,
})

#: Section 6.9.4.  Recorded so no report can cite F9's PASS/FAIL as validated
#: robustness.
F9_CALIBRATION_STATUS = "NOT_PROVEN_FOR_HARD_GATE"

# --- the numeric ledger, section 6.8 -----------------------------------
F1_RERUN_COUNT = 1
F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX = 5          # of 0..5, from N_COMPOUNDS // N_SCAFFOLDS
F4_PASS_BAR = 0.0                              # R2's own zero point
F7_LOSO_FOLDS = N_SCAFFOLDS - 10               # 20: the frozen train scaffold allocation
F9_FOLDS = len(ENERGY_GRID)                    # 6
F10_CONSTRUCTIONS: tuple[str, ...] = tuple(sorted(CONSTRUCTION_ALLOCATION))  # 3
_COMPOUNDS_PER_SCAFFOLD = N_COMPOUNDS // N_SCAFFOLDS   # 6


# -----------------------------------------------------------------------
# Inputs and outputs
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class FalsificationInputs:
    """Exactly what section 6.0 permits a rung to consume.

    There is deliberately no ``truth``, no ``family``, no ``variant``, and no
    ``partition_label`` field: the type itself is the truth-blindness guard.
    """

    case_id: str
    discovered_expression_string: str
    complexity: int
    effective_support: frozenset[str] | None
    target: np.ndarray                 # per-compound raw g, aligned to `compounds`
    compounds: pd.DataFrame
    trajectories: pd.DataFrame
    null_threshold: Mapping[int, float]

    @property
    def bar(self) -> float:
        """``null_threshold[min(complexity, 20)]``, read verbatim, never rebuilt."""
        return float(self.null_threshold[min(int(self.complexity), MAX_COMPLEXITY)])

    def mask(self, split: str) -> np.ndarray:
        return np.asarray(
            [str(s) == split for s in self.compounds["split"]], dtype=bool
        )

    def design(self) -> np.ndarray:
        return np.column_stack(
            [
                np.asarray(self.compounds[c], dtype=np.float64)
                for c in GRAMMAR_PRIMITIVES
            ]
        )


@dataclass(frozen=True)
class RungOutcome:
    """One rung's result and the statistic behind it."""

    rung: FalsificationRung
    result: FalsificationResult
    metric: float
    detail: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.result is FalsificationResult.NOT_APPLICABLE:
            raise ValueError(
                f"{self.rung.value} emitted NOT_APPLICABLE, which A3.5 section 6.0 "
                f"forbids for every rung of this contract"
            )


@dataclass(frozen=True)
class CaseFalsification:
    """Every rung result for one case, hard set and secondary kept apart."""

    hard: Mapping[FalsificationRung, FalsificationResult]
    f9_stress_test_result: FalsificationResult
    f9_stress_test_metric: float
    metrics: Mapping[str, float]
    f9_calibration_status: str = F9_CALIBRATION_STATUS

    def __post_init__(self) -> None:
        missing = sorted(r.value for r in REQUIRED_HARD_GATES if r not in self.hard)
        if missing:
            raise ValueError(f"hard gate results missing: {missing}")
        extra = sorted(r.value for r in self.hard if r not in REQUIRED_HARD_GATES)
        if extra:
            raise ValueError(
                f"{extra} are not hard gates; F5 is superseded and F9 is a "
                f"reported secondary, so neither may enter the hard mapping"
            )


# -----------------------------------------------------------------------
# Section 6.0's affine refit
# -----------------------------------------------------------------------

def _expression_values(expression_string: str, design: np.ndarray) -> np.ndarray:
    """Evaluate the fixed structural form on a design matrix.

    Parsed by the frozen G2 parser -- which resolves both the primitive names
    and PySR's ``x{i}`` aliases -- then evaluated under ``grammar.evaluate``'s
    protected semantics.  Invalid points come back as NaN so they propagate to
    ``-inf`` rather than silently scoring well.
    """
    parsed = _safe_parse(expression_string)
    if parsed is None:
        return np.full(len(design), np.nan)
    values, valid = grammar_evaluate(parsed, list(GRAMMAR_PRIMITIVES), design)
    return np.where(valid, values, np.nan)


def affine_refit_r2(
    expression_string: str,
    design: np.ndarray,
    target: np.ndarray,
    train_mask: np.ndarray,
    eval_mask: np.ndarray,
) -> float:
    """Section 6.0's convention, exactly.

    Two free parameters, fitted on the training rows only and never on the rows
    being evaluated.  Any degeneracy -- an unparseable form, a non-finite
    value, a singular design matrix, or zero target variance on the evaluation
    rows -- yields ``-inf``, the frozen sentinel, rather than a skip.
    """
    values = _expression_values(expression_string, design)
    y = np.asarray(target, dtype=np.float64)

    fit_x, fit_y = values[train_mask], y[train_mask]
    finite = np.isfinite(fit_x) & np.isfinite(fit_y)
    if finite.sum() < 2:
        return float("-inf")
    fit_x, fit_y = fit_x[finite], fit_y[finite]
    if np.ptp(fit_x) == 0.0:
        # Singular design matrix: the slope is unidentified.
        return float("-inf")

    matrix = np.column_stack([np.ones_like(fit_x), fit_x])
    try:
        coefficients, *_ = np.linalg.lstsq(matrix, fit_y, rcond=None)
    except np.linalg.LinAlgError:  # pragma: no cover - lstsq is very tolerant
        return float("-inf")
    intercept, slope = float(coefficients[0]), float(coefficients[1])

    eval_x, eval_y = values[eval_mask], y[eval_mask]
    if eval_y.size == 0 or not np.all(np.isfinite(eval_y)):
        return float("-inf")
    predictions = intercept + slope * eval_x
    if not np.all(np.isfinite(predictions)):
        return float("-inf")
    return _r2(eval_y, predictions)


def candidate_test_r2(inputs: FalsificationInputs) -> float:
    """The representative candidate's ``test``-partition R2, computed **once**.

    Section 6.3(i) binds this quantity identical to old F5's R2 and computed
    once; section 6.9.3 states the amendment "does not add a second computation
    of it"; obligation 13 makes the single computation an RC5 requirement.  The
    single value feeds both ``estimate_ceiling`` (for ``ceiling_fraction``) and
    Gate 7's amended waiver floor.  It is **not** a rung and produces no
    ``FalsificationResult``.
    """
    return affine_refit_r2(
        inputs.discovered_expression_string,
        inputs.design(),
        inputs.target,
        inputs.mask(TRAIN_SPLIT),
        inputs.mask(TEST_SPLIT),
    )


# -----------------------------------------------------------------------
# F1 -- execution determinism
# -----------------------------------------------------------------------

def run_f1_reproducibility(
    inputs: FalsificationInputs,
    reexecute: Callable[[], str | None],
) -> RungOutcome:
    """Section 6.1: an execution-determinism check, not a robustness test.

    The case pipeline is re-executed from byte-identical inputs under the
    byte-identical 30 already-derived seeds; the perturbation is the identity
    and the seeds are reused **verbatim**.  PASS iff the re-execution's selected
    structural form is identical to the original under the section 7 identity
    rule -- which is scoped to affine-coefficient position, so exponents and
    operator identity are preserved.

    ``reexecute`` returns the re-run's representative expression string, or
    ``None`` if the re-run produced no candidate.  Universal scope, no
    sampling: F1 runs for **every** case reaching Gate 8.
    """
    try:
        replayed = reexecute()
    except Exception as error:  # EXECUTION_FAILURE resolves to FAIL (section 6.0)
        return RungOutcome(
            FalsificationRung.F1_REPRODUCIBILITY,
            FalsificationResult.FAIL,
            0.0,
            {"replicates": F1_RERUN_COUNT, "error_type": type(error).__name__},
        )

    if replayed is None:
        return RungOutcome(
            FalsificationRung.F1_REPRODUCIBILITY,
            FalsificationResult.FAIL,
            0.0,
            {"replicates": F1_RERUN_COUNT, "reason": "re-execution retained nothing"},
        )

    try:
        identical = positive_scale_equivalent(
            parse_candidate(inputs.discovered_expression_string),
            parse_candidate(replayed),
        )
    except Exception as error:
        return RungOutcome(
            FalsificationRung.F1_REPRODUCIBILITY,
            FalsificationResult.FAIL,
            0.0,
            {"replicates": F1_RERUN_COUNT, "error_type": type(error).__name__},
        )

    return RungOutcome(
        FalsificationRung.F1_REPRODUCIBILITY,
        FalsificationResult.PASS if identical else FalsificationResult.FAIL,
        1.0 if identical else 0.0,
        {"replicates": F1_RERUN_COUNT, "replayed_expression": replayed},
    )


# -----------------------------------------------------------------------
# F4 -- coefficient generalisation
# -----------------------------------------------------------------------

def _f4_held_out_mask(compounds: pd.DataFrame, train_mask: np.ndarray) -> np.ndarray:
    """One held-out compound per training scaffold, at within-scaffold index 5.

    A content-blind positional rule derivable from the frozen
    ``N_COMPOUNDS // N_SCAFFOLDS == 6`` geometry.  It reads scaffold identity
    and position, and nothing else.
    """
    held = np.zeros(len(compounds), dtype=bool)
    scaffolds = np.asarray(compounds["scaffold_id"], dtype=object)
    for scaffold in dict.fromkeys(scaffolds[train_mask]):
        positions = np.where((scaffolds == scaffold) & train_mask)[0]
        if len(positions) > F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX:
            held[positions[F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX]] = True
    return held


def run_f4_compound_holdout(inputs: FalsificationInputs) -> RungOutcome:
    """Section 6.2: a **coefficient-generalisation** rung.

    Not a discovery holdout, and no report may describe it as one: the search
    fit on the full frozen ``train`` partition, so it already saw every
    compound F4 evaluates.  Structure fixed, coefficients refit without the
    held-out compounds, no ``g`` refit, no search rerun.  100 of 120 train, 20
    evaluate.  PASS: ``R2 > 0.0``.
    """
    train = inputs.mask(TRAIN_SPLIT)
    held = _f4_held_out_mask(inputs.compounds, train)
    fit_rows = train & ~held
    value = affine_refit_r2(
        inputs.discovered_expression_string,
        inputs.design(),
        inputs.target,
        fit_rows,
        held,
    )
    return RungOutcome(
        FalsificationRung.F4_COMPOUND_HOLDOUT,
        FalsificationResult.PASS if value > F4_PASS_BAR else FalsificationResult.FAIL,
        value,
        {
            "replicates": 1,
            "fit_rows": int(fit_rows.sum()),
            "evaluation_rows": int(held.sum()),
            "bar": F4_PASS_BAR,
        },
    )


# -----------------------------------------------------------------------
# F7 -- exhaustive leave-one-scaffold-out over train
# -----------------------------------------------------------------------

def run_f7_influence_drop(inputs: FalsificationInputs) -> RungOutcome:
    """Section 6.4: exhaustive LOSO over ``train``, evaluated on ``test``.

    Fold ``k`` trains on the 114 ``train`` compounds excluding scaffold ``k``'s
    6; evaluation rows are ``test`` (30), unchanged and identical across all
    folds.  No randomness -- LOSO is exhaustive over an already-labelled
    partition, not sampled.  Metric ``min_k(R2_k)``; a fold whose refit is
    singular contributes ``-inf`` and participates normally in the ``min``.
    PASS: ``min_k(R2_k) > null_threshold[min(complexity, 20)]``.

    Phase 3's ``INFLUENCE_DROP_FRACTION = 0.05`` top-5% residual-quantile
    selection is rejected and is not imported.
    """
    train = inputs.mask(TRAIN_SPLIT)
    test = inputs.mask(TEST_SPLIT)
    design = inputs.design()
    scaffolds = np.asarray(inputs.compounds["scaffold_id"], dtype=object)
    train_scaffolds = list(dict.fromkeys(scaffolds[train]))

    per_fold: list[float] = []
    for scaffold in train_scaffolds:
        fold = train & (scaffolds != scaffold)
        per_fold.append(
            affine_refit_r2(
                inputs.discovered_expression_string,
                design,
                inputs.target,
                fold,
                test,
            )
        )
    value = float(min(per_fold)) if per_fold else float("-inf")
    bar = inputs.bar
    return RungOutcome(
        FalsificationRung.F7_INFLUENCE_DROP,
        FalsificationResult.PASS if value > bar else FalsificationResult.FAIL,
        value,
        {
            "replicates": len(per_fold),
            "expected_replicates": F7_LOSO_FOLDS,
            "bar": bar,
            "per_fold_r2": [float(v) for v in per_fold],
        },
    )


# -----------------------------------------------------------------------
# F9 -- exhaustive leave-one-energy-out (secondary, non-gating)
# -----------------------------------------------------------------------

def run_f9_energy_subset(inputs: FalsificationInputs) -> RungOutcome:
    """Section 6.5: exhaustive leave-one-energy-out, 6 folds.

    Fold ``k`` restricts every compound's trajectory rows to the five energies
    other than ``ENERGY_GRID[k]``.  Uniquely among the rungs, **F9 does refit
    the scalar/g pipeline** on the restricted energy domain -- that is the
    rung's entire point, and it is exactly why section 6.9.4 treats its
    calibration scope differently from F7's despite the shared fold/minimum
    shape.  Metric ``min_k(R2_k)``; PASS bar is the same ``null_threshold``.

    The result is **reported, never gating**.  ``50e42c7``'s five hand-named
    energy subsets are struck -- two of them were literally hard-coded Phase 3
    constants -- and are not imported.
    """
    design = inputs.design()
    train = inputs.mask(TRAIN_SPLIT)
    test = inputs.mask(TEST_SPLIT)

    per_fold: list[float] = []
    for energy in ENERGY_GRID:
        restricted = inputs.trajectories[
            inputs.trajectories["energy"] != energy
        ]
        try:
            refit = fit_case_scalars(inputs.compounds, restricted)
            fold_target = refit.g
        except Exception:
            # Degeneracy is not a skip: it scores -inf and participates.
            per_fold.append(float("-inf"))
            continue
        per_fold.append(
            affine_refit_r2(
                inputs.discovered_expression_string,
                design,
                fold_target,
                train,
                test,
            )
        )

    value = float(min(per_fold)) if per_fold else float("-inf")
    bar = inputs.bar
    return RungOutcome(
        FalsificationRung.F9_ENERGY_SUBSET,
        FalsificationResult.PASS if value > bar else FalsificationResult.FAIL,
        value,
        {
            "replicates": len(per_fold),
            "expected_replicates": F9_FOLDS,
            "bar": bar,
            "per_fold_r2": [float(v) for v in per_fold],
            "calibration_status": F9_CALIBRATION_STATUS,
            "refits_the_g_pipeline": True,
        },
    )


# -----------------------------------------------------------------------
# F10 -- pipeline-integrity negative control
# -----------------------------------------------------------------------

def _corrupt(
    construction: str,
    case_id: str,
    compounds: pd.DataFrame,
    target: np.ndarray,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Apply one frozen A3.2 corruption mechanism to this case's population.

    Only the three frozen *mechanisms* are reused; no per-case null
    distribution is built and no calibration quantity is recomputed.  The seed
    namespace is section 6.6's, one dedicated content-blind seed per
    construction per case.
    """
    if construction in EXCLUDED_CONSTRUCTIONS:
        raise ValueError(
            f"{construction!r} is excluded by the frozen contract and its "
            f"unchanged reason: it leaves the per-compound scalar mean, the "
            f"exact quantity the pipeline estimates, untouched"
        )
    if construction not in CONSTRUCTION_ALLOCATION:
        raise ValueError(f"unknown construction {construction!r}")

    rng = np.random.default_rng(
        derive_seed(case_id, "F10_NEGATIVE_CONTROL", construction)
    )
    n = len(compounds)
    if construction == "target_permuted_across_compounds":
        return compounds, np.asarray(target, dtype=np.float64)[rng.permutation(n)]
    if construction == "descriptors_permuted_across_compounds":
        order = rng.permutation(n)
        corrupted = compounds.copy()
        for column in GRAMMAR_PRIMITIVES:
            corrupted[column] = np.asarray(corrupted[column])[order]
        return corrupted, np.asarray(target, dtype=np.float64)
    # gaussian_targets_with_observed_variance
    values = np.asarray(target, dtype=np.float64)
    return compounds, rng.normal(float(values.mean()), float(values.std(ddof=0)), n)


def run_f10_negative_control(inputs: FalsificationInputs) -> RungOutcome:
    """Section 6.6: a **pipeline-integrity control, not a significance test**.

    Does the fixed evaluation pipeline still report apparent validity after the
    covariate-to-target link is destroyed?  Three corruptions, forced by
    ``len(CONSTRUCTION_ALLOCATION) == 3``; Phase 3's ``N = 20`` is rejected.
    Coefficients **are** refit, deliberately, so a FAIL is attributable to
    genuine absence of signal rather than to a refusal to fit.  No ``g`` refit:
    the already-computed target is corrupted post hoc.  Training rows ``train``
    under each corruption; evaluation rows ``test`` under the **same**
    corruption, so the broken alignment is not repaired at the partition
    boundary.

    The bar is ``null_threshold[min(complexity, 20)]``, applied as the test's
    own decision rule -- here a bar **not** to clear.  PASS iff no corruption
    clears it.  Section 6.7 discloses that the reuse is *lenient* in this
    direction, which is exactly why F10 is bound narrowly as a control.
    """
    train = inputs.mask(TRAIN_SPLIT)
    test = inputs.mask(TEST_SPLIT)
    bar = inputs.bar

    per_construction: dict[str, float] = {}
    for construction in F10_CONSTRUCTIONS:
        corrupted_compounds, corrupted_target = _corrupt(
            construction, inputs.case_id, inputs.compounds, inputs.target
        )
        design = np.column_stack(
            [
                np.asarray(corrupted_compounds[c], dtype=np.float64)
                for c in GRAMMAR_PRIMITIVES
            ]
        )
        per_construction[construction] = affine_refit_r2(
            inputs.discovered_expression_string,
            design,
            corrupted_target,
            train,
            test,
        )

    worst = float(max(per_construction.values()))
    return RungOutcome(
        FalsificationRung.F10_NEGATIVE_CONTROL,
        FalsificationResult.PASS if worst <= bar else FalsificationResult.FAIL,
        worst,
        {
            "replicates": len(per_construction),
            "expected_replicates": len(CONSTRUCTION_ALLOCATION),
            "bar": bar,
            "per_construction_r2": {k: float(v) for k, v in per_construction.items()},
            "excluded_constructions": sorted(EXCLUDED_CONSTRUCTIONS),
        },
    )


# -----------------------------------------------------------------------
# The executor
# -----------------------------------------------------------------------

def run_falsification(
    inputs: FalsificationInputs,
    reexecute: Callable[[], str | None],
) -> CaseFalsification:
    """Run every procedure and split hard gates from the reported secondary.

    The return type keeps them apart structurally: ``hard`` admits exactly the
    four ``REQUIRED_HARD_GATES`` members and raises on any other key, so F9
    cannot reach the Gate-8 mapping by accident, and neither can a resurrected
    F5.
    """
    f1 = run_f1_reproducibility(inputs, reexecute)
    f4 = run_f4_compound_holdout(inputs)
    f7 = run_f7_influence_drop(inputs)
    f10 = run_f10_negative_control(inputs)
    f9 = run_f9_energy_subset(inputs)

    return CaseFalsification(
        hard={
            FalsificationRung.F1_REPRODUCIBILITY: f1.result,
            FalsificationRung.F4_COMPOUND_HOLDOUT: f4.result,
            FalsificationRung.F7_INFLUENCE_DROP: f7.result,
            FalsificationRung.F10_NEGATIVE_CONTROL: f10.result,
        },
        f9_stress_test_result=f9.result,
        f9_stress_test_metric=f9.metric,
        metrics={
            "f1_identical": f1.metric,
            "f4_r2": f4.metric,
            "f7_min_loso_r2": f7.metric,
            "f10_max_corrupted_r2": f10.metric,
            "f9_min_loeo_r2": f9.metric,
        },
    )
