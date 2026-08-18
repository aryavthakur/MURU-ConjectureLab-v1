"""Tests for the E2b direct three-way attribution evaluator.

All fixtures are synthetic. No real front artifacts, no historical labels,
no v1 decomposition data. Every branch of the four-way partition is covered,
plus the Gate 1 threshold boundary.
"""
from __future__ import annotations

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from e2b_direct_evaluator import (
    FROZEN_MATERIAL_THRESHOLD,
    HISTORICAL_GENERATION,
    HISTORICAL_RETENTION,
    SEEDS_PER_CASE,
    CaseAttribution,
    DirectClass,
    GateResult,
    SeedFrontResult,
    classify_case,
    evaluate_gate_1,
    evaluate_seed_front,
    is_row_g2_correct,
)


# -----------------------------------------------------------------------
# Shared truth fixtures
# -----------------------------------------------------------------------

# mass_affine_descriptor: support = {"mass", "descriptor"}, family = "mass_affine_descriptor"
TRUTH_SUPPORT_AFFINE = frozenset({"mass", "descriptor"})
TRUTH_FAMILY_AFFINE = "mass_affine_descriptor"

# mass_power: support = {"mass"}, family = "mass_power"
TRUTH_SUPPORT_POWER = frozenset({"mass"})
TRUTH_FAMILY_POWER = "mass_power"

# A correct expression for mass_affine_descriptor
CORRECT_AFFINE_EXPR = "1.5 * sqrt(mass / 250) * (1 + 0.4 * descriptor)"

# An incorrect expression (mass_power, wrong family for affine truth)
INCORRECT_EXPR_POWER = "1.3 * (mass / 250) ** 0.6"

# A correct expression for mass_power
CORRECT_POWER_EXPR = "1.3 * (mass / 250) ** 0.6"


# -----------------------------------------------------------------------
# Helper: build synthetic front rows
# -----------------------------------------------------------------------

def make_front_row(
    equation: str,
    score: float,
    seed_ordinal: int = 0,
    seed: int = 42,
) -> dict:
    """Build a minimal synthetic front row dict."""
    return {
        "equation": equation,
        "score": score,
        "loss": 1.0 / (1.0 + score) if score > 0 else 1.0,
        "complexity": len(equation),
        "valid_r2": 0.9,
        "_case_id": "TEST_CASE",
        "_seed_ordinal": seed_ordinal,
        "_seed": seed,
    }


def make_seed_result(
    seed_ordinal: int,
    correct_on_front: bool,
    retained_correct: bool,
    seed: int = -1,
) -> SeedFrontResult:
    """Build a synthetic SeedFrontResult."""
    return SeedFrontResult(
        seed_ordinal=seed_ordinal,
        seed=seed,
        front_size=10,
        correct_on_front=correct_on_front,
        retained_correct=retained_correct,
        correct_row_count=1 if correct_on_front else 0,
    )


def make_n_seed_results(
    n_total: int = SEEDS_PER_CASE,
    n_correct_on_front: int = 0,
    n_retained_correct: int = 0,
) -> list[SeedFrontResult]:
    """Build n_total SeedFrontResults with specified correct counts.

    The first n_retained_correct seeds have retained_correct=True (implies
    correct_on_front=True). Then additional seeds up to n_correct_on_front
    have correct_on_front=True but retained_correct=False. Remaining seeds
    have both False.
    """
    assert n_retained_correct <= n_correct_on_front <= n_total
    results = []
    for i in range(n_total):
        if i < n_retained_correct:
            results.append(make_seed_result(i, True, True))
        elif i < n_correct_on_front:
            results.append(make_seed_result(i, True, False))
        else:
            results.append(make_seed_result(i, False, False))
    return results


# -----------------------------------------------------------------------
# Tests: is_row_g2_correct
# -----------------------------------------------------------------------

class TestIsRowG2Correct:

    def test_correct_affine(self):
        assert is_row_g2_correct(
            CORRECT_AFFINE_EXPR, TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE
        ) is True

    def test_wrong_family(self):
        """mass_power expression is not correct for affine truth."""
        assert is_row_g2_correct(
            INCORRECT_EXPR_POWER, TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE
        ) is False

    def test_correct_power(self):
        assert is_row_g2_correct(
            CORRECT_POWER_EXPR, TRUTH_SUPPORT_POWER, TRUTH_FAMILY_POWER
        ) is True

    def test_wrong_support(self):
        """mass+descriptor expression is not correct for mass-only truth."""
        assert is_row_g2_correct(
            CORRECT_AFFINE_EXPR, TRUTH_SUPPORT_POWER, TRUTH_FAMILY_POWER
        ) is False

    def test_unparseable(self):
        """Unparseable expression is not G2-correct."""
        assert is_row_g2_correct(
            "???invalid??!", TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE
        ) is False

    def test_empty_string(self):
        """Empty expression is not G2-correct."""
        assert is_row_g2_correct(
            "", TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE
        ) is False


# -----------------------------------------------------------------------
# Tests: evaluate_seed_front
# -----------------------------------------------------------------------

class TestEvaluateSeedFront:

    def test_front_with_correct_retained(self):
        """Front where the argmax(score) row is correct."""
        rows = [
            make_front_row(INCORRECT_EXPR_POWER, score=0.5, seed_ordinal=0),
            make_front_row(CORRECT_AFFINE_EXPR, score=1.0, seed_ordinal=0),  # highest score
        ]
        result = evaluate_seed_front(rows, TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert result.correct_on_front is True
        assert result.retained_correct is True
        assert result.correct_row_count == 1
        assert result.front_size == 2

    def test_front_with_correct_not_retained(self):
        """Front where a correct row exists but argmax(score) picks another."""
        rows = [
            make_front_row(CORRECT_AFFINE_EXPR, score=0.5, seed_ordinal=0),
            make_front_row(INCORRECT_EXPR_POWER, score=1.0, seed_ordinal=0),  # highest score
        ]
        result = evaluate_seed_front(rows, TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert result.correct_on_front is True
        assert result.retained_correct is False
        assert result.correct_row_count == 1

    def test_front_no_correct(self):
        """Front with no correct rows."""
        rows = [
            make_front_row(INCORRECT_EXPR_POWER, score=1.0, seed_ordinal=0),
            make_front_row(INCORRECT_EXPR_POWER, score=0.5, seed_ordinal=0),
        ]
        result = evaluate_seed_front(rows, TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert result.correct_on_front is False
        assert result.retained_correct is False
        assert result.correct_row_count == 0

    def test_front_multiple_correct(self):
        """Front with multiple correct rows."""
        rows = [
            make_front_row(CORRECT_AFFINE_EXPR, score=1.0, seed_ordinal=0),
            make_front_row(CORRECT_AFFINE_EXPR, score=0.5, seed_ordinal=0),
            make_front_row(INCORRECT_EXPR_POWER, score=0.3, seed_ordinal=0),
        ]
        result = evaluate_seed_front(rows, TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert result.correct_on_front is True
        assert result.retained_correct is True
        assert result.correct_row_count == 2


# -----------------------------------------------------------------------
# Tests: classify_case - four-way partition
# -----------------------------------------------------------------------

class TestClassifyCase:
    """Tests for the four-way E2b attribution partition."""

    def test_success_branch(self):
        """SUCCESS: representative is G2-correct."""
        seed_results = make_n_seed_results(
            n_total=SEEDS_PER_CASE,
            n_correct_on_front=5,
            n_retained_correct=3,
        )
        attribution = classify_case(
            case_id="TEST|SUCCESS",
            seed_results=seed_results,
            representative_expression=CORRECT_AFFINE_EXPR,
            truth_support=TRUTH_SUPPORT_AFFINE,
            truth_family=TRUTH_FAMILY_AFFINE,
        )
        assert attribution.direct_class == DirectClass.SUCCESS
        assert attribution.representative_correct is True
        assert attribution.seeds_with_correct_on_front == 5
        assert attribution.seeds_with_retained_correct == 3
        assert attribution.valid is True

    def test_never_on_front_branch(self):
        """NEVER_ON_FRONT: 0 seeds have any correct row on front."""
        seed_results = make_n_seed_results(
            n_total=SEEDS_PER_CASE,
            n_correct_on_front=0,
            n_retained_correct=0,
        )
        attribution = classify_case(
            case_id="TEST|GENERATION",
            seed_results=seed_results,
            representative_expression=INCORRECT_EXPR_POWER,
            truth_support=TRUTH_SUPPORT_AFFINE,
            truth_family=TRUTH_FAMILY_AFFINE,
        )
        assert attribution.direct_class == DirectClass.NEVER_ON_FRONT
        assert attribution.representative_correct is False
        assert attribution.seeds_with_correct_on_front == 0
        assert attribution.seeds_with_retained_correct == 0
        assert attribution.valid is True

    def test_lost_in_retention_branch(self):
        """LOST_IN_RETENTION: correct on front but 0 retained correct."""
        seed_results = make_n_seed_results(
            n_total=SEEDS_PER_CASE,
            n_correct_on_front=10,
            n_retained_correct=0,
        )
        attribution = classify_case(
            case_id="TEST|RETENTION",
            seed_results=seed_results,
            representative_expression=INCORRECT_EXPR_POWER,
            truth_support=TRUTH_SUPPORT_AFFINE,
            truth_family=TRUTH_FAMILY_AFFINE,
        )
        assert attribution.direct_class == DirectClass.LOST_IN_RETENTION
        assert attribution.representative_correct is False
        assert attribution.seeds_with_correct_on_front == 10
        assert attribution.seeds_with_retained_correct == 0
        assert attribution.valid is True

    def test_lost_in_cross_seed_branch(self):
        """LOST_IN_CROSS_SEED: correct retained but representative not correct."""
        seed_results = make_n_seed_results(
            n_total=SEEDS_PER_CASE,
            n_correct_on_front=8,
            n_retained_correct=3,
        )
        attribution = classify_case(
            case_id="TEST|CROSS_SEED",
            seed_results=seed_results,
            representative_expression=INCORRECT_EXPR_POWER,
            truth_support=TRUTH_SUPPORT_AFFINE,
            truth_family=TRUTH_FAMILY_AFFINE,
        )
        assert attribution.direct_class == DirectClass.LOST_IN_CROSS_SEED
        assert attribution.representative_correct is False
        assert attribution.seeds_with_correct_on_front == 8
        assert attribution.seeds_with_retained_correct == 3
        assert attribution.valid is True

    def test_none_representative(self):
        """Representative is None (no winning class) => not correct."""
        seed_results = make_n_seed_results(
            n_total=SEEDS_PER_CASE,
            n_correct_on_front=0,
            n_retained_correct=0,
        )
        attribution = classify_case(
            case_id="TEST|NO_REP",
            seed_results=seed_results,
            representative_expression=None,
            truth_support=TRUTH_SUPPORT_AFFINE,
            truth_family=TRUTH_FAMILY_AFFINE,
        )
        assert attribution.direct_class == DirectClass.NEVER_ON_FRONT
        assert attribution.representative_correct is False
        assert attribution.valid is True

    def test_invalid_seed_count(self):
        """If not exactly 30 seed results, case is invalid."""
        seed_results = make_n_seed_results(
            n_total=15,  # only 15 seeds
            n_correct_on_front=5,
            n_retained_correct=2,
        )
        attribution = classify_case(
            case_id="TEST|INVALID",
            seed_results=seed_results,
            representative_expression=INCORRECT_EXPR_POWER,
            truth_support=TRUTH_SUPPORT_AFFINE,
            truth_family=TRUTH_FAMILY_AFFINE,
        )
        assert attribution.valid is False
        assert "Expected 30" in attribution.invalid_reason

    def test_partition_exhaustive(self):
        """The four classes are exhaustive: every valid combination falls
        into exactly one bucket."""
        # Case 1: representative correct => SUCCESS
        sr = make_n_seed_results(30, 5, 5)
        a = classify_case("X", sr, CORRECT_AFFINE_EXPR,
                          TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert a.direct_class == DirectClass.SUCCESS

        # Case 2: nothing on any front => NEVER_ON_FRONT
        sr = make_n_seed_results(30, 0, 0)
        a = classify_case("X", sr, INCORRECT_EXPR_POWER,
                          TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert a.direct_class == DirectClass.NEVER_ON_FRONT

        # Case 3: on front, retained, but rep wrong => LOST_IN_CROSS_SEED
        sr = make_n_seed_results(30, 10, 5)
        a = classify_case("X", sr, INCORRECT_EXPR_POWER,
                          TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert a.direct_class == DirectClass.LOST_IN_CROSS_SEED

        # Case 4: on front, NOT retained => LOST_IN_RETENTION
        sr = make_n_seed_results(30, 10, 0)
        a = classify_case("X", sr, INCORRECT_EXPR_POWER,
                          TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert a.direct_class == DirectClass.LOST_IN_RETENTION

    def test_mutual_exclusivity(self):
        """For any single case, exactly one class is assigned."""
        configs = [
            # (n_correct_on_front, n_retained_correct, rep_expr)
            (0, 0, INCORRECT_EXPR_POWER),
            (10, 0, INCORRECT_EXPR_POWER),
            (10, 5, INCORRECT_EXPR_POWER),
            (10, 5, CORRECT_AFFINE_EXPR),
            (30, 30, CORRECT_AFFINE_EXPR),
            (1, 0, INCORRECT_EXPR_POWER),
            (1, 1, INCORRECT_EXPR_POWER),
            (1, 1, CORRECT_AFFINE_EXPR),
        ]
        for n_front, n_ret, rep in configs:
            sr = make_n_seed_results(30, n_front, n_ret)
            a = classify_case("X", sr, rep,
                              TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
            assert a.valid is True
            assert a.direct_class in (
                DirectClass.SUCCESS,
                DirectClass.NEVER_ON_FRONT,
                DirectClass.LOST_IN_RETENTION,
                DirectClass.LOST_IN_CROSS_SEED,
            )

    def test_edge_single_seed_correct_not_retained(self):
        """Edge: exactly 1 seed has correct on front but not retained."""
        sr = make_n_seed_results(30, 1, 0)
        a = classify_case("X", sr, INCORRECT_EXPR_POWER,
                          TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert a.direct_class == DirectClass.LOST_IN_RETENTION

    def test_edge_single_seed_retained_not_winning(self):
        """Edge: exactly 1 seed retains correct but rep is wrong."""
        sr = make_n_seed_results(30, 1, 1)
        a = classify_case("X", sr, INCORRECT_EXPR_POWER,
                          TRUTH_SUPPORT_AFFINE, TRUTH_FAMILY_AFFINE)
        assert a.direct_class == DirectClass.LOST_IN_CROSS_SEED


# -----------------------------------------------------------------------
# Tests: evaluate_gate_1 - threshold boundaries
# -----------------------------------------------------------------------

class TestGate1:
    """Tests for the Gate 1 falsification hook threshold."""

    def _make_attributions(
        self,
        n_retention: int,
        n_generation: int,
        n_success: int = 0,
        n_cross_seed: int = 0,
        n_invalid: int = 0,
    ) -> list[CaseAttribution]:
        """Build a list of CaseAttributions with specified class counts."""
        attrs: list[CaseAttribution] = []
        idx = 0

        for _ in range(n_success):
            attrs.append(CaseAttribution(
                case_id=f"CASE_{idx:03d}", direct_class=DirectClass.SUCCESS,
                seeds_with_correct_on_front=10, seeds_with_retained_correct=5,
                representative_correct=True, valid=True, invalid_reason=None,
            ))
            idx += 1

        for _ in range(n_retention):
            attrs.append(CaseAttribution(
                case_id=f"CASE_{idx:03d}", direct_class=DirectClass.LOST_IN_RETENTION,
                seeds_with_correct_on_front=10, seeds_with_retained_correct=0,
                representative_correct=False, valid=True, invalid_reason=None,
            ))
            idx += 1

        for _ in range(n_generation):
            attrs.append(CaseAttribution(
                case_id=f"CASE_{idx:03d}", direct_class=DirectClass.NEVER_ON_FRONT,
                seeds_with_correct_on_front=0, seeds_with_retained_correct=0,
                representative_correct=False, valid=True, invalid_reason=None,
            ))
            idx += 1

        for _ in range(n_cross_seed):
            attrs.append(CaseAttribution(
                case_id=f"CASE_{idx:03d}", direct_class=DirectClass.LOST_IN_CROSS_SEED,
                seeds_with_correct_on_front=10, seeds_with_retained_correct=3,
                representative_correct=False, valid=True, invalid_reason=None,
            ))
            idx += 1

        for _ in range(n_invalid):
            attrs.append(CaseAttribution(
                case_id=f"CASE_{idx:03d}", direct_class=DirectClass.NEVER_ON_FRONT,
                seeds_with_correct_on_front=0, seeds_with_retained_correct=0,
                representative_correct=False, valid=False,
                invalid_reason="test invalid",
            ))
            idx += 1

        return attrs

    def test_exact_historical_pass(self):
        """Exact 69/57 split => deviation 0/0 => PASS."""
        attrs = self._make_attributions(
            n_retention=69, n_generation=57,
            n_success=4, n_cross_seed=2, n_invalid=12,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.direct_retention == 69
        assert gate.direct_generation == 57
        assert gate.retention_deviation == 0
        assert gate.generation_deviation == 0
        assert gate.threshold_triggered is False
        assert gate.e2b_69_57_hook == "PASS"

    def test_deviation_9_pass(self):
        """Deviation of 9 in both => PASS (within 10)."""
        attrs = self._make_attributions(
            n_retention=60,  # 69 - 9 = 60
            n_generation=48,  # 57 - 9 = 48
            n_success=36,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.retention_deviation == 9
        assert gate.generation_deviation == 9
        assert gate.threshold_triggered is False
        assert gate.e2b_69_57_hook == "PASS"

    def test_deviation_10_pass(self):
        """Deviation of exactly 10 => PASS.

        "more than 10 cases" means > 10, not >= 10. So deviation 10 is within
        tolerance.
        """
        attrs = self._make_attributions(
            n_retention=79,  # 69 + 10 = 79
            n_generation=47,  # 57 - 10 = 47
            n_success=18,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.retention_deviation == 10
        assert gate.generation_deviation == 10
        assert gate.threshold_triggered is False
        assert gate.e2b_69_57_hook == "PASS"

    def test_deviation_11_fail(self):
        """Deviation of 11 in retention => FAIL (more than 10)."""
        attrs = self._make_attributions(
            n_retention=80,  # 69 + 11 = 80
            n_generation=57,
            n_success=7,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.retention_deviation == 11
        assert gate.generation_deviation == 0
        assert gate.threshold_triggered is True
        assert gate.e2b_69_57_hook == "FAIL"

    def test_generation_deviation_11_fail(self):
        """Deviation of 11 in generation only => FAIL."""
        attrs = self._make_attributions(
            n_retention=69,
            n_generation=68,  # 57 + 11 = 68
            n_success=7,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.retention_deviation == 0
        assert gate.generation_deviation == 11
        assert gate.threshold_triggered is True
        assert gate.e2b_69_57_hook == "FAIL"

    def test_both_deviations_large_fail(self):
        """Both deviations exceed 10 => FAIL."""
        attrs = self._make_attributions(
            n_retention=90,  # 69 + 21 = 90
            n_generation=80,  # 57 + 23 = 80
            n_success=0,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.retention_deviation == 21
        assert gate.generation_deviation == 23
        assert gate.threshold_triggered is True
        assert gate.e2b_69_57_hook == "FAIL"

    def test_retention_deviation_10_generation_11_fail(self):
        """Retention deviation 10 (ok), generation deviation 11 (exceeds) => FAIL.

        Only one needs to exceed for the threshold to trigger.
        """
        attrs = self._make_attributions(
            n_retention=79,  # deviation 10
            n_generation=68,  # deviation 11
            n_success=0,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.retention_deviation == 10
        assert gate.generation_deviation == 11
        assert gate.threshold_triggered is True
        assert gate.e2b_69_57_hook == "FAIL"

    def test_third_class_counts(self):
        """DIRECT_THIRD_CLASS = SUCCESS + LOST_IN_CROSS_SEED."""
        attrs = self._make_attributions(
            n_retention=69, n_generation=57,
            n_success=4, n_cross_seed=2,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.direct_third_class == 6  # 4 + 2

    def test_invalid_cases_not_counted(self):
        """Invalid cases are excluded from classification counts."""
        attrs = self._make_attributions(
            n_retention=69, n_generation=57,
            n_success=4, n_cross_seed=2, n_invalid=12,
        )
        gate = evaluate_gate_1(attrs)
        assert gate.invalid_cases == 12
        assert gate.direct_retention == 69
        assert gate.direct_generation == 57
        assert gate.direct_third_class == 6

    def test_output_format(self):
        """Verify the to_dict output has all required keys."""
        attrs = self._make_attributions(
            n_retention=69, n_generation=57,
            n_success=4, n_cross_seed=2,
        )
        gate = evaluate_gate_1(attrs)
        d = gate.to_dict()
        assert set(d.keys()) == {
            "DIRECT_RETENTION",
            "DIRECT_GENERATION",
            "DIRECT_THIRD_CLASS",
            "INVALID_CASES",
            "HISTORICAL_RETENTION",
            "HISTORICAL_GENERATION",
            "RETENTION_DEVIATION",
            "GENERATION_DEVIATION",
            "FROZEN_MATERIAL_THRESHOLD",
            "THRESHOLD_TRIGGERED",
            "E2B_69_57_HOOK",
        }
        assert d["HISTORICAL_RETENTION"] == 69
        assert d["HISTORICAL_GENERATION"] == 57
        assert d["FROZEN_MATERIAL_THRESHOLD"] == 10
        assert d["THRESHOLD_TRIGGERED"] in ("YES", "NO")
        assert d["E2B_69_57_HOOK"] in ("PASS", "FAIL")

    def test_zero_valid_cases(self):
        """Edge: all cases invalid."""
        attrs = self._make_attributions(n_retention=0, n_generation=0, n_invalid=10)
        gate = evaluate_gate_1(attrs)
        assert gate.direct_retention == 0
        assert gate.direct_generation == 0
        assert gate.retention_deviation == 69
        assert gate.generation_deviation == 57
        assert gate.threshold_triggered is True
        assert gate.e2b_69_57_hook == "FAIL"


# -----------------------------------------------------------------------
# Tests: CaseAttribution.to_dict output format
# -----------------------------------------------------------------------

class TestCaseAttributionFormat:

    def test_output_keys(self):
        """Verify per-case output has all required keys."""
        a = CaseAttribution(
            case_id="TEST_001",
            direct_class=DirectClass.LOST_IN_RETENTION,
            seeds_with_correct_on_front=5,
            seeds_with_retained_correct=0,
            representative_correct=False,
            valid=True,
            invalid_reason=None,
        )
        d = a.to_dict()
        assert set(d.keys()) == {
            "case_id",
            "direct_class",
            "seeds_with_correct_on_front",
            "seeds_with_retained_correct",
            "representative_correct",
            "valid",
            "invalid_reason",
        }
        assert d["direct_class"] == "LOST_IN_RETENTION"
        assert d["valid"] is True
        assert d["invalid_reason"] is None

    def test_all_classes_serializable(self):
        """Every DirectClass value serializes to its string name."""
        for cls in DirectClass:
            a = CaseAttribution(
                case_id="X", direct_class=cls,
                seeds_with_correct_on_front=0,
                seeds_with_retained_correct=0,
                representative_correct=False,
                valid=True, invalid_reason=None,
            )
            d = a.to_dict()
            assert d["direct_class"] == cls.value


# -----------------------------------------------------------------------
# Tests: no historical labels used
# -----------------------------------------------------------------------

class TestHistoricalLabelsNotUsed:
    """Verify the classifier does not use any v1 decomposition labels."""

    def test_classification_uses_only_front_and_truth(self):
        """classify_case takes only front results, representative, and truth.
        It does not accept or use any historical label parameter."""
        import inspect
        sig = inspect.signature(classify_case)
        params = set(sig.parameters.keys())
        # Must not have any parameter named like historical/v1/decomposition
        assert "historical_label" not in params
        assert "v1_class" not in params
        assert "decomposition_class" not in params
        # Must have exactly these parameters
        assert params == {
            "case_id",
            "seed_results",
            "representative_expression",
            "truth_support",
            "truth_family",
        }


# -----------------------------------------------------------------------
# Tests: evaluator SHA-256
# -----------------------------------------------------------------------

class TestEvaluatorHash:

    def test_sha256_is_deterministic(self):
        """Same script content yields same hash."""
        from e2b_direct_evaluator import compute_evaluator_sha256
        h1 = compute_evaluator_sha256()
        h2 = compute_evaluator_sha256()
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest length

    def test_sha256_is_hex(self):
        """Hash is a valid hex string."""
        from e2b_direct_evaluator import compute_evaluator_sha256
        h = compute_evaluator_sha256()
        int(h, 16)  # should not raise


# -----------------------------------------------------------------------
# Tests: constants match primary sources
# -----------------------------------------------------------------------

class TestFrozenConstants:

    def test_historical_retention(self):
        assert HISTORICAL_RETENTION == 69

    def test_historical_generation(self):
        assert HISTORICAL_GENERATION == 57

    def test_threshold(self):
        assert FROZEN_MATERIAL_THRESHOLD == 10

    def test_seeds_per_case(self):
        assert SEEDS_PER_CASE == 30
