import pandas as pd
import pytest

from muru.paper_benchmark.protocol import estimate_one, fit_training_scalar


def _rows(compound_id, split, values):
    return pd.DataFrame({"compound_id": compound_id, "split": split, "energy": [15, 30, 45, 60, 75, 90], "mu": values})


def test_test_compound_b_cannot_change_test_compound_a_estimate():
    train = pd.concat([_rows("T1", "train", [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]), _rows("T2", "train", [0.8, 0.7, 0.6, 0.5, 0.4, 0.3])])
    frozen = fit_training_scalar(train)
    a = _rows("A", "test", [0.85, 0.75, 0.65, 0.55, 0.45, 0.35])
    b = _rows("B", "test", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    before = estimate_one(frozen, a)
    b.loc[:, "mu"] = 0.999
    assert estimate_one(frozen, a) == before


def test_fit_refuses_nontraining_rows():
    with pytest.raises(ValueError, match="training rows"):
        fit_training_scalar(_rows("A", "test", [0.8] * 6))
