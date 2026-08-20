"""FRESH HOLDOUT — Phase A: record and verify the method freeze.

Runs BEFORE any holdout world exists. Records git identity, SHA256 of every
frozen implementation file on the scientific decision path, interpreter/engine
versions, and FITS THE DEPLOYMENT GATE ONCE on the full development population.

The sprint fit (t1, t2) per CV fold, which is the correct way to *estimate*
gate performance but does not by itself define a deployable gate. The frozen
gate FORM and the frozen fitting rule (`accopt_selectors.fit_gate`, maximise
sensitivity subject to training null FPR <= 5%) are applied ONCE to all 286
development positive+null worlds, giving a single (t1, t2) that is fixed here,
before the holdout exists. No holdout quantity is available at this point.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

FROZEN_FILES = [
    "src/muru/objval/select.py",
    "src/muru/objval/equiv.py",
    "src/muru/objval/signature.py",
    "src/muru/objval/recovery.py",
    "src/muru/objval/generators2.py",
    "src/muru/objval/truth2.py",
    "src/muru/objval/plan2.py",
    "src/muru/discovery/grammar.py",
    "src/muru/discovery/engine.py",
    "src/muru/discovery/protocol.py",
    "src/muru/discovery/checkpoint.py",
    "src/muru/synth/generators.py",
    "scripts/accopt_selectors.py",
    "scripts/accopt_build_cache.py",
    "artifacts/sprint/architecture_freeze.json",
]

POSITIVE_BLOCKS = {"G1A", "G1B", "G1C"}
NULL_BLOCKS = {"G4", "G4M", "NCAL"}


def sh(*a):
    try:
        return subprocess.run(a, cwd=ROOT, capture_output=True,
                              text=True).stdout.strip()
    except Exception:
        return ""


def block_of(wid: str) -> str:
    p = wid.split("|")
    if p[1] == "NULL":
        return "NCAL"
    fam = p[1]
    return fam


def main() -> int:
    import accopt_selectors as sel
    from muru.discovery import engine, grammar
    from muru.objval import plan2

    hashes = {}
    for rel in FROZEN_FILES:
        p = ROOT / rel
        hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()

    # ---- fit the deployment gate ONCE on the full development population ---
    dev = json.loads((ROOT / "artifacts" / "sprint"
                      / "outer_fold_predictions.json").read_text())["A_CURRENT_FINAL"]
    rows = []
    for wid, r in sorted(dev.items()):
        b = block_of(wid)
        cat = ("positive" if b in POSITIVE_BLOCKS
               else "null" if b in NULL_BLOCKS else "refusal")
        rows.append({"world_id": wid, "block": b, "category": cat,
                     "gate": {"median_seed_best_r2": r["gate"]["median_seed_best_r2"],
                              "selection_fraction": r["gate"]["selection_fraction"]}})
    gate = sel.fit_gate(rows)
    npos = sum(r["category"] == "positive" for r in rows)
    nnul = sum(r["category"] == "null" for r in rows)

    versions = {"python": sys.version.split()[0]}
    try:
        import pysr
        versions["pysr"] = pysr.__version__
    except Exception as e:                                    # pragma: no cover
        versions["pysr"] = f"unavailable: {e}"
    try:
        import sympy
        versions["sympy"] = sympy.__version__
    except Exception:
        pass
    try:
        import numpy
        versions["numpy"] = numpy.__version__
    except Exception:
        pass
    versions["julia"] = sh("julia", "--version") or "not on PATH (juliacall-managed)"

    out = {
        "phase": "A_METHOD_FREEZE",
        "purpose": ("Frozen-method identity recorded BEFORE the fresh holdout "
                    "population exists."),
        "git": {"head": sh("git", "rev-parse", "HEAD"),
                "branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD"),
                "status_porcelain": sh("git", "status", "--porcelain"),
                "clean": sh("git", "status", "--porcelain") == ""},
        "frozen_architecture": {
            "family_aggregation": "B2 validation-quality-weighted family vote",
            "representative": "R1 highest-validation-R2 representative",
            "null_gate": ("CURRENT_GATE: REPORT iff median_seed_best_r2 >= t1 "
                          "AND selection_fraction >= t2"),
            "recovery": "corrected production parser (muru.objval.recovery)",
            "grammar": "frozen p3 grammar, SAFE_EXP NOT adopted",
            "cas": "SymPy only",
            "excluded": ["STRUCTURAL_MODAL", "CONSTANT_REFIT",
                         "ROBUST_GENERALIZATION", "SMALL_FAMILY_RANKER",
                         "MONOTONIC_LINEAR_GATE", "SAFE_EXP", "Maxima",
                         "Giac", "Wolfram"],
        },
        "deployment_gate": {
            "form": "CURRENT_GATE",
            "fitting_rule": ("accopt_selectors.fit_gate — maximise positive "
                             "sensitivity subject to null FPR <= 5%"),
            "fit_population": "full development population, architecture A_CURRENT_FINAL",
            "n_positive": npos, "n_null": nnul,
            "t1": gate["t1"], "t2": gate["t2"],
            "dev_fit_sensitivity": gate["train_sens"],
            "dev_fit_fpr": gate["train_fpr"],
            "frozen_before_holdout_exists": True,
        },
        "frozen_constants": {
            "EXPONENT_TOL": getattr(grammar, "EXPONENT_TOL", None),
            "BAND_TOL": sel.BAND_TOL,
            "MAX_COMPLEXITY": grammar.MAX_COMPLEXITY,
            "PYSR_CONFIG": {k: (v if isinstance(v, (int, float, str, bool, type(None)))
                                else str(v)) for k, v in engine.PYSR_CONFIG.items()},
            "ENGINE_VERSION": engine.ENGINE_VERSION,
            "PLAN2_VERSION": plan2.PLAN2_VERSION,
        },
        "file_sha256": hashes,
        "versions": versions,
        "development_reference_numbers": {
            "support_ungated": [55, 56], "support_end_to_end": [54, 56],
            "family_recovery": [47, 56], "G1A_family": [6, 6],
            "G1B_family": [35, 40], "G1C_family": [6, 10],
            "null_fpr": 7 / 230, "sensitivity": 0.9642857142857143,
            "specificity": 0.9695652173913043,
            "balanced_accuracy": 0.9669254658385094,
            "roc_auc": 0.9990683229813665,
            "provenance": ("DEVELOPMENT cross-validation, NOT fresh-holdout "
                           "performance."),
        },
    }
    p = ROOT / "FRESH_HOLDOUT_METHOD_FREEZE.json"
    p.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps({"t1": gate["t1"], "t2": gate["t2"],
                      "dev_sens": gate["train_sens"], "dev_fpr": gate["train_fpr"],
                      "n_pos": npos, "n_null": nnul,
                      "freeze_sha256": hashlib.sha256(p.read_bytes()).hexdigest()},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
