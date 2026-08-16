"""Tests for rc5_adequacy: the M0/M1/M2/M3 adequacy fitting and LOEO engine."""

import math
import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark.adequacy import (
    BOUNDARY_CONTACT_TOL,
    COARSE_LOG_G_POINTS,
    COARSE_LOG_SHAPE_POINTS,
    E_REF,
    LOG_G_BOUNDS,
    LOG_SHAPE_BOUNDS,
    MIN_VERTICAL_AMPLITUDE,
    MU_CEIL,
    MU_FLOOR,
    CaseAdequacyStatus,
    CompoundContrastStatus,
    classify_compound_contrast,
)
from muru.paper_benchmark.rc5_adequacy import (
    FitResult,
    ProfileShape,
    evaluate_compound_contrast,
    fit_model,
    predict_model,
    run_case_adequacy,
)
from muru.paper_benchmark.rc5_estimate import FrozenPhi


def _make_mock_phi(
    a_lo: float = 0.95,
    a_hi: float = 0.05,
    e_ref: float = 45.0,
) -> FrozenPhi:
    knots = np.linspace(-3.0, 3.0, 60)
    u = np.exp(knots)
    raw = np.exp(-u**1.2)
    # Scale raw strictly to [0, 1] so endpoints match a_lo and a_hi exactly
    s = (raw - raw[-1]) / (raw[0] - raw[-1])
    vals = a_hi + (a_lo - a_hi) * s
    vals = np.maximum.accumulate(vals[::-1])[::-1]  # monotone decreasing
    return FrozenPhi(
        knots=knots,
        values=vals,
        e_ref=e_ref,
        n_knots=60,
        n_training_compounds=120,
        alternations=3,
    )


def test_profile_shape_properties():
    phi = _make_mock_phi(a_lo=0.95, a_hi=0.05)
    shape = ProfileShape.from_phi(phi)
    assert shape.usable is True
    assert math.isclose(shape.a_lo, 0.95, rel_tol=1e-5)
    assert math.isclose(shape.a_hi, 0.05, rel_tol=1e-5)
    assert math.isclose(shape.amplitude, 0.90, rel_tol=1e-5)

    # Unusable amplitude
    phi_bad = _make_mock_phi(a_lo=0.52, a_hi=0.50)
    shape_bad = ProfileShape.from_phi(phi_bad)
    assert shape_bad.usable is False


def test_m0_fitting_and_recovery():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    true_log_g = 0.35
    true_g = math.exp(true_log_g)

    energies = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 80.0])
    mu = predict_model("M0", shape, energies, {"log_g": true_log_g})

    fit = fit_model("M0", shape, energies, mu)
    assert fit.ok is True
    assert math.isclose(fit.params["log_g"], true_log_g, abs_tol=1e-4)
    assert fit.objective < 1e-8
    assert fit.boundary_contact is False
    assert fit.unresolved_boundary is False


def test_m1_fitting_and_recovery():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    true_log_g = -0.2
    true_log_shape = 0.3  # ln(s)

    energies = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 80.0])
    mu = predict_model(
        "M1",
        shape,
        energies,
        {"log_g": true_log_g, "log_shape": true_log_shape},
    )

    fit = fit_model("M1", shape, energies, mu)
    assert fit.ok is True
    assert math.isclose(fit.params["log_g"], true_log_g, abs_tol=1e-3)
    assert math.isclose(fit.params["log_shape"], true_log_shape, abs_tol=1e-3)
    assert fit.objective < 1e-6


def test_m2_fitting_and_recovery():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    true_log_g = 0.1
    true_a = 0.25  # high-energy floor

    energies = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 80.0])
    mu = predict_model(
        "M2",
        shape,
        energies,
        {"log_g": true_log_g, "high_energy_asymptote": true_a},
    )

    fit = fit_model("M2", shape, energies, mu)
    assert fit.ok is True
    assert math.isclose(fit.params["log_g"], true_log_g, abs_tol=1e-4)
    assert math.isclose(
        fit.params["high_energy_asymptote"], true_a, abs_tol=1e-4
    )
    assert fit.objective < 1e-8


def test_m3_fitting_and_recovery():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    true_log_g = -0.15
    true_b = 0.75  # low-energy ceiling

    energies = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 80.0])
    mu = predict_model(
        "M3",
        shape,
        energies,
        {"log_g": true_log_g, "low_energy_plateau": true_b},
    )

    fit = fit_model("M3", shape, energies, mu)
    assert fit.ok is True
    assert math.isclose(fit.params["log_g"], true_log_g, abs_tol=1e-4)
    assert math.isclose(fit.params["low_energy_plateau"], true_b, abs_tol=1e-4)
    assert fit.objective < 1e-8


def test_unresolved_boundary_detection():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    # Generate data with true log_g far above upper bound (+2.0)
    out_of_bounds_log_g = 3.5
    energies = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 80.0])
    mu = predict_model("M0", shape, energies, {"log_g": out_of_bounds_log_g})

    fit = fit_model("M0", shape, energies, mu)
    assert fit.ok is True
    # Should clamp at upper bound
    assert math.isclose(fit.params["log_g"], LOG_G_BOUNDS[1], abs_tol=1e-5)
    assert fit.boundary_contact is True
    assert fit.unresolved_boundary is True


def test_evaluate_compound_contrast_fewer_than_five_energies():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    energies = np.array([10.0, 20.0, 30.0, 45.0])  # 4 energies < 5
    mu = np.array([0.9, 0.7, 0.5, 0.3])

    record = evaluate_compound_contrast("C01", "M1", energies, mu, shape)
    assert record.observed_energy_count == 4
    assert record.mae_m0 is None
    assert record.mae_alt is None
    assert (
        classify_compound_contrast(record)
        == CompoundContrastStatus.INSUFFICIENT_DATA
    )


def test_evaluate_compound_contrast_m1_practical_win():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    # Strong horizontal shape warp (s = 2.0 -> log_shape = ln 2)
    log_shape = math.log(1.9)
    energies = np.array([10.0, 20.0, 30.0, 45.0, 60.0, 80.0])
    mu = predict_model(
        "M1", shape, energies, {"log_g": 0.0, "log_shape": log_shape}
    )

    record = evaluate_compound_contrast("C01", "M1", energies, mu, shape)
    assert record.observed_energy_count == 6
    assert record.mae_m0 is not None
    assert record.mae_alt is not None
    assert record.mae_alt < record.mae_m0 * 0.90
    assert (
        classify_compound_contrast(record)
        == CompoundContrastStatus.PRACTICAL_WIN
    )


def test_run_case_adequacy_null_m0_not_rejected():
    phi = _make_mock_phi()
    # Build synthetic 30 test compounds generated by M0 with realistic measurement noise
    compounds = pd.DataFrame(
        {
            "compound_id": [f"test_{i:02d}" for i in range(30)],
            "split": ["test"] * 30,
        }
    )
    rows = []
    energies = [10.0, 20.0, 30.0, 45.0, 60.0, 80.0]
    shape = ProfileShape.from_phi(phi)
    rng = np.random.default_rng(42)
    for i in range(30):
        cid = f"test_{i:02d}"
        log_g = -1.0 + 2.0 * (i / 29.0)  # spans [-1.0, 1.0]
        mu = predict_model("M0", shape, np.array(energies), {"log_g": log_g})
        mu = np.clip(mu + rng.normal(0, 0.01, size=len(energies)), 1e-3, 1.0 - 1e-3)
        for e, m in zip(energies, mu):
            rows.append({"compound_id": cid, "energy": e, "mu": m})
    trajectories = pd.DataFrame(rows)

    result = run_case_adequacy(
        "PB|development|F01|r000", compounds, trajectories, phi
    )
    assert result.status == CaseAdequacyStatus.M0_NOT_REJECTED


def test_run_case_adequacy_m1_rejection():
    phi = _make_mock_phi()
    shape = ProfileShape.from_phi(phi)
    compounds = pd.DataFrame(
        {
            "compound_id": [f"test_{i:02d}" for i in range(30)],
            "split": ["test"] * 30,
        }
    )
    rows = []
    energies = [10.0, 20.0, 30.0, 45.0, 60.0, 80.0]
    # Strong M1 shape deviation for all 30 compounds
    log_shape = math.log(1.8)
    for i in range(30):
        cid = f"test_{i:02d}"
        log_g = -0.5 + 1.0 * (i / 29.0)
        mu = predict_model(
            "M1",
            shape,
            np.array(energies),
            {"log_g": log_g, "log_shape": log_shape},
        )
        for e, m in zip(energies, mu):
            rows.append({"compound_id": cid, "energy": e, "mu": m})
    trajectories = pd.DataFrame(rows)

    result = run_case_adequacy(
        "PB|development|F06|r000", compounds, trajectories, phi
    )
    assert result.status == CaseAdequacyStatus.M0_REJECTED_M1
