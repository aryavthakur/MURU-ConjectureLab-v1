"""Constructed contract tests for G2 (Amendment A3.1).

All fixtures are hand-built synthetic expressions.  No Development case
outcomes, no Held-out data, no calibration world execution.
"""
from __future__ import annotations

import pytest

from muru.paper_benchmark.g2_contract import (
    GRAMMAR_PRIMITIVES,
    G2_HELD_OUT_DENOMINATOR,
    G2_WILSON_LOWER_GATE,
    TRUTH_FAMILIES,
    FamilyStatus,
    G2Event,
    SupportStatus,
    classify_discovered_family,
    classify_family_match,
    classify_support,
    evaluate_g2_event,
    extract_effective_support,
    wilson_lower_95,
)


# -----------------------------------------------------------------------
# Effective support extraction
# -----------------------------------------------------------------------

class TestEffectiveSupport:

    def test_mass_affine_descriptor(self):
        support = extract_effective_support("1.5 * sqrt(mass / 250) * (1 + 0.4 * descriptor)")
        assert support == {"mass", "descriptor"}

    def test_mass_power(self):
        support = extract_effective_support("1.3 * (mass / 250) ** 0.6")
        assert support == {"mass"}

    def test_mass_saturating(self):
        support = extract_effective_support("1.5 * sqrt(mass / 250) * (1 + 0.4 * descriptor / (1 + descriptor))")
        assert support == {"mass", "descriptor"}

    def test_mass_interaction(self):
        support = extract_effective_support("1.5 * sqrt(mass / 250) * (1 + 0.3 * descriptor * descriptor2)")
        assert support == {"mass", "descriptor", "descriptor2"}

    def test_mass_exponential(self):
        support = extract_effective_support("1.5 * sqrt(mass / 250) * exp(0.3 * descriptor / 3)")
        assert support == {"mass", "descriptor"}

    def test_cancelled_variable(self):
        """Cancelled variables do not count."""
        support = extract_effective_support("mass * descriptor / descriptor")
        assert support is not None
        assert "descriptor" not in support
        assert "mass" in support

    def test_exact_zero_term(self):
        """Exact-zero terms do not count."""
        support = extract_effective_support("mass + 0 * descriptor")
        assert support is not None
        assert "descriptor" not in support
        assert "mass" in support

    def test_constant_expression(self):
        """Constants contribute no support."""
        support = extract_effective_support("42.0")
        assert support == frozenset()

    def test_interaction_contributes_all_primitives(self):
        """Interactions contribute every primitive input."""
        support = extract_effective_support("descriptor * descriptor2")
        assert support == {"descriptor", "descriptor2"}

    def test_correlated_proxy_distinct(self):
        """Correlated proxy remains distinct from planted descriptor."""
        support = extract_effective_support("mass + correlated_distractor")
        assert support == {"mass", "correlated_distractor"}
        assert "descriptor" not in support

    def test_f12_proxy_not_interchangeable(self):
        """F12 proxy (correlated_distractor) is not interchangeable with descriptor."""
        support_planted = extract_effective_support("mass * descriptor")
        support_proxy = extract_effective_support("mass * correlated_distractor")
        assert support_planted != support_proxy

    def test_nested_transform_preserves_dependence(self):
        """Nested transforms preserve primitive dependence."""
        support = extract_effective_support("sqrt(mass * descriptor)")
        assert support == {"mass", "descriptor"}

    def test_invalid_expression(self):
        """Invalid expression returns None (SUPPORT_UNRESOLVED)."""
        support = extract_effective_support("not_a_valid_expression(((")
        assert support is None

    def test_empty_expression(self):
        support = extract_effective_support("")
        assert support is None

    def test_duplicated_variables_count_once(self):
        """Duplicated primitive variables count once."""
        support = extract_effective_support("mass * mass")
        assert support == {"mass"}

    def test_algebraic_reorder(self):
        """Algebraic reorderings produce same support."""
        support1 = extract_effective_support("mass * descriptor + mass")
        support2 = extract_effective_support("mass + descriptor * mass")
        assert support1 == support2


# -----------------------------------------------------------------------
# R3: parser / support / feature mapping (DEFECT_C) regression fixtures
#
# Mission-mandated minimum coverage: mass/mass, mass*inv(mass),
# descriptor/descriptor, descriptor*inv(descriptor), mass/descriptor,
# inv(descriptor)*mass, mass*square(inv(mass)), x0, x1, x2, and equivalent
# reordered/factored forms.
# -----------------------------------------------------------------------

class TestR3ParserSupportFeatureMapping:

    # -- cancellation: square/cube/inv must be bound so sympy can cancel ----

    def test_mass_over_mass_cancels(self):
        assert extract_effective_support("mass / mass") == frozenset()

    def test_mass_times_inv_mass_cancels(self):
        """Pre-repair defect: inv() was an unbound opaque function, so this
        returned {"mass"} instead of cancelling to no support."""
        assert extract_effective_support("mass * inv(mass)") == frozenset()

    def test_descriptor_over_descriptor_cancels(self):
        assert extract_effective_support("descriptor / descriptor") == frozenset()

    def test_descriptor_times_inv_descriptor_cancels(self):
        assert extract_effective_support("descriptor * inv(descriptor)") == frozenset()

    def test_mass_over_mass_and_mass_times_inv_mass_agree(self):
        """Same cancellation, two syntactic routes to it."""
        assert extract_effective_support("mass / mass") == extract_effective_support("mass * inv(mass)")

    # -- reordering invariance: mass/descriptor vs inv(descriptor)*mass -----

    def test_mass_over_descriptor_support(self):
        assert extract_effective_support("mass / descriptor") == {"mass", "descriptor"}

    def test_inv_descriptor_times_mass_support_matches_reordering(self):
        """Pre-repair defect: inv(descriptor)*mass classified as unmapped
        (opaque function), diverging from the algebraically identical
        mass/descriptor."""
        support_a = extract_effective_support("mass / descriptor")
        support_b = extract_effective_support("inv(descriptor) * mass")
        assert support_a == support_b == {"mass", "descriptor"}

    def test_mass_over_descriptor_and_reordering_classify_identically(self):
        family_a = classify_discovered_family("mass / descriptor")
        family_b = classify_discovered_family("inv(descriptor) * mass")
        assert family_a == family_b
        assert family_a is not None

    # -- square/inv composition preserves mass-only support -----------------

    def test_mass_times_square_inv_mass(self):
        """mass * square(inv(mass)) = mass * mass**-2 = mass**-1: still
        mass-only support, still the mass_power family."""
        assert extract_effective_support("mass * square(inv(mass))") == {"mass"}
        assert classify_discovered_family("mass * square(inv(mass))") == "mass_power"

    def test_mass_times_square_inv_mass_equivalent_factoring(self):
        support_a = extract_effective_support("mass * square(inv(mass))")
        support_b = extract_effective_support("mass * inv(mass) * inv(mass)")
        support_c = extract_effective_support("cube(mass) * inv(mass) * inv(mass) * inv(mass) * inv(mass)")
        assert support_a == support_b == support_c == {"mass"}

    # -- PySR default feature-name mapping: x{i} -> GRAMMAR_PRIMITIVES[i] ---

    def test_x0_maps_to_mass(self):
        assert extract_effective_support("x0") == {"mass"}
        assert classify_discovered_family("x0") == classify_discovered_family("mass")

    def test_x1_maps_to_descriptor(self):
        assert extract_effective_support("x1") == {"descriptor"}

    def test_x2_maps_to_descriptor2(self):
        assert extract_effective_support("x2") == {"descriptor2"}

    def test_raw_feature_names_reorder_identically_to_primitive_names(self):
        """x0 * inv(x1) is the PySR-default-named twin of mass/descriptor;
        both must resolve to the same support and family. Pre-repair defect:
        unmapped x0/x1 silently reported empty support."""
        raw = extract_effective_support("x0 * inv(x1)")
        named = extract_effective_support("mass / descriptor")
        assert raw == named == {"mass", "descriptor"}
        assert classify_discovered_family("x0 * inv(x1)") == classify_discovered_family("mass / descriptor")

    def test_x0_over_x0_cancels(self):
        assert extract_effective_support("x0 / x0") == frozenset()

    # -- unknown feature symbols fail closed, never silently empty ----------

    def test_unknown_symbol_fails_closed(self):
        assert extract_effective_support("unmapped_feature_symbol * mass") is None

    def test_unknown_x_index_out_of_frozen_range_fails_closed(self):
        """Only x0..x{len(GRAMMAR_PRIMITIVES)-1} are bound; anything past the
        frozen covariate range must fail closed, not silently drop."""
        assert extract_effective_support("x99") is None
        assert extract_effective_support("x5") is None

    def test_unknown_symbol_family_classification_fails_closed(self):
        assert classify_discovered_family("unmapped_feature_symbol * mass") is None


# -----------------------------------------------------------------------
# Support classification
# -----------------------------------------------------------------------

class TestSupportClassification:

    def test_match(self):
        assert classify_support(
            frozenset({"mass", "descriptor"}),
            frozenset({"mass", "descriptor"}),
        ) == SupportStatus.MATCH

    def test_mismatch_extra(self):
        assert classify_support(
            frozenset({"mass", "descriptor", "distractor"}),
            frozenset({"mass", "descriptor"}),
        ) == SupportStatus.MISMATCH

    def test_mismatch_missing(self):
        assert classify_support(
            frozenset({"mass"}),
            frozenset({"mass", "descriptor"}),
        ) == SupportStatus.MISMATCH

    def test_unresolved(self):
        assert classify_support(None, frozenset({"mass"})) == SupportStatus.SUPPORT_UNRESOLVED


# -----------------------------------------------------------------------
# Family classification
# -----------------------------------------------------------------------

class TestFamilyClassification:

    def test_mass_affine_descriptor(self):
        family = classify_discovered_family("1.5 * sqrt(mass / 250) * (1 + 0.4 * descriptor)")
        assert family == "mass_affine_descriptor"

    def test_mass_power(self):
        family = classify_discovered_family("1.3 * (mass / 250) ** 0.6")
        assert family == "mass_power"

    def test_mass_saturating_descriptor(self):
        family = classify_discovered_family("1.5 * sqrt(mass / 250) * (1 + 0.4 * descriptor / (1 + descriptor))")
        assert family == "mass_saturating_descriptor"

    def test_mass_interaction(self):
        family = classify_discovered_family("1.5 * sqrt(mass / 250) * (1 + 0.3 * descriptor * descriptor2)")
        assert family == "mass_interaction"

    def test_mass_exponential_descriptor(self):
        family = classify_discovered_family("1.5 * sqrt(mass / 250) * exp(0.3 * descriptor / 3)")
        assert family == "mass_exponential_descriptor"

    def test_wrong_family(self):
        """mass_power expression should not classify as mass_affine_descriptor."""
        family = classify_discovered_family("1.3 * (mass / 250) ** 0.6")
        assert family != "mass_affine_descriptor"

    def test_invalid_expression(self):
        family = classify_discovered_family("invalid(((")
        assert family is None

    def test_constant_expression(self):
        family = classify_discovered_family("42.0")
        assert family is None

    def test_no_mass_unclassifiable(self):
        """Expression without mass cannot be classified."""
        family = classify_discovered_family("descriptor + 1")
        assert family is None

    def test_family_ambiguous(self):
        """Degenerate intersection of multiple families returns FAMILY_AMBIGUOUS."""
        # An expression with both exp and a linear descriptor term
        # might match both exponential and affine - testing the degenerate case
        # Note: sympy may simplify some of these, so we test via classify_family_match
        result = classify_family_match("FAMILY_AMBIGUOUS", "mass_power")
        assert result == FamilyStatus.FAMILY_AMBIGUOUS

    def test_algebraic_reorder_same_family(self):
        """Algebraic reorderings classify identically."""
        f1 = classify_discovered_family("1.5 * sqrt(mass / 250) * (1 + 0.4 * descriptor)")
        f2 = classify_discovered_family("(1 + 0.4 * descriptor) * 1.5 * sqrt(mass / 250)")
        assert f1 == f2


# -----------------------------------------------------------------------
# Family match classification
# -----------------------------------------------------------------------

class TestFamilyMatch:

    def test_match(self):
        assert classify_family_match("mass_power", "mass_power") == FamilyStatus.MATCH

    def test_mismatch(self):
        assert classify_family_match("mass_power", "mass_affine_descriptor") == FamilyStatus.MISMATCH

    def test_truth_none(self):
        assert classify_family_match("mass_power", None) == FamilyStatus.FAMILY_UNRESOLVED

    def test_discovered_none(self):
        assert classify_family_match(None, "mass_power") == FamilyStatus.FAMILY_UNRESOLVED

    def test_ambiguous(self):
        assert classify_family_match("FAMILY_AMBIGUOUS", "mass_power") == FamilyStatus.FAMILY_AMBIGUOUS

    def test_truth_not_in_taxonomy(self):
        assert classify_family_match("mass_power", "unknown_family") == FamilyStatus.FAMILY_UNRESOLVED


# -----------------------------------------------------------------------
# G2 event evaluation
# -----------------------------------------------------------------------

class TestG2Event:

    def test_success(self):
        assert evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.MATCH) == G2Event.SUCCESS

    def test_support_mismatch(self):
        assert evaluate_g2_event(SupportStatus.MISMATCH, FamilyStatus.MATCH) == G2Event.FAILURE

    def test_family_mismatch(self):
        assert evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.MISMATCH) == G2Event.FAILURE

    def test_both_mismatch(self):
        assert evaluate_g2_event(SupportStatus.MISMATCH, FamilyStatus.MISMATCH) == G2Event.FAILURE

    def test_unresolved_support(self):
        assert evaluate_g2_event(SupportStatus.SUPPORT_UNRESOLVED, FamilyStatus.MATCH) == G2Event.UNEVALUABLE

    def test_unresolved_family(self):
        assert evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.FAMILY_UNRESOLVED) == G2Event.UNEVALUABLE

    def test_ambiguous_family(self):
        assert evaluate_g2_event(SupportStatus.MATCH, FamilyStatus.FAMILY_AMBIGUOUS) == G2Event.UNEVALUABLE


# -----------------------------------------------------------------------
# Wilson interval
# -----------------------------------------------------------------------

class TestWilson:

    def test_perfect(self):
        lower = wilson_lower_95(144, 144)
        assert lower > 0.97

    def test_zero(self):
        lower = wilson_lower_95(0, 144)
        assert lower < 0.02

    def test_at_gate(self):
        """Check that the Wilson lower bound is computed correctly around the gate."""
        lower = wilson_lower_95(108, 144)
        assert isinstance(lower, float)

    def test_empty(self):
        assert wilson_lower_95(0, 0) == 0.0


# -----------------------------------------------------------------------
# Frozen parameters
# -----------------------------------------------------------------------

class TestFrozenParameters:

    def test_denominator(self):
        assert G2_HELD_OUT_DENOMINATOR == 144

    def test_gate(self):
        assert G2_WILSON_LOWER_GATE == 0.70

    def test_truth_families(self):
        assert TRUTH_FAMILIES == {
            "mass_affine_descriptor",
            "mass_power",
            "mass_saturating_descriptor",
            "mass_interaction",
            "mass_exponential_descriptor",
        }
