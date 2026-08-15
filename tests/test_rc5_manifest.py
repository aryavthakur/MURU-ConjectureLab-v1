"""A3.5 section 8.4: the two-layer pre-execution manifest.

The builders are exercised against fixtures.  **No partition is executed**, and
no manifest written here names a real output location.
"""
from __future__ import annotations

import ast
import inspect
import json

import pytest

from muru.paper_benchmark.registry import PARTITIONS, iter_case_ids
from muru.paper_benchmark.rc5_manifest import (
    DIGEST_CONVENTION,
    GLOBAL_PLAN_SCHEMA_VERSION,
    PARTITION_MANIFEST_SCHEMA_VERSION,
    RESUME_CONTRACT,
    EnvironmentIdentity,
    ManifestDerivationError,
    ManifestExists,
    build_global_science_plan,
    build_partition_manifest,
    canonical_manifest_json,
    derive_partition_science,
    manifest_digest,
    resolve_tag_commit,
    verify_partition_manifest,
    write_manifest_once,
)
from muru.paper_benchmark.rc5_seeds import A35_SEEDS_PER_CASE

THRESHOLD = {c: 0.10 + 0.001 * c for c in range(1, 21)}
ENGINEERING_PARENT = "69e33c778efb14362439941d25ebbfcfb1068284"
A3_5_TAG = "benchmark-content-freeze-a3-5"
A3_5_TAG_OBJECT = "533777b73748e3c45dd1ecbda07098ba9837c587"
A3_5_COMMIT = "560bf28568e2762c60edc994aac7f2b6de14081f"


def _plan(**overrides):
    kwargs = dict(
        engineering_parent_commit=ENGINEERING_PARENT,
        a3_5_tag=A3_5_TAG,
        a3_5_tag_object=A3_5_TAG_OBJECT,
        a3_5_commit=A3_5_COMMIT,
        null_threshold=THRESHOLD,
        calibration_manifest_digest="c" * 64,
        code_provenance={"muru.paper_benchmark": "rc5"},
    )
    kwargs.update(overrides)
    return build_global_science_plan(**kwargs)


def _environment(**overrides) -> EnvironmentIdentity:
    base = dict(
        platform="TestOS-1",
        machine="arm64",
        python_version="3.13.12",
        python_implementation="CPython",
        environment_lock_digest="d" * 64,
        python_packages={"pysr": "1.5.10"},
        julia={"julia": "1.12.6", "SymbolicRegression.jl": "1.11.3"},
    )
    base.update(overrides)
    return EnvironmentIdentity(**base)


# =======================================================================
# Layer 1
# =======================================================================

def test_the_global_plan_is_partition_agnostic_by_construction():
    params = inspect.signature(build_global_science_plan).parameters
    assert "partition" not in params
    plan = _plan()
    assert plan["partition_agnostic"] is True
    assert plan["layer"] == "global_science_execution_plan"
    assert plan["schema_version"] == GLOBAL_PLAN_SCHEMA_VERSION


def test_the_plan_binds_every_field_the_mission_requires():
    plan = _plan()
    assert plan["engineering_parent_commit"] == ENGINEERING_PARENT
    assert plan["a3_5_science_freeze"] == {
        "tag": A3_5_TAG,
        "tag_object": A3_5_TAG_OBJECT,
        "commit": A3_5_COMMIT,
    }
    for key in (
        "record_schema_version",
        "grammar_identity",
        "grammar_identity_digest",
        "search_settings_digest",
        "threshold_table_digest",
        "calibration_manifest_digest",
        "seed_derivation",
        "case_inventory",
        "case_search_seeds",
        "science_semantics",
        "digest_convention",
        "resume_contract",
        "code_provenance",
        "digest",
    ):
        assert key in plan, key


def test_the_case_inventory_is_the_closed_380_case_population():
    plan = _plan()
    total = 0
    for partition in PARTITIONS:
        expected = list(iter_case_ids(partition))
        assert plan["case_inventory"][partition]["case_ids"] == expected
        assert plan["case_inventory"][partition]["case_count"] == len(expected)
        total += len(expected)
    assert total == 380
    assert len(plan["case_search_seeds"]) == 380
    assert all(len(s) == A35_SEEDS_PER_CASE for s in plan["case_search_seeds"].values())
    flat = [s for seeds in plan["case_search_seeds"].values() for s in seeds]
    assert len(flat) == 11_400
    assert len(set(flat)) == 11_400


def test_the_seed_invariant_guard_runs_before_any_manifest_is_built():
    tree = ast.parse(inspect.getsource(build_global_science_plan))
    body = [n for n in tree.body[0].body if not isinstance(n, ast.Expr)]
    first = body[0]
    assert isinstance(first, ast.Assign)
    call = first.value
    assert isinstance(call, ast.Call)
    assert getattr(call.func, "id", "") == "verify_search_seed_invariants"


def test_the_digest_convention_is_stated_inside_the_manifest():
    plan = _plan()
    assert plan["digest_convention"] == DIGEST_CONVENTION
    assert plan["digest_convention"]["algorithm"] == "sha256"
    assert "canonical" in plan["digest_convention"]["note"].lower()
    assert "raw" in plan["digest_convention"]["note"].lower()


def test_the_digest_is_over_the_canonical_form_not_the_raw_bytes(tmp_path):
    import hashlib

    plan = _plan()
    path = tmp_path / "plan.json"
    digest = write_manifest_once(path, plan)
    assert digest == plan["digest"] == manifest_digest(plan)
    raw = hashlib.sha256(path.read_bytes()).hexdigest()
    # The live example section 8.4 cites: the two differ, and a verifier
    # hashing raw bytes would raise a false alarm on an intact manifest.
    assert raw != digest


def test_the_plan_digest_is_stable_across_two_independent_builds():
    assert _plan()["digest"] == _plan()["digest"]
    assert canonical_manifest_json(_plan()) == canonical_manifest_json(_plan())


def test_the_plan_digest_moves_when_any_bound_science_moves():
    baseline = _plan()["digest"]
    other = dict(THRESHOLD)
    other[7] += 1e-9
    assert _plan(null_threshold=other)["digest"] != baseline
    assert _plan(calibration_manifest_digest="e" * 64)["digest"] != baseline
    assert _plan(engineering_parent_commit="0" * 40)["digest"] != baseline


def test_the_resume_contract_is_bound_in_the_plan():
    plan = _plan()
    assert plan["resume_contract"] == RESUME_CONTRACT
    assert plan["resume_contract"]["replacement_seed"] is False
    assert plan["resume_contract"]["retry_that_erases_a_prior_execution_failure"] is False
    assert plan["resume_contract"]["completed_case_is_never_re_executed"] is True


def test_the_plan_records_the_amended_gate_semantics():
    gates = _plan()["science_semantics"]["gates"]
    assert gates["gate8_required_hard_gates"] == [
        "F10_NEGATIVE_CONTROL",
        "F1_REPRODUCIBILITY",
        "F4_COMPOUND_HOLDOUT",
        "F7_INFLUENCE_DROP",
    ]
    assert "fail-closed" in gates["gate8_predicate"]
    assert "candidate_test_r2 >" in gates["gate7_rule"]
    assert gates["candidate_test_r2_computed_once"] is True
    falsification = _plan()["science_semantics"]["falsification"]
    assert falsification["f9_role"] == "computed and reported, never acceptance-determining"
    assert falsification["f9_acceptance_calibration_status"] == "NOT_PROVEN_FOR_HARD_GATE"
    assert "superseded" in falsification["f5_disposition"]


def test_the_plan_records_e_ref_45_and_the_denominator_30():
    semantics = _plan()["science_semantics"]
    assert semantics["profile_and_target"]["energy_scale_e_ref"] == 45.0
    assert semantics["profile_and_target"]["recentre_after_phi_freeze"] is False
    assert semantics["invalid_fraction"]["denominator"] == 30


# =======================================================================
# Commit fields
# =======================================================================

def test_a_commit_field_is_dereferenced_from_the_tag_object():
    # Section 1's manifest rule, exercised against the repository's real tags.
    assert resolve_tag_commit(A3_5_TAG) == A3_5_COMMIT
    assert resolve_tag_commit("engineering-rc4-2-1-integrity-closure") == ENGINEERING_PARENT
    # And the tag object is a different SHA, which is the whole point.
    assert A3_5_TAG_OBJECT != A3_5_COMMIT


def test_the_only_route_to_a_commit_field_dereferences():
    import muru.paper_benchmark.rc5_manifest as module

    tree = ast.parse(inspect.getsource(resolve_tag_commit))
    literals = [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]
    assert any("^{commit}" in literal for literal in literals)


# =======================================================================
# Layer 2
# =======================================================================

def test_a_partition_manifest_adds_only_host_facts_and_locations():
    plan = _plan()
    manifest = build_partition_manifest(
        plan, "development", _environment(), "/tmp/nowhere", "abc123", True
    )
    assert manifest["schema_version"] == PARTITION_MANIFEST_SCHEMA_VERSION
    assert manifest["layer"] == "partition_pre_execution_manifest"
    assert set(manifest["run"]) == {
        "environment",
        "output_root",
        "records_subdirectory",
        "seed_records_subdirectory",
        "provenance_subdirectory",
        "run_commit",
        "tree_clean",
    }
    assert manifest["run"]["environment"]["julia"]["SymbolicRegression.jl"] == "1.11.3"


def test_every_scientific_field_is_a_pure_derivation_of_plan_and_partition():
    plan = _plan()
    for partition in PARTITIONS:
        manifest = build_partition_manifest(
            plan, partition, _environment(), "/tmp/nowhere", "abc123", True
        )
        assert manifest["science"] == derive_partition_science(plan, partition)
        report = verify_partition_manifest(plan, manifest)
        assert report["partition"] == partition
        assert report["global_plan_digest"] == plan["digest"]


def test_the_derivation_reads_only_the_plan_and_the_partition_name():
    params = list(inspect.signature(derive_partition_science).parameters)
    assert params == ["plan", "partition"]


def test_no_parameter_exists_through_which_science_could_be_injected():
    params = set(inspect.signature(build_partition_manifest).parameters)
    assert params == {
        "plan", "partition", "environment", "output_root", "run_commit", "tree_clean"
    }
    for scientific in (
        "threshold", "null_threshold", "seeds", "grammar", "search_settings",
        "complexity", "gate", "case_ids",
    ):
        assert scientific not in params


def test_a_tampered_scientific_field_is_caught_by_the_verifier():
    plan = _plan()
    manifest = build_partition_manifest(
        plan, "development", _environment(), "/tmp/nowhere", "abc123", True
    )
    tampered = json.loads(json.dumps(manifest))
    tampered["science"]["threshold_table_digest"] = "0" * 64
    with pytest.raises(ManifestDerivationError, match="pure derivation"):
        verify_partition_manifest(plan, tampered)


def test_a_dropped_case_is_caught_by_the_verifier():
    plan = _plan()
    manifest = build_partition_manifest(
        plan, "development", _environment(), "/tmp/nowhere", "abc123", True
    )
    tampered = json.loads(json.dumps(manifest))
    dropped = tampered["science"]["case_ids"].pop()
    tampered["science"]["case_search_seeds"].pop(dropped)
    tampered["science"]["case_count"] -= 1
    with pytest.raises(ManifestDerivationError):
        verify_partition_manifest(plan, tampered)


def test_a_manifest_citing_another_plan_is_caught():
    plan = _plan()
    manifest = build_partition_manifest(
        plan, "development", _environment(), "/tmp/nowhere", "abc123", True
    )
    other = _plan(calibration_manifest_digest="f" * 64)
    with pytest.raises(ManifestDerivationError):
        verify_partition_manifest(other, manifest)


def test_a_tampered_digest_is_caught():
    plan = _plan()
    manifest = build_partition_manifest(
        plan, "development", _environment(), "/tmp/nowhere", "abc123", True
    )
    tampered = json.loads(json.dumps(manifest))
    tampered["run"]["run_commit"] = "deadbeef"
    with pytest.raises(ManifestDerivationError, match="own digest"):
        verify_partition_manifest(plan, tampered)


def test_the_scientific_block_is_identical_across_partitions_except_its_own_identity():
    plan = _plan()
    development = derive_partition_science(plan, "development")
    held_out = derive_partition_science(plan, "held_out")
    administrative = {"partition", "case_count", "case_ids", "case_search_seeds"}
    for key in set(development) - administrative:
        assert development[key] == held_out[key], key


def test_host_facts_do_not_leak_into_the_scientific_block():
    plan = _plan()
    a = build_partition_manifest(
        plan, "development", _environment(), "/tmp/a", "commit-a", True
    )
    b = build_partition_manifest(
        plan,
        "development",
        _environment(platform="OtherOS-9", machine="x86_64"),
        "/tmp/b",
        "commit-b",
        False,
    )
    assert a["science"] == b["science"]
    assert a["run"] != b["run"]
    assert a["digest"] != b["digest"]


def test_an_unknown_partition_is_refused():
    plan = _plan()
    with pytest.raises(ValueError, match="unknown partition"):
        derive_partition_science(plan, "confirmation")


# =======================================================================
# Anti-retry
# =======================================================================

def test_a_written_manifest_is_never_amended(tmp_path):
    plan = _plan()
    path = tmp_path / "development_manifest.json"
    write_manifest_once(path, build_partition_manifest(
        plan, "development", _environment(), str(tmp_path), "abc123", True
    ))
    with pytest.raises(ManifestExists, match="never"):
        write_manifest_once(path, build_partition_manifest(
            plan, "development", _environment(), str(tmp_path), "abc123", True
        ))


def test_a_written_manifest_round_trips_through_its_canonical_form(tmp_path):
    plan = _plan()
    path = tmp_path / "plan.json"
    write_manifest_once(path, plan)
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert reloaded == json.loads(canonical_manifest_json(plan))
    assert manifest_digest(reloaded) == plan["digest"]


def test_the_manifest_states_that_amendment_is_forbidden():
    plan = _plan()
    manifest = build_partition_manifest(
        plan, "development", _environment(), "/tmp/nowhere", "abc123", True
    )
    assert "never amended" in manifest["amendment_forbidden"]
    assert "append-only" in manifest["amendment_forbidden"]
