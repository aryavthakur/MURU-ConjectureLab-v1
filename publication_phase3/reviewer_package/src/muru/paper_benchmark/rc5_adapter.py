"""Engineering RC5: the case-to-search adapter, and Gate-2 input provenance.

Turns one case's compound frame plus its per-compound raw ``g`` into exactly
the design PySR searches on, and computes the two Gate-2 inputs from the
**calibration path**, which A3.5 section 7.2 makes a forced correctness
requirement rather than a style preference.

Bound rules, all from A3.5 section 4.3 and section 7.2:

======================  =====================================================
Target                  the **raw, untransformed** ``g`` -- not ``log g``,
                        not reweighted, not renormalised
Rows                    **one row per compound**, over the case's frozen split
Covariates              exactly the five ``GRAMMAR_PRIMITIVES``, frozen order
Weights                 **none** -- unweighted, unnormalised
Row filtering           **none**; F04/F05-flagged compounds are not dropped
``complexity``          PySR's own ``equations_["complexity"]`` column
``valid_r2``            unweighted ``rc3_calibration_runner._r2`` on
                        ``model.predict(design[validation], index=row)``
======================  =====================================================

**Why the Gate-2 sources are forced.**  The null threshold table's complexity
axis *is* PySR's ``equations_["complexity"]`` column and its ``valid_r2`` axis
*is* the unweighted ``_r2``.  ``discovery/engine.py`` instead treats
``grammar.complexity(parse(...))`` as authoritative and computes a weighted,
invalid-masked R2.  The two complexity metrics diverge **upward** (sympy renders
``a / b`` as ``Mul(a, Pow(b, -1))``, costing 4, while PySR counts ``/`` as one
binary operator, costing 3), and ``null_threshold`` is *indexed by complexity*
with ``threshold[c]`` enforced non-decreasing -- so an inflated complexity looks
up a different, generally higher bar than the one calibrated for that candidate,
and ``MAX_COMPLEXITY = 20`` could reject at grammar-complexity 24 a candidate
PySR reports at 20.  ``engine.run_pysr``'s ``Candidate`` is therefore excluded
from every gate input, and ``discovery.engine`` is not imported by this module
at all.

**Implementation landmine (section 7.2, binding).**  ``idx_model_selection``
returns a pandas **label**, while ``predict(index=...)`` and ``.iloc[]`` take
**positions**.  :func:`row_position` performs the mandatory
``equations_.index.get_loc(label)`` conversion; conflating the two silently
scores the wrong row.

**Grammar.**  Operators come from the frozen ``SEARCH_SETTINGS`` and are
asserted against ``excluded_unary`` before any regressor is built.  ``exp`` is
not added, and section 10.2's F18 representability limitation is carried
forward as a disclosed, unfixed property: "Bound response: none."

Nothing here reads planted truth, the generative family, or the partition
label.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from .calibration_contract import MAX_COMPLEXITY, SEARCH_SETTINGS
from .g2_contract import GRAMMAR_PRIMITIVES
from .rc3_calibration_runner import _r2
from .rc5_estimate import (
    TEST_SPLIT,
    TRAIN_SPLIT,
    VALIDATION_SPLIT,
    CaseScalars,
)

__all__ = [
    "CASE_COVARIATE_ORDER",
    "FEATURE_NAME_ALIASES",
    "CaseDesign",
    "build_case_design",
    "row_position",
    "row_complexity",
    "candidate_r2_on",
    "GrammarSettingsError",
    "assert_grammar_settings",
    "build_case_regressor",
]

#: Literally the frozen tuple, not a copy: the design-matrix column meaning
#: cannot drift from the calibration or ceiling covariate order.
CASE_COVARIATE_ORDER: tuple[str, ...] = GRAMMAR_PRIMITIVES

#: PySR's default feature naming, positionally aliased to the frozen order --
#: the same mapping ``g2_contract._FEATURE_NAME_ALIASES`` binds, restated here
#: as data so the adapter's own column contract is checkable.
FEATURE_NAME_ALIASES: dict[str, str] = {
    f"x{index}": name for index, name in enumerate(CASE_COVARIATE_ORDER)
}


class GrammarSettingsError(RuntimeError):
    """The frozen search settings do not describe the frozen grammar."""


def assert_grammar_settings() -> dict[str, object]:
    """Fail loudly unless the grammar is exactly the frozen one.

    Guards the two failure modes A3.5 forbids by name: an excluded operator
    appearing in the grammar (section 10.2's ``exp``, added "to help F18"), and
    any operator-set expansion at all.
    """
    binary = list(SEARCH_SETTINGS["binary_operators"])
    unary = list(SEARCH_SETTINGS["unary_operators"])
    excluded = set(SEARCH_SETTINGS["excluded_unary"])
    if binary != ["+", "-", "*", "/"]:
        raise GrammarSettingsError(f"binary operators are not the frozen set: {binary}")
    if unary != ["sqrt", "log", "square", "cube", "inv"]:
        raise GrammarSettingsError(f"unary operators are not the frozen set: {unary}")
    overlap = excluded.intersection(unary)
    if overlap:
        raise GrammarSettingsError(f"excluded operators present in grammar: {overlap}")
    if "exp" in unary:
        raise GrammarSettingsError(
            "exp is in the grammar; A3.5 section 10.2 binds 'Bound response: none' "
            "to F18's representability limitation -- the grammar is not changed"
        )
    return {"binary_operators": binary, "unary_operators": unary,
            "excluded_unary": sorted(excluded)}


# -----------------------------------------------------------------------
# The design
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseDesign:
    """One case's search design: rows, columns, target, splits."""

    compound_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    design: np.ndarray          # (n_compounds, 5)
    target: np.ndarray          # (n_compounds,) raw g
    splits: tuple[str, ...]

    def mask(self, split: str) -> np.ndarray:
        return np.asarray([s == split for s in self.splits], dtype=bool)

    @property
    def train_mask(self) -> np.ndarray:
        return self.mask(TRAIN_SPLIT)

    @property
    def validation_mask(self) -> np.ndarray:
        return self.mask(VALIDATION_SPLIT)

    @property
    def test_mask(self) -> np.ndarray:
        return self.mask(TEST_SPLIT)


def build_case_design(compounds: pd.DataFrame, scalars: CaseScalars) -> CaseDesign:
    """Assemble the frozen design: one row per compound, five columns, raw g.

    No weight column is produced and no row is dropped.  Section 4.3 struck the
    inverse-variance weight channel outright (the A3.2 null was computed fully
    unweighted, and "weight"/"g_var" appear nowhere in the calibration path), so
    a weight vector has nowhere legitimate to go and is simply never built.
    """
    compound_ids = tuple(str(c) for c in compounds["compound_id"])
    if compound_ids != scalars.compound_ids:
        raise ValueError(
            "compound frame and scalar estimates disagree on row order or membership"
        )
    missing = [c for c in CASE_COVARIATE_ORDER if c not in compounds.columns]
    if missing:
        raise ValueError(f"case covariates missing from frame: {missing}")

    design = np.column_stack(
        [np.asarray(compounds[c], dtype=np.float64) for c in CASE_COVARIATE_ORDER]
    )
    target = np.asarray(scalars.g, dtype=np.float64)
    if target.shape[0] != design.shape[0]:
        raise ValueError("target and design row counts disagree")

    return CaseDesign(
        compound_ids=compound_ids,
        feature_names=CASE_COVARIATE_ORDER,
        design=design,
        target=target,
        splits=tuple(str(s) for s in compounds["split"]),
    )


# -----------------------------------------------------------------------
# Gate-2 input provenance
# -----------------------------------------------------------------------

def row_position(equations: pd.DataFrame, label: Any) -> int:
    """Convert a pandas **label** to a **position** (section 7.2, mandatory).

    ``idx_model_selection`` returns a label; ``predict(index=...)`` and
    ``.iloc[]`` take positions.  Conflating them silently scores the wrong row,
    which is why this conversion is a named function with its own test rather
    than an inline expression.
    """
    return int(equations.index.get_loc(label))


def row_complexity(equations: pd.DataFrame, label: Any) -> int:
    """PySR's own complexity for one row -- the null table's complexity axis.

    Deliberately **not** ``grammar.complexity(parse(...))``, which diverges
    upward and would look up a bar the candidate was never calibrated against.
    """
    return int(equations["complexity"].iloc[row_position(equations, label)])


def candidate_r2_on(
    model: Any,
    equations: pd.DataFrame,
    label: Any,
    design: np.ndarray,
    target: np.ndarray,
    mask: np.ndarray,
) -> float:
    """Unweighted R2 of one emitted row on a masked row set.

    Exactly ``rc3_calibration_runner._r2`` on
    ``model.predict(design[mask], index=row)``, which is the null's own axis:
    plain R2, no sample weights, no invalid masking.  Zero target variance
    yields ``-inf``, the frozen sentinel.
    """
    position = row_position(equations, label)
    predictions = np.asarray(
        model.predict(design[mask], index=position), dtype=np.float64
    )
    return _r2(np.asarray(target, dtype=np.float64)[mask], predictions)


# -----------------------------------------------------------------------
# The regressor
# -----------------------------------------------------------------------

def build_case_regressor(seed: int, work_dir: Path | None = None):
    """A PySR regressor under the frozen settings, for one case seed.

    Mirrors ``rc3_calibration_runner.PySRBackend._make_regressor`` exactly,
    with two deliberate differences, both bound:

    * ``niterations`` has **no override path** -- the calibration backend's
      override exists solely for the quarantined engineering smoke, which has
      no analogue on the production case path.
    * ``model_selection`` is **not set on the regressor** (section 7.1,
      implementation obligation 6): retention is applied to the emitted
      ``equations_`` frame, so the engine's own ``.predict()`` path is never
      implicitly re-selected.
    """
    assert_grammar_settings()
    from pysr import PySRRegressor

    kwargs: dict[str, object] = dict(
        binary_operators=list(SEARCH_SETTINGS["binary_operators"]),
        unary_operators=list(SEARCH_SETTINGS["unary_operators"]),
        maxsize=int(SEARCH_SETTINGS["maxsize"]),
        niterations=int(SEARCH_SETTINGS["niterations"]),
        populations=int(SEARCH_SETTINGS["populations"]),
        population_size=int(SEARCH_SETTINGS["population_size"]),
        parsimony=float(SEARCH_SETTINGS["parsimony"]),
        adaptive_parsimony_scaling=float(
            SEARCH_SETTINGS["adaptive_parsimony_scaling"]
        ),
        deterministic=bool(SEARCH_SETTINGS["deterministic"]),
        parallelism="serial",
        random_state=int(seed),
        progress=False,
        verbosity=0,
        temp_equation_file=True,
    )
    if work_dir is not None:
        kwargs["tempdir"] = str(work_dir)
    return PySRRegressor(**kwargs)


def assert_selected_complexity_in_range(complexity: int) -> None:
    """Section 7.6: a selected row outside 1..20 is an ``EXECUTION_FAILURE``.

    Matching the calibration canary rather than silently dropping the row.
    """
    if not (1 <= complexity <= MAX_COMPLEXITY):
        raise ValueError(
            f"selected row complexity {complexity} outside 1..{MAX_COMPLEXITY}"
        )
