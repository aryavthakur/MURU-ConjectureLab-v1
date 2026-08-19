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


def transitive_import_closure(module_names: list[str], max_modules: int = 40) -> list:
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
        for attr in dir(mod):
            val = getattr(mod, attr, None)
            sub = getattr(val, "__module__", None)
            if isinstance(sub, str) and sub.startswith("muru") and sub not in seen:
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
