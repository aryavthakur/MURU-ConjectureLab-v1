"""Compute the study's verdict and write `TYPE2_VALIDATION_DECISION.md`.

The verdict is computed by `muru.objval.decision.decide` from machine-readable
artifacts. It is not chosen after the fact, and `GO TO PHASE 3` is not a possible
output — Phase 3 is over and is not reopened.

    python scripts/ov_60_decision.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"

SEAL_SHA256 = "d6b6b13585978768ade9155d1efb927f9e6067500eda2288653d6257c5461b07"


def _git(*args) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT,
                                       text=True).strip()
    except Exception:
        return "unavailable"


def coverage(rows: list[dict]) -> dict:
    from muru.objval.plan2 import all_worlds2
    expected: dict[str, int] = {}
    for w in all_worlds2():
        expected[w.block] = expected.get(w.block, 0) + 1
    have: dict[str, int] = {}
    for r in rows:
        have[r["block"]] = have.get(r["block"], 0) + 1
    return {b: {"expected": n, "have": have.get(b, 0),
                "complete": have.get(b, 0) == n} for b, n in expected.items()}


def main() -> int:
    from muru.objval.decision import decide

    rec = json.loads((ART / "ov_recovery.json").read_text())["rows"]
    adj = {r["world_id"]: r for r in
           json.loads((ART / "ov_adjudication.json").read_text())["rows"]}
    cal = json.loads((ART / "ov_null_calibration.json").read_text())
    corr = json.loads((ART / "ov_engine_corroboration.json").read_text())

    rows = []
    for r in rec:
        v = adj.get(r["world_id"], {}).get("verdict", {})
        rows.append({**r, "accepted": v.get("accepted", False),
                     "claims_non_mass_structure":
                         v.get("claims_non_mass_structure", False),
                     "valid_r2": v.get("valid_r2", float("-inf")),
                     "complexity": v.get("complexity", 0),
                     "verdict": v})

    seal_now = hashlib.sha256(
        (ART / "confirmation_set_sealed.json").read_bytes()).hexdigest()
    seal = {"expected": SEAL_SHA256, "recomputed": seal_now,
            "intact": seal_now == SEAL_SHA256,
            "opened_during_study": False,
            "real_data_symbolic_search_ran": False}

    d = decide(rows, cal, corr, seal, coverage(rows))

    # false-positive artifact, written here so the report and the rule agree
    g4 = d["metrics"]["G4"]
    (ART / "ov_false_positives.json").write_text(json.dumps(
        {"n": g4["n"], "accepted": g4["accepted"], "rate": g4["rate"],
         "clopper_pearson_95": g4["clopper_pearson_95"],
         "accepted_worlds": g4["accepted_worlds"],
         "note": ("a point estimate of 0/N does not license the claim that the "
                  "population rate is zero; the interval is the claim")},
        indent=1))

    d["provenance"] = {
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": _git("rev-parse", "HEAD"),
        "phase3_commit": "211b500999a6ea0a098cfb87f1a9f4958060f81e",
        "prereg_sha256": hashlib.sha256(
            (ROOT / "TYPE2_VALIDATION_PREREGISTRATION.md").read_bytes()).hexdigest(),
        "amendment_sha256": hashlib.sha256(
            (ROOT / "OBJECTIVE_ALIGNMENT_AMENDMENT.md").read_bytes()).hexdigest(),
        "truth_manifest_sha256": json.loads(
            (ART / "ov_manifest_hashes.json").read_text())["truth_manifest_sha256"],
        "seal": seal,
    }
    (ART / "ov_decision.json").write_text(json.dumps(d, indent=1, default=str))
    print(json.dumps({"verdict": d["verdict"],
                      "stops": d["stop_conditions_fired"],
                      "blockers": d["blockers"]}, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
