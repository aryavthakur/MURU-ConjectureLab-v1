from muru.paper_benchmark.analysis import CaseOutcome, classify_negative_control, umbrella_decision


def _outcome(case_id: str, **overrides):
    defaults = dict(case_id=case_id, g_spearman=0.9, trajectory_mae=0.5, per_energy_mean_mae=1.0, m0_accepted=True, family_recovered=True, unsupported_non_mass=False, richer_family=False, adversarial_flagged=True, null_flagged=True)
    defaults.update(overrides)
    return CaseOutcome(**defaults)


def test_negative_controls_have_separate_error_types():
    assert classify_negative_control(_outcome("PB|held_out|F07|r000", unsupported_non_mass=True)) == "false_extra_structure"
    assert classify_negative_control(_outcome("PB|held_out|F19|r008", null_flagged=False)) == "false_null_structure"
    assert classify_negative_control(_outcome("PB|held_out|F20|r000", adversarial_flagged=False)) == "false_adversarial_structure"


def test_umbrella_requires_scalar_family_and_safety_gates():
    scalar_failure = [_outcome("PB|held_out|F01|r000", g_spearman=0.1)]
    report = umbrella_decision(scalar_failure)
    assert not report.positive_claim
    assert "G1" in report.failed_gates


def test_g1_competence_requires_rank_trajectory_and_m0():
    good = _outcome("PB|held_out|F01|r000")
    assert good.scalar_competent
    assert not _outcome("PB|held_out|F01|r000", trajectory_mae=0.81).scalar_competent
    assert not _outcome("PB|held_out|F01|r000", m0_accepted=False).scalar_competent
