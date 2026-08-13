"""Immutable benchmark registry and endpoint applicability.

The registry is the sole authority for the case population.  It intentionally
contains metadata only: it cannot load inputs, truth values, outcomes, or
real-world records.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

ROOT_SEED = 20260813
ENERGY_GRID = (15, 30, 45, 60, 75, 90)
PARTITIONS = ("development", "held_out", "challenge")
PARTITION_CASE_COUNTS = {"development": 4, "held_out": 12, "challenge": 3}


@dataclass(frozen=True)
class VariantSpec:
    """Variant-specific scientific truth and endpoint applicability."""

    code: str
    scalar_truth_defined: bool
    m0_adequacy_truth: str
    symbolic_truth_kind: str
    endpoint_names: frozenset[str]
    expected_behavior: str
    generative_kind: str


@dataclass(frozen=True)
class FamilySpec:
    """One of the 20 prospectively defined benchmark families."""

    code: str
    name: str
    scientific_question: str
    partition_counts: Mapping[str, int]
    variants: Mapping[str, VariantSpec]
    variant_cycle: tuple[str, ...] = field(default=("BASE",))

    def variant_for_replicate(self, replicate: int) -> VariantSpec:
        return self.variants[self.variant_cycle[replicate % len(self.variant_cycle)]]

    def held_out_cases_for(self, endpoint_name: str) -> int:
        count = 0
        for replicate in range(self.partition_counts["held_out"]):
            if endpoint_name in self.variant_for_replicate(replicate).endpoint_names:
                count += 1
        return count


@dataclass(frozen=True)
class EndpointSpec:
    """A named endpoint whose held-out denominator comes from the registry."""

    name: str
    role: str
    description: str


def _endpoints(*names: str) -> frozenset[str]:
    return frozenset(names)


SCALAR_ENDPOINTS = _endpoints(
    "scalar_competence",
    "scalar_target_yield",
    "g_recovery",
    "trajectory_prediction",
    "profile_stability",
    "m0_specificity",
)
SYMBOLIC_ENDPOINTS = _endpoints(
    "family_recovery",
    "support_recovery",
    "parameter_recovery",
    "predictive_equivalence",
)


def _base_variant(
    code: str,
    *,
    scalar: bool,
    adequacy: str,
    symbolic: str,
    endpoints: frozenset[str],
    expected: str,
    kind: str,
) -> dict[str, VariantSpec]:
    return {
        "BASE": VariantSpec(
            code=code,
            scalar_truth_defined=scalar,
            m0_adequacy_truth=adequacy,
            symbolic_truth_kind=symbolic,
            endpoint_names=endpoints,
            expected_behavior=expected,
            generative_kind=kind,
        )
    }


def _family(
    code: str,
    name: str,
    question: str,
    *,
    scalar: bool,
    adequacy: str,
    symbolic: str,
    endpoints: frozenset[str],
    expected: str,
    kind: str,
) -> FamilySpec:
    return FamilySpec(
        code=code,
        name=name,
        scientific_question=question,
        partition_counts=PARTITION_CASE_COUNTS,
        variants=_base_variant(
            code,
            scalar=scalar,
            adequacy=adequacy,
            symbolic=symbolic,
            endpoints=endpoints,
            expected=expected,
            kind=kind,
        ),
    )


CASE_FAMILIES: tuple[FamilySpec, ...] = (
    _family("F01", "noiseless scalar collapse", "recover unambiguous collapse", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS | _endpoints("exact_algebra"), expected="recover scalar and family", kind="scalar_noiseless"),
    _family("F02", "moderate-noise scalar collapse", "recover under moderate noise", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS, expected="recover scalar and family", kind="scalar_moderate"),
    _family("F03", "stronger realistic noise", "characterize graceful degradation", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS, expected="report degradation without false structure", kind="scalar_strong"),
    _family("F04", "missing-one-energy", "recover with declared missingness", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS, expected="recover with missingness diagnostics", kind="missing_one_energy"),
    _family("F05", "boundary-scale", "detect profile boundaries", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS | _endpoints("boundary_hit"), expected="report boundary diagnostics", kind="boundary_scale"),
    _family("F06", "no molecule-specific scalar truth", "reject an unsupported scalar", scalar=False, adequacy="M1", symbolic="none", endpoints=_endpoints("m1_sensitivity"), expected="reject M0", kind="no_scalar"),
    _family("F07", "mass-only g truth", "avoid invented non-mass structure", scalar=True, adequacy="M0", symbolic="mass_only", endpoints=SCALAR_ENDPOINTS | _endpoints("parameter_recovery", "false_extra_structure", "principal_structural_safety"), expected="accept mass only and reject richer structure", kind="mass_only"),
    _family("F08", "simple descriptor law", "recover a monotone descriptor law", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS | _endpoints("exact_algebra"), expected="recover family", kind="simple_descriptor"),
    _family("F09", "nonlinear descriptor law", "recognize saturation", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS | _endpoints("exact_algebra"), expected="recover saturating family", kind="nonlinear_descriptor"),
    _family("F10", "interaction law", "recognize interpretable interaction", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS | _endpoints("exact_algebra"), expected="recover interaction family", kind="interaction"),
    _family("F11", "irrelevant distractors", "exclude independent nuisance variables", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS, expected="recover sparse support", kind="irrelevant_distractors"),
    _family("F12", "correlated distractors", "separate support from correlation", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS, expected="report support ambiguity correctly", kind="correlated_distractors"),
    _family("F13", "horizontal-shape violation", "detect M1", scalar=False, adequacy="M1", symbolic="none", endpoints=_endpoints("m1_sensitivity"), expected="reject M0 in favor of M1", kind="m1_horizontal"),
    _family("F14", "high-energy vertical violation", "detect M2", scalar=False, adequacy="M2", symbolic="none", endpoints=_endpoints("m2_sensitivity"), expected="reject M0 in favor of M2", kind="m2_high_energy"),
    _family("F15", "low-energy vertical violation", "detect M3", scalar=False, adequacy="M3", symbolic="none", endpoints=_endpoints("m3_sensitivity"), expected="reject M0 in favor of M3", kind="m3_low_energy"),
    _family("F16", "combined mild non-scalar violation", "flag combined violations", scalar=False, adequacy="M1+M2+M3", symbolic="none", endpoints=_endpoints("m1_sensitivity", "m2_sensitivity", "m3_sensitivity"), expected="flag at least one violation", kind="combined_violation"),
    _family("F17", "equivalent symbolic forms", "canonicalize equivalent laws", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS | _endpoints("exact_algebra"), expected="score equivalent forms once", kind="equivalent_forms"),
    _family("F18", "algebraically difficult predictively simple", "separate prediction from exact algebra", scalar=True, adequacy="M0", symbolic="defined", endpoints=SCALAR_ENDPOINTS | SYMBOLIC_ENDPOINTS, expected="report predictive equivalence separately", kind="difficult_algebra"),
    FamilySpec(
        code="F19",
        name="target-specific null worlds",
        scientific_question="prevent the specified null structure from being accepted",
        partition_counts=PARTITION_CASE_COUNTS,
        variants={
            "F19A": VariantSpec("F19A", True, "M0", "none", SCALAR_ENDPOINTS | _endpoints("false_null_structure", "principal_structural_safety"), "descriptor link destroyed; descriptor acceptance is false-null structure", "descriptor_link_permutation"),
            "F19B": VariantSpec("F19B", True, "M0", "mass_only_allowance", SCALAR_ENDPOINTS | _endpoints("false_null_structure", "principal_structural_safety"), "mass-only allowance; non-mass acceptance is false-null structure", "mass_preserving_null"),
            "F19C": VariantSpec("F19C", False, "not_applicable", "none", _endpoints("false_null_structure", "principal_structural_safety", "response_structure_diagnostic"), "trajectory destruction must be flagged non-evaluable", "response_cell_resampling"),
        },
        variant_cycle=("F19A", "F19B", "F19C"),
    ),
    FamilySpec(
        code="F20",
        name="adversarial worlds",
        scientific_question="reject or flag specified traps",
        partition_counts=PARTITION_CASE_COUNTS,
        variants={
            "F20A": VariantSpec("F20A", False, "not_applicable", "none", _endpoints("false_adversarial_structure", "principal_structural_safety"), "flag latent driver", "latent_driver"),
            "F20B": VariantSpec("F20B", False, "not_applicable", "none", _endpoints("false_adversarial_structure", "principal_structural_safety"), "flag measurement coupling", "measurement_coupling"),
            "F20C": VariantSpec("F20C", False, "not_applicable", "none", _endpoints("false_adversarial_structure", "principal_structural_safety"), "reject out-of-grammar trap", "out_of_grammar"),
        },
        variant_cycle=("F20A", "F20B", "F20C"),
    ),
)

ENDPOINTS = {
    "scalar_competence": EndpointSpec("scalar_competence", "primary_scalar", "G1 scalar competence"),
    "family_recovery": EndpointSpec("family_recovery", "primary_symbolic", "G2 family recovery"),
    "principal_structural_safety": EndpointSpec("principal_structural_safety", "primary_safety", "G3 combined safety"),
}


def _family_by_code(code: str) -> FamilySpec:
    for family in CASE_FAMILIES:
        if family.code == code:
            return family
    raise ValueError(f"unknown benchmark family: {code}")


def endpoint_applies_to_variant(endpoint_name: str, variant: VariantSpec) -> bool:
    return endpoint_name in variant.endpoint_names


def endpoint_case_count(endpoint_name: str) -> int:
    return sum(family.held_out_cases_for(endpoint_name) for family in CASE_FAMILIES)


def resolve_case_id(case_id: str) -> tuple[FamilySpec, VariantSpec, int]:
    """Resolve a case identifier without generating or loading its contents."""
    parts = case_id.split("|")
    if len(parts) != 4 or parts[0] != "PB":
        raise ValueError(f"invalid case id: {case_id}")
    _, partition, family_code, replicate_text = parts
    if partition not in PARTITIONS or not replicate_text.startswith("r"):
        raise ValueError(f"invalid case id: {case_id}")
    try:
        replicate = int(replicate_text[1:])
    except ValueError as exc:
        raise ValueError(f"invalid case id: {case_id}") from exc
    family = _family_by_code(family_code)
    if not 0 <= replicate < family.partition_counts[partition]:
        raise ValueError(f"replicate outside partition range: {case_id}")
    return family, family.variant_for_replicate(replicate), replicate


def iter_case_ids(partition: str) -> Iterable[str]:
    """Yield case IDs for internal artifact construction only."""
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    for family in CASE_FAMILIES:
        for replicate in range(family.partition_counts[partition]):
            yield f"PB|{partition}|{family.code}|r{replicate:03d}"
