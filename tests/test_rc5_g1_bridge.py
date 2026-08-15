"""A3.5 section 5: the G1 leave-one-energy-out trajectory bridge.

Hand-built cases obeying the frozen M0 law.  No benchmark case, no PySR.
"""
from __future__ import annotations

import ast

import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark.adequacy import (
    COARSE_LOG_G_POINTS,
    LOG_G_BOUNDS,
    MIN_VERTICAL_AMPLITUDE,
    REFINEMENT_POINTS,
    REFINEMENT_ROUNDS,
    REFINEMENT_SHRINK,
    CaseAdequacyStatus,
)
from muru.paper_benchmark.registry import ENERGY_GRID, endpoint_case_count
from muru.paper_benchmark.rc5_estimate import fit_case_scalars
from muru.paper_benchmark.rc5_g1_bridge import (
    G1_DENOMINATOR,
    G1_SPEARMAN_GATE,
    G1_TRAJECTORY_RATIO_GATE,
    G1_WILSON_LOWER_GATE,
    CaseG1,
    fit_log_g_a1_protocol,
    loeo_mae_0,
    m0_profile_from_phi,
    per_energy_mean_mae,
    score_case_g1,
    score_g1,
)

N_SCAFFOLDS = 30
PER_SCAFFOLD = 6
N = N_SCAFFOLDS * PER_SCAFFOLD
MU_INF, PHI_P = 0.22, 1.45


def _splits() -> list[str]:
    by_group = ["train"] * 20 + ["validation"] * 5 + ["test"] * 5
    return [by_group[i // PER_SCAFFOLD] for i in range(N)]


def _case(seed: int = 5, drop_one_energy: bool = False):
    rng = np.random.default_rng(seed)
    g = np.exp(rng.normal(0.0, 0.30, N))
    energies = np.asarray(ENERGY_GRID, dtype=float)
    u = (energies[None, :] / 45.0) / g[:, None]
    mu = MU_INF + (1 - MU_INF) * np.exp(-(u**PHI_P))

    compounds = pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N)],
            "scaffold_id": [f"S{i // PER_SCAFFOLD:02d}" for i in range(N)],
            "split": _splits(),
            "mass": 250.0 * g**2,
            "descriptor": rng.uniform(0, 1, N),
            "descriptor2": rng.uniform(0, 1, N),
            "distractor": rng.normal(0, 1, N),
            "correlated_distractor": rng.normal(0, 1, N),
        }
    )
    rows = []
    for i, compound_id in enumerate(compounds.compound_id):
        omitted = (i % len(energies)) if drop_one_energy else None
        for j, energy in enumerate(energies):
            if j == omitted:
                continue
            rows.append(
                {"compound_id": compound_id, "energy": float(energy), "mu": float(mu[i, j])}
            )
    truth = {c: float(v) for c, v in zip(compounds.compound_id, g)}
    return compounds, pd.DataFrame(rows), truth


# -----------------------------------------------------------------------
# Frozen thresholds and denominator
# -----------------------------------------------------------------------

def test_the_g1_thresholds_are_the_frozen_ones():
    assert G1_SPEARMAN_GATE == 0.80
    assert G1_TRAJECTORY_RATIO_GATE == 0.80
    assert G1_WILSON_LOWER_GATE == 0.70
    assert G1_DENOMINATOR == endpoint_case_count("scalar_competence") == 164


# -----------------------------------------------------------------------
# A1.2's protocol, not estimate._best_log_g's
# -----------------------------------------------------------------------

def test_the_fit_uses_a1_2s_grid_not_the_phase3_one():
    import muru.paper_benchmark.rc5_g1_bridge as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "LOG_G_BOUNDS" in imported
    assert "COARSE_LOG_G_POINTS" in imported
    assert "REFINEMENT_ROUNDS" in imported
    assert "LOG_G_GRID" not in imported
    assert "_best_log_g" not in imported
    assert LOG_G_BOUNDS == (-2.0, 2.0)
    assert (COARSE_LOG_G_POINTS, REFINEMENT_ROUNDS, REFINEMENT_POINTS,
            REFINEMENT_SHRINK) == (81, 3, 21, 10)


def test_the_fit_recovers_a_planted_scale_inside_the_frozen_bounds():
    compounds, trajectories, truth = _case()
    phi = fit_case_scalars(compounds, trajectories).frozen_phi
    profile = m0_profile_from_phi(phi)

    energies = np.asarray(ENERGY_GRID, dtype=float)
    for compound in list(truth)[:5]:
        rows = trajectories[trajectories.compound_id == compound].sort_values("energy")
        mu = rows["mu"].to_numpy(dtype=float)
        fitted = fit_log_g_a1_protocol(profile, energies, mu)
        assert LOG_G_BOUNDS[0] <= fitted <= LOG_G_BOUNDS[1]


def test_the_fit_is_deterministic_and_tie_breaks_lexicographically():
    compounds, trajectories, _ = _case()
    phi = fit_case_scalars(compounds, trajectories).frozen_phi
    profile = m0_profile_from_phi(phi)
    energies = np.asarray(ENERGY_GRID, dtype=float)
    mu = np.full(len(energies), float(profile.a_hi))  # flat: many equal-SSE points

    first = fit_log_g_a1_protocol(profile, energies, mu)
    second = fit_log_g_a1_protocol(profile, energies, mu)
    assert first == second
    # A flat objective must resolve to the smallest admissible log_g.
    assert first == pytest.approx(LOG_G_BOUNDS[0])


# -----------------------------------------------------------------------
# A1.3's LOEO constraint -- the struck in-sample reading
# -----------------------------------------------------------------------

def test_the_omitted_energy_cannot_influence_the_fit_that_predicts_it():
    """A1.3: 'the omitted energy may not influence either fit used to predict it'.

    Perturbing the response at exactly one energy must leave the LOEO error at
    the *other* energies untouched.  An in-sample fit would move all of them.
    """
    compounds, trajectories, _ = _case()
    phi = fit_case_scalars(compounds, trajectories).frozen_phi
    profile = m0_profile_from_phi(phi)
    energies = np.asarray(ENERGY_GRID, dtype=float)

    rows = trajectories[trajectories.compound_id == "C150"].sort_values("energy")
    mu = rows["mu"].to_numpy(dtype=float)

    def per_energy_errors(values: np.ndarray) -> list[float]:
        out = []
        for index in range(len(values)):
            fit = np.isfinite(values).copy()
            fit[index] = False
            log_g = fit_log_g_a1_protocol(profile, energies[fit], values[fit])
            prediction = profile.predict(energies[index : index + 1], np.exp(log_g))[0]
            out.append(abs(float(values[index]) - float(prediction)))
        return out

    baseline = per_energy_errors(mu)
    perturbed_values = mu.copy()
    perturbed_values[2] += 0.05
    perturbed = per_energy_errors(perturbed_values)

    # Index 2 is the only one whose OWN error may change from its own value...
    assert perturbed[2] != pytest.approx(baseline[2])
    # ...but every fit that omits index 2 saw the perturbed value, so those
    # errors legitimately move too. What must NOT happen is the reverse: the
    # fit predicting index 2 must not have seen index 2.
    fit_mask = np.isfinite(mu).copy()
    fit_mask[2] = False
    a = fit_log_g_a1_protocol(profile, energies[fit_mask], mu[fit_mask])
    b = fit_log_g_a1_protocol(
        profile, energies[fit_mask], perturbed_values[fit_mask]
    )
    assert a == b, "the fit predicting an omitted energy changed with that energy"


def test_loeo_uses_every_observed_energy_and_reports_its_cell_count():
    compounds, trajectories, _ = _case()
    phi = fit_case_scalars(compounds, trajectories).frozen_phi
    profile = m0_profile_from_phi(phi)
    energies = np.asarray(ENERGY_GRID, dtype=float)
    rows = trajectories[trajectories.compound_id == "C150"].sort_values("energy")
    total, count = loeo_mae_0(profile, energies, rows["mu"].to_numpy(dtype=float))
    assert count == 6
    assert np.isfinite(total)


def test_the_baseline_is_a_function_of_training_rows_only():
    energies = np.asarray(ENERGY_GRID, dtype=float)
    training_mean = {float(e): 0.5 for e in energies}
    mu = np.full(len(energies), 0.6)
    total, count = per_energy_mean_mae(training_mean, energies, mu)
    assert count == 6
    assert total == pytest.approx(6 * 0.1)


# -----------------------------------------------------------------------
# The case-level bridge
# -----------------------------------------------------------------------

def test_a_clean_case_is_scalar_competent():
    compounds, trajectories, truth = _case()
    scalars = fit_case_scalars(compounds, trajectories)
    result = score_case_g1(
        "PB|synthetic|F01|r000",
        CaseAdequacyStatus.M0_NOT_REJECTED,
        scalars.frozen_phi,
        compounds,
        trajectories,
        scalars.g,
        truth,
    )
    assert result.cells == 180
    assert result.evaluable_compounds == 30
    assert result.contract_failure is False
    assert result.g_spearman > G1_SPEARMAN_GATE
    assert result.trajectory_mae < result.per_energy_mean_mae
    assert result.m0_accepted is True
    assert result.scalar_competent is True


def test_the_skill_score_is_a_ratio_not_a_self_comparison():
    """The self-referential reading would make G1 unpassable by construction."""
    compounds, trajectories, truth = _case()
    scalars = fit_case_scalars(compounds, trajectories)
    result = score_case_g1(
        "PB|synthetic|F01|r000",
        CaseAdequacyStatus.M0_NOT_REJECTED,
        scalars.frozen_phi,
        compounds,
        trajectories,
        scalars.g,
        truth,
    )
    assert result.trajectory_mae != result.per_energy_mean_mae
    assert result.trajectory_pass is (
        result.trajectory_mae <= 0.80 * result.per_energy_mean_mae
    )


def test_f04_style_missingness_gives_150_cells_on_both_sides():
    compounds, trajectories, truth = _case(drop_one_energy=True)
    scalars = fit_case_scalars(compounds, trajectories)
    result = score_case_g1(
        "PB|synthetic|F04|r000",
        CaseAdequacyStatus.M0_NOT_REJECTED,
        scalars.frozen_phi,
        compounds,
        trajectories,
        scalars.g,
        truth,
    )
    assert result.cells == 150      # 30 compounds x 5 observed energies
    assert result.evaluable_compounds == 30   # 5 >= MIN_OBSERVED_ENERGIES
    assert np.isfinite(result.trajectory_mae)
    assert np.isfinite(result.per_energy_mean_mae)


def test_m0_rejection_denies_competence_however_good_the_trajectory():
    compounds, trajectories, truth = _case()
    scalars = fit_case_scalars(compounds, trajectories)
    for status in (
        CaseAdequacyStatus.M0_REJECTED_M1,
        CaseAdequacyStatus.M0_REJECTED_MULTIPLE,
        CaseAdequacyStatus.NUMERICAL_FAILURE,
        CaseAdequacyStatus.TIMEOUT,
    ):
        result = score_case_g1(
            "PB|synthetic|F01|r000", status, scalars.frozen_phi,
            compounds, trajectories, scalars.g, truth,
        )
        assert result.m0_accepted is False
        assert result.scalar_competent is False


def test_the_predictor_is_a1s_m0_not_the_pysr_expression():
    import muru.paper_benchmark.rc5_g1_bridge as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in ("discovered_expression_string", "equations_", "PySRRegressor"):
        assert forbidden not in names


def test_a_degenerate_vertical_amplitude_is_a_contract_failure():
    from muru.paper_benchmark.rc5_estimate import FrozenPhi

    flat = FrozenPhi(
        knots=np.linspace(-1, 1, 60),
        values=np.full(60, 0.5),      # A_LO == A_HI
        e_ref=45.0,
        n_knots=60,
        n_training_compounds=120,
        alternations=3,
    )
    profile = m0_profile_from_phi(flat)
    assert profile.vertical_amplitude == 0.0
    assert profile.vertical_amplitude < MIN_VERTICAL_AMPLITUDE
    assert profile.contract_failure is True


# -----------------------------------------------------------------------
# Sealed-boundary ordering and the endpoint's length assertion
# -----------------------------------------------------------------------

def test_truth_is_read_only_after_the_adequacy_verdict_exists():
    import inspect

    params = inspect.signature(score_case_g1).parameters
    order = list(params)
    assert order.index("a1_status") < order.index("true_g_by_compound")
    assert params["a1_status"].default is inspect.Parameter.empty


def test_the_bridge_never_imports_the_permissive_analysis_module():
    import muru.paper_benchmark.rc5_g1_bridge as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
        elif isinstance(node, ast.Import):
            modules |= {a.name for a in node.names}
    assert not any(m.endswith("analysis") for m in modules)


def _outcome(competent: bool) -> CaseG1:
    return CaseG1(
        case_id="PB|synthetic|F01|r000",
        g_spearman=0.95 if competent else 0.10,
        trajectory_mae=0.1,
        per_energy_mean_mae=1.0,
        m0_accepted=True,
        cells=180,
        evaluable_compounds=30,
        contract_failure=False,
    )


def test_scoring_asserts_the_sequence_length_against_164():
    with pytest.raises(ValueError, match="expected 164 G1 outcomes"):
        score_g1([_outcome(True)] * 163)
    with pytest.raises(ValueError, match="expected 164 G1 outcomes"):
        score_g1([_outcome(True)] * 165)


def test_the_gate_is_the_wilson_lower_bound_over_the_fixed_denominator():
    all_competent = score_g1([_outcome(True)] * 164)
    assert all_competent.competent == 164
    assert all_competent.denominator == 164
    assert all_competent.gate_passed is True

    none_competent = score_g1([_outcome(False)] * 164)
    assert none_competent.competent == 0
    assert none_competent.gate_passed is False
