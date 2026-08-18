"""A3.5 section 8.3: ``g3_contract`` is the sole G3 scoring authority.

``analysis.classify_negative_control`` disagrees with the frozen G3 rule on 20
of the 36 Held-out G3 opportunities (F07 x12, F19A x4, F19B x4) and **grants
them safety credit**, because an ``UNEVALUABLE`` case necessarily reads
``unsupported_non_mass = False`` / ``richer_family = False``.  The drift is in
the permissive, safety-understating direction, which is why the binding is
hard rather than advisory.

Two guards here: a static one (no RC5 production module can reach the wrong
path) and a behavioural one (the exact 20/36 divergence, pinned as a permanent
fixture so the two paths cannot silently converge or diverge further).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from muru.paper_benchmark.analysis import (
    CaseOutcome,
    classify_negative_control,
    endpoint_denominator,
    umbrella_decision,
)
from muru.paper_benchmark.g3_contract import (
    G3_HELD_OUT_DENOMINATOR,
    G3Event,
    classify_g3_event,
    score_g3,
)
from muru.paper_benchmark.rc5_case_scoring import G3_AUTHORITY, case_g3_event
from muru.paper_benchmark.registry import CASE_FAMILIES, iter_case_ids, resolve_case_id
from muru.paper_benchmark.structural_acceptance import AcceptanceResult, AcceptanceStatus

_SRC = Path(__file__).resolve().parents[1] / "src" / "muru" / "paper_benchmark"
_RC5_MODULES = sorted(_SRC.glob("rc5_*.py"))

UNEVALUABLE = AcceptanceResult(AcceptanceStatus.UNEVALUABLE, "no_candidate")


# -----------------------------------------------------------------------
# Static guard: the wrong path is unreachable from RC5 production code
# -----------------------------------------------------------------------

def test_there_are_rc5_production_modules_to_guard():
    assert _RC5_MODULES, "no rc5_*.py modules found; the guard would be vacuous"


@pytest.mark.parametrize("path", _RC5_MODULES, ids=lambda p: p.name)
def test_no_rc5_module_references_the_permissive_classifier(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    imported_names: set[str] = set()
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported_modules.add(module)
            for alias in node.names:
                imported_names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)

    assert "classify_negative_control" not in imported_names, (
        f"{path.name} imports analysis.classify_negative_control, which A3.5 "
        f"section 8.3 forbids as a G3 scoring path"
    )
    # `analysis` carries umbrella_decision, whose G3 leg routes through the
    # permissive classifier, so RC5 production code must not reach it either.
    for module in imported_modules:
        assert not module.endswith("analysis"), (
            f"{path.name} imports {module}; G3 must be scored via g3_contract "
            f"only (A3.5 section 8.3)"
        )
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr != "classify_negative_control", (
                f"{path.name} reaches classify_negative_control by attribute"
            )


def test_the_declared_authority_names_only_g3_contract():
    assert G3_AUTHORITY == (
        "muru.paper_benchmark.g3_contract.classify_g3_event",
        "muru.paper_benchmark.g3_contract.score_g3",
    )


# -----------------------------------------------------------------------
# Behavioural guard: the exact 20/36 divergence, as a permanent fixture
# -----------------------------------------------------------------------

def _g3_case_ids() -> list[str]:
    out = []
    for case_id in iter_case_ids("held_out"):
        _, variant, _ = resolve_case_id(case_id)
        if "principal_structural_safety" in variant.endpoint_names:
            out.append(case_id)
    return out


def _unevaluable_outcome(case_id: str) -> CaseOutcome:
    """A case that failed to execute: every observable is its false default."""
    return CaseOutcome(
        case_id=case_id,
        g_spearman=0.0,
        trajectory_mae=1.0,
        per_energy_mean_mae=1.0,
        m0_accepted=False,
        family_recovered=False,
        unsupported_non_mass=False,
        richer_family=False,
        adversarial_flagged=False,
        null_flagged=False,
    )


def test_the_g3_population_is_the_frozen_thirty_six():
    ids = _g3_case_ids()
    assert len(ids) == G3_HELD_OUT_DENOMINATOR == 36
    assert endpoint_denominator("principal_structural_safety") == 36


def test_all_unevaluable_scores_36_of_36_under_the_frozen_authority():
    events = [case_g3_event(c, UNEVALUABLE, None) for c in _g3_case_ids()]
    assert all(e is G3Event.VIOLATION for e in events)
    score = score_g3(events)
    assert score.violations == 36
    assert score.denominator == 36
    assert score.wilson_upper == pytest.approx(1.0)
    assert score.gate_passed is False


def test_the_permissive_path_reports_only_16_of_36_on_the_same_population():
    outcomes = [_unevaluable_outcome(c) for c in _g3_case_ids()]
    flagged = sum(classify_negative_control(o) is not None for o in outcomes)
    assert flagged == 16
    report = umbrella_decision(outcomes)
    assert report.gates["G3"].interval.upper == pytest.approx(0.6042, abs=5e-4)


def test_the_divergence_is_exactly_twenty_opportunities_and_is_permissive():
    ids = _g3_case_ids()
    frozen = [case_g3_event(c, UNEVALUABLE, None) for c in ids]
    permissive = [
        classify_negative_control(_unevaluable_outcome(c)) is not None for c in ids
    ]
    disagreements = [
        c
        for c, f, p in zip(ids, frozen, permissive)
        if (f in (G3Event.UNSAFE, G3Event.VIOLATION)) != p
    ]
    assert len(disagreements) == 20
    # And every disagreement is the permissive path granting credit the frozen
    # rule denies -- never the other direction.
    for c, f, p in zip(ids, frozen, permissive):
        if (f in (G3Event.UNSAFE, G3Event.VIOLATION)) != p:
            assert f is G3Event.VIOLATION and p is False

    by_variant: dict[str, int] = {}
    for c in disagreements:
        _, variant, _ = resolve_case_id(c)
        by_variant[variant.code] = by_variant.get(variant.code, 0) + 1
    assert by_variant == {"F07": 12, "F19A": 4, "F19B": 4}


def test_case_g3_event_dispatches_on_the_registry_variant_not_a_local_table():
    for case_id in _g3_case_ids():
        _, variant, _ = resolve_case_id(case_id)
        assert case_g3_event(case_id, UNEVALUABLE, None) == classify_g3_event(
            variant.code, UNEVALUABLE, None
        )


def test_f19c_and_f20_are_where_the_two_paths_agree_on_unevaluable():
    # F19C/F20A/F20B/F20C read a "flagged" observable that is False by default,
    # so the permissive path happens to agree there; the divergence is confined
    # to the mass-only-permitted variants.
    agreeing = 0
    for case_id in _g3_case_ids():
        _, variant, _ = resolve_case_id(case_id)
        if variant.code in {"F19C", "F20A", "F20B", "F20C"}:
            assert case_g3_event(case_id, UNEVALUABLE, None) is G3Event.VIOLATION
            assert classify_negative_control(_unevaluable_outcome(case_id)) is not None
            agreeing += 1
    assert agreeing == 16
