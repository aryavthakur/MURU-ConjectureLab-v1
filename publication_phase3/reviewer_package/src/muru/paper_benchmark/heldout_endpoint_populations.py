"""Endpoint populations built from the frozen registry, never from record counts.

Rescue requirement 1: *"Never compute an endpoint denominator from
``len(case_ids)``.  Build each population via
``registry.endpoint_applies_to_variant(endpoint, variant)`` and assert its size
against ``registry.endpoint_case_count(endpoint)`` before scoring."*

The superseded analyzer set ``total_cases = len(expected_case_ids)`` once and
passed that single value as the denominator for G1, G2, G3, Gate 7, Gate 8 and
F9 alike.  Endpoint eligibility was never consulted: ``endpoint_applies_to_variant``
and ``endpoint_case_count`` appear in no post-run module.  The result inflated
G1 by 46%, G2 by 67% and G3 by 567%, and credited families with zero
applicability (F07 and F19 contributed 16 of the 23 reported G2 "successes"
despite carrying no ``family_recovery`` endpoint at all).

240 is the Held-out **case population**.  No frozen endpoint has a denominator
of 240, and 164 + 144 + 36 = 344 ≠ 240 because the endpoints overlap and five
families (F06, F13, F14, F15, F16) carry no primary endpoint whatsoever.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .registry import (
    ENDPOINTS,
    endpoint_applies_to_variant,
    endpoint_case_count,
    iter_case_ids,
    resolve_case_id,
)

__all__ = [
    "HELD_OUT_PARTITION",
    "PopulationError",
    "EndpointPopulation",
    "build_endpoint_population",
    "build_all_primary_populations",
    "held_out_case_ids",
    "variant_code_for_case",
]

HELD_OUT_PARTITION = "held_out"


class PopulationError(RuntimeError):
    """A built endpoint population disagrees with the frozen registry."""


@dataclass(frozen=True)
class EndpointPopulation:
    """The ordered, registry-derived case population for one endpoint."""

    endpoint_name: str
    role: str
    case_ids: tuple[str, ...]
    denominator: int

    def __post_init__(self) -> None:
        if len(self.case_ids) != self.denominator:
            raise PopulationError(
                f"{self.endpoint_name}: built {len(self.case_ids)} cases but the "
                f"frozen denominator is {self.denominator}"
            )
        if len(set(self.case_ids)) != len(self.case_ids):
            raise PopulationError(f"{self.endpoint_name}: duplicate case ids")

    @property
    def case_id_set(self) -> frozenset[str]:
        return frozenset(self.case_ids)


def held_out_case_ids() -> tuple[str, ...]:
    """The 240 Held-out case ids, in registry order."""
    return tuple(iter_case_ids(HELD_OUT_PARTITION))


def variant_code_for_case(case_id: str) -> str:
    """The variant code the frozen registry assigns to this case.

    This is the value ``g3_contract.classify_g3_event`` dispatches on, and it
    is *not* the family id: F19 cycles F19A/F19B/F19C and F20 cycles
    F20A/F20B/F20C across replicates.
    """
    _family, variant, _replicate = resolve_case_id(case_id)
    return variant.code


def build_endpoint_population(endpoint_name: str) -> EndpointPopulation:
    """Build one endpoint's Held-out population from the registry alone.

    Membership comes from ``endpoint_applies_to_variant``; the size is then
    asserted against ``endpoint_case_count``.  Both must agree, so a drift in
    either the variant table or the counting rule is caught rather than
    absorbed.
    """
    if endpoint_name not in ENDPOINTS:
        raise PopulationError(
            f"{endpoint_name!r} is not one of the three frozen primary "
            f"endpoints {sorted(ENDPOINTS)}"
        )

    members: list[str] = []
    for case_id in held_out_case_ids():
        _family, variant, _replicate = resolve_case_id(case_id)
        if endpoint_applies_to_variant(endpoint_name, variant):
            members.append(case_id)

    frozen_denominator = endpoint_case_count(endpoint_name)
    if len(members) != frozen_denominator:
        raise PopulationError(
            f"{endpoint_name}: applicability scan yielded {len(members)} cases, "
            f"registry.endpoint_case_count says {frozen_denominator}; the two "
            f"frozen routes to the denominator disagree"
        )

    return EndpointPopulation(
        endpoint_name=endpoint_name,
        role=ENDPOINTS[endpoint_name].role,
        case_ids=tuple(members),
        denominator=frozen_denominator,
    )


def build_all_primary_populations() -> Mapping[str, EndpointPopulation]:
    """Build all three primary endpoint populations, asserting each."""
    return {name: build_endpoint_population(name) for name in sorted(ENDPOINTS)}
