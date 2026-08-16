"""E1: the instrumented fitter and fit-record instrument.

New code, written for this experiment only. Calls the frozen production
functions ``rc5_adequacy.fit_model`` / ``predict_model`` / ``_objective_at``
unmodified; the only runtime manipulation is temporary global reassignment
of ``rc5_adequacy``'s bound constants (``MU_CEIL`` for the E1 factor itself,
and, only inside the C4 relaxed-refit context, whichever bound a fold
touched) -- always restored in a ``finally`` block, exactly the pattern
``scripts/e0_common.py`` established for ``MU_CEIL``.

See ``MURU_V2_E1_PROTOCOL.md`` Sec 5 and 7.1 for the exact field list and the
declared C2/C3/C4 constructions implemented here.
"""
from __future__ import annotations

import math
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(os.path.dirname(_THIS_DIR), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from muru.paper_benchmark import adequacy  # noqa: E402
from muru.paper_benchmark import rc5_adequacy  # noqa: E402
from muru.paper_benchmark import rc5_estimate  # noqa: E402

assert "pysr" not in sys.modules, "E1 must never import PySR"

C4_RELAXATION_FRACTION = 0.10  # MURU_V2_E1_PROTOCOL.md Sec 7.1, declared, not swept
PROFILE_GRID_POINTS = 41  # M1 nested-grid profile approximation, disclosed Sec 7.1


# --------------------------------------------------------------------------
# Bound geometry: which global(s) a touched (model, param, side) maps to.
# --------------------------------------------------------------------------


def _dev_basis_offset(model: str, shape, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sv = shape.s(x)
    if model == "M2":
        return 1.0 - sv, shape.a_lo * sv
    if model == "M3":
        return sv, shape.a_hi * (1.0 - sv)
    raise ValueError(model)


def _dev_bound_range(model: str, shape) -> tuple[float, float]:
    if model == "M2":
        return rc5_adequacy.MU_FLOOR, shape.a_lo - rc5_adequacy.MIN_VERTICAL_AMPLITUDE
    if model == "M3":
        return shape.a_hi + rc5_adequacy.MIN_VERTICAL_AMPLITUDE, rc5_adequacy.MU_CEIL
    raise ValueError(model)


def _touched_params(model: str) -> list[str]:
    if model == "M1":
        return ["log_g", "log_shape"]
    if model in ("M2", "M3"):
        return ["log_g", {"M2": "high_energy_asymptote", "M3": "low_energy_plateau"}[model]]
    return ["log_g"]


def admissible_range(model: str, param: str, shape) -> float:
    if param == "log_g":
        lo, hi = rc5_adequacy.LOG_G_BOUNDS
    elif param == "log_shape":
        lo, hi = rc5_adequacy.LOG_SHAPE_BOUNDS
    else:
        lo, hi = _dev_bound_range(model, shape)
    return float(hi - lo)


def _touched_bounds(model: str, shape, params: dict) -> list[tuple[str, str, float]]:
    """[(param, side, bound_value), ...] for every bound this fit's params touch."""
    out = []
    for param in _touched_params(model):
        val = params.get(param)
        if val is None or not math.isfinite(val):
            continue
        if param == "log_g":
            lo, hi = rc5_adequacy.LOG_G_BOUNDS
        elif param == "log_shape":
            lo, hi = rc5_adequacy.LOG_SHAPE_BOUNDS
        else:
            lo, hi = _dev_bound_range(model, shape)
        for bound, side in ((lo, "lower"), (hi, "upper")):
            if abs(val - bound) <= rc5_adequacy.BOUNDARY_CONTACT_TOL:
                out.append((param, side, bound))
    return out


@contextmanager
def _relaxed_globals(touches: list[tuple[str, str, float]], model: str, shape):
    """Patch rc5_adequacy globals to relax every touched bound outward by
    C4_RELAXATION_FRACTION * admissible_range, restoring on exit."""
    saved = {}
    try:
        for param, side, _bound in touches:
            margin = C4_RELAXATION_FRACTION * admissible_range(model, param, shape)
            if param == "log_g":
                if "LOG_G_BOUNDS" not in saved:
                    saved["LOG_G_BOUNDS"] = rc5_adequacy.LOG_G_BOUNDS
                lo, hi = rc5_adequacy.LOG_G_BOUNDS
                rc5_adequacy.LOG_G_BOUNDS = (lo - margin, hi) if side == "lower" else (lo, hi + margin)
            elif param == "log_shape":
                if "LOG_SHAPE_BOUNDS" not in saved:
                    saved["LOG_SHAPE_BOUNDS"] = rc5_adequacy.LOG_SHAPE_BOUNDS
                lo, hi = rc5_adequacy.LOG_SHAPE_BOUNDS
                rc5_adequacy.LOG_SHAPE_BOUNDS = (lo - margin, hi) if side == "lower" else (lo, hi + margin)
            elif param == "high_energy_asymptote":
                if side == "lower":
                    saved.setdefault("MU_FLOOR", rc5_adequacy.MU_FLOOR)
                    rc5_adequacy.MU_FLOOR = max(rc5_adequacy.MU_FLOOR - margin, 1e-9)
                else:
                    saved.setdefault("MIN_VERTICAL_AMPLITUDE", rc5_adequacy.MIN_VERTICAL_AMPLITUDE)
                    rc5_adequacy.MIN_VERTICAL_AMPLITUDE = max(rc5_adequacy.MIN_VERTICAL_AMPLITUDE - margin, 1e-9)
            elif param == "low_energy_plateau":
                if side == "lower":
                    saved.setdefault("MIN_VERTICAL_AMPLITUDE", rc5_adequacy.MIN_VERTICAL_AMPLITUDE)
                    rc5_adequacy.MIN_VERTICAL_AMPLITUDE = max(rc5_adequacy.MIN_VERTICAL_AMPLITUDE - margin, 1e-9)
                else:
                    saved.setdefault("MU_CEIL", rc5_adequacy.MU_CEIL)
                    rc5_adequacy.MU_CEIL = rc5_adequacy.MU_CEIL + margin
        yield
    finally:
        for name, value in saved.items():
            setattr(rc5_adequacy, name, value)


# --------------------------------------------------------------------------
# Probe detail (C0/C1/C2), sigma_hat (C2), profile width (C3): all computed
# per touched bound, per fold.
# --------------------------------------------------------------------------


@dataclass
class ProbeSummary:
    """Sufficient statistics over every touched-bound probe in one fold/model.

    Each criterion's "unresolved iff ANY touched probe satisfies X" test is
    monotone in a single per-probe scalar, so the max of that scalar over
    touched probes is exactly equivalent to the "any" test -- this is what
    lets the fit record stay flat (no nested per-probe list) without losing
    any criterion's information. See MURU_V2_E1_PROTOCOL.md Sec 5, 7.1.
    """

    n_touched: int = 0
    max_probe_gain_rel: float | None = None  # C1
    max_probe_gain_abs: float | None = None  # C2
    max_profile_ratio: float | None = None  # C3 (extent / admissible_range, max over probes)


def _probe_and_profile(model: str, shape, e: np.ndarray, y: np.ndarray, fit, sigma_hat_sq: float) -> ProbeSummary:
    touches = _touched_bounds(model, shape, fit.params)
    summary = ProbeSummary(n_touched=len(touches))
    if not touches:
        return summary
    g = math.exp(float(fit.params["log_g"]))
    gain_rels, gain_abs, profile_ratios = [], [], []
    for param, side, bound in touches:
        outward = 1.0 if side == "upper" else -1.0
        probed = dict(fit.params)
        probed[param] = bound + outward * rc5_adequacy.BOUNDARY_OUTWARD_PROBE
        try:
            probe_obj = rc5_adequacy._objective_at(model, shape, e, y, probed)
        except Exception:
            probe_obj = None
        gain_rel = gain_abs_val = None
        if probe_obj is not None and math.isfinite(probe_obj) and math.isfinite(fit.objective):
            gain_abs_val = fit.objective - probe_obj
            if fit.objective != 0:
                gain_rel = gain_abs_val / fit.objective

        rng = admissible_range(model, param, shape)
        if param in ("high_energy_asymptote", "low_energy_plateau"):
            x = e / g
            basis, offset = _dev_basis_offset(model, shape, x)
            den = float(np.sum(basis * basis))
            if den > 1e-15:
                num = float(np.sum(basis * (y - offset)))
                dev_hat_raw = num / den
                half_width = math.sqrt(sigma_hat_sq / den) if sigma_hat_sq > 0 else 0.0
                extent = abs(dev_hat_raw - bound) + half_width
            else:
                extent = rng  # unidentified: treat as saturating the full range
        else:
            extent = _grid_profile_outward_extent(model, shape, e, y, param, bound, outward, fit.params, sigma_hat_sq, rng)

        if gain_rel is not None:
            gain_rels.append(gain_rel)
        if gain_abs_val is not None:
            gain_abs.append(gain_abs_val)
        if extent is not None and math.isfinite(extent) and rng > 0:
            profile_ratios.append(min(extent, 3 * rng) / rng)

    summary.max_probe_gain_rel = max(gain_rels) if gain_rels else None
    summary.max_probe_gain_abs = max(gain_abs) if gain_abs else None
    summary.max_profile_ratio = max(profile_ratios) if profile_ratios else None
    return summary


def _grid_profile_outward_extent(model, shape, e, y, param, bound, outward, fitted_params, sigma_hat_sq, rng) -> float:
    """log_g / log_shape profile via nested grid (disclosed approximation, E1_PROTOCOL.md Sec 7.1)."""
    span = rng
    # Sweep runs from just inside the bound to 1.5x the admissible range beyond it.
    sweep = np.linspace(bound - outward * 0.05 * span, bound + outward * 1.5 * span, PROFILE_GRID_POINTS)
    if param == "log_g":
        if model == "M1":
            fixed_shape = np.array([float(fitted_params.get("log_shape", 0.0))])
            sse, _ = rc5_adequacy._grid_objective(model, shape, e, y, [sweep, fixed_shape])
            profile = sse[:, 0]
        else:
            sse, _ = rc5_adequacy._grid_objective(model, shape, e, y, [sweep])
            profile = sse if sse.ndim == 1 else sse[:, 0]
    elif param == "log_shape":
        log_g_grid = np.linspace(*rc5_adequacy.LOG_G_BOUNDS, rc5_adequacy.COARSE_LOG_G_POINTS)
        sse, _ = rc5_adequacy._grid_objective(model, shape, e, y, [log_g_grid, sweep])
        profile = sse.min(axis=0)
    else:
        raise ValueError(param)

    finite = np.isfinite(profile)
    if not finite.any():
        return rng
    prof_min = float(np.min(profile[finite]))
    argmin = int(np.argmin(np.where(finite, profile, np.inf)))
    theta_hat = float(sweep[argmin])
    threshold = prof_min + (sigma_hat_sq if sigma_hat_sq > 0 else 0.0)
    # Walk outward from theta_hat along `outward` direction until profile exceeds threshold.
    order = np.argsort(sweep) if outward > 0 else np.argsort(-sweep)
    idx_sorted = order[sweep[order] * outward >= theta_hat * outward]
    crossing = None
    prev_t, prev_v = theta_hat, prof_min
    for idx in idx_sorted:
        t, v = float(sweep[idx]), float(profile[idx]) if finite[idx] else np.inf
        if v > threshold:
            if v == np.inf or prev_v == np.inf:
                crossing = t
            else:
                frac = (threshold - prev_v) / (v - prev_v) if v != prev_v else 0.0
                crossing = prev_t + frac * (t - prev_t)
            break
        prev_t, prev_v = t, v
    if crossing is None:
        crossing = float(sweep[idx_sorted[-1]]) if len(idx_sorted) else theta_hat + outward * span
    extent = abs(theta_hat - bound) + max(0.0, abs(crossing - theta_hat))
    return min(extent, 3 * rng)


# --------------------------------------------------------------------------
# Per-compound instrumented contrast: fit, probe/profile, C4 relaxed refit,
# all persisted per fold.
# --------------------------------------------------------------------------


@dataclass
class FoldRecord:
    fold_index: int
    n_fold: int
    held_energy: float
    held_response: float
    m0_objective: float | None
    m0_abs_error: float | None
    mk_objective: float | None
    mk_abs_error: float | None
    m0_boundary_contact: bool
    mk_boundary_contact: bool
    m0_unresolved_c0: bool
    mk_unresolved_c0: bool
    sigma_hat_sq: float | None
    m0_probe_summary: ProbeSummary = field(default_factory=ProbeSummary)
    mk_probe_summary: ProbeSummary = field(default_factory=ProbeSummary)
    mk_relaxed_abs_error: float | None = None
    m0_relaxed_abs_error: float | None = None
    state: str = "OK"


def instrumented_compound_contrast(
    compound_id: str, detector: str, energies: np.ndarray, mu: np.ndarray, shape,
) -> tuple["rc5_adequacy.CompoundContrastRecord", list[FoldRecord]]:
    e, y = rc5_adequacy._observed_energies(energies, mu)
    n = int(e.size)
    folds: list[FoldRecord] = []

    if n < adequacy.MIN_OBSERVED_ENERGIES:
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n,
            mae_m0=None, mae_alt=None, execution_state="OK",
        )
        return rec, folds
    if not shape.usable:
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n,
            mae_m0=None, mae_alt=None, execution_state="MODEL_FIT_FAILURE",
        )
        return rec, folds

    err0, errk = [], []
    contact = unresolved = False
    state = "OK"

    for j in range(n):
        keep = np.ones(n, dtype=bool)
        keep[j] = False
        fold_e, fold_y = e[keep], y[keep]
        held_e, held_y = float(e[j]), float(y[j])
        n_fold = n - 1

        fit0 = rc5_adequacy.fit_model("M0", shape, fold_e, fold_y)
        if not fit0.ok:
            rec = rc5_adequacy.CompoundContrastRecord(
                compound_id=compound_id, detector=detector, observed_energy_count=n,
                mae_m0=None, mae_alt=None, execution_state=fit0.state,
                boundary_contact=fit0.boundary_contact, unresolved_boundary=fit0.unresolved_boundary,
            )
            return rec, folds
        contact = contact or fit0.boundary_contact
        unresolved = unresolved or fit0.unresolved_boundary

        fitk = rc5_adequacy.fit_model(detector, shape, fold_e, fold_y)
        if not fitk.ok:
            rec = rc5_adequacy.CompoundContrastRecord(
                compound_id=compound_id, detector=detector, observed_energy_count=n,
                mae_m0=None, mae_alt=None, execution_state=fitk.state,
                boundary_contact=fitk.boundary_contact, unresolved_boundary=fitk.unresolved_boundary,
            )
            return rec, folds
        contact = contact or fitk.boundary_contact
        unresolved = unresolved or fitk.unresolved_boundary

        p0 = float(rc5_adequacy.predict_model("M0", shape, np.array([held_e]), fit0.params)[0])
        pk = float(rc5_adequacy.predict_model(detector, shape, np.array([held_e]), fitk.params)[0])
        if not (math.isfinite(p0) and math.isfinite(pk)):
            state = "NUMERICAL_FAILURE"
            break
        e0, ek = abs(held_y - p0), abs(held_y - pk)
        err0.append(e0)
        errk.append(ek)

        sigma_hat_sq = fit0.objective / max(n_fold - 1, 1) if math.isfinite(fit0.objective) else None

        m0_probes = _probe_and_profile("M0", shape, fold_e, fold_y, fit0, sigma_hat_sq or 0.0) if fit0.boundary_contact else ProbeSummary()
        mk_probes = _probe_and_profile(detector, shape, fold_e, fold_y, fitk, sigma_hat_sq or 0.0) if fitk.boundary_contact else ProbeSummary()

        relaxed_e0, relaxed_ek = None, None
        touches0 = _touched_bounds("M0", shape, fit0.params) if fit0.boundary_contact else []
        touchesk = _touched_bounds(detector, shape, fitk.params) if fitk.boundary_contact else []
        if touches0:
            with _relaxed_globals(touches0, "M0", shape):
                fit0r = rc5_adequacy.fit_model("M0", shape, fold_e, fold_y)
            if fit0r.ok:
                p0r = float(rc5_adequacy.predict_model("M0", shape, np.array([held_e]), fit0r.params)[0])
                if math.isfinite(p0r):
                    relaxed_e0 = abs(held_y - p0r)
        if touchesk:
            with _relaxed_globals(touchesk, detector, shape):
                fitkr = rc5_adequacy.fit_model(detector, shape, fold_e, fold_y)
            if fitkr.ok:
                pkr = float(rc5_adequacy.predict_model(detector, shape, np.array([held_e]), fitkr.params)[0])
                if math.isfinite(pkr):
                    relaxed_ek = abs(held_y - pkr)

        folds.append(
            FoldRecord(
                fold_index=j, n_fold=n_fold, held_energy=held_e, held_response=held_y,
                m0_objective=fit0.objective, m0_abs_error=e0,
                mk_objective=fitk.objective, mk_abs_error=ek,
                m0_boundary_contact=fit0.boundary_contact, mk_boundary_contact=fitk.boundary_contact,
                m0_unresolved_c0=fit0.unresolved_boundary, mk_unresolved_c0=fitk.unresolved_boundary,
                sigma_hat_sq=sigma_hat_sq, m0_probe_summary=m0_probes, mk_probe_summary=mk_probes,
                mk_relaxed_abs_error=relaxed_ek, m0_relaxed_abs_error=relaxed_e0,
            )
        )

    if state != "OK":
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n,
            mae_m0=None, mae_alt=None, execution_state=state,
            boundary_contact=contact, unresolved_boundary=unresolved,
        )
        return rec, folds

    mae_0, mae_k = float(np.mean(err0)), float(np.mean(errk))
    if not (math.isfinite(mae_0) and math.isfinite(mae_k)):
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n,
            mae_m0=None, mae_alt=None, execution_state="NUMERICAL_FAILURE",
            boundary_contact=contact, unresolved_boundary=unresolved,
        )
        return rec, folds

    rec = rc5_adequacy.CompoundContrastRecord(
        compound_id=compound_id, detector=detector, observed_energy_count=n,
        mae_m0=mae_0, mae_alt=mae_k, execution_state="OK",
        boundary_contact=contact, unresolved_boundary=unresolved,
    )
    return rec, folds


# --------------------------------------------------------------------------
# Compound-level aggregation: reduces the (up to 6) fold records to exactly
# the sufficient statistics e1_rules.py's criteria/rules need.
#
# Equivalence: every criterion's "unresolved iff ANY touched probe (across
# both the M0 and Mk fold fits, across every fold) satisfies X" test is
# monotone in a single per-probe scalar (probe_gain_rel for C1, the
# gain_abs/(sigma_hat_sq * n_fold) ratio for C2, profile_ratio for C3), so
# the max of that scalar over every probe in every fold is exactly
# equivalent to the "any" test -- no fold-level detail is lost for any
# criterion in the C0-C4 grid. Proven by scripts/test_e1_aggregation.py.
# --------------------------------------------------------------------------


def aggregate_compound(record: "rc5_adequacy.CompoundContrastRecord", folds: list[FoldRecord]) -> dict:
    out = {
        "compound_id": record.compound_id,
        "detector": record.detector,
        "observed_energy_count": record.observed_energy_count,
        "execution_state": record.execution_state,
        "mae_m0": record.mae_m0,
        "mae_alt": record.mae_alt,
        "boundary_contact": record.boundary_contact,
        "n_fold": folds[0].n_fold if folds else None,
    }

    def _max_none(values):
        vals = [v for v in values if v is not None and math.isfinite(v)]
        return max(vals) if vals else None

    out["m0_unresolved_c0_any"] = any(f.m0_unresolved_c0 for f in folds)
    out["mk_unresolved_c0_any"] = any(f.mk_unresolved_c0 for f in folds)
    out["m0_max_probe_gain_rel"] = _max_none(f.m0_probe_summary.max_probe_gain_rel for f in folds)
    out["mk_max_probe_gain_rel"] = _max_none(f.mk_probe_summary.max_probe_gain_rel for f in folds)
    out["m0_max_profile_ratio"] = _max_none(f.m0_probe_summary.max_profile_ratio for f in folds)
    out["mk_max_profile_ratio"] = _max_none(f.mk_probe_summary.max_profile_ratio for f in folds)

    def _c2_ratio(f: FoldRecord, summary: ProbeSummary) -> float | None:
        if summary.max_probe_gain_abs is None or f.sigma_hat_sq is None or f.sigma_hat_sq <= 0 or not f.n_fold:
            return None
        return summary.max_probe_gain_abs / (f.sigma_hat_sq * f.n_fold)

    # C2's threshold is `gain_abs > delta * sigma_hat_sq * n_fold`, i.e.
    # `gain_abs / (sigma_hat_sq * n_fold) > delta`: this ratio, not the raw
    # gain, is the sufficient statistic e1_rules.c2_unresolved compares
    # directly against delta.
    out["m0_max_c2_ratio"] = _max_none(_c2_ratio(f, f.m0_probe_summary) for f in folds)
    out["mk_max_c2_ratio"] = _max_none(_c2_ratio(f, f.mk_probe_summary) for f in folds)

    # C4: verdict invariance. Fall back to the primal error when a fold's
    # model didn't touch a bound (nothing to relax there).
    if record.mae_m0 is not None and record.mae_alt is not None and folds:
        relaxed_e0 = [f.m0_relaxed_abs_error if f.m0_relaxed_abs_error is not None else f.m0_abs_error for f in folds]
        relaxed_ek = [f.mk_relaxed_abs_error if f.mk_relaxed_abs_error is not None else f.mk_abs_error for f in folds]
        if all(v is not None for v in relaxed_e0) and all(v is not None for v in relaxed_ek):
            relaxed_mae_m0 = float(np.mean(relaxed_e0))
            relaxed_mae_alt = float(np.mean(relaxed_ek))
            any_relaxed = any(f.m0_relaxed_abs_error is not None or f.mk_relaxed_abs_error is not None for f in folds)
            original_win = record.mae_m0 > 0 and record.mae_alt <= 0.90 * record.mae_m0
            relaxed_win = relaxed_mae_m0 > 0 and relaxed_mae_alt <= 0.90 * relaxed_mae_m0
            out["c4_verdict_flip"] = bool(any_relaxed and (original_win != relaxed_win))
        else:
            out["c4_verdict_flip"] = False
    else:
        out["c4_verdict_flip"] = False

    return out
