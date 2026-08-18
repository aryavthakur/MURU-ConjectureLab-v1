"""Engineering RC5 (D9): the two-layer pre-execution manifest.

A3.5 section 8.4 binds two layers:

============================  =======================================  ==========
layer                         content                                  timing
============================  =======================================  ==========
**Global science execution    partition-agnostic rules: the seed-      written once,
plan**                        derivation function and constants, the   before any
                              threshold-table digest, the search-      partition
                              settings digest, the grammar identity,   executes
                              the record schema, and every section
                              3-7 semantic
**Partition pre-execution     that partition's case IDs, its 30xN      written
manifest**                    derived seeds, the environment/host      immediately
                              lock, the resolved engineering parent,   before that
                              output locations, the resume contract    partition runs
============================  =======================================  ==========

**Why per-partition is forced.**  The frozen precedent bakes **per-run host
identity** into the manifest -- ``calibration/a3_2/execution_manifest.json``
carries ``platform``, ``machine``, ``python_version``, ``python_implementation``,
``python_packages``, ``julia``.  One manifest covering three partitions
executed at different times cannot truthfully attest that, and amending a
written manifest is forbidden.

**Identical science is preserved by a binding derivation clause.**  Every
*scientific* field of a partition manifest MUST be a pure function of
``(global plan, partition name)``, byte-reproducible by an independent
verifier.  Nothing scientific is ever chosen at partition-manifest time; only
host/environment facts are new.  That clause is enforced here structurally: a
partition manifest's ``science`` block is *rebuilt* from the plan by
:func:`derive_partition_science` and compared byte-for-byte by
:func:`verify_partition_manifest`, and there is deliberately **no parameter**
through which a caller could inject a scientific value at Layer 2.

**Digest convention (binding).**  The digest is computed over a pinned
canonical JSON serialisation and the convention is stated **inside** the
manifest itself.  This matters concretely: ``calibration/a3_2/execution_manifest.json``
digests to ``9950b964...`` canonically but ``c8350180...`` over raw bytes, so a
verifier hashing raw bytes would raise a false tamper alarm on an intact
manifest.

**Commit fields.**  Section 1's manifest rule: any field typed as a commit MUST
be populated from ``git rev-parse <tag>^{}``, never ``git rev-parse <tag>``.
:func:`resolve_tag_commit` is the only way a commit reaches a manifest here.

**Post-execution provenance is separate and append-only** -- see
:mod:`muru.paper_benchmark.rc5_store`.  A pre-execution manifest is written
once and never appended to; :func:`write_manifest_once` refuses to overwrite.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .calibration_contract import SEARCH_SETTINGS
from .g2_contract import GRAMMAR_PRIMITIVES
from .rc3_acceptance import null_threshold_digest
from .rc3_calibration_runner import FROZEN_SETTINGS_DIGEST
from .rc3_record import RECORD_SCHEMA_VERSION
from .rc5_authorization import assert_partition_authorised
from .registry import ENERGY_GRID, PARTITIONS, iter_case_ids
from .rc5_estimate import (
    A35_LOG_G_GRID_HIGH,
    A35_LOG_G_GRID_LOW,
    A35_LOG_G_GRID_POINTS,
    E_REF,
    N_VALIDATION_COMPOUNDS,
    PHI_ALTERNATIONS,
    PHI_N_KNOTS,
)
from .rc5_falsify import (
    F1_RERUN_COUNT,
    F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX,
    F7_LOSO_FOLDS,
    F9_CALIBRATION_STATUS,
    F9_FOLDS,
    F10_CONSTRUCTIONS,
    REQUIRED_HARD_GATES,
)
from .rc5_g1_bridge import (
    G1_DENOMINATOR,
    G1_SPEARMAN_GATE,
    G1_TRAJECTORY_RATIO_GATE,
    G1_WILSON_LOWER_GATE,
)
from .rc5_seeds import (
    A35_SEARCH_SEED_BASE,
    A35_SEARCH_SEED_MAX,
    A35_SEARCH_SEED_MIN,
    A35_SEEDS_PER_CASE,
    A35_TOTAL_CASES,
    case_ordinal,
    case_search_seeds,
    verify_search_seed_invariants,
)
from .structural_acceptance import (
    CEILING_FRACTION_GATE,
    CEILING_WAIVER_THRESHOLD,
    MAX_COMPLEXITY,
    MAX_INVALID_FRACTION,
    STABILITY_DENOMINATOR,
    STABILITY_GATE,
)

__all__ = [
    "GLOBAL_PLAN_SCHEMA_VERSION",
    "PARTITION_MANIFEST_SCHEMA_VERSION",
    "DIGEST_CONVENTION",
    "RESUME_CONTRACT",
    "ManifestExists",
    "ManifestDerivationError",
    "canonical_manifest_json",
    "manifest_digest",
    "resolve_tag_commit",
    "EnvironmentIdentity",
    "capture_environment",
    "build_global_science_plan",
    "verify_global_plan",
    "derive_partition_science",
    "build_partition_manifest",
    "verify_partition_manifest",
    "write_manifest_once",
]

GLOBAL_PLAN_SCHEMA_VERSION = "muru-rc5-global-science-plan-1.0.0"
PARTITION_MANIFEST_SCHEMA_VERSION = "muru-rc5-partition-execution-manifest-1.0.0"

#: Stated inside every manifest this module writes, per section 8.4.
DIGEST_CONVENTION: dict[str, str] = {
    "algorithm": "sha256",
    "serialization": (
        "json.dumps(payload, sort_keys=True, separators=(',',':'), "
        "ensure_ascii=True, allow_nan=False)"
    ),
    "scope": "the manifest payload with its own 'digest' key removed",
    "note": (
        "computed over the CANONICAL serialization, never over raw file bytes; "
        "hashing raw bytes yields a different value and would raise a false "
        "tamper alarm on an intact manifest"
    ),
}

#: Section 8.2 and section 12, stated in the manifest so a resumed run is
#: governed by the same words the plan was written under.
RESUME_CONTRACT: dict[str, object] = {
    "unit": "case",
    "completed_case_is_never_re_executed": True,
    "per_seed_records_are_append_only": True,
    "duplicate_seed_record_is_refused_on_load": True,
    "replacement_seed": False,
    "retry_that_erases_a_prior_execution_failure": False,
    "case_denominator_is_never_case_conditional": True,
    "any_seed_execution_failure_makes_the_case_unevaluable": True,
    "post_execution_provenance": "separate, append-only, never merged into this manifest",
}


class ManifestExists(RuntimeError):
    """A pre-execution manifest is already written and must not be amended."""


class ManifestDerivationError(RuntimeError):
    """A partition manifest's scientific block is not a pure derivation."""


# -----------------------------------------------------------------------
# Canonical serialization
# -----------------------------------------------------------------------

def canonical_manifest_json(payload: Mapping[str, Any]) -> str:
    """The pinned canonical serialization named in :data:`DIGEST_CONVENTION`."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def manifest_digest(payload: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical serialization, excluding any ``digest`` key."""
    body = {k: v for k, v in payload.items() if k != "digest"}
    return hashlib.sha256(canonical_manifest_json(body).encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------
# Git identity
# -----------------------------------------------------------------------

def _git(*arguments: str, root: Path | None = None) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=str(root) if root else None,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _assert_is_commit(value: str, field: str, root: Path | None = None) -> str:
    """Section 1's manifest rule, enforced rather than merely documented.

    A field typed as a commit must actually be a commit.  Passing an annotated
    tag OBJECT here is exactly the defect section 1 records, and a docstring
    saying "only reachable through resolve_tag_commit" is a convention, not a
    structural property -- so the value is checked.
    """
    if not (isinstance(value, str) and len(value) == 40):
        raise ValueError(f"{field} must be a 40-character commit SHA, got {value!r}")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be lowercase hexadecimal, got {value!r}")
    probe = subprocess.run(
        ["git", "cat-file", "-t", value],
        cwd=str(root) if root else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0 and probe.stdout.strip() != "commit":
        raise ValueError(
            f"{field} is {value} which git reports as a "
            f"{probe.stdout.strip()!r}, not a commit; section 1 requires "
            f"`git rev-parse <tag>^{{}}`, never `git rev-parse <tag>`"
        )
    return value


def resolve_tag_commit(tag: str, root: Path | None = None) -> str:
    """Section 1's manifest rule: dereference the tag to its **commit**.

    ``git rev-parse <tag>`` on an annotated tag returns the tag *object*.
    Using that where a commit is expected is exactly how the defect section 1
    documents was introduced, so a commit only ever reaches a manifest through
    this function.
    """
    return _git("rev-parse", f"{tag}^{{commit}}", root=root)


# -----------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class EnvironmentIdentity:
    """Per-run host and environment facts.

    These are the **only** new facts a partition manifest may add, and none of
    them is scientific.
    """

    platform: str
    machine: str
    python_version: str
    python_implementation: str
    environment_lock_digest: str
    python_packages: Mapping[str, str] = field(default_factory=dict)
    julia: Mapping[str, str] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "machine": self.machine,
            "python_version": self.python_version,
            "python_implementation": self.python_implementation,
            "environment_lock_digest": self.environment_lock_digest,
            "python_packages": dict(sorted(self.python_packages.items())),
            "julia": dict(sorted(self.julia.items())),
        }


def capture_environment(
    lock_path: Path | None = None,
    start_julia: bool = False,
) -> EnvironmentIdentity:
    """Read the host and environment identity from the live interpreter.

    Julia and ``SymbolicRegression.jl`` identities come from
    ``rc3_provenance``'s frozen readers, which resolve the ``SymbolicRegression.jl``
    pin from PySR's ``juliapkg.json`` without starting Julia unless asked.
    """
    from .rc3_provenance import _julia_versions, verify_dependencies

    digest = ""
    if lock_path is not None and Path(lock_path).is_file():
        digest = hashlib.sha256(Path(lock_path).read_bytes()).hexdigest()

    return EnvironmentIdentity(
        platform=platform.platform(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        environment_lock_digest=digest,
        python_packages=verify_dependencies(),
        julia=_julia_versions(start_julia=start_julia),
    )


# -----------------------------------------------------------------------
# Layer 1: the global science execution plan
# -----------------------------------------------------------------------

def _grammar_identity() -> dict[str, Any]:
    return {
        "primitives": list(GRAMMAR_PRIMITIVES),
        "primitive_count": len(GRAMMAR_PRIMITIVES),
        "feature_name_aliases": {
            f"x{i}": name for i, name in enumerate(GRAMMAR_PRIMITIVES)
        },
        "binary_operators": list(SEARCH_SETTINGS["binary_operators"]),
        "unary_operators": list(SEARCH_SETTINGS["unary_operators"]),
        "excluded_unary": list(SEARCH_SETTINGS["excluded_unary"]),
        "energy_grid": list(ENERGY_GRID),
    }


def _science_semantics() -> dict[str, Any]:
    """Every section 3-7 semantic RC5 executes, stated once, partition-agnostic."""
    return {
        "profile_and_target": {
            "phi_fit": "isotonic decreasing on (log u, mu), training fold only, then frozen",
            "phi_knots": PHI_N_KNOTS,
            "phi_alternations": PHI_ALTERNATIONS,
            "phi_interpolation": "linear between knots, flat clamp outside",
            "energy_scale_e_ref": E_REF,
            "log_g_grid": {
                "low": A35_LOG_G_GRID_LOW,
                "high": A35_LOG_G_GRID_HIGH,
                "points": A35_LOG_G_GRID_POINTS,
                "refinement": "parabolic on the interior minimum",
            },
            "recentre_after_phi_freeze": False,
            "search_target": "raw untransformed per-compound g",
            "rows": "one row per compound",
            "weights": None,
            "row_filtering": None,
        },
        "invalid_fraction": {
            "domain": "validation rows",
            "predicate": "grammar.finite_mask: isfinite(y) & (abs(y) < 1e12)",
            "denominator": N_VALIDATION_COMPOUNDS,
            "gate": MAX_INVALID_FRACTION,
        },
        "selection": {
            "per_seed_retention": "argmax of PySR's own score column",
            "model_selection_set_on_regressor": False,
            "seeds_per_case": A35_SEEDS_PER_CASE,
            "one_seed_one_vote": True,
            "identity_contract": "positive_scale_equivalent / template_key",
            "winning_class": "largest, ties to the class containing the lowest seed ordinal",
            "representative": "lowest seed ordinal in the winning class, values verbatim",
            "selection_denominator": STABILITY_DENOMINATOR,
            "stability_gate": STABILITY_GATE,
            "non_gating_diagnostics": [
                "winning_class_distinct_expression_strings",
                "winning_class_distinct_coefficient_vectors",
            ],
        },
        "gates": {
            "max_complexity": MAX_COMPLEXITY,
            "ceiling_fraction_gate": CEILING_FRACTION_GATE,
            "ceiling_waiver_threshold": CEILING_WAIVER_THRESHOLD,
            "gate7_rule": (
                "ceiling_fraction >= CEILING_FRACTION_GATE OR "
                "(ceiling_r2 < CEILING_WAIVER_THRESHOLD AND "
                "candidate_test_r2 > null_threshold[min(complexity, MAX_COMPLEXITY)])"
            ),
            "candidate_test_r2_computed_once": True,
            "gate8_required_hard_gates": sorted(r.value for r in REQUIRED_HARD_GATES),
            "gate8_predicate": "result != PASS rejects (fail-closed)",
        },
        "falsification": {
            "f1_rerun_count": F1_RERUN_COUNT,
            "f4_held_out_within_scaffold_index": F4_HELD_OUT_WITHIN_SCAFFOLD_INDEX,
            "f4_pass_bar": "R2 > 0.0",
            "f7_loso_folds": F7_LOSO_FOLDS,
            "f9_folds": F9_FOLDS,
            "f9_role": "computed and reported, never acceptance-determining",
            "f9_acceptance_calibration_status": F9_CALIBRATION_STATUS,
            "f10_constructions": list(F10_CONSTRUCTIONS),
            "f5_disposition": "superseded; its floor is folded into Gate 7",
            "affine_refit": "y ~ a + b*E(x), OLS on training rows only, two free parameters",
            "not_applicable_ever_emitted": False,
        },
        "g1": {
            "spearman_gate": G1_SPEARMAN_GATE,
            "trajectory_ratio_gate": G1_TRAJECTORY_RATIO_GATE,
            "denominator": G1_DENOMINATOR,
            "wilson_lower_gate": G1_WILSON_LOWER_GATE,
            "estimation_scheme": "within-compound leave-one-energy-out (A1.3)",
            "fitting_protocol": "A1.2's coarse-to-fine grid on LOG_G_BOUNDS",
        },
        "g3_authority": [
            "g3_contract.classify_g3_event",
            "g3_contract.score_g3",
        ],
        "exact_algebra": "DEFER_AS_UNEXECUTABLE_DESCRIPTIVE_ENDPOINT",
        "f18_grammar_representability": (
            "disclosed limitation; the grammar is not changed and the G2 "
            "denominator is not changed"
        ),
    }


def build_global_science_plan(
    engineering_parent_commit: str,
    a3_5_tag: str,
    a3_5_tag_object: str,
    a3_5_commit: str,
    null_threshold: Mapping[int, float],
    calibration_manifest_digest: str,
    code_provenance: Mapping[str, str],
) -> dict[str, Any]:
    """Layer 1: the partition-agnostic global science execution plan.

    Deliberately takes **no partition argument**: there is no parameter through
    which a partition could influence a scientific field.  The mandatory
    search-seed invariant guard (obligation 10) runs before anything is built,
    so no manifest can be produced over a seed scheme that does not hold.
    """
    seed_report = verify_search_seed_invariants()
    engineering_parent_commit = _assert_is_commit(
        engineering_parent_commit, "engineering_parent_commit"
    )
    a3_5_commit = _assert_is_commit(a3_5_commit, "a3_5_science_freeze.commit")

    inventory: dict[str, Any] = {}
    seeds: dict[str, list[int]] = {}
    for partition in PARTITIONS:
        case_ids = list(iter_case_ids(partition))
        inventory[partition] = {
            "case_count": len(case_ids),
            "case_ids": case_ids,
            "case_ordinals": [case_ordinal(c) for c in case_ids],
        }
        for case_id in case_ids:
            seeds[case_id] = list(case_search_seeds(case_id))

    payload: dict[str, Any] = {
        "schema_version": GLOBAL_PLAN_SCHEMA_VERSION,
        "layer": "global_science_execution_plan",
        "partition_agnostic": True,
        "engineering_parent_commit": engineering_parent_commit,
        "a3_5_science_freeze": {
            "tag": a3_5_tag,
            "tag_object": a3_5_tag_object,
            "commit": a3_5_commit,
        },
        "record_schema_version": RECORD_SCHEMA_VERSION,
        "grammar_identity": _grammar_identity(),
        "grammar_identity_digest": hashlib.sha256(
            canonical_manifest_json(_grammar_identity()).encode("utf-8")
        ).hexdigest(),
        "search_settings_digest": FROZEN_SETTINGS_DIGEST,
        "search_settings": {k: v for k, v in sorted(SEARCH_SETTINGS.items())},
        "threshold_table_digest": null_threshold_digest(null_threshold),
        "calibration_manifest_digest": calibration_manifest_digest,
        "seed_derivation": {
            "function": "search_seed(case_ordinal, k) = BASE + case_ordinal*SEEDS_PER_CASE + k",
            "base": A35_SEARCH_SEED_BASE,
            "seeds_per_case": A35_SEEDS_PER_CASE,
            "total_cases": A35_TOTAL_CASES,
            "band_min": A35_SEARCH_SEED_MIN,
            "band_max": A35_SEARCH_SEED_MAX,
            "case_ordinal_rule": (
                "position in the frozen registry enumeration, partition-major, "
                "then family, then replicate"
            ),
            "invariants": seed_report,
        },
        "case_inventory": inventory,
        "case_search_seeds": seeds,
        "science_semantics": _science_semantics(),
        "digest_convention": dict(DIGEST_CONVENTION),
        "resume_contract": dict(RESUME_CONTRACT),
        "code_provenance": dict(sorted(code_provenance.items())),
    }
    payload["digest"] = manifest_digest(payload)
    return payload


# -----------------------------------------------------------------------
# Layer 2: the per-partition pre-execution manifest
# -----------------------------------------------------------------------

def verify_global_plan(plan: Mapping[str, Any]) -> str:
    """Re-verify a global plan's own digest against its content.

    A plan loaded from disk is otherwise trusted: ``verify_partition_manifest``
    compares a manifest's cited plan digest against ``plan["digest"]`` as
    given, so a plan whose body was edited while its digest field was left
    alone would verify self-consistently.  A3.5 section 12 forbids amending a
    written pre-execution manifest; this is what makes that detectable.
    """
    recomputed = manifest_digest(plan)
    declared = plan.get("digest")
    if recomputed != declared:
        raise ManifestDerivationError(
            f"the global science plan's content digests to {recomputed} but it "
            f"declares {declared}; a written pre-execution plan is never amended"
        )
    return recomputed


def derive_partition_science(
    plan: Mapping[str, Any], partition: str
) -> dict[str, Any]:
    """The scientific block of a partition manifest.

    A **pure function of ``(global plan, partition name)``**, byte-reproducible
    by an independent verifier.  It reads only the plan and the partition name;
    it takes no host, no clock, no path, and no caller-supplied value.
    """
    if partition not in PARTITIONS:
        raise ValueError(f"unknown partition: {partition}")
    inventory = plan["case_inventory"][partition]
    case_ids = list(inventory["case_ids"])
    return {
        "partition": partition,
        "global_plan_digest": plan["digest"],
        "global_plan_schema_version": plan["schema_version"],
        "engineering_parent_commit": plan["engineering_parent_commit"],
        "a3_5_science_freeze": dict(plan["a3_5_science_freeze"]),
        "record_schema_version": plan["record_schema_version"],
        "grammar_identity_digest": plan["grammar_identity_digest"],
        "search_settings_digest": plan["search_settings_digest"],
        "threshold_table_digest": plan["threshold_table_digest"],
        "calibration_manifest_digest": plan["calibration_manifest_digest"],
        "case_count": inventory["case_count"],
        "case_ids": case_ids,
        "case_search_seeds": {c: list(plan["case_search_seeds"][c]) for c in case_ids},
        "seeds_per_case": plan["seed_derivation"]["seeds_per_case"],
        "resume_contract": dict(plan["resume_contract"]),
    }


def build_partition_manifest(
    plan: Mapping[str, Any],
    partition: str,
    environment: EnvironmentIdentity,
    output_root: str,
    run_commit: str,
    tree_clean: bool,
) -> dict[str, Any]:
    """Layer 2: written immediately before that partition executes.

    Every scientific field comes from :func:`derive_partition_science`; the
    only new content is host/environment identity and output locations.  There
    is no parameter here through which a scientific value could be supplied.
    """
    # Section 8.4 defines a Layer-2 manifest as the object written "immediately
    # before that partition executes", so it is the artifact whose existence
    # declares a partition is about to run.  Section 14.2 therefore applies here
    # as much as it does in the runner.  `derive_partition_science` stays
    # unguarded so an independent verifier can still re-derive any partition's
    # science block without being authorised to execute it.
    assert_partition_authorised(partition)
    # Obligation 10 covers a plan loaded from disk too, not only one just built.
    verify_search_seed_invariants()
    verify_global_plan(plan)
    science = derive_partition_science(plan, partition)
    payload: dict[str, Any] = {
        "schema_version": PARTITION_MANIFEST_SCHEMA_VERSION,
        "layer": "partition_pre_execution_manifest",
        "science": science,
        "run": {
            "environment": environment.to_payload(),
            "output_root": str(output_root),
            "records_subdirectory": "records",
            "seed_records_subdirectory": "seed_records",
            "provenance_subdirectory": "provenance",
            "run_commit": run_commit,
            "tree_clean": bool(tree_clean),
        },
        "digest_convention": dict(DIGEST_CONVENTION),
        "amendment_forbidden": (
            "a written pre-execution manifest is never amended; post-execution "
            "provenance is a separate, append-only record"
        ),
    }
    payload["digest"] = manifest_digest(payload)
    return payload


def verify_partition_manifest(
    plan: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, str]:
    """Independently re-derive and compare the manifest's scientific block.

    This is section 8.4's derivation clause, executable: an independent
    verifier rebuilds ``science`` from ``(plan, partition)`` and requires
    byte-identical canonical JSON.  Any scientific value chosen at partition
    time -- by defect or otherwise -- fails here.
    """
    verify_global_plan(plan)
    science = manifest["science"]
    partition = science["partition"]
    expected = derive_partition_science(plan, partition)

    actual_json = canonical_manifest_json(science)
    expected_json = canonical_manifest_json(expected)
    if actual_json != expected_json:
        raise ManifestDerivationError(
            f"the {partition} manifest's scientific block is not a pure "
            f"derivation of (global plan, partition name); nothing scientific "
            f"may be chosen at partition-manifest time"
        )
    if science["global_plan_digest"] != plan["digest"]:
        raise ManifestDerivationError(
            f"the {partition} manifest cites global plan "
            f"{science['global_plan_digest']}, but this plan digests to "
            f"{plan['digest']}"
        )
    recomputed = manifest_digest(manifest)
    if recomputed != manifest.get("digest"):
        raise ManifestDerivationError(
            f"the {partition} manifest's own digest does not match its content"
        )
    return {
        "partition": partition,
        "global_plan_digest": plan["digest"],
        "manifest_digest": recomputed,
        "science_digest": hashlib.sha256(expected_json.encode("utf-8")).hexdigest(),
    }


# -----------------------------------------------------------------------
# Writing
# -----------------------------------------------------------------------

def write_manifest_once(path: Path, payload: Mapping[str, Any]) -> str:
    """Write a pre-execution manifest exactly once, never amending.

    A second write for the same path raises: a written manifest is immutable,
    and appending to one is how anti-retry would be defeated.
    """
    path = Path(path)
    if path.exists():
        raise ManifestExists(
            f"{path} already exists; a written pre-execution manifest is never "
            f"amended or rewritten (A3.5 section 8.4, section 12)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    body = canonical_manifest_json(payload).encode("utf-8")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return manifest_digest(payload)
