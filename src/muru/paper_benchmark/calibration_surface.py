"""Calibration surface population — MURU v2 re-entry, Route R-B (protocol v2 section 5.2).

This module declares a calibration population ENTIRELY OUTSIDE the byte-frozen
benchmark files. It imports `registry` and `generator` read-only and mutates
nothing in them. No protected path changes; `pb_33`/`pb_34` are unaffected.

Case-id namespace is `PBC`, not `PB`:

    PBC|calibration|<family_code>|r<replicate:03d>

`registry.resolve_case_id` rejects any id whose first field is not "PB", so the
frozen resolver cannot be fed a calibration id and no existing `case_ordinal`,
seed or manifest can move. Because `generator.derive_seed` hashes the full
case-id string, the `PBC` prefix also makes every calibration draw statistically
independent of the `held_out`, `development` and `challenge` draws at the same
family and replicate.

The calibration surface is NOT a benchmark partition. `iter_case_ids("calibration")`
still raises, and the benchmark's case population remains the frozen 380.
"""
from __future__ import annotations

import pandas as pd

from . import registry
from . import generator
from .generator import (
    ENERGY_GRID, GENERATOR_VERSION, CaseInputs, GeneratedCase, TruthRecord,
    derive_seed, scientific_payload_hash, _law, _response_matrix, _rng,
    _synthetic_compounds,
)

# ----------------------------------------------------------------- population
CALIBRATION_REPLICATES = 138


def _g2_families_from_registry() -> tuple[str, ...]:
    """DEF-M7: DERIVE the twelve G2 families from a predicate over the frozen
    registry, instead of hand-transcribing a literal tuple under a citation that
    points at eighteen families.

    A family is in the G2 primary stratum iff EVERY variant it can present declares
    `symbolic_truth_kind == "defined"` -- i.e. there is a genuine symbolic truth to
    recover, in every replicate, with no mass-only allowance and no null variant.

    This cleanly separates the three groups the registry actually declares:
      "defined"             -> a symbolic truth exists                   -> G2 primary
      "mass_only"           -> F07: mass-only truth, accepting a         -> NEG control
                               descriptor IS false structure
      "none" / "mass_only_allowance" (F19A/B/C), or no g_recovery at all
                            -> null or non-G2-relevant                   -> NEG / excluded
    """
    out = []
    for fam in registry.CASE_FAMILIES:
        variants = {fam.variant_for_replicate(r) for r in range(CALIBRATION_REPLICATES)}
        if variants and all(v.symbolic_truth_kind == "defined" for v in variants):
            out.append(fam.code)
    return tuple(out)


def _neg_families_from_registry() -> tuple[str, ...]:
    """The negative-control stratum: families for which accepting non-mass structure
    is by declaration FALSE structure -- either the family carries the
    `false_null_structure` endpoint (F19A/B/C), or its truth is mass-only so any
    descriptor acceptance is spurious (F07)."""
    out = []
    for fam in registry.CASE_FAMILIES:
        variants = {fam.variant_for_replicate(r) for r in range(CALIBRATION_REPLICATES)}
        if not variants:
            continue
        if all("false_null_structure" in v.endpoint_names or
               v.symbolic_truth_kind == "mass_only" for v in variants):
            out.append(fam.code)
    return tuple(out)


CALIBRATION_G2_FAMILIES = _g2_families_from_registry()
CALIBRATION_NEG_FAMILIES = _neg_families_from_registry()
CALIBRATION_FAMILIES = CALIBRATION_G2_FAMILIES + CALIBRATION_NEG_FAMILIES

#: The literals v2 declared, retained ONLY as an assertion target so that the
#: derived predicate is checked against the intended population rather than
#: silently replacing it.
_EXPECTED_G2 = ("F01", "F02", "F03", "F04", "F05", "F08",
                "F09", "F10", "F11", "F12", "F17", "F18")
_EXPECTED_NEG = ("F07", "F19")

CALIBRATION_PREFIX = "PBC"
CALIBRATION_PARTITION = "calibration"

_FAMILY_BY_CODE = {f.code: f for f in registry.CASE_FAMILIES}


def calibration_case_id(family_code: str, replicate: int) -> str:
    if family_code not in CALIBRATION_FAMILIES:
        raise ValueError(f"family {family_code} is not in the calibration surface")
    if not 0 <= replicate < CALIBRATION_REPLICATES:
        raise ValueError(f"replicate {replicate} out of range")
    return f"{CALIBRATION_PREFIX}|{CALIBRATION_PARTITION}|{family_code}|r{replicate:03d}"


def iter_calibration_case_ids() -> list[str]:
    """Family-major over the 14 declared families, then replicate. This ordering
    defines `calibration_ordinal` and is fixed by this module (protocol v2 5.2)."""
    return [calibration_case_id(fc, r)
            for fc in CALIBRATION_FAMILIES
            for r in range(CALIBRATION_REPLICATES)]


def calibration_ordinal(case_id: str) -> int:
    try:
        return iter_calibration_case_ids().index(case_id)
    except ValueError:
        raise ValueError(f"not a calibration case id: {case_id}") from None


def resolve_calibration_case_id(case_id: str):
    """The ONLY thing this module changes relative to `generator.generate_case`."""
    parts = case_id.split("|")
    if len(parts) != 4 or parts[0] != CALIBRATION_PREFIX or parts[1] != CALIBRATION_PARTITION:
        raise ValueError(f"invalid calibration case id: {case_id}")
    family_code, rep_field = parts[2], parts[3]
    if family_code not in _FAMILY_BY_CODE:
        raise ValueError(f"unknown family: {family_code}")
    if not (rep_field.startswith("r") and rep_field[1:].isdigit()):
        raise ValueError(f"invalid replicate field: {rep_field}")
    replicate = int(rep_field[1:])
    family = _FAMILY_BY_CODE[family_code]
    return family, family.variant_for_replicate(replicate), replicate


# ------------------------------------------------------- the generative body
def generate_case_body(case_id: str, family, variant) -> GeneratedCase:
    """VERBATIM the body of `generator.generate_case`, with the resolver hoisted
    out. Every call below is the frozen function, imported unmodified.

    Kept line-for-line identical to `generator.generate_case` so that control
    C-0 is a meaningful equivalence test rather than a restatement.
    """
    compounds, seeds = _synthetic_compounds(case_id)
    law_rng, law_seed = _rng(case_id, "law")
    response_rng, response_seed = _rng(case_id, "response")
    g, mathematical_family, active, relationship, coefficients, exponents = _law(variant.generative_kind, compounds, law_rng)
    mu, noise, missingness, phi, generated_adequacy = _response_matrix(variant.generative_kind, g, compounds, response_rng)
    rows: list[dict[str, object]] = []
    for i, compound_id in enumerate(compounds.compound_id):
        omitted = (i + derive_seed(case_id, "missing")) % len(ENERGY_GRID) if missingness["mechanism"] != "none" else None
        for j, energy in enumerate(ENERGY_GRID):
            if j == omitted:
                continue
            rows.append({"compound_id": compound_id, "energy": energy, "mu": float(mu[i, j])})
    trajectories = pd.DataFrame(rows)
    seeds.update({"law": law_seed, "response": response_seed, "missingness": derive_seed(case_id, "missing")})
    truth = TruthRecord(
        case_id=case_id,
        partition=case_id.split("|")[1],
        family=family.code,
        variant=variant.code,
        seeds=seeds,
        phi={"family": "stretched_exponential", **phi},
        g_definition=relationship,
        g_by_compound={} if not variant.scalar_truth_defined or g is None else {key: float(value) for key, value in zip(compounds.compound_id, g)},
        descriptor_relationship=relationship,
        active_variables=active,
        mathematical_family=mathematical_family,
        coefficients=coefficients,
        exponents=exponents,
        noise=noise,
        missingness=missingness,
        scalar_truth_defined=variant.scalar_truth_defined,
        m0_adequacy_truth=variant.m0_adequacy_truth if variant.m0_adequacy_truth != "M0" else generated_adequacy,
        symbolic_truth_kind=variant.symbolic_truth_kind,
        applicable_endpoints=sorted(variant.endpoint_names),
        expected_behavior=variant.expected_behavior,
    )
    inputs = CaseInputs(compounds=compounds, trajectories=trajectories)
    content_hash = scientific_payload_hash(inputs, truth, GENERATOR_VERSION)
    return GeneratedCase(case_id=case_id, inputs=inputs, truth=truth, content_hash=content_hash)


def generate_calibration_case(case_id: str) -> GeneratedCase:
    family, variant, _ = resolve_calibration_case_id(case_id)
    return generate_case_body(case_id, family, variant)


# --------------------------------------------------------------- control C-0
def control_c0() -> dict:
    """MANDATORY equivalence control (protocol v2 5.2).

    For every one of the frozen benchmark case ids, the duplicated body must
    reproduce `generator.generate_case`'s content_hash EXACTLY. Duplicating a
    frozen generator is a risk; C-0 discharges it exhaustively rather than by
    argument.

    C-0 fails => Route R-B is abandoned and Route R-A is attempted (5.3).
    NO WORLD IS GENERATED UNDER A FAILING C-0.
    """
    ids: list[str] = []
    for partition in ("development", "held_out", "challenge"):
        try:
            ids.extend(registry.iter_case_ids(partition))
        except Exception:
            pass
    mismatches = []
    for cid in ids:
        family, variant, _ = registry.resolve_case_id(cid)
        mine = generate_case_body(cid, family, variant).content_hash
        theirs = generator.generate_case(cid).content_hash
        if mine != theirs:
            mismatches.append({"case_id": cid, "body": mine, "frozen": theirs})
    return {"control": "C-0", "n_cases": len(ids), "n_mismatched": len(mismatches),
            "mismatches": mismatches[:20], "passed": len(ids) > 0 and not mismatches,
            "generator_version": GENERATOR_VERSION}


# DEF-M7: the derived predicate must reproduce the intended population exactly. If the
# registry ever changes such that it does not, the module refuses to import rather than
# silently redefining the calibration population.
if CALIBRATION_G2_FAMILIES != _EXPECTED_G2:
    raise AssertionError(
        f"G2 stratum predicate no longer reproduces the declared population:\n"
        f"  derived  {CALIBRATION_G2_FAMILIES}\n  expected {_EXPECTED_G2}")
if CALIBRATION_NEG_FAMILIES != _EXPECTED_NEG:
    raise AssertionError(
        f"NEG stratum predicate no longer reproduces the declared population:\n"
        f"  derived  {CALIBRATION_NEG_FAMILIES}\n  expected {_EXPECTED_NEG}")
