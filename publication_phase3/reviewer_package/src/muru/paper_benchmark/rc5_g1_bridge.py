"""Engineering RC5 (D8): the G1 scalar-competence bridge.

G1 is frozen content, not new design.  ``docs/superpowers/specs/``'s benchmark
design (blob ``80f20e2f``, byte-identical at ``d94d2c9`` and at ``69e33c7``)
already states it verbatim:

    A scalar-applicable held-out case is competent only when all three
    conditions hold: its fold-local ``g`` estimate has Spearman correlation at
    least 0.80 with true log-``g`` across the test compounds; its frozen
    training-only ``Phi`` predicts test trajectories with MAE no greater than
    0.80 of the training-only per-energy-mean baseline MAE; and the M0 adequacy
    ladder does not reject M0.  The G1 rate uses the 164-case scalar
    denominator and passes only when its lower 95% Wilson bound is at least
    0.70.

A3.5 section 5.2 binds the operational detail **by citation to A1.3/A1.4**, not
by new derivation.  ``trajectory_mae`` *is* the case-level aggregate of
``MAE_0,i``, A1.3's already-frozen within-compound leave-one-energy-out M0
prediction error.

The in-sample reading is struck
--------------------------------
An earlier draft fitted ``g_hat_i`` on **all** of test compound ``i``'s
observed energies and then scored on **those same cells** -- a one-free-
parameter in-sample fit compared against a zero-free-parameter out-of-sample
baseline, structurally biased toward passing G1.  Section 5.2 strikes it, on
A1.3's own constraint that "the omitted energy may not influence either fit
used to predict it" and the frozen spec's requirement of **out-of-sample**
trajectory prediction.  :func:`loeo_mae_0` therefore omits energy ``e`` from
the fit that predicts ``mu_i(e)``, and a dedicated test proves it.

Two ``g`` objects, deliberately distinct
-----------------------------------------
============================  ==================  =======================
object                        scheme              fitter
============================  ==================  =======================
G1 trajectory scalar          leave-one-energy-   **A1.2's** frozen 81-point
(``MAE_0,i``)                 out (A1.3)          coarse-to-fine protocol
Search-target scalar          point estimate      section 4.2's estimator
(the raw ``g`` for PySR)                          (:mod:`rc5_estimate`)
============================  ==================  =======================

Using LOEO for the search target, or a point estimate for ``MAE_0``, are both
errors.  ``g_spearman``'s left-hand side is the **point estimate**, per section
5.2's own table.

A1.2's protocol, and the one composition detail it leaves implicit
-------------------------------------------------------------------
Every constant is read from ``adequacy.py``: ``LOG_G_BOUNDS = (-2.0, 2.0)``,
``COARSE_LOG_G_POINTS = 81`` (endpoint-inclusive), ``REFINEMENT_ROUNDS = 3``,
``REFINEMENT_POINTS = 21``, ``REFINEMENT_SHRINK = 10``, objective
``unweighted_sum_of_squared_mu_residuals``, lexicographic tie-break.  This is
explicitly **not** ``estimate._best_log_g``'s 241-point ``[-1.6, 1.6]`` grid
with parabolic refinement.

``adequacy.py`` states its own scope boundary -- it "deliberately contains no
fitter, no optimiser, and no numerical model evaluation" -- so the protocol
exists as a frozen specification and RC5 implements it.  The single detail the
specification leaves implicit is how "shrink 10" composes across rounds; it is
resolved conservatively and stated here rather than chosen silently: each
round's window is the previous window's width divided by ``REFINEMENT_SHRINK``,
centred on the running best and clipped to ``LOG_G_BOUNDS``.  No constant is
invented and no bound is widened.

Sealed-boundary ordering
-------------------------
``g_spearman`` legitimately reads ``TruthRecord.g_by_compound`` -- G1 is a
post-hoc scoring endpoint, not the acceptance predicate -- but that read must
happen strictly **after** ``acceptance_status`` is already derived from the
truth-blind path.  :func:`score_case_g1` takes the already-derived
``CaseAdequacyStatus`` as a required argument, so the ordering is enforced by
the signature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .adequacy import (
    COARSE_LOG_G_POINTS,
    LOG_G_BOUNDS,
    MIN_EVALUABLE_COMPOUNDS,
    MIN_OBSERVED_ENERGIES,
    MIN_VERTICAL_AMPLITUDE,
    N_TEST_COMPOUNDS_EXPECTED,
    REFINEMENT_POINTS,
    REFINEMENT_ROUNDS,
    REFINEMENT_SHRINK,
    CaseAdequacyStatus,
    adequacy_satisfies_g1,
)
from .g2_contract import wilson_lower_95
from .registry import endpoint_case_count
from .rc5_estimate import TEST_SPLIT, TRAIN_SPLIT, FrozenPhi

__all__ = [
    "G1_SPEARMAN_GATE",
    "G1_TRAJECTORY_RATIO_GATE",
    "G1_DENOMINATOR",
    "G1_WILSON_LOWER_GATE",
    "M0Profile",
    "m0_profile_from_phi",
    "fit_log_g_a1_protocol",
    "loeo_mae_0",
    "per_energy_mean_mae",
    "CaseG1",
    "score_case_g1",
    "G1Score",
    "score_g1",
]

#: The frozen G1 thresholds, quoted from the content-freeze text.  None is
#: introduced here.
G1_SPEARMAN_GATE = 0.80
G1_TRAJECTORY_RATIO_GATE = 0.80
G1_WILSON_LOWER_GATE = 0.70

#: Computed from the frozen registry, never restated as a literal.
G1_DENOMINATOR = endpoint_case_count("scalar_competence")


# -----------------------------------------------------------------------
# A1's M0
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class M0Profile:
    """A1's M0 predictor, built from the frozen training-only ``Phi``.

    ``mu_i(E) = A_HI + (A_LO - A_HI) * S(E / g_i)`` with
    ``S(t) = clip((Phi(t) - A_HI) / (A_LO - A_HI), 0, 1)``.

    ``A_LO`` and ``A_HI`` are ``Phi``'s own asymptotes -- its flat-clamp values
    at the low-``u`` and high-``u`` ends, which section 4.1 fixes as
    ``vals[0]`` and ``vals[-1]``.  Because ``Phi`` is monotone non-increasing
    and already lies between them, the composed predictor equals ``Phi``
    evaluated at ``u``; the decomposition is retained because A1's
    contract-failure guard is stated on ``A_LO - A_HI``, and because the model
    form is A1's M0 rather than a bare ``Phi`` evaluation.
    """

    phi: FrozenPhi
    a_lo: float
    a_hi: float

    @property
    def vertical_amplitude(self) -> float:
        return float(self.a_lo - self.a_hi)

    @property
    def contract_failure(self) -> bool:
        """A1's guard, unchanged: amplitude below 0.05 is CONTRACT_FAILURE."""
        return self.vertical_amplitude < MIN_VERTICAL_AMPLITUDE

    def shape(self, t: np.ndarray) -> np.ndarray:
        amplitude = self.vertical_amplitude
        if amplitude <= 0.0:
            return np.zeros_like(np.asarray(t, dtype=np.float64))
        return np.clip((self.phi.evaluate(t) - self.a_hi) / amplitude, 0.0, 1.0)

    def predict(self, energies: np.ndarray, g: float) -> np.ndarray:
        t = (np.asarray(energies, dtype=np.float64) / self.phi.e_ref) / float(g)
        return self.a_hi + self.vertical_amplitude * self.shape(t)


def m0_profile_from_phi(phi: FrozenPhi) -> M0Profile:
    """A_LO / A_HI are Phi's own clamped asymptotes (section 4.1, step 4)."""
    return M0Profile(phi=phi, a_lo=float(phi.values[0]), a_hi=float(phi.values[-1]))


# -----------------------------------------------------------------------
# A1.2's fitting protocol
# -----------------------------------------------------------------------

def _sse(profile: M0Profile, energies: np.ndarray, mu: np.ndarray, log_g: float) -> float:
    residual = mu - profile.predict(energies, float(np.exp(log_g)))
    return float(np.sum(residual * residual))


def fit_log_g_a1_protocol(
    profile: M0Profile,
    energies: np.ndarray,
    mu: np.ndarray,
) -> float:
    """A1.2's frozen coarse-to-fine fit, exactly.

    81-point endpoint-inclusive coarse grid on ``LOG_G_BOUNDS``, then
    ``REFINEMENT_ROUNDS`` rounds of ``REFINEMENT_POINTS`` points, each round's
    window the previous width divided by ``REFINEMENT_SHRINK``, centred on the
    running best and clipped to the bounds.  Objective:
    unweighted sum of squared ``mu`` residuals.  Ties break lexicographically,
    i.e. toward the smallest ``log_g``.
    """
    low, high = LOG_G_BOUNDS
    grid = np.linspace(low, high, COARSE_LOG_G_POINTS)
    width = float(high - low)

    best = float(grid[0])
    best_sse = float("inf")
    for candidate in grid:
        value = _sse(profile, energies, mu, float(candidate))
        if value < best_sse:                       # strict: first wins a tie
            best, best_sse = float(candidate), value

    for _ in range(REFINEMENT_ROUNDS):
        width = width / REFINEMENT_SHRINK
        half = width / 2.0
        window = np.linspace(
            max(low, best - half), min(high, best + half), REFINEMENT_POINTS
        )
        for candidate in window:
            value = _sse(profile, energies, mu, float(candidate))
            if value < best_sse:                   # strict: first wins a tie
                best, best_sse = float(candidate), value
    return best


# -----------------------------------------------------------------------
# A1.3's leave-one-energy-out MAE_0
# -----------------------------------------------------------------------

def loeo_mae_0(
    profile: M0Profile,
    energies: np.ndarray,
    mu: np.ndarray,
) -> tuple[float, int]:
    """``MAE_0,i`` for one compound, and its observed-cell count.

    For each observed energy ``e``: **omit e**, fit M0's compound-specific
    parameter on the *other* observed energies with everything training-side
    frozen, then predict ``mu_i(e)``.  The omitted energy influences neither
    fit used to predict it, which is A1.3's constraint and the reason the
    struck in-sample reading is not reachable from here.
    """
    energies = np.asarray(energies, dtype=np.float64)
    mu = np.asarray(mu, dtype=np.float64)
    observed = np.isfinite(mu)

    errors: list[float] = []
    for index in np.where(observed)[0]:
        fit_mask = observed.copy()
        fit_mask[index] = False
        if not fit_mask.any():
            continue
        log_g = fit_log_g_a1_protocol(
            profile, energies[fit_mask], mu[fit_mask]
        )
        prediction = profile.predict(
            energies[index : index + 1], float(np.exp(log_g))
        )[0]
        errors.append(abs(float(mu[index]) - float(prediction)))
    if not errors:
        return float("nan"), 0
    return float(np.sum(errors)), len(errors)


def per_energy_mean_mae(
    training_mean_by_energy: Mapping[float, float],
    energies: np.ndarray,
    mu: np.ndarray,
) -> tuple[float, int]:
    """The training-only per-energy-mean baseline's absolute error.

    Predict every compound at energy ``E_j`` by the training-fold mean at
    ``E_j``.  A function of **training** rows only, so it never sees the test
    compound's data and is already out-of-sample: both sides of G1's ratio are
    out-of-sample, and the comparison is fair.  It needs no LOEO.
    """
    energies = np.asarray(energies, dtype=np.float64)
    mu = np.asarray(mu, dtype=np.float64)
    observed = np.isfinite(mu)
    errors: list[float] = []
    for index in np.where(observed)[0]:
        baseline = training_mean_by_energy.get(float(energies[index]))
        if baseline is None:
            continue
        errors.append(abs(float(mu[index]) - float(baseline)))
    if not errors:
        return float("nan"), 0
    return float(np.sum(errors)), len(errors)


# -----------------------------------------------------------------------
# The case-level bridge
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CaseG1:
    """One case's G1 quantities and its competence verdict."""

    case_id: str
    g_spearman: float
    trajectory_mae: float
    per_energy_mean_mae: float
    m0_accepted: bool
    cells: int
    evaluable_compounds: int
    contract_failure: bool

    @property
    def trajectory_pass(self) -> bool:
        return self.trajectory_mae <= G1_TRAJECTORY_RATIO_GATE * self.per_energy_mean_mae

    @property
    def spearman_pass(self) -> bool:
        return self.g_spearman >= G1_SPEARMAN_GATE

    @property
    def scalar_competent(self) -> bool:
        if self.contract_failure:
            return False
        return self.spearman_pass and self.trajectory_pass and self.m0_accepted


def _spearman(a: Sequence[float], b: Sequence[float]) -> float:
    """Spearman rank correlation, average ranks for ties."""
    x = pd.Series(np.asarray(a, dtype=np.float64)).rank()
    y = pd.Series(np.asarray(b, dtype=np.float64)).rank()
    if x.std(ddof=0) == 0 or y.std(ddof=0) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def score_case_g1(
    case_id: str,
    a1_status: CaseAdequacyStatus,
    frozen_phi: FrozenPhi,
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
    point_estimate_g: np.ndarray,
    true_g_by_compound: Mapping[str, float],
) -> CaseG1:
    """Score one case's G1 quantities.

    ``a1_status`` is required and consumed first: the truth-blind acceptance
    path must already have produced it before this function reads any planted
    truth.  ``true_g_by_compound`` is the only truth this module touches, and
    it feeds ``g_spearman`` alone.
    """
    profile = m0_profile_from_phi(frozen_phi)

    is_test = np.asarray([str(s) == TEST_SPLIT for s in compounds["split"]], dtype=bool)
    is_train = np.asarray([str(s) == TRAIN_SPLIT for s in compounds["split"]], dtype=bool)
    test_ids = [str(c) for c in compounds.loc[is_test, "compound_id"]]

    training_ids = set(str(c) for c in compounds.loc[is_train, "compound_id"])
    training_rows = trajectories[trajectories["compound_id"].astype(str).isin(training_ids)]
    training_mean = {
        float(energy): float(value)
        for energy, value in training_rows.groupby("energy")["mu"].mean().items()
    }

    pivot = trajectories.pivot_table(
        index="compound_id", columns="energy", values="mu"
    ).reindex(test_ids)
    energies = np.asarray(pivot.columns, dtype=np.float64)
    matrix = pivot.to_numpy(dtype=np.float64)

    model_error_sum = baseline_error_sum = 0.0
    model_cells = baseline_cells = 0
    evaluable = 0
    for row in range(matrix.shape[0]):
        mu = matrix[row]
        observed = int(np.count_nonzero(np.isfinite(mu)))
        if observed >= MIN_OBSERVED_ENERGIES:
            evaluable += 1
        model_sum, model_n = loeo_mae_0(profile, energies, mu)
        base_sum, base_n = per_energy_mean_mae(training_mean, energies, mu)
        # "Missing cells omitted from both sides over the identical cell set."
        if model_n != base_n:  # pragma: no cover - both use the same observed mask
            raise RuntimeError(
                "the model and the baseline saw different cell counts; A3.5 "
                "section 5.2 requires the identical cell set on both sides"
            )
        if model_n:
            model_error_sum += model_sum
            baseline_error_sum += base_sum
            model_cells += model_n
            baseline_cells += base_n

    # Flat mean over cells (bound for determinacy; provably immaterial here).
    trajectory = model_error_sum / model_cells if model_cells else float("nan")
    baseline = baseline_error_sum / baseline_cells if baseline_cells else float("nan")

    estimated = np.asarray(point_estimate_g, dtype=np.float64)[is_test]
    truth = np.asarray(
        [float(true_g_by_compound[c]) for c in test_ids], dtype=np.float64
    )
    # Spearman is rank-based, so g against log g is the same statistic.
    spearman = _spearman(estimated, np.log(truth))

    return CaseG1(
        case_id=case_id,
        g_spearman=spearman,
        trajectory_mae=trajectory,
        per_energy_mean_mae=baseline,
        m0_accepted=adequacy_satisfies_g1(a1_status),
        cells=model_cells,
        evaluable_compounds=evaluable,
        contract_failure=profile.contract_failure
        or len(test_ids) != N_TEST_COMPOUNDS_EXPECTED
        or evaluable < MIN_EVALUABLE_COMPOUNDS,
    )


# -----------------------------------------------------------------------
# The endpoint
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class G1Score:
    """G1 over its frozen 164-case denominator."""

    competent: int
    denominator: int
    wilson_lower: float
    gate_passed: bool


def score_g1(outcomes: Sequence[CaseG1]) -> G1Score:
    """Score G1, asserting the sequence length first.

    A3.5 implementation obligation 12: ``analysis.umbrella_decision`` performs
    no length assertion on its outcome sequence, while ``score_g2``/``score_g3``
    both raise on a short one.  The RC5 harness MUST assert the G1 sequence
    length against the 164 denominator before scoring, so a silently short
    sequence cannot inflate the rate.
    """
    if len(outcomes) != G1_DENOMINATOR:
        raise ValueError(
            f"expected {G1_DENOMINATOR} G1 outcomes, got {len(outcomes)}; a "
            f"short sequence would silently change the endpoint's denominator"
        )
    competent = sum(1 for outcome in outcomes if outcome.scalar_competent)
    lower = wilson_lower_95(competent, G1_DENOMINATOR)
    return G1Score(
        competent=competent,
        denominator=G1_DENOMINATOR,
        wilson_lower=lower,
        gate_passed=lower >= G1_WILSON_LOWER_GATE,
    )
