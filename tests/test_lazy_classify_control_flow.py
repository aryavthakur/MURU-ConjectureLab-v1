"""Control-flow tests for lazy_classify.lazy_evaluate_world.

`classify_expression` (the SymPy-heavy call) is mocked -- these tests are
about the witness-order ALGORITHM (how many calls it makes, which stage it
picks, when it short-circuits), not about SymPy itself. `g2_contract`'s
`classify_support`/`classify_family_match`/`evaluate_g2_event` are used FOR
REAL (they are pure, cheap set/string comparisons, not symbolic -- no
reason to fake them, and using them for real is more faithful).
`algebraically_equivalent` and its parse helpers ARE mocked for the D-vs-C
tests only, to keep this tier fast and fully synthetic.

Scientific fidelity against the real frozen classifier end-to-end is
validated separately by the replay-parity harness (Part V) against real
completed worlds. See MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md section 4 for
why this two-tier split is the right testing strategy.
"""
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.v2_calibration.e2_rescue_v2 import lazy_classify as lc  # noqa: E402

TRUTH_FAMILY = "mass_power"  # a real TRUTH_FAMILIES entry; classify_family_match needs it to resolve
TRUTH_SUPPORT = frozenset({"x0", "x1"})


@dataclass(frozen=True)
class FakeTruth:
    support: frozenset = TRUTH_SUPPORT
    family: str = TRUTH_FAMILY
    law_string: str = "x0"


@dataclass(frozen=True)
class FakeClassification:
    parse_ok: bool = True
    canonicalization_status: str = "OK"
    canonical_expression: str = "x0"
    effective_support: frozenset = TRUTH_SUPPORT       # correct by default
    discovered_family: str = TRUTH_FAMILY              # correct by default
    template_key_repr: str = "fake_key"
    coefficient_estimates: tuple = (1.0,)


def _raw(seed: int, k: int, rank: int, expr: str, retained: bool) -> lc.RawFrontRow:
    return lc.RawFrontRow(
        seed_ordinal_k=k, seed=seed, front_rank=rank, expression_string=expr,
        complexity=3, valid_r2=0.9, invalid_fraction=0.0, candidate_test_r2=0.9,
        retained_by_argmax_score=retained,
    )


def _run(seed_raw_fronts, correct_exprs, equivalence_result=None):
    """correct_exprs: set of expression strings that classify as g2_correct
    (real support/family match against FakeTruth); anything else is
    incorrect (wrong family)."""
    lc.reset_call_counters()

    def fake_classify(expr):
        if expr in correct_exprs:
            return FakeClassification()
        return FakeClassification(effective_support=frozenset({"x9"}), discovered_family="mass_affine_descriptor")

    with patch.object(lc.e2_classify, "classify_expression", side_effect=fake_classify), \
         patch.object(lc, "algebraically_equivalent", side_effect=lambda a, b: equivalence_result), \
         patch.object(lc, "parse_production_candidate", side_effect=lambda s: s), \
         patch.object(lc, "_parse_truth", side_effect=lambda s: s):
        return lc.lazy_evaluate_world(seed_raw_fronts, truth=FakeTruth())


def test_stage_e_needs_only_one_classify_call_per_seed():
    fronts = {0: [_raw(0, 0, 0, "CORRECT", retained=True), _raw(0, 0, 1, "junk0", retained=False)]}
    for s in range(1, 30):
        fronts[s] = [_raw(s, s, 0, f"other{s}", retained=True)]
    result = _run(fronts, correct_exprs={"CORRECT"})
    assert result.first_loss_stage == "E"
    assert result.witness_path == "PHASE1_RETAINED_ONLY"
    assert result.n_classify_calls == 30  # one retained row per seed, no front-scan, no equivalence call
    assert result.n_equivalence_calls == 0


def test_stage_b_short_circuits_on_first_witness_in_seed_order():
    fronts = {
        0: [
            _raw(0, 0, 0, "retained0", retained=True),
            _raw(0, 0, 1, "WITNESS", retained=False),
            _raw(0, 0, 2, "never_reached", retained=False),
        ],
    }
    for s in range(1, 30):
        fronts[s] = [_raw(s, s, 0, f"retained{s}", retained=True), _raw(s, s, 1, f"unreached{s}", retained=False)]
    result = _run(fronts, correct_exprs={"WITNESS"})
    assert result.first_loss_stage == "B"
    assert result.witness_path == "PHASE2_FRONT_SCAN_B"
    assert result.n_classify_calls == 31  # 30 retained (phase 1) + exactly 1 more (the witness), not 60
    assert result.n_equivalence_calls == 0  # stage B never needs the equivalence check


def test_stage_a_requires_full_scan_every_row():
    fronts = {}
    for s in range(30):
        fronts[s] = [
            _raw(s, s, 0, f"retained{s}", retained=True),
            _raw(s, s, 1, f"other{s}", retained=False),
        ]
    result = _run(fronts, correct_exprs=set())  # nothing is ever correct
    assert result.first_loss_stage == "A"
    assert result.witness_path == "PHASE2_FULL_SCAN_A"
    assert result.n_classify_calls == 60  # every single row, same as exhaustive
    assert result.n_equivalence_calls == 0


def test_stage_d_vs_c_uses_at_most_one_equivalence_call():
    # Seed 0's retained candidate is a correct, but SOLITARY, minority
    # class (size 1) -> proves not-B (n_retained_correct > 0). Seeds 1-10
    # all retain the SAME wrong expression -> a majority class of size 10
    # that group_and_select's (size desc, min_ordinal asc) rule picks as
    # winner over the size-1 correct class. The representative is
    # therefore the WRONG majority candidate, not the correct minority one
    # -- exactly the scenario section 6 of the predeclaration calls C/D
    # ("a genuinely incorrect class won the cross-seed vote").
    fronts = {0: [_raw(0, 0, 0, "CORRECT_MINORITY", retained=True)]}
    for s in range(1, 11):
        fronts[s] = [_raw(s, s, 0, "WRONG_MAJORITY", retained=True)]

    result = _run(fronts, correct_exprs={"CORRECT_MINORITY"}, equivalence_result=True)
    assert result.first_loss_stage == "D"
    assert result.representative_expression == "WRONG_MAJORITY"
    assert result.n_equivalence_calls == 1

    result_c = _run(fronts, correct_exprs={"CORRECT_MINORITY"}, equivalence_result=False)
    assert result_c.first_loss_stage == "C"
    assert result_c.n_equivalence_calls == 1


def test_stage_e_never_calls_equivalence_even_though_score_row_would_have():
    # This is the deliberate divergence from score_row's own per-row
    # behavior -- see lazy_classify.py's module docstring, "Why g2_correct
    # and truth_equivalent are computed via two separate calls".
    fronts = {0: [_raw(0, 0, 0, "CORRECT", retained=True)]}
    for s in range(1, 30):
        fronts[s] = [_raw(s, s, 0, f"other{s}", retained=True)]
    result = _run(fronts, correct_exprs={"CORRECT"}, equivalence_result=True)
    assert result.first_loss_stage == "E"
    assert result.n_equivalence_calls == 0
    assert result.representative_truth_equivalent is None  # intentionally not computed


if __name__ == "__main__":
    import inspect
    import traceback
    mod = sys.modules[__name__]
    fns = [f for name, f in inspect.getmembers(mod, inspect.isfunction) if name.startswith("test_")]
    failed = 0
    for f in fns:
        try:
            f()
            print(f"PASS {f.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {f.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
