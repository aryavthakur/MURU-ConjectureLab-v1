"""Serialized v2 candidate reloads to identical predictions; Morgan counts are deterministic."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from muru.wur_v2 import candidate as CA, representations as R

ROOT = Path(__file__).resolve().parents[2]
CAND = ROOT / "artifacts/wur_v2/candidate"


def test_morgan_counts_deterministic():
    s = pd.Series(["CCN(CC)CC(=O)Nc1c(C)cccc1C", "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "C[C@H](N)C(=O)O"])
    a, b = R.morgan_counts(s).to_numpy(), R.morgan_counts(s).to_numpy()
    assert np.array_equal(a, b) and a.shape == (3, 2048)
    # chirality is ignored by construction
    c = R.morgan_counts(pd.Series(["C[C@@H](N)C(=O)O"])).to_numpy()
    assert np.array_equal(a[2], c[0])


@pytest.mark.skipif(not (CAND / f"{CA.CANDIDATE_ID}.json").exists(), reason="candidate not built")
def test_candidate_hash_and_prediction_shape():
    m = json.loads((CAND / f"{CA.CANDIDATE_ID}.json").read_text())
    man = json.loads((CAND / "candidate_manifest.json").read_text())
    assert CA.sha256_of(m) == man[CA.CANDIDATE_ID]["sha256"]
    mu = CA.predict_mu(m, ["CCN(CC)CC(=O)Nc1c(C)cccc1C"], [235.18], [30.0, 60.0, 90.0])
    assert mu.shape == (1, 3) and np.all(np.diff(mu[0]) <= 1e-12) and np.all((mu >= 0) & (mu <= 1))
    # per-compound energy matrix (native energies through an adapter) is accepted
    mu2 = CA.predict_mu(m, ["CCN(CC)CC(=O)Nc1c(C)cccc1C"] * 2, [235.18, 235.18], np.array([[30.0, 60.0, 90.0], [30.0, 60.0, 90.0]]))
    assert np.allclose(mu2[0], mu[0])
