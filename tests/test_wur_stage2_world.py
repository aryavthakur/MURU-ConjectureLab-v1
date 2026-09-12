import numpy as np
import pandas as pd
import pytest

from muru.discovery.protocol import FEATURES
from muru.wur_bridge_constants import LADDER_ENERGIES
from muru.wur_stage2 import world as W


def _wur_mu(keys, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for k in keys:
        base = np.sort(rng.uniform(0.2, 0.95, 6))[::-1]
        for e, m in zip(LADDER_ENERGIES, base):
            rows.append({"connectivity_key": k, "ce_numeric": float(e), "mu": float(m)})
    return pd.DataFrame(rows)


def test_aligned_wur_long_drops_e15_and_accounts_clamping():
    mu = _wur_mu([f"K{i}" for i in range(5)])
    out = W.aligned_wur_long(mu, -5.95552603907965, 0.8618030610784555)
    assert sorted(out.ce_numeric.unique()) == list(W.POOLED_ENERGIES)
    assert out.group_key.nunique() == 5 and len(out) == 25
    assert (out.source == "WUR").all()
    # a map with an in-ladder T(15) (a=0, b=1) yields the native values at the rungs
    ident = W.aligned_wur_long(mu, 0.0, 1.0)
    nat = mu[mu.ce_numeric.isin(W.POOLED_ENERGIES)].sort_values(["connectivity_key", "ce_numeric"])
    assert np.allclose(ident.sort_values(["group_key", "ce_numeric"]).mu.to_numpy(), nat.mu.to_numpy())


def test_aligned_wur_long_rejects_unexpected_clamping():
    mu = _wur_mu(["A", "B"])
    with pytest.raises(ValueError):
        W.aligned_wur_long(mu, 60.0, 1.0)   # every pooled rung maps past 90


def test_pooled_long_keeps_lcsb_copy_and_forbids_duplicates():
    wur = W.aligned_wur_long(_wur_mu(["A", "B", "C"]), 0.0, 1.0)
    lcsb = W.native_long(_wur_mu(["B", "D"], seed=5), "LCSB")
    out, census = W.pooled_long(lcsb, wur)
    assert census == {"n_lcsb_keys": 2, "n_wur_keys": 3, "n_both_lcsb_kept": 1,
                      "n_pooled_keys": 4}
    b = out[out.group_key == "B"]
    assert (b.source == "LCSB").all() and len(b) == 5
    assert sorted(out.ce_numeric.unique()) == list(W.POOLED_ENERGIES)


def _cov(keys, seed=0):
    rng = np.random.default_rng(seed)
    d = {f: rng.uniform(0.5, 2.0, len(keys)) for f in FEATURES}
    return pd.DataFrame({"connectivity_key": keys,
                         "scaffold_group": [f"S{i % 7}" for i in range(len(keys))],
                         **d, "source": "WUR"})


def test_build_world_splits_by_scaffold_and_asserts_disjoint():
    keys = [f"K{i:02d}" for i in range(40)]
    long = W.native_long(_wur_mu(keys), "WUR")
    cov = _cov(keys)
    wd, frame = W.build_world("B_WUR_NATIVE", long, cov)
    assert wd.world_id == "WUR2A|B_WUR_NATIVE|seed20260911"
    assert set(frame.split) <= {"train", "valid", "test"}
    assert frame.groupby("scaffold_group").split.nunique().max() == 1
    assert len(frame) == 40 and wd.X.shape == (40, 12)
    # keys absent from covariates are dropped from the world, not silently NaN
    wd2, frame2 = W.build_world("B_WUR_NATIVE", long, cov.iloc[:30])
    assert len(frame2) == 30
