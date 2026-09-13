"""Static choke-point checks for MSnLib confirmation study 2.

The runtime boundary (decode_authority + external_mzml.decode_selected) only helps if nothing routes around it.
These tests parse source files (no execution) and fail if:
  * any module under src/ or scripts/ outside a short, reasoned allowlist touches a binary-array decoding
    primitive (_decode_array, numpress_pic_decode, base64 b64decode, zlib decompress, pymzml, pyteomics,
    pyopenms, muru.io.mzml);
  * a study-2 script overrides an authority's root/ledger/allowlist location, builds an authority with
    __new__, assigns an authority's scope attributes, imports a legacy/void guard, or hard-codes another
    session's worktree or scratch path (the burned study's scripts did all of the last two).
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECODER = ROOT / "src/muru/wur_v2/external_mzml.py"
ALL_CODE = sorted(p for p in list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py"))
                  if "__pycache__" not in p.parts)
STUDY2_SCRIPTS = sorted((ROOT / "scripts/wur_v2_confirmation_v2").rglob("*.py"))
# The only code allowed to touch a decoding primitive, each with the reason it is safe.
DECODE_ALLOWLIST = {
    "src/muru/wur_v2/external_mzml.py": "the guarded decoder itself",
    "src/muru/io/mzml.py": "legacy LCSB raw-branch pymzml reader; refuses MSnLib/MultiMS2 paths (ExternalSourceRefused)",
    "scripts/t1_12_raw_branch.py": "legacy LCSB raw-branch driver of muru.io.mzml (LCSB mixes only)",
    "scripts/wur_v2/ext10_msnlib_anchor_files.py": "zlib inflates ZIP members to extract anchor files; decodes no array",
}

DECODE_PRIMITIVES = {"_decode_array", "numpress_pic_decode", "b64decode", "decodebytes", "decompress", "decompressobj"}
FORBIDDEN_MODULES = {"pymzml", "muru.io.mzml", "base64", "zlib", "gzip", "lzma", "bz2", "pyteomics", "pyopenms"}
AUTHORITIES = {"AnchorPreflightAuthority", "ConfirmationV2Authority"}
LOCATION_OVERRIDES = {"root", "code_root", "ledger_dir", "allowlist_rel", "exposed_files_rel", "study_id"}
SCOPE_ATTRS = {"authorized", "allowed", "files", "manifest", "freeze_commit", "ledger_path"}
LEGACY_GUARDS = {"muru.wur_v2.external_guard", "muru.wur_v2.confirmation_guard"}
FOREIGN_PATH_MARKERS = ("muru-accuracy-sprint", "/private/tmp", "recursive-executor-framework", "scratchpad")


def _tree(path):
    return ast.parse(path.read_text(), filename=str(path))


def _imported_modules(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module
            for a in node.names:
                yield f"{node.module}.{a.name}"


def _names(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, ast.alias):
            yield node.name.split(".")[-1]


def test_only_allowlisted_modules_touch_binary_decoding_primitives():
    offenders = []
    for path in ALL_CODE:
        rel = str(path.relative_to(ROOT))
        if rel in DECODE_ALLOWLIST:
            continue
        tree = _tree(path)
        bad_names = set(_names(tree)) & DECODE_PRIMITIVES
        bad_mods = {m for m in _imported_modules(tree)
                    if m in FORBIDDEN_MODULES or m.split(".")[0] in {"pymzml", "pyteomics", "pyopenms"}}
        if bad_names or bad_mods:
            offenders.append((rel, sorted(bad_names | bad_mods)))
    assert not offenders, offenders
    assert all((ROOT / rel).is_file() for rel in DECODE_ALLOWLIST)


def test_decoder_module_calls_authorize_before_decoding():
    src = DECODER.read_text()
    body = src[src.index("def decode_selected"):]
    assert body.index("guard.authorize(") < body.index("_decode_array(")
    assert "type(guard) not in _authority_types()" in body and "not _constructed(guard)" in body


def test_study2_scripts_do_not_weaken_or_bypass_authorities():
    problems = []
    for path in STUDY2_SCRIPTS:
        text = path.read_text()
        tree = _tree(path)
        rel = str(path.relative_to(ROOT))
        for marker in FOREIGN_PATH_MARKERS:
            if marker in text:
                problems.append((rel, f"foreign path marker {marker!r}"))
        for mod in _imported_modules(tree):
            if any(mod == g or mod.startswith(g + ".") for g in LEGACY_GUARDS):
                problems.append((rel, f"imports legacy/void guard {mod}"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if fn in AUTHORITIES:
                    overrides = {k.arg for k in node.keywords} & LOCATION_OVERRIDES
                    if overrides or any(k.arg is None for k in node.keywords):
                        problems.append((rel, f"{fn} constructed with overrides {sorted(overrides) or ['**kwargs']}"))
                if fn == "__new__":
                    problems.append((rel, "__new__ call"))
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    if isinstance(t, ast.Attribute) and t.attr in SCOPE_ATTRS:
                        problems.append((rel, f"assigns .{t.attr}"))
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setattr":
                problems.append((rel, "setattr call"))
    assert not problems, problems


def test_static_checker_detects_the_burned_preflight_pattern(tmp_path):
    """Self-test: the checks above must flag the actual as-run buggy script's constructs."""
    burned = ROOT / "artifacts/wur_v2_confirmation/QUARANTINE_leakage_incident_2026-09-13/10_parser_preflight_BUGGY_AS_RUN.py"
    text = burned.read_text()
    assert any(m in text for m in FOREIGN_PATH_MARKERS)
    tree = ast.parse(text)
    assigned = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    assert "authorized" in assigned      # class-level `authorized = True` duck guard
