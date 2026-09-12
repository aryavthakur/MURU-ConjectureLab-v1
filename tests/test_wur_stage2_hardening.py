"""Mutation-detecting tests added after the Stage 2A implementation review."""
import json

import numpy as np
import pandas as pd
import pytest

from muru.discovery import engine, grammar, protocol
from muru.io import wur_spectra as WS
from muru.paper_benchmark.rc5_estimate import fit_case_phi
from muru.wur_bridge import interpolate_ladder
from muru.wur_bridge_constants import LADDER_ENERGIES
from muru.wur_stage2 import adequacy_fraction as AF
from muru.wur_stage2 import run2a, selection as SEL, world as W

A_FROZEN, B_FROZEN = -5.95552603907965, 0.8618030610784555


def _acc(keys):
    return pd.DataFrame({"connectivity_key": keys, "source_library": "x",
                         "source_polarity_file": "POS", "spectrum_id": range(len(keys)),
                         "energy": 15.0, "precursor_mass": 100.0})


# ---------------------------------------------------------------- guard --
def test_guard_is_fail_closed_when_the_seal_artifact_is_missing(monkeypatch, tmp_path):
    import pathlib
    monkeypatch.setattr(WS, "__file__", str(tmp_path / "a" / "b" / "c" / "wur_spectra.py"))
    with pytest.raises(WS.SealedReadError):
        WS.sealed_keys_on_disk()
    assert WS.sealed_keys_on_disk(missing_ok=True) == set()
    with pytest.raises(WS.SealedReadError):
        WS.assert_no_sealed_key(_acc(["A"]))


def test_guard_covers_forbidden_holdout_even_when_sealed_is_allowed():
    with pytest.raises(WS.SealedReadError):
        WS.assert_no_sealed_key(_acc(["A", "H1"]), sealed=set(), forbidden={"H1"})
    with pytest.raises(WS.SealedReadError):
        WS.assert_no_sealed_key(_acc(["A", "H1"]), allow_sealed=True, forbidden={"H1"})
    WS.assert_no_sealed_key(_acc(["A"]), sealed={"S"}, forbidden={"H1"})


def test_real_holdout_keys_are_disjoint_from_real_sealed_keys():
    from muru.wur_stage2.population import load_internal_holdout
    hold = set(load_internal_holdout()["hold"]["connectivity_keys"])
    assert len(hold) == 130 and not (hold & WS.sealed_keys_on_disk())


# ------------------------------------------------------- map direction --
def _wur_mu(keys, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for k in keys:
        base = np.sort(rng.uniform(0.2, 0.95, 6))[::-1]
        for e, m in zip(LADDER_ENERGIES, base):
            rows.append({"connectivity_key": k, "ce_numeric": float(e), "mu": float(m)})
    return pd.DataFrame(rows)


def test_aligned_values_are_the_wur_ladder_read_at_a_plus_b_times_e():
    mu = _wur_mu(["A", "B"], seed=3)
    out = W.aligned_wur_long(mu, A_FROZEN, B_FROZEN)
    for k in ("A", "B"):
        lad = mu[mu.connectivity_key == k].sort_values("ce_numeric")
        for e in W.POOLED_ENERGIES:
            expect = interpolate_ladder(lad.ce_numeric.to_numpy(), lad.mu.to_numpy(),
                                        np.array([A_FROZEN + B_FROZEN * e]))[0]
            got = out[(out.group_key == k) & (out.ce_numeric == e)].mu.iloc[0]
            assert got == pytest.approx(expect, abs=1e-12)
            # and NOT the inverse direction (E - a) / b
            inv = interpolate_ladder(lad.ce_numeric.to_numpy(), lad.mu.to_numpy(),
                                     np.array([(e - A_FROZEN) / B_FROZEN]))[0]
            assert abs(got - inv) > 1e-6 or e == 90.0


# ------------------------------------------------------ world key drop --
def _cov(keys, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"connectivity_key": keys,
                         "scaffold_group": [f"S{i % 7}" for i in range(len(keys))],
                         **{f: rng.uniform(0.5, 2.0, len(keys)) for f in protocol.FEATURES},
                         "source": "WUR"})


def test_build_world_raises_on_unaccounted_key_drop_and_reports_accounted_one():
    keys = [f"K{i:02d}" for i in range(30)]
    long = W.native_long(_wur_mu(keys), "WUR")
    cov = _cov(keys)
    with pytest.raises(ValueError):
        W.build_world("X", long, cov.iloc[:25])
    wd, frame = W.build_world("X", long, cov.iloc[:25], max_dropped=5)
    assert frame.attrs["dropped"]["long_only"] == keys[25:] and len(frame) == 25
    with pytest.raises(ValueError):
        W.build_world("X", long.iloc[:-6], cov)          # cov_only key


def test_pooled_covariates_keep_the_lcsb_row_for_a_shared_key():
    keys = ["A", "B", "C"]
    l = _cov(["B", "D"], seed=1).assign(source="LCSB")
    w = _cov(keys, seed=2)
    out = W.pooled_covariates(l, w, {"A", "B", "C", "D"})
    assert out.set_index("connectivity_key").loc["B", "source"] == "LCSB"
    assert out.set_index("connectivity_key").loc["B", "tpsa"] == l.set_index("connectivity_key").loc["B", "tpsa"]


# ------------------------------------------------------- ladder glue --
def _ladder_world(n=40, seed=0):
    rng = np.random.default_rng(seed)
    keys = [f"K{i:02d}" for i in range(n)]
    cov = _cov(keys, seed)
    rows = []
    for i, k in enumerate(keys):
        g = np.exp(rng.normal(0, 0.3))
        for e in (15, 30, 45, 60, 75, 90):
            rows.append({"group_key": k, "ce_numeric": float(e),
                         "mu": float(0.15 + 0.8 / (1 + ((e / 45) / g) ** 2) + rng.normal(0, 0.01)),
                         "source": "WUR"})
    return W.build_world("L", pd.DataFrame(rows), cov)


def test_ladder_uses_test_compounds_only_and_train_phi():
    wd, frame = _ladder_world()
    rec = run2a.ladder("L", wd, frame)
    n_test = int((frame.split == "test").sum())
    n_train = int((frame.split == "train").sum())
    assert rec["n_train_for_phi"] == n_train
    for d in ("M1", "M2", "M3"):
        ids = [r["compound_id"] for r in rec["records"][d]]
        assert sorted(ids) == sorted(frame.loc[frame.split == "test", "group_key"])
        assert rec["per_detector"][d]["n_test"] == n_test
        assert all(r["observed_energy_count"] == 6 for r in rec["records"][d])


def test_run_case_adequacy_fraction_swapped_energy_and_mu_is_detected():
    wd, frame = _ladder_world(seed=1)
    compounds = pd.DataFrame({"compound_id": frame.group_key, "split": frame.split})
    traj = wd.long.rename(columns={"group_key": "compound_id", "ce_numeric": "energy"})
    phi = fit_case_phi(compounds, traj[["compound_id", "energy", "mu"]])
    res, recs = AF.run_case_adequacy_fraction("L", compounds, traj, phi)
    ok = [r for r in recs["M1"] if r.mae_m0 is not None]
    assert ok and all(r.mae_m0 < 0.2 for r in ok)
    swapped = traj.rename(columns={"energy": "mu", "mu": "energy"})
    res2, recs2 = AF.run_case_adequacy_fraction("L", compounds, swapped, phi)
    assert not any(r.mae_m0 is not None and r.mae_m0 < 0.2 for r in recs2["M1"])


# --------------------------------------------------- selection gate edge --
def _cand(expr_str, wd, seed, train_r2, valid_r2):
    expr = grammar.parse(expr_str, list(wd.variables))
    return engine.Candidate(expr_str=expr_str, expr=expr, complexity=grammar.complexity(expr),
                            support=grammar.variable_support(expr, list(wd.variables)),
                            engine="pysr", seed=seed, train_r2=train_r2, valid_r2=valid_r2,
                            invalid_fraction=0.0, valid=True)


def test_gate_is_inclusive_at_both_thresholds_and_uses_validation_not_train():
    wd, _ = _ladder_world(seed=2)
    seeds = protocol.seed_list(wd.world_id)[:5]
    per_seed = {s: [_cand("tpsa", wd, s, train_r2=0.99, valid_r2=0.595)] for s in seeds[:1]}
    per_seed.update({s: [_cand("n_O", wd, s, train_r2=0.99, valid_r2=0.595)] for s in seeds[1:]})
    cache = SEL.candidate_cache(wd.world_id, wd, per_seed, seeds)
    assert all(m["valid_r2"] == 0.595 and m["train_r2"] == 0.99 for m in cache["members"])
    sel = SEL.select_and_gate(cache)
    assert sel["gate"]["features"]["median_seed_best_r2"] == 0.595
    assert sel["report"] is True                     # >= at t1 exactly
    low = {s: [_cand("tpsa", wd, s, 0.99, 0.5949)] for s in seeds}
    assert SEL.select_and_gate(SEL.candidate_cache(wd.world_id, wd, low, seeds))["report"] is False
    # selection fraction exactly 0.2 = 1 of 5 seeds for the chosen family
    one = {seeds[0]: [_cand("tpsa", wd, seeds[0], 0.9, 0.7)]}
    one.update({s: [_cand("n_O", wd, s, 0.9, 0.6)] for s in seeds[1:]})
    sel2 = SEL.select_and_gate(SEL.candidate_cache(wd.world_id, wd, one, seeds))
    assert sel2["expr"] == "n_O" and sel2["gate"]["features"]["selection_fraction"] == pytest.approx(0.8)


def test_bootstrap_resamples_weights_with_targets_and_reports_finite_count():
    wd, frame = _ladder_world(seed=3)
    lad = run2a.ladder("L", wd, frame)
    sel = {"expr": "tpsa"}
    out = run2a.bootstrap(wd, frame, lad, sel)
    assert out["rep_test_r2_n_finite_resamples"] == run2a.BOOT_N
    assert len(out["rep_test_r2_weighted_ci95"]) == 2
    for d in ("M1", "M2", "M3"):
        assert 0 <= out[d]["win_fraction_ci95"][0] <= out[d]["win_fraction_ci95"][1] <= 1


def test_json_default_handles_numpy_bool():
    assert json.dumps({"x": np.bool_(True)}, default=run2a._json_default) == '{"x": true}'
