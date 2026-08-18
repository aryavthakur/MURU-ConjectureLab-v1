"""Phase 3 must not be able to start Phase 4.

Phase 3 builds and calibrates the discovery engine. Running symbolic regression
against the real `mu` response, or opening the sealed confirmation outcomes, is
reserved for later phases and only if Phase 3 authorizes them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from muru.discovery import phase_boundary as pb  # noqa: E402


def test_the_phase4_entry_point_refuses_to_run_from_phase_3():
    with pytest.raises(pb.PhaseBoundaryError):
        pb.real_data_symbolic_search()


def test_authorization_requires_an_explicit_phase3_verdict(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "ROOT", tmp_path)
    assert pb.phase3_verdict() is None
    assert not pb.phase4_authorized()
    with pytest.raises(pb.PhaseBoundaryError):
        pb.assert_phase4_authorized()


@pytest.mark.parametrize("verdict,allowed", [
    ("GO TO PHASE 4", True),
    ("RESTRICT AND GO TO PHASE 4", True),
    ("STOP BEFORE PHASE 4", False),
    ("INCONCLUSIVE DUE TO BLOCKER", False),
])
def test_only_authorizing_verdicts_open_the_door(monkeypatch, tmp_path,
                                                 verdict, allowed):
    monkeypatch.setattr(pb, "ROOT", tmp_path)
    (tmp_path / "PHASE3_DECISION.md").write_text(
        f"# PHASE3_DECISION.md\n\n# {verdict}\n\nbody\n")
    assert pb.phase3_verdict() == verdict
    assert pb.phase4_authorized() is allowed
    if allowed:
        pb.assert_phase4_authorized()
    else:
        with pytest.raises(pb.PhaseBoundaryError):
            pb.assert_phase4_authorized()


def test_even_when_authorized_phase_4_is_not_implemented_here(monkeypatch, tmp_path):
    """Authorization is not execution. Phase 3 authorizes Phase 4; it does not
    perform it, and this commit contains no Phase 4 implementation."""
    monkeypatch.setattr(pb, "ROOT", tmp_path)
    (tmp_path / "PHASE3_DECISION.md").write_text("# GO TO PHASE 4\n")
    with pytest.raises(NotImplementedError):
        pb.real_data_symbolic_search()


def test_confirmation_outcome_guard_rejects_a_sealed_key():
    import json
    seal = json.loads(
        (ROOT / "artifacts" / "confirmation_set_sealed.json").read_text())
    key = seal["connectivity_keys"][0]
    with pytest.raises(pb.PhaseBoundaryError):
        pb.assert_no_confirmation_outcomes([key, "AAAAAAAAAAAAAA"])
    pb.assert_no_confirmation_outcomes(["AAAAAAAAAAAAAA"])


def test_no_phase3_script_fits_a_symbolic_engine_to_the_real_response():
    """The real corpus artifact must never reach a search call in Phase 3."""
    offenders = []
    for p in sorted((ROOT / "scripts").glob("t3_*.py")):
        text = p.read_text()
        if "p2_dev_corpus" in text or "p2_splits" in text:
            offenders.append(p.name)
    assert not offenders, (
        f"{offenders} reference the real response corpus; Phase 3 may not fit "
        "a symbolic engine to observed mu")


def test_phase3_search_reads_only_synthetic_responses():
    src = (ROOT / "src" / "muru" / "discovery").glob("*.py")
    for p in src:
        t = p.read_text()
        assert "p2_dev_corpus" not in t, f"{p.name} reads the real response"
