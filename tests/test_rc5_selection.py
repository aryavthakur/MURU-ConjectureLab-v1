"""A3.5 sections 7.1, 7.3-7.6: per-seed retention, identity, grouping,
``selection_count``, representative selection.

All fixtures are hand-built frames and hand-built candidates.  No PySR run, no
benchmark case, no truth.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.identity_contract import (
    parse_candidate,
    positive_scale_equivalent,
    template_key,
)
from muru.paper_benchmark.rc5_selection import (
    SEEDS_PER_CASE,
    RetainedCandidate,
    SeedExecutionFailure,
    SeedNoCandidate,
    SeedSelection,
    coefficient_vector,
    group_and_select,
    select_row_label,
)


def _front(rows: list[tuple[int, float]], with_score: bool = True) -> pd.DataFrame:
    """A Pareto front frame shaped like PySR's ``equations_``.

    ``score`` is computed by PySR's own rule: 0.0 for the first row, then
    ``-log(loss_k / loss_{k-1}) / (complexity_k - complexity_{k-1})``.
    """
    complexities = [c for c, _ in rows]
    losses = [l for _, l in rows]
    frame = pd.DataFrame(
        {
            "complexity": complexities,
            "loss": losses,
            "equation": [f"e{i}" for i in range(len(rows))],
        },
        index=[10 * (i + 1) for i in range(len(rows))],  # non-positional labels
    )
    if with_score:
        scores = []
        last_loss = None
        last_complexity = 0
        for complexity, loss in rows:
            if last_loss is None:
                scores.append(0.0)
            elif loss > 0.0:
                scores.append(-np.log(loss / last_loss) / (complexity - last_complexity))
            else:
                scores.append(np.inf)
            last_loss, last_complexity = loss, complexity
        frame["score"] = scores
    return frame


def _candidate(k: int, expression: str, **overrides) -> RetainedCandidate:
    base = dict(
        k=k,
        seed=2_100_000_000 + k,
        expression_string=expression,
        complexity=5,
        valid_r2=0.9,
        invalid_fraction=0.0,
        candidate_test_r2=0.85,
    )
    base.update(overrides)
    return RetainedCandidate(**base)


def _selection(k: int, expression: str | None, **overrides) -> SeedSelection:
    if expression is None:
        return SeedSelection(
            k=k,
            seed=2_100_000_000 + k,
            status=overrides.pop("status", SeedStatus.COMPLETED_NO_CANDIDATE),
            candidate=None,
            error_message=overrides.pop("error_message", ""),
        )
    return SeedSelection(
        k=k,
        seed=2_100_000_000 + k,
        status=SeedStatus.COMPLETED_WITH_CANDIDATES,
        candidate=_candidate(k, expression, **overrides),
    )


# =======================================================================
# Per-seed retention (section 7.1, 7.6)
# =======================================================================

def test_exactly_one_candidate_per_completed_seed_by_argmax_score():
    front = _front([(1, 1.0), (4, 0.2), (13, 0.19), (20, 0.185)])
    label = select_row_label(front)
    assert label == front["score"].idxmax()
    assert front["complexity"].loc[label] == 4


def test_the_selector_returns_a_label_not_a_position():
    front = _front([(1, 1.0), (4, 0.2)])
    label = select_row_label(front)
    assert label in front.index
    assert label not in range(len(front))  # labels are 10, 20 here


def test_empty_or_absent_equations_is_no_candidate():
    with pytest.raises(SeedNoCandidate):
        select_row_label(None)
    with pytest.raises(SeedNoCandidate):
        select_row_label(_front([]).iloc[0:0])


def test_a_missing_score_column_is_an_execution_failure_not_a_silent_fallback():
    # PySR's own idx_model_selection would silently switch to "accuracy"
    # (loss.idxmin()) here.  Section 7.6 forbids that.
    front = _front([(1, 1.0), (4, 0.2)], with_score=False)
    with pytest.raises(SeedExecutionFailure, match="no 'score' column"):
        select_row_label(front)


def test_a_non_finite_loss_is_an_execution_failure():
    front = _front([(1, 1.0), (4, 0.2)])
    front.loc[front.index[1], "loss"] = np.nan
    with pytest.raises(SeedExecutionFailure, match="non-finite loss"):
        select_row_label(front)
    front.loc[front.index[1], "loss"] = np.inf
    with pytest.raises(SeedExecutionFailure, match="non-finite loss"):
        select_row_label(front)


def test_zero_loss_yields_inf_and_the_first_such_row_deterministically():
    front = _front([(1, 1.0), (4, 0.0), (8, 0.0)])
    assert np.isinf(front["score"].iloc[1])
    label = select_row_label(front)
    assert label == front.index[1]
    assert select_row_label(front) == label


def test_a_flat_front_takes_the_first_row_deterministically():
    front = _front([(1, 0.5), (4, 0.5), (8, 0.5)])
    assert list(front["score"]) == [0.0, 0.0, 0.0] or front["score"].iloc[0] == 0.0
    assert select_row_label(front) == front.index[0]


def test_a_single_row_front_is_selected_trivially():
    front = _front([(3, 0.4)])
    assert select_row_label(front) == front.index[0]
    assert front["score"].iloc[0] == 0.0


def test_no_hidden_fallback_selector_exists():
    import ast
    import inspect

    import muru.paper_benchmark.rc5_selection as module

    tree = ast.parse(inspect.getsource(module.select_row_label))
    # Checked on the call graph, not on text: an error message that *names*
    # the forbidden fallback must not be able to fail this test, and a real
    # call to it must not be able to pass.
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "idxmin" not in called
    assert "idxmax" in called
    assert "query" not in called  # "best"'s 1.5x band filter is not reachable


# =======================================================================
# One seed, one vote (section 7.5)
# =======================================================================

def test_each_seed_contributes_exactly_one_membership():
    selections = [_selection(k, "mass * descriptor") for k in range(30)]
    result = group_and_select(selections)
    assert result.selection_count == 30
    assert result.voting_seeds == 30
    assert sum(c.size for c in result.classes) == 30


def test_a_duplicate_seed_ordinal_is_refused():
    selections = [_selection(0, "mass"), _selection(0, "descriptor")]
    with pytest.raises(ValueError, match="one seed, one vote"):
        group_and_select(selections)


def test_failed_and_barren_seeds_vote_for_nothing_while_the_denominator_stays_30():
    selections = [_selection(k, "mass * descriptor") for k in range(25)]
    selections += [
        _selection(25, None, status=SeedStatus.EXECUTION_FAILURE, error_message="RuntimeError: x"),
        _selection(26, None, status=SeedStatus.COMPLETED_NO_CANDIDATE),
        _selection(27, None, status=SeedStatus.COMPLETED_NO_CANDIDATE),
        _selection(28, None, status=SeedStatus.EXECUTION_FAILURE),
        _selection(29, None, status=SeedStatus.COMPLETED_NO_CANDIDATE),
    ]
    result = group_and_select(selections)
    assert result.selection_count == 25
    assert result.selection_denominator == SEEDS_PER_CASE == 30
    assert result.voting_seeds == 25
    assert result.selection_fraction == pytest.approx(25 / 30)


def test_zero_retained_seeds_yields_count_zero_and_no_representative():
    selections = [_selection(k, None) for k in range(30)]
    result = group_and_select(selections)
    assert result.selection_count == 0
    assert result.representative is None
    assert result.winning is None
    assert result.classes == ()
    assert result.selection_fraction == 0.0  # no division by zero anywhere


# =======================================================================
# Stability boundary (Gate 3)
# =======================================================================

@pytest.mark.parametrize(
    "k,expected", [(19, False), (20, True), (21, True)]
)
def test_the_stability_boundary_is_exactly_20_of_30(k, expected):
    selections = [_selection(i, "mass * descriptor") for i in range(k)]
    selections += [_selection(i, f"descriptor2 + {i}") for i in range(k, 30)]
    result = group_and_select(selections)
    assert result.selection_count == k
    assert result.stability_gate_passed is expected


def test_twenty_of_thirty_passes_by_exact_float_equality():
    selections = [_selection(i, "mass * descriptor") for i in range(20)]
    selections += [_selection(i, f"distractor + {i}") for i in range(20, 30)]
    result = group_and_select(selections)
    assert result.selection_fraction == 20 / 30
    assert result.selection_fraction >= 20 / 30
    assert result.stability_gate_passed is True


# =======================================================================
# Grouping by the frozen identity contract
# =======================================================================

def test_positive_scale_equivalent_expressions_merge():
    selections = [
        _selection(0, "mass * descriptor"),
        _selection(1, "2.0 * mass * descriptor"),
        _selection(2, "0.5 * mass * descriptor"),
    ]
    result = group_and_select(selections)
    assert len(result.classes) == 1
    assert result.selection_count == 3


def test_non_equivalent_rational_expressions_do_not_merge():
    selections = [
        _selection(0, "mass / (1.0 + descriptor)"),
        _selection(1, "mass / (1.0 + descriptor2)"),
        _selection(2, "descriptor / (1.0 + mass)"),
    ]
    result = group_and_select(selections)
    assert len(result.classes) == 3
    assert result.selection_count == 1


def test_the_session_2_rational_scale_stripping_failure_cannot_regress():
    """Adversarial rational functions, positively scaled.

    The superseded seven-step recipe's global-scale-strip step was proven
    unsound for exactly this shape: ``cancel()``'s incidental choice of which
    side absorbs shared numeric content made the key scale-dependent, so a
    candidate and its own positive multiple fragmented into different classes.
    The frozen contract strips content from numerator and denominator
    *separately*, which is the fix.  Every pair below is a single candidate and
    a positive scalar multiple of it, so each must form ONE class.
    """
    cases = [
        ("mass / (1.0 + descriptor)", 3.0),
        ("(mass + descriptor) / (descriptor2 + 2.0)", 0.25),
        ("(2.0 * mass - descriptor) / (3.0 * descriptor2 + 7.0)", 5.0),
        ("sqrt(mass) / (descriptor + distractor)", 1.5),
        ("(mass * descriptor) / (1.0 + correlated_distractor * descriptor2)", 100.0),
        ("inv(1.0 + descriptor) * mass", 0.125),
        ("(mass + 1.0) / (mass - 1.0)", 8.0),
    ]
    for expression, scale in cases:
        scaled = f"{scale} * ({expression})"
        assert positive_scale_equivalent(
            parse_candidate(expression), parse_candidate(scaled)
        ), f"{expression} did not merge with its {scale}x multiple"
        result = group_and_select(
            [_selection(0, expression), _selection(1, scaled)]
        )
        assert len(result.classes) == 1, f"{expression} fragmented under scaling"
        assert result.selection_count == 2


def test_a_negative_scale_is_not_a_positive_scale():
    result = group_and_select(
        [_selection(0, "mass / (1.0 + descriptor)"),
         _selection(1, "-1.0 * mass / (1.0 + descriptor)")]
    )
    assert len(result.classes) == 2


def test_duplicate_identical_representations_merge_into_one_class():
    selections = [_selection(k, "mass * descriptor") for k in range(30)]
    result = group_and_select(selections)
    assert len(result.classes) == 1
    assert result.distinct_expression_strings == 1


# =======================================================================
# Winning class, tie-break, representative
# =======================================================================

def test_largest_class_wins():
    selections = [_selection(k, "mass * descriptor") for k in range(0, 18)]
    selections += [_selection(k, "descriptor2 + distractor") for k in range(18, 30)]
    result = group_and_select(selections)
    assert result.selection_count == 18
    assert result.representative.expression_string == "mass * descriptor"


def test_a_tie_breaks_toward_the_class_containing_the_lowest_seed_ordinal():
    # Class A holds ordinals 0..14, class B holds 15..29: equal size, and A
    # contains the lowest ordinal overall.
    selections = [_selection(k, "mass * descriptor") for k in range(0, 15)]
    selections += [_selection(k, "descriptor2 + distractor") for k in range(15, 30)]
    result = group_and_select(selections)
    assert result.selection_count == 15
    assert result.winning.min_ordinal == 0
    assert result.representative.k == 0

    # Reversed: now B holds the lowest ordinal, so B wins despite identical
    # sizes and identical expression content.
    selections = [_selection(k, "descriptor2 + distractor") for k in range(0, 15)]
    selections += [_selection(k, "mass * descriptor") for k in range(15, 30)]
    result = group_and_select(selections)
    assert result.winning.min_ordinal == 0
    assert result.representative.expression_string == "descriptor2 + distractor"


def test_the_tie_break_is_total_because_minimum_ordinals_are_unique():
    selections = [
        _selection(0, "mass"),
        _selection(1, "descriptor"),
        _selection(2, "descriptor2"),
        _selection(3, "distractor"),
    ]
    result = group_and_select(selections)
    minima = [c.min_ordinal for c in result.classes]
    assert len(set(minima)) == len(minima)
    assert result.representative.k == 0


def test_the_representative_is_the_earliest_seed_in_the_winning_class():
    selections = [_selection(k, None) for k in range(0, 5)]
    selections += [_selection(k, "mass * descriptor") for k in range(5, 25)]
    selections += [_selection(k, "distractor") for k in range(25, 30)]
    result = group_and_select(selections)
    assert result.representative.k == 5
    assert result.representative.seed == 2_100_000_005


def test_representative_values_are_used_verbatim_never_refit_or_pooled():
    selections = [
        _selection(0, "mass * descriptor", valid_r2=0.11, complexity=3,
                   invalid_fraction=0.0, candidate_test_r2=0.21),
        _selection(1, "2.0 * mass * descriptor", valid_r2=0.99, complexity=9,
                   invalid_fraction=0.0, candidate_test_r2=0.98),
        _selection(2, "3.0 * mass * descriptor", valid_r2=0.95, complexity=7,
                   invalid_fraction=0.0, candidate_test_r2=0.94),
    ]
    result = group_and_select(selections)
    representative = result.representative
    # The earliest seed's own emitted values, not the best, not the mean.
    assert representative.k == 0
    assert representative.valid_r2 == 0.11
    assert representative.complexity == 3
    assert representative.candidate_test_r2 == 0.21
    assert representative.expression_string == "mass * descriptor"


def test_the_rule_never_inspects_valid_r2_complexity_or_support():
    # Same membership, wildly different quality: the winner and representative
    # must be identical either way.
    poor_first = [
        _selection(0, "mass * descriptor", valid_r2=0.01, complexity=20),
        _selection(1, "mass * descriptor", valid_r2=0.99, complexity=1),
    ]
    rich_first = [
        _selection(0, "mass * descriptor", valid_r2=0.99, complexity=1),
        _selection(1, "mass * descriptor", valid_r2=0.01, complexity=20),
    ]
    assert group_and_select(poor_first).representative.k == 0
    assert group_and_select(rich_first).representative.k == 0


def test_selection_count_is_derived_from_the_winning_class():
    selections = [_selection(k, "mass * descriptor") for k in range(0, 22)]
    selections += [_selection(k, "distractor") for k in range(22, 30)]
    result = group_and_select(selections)
    assert result.selection_count == result.winning.size == 22


# =======================================================================
# Determinism and replay
# =======================================================================

def test_grouping_replays_deterministically():
    selections = [
        _selection(0, "mass / (1.0 + descriptor)"),
        _selection(1, "2.0 * mass / (2.0 + 2.0 * descriptor)"),
        _selection(2, "descriptor2"),
        _selection(3, "mass / (1.0 + descriptor)"),
    ]
    first = group_and_select(selections)
    second = group_and_select(list(reversed(selections)))
    assert first.selection_count == second.selection_count
    assert first.representative.k == second.representative.k
    assert [c.min_ordinal for c in first.classes] == [
        c.min_ordinal for c in second.classes
    ]


def test_class_keys_come_from_the_frozen_identity_contract():
    selections = [_selection(0, "mass * descriptor")]
    result = group_and_select(selections)
    assert result.classes[0].key == template_key(parse_candidate("mass * descriptor"))


# =======================================================================
# Non-gating diagnostics (section 7.4)
# =======================================================================

def test_the_two_class_heterogeneity_diagnostics_are_recorded():
    selections = [
        _selection(0, "2.0*(mass + descriptor)"),
        _selection(1, "2.0*mass + 2.0*descriptor"),
        _selection(2, "3.0*mass + 3.0*descriptor"),
    ]
    result = group_and_select(selections)
    assert result.selection_count == 3            # they merge
    assert result.distinct_expression_strings == 3  # but are visibly different
    assert result.distinct_coefficient_vectors >= 2
    diagnostics = result.diagnostics()
    assert diagnostics["winning_class_distinct_expression_strings"] == 3


#: A3.5 section 7.4's five executed merge confirmations.  Every one of them is
#: a property of the **superseded** section-7.3 ``TEMPLATE_KEY`` recipe, which
#: templated every numeric position.  The frozen replacement contract
#: (``MURU_A3_5_IDENTITY_FINAL_CONTRACT.md``, named as closed by section 14.1)
#: is a *positive-scale-equivalence* relation, which is strictly narrower: it
#: merges a candidate with ``c * candidate`` for a single ``c > 0`` and nothing
#: else.  Pinned here as a permanent, explicit record of the supersession's
#: consequence -- see the reconciliation audit's difference X6.
SUPERSEDED_TEMPLATE_KEY_MERGES = [
    ("2.0*(mass+descriptor)", "2.0*mass + 3.0*descriptor"),
    ("2.0*mass + 2.0*descriptor", "2.0*mass + 3.0*descriptor"),
    ("mass/(1.0+descriptor)", "mass/(2.0+descriptor)"),
    ("-(mass*descriptor)", "mass*descriptor"),
    ("mass+descriptor", "mass-descriptor"),
]


@pytest.mark.parametrize("a,b", SUPERSEDED_TEMPLATE_KEY_MERGES)
def test_the_superseded_template_key_merges_do_not_occur(a, b):
    """The frozen contract is narrower than section 7.4's struck recipe.

    Direction check, which is what makes accepting the narrower relation safe:
    a narrower identity relation yields MORE and SMALLER classes, hence a
    SMALLER ``selection_count``, hence a HARDER Gate 3 -- the acceptance-harder
    direction.  It cannot manufacture stability that the broader rule would
    not also have found.
    """
    result = group_and_select([_selection(0, a), _selection(1, b)])
    assert len(result.classes) == 2
    assert result.selection_count == 1
    assert not positive_scale_equivalent(parse_candidate(a), parse_candidate(b))


def test_the_frozen_contract_merges_positive_scalar_multiples_and_only_those():
    for expression in [
        "2.0*(mass+descriptor)",
        "mass/(1.0+descriptor)",
        "mass+descriptor",
        "sqrt(mass)*descriptor2",
    ]:
        for scale in (0.25, 3.0, 1000.0):
            result = group_and_select(
                [_selection(0, expression), _selection(1, f"{scale}*({expression})")]
            )
            assert len(result.classes) == 1
            assert result.distinct_expression_strings == 2


def test_class_heterogeneity_is_visible_when_a_class_holds_distinct_strings():
    selections = [
        _selection(0, "mass * descriptor"),
        _selection(1, "2.0 * mass * descriptor"),
        _selection(2, "0.5*(mass * descriptor)"),
    ]
    result = group_and_select(selections)
    assert result.selection_count == 3
    assert result.distinct_expression_strings == 3
    assert result.distinct_coefficient_vectors >= 2


def test_the_diagnostics_enter_no_gate():
    import ast
    import inspect

    import muru.paper_benchmark.rc5_selection as module

    tree = ast.parse(inspect.getsource(module.CrossSeedSelection))
    gate = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "stability_gate_passed"
    )
    names = {n.attr for n in ast.walk(gate) if isinstance(n, ast.Attribute)}
    assert "distinct_expression_strings" not in names
    assert "distinct_coefficient_vectors" not in names


def test_coefficient_vector_is_none_for_an_unparseable_string():
    assert coefficient_vector("this is ( not an expression") is None


# =======================================================================
# Blindness
# =======================================================================

def test_selection_reads_no_partition_no_family_no_truth():
    import ast
    import inspect

    import muru.paper_benchmark.rc5_selection as module

    source = inspect.getsource(module)
    tree = ast.parse(source)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in (
        "partition_label",
        "partition",
        "truth_family",
        "mathematical_family",
        "active_variables",
        "g_by_compound",
        "TruthRecord",
        "classify_discovered_family",
    ):
        assert forbidden not in names, f"selection reaches {forbidden}"


def test_the_same_candidates_group_identically_regardless_of_seed_values():
    # Seed *values* differ (a different case ordinal); ordinals do not.
    a = [
        SeedSelection(k, 2_100_000_000 + k, SeedStatus.COMPLETED_WITH_CANDIDATES,
                      _candidate(k, "mass * descriptor"))
        for k in range(5)
    ]
    b = [
        SeedSelection(k, 2_100_009_000 + k, SeedStatus.COMPLETED_WITH_CANDIDATES,
                      _candidate(k, "mass * descriptor", seed=2_100_009_000 + k))
        for k in range(5)
    ]
    assert group_and_select(a).selection_count == group_and_select(b).selection_count
    assert group_and_select(a).representative.k == group_and_select(b).representative.k
