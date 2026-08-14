"""Engineering RC3: dependency provenance and seed-band separation.

Two jobs:

1. **Provenance.**  Emit a manifest recording the exact version of every
   engine that can change a number, plus the commit, and fail loudly when an
   installed version does not match the pinned lock.

2. **Seed-band separation.**  The engineering smoke must be unable to
   collide with any calibration seed.  The calibration band is derived from
   the frozen ``PB_SEED_BASE``/``PB_SEED_SPREAD``; the smoke band lives
   strictly below it, with a wide guard gap, and both stay signed-32-bit
   safe so Julia can consume them.

The lock consulted is ``configs/rc3_requirements_lock_c7c2332.txt``, a
byte-identical copy of ``requirements.lock.txt`` at RC2 commit
``c7c23324d40cd432bdd14bf9d3292b5a2867ef9e`` - the provenance the frozen
``CEILING_ESTIMATOR_SPEC`` names.  The tree's own ``requirements.lock.txt``
is a reduced Phase-1 lock that omits PySR, SymPy, gplearn and the Julia
bridge entirely, so it cannot serve as the RC3 pin source.

It lives under ``configs/`` rather than ``artifacts/`` because ``artifacts/``
is gitignored wholesale, and a runtime dependency guard that reads a file
absent from a fresh clone is not a guard.  ``configs/`` is tracked by the
repository's own stated convention.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .calibration_contract import (
    N_SEEDS_PER_WORLD,
    PB_SEED_BASE,
    PB_SEED_SPREAD,
)

__all__ = [
    "RC2_LOCK_RELPATH",
    "RC2_LOCK_COMMIT",
    "RC2_LOCK_SHA256",
    "REQUIRED_PACKAGES",
    "CALIBRATION_SEED_MIN",
    "CALIBRATION_SEED_MAX",
    "RC3_SMOKE_SEED_BASE",
    "RC3_SMOKE_SEED_MAX",
    "SIGNED_32BIT_MAX",
    "DependencyMismatch",
    "smoke_seed",
    "assert_seed_band_separation",
    "read_lock_pins",
    "verify_dependencies",
    "build_provenance_manifest",
]

ROOT = Path(__file__).resolve().parents[3]

RC2_LOCK_RELPATH = "configs/rc3_requirements_lock_c7c2332.txt"
RC2_LOCK_COMMIT = "c7c23324d40cd432bdd14bf9d3292b5a2867ef9e"
RC2_LOCK_SHA256 = "13b21b8ca409b82d1ef8d94aa5e487e2523d5264807f04fc1e65a5553c357fa8"

#: Distribution names for everything that can move a number.  Versions are
#: read from installed distribution metadata, never by importing the module:
#: importing ``juliacall`` ahead of ``pysr`` segfaults the interpreter, and a
#: provenance check must not be able to crash the run it is protecting.
#: Julia and SymbolicRegression.jl are recorded separately - not pip
#: distributions.
REQUIRED_PACKAGES: tuple[str, ...] = (
    "pysr",
    "gplearn",
    "sympy",
    "rdkit",
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "juliacall",
)


# -----------------------------------------------------------------------
# Seed-band separation
# -----------------------------------------------------------------------

SIGNED_32BIT_MAX = 2**31 - 1

#: The calibration band, computed from the frozen constants rather than
#: restated: base in [PB_SEED_BASE, PB_SEED_BASE + (PB_SEED_SPREAD-1)*100],
#: offsets 0..29.
CALIBRATION_SEED_MIN = PB_SEED_BASE
CALIBRATION_SEED_MAX = (
    PB_SEED_BASE + (PB_SEED_SPREAD - 1) * 100 + (N_SEEDS_PER_WORLD - 1)
)

#: The engineering band sits strictly BELOW the calibration band, not above:
#: above would exceed signed 32-bit.  The gap is ~200 million, far wider than
#: any plausible future widening of PB_SEED_SPREAD.
RC3_SMOKE_SEED_BASE = 1_900_000_000
RC3_SMOKE_SEED_SPAN = 1_000_000
RC3_SMOKE_SEED_MAX = RC3_SMOKE_SEED_BASE + RC3_SMOKE_SEED_SPAN - 1


class DependencyMismatch(RuntimeError):
    """An installed dependency does not match the pinned lock."""


#: Seeds per world in the smoke band's addressing scheme.  Bounding
#: ``seed_index`` is what makes ``smoke_seed`` injective: without it,
#: ``smoke_seed(0, 1000)`` and ``smoke_seed(1, 0)`` are the same seed.
RC3_SMOKE_SEEDS_PER_WORLD = 1000


def smoke_seed(world_index: int, seed_index: int) -> int:
    """Derive an engineering-smoke seed inside the quarantined band.

    Injective over its whole accepted domain, and every returned value lies
    in the band regardless of input.
    """
    if world_index < 0 or seed_index < 0:
        raise ValueError("indices must be non-negative")
    if seed_index >= RC3_SMOKE_SEEDS_PER_WORLD:
        raise ValueError(
            f"seed_index must be < {RC3_SMOKE_SEEDS_PER_WORLD}; larger values "
            f"would alias onto the next world's seeds"
        )
    seed = RC3_SMOKE_SEED_BASE + world_index * RC3_SMOKE_SEEDS_PER_WORLD + seed_index
    if seed > RC3_SMOKE_SEED_MAX:
        raise ValueError(f"smoke seed {seed} escapes the engineering band")
    return seed


def assert_seed_band_separation() -> dict[str, int]:
    """Fail loudly unless the two seed bands are provably disjoint."""
    if RC3_SMOKE_SEED_MAX >= CALIBRATION_SEED_MIN:
        raise RuntimeError(
            f"seed bands overlap: smoke max {RC3_SMOKE_SEED_MAX} >= "
            f"calibration min {CALIBRATION_SEED_MIN}"
        )
    if CALIBRATION_SEED_MAX > SIGNED_32BIT_MAX:
        raise RuntimeError(
            f"calibration seed max {CALIBRATION_SEED_MAX} exceeds signed 32-bit"
        )
    if RC3_SMOKE_SEED_BASE <= 0:
        raise RuntimeError("smoke seed band must be positive")
    return {
        "calibration_seed_min": CALIBRATION_SEED_MIN,
        "calibration_seed_max": CALIBRATION_SEED_MAX,
        "smoke_seed_min": RC3_SMOKE_SEED_BASE,
        "smoke_seed_max": RC3_SMOKE_SEED_MAX,
        "gap": CALIBRATION_SEED_MIN - RC3_SMOKE_SEED_MAX,
    }


# -----------------------------------------------------------------------
# Dependency verification
# -----------------------------------------------------------------------

def read_lock_pins(lock_path: Path | None = None) -> dict[str, str]:
    """Parse ``name==version`` pins from the RC2 lock, verifying its hash."""
    path = Path(lock_path) if lock_path is not None else ROOT / RC2_LOCK_RELPATH
    if not path.exists():
        raise DependencyMismatch(f"RC2 lock not found at {path}")

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if lock_path is None and digest != RC2_LOCK_SHA256:
        raise DependencyMismatch(
            f"{RC2_LOCK_RELPATH} sha256 is {digest}, expected {RC2_LOCK_SHA256} "
            f"(byte copy of requirements.lock.txt at {RC2_LOCK_COMMIT})"
        )

    pins: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, version = line.split("==", 1)
        pins[name.strip().lower()] = version.strip()
    return pins


def _installed_version(dist: str) -> str | None:
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


def verify_dependencies(lock_path: Path | None = None) -> dict[str, str]:
    """Fail loudly on any dependency mismatch against the pinned lock.

    Returns the installed version map on success.
    """
    pins = read_lock_pins(lock_path)
    installed: dict[str, str] = {}
    errors: list[str] = []

    for dist in sorted(REQUIRED_PACKAGES):
        expected = pins.get(dist.lower())
        actual = _installed_version(dist)
        installed[dist] = actual or "NOT_INSTALLED"
        if expected is None:
            errors.append(f"{dist}: not pinned in {RC2_LOCK_RELPATH}")
            continue
        if actual is None:
            errors.append(f"{dist}: not installed, lock pins {expected}")
            continue
        # rdkit reports 2026.03.5 for the 2026.3.5 pin; compare numerically.
        if not _versions_equal(actual, expected):
            errors.append(f"{dist}: installed {actual}, lock pins {expected}")

    if errors:
        raise DependencyMismatch(
            "dependency mismatch against "
            f"{RC2_LOCK_RELPATH} ({RC2_LOCK_COMMIT}):\n  "
            + "\n  ".join(errors)
        )
    return installed


def _versions_equal(actual: str, expected: str) -> bool:
    if actual == expected:
        return True
    def parts(v: str) -> tuple[int, ...] | None:
        try:
            return tuple(int(p) for p in v.split("."))
        except ValueError:
            return None
    a, b = parts(actual), parts(expected)
    return a is not None and a == b


# -----------------------------------------------------------------------
# Provenance manifest
# -----------------------------------------------------------------------

def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], capture_output=True, cwd=ROOT, check=False
        )
        return out.stdout.decode("utf-8").strip() if out.returncode == 0 else "UNKNOWN"
    except Exception:  # pragma: no cover - git always present in this repo
        return "UNKNOWN"


def _julia_versions(start_julia: bool = False) -> dict[str, str]:
    """Record the Julia side of the stack.

    ``start_julia=False`` (the default) reads the declared
    ``SymbolicRegression.jl`` pin from PySR's ``juliapkg.json`` without
    booting a Julia runtime.  Booting Julia costs seconds and must never be
    a side effect of building a manifest; the execution path passes
    ``start_julia=True`` once, after PySR is already imported.
    """
    versions = {"julia": "NOT_STARTED", "SymbolicRegression.jl": _srjl_from_juliapkg()}
    if not start_julia:
        return versions
    try:
        import pysr  # noqa: F401  - must import before juliacall, or segfault
        from pysr.julia_import import jl  # type: ignore

        versions["julia"] = str(jl.seval("string(VERSION)"))
    except Exception as exc:  # pragma: no cover - environment dependent
        versions["julia"] = f"UNAVAILABLE: {type(exc).__name__}"
    return versions


def _srjl_from_juliapkg() -> str:
    try:
        import json as _json

        spec = Path(importlib.metadata.distribution("pysr").locate_file("pysr")) / "juliapkg.json"
        if spec.exists():
            data = _json.loads(spec.read_text())
            for name, entry in data.get("packages", {}).items():
                if name == "SymbolicRegression":
                    return str(entry.get("version", "UNKNOWN"))
    except Exception:
        pass
    return "UNKNOWN"


@dataclass(frozen=True)
class ProvenanceManifest:
    commit: str
    dirty: bool
    lock_relpath: str
    lock_commit: str
    lock_sha256: str
    python_packages: Mapping[str, str]
    julia: Mapping[str, str]
    seed_bands: Mapping[str, int]

    def to_payload(self) -> dict:
        return {
            "commit": self.commit,
            "dirty": self.dirty,
            "lock_relpath": self.lock_relpath,
            "lock_commit": self.lock_commit,
            "lock_sha256": self.lock_sha256,
            "python_packages": dict(sorted(self.python_packages.items())),
            "julia": dict(sorted(self.julia.items())),
            "seed_bands": dict(sorted(self.seed_bands.items())),
        }


def build_provenance_manifest(
    strict: bool = True, start_julia: bool = False
) -> ProvenanceManifest:
    """Build the provenance manifest.

    With ``strict=True`` (the default and the only setting any execution
    path uses) a dependency mismatch raises rather than being recorded.
    """
    if strict:
        packages = verify_dependencies()
    else:
        packages = {
            dist: (_installed_version(dist) or "NOT_INSTALLED")
            for dist in sorted(REQUIRED_PACKAGES)
        }

    return ProvenanceManifest(
        commit=_git("rev-parse", "HEAD"),
        dirty=bool(_git("status", "--porcelain")),
        lock_relpath=RC2_LOCK_RELPATH,
        lock_commit=RC2_LOCK_COMMIT,
        lock_sha256=RC2_LOCK_SHA256,
        python_packages=packages,
        julia=_julia_versions(start_julia=start_julia),
        seed_bands=assert_seed_band_separation(),
    )
