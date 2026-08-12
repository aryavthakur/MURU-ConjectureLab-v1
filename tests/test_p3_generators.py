"""Synthetic generators: determinism, versioning, and the properties each
family is supposed to have.

A generator that does not have the property it was built for would invalidate
the gate that rests on it, so each family's defining property is asserted
directly rather than assumed from the code.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.synth import generators as G  # noqa: E402
from muru.synth import plan, truth  # noqa: E402


@pytest.fixture(scope="module")
def cov():
    if not (ROOT / "artifacts" / "p2_compounds.parquet").exists():
        pytest.skip("Phase 2 artifacts not generated in this checkout")
    return G.load_dev_covariates()


# --- reproducibility --------------------------------------------------------
def test_same_seed_and_version_reproduce_the_same_world(cov):
    a = G.build_world("G1B", 2, "moderate", cov=cov)
    b = G.build_world("G1B", 2, "moderate", cov=cov)
    assert a.output_sha256 == b.output_sha256
    assert a.seed == b.seed


def test_different_replicates_are_different_worlds(cov):
    a = G.build_world("G1B", 2, "moderate", cov=cov)
    b = G.build_world("G1B", 3, "moderate", cov=cov)
    assert a.output_sha256 != b.output_sha256


def test_noise_regime_changes_the_world(cov):
    a = G.build_world("G1B", 2, "low", cov=cov)
    b = G.build_world("G1B", 2, "adverse", cov=cov)
    assert a.output_sha256 != b.output_sha256
    assert a.long.mu.std() < b.long.mu.std()


def test_world_seed_depends_on_generator_version():
    s = G.world_seed("G1B", 0, "moderate")
    assert s == G.world_seed("G1B", 0, "moderate")
    assert s != G.world_seed("G1B", 0, "low")


def test_manifest_records_everything_needed_to_regenerate(cov):
    m = G.build_world("G1B", 1, "moderate", cov=cov).manifest()
    for k in ("world_id", "family", "replicate", "noise_regime", "seed",
              "generator_version", "truth_version", "covariate_source",
              "planted_expr", "output_sha256", "params"):
        assert k in m, f"manifest is missing {k}"


# --- shared invariants ------------------------------------------------------
@pytest.mark.parametrize("fam", ["G1", "G1B", "G2", "G3", "G4", "G4M", "G5", "GRT"])
def test_mu_stays_in_the_pipeline_bounds(cov, fam):
    w = G.build_world(fam, 0, "moderate", cov=cov)
    assert w.long.mu.min() > 0.0 and w.long.mu.max() <= 1.0


@pytest.mark.parametrize("fam", ["G1B", "G3", "G4"])
def test_energy_coverage_matches_the_measured_rate(cov, fam):
    w = G.build_world(fam, 0, "moderate", cov=cov)
    n = w.long.groupby("group_key").ce_numeric.nunique()
    assert n.min() >= G.MIN_ENERGIES_PER_COMPOUND
    assert 0.97 <= len(w.long) / (len(cov) * 6) <= 1.0


def test_confirmation_compounds_never_enter_a_world(cov):
    keys = G.sealed_keys()
    assert not (set(cov.inchikey_first_block) & keys)
    assert len(cov) == 439


# --- family-defining properties --------------------------------------------
def test_G4_offsets_are_independent_of_every_descriptor(cov):
    """The pure null must contain no descriptor signal at all — this is the
    world K6 is computed on."""
    for r in range(3):
        w = G.build_world("G4", r, "moderate", cov=cov)
        assert w.params["max_abs_corr_offset_descriptor"] < 0.15


def test_G4_shows_no_mass_association(cov):
    w = G.build_world("G4", 0, "moderate", cov=cov)
    L = w.long.merge(w.cov[["group_key", "precursor_mz"]], on="group_key")
    rho = L.groupby("ce_numeric").apply(
        lambda g: g.mu.corr(g.precursor_mz, method="spearman"), include_groups=False)
    assert rho.abs().max() < 0.15


def test_G3_is_carried_by_mass(cov):
    w = G.build_world("G3", 0, "moderate", cov=cov)
    L = w.long.merge(w.cov[["group_key", "precursor_mz"]], on="group_key")
    rho = L.groupby("ce_numeric").apply(
        lambda g: g.mu.corr(g.precursor_mz, method="spearman"), include_groups=False)
    assert rho.abs().min() > 0.5


def test_G5_driver_is_latent_and_only_proxied_by_observables(cov):
    w = G.build_world("G5", 0, "moderate", cov=cov)
    assert w.params["latent_max_abs_corr_observed"] < 0.85, (
        "if the latent equalled an observed descriptor the world would not be "
        "confounded, it would be observed")


def test_G2_plants_a_varying_shape_so_no_single_collapse_exists(cov):
    w = G.build_world("G2", 0, "moderate", cov=cov)
    lo, hi = w.params["p_i_range"]
    assert hi - lo > 0.3
    assert truth.planted("G2").collapses is False


def test_GA_uses_no_real_chemistry():
    w = G.build_world("GA", 0, "moderate")
    assert w.covariate_source == "fully_synthetic"
    assert w.cov.group_key.str.startswith("GA").all()


# --- the measurement-coupling adversary ------------------------------------
def test_purely_fractional_fragmentation_carries_no_mass_association(cov):
    """The analytic claim behind the Phase 2 coupling audit, asserted."""
    w = G.build_world("GC", 0, "low", cov=cov, cutoff_da=None)
    assert max(abs(r) for r in w.params["rho_mu_mass_by_energy"]) < 0.15


@pytest.mark.parametrize("cut", [30.0, 50.0, 80.0])
def test_an_absolute_cutoff_manufactures_a_negative_mass_association(cov, cut):
    """Same fractional law, one absolute instrument limit, no chemistry."""
    w = G.build_world("GC", 0, "moderate", cov=cov, cutoff_da=cut)
    rho = w.params["rho_mu_mass_by_energy"]
    assert all(r < 0 for r in rho)
    assert abs(rho[-1]) > 0.3


def test_coupling_cutoffs_are_stipulated_not_fitted():
    assert truth.planted("GC").extra["cutoffs_da"] == (30.0, 50.0, 80.0)


# --- null constructions -----------------------------------------------------
@pytest.mark.parametrize("con", G.NULL_CONSTRUCTIONS)
def test_each_null_construction_builds_and_is_reproducible(cov, con):
    a = G.build_null_world(0, con, cov)
    b = G.build_null_world(0, con, cov)
    assert a.output_sha256 == b.output_sha256
    assert a.planted_support == ()
    assert a.long.mu.between(0, 1).all()


def test_an_unknown_null_construction_is_an_error(cov):
    with pytest.raises(ValueError):
        G.build_null_world(0, "not_a_construction", cov)


# --- the frozen plan --------------------------------------------------------
def test_the_plan_arithmetic_is_a_product_not_a_sum():
    c = plan.run_counts()
    for block, n in c["worlds_by_block"].items():
        assert c["pysr_runs_by_block"][block] == n * plan.N_SEEDS
    assert c["pysr_runs_total"] == sum(
        n * plan.N_SEEDS for n in c["worlds_by_block"].values())


def test_the_plan_meets_the_master_plan_minimums():
    c = plan.run_counts()
    assert plan.N_SEEDS == 30, "master plan 13.4 requires at least 30 seeds"
    assert c["worlds_by_block"]["G4"] == 100, "K6 requires 100 G4 replicates"
    assert plan.N_NULL_CAL >= 40


def test_calibration_worlds_and_g4_worlds_are_disjoint():
    ids = {s.block: {w.world_id for w in plan.all_worlds() if w.block == s.block}
           for s in plan.all_worlds()}
    assert not (ids["NCAL"] & ids["G4"]), (
        "the threshold must not be fitted to the worlds that measure the "
        "false-positive rate")


def test_every_world_id_is_unique():
    ids = [s.world_id for s in plan.all_worlds()]
    assert len(ids) == len(set(ids))
