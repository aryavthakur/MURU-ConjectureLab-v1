"""Engineering-owned paths inside the frozen tracked-path sets.

The amendment integrity scripts (`pb_30`, `pb_31`, `pb_32`) enumerate *every*
tracked path at their reference commit and treat an undeclared change as a
breach.  That set includes engineering-only files carrying no benchmark
science, so an engineering repair to one of them needs somewhere honest to be
declared.

It is declared HERE and not inside any amendment's allowed-change set, so an
engineering exemption can never be read as a science amendment, and so all
three scripts agree by construction rather than by three copies staying in
sync.

Current contents
----------------
``requirements.lock.txt``
    RC4.1 environment closure.  It was a reduced 39-pin Phase-1 lock omitting
    SymPy, mpmath, PySR, gplearn and the Julia bridge, while `README.md`
    instructs a replicator to build the environment from exactly that file.
    It is now byte-identical to `configs/rc3_requirements_lock_c7c2332.txt`,
    the 50-pin lock the frozen runtime guard already enforced and the audited
    A3.2 calibration declared in its own execution manifest.  No version was
    chosen and no science moved.
"""
from __future__ import annotations

ENGINEERING_OWNER = "RC4.1_environment_closure"

ENGINEERING_CHANGED_PATHS = frozenset({
    "requirements.lock.txt",
})

#: Prefixes an engineering-declared path may never touch.  Without this, the
#: engineering channel would simply be a second, unaudited way to change the
#: benchmark.
SCIENCE_SURFACE_PREFIXES = (
    "src/muru/paper_benchmark/",
    "artifacts/",
    "MURU_PAPER_BENCHMARK",
    "tests/test_a3_",
    "tests/test_paper_benchmark",
    "configs/dataset.yaml",
    "configs/preprocessing.yaml",
    "inputs/",
    "truth/",
)


class EngineeringExemptionCoversScience(RuntimeError):
    """An engineering-declared path reaches the benchmark science surface."""


def science_surface_violations() -> list[str]:
    """Engineering-declared paths that reach the benchmark science surface.

    Returned rather than asserted so a manifest can record the *computed*
    result instead of a hardcoded ``True``.
    """
    return sorted(
        path
        for path in ENGINEERING_CHANGED_PATHS
        if path.startswith(SCIENCE_SURFACE_PREFIXES)
    )


def assert_engineering_paths_carry_no_science() -> None:
    offending = science_surface_violations()
    if offending:
        raise EngineeringExemptionCoversScience(
            "ENGINEERING_EXEMPTION_COVERS_SCIENCE: "
            + ", ".join(offending)
            + " - an engineering exemption may never be used to change a "
            "benchmark science path"
        )
