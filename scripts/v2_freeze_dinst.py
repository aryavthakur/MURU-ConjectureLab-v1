#!/usr/bin/env python3
"""Regenerate D-INST's freeze record from the tool AS IT STANDS RIGHT NOW.

This exists because the freeze record went stale FOUR TIMES in a row
(14a50d51 -> a3f97e38 -> 9826cefe -> 1f8d4b4a, each written after the tool it
described had already moved on) -- CRITIC_GOVERNANCE G10, N4. A record that is
hand-edited every time the tool changes will always be one edit behind the tool.
This script computes the hash and the binding statement from the live file, so
"regenerate the freeze record" is one command, not a paragraph to remember to
rewrite.

Run this AFTER any change to scripts/e2a_instrument_diagnostic.py and BEFORE
Stage 0 executes. It is idempotent: running it twice with no tool change writes
byte-identical output.
"""
from __future__ import annotations
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "scripts" / "e2a_instrument_diagnostic.py"
PROTOCOL = ROOT / "audit" / "muru_v2_reentry_20260819" / "MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md"
OUT = ROOT / "audit" / "muru_v2_reentry_20260819" / "DINST_FREEZE_CURRENT.txt"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_constant(name: str) -> str:
    for line in TOOL.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{name} = ") or line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().split("#")[0].strip()
    return "NOT_FOUND"


def main() -> None:
    tool_hash = sha256(TOOL)
    proto_hash = sha256(PROTOCOL)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", str(TOOL)],
                           capture_output=True, text=True).stdout.strip()

    lines = [
        "# D-INST freeze record -- GENERATED, do not hand-edit (see v2_freeze_dinst.py)",
        f"# generated_from_commit: {commit}{'  [UNCOMMITTED CHANGES TO THE TOOL]' if dirty else ''}",
        "",
        f"{tool_hash}  scripts/e2a_instrument_diagnostic.py",
        f"{proto_hash}  audit/muru_v2_reentry_20260819/MURU_V2_E2A_INSTRUMENT_DIAGNOSTIC_PROTOCOL.md",
        "",
        "# Binding statement, mechanically derived from the tool source at generation time.",
        "Stage 0 results are admissible ONLY if produced by tool",
        f"    {tool_hash}",
        "under protocol",
        f"    {proto_hash}",
        "with:",
    ]
    for const in ("TIER1_CPU_SECONDS", "CLASSIFIER_VERSION", "CLASSIFY_CACHE_SHA256"):
        lines.append(f"    {const} = {extract_constant(const)}")
    lines.append("    ADDRESS_SPACE_BYTES = _host_rss_ceiling_bytes()  (host-derived rule, section 25.4 -- not a literal)")
    lines.append("")
    lines.append("Any record naming a different tool hash is STALE and MUST NOT be treated as binding;")
    lines.append("regenerate with `python3 scripts/v2_freeze_dinst.py` and re-commit before Stage 0 runs.")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")
    print(f"tool_hash = {tool_hash}")
    if dirty:
        print("WARNING: the tool has uncommitted changes; commit before treating this as a freeze.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
