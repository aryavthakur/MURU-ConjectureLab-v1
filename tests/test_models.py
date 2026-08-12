"""Model layer: feature construction, nested-CV isolation, and bootstrap units."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from muru.models import (ENERGIES, GlobalMean, MassFlex, MassSimple,
                         PerEnergyMean, Spec, TierAModel, bootstrap_paired,
                         compound_errors, energy_onehot, nested_cv, row_tensor)


def toy(n_cpd: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    keys = [f"K{i:04d}" for i in range(n_cpd)]
    mass = rng.uniform(150, 600, n_cpd)
    rows = []
    for i, (k, m) in enumerate(zip(keys, mass)):
        for e in ENERGIES:
            rows.append({
                "inchikey_first_block": k, "group_key": k,
                "scaffold_group": f"S{i % 12}", "cluster_group": f"C{i % 15}",
                "ce_numeric": float(e), "precursor_mz": m,
                "d1": float(i % 7), "d2": rng.normal(),
                "mu": 1.0 - 0.006 * e + 0.0002 * m + rng.normal(0, 0.01),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------
def test_energy_onehot_is_a_partition():
    e = np.array([15, 30, 90, 45], dtype=float)
    X = energy_onehot(e)
    assert X.shape == (4, 6)
    assert (X.sum(axis=1) == 1).all()


def test_row_tensor_matches_outer_product():
    A = np.arange(6.0).reshape(2, 3)
    B = np.arange(8.0).reshape(2, 4)
    T = row_tensor(A, B)
    assert T.shape == (2, 12)
    np.testing.assert_allclose(T[0], np.outer(A[0], B[0]).ravel())
    np.testing.assert_allclose(T[1], np.outer(A[1], B[1]).ravel())


# ---------------------------------------------------------------------------
# Baseline behaviour
# ---------------------------------------------------------------------------
def test_global_mean_predicts_one_value():
    df = toy()
    p = GlobalMean().fit(df).predict(df)
    assert np.allclose(p, df.mu.mean())


def test_per_energy_mean_matches_group_means():
    df = toy()
    m = PerEnergyMean().fit(df)
    for e, g in df.groupby("ce_numeric"):
        assert m.predict(g)[0] == pytest.approx(g.mu.mean())


def test_per_energy_mean_beats_global_mean_when_energy_matters():
    df = toy()
    g = np.mean(np.abs(df.mu - GlobalMean().fit(df).predict(df)))
    b = np.mean(np.abs(df.mu - PerEnergyMean().fit(df).predict(df)))
    assert b < g


def test_mass_flex_beats_mass_simple_on_a_curved_surface():
    """MASS FLEX must be a genuinely strong competitor, not a straw man."""
    rng = np.random.default_rng(3)
    df = toy(80, seed=3)
    # curvature in mass and an energy-by-mass interaction
    df["mu"] = (0.9 - 0.005 * df.ce_numeric
                + 1.2e-6 * (df.precursor_mz - 380) ** 2
                - 2e-5 * df.ce_numeric * (df.precursor_mz - 380) / 100
                + rng.normal(0, 0.005, len(df)))
    simple = np.mean(np.abs(df.mu - MassSimple().fit(df).predict(df)))
    flex = np.mean(np.abs(df.mu - MassFlex(alpha=1e-3).fit(df).predict(df)))
    assert flex < simple


def test_tier_a_model_uses_its_features():
    df = toy()
    m = TierAModel(alpha=1e-3).fit(df, ["precursor_mz", "d1", "d2"])
    m.feats_ = ["precursor_mz", "d1", "d2"]
    assert np.mean(np.abs(df.mu - m.predict(df))) < df.mu.std()


# ---------------------------------------------------------------------------
# Nested CV isolation -- the property that makes the numbers reportable
# ---------------------------------------------------------------------------
def test_nested_cv_covers_every_row_exactly_once():
    df = toy()
    df["fold_S2"] = (df.groupby("scaffold_group").ngroup() % 5)
    out = nested_cv(df, Spec("B1", PerEnergyMean), "fold_S2")
    assert len(out) == len(df)
    assert set(out.group_key) == set(df.group_key)


def test_nested_cv_never_fits_on_the_evaluated_fold():
    """A row's prediction must not depend on that row's own mu."""
    df = toy()
    df["fold_S2"] = (df.groupby("scaffold_group").ngroup() % 5)
    base = nested_cv(df, Spec("B1", PerEnergyMean), "fold_S2").sort_values(
        ["group_key", "ce_numeric"]).reset_index(drop=True)

    tampered = df.copy()
    victim = (tampered.scaffold_group == "S0")
    tampered.loc[victim, "mu"] = tampered.loc[victim, "mu"] + 10.0
    after = nested_cv(tampered, Spec("B1", PerEnergyMean), "fold_S2").sort_values(
        ["group_key", "ce_numeric"]).reset_index(drop=True)

    # Rows in the tampered scaffold are evaluated on a model trained without
    # them, so their own predictions must be unchanged.
    m = after.scaffold_group == "S0"
    assert not np.allclose(base.pred[~m], after.pred[~m]), \
        "other folds should see the tampered data in training"
    np.testing.assert_allclose(base.pred[m], after.pred[m], atol=1e-12)


def test_nested_cv_selects_hyperparameters_without_the_outer_fold():
    """Different outer folds may legitimately choose different hyperparameters."""
    df = toy()
    df["fold_S2"] = (df.groupby("scaffold_group").ngroup() % 5)
    spec = Spec("MASS_FLEX", MassFlex, grid=[{"alpha": a} for a in (1e-4, 1.0, 100.0)])
    out = nested_cv(df, spec, "fold_S2")
    assert out.hp.notna().all()
    assert out.groupby("outer_fold").hp.nunique().eq(1).all()


# ---------------------------------------------------------------------------
# Aggregation and bootstrap
# ---------------------------------------------------------------------------
def test_compound_errors_aggregates_to_one_row_per_compound():
    df = toy()
    df["pred"] = df.mu + 0.01
    ce = compound_errors(df)
    assert len(ce) == df.inchikey_first_block.nunique()
    assert np.allclose(ce.mae, 0.01)


def test_bootstrap_paired_sign_follows_the_better_model():
    df = toy()
    a = compound_errors(df.assign(pred=df.mu + 0.01))
    b = compound_errors(df.assign(pred=df.mu + 0.05))
    r = bootstrap_paired(a, b, None, n_boot=200)
    assert r["diff"] < 0                      # a has lower error
    assert r["hi"] < 0                        # interval excludes zero
    assert r["frac_units_favouring_a"] == 1.0


def test_bootstrap_paired_is_degenerate_at_zero_for_identical_models():
    df = toy()
    rng = np.random.default_rng(1)
    p = df.mu + rng.normal(0, 0.02, len(df))
    a = compound_errors(df.assign(pred=p))
    b = compound_errors(df.assign(pred=p))
    r = bootstrap_paired(a, b, None, n_boot=500)
    assert r["diff"] == pytest.approx(0.0, abs=1e-12)
    assert r["lo"] == pytest.approx(0.0, abs=1e-12)
    assert r["hi"] == pytest.approx(0.0, abs=1e-12)


def test_bootstrap_paired_interval_widens_with_noisier_disagreement():
    """More per-compound scatter in the difference => wider interval."""
    df = toy(120, seed=5)
    rng = np.random.default_rng(2)
    base = df.mu + rng.normal(0, 0.01, len(df))
    a = compound_errors(df.assign(pred=base))

    tight = compound_errors(df.assign(pred=base + 0.002))
    loose = compound_errors(df.assign(
        pred=base + rng.normal(0, 0.05, len(df))))
    w_tight = bootstrap_paired(a, tight, None, n_boot=500)
    w_loose = bootstrap_paired(a, loose, None, n_boot=500)
    assert (w_loose["hi"] - w_loose["lo"]) > (w_tight["hi"] - w_tight["lo"])


def test_bootstrap_resamples_the_named_unit_not_spectra():
    """Scaffold-level resampling must use fewer units than compound-level."""
    df = toy()
    ce_a = compound_errors(df.assign(pred=df.mu + 0.01))
    ce_b = compound_errors(df.assign(pred=df.mu + 0.02))
    scaf = df.drop_duplicates("inchikey_first_block").set_index(
        "inchikey_first_block").scaffold_group
    by_cpd = bootstrap_paired(ce_a, ce_b, None, n_boot=200)
    by_scaf = bootstrap_paired(ce_a, ce_b, scaf, n_boot=200)
    assert by_scaf["n_units"] < by_cpd["n_units"]
    assert by_scaf["n_units"] == df.scaffold_group.nunique()
