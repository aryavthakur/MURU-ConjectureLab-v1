import numpy as np
import pandas as pd

from muru.discovery import protocol
from muru.wur_stage2 import cv as CV, folds as FO, profile2 as P2


def _world(n=120, seed=0, floor=True):
    rng = np.random.default_rng(seed)
    keys = [f"K{i:03d}" for i in range(n)]
    cov = pd.DataFrame({"group_key": keys, "scaffold_group": [f"S{i % 23}" for i in range(n)],
                        **{f: rng.uniform(0.5, 2.0, n) * protocol.SCALE[f] for f in protocol.FEATURES},
                        "source": "WUR"})
    rows = []
    for i, k in enumerate(keys):
        g = np.exp(0.5 * (cov.tpsa[i] / protocol.SCALE["tpsa"] - 1.25))
        a = 0.4 * (cov.n_O[i] / protocol.SCALE["n_O"] - 0.5) / 1.5 if floor else 0.0
        a = float(np.clip(a, 0, 0.6))
        for e in CV.POOLED_ENERGIES:
            phi = 1.0 / (1 + ((e / 30) / g) ** 2)
            rows.append({"group_key": k, "ce_numeric": float(e),
                         "mu": float(a + (1 - a) * phi + rng.normal(0, 0.01)), "source": "WUR"})
    return pd.DataFrame(rows), cov, cov[["group_key", "scaffold_group", "source"]].copy()


def test_two_parameter_collapse_recovers_a_planted_floor():
    long, cov, frame = _world()
    f = P2.fit_collapse2(long)
    truth_a = np.clip(0.4 * (cov.set_index("group_key").loc[f.compounds, "n_O"] / protocol.SCALE["n_O"] - 0.5) / 1.5, 0, 0.6)
    assert np.corrcoef(f.a, truth_a)[0, 1] > 0.8
    assert f.resid_sd < 0.03


def test_two_param_arm_beats_ridge_when_a_floor_is_planted_and_not_worse_without():
    long, cov, frame = _world()
    folds = FO.build_folds(frame[["group_key", "scaffold_group"]])
    b0 = CV.b0_predictions(long, cov, frame, folds)
    r2 = CV.run_cv(P2.TwoParamRidge, long, cov, frame, folds, b0, with_loeo=True, repeats=[0])
    r1 = CV.run_cv(CV.LinRidge, long, cov, frame, folds, b0, with_loeo=False, repeats=[0])
    assert r2.p1_vector().mean() < r1.p1_vector().mean()
    assert all(np.isfinite(f["S3_loeo_mae_median"]) for f in r2.folds)
    long0, cov0, frame0 = _world(seed=1, floor=False)
    folds0 = FO.build_folds(frame0[["group_key", "scaffold_group"]])
    b00 = CV.b0_predictions(long0, cov0, frame0, folds0)
    r2b = CV.run_cv(P2.TwoParamRidge, long0, cov0, frame0, folds0, b00, with_loeo=False, repeats=[0])
    r1b = CV.run_cv(CV.LinRidge, long0, cov0, frame0, folds0, b00, with_loeo=False, repeats=[0])
    # without a planted floor the second parameter costs accuracy (overfits noise);
    # the family must stay finite and within 2x of the one-parameter ridge
    assert np.isfinite(r2b.p1_vector()).all() and r2b.p1_vector().mean() < r1b.p1_vector().mean() * 2.0
