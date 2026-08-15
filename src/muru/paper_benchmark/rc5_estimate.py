"""Engineering RC5 (D14): the benchmark profile ``Phi``, the per-compound ``g``,
the symbolic search target, and ``invalid_fraction``.

Bound by Amendment A3.5 section 4.  Every rule below is that section's; this
module states none of its own.

Section 4.1 -- ``Phi``
---------------------
Estimated **on the training fold only**, then **frozen**, by: isotonic
projection (monotone decreasing) of the observed ``(log u, mu)`` pairs of the
training compounds with ``u = (E / E_REF) / g``; **60 knots** on a uniform
``log u`` grid with ``np.minimum.accumulate``; **linear interpolation** between
knots; **flat boundary clamp** outside the knot range.  That is exactly
``discovery.estimate._fit_phi`` / ``_phi_eval``, which section 4.1 verified
present and exact -- so this module *reuses those two functions verbatim*
rather than restating them.

Three corrections section 4.1 makes, all implemented here:

1. **Fold-locality.**  ``estimate.fit_collapse`` alternates over *all* supplied
   compounds.  A3.5 requires a two-stage call: fit ``Phi`` on the **120
   training compounds only**, freeze it, then estimate ``g`` for all compounds
   against that frozen ``Phi``.  "This is new code, not call-site discipline."
2. **No re-centring after the freeze.**  ``fit_collapse`` applies
   ``log_g -= log_g.mean()`` *inside* its alternation loop
   (``estimate.py:109``), because ``g`` is scale-identified only while ``Phi``
   is still moving.  Once ``Phi`` is frozen the re-centring MUST NOT be
   applied: it would shift every ``g`` relative to a fixed ``Phi``, breaking
   ``(Phi, g)`` consistency and corrupting ``trajectory_mae``.  The alternation
   below keeps it; :func:`estimate_case_g` does not have it.
3. **Energy scale.**  The scale is the paper benchmark's own frozen
   ``E_REF = 45.0`` (``adequacy.py``), matching the generator's
   ``u = (energy / 45.0) / g``.  It is **NOT**
   ``discovery/estimate.py``'s module constant ``ENERGY_SCALE = 30.0``, which
   belongs to the Phase-3 real-data track: normalising by 30 against a truth
   generated on 45 rescales every ``g_hat`` by 2/3.  ``valid_r2``
   (affine-invariant) and ``g_spearman`` (rank-based) would absorb that
   silently, but **A3.4 parameter recovery would not**.  Section 4.1 therefore
   requires any reuse of ``estimate.py`` to **parameterise** the scale, which
   is why :func:`_best_log_g` is written here instead of imported: the frozen
   one divides by its module constant.

Grid provenance, stated rather than assumed
-------------------------------------------
Section 4.1: "A3.5 must not silently inherit ``estimate.py``'s
``LOG_G_GRID = linspace(-1.6, 1.6, 241)`` or ``N_ALTERNATIONS = 3`` ... the
A3.5 ``g`` estimator's grid MUST be **stated explicitly rather than
imported**."  The remedy that sentence names is explicit statement, not a
different number -- and section 4.2 independently binds the estimator to
"grid search plus parabolic refinement (``estimate._best_log_g``)", section
6.8's ledger admits no new constant, and section 12 forbids changing the ``g``
estimator.  So the values below are **transcribed** from ``estimate.py`` and
**owned** by A3.5: identical arithmetic, different ownership.  A later edit to
the Phase-3 module can no longer move the benchmark silently, which is the
entire point of the prohibition.  No number here was chosen, tuned, or adjusted
against any observed benchmark outcome.

Section 4.2 -- per-compound ``g``
---------------------------------
"A genuine per-compound A1 M0 fit against the frozen ``Phi``: for each
compound, the scalar minimising the sum of squared ``mu`` residuals over that
compound's own observed energies, by grid search plus parabolic refinement,
evaluated against the **frozen** ``Phi``."  ``protocol.estimate_one`` is
**excluded** by name: it evaluates no ``Phi`` curve at all.

This estimator is deliberately distinct from G1's trajectory scalar (section
5.2): that one is a **leave-one-energy-out** aggregate under **A1.2's** own
protocol.  Using LOEO for the search target, or a point estimate for
``MAE_0``, are both errors.  See :mod:`muru.paper_benchmark.rc5_g1_bridge`.

Sections 4.3, 4.4 -- target, rows, covariates, ``invalid_fraction``
--------------------------------------------------------------------
Target: the **raw, untransformed** ``g`` -- not ``log g``, not reweighted, not
renormalised.  Rows: **one row per compound**.  Covariates: exactly the five
``GRAMMAR_PRIMITIVES``, in frozen order.  Weights: **none**.  Row filtering:
**none** -- F04/F05-flagged compounds are not dropped.  ``invalid_fraction``:
the representative candidate's predictions on the case's **validation** rows,
under ``grammar.finite_mask``, over a denominator of **30**.

This module reads no planted truth and branches on no partition label.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from muru.discovery.estimate import _fit_phi, _phi_eval
from muru.discovery.grammar import finite_mask

from .adequacy import E_REF
from .structural_acceptance import MAX_INVALID_FRACTION

__all__ = [
    "E_REF",
    "PHI_N_KNOTS",
    "PHI_ALTERNATIONS",
    "A35_LOG_G_GRID_LOW",
    "A35_LOG_G_GRID_HIGH",
    "A35_LOG_G_GRID_POINTS",
    "A35_LOG_G_GRID",
    "TRAIN_SPLIT",
    "VALIDATION_SPLIT",
    "TEST_SPLIT",
    "N_VALIDATION_COMPOUNDS",
    "FrozenPhi",
    "fit_case_phi",
    "estimate_case_g",
    "CaseScalars",
    "fit_case_scalars",
    "invalid_fraction",
]

#: Section 4.1, step 2.
PHI_N_KNOTS = 60

#: Transcribed from ``estimate.N_ALTERNATIONS``; owned by A3.5 (see the module
#: docstring's "Grid provenance").  Governs the training-fold alternation that
#: produces ``Phi``, never anything after the freeze.
PHI_ALTERNATIONS = 3

#: Transcribed from ``estimate.LOG_G_GRID``; owned by A3.5.  Stated as three
#: scalars so the grid is literally readable here rather than imported.
A35_LOG_G_GRID_LOW = -1.6
A35_LOG_G_GRID_HIGH = 1.6
A35_LOG_G_GRID_POINTS = 241
A35_LOG_G_GRID = np.linspace(
    A35_LOG_G_GRID_LOW, A35_LOG_G_GRID_HIGH, A35_LOG_G_GRID_POINTS
)

#: The parabolic-refinement vertex coefficient and degenerate-curvature guard,
#: transcribed verbatim from ``estimate._best_log_g``.  Named rather than left
#: inline so a reviewer auditing numeric literals can trace both to the frozen
#: mechanism section 4.2 binds.  Neither is a threshold: ``0.5`` is the vertex
#: formula's own coefficient, and the guard only avoids dividing by a
#: numerically flat curvature.
_PARABOLIC_VERTEX_COEFFICIENT = 0.5
_PARABOLIC_DEGENERACY_GUARD = 1e-15

TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
TEST_SPLIT = "test"

#: Section 4.4: real cases use 120 / 30 / 30 compounds (``generator.py``'s
#: 20/5/5 scaffold groups x 6), so ``invalid_fraction``'s denominator is 30 --
#: NOT the calibration worlds' 36 (18/6/6 groups).
N_VALIDATION_COMPOUNDS = 30


# -----------------------------------------------------------------------
# The frozen profile
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class FrozenPhi:
    """A training-fold profile, frozen.

    ``knots`` are ``log u`` positions and ``values`` the isotonic knot values,
    exactly the pair ``estimate._fit_phi`` returns.  ``e_ref`` travels with the
    object so a consumer cannot evaluate it under a different energy scale than
    it was fitted under.
    """

    knots: np.ndarray
    values: np.ndarray
    e_ref: float
    n_knots: int
    n_training_compounds: int
    alternations: int

    def evaluate(self, u: np.ndarray) -> np.ndarray:
        """Linear interpolation between knots, flat clamp outside."""
        return _phi_eval(self.knots, self.values, np.asarray(u, dtype=np.float64))

    def identity(self) -> dict[str, object]:
        """Reproducibility projection: the shape, not the data it came from."""
        return {
            "e_ref": float(self.e_ref),
            "n_knots": int(self.n_knots),
            "alternations": int(self.alternations),
            "n_training_compounds": int(self.n_training_compounds),
            "knots": [float(v) for v in self.knots],
            "values": [float(v) for v in self.values],
        }


def _wide(
    trajectories: pd.DataFrame, compound_ids: Sequence[str]
) -> tuple[np.ndarray, np.ndarray]:
    """``(energies, mu matrix)`` for ``compound_ids``, NaN for missing cells.

    Row order follows ``compound_ids`` exactly, so the caller's ordering -- not
    a pivot's sort -- decides which row is which compound.
    """
    pivot = trajectories.pivot_table(
        index="compound_id", columns="energy", values="mu"
    )
    pivot = pivot.reindex(list(compound_ids))
    energies = np.asarray(pivot.columns, dtype=np.float64)
    return energies, pivot.to_numpy(dtype=np.float64)


def _best_log_g(
    energies: np.ndarray,
    mu: np.ndarray,
    knots: np.ndarray,
    values: np.ndarray,
    e_ref: float,
    grid: np.ndarray = A35_LOG_G_GRID,
) -> np.ndarray:
    """Per-compound scale by grid search plus parabolic refinement.

    Section 4.2's estimator.  Mechanically identical to
    ``estimate._best_log_g`` except that the energy scale is a **parameter**
    rather than that module's ``ENERGY_SCALE = 30.0`` -- the one change section
    4.1 requires of any reuse.  Missing cells contribute nothing, so a compound
    is fitted over its own observed energies only.
    """
    scaled = np.asarray(energies, dtype=np.float64) / float(e_ref)
    observed = np.isfinite(mu)
    sse = np.empty((mu.shape[0], len(grid)), dtype=np.float64)
    for index, log_g in enumerate(grid):
        prediction = _phi_eval(knots, values, scaled / np.exp(log_g))
        residual = np.where(observed, mu - prediction[None, :], 0.0)
        sse[:, index] = (residual * residual).sum(1)
    argmin = np.argmin(sse, axis=1)
    out = grid[argmin].astype(np.float64)
    interior = (argmin > 0) & (argmin < len(grid) - 1)
    if interior.any():
        # Parabolic refinement on the interior minimum, transcribed verbatim
        # from ``estimate._best_log_g`` -- the mechanism section 4.2 names.  The
        # ``0.5`` is the vertex formula's own coefficient and the ``1e-15`` is
        # that function's own degenerate-curvature guard; neither is a threshold
        # and neither was chosen here.
        rows = np.where(interior)[0]
        left = sse[rows, argmin[rows] - 1]
        centre = sse[rows, argmin[rows]]
        right = sse[rows, argmin[rows] + 1]
        denominator = left - 2 * centre + right
        step = np.where(
            np.abs(denominator) > _PARABOLIC_DEGENERACY_GUARD,
            _PARABOLIC_VERTEX_COEFFICIENT * (left - right) / denominator,
            0.0,
        )
        out[rows] = grid[argmin[rows]] + np.clip(step, -1, 1) * (grid[1] - grid[0])
    return out


def fit_case_phi(
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
    e_ref: float = E_REF,
    n_knots: int = PHI_N_KNOTS,
    alternations: int = PHI_ALTERNATIONS,
) -> FrozenPhi:
    """Fit ``Phi`` on the training compounds only, then freeze it.

    The alternation keeps ``fit_collapse``'s in-loop ``log_g -= log_g.mean()``,
    which is correct and required *while* ``Phi`` is still moving.  Nothing
    downstream of the returned object re-centres anything.
    """
    training = compounds.loc[compounds["split"] == TRAIN_SPLIT, "compound_id"]
    training_ids = [str(c) for c in training]
    if not training_ids:
        raise ValueError("no training compounds: Phi cannot be fold-local")

    energies, mu = _wide(trajectories, training_ids)
    scaled = energies / float(e_ref)
    observed = np.isfinite(mu)
    if not observed.any():
        raise ValueError("training compounds have no observed responses")

    log_g = np.zeros(len(training_ids), dtype=np.float64)
    knots = values = None
    for _ in range(alternations):
        u = scaled[None, :] / np.exp(log_g)[:, None]
        knots, values = _fit_phi(u[observed], mu[observed], n_knots=n_knots)
        log_g = _best_log_g(energies, mu, knots, values, e_ref)
        # Inside the loop only: g is scale-identified while Phi still moves.
        log_g = log_g - log_g.mean()

    u = scaled[None, :] / np.exp(log_g)[:, None]
    knots, values = _fit_phi(u[observed], mu[observed], n_knots=n_knots)

    return FrozenPhi(
        knots=np.asarray(knots, dtype=np.float64),
        values=np.asarray(values, dtype=np.float64),
        e_ref=float(e_ref),
        n_knots=int(n_knots),
        n_training_compounds=len(training_ids),
        alternations=int(alternations),
    )


def estimate_case_g(
    frozen_phi: FrozenPhi,
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
) -> np.ndarray:
    """Per-compound raw ``g`` against the frozen ``Phi``, in frame row order.

    **No re-centring.**  Section 4.1 makes this a binding: once ``Phi`` is
    frozen, subtracting the mean of ``log_g`` would shift every ``g`` relative
    to a fixed profile.  There is deliberately no ``.mean()`` anywhere in this
    function.
    """
    compound_ids = [str(c) for c in compounds["compound_id"]]
    energies, mu = _wide(trajectories, compound_ids)
    log_g = _best_log_g(
        energies, mu, frozen_phi.knots, frozen_phi.values, frozen_phi.e_ref
    )
    return np.exp(log_g)


# -----------------------------------------------------------------------
# The case's search-target bundle
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseScalars:
    """One case's frozen ``Phi`` and its per-compound raw ``g``."""

    compound_ids: tuple[str, ...]
    splits: tuple[str, ...]
    g: np.ndarray
    frozen_phi: FrozenPhi

    def g_by_compound(self) -> dict[str, float]:
        return {c: float(v) for c, v in zip(self.compound_ids, self.g)}

    def mask(self, split: str) -> np.ndarray:
        return np.asarray([s == split for s in self.splits], dtype=bool)


def fit_case_scalars(
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
    e_ref: float = E_REF,
) -> CaseScalars:
    """The two-stage fit of section 4.1, as one call.

    Stage 1 freezes ``Phi`` on the 120 training compounds.  Stage 2 estimates
    ``g`` for **all** compounds against that frozen profile.  No compound is
    filtered: section 4.3 binds "Row filtering: none", and F04's five observed
    energies still meet A1's ``MIN_OBSERVED_ENERGIES = 5``.
    """
    frozen_phi = fit_case_phi(compounds, trajectories, e_ref=e_ref)
    g = estimate_case_g(frozen_phi, compounds, trajectories)
    return CaseScalars(
        compound_ids=tuple(str(c) for c in compounds["compound_id"]),
        splits=tuple(str(s) for s in compounds["split"]),
        g=np.asarray(g, dtype=np.float64),
        frozen_phi=frozen_phi,
    )


# -----------------------------------------------------------------------
# invalid_fraction
# -----------------------------------------------------------------------

def invalid_fraction(
    predictions: np.ndarray,
    denominator: int = N_VALIDATION_COMPOUNDS,
) -> float:
    """Section 4.4, exactly.

    Domain: the case's validation rows.  Predicate: ``grammar.finite_mask``.
    Denominator: **30**, the real-case validation compound count -- not the
    calibration worlds' 36.  The gate is ``<= 0.005``, so the operative effect
    is zero invalid rows tolerated (``1/30 = 0.0333 > 0.005``).
    """
    values = np.asarray(predictions, dtype=np.float64)
    if values.size != denominator:
        raise ValueError(
            f"invalid_fraction expects {denominator} validation predictions, "
            f"got {values.size}"
        )
    return float(np.count_nonzero(~finite_mask(values))) / float(denominator)


def invalid_fraction_passes(value: float) -> bool:
    """The frozen A3.1 gate, restated only as executable enforcement."""
    return value <= MAX_INVALID_FRACTION
