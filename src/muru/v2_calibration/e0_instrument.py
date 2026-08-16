"""E0 instrumentation: fit-level records from the frozen A1 fitter, unchanged.

Two properties this module exists to guarantee, both of them hostile-review
targets in the committed plan (Lens 6, "instrumentation that changes what it
measures"):

**The fitter is not reimplemented.**  `rc5_adequacy.fit_model`,
`rc5_adequacy.predict_model` and `rc5_adequacy._objective_at` are called
verbatim.  Factor 2 of the design -- the fitter admissible ceiling -- is applied
by rebinding the single module global `rc5_adequacy.MU_CEIL` inside an audited
context manager, so the arithmetic that runs under every cell is the frozen
arithmetic and the only difference between cells is the constant the design says
should differ.

**The observer is checked against the thing it observes.**  `probe_gain_rel`
needs the probe objectives, which the frozen `_boundary_flags` computes and
discards.  :func:`observe_boundary` recomputes them along the frozen function's
own bound list and, on **every fit**, asserts that the `(boundary_contact,
unresolved_boundary)` pair it derives equals the pair the frozen function
returned.  A disagreement raises :class:`InstrumentationDrift` and aborts the
run rather than being recorded.
"""
from __future__ import annotations

import contextlib
import math
import sys
from dataclasses import dataclass
from typing import Iterator, Sequence

import numpy as np
import pandas as pd

from muru.paper_benchmark import rc5_adequacy as _rc5
from muru.paper_benchmark.adequacy import (
    BOUNDARY_CONTACT_TOL,
    BOUNDARY_OUTWARD_PROBE,
    DETECTORS,
    MIN_OBSERVED_ENERGIES,
    MU_CEIL as V1_MU_CEIL,
    CaseAdequacyResult,
    CompoundContrastRecord,
    decide_case_adequacy,
)
from muru.paper_benchmark.rc5_estimate import FrozenPhi

__all__ = [
    "InstrumentationDrift",
    "PySRImportBlocked",
    "block_pysr_imports",
    "assert_pysr_absent",
    "mu_ceil_injected",
    "observe_boundary",
    "run_case_adequacy_instrumented",
]


class InstrumentationDrift(RuntimeError):
    """The observer disagreed with the frozen fitter.  E0 fails closed."""


class PySRImportBlocked(ImportError):
    """Something attempted to import a symbolic search engine during E0."""


# ---------------------------------------------------------------------------
# No symbolic search
# ---------------------------------------------------------------------------

class _PySRBlocker:
    """A `sys.meta_path` finder that refuses `pysr` and its submodules."""

    BLOCKED = ("pysr", "sympy_pysr", "julia", "juliacall")

    def find_module(self, fullname, path=None):  # pragma: no cover - legacy API
        self.find_spec(fullname, path)
        return None

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root in self.BLOCKED:
            raise PySRImportBlocked(
                f"E0 runs no symbolic search; import of {fullname!r} is blocked"
            )
        return None


@contextlib.contextmanager
def block_pysr_imports() -> Iterator[None]:
    """Make any symbolic-search import an error for the duration of the run."""
    blocker = _PySRBlocker()
    sys.meta_path.insert(0, blocker)
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.meta_path.remove(blocker)


def assert_pysr_absent() -> None:
    """Fail closed if a symbolic search engine was imported at any point."""
    offenders = sorted(
        name for name in sys.modules
        if name.split(".")[0] in _PySRBlocker.BLOCKED
    )
    if offenders:
        raise PySRImportBlocked(f"symbolic search modules present: {offenders}")


# ---------------------------------------------------------------------------
# Factor 2: the fitter admissible ceiling
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def mu_ceil_injected(value: float) -> Iterator[float]:
    """Rebind the frozen fitter's `MU_CEIL` for the duration of a cell.

    Asserts the v1 value is in place on entry, so a leaked injection from an
    earlier cell is an error rather than a silent contamination, and restores it
    on exit even if the body raises.

    `rc5_adequacy` reads `MU_CEIL` as a module global in exactly three places --
    `ProfileShape.usable`, `_grid_objective`'s M3 branch, and `_boundary_flags`'
    M3 bound -- all of which resolve at call time, so this rebinding reaches
    every consumer in the A1 path and no consumer outside it.
    """
    if _rc5.MU_CEIL != V1_MU_CEIL:
        raise InstrumentationDrift(
            f"MU_CEIL was {_rc5.MU_CEIL!r} on entry, expected the v1 value {V1_MU_CEIL!r}"
        )
    _rc5.MU_CEIL = float(value)
    try:
        yield float(value)
    finally:
        _rc5.MU_CEIL = V1_MU_CEIL


# ---------------------------------------------------------------------------
# The observer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProbeRecord:
    parameter: str
    side: str
    bound: float
    best_objective: float
    probe_objective: float
    probe_gain_rel: float
    triggered: bool


def _frozen_param_bounds(model: str, shape: _rc5.ProfileShape) -> list[tuple[str, float, float]]:
    """`_boundary_flags`' own bound list, read through the injected globals."""
    bounds: list[tuple[str, float, float]] = [
        ("log_g", _rc5.LOG_G_BOUNDS[0], _rc5.LOG_G_BOUNDS[1])
    ]
    if model == "M1":
        bounds.append(("log_shape", _rc5.LOG_SHAPE_BOUNDS[0], _rc5.LOG_SHAPE_BOUNDS[1]))
    elif model == "M2":
        bounds.append(("high_energy_asymptote", _rc5.MU_FLOOR, shape.a_lo - _rc5.MIN_VERTICAL_AMPLITUDE))
    elif model == "M3":
        bounds.append(("low_energy_plateau", shape.a_hi + _rc5.MIN_VERTICAL_AMPLITUDE, _rc5.MU_CEIL))
    return bounds


def observe_boundary(
    model: str,
    shape: _rc5.ProfileShape,
    energies: np.ndarray,
    y: np.ndarray,
    params: dict[str, float],
    best_obj: float,
    fit: _rc5.FitResult,
) -> tuple[list[ProbeRecord], str | None]:
    """Recompute the probes the frozen flags discarded, then check agreement.

    Returns the probe records and the dominant bound hit, or raises
    :class:`InstrumentationDrift` if the derived flags disagree with the frozen
    fitter's own.
    """
    contact = unresolved = False
    probes: list[ProbeRecord] = []
    dominant: str | None = None

    for name, lower, upper in _frozen_param_bounds(model, shape):
        val = params.get(name)
        if val is None or not math.isfinite(val):
            continue
        for bound, outward in ((lower, -1.0), (upper, +1.0)):
            if abs(val - bound) > BOUNDARY_CONTACT_TOL:
                continue
            contact = True
            side = "lower" if outward < 0 else "upper"
            if dominant is None:
                dominant = f"{model}:{name}@{side}"
            probed = dict(params)
            probed[name] = bound + outward * BOUNDARY_OUTWARD_PROBE
            try:
                obj = _rc5._objective_at(model, shape, energies, y, probed)
            except Exception:
                continue
            triggered = math.isfinite(obj) and obj < best_obj - 1e-12
            if triggered:
                unresolved = True
            gain = (best_obj - obj) / best_obj if best_obj > 0 and math.isfinite(obj) else float("nan")
            probes.append(ProbeRecord(name, side, float(bound), float(best_obj), float(obj), float(gain), triggered))

    if (contact, unresolved) != (fit.boundary_contact, fit.unresolved_boundary):
        raise InstrumentationDrift(
            f"observer derived (contact={contact}, unresolved={unresolved}) but the frozen "
            f"fitter reported (contact={fit.boundary_contact}, unresolved={fit.unresolved_boundary}) "
            f"for model {model}"
        )
    return probes, dominant


# ---------------------------------------------------------------------------
# The instrumented contrast, byte-compatible with the frozen one
# ---------------------------------------------------------------------------

def _evaluate_compound_contrast_instrumented(
    compound_id: str,
    detector: str,
    energies: np.ndarray | Sequence[float],
    mu: np.ndarray | Sequence[float],
    shape: _rc5.ProfileShape,
    sink: list[dict[str, object]],
    context: dict[str, object],
) -> CompoundContrastRecord:
    """`rc5_adequacy.evaluate_compound_contrast`, transcribed, with recording.

    The control flow, the early returns, the `or`-accumulation of the boundary
    flags and the returned record are the frozen function's.  The only additions
    are `sink.append(...)` calls, which read state and write nothing back.
    """
    e, y = _rc5._observed_energies(energies, mu)
    n = int(e.size)
    if n < MIN_OBSERVED_ENERGIES:
        return CompoundContrastRecord(compound_id, detector, n, None, None, "OK")
    if not shape.usable:
        return CompoundContrastRecord(compound_id, detector, n, None, None, "MODEL_FIT_FAILURE")

    err0: list[float] = []
    errk: list[float] = []
    contact = unresolved = False
    state = "OK"

    def record(fold: int, model: str, fit: _rc5.FitResult, fold_e: np.ndarray, fold_y: np.ndarray) -> None:
        probes, dominant = observe_boundary(model, shape, fold_e, fold_y, fit.params, fit.objective, fit)
        triggering = [p for p in probes if p.triggered]
        sink.append({
            **context,
            "compound_id": compound_id,
            "detector": detector,
            "fold_index": fold,
            "model": model,
            "n_fold_energies": int(fold_e.size),
            "objective": float(fit.objective),
            "state": fit.state,
            "boundary_contact": bool(fit.boundary_contact),
            "unresolved_boundary": bool(fit.unresolved_boundary),
            "dominant_bound_hit": dominant,
            "log_g": float(fit.params.get("log_g", float("nan"))),
            "log_shape": float(fit.params.get("log_shape", float("nan"))),
            "high_energy_asymptote": float(fit.params.get("high_energy_asymptote", float("nan"))),
            "low_energy_plateau": float(fit.params.get("low_energy_plateau", float("nan"))),
            "n_probes": len(probes),
            "n_probes_triggering": len(triggering),
            "probe_gain_rel_max": max((p.probe_gain_rel for p in triggering), default=float("nan")),
            "probe_objective_min": min((p.probe_objective for p in triggering), default=float("nan")),
        })

    for j in range(n):
        keep = np.ones(n, dtype=bool)
        keep[j] = False
        fold_e, fold_y = e[keep], y[keep]
        held_e, held_y = e[j], y[j]

        fit0 = _rc5.fit_model("M0", shape, fold_e, fold_y)
        record(j, "M0", fit0, fold_e, fold_y)
        if not fit0.ok:
            return CompoundContrastRecord(
                compound_id, detector, n, None, None, fit0.state,
                fit0.boundary_contact, fit0.unresolved_boundary,
            )
        contact = contact or fit0.boundary_contact
        unresolved = unresolved or fit0.unresolved_boundary

        fitk = _rc5.fit_model(detector, shape, fold_e, fold_y)
        record(j, detector, fitk, fold_e, fold_y)
        if not fitk.ok:
            return CompoundContrastRecord(
                compound_id, detector, n, None, None, fitk.state,
                fitk.boundary_contact, fitk.unresolved_boundary,
            )
        contact = contact or fitk.boundary_contact
        unresolved = unresolved or fitk.unresolved_boundary

        p0 = float(_rc5.predict_model("M0", shape, np.array([held_e]), fit0.params)[0])
        pk = float(_rc5.predict_model(detector, shape, np.array([held_e]), fitk.params)[0])
        if not (math.isfinite(p0) and math.isfinite(pk)):
            state = "NUMERICAL_FAILURE"
            break
        err0.append(abs(held_y - p0))
        errk.append(abs(held_y - pk))

    if state != "OK":
        return CompoundContrastRecord(compound_id, detector, n, None, None, state, contact, unresolved)

    mae_0 = float(np.mean(err0))
    mae_k = float(np.mean(errk))
    if not (math.isfinite(mae_0) and math.isfinite(mae_k)):
        return CompoundContrastRecord(
            compound_id, detector, n, None, None, "NUMERICAL_FAILURE", contact, unresolved
        )
    return CompoundContrastRecord(
        compound_id, detector, n, mae_0, mae_k, "OK", contact, unresolved
    )


def run_case_adequacy_instrumented(
    case_id: str,
    compounds: pd.DataFrame,
    trajectories: pd.DataFrame,
    phi: FrozenPhi,
    context: dict[str, object] | None = None,
) -> tuple[CaseAdequacyResult, list[dict[str, object]], list[dict[str, object]]]:
    """`rc5_adequacy.run_case_adequacy`, transcribed, with fit-level records.

    Returns the frozen case result unchanged, plus one record per
    (detector, compound, fold, model) fit and one per (detector, compound)
    contrast.
    """
    shape = _rc5.ProfileShape.from_phi(phi)
    test_compounds = compounds[compounds["split"] == "test"]
    if len(test_compounds) != _rc5.N_TEST_COMPOUNDS_EXPECTED:
        raise ValueError(
            f"case {case_id} has {len(test_compounds)} test compounds, "
            f"expected {_rc5.N_TEST_COMPOUNDS_EXPECTED}"
        )
    test_ids = list(test_compounds["compound_id"])

    # Identical inputs to the frozen per-compound filter, hoisted out of the
    # 90-iteration loop.  `trajectories` is emitted compound-major with energy
    # ascending, so the per-group arrays equal the frozen boolean-mask result.
    grouped = {str(cid): sub for cid, sub in trajectories.groupby("compound_id", sort=False)}

    ctx = dict(context or {})
    fits: list[dict[str, object]] = []
    contrasts: list[dict[str, object]] = []
    contrast_records: dict[str, list[CompoundContrastRecord]] = {d: [] for d in DETECTORS}

    for detector in DETECTORS:
        for cid in test_ids:
            subset = grouped[str(cid)]
            record = _evaluate_compound_contrast_instrumented(
                compound_id=cid,
                detector=detector,
                energies=subset["energy"].to_numpy(),
                mu=subset["mu"].to_numpy(),
                shape=shape,
                sink=fits,
                context=ctx,
            )
            contrast_records[detector].append(record)
            contrasts.append({
                **ctx,
                "compound_id": cid,
                "detector": detector,
                "observed_energy_count": record.observed_energy_count,
                "mae_m0": record.mae_m0,
                "mae_alt": record.mae_alt,
                "execution_state": record.execution_state,
                "boundary_contact": bool(record.boundary_contact),
                "unresolved_boundary": bool(record.unresolved_boundary),
                "mu_max_observed": float(np.max(subset["mu"].to_numpy())),
            })

    return decide_case_adequacy(case_id, contrast_records), fits, contrasts
