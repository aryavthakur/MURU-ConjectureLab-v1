#!/usr/bin/env python3
"""Deterministic finalizer for the sealed Gate 1 artifacts.

reconcile_and_gate.py REGENERATES GATE_1_DEFINITIVE.json from scratch, which
silently clobbered post-hoc blocks added by hand (CRITIC_B caught exactly this:
AUTHORITY_OBJECT_PRESERVATION went missing after a re-run). Every enrichment now
lives here and is re-applied in one ordered pass, so the sealed artifact is
reproducible from: reconcile -> finalize -> render.
"""
import json, subprocess, sys
from pathlib import Path

D = Path(__file__).resolve().parent
G = D / "GATE_1_DEFINITIVE.json"


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()


def main():
    subprocess.run([sys.executable, str(D / "reconcile_and_gate.py")],
                   capture_output=True, text=True, check=True)
    g = json.loads(G.read_text())

    TAGS = [
        ("d6f607a", "muru-authority/d6f607a-reference", "authoritative reference replay"),
        ("dabcb4b", "muru-authority/dabcb4b-execution-freeze", "execution freeze; frozen evaluator SHA ee285a8b"),
        ("6b18dd8", "muru-authority/6b18dd8-post-run", "post-run commit carrying the corpus"),
        ("f4c1105", "muru-authority/f4c1105-preregistration", "preregistration; Gate 1 hook and the >10 tolerance"),
        ("befca0d", "muru-authority/befca0d-study-design", "G2 Pareto study design; 2.1 H_partial, 2.7, 2.9, 2.10, 2.11"),
        ("ae002d2", "muru-authority/ae002d2-v1-taxonomy", "v1 G2 failure taxonomy (the 69/57 source)"),
        ("1d20731", "muru-authority/1d20731-e3-identifiability", "E3 identifiability study, executed"),
        ("94abf97", "muru-authority/94abf97-e3-hostile-audit", "E3 independent hostile audit"),
        ("bdbcea6", "muru-authority/bdbcea6-e0-complete", "E0 complete"),
        ("4841f11", "muru-authority/4841f11-e1-complete", "E1 complete"),
    ]
    g["AUTHORITY_OBJECT_PRESERVATION"] = {
        "why": ("Every authority and prior-result commit this adjudication rests on is a "
                "NON-ANCESTOR of HEAD, reachable only from refs/remotes/mac-transfer/*. A git "
                "remote prune, re-clone or gc would have destroyed the evidential basis of a "
                "sealed governance verdict; commit 62b4b55 once already declared the "
                "preregistration 'unrecoverable' on exactly that basis."),
        "remedy": "Local tags under refs/tags/muru-authority/* pin every cited object.",
        "caveat": ("These tags are LOCAL. If this package is expected to travel, `git push --tags` "
                   "or a bundle is required, otherwise the preservation is host-local only."),
        "objects": {s: {"tag": t, "object_id": sh("git", "rev-parse", s), "description": d,
                        "was_ancestor_of_HEAD_before_tagging": False}
                    for s, t, d in TAGS},
    }
    extra = json.loads((D / "_gate_enrichment.json").read_text())
    g.update(extra)

    pre = g["definitive_preconditions"]
    ok = (all(pre[k] for k in pre) and g.get("CRITIC_A") == "PASS" and g.get("CRITIC_B") == "PASS")
    g["GATE_1_DEFINITIVE"] = "YES" if ok else "NO"
    G.write_text(json.dumps(g, indent=2))
    subprocess.run([sys.executable, str(D / "write_gate1_md.py")], check=True)
    print(f"finalized: GATE_1={g['GATE_1']} GATE_1_DEFINITIVE={g['GATE_1_DEFINITIVE']} "
          f"authority_objects={len(g['AUTHORITY_OBJECT_PRESERVATION']['objects'])}")


if __name__ == "__main__":
    main()
