import json

import numpy as np
import pytest

from muru.wur_stage2 import candidates as CA
from muru.wur_stage2 import cv as CV


def _ledger(tmp, cid, p1s, s3, s4, n_feat, comps=None, interp=True):
    folds = [{"P1": p, "S3_loeo_mae_median": s3, "S4_catastrophic": s4} for p in p1s]
    d = {"candidate_id": cid, "folds": folds, "P1_mean": float(np.mean(p1s)),
         "P1_sd": float(np.std(p1s, ddof=1)), "features": {"n_features": n_feat, "n_free_params": n_feat},
         "interpretable": interp, "comparisons": {"fold_compare": comps or {}}}
    (tmp / f"{cid}.json").write_text(json.dumps(d))


def test_rule_requires_every_condition(tmp_path, monkeypatch):
    monkeypatch.setattr(CV, "LEDGER", tmp_path)
    ref = [0.15 + 0.01 * (i % 3) for i in range(15)]
    _ledger(tmp_path, "S2A_FROZEN_PIPELINE", ref, 0.0465, 0.12, 12)
    good = [0.13] * 15
    comps = {"S2A_FROZEN_PIPELINE": {"wins": 15, "mean_rel_improvement": 0.13},
             "B0_NULL_PROFILE": {"wins": 15}, "B1_MASS_ONLY_ISOTONIC": {"wins": 15}}
    _ledger(tmp_path, "C_OK", good, 0.046, 0.10, 12, comps)
    r = CA.evaluate_rule("C_OK")
    assert r["beats_s2a"] and r["gate_clauses"]
    # each condition individually
    _ledger(tmp_path, "C_W11", good, 0.046, 0.10, 12, {**comps, "S2A_FROZEN_PIPELINE": {"wins": 11, "mean_rel_improvement": 0.13}})
    assert not CA.evaluate_rule("C_W11")["conditions"]["c1_wins_vs_s2a"]
    _ledger(tmp_path, "C_REL", good, 0.046, 0.10, 12, {**comps, "S2A_FROZEN_PIPELINE": {"wins": 15, "mean_rel_improvement": 0.049}})
    assert not CA.evaluate_rule("C_REL")["conditions"]["c2_rel_improvement"]
    _ledger(tmp_path, "C_B1", good, 0.046, 0.10, 12, {**comps, "B1_MASS_ONLY_ISOTONIC": {"wins": 11}})
    assert not CA.evaluate_rule("C_B1")["conditions"]["c3_beats_b0_and_b1"]
    _ledger(tmp_path, "C_S4", good, 0.046, 0.13, 12, comps)
    assert not CA.evaluate_rule("C_S4")["conditions"]["c4_no_catastrophic_regression"]
    _ledger(tmp_path, "C_S3", good, 0.0496, 0.10, 12, comps)
    assert not CA.evaluate_rule("C_S3")["conditions"]["c5_inherited_s3_A1"]
    _ledger(tmp_path, "C_S3ok", good, 0.0495, 0.10, 12, comps)
    assert CA.evaluate_rule("C_S3ok")["conditions"]["c5_inherited_s3_A1"]
    _ledger(tmp_path, "C_BB", good, 0.046, 0.10, 12, comps, interp=False)
    bb = CA.evaluate_rule("C_BB")
    assert bb["conditions"]["c2_rel_improvement"] and bb["beats_s2a"]      # section 7 stays at 5%
    assert not bb["conditions"]["g_black_box_bar"] and not bb["gate_clauses"]  # section 8 S6 bar
    _ledger(tmp_path, "C_FEAT", good, 0.046, 0.10, 25, comps)
    assert not CA.evaluate_rule("C_FEAT")["conditions"]["g_complexity"]
    _ledger(tmp_path, "C_SD", [0.10, 0.20] * 7 + [0.1], 0.046, 0.10, 12, comps)
    assert not CA.evaluate_rule("C_SD")["conditions"]["g_stability"]


def test_ranking_prefers_simplest_within_one_se(tmp_path, monkeypatch):
    monkeypatch.setattr(CV, "LEDGER", tmp_path)
    rng = np.random.default_rng(0)
    base = 0.13 + rng.normal(0, 0.01, 15)
    _ledger(tmp_path, "COMPLEX", list(base), 0.046, 0.1, 20)
    _ledger(tmp_path, "SIMPLE", list(base + 0.0005 + rng.normal(0, 0.003, 15)), 0.046, 0.1, 6)  # within SE
    _ledger(tmp_path, "WORSE", list(base + 0.02 + rng.normal(0, 0.003, 15)), 0.046, 0.1, 3)     # not within SE
    ranked = CA.rank_candidates(["COMPLEX", "SIMPLE", "WORSE"])
    sel = [r["id"] for r in ranked if r["selected"]]
    assert sel == ["SIMPLE"]
    assert not [r for r in ranked if r["id"] == "WORSE"][0]["tied_with_best"]
