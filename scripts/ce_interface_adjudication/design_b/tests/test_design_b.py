"""Synthetic tests only. No real spectrum, prediction or procurement decision is read."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

D = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(D))
import design_b_constants as C  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace(".py", "").lstrip("0123456789_"), D / name)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


Q, W, X, A = load("30_build_queues.py"), load("35_procurement_walk.py"), load("40_extract_spectra.py"), load("60_analysis.py")


# ---------------- ordering ----------------
def test_ordering_key_is_sha256_of_frozen_string():
    import hashlib
    k = Q.ordering_key("H", "ABCDEFGHIJKLMN")
    assert k == hashlib.sha256(f"{C.STUDY_ID}|{C.FRAME_SHA256}|H|ABCDEFGHIJKLMN".encode()).hexdigest()


def test_queue_is_row_order_invariant_and_ranked_per_stratum():
    f = pd.DataFrame({"parent_key": [f"K{i:02d}" for i in range(20)], "stratum": ["L", "N", "H", "L"] * 5,
                      "scaffold_group": [f"g{i}" for i in range(20)]})
    a = Q.build(f)
    b = Q.build(f.sample(frac=1, random_state=3))
    assert a.reset_index(drop=True).equals(b.reset_index(drop=True))
    for s, g in a.groupby("stratum"):
        assert list(g["rank"]) == list(range(1, len(g) + 1))
        assert list(g["ordering_key"]) == sorted(g["ordering_key"])


def test_duplicate_key_refused():
    f = pd.DataFrame({"parent_key": ["A", "A"], "stratum": ["L", "L"], "scaffold_group": ["x", "y"]})
    with pytest.raises(SystemExit):
        Q.build(f)


# ---------------- walk ----------------
def queues(n=5, shared=None):
    rows = []
    for s in ("N", "H", "L"):
        for i in range(n):
            rows.append({"stratum": s, "rank": i + 1, "parent_key": f"{s}{i}", "scaffold_group": f"{s}g{i}"})
    q = pd.DataFrame(rows)
    if shared:
        for k, g in shared.items():
            q.loc[q["parent_key"] == k, "scaffold_group"] = g
    return q


def dec(keys, fail=None):
    fail = fail or {}
    return {k: {"decision": "FAIL" if k in fail else "PASS", "reason_code": fail.get(k, "")} for k in keys}


def test_walk_accepts_in_rank_order_and_skips_only_for_logged_reasons():
    q = queues()
    keys = list(q["parent_key"])
    trace, acc, st = W.walk(q, dec(keys, {"N1": "NO_SUPPLY", "H0": "PURITY_LT_95"}), target=3)
    assert acc == {"N": ["N0", "N2", "N3"], "H": ["H1", "H2", "H3"], "L": ["L0", "L1", "L2"]}
    assert all(v["state"] == "COMPLETE" for v in st.values())
    assert set(trace.loc[trace["outcome"] == "SKIP", "reason_code"]) == {"NO_SUPPLY", "PURITY_LT_95"}


def test_walk_stops_at_first_undecided_and_blocks_lower_priority():
    q = queues()
    d = dec(["N0", "N2", "N3", "H0", "H1", "H2"])  # N1 undecided
    trace, acc, st = W.walk(q, d, target=3)
    assert acc["N"] == ["N0"] and st["N"]["state"] == "PENDING"
    assert st["H"]["state"] == "BLOCKED_BY_HIGHER_PRIORITY_STRATUM" and acc["H"] == []


def test_cross_stratum_scaffold_priority_N_then_H_then_L():
    q = queues(shared={"N0": "shared", "H0": "shared", "L0": "shared"})
    trace, acc, st = W.walk(q, dec(list(q["parent_key"])), target=2)
    assert "N0" in acc["N"] and "H0" not in acc["H"] and "L0" not in acc["L"]
    assert (trace["reason_code"] == "SCAFFOLD_ALREADY_ACCEPTED").sum() == 2


def test_within_stratum_scaffold_duplicate_skipped():
    q = queues(shared={"N0": "s", "N1": "s"})
    trace, acc, st = W.walk(q, dec(list(q["parent_key"])), target=2)
    assert acc["N"] == ["N0", "N2"]


def test_exhausted_queue_reported():
    q = queues(n=3)
    trace, acc, st = W.walk(q, dec(list(q["parent_key"]), {"N2": "NO_SUPPLY"}), target=3)
    assert st["N"]["state"] == "EXHAUSTED"


def test_log_rejects_unregistered_reason_and_cost(tmp_path):
    p = tmp_path / "log.csv"
    row = {c: "" for c in W.LOG_COLUMNS}
    row.update(parent_key="A", stratum="L", decision="FAIL", reason_code="TOO_EXPENSIVE", evidence="e")
    pd.DataFrame([row]).to_csv(p, index=False)
    with pytest.raises(W.LogError):
        W.load_log(p)


def test_log_pass_requires_purity_and_quantity(tmp_path):
    p = tmp_path / "log.csv"
    row = {c: "" for c in W.LOG_COLUMNS}
    row.update(parent_key="A", stratum="L", decision="PASS", vendor="MCE", catalogue_id="HY-1", evidence="q",
               purity_percent="94.9", quantity_mg="5")
    pd.DataFrame([row]).to_csv(p, index=False)
    with pytest.raises(W.LogError):
        W.load_log(p)
    row["purity_percent"] = "98.1"
    pd.DataFrame([row]).to_csv(p, index=False)
    assert W.load_log(p)["A"]["decision"] == "PASS"


# ---------------- extraction ----------------
MH = 250.1234


def ms1(rt, amp, contaminant=0.0):
    return {"level": 1, "rt": rt, "mz": np.array([MH, MH + 0.3]), "it": np.array([amp, contaminant])}


def ms2(rt, nce, n_peaks=2):
    return {"level": 2, "rt": rt, "isolation": MH, "nce": float(nce),
            "mz": np.linspace(50, 200, n_peaks), "it": np.ones(n_peaks)}


def injection(amps, contaminant=0.0, nces=C.NCE_GRID):
    scans = []
    for i, a in enumerate(amps):
        scans.append(ms1(float(i), a, contaminant * a))
        for n in nces:
            scans.append(ms2(i + 0.1, n))
    return scans


def test_extraction_passes_with_three_scans_in_half_height_window():
    e = X.extract_injection(injection([0, 10, 60, 100, 70, 40, 5]), MH)
    assert e["pass"]
    assert all(c["n_qualifying"] == 3 for c in e["cells"].values())  # rt 2,3,4 are >= 50% of apex
    assert len(e["cells"][15]["mz"]) == 6  # concatenation, 3 scans x 2 peaks


def test_extraction_fails_below_three_scans():
    e = X.extract_injection(injection([0, 10, 100, 40, 5]), MH)
    assert not e["pass"] and e["cells"][30]["n_qualifying"] == 1


def test_purity_threshold_excludes_contaminated_scans():
    e = X.extract_injection(injection([0, 60, 100, 70, 0], contaminant=0.3), MH)  # purity 1/1.3 = 0.77
    assert not e["pass"] and e["cells"][45]["n_qualifying"] == 0


def test_missing_nce_level_fails_injection():
    e = X.extract_injection(injection([0, 60, 100, 70, 0], nces=(15, 30, 45, 60)), MH)
    assert not e["pass"] and not e["cells"][75]["pass"]


def test_undetected_precursor():
    e = X.extract_injection(injection([0, 0, 0]), MH)
    assert not e["pass"] and e["cells"][15]["reason"] == "precursor_not_detected"


def test_compound_outcome_uses_one_injection_only():
    good = X.extract_injection(injection([0, 60, 100, 70, 0]), MH)
    bad = X.extract_injection(injection([0, 100, 0]), MH)
    assert X.compound_outcome(good, None)["source"] == "primary"
    assert X.compound_outcome(bad, good)["source"] == "reinjection"
    assert X.compound_outcome(bad, bad)["status"] == "ACQUISITION_FAILURE"
    assert X.compound_outcome(bad, None)["status"] == "ACQUISITION_FAILURE"


def test_reproducibility_set_deterministic_9_per_stratum():
    man = pd.DataFrame({"parent_key": [f"K{i}" for i in range(198)], "stratum": ["L", "N", "H"] * 66})
    a, b = X.reproducibility_set(man), X.reproducibility_set(man.iloc[::-1])
    assert a == b and len(a) == 27
    assert man[man["parent_key"].isin(a)].groupby("stratum").size().to_dict() == {"H": 9, "L": 9, "N": 9}


# ---------------- analysis ----------------
def synth(effect=dict(L=0.05, N=0.0, H=0.05), n=60, sd=0.05, seed=1, mh=dict(L=200.0, N=500.0, H=800.0)):
    rng = np.random.default_rng(seed)
    rows = []
    for s, eff in effect.items():
        for i in range(n):
            base = rng.uniform(0.3, 0.7)
            ci_ = rng.normal(eff, sd)
            for nce in C.NCE_GRID:
                for mdl in C.MODELS:
                    for m, v in (("K1", base + ci_ / 2), ("K2", base - ci_ / 2), ("K3", base - ci_ / 2 - 0.001)):
                        rows.append({"compound_id": f"{s}{i}", "stratum": s, "scaffold_group": f"{s}g{i}",
                                     "theoretical_mh": mh[s], "nce": nce, "model": mdl, "mapping": m,
                                     "cosine": v, "js": v, "drop_reason": ""})
    return pd.DataFrame(rows)


def test_supported_and_identified():
    r = A.analyse(synth(), B=2000)
    assert r["decision"]["verdict"] == "K1 SUPPORTED AND IDENTIFIED"
    assert r["primary"]["point"]["D_div"] == pytest.approx(0.05, abs=0.02)


def test_favoured_not_identified_when_null_stratum_shows_same_effect():
    r = A.analyse(synth(effect=dict(L=0.05, N=0.05, H=0.05)), B=2000)
    assert r["decision"]["verdict"] == "K1 FAVOURED, NOT IDENTIFIED" and not r["decision"]["I_significant"]


def test_favoured_not_identified_when_L_and_H_disagree():
    r = A.analyse(synth(effect=dict(L=0.12, N=0.0, H=-0.01)), B=2000)
    assert r["decision"]["primary_rejects"] and not r["decision"]["L_H_signs_agree"]
    assert r["decision"]["verdict"] == "K1 FAVOURED, NOT IDENTIFIED"


def test_k2_direction():
    r = A.analyse(synth(effect=dict(L=-0.05, N=0.0, H=-0.05)), B=2000)
    assert r["decision"]["verdict"] == "K2 SUPPORTED AND IDENTIFIED"


def test_unresolved_on_null():
    r = A.analyse(synth(effect=dict(L=0.0, N=0.0, H=0.0), sd=0.13, seed=11), B=2000)
    assert r["decision"]["verdict"] == "INTERFACE UNRESOLVED" and not r["decision"]["identifying_test_run"]


def test_bootstrap_deterministic_and_equal_stratum_weights():
    s = synth(effect=dict(L=0.02, N=0.0, H=0.10))
    r1, r2 = A.analyse(s, B=500), A.analyse(s, B=500)
    assert r1["primary"]["ci_D_div"] == r2["primary"]["ci_D_div"]
    p = r1["primary"]["point"]
    assert p["D_div"] == pytest.approx((p["mean_L"] + p["mean_H"]) / 2)


def test_incomplete_compound_excluded_from_primary():
    s = synth()
    s.loc[(s["compound_id"] == "L0") & (s["mapping"] == "K2") & (s["nce"] == 15) & (s["model"] == "GLACIER"), "cosine"] = np.nan
    r = A.analyse(s, B=200)
    assert r["excluded_incomplete_prediction"] == ["L0"] and r["primary"]["n"]["L"] == 59


def test_q95_sensitivity_drops_high_ce_cells():
    r = A.analyse(synth(), B=200)
    # H at m/z 800: K2 > 90 for NCE >= 60, so those cells leave the sensitivity analysis
    assert r["descriptive"]["q95_support_sensitivity"]["n"]["H"] == 60
    s = synth()
    k2 = s["nce"] * s["theoretical_mh"] / 500
    assert ((s["stratum"] == "H") & (k2 > 90)).any()


def test_underpowered_disclosure_does_not_change_verdict():
    r = A.analyse(synth(n=45), B=1000)
    assert r["underpowered_disclosure"] == {"L": True, "N": True, "H": True}
    assert r["decision"]["verdict"].startswith("K1")
