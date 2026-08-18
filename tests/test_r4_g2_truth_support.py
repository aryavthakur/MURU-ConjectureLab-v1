"""R4: G2 truth_support producer (DEFECT_D).

classify_support(discovered_support, truth_support) has always required a
truth_support operand that nothing in the repository produced
(g2_contract.py:135 declares the parameter; rc3_acceptance.py explicitly
declines to read it; rc3_record.py's CaseExecutionRecord.truth_support is a
schema slot only). truth_support_for_case derives it mechanically from
generator.py::_law's active_variables -- the single source of truth already
written for every case -- with no hand-coded per-family label table.

All fixtures either use hand-built TruthRecord objects or generate_case on
the "development" partition only (already historically executed under a
superseded contract, and used identically by the frozen
tests/test_paper_benchmark_truth.py). No Held-out or Challenge case is ever
generated here.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.g2_contract import (
    GRAMMAR_PRIMITIVES,
    TRUTH_FAMILIES,
    classify_support,
    extract_effective_support,
    truth_support_for_case,
)
from muru.paper_benchmark.generator import generate_case
from muru.paper_benchmark.registry import CASE_FAMILIES
from muru.paper_benchmark.truth import TruthRecord

# The 12 registry-frozen G2-applicable families (symbolic_truth_kind ==
# "defined", i.e. carrying the family_recovery/support_recovery endpoints).
G2_APPLICABLE_FAMILIES = ("F01", "F02", "F03", "F04", "F05", "F08", "F09", "F10", "F11", "F12", "F17", "F18")

# Families that are NOT G2-applicable, spanning every non-"defined"
# symbolic_truth_kind value in the registry (none, mass_only, mass_only_allowance).
G2_INAPPLICABLE_FAMILIES = ("F06", "F07", "F13", "F14", "F15", "F16", "F19", "F20")


def _development_case_id(family_code: str, replicate: int = 0) -> str:
    return f"PB|development|{family_code}|r{replicate:03d}"


def _truth_record(**overrides) -> TruthRecord:
    base = dict(
        case_id="PB|development|F01|r000",
        partition="development",
        family="F01",
        variant="BASE",
        seeds={},
        phi={},
        g_definition=None,
        g_by_compound={},
        descriptor_relationship=None,
        active_variables=["mass", "descriptor"],
        mathematical_family="mass_affine_descriptor",
        coefficients={},
        exponents={},
        noise={},
        missingness={},
        scalar_truth_defined=True,
        m0_adequacy_truth="M0",
        symbolic_truth_kind="defined",
        applicable_endpoints=[],
        expected_behavior="",
    )
    base.update(overrides)
    return TruthRecord(**base)


# -----------------------------------------------------------------------
# Hand-built unit coverage of the block-label mapping
# -----------------------------------------------------------------------

def test_mass_and_descriptor_map_identically():
    truth = _truth_record(active_variables=["mass", "descriptor"], mathematical_family="mass_affine_descriptor")
    assert truth_support_for_case(truth) == {"mass", "descriptor"}


def test_mass_only_family_is_not_g2_applicable_despite_defined_active_variables():
    """F07 is scalar-only (symbolic_truth_kind='mass_only'): even though its
    active_variables=['mass'] would map cleanly, it must still raise --
    confirms the gate is registry metadata, not the shape of active_variables."""
    truth = _truth_record(
        case_id="PB|development|F07|r000",
        family="F07",
        active_variables=["mass"],
        mathematical_family="mass_power",
        symbolic_truth_kind="mass_only",
    )
    with pytest.raises(ValueError):
        truth_support_for_case(truth)


def test_interaction_block_labels_map_positionally_to_descriptor_pair():
    """generator.py's interaction branch writes 'descriptor * descriptor2' in
    the same call that returns active_variables=['mass', 'interaction_left',
    'interaction_right']; the block labels must map 1:1 onto that pair."""
    truth = _truth_record(
        case_id="PB|development|F10|r000",
        family="F10",
        active_variables=["mass", "interaction_left", "interaction_right"],
        mathematical_family="mass_interaction",
    )
    assert truth_support_for_case(truth) == {"mass", "descriptor", "descriptor2"}


def test_unmapped_active_variable_label_raises():
    truth = _truth_record(active_variables=["mass", "not_a_real_block_label"])
    with pytest.raises(ValueError):
        truth_support_for_case(truth)


def test_non_g2_applicable_family_raises_rather_than_guessing():
    truth = _truth_record(
        case_id="PB|development|F19|r000",
        family="F19",
        variant="F19B",
        active_variables=["mass"],
        mathematical_family="mass_power",
        symbolic_truth_kind="mass_only_allowance",
    )
    with pytest.raises(ValueError):
        truth_support_for_case(truth)


def test_unrecognized_mathematical_family_raises():
    truth = _truth_record(mathematical_family="not_a_frozen_truth_family")
    with pytest.raises(ValueError):
        truth_support_for_case(truth)


# -----------------------------------------------------------------------
# Deterministic, exhaustive over every G2-applicable family
# -----------------------------------------------------------------------

@pytest.mark.parametrize("family_code", G2_APPLICABLE_FAMILIES)
def test_every_g2_applicable_family_produces_truth_support(family_code):
    truth = generate_case(_development_case_id(family_code)).truth
    support = truth_support_for_case(truth)
    assert support, f"{family_code} produced empty truth support"
    assert support <= set(GRAMMAR_PRIMITIVES)
    assert truth.mathematical_family in TRUTH_FAMILIES


@pytest.mark.parametrize("family_code", G2_INAPPLICABLE_FAMILIES)
def test_no_g2_inapplicable_family_produces_a_guessed_label(family_code):
    """Non-G2 families must raise, never silently return an arbitrary
    frozenset, per the mission's 'do not hand-code arbitrary labels' rule."""
    family = next(f for f in CASE_FAMILIES if f.code == family_code)
    variant = family.variant_for_replicate(0)
    assert variant.symbolic_truth_kind != "defined"
    truth = generate_case(_development_case_id(family_code)).truth
    with pytest.raises(ValueError):
        truth_support_for_case(truth)


@pytest.mark.parametrize("family_code", G2_APPLICABLE_FAMILIES)
def test_truth_support_is_deterministic(family_code):
    case_id = _development_case_id(family_code)
    a = truth_support_for_case(generate_case(case_id).truth)
    b = truth_support_for_case(generate_case(case_id).truth)
    assert a == b


# Expected truth support per family, hand-derived by reading
# generator.py::_law's dispatch directly (independent of truth_support_for_case
# itself, so this is a real cross-check and not a circular restatement):
#   - the nine "mass * (1 + coefficient * descriptor)"-shaped kinds
#     (scalar_noiseless/moderate/strong, missing_one_energy, boundary_scale,
#     simple_descriptor, irrelevant_distractors, correlated_distractors,
#     equivalent_forms) -> {mass, descriptor}          (F01-F05, F11, F12, F17)
#   - nonlinear_descriptor (saturating)                -> {mass, descriptor}  (F09)
#   - interaction (mass * descriptor * descriptor2)     -> {mass, descriptor, descriptor2} (F10)
#   - difficult_algebra (exponential descriptor)         -> {mass, descriptor}  (F18)
_EXPECTED_TRUTH_SUPPORT_BY_FAMILY = {
    "F01": {"mass", "descriptor"},
    "F02": {"mass", "descriptor"},
    "F03": {"mass", "descriptor"},
    "F04": {"mass", "descriptor"},
    "F05": {"mass", "descriptor"},
    "F08": {"mass", "descriptor"},
    "F09": {"mass", "descriptor"},
    "F10": {"mass", "descriptor", "descriptor2"},
    "F11": {"mass", "descriptor"},
    "F12": {"mass", "descriptor"},
    "F17": {"mass", "descriptor"},
    "F18": {"mass", "descriptor"},
}


@pytest.mark.parametrize("family_code", G2_APPLICABLE_FAMILIES)
def test_truth_support_matches_the_planted_family_definition(family_code):
    """The producer must agree with the frozen planted-family definitions,
    for every replicate of every G2-applicable family."""
    family = next(f for f in CASE_FAMILIES if f.code == family_code)
    for replicate in range(family.partition_counts["development"]):
        truth = generate_case(_development_case_id(family_code, replicate)).truth
        support = truth_support_for_case(truth)
        assert support == _EXPECTED_TRUTH_SUPPORT_BY_FAMILY[family_code], (family_code, replicate, support)


# -----------------------------------------------------------------------
# No partition-dependent logic
# -----------------------------------------------------------------------

def test_producer_never_branches_on_partition():
    """Structural proof, not a sampled equivalence check: the compiled
    function body never *references* the partition field's name at all (as
    opposed to merely mentioning the word in prose/docstrings), so it cannot
    special-case development/held_out/challenge."""
    assert "partition" not in truth_support_for_case.__code__.co_names


def test_producer_result_unaffected_by_partition_label_on_an_otherwise_identical_record():
    """Two hand-built records that differ only in their partition label (and
    the case_id's partition component, needed for resolve_case_id) must
    produce identical truth support. No real Held-out or Challenge case data
    is read; these are synthetic labels only."""
    development = _truth_record(
        case_id="PB|development|F10|r000",
        partition="development",
        family="F10",
        active_variables=["mass", "interaction_left", "interaction_right"],
        mathematical_family="mass_interaction",
    )
    held_out_labeled = _truth_record(
        case_id="PB|held_out|F10|r000",
        partition="held_out",
        family="F10",
        active_variables=["mass", "interaction_left", "interaction_right"],
        mathematical_family="mass_interaction",
    )
    assert truth_support_for_case(development) == truth_support_for_case(held_out_labeled)


# -----------------------------------------------------------------------
# Integration with the already-frozen classify_support rule
# -----------------------------------------------------------------------

def test_producer_output_feeds_classify_support_unchanged():
    """R4 supplies the missing operand; it does not alter classify_support
    itself (frozen, untouched by this repair). truth.g_definition is a
    human-readable template ("sqrt(mass) * (1 + coefficient * descriptor)",
    with the literal placeholder word "coefficient", not a realized numeric
    expression), so a concrete discovered-side expression is hand-built here
    instead of parsing it."""
    truth = generate_case(_development_case_id("F09")).truth
    truth_support = truth_support_for_case(truth)
    matching_discovered = extract_effective_support("sqrt(mass) * (1 + 0.4 * descriptor / (1 + descriptor))")
    assert classify_support(matching_discovered, truth_support).value == "MATCH"
    assert classify_support(frozenset({"mass"}), truth_support).value in ("MATCH", "MISMATCH")
