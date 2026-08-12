"""The falsification harness.

Master plan, Phase 3 Tests: "Harness must reject a deliberately planted artifact
expression." These tests build small worlds with known answers and require the
ladder to behave: pass a genuine relationship, reject a manufactured one, and
never count a non-applicable rung as a pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery import falsify, grammar  # noqa: E402
from muru.discovery.protocol import WorldData, group_split  # noqa: E402

V = ["precursor_mz", "total_atom_count", "rotatable_bonds", "ring_count",
     "aromatic_ring_count", "rdbe", "tpsa", "heteroatom_fraction",
     "n_N", "n_O", "n_S", "n_halogen"]
ENERGIES = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def make_world(n=300, structural=True, seed=0) -> WorldData:
    """A small collapse world: g depends on mass (and optionally on structure)."""
    rng = np.random.default_rng(seed)
    X = rng.uniform(0.3, 1.8, size=(n, len(V)))
    g = 1.7 * np.sqrt(X[:, 0])
    if structural:
        g = g * (1 + 0.35 * X[:, 7])
    keys = np.array([f"C{i:04d}" for i in range(n)])
    groups = np.array([f"S{i % 50:03d}" for i in range(n)])

    u = (np.array(ENERGIES) / 30.0)[None, :] / g[:, None]
    mu = np.clip(0.2414 + 0.7586 / (1 + u ** 1.4874)
                 + rng.normal(0, 0.02, (n, len(ENERGIES))), 1e-3, 1.0)
    long = pd.DataFrame({
        "group_key": np.repeat(keys, len(ENERGIES)),
        "ce_numeric": np.tile(ENERGIES, n),
        "mu": mu.ravel()})
    cov = pd.DataFrame(X, columns=V)
    cov.insert(0, "group_key", keys)
    cov["scaffold_group"] = groups
    cov["cluster_group"] = groups
    cov["mix"] = np.arange(n) % 3

    from muru.discovery.estimate import fit_collapse
    fit = fit_collapse(long)
    cov = cov.set_index("group_key").loc[fit.compounds].reset_index()
    Xo = cov[V].to_numpy(float)
    return WorldData("W", list(V), Xo, fit.g_hat.copy(), fit.weights.copy(),
                     cov.scaffold_group.to_numpy(),
                     group_split(cov.scaffold_group.to_numpy(), "W"),
                     fit, long, cov)


THR = np.full(21, 0.25)


@pytest.fixture(scope="module")
def world():
    return make_world()


def run(wd, expr_str):
    e = grammar.parse(expr_str, V)
    return falsify.run_harness(wd, e, grammar.complexity(e),
                               grammar.variable_support(e, V), THR,
                               {"fraction": 1.0})


# --- the genuine relationship should survive ---------------------------------
def test_the_true_law_survives_the_ladder(world):
    h = run(world, "sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)")
    assert h["passed"], f"the planted law failed {h['failed_rungs']}"


def test_the_primary_gate_is_the_scaffold_holdout(world):
    h = run(world, "sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)")
    assert "PRIMARY" in h["rungs"]["F5"]["name"]
    assert h["rungs"]["F5"]["r2"] > h["rungs"]["F5"]["threshold"]


# --- planted artifacts must be rejected --------------------------------------
def test_an_unrelated_descriptor_expression_is_rejected(world):
    """A candidate built from descriptors that carry no signal must not pass."""
    h = run(world, "n_S + n_halogen*2.0")
    assert not h["passed"]
    assert "F5" in h["failed_rungs"] or "F4" in h["failed_rungs"]


def test_a_constant_expression_is_rejected(world):
    h = run(world, "n_S - n_S + 1.0")
    assert not h["passed"]


def test_a_deliberately_planted_noise_interpolant_is_rejected(world):
    """High-complexity junk that cannot generalize off the training scaffolds."""
    h = run(world, "n_S*n_halogen*n_N*n_O + n_S/(n_halogen + 0.001)")
    assert not h["passed"]


# --- F10: the pipeline itself is under test ----------------------------------
def test_negative_controls_destroy_the_true_law(world):
    """If a candidate survives permuted targets, the pipeline is broken."""
    h = run(world, "sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)")
    f10 = h["rungs"]["F10"]
    assert f10["pass"] and f10["fraction"] <= 0.05
    assert f10["median_permuted_r2"] < 0.25


# --- F8: labelling, not rejection --------------------------------------------
def test_f8_identifies_mass_as_the_carrier_in_a_mass_only_world():
    wd = make_world(structural=False, seed=3)
    h = run(wd, "sqrt(precursor_mz)")
    assert h["mass_carried"] is True
    assert h["structural_beyond_mass_supported"] is False


def test_f8_supports_a_structural_claim_when_structure_is_real(world):
    h = run(world, "sqrt(precursor_mz)*(1 + 0.35*heteroatom_fraction)")
    assert h["rungs"]["F8"]["pass"] is True, "F8 labels, it does not reject"
    assert h["rungs"]["F8"]["labelling_only"] is True


# --- rung bookkeeping --------------------------------------------------------
def test_non_applicable_rungs_are_never_counted_as_passes(world):
    h = run(world, "sqrt(precursor_mz)")
    for rung in ("F3", "F11"):
        assert h["rungs"][rung]["pass"] is None
        assert h["rungs"][rung]["not_applicable"] is True
        assert rung not in h["required"]


def test_the_extrapolation_probe_is_never_a_gate(world):
    h = run(world, "sqrt(precursor_mz)")
    assert h["rungs"]["F12"]["supporting_only"] is True
    assert "F12" not in h["required"]


def test_every_required_rung_is_reported(world):
    h = run(world, "sqrt(precursor_mz)")
    assert set(h["required_results"]) == set(falsify.REQUIRED)
    assert h["passed"] == all(h["required_results"].values())


def test_all_twelve_rungs_are_present(world):
    h = run(world, "sqrt(precursor_mz)")
    assert set(h["rungs"]) == {f"F{i}" for i in range(1, 13)}


def test_energy_subsets_are_the_master_plan_subsets(world):
    h = run(world, "sqrt(precursor_mz)")
    assert set(h["rungs"]["F9"]["subsets"]) == {
        "low_{15,30,45}", "high_{45,60,75,90}", "odd_index_{15,45,75}"}
