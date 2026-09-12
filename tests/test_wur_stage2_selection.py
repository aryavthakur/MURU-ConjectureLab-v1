import json

import numpy as np
import pandas as pd

from muru.discovery import engine, grammar, protocol
from muru.wur_stage2 import selection as SEL
from muru.wur_stage2 import world as W


def _world(n=60, seed=0):
    rng = np.random.default_rng(seed)
    keys = [f"K{i:02d}" for i in range(n)]
    cov = pd.DataFrame({"connectivity_key": keys,
                        "scaffold_group": [f"S{i % 9}" for i in range(n)],
                        **{f: rng.uniform(0.5, 2.0, n) * protocol.SCALE[f] for f in protocol.FEATURES},
                        "source": "WUR"})
    rows = []
    for i, k in enumerate(keys):
        g = 1.0 + 0.5 * (cov.tpsa[i] / protocol.SCALE["tpsa"])
        for e in (15, 30, 45, 60, 75, 90):
            rows.append({"group_key": k, "ce_numeric": float(e),
                         "mu": float(np.exp(-(e / 30.0) / g) * 0.8 + 0.1), "source": "WUR"})
    wd, frame = W.build_world("T", pd.DataFrame(rows), cov)
    return wd


def _cand(expr_str, wd, seed, valid_r2):
    expr = grammar.parse(expr_str, list(wd.variables))
    return engine.Candidate(expr_str=expr_str, expr=expr, complexity=grammar.complexity(expr),
                            support=grammar.variable_support(expr, list(wd.variables)),
                            engine="pysr", seed=seed, train_r2=valid_r2, valid_r2=valid_r2,
                            invalid_fraction=0.0, valid=True)


def test_gate_thresholds_are_read_from_the_freeze_file():
    g = SEL.frozen_gate()
    fz = json.loads(SEL.FREEZE.read_text())["deployment_gate"]
    assert g["t1"] == fz["t1"] == 0.595 and g["t2"] == fz["t2"] == 0.2


def test_cache_select_gate_and_heldout_scoring_end_to_end():
    wd = _world()
    seeds = protocol.seed_list(wd.world_id)[:6]
    per_seed = {}
    for i, s in enumerate(seeds):
        cands = [_cand("0.5*tpsa + 1.0", wd, s, 0.9), _cand("tpsa*tpsa", wd, s, 0.85)]
        if i == 5:
            cands = [_cand("n_O + 1.0", wd, s, 0.3)]
        per_seed[s] = cands
    cache = SEL.candidate_cache(wd.world_id, wd, per_seed, seeds)
    assert cache["n_seeds"] == 6 and cache["missing_seeds"] == []
    assert len(cache["members"]) == 6      # band keeps only within 0.01 of each seed best
    sel = SEL.select_and_gate(cache)
    assert sel["report"] is True                       # median 0.9 >= 0.595, frac 5/6 >= 0.2
    assert sel["expr"] == "0.5*tpsa + 1.0"
    assert sel["gate"]["features"]["selection_fraction"] >= 5 / 6 - 1e-12
    test = SEL.score_on_part(sel["expr"], wd, "test")
    assert test["n"] == int((wd.split == "test").sum()) and np.isfinite(test["r2_weighted"])


def test_gate_refuses_when_median_seed_best_r2_is_low_and_missing_seeds_flagged():
    wd = _world(seed=1)
    seeds = protocol.seed_list(wd.world_id)[:4]
    per_seed = {s: [_cand("tpsa", wd, s, 0.2)] for s in seeds[:3]}
    cache = SEL.candidate_cache(wd.world_id, wd, per_seed, seeds)
    assert cache["missing_seeds"] == [seeds[3]]
    sel = SEL.select_and_gate(cache)
    assert sel["report"] is False and sel["computational_failure"] is True


def test_empty_cache_yields_no_representative():
    wd = _world(seed=2)
    seeds = protocol.seed_list(wd.world_id)[:2]
    cache = SEL.candidate_cache(wd.world_id, wd, {s: [] for s in seeds}, seeds)
    sel = SEL.select_and_gate(cache)
    assert sel["rep_index"] is None and sel["report"] is False
