"""A3.5 sections 4.3 and 7.2: the case-to-search adapter and Gate-2 provenance.

Row shape, target identity, feature identity, complexity provenance, and
partition blindness.  Hand-built fixtures only; no benchmark case, no PySR run.
"""
from __future__ import annotations

import ast
import inspect

import numpy as np
import pandas as pd
import pytest

from muru.paper_benchmark.calibration_contract import MAX_COMPLEXITY
from muru.paper_benchmark.g2_contract import GRAMMAR_PRIMITIVES
from muru.paper_benchmark.rc3_calibration_worlds import CALIBRATION_COVARIATE_ORDER
from muru.paper_benchmark.rc5_adapter import (
    CASE_COVARIATE_ORDER,
    FEATURE_NAME_ALIASES,
    GrammarSettingsError,
    assert_grammar_settings,
    assert_selected_complexity_in_range,
    build_case_design,
    candidate_r2_on,
    row_complexity,
    row_position,
)
from muru.paper_benchmark.rc5_estimate import CaseScalars, FrozenPhi

N = 12


def _frame() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    return pd.DataFrame(
        {
            "compound_id": [f"C{i:03d}" for i in range(N)],
            "scaffold_id": [f"S{i // 2:02d}" for i in range(N)],
            "split": ["train"] * 8 + ["validation"] * 2 + ["test"] * 2,
            "mass": rng.uniform(200, 400, N),
            "descriptor": rng.uniform(0, 1, N),
            "descriptor2": rng.uniform(0, 1, N),
            "distractor": rng.normal(0, 1, N),
            "correlated_distractor": rng.normal(0, 1, N),
        }
    )


def _scalars(frame: pd.DataFrame) -> CaseScalars:
    return CaseScalars(
        compound_ids=tuple(frame.compound_id),
        splits=tuple(frame.split),
        g=np.linspace(1.0, 2.0, len(frame)),
        frozen_phi=FrozenPhi(
            knots=np.linspace(-1, 1, 60),
            values=np.linspace(1.0, 0.2, 60),
            e_ref=45.0,
            n_knots=60,
            n_training_compounds=8,
            alternations=3,
        ),
    )


# -----------------------------------------------------------------------
# Row shape, feature identity, target identity
# -----------------------------------------------------------------------

def test_the_design_is_one_row_per_compound_and_five_columns():
    frame = _frame()
    design = build_case_design(frame, _scalars(frame))
    assert design.design.shape == (N, 5)
    assert design.target.shape == (N,)
    assert design.compound_ids == tuple(frame.compound_id)


def test_feature_identity_and_order_are_the_frozen_tuple_object():
    assert CASE_COVARIATE_ORDER is GRAMMAR_PRIMITIVES
    assert CASE_COVARIATE_ORDER is CALIBRATION_COVARIATE_ORDER
    frame = _frame()
    design = build_case_design(frame, _scalars(frame))
    assert design.feature_names == (
        "mass",
        "descriptor",
        "descriptor2",
        "distractor",
        "correlated_distractor",
    )
    for index, name in enumerate(design.feature_names):
        assert np.array_equal(design.design[:, index], frame[name].to_numpy())


def test_the_alias_mapping_is_positional_and_exact():
    assert FEATURE_NAME_ALIASES == {
        "x0": "mass",
        "x1": "descriptor",
        "x2": "descriptor2",
        "x3": "distractor",
        "x4": "correlated_distractor",
    }
    # And it agrees with the frozen parser's own alias table.
    from muru.paper_benchmark.g2_contract import _FEATURE_NAME_ALIASES

    assert set(FEATURE_NAME_ALIASES) == set(_FEATURE_NAME_ALIASES)
    for alias, name in FEATURE_NAME_ALIASES.items():
        assert _FEATURE_NAME_ALIASES[alias].name == name


def test_the_target_is_the_raw_g_verbatim():
    frame = _frame()
    scalars = _scalars(frame)
    design = build_case_design(frame, scalars)
    assert np.array_equal(design.target, scalars.g)
    # Not log g, and not renormalised to unit mean or unit geometric mean.
    assert not np.allclose(design.target, np.log(scalars.g))
    assert not np.isclose(float(np.mean(np.log(design.target))), 0.0, atol=1e-9)


def test_no_weight_channel_is_produced():
    frame = _frame()
    design = build_case_design(frame, _scalars(frame))
    assert not hasattr(design, "weights")
    assert "weight" not in {f for f in design.__dataclass_fields__}
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(build_case_design)))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.arg for n in ast.walk(tree) if isinstance(n, ast.keyword) and n.arg}
    assert "sample_weight" not in names
    assert "g_var" not in names


def test_no_row_is_filtered_even_with_missingness_flagged_compounds():
    frame = _frame()
    design = build_case_design(frame, _scalars(frame))
    assert design.design.shape[0] == len(frame)
    assert design.train_mask.sum() == 8
    assert design.validation_mask.sum() == 2
    assert design.test_mask.sum() == 2


def test_a_row_order_mismatch_is_refused_rather_than_silently_realigned():
    frame = _frame()
    scalars = _scalars(frame)
    shuffled = frame.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="row order or membership"):
        build_case_design(shuffled, scalars)


def test_a_missing_covariate_is_refused():
    frame = _frame().drop(columns=["distractor"])
    scalars = _scalars(_frame())
    with pytest.raises(ValueError, match="covariates missing"):
        build_case_design(frame, scalars)


# -----------------------------------------------------------------------
# Gate-2 complexity provenance and the label/position landmine
# -----------------------------------------------------------------------

def _equations() -> pd.DataFrame:
    # Non-positional labels, exactly the shape that makes the landmine bite.
    return pd.DataFrame(
        {"complexity": [1, 4, 13], "loss": [1.0, 0.2, 0.19],
         "equation": ["mass", "mass*descriptor", "mass*descriptor + distractor"]},
        index=[7, 11, 23],
    )


def test_row_position_converts_a_label_to_a_position():
    equations = _equations()
    assert row_position(equations, 7) == 0
    assert row_position(equations, 11) == 1
    assert row_position(equations, 23) == 2


def test_using_the_label_as_a_position_would_score_the_wrong_row():
    equations = _equations()
    label = 11
    assert row_position(equations, label) != label
    assert equations["complexity"].iloc[row_position(equations, label)] == 4


def test_complexity_comes_from_pysrs_own_column():
    equations = _equations()
    assert row_complexity(equations, 11) == 4
    # And it is NOT grammar.complexity, which diverges upward on division.
    from muru.discovery.grammar import complexity as grammar_complexity, parse

    grammar_value = grammar_complexity(
        parse("mass / descriptor", list(GRAMMAR_PRIMITIVES))
    )
    pysr_value_for_a_division = 3  # PySR counts `/` as one binary operator
    assert grammar_value > pysr_value_for_a_division


def test_the_adapter_never_imports_the_discovery_engine():
    import muru.paper_benchmark.rc5_adapter as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
        elif isinstance(node, ast.Import):
            modules |= {a.name for a in node.names}
    assert not any(m.endswith("discovery.engine") for m in modules)
    assert not any(m.endswith("engine") for m in modules)


def test_valid_r2_comes_from_the_unweighted_calibration_r2():
    import muru.paper_benchmark.rc5_adapter as module

    tree = ast.parse(open(module.__file__, encoding="utf-8").read())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "_r2" in imported


class _Model:
    """Minimal stand-in that records which row position it was asked for."""

    def __init__(self, columns):
        self.columns = columns
        self.seen: list[int] = []

    def predict(self, design, index):
        self.seen.append(index)
        return design[:, 0] * (index + 1)


def test_candidate_r2_scores_the_converted_position_on_the_masked_rows():
    frame = _frame()
    design = build_case_design(frame, _scalars(frame))
    equations = _equations()
    model = _Model(design.feature_names)
    value = candidate_r2_on(
        model, equations, 23, design.design, design.target, design.validation_mask
    )
    assert model.seen == [2]  # position, not the label 23
    assert isinstance(value, float)


def test_zero_target_variance_yields_the_frozen_minus_infinity_sentinel():
    frame = _frame()
    scalars = _scalars(frame)
    flat = CaseScalars(
        compound_ids=scalars.compound_ids,
        splits=scalars.splits,
        g=np.ones(len(frame)),
        frozen_phi=scalars.frozen_phi,
    )
    design = build_case_design(frame, flat)
    model = _Model(design.feature_names)
    value = candidate_r2_on(
        model, _equations(), 7, design.design, design.target, design.validation_mask
    )
    assert value == float("-inf")


# -----------------------------------------------------------------------
# Grammar
# -----------------------------------------------------------------------

def test_the_grammar_guard_accepts_the_frozen_settings():
    report = assert_grammar_settings()
    assert report["binary_operators"] == ["+", "-", "*", "/"]
    assert report["unary_operators"] == ["sqrt", "log", "square", "cube", "inv"]
    assert "exp" in report["excluded_unary"]


def test_adding_exp_to_help_f18_is_refused(monkeypatch):
    from muru.paper_benchmark import rc5_adapter

    settings = dict(rc5_adapter.SEARCH_SETTINGS)
    settings["unary_operators"] = ["sqrt", "log", "square", "cube", "inv", "exp"]
    monkeypatch.setattr(rc5_adapter, "SEARCH_SETTINGS", settings)
    with pytest.raises(GrammarSettingsError):
        assert_grammar_settings()


def test_any_operator_expansion_is_refused(monkeypatch):
    from muru.paper_benchmark import rc5_adapter

    settings = dict(rc5_adapter.SEARCH_SETTINGS)
    settings["binary_operators"] = ["+", "-", "*", "/", "^"]
    monkeypatch.setattr(rc5_adapter, "SEARCH_SETTINGS", settings)
    with pytest.raises(GrammarSettingsError, match="binary operators"):
        assert_grammar_settings()


def test_a_selected_complexity_outside_1_to_20_is_refused():
    assert_selected_complexity_in_range(1)
    assert_selected_complexity_in_range(MAX_COMPLEXITY)
    with pytest.raises(ValueError):
        assert_selected_complexity_in_range(0)
    with pytest.raises(ValueError):
        assert_selected_complexity_in_range(MAX_COMPLEXITY + 1)


# -----------------------------------------------------------------------
# Blindness
# -----------------------------------------------------------------------

def test_the_adapter_reads_no_partition_no_family_no_truth():
    import muru.paper_benchmark.rc5_adapter as module

    source = open(module.__file__, encoding="utf-8").read()
    tree = ast.parse(source)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in (
        "partition_label",
        "TruthRecord",
        "truth",
        "mathematical_family",
        "classify_discovered_family",
        "resolve_case_id",
    ):
        assert forbidden not in names, f"adapter reaches {forbidden}"


def test_the_design_is_a_pure_function_of_covariates_and_target():
    # Identical covariates and target, different compound identifiers: the
    # design must be byte-identical, so nothing can key off an ID.
    frame = _frame()
    scalars = _scalars(frame)
    renamed = frame.copy()
    renamed["compound_id"] = [f"Z{i:03d}" for i in range(N)]
    renamed_scalars = CaseScalars(
        compound_ids=tuple(renamed.compound_id),
        splits=scalars.splits,
        g=scalars.g,
        frozen_phi=scalars.frozen_phi,
    )
    first = build_case_design(frame, scalars)
    second = build_case_design(renamed, renamed_scalars)
    assert np.array_equal(first.design, second.design)
    assert np.array_equal(first.target, second.target)
    assert first.splits == second.splits
