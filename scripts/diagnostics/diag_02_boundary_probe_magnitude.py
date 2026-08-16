"""Stage 2: how hard does the A1 unresolved-boundary test actually push?

``rc5_adequacy._boundary_flags`` declares a fit ``unresolved`` when a single
outward probe of ``BOUNDARY_OUTWARD_PROBE`` improves the sum of squared
residuals by *anything at all*::

    if math.isfinite(obj) and obj < best_obj - 1e-12:
        unresolved = True

There is no relative-magnitude floor, no scale normalisation, and no
significance test.  Stage 1 showed that a single unresolved fit in a single
leave-one-energy-out fold marks the whole compound ``BOUNDARY_LIMITED`` for that
detector, and that 24 evaluable compounds are needed for the contrast to decide.

This stage measures the *size* of every improvement that fired, so the
diagnosis can state whether the rule is detecting a real identifiability
failure or firing on numerically negligible slope.  It also computes, purely as
a counterfactual and without touching the official verdict, what the A1 status
distribution would have been had the test required a relative improvement of
1e-6, 1e-4, 1e-3, 1e-2 or 1e-1 instead of ``> 0``.

Nothing here is written back into the frozen rule.  The frozen ``fit_model`` is
called unmodified; only the probe comparison is re-evaluated at other
thresholds, in this script's own local copy of the arithmetic.
"""
from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    install_frozen_src,
    load_case_manifest,
    write_json,
)

install_frozen_src()

import numpy as np  # noqa: E402

from muru.paper_benchmark.adequacy import (  # noqa: E402
    BOUNDARY_CONTACT_TOL,
    BOUNDARY_OUTWARD_PROBE,
    DETECTORS,
    LOG_G_BOUNDS,
    LOG_SHAPE_BOUNDS,
    MIN_EVALUABLE_COMPOUNDS,
    MIN_OBSERVED_ENERGIES,
    MIN_PRACTICAL_WINS,
    MIN_VERTICAL_AMPLITUDE,
    MU_CEIL,
    MU_FLOOR,
    is_practical_win,
)
from muru.paper_benchmark.rc5_adequacy import (  # noqa: E402
    ProfileShape,
    _objective_at,
    _observed_energies,
    fit_model,
    predict_model,
)
from muru.paper_benchmark.rc5_estimate import fit_case_scalars  # noqa: E402
from muru.paper_benchmark.rc5_runner import materialize_case  # noqa: E402

MODELS = ("M0",) + tuple(DETECTORS)

#: Counterfactual relative-improvement floors, in addition to the frozen ``>0``.
REL_FLOORS = (0.0, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1)


def _bounds_for(model: str, shape: ProfileShape) -> list[tuple[str, float, float]]:
    bounds = [("log_g", LOG_G_BOUNDS[0], LOG_G_BOUNDS[1])]
    if model == "M1":
        bounds.append(("log_shape", LOG_SHAPE_BOUNDS[0], LOG_SHAPE_BOUNDS[1]))
    elif model == "M2":
        bounds.append(
            ("high_energy_asymptote", MU_FLOOR, shape.a_lo - MIN_VERTICAL_AMPLITUDE)
        )
    elif model == "M3":
        bounds.append(
            ("low_energy_plateau", shape.a_hi + MIN_VERTICAL_AMPLITUDE, MU_CEIL)
        )
    return bounds


def _probe_improvements(
    model: str,
    shape: ProfileShape,
    energies: np.ndarray,
    y: np.ndarray,
    params: dict,
    best_obj: float,
) -> list[tuple[str, float]]:
    """(bound_tag, relative SSE improvement) for every bound the fit sits on."""
    out: list[tuple[str, float]] = []
    for name, lower, upper in _bounds_for(model, shape):
        value = params.get(name)
        if value is None or not math.isfinite(value):
            continue
        for bound, outward, side in ((lower, -1.0, "lower"), (upper, +1.0, "upper")):
            if abs(value - bound) > BOUNDARY_CONTACT_TOL:
                continue
            probed = dict(params)
            probed[name] = bound + outward * BOUNDARY_OUTWARD_PROBE
            try:
                obj = _objective_at(model, shape, energies, y, probed)
            except Exception:
                continue
            if not math.isfinite(obj):
                continue
            absolute = best_obj - obj
            relative = absolute / best_obj if best_obj > 0 else float("inf")
            out.append((f"{model}:{name}@{side}", relative))
    return out


def analyse_case(case_id: str) -> dict:
    content = materialize_case(case_id)
    scalars = fit_case_scalars(content.compounds, content.trajectories)
    shape = ProfileShape.from_phi(scalars.frozen_phi)

    compounds = content.compounds
    trajectories = content.trajectories
    test_ids = list(compounds[compounds["split"] == "test"]["compound_id"])

    improvements: list[float] = []
    tagged: list[tuple[str, float]] = []
    # floor -> model -> set of compounds unresolved at that floor
    unresolved: dict[float, dict[str, set[str]]] = {
        floor: {m: set() for m in MODELS} for floor in REL_FLOORS
    }
    # detector -> compound -> (mae_m0, mae_alt) when the LOEO loop completes
    losses: dict[str, dict[str, tuple[float, float]]] = {d: {} for d in DETECTORS}
    short_energy: set[str] = set()

    for compound_id in test_ids:
        subset = trajectories[trajectories["compound_id"] == compound_id]
        e, y = _observed_energies(subset["energy"].to_numpy(), subset["mu"].to_numpy())
        n = int(e.size)
        if n < MIN_OBSERVED_ENERGIES:
            short_energy.add(compound_id)
            continue

        err: dict[str, list[float]] = {m: [] for m in MODELS}
        broke = False
        for j in range(n):
            keep = np.ones(n, dtype=bool)
            keep[j] = False
            fold_e, fold_y = e[keep], y[keep]
            for model in MODELS:
                fit = fit_model(model, shape, fold_e, fold_y)
                if not fit.ok:
                    broke = True
                    break
                for tag, relative in _probe_improvements(
                    model, shape, fold_e, fold_y, fit.params, fit.objective
                ):
                    if relative > 0.0:
                        improvements.append(relative)
                        tagged.append((tag, relative))
                    for floor in REL_FLOORS:
                        if relative > floor:
                            unresolved[floor][model].add(compound_id)
                pred = float(
                    predict_model(model, shape, np.array([e[j]]), fit.params)[0]
                )
                if not math.isfinite(pred):
                    broke = True
                    break
                err[model].append(abs(y[j] - pred))
            if broke:
                break
        if broke:
            continue
        mae0 = float(np.mean(err["M0"]))
        for detector in DETECTORS:
            losses[detector][compound_id] = (mae0, float(np.mean(err[detector])))

    # Counterfactual adequacy at each floor, applying the frozen aggregation.
    counterfactual: dict[str, dict] = {}
    for floor in REL_FLOORS:
        per_detector = {}
        fired = []
        blocked = []
        for detector in DETECTORS:
            excluded = unresolved[floor]["M0"] | unresolved[floor][detector]
            evaluable = 0
            wins = 0
            for compound_id, (mae0, maek) in losses[detector].items():
                if compound_id in excluded:
                    continue
                evaluable += 1
                if is_practical_win(mae0, maek):
                    wins += 1
            sufficient = evaluable >= MIN_EVALUABLE_COMPOUNDS
            did_fire = sufficient and wins >= MIN_PRACTICAL_WINS
            per_detector[detector] = {
                "evaluable": evaluable,
                "practical_wins": wins,
                "evaluable_sufficient": sufficient,
                "fired": did_fire,
            }
            if did_fire:
                fired.append(detector)
            if not sufficient:
                blocked.append(detector)
        if fired:
            status = (
                "M0_REJECTED_MULTIPLE" if len(fired) > 1 else f"M0_REJECTED_{fired[0]}"
            )
        elif not blocked:
            status = "M0_NOT_REJECTED"
        else:
            status = "BOUNDARY_LIMITED"
        counterfactual[repr(floor)] = {
            "status": status,
            "blocking_detectors": blocked,
            "fired_detectors": fired,
            "per_detector": per_detector,
        }

    tag_counts: Counter[str] = Counter(tag for tag, _ in tagged)
    return {
        "case_id": case_id,
        "family_id": case_id.split("|")[2],
        "probe_improvement_count": len(improvements),
        "probe_improvement_quantiles": _quantiles(improvements),
        "probe_tag_counts": dict(tag_counts),
        "compounds_below_min_energies": len(short_energy),
        "counterfactual_by_relative_floor": counterfactual,
    }


def _quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    array = np.asarray(values, dtype=float)
    return {
        "min": float(array.min()),
        "p05": float(np.quantile(array, 0.05)),
        "p25": float(np.quantile(array, 0.25)),
        "median": float(np.median(array)),
        "p75": float(np.quantile(array, 0.75)),
        "p95": float(np.quantile(array, 0.95)),
        "max": float(array.max()),
    }


def main() -> int:
    manifest = load_case_manifest()
    case_ids = list(manifest)

    rows = []
    pooled: list[float] = []
    pooled_tags: Counter[str] = Counter()
    for index, case_id in enumerate(case_ids, start=1):
        row = analyse_case(case_id)
        rows.append(row)
        quant = row["probe_improvement_quantiles"]
        if quant:
            pooled.append(quant["median"])
        for tag, count in row["probe_tag_counts"].items():
            pooled_tags[tag] += count
        if index % 10 == 0 or index == len(case_ids):
            print(f"  boundary probe: {index}/{len(case_ids)}", flush=True)

    status_by_floor = {
        repr(floor): dict(
            Counter(r["counterfactual_by_relative_floor"][repr(floor)]["status"] for r in rows)
        )
        for floor in REL_FLOORS
    }

    write_json(
        OUT_DIR / "boundary_probe_magnitude.json",
        {
            "method": (
                "frozen fit_model called unmodified; the outward-probe SSE "
                "comparison is re-evaluated at additional relative floors in "
                "this script only.  The frozen rule (floor 0.0) is reproduced "
                "as the control arm."
            ),
            "frozen_rule": "unresolved iff probed_sse < best_sse - 1e-12 (no relative floor)",
            "BOUNDARY_OUTWARD_PROBE": BOUNDARY_OUTWARD_PROBE,
            "relative_floors_tested": list(REL_FLOORS),
            "pooled_median_of_case_medians": float(np.median(pooled)) if pooled else None,
            "pooled_probe_tag_counts": dict(pooled_tags),
            "a1_status_counts_by_relative_floor": status_by_floor,
            "per_case": rows,
        },
    )
    print("\n  A1 status by counterfactual relative floor:")
    for floor in REL_FLOORS:
        print(f"    {floor!r:>8}: {status_by_floor[repr(floor)]}")
    print(f"  wrote {OUT_DIR / 'boundary_probe_magnitude.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
