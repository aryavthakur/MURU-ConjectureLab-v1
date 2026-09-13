"""v2 data contracts (review T-1): population and partition hashes, archive-copy collapse, endpoint with
precursor included, undefined fragment depth, energy-map direction, kernel key alignment, cache invalidation."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from muru.io.wur_provenance import canonical_key_hash
from muru.wur_bridge import interpolate_ladder
from muru.wur_v2 import folds as FO, spectra as SP

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "artifacts/wur_v2/data"
POP_SHA = "81eef787d7c9687b79060f3af7e95cfe2459c74eeb221d2d86264eacec8c0abd"


def test_population_hash_and_partition_hashes():
    cov = pd.read_csv(D / "compounds.csv")
    assert canonical_key_hash(cov.group_key) == POP_SHA
    f = json.loads((ROOT / "artifacts/wur_v2/folds.json").read_text())
    assert f["population_keys_sha256"] == POP_SHA
    for name, p in f["partitions"].items():
        a = pd.Series(p["assignment"])
        assert FO.assignment_hash(a) == p["assignment_sha256"]
        col = {"STRICT": "strict_cluster", "RANDOM": None}.get(name, "scaffold_group")
        if col:
            FO.check_disjoint(cov, a, col)


def test_endpoint_includes_precursor_and_depth_is_nan_when_precursor_only():
    q = SP.spectrum_quantities(np.array([100.0, 300.0]), np.array([1.0, 3.0]), 300.0)
    assert q["mu"] == pytest.approx((100 * 1 + 300 * 3) / 4 / 300)            # precursor counted
    assert q["survival_yield"] == pytest.approx(0.75) and q["fragment_depth"] == pytest.approx(100 / 300)
    only = SP.spectrum_quantities(np.array([300.0]), np.array([5.0]), 300.0)
    assert only["mu"] == pytest.approx(1.0) and np.isnan(only["fragment_depth"])


def test_archive_copies_collapse_but_distinct_acquisitions_do_not():
    base = dict(connectivity_key="K", ce_numeric=30.0, precursor_mass=300.0, scan_lo=40.0, adduct="[M+H]+",
                survival_yield=0.5, fragment_depth=0.4, precursor_mass_ratio=1.0, defect="")
    rows = [dict(base, spectrum_id=1, peak_hash="h1", scan_number=10, creation_date=None, mu=0.5),
            dict(base, spectrum_id=1, peak_hash="h1", scan_number=10, creation_date=None, mu=0.5),   # archive copy
            dict(base, spectrum_id=2, peak_hash="h2", scan_number=11, creation_date=None, mu=0.7)]   # distinct
    cells = SP.aggregate_cells(pd.DataFrame(rows))
    assert int(cells.n_acquisitions.iloc[0]) == 2 and cells.mu.iloc[0] == pytest.approx(0.6)
    assert int(cells.n_accepted_rows.iloc[0]) == 3


def test_energy_map_direction_wur_read_at_T_of_lcsb_energy():
    g = json.loads((ROOT / "artifacts/wur_bridge_gate.json").read_text())["alignment"]
    a, b = g["a"], g["b"]
    cells = pd.read_csv(D / "wur_pos_cells.csv")
    aligned = pd.read_csv(D / "wur_aligned_all.csv")
    key = sorted(cells.connectivity_key.unique())[0]
    lad = cells[cells.connectivity_key == key].sort_values("ce_numeric")
    for e in (30.0, 60.0, 90.0):
        want = float(interpolate_ladder(lad.ce_numeric.to_numpy(), lad.mu.to_numpy(), np.array([a + b * e]))[0])
        got = float(aligned[(aligned.group_key == key) & (aligned.ce_numeric == e)].mu.iloc[0])
        assert got == pytest.approx(want, abs=1e-12)
        wrong = float(interpolate_ladder(lad.ce_numeric.to_numpy(), lad.mu.to_numpy(), np.array([(e - a) / b]))[0])
        assert abs(wrong - want) > 1e-6 or e == 90.0


def test_kernel_block_refuses_unknown_key():
    from muru.wur_v2 import engine as EN, models as MO
    d = EN.Data(cov=pd.DataFrame(index=["A", "B"]), Y=pd.DataFrame(), long=pd.DataFrame())
    d.kernels["K"] = (pd.Index(["A", "B"]), np.eye(2))
    assert MO.kernel_block(d, "K", ["A"], ["B"]).shape == (1, 1)
    with pytest.raises(KeyError):
        MO.kernel_block(d, "K", ["Z"], ["A"])


def test_cache_is_invalidated_when_inputs_change(tmp_path, monkeypatch):
    from muru.wur_v2 import engine as EN, models as MO, runner as RU
    import test_v2_engine_nesting as T
    d = T.synthetic(n=80, groups=20)
    d.cov["compound_group"] = d.cov.index
    cov = d.cov.reset_index()
    a = FO.grouped(cov, "scaffold_group", 7)
    monkeypatch.setattr(RU, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(RU, "DATA", tmp_path / "data")
    monkeypatch.setattr(RU, "folds", lambda: {"partitions": {"PRIMARY": {"assignment": a.to_dict(), "assignment_sha256": "x" * 64}}})
    m = MO.RidgeModel("X", model_id="R")
    EN._COLLAPSE_CACHE.clear()
    RU.run(m, d, "PRIMARY")
    d2 = T.synthetic(n=80, groups=20)
    d2.cov["compound_group"] = d2.cov.index
    d2.Y = d2.Y * 0.5
    d2.long = d2.long.assign(mu=d2.long.mu * 0.5)
    EN._COLLAPSE_CACHE.clear()
    with pytest.raises(RU.StaleCacheError):
        RU.run(m, d2, "PRIMARY")
