import numpy as np
import pandas as pd
import pytest

from muru.discovery import protocol
from muru.wur_stage2 import cv as CV
from muru.wur_stage2 import folds as FO


def _dev(n=150, seed=0):
    rng = np.random.default_rng(seed)
    keys = [f"K{i:03d}" for i in range(n)]
    cov = pd.DataFrame({"group_key": keys, "scaffold_group": [f"S{i % 31}" for i in range(n)],
                        **{f: rng.uniform(0.5, 2.0, n) * protocol.SCALE[f] for f in protocol.FEATURES},
                        "source": ["WUR" if i % 2 else "LCSB" for i in range(n)]})
    rows = []
    for i, k in enumerate(keys):
        g = np.exp(0.6 * (cov.tpsa[i] / protocol.SCALE["tpsa"] - 1.25) + 0.3 * (cov.precursor_mz[i] / 500 - 1.25))
        for e in CV.POOLED_ENERGIES:
            rows.append({"group_key": k, "ce_numeric": float(e),
                         "mu": float(0.15 + 0.8 / (1 + ((e / 30) / g) ** 1.8) + rng.normal(0, 0.02)),
                         "source": cov.source[i]})
    frame = cov[["group_key", "scaffold_group", "source"]].copy()
    return pd.DataFrame(rows), cov, frame


def test_reference_arms_rank_as_expected_on_a_planted_world():
    long, cov, frame = _dev()
    folds = FO.build_folds(frame[["group_key", "scaffold_group"]])
    b0p = CV.b0_predictions(long, cov, frame, folds)
    r0 = CV.run_cv(CV.B0NullProfile, long, cov, frame, folds, b0p, with_loeo=False, repeats=[0])
    r1 = CV.run_cv(CV.B1MassOnly, long, cov, frame, folds, b0p, with_loeo=False, repeats=[0])
    rl = CV.run_cv(CV.LinRidge, long, cov, frame, folds, b0p, with_loeo=True, repeats=[0])
    assert len(r0.folds) == len(r1.folds) == len(rl.folds) == 5
    assert rl.p1_vector().mean() < r1.p1_vector().mean() < r0.p1_vector().mean()
    c = CV.compare(rl, r0)
    assert c["wins"] == 5 and c["mean_rel_improvement"] > 0.1
    assert all("S3_loeo_mae_median" in f for f in rl.folds)
    assert all(0 <= f["S2_descriptor_practical_win"] <= 1 for f in rl.folds)
    pb = CV.paired_bootstrap(rl, r0)
    assert pb["0"]["ci"][1] < 0
    # held-out sets are disjoint from training within a fold, by construction of the folds
    assert set(rl.per_compound) == set(frame.group_key)


def test_b0_metrics_relative_to_itself_are_trivial():
    long, cov, frame = _dev(seed=1)
    folds = FO.build_folds(frame[["group_key", "scaffold_group"]])
    r0 = CV.run_cv(CV.B0NullProfile, long, cov, frame, folds, None, with_loeo=False, repeats=[0])
    assert all(f["S2_descriptor_practical_win"] == 0.0 and f["S4_catastrophic"] == 0.0 for f in r0.folds)


def test_s2a_arm_runs_with_two_seeds_and_records_gate(tmp_path):
    long, cov, frame = _dev(seed=2, n=120)
    folds = FO.build_folds(frame[["group_key", "scaffold_group"]])
    folds["repeats"] = folds["repeats"][:1]
    b0p = CV.b0_predictions(long, cov, frame, folds)
    r = CV.run_cv(lambda: CV.S2AFrozen(tmp_path, n_seeds=2), long, cov, frame, folds, b0p,
                  with_loeo=False, repeats=[0])
    assert len(r.folds) == 5
    assert all("report" in f["diagnostics"] for f in r.folds)
    assert np.isfinite(r.p1_vector()).all()


def test_ledger_is_append_only(tmp_path, monkeypatch):
    monkeypatch.setattr(CV, "LEDGER", tmp_path / "ledger")
    res = CV.CVResult(arm_id="X", folds=[{"P1": 0.1}, {"P1": 0.2}])
    p = CV.ledger_entry("X", res, {"hypothesis": "h"}, {}, "abc", "def")
    assert p.exists()
    with pytest.raises(FileExistsError):
        CV.ledger_entry("X", res, {}, {}, "abc", "def")
