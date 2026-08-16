"""Stage 1: exhaustive A1 adequacy decomposition for every Held-out case.

For each case this re-derives the frozen A1 verdict *and* the per-detector,
per-compound, per-parameter attribution the sealed record never stored.

Method
------
``materialize_case -> fit_case_scalars -> fit_model`` per (compound, fold,
model).  All three are search-independent (A3.5 section 8.2) and none of them
imports PySR; ``searches_run`` stays at 0 and is asserted at the end.

The frozen ``fit_model`` already reports ``boundary_contact`` and
``unresolved_boundary`` per fit.  This script does not reimplement that logic --
it calls the frozen function once per (compound, fold, model) and *observes*
which model and which bound raised the flag.  ``evaluate_compound_contrast``
folds M0's own flags into every detector's record, so an unresolved M0 fit
poisons M1, M2 and M3 for that compound simultaneously.  That attribution is the
single most load-bearing quantity in the whole G1 diagnosis, and it is invisible
in the sealed schema, which is why it is recomputed here.

Verification
------------
The recomputed ``CaseAdequacyStatus`` is compared against the sealed
``a1_case_adequacy_status`` for all 240 cases.  Any mismatch aborts: it would
mean the regenerated content is not the executed content.
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from muru_v1_diag_common import (  # noqa: E402
    OUT_DIR,
    install_frozen_src,
    load_case_manifest,
    load_sealed_records,
    write_json,
)

install_frozen_src()

import numpy as np  # noqa: E402

from muru.paper_benchmark.adequacy import (  # noqa: E402
    BOUNDARY_CONTACT_TOL,
    DETECTORS,
    LOG_G_BOUNDS,
    LOG_SHAPE_BOUNDS,
    MIN_EVALUABLE_COMPOUNDS,
    MIN_OBSERVED_ENERGIES,
    MIN_PRACTICAL_WINS,
    MIN_VERTICAL_AMPLITUDE,
    MU_CEIL,
    MU_FLOOR,
    CompoundContrastStatus,
)
from muru.paper_benchmark.rc5_adequacy import (  # noqa: E402
    ProfileShape,
    _observed_energies,
    fit_model,
    run_case_adequacy,
)
from muru.paper_benchmark.rc5_estimate import fit_case_scalars  # noqa: E402
from muru.paper_benchmark.rc5_runner import materialize_case  # noqa: E402

MODELS = ("M0",) + tuple(DETECTORS)


def _bounds_for(model: str, shape: ProfileShape) -> list[tuple[str, float, float]]:
    """The frozen admissible ranges ``_boundary_flags`` checks, mirrored for
    attribution only.  Values are read from the frozen constants, never
    redefined."""
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


def _which_bounds_touched(model: str, shape: ProfileShape, params: dict) -> list[str]:
    """Which ``param@lower``/``param@upper`` the fitted optimum sits on."""
    touched: list[str] = []
    for name, lower, upper in _bounds_for(model, shape):
        value = params.get(name)
        if value is None or not math.isfinite(value):
            continue
        if abs(value - lower) <= BOUNDARY_CONTACT_TOL:
            touched.append(f"{name}@lower")
        if abs(value - upper) <= BOUNDARY_CONTACT_TOL:
            touched.append(f"{name}@upper")
    return touched


def decompose_case(case_id: str) -> dict:
    content = materialize_case(case_id)
    scalars = fit_case_scalars(content.compounds, content.trajectories)
    shape = ProfileShape.from_phi(scalars.frozen_phi)

    verdict = run_case_adequacy(
        case_id, content.compounds, content.trajectories, scalars.frozen_phi
    )

    compounds = content.compounds
    trajectories = content.trajectories
    test_ids = list(compounds[compounds["split"] == "test"]["compound_id"])

    # model -> set of compounds whose fit was unresolved at a bound
    unresolved_by_model: dict[str, set[str]] = {m: set() for m in MODELS}
    contact_by_model: dict[str, set[str]] = {m: set() for m in MODELS}
    bound_hits: Counter[str] = Counter()
    fit_failures: Counter[str] = Counter()
    short_energy_compounds: list[str] = []
    energy_counts: list[int] = []

    for compound_id in test_ids:
        subset = trajectories[trajectories["compound_id"] == compound_id]
        e, y = _observed_energies(
            subset["energy"].to_numpy(), subset["mu"].to_numpy()
        )
        n = int(e.size)
        energy_counts.append(n)
        if n < MIN_OBSERVED_ENERGIES:
            short_energy_compounds.append(compound_id)
            continue
        if not shape.usable:
            fit_failures["SHAPE_UNUSABLE"] += 1
            continue

        for j in range(n):
            keep = np.ones(n, dtype=bool)
            keep[j] = False
            fold_e, fold_y = e[keep], y[keep]
            for model in MODELS:
                fit = fit_model(model, shape, fold_e, fold_y)
                if not fit.ok:
                    fit_failures[f"{model}:{fit.state}"] += 1
                    continue
                if fit.boundary_contact:
                    contact_by_model[model].add(compound_id)
                if fit.unresolved_boundary:
                    unresolved_by_model[model].add(compound_id)
                    for tag in _which_bounds_touched(model, shape, fit.params):
                        bound_hits[f"{model}:{tag}"] += 1

    # A compound's contrast is BOUNDARY_LIMITED when the shared M0 fit OR the
    # detector's own fit was unresolved -- the frozen `or` in
    # evaluate_compound_contrast, observed rather than reimplemented.
    m0_unresolved = unresolved_by_model["M0"]
    attribution: dict[str, dict[str, int]] = {}
    for detector in DETECTORS:
        own = unresolved_by_model[detector]
        attribution[detector] = {
            "boundary_limited_compounds": len(m0_unresolved | own),
            "caused_by_m0_only": len(m0_unresolved - own),
            "caused_by_detector_only": len(own - m0_unresolved),
            "caused_by_both": len(m0_unresolved & own),
        }

    contrasts = {}
    for detector, result in verdict.contrasts.items():
        contrasts[detector] = {
            "evaluable": result.evaluable,
            "practical_wins": result.practical_wins,
            "evaluable_sufficient": bool(result.evaluable_sufficient),
            "fired": bool(result.fired),
            "status_counts": {k: v for k, v in result.status_counts.items() if v},
            "evaluable_shortfall": max(0, MIN_EVALUABLE_COMPOUNDS - result.evaluable),
            "wins_shortfall": max(0, MIN_PRACTICAL_WINS - result.practical_wins),
        }

    blocking = [
        d for d in DETECTORS if not verdict.contrasts[d].evaluable_sufficient
    ]

    return {
        "case_id": case_id,
        "family_id": case_id.split("|")[2],
        "recomputed_a1_status": verdict.status.value,
        "a1_blocker": verdict.blocker,
        "fired_detectors": list(verdict.fired),
        "boundary_counts_sealed_rule": dict(verdict.boundary_counts),
        "contrasts": contrasts,
        "blocking_detectors": blocking,
        "blocking_detector_count": len(blocking),
        "m0_unresolved_compounds": len(m0_unresolved),
        "unresolved_compounds_by_model": {
            m: len(unresolved_by_model[m]) for m in MODELS
        },
        "contact_compounds_by_model": {m: len(contact_by_model[m]) for m in MODELS},
        "boundary_attribution": attribution,
        "bound_hit_counts": dict(bound_hits),
        "fit_failure_counts": dict(fit_failures),
        "compounds_below_min_energies": len(short_energy_compounds),
        "min_observed_energies": int(min(energy_counts)) if energy_counts else 0,
        "max_observed_energies": int(max(energy_counts)) if energy_counts else 0,
        "shape_a_lo": float(shape.a_lo),
        "shape_a_hi": float(shape.a_hi),
        "shape_amplitude": float(shape.amplitude),
        "shape_usable": bool(shape.usable),
        "content_hash": content.content_hash,
    }


def main() -> int:
    sealed = load_sealed_records()
    manifest = load_case_manifest()
    case_ids = list(manifest)
    if len(case_ids) != 240:
        raise SystemExit(f"expected 240 Held-out cases, found {len(case_ids)}")

    rows = []
    mismatches = []
    for index, case_id in enumerate(case_ids, start=1):
        row = decompose_case(case_id)
        sealed_status = sealed[case_id]["a1_case_adequacy_status"]
        row["sealed_a1_status"] = sealed_status
        row["a1_status_reproduced"] = row["recomputed_a1_status"] == sealed_status
        if not row["a1_status_reproduced"]:
            mismatches.append(case_id)
        if row["content_hash"] != manifest[case_id]["content_hash"]:
            raise SystemExit(f"content hash drift on {case_id}")
        rows.append(row)
        if index % 10 == 0 or index == len(case_ids):
            print(f"  a1 decomposition: {index}/{len(case_ids)}", flush=True)

    if mismatches:
        raise SystemExit(
            f"{len(mismatches)} cases did not reproduce their sealed A1 verdict: "
            f"{mismatches[:5]}"
        )
    if "pysr" in sys.modules:
        raise SystemExit("PySR was imported; this stage must stay search-free")

    status_counts = Counter(r["recomputed_a1_status"] for r in rows)
    write_json(
        OUT_DIR / "a1_decomposition.json",
        {
            "method": (
                "materialize_case -> fit_case_scalars -> fit_model per "
                "(compound, fold, model); frozen predicates observed, never "
                "reimplemented"
            ),
            "searches_run": 0,
            "pysr_imported": False,
            "cases": len(rows),
            "sealed_status_reproduced": len(rows) - len(mismatches),
            "sealed_status_mismatches": len(mismatches),
            "status_counts": dict(status_counts),
            "frozen_constants": {
                "MIN_EVALUABLE_COMPOUNDS": MIN_EVALUABLE_COMPOUNDS,
                "MIN_PRACTICAL_WINS": MIN_PRACTICAL_WINS,
                "MIN_OBSERVED_ENERGIES": MIN_OBSERVED_ENERGIES,
                "LOG_G_BOUNDS": list(LOG_G_BOUNDS),
                "LOG_SHAPE_BOUNDS": list(LOG_SHAPE_BOUNDS),
                "BOUNDARY_CONTACT_TOL": BOUNDARY_CONTACT_TOL,
                "boundary_limited_status": CompoundContrastStatus.BOUNDARY_LIMITED.value,
            },
            "per_case": rows,
        },
    )
    print(f"\n  status counts: {dict(status_counts)}")
    print(f"  wrote {OUT_DIR / 'a1_decomposition.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
