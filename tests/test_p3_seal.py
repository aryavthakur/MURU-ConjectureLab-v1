"""The confirmation seal must hold through the whole of Phase 3.

Phase 3 may read the confirmation identifiers only, and only to exclude them.
No response value of any confirmation compound may be opened by symbolic
search, threshold calibration, candidate selection or falsification tuning.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
SEAL = ART / "confirmation_set_sealed.json"
SEAL_SHA256 = "d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07"


def _need(p: Path) -> Path:
    if not p.exists():
        pytest.skip(f"{p.name} not generated in this checkout")
    return p


def sealed_keys() -> set[str]:
    return set(json.loads(_need(SEAL).read_text())["connectivity_keys"])


def test_seal_hash_is_unchanged_by_phase_3():
    digest = hashlib.sha256(_need(SEAL).read_bytes()).hexdigest()
    assert digest == SEAL_SHA256, (
        "the sealed confirmation set changed during Phase 3; the seal is void")


def test_seal_carries_no_response_values():
    """The artifact holds identifiers, not outcomes. If a response column ever
    appeared here, merely reading the seal would break it."""
    s = json.loads(_need(SEAL).read_text())
    assert set(s) == {"purpose", "constructed_utc", "seed", "selection_unit",
                      "target_fraction", "n_scaffold_groups", "n_compounds",
                      "frac_compounds", "connectivity_keys", "disclosure"}
    assert all(isinstance(k, str) for k in s["connectivity_keys"])


def test_phase3_covariate_matrix_excludes_every_confirmation_compound():
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from muru.synth.generators import load_dev_covariates
    _need(ART / "p2_compounds.parquet")
    cov = load_dev_covariates()
    assert not (set(cov.inchikey_first_block) & sealed_keys())
    assert len(cov) == 439, "Phase 3 must build on the 439 development compounds"


def test_no_phase3_artifact_names_a_sealed_compound():
    keys = sealed_keys()
    hits = []
    for p in sorted(ART.glob("p3_*.json")):
        text = p.read_text()
        hits += [(p.name, k) for k in keys if k in text]
    assert not hits, f"sealed identifiers appear in Phase 3 artifacts: {hits[:5]}"


def test_no_checkpoint_names_a_sealed_compound():
    ck = ART / "p3_ckpt"
    if not ck.exists():
        pytest.skip("no checkpoint store in this checkout")
    keys = sealed_keys()
    for p in list(ck.rglob("_world.json"))[:200]:
        text = p.read_text()
        assert not any(k in text for k in keys), f"sealed key in {p}"


def test_synthetic_worlds_never_use_an_observed_response():
    """The generated response must come from the planted law, not from mu."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import pandas as pd
    from muru.synth.generators import build_world, load_dev_covariates
    _need(ART / "p2_dev_corpus.parquet")
    cov = load_dev_covariates()
    w = build_world("G1B", 0, "moderate", cov=cov)
    real = pd.read_parquet(ART / "p2_dev_corpus.parquet")
    merged = w.long.merge(real[["group_key", "ce_numeric", "mu"]],
                          on=["group_key", "ce_numeric"], suffixes=("_syn", "_real"))
    assert len(merged) > 1000
    # identical values would mean the observed response leaked into the world
    assert not (merged.mu_syn == merged.mu_real).any()
    assert abs(merged.mu_syn.corr(merged.mu_real)) < 0.9
