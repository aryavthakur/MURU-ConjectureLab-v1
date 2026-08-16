"""E0 analysis: the preregistered metrics, abort gate and decision rule.

Every threshold, band and denominator in this module is fixed by
`MURU_V2_A1_STUDY_DESIGN.md` section 2 and `MURU_V2_E0_PROTOCOL.md` sections 3
to 5, both committed before any world existed.  The module is written to be run
exactly once over the persisted corpus.

Wilson intervals use the frozen `g2_contract` implementation so that E0's
interval convention is the endpoint's own.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from muru.paper_benchmark.adequacy import BOUNDARY_CONTACT_TOL
from muru.paper_benchmark.g2_contract import wilson_lower_95, wilson_upper_95

from . import e0_cells

__all__ = ["cell_metrics", "abort_gate", "contrast", "decide", "analyse"]

#: Design section 2.5: 30 test compounds, 6 energies, 3 detectors, 2 models.
FITS_PER_WORLD = 3 * 30 * 6 * 2
M3_FITS_PER_WORLD = 30 * 6
TEST_COMPOUNDS = 30
#: The v1 constant, kept as a fixed comparison point in the unclipped cell.
V1_CLIP_CONSTANT = 1.0 - 1e-4


def _proportion(successes: int, total: int) -> dict[str, float]:
    return {
        "successes": int(successes),
        "total": int(total),
        "rate": (successes / total) if total else float("nan"),
        "wilson_lower_95": wilson_lower_95(successes, total),
        "wilson_upper_95": wilson_upper_95(successes, total),
    }


def cell_metrics(cell: e0_cells.Cell, worlds: pd.DataFrame, fits: pd.DataFrame) -> dict[str, Any]:
    """Every metric the design names, for one cell."""
    w = worlds[worlds.cell_id == cell.cell_id]
    f = fits[fits.cell_id == cell.cell_id]
    n_worlds = len(w)

    m3 = f[f.model == "M3"]
    pinned = int(np.count_nonzero(
        np.abs(m3.low_energy_plateau.to_numpy() - cell.fitter_mu_ceil) <= BOUNDARY_CONTACT_TOL
    ))

    triggering = f[f.n_probes_triggering > 0]
    gains = triggering.probe_gain_rel_max.to_numpy()
    gains = gains[np.isfinite(gains)]

    bl_worlds = w[w.case_status == "BOUNDARY_LIMITED"]
    dominant = bl_worlds.dominant_bound_hit.value_counts()

    metrics: dict[str, Any] = {
        "cell_id": cell.cell_id,
        "generator_clip_level": cell.generator_clip_level,
        "fitter_ceil_level": cell.fitter_ceil_level,
        "generator_clip": cell.generator_clip,
        "fitter_mu_ceil": cell.fitter_mu_ceil,
        "coupled": cell.coupled,
        "n_worlds": n_worlds,
        "boundary_limited_rate": _proportion(int((w.case_status == "BOUNDARY_LIMITED").sum()), n_worlds),
        "m0_not_rejected_rate": _proportion(int((w.case_status == "M0_NOT_REJECTED").sum()), n_worlds),
        "false_rejection_rate": _proportion(int((w.n_fired > 0).sum()), n_worlds),
        "case_status_counts": {k: int(v) for k, v in w.case_status.value_counts().items()},
        "contact_rate": _proportion(int(f.boundary_contact.sum()), len(f)),
        "unresolved_rate": _proportion(int(f.unresolved_boundary.sum()), len(f)),
        "contact_rate_by_model": {
            model: _proportion(int(sub.boundary_contact.sum()), len(sub))
            for model, sub in f.groupby("model")
        },
        "unresolved_rate_by_model": {
            model: _proportion(int(sub.unresolved_boundary.sum()), len(sub))
            for model, sub in f.groupby("model")
        },
        "pin_at_ceiling_share": _proportion(pinned, len(m3)),
        "evaluable_M3": {
            "mean": float(w.evaluable_M3.mean()),
            "median": float(w.evaluable_M3.median()),
            "min": int(w.evaluable_M3.min()),
            "max": int(w.evaluable_M3.max()),
            "below_floor_24": int((w.evaluable_M3 < 24).sum()),
        },
        "probe_gain_rel": {
            "n_triggering_fits": int(len(triggering)),
            "median": float(np.median(gains)) if gains.size else None,
            "q25": float(np.percentile(gains, 25)) if gains.size else None,
            "q75": float(np.percentile(gains, 75)) if gains.size else None,
            "max": float(gains.max()) if gains.size else None,
        },
        "dominant_bound_hit_among_boundary_limited": {k: int(v) for k, v in dominant.items()},
        "modal_dominant_bound": (dominant.index[0] if len(dominant) else None),
        "generator_ceiling_clip_activations": int(w.ceiling_clip_activations.sum()),
        "generator_floor_clip_activations": int(w.floor_clip_activations.sum()),
    }

    # `mu_max_at_clip_share`: share of test compounds whose observed max
    # response equals the cell's clip exactly.  Undefined where there is no
    # clip; the v1 constant is reported there instead, for comparability.
    at_v1 = _proportion(int(w.test_compounds_mu_max_at_v1_constant.sum()), n_worlds * TEST_COMPOUNDS)
    if cell.generator_clip is None:
        metrics["mu_max_at_clip_share"] = None
        metrics["mu_max_at_clip_share_note"] = "no clip in this cell; metric undefined by construction"
    else:
        metrics["mu_max_at_clip_share"] = _proportion(
            int(w.test_compounds_mu_max_at_clip.sum()), n_worlds * TEST_COMPOUNDS
        )
    metrics["mu_max_at_v1_constant_share"] = at_v1
    metrics["world_mu_max_at_clip_rate"] = _proportion(
        int((w.test_compounds_mu_max_at_clip > 0).sum()), n_worlds
    )
    return metrics


def abort_gate(control: dict[str, Any]) -> dict[str, Any]:
    """Protocol section 3: G-A, G-B, G-C on the control cell alone."""
    ref = e0_cells.V1_MATCHED_REFERENCE
    bl = control["boundary_limited_rate"]
    overlap = (bl["wilson_lower_95"] <= ref["wilson_upper_95"]) and (
        ref["wilson_lower_95"] <= bl["wilson_upper_95"]
    )
    g_a = {
        "id": "G-A",
        "statement": "control-cell boundary_limited_rate Wilson95 overlaps the v1 matched reference",
        "control_rate": bl["rate"],
        "control_wilson_95": [bl["wilson_lower_95"], bl["wilson_upper_95"]],
        "v1_reference_rate": ref["boundary_limited_rate"],
        "v1_reference_wilson_95": [ref["wilson_lower_95"], ref["wilson_upper_95"]],
        "passed": bool(overlap),
    }
    g_b = {
        "id": "G-B",
        "statement": "modal dominant bound among BOUNDARY_LIMITED control worlds is M3 low_energy_plateau at its upper bound",
        "observed": control["modal_dominant_bound"],
        "v1_reference": ref["modal_dominant_bound"],
        "passed": control["modal_dominant_bound"] == ref["modal_dominant_bound"],
    }
    g_c = {
        "id": "G-C",
        "statement": "no detector fires on any control-cell world (every world is true M0)",
        "observed_false_rejections": control["false_rejection_rate"]["successes"],
        "v1_reference": ref["detectors_fired"],
        "passed": control["false_rejection_rate"]["successes"] == 0,
    }
    gates = [g_a, g_b, g_c]
    return {
        "gates": gates,
        "passed": all(g["passed"] for g in gates),
        "failed_ids": [g["id"] for g in gates if not g["passed"]],
    }


def contrast(name: str, worlds: pd.DataFrame, left_id: str, right_id: str) -> dict[str, Any]:
    """A paired difference in `boundary_limited_rate` between two cells.

    The cells share their replicate draws, so the pairing is exact and the
    discordant counts are a McNemar table.  The point estimate is the design's
    statistic; the interval is a paired-bootstrap addition reported for
    uncertainty and used by no decision.
    """
    def series(cell_id: str) -> pd.Series:
        sub = worlds[worlds.cell_id == cell_id].set_index("replicate").sort_index()
        return (sub.case_status == "BOUNDARY_LIMITED").astype(int)

    left, right = series(left_id), series(right_id)
    if not left.index.equals(right.index):
        raise ValueError(f"{left_id} and {right_id} are not replicate-aligned")
    n = len(left)
    delta = float(left.mean() - right.mean())

    b = int(((left == 1) & (right == 0)).sum())  # boundary-limited only on the left
    c = int(((left == 0) & (right == 1)).sum())  # only on the right
    mcnemar_p = _exact_mcnemar_p(b, c)

    diff = (left - right).to_numpy()
    rng = np.random.default_rng(20260816)
    boot = np.array([diff[rng.integers(0, n, n)].mean() for _ in range(20000)])
    return {
        "name": name,
        "left_cell": left_id,
        "right_cell": right_id,
        "left_rate": float(left.mean()),
        "right_rate": float(right.mean()),
        "delta": delta,
        "n_pairs": n,
        "discordant_left_only": b,
        "discordant_right_only": c,
        "mcnemar_exact_p": mcnemar_p,
        "paired_bootstrap_95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
    }


def _exact_mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p on the discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / float(2**n)
    return float(min(1.0, 2.0 * tail))


def decide(contrasts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Protocol section 4: the band, read on the primary statistic only."""
    primary = contrasts["primary_full_decoupling"]
    delta = primary["delta"]
    gen = contrasts["generator_clip_main_effect"]["delta"]
    fit = contrasts["fitter_ceiling_main_effect"]["delta"]
    return {
        "primary_statistic": "boundary_limited_rate(control) - boundary_limited_rate(fully decoupled)",
        "control_cell": e0_cells.CONTROL_CELL,
        "decoupled_cell": e0_cells.DECOUPLED_CELL,
        "delta_BL": delta,
        "bands": [{"outcome": o, "rule": r} for o, r in e0_cells.DECISION_BANDS],
        "band": e0_cells.classify_delta(delta),
        "supporting_not_decisional": {
            "delta_generator_clip_main_effect": gen,
            "delta_fitter_ceiling_main_effect": fit,
            "interaction_delta_minus_sum_of_main_effects": delta - (gen + fit),
        },
    }


def analyse(worlds: pd.DataFrame, fits: pd.DataFrame) -> dict[str, Any]:
    """Run the whole preregistered analysis once."""
    metrics = {cell.cell_id: cell_metrics(cell, worlds, fits) for cell in e0_cells.CELLS}
    gate = abort_gate(metrics[e0_cells.CONTROL_CELL])

    contrasts = {
        "primary_full_decoupling": contrast(
            "primary_full_decoupling", worlds, e0_cells.CONTROL_CELL, e0_cells.DECOUPLED_CELL
        ),
        "generator_clip_main_effect": contrast(
            "generator_clip_main_effect", worlds, e0_cells.CONTROL_CELL, e0_cells.GEN_ONLY_CELL
        ),
        "fitter_ceiling_main_effect": contrast(
            "fitter_ceiling_main_effect", worlds, e0_cells.CONTROL_CELL, e0_cells.FIT_ONLY_CELL
        ),
    }
    return {
        "cell_metrics": metrics,
        "abort_gate": gate,
        "contrasts": contrasts,
        "decision": decide(contrasts) if gate["passed"] else None,
        "blocked_reason": None if gate["passed"] else
            f"control-arm abort gate failed: {', '.join(gate['failed_ids'])}",
    }
