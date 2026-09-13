"""External scoring on synthetic outcomes: adapter direction, support accounting, primary decision rule."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from muru.wur_v2 import external_multims2 as E

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(not (ROOT / "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json").exists(), reason="no candidate")


def test_adapter_scales_with_energy_and_inverse_mass():
    assert E.adapter_energy(40.0, 500.0, 1.0) == pytest.approx(40.0)
    assert E.adapter_energy(40.0, 250.0, 1.0) == pytest.approx(80.0)          # lighter ion: higher normalized energy
    assert E.adapter_energy(40.0, 250.0, 1.0, gamma=0.0) == pytest.approx(40.0)


def test_scoring_on_synthetic_truth_prefers_the_model_that_generated_it(monkeypatch):
    models = E.load_models()
    cov = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv").head(60)
    pop = pd.DataFrame({"key": cov.group_key, "smiles": cov.smiles, "mh": cov.precursor_mz, "collection": "NEXUS",
                        "position": "P", "scaffold_group": cov.scaffold_group})
    adapter = {"k": 1.0, "gamma": 1.0}
    Emat = np.vstack([E.adapter_energy(np.array(E.ENERGIES), m, 1.0) for m in pop.mh])
    from muru.wur_v2 import candidate as CA
    truth = CA.predict_mu(models["CANDIDATE"], pop.smiles, pop.mh, Emat)
    rng = np.random.default_rng(0)
    mu = pd.DataFrame([(k, e, truth[i, j] + rng.normal(0, 0.01)) for i, k in enumerate(pop.key) for j, e in enumerate(E.ENERGIES)],
                      columns=["key", "energy", "mu"])
    monkeypatch.setattr(E, "BOOT_B", 500)
    res = E.score_population(mu, pop, adapter, models)
    assert res["n_scored"] + res["n_unsupported"] + res["n_incomplete"] == 60
    d = E.decide(res)
    assert d["P1_ratio"] < 1.0 and d["primary_supported"]
    assert d["limited_transfer_study"]
