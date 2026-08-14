#!/usr/bin/env python3
"""Freeze A3.4 science and preserve its score-only execution boundary.

This verifier deliberately has no dependency on the benchmark package.  It
compares bytes exposed by Git and parses endpoint source with :mod:`ast`; it
does not import an A3.4 endpoint, run the frozen generator, or open a search,
calibration, partition, or outcome API.
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

A34_FREEZE_COMMIT = "be23b80d63fbd30227f0ab8f200dddc2121f3bfe"
A34_CREATION_COMMIT = "d0ea5d4b0309e4e95dcab4035b9be66e166765b1"
FROZEN_A33_PARENT_LITERAL = "71f53697e8894df6469ad0ff7150a049fa531b74"
FROZEN_RECORDED_PROTECTED_AGGREGATE = (
    "d24cc91698a562acfe61c8bab65a9f33ccc517b284411c65c66e394fe7a6d1b8"
)

A34_AMENDMENT_PATH = "MURU_PAPER_BENCHMARK_AMENDMENT_A3_4.md"
A34_ARTIFACT_PATH = "artifacts/paper_benchmark_amendment_a3_4.json"
A34_GOVERNANCE_PATHS = (A34_AMENDMENT_PATH, A34_ARTIFACT_PATH)

A34_SCHEMA_VERSION = "muru-paper-benchmark-amendment-a3.4-1.0.0"
A34_REFERENCE_DIGEST = "4fef2379ae33a10d089bd66794fdd21418b2b30c656fd801bc619f55c3fe7a44"

# These names can materialize a partition or case.  They are forbidden both as
# direct imports and as attributes reached through an alias.
PARTITION_API_NAMES = frozenset(
    {
        "generate_partition",
        "iter_case_ids",
        "resolve_case_id",
        "generate_case",
        "load_partition",
        "read_partition",
        "open_partition",
        "materialize_partition",
    }
)

SEARCH_SELECTION_API_NAMES = frozenset(
    {
        "search",
        "select",
        "select_candidate",
        "candidate_selection",
        "run_search",
        "run_selection",
    }
)

CALIBRATION_OUTCOME_API_NAMES = frozenset(
    {
        "run_calibration",
        "build_calibration_world",
        "all_world_ids",
        "derive_calibration_seeds",
        "evaluate_structural_acceptance",
        "load_outcome",
        "read_outcome",
        "open_outcome",
        "load_result",
        "read_result",
        "open_result",
        "record_outcome",
    }
)

FORBIDDEN_API_NAMES = (
    PARTITION_API_NAMES
    | SEARCH_SELECTION_API_NAMES
    | CALIBRATION_OUTCOME_API_NAMES
)

# Module tokens are deliberately narrow: TruthRecord, the frozen G2 parser,
# and endpoint sidecars are legitimate score-only dependencies.  The one
# generator exception is handled separately below.
FORBIDDEN_MODULE_TOKENS = frozenset(
    {
        "generator",
        "registry",
        "artifacts",
        "partition",
        "partitions",
        "search",
        "selection",
        "select",
        "analysis",
        "adequacy",
        "structural_acceptance",
        "g3_contract",
        "rc3_acceptance",
        "rc3_scoring",
        "rc3_ceiling",
        "rc3_provenance",
        "rc3_calibration_runner",
        "rc3_calibration_worlds",
        "calibration_contract",
        "rc3_record",
        "outcome",
        "outcomes",
    }
)


def sha256_bytes(content: bytes) -> str:
    """Return the SHA-256 identity used by the frozen amendment artifact."""
    return hashlib.sha256(content).hexdigest()


def git_show_bytes(root: Path, commit: str, relative_path: str) -> bytes | None:
    """Read a committed blob without checking it out or importing project code."""
    result = subprocess.run(
        ("git", "show", f"{commit}:{relative_path}"),
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def check_byte_identity(
    root: Path,
    commit: str,
    paths: Iterable[str],
    *,
    label: str,
) -> list[str]:
    """Require each current file to be byte-identical to one committed blob."""
    errors: list[str] = []
    marker = label.upper()
    for relative_path in sorted(set(paths)):
        current_path = root / relative_path
        if not current_path.is_file():
            errors.append(f"MISSING_{marker}: {relative_path}")
            continue
        frozen = git_show_bytes(root, commit, relative_path)
        if frozen is None:
            errors.append(f"NOT_AT_{marker}: {relative_path}")
            continue
        try:
            current = current_path.read_bytes()
        except OSError as exc:
            errors.append(f"UNREADABLE_{marker}: {relative_path}: {type(exc).__name__}")
            continue
        if current != frozen:
            errors.append(f"MODIFIED_{marker}: {relative_path}")
    return errors


def _load_frozen_a34_artifact(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load the artifact from the frozen commit, never from mutable checkout bytes."""
    raw = git_show_bytes(root, A34_FREEZE_COMMIT, A34_ARTIFACT_PATH)
    if raw is None:
        return None, ["FROZEN_A3_4_ARTIFACT_MISSING"]
    try:
        artifact = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [f"FROZEN_A3_4_ARTIFACT_JSON: {type(exc).__name__}"]
    if not isinstance(artifact, dict):
        return None, ["FROZEN_A3_4_ARTIFACT_TYPE: expected object"]
    return artifact, []


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _frozen_commit_parent(root: Path, commit: str) -> str | None:
    result = subprocess.run(
        ("git", "rev-parse", f"{commit}^"),
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _is_commit_object(root: Path, revision: str) -> bool:
    """Return whether a provenance literal resolves locally to a commit object."""
    result = subprocess.run(
        ("git", "cat-file", "-e", f"{revision}^{{commit}}"),
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _protected_path_digest(digests: Mapping[str, str]) -> str:
    payload = "".join(
        f"{relative_path}:{digests[relative_path]}\n"
        for relative_path in sorted(digests)
    )
    return sha256_bytes(payload.encode("utf-8"))


def _artifact_protected_paths(artifact: Mapping[str, Any]) -> tuple[str, ...] | None:
    protected_paths = artifact.get("protected_paths")
    if not isinstance(protected_paths, list) or not all(
        isinstance(path, str) for path in protected_paths
    ):
        return None
    return tuple(protected_paths)


def frozen_standard_protected_aggregate(root: Path = ROOT) -> str | None:
    """Compute the standard ``path:sha256\\n`` aggregate from frozen entries.

    This is an independent engineering calculation.  It deliberately does not
    treat a difference from the immutable historical field as science drift.
    """
    artifact, _ = _load_frozen_a34_artifact(root)
    if artifact is None:
        return None
    protected_paths = _artifact_protected_paths(artifact)
    protected_digests = artifact.get("protected_sha256")
    if (
        protected_paths is None
        or not isinstance(protected_digests, dict)
        or set(protected_digests) != set(protected_paths)
        or not all(_is_sha256(digest) for digest in protected_digests.values())
    ):
        return None
    return _protected_path_digest(protected_digests)


def known_frozen_metadata_advisories(root: Path = ROOT) -> list[str]:
    """Report, without failing, the two known immutable provenance facts.

    Their literals remain byte-pinned by the frozen artifact.  They are not a
    change to the 31 protected scientific paths, all of whose individual
    SHA-256 entries are checked separately below.
    """
    artifact, _ = _load_frozen_a34_artifact(root)
    if artifact is None:
        return []
    advisories: list[str] = []
    if (
        artifact.get("parent_a3_3_commit") == FROZEN_A33_PARENT_LITERAL
        and not _is_commit_object(root, FROZEN_A33_PARENT_LITERAL)
    ):
        advisories.append("ADVISORY_A3_4_PARENT_A3_3_LITERAL_NONOBJECT")
    standard_aggregate = frozen_standard_protected_aggregate(root)
    if (
        artifact.get("protected_path_digest")
        == FROZEN_RECORDED_PROTECTED_AGGREGATE
        and standard_aggregate is not None
        and standard_aggregate != FROZEN_RECORDED_PROTECTED_AGGREGATE
    ):
        advisories.append("ADVISORY_A3_4_PROTECTED_AGGREGATE_NONSTANDARD")
    return advisories


def check_a34_artifact_linkage(root: Path = ROOT) -> list[str]:
    """Verify that the frozen A3.4 artifact links every published digest.

    The A3.4 artifact is itself first byte-pinned in ``main``.  This check
    additionally proves that its frozen content has a coherent lineage,
    protected-path manifest, and published reference-covariate identity.  It
    intentionally computes no reference rows: recomputation would execute the
    frozen generator, which is outside an integrity gate's authority.
    """
    artifact, errors = _load_frozen_a34_artifact(root)
    if artifact is None:
        return errors

    if artifact.get("amendment") != "A3.4":
        errors.append("A3_4_ARTIFACT_AMENDMENT")
    if artifact.get("schema_version") != A34_SCHEMA_VERSION:
        errors.append("A3_4_ARTIFACT_SCHEMA")
    if artifact.get("creation_commit") != A34_CREATION_COMMIT:
        errors.append("A3_4_ARTIFACT_CREATION_COMMIT")
    if _frozen_commit_parent(root, A34_FREEZE_COMMIT) != A34_CREATION_COMMIT:
        errors.append("A3_4_FREEZE_PARENT")

    added_paths = artifact.get("added_paths")
    if added_paths != list(A34_GOVERNANCE_PATHS):
        errors.append("A3_4_ARTIFACT_ADDED_PATHS")

    amendment_digests = artifact.get("amendment_file_sha256")
    if not isinstance(amendment_digests, dict):
        errors.append("A3_4_ARTIFACT_AMENDMENT_DIGESTS")
    else:
        expected_document_digest = amendment_digests.get(A34_AMENDMENT_PATH)
        frozen_document = git_show_bytes(root, A34_FREEZE_COMMIT, A34_AMENDMENT_PATH)
        if (
            not _is_sha256(expected_document_digest)
            or frozen_document is None
            or sha256_bytes(frozen_document) != expected_document_digest
        ):
            errors.append("A3_4_ARTIFACT_AMENDMENT_SHA256")
        if amendment_digests.get(A34_ARTIFACT_PATH) != "self":
            errors.append("A3_4_ARTIFACT_SELF_DIGEST")

    protected_paths = _artifact_protected_paths(artifact)
    protected_digests = artifact.get("protected_sha256")
    if protected_paths is None or not isinstance(protected_digests, dict):
        errors.append("A3_4_ARTIFACT_PROTECTED_MANIFEST")
    else:
        expected_paths = set(protected_paths)
        if len(protected_paths) != len(expected_paths):
            errors.append("A3_4_ARTIFACT_DUPLICATE_PROTECTED_PATH")
        if artifact.get("protected_path_count") != len(protected_paths):
            errors.append("A3_4_ARTIFACT_PROTECTED_COUNT")
        if set(protected_digests) != expected_paths:
            errors.append("A3_4_ARTIFACT_PROTECTED_KEYS")
        elif not all(_is_sha256(digest) for digest in protected_digests.values()):
            errors.append("A3_4_ARTIFACT_PROTECTED_SHA256_FORMAT")
        else:
            for relative_path in sorted(protected_paths):
                frozen = git_show_bytes(root, A34_FREEZE_COMMIT, relative_path)
                if frozen is None:
                    errors.append(f"A3_4_ARTIFACT_PROTECTED_MISSING: {relative_path}")
                elif sha256_bytes(frozen) != protected_digests[relative_path]:
                    errors.append(f"A3_4_ARTIFACT_PROTECTED_DRIFT: {relative_path}")

    reference_contract = artifact.get("predictive_equivalence_contract")
    if not isinstance(reference_contract, dict):
        errors.append("A3_4_ARTIFACT_REFERENCE_CONTRACT")
    else:
        distribution = reference_contract.get("reference_distribution")
        if not isinstance(distribution, dict):
            errors.append("A3_4_ARTIFACT_REFERENCE_DISTRIBUTION")
        else:
            if distribution.get("aggregate_reference_covariates_sha256") != A34_REFERENCE_DIGEST:
                errors.append("A3_4_ARTIFACT_REFERENCE_DIGEST")
            frame_manifest = distribution.get("frame_manifest")
            if (
                distribution.get("n_frames") != 12
                or distribution.get("total_evaluation_points") != 2160
                or not isinstance(frame_manifest, list)
                or len(frame_manifest) != 12
            ):
                errors.append("A3_4_ARTIFACT_REFERENCE_GEOMETRY")
            elif not all(
                isinstance(frame, dict)
                and _is_sha256(frame.get("frame_content_sha256"))
                for frame in frame_manifest
            ):
                errors.append("A3_4_ARTIFACT_REFERENCE_FRAME_DIGEST")

    expected_status = {
        "calibration": "NOT_EXECUTED",
        "development": "NOT_OPENED",
        "held_out": "SEALED_NOT_OPENED",
        "confirmation": "SEALED_NOT_OPENED",
    }
    if artifact.get("status") != expected_status:
        errors.append("A3_4_ARTIFACT_STATUS")
    return sorted(set(errors))


def check_protected_science_paths(root: Path = ROOT) -> list[str]:
    """Byte-pin A3.4 plus the inherited RC3/A3.2 science manifest.

    The frozen A3.4 artifact carries the 31 inherited A2.1/A3.1/A3.2/A3.3
    protected science paths.  Adding its own amendment and artifact makes the
    complete engineering check independent of executing the RC3 verifier.
    """
    artifact, errors = _load_frozen_a34_artifact(root)
    if artifact is None:
        return errors
    protected_paths = _artifact_protected_paths(artifact)
    if protected_paths is None:
        return errors + ["A3_4_ARTIFACT_PROTECTED_MANIFEST"]
    return errors + check_byte_identity(
        root,
        A34_FREEZE_COMMIT,
        (*A34_GOVERNANCE_PATHS, *protected_paths),
        label="a3_4",
    )


def _module_components(module: str | None) -> frozenset[str]:
    if not module:
        return frozenset()
    return frozenset(component for component in module.split(".") if component)


def _forbidden_module_reason(module: str | None) -> str | None:
    # A package-root import can defer access to an arbitrary local submodule
    # (for example ``benchmark.analysis``).  It has no bounded static target,
    # so reject it instead of importing or executing the package to discover
    # its attributes.
    if module == "muru.paper_benchmark":
        return "unbounded_package"
    components = _module_components(module)
    if "generator" in components:
        return "generator"
    for component in sorted(components):
        if component in FORBIDDEN_MODULE_TOKENS:
            return component
        if "calibrat" in component:
            return component
        if "search" in component or "select" in component:
            return component
    return None


def _is_allowed_covariate_adapter(
    relative_path: str,
    node: ast.ImportFrom,
) -> bool:
    """Permit only A3.4's frozen ``_synthetic_compounds`` adapter import."""
    return (
        relative_path == "src/muru/paper_benchmark/a34_contract.py"
        and node.level == 1
        and node.module == "generator"
        and len(node.names) == 1
        and node.names[0].name == "_synthetic_compounds"
    )


def _import_from_module(node: ast.ImportFrom, alias: ast.alias) -> str | None:
    if node.module:
        return node.module
    # ``from . import generator`` encodes the module name in the alias.
    return alias.name if node.level else None


def _scan_import_node(relative_path: str, node: ast.AST) -> list[str]:
    errors: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            reason = _forbidden_module_reason(alias.name)
            if reason:
                errors.append(
                    f"SEALED_BOUNDARY_MODULE: {relative_path}: {alias.name} ({reason})"
                )
    elif isinstance(node, ast.ImportFrom):
        if _is_allowed_covariate_adapter(relative_path, node):
            return errors
        for alias in node.names:
            module = _import_from_module(node, alias)
            reason = _forbidden_module_reason(module)
            if reason:
                errors.append(
                    f"SEALED_BOUNDARY_MODULE: {relative_path}: {module} ({reason})"
                )
            elif node.module and alias.name != "*":
                qualified_module = f"{node.module}.{alias.name}"
                qualified_reason = _forbidden_module_reason(qualified_module)
                if qualified_reason:
                    errors.append(
                        "SEALED_BOUNDARY_MODULE: "
                        f"{relative_path}: {qualified_module} ({qualified_reason})"
                    )
            if alias.name in FORBIDDEN_API_NAMES:
                errors.append(
                    f"SEALED_BOUNDARY_IMPORT: {relative_path}: {alias.name}"
                )
    return errors


def _scan_reference_node(relative_path: str, node: ast.AST) -> list[str]:
    errors: list[str] = []
    if isinstance(node, ast.Name) and node.id in FORBIDDEN_API_NAMES:
        errors.append(f"SEALED_BOUNDARY_REFERENCE: {relative_path}: {node.id}")
    elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_API_NAMES:
        errors.append(f"SEALED_BOUNDARY_REFERENCE: {relative_path}: {node.attr}")
    elif isinstance(node, ast.Call):
        function_name = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else None
        )
        if function_name in {"__import__", "import_module"} and node.args:
            argument = node.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                reason = _forbidden_module_reason(argument.value)
                if reason:
                    errors.append(
                        f"SEALED_BOUNDARY_DYNAMIC_IMPORT: {relative_path}: "
                        f"{argument.value} ({reason})"
                    )
        if function_name == "getattr" and len(node.args) >= 2:
            attribute = node.args[1]
            if isinstance(attribute, ast.Constant) and attribute.value in FORBIDDEN_API_NAMES:
                errors.append(
                    f"SEALED_BOUNDARY_DYNAMIC_REFERENCE: {relative_path}: "
                    f"{attribute.value}"
                )
    return errors


def _is_within(path: Path, directory: Path) -> bool:
    """Return whether ``path`` resolves beneath ``directory``."""
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def _existing_local_module(
    base: Path,
    module_parts: tuple[str, ...],
    source_root: Path,
) -> Path | None:
    """Resolve one local module file without importing it."""
    if not module_parts:
        return None
    candidate_base = base.joinpath(*module_parts)
    for candidate in (
        candidate_base.with_suffix(".py"),
        candidate_base / "__init__.py",
    ):
        if candidate.is_file() and _is_within(candidate, source_root):
            return candidate
    return None


def _local_module_path(
    source_path: Path,
    *,
    level: int,
    module: str | None,
    source_root: Path,
) -> Path | None:
    """Resolve a relative or package-qualified import inside paper_benchmark."""
    if level:
        base = source_path.parent
        for _ in range(level - 1):
            base = base.parent
        module_parts = tuple(module.split(".")) if module else ()
    else:
        if not module:
            return None
        parts = tuple(module.split("."))
        if parts[:2] != ("muru", "paper_benchmark"):
            return None
        base = source_root
        module_parts = parts[2:]
    return _existing_local_module(base, module_parts, source_root)


def _local_import_targets(
    source_path: Path,
    tree: ast.AST,
    source_root: Path,
    relative_path: str,
) -> tuple[Path, ...]:
    """Find safe local import targets to parse transitively, never import.

    A forbidden module is already reported by the direct-node scan, so it is
    deliberately not opened here.  The one permitted covariate adapter is a
    terminal leaf: following ``generator.py`` would incorrectly treat its
    unrelated partition APIs as an A3.4 endpoint dependency.
    """
    targets: set[Path] = set()

    def add_target(level: int, module: str | None) -> None:
        if _forbidden_module_reason(module):
            return
        target = _local_module_path(
            source_path,
            level=level,
            module=module,
            source_root=source_root,
        )
        if target is not None:
            targets.add(target)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_target(0, alias.name)
        elif isinstance(node, ast.ImportFrom):
            if _is_allowed_covariate_adapter(relative_path, node):
                continue
            add_target(node.level, node.module)
            if node.module:
                for alias in node.names:
                    if alias.name != "*":
                        add_target(node.level, f"{node.module}.{alias.name}")
            else:
                for alias in node.names:
                    if alias.name != "*":
                        add_target(node.level, alias.name)
    return tuple(sorted(targets))


def scan_a34_endpoint_sources(root: Path = ROOT) -> list[str]:
    """Statically reject execution-boundary references in the A3.4 closure.

    Every ``a34_*.py`` root is parsed, then every safe local import reached
    from those roots is parsed recursively. AST parsing reads source syntax
    only; it never imports or evaluates the scanned endpoints. This keeps the
    integrity gate unable to invoke the generator, search/selection code,
    calibration code, or outcome APIs.
    """
    source_root = root / "src/muru/paper_benchmark"
    errors: list[str] = []
    pending = list(reversed(sorted(source_root.glob("a34_*.py"))))
    scanned: set[Path] = set()
    while pending:
        path = pending.pop()
        resolved_path = path.resolve()
        if resolved_path in scanned:
            continue
        scanned.add(resolved_path)
        relative_path = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"SEALED_BOUNDARY_PARSE: {relative_path}: {type(exc).__name__}")
            continue
        for node in ast.walk(tree):
            errors.extend(_scan_import_node(relative_path, node))
            errors.extend(_scan_reference_node(relative_path, node))
        pending.extend(
            reversed(_local_import_targets(path, tree, source_root, relative_path))
        )
    return sorted(set(errors))


def _report(section: str, errors: list[str], details: Iterable[str] = ()) -> None:
    print(section)
    if errors:
        print("   VIOLATIONS")
        for error in errors:
            print(f"   ERROR: {error}")
    else:
        print("   VERIFIED")
    for detail in details:
        print(f"   {detail}")


def _report_advisories(advisories: Iterable[str]) -> None:
    print("2b. Frozen historical metadata advisories...")
    emitted = False
    for advisory in advisories:
        emitted = True
        print(f"   ADVISORY: {advisory}")
    if not emitted:
        print("   NONE")


def main() -> int:
    """Run deterministic, read-only A3.4 integrity checks."""
    print("A3.4 science and sealed-boundary integrity verification")
    print("=" * 60)

    protected_errors = check_protected_science_paths(ROOT)
    _report("1. Frozen A3.4 and inherited RC3/A3.2 science bytes...", protected_errors)

    artifact_errors = check_a34_artifact_linkage(ROOT)
    standard_aggregate = frozen_standard_protected_aggregate(ROOT)
    _report(
        "2. Frozen A3.4 artifact linkage and digests...",
        artifact_errors,
        (
            "STANDARD_PROTECTED_AGGREGATE: "
            f"{standard_aggregate or 'UNAVAILABLE'}",
        ),
    )
    _report_advisories(known_frozen_metadata_advisories(ROOT))

    boundary_errors = scan_a34_endpoint_sources(ROOT)
    _report("3. A3.4 endpoint static sealed-boundary scan...", boundary_errors)

    all_errors = protected_errors + artifact_errors + boundary_errors
    print("=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} violation(s)")
        return 1
    print("A3.4 INTEGRITY VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
