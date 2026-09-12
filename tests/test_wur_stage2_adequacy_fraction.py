import numpy as np
import pytest

from muru.paper_benchmark import adequacy as A
from muru.paper_benchmark.adequacy import CompoundContrastRecord as R
from muru.wur_stage2 import adequacy_fraction as F


def _rec(i, det, m0, alt, state="OK", n=6, unresolved=False):
    return R(compound_id=f"c{i}", detector=det, observed_energy_count=n,
             mae_m0=m0, mae_alt=alt, execution_state=state,
             unresolved_boundary=unresolved)


def test_thresholds_reproduce_frozen_contract_at_n30():
    assert F.min_evaluable(30) == A.MIN_EVALUABLE_COMPOUNDS == 24
    assert F.min_wins(30) == A.MIN_PRACTICAL_WINS == 20
    assert F.evaluable_sufficient(24, 30) and not F.evaluable_sufficient(23, 30)
    assert F.wins_sufficient(20, 30) and not F.wins_sufficient(19, 30)


@pytest.mark.parametrize("n,ev,w", [(10, 8, 7), (7, 6, 5), (1, 1, 1),
                                    (100, 80, 67), (791, 633, 528), (158, 127, 106)])
def test_thresholds_are_ceilings_of_fractions(n, ev, w):
    assert F.min_evaluable(n) == ev
    assert F.min_wins(n) == w
    assert F.min_evaluable(n) >= 0.8 * n - 1e-12
    assert F.min_wins(n) >= 2 * n / 3 - 1e-12


def test_float_rounding_cannot_move_the_threshold():
    # integer arithmetic: independent of how 0.8 * N or 2 * N / 3 round in binary64
    for n in range(1, 2000):
        assert F.evaluable_sufficient(F.min_evaluable(n), n)
        assert not F.evaluable_sufficient(F.min_evaluable(n) - 1, n)
        assert F.wins_sufficient(F.min_wins(n), n)
        assert not F.wins_sufficient(F.min_wins(n) - 1, n)


@pytest.mark.parametrize("seed", range(20))
def test_matches_frozen_evaluate_contrast_at_n30(seed):
    rng = np.random.default_rng(seed)
    recs = []
    for i in range(30):
        m0 = float(rng.uniform(0.01, 0.1))
        alt = m0 * float(rng.uniform(0.7, 1.1))
        state = "OK" if rng.random() > 0.1 else "NUMERICAL_FAILURE"
        n = 6 if rng.random() > 0.1 else 4
        recs.append(_rec(i, "M1", m0, alt, state, n, unresolved=rng.random() < 0.05))
    a = A.evaluate_contrast("M1", recs)
    b = F.evaluate_contrast_fraction("M1", recs)
    assert (a.evaluable, a.practical_wins, a.evaluable_sufficient, a.fired) == \
        (b.evaluable, b.practical_wins, b.evaluable_sufficient, b.fired)
    assert dict(a.status_counts) == dict(b.status_counts)


def test_case_decision_fires_and_not_rejected_and_indeterminate():
    n = 10
    win = [_rec(i, "M2", 0.1, 0.05) for i in range(n)]          # 10 wins of 10
    lose = {d: [_rec(i, d, 0.1, 0.1) for i in range(n)] for d in ("M1", "M3")}
    res = F.decide_case_adequacy_fraction("x", {"M2": win, **lose})
    assert res.status is A.CaseAdequacyStatus.M0_REJECTED_M2 and res.fired == ("M2",)
    allok = {d: [_rec(i, d, 0.1, 0.1) for i in range(n)] for d in ("M1", "M2", "M3")}
    assert F.decide_case_adequacy_fraction("x", allok).status is A.CaseAdequacyStatus.M0_NOT_REJECTED
    short = {d: [_rec(i, d, 0.1, 0.1, n=4) for i in range(n)] for d in ("M1", "M2", "M3")}
    r = F.decide_case_adequacy_fraction("x", short)
    assert r.status is A.CaseAdequacyStatus.INSUFFICIENT_DATA
    assert "8-of-10" in r.blocker
    # exactly 7 of 10 wins fires, 6 does not
    seven = {"M1": [_rec(i, "M1", 0.1, 0.05 if i < 7 else 0.1) for i in range(n)],
             "M2": allok["M2"], "M3": allok["M3"]}
    assert F.decide_case_adequacy_fraction("x", seven).fired == ("M1",)
    six = {"M1": [_rec(i, "M1", 0.1, 0.05 if i < 6 else 0.1) for i in range(n)],
           "M2": allok["M2"], "M3": allok["M3"]}
    assert F.decide_case_adequacy_fraction("x", six).fired == ()


def test_duplicate_and_empty_are_contract_failures():
    with pytest.raises(A.ContractFailure):
        F.evaluate_contrast_fraction("M1", [])
    with pytest.raises(A.ContractFailure):
        F.evaluate_contrast_fraction("M1", [_rec(1, "M1", .1, .1), _rec(1, "M1", .1, .1)])
