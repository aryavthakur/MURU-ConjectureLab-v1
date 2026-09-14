"""Static choke-point checks for MSnLib confirmation study 2 (source parsing only, no execution).

The runtime boundary (decode_authority + external_mzml.decode_selected) only helps if nothing routes around it.
The pre-sampling leakage review (F-07) showed nine realistic bypass scripts that an earlier, narrower version of
these checks let through; every one of them is reproduced below as a self-test and must be flagged. Checks run over
every *.py and *.ipynb file in the repository except tests/ (tests construct synthetic data) and a short, reasoned
allowlist. They cannot see code that is never committed; the runtime provenance check refuses such code for the
one look itself.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".claude", "node_modules", "tests", "__pycache__", ".venv"}

DECODE_ALLOWLIST = {
    "src/muru/wur_v2/external_mzml.py": "the guarded decoder itself",
    "src/muru/io/mzml.py": "legacy LCSB raw-branch pymzml reader; opens only indexed LCSB files (content allowlist)",
    "scripts/t1_12_raw_branch.py": "legacy LCSB raw-branch driver of muru.io.mzml (LCSB mixes only)",
    "scripts/wur_v2/ext10_msnlib_anchor_files.py": "zlib inflates ZIP members to extract anchor files; decodes no array",
    "scripts/pb_34_rc3_integrity.py": "integrity scanner imports repo modules by computed name; decodes nothing",
    "artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/10_parser_preflight_BUGGY_AS_RUN.py":
        "quarantined incident evidence, preserved as run",
}
BOUNDARY_MODULES = {"src/muru/wur_v2/external_mzml.py", "src/muru/wur_v2/decode_authority.py"}

DECODE_PRIMITIVES = {"_decode_array", "numpress_pic_decode", "b64decode", "standard_b64decode", "urlsafe_b64decode",
                     "decodebytes", "a2b_base64", "decompress", "decompressobj"}
FORBIDDEN_MODULE_ROOTS = {"pymzml", "pyteomics", "pyopenms", "matchms", "spectrum_utils", "base64", "zlib", "gzip",
                          "lzma", "bz2", "binascii"}
PRIVATE_BOUNDARY_NAMES = {"_for_tests", "_TestOverrides", "_SCOPES", "_RECORDS", "_PERMIT", "_decode_array",
                          "authorize_decode", "_iter_spectra", "_spectrum_scope", "TEST_MODE_ENV"}
PRIVATE_STRINGS = ("MURU_DECODE_AUTHORITY_TEST_MODE",)
BOUNDARY_IMPORTS = ("muru.wur_v2.external_mzml", "muru.wur_v2.decode_authority")
AUTHORITY_CLASSES = {"AnchorPreflightAuthority", "ConfirmationV2Authority"}
REFLECTION_ATTRS = {"__dict__", "__kwdefaults__", "__defaults__", "__code__", "__globals__"}
LEGACY_GUARDS = ("muru.wur_v2.external_guard", "muru.wur_v2.confirmation_guard")
FOREIGN_PATH_MARKERS = ("muru-accuracy-sprint", "/private/tmp", "recursive-executor-framework", "scratchpad")


def _sources():
    for p in sorted(ROOT.rglob("*")):
        if p.suffix not in (".py", ".ipynb") or not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if set(rel.parts[:-1]) & SKIP_DIRS or rel.parts[0] in SKIP_DIRS:
            continue
        text = p.read_text(errors="replace")
        if p.suffix == ".ipynb":
            try:
                cells = json.loads(text).get("cells", [])
                text = "\n".join("".join(c.get("source", [])) for c in cells if c.get("cell_type") == "code")
            except json.JSONDecodeError:
                pass
        yield str(rel), text


def _module_aliases(tree) -> tuple[set, set]:
    """Names bound to the boundary modules, and names bound to authority classes."""
    mods, classes = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name in BOUNDARY_IMPORTS:
                    mods.add(a.asname or a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module:
            for a in n.names:
                full = f"{n.module}.{a.name}"
                if full in BOUNDARY_IMPORTS:
                    mods.add(a.asname or a.name)
                if n.module in BOUNDARY_IMPORTS and a.name in AUTHORITY_CLASSES:
                    classes.add(a.asname or a.name)
    return mods, classes


def _root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.value if not isinstance(node, ast.Call) else node.func
    return node.id if isinstance(node, ast.Name) else None


def violations(rel: str, text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    in_boundary = rel in BOUNDARY_MODULES
    if rel not in DECODE_ALLOWLIST:
        for n in ast.walk(tree):
            if isinstance(n, (ast.Name, ast.Attribute)):
                name = n.id if isinstance(n, ast.Name) else n.attr
                if name in DECODE_PRIMITIVES:
                    out.append(f"decode primitive {name}")
            elif isinstance(n, ast.Import):
                out += [f"imports {a.name}" for a in n.names if a.name.split(".")[0] in FORBIDDEN_MODULE_ROOTS
                        or a.name == "muru.io.mzml"]
            elif isinstance(n, ast.ImportFrom) and n.module:
                if n.module.split(".")[0] in FORBIDDEN_MODULE_ROOTS or n.module == "muru.io.mzml" or \
                        (n.module == "muru.io" and any(a.name == "mzml" for a in n.names)):
                    out.append(f"imports from {n.module}")
            elif isinstance(n, ast.Call):
                fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                if fn in ("import_module", "__import__"):
                    a0 = n.args[0] if n.args else None
                    if not isinstance(a0, ast.Constant) or str(a0.value).split(".")[0] in FORBIDDEN_MODULE_ROOTS:
                        out.append(f"dynamic import {fn}")
                if fn in ("decode", "encode") and _root_name(n.func) == "codecs":
                    enc = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == "encoding"), None)
                    if not isinstance(enc, ast.Constant) or any(x in str(enc.value) for x in ("zlib", "base64", "bz2")):
                        out.append("codecs decode")
    if not in_boundary:
        mods, classes = _module_aliases(tree)
        imports_boundary = bool(mods or classes) or any(b in text for b in BOUNDARY_IMPORTS)
        for n in ast.walk(tree):
            if isinstance(n, ast.Subscript):
                key = n.slice.value if isinstance(n.slice, ast.Constant) else None
                is_sys_modules = isinstance(n.value, ast.Attribute) and n.value.attr == "modules" and _root_name(n.value) == "sys"
                if is_sys_modules and (key is None or any(str(key).startswith(b) for b in BOUNDARY_IMPORTS)):
                    out.append("sys.modules access to a boundary module")
                if isinstance(key, str) and key in PRIVATE_BOUNDARY_NAMES | REFLECTION_ATTRS:
                    out.append(f"string subscript of private boundary name {key}")
            elif isinstance(n, ast.Call):
                fn = getattr(n.func, "id", None) or (n.func.attr if isinstance(n.func, ast.Attribute) else "")
                if isinstance(n.func, ast.Name) and fn in ("exec", "eval", "compile") and imports_boundary:
                    out.append(f"{fn}() in code that touches the decode boundary")
                if fn in ("getattr", "setattr", "delattr", "hasattr") and len(n.args) > 1 and \
                        isinstance(n.args[1], ast.Constant) and n.args[1].value in PRIVATE_BOUNDARY_NAMES:
                    out.append(f"{fn} of private boundary name {n.args[1].value}")
        for n in ast.walk(tree):
            if isinstance(n, (ast.Name, ast.Attribute)):
                name = n.id if isinstance(n, ast.Name) else n.attr
                if name in PRIVATE_BOUNDARY_NAMES:
                    out.append(f"private boundary name {name}")
                if isinstance(n, ast.Attribute) and n.attr in REFLECTION_ATTRS and (mods or classes):
                    out.append(f"reflection {n.attr}")
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and any(s in n.value for s in PRIVATE_STRINGS):
                out.append("test-mode switch string")
            elif isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete)):
                targets = n.targets if isinstance(n, (ast.Assign, ast.Delete)) else [n.target]
                for t in targets:
                    if isinstance(t, (ast.Attribute, ast.Subscript)) and _root_name(t) in (mods | classes):
                        out.append(f"assignment into boundary module/class {_root_name(t)}")
            elif isinstance(n, ast.Call):
                fn = getattr(n.func, "id", None) or (n.func.attr if isinstance(n.func, ast.Attribute) else "")
                if fn in ("setattr", "delattr", "getattr") and n.args and _root_name(n.args[0]) in (mods | classes):
                    a1 = n.args[1] if len(n.args) > 1 else None
                    if fn != "getattr" or not isinstance(a1, ast.Constant) or str(a1.value).startswith("_"):
                        out.append(f"{fn} on boundary module/class")
                if fn == "vars" and (mods or classes):
                    out.append("vars() in code that imports the boundary")
                if fn == "partial" and any(_root_name(a) in (mods | classes) or getattr(a, "attr", "") in AUTHORITY_CLASSES
                                           for a in n.args):
                    out.append("functools.partial of an authority")
                if fn in AUTHORITY_CLASSES and (n.keywords and any(k.arg != "log_path" for k in n.keywords)):
                    out.append(f"{fn} constructed with keywords {[k.arg for k in n.keywords]}")
                if fn == "__new__":
                    out.append("__new__ call")
    return out


def study2_violations(rel: str, text: str) -> list[str]:
    out = [f"foreign path marker {m!r}" for m in FOREIGN_PATH_MARKERS if m in text]
    tree = ast.parse(text)
    for n in ast.walk(tree):
        mod = n.module if isinstance(n, ast.ImportFrom) else None
        names = [a.name for a in n.names] if isinstance(n, (ast.Import, ast.ImportFrom)) else []
        for m in ([mod] if mod else []) + names:
            if any(m == g or m.startswith(g + ".") for g in LEGACY_GUARDS):
                out.append(f"imports legacy/void guard {m}")
        if isinstance(n, ast.Call):
            fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            if fn == "scan_headers" and not rel.endswith("01_build_exposure_registry.py"):
                out.append("full scan_headers on study-2 data (use scan_headers_rung_only)")
    return out


def test_no_source_file_routes_around_the_decode_boundary():
    problems = {rel: v for rel, text in _sources() if (v := violations(rel, text))}
    assert not problems, problems
    assert all((ROOT / rel).is_file() for rel in DECODE_ALLOWLIST)


def test_study2_scripts_follow_the_study_rules():
    problems = {}
    for p in sorted((ROOT / "scripts/wur_v2_confirmation_v2").rglob("*.py")):
        rel = str(p.relative_to(ROOT))
        v = study2_violations(rel, p.read_text())
        if v:
            problems[rel] = v
    assert not problems, problems


def test_decoder_orders_authorization_before_the_permit_and_decode():
    src = (ROOT / "src/muru/wur_v2/external_mzml.py").read_text()
    body = src[src.index("def decode_selected"):]
    assert body.index("DA.authorize_decode(") < body.index("_PERMIT.set(") < body.index("_decode_array(b)")
    assert "type(guard) not in DA.AUTHORITY_TYPES or not DA.is_constructed(guard)" in body
    prim = src[src.index("def _decode_array"):src.index("def _spectrum_scope")]
    assert prim.index("_PERMIT.get() is None") < prim.index("b64decode")


BYPASSES = {   # the leakage reviewer's F-07 bypass scripts, as study scripts would write them
    "B01_subscript_widen": "from muru.wur_v2 import decode_authority as DA\nDA._SCOPES[a] = s\n",
    "B02_authorize_override": "from muru.wur_v2.decode_authority import AnchorPreflightAuthority\nAnchorPreflightAuthority.authorize = f\n",
    "B03_independent_decoder": "import binascii, codecs\nraw = codecs.decode(binascii.a2b_base64(t), 'zlib')\n",
    "B04_partial_override": "import functools\nfrom muru.wur_v2 import decode_authority as DA\nf = functools.partial(DA.AnchorPreflightAuthority, _ov=o)\n",
    "B05_getattr_private": "from muru.wur_v2 import external_mzml as X\nd = getattr(X, '_decode_' + 'array')\n",
    "B06_module_patch": "from muru.wur_v2 import external_mzml as X\nX._authority_module = lambda: fake\n",
    "B07_importlib": "import importlib\nm = importlib.import_module('pym' + 'zml')\n",
    "B08_test_mode_env": "import os\nos.environ['MURU_DECODE_AUTHORITY_TEST_MODE'] = '1'\n",
    "B09_vars": "from muru.wur_v2 import decode_authority as DA\nvars(DA)['SEL_TOL'] = 1.0\n",
    "B10_overrides": "from muru.wur_v2.decode_authority import ConfirmationV2Authority\nConfirmationV2Authority(_ov=o)\n",
    "B11_legacy_reader": "from muru.io.mzml import iter_ms2\n",
    "B12_new": "from muru.wur_v2.decode_authority import AnchorPreflightAuthority\nx = object.__new__(AnchorPreflightAuthority)\n",
    # round-2 leakage review NF-1: module objects reached through sys.modules and string subscripts
    "S1_sys_modules_authorize": "import sys\nsys.modules['muru.wur_v2.decode_authority'].__dict__['authorize_decode'] = f\n",
    "S2_sys_modules_authority_module": "import sys\nm = sys.modules['muru.wur_v2.external_mzml']\nm.__dict__['_authority_module'] = f\n",
    "S3_permit_by_string": "import sys\nd = vars(sys.modules['muru.wur_v2.' + 'external_mzml'])\nd['_PERMIT'].set(1)\n",
    "S4_exec": "import muru.wur_v2.external_mzml\nexec('X._PERMIT.set(1)')\n",
    "S5_getattr_string": "import sys\ng = getattr(sys.modules[name], '_decode_array')\n",
}


def test_every_known_bypass_pattern_is_flagged():
    for name, code in BYPASSES.items():
        assert violations(f"scripts/wur_v2_confirmation_v2/{name}.py", code), name
    assert violations("scripts/wur_v2_confirmation_v2/x.py",
                      "from muru.wur_v2 import external_mzml as X\nX.decode_selected(src, ids, auth)\n") == []


def test_checker_flags_the_burned_preflight():
    rel = "artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/10_parser_preflight_BUGGY_AS_RUN.py"
    text = (ROOT / rel).read_text()
    assert study2_violations("scripts/wur_v2_confirmation_v2/burned.py", text)
