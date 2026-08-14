"""Engineering RC3: ceiling estimator wiring.

The estimator, its hyperparameters, its dependency pin and its train/score
partitions are frozen in ``structural_acceptance.CEILING_ESTIMATOR_SPEC``.
This module imports that spec rather than restating it, constructs the
estimator from it, and refuses to run under any scikit-learn other than the
pinned version.

    HistGradientBoostingRegressor(
        max_iter=150, max_depth=3, min_samples_leaf=20, random_state=0)
    scikit-learn == 1.9.0   (requirements.lock.txt at c7c2332)

Train on the ``train`` partition.  Score on the ``test`` partition.
The covariate order is frozen and is the grammar primitive order.

Gates (already frozen, restated only as executable enforcement):
    ceiling_fraction >= 0.80          strict as written: >=
    waiver at ceiling_r2 < 0.05       strict as written: <
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .g2_contract import GRAMMAR_PRIMITIVES
from .structural_acceptance import (
    CEILING_ESTIMATOR_SPEC,
    CEILING_FRACTION_GATE,
    CEILING_WAIVER_THRESHOLD,
)

__all__ = [
    "REQUIRED_SKLEARN_VERSION",
    "CEILING_COVARIATE_ORDER",
    "SklearnVersionError",
    "assert_sklearn_version",
    "build_ceiling_estimator",
    "CeilingEstimate",
    "estimate_ceiling",
]

#: Parsed from the frozen spec so the pin can only be changed by editing the
#: frozen module, which RC3 may not do.
REQUIRED_SKLEARN_VERSION = CEILING_ESTIMATOR_SPEC["dependency"].split("==", 1)[1]

#: Frozen covariate order.  Identical to the protected grammar primitive
#: order, so the design matrix column meaning cannot drift.
CEILING_COVARIATE_ORDER: tuple[str, ...] = GRAMMAR_PRIMITIVES

TRAIN_PARTITION = CEILING_ESTIMATOR_SPEC["train_partition"]
SCORE_PARTITION = CEILING_ESTIMATOR_SPEC["score_partition"]


class SklearnVersionError(RuntimeError):
    """Raised when the installed scikit-learn is not the pinned version."""


def assert_sklearn_version() -> str:
    """Fail loudly unless scikit-learn is exactly the pinned version."""
    try:
        import sklearn
    except ImportError as exc:  # pragma: no cover - environment failure
        raise SklearnVersionError(
            f"scikit-learn is not installed; {CEILING_ESTIMATOR_SPEC['dependency']} "
            f"is required ({CEILING_ESTIMATOR_SPEC['provenance']})"
        ) from exc

    installed = sklearn.__version__
    if installed != REQUIRED_SKLEARN_VERSION:
        raise SklearnVersionError(
            f"scikit-learn {installed} is installed but "
            f"{REQUIRED_SKLEARN_VERSION} is required exactly "
            f"({CEILING_ESTIMATOR_SPEC['provenance']}). "
            f"The ceiling estimate is not comparable across versions; refusing to run."
        )
    return installed


def build_ceiling_estimator():
    """Construct the frozen ceiling estimator.

    Guards the version first, so a wrong environment fails before any
    numbers exist to be tempted by.
    """
    assert_sklearn_version()
    from sklearn.ensemble import HistGradientBoostingRegressor

    model = HistGradientBoostingRegressor(**CEILING_ESTIMATOR_SPEC["params"])

    # Check the object actually constructed, not the name it was imported by.
    expected_class = CEILING_ESTIMATOR_SPEC["class"]
    expected_name = expected_class.rsplit(".", 1)[-1]
    if type(model).__name__ != expected_name:
        raise SklearnVersionError(  # pragma: no cover - spec is frozen
            f"frozen spec names {expected_class}, constructed "
            f"{type(model).__module__}.{type(model).__name__}"
        )
    for key, value in CEILING_ESTIMATOR_SPEC["params"].items():
        actual = getattr(model, key, None)
        if actual != value:
            raise SklearnVersionError(  # pragma: no cover - constructor honours kwargs
                f"ceiling estimator {key} is {actual!r}, frozen spec requires {value!r}"
            )

    return model


def _design_matrix(compounds, covariate_order: Sequence[str] = CEILING_COVARIATE_ORDER) -> np.ndarray:
    missing = [c for c in covariate_order if c not in compounds.columns]
    if missing:
        raise ValueError(f"ceiling covariates missing from frame: {missing}")
    return np.column_stack(
        [np.asarray(compounds[c], dtype=np.float64) for c in covariate_order]
    )


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of determination against the mean of ``y_true``.

    A constant target on the scoring partition makes R2 undefined.  That is a
    data defect, and it raises: returning ``-inf`` would flow straight into
    ``ceiling_r2 < 0.05`` and silently *satisfy* the frozen waiver, turning a
    broken partition into a passed gate.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    if ss_tot == 0.0:
        raise ValueError(
            "ceiling R2 is undefined: the target is constant on the "
            f"'{SCORE_PARTITION}' partition"
        )
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    return 1.0 - ss_res / ss_tot


@dataclass(frozen=True)
class CeilingEstimate:
    """The ceiling comparison for one case."""

    ceiling_r2: float
    candidate_r2: float
    ceiling_fraction: float
    gate_passed: bool
    waiver_applied: bool
    sklearn_version: str

    @property
    def ceiling_satisfied(self) -> bool:
        """Gate 7 of the frozen acceptance predicate."""
        return self.gate_passed or self.waiver_applied


def estimate_ceiling(
    compounds,
    target: np.ndarray,
    candidate_test_r2: float,
    split_column: str = "split",
) -> CeilingEstimate:
    """Fit the frozen ceiling estimator and compare a candidate against it.

    Parameters
    ----------
    compounds
        Frame carrying the frozen covariates and a ``split`` column whose
        values include ``train`` and ``test``.
    target
        Per-compound scalar target, aligned to ``compounds`` row order.
    candidate_test_r2
        The candidate expression's R2 on the ``test`` partition.  Supplied by
        the caller; this function never refits the candidate.

    Notes
    -----
    ``ceiling_fraction`` is ``candidate_r2 / ceiling_r2``.  When the ceiling
    itself is non-positive the fraction is not meaningful, so it is reported
    as ``-inf`` and only the frozen waiver (``ceiling_r2 < 0.05``) can carry
    the case past gate 7.
    """
    version = assert_sklearn_version()

    if split_column not in compounds.columns:
        raise ValueError(f"frame has no '{split_column}' column")

    target = np.asarray(target, dtype=np.float64)
    if len(target) != len(compounds):
        raise ValueError(
            f"target has {len(target)} rows, frame has {len(compounds)}"
        )

    splits = np.asarray(compounds[split_column], dtype=object)
    train_mask = splits == TRAIN_PARTITION
    score_mask = splits == SCORE_PARTITION

    if not train_mask.any():
        raise ValueError(f"no rows in the '{TRAIN_PARTITION}' partition")
    if not score_mask.any():
        raise ValueError(f"no rows in the '{SCORE_PARTITION}' partition")

    design = _design_matrix(compounds)

    model = build_ceiling_estimator()
    model.fit(design[train_mask], target[train_mask])
    predictions = model.predict(design[score_mask])

    ceiling_r2 = _r2(target[score_mask], predictions)

    if ceiling_r2 > 0.0:
        fraction = candidate_test_r2 / ceiling_r2
    else:
        fraction = float("-inf")

    return CeilingEstimate(
        ceiling_r2=ceiling_r2,
        candidate_r2=float(candidate_test_r2),
        ceiling_fraction=float(fraction),
        gate_passed=bool(fraction >= CEILING_FRACTION_GATE),
        waiver_applied=bool(ceiling_r2 < CEILING_WAIVER_THRESHOLD),
        sklearn_version=version,
    )
