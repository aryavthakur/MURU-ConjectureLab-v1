"""The sealed confirmation set must not touch any Phase 2 modelling artifact.

These are acceptance-criterion tests, not unit tests: they assert a property of
the artifacts actually produced by this phase. They skip if the artifacts are
absent so that a clean checkout without generated data still runs the suite.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

ART = Path(__file__).resolve().parents[1] / "artifacts"
SEAL = ART / "confirmation_set_sealed.json"


def _need(p: Path):
    if not p.exists():
        pytest.skip(f"{p.name} not generated in this checkout")
    return p


def sealed_keys() -> set[str]:
    return set(json.loads(_need(SEAL).read_text())["connectivity_keys"])


def test_seal_exists_and_is_20_percent():
    s = json.loads(_need(SEAL).read_text())
    assert 0.18 <= s["frac_compounds"] <= 0.23, (
        f"confirmation set is {100*s['frac_compounds']:.1f}% of the corpus, "
        "outside the pre-registered 20% target band")
    assert s["selection_unit"] == "bemis_murcko_scaffold_group"


def test_seal_hash_matches_the_preregistration():
    prereg = (Path(__file__).resolve().parents[1] / "PREREGISTRATION.md").read_text()
    digest = hashlib.sha256(_need(SEAL).read_bytes()).hexdigest()
    assert digest in prereg, (
        "the sealed confirmation set's SHA-256 does not appear in "
        "PREREGISTRATION.md; the seal has changed since it was frozen")


def test_seal_carries_the_mandatory_disclosure():
    s = json.loads(_need(SEAL).read_text())
    d = s["disclosure"].lower()
    assert "phase 1" in d and "not unseen" in d, (
        "the seal must record that Phase 1 selected the endpoint using the full "
        "corpus, so these compounds are not unseen with respect to all design")


def test_no_confirmation_compound_appears_in_the_development_splits():
    d = pd.read_parquet(_need(ART / "p2_splits.parquet"))
    overlap = set(d.inchikey_first_block) & sealed_keys()
    assert not overlap, f"{len(overlap)} confirmation compounds leaked into splits"


def test_no_confirmation_compound_appears_in_the_descriptors():
    keys = sealed_keys()
    cm = pd.read_parquet(_need(ART / "p2_compounds.parquet"))
    dev_keys = set(cm[~cm.in_confirmation].inchikey_first_block)
    for f in ("p2_tierA.parquet", "p2_tierB.parquet"):
        t = pd.read_parquet(_need(ART / f))
        gk = set(cm.set_index("group_key").loc[
            t.group_key, "inchikey_first_block"])
        assert not (gk & keys), f"confirmation compounds present in {f}"
        assert gk <= dev_keys


def test_no_confirmation_compound_appears_in_any_prediction():
    p = pd.read_parquet(_need(ART / "p2_predictions.parquet"))
    overlap = set(p.inchikey_first_block) & sealed_keys()
    assert not overlap, (
        f"{len(overlap)} confirmation compounds were scored during Phase 2; "
        "the confirmation set must not be evaluated")


def test_development_and_confirmation_partition_the_corpus():
    cm = pd.read_parquet(_need(ART / "p2_compounds.parquet"))
    keys = sealed_keys()
    conf = set(cm[cm.in_confirmation].inchikey_first_block)
    dev = set(cm[~cm.in_confirmation].inchikey_first_block)
    assert conf == keys
    assert not (conf & dev)
    assert len(conf) + len(dev) == len(cm)


def test_confirmation_split_respects_scaffold_groups():
    """A scaffold group must be wholly in or wholly out of the confirmation set."""
    cm = pd.read_parquet(_need(ART / "p2_compounds.parquet"))
    spread = cm.groupby("scaffold_group").in_confirmation.nunique()
    bad = spread[spread > 1]
    assert len(bad) == 0, (
        f"{len(bad)} scaffold groups straddle the confirmation boundary")
