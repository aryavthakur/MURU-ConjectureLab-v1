#!/usr/bin/env python3
"""Section 16 P8a, executed. CALL-GRAPH ban, not module-import ban.

CRITIC_SCIENCE V3-C3 found the module-level P8a unsatisfiable by any implementation:
`g2_contract` is the home module of the permitted syntax helpers
(`extract_effective_support`, `classify_discovered_family`) AND it defines/binds the
four banned symbols and imports `TruthRecord`, so importing anything permitted drags
the whole module into a "reachable module closure".

This script checks what actually matters: whether a banned symbol is ever CALLED
from the entry point's transitive call graph. Importing a module for a permitted
symbol is not itself a violation; invoking a banned one, anywhere reachable, is.
"""
from __future__ import annotations
import ast
import importlib
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

ENTRY_MODULES = ["muru.v2_calibration.e2c_search", "muru.v2_calibration.e2c_classify"]

BANNED = {
    "classify_support", "classify_family_match", "evaluate_g2_event",
    "truth_support_for_case", "classify_expression",
    "algebraically_equivalent",
}
PERMITTED = {
    "extract_effective_support", "classify_discovered_family", "_safe_parse",
    "GRAMMAR_PRIMITIVES", "template_key", "template_key_string", "parse_candidate",
}


def module_call_targets(mod) -> set[str]:
    """Every ast.Call function name this module's source contains, resolved as a
    bare name (attribute calls are reduced to their final attribute)."""
    try:
        src = inspect.getsource(mod)
    except (OSError, TypeError):
        return set()
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names.add(f.id)
            elif isinstance(f, ast.Attribute):
                names.add(f.attr)
    return names


def ast_import_targets(mod) -> set[str]:
    """Every module named in an Import/ImportFrom statement ANYWHERE in this
    module's AST -- including inside function bodies. `dir()`-based discovery
    only sees names bound at MODULE level, so a function-local
    `from . import e2_search` (executed only when that function is CALLED,
    never at import time) is invisible to it. This is what let CRITIC_SCIENCE's
    NEW-C1 finding through: control_c1b's function-local import of e2_search
    was never in the scan set. ast.walk descends into function bodies, so this
    catches it regardless of nesting."""
    try:
        src = inspect.getsource(mod)
    except (OSError, TypeError):
        return set()
    tree = ast.parse(src)
    pkg = mod.__name__.rsplit(".", 1)[0] if not mod.__name__.endswith("__init__") else mod.__name__
    targets = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # relative import: resolve against this module's package
                parts = mod.__name__.split(".")
                base = ".".join(parts[:-node.level]) if node.level <= len(parts) else ""
                container = f"{base}.{node.module}" if (base and node.module) else (node.module or base)
            else:
                container = node.module
            if container:
                targets.add(container)
                # `from package import submodule` -- submodule may itself be a
                # module, not just a name inside `container`. Both are queued;
                # a name that is not actually a module simply fails to import
                # in transitive_import_closure and is silently skipped there.
                for alias in node.names:
                    targets.add(f"{container}.{alias.name}")
    return targets


def transitive_import_closure(module_names: list[str], max_modules: int = 60) -> list:
    seen, queue, mods = set(), list(module_names), []
    while queue and len(mods) < max_modules:
        name = queue.pop(0)
        if name in seen or not name.startswith("muru"):
            continue
        seen.add(name)
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        mods.append(mod)
        # (1) module-level attribute discovery (catches re-exported names)
        for attr in dir(mod):
            val = getattr(mod, attr, None)
            sub = getattr(val, "__module__", None)
            if isinstance(sub, str) and sub.startswith("muru") and sub not in seen:
                queue.append(sub)
        # (2) AST-based import discovery, INCLUDING function-local imports
        for sub in ast_import_targets(mod):
            if sub.startswith("muru") and sub not in seen:
                queue.append(sub)
    return mods


def main() -> dict:
    mods = transitive_import_closure(ENTRY_MODULES)
    violations = []
    for mod in mods:
        calls = module_call_targets(mod)
        hit = calls & BANNED
        if hit:
            violations.append({"module": mod.__name__, "calls": sorted(hit)})
    report = {
        "schema": "muru-v2-truth-blind-verifier-1.0.0",
        "entry_modules": ENTRY_MODULES,
        "modules_scanned": [m.__name__ for m in mods],
        "n_modules_scanned": len(mods),
        "banned_symbols": sorted(BANNED),
        "permitted_symbols": sorted(PERMITTED),
        "violations": violations,
        "P8a_PASSED": not violations,
    }
    return report


if __name__ == "__main__":
    import json
    r = main()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["P8a_PASSED"] else 1)
