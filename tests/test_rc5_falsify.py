"""A3.5 section 6, as amended by section 6.9: the per-case falsification executor.

Hand-built cases only.  No benchmark case is generated, no PySR run, no truth.
"""
from __future__ import annotations

import ast
import inspect

import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark.calibration_contract import (
    CONSTRUCTION_ALLOCATION,
    EXCLUDED_CONSTRUCTIONS,
)
from muru.paper_benchmark.registry import ENERGY_GRID
from muru.paper_benchmark.rc5_falsify import (
    F1_RERUN_COUNT,
    F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX,
    F4_PASS_BAR,
    F7_LOSO_FOLDS,
    F9_CALIBRATION_STATUS,
    F9_FOLDS,
    F10_CONSTRUCTIONS,
    REQUIRED_HARD_GATES,
    CaseFalsification,
    FalsificationInputs,
    affine_refit_r2,
    candidate_test_r2,
    run_f1_reproducibility,
    run_f4_compound_holdout,
    run_f7_influence_drop,
    run_f9_energy_subset,
    run_f10_negative_control,
    run_falsification,
)
from muru.paper_benchmark.structural_acceptance import (
    SECONDARY_REPORTED_RUNGS,
    FalsificationResult,
    FalsificationRung,
)

N_SCAFFOLDS = 30
PER_SCAFFOLD = 6
N = N_SCAFFOLDS * PER_SCAFFOLD
THRESHOLD = {c: 0.10 for c in range(1, 21)}
MU_INF, PHI_P = 0.22, 1.45


def _splits() -> list[str]:
    by_group = ["train"] * 20 + ["validation"] * 5 + ["test"] * 5
    return [by_group[i // PER_SCAFFOLD] for i in range(N)]


def _inputs(expression: str = "mass", noise: float = 0.0, seed: int = 11):
    """A case whose target genuinely depends on `mass`, so a real form scores."""
    rng = np.random.default_rng(seed)
    mass = rng.uniform(200.0, 400.0, N)
    g = 1.0 + 0.004 * (mass - 300.0) + rng.normal(0.0, noise, N)
    g = np.clip(g, 0.4, 2.5)

    compounds = pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N)],
            "scaffold_id": [f"S{i // PER_SCAFFOLD:02d}" for i in range(N)],
            "split": _splits(),
            "mass": mass,
            "descriptor": rng.uniform(0, 1, N),
            "descriptor2": rng.uniform(0, 1, N),
            "distractor": rng.normal(0, 1, N),
            "correlated_distractor": rng.normal(0, 1, N),
        }
    )
    energies = np.asarray(ENERGY_GRID, dtype=float)
    u = (energies[None, :] / 45.0) / g[:, None]
    mu = MU_INF + (1 - MU_INF) * np.exp(-(u**PHI_P))
    rows = [
        {"compound_id": c, "energy": float(e), "mu": float(mu[i, j])}
        for i, c in enumerate(compounds.compound_id)
        for j, e in enumerate(energies)
    ]
    return FalsificationInputs(
        case_id="PB|synthetic|F01|r000",
        discovered_expression_string=expression,
        complexity=3,
        effective_support=frozenset({"mass"}),
        target=g,
        compounds=compounds,
        trajectories=pd.DataFrame(rows),
        null_threshold=THRESHOLD,
    )


# =======================================================================
# Section 6.0 -- the affine refit convention
# =======================================================================

def test_the_refit_has_exactly_two_free_parameters():
    inputs = _inputs()
    design = inputs.design()
    train = inputs.mask("train")
    test = inputs.mask("test")
    # y = a + b*mass reproduces the planted linear target, so R2 is ~1.
    value = affine_refit_r2("mass", design, inputs.target, train, test)
    assert value > 0.99
    # An affine reparameterisation of the SAME form is absorbed by (a, b), so
    # the two score identically -- that is exactly two free parameters.
    scaled = affine_refit_r2("3.0 * mass + 7.0", design, inputs.target, train, test)
    assert scaled == pytest.approx(value, abs=1e-9)


def test_the_refit_never_fits_on_the_rows_it_evaluates():
    inputs = _inputs()
    design = inputs.design()
    train = inputs.mask("train")
    test = inputs.mask("test")

    baseline = affine_refit_r2("mass", design, inputs.target, train, test)
    # Corrupting the evaluation rows' covariates must change the score; if the
    # fit had seen them it could compensate.
    corrupted = design.copy()
    corrupted[test, 0] = corrupted[test, 0] * -1.0
    after = affine_refit_r2("mass", corrupted, inputs.target, train, test)
    assert after != pytest.approx(baseline)


def test_zero_variance_on_the_evaluation_rows_is_minus_infinity():
    inputs = _inputs()
    design = inputs.design()
    flat = np.array(inputs.target, dtype=float)
    flat[inputs.mask("test")] = 1.0
    assert affine_refit_r2(
        "mass", design, flat, inputs.mask("train"), inputs.mask("test")
    ) == float("-inf")


def test_a_singular_design_is_minus_infinity_not_a_skip():
    inputs = _inputs()
    design = inputs.design()
    # A constant form has no slope: the design matrix is singular.
    assert affine_refit_r2(
        "1.0", design, inputs.target, inputs.mask("train"), inputs.mask("test")
    ) == float("-inf")


def test_an_unparseable_form_is_minus_infinity():
    inputs = _inputs()
    assert affine_refit_r2(
        "this is ( not", inputs.design(), inputs.target,
        inputs.mask("train"), inputs.mask("test"),
    ) == float("-inf")


# =======================================================================
# candidate_test_r2 -- computed once, not a rung
# =======================================================================

def test_candidate_test_r2_produces_no_rung_result():
    value = candidate_test_r2(_inputs())
    assert isinstance(value, float)
    assert not isinstance(value, FalsificationResult)


def test_candidate_test_r2_equals_the_train_to_test_affine_refit():
    inputs = _inputs()
    assert candidate_test_r2(inputs) == affine_refit_r2(
        inputs.discovered_expression_string,
        inputs.design(),
        inputs.target,
        inputs.mask("train"),
        inputs.mask("test"),
    )


def test_f5_has_no_procedure_and_no_rung():
    import muru.paper_benchmark.rc5_falsify as module

    names = {n for n in dir(module) if "f5" in n.lower()}
    assert not names
    assert "F5_SCAFFOLD_HOLDOUT" not in {r.value for r in FalsificationRung}


# =======================================================================
# F1
# =======================================================================

def test_f1_passes_on_an_identical_re_execution():
    inputs = _inputs()
    outcome = run_f1_reproducibility(inputs, lambda: inputs.discovered_expression_string)
    assert outcome.result is FalsificationResult.PASS
    assert outcome.detail["replicates"] == F1_RERUN_COUNT == 1


def test_f1_passes_on_a_positive_scale_multiple_but_not_on_a_different_form():
    inputs = _inputs("mass * descriptor")
    assert run_f1_reproducibility(
        inputs, lambda: "3.0 * (mass * descriptor)"
    ).result is FalsificationResult.PASS
    assert run_f1_reproducibility(
        inputs, lambda: "mass + descriptor"
    ).result is FalsificationResult.FAIL


def test_f1_preserves_exponent_and_operator_identity():
    """Section 6.1 / section 13 row 12: scoped to affine-coefficient position."""
    inputs = _inputs("square(mass)")
    for different in ("cube(mass)", "sqrt(mass)", "inv(mass)", "mass"):
        assert run_f1_reproducibility(
            inputs, lambda d=different: d
        ).result is FalsificationResult.FAIL, different


def test_f1_fails_when_the_re_execution_retains_nothing():
    inputs = _inputs()
    assert run_f1_reproducibility(inputs, lambda: None).result is FalsificationResult.FAIL


def test_an_execution_failure_resolves_to_fail_never_to_not_applicable():
    inputs = _inputs()

    def boom():
        raise RuntimeError("engine died")

    outcome = run_f1_reproducibility(inputs, boom)
    assert outcome.result is FalsificationResult.FAIL
    assert outcome.result is not FalsificationResult.NOT_APPLICABLE
    assert outcome.detail["error_type"] == "RuntimeError"


# =======================================================================
# F4
# =======================================================================

def test_f4_holds_out_one_compound_per_training_scaffold_at_index_5():
    inputs = _inputs()
    outcome = run_f4_compound_holdout(inputs)
    assert F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX == 5
    assert outcome.detail["evaluation_rows"] == 20      # one per training scaffold
    assert outcome.detail["fit_rows"] == 100            # 120 - 20
    assert outcome.detail["replicates"] == 1


def test_f4_passes_a_genuine_form_and_fails_a_null_one():
    assert run_f4_compound_holdout(_inputs("mass")).result is FalsificationResult.PASS
    assert F4_PASS_BAR == 0.0
    weak = run_f4_compound_holdout(_inputs("distractor"))
    assert weak.result is FalsificationResult.FAIL
    assert weak.metric <= 0.0


def test_f4_has_no_randomness():
    inputs = _inputs()
    first = run_f4_compound_holdout(inputs)
    second = run_f4_compound_holdout(inputs)
    assert first.metric == second.metric


# =======================================================================
# F7
# =======================================================================

def test_f7_runs_exactly_twenty_exhaustive_loso_folds_on_fixed_test_rows():
    outcome = run_f7_influence_drop(_inputs())
    assert outcome.detail["replicates"] == 20 == F7_LOSO_FOLDS
    assert len(outcome.detail["per_fold_r2"]) == 20


def test_f7_is_the_minimum_over_folds_and_reads_the_frozen_bar():
    inputs = _inputs()
    outcome = run_f7_influence_drop(inputs)
    assert outcome.metric == min(outcome.detail["per_fold_r2"])
    assert outcome.detail["bar"] == THRESHOLD[inputs.complexity]
    assert outcome.result is FalsificationResult.PASS


def test_f7_fails_a_form_that_cannot_clear_the_bar():
    outcome = run_f7_influence_drop(_inputs("distractor"))
    assert outcome.result is FalsificationResult.FAIL


def test_f7_rejects_the_phase3_influence_drop_fraction():
    import muru.paper_benchmark.rc5_falsify as module

    text = open(module.__file__, encoding="utf-8").read()
    tree = ast.parse(text)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "INFLUENCE_DROP_FRACTION" not in names
    assert "N_PERMUTATIONS_F10" not in names


# =======================================================================
# F9 -- computed, reported, never gating
# =======================================================================

def test_f9_runs_exactly_six_leave_one_energy_out_folds():
    outcome = run_f9_energy_subset(_inputs())
    assert outcome.detail["replicates"] == 6 == F9_FOLDS == len(ENERGY_GRID)
    assert len(outcome.detail["per_fold_r2"]) == 6


def test_f9_refits_the_g_pipeline_which_is_what_makes_it_different_from_f7():
    outcome = run_f9_energy_subset(_inputs())
    assert outcome.detail["refits_the_g_pipeline"] is True
    assert outcome.detail["calibration_status"] == F9_CALIBRATION_STATUS
    assert F9_CALIBRATION_STATUS == "NOT_PROVEN_FOR_HARD_GATE"


def test_f9_uses_no_hand_named_energy_subset():
    import muru.paper_benchmark.rc5_falsify as module

    text = open(module.__file__, encoding="utf-8").read()
    # The struck five, two of which are hard-coded Phase 3 constants.
    for struck in ("{15, 45, 75}", "[15, 45, 75]", "(15, 45, 75)",
                   "{30, 60, 90}", "[30, 60, 90]", "(30, 60, 90)"):
        assert struck not in text


def test_f9_is_not_a_hard_gate_and_cannot_reach_the_gate8_mapping():
    assert FalsificationRung.F9_ENERGY_SUBSET not in REQUIRED_HARD_GATES
    assert FalsificationRung.F9_ENERGY_SUBSET in SECONDARY_REPORTED_RUNGS
    with pytest.raises(ValueError, match="not hard gates"):
        CaseFalsification(
            hard={
                **{r: FalsificationResult.PASS for r in REQUIRED_HARD_GATES},
                FalsificationRung.F9_ENERGY_SUBSET: FalsificationResult.FAIL,
            },
            f9_stress_test_result=FalsificationResult.FAIL,
            f9_stress_test_metric=-1.0,
            metrics={},
        )


def test_a_failing_f9_leaves_an_otherwise_passing_case_passing():
    from muru.paper_benchmark.structural_acceptance import check_gate8

    result = CaseFalsification(
        hard={r: FalsificationResult.PASS for r in REQUIRED_HARD_GATES},
        f9_stress_test_result=FalsificationResult.FAIL,
        f9_stress_test_metric=-9.0,
        metrics={},
    )
    assert check_gate8(result.hard) is True
    assert result.f9_stress_test_result is FalsificationResult.FAIL


# =======================================================================
# F10
# =======================================================================

def test_f10_uses_exactly_the_three_frozen_constructions():
    outcome = run_f10_negative_control(_inputs())
    assert outcome.detail["replicates"] == 3 == len(CONSTRUCTION_ALLOCATION)
    assert set(outcome.detail["per_construction_r2"]) == set(CONSTRUCTION_ALLOCATION)
    assert set(F10_CONSTRUCTIONS) == set(CONSTRUCTION_ALLOCATION)


def test_f10_excludes_within_compound_energy_permutation():
    outcome = run_f10_negative_control(_inputs())
    assert outcome.detail["excluded_constructions"] == sorted(EXCLUDED_CONSTRUCTIONS)
    assert "within_compound_energy_permutation" in EXCLUDED_CONSTRUCTIONS
    assert "within_compound_energy_permutation" not in F10_CONSTRUCTIONS


def test_f10_passes_when_corruption_destroys_apparent_validity():
    outcome = run_f10_negative_control(_inputs("mass"))
    assert outcome.result is FalsificationResult.PASS
    assert outcome.metric <= outcome.detail["bar"]


def test_f10_is_a_bar_not_to_clear():
    # With a threshold of -inf every corruption "clears" it, so the control
    # must FAIL: the pipeline reported apparent validity on broken data.
    inputs = _inputs("mass")
    permissive = FalsificationInputs(
        case_id=inputs.case_id,
        discovered_expression_string=inputs.discovered_expression_string,
        complexity=inputs.complexity,
        effective_support=inputs.effective_support,
        target=inputs.target,
        compounds=inputs.compounds,
        trajectories=inputs.trajectories,
        null_threshold={c: -1e9 for c in range(1, 21)},
    )
    assert run_f10_negative_control(permissive).result is FalsificationResult.FAIL


def test_f10_is_deterministic_under_its_derived_seed():
    inputs = _inputs()
    first = run_f10_negative_control(inputs)
    second = run_f10_negative_control(inputs)
    assert first.detail["per_construction_r2"] == second.detail["per_construction_r2"]


def test_f10_seeds_are_namespaced_per_case_and_per_construction():
    tree = ast.parse(inspect.getsource(
        __import__("muru.paper_benchmark.rc5_falsify", fromlist=["_corrupt"])._corrupt
    ))
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "derive_seed"
    ]
    assert calls, "F10 must derive its randomness through derive_seed"
    literals = [a.value for c in calls for a in c.args if isinstance(a, ast.Constant)]
    assert "F10_NEGATIVE_CONTROL" in literals


# =======================================================================
# The executor
# =======================================================================

def test_the_executor_returns_four_hard_gates_and_one_reported_secondary():
    inputs = _inputs("mass")
    result = run_falsification(inputs, lambda: inputs.discovered_expression_string)
    assert set(result.hard) == set(REQUIRED_HARD_GATES)
    assert len(result.hard) == 4
    assert result.f9_stress_test_result in (
        FalsificationResult.PASS, FalsificationResult.FAIL
    )
    assert isinstance(result.f9_stress_test_metric, float)
    assert result.f9_calibration_status == "NOT_PROVEN_FOR_HARD_GATE"


def test_a_missing_hard_gate_is_refused_by_the_container():
    with pytest.raises(ValueError, match="hard gate results missing"):
        CaseFalsification(
            hard={FalsificationRung.F1_REPRODUCIBILITY: FalsificationResult.PASS},
            f9_stress_test_result=FalsificationResult.PASS,
            f9_stress_test_metric=0.0,
            metrics={},
        )


def test_no_rung_may_emit_not_applicable():
    from muru.paper_benchmark.rc5_falsify import RungOutcome

    with pytest.raises(ValueError, match="NOT_APPLICABLE"):
        RungOutcome(
            FalsificationRung.F4_COMPOUND_HOLDOUT,
            FalsificationResult.NOT_APPLICABLE,
            0.0,
            {},
        )


# =======================================================================
# Truth-blindness and partition-blindness (section 6.0)
# =======================================================================

def test_the_input_type_carries_no_truth_and_no_partition():
    fields = set(FalsificationInputs.__dataclass_fields__)
    for forbidden in (
        "truth", "truth_family", "truth_support", "partition_label", "partition",
        "family_id", "variant", "mathematical_family", "g_by_compound",
        "m0_adequacy_truth", "scalar_truth_defined", "symbolic_truth_kind",
    ):
        assert forbidden not in fields


def test_no_falsification_function_reads_partition_label():
    import muru.paper_benchmark.rc5_falsify as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in (
        "partition_label", "partition", "resolve_case_id", "TruthRecord",
        "truth_family", "mathematical_family", "classify_discovered_family",
        "active_variables", "g_by_compound",
    ):
        assert forbidden not in names, f"a falsification path reaches {forbidden}"


def test_case_id_is_used_only_as_a_seed_namespace_and_a_key():
    """Section 6.0: ``case_id`` may be a ``derive_seed`` namespace component
    and a record key, and may never branch rung behaviour.

    Traced one hop: every ``.case_id`` read must be an argument to
    ``derive_seed`` or to ``_corrupt``, and ``_corrupt``'s own ``case_id``
    parameter must reach nothing but ``derive_seed``.
    """
    import muru.paper_benchmark.rc5_falsify as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())

    permitted_sinks = {"derive_seed", "_corrupt"}
    sink_args = {
        id(a)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") in permitted_sinks
        for a in n.args
    }
    reads = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr == "case_id"
    ]
    assert reads
    for read in reads:
        assert id(read) in sink_args, (
            "case_id is read somewhere other than a seed-derivation call"
        )

    corrupt = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_corrupt"
    )
    derive_args = {
        id(a)
        for n in ast.walk(corrupt)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "derive_seed"
        for a in n.args
    }
    uses = [
        n for n in ast.walk(corrupt)
        if isinstance(n, ast.Name) and n.id == "case_id" and isinstance(n.ctx, ast.Load)
    ]
    assert uses
    for use in uses:
        assert id(use) in derive_args, "_corrupt uses case_id outside derive_seed"

    # And no comparison anywhere branches on it.
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            for operand in operands:
                if isinstance(operand, ast.Attribute):
                    assert operand.attr != "case_id"
                if isinstance(operand, ast.Name):
                    assert operand.id != "case_id"


def test_the_same_case_content_scores_identically_under_any_case_id():
    """Partition identity cannot change a rung's answer.

    Only F10 consumes case_id at all, and only as a seed namespace, so a
    different label changes its draw but nothing about the other four.
    """
    base = _inputs("mass")
    relabelled = FalsificationInputs(
        case_id="PB|held_out|F01|r000",
        discovered_expression_string=base.discovered_expression_string,
        complexity=base.complexity,
        effective_support=base.effective_support,
        target=base.target,
        compounds=base.compounds,
        trajectories=base.trajectories,
        null_threshold=base.null_threshold,
    )
    assert run_f4_compound_holdout(base).metric == run_f4_compound_holdout(relabelled).metric
    assert run_f7_influence_drop(base).metric == run_f7_influence_drop(relabelled).metric
    assert run_f9_energy_subset(base).metric == run_f9_energy_subset(relabelled).metric
    assert (
        run_f1_reproducibility(base, lambda: "mass").result
        is run_f1_reproducibility(relabelled, lambda: "mass").result
    )


def test_no_rung_applies_a_validity_floor_or_skips():
    import muru.paper_benchmark.rc5_falsify as module

    text = open(module.__file__, encoding="utf-8").read()
    tree = ast.parse(text)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    for forbidden in ("MIN_ROWS", "MIN_COMPOUNDS", "MIN_ENERGIES", "MIN_TEST_R2"):
        assert forbidden not in names
    # Every rung reports its replicate count, and none of them is conditional.
    inputs = _inputs()
    assert run_f7_influence_drop(inputs).detail["replicates"] == F7_LOSO_FOLDS
    assert run_f9_energy_subset(inputs).detail["replicates"] == F9_FOLDS
    assert run_f10_negative_control(inputs).detail["replicates"] == 3
