"""E0 (A1_ADMISSIBLE_RANGE_PROVENANCE): world generation and instrumented fitting.

New code, written for this experiment only. Reads and calls the frozen
production modules (``generator``, ``adequacy``, ``rc5_adequacy``,
``rc5_estimate``, ``registry``, ``discovery.estimate``) but modifies none of
their files on disk. The one runtime manipulation this module performs --
reassigning ``rc5_adequacy.MU_CEIL`` per cell before each world's fit -- is
the E0 fitter-side independent variable itself (design factor `MU_CEIL`,
`MURU_V2_E0_PROTOCOL.md` Sec 2), not an alteration of frozen behaviour: E0's
entire purpose is to run the frozen fitter under ceilings other than its
default, on fresh worlds it was always going to see fresh parameters for.

Seed namespace is disjoint from v1: prefix ``"muru-v2-calibration|"`` versus
``generator.derive_seed``'s ``"paper-benchmark-v1|"`` (remediation plan Sec
2.2). The world's mathematical law (mass_affine_descriptor) and covariate
generation formulas are transcribed from ``generator.py`` (read-only) so that
fresh V2C-namespaced worlds reproduce the same generative mechanism; see
``MURU_V2_E0_PROTOCOL.md`` Sec 1 for the derivation of which generative cell
is "modal" and why the specific kind label among the five functionally-tied
candidates has no numerical consequence.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys
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
from muru.paper_benchmark import registry  # noqa: E402

assert "pysr" not in sys.modules, "E0 must never import PySR"

# --------------------------------------------------------------------------
# Frozen constants reused by reference (not copied as new numeric literals)
# --------------------------------------------------------------------------
ENERGY_GRID = tuple(float(e) for e in registry.ENERGY_GRID)
N_COMPOUNDS = 180
N_SCAFFOLDS = 30
E_REF = adequacy.E_REF
MU_FLOOR = adequacy.MU_FLOOR  # 1e-4, fixed in every E0 cell (only the ceiling is varied)
V1_MU_CEIL_DEFAULT = adequacy.MU_CEIL  # 1 - 1e-4, restored between worlds defensively

SEED_NAMESPACE_PREFIX = "muru-v2-calibration|"


def derive_seed(*parts: str) -> int:
    """V2-namespaced seed derivation, disjoint from generator.derive_seed."""
    payload = SEED_NAMESPACE_PREFIX + "|".join(parts)
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


# --------------------------------------------------------------------------
# Cell design (MURU_V2_E0_PROTOCOL.md Sec 2)
# --------------------------------------------------------------------------
C_GEN_LEVELS = {
    "g1e4": 1.0 - 1e-4,
    "g1e3": 1.0 - 1e-3,
    "gnone": None,  # no clip applied
}
MU_CEIL_LEVELS = {
    "c1e4": 1.0 - 1e-4,
    "c1e3": 1.0 - 1e-3,
    "copen": 1.0 + 1e-2,
}
CONTROL_CELL = "g1e4_c1e4"
DECOUPLED_CELL = "gnone_copen"
N_REPLICATES = 60


def all_cells() -> list[str]:
    return [f"{g}_{c}" for g in C_GEN_LEVELS for c in MU_CEIL_LEVELS]


def build_world_manifest(n_replicates: int = N_REPLICATES) -> pd.DataFrame:
    """540 (9 cells x n_replicates) world index rows. No random draw here."""
    rows = []
    for g_level, g_value in C_GEN_LEVELS.items():
        for c_level, c_value in MU_CEIL_LEVELS.items():
            cell_id = f"{g_level}_{c_level}"
            for r in range(n_replicates):
                world_id = f"V2C|E0|{cell_id}|r{r:03d}"
                rows.append(
                    {
                        "world_id": world_id,
                        "cell_id": cell_id,
                        "c_gen_level": g_level,
                        "c_gen_value": g_value,
                        "mu_ceil_level": c_level,
                        "mu_ceil_value": c_value,
                        "replicate": r,
                        "seed_compounds": derive_seed("E0", f"r{r:03d}", "compounds"),
                        "seed_law": derive_seed("E0", f"r{r:03d}", "law"),
                        "seed_response": derive_seed("E0", f"r{r:03d}", "response"),
                    }
                )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# World generation: the mass_affine_descriptor law, transcribed from
# generator.py's _synthetic_compounds / _law / _response_matrix (shared M0
# branch), reseeded under the V2C namespace, with a configurable final clip.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SharedDraw:
    """One replicate's covariate + law + response draw, shared across all 9 cells."""

    replicate: int
    compounds: pd.DataFrame
    mu_raw: np.ndarray  # (180, 6), pre-clip, post-noise
    mu_inf: float
    phi_p: float
    scale: float
    coefficient: float


def _synthetic_compounds(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    scaffold = np.repeat(np.arange(N_SCAFFOLDS), N_COMPOUNDS // N_SCAFFOLDS)
    split_by_group = np.array(["train"] * 20 + ["validation"] * 5 + ["test"] * 5)
    group_latent = rng.normal(0, 1, N_SCAFFOLDS)
    latent = group_latent[scaffold] + rng.normal(0, 0.35, N_COMPOUNDS)
    mass = np.exp(5.55 + 0.25 * latent + rng.normal(0, 0.18, N_COMPOUNDS))
    descriptor = latent + rng.normal(0, 0.45, N_COMPOUNDS) - latent.min()
    descriptor /= descriptor.max()
    frame = pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N_COMPOUNDS)],
            "scaffold_id": [f"S{i:02d}" for i in scaffold],
            "split": split_by_group[scaffold],
            "mass": mass,
            "descriptor": descriptor,
        }
    )
    return frame


def generate_shared_draw(replicate: int, manifest_row_lookup: dict) -> SharedDraw:
    """Generate the one raw (pre-clip) draw shared by all 9 cells of `replicate`."""
    seed_compounds = derive_seed("E0", f"r{replicate:03d}", "compounds")
    seed_law = derive_seed("E0", f"r{replicate:03d}", "law")
    seed_response = derive_seed("E0", f"r{replicate:03d}", "response")

    compounds = _synthetic_compounds(seed_compounds)
    mass = compounds["mass"].to_numpy()
    descriptor = compounds["descriptor"].to_numpy()

    law_rng = np.random.default_rng(seed_law)
    scale = float(law_rng.uniform(1.1, 1.8))
    coefficient = float(law_rng.uniform(0.25, 0.55))
    g = scale * np.sqrt(mass / 250.0) * (1 + coefficient * descriptor)

    response_rng = np.random.default_rng(seed_response)
    mu_inf = float(response_rng.uniform(0.15, 0.30))
    phi_p = float(response_rng.uniform(1.20, 1.70))
    energy = np.asarray(ENERGY_GRID, dtype=float)
    u = (energy[None, :] / E_REF) / g[:, None]
    mu = mu_inf + (1 - mu_inf) * np.exp(-(u ** phi_p))
    mu = mu + response_rng.normal(0, 0.02, mu.shape)  # noise_sd=0.02 (default branch)

    return SharedDraw(
        replicate=replicate,
        compounds=compounds,
        mu_raw=mu,
        mu_inf=mu_inf,
        phi_p=phi_p,
        scale=scale,
        coefficient=coefficient,
    )


def clip_mu(mu_raw: np.ndarray, c_gen_value: float | None) -> np.ndarray:
    if c_gen_value is None:
        return mu_raw
    return np.clip(mu_raw, MU_FLOOR, c_gen_value)


def build_trajectories(compounds: pd.DataFrame, mu: np.ndarray) -> pd.DataFrame:
    rows = []
    for i, compound_id in enumerate(compounds["compound_id"]):
        for j, energy in enumerate(ENERGY_GRID):
            rows.append({"compound_id": compound_id, "energy": energy, "mu": float(mu[i, j])})
    return pd.DataFrame(rows)


def world_content_hash(compounds: pd.DataFrame, trajectories: pd.DataFrame) -> str:
    payload = (
        compounds.sort_values("compound_id").to_csv(index=False)
        + "|"
        + trajectories.sort_values(["compound_id", "energy"]).to_csv(index=False)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Instrumented adequacy fitting: reuses rc5_adequacy.fit_model / predict_model
# / _objective_at verbatim (imported, never modified); adds fit- and probe-
# level record capture that the frozen evaluate_compound_contrast discards.
# --------------------------------------------------------------------------


def _probe_detail(model: str, shape, energies: np.ndarray, y: np.ndarray, fit) -> list[dict]:
    """Re-derive per-bound probe detail for a fit that touched a boundary.

    Mirrors rc5_adequacy._boundary_flags's bound list exactly, calling the
    frozen _objective_at / predict_model for the probed objective, but
    returns per-probe detail instead of collapsing to two booleans.
    """
    if not (fit.ok and fit.boundary_contact):
        return []
    param_bounds: list[tuple[str, float, float]] = [
        ("log_g", rc5_adequacy.LOG_G_BOUNDS[0], rc5_adequacy.LOG_G_BOUNDS[1])
    ]
    if model == "M1":
        param_bounds.append(("log_shape", rc5_adequacy.LOG_SHAPE_BOUNDS[0], rc5_adequacy.LOG_SHAPE_BOUNDS[1]))
    elif model == "M2":
        param_bounds.append(("high_energy_asymptote", rc5_adequacy.MU_FLOOR, shape.a_lo - rc5_adequacy.MIN_VERTICAL_AMPLITUDE))
    elif model == "M3":
        param_bounds.append(("low_energy_plateau", shape.a_hi + rc5_adequacy.MIN_VERTICAL_AMPLITUDE, rc5_adequacy.MU_CEIL))

    probes = []
    for name, lower, upper in param_bounds:
        val = fit.params.get(name)
        if val is None or not math.isfinite(val):
            continue
        for bound, outward in ((lower, -1.0), (upper, 1.0)):
            if abs(val - bound) > rc5_adequacy.BOUNDARY_CONTACT_TOL:
                continue
            probed = dict(fit.params)
            probed[name] = bound + outward * rc5_adequacy.BOUNDARY_OUTWARD_PROBE
            try:
                probe_obj = rc5_adequacy._objective_at(model, shape, energies, y, probed)
            except Exception:
                continue
            gain_rel = None
            if math.isfinite(probe_obj) and math.isfinite(fit.objective) and fit.objective != 0:
                gain_rel = (fit.objective - probe_obj) / fit.objective
            probes.append(
                {
                    "probe_param": name,
                    "probe_side": "upper" if outward > 0 else "lower",
                    "probe_obj": float(probe_obj) if math.isfinite(probe_obj) else None,
                    "probe_gain_rel": gain_rel,
                    "unresolved": bool(math.isfinite(probe_obj) and probe_obj < fit.objective - 1e-12),
                }
            )
    return probes


@dataclass
class InstrumentedContrast:
    record: "rc5_adequacy.CompoundContrastRecord"
    fit_rows: list[dict] = field(default_factory=list)
    probe_rows: list[dict] = field(default_factory=list)


def instrumented_evaluate_compound_contrast(
    compound_id: str,
    detector: str,
    energies: np.ndarray,
    mu: np.ndarray,
    shape,
    world_id: str,
    cell_id: str,
    replicate: int,
    mu_ceil_used: float,
) -> InstrumentedContrast:
    """Line-for-line mirror of rc5_adequacy.evaluate_compound_contrast that
    additionally records every FitResult and boundary probe it produces.
    """
    fit_rows: list[dict] = []
    probe_rows: list[dict] = []

    e, y = rc5_adequacy._observed_energies(energies, mu)
    n = int(e.size)
    base = dict(world_id=world_id, cell_id=cell_id, replicate=replicate, compound_id=compound_id, detector=detector, mu_ceil_used=mu_ceil_used)

    def _log_fit(fold_index, held_energy, model, fit):
        row = dict(base)
        row.update(
            fold_index=fold_index,
            held_energy=float(held_energy) if held_energy is not None else None,
            model=model,
            objective=fit.objective if math.isfinite(fit.objective) else None,
            log_g=fit.params.get("log_g"),
            extra_param_name=next((k for k in fit.params if k != "log_g"), None),
            extra_param_value=next((v for k, v in fit.params.items() if k != "log_g"), None),
            boundary_contact=fit.boundary_contact,
            unresolved_boundary=fit.unresolved_boundary,
            state=fit.state,
        )
        fit_rows.append(row)
        for probe in _probe_detail(model, shape, e_local[0], e_local[1], fit):
            prow = dict(base)
            prow.update(fold_index=fold_index, model=model, **probe)
            probe_rows.append(prow)

    if n < adequacy.MIN_OBSERVED_ENERGIES:
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=None, mae_alt=None, execution_state="OK"
        )
        return InstrumentedContrast(rec, fit_rows, probe_rows)
    if not shape.usable:
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=None, mae_alt=None, execution_state="MODEL_FIT_FAILURE"
        )
        return InstrumentedContrast(rec, fit_rows, probe_rows)

    err0: list[float] = []
    errk: list[float] = []
    contact = unresolved = False
    state = "OK"

    for j in range(n):
        keep = np.ones(n, dtype=bool)
        keep[j] = False
        fold_e, fold_y = e[keep], y[keep]
        held_e, held_y = e[j], y[j]
        e_local = (fold_e, fold_y)

        fit0 = rc5_adequacy.fit_model("M0", shape, fold_e, fold_y)
        _log_fit(j, held_e, "M0", fit0)
        if not fit0.ok:
            rec = rc5_adequacy.CompoundContrastRecord(
                compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=None, mae_alt=None,
                execution_state=fit0.state, boundary_contact=fit0.boundary_contact, unresolved_boundary=fit0.unresolved_boundary,
            )
            return InstrumentedContrast(rec, fit_rows, probe_rows)
        contact = contact or fit0.boundary_contact
        unresolved = unresolved or fit0.unresolved_boundary

        fitk = rc5_adequacy.fit_model(detector, shape, fold_e, fold_y)
        _log_fit(j, held_e, detector, fitk)
        if not fitk.ok:
            rec = rc5_adequacy.CompoundContrastRecord(
                compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=None, mae_alt=None,
                execution_state=fitk.state, boundary_contact=fitk.boundary_contact, unresolved_boundary=fitk.unresolved_boundary,
            )
            return InstrumentedContrast(rec, fit_rows, probe_rows)
        contact = contact or fitk.boundary_contact
        unresolved = unresolved or fitk.unresolved_boundary

        p0 = float(rc5_adequacy.predict_model("M0", shape, np.array([held_e]), fit0.params)[0])
        pk = float(rc5_adequacy.predict_model(detector, shape, np.array([held_e]), fitk.params)[0])
        if not (math.isfinite(p0) and math.isfinite(pk)):
            state = "NUMERICAL_FAILURE"
            break
        err0.append(abs(held_y - p0))
        errk.append(abs(held_y - pk))

    if state != "OK":
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=None, mae_alt=None,
            execution_state=state, boundary_contact=contact, unresolved_boundary=unresolved,
        )
        return InstrumentedContrast(rec, fit_rows, probe_rows)

    mae_0 = float(np.mean(err0))
    mae_k = float(np.mean(errk))
    if not (math.isfinite(mae_0) and math.isfinite(mae_k)):
        rec = rc5_adequacy.CompoundContrastRecord(
            compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=None, mae_alt=None,
            execution_state="NUMERICAL_FAILURE", boundary_contact=contact, unresolved_boundary=unresolved,
        )
        return InstrumentedContrast(rec, fit_rows, probe_rows)

    rec = rc5_adequacy.CompoundContrastRecord(
        compound_id=compound_id, detector=detector, observed_energy_count=n, mae_m0=mae_0, mae_alt=mae_k,
        execution_state="OK", boundary_contact=contact, unresolved_boundary=unresolved,
    )
    return InstrumentedContrast(rec, fit_rows, probe_rows)


def run_world(manifest_row: pd.Series, shared_draw: SharedDraw) -> tuple[dict, list[dict], list[dict]]:
    """Fit one world (one cell x one replicate). Returns (world_record, fit_rows, probe_rows)."""
    world_id = manifest_row["world_id"]
    cell_id = manifest_row["cell_id"]
    replicate = int(manifest_row["replicate"])
    c_gen_value = manifest_row["c_gen_value"]
    if c_gen_value is None or (isinstance(c_gen_value, float) and math.isnan(c_gen_value)):
        c_gen_value = None  # "gnone": pandas stores the design's None as NaN in a float64 column
    else:
        c_gen_value = float(c_gen_value)
    mu_ceil_value = float(manifest_row["mu_ceil_value"])

    mu = clip_mu(shared_draw.mu_raw, c_gen_value)
    compounds = shared_draw.compounds
    trajectories = build_trajectories(compounds, mu)

    frozen_phi = rc5_estimate.fit_case_phi(compounds, trajectories)
    shape = rc5_adequacy.ProfileShape.from_phi(frozen_phi)

    previous_ceil = rc5_adequacy.MU_CEIL
    try:
        rc5_adequacy.MU_CEIL = mu_ceil_value

        test_compounds = compounds[compounds["split"] == "test"]
        test_ids = list(test_compounds["compound_id"])
        contrast_records: dict[str, list] = {d: [] for d in adequacy.DETECTORS}
        all_fit_rows: list[dict] = []
        all_probe_rows: list[dict] = []

        for detector in ("M1", "M2", "M3"):
            for cid in test_ids:
                subset = trajectories[trajectories["compound_id"] == cid]
                energies = subset["energy"].to_numpy()
                mu_vals = subset["mu"].to_numpy()
                result = instrumented_evaluate_compound_contrast(
                    cid, detector, energies, mu_vals, shape, world_id, cell_id, replicate, mu_ceil_value
                )
                contrast_records[detector].append(result.record)
                all_fit_rows.extend(result.fit_rows)
                all_probe_rows.extend(result.probe_rows)

        case_result = adequacy.decide_case_adequacy(world_id, contrast_records)
    finally:
        rc5_adequacy.MU_CEIL = previous_ceil

    m3_fit_rows = [r for r in all_fit_rows if r["model"] == "M3" and r["state"] == "OK"]
    pin_at_ceiling = [
        r for r in m3_fit_rows
        if r["extra_param_value"] is not None and abs(r["extra_param_value"] - mu_ceil_value) <= rc5_adequacy.BOUNDARY_CONTACT_TOL
    ]
    pin_at_ceiling_share = (len(pin_at_ceiling) / len(m3_fit_rows)) if m3_fit_rows else None

    if c_gen_value is not None:
        test_mu = mu[compounds["split"].to_numpy() == "test"]
        obs_max = test_mu.max(axis=1)
        mu_max_at_clip_share = float(np.mean(np.abs(obs_max - c_gen_value) <= 1e-9))
    else:
        mu_max_at_clip_share = 0.0

    boundary_counts = {d: case_result.boundary_counts.get(d, 0) for d in ("M1", "M2", "M3")}
    contrasts = case_result.contrasts
    world_record = {
        "world_id": world_id,
        "cell_id": cell_id,
        "c_gen_level": manifest_row["c_gen_level"],
        "mu_ceil_level": manifest_row["mu_ceil_level"],
        "replicate": replicate,
        "content_hash": world_content_hash(compounds, trajectories),
        "case_status": case_result.status.value,
        "false_m0_rejection": case_result.status.value.startswith("M0_REJECTED"),
        "fired": ",".join(case_result.fired),
        "boundary_counts_m1": boundary_counts["M1"],
        "boundary_counts_m2": boundary_counts["M2"],
        "boundary_counts_m3": boundary_counts["M3"],
        "evaluable_m1": contrasts["M1"].evaluable if "M1" in contrasts else None,
        "evaluable_m2": contrasts["M2"].evaluable if "M2" in contrasts else None,
        "evaluable_m3": contrasts["M3"].evaluable if "M3" in contrasts else None,
        "evaluable_sufficient_m1": contrasts["M1"].evaluable_sufficient if "M1" in contrasts else None,
        "evaluable_sufficient_m2": contrasts["M2"].evaluable_sufficient if "M2" in contrasts else None,
        "evaluable_sufficient_m3": contrasts["M3"].evaluable_sufficient if "M3" in contrasts else None,
        "practical_wins_m1": contrasts["M1"].practical_wins if "M1" in contrasts else None,
        "practical_wins_m2": contrasts["M2"].practical_wins if "M2" in contrasts else None,
        "practical_wins_m3": contrasts["M3"].practical_wins if "M3" in contrasts else None,
        "boundary_limited": case_result.status.value == "BOUNDARY_LIMITED",
        "mu_max_at_clip_share": mu_max_at_clip_share,
        "pin_at_ceiling_share": pin_at_ceiling_share,
        "n_fit_rows": len(all_fit_rows),
        "n_contact_fits": sum(1 for r in all_fit_rows if r["boundary_contact"]),
        "n_unresolved_fits": sum(1 for r in all_fit_rows if r["unresolved_boundary"]),
        "mu_inf": shared_draw.mu_inf,
        "phi_p": shared_draw.phi_p,
        "scale": shared_draw.scale,
        "coefficient": shared_draw.coefficient,
    }
    return world_record, all_fit_rows, all_probe_rows


def source_hashes() -> dict:
    files = [
        "src/muru/paper_benchmark/generator.py",
        "src/muru/paper_benchmark/adequacy.py",
        "src/muru/paper_benchmark/rc5_adequacy.py",
        "src/muru/paper_benchmark/rc5_estimate.py",
        "src/muru/paper_benchmark/registry.py",
        "src/muru/discovery/estimate.py",
        "scripts/e0_common.py",
    ]
    repo_root = os.path.dirname(_THIS_DIR)
    out = {}
    for rel in files:
        path = os.path.join(repo_root, rel)
        with open(path, "rb") as fh:
            out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out
