import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from muru.paper_benchmark.protocol import FrozenScalarObjects, estimate_one, fit_training_scalar


def _rows(compound_id, split, values):
    return pd.DataFrame({"compound_id": compound_id, "split": split, "energy": [15, 30, 45, 60, 75, 90], "mu": values})


def test_test_compound_b_cannot_change_test_compound_a_estimate():
    train = pd.concat([_rows("T1", "train", [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]), _rows("T2", "train", [0.8, 0.7, 0.6, 0.5, 0.4, 0.3])])
    frozen = fit_training_scalar(train)
    a = _rows("A", "test", [0.85, 0.75, 0.65, 0.55, 0.45, 0.35])
    b = _rows("B", "test", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    before = estimate_one(frozen, a)
    b.loc[:, "mu"] = 0.999
    assert estimate_one(frozen, a) == before


def test_fit_refuses_nontraining_rows():
    with pytest.raises(ValueError, match="training rows"):
        fit_training_scalar(_rows("A", "test", [0.8] * 6))


# --- R1: G1 scalar estimator orientation (DEFECT_A) -----------------------------
#
# Hand-built canaries constructed directly from the frozen M0 generator law
# (src/muru/paper_benchmark/generator.py::_response_matrix):
#   u = (E / 45) / g
#   mu = mu_inf + (1 - mu_inf) * exp(-(u ** phi_p))
# reproduced here verbatim with fixed mu_inf, phi_p so the fixture is fully
# deterministic. No case_id, registry, generator.generate_case, or partition
# membership is used anywhere in this module.

_ENERGY_GRID = (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)
_MU_INF = 0.20
_PHI_P = 1.40


def _m0_mu(g, mu_inf=_MU_INF, phi_p=_PHI_P):
    energy = np.asarray(_ENERGY_GRID, dtype=float)
    u = (energy / 45.0) / g
    return mu_inf + (1 - mu_inf) * np.exp(-(u**phi_p))


def _rows_for_g(compound_id, split, g):
    return pd.DataFrame({"compound_id": compound_id, "split": split, "energy": list(_ENERGY_GRID), "mu": _m0_mu(g)})


# Training population's scale is centered near g=1.4 (five compounds spanning
# 0.9-1.9), disjoint from every canary g below.
_TRAINING_GS = (0.9, 1.15, 1.4, 1.65, 1.9)

# Same true-g canaries independently reproduced by the defect adjudication
# (audit/muru_benchmark_core_defect_adjudication.json, DEFECT_A).
_TRUE_G_CANARIES = (0.75, 1.00, 1.30, 1.60, 2.00, 2.50)


def _fit_canary_training():
    train = pd.concat([_rows_for_g(f"TRAIN{i}", "train", g) for i, g in enumerate(_TRAINING_GS)])
    return fit_training_scalar(train)


def _canary_estimates():
    frozen = _fit_canary_training()
    estimates = []
    for g in _TRUE_G_CANARIES:
        held_out = _rows_for_g(f"CANARY_{g}", "test", g)
        estimates.append(estimate_one(frozen, held_out).log_g)
    return estimates


def test_g1_estimate_is_positive_monotonic_in_true_g():
    """Increasing frozen truth g must map to a strictly increasing estimate."""
    estimates = _canary_estimates()
    assert all(b > a for a, b in zip(estimates, estimates[1:])), estimates


def test_g1_estimate_orientation_matches_frozen_generator():
    """Spearman(true log g, estimated log-g) must be strongly positive (G1
    requires >= 0.80 against the true relationship, never its negation)."""
    log_true_g = np.log(_TRUE_G_CANARIES)
    estimates = _canary_estimates()
    rho, _ = spearmanr(log_true_g, estimates)
    assert rho == pytest.approx(1.0)
    assert rho >= 0.80


def test_g1_estimate_sign_is_not_inverted():
    """A held-out compound with g far below the training center must receive a
    negative estimate; one far above must receive a positive estimate. The
    pre-repair defect produced the opposite sign for both."""
    frozen = _fit_canary_training()
    low = estimate_one(frozen, _rows_for_g("LOW", "test", 0.75))
    high = estimate_one(frozen, _rows_for_g("HIGH", "test", 2.50))
    assert low.log_g < 0
    assert high.log_g > 0


def _fit_homogeneous_training(g):
    """A training population with every compound at the same true g, so the
    fold-local baseline equals _m0_mu(g) exactly (no cross-compound averaging
    skew from the law's nonlinearity in g)."""
    train = pd.concat([_rows_for_g(f"HOMO{i}", "train", g) for i in range(3)])
    return fit_training_scalar(train)


def test_g1_degenerate_case_estimate_is_zero():
    """A held-out compound whose trajectory equals the training baseline
    exactly (same true g as every training compound) must estimate
    log_g == 0, independent of the sign convention. Unchanged by the repair."""
    frozen = _fit_homogeneous_training(1.4)
    center = estimate_one(frozen, _rows_for_g("CENTER", "test", 1.4))
    assert center.log_g == pytest.approx(0.0, abs=1e-9)
    assert center.boundary_hit is False


def test_g1_boundary_clip_direction_is_correct():
    """A residual whose magnitude exceeds frozen.support clips to the
    boundary matching its own sign, not the boundary's negation. Support is
    set artificially tight here only to exercise the clip path deterministically;
    fit_training_scalar's real (-2.0, 2.0) support is untouched by this repair."""
    frozen = FrozenScalarObjects(energy=_ENERGY_GRID, training_mean=tuple(_m0_mu(1.4)), support=(-0.05, 0.05))
    high = estimate_one(frozen, _rows_for_g("HIGH", "test", 2.50))
    low = estimate_one(frozen, _rows_for_g("LOW", "test", 0.75))
    assert high.log_g == pytest.approx(0.05)
    assert high.boundary_hit is True
    assert low.log_g == pytest.approx(-0.05)
    assert low.boundary_hit is True


def test_fm06_fold_locality_holds_across_true_g_canaries():
    """FM-06: no held-out compound's estimate may depend on another held-out
    compound's rows, for the full canary sweep (not just the single pair
    already covered above)."""
    frozen = _fit_canary_training()
    baseline = {g: estimate_one(frozen, _rows_for_g(f"C{g}", "test", g)) for g in _TRUE_G_CANARIES}
    # Perturbing one canary's held-out rows must not change any other canary's estimate.
    perturbed_low = _rows_for_g("C0.75", "test", 0.75)
    perturbed_low.loc[:, "mu"] = 0.999
    _ = estimate_one(frozen, perturbed_low)  # exercise the perturbed compound itself
    for g in _TRUE_G_CANARIES:
        if g == 0.75:
            continue
        again = estimate_one(frozen, _rows_for_g(f"C{g}", "test", g))
        assert again == baseline[g]
