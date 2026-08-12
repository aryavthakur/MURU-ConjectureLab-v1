"""Candidate selection must not be able to inspect the planted answer.

Two separate guarantees, tested separately:

* the **truth module** is outside the import closure of every discovery-side
  module, walked transitively rather than grepped, exactly as
  `tests/test_p3_import_graph.py` does for Phase 3;
* the **truth manifest artifact** is referenced by no search-side or
  selection-side script, and the recovery script refuses to open it until every
  world in scope has a frozen selection result and a frozen verdict.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"

# The Type 2 discovery side: everything selection runs through.
DISCOVERY_SIDE = ["muru.objval.signature", "muru.objval.select",
                  "muru.objval.equiv", "muru.objval.adjudicate",
                  "muru.objval.decision"]
FORBIDDEN = {"muru.objval.truth2", "muru.objval.generators2",
             "muru.synth.truth", "muru.synth.generators"}
TRUTH_ARTIFACT = "ov_truth_manifest"


def _module_path(mod: str) -> Path | None:
    p = SRC / (mod.replace(".", "/") + ".py")
    return p if p.exists() else None


def _imports(path: Path) -> set[str]:
    """Modules this file imports, including `from pkg import submodule`.

    That second form is the one this codebase actually uses — `generators2` says
    `from muru.objval import truth2` — so a checker that only recorded `pkg`
    would walk straight past a real leak.
    """
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module)
            for alias in node.names:
                cand = f"{node.module}.{alias.name}"
                if _module_path(cand) is not None:
                    out.add(cand)
    return out


def _closure(mod: str) -> set[str]:
    seen, stack = set(), [mod]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        p = _module_path(m)
        if p is None:
            continue
        for i in _imports(p):
            if i.startswith("muru.") and i not in seen:
                stack.append(i)
    return seen


@pytest.mark.parametrize("mod", DISCOVERY_SIDE)
def test_truth_is_outside_the_discovery_import_closure(mod):
    assert not (_closure(mod) & FORBIDDEN), \
        f"{mod} can reach a planted law: {sorted(_closure(mod) & FORBIDDEN)}"


def test_the_import_graph_check_can_actually_fail():
    """Plant a violation and require it to be caught."""
    tmp = SRC / "muru" / "objval" / "_leak_probe.py"
    tmp.write_text("from muru.objval import truth2  # noqa\n")
    try:
        assert "muru.objval.truth2" in _closure("muru.objval._leak_probe")
    finally:
        tmp.unlink()


def test_search_and_selection_scripts_never_open_the_truth_manifest():
    for name in ("ov_20_search.py", "ov_30_select.py", "ov_40_adjudicate.py"):
        text = (SCRIPTS / name).read_text()
        # a comment mentioning the manifest is fine; a read of it is not
        code = "\n".join(l for l in text.splitlines()
                         if not l.strip().startswith("#"))
        body = code.split('"""')[-1] if code.count('"""') >= 2 else code
        assert TRUTH_ARTIFACT not in body, f"{name} references the truth manifest"


def test_recovery_script_guards_on_frozen_selection_and_adjudication():
    text = (SCRIPTS / "ov_45_recovery.py").read_text()
    assert "refusing to open the truth manifest" in text
    assert "selstore.done" in text and "adjstore.done" in text


def test_world_manifest_carries_no_planted_law():
    from muru.objval.generators2 import build_world2
    from muru.synth.generators import load_dev_covariates
    w = build_world2("G1B", 0, "moderate", cov=load_dev_covariates())
    m = w.manifest()
    flat = repr(m)
    assert "planted" not in flat
    assert "sqrt(precursor_mz)" not in flat
    # and the truth record does carry it, so the separation is real
    assert "planted_expr" in w.truth_record()


def test_search_inputs_expose_only_response_and_covariates():
    from muru.objval.generators2 import build_world2
    from muru.synth.generators import load_dev_covariates
    w = build_world2("G1B", 1, "moderate", cov=load_dev_covariates())
    long, cov = w.search_inputs()
    assert set(long.columns) <= {"group_key", "ce_numeric", "mu",
                                 "retention_time_min"}
    assert "mu" in long.columns
    assert not any("planted" in c or "truth" in c for c in cov.columns)
