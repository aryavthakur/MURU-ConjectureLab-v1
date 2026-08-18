"""Generators, null-calibration arithmetic, checkpointing and phase boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from muru.discovery.checkpoint import Store
from muru.objval import truth2
from muru.objval.calibration import threshold_table
from muru.objval.generators2 import (GENERATOR2_VERSION, build_null_world2,
                                     build_world2, NULL_CONSTRUCTIONS2)
from muru.objval.plan2 import all_worlds2, run_counts2, seed_list2
from muru.synth.generators import FEATURES, load_dev_covariates

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


@pytest.fixture(scope="module")
def cov():
    return load_dev_covariates()


# --- generators --------------------------------------------------------------
def test_a_world_rebuilds_bit_identically(cov):
    a = build_world2("G1B", 0, "moderate", cov=cov)
    b = build_world2("G1B", 0, "moderate", cov=cov)
    assert a.output_sha256 == b.output_sha256


def test_replicates_and_regimes_produce_different_worlds(cov):
    h = {build_world2("G1B", i, r, cov=cov).output_sha256
         for i in range(3) for r in ("low", "moderate", "adverse")}
    assert len(h) == 9


def test_drawn_parameters_stay_inside_the_preregistered_ranges(cov):
    lo, hi = truth2.PHI_RANGES["p"]
    slo, shi = truth2.STRUCT_COEF_RANGE
    for i in range(6):
        w = build_world2("G1B", i, "moderate", cov=cov)
        p = w.truth["params"]
        assert lo <= p["phi_p"] <= hi
        assert slo <= p["struct_coef"] <= shi
        assert p["carrier"] in truth2.NON_MASS_CARRIERS


def test_the_non_mass_carrier_rotates_across_replicates(cov):
    carriers = {build_world2("G1B", i, "moderate", cov=cov).truth["params"]["carrier"]
                for i in range(3)}
    assert carriers == set(truth2.NON_MASS_CARRIERS)


def test_constants_are_not_the_phase3_literals(cov):
    """Phase 3 froze c1 = 1.7017 and the Phi exponent 1.4874."""
    for i in range(6):
        p = build_world2("G1B", i, "moderate", cov=cov).truth["params"]
        assert abs(p["g_scale"] - 1.7017) > 1e-6
        assert abs(p["phi_p"] - 1.4874) > 1e-6


def test_g1c_plants_a_law_the_frozen_grammar_cannot_represent(cov):
    w = build_world2("G1C", 0, "moderate", cov=cov)
    assert w.truth["exactly_representable"] is False
    assert "exp(" in w.truth["planted_expr"]


def test_the_pure_null_contains_no_descriptor_signal(cov):
    for i in range(5):
        w = build_world2("G4", i, "moderate", cov=cov)
        assert w.truth["diagnostics"]["max_abs_corr_offset_descriptor"] < 0.25
        assert w.truth["planted_support"] == []


def test_the_coupling_adversary_manufactures_a_mass_association_with_no_chemistry(cov):
    w = build_world2("GC", 0, "moderate", cov=cov, cutoff_da=80.0)
    rho = w.truth["diagnostics"]["rho_mu_mass_by_energy"]
    assert all(r < 0 for r in rho[1:]), "a negative mu-mass association should appear"
    assert w.truth["planted_support"] == []


def test_g1a_is_independent_of_real_chemistry():
    w = build_world2("G1A", 0, "moderate")
    assert w.covariate_source == "fully_synthetic"
    assert not set(w.cov.group_key) & set(load_dev_covariates().group_key)


def test_null_constructions_destroy_the_descriptor_response_link(cov):
    for c in NULL_CONSTRUCTIONS2:
        w = build_null_world2(0, c, cov)
        assert w.truth["planted_support"] == []
        assert w.truth["params"]["construction"] == c


def test_no_sealed_confirmation_compound_reaches_a_world(cov):
    seal = json.loads((ART / "confirmation_set_sealed.json").read_text())
    keys = set(seal["connectivity_keys"])
    w = build_world2("G1B", 0, "moderate", cov=cov)
    assert not (set(w.cov.inchikey_first_block) & keys)


def test_the_confirmation_seal_hash_is_unchanged():
    h = hashlib.sha256((ART / "confirmation_set_sealed.json").read_bytes()).hexdigest()
    assert h == "d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07"


def test_no_observed_mu_enters_a_synthetic_response(cov):
    """The generator reads covariates only; the response is planted."""
    w = build_world2("G1B", 0, "moderate", cov=cov)
    assert set(w.long.columns) == {"group_key", "ce_numeric", "mu"}
    traj = ART / "trajectories.parquet"
    if not traj.exists():
        pytest.skip("real trajectories not present in this checkout")
    import pandas as pd
    real = pd.read_parquet(traj)
    if "mu" not in real.columns:
        pytest.skip("no mu column")
    assert not np.isclose(np.sort(w.long.mu.to_numpy())[:50],
                          np.sort(real.mu.dropna().to_numpy())[:50]).all()


# --- plan arithmetic ---------------------------------------------------------
def test_run_counts_are_products_of_the_actual_world_list():
    c = run_counts2()
    assert c["n_worlds"] == len(all_worlds2())
    assert c["pysr_runs_total"] == sum(c["pysr_runs_by_block"].values())
    for block, n in c["worlds_by_block"].items():
        assert c["pysr_runs_by_block"][block] == n * c["n_seeds_per_world"]


def test_the_master_plan_mandated_counts_are_present():
    c = run_counts2()
    assert c["worlds_by_block"]["G4"] == 100      # master plan 18.3
    assert c["n_seeds_per_world"] == 30           # master plan 13.4 minimum


def test_null_calibration_is_larger_than_phase3_s():
    from muru.synth.plan import N_NULL_CAL as P3
    assert run_counts2()["worlds_by_block"]["NCAL"] > P3


# --- null calibration arithmetic --------------------------------------------
def _curves(n=100, c=21, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.normal(0.0, 0.15, (n, 1))
    return np.maximum.accumulate(base + np.linspace(0, 0.4, c)[None, :], axis=1)


def test_threshold_is_the_95th_percentile_across_worlds():
    M = _curves()
    t = threshold_table(M, n_boot=200)
    assert t["threshold"][10] == pytest.approx(
        float(np.maximum.accumulate(np.quantile(M, 0.95, axis=0))[10]), abs=1e-9)


def test_thresholds_are_non_decreasing_in_complexity():
    t = threshold_table(_curves(), n_boot=200)
    assert all(b >= a - 1e-12 for a, b in zip(t["threshold"], t["threshold"][1:]))


def test_the_threshold_sits_far_above_the_null_median():
    t = threshold_table(_curves(), n_boot=200)
    assert t["threshold"][20] > t["median"][20]


def test_the_bootstrap_interval_brackets_the_point_estimate():
    t = threshold_table(_curves(), n_boot=500)
    for lo, x, hi in zip(t["threshold_ci_lo"], t["threshold"], t["threshold_ci_hi"]):
        assert lo <= x + 1e-9 and x <= hi + 1e-9


def test_more_calibration_worlds_narrow_the_quantile_s_own_interval():
    w40 = np.mean(threshold_table(_curves(40, seed=1), n_boot=800)["interval_width"])
    w200 = np.mean(threshold_table(_curves(200, seed=1), n_boot=800)["interval_width"])
    assert w200 < w40, "this is the reason NCAL was raised from 40 to 100"


def test_non_finite_entries_are_floored_not_dropped():
    M = _curves(20)
    M[0, :] = np.nan
    t = threshold_table(M, n_boot=200)
    assert t["n_calibration_worlds"] == 20


def test_calibration_refuses_a_degenerate_sample():
    with pytest.raises(ValueError):
        threshold_table(_curves(1), n_boot=10)


# --- checkpointing -----------------------------------------------------------
def test_a_completed_unit_is_never_recomputed(tmp_path):
    st = Store(tmp_path)
    st.write("G1B", "OV|G1B|r000|moderate", 1700000000, {"seed": 1700000000})
    assert st.pending("G1B", "OV|G1B|r000|moderate",
                      [1700000000, 1700000001]) == [1700000001]


def test_resume_advances_to_the_next_incomplete_unit(tmp_path):
    st = Store(tmp_path)
    seeds = seed_list2("OV|G1B|r000|moderate")
    for s in seeds[:7]:
        st.write("G1B", "OV|G1B|r000|moderate", s, {"seed": s})
    assert st.pending("G1B", "OV|G1B|r000|moderate", seeds) == seeds[7:]


def test_a_truncated_file_counts_as_incomplete(tmp_path):
    st = Store(tmp_path)
    p = st.write("G1B", "OV|G1B|r000|moderate", 1700000000, {"seed": 1})
    p.write_text('{"seed": 1')
    assert not st.done("G1B", "OV|G1B|r000|moderate", 1700000000)


def test_aggregation_is_invariant_to_completion_order(tmp_path):
    a, b = Store(tmp_path / "a"), Store(tmp_path / "b")
    seeds = seed_list2("OV|G1B|r001|moderate")[:5]
    for s in seeds:
        a.write("G1B", "w", s, {"seed": s})
    for s in reversed(seeds):
        b.write("G1B", "w", s, {"seed": s})
    assert a.read_world("G1B", "w") == b.read_world("G1B", "w")


# --- phase boundary ----------------------------------------------------------
def test_phase3_verdict_is_unchanged_and_phase4_is_not_authorized():
    from muru.discovery.phase_boundary import phase3_verdict, phase4_authorized
    assert phase3_verdict() == "STOP BEFORE PHASE 4"
    assert not phase4_authorized()


def test_this_study_creates_no_new_numbered_phase():
    names = {p.name for p in ROOT.glob("PHASE*.md")}
    assert not any(n.startswith("PHASE6") or "3B" in n.upper() for n in names)


def test_completed_phase3_artifacts_are_not_modified_by_this_study():
    """Every objective-validation script writes only `ov_*` artifacts."""
    for p in sorted((ROOT / "scripts").glob("ov_*.py")):
        text = p.read_text()
        for forbidden in ("p3_decision", "p3_null_calibration", "p3_candidates",
                          "phase4_frozen_protocol"):
            assert f'"{forbidden}' not in text and f"'{forbidden}" not in text


def test_no_objective_validation_script_touches_the_real_response():
    for p in sorted((ROOT / "scripts").glob("ov_*.py")):
        text = p.read_text()
        assert "trajectories.parquet" not in text
        assert "p2_predictions" not in text


def test_generator_version_is_namespaced_for_this_study():
    assert GENERATOR2_VERSION.startswith("ov-")
    assert truth2.TRUTH2_VERSION.startswith("ov-")


def test_every_feature_is_supplied_to_the_search(cov):
    w = build_world2("G1B", 0, "moderate", cov=cov)
    assert set(FEATURES) <= set(w.cov.columns)


def test_g1c_worlds_reproduce_their_frozen_hash_after_the_centering_fix(cov):
    """D2 must not have moved a single generated value."""
    p = ART / "ov_worlds.json"
    if not p.exists():
        pytest.skip("fresh world manifest not present")
    man = {w["world_id"]: w for w in json.loads(p.read_text())["worlds"]}
    for i in range(10):
        w = build_world2("G1C", i, "moderate", cov=cov)
        assert w.output_sha256 == man[w.world_id]["output_sha256"], w.world_id


def test_every_frozen_world_hash_is_still_reproducible(cov):
    """Spot-check across families that nothing in the study moved the data."""
    p = ART / "ov_worlds.json"
    if not p.exists():
        pytest.skip("fresh world manifest not present")
    man = {w["world_id"]: w for w in json.loads(p.read_text())["worlds"]}
    for fam, n in (("G1B", 4), ("G3", 3), ("G4", 3), ("G4M", 2), ("G5", 2)):
        for i in range(n):
            w = build_world2(fam, i, "moderate", cov=cov)
            assert w.output_sha256 == man[w.world_id]["output_sha256"], w.world_id
