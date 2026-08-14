"""RC4.1 environment closure: verify and record the executable environment.

Engineering only.  This script changes no scientific definition, reads no
benchmark case, and touches no sealed partition.  It exists because a hostile
exact-lineage reproducibility audit found that the tracked
``requirements.lock.txt`` was a reduced Phase-1 lock of 39 distributions that
omitted SymPy, mpmath, PySR, gplearn and the Julia bridge, while
``README.md`` instructs a replicator to build the environment from exactly
that file.  A fresh clone followed literally could not import the strict
evaluator, let alone run a prospective search.

What this verifies
------------------
1. ``requirements.lock.txt`` is byte-identical to
   ``configs/rc3_requirements_lock_c7c2332.txt``, the pin source the frozen
   runtime guard ``rc3_provenance.verify_dependencies`` already checks.  The
   tracked bootstrap and the enforced pin source are then the same bytes, so
   they cannot drift apart.
2. Every distribution the frozen guard requires is pinned in that lock.
3. Every third-party top-level import reachable from ``src/``, ``scripts/``
   and ``tests/`` maps to a pinned distribution.  No undeclared hard import.
4. The Julia side is bound: the vendored ``configs/julia/Manifest.toml``
   records the exact resolved Julia dependency graph, and (with
   ``--start-julia``) the live Julia and SymbolicRegression.jl versions are
   compared against the frozen ones and refused on mismatch.

Why the Julia side needs an enforced gate rather than a pin
-----------------------------------------------------------
The Python lock pins ``pysr``, ``juliacall`` and ``juliapkg`` exactly, but
juliapkg resolves the Julia runtime and ``SymbolicRegression.jl`` from
compatibility ranges (``julia = "=1.10.0, 1.10.3"``, ``SymbolicRegression =
"~1.11.0"``) at install time.  A fresh install months later can therefore
resolve a different patch release of either.  Pinning is not available
through that path, so the identity is instead frozen here and checked at
execution time, failing closed.

Nothing in this module chooses a version.  Every frozen value below is the
version already used by the audited A3.2 null calibration.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_src = str(ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
_scripts = str(Path(__file__).resolve().parent)
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

from muru.paper_benchmark.rc3_provenance import (  # noqa: E402
    RC2_LOCK_COMMIT,
    RC2_LOCK_RELPATH,
    RC2_LOCK_SHA256,
    REQUIRED_PACKAGES,
)

ENVIRONMENT_CLOSURE_IDENTITY = "muru-rc4.1-environment-closure-1.0.0"

#: The RC4 engineering freeze this closure is a child of.
RC4_PARENT_COMMIT = "c800e7a59eca904ee32231e43ce3d1ddda4a26ee"
RC4_PARENT_TAG = "engineering-rc4-a3-4"

#: The tracked bootstrap a replicator installs from, and the pin source the
#: frozen runtime guard verifies.  After this closure they are the same bytes.
TRACKED_LOCK_RELPATH = "requirements.lock.txt"

#: Interpreter identity of the environment that executed the audited A3.2
#: calibration, read from its frozen execution manifest.
FROZEN_PYTHON_VERSION = "3.13.12"
FROZEN_PYTHON_IMPLEMENTATION = "CPython"

#: Julia-side identity, read from the live session of the environment that
#: executed the audited A3.2 calibration.  The calibration's own manifest
#: recorded ``julia: NOT_STARTED`` because building a manifest must not boot
#: a Julia runtime; these are the versions that same environment reports when
#: it is booted.
FROZEN_JULIA_VERSION = "1.12.6"
FROZEN_SYMBOLICREGRESSION_JL_VERSION = "1.11.3"
FROZEN_PYTHONCALL_JL_VERSION = "0.9.26"

JULIA_PROJECT_RELPATH = "configs/julia/Project.toml"
JULIA_MANIFEST_RELPATH = "configs/julia/Manifest.toml"
JULIA_PROJECT_SHA256 = (
    "2549db49b812ef17b253216303e7ea2078e6cfd903c9b42617c19689a27c54d7"
)
JULIA_MANIFEST_SHA256 = (
    "75fc2d89ed104eebeb8a8a77d8cc6582861d3ef123ba0934b5780c8a6b280705"
)

#: Import name -> distribution name, where they differ.
IMPORT_TO_DISTRIBUTION = {
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "PIL": "pillow",
}

#: Distributions retained for a stated scope other than prospective search.
#: ``gplearn`` is a historical Phase-3 / objective-validation baseline engine.
#: No prospective benchmark module executes it; the only prospective reference
#: is ``rc3_provenance.REQUIRED_PACKAGES``, which records its version and
#: refuses to build a provenance manifest when it is absent.  It is therefore
#: mandatory to INSTALL and not a prospective search engine.
DECLARED_SCOPES = {
    "gplearn": (
        "historical baseline engine (Phase 3 / objective validation) only; "
        "no prospective benchmark module executes it. Retained because the "
        "frozen provenance guard rc3_provenance.verify_dependencies requires "
        "it to be installed and pinned."
    ),
    "pymzml": "historical mzML acquisition path only",
    "pypdf": "historical reference-integrity check only",
    "statsmodels": "historical Phase-2 variance decomposition only",
    "matplotlib": "figure rendering only; no scientific value is computed",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pins[name.strip().lower()] = version.strip()
    return pins


def third_party_imports() -> dict[str, list[str]]:
    """Top-level non-stdlib, non-local imports reachable from the tree."""
    stdlib = set(sys.stdlib_module_names)
    local_modules = {"muru"}
    # Only TOP-LEVEL modules of scripts/ and tests/ are importable as bare
    # names (both directories are put on sys.path by their own callers and by
    # pytest).  Absorbing every nested stem would let a third-party
    # distribution that happens to share a filename with some test escape the
    # closure check unnoticed.
    for base in ("scripts", "tests"):
        for path in (ROOT / base).glob("*.py"):
            local_modules.add(path.stem)

    found: dict[str, set[str]] = {}
    for base in ("src", "scripts", "tests"):
        for path in sorted((ROOT / base).rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        continue
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for name in names:
                    if not name or name in stdlib or name in local_modules:
                        continue
                    found.setdefault(name, set()).add(
                        str(path.relative_to(ROOT))
                    )
    return {name: sorted(files) for name, files in sorted(found.items())}


def check_closure() -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []

    tracked = ROOT / TRACKED_LOCK_RELPATH
    pinned_source = ROOT / RC2_LOCK_RELPATH
    tracked_sha = sha256_file(tracked)
    source_sha = sha256_file(pinned_source)

    if source_sha != RC2_LOCK_SHA256:
        errors.append(
            f"PIN_SOURCE_DRIFT: {RC2_LOCK_RELPATH} sha256 {source_sha} != "
            f"{RC2_LOCK_SHA256}"
        )
    if tracked_sha != source_sha:
        errors.append(
            f"BOOTSTRAP_NOT_PIN_SOURCE: {TRACKED_LOCK_RELPATH} sha256 "
            f"{tracked_sha} != {RC2_LOCK_RELPATH} sha256 {source_sha}. The "
            f"file README.md tells a replicator to install from must be the "
            f"same bytes the runtime dependency guard enforces."
        )

    pins = read_pins(tracked)
    for distribution in sorted(REQUIRED_PACKAGES):
        if distribution.lower() not in pins:
            errors.append(f"REQUIRED_NOT_PINNED: {distribution}")

    imports = third_party_imports()
    unpinned_imports: list[str] = []
    for name in imports:
        distribution = IMPORT_TO_DISTRIBUTION.get(name, name)
        if distribution.lower() not in pins:
            unpinned_imports.append(name)
            errors.append(
                f"UNDECLARED_HARD_IMPORT: {name} (distribution "
                f"{distribution}) imported by {imports[name][0]} is not "
                f"pinned in {TRACKED_LOCK_RELPATH}"
            )

    julia_project = ROOT / JULIA_PROJECT_RELPATH
    julia_manifest = ROOT / JULIA_MANIFEST_RELPATH
    for relpath, path, expected in (
        (JULIA_PROJECT_RELPATH, julia_project, JULIA_PROJECT_SHA256),
        (JULIA_MANIFEST_RELPATH, julia_manifest, JULIA_MANIFEST_SHA256),
    ):
        if not path.exists():
            errors.append(f"JULIA_BINDING_MISSING: {relpath}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errors.append(
                f"JULIA_BINDING_DRIFT: {relpath} sha256 {actual} != {expected}"
            )

    installed = {
        distribution: _installed(distribution)
        for distribution in sorted(set(REQUIRED_PACKAGES) | {"juliapkg", "mpmath"})
    }

    payload: dict[str, object] = {
        "identity": ENVIRONMENT_CLOSURE_IDENTITY,
        "rc4_parent_commit": RC4_PARENT_COMMIT,
        "rc4_parent_tag": RC4_PARENT_TAG,
        "tracked_lock_relpath": TRACKED_LOCK_RELPATH,
        "tracked_lock_sha256": tracked_sha,
        "pin_source_relpath": RC2_LOCK_RELPATH,
        "pin_source_sha256": source_sha,
        "pin_source_commit": RC2_LOCK_COMMIT,
        "pinned_distribution_count": len(pins),
        "pins": dict(sorted(pins.items())),
        "python_version": FROZEN_PYTHON_VERSION,
        "python_implementation": FROZEN_PYTHON_IMPLEMENTATION,
        "julia": {
            "julia": FROZEN_JULIA_VERSION,
            "SymbolicRegression.jl": FROZEN_SYMBOLICREGRESSION_JL_VERSION,
            "PythonCall.jl": FROZEN_PYTHONCALL_JL_VERSION,
            "project_relpath": JULIA_PROJECT_RELPATH,
            "project_sha256": JULIA_PROJECT_SHA256,
            "manifest_relpath": JULIA_MANIFEST_RELPATH,
            "manifest_sha256": JULIA_MANIFEST_SHA256,
            "resolution_note": (
                "juliapkg resolves julia and SymbolicRegression.jl from "
                "compatibility ranges, not pins; the identity is enforced at "
                "execution time by assert_julia_identity rather than pinned "
                "by the installer"
            ),
        },
        "third_party_imports": imports,
        "unpinned_imports": sorted(unpinned_imports),
        "declared_scopes": dict(sorted(DECLARED_SCOPES.items())),
        "installed_versions": installed,
        # Derived from the tree, not asserted: every path under
        # src/muru/paper_benchmark/ is compared byte-for-byte against the RC4
        # parent.  A self-declared "no science changed" flag would be worth
        # nothing.  This is the raw diff (never filtered) so the true history
        # is always visible; RC4.2.1 gates on the *unauthorized* subset below,
        # not on this field being empty.
        "paper_benchmark_paths_changed_vs_rc4_parent": _paper_benchmark_drift(),
        # The Julia identity is NOT covered by this flag; it is verified only
        # under --start-julia and recorded separately.  See
        # julia_identity_proof_relpath and limitation L1 in
        # ENVIRONMENT_CLOSURE.md.
        "static_closure_verified": not errors,
        "julia_identity_proof_relpath": "configs/rc4_1_julia_identity_proof.json",
        "errors": errors,
    }
    drift = payload["paper_benchmark_paths_changed_vs_rc4_parent"]
    if drift and drift != ["UNKNOWN_GIT_UNAVAILABLE"]:
        from pb_rc4_2_authorized_delta import split_unexpected_changed

        unauthorized, authorized = split_unexpected_changed(
            drift, frozen_commit=RC4_PARENT_COMMIT, root=ROOT,
        )
        payload["paper_benchmark_paths_changed_vs_rc4_parent_authorized_rc4_2_delta"] = authorized
        payload["paper_benchmark_paths_changed_vs_rc4_parent_unauthorized"] = unauthorized
        if unauthorized:
            errors.append(f"SCIENCE_DRIFT_VS_RC4_PARENT: {unauthorized}")
            payload["static_closure_verified"] = False
    else:
        payload["paper_benchmark_paths_changed_vs_rc4_parent_authorized_rc4_2_delta"] = []
        payload["paper_benchmark_paths_changed_vs_rc4_parent_unauthorized"] = []
    return errors, payload


def _paper_benchmark_drift() -> list[str]:
    """Paths under src/muru/paper_benchmark/ that differ from the RC4 parent."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", RC4_PARENT_COMMIT, "--",
         "src/muru/paper_benchmark/"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return ["UNKNOWN_GIT_UNAVAILABLE"]
    return sorted(line for line in result.stdout.splitlines() if line)


def _installed(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


class JuliaIdentityMismatch(RuntimeError):
    """The live Julia stack is not the frozen one."""


def pin_julia_project(target: Path) -> dict[str, str]:
    """Materialise the frozen Julia graph into ``target`` and instantiate it.

    juliapkg resolves from compatibility ranges, so a fresh install reproduces
    the three gated versions but not necessarily the whole transitive graph.
    Reviewed evidence: a fresh resolution two days after the calibration
    environment matched on julia, SymbolicRegression.jl and PythonCall.jl but
    drifted on 3 of 115 Julia packages (ArrayInterface 7.28.1 -> 7.29.0,
    TestItems 1.0.0 -> 1.1.0, pixi_jll 0.63.2+0 -> 0.76.2+0).

    Seeding a project from ``configs/julia`` and instantiating it restores the
    exact graph.  Verified: instantiating reproduces ArrayInterface 7.28.1
    alongside SymbolicRegression 1.11.3 on julia 1.12.6, and leaves
    ``Manifest.toml`` byte-identical.

    Returns the environment variables that make juliapkg use it instead of
    re-resolving.  Nothing here is a version choice: both files are the frozen
    vendored bytes, hash-checked before use.
    """
    import shutil
    import subprocess

    errors, _ = check_closure()
    julia_errors = [e for e in errors if e.startswith("JULIA_BINDING_")]
    if julia_errors:
        raise JuliaIdentityMismatch(
            "refusing to pin from a drifted vendored graph: " + "; ".join(julia_errors)
        )

    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for relpath in (JULIA_PROJECT_RELPATH, JULIA_MANIFEST_RELPATH):
        shutil.copyfile(ROOT / relpath, target / Path(relpath).name)

    import pysr  # noqa: F401  - must import before juliacall, or segfault
    from pysr.julia_import import jl  # type: ignore

    executable = str(jl.seval("string(Base.julia_cmd()[1])"))
    subprocess.run(
        [executable, f"--project={target}", "-e",
         "using Pkg; Pkg.instantiate()"],
        check=True,
    )
    return {
        "PYTHON_JULIAPKG_EXE": executable,
        "PYTHON_JULIAPKG_PROJECT": str(target),
        "PYTHON_JULIAPKG_OFFLINE": "yes",
    }


def assert_julia_identity() -> dict[str, str]:
    """Boot Julia through PySR and refuse a stack that is not the frozen one.

    Called by prospective execution paths, never at import time: booting
    Julia costs seconds and must not be a side effect.
    """
    import pysr  # noqa: F401  - must import before juliacall, or segfault
    from pysr.julia_import import jl  # type: ignore

    live = {
        "julia": str(jl.seval("string(VERSION)")),
        "SymbolicRegression.jl": str(
            jl.seval(
                "string(pkgversion(Base.loaded_modules[Base.PkgId("
                'Base.UUID("8254be44-1295-4e6a-a16d-46603ac705cb"), '
                '"SymbolicRegression")]))'
            )
        ),
        "PythonCall.jl": str(
            jl.seval(
                "string(pkgversion(Base.loaded_modules[Base.PkgId("
                'Base.UUID("6099a3de-0909-46bc-b1f4-468b9a2dfc0d"), '
                '"PythonCall")]))'
            )
        ),
    }
    frozen = {
        "julia": FROZEN_JULIA_VERSION,
        "SymbolicRegression.jl": FROZEN_SYMBOLICREGRESSION_JL_VERSION,
        "PythonCall.jl": FROZEN_PYTHONCALL_JL_VERSION,
    }
    mismatched = {k: (live[k], frozen[k]) for k in frozen if live[k] != frozen[k]}
    if mismatched:
        raise JuliaIdentityMismatch(
            "live Julia stack differs from the frozen environment closure: "
            + "; ".join(
                f"{k}: live {got}, frozen {want}"
                for k, (got, want) in sorted(mismatched.items())
            )
        )
    return live


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "configs" / "rc4_1_environment_manifest.json"
    )
    parser.add_argument(
        "--start-julia",
        action="store_true",
        help="boot Julia and verify the live stack against the frozen identity",
    )
    parser.add_argument(
        "--julia-proof",
        type=Path,
        default=ROOT / "configs" / "rc4_1_julia_identity_proof.json",
        help="where --start-julia writes its live verification",
    )
    parser.add_argument(
        "--pin-julia",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "seed DIR from configs/julia and instantiate it, restoring the "
            "exact frozen Julia graph, then print the environment variables "
            "that make juliapkg use it instead of re-resolving from ranges"
        ),
    )
    arguments = parser.parse_args()

    errors, payload = check_closure()

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")

    # The live Julia proof is written to its own file so that re-running this
    # script without --start-julia is idempotent and cannot silently erase a
    # recorded proof by replacing it with a run that never booted Julia.
    if arguments.start_julia:
        proof: dict[str, object] = {
            "identity": ENVIRONMENT_CLOSURE_IDENTITY,
            "frozen": {
                "julia": FROZEN_JULIA_VERSION,
                "SymbolicRegression.jl": FROZEN_SYMBOLICREGRESSION_JL_VERSION,
                "PythonCall.jl": FROZEN_PYTHONCALL_JL_VERSION,
            },
        }
        try:
            proof["live"] = assert_julia_identity()
            proof["julia_identity_verified"] = True
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            proof["live"] = {"error": f"{type(exc).__name__}: {exc}"}
            proof["julia_identity_verified"] = False
            errors.append(f"JULIA_IDENTITY: {exc}")
        (arguments.julia_proof).write_text(
            json.dumps(proof, indent=1, sort_keys=True) + "\n"
        )
        print(f"julia identity verified:  {proof['julia_identity_verified']}")

    print(f"identity:                {ENVIRONMENT_CLOSURE_IDENTITY}")
    print(f"RC4 parent:              {RC4_PARENT_COMMIT}")
    print(f"tracked lock:            {payload['tracked_lock_sha256']}")
    print(f"pinned distributions:    {payload['pinned_distribution_count']}")
    print(f"third-party imports:     {len(payload['third_party_imports'])}")
    print(f"undeclared hard imports: {len(payload['unpinned_imports'])}")
    print(f"julia (frozen):          {FROZEN_JULIA_VERSION}")
    print(f"SymbolicRegression.jl:   {FROZEN_SYMBOLICREGRESSION_JL_VERSION}")
    if not arguments.start_julia:
        print("julia identity:          NOT CHECKED (pass --start-julia)")

    if arguments.pin_julia is not None:
        try:
            environment = pin_julia_project(arguments.pin_julia)
            print("frozen Julia graph pinned; export these:")
            for key in sorted(environment):
                print(f"  {key}={environment[key]}")
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            errors.append(f"JULIA_PIN: {type(exc).__name__}: {exc}")
    if errors:
        print("ENVIRONMENT CLOSURE FAILED", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("static environment closure verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
