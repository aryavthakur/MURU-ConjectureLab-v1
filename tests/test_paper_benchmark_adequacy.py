"""Amendment A1 contract tests.

These tests exercise the M0/M1/M2/M3 adequacy DECISION LOGIC using constructed
outcome records only.  They never generate, load, or score a Development or
Held-out benchmark case.
"""
import pytest

from muru.paper_benchmark.adequacy import (
    ADEQUACY_MODELS,
    COARSE_LOG_G_POINTS,
    COARSE_LOG_SHAPE_POINTS,
    DETECTORS,
    E_REF,
    LOG_G_BOUNDS,
    LOG_SHAPE_BOUNDS,
    MIN_EVALUABLE_COMPOUNDS,
    MIN_OBSERVED_ENERGIES,
    MIN_PRACTICAL_WINS,
    MIN_VERTICAL_AMPLITUDE,
    MU_CEIL,
    MU_FLOOR,
    N_TEST_COMPOUNDS_EXPECTED,
    PRACTICAL_WIN_RATIO,
    REFINEMENT_POINTS,
    REFINEMENT_ROUNDS,
    REFINEMENT_SHRINK,
    CaseAdequacyStatus,
    CompoundContrastRecord,
    CompoundContrastStatus,
    ContractFailure,
    adequacy_satisfies_g1,
    classify_compound_contrast,
    decide_case_adequacy,
    detector_sensitivity_success,
    directional_null_tail,
    evaluate_contrast,
    is_practical_win,
    sensitivity_score,
)

M1_CASE = "PB|held_out|F13|r000"
M2_CASE = "PB|held_out|F14|r000"
M3_CASE = "PB|held_out|F15|r000"
COMBINED_CASE = "PB|held_out|F16|r000"
M0_CASE = "PB|held_out|F01|r000"


def _record(index, detector, *, mae_m0=1.0, mae_alt=1.0, energies=6, state="OK", boundary=False):
    return CompoundContrastRecord(
        compound_id=f"C{index:03d}",
        detector=detector,
        observed_energy_count=energies,
        mae_m0=mae_m0,
        mae_alt=mae_alt,
        execution_state=state,
        unresolved_boundary=boundary,
    )


def _records(detector, *, wins=0, losses=0, **kinds):
    """Build exactly 30 constructed records for one M0-vs-Mk contrast."""
    out, index = [], 0
    for _ in range(wins):
        out.append(_record(index, detector, mae_m0=1.0, mae_alt=0.5))
        index += 1
    for _ in range(losses):
        out.append(_record(index, detector, mae_m0=1.0, mae_alt=1.0))
        index += 1
    for kind, count in kinds.items():
        for _ in range(count):
            if kind == "insufficient":
                out.append(_record(index, detector, energies=4))
            elif kind == "boundary":
                out.append(_record(index, detector, boundary=True))
            else:
                out.append(_record(index, detector, state=kind.upper()))
            index += 1
    if len(out) != N_TEST_COMPOUNDS_EXPECTED:
        raise AssertionError("constructed contrast must hold exactly 30 records")
    return out


def _contrasts(**per_detector):
    return {detector: _records(detector, **per_detector.get(detector, {"losses": 30})) for detector in DETECTORS}


# --------------------------------------------------------------------------
# Section 6 - compound practical-win statistic and frozen tolerance semantics
# --------------------------------------------------------------------------


def test_practical_win_requires_at_least_a_ten_percent_error_reduction():
    assert is_practical_win(1.0, 0.90)
    assert is_practical_win(1.0, 0.5)
    assert not is_practical_win(1.0, 0.9000000000000002)
    assert not is_practical_win(1.0, 0.95)


def test_an_exact_tie_is_never_a_practical_win():
    assert not is_practical_win(1.0, 1.0)
    assert not is_practical_win(0.25, 0.25)


def test_a_perfect_m0_fit_cannot_be_beaten_by_a_zero_error_alternative():
    assert not is_practical_win(0.0, 0.0)


def test_a_negative_loss_is_a_contract_failure():
    with pytest.raises(ContractFailure):
        is_practical_win(1.0, -0.1)


# --------------------------------------------------------------------------
# Sections 10, 11, 12 - compound-level status
# --------------------------------------------------------------------------


def test_five_energy_f04_compound_is_adequacy_evaluable():
    status = classify_compound_contrast(_record(0, "M1", energies=5, mae_m0=1.0, mae_alt=0.5))
    assert status is CompoundContrastStatus.PRACTICAL_WIN


def test_four_energy_compound_is_insufficient_data():
    status = classify_compound_contrast(_record(0, "M1", energies=4, mae_m0=1.0, mae_alt=0.5))
    assert status is CompoundContrastStatus.INSUFFICIENT_DATA


def test_unresolved_boundary_contact_is_neither_a_win_nor_a_loss():
    status = classify_compound_contrast(_record(0, "M2", boundary=True, mae_m0=1.0, mae_alt=0.1))
    assert status is CompoundContrastStatus.BOUNDARY_LIMITED


def test_resolved_boundary_contact_stays_evaluable():
    record = CompoundContrastRecord("C000", "M2", 6, 1.0, 0.5, boundary_contact=True, unresolved_boundary=False)
    assert classify_compound_contrast(record) is CompoundContrastStatus.PRACTICAL_WIN


def test_execution_failures_map_to_their_own_compound_states():
    assert classify_compound_contrast(_record(0, "M1", state="TIMEOUT")) is CompoundContrastStatus.TIMEOUT
    assert classify_compound_contrast(_record(0, "M1", state="MODEL_FIT_FAILURE")) is CompoundContrastStatus.MODEL_FIT_FAILURE
    assert classify_compound_contrast(_record(0, "M1", state="NUMERICAL_FAILURE")) is CompoundContrastStatus.NUMERICAL_FAILURE


def test_non_finite_loss_is_a_numerical_failure_not_a_loss():
    assert classify_compound_contrast(_record(0, "M1", mae_alt=float("nan"))) is CompoundContrastStatus.NUMERICAL_FAILURE
    assert classify_compound_contrast(_record(0, "M1", mae_m0=None)) is CompoundContrastStatus.NUMERICAL_FAILURE


# --------------------------------------------------------------------------
# Section 7 - case-level detector firing
# --------------------------------------------------------------------------


def test_nineteen_wins_of_thirty_does_not_fire():
    result = evaluate_contrast("M1", _records("M1", wins=19, losses=11))
    assert result.evaluable == 30 and result.practical_wins == 19
    assert not result.fired


def test_twenty_wins_of_thirty_fires():
    result = evaluate_contrast("M1", _records("M1", wins=20, losses=10))
    assert result.practical_wins == 20
    assert result.fired


def test_twenty_wins_with_only_twenty_three_evaluable_is_indeterminate():
    result = evaluate_contrast("M1", _records("M1", wins=20, losses=3, boundary=7))
    assert result.evaluable == 23 and result.practical_wins == 20
    assert not result.evaluable_sufficient
    assert not result.fired


def test_twenty_four_evaluable_with_twenty_wins_fires():
    result = evaluate_contrast("M1", _records("M1", wins=20, losses=4, boundary=6))
    assert result.evaluable == MIN_EVALUABLE_COMPOUNDS and result.practical_wins == MIN_PRACTICAL_WINS
    assert result.evaluable_sufficient
    assert result.fired


def test_more_than_thirty_test_compounds_is_a_contract_failure():
    records = _records("M1", losses=30) + [_record(99, "M1")]
    with pytest.raises(ContractFailure, match="contract failure"):
        evaluate_contrast("M1", records)


def test_fewer_than_thirty_test_compounds_is_a_registry_inconsistency():
    with pytest.raises(ContractFailure, match="registry inconsistency"):
        evaluate_contrast("M1", _records("M1", losses=30)[:29])


def test_a_record_from_another_contrast_is_a_contract_failure():
    records = _records("M1", losses=30)[:29] + [_record(29, "M2")]
    with pytest.raises(ContractFailure, match="detector"):
        evaluate_contrast("M1", records)


# --------------------------------------------------------------------------
# Sections 8 and 12 - case adequacy status
# --------------------------------------------------------------------------


def test_no_detector_fires_with_all_contrasts_evaluable_gives_m0_not_rejected():
    result = decide_case_adequacy(M0_CASE, _contrasts())
    assert result.status is CaseAdequacyStatus.M0_NOT_REJECTED
    assert result.m0_not_rejected
    assert result.fired == ()


def test_m1_only_gives_m0_rejected_m1():
    result = decide_case_adequacy(M1_CASE, _contrasts(M1={"wins": 20, "losses": 10}))
    assert result.status is CaseAdequacyStatus.M0_REJECTED_M1
    assert result.fired == ("M1",)


def test_m2_only_gives_m0_rejected_m2():
    result = decide_case_adequacy(M2_CASE, _contrasts(M2={"wins": 20, "losses": 10}))
    assert result.status is CaseAdequacyStatus.M0_REJECTED_M2


def test_m3_only_gives_m0_rejected_m3():
    result = decide_case_adequacy(M3_CASE, _contrasts(M3={"wins": 20, "losses": 10}))
    assert result.status is CaseAdequacyStatus.M0_REJECTED_M3


def test_multiple_alternatives_give_m0_rejected_multiple():
    result = decide_case_adequacy(
        COMBINED_CASE,
        _contrasts(M1={"wins": 22, "losses": 8}, M3={"wins": 25, "losses": 5}),
    )
    assert result.status is CaseAdequacyStatus.M0_REJECTED_MULTIPLE
    assert result.fired == ("M1", "M3")


def test_model_fit_failure_below_the_floor_is_not_m0_acceptance():
    result = decide_case_adequacy(M0_CASE, _contrasts(M2={"losses": 23, "model_fit_failure": 7}))
    assert result.status is CaseAdequacyStatus.MODEL_FIT_FAILURE
    assert not result.m0_not_rejected


def test_timeout_below_the_floor_is_not_m0_acceptance():
    result = decide_case_adequacy(M0_CASE, _contrasts(M3={"losses": 23, "timeout": 7}))
    assert result.status is CaseAdequacyStatus.TIMEOUT
    assert not result.m0_not_rejected


def test_boundary_limited_case_below_the_evaluability_floor_is_not_m0_acceptance():
    result = decide_case_adequacy(M0_CASE, _contrasts(M1={"losses": 23, "boundary": 7}))
    assert result.status is CaseAdequacyStatus.BOUNDARY_LIMITED
    assert not result.m0_not_rejected


def test_insufficient_data_below_the_floor_is_not_m0_acceptance():
    result = decide_case_adequacy(M0_CASE, _contrasts(M1={"losses": 23, "insufficient": 7}))
    assert result.status is CaseAdequacyStatus.INSUFFICIENT_DATA
    assert not result.m0_not_rejected


def test_boundary_limitation_above_the_floor_still_decides_the_case():
    result = decide_case_adequacy(M0_CASE, _contrasts(M1={"losses": 24, "boundary": 6}))
    assert result.status is CaseAdequacyStatus.M0_NOT_REJECTED
    assert result.contrasts["M1"].status_counts["BOUNDARY_LIMITED"] == 6


def test_the_most_severe_non_evaluable_cause_names_the_indeterminate_status():
    result = decide_case_adequacy(
        M0_CASE,
        _contrasts(M1={"losses": 23, "boundary": 7}, M2={"losses": 23, "timeout": 7}),
    )
    assert result.status is CaseAdequacyStatus.TIMEOUT


def test_a_firing_detector_rejects_m0_even_when_another_contrast_is_indeterminate():
    result = decide_case_adequacy(
        M1_CASE,
        _contrasts(M1={"wins": 20, "losses": 10}, M2={"losses": 23, "timeout": 7}),
    )
    assert result.status is CaseAdequacyStatus.M0_REJECTED_M1


def test_a_missing_required_contrast_is_a_contract_failure():
    contrasts = _contrasts()
    contrasts.pop("M3")
    result = decide_case_adequacy(M0_CASE, contrasts)
    assert result.status is CaseAdequacyStatus.CONTRACT_FAILURE
    assert not result.m0_not_rejected


# --------------------------------------------------------------------------
# Section 9 - detector-specific sensitivity
# --------------------------------------------------------------------------


def test_a_wrong_alternative_firing_does_not_satisfy_the_correct_detector():
    result = decide_case_adequacy(M1_CASE, _contrasts(M2={"wins": 20, "losses": 10}))
    assert result.status is CaseAdequacyStatus.M0_REJECTED_M2
    assert not detector_sensitivity_success(result, "M1")
    assert detector_sensitivity_success(result, "M2")


def test_each_combined_case_detector_endpoint_is_scored_independently():
    result = decide_case_adequacy(
        COMBINED_CASE,
        _contrasts(M1={"wins": 20, "losses": 10}, M2={"wins": 26, "losses": 4}),
    )
    assert detector_sensitivity_success(result, "M1")
    assert detector_sensitivity_success(result, "M2")
    assert not detector_sensitivity_success(result, "M3")


def test_sensitivity_scoring_uses_the_frozen_registry_denominator_and_applicability():
    fires = decide_case_adequacy(M1_CASE, _contrasts(M1={"wins": 20, "losses": 10}))
    misfires = decide_case_adequacy(M2_CASE, _contrasts(M1={"wins": 30}))
    score = sensitivity_score("M1", [fires, misfires])

    assert score.denominator == 36
    assert score.applicable_supplied == 1
    assert score.numerator == 1
    assert not score.complete


def test_m2_and_m3_sensitivity_denominators_are_unchanged_by_the_amendment():
    assert sensitivity_score("M2", []).denominator == 24
    assert sensitivity_score("M3", []).denominator == 24


# --------------------------------------------------------------------------
# Section 13 - G1 interaction
# --------------------------------------------------------------------------


def test_only_m0_not_rejected_satisfies_the_g1_adequacy_component():
    assert adequacy_satisfies_g1(CaseAdequacyStatus.M0_NOT_REJECTED)
    for status in CaseAdequacyStatus:
        if status is not CaseAdequacyStatus.M0_NOT_REJECTED:
            assert not adequacy_satisfies_g1(status)


def test_g1_scalar_competence_reads_m0_acceptance_from_the_adequacy_status():
    from muru.paper_benchmark.analysis import CaseOutcome, m0_accepted_from_adequacy

    indeterminate = decide_case_adequacy(M0_CASE, _contrasts(M1={"losses": 23, "boundary": 7}))
    outcome = CaseOutcome(
        case_id=M0_CASE,
        g_spearman=0.99,
        trajectory_mae=0.10,
        per_energy_mean_mae=1.0,
        m0_accepted=m0_accepted_from_adequacy(indeterminate.status),
        family_recovered=True,
        unsupported_non_mass=False,
        richer_family=False,
        adversarial_flagged=True,
        null_flagged=True,
    )
    assert not outcome.scalar_competent


# --------------------------------------------------------------------------
# Section 7 - mathematical rationale for the 20-of-30 threshold
# --------------------------------------------------------------------------


def test_twenty_of_thirty_matches_the_stated_directional_null_tail():
    assert round(directional_null_tail(MIN_PRACTICAL_WINS, N_TEST_COMPOUNDS_EXPECTED), 4) == 0.0494


def test_the_fixed_win_count_never_becomes_more_permissive_as_evaluability_drops():
    tails = [directional_null_tail(MIN_PRACTICAL_WINS, n) for n in range(MIN_EVALUABLE_COMPOUNDS, N_TEST_COMPOUNDS_EXPECTED + 1)]
    assert tails == sorted(tails)
    assert max(tails) == directional_null_tail(MIN_PRACTICAL_WINS, N_TEST_COMPOUNDS_EXPECTED)


# --------------------------------------------------------------------------
# Sections 4 and 5 - frozen parameterization, bounds, and search protocol
# --------------------------------------------------------------------------


def test_m0_carries_exactly_one_compound_specific_parameter():
    assert [parameter.name for parameter in ADEQUACY_MODELS["M0"].free_parameters] == ["log_g"]


def test_each_alternative_adds_exactly_one_deviation_parameter_beyond_g():
    for detector in DETECTORS:
        names = [parameter.name for parameter in ADEQUACY_MODELS[detector].free_parameters]
        assert names[0] == "log_g"
        assert len(names) == 2
        assert ADEQUACY_MODELS[detector].reduces_to_m0_when


def test_the_alternatives_match_the_frozen_generative_deviation_axes():
    assert ADEQUACY_MODELS["M1"].deviation == "horizontal_shape"
    assert ADEQUACY_MODELS["M2"].deviation == "high_energy_vertical_asymptote"
    assert ADEQUACY_MODELS["M3"].deviation == "low_energy_vertical_plateau"
    assert set(ADEQUACY_MODELS) == {"M0", "M1", "M2", "M3"}


def test_log_g_bounds_are_inherited_from_the_frozen_training_side_support():
    import pandas as pd

    from muru.paper_benchmark.protocol import fit_training_scalar

    rows = pd.DataFrame({
        "compound_id": "T1",
        "split": "train",
        "energy": [15, 30, 45, 60, 75, 90],
        "mu": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
    })
    assert fit_training_scalar(rows).support == LOG_G_BOUNDS


def test_frozen_numeric_constants_are_pinned():
    assert (N_TEST_COMPOUNDS_EXPECTED, MIN_EVALUABLE_COMPOUNDS, MIN_PRACTICAL_WINS) == (30, 24, 20)
    assert PRACTICAL_WIN_RATIO == 0.90
    assert MIN_OBSERVED_ENERGIES == 5
    assert LOG_SHAPE_BOUNDS == (-0.6931471805599453, 0.6931471805599453)
    assert (MU_FLOOR, MU_CEIL) == (1e-4, 1 - 1e-4)
    assert MIN_VERTICAL_AMPLITUDE == 0.05
    assert E_REF == 45.0


def test_the_search_protocol_is_identical_for_every_free_dimension():
    assert (COARSE_LOG_G_POINTS, COARSE_LOG_SHAPE_POINTS) == (81, 29)
    assert (REFINEMENT_ROUNDS, REFINEMENT_POINTS, REFINEMENT_SHRINK) == (3, 21, 10)
    for model in ADEQUACY_MODELS.values():
        assert model.objective == "unweighted_sum_of_squared_mu_residuals"


def test_no_information_criterion_penalty_is_part_of_the_contract():
    import inspect

    import muru.paper_benchmark.adequacy as adequacy

    source = inspect.getsource(adequacy).upper()
    assert "AIC" not in source
    assert "BIC" not in source
