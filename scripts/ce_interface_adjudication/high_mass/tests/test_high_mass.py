"""Synthetic tests for the high-mass replication wrappers. No real spectrum, prediction or score is used."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), HERE / name)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


AN = load("60_analysis.py")
C = AN.C


def synth(shift, seed=0):
    pop = pd.read_csv(ROOT / C.STUDY_DIR_REL / "population/high_mass_compounds.csv")
    rec = pd.read_csv(ROOT / C.STUDY_DIR_REL / "population/high_mass_records.csv")
    rng = np.random.default_rng(seed)
    rows = []
    for r in rec.itertuples():
        base = rng.uniform(0.2, 0.8)
        for m in C.MODELS:
            for k in C.MAPPINGS:
                v = base + (shift if k == "K1" else 0.0) + rng.normal(0, 0.02)
                rows.append({"record_id": f"{r.record_id}__{m}__{k}", "compound_id": r.compound_id,
                             "scaffold_group": r.scaffold_group, "nce": r.nce, "model": m, "mapping": k,
                             "cosine": v, "js": v, "drop_reason": ""})
    return pd.DataFrame(rows), pop


def test_verdicts():
    A = AN.load_design_a()
    for shift, want in ((0.1, "HIGH_MASS_SUPPORTS_K1"), (-0.1, "HIGH_MASS_SUPPORTS_K2"), (0.0, "HIGH_MASS_UNRESOLVED")):
        s, p = synth(shift)
        res = AN.analyse(A, s, p, n_boot=500)
        assert res["verdict"] == want, (shift, res["verdict"])
        assert res["primary"]["n_compounds_analysed"] == 32


def test_drop_rule_keeps_pairing():
    A = AN.load_design_a()
    s, p = synth(0.05)
    victim = p["compound_id"].iloc[0]
    idx = s.index[(s.compound_id == victim) & (s.mapping == "K3") & (s.nce == 15)]
    s.loc[idx, "drop_reason"] = "empty_prediction"
    res = AN.analyse(A, s, p, n_boot=200)
    assert res["primary"]["n_compounds_analysed"] == 31


def test_decide():
    assert AN.decide([0.001, 0.2]) == "HIGH_MASS_SUPPORTS_K1"
    assert AN.decide([-0.2, -0.001]) == "HIGH_MASS_SUPPORTS_K2"
    assert AN.decide([-0.01, 0.2]) == "HIGH_MASS_UNRESOLVED"


def test_wrappers_pin_design_a():
    S = load("40_score_spectra.py").load_scorer()
    assert S.NCE_CELLS == C.NCE_GRID and S.FREEZE_REF == C.FREEZE_REF
    pop = S.read_population(ROOT / S.RECORDS_CSV_REL)
    assert len(pop) == 364
    H = load("30_run_predictions.py").load_harness()
    assert H.NCE_RUNGS == C.NCE_GRID and H.EXECUTE_ENV_VAR == C.EXECUTE_ENV_VAR


def test_k2_above_k1_for_high_mass():
    pop = pd.read_csv(ROOT / C.STUDY_DIR_REL / "population/high_mass_compounds.csv")
    assert (pop["theoretical_mh"] > 500).sum() == 29
    assert pop["scaffold_group"].is_unique
