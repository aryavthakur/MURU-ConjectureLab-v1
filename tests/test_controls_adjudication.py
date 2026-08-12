"""Regression tests for the negative-control adjudication (DEVIATIONS D16).

The first implementation adjudicated all six controls with one rule and inverted
the p-value, so a perfectly passing destruction control (no permuted replicate
beat the baseline) was reported as a BLOCKER, while the one control that
genuinely fires was concealed. These tests pin the corrected behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

ART = Path(__file__).resolve().parents[1] / "artifacts"
CTRL = ART / "p2_controls.json"


def _load():
    if not CTRL.exists():
        pytest.skip("p2_controls.json not generated in this checkout")
    return json.loads(CTRL.read_text())


DESTRUCTION = {"NC1_energy_shuffle_within_compound", "NC2_descriptor_shuffle",
               "NC3_trajectory_shuffle"}
NUISANCE = {"NC4_sham_descriptors", "NC6_mixture_identity", "NC7_retention_time"}


def test_every_control_declares_a_family():
    c = _load()["controls"]
    assert set(c) == DESTRUCTION | NUISANCE
    for n, v in c.items():
        assert v["family"] == ("destruction" if n in DESTRUCTION else "nuisance")


def test_destruction_controls_are_judged_on_residual_effect_share_not_p_value():
    """The object under test is the NULL, not the real-data statistic."""
    for n, v in _load()["controls"].items():
        if v["family"] != "destruction":
            continue
        assert "null_p95_as_share_of_real_effect" in v
        assert v["fires"] == (v["null_p95_as_share_of_real_effect"] > v["limit"])


def test_a_destruction_control_whose_null_never_beats_baseline_does_not_fire():
    """The exact inversion that produced the original false BLOCKER.

    NC1's null never beats B1 -- permutation destroyed the signal completely.
    That is a control PASSING, and it must not be reported as firing.
    """
    v = _load()["controls"]["NC1_energy_shuffle_within_compound"]
    assert v["frac_null_replicates_beating_B1"] == 0.0
    assert v["null_p95"] < 0
    assert v["fires"] is False


def test_real_data_exceeding_a_destruction_null_is_not_treated_as_failure():
    c = _load()["controls"]
    for n in DESTRUCTION:
        v = c[n]
        assert v["observed"] > v["null_p95"], "real data should beat the null"
        assert v["fires"] is False, (
            "real data beating a destruction null is the DESIRED outcome and "
            "must never mark the control as fired")


def test_nuisance_controls_compare_observed_against_their_own_null():
    for n, v in _load()["controls"].items():
        if v["family"] != "nuisance":
            continue
        assert v["exceeds_null_p95"] == (v["observed"] > v["null_p95"])
        assert v["fires"] == (v["exceeds_null_p95"] and v["bh_significant_at_q0.10"])


def test_sham_and_mixture_controls_are_null():
    c = _load()["controls"]
    assert c["NC4_sham_descriptors"]["fires"] is False
    assert c["NC6_mixture_identity"]["fires"] is False


def test_retention_time_control_fires_and_is_recorded():
    """NC7 genuinely exceeds its null; the record must say so plainly."""
    c = _load()
    assert c["controls"]["NC7_retention_time"]["fires"] is True
    assert "NC7_retention_time" in c["controls_fired"]
    assert "BLOCKER" in c["verdict"]


def test_nc7_followup_shows_rt_is_a_structure_surrogate():
    f = _load()["nc7_followup"]
    incremental = f["incremental_gain_from_adding_rt"]
    tier_a = f["improvement_tier_a_alone"]
    assert f["improvement_rt_alone"] > 0, "RT does predict on its own"
    assert incremental / tier_a < 0.10, (
        "RT must add little beyond Tier A for the structure-surrogate "
        "explanation to hold")


def test_bh_correction_applies_only_to_the_comparable_family():
    """Destruction controls are judged on effect share, so BH does not apply."""
    for n, v in _load()["controls"].items():
        if v["family"] == "destruction":
            assert "bh_significant_at_q0.10" not in v
        else:
            assert "bh_significant_at_q0.10" in v
