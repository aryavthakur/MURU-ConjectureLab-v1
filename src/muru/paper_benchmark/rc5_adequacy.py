"""Engineering RC5: the M0/M1/M2/M3 adequacy engine.

Implements the frozen Amendment A1 decision contract and execution protocols
across M0, M1, M2, and M3.

All constants, bounds, and rules are imported from
``src/muru/paper_benchmark/adequacy.py``; this module contains the deterministic
fitter and within-compound leave-one-energy-out (LOEO) evaluator.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .adequacy import (
    BOUNDARY_CONTACT_TOL,
    BOUNDARY_OUTWARD_PROBE,
    COARSE_LOG_G_POINTS,
    COARSE_LOG_SHAPE_POINTS,
    DETECTORS,
    E_REF,
    LOG_G_BOUNDS,
    LOG_SHAPE_BOUNDS,
    MIN_OBSERVED_ENERGIES,
    MIN_VERTICAL_AMPLITUDE,
    MU_CEIL,
    MU_FLOOR,
    N_TEST_COMPOUNDS_EXPECTED,
    REFINEMENT_POINTS,
    REFINEMENT_ROUNDS,
    REFINEMENT_SHRINK,
    CaseAdequacyResult,
    CaseAdequacyStatus,
    CompoundContrastRecord,
    decide_case_adequacy,
)
from .rc5_estimate import FrozenPhi

__all__ = [
    "ProfileShape",
    "FitResult",
    "fit_model",
    "predict_model",
    "evaluate_compound_contrast",
    "run_case_adequacy",
]


@dataclass(frozen=True)
class ProfileShape:
    """The normalized shape S and asymptotes derived from a FrozenPhi profile."""

    phi_obj: FrozenPhi

    @classmethod
    def from_phi(cls, phi: FrozenPhi) -> ProfileShape:
        return cls(phi_obj=phi)

    @property
    def a_lo(self) -> float:
        return float(self.phi_obj.values[0])

    @property
    def a_hi(self) -> float:
        return float(self.phi_obj.values[-1])

    @property
    def e_ref(self) -> float:
        return float(self.phi_obj.e_ref)

    @property
    def amplitude(self) -> float:
        return float(self.a_lo - self.a_hi)

    @property
    def usable(self) -> bool:
        if not (math.isfinite(self.a_lo) and math.isfinite(self.a_hi)):
            return False
        if self.amplitude < MIN_VERTICAL_AMPLITUDE:
            return False
        if self.a_lo - MIN_VERTICAL_AMPLITUDE <= MU_FLOOR:
            return False
        if self.a_hi + MIN_VERTICAL_AMPLITUDE >= MU_CEIL:
            return False
        return True

    def phi(self, x: np.ndarray) -> np.ndarray:
        arr = np.asarray(x, dtype=np.float64)
        u = arr / self.e_ref
        return self.phi_obj.evaluate(u)

    def s(self, x: np.ndarray) -> np.ndarray:
        amp = self.amplitude
        if amp <= 0.0:
            return np.zeros_like(np.asarray(x, dtype=np.float64))
        return np.clip((self.phi(x) - self.a_hi) / amp, 0.0, 1.0)


@dataclass(frozen=True)
class FitResult:
    """Outcome of fitting one model to one fold."""

    model: str
    params: dict[str, float] = field(default_factory=dict)
    objective: float = float("nan")
    boundary_contact: bool = False
    unresolved_boundary: bool = False
    state: str = "OK"
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.state == "OK"


def _sse(y: np.ndarray, pred: np.ndarray, axis: int) -> np.ndarray:
    r = y - pred
    return (r * r).sum(axis=axis)


def _grid_objective(
    model: str,
    shape: ProfileShape,
    energies: np.ndarray,
    y: np.ndarray,
    grids: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray | None]:
    """SSE over the parameter product grid."""
    e = energies
    if model == "M1":
        log_g, log_shape = grids
        g = np.exp(log_g)[:, None, None]
        s_exp = np.exp(log_shape)[None, :, None]
        x = shape.e_ref * (e[None, None, :] / (shape.e_ref * g)) ** s_exp
        sv = shape.s(x)
        pred = shape.a_hi + shape.amplitude * sv
        return _sse(y[None, None, :], pred, axis=2), None

    (log_g,) = grids
    x = e[None, :] / np.exp(log_g)[:, None]
    sv = shape.s(x)

    if model == "M0":
        pred = shape.a_hi + shape.amplitude * sv
        return _sse(y[None, :], pred, axis=1), None

    if model == "M2":
        lo, hi = MU_FLOOR, shape.a_lo - MIN_VERTICAL_AMPLITUDE
        basis, offset = 1.0 - sv, shape.a_lo * sv
    elif model == "M3":
        lo, hi = shape.a_hi + MIN_VERTICAL_AMPLITUDE, MU_CEIL
        basis, offset = sv, shape.a_hi * (1.0 - sv)
    else:
        raise ValueError(f"unknown model {model}")

    den = (basis * basis).sum(axis=1)
    num = (basis * (y[None, :] - offset)).sum(axis=1)
    dev = np.where(den > 0.0, num / np.where(den > 0.0, den, 1.0), lo)
    dev = np.clip(dev, lo, hi)
    pred = offset + dev[:, None] * basis
    return _sse(y[None, :], pred, axis=1), dev


def predict_model(
    model: str,
    shape: ProfileShape,
    energies: np.ndarray,
    params: Mapping[str, float],
) -> np.ndarray:
    """Predict response mu under the fitted model and parameters."""
    e = np.asarray(energies, dtype=np.float64)
    log_g = float(params["log_g"])
    g = math.exp(log_g)

    if model == "M0":
        x = e / g
        return shape.a_hi + shape.amplitude * shape.s(x)
    elif model == "M1":
        log_shape = float(params.get("log_shape", 0.0))
        s_exp = math.exp(log_shape)
        x = shape.e_ref * (e / (shape.e_ref * g)) ** s_exp
        return shape.a_hi + shape.amplitude * shape.s(x)
    elif model == "M2":
        x = e / g
        sv = shape.s(x)
        a = float(params.get("high_energy_asymptote", shape.a_hi))
        return shape.a_lo * sv + a * (1.0 - sv)
    elif model == "M3":
        x = e / g
        sv = shape.s(x)
        b = float(params.get("low_energy_plateau", shape.a_lo))
        return shape.a_hi * (1.0 - sv) + b * sv
    else:
        raise ValueError(f"unknown model {model}")


def _objective_at(
    model: str,
    shape: ProfileShape,
    energies: np.ndarray,
    y: np.ndarray,
    params: Mapping[str, float],
) -> float:
    pred = predict_model(model, shape, energies, params)
    r = np.asarray(y, dtype=np.float64) - pred
    return float(np.sum(r * r))


def _boundary_flags(
    model: str,
    shape: ProfileShape,
    energies: np.ndarray,
    y: np.ndarray,
    params: dict[str, float],
    best_obj: float,
) -> tuple[bool, bool]:
    """Check boundary contact and outward unresolved probe."""
    contact = unresolved = False

    param_bounds: list[tuple[str, float, float]] = [
        ("log_g", LOG_G_BOUNDS[0], LOG_G_BOUNDS[1])
    ]
    if model == "M1":
        param_bounds.append(("log_shape", LOG_SHAPE_BOUNDS[0], LOG_SHAPE_BOUNDS[1]))
    elif model == "M2":
        param_bounds.append(
            ("high_energy_asymptote", MU_FLOOR, shape.a_lo - MIN_VERTICAL_AMPLITUDE)
        )
    elif model == "M3":
        param_bounds.append(
            ("low_energy_plateau", shape.a_hi + MIN_VERTICAL_AMPLITUDE, MU_CEIL)
        )

    for name, lower, upper in param_bounds:
        val = params.get(name)
        if val is None or not math.isfinite(val):
            continue
        for bound, outward in ((lower, -1.0), (upper, +1.0)):
            if abs(val - bound) > BOUNDARY_CONTACT_TOL:
                continue
            contact = True
            probed = dict(params)
            probed[name] = bound + outward * BOUNDARY_OUTWARD_PROBE
            try:
                obj = _objective_at(model, shape, energies, y, probed)
            except Exception:
                continue
            if math.isfinite(obj) and obj < best_obj - 1e-12:
                unresolved = True

    return contact, unresolved


def fit_model(
    model: str,
    shape: ProfileShape,
    energies: np.ndarray,
    mu: np.ndarray,
) -> FitResult:
    """Fit one model to one fold under the frozen A1 search protocol."""
    e = np.asarray(energies, dtype=np.float64)
    y = np.asarray(mu, dtype=np.float64)
    if e.shape != y.shape:
        return FitResult(
            model=model,
            state="MODEL_FIT_FAILURE",
            reason="energies and mu have different shapes",
        )
    if e.size == 0 or not np.isfinite(e).all() or not np.isfinite(y).all():
        return FitResult(
            model=model,
            state="NUMERICAL_FAILURE",
            reason="fold contains non-finite energy or response",
        )
    if (e <= 0).any():
        return FitResult(
            model=model,
            state="NUMERICAL_FAILURE",
            reason="fold contains non-positive energy",
        )
    if not shape.usable:
        return FitResult(
            model=model,
            state="MODEL_FIT_FAILURE",
            reason="profile shape is unusable",
        )

    if model == "M1":
        searched_bounds = [LOG_G_BOUNDS, LOG_SHAPE_BOUNDS]
        searched_points = [COARSE_LOG_G_POINTS, COARSE_LOG_SHAPE_POINTS]
        searched_names = ["log_g", "log_shape"]
    else:
        searched_bounds = [LOG_G_BOUNDS]
        searched_points = [COARSE_LOG_G_POINTS]
        searched_names = ["log_g"]

    grids = [
        np.linspace(b[0], b[1], pts)
        for b, pts in zip(searched_bounds, searched_points)
    ]
    steps = [
        (b[1] - b[0]) / (pts - 1)
        for b, pts in zip(searched_bounds, searched_points)
    ]

    best_values: list[float] = []
    best_dev: float | None = None
    best_obj = float("inf")

    for round_index in range(REFINEMENT_ROUNDS + 1):
        try:
            sse, dev = _grid_objective(model, shape, e, y, grids)
        except Exception as exc:
            return FitResult(
                model=model,
                state="NUMERICAL_FAILURE",
                reason=f"objective evaluation failed: {exc!r}",
            )
        finite = np.isfinite(sse)
        if not finite.any():
            return FitResult(
                model=model,
                state="NUMERICAL_FAILURE",
                reason="objective is non-finite everywhere",
            )
        masked = np.where(finite, sse, np.inf)
        flat = int(np.argmin(masked))
        idx = np.unravel_index(flat, masked.shape)
        best_obj = float(masked[idx])
        best_values = [float(grids[d][idx[d]]) for d in range(len(searched_bounds))]
        best_dev = None if dev is None else float(dev[idx[0]])

        if round_index == REFINEMENT_ROUNDS:
            break

        new_grids, new_steps = [], []
        for d in range(len(searched_bounds)):
            half = steps[d]
            span = np.linspace(
                best_values[d] - half,
                best_values[d] + half,
                REFINEMENT_POINTS,
            )
            low, high = searched_bounds[d]
            new_grids.append(np.clip(span, low, high))
            new_steps.append(half / REFINEMENT_SHRINK)
        grids, steps = new_grids, new_steps

    params: dict[str, float] = {
        name: best_values[d] for d, name in enumerate(searched_names)
    }
    if model == "M2":
        params["high_energy_asymptote"] = float(best_dev)
    elif model == "M3":
        params["low_energy_plateau"] = float(best_dev)

    if not math.isfinite(best_obj):
        return FitResult(
            model=model,
            params=params,
            objective=best_obj,
            state="NUMERICAL_FAILURE",
            reason="best objective is non-finite",
        )

    contact, unresolved = _boundary_flags(model, shape, e, y, params, best_obj)
    return FitResult(
        model=model,
        params=params,
        objective=best_obj,
        boundary_contact=contact,
        unresolved_boundary=unresolved,
        state="OK",
    )


def _observed_energies(
    energies: np.ndarray | Sequence[float],
    mu: np.ndarray | Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    """Extract distinct positive finite observations sorted by energy."""
    e = np.asarray(energies, dtype=np.float64)
    y = np.asarray(mu, dtype=np.float64)
    ok = np.isfinite(e) & np.isfinite(y) & (e > 0)
    e, y = e[ok], y[ok]
    order = np.argsort(e, kind="stable")
    e, y = e[order], y[order]
    _, first = np.unique(e, return_index=True)
    return e[np.sort(first)], y[np.sort(first)]


def evaluate_compound_contrast(
    compound_id: str,
    detector: str,
    energies: np.ndarray | Sequence[float],
    mu: np.ndarray | Sequence[float],
    shape: ProfileShape,
) -> CompoundContrastRecord:
    """Evaluate one test compound's leave-one-energy-out contrast against M0."""
    e, y = _observed_energies(energies, mu)
    n = int(e.size)
    if n < MIN_OBSERVED_ENERGIES:
        return CompoundContrastRecord(
            compound_id=compound_id,
            detector=detector,
            observed_energy_count=n,
            mae_m0=None,
            mae_alt=None,
            execution_state="OK",
        )
    if not shape.usable:
        return CompoundContrastRecord(
            compound_id=compound_id,
            detector=detector,
            observed_energy_count=n,
            mae_m0=None,
            mae_alt=None,
            execution_state="MODEL_FIT_FAILURE",
        )

    err0: list[float] = []
    errk: list[float] = []
    contact = unresolved = False
    state = "OK"

    for j in range(n):
        keep = np.ones(n, dtype=bool)
        keep[j] = False
        fold_e, fold_y = e[keep], y[keep]
        held_e, held_y = e[j], y[j]

        fit0 = fit_model("M0", shape, fold_e, fold_y)
        if not fit0.ok:
            return CompoundContrastRecord(
                compound_id=compound_id,
                detector=detector,
                observed_energy_count=n,
                mae_m0=None,
                mae_alt=None,
                execution_state=fit0.state,
                boundary_contact=fit0.boundary_contact,
                unresolved_boundary=fit0.unresolved_boundary,
            )
        contact = contact or fit0.boundary_contact
        unresolved = unresolved or fit0.unresolved_boundary

        fitk = fit_model(detector, shape, fold_e, fold_y)
        if not fitk.ok:
            return CompoundContrastRecord(
                compound_id=compound_id,
                detector=detector,
                observed_energy_count=n,
                mae_m0=None,
                mae_alt=None,
                execution_state=fitk.state,
                boundary_contact=fitk.boundary_contact,
                unresolved_boundary=fitk.unresolved_boundary,
            )
        contact = contact or fitk.boundary_contact
        unresolved = unresolved or fitk.unresolved_boundary

        p0 = float(predict_model("M0", shape, np.array([held_e]), fit0.params)[0])
        pk = float(
            predict_model(detector, shape, np.array([held_e]), fitk.params)[0]
        )
        if not (math.isfinite(p0) and math.isfinite(pk)):
            state = "NUMERICAL_FAILURE"
            break
        err0.append(abs(held_y - p0))
        errk.append(abs(held_y - pk))

    if state != "OK":
        return CompoundContrastRecord(
            compound_id=compound_id,
            detector=detector,
            observed_energy_count=n,
            mae_m0=None,
            mae_alt=None,
            execution_state=state,
            boundary_contact=contact,
            unresolved_boundary=unresolved,
        )

    mae_0 = float(np.mean(err0))
    mae_k = float(np.mean(errk))
    if not (math.isfinite(mae_0) and math.isfinite(mae_k)):
        return CompoundContrastRecord(
            compound_id=compound_id,
            detector=detector,
            observed_energy_count=n,
            mae_m0=None,
            mae_alt=None,
            execution_state="NUMERICAL_FAILURE",
            boundary_contact=contact,
            unresolved_boundary=unresolved,
        )

    return CompoundContrastRecord(
        compound_id=compound_id,
        detector=detector,
        observed_energy_count=n,
        mae_m0=mae_0,
        mae_alt=mae_k,
        execution_state="OK",
        boundary_contact=contact,
        unresolved_boundary=unresolved,
    )


def run_case_adequacy(
    case_id: str,
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
    phi: FrozenPhi,
) -> CaseAdequacyResult:
    """Execute A1 adequacy testing on the 30 test compounds of a case.

    Evaluates M1, M2, and M3 LOEO contrasts against M0 and returns the
    aggregated :class:`CaseAdequacyResult`.
    """
    shape = ProfileShape.from_phi(phi)
    test_compounds = compounds[compounds["split"] == "test"]
    if len(test_compounds) != N_TEST_COMPOUNDS_EXPECTED:
        raise ValueError(
            f"case {case_id} has {len(test_compounds)} test compounds, "
            f"expected {N_TEST_COMPOUNDS_EXPECTED}"
        )

    test_ids = list(test_compounds["compound_id"])
    contrast_records: dict[str, list[CompoundContrastRecord]] = {
        d: [] for d in DETECTORS
    }

    for detector in DETECTORS:
        for cid in test_ids:
            subset = trajectories[trajectories["compound_id"] == cid]
            energies = subset["energy"].to_numpy()
            mu = subset["mu"].to_numpy()
            record = evaluate_compound_contrast(
                compound_id=cid,
                detector=detector,
                energies=energies,
                mu=mu,
                shape=shape,
            )
            contrast_records[detector].append(record)

    return decide_case_adequacy(case_id, contrast_records)
