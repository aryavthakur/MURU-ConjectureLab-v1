"""MSnLib fixed-rung identification by run position: the Assisted scan is never a rung."""
import numpy as np
import pandas as pd

from muru.wur_v2 import external_msnlib as L


def _h(rows):
    return pd.DataFrame(rows, columns=["index", "ms_level", "selected_ion_mz", "collision_energy", "spectrum_id",
                                       "scan_window_lower_limit", "scan_window_upper_limit"])


def test_triplets_first20_last60_assisted_excluded_even_at_60():
    h = _h([(0, 1, np.nan, np.nan, "s0", 100, 1000),
            (1, 2, 300.1, 20.0, "a20", 40, 311), (2, 2, 300.1, 60.0, "assisted60", 40, 311), (3, 2, 300.1, 60.0, "f60", 40, 311),
            (4, 2, 400.2, 20.0, "b20", 40, 411), (5, 2, 400.2, 20.0, "assisted20", 40, 411), (6, 2, 400.2, 60.0, "g60", 40, 411),
            (7, 1, np.nan, np.nan, "s7", 100, 1000),
            (8, 2, 500.3, 15.0, "x15", 40, 511), (9, 2, 500.3, 30.0, "x30", 40, 511)])
    r = L.fixed_rung_scans(h).set_index("spectrum_id").rung
    assert r["a20"] == 20.0 and r["f60"] == 60.0 and np.isnan(r["assisted60"])
    assert r["b20"] == 20.0 and r["g60"] == 60.0 and np.isnan(r["assisted20"])
    assert np.isnan(r["x15"]) and np.isnan(r["x30"])


def test_adapter_families():
    assert L.adapter_energy(20.0, "A0", {}) == pytest_approx((20.0 + 5.95552603907965) / 0.8618030610784555)
    assert L.adapter_energy(60.0, "A1", {"k": 1.5}) == 90.0
    assert L.adapter_energy(60.0, "A2", {"a": 5.0, "b": 1.0}) == 65.0


def pytest_approx(x):
    import pytest
    return pytest.approx(x)
