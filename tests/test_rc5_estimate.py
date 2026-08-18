"""A3.5 section 4: ``Phi``, per-compound ``g``, the search target,
``invalid_fraction``.

Every fixture is hand-built from the frozen M0 law, so no benchmark case is
generated and the sealed-state attestations do not move.

The five regressions A3.5's corrections exist to prevent each have a test that
would fail if the correction were reverted:

1. ``ENERGY_SCALE = 30.0`` leaking into benchmark estimation
2. ``g`` silently rescaled by 2/3
3. post-freeze re-centring reintroduced
4. denominator 36 used for a production case
5. the wrong estimator machinery substituted for the A1-compatible procedure
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from muru.discovery.estimate import ENERGY_SCALE, LOG_G_GRID, N_ALTERNATIONS
from muru.paper_benchmark.adequacy import E_REF as ADEQUACY_E_REF
from muru.paper_benchmark.registry import ENERGY_GRID
from muru.paper_benchmark.rc5_estimate import (
    A35_LOG_G_GRID,
    A35_LOG_G_GRID_HIGH,
    A35_LOG_G_GRID_LOW,
    A35_LOG_G_GRID_POINTS,
    E_REF,
    N_VALIDATION_COMPOUNDS,
    PHI_ALTERNATIONS,
    PHI_N_KNOTS,
    estimate_case_g,
    fit_case_phi,
    fit_case_scalars,
    invalid_fraction,
    invalid_fraction_passes,
)

MU_INF = 0.22
PHI_P = 1.45
N_SCAFFOLDS = 30
PER_SCAFFOLD = 6
N_COMPOUNDS = N_SCAFFOLDS * PER_SCAFFOLD  # 180, the frozen geometry


def _splits() -> list[str]:
    """The frozen 20/5/5 scaffold-group split, x6 compounds -> 120/30/30."""
    by_group = ["train"] * 20 + ["validation"] * 5 + ["test"] * 5
    return [by_group[i // PER_SCAFFOLD] for i in range(N_COMPOUNDS)]


def _truth_g(rng: np.random.Generator) -> np.ndarray:
    # Deliberately spread but well inside the grid, so a boundary hit is not
    # what any assertion below is really measuring.
    return np.exp(rng.normal(0.0, 0.30, N_COMPOUNDS))


def _case(seed: int = 7, e_ref: float = 45.0, drop_one_energy: bool = False):
    """A synthetic case obeying the frozen M0 law exactly."""
    rng = np.random.default_rng(seed)
    g = _truth_g(rng)
    energies = np.asarray(ENERGY_GRID, dtype=float)
    u = (energies[None, :] / e_ref) / g[:, None]
    mu = MU_INF + (1 - MU_INF) * np.exp(-(u**PHI_P))

    compounds = pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N_COMPOUNDS)],
            "scaffold_id": [f"S{i // PER_SCAFFOLD:02d}" for i in range(N_COMPOUNDS)],
            "split": _splits(),
            "mass": 250.0 * g**2,
            "descriptor": rng.uniform(0, 1, N_COMPOUNDS),
            "descriptor2": rng.uniform(0, 1, N_COMPOUNDS),
            "distractor": rng.normal(0, 1, N_COMPOUNDS),
            "correlated_distractor": rng.normal(0, 1, N_COMPOUNDS),
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
    return compounds, pd.DataFrame(rows), g


# -----------------------------------------------------------------------
# Constants and provenance
# -----------------------------------------------------------------------

def test_e_ref_is_the_benchmark_45_not_the_phase3_30():
    assert E_REF == 45.0
    assert E_REF is ADEQUACY_E_REF or E_REF == ADEQUACY_E_REF
    assert ENERGY_SCALE == 30.0
    assert E_REF != ENERGY_SCALE


def _imported_names(module) -> set[str]:
    """Every name the module actually imports, by AST, not by text search."""
    import ast

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.name)
    return names


def test_the_grid_is_stated_explicitly_not_imported():
    import muru.paper_benchmark.rc5_estimate as module

    # Section 4.1: "stated explicitly rather than imported".  Checked against
    # the real import list, so a docstring quoting the prohibition does not
    # accidentally satisfy or violate it.
    imported = _imported_names(module)
    assert "LOG_G_GRID" not in imported
    assert "N_ALTERNATIONS" not in imported
    assert "ENERGY_SCALE" not in imported

    assert (A35_LOG_G_GRID_LOW, A35_LOG_G_GRID_HIGH, A35_LOG_G_GRID_POINTS) == (
        -1.6,
        1.6,
        241,
    )
    # Same arithmetic as the frozen module, owned here: no new number, and a
    # later edit to the Phase-3 constant cannot move the benchmark silently.
    assert np.allclose(A35_LOG_G_GRID, LOG_G_GRID)
    assert PHI_ALTERNATIONS == N_ALTERNATIONS == 3
    assert PHI_N_KNOTS == 60


def test_phi_shape_constants_are_the_frozen_ones():
    compounds, trajectories, _ = _case()
    phi = fit_case_phi(compounds, trajectories)
    assert phi.n_knots == 60
    assert len(phi.knots) == 60
    assert len(phi.values) == 60
    assert phi.e_ref == 45.0
    assert phi.n_training_compounds == 120


# -----------------------------------------------------------------------
# Phi: fold locality, monotonicity, clamp
# -----------------------------------------------------------------------

def test_phi_is_fitted_on_the_training_fold_only():
    compounds, trajectories, _ = _case()
    phi_all = fit_case_phi(compounds, trajectories)

    # Corrupting only validation/test rows must not move the frozen profile.
    corrupted = trajectories.copy()
    non_train = set(
        compounds.loc[compounds.split != "train", "compound_id"].astype(str)
    )
    mask = corrupted.compound_id.astype(str).isin(non_train)
    corrupted.loc[mask, "mu"] = 0.5
    phi_corrupt = fit_case_phi(compounds, corrupted)

    assert np.array_equal(phi_all.knots, phi_corrupt.knots)
    assert np.array_equal(phi_all.values, phi_corrupt.values)


def test_phi_is_monotone_non_increasing_on_its_knot_grid():
    compounds, trajectories, _ = _case()
    phi = fit_case_phi(compounds, trajectories)
    assert np.all(np.diff(phi.values) <= 0.0)


def test_phi_clamps_flat_outside_the_knot_range():
    compounds, trajectories, _ = _case()
    phi = fit_case_phi(compounds, trajectories)
    lo = float(np.exp(phi.knots[0]))
    hi = float(np.exp(phi.knots[-1]))
    assert phi.evaluate(np.array([lo / 1e6]))[0] == pytest.approx(phi.values[0])
    assert phi.evaluate(np.array([hi * 1e6]))[0] == pytest.approx(phi.values[-1])


# -----------------------------------------------------------------------
# g: A1-compatible, no re-centring, right scale
# -----------------------------------------------------------------------

def test_g_recovers_the_planted_scalar_up_to_a_positive_constant():
    compounds, trajectories, truth = _case()
    scalars = fit_case_scalars(compounds, trajectories)
    ratio = scalars.g / truth
    # A single positive constant across every compound is exactly the
    # identification A1 allows.
    assert np.std(np.log(ratio)) < 0.05
    from scipy.stats import spearmanr  # noqa: PLC0415 - optional, checked below

    rho = spearmanr(scalars.g, truth).statistic
    assert rho > 0.98


def test_no_post_freeze_recentering_of_log_g():
    """Regression 3: post-freeze re-centring reintroduced.

    A re-centred estimate has mean(log g) == 0 by construction.  The frozen
    contract forbids that once ``Phi`` is fixed, so the mean must be free to
    sit wherever the frozen profile puts it.
    """
    compounds, trajectories, _ = _case()
    phi = fit_case_phi(compounds, trajectories)
    g = estimate_case_g(phi, compounds, trajectories)
    mean_log_g = float(np.mean(np.log(g)))
    assert abs(mean_log_g) > 1e-6, (
        "mean(log g) is ~0, which is the signature of a post-freeze re-centring "
        "that A3.5 section 4.1 forbids"
    )


def test_no_mean_subtraction_appears_in_the_post_freeze_estimator():
    """Structural companion to the numeric test above, by AST not text.

    A docstring saying "no ``.mean()`` here" must not be able to fail the test,
    and a real ``.mean()`` hidden in a comment-free line must not be able to
    pass it.
    """
    import ast
    import inspect
    import textwrap

    import muru.paper_benchmark.rc5_estimate as module

    tree = ast.parse(textwrap.dedent(inspect.getsource(module.estimate_case_g)))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "mean" not in called
    names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    assert "mean" not in names


def test_energy_scale_30_leaks_exactly_where_a3_5_says_and_nowhere_here():
    """Regressions 1 and 2, at the boundary A3.5 section 4.1 actually names.

    Section 4.1's claim is about **reusing ``estimate.py`` verbatim**:
    ``estimate._best_log_g`` divides by its module constant
    ``ENERGY_SCALE = 30.0``, so pointing it at a ``Phi`` fitted on the
    benchmark's ``E_REF = 45.0`` normalises by 30 against a truth generated on
    45 and rescales every ``g_hat`` by exactly 45/30.  That is the leak, and it
    is reproduced here so the regression is anchored to a real failure mode.

    Note what the leak is *not*: changing ``E_REF`` uniformly across **both**
    stages is absorbed by the isotonic ``Phi``, which is re-fitted on the same
    ``u``, so an end-to-end scale change leaves ``g_hat`` unchanged.  The leak
    is therefore invisible end-to-end and detectable only at this boundary --
    which is precisely why section 4.1's remedy is "parameterise the scale"
    inside the estimator rather than "pass a different constant".
    """
    from muru.discovery.estimate import _best_log_g as phase3_best_log_g

    compounds, trajectories, _ = _case()
    correct = fit_case_scalars(compounds, trajectories)
    assert correct.frozen_phi.e_ref == 45.0

    energies = np.asarray(ENERGY_GRID, dtype=float)
    pivot = trajectories.pivot_table(
        index="compound_id", columns="energy", values="mu"
    ).reindex(list(correct.compound_ids))
    mu = pivot.to_numpy(dtype=float)

    leaked = np.exp(
        phase3_best_log_g(
            energies, mu, correct.frozen_phi.knots, correct.frozen_phi.values
        )
    )
    ratio = correct.g / leaked
    assert np.median(ratio) == pytest.approx(30.0 / 45.0, rel=0.02)
    assert not np.allclose(correct.g, leaked)


def test_an_end_to_end_scale_change_is_absorbed_by_the_refitted_profile():
    # Recorded as a property, so a future reader does not mistake the absence
    # of an end-to-end 2/3 shift for a missing correction.
    compounds, trajectories, _ = _case()
    at_45 = fit_case_scalars(compounds, trajectories, e_ref=45.0)
    at_30 = fit_case_scalars(compounds, trajectories, e_ref=30.0)
    assert at_45.frozen_phi.e_ref == 45.0
    assert at_30.frozen_phi.e_ref == 30.0
    assert np.allclose(at_45.g, at_30.g, rtol=1e-6)
    # The profiles themselves differ, by exactly the log shift.
    assert np.allclose(
        at_30.frozen_phi.knots - at_45.frozen_phi.knots,
        np.log(45.0 / 30.0),
        atol=1e-6,
    )


def test_the_default_scale_is_45_so_a_caller_cannot_inherit_30_by_omission():
    compounds, trajectories, _ = _case()
    explicit = fit_case_scalars(compounds, trajectories, e_ref=45.0)
    default = fit_case_scalars(compounds, trajectories)
    assert np.allclose(default.g, explicit.g)


def test_the_estimator_is_the_a1_compatible_procedure_not_the_adapter():
    """Regression 5: the wrong estimator machinery substituted.

    ``protocol.estimate_one`` is excluded by name in section 4.2: it evaluates
    no ``Phi`` curve at all, only a per-energy mean residual.  Its answer and
    this module's must not coincide.
    """
    import muru.paper_benchmark.rc5_estimate as module

    text = open(module.__file__, encoding="utf-8").read()
    assert "estimate_one" not in text.split('"""', 2)[2]

    compounds, trajectories, _ = _case()
    scalars = fit_case_scalars(compounds, trajectories)

    from muru.paper_benchmark.protocol import estimate_one, fit_training_scalar

    training_rows = trajectories.merge(
        compounds[["compound_id", "split"]], on="compound_id"
    )
    frozen = fit_training_scalar(training_rows[training_rows.split == "train"])
    one = compounds.compound_id.iloc[0]
    adapter = estimate_one(
        frozen, training_rows[training_rows.compound_id == one]
    )
    assert not np.isclose(np.log(scalars.g[0]), adapter.log_g, atol=1e-6)


def test_every_compound_gets_a_g_including_f04_style_missingness():
    compounds, trajectories, truth = _case(drop_one_energy=True)
    scalars = fit_case_scalars(compounds, trajectories)
    assert len(scalars.g) == N_COMPOUNDS
    assert np.all(np.isfinite(scalars.g))
    assert np.all(scalars.g > 0)
    # Section 4.3: no row filtering; F04 compounds are not dropped.
    assert len(scalars.compound_ids) == N_COMPOUNDS


def test_g_is_raw_not_log_and_strictly_positive():
    compounds, trajectories, _ = _case()
    scalars = fit_case_scalars(compounds, trajectories)
    assert np.all(scalars.g > 0.0)
    # log g would routinely be negative; raw g never is.
    assert float(np.min(scalars.g)) > 0.0


def test_the_two_stage_fit_is_deterministic():
    compounds, trajectories, _ = _case()
    first = fit_case_scalars(compounds, trajectories)
    second = fit_case_scalars(compounds, trajectories)
    assert np.array_equal(first.g, second.g)
    assert np.array_equal(first.frozen_phi.values, second.frozen_phi.values)


# -----------------------------------------------------------------------
# invalid_fraction
# -----------------------------------------------------------------------

def test_denominator_is_thirty_not_thirty_six():
    """Regression 4: denominator 36 used for a production case."""
    assert N_VALIDATION_COMPOUNDS == 30
    good = np.ones(30)
    assert invalid_fraction(good) == 0.0
    with pytest.raises(ValueError, match="expects 30 validation predictions"):
        invalid_fraction(np.ones(36))


def test_the_predicate_is_finite_mask_including_the_overflow_bound():
    values = np.ones(30)
    values[0] = np.nan
    assert invalid_fraction(values) == pytest.approx(1 / 30)
    values = np.ones(30)
    values[0] = np.inf
    assert invalid_fraction(values) == pytest.approx(1 / 30)
    values = np.ones(30)
    values[0] = 1e13  # finite, but beyond finite_mask's 1e12 overflow bound
    assert invalid_fraction(values) == pytest.approx(1 / 30)


def test_the_gate_tolerates_zero_invalid_rows_in_effect():
    assert invalid_fraction_passes(0.0) is True
    # 1/30 = 0.0333 > 0.005, so a single invalid row already fails.
    assert invalid_fraction_passes(1 / 30) is False
    assert invalid_fraction_passes(1 / 36) is False
