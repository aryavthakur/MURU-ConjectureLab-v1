"""Machine-readable summaries: Type 2 recovery, Type 3 diagnostic, refusal
worlds, checkpoint state and actual runtime.

Writes `artifacts/ov_type2_recovery.json`, `artifacts/ov_exact_form_recovery.json`,
`artifacts/ov_refusal_worlds.json`, `artifacts/ov_checkpoint_state.json` and
`artifacts/ov_runtime_actual.json`.

    python scripts/ov_55_summary.py
"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ART = ROOT / "artifacts"


def _load():
    rec = {r["world_id"]: r for r in
           json.loads((ART / "ov_recovery.json").read_text())["rows"]}
    adj = {r["world_id"]: r for r in
           json.loads((ART / "ov_adjudication.json").read_text())["rows"]}
    sel = {r["world_id"]: r for r in
           json.loads((ART / "ov_selection.json").read_text())["rows"]}
    return rec, adj, sel


def _frac(xs):
    xs = list(xs)
    return (sum(bool(x) for x in xs) / len(xs)) if xs else float("nan")


def main() -> int:
    from muru.objval.decision import type2_success
    rec, adj, sel = _load()

    groups: dict[str, list] = {}
    for w, r in rec.items():
        key = r["block"] if r["block"] not in ("G1A", "G1B") \
            else f"{r['block']}/{r['noise_regime']}"
        groups.setdefault(key, []).append(w)

    t2, t3 = {}, {}
    for key, ws in sorted(groups.items()):
        R = [rec[w]["recovery"] for w in ws]
        A = [adj[w]["verdict"] for w in ws]
        S = [sel[w]["reported"] for w in ws]
        applicable = [x for x in R if x["support_recovery"].get("applicable")]
        t2[key] = {
            "n": len(ws),
            "accepted": sum(v["accepted"] for v in A),
            "type2_success": sum(type2_success({**rec[w],
                                                "accepted": adj[w]["verdict"]["accepted"]})
                                 for w in ws),
            "support_recovered": _frac(x["support_recovery"].get("recovered")
                                       for x in applicable),
            "exponent_recovered": _frac(x["exponent_recovery"].get("recovered")
                                        for x in applicable),
            "shape_family_recovered": _frac(x["shape"].get("shape_family_recovered")
                                            for x in R if x["shape"].get("applicable")),
            "family_recovered": _frac(x["family_recovery"].get("recovered")
                                      for x in applicable),
            "median_selection_fraction": st.median(
                [rec[w]["selection_fraction"] for w in ws]),
            "median_complexity": st.median(
                [(adj[w]["verdict"].get("complexity") or 0) for w in ws]),
            "median_test_r2": st.median(
                [(adj[w]["verdict"].get("test_r2") or float("nan")) for w in ws]),
            "median_ceiling_fraction": st.median(
                [(adj[w]["verdict"].get("ceiling_fraction") or float("nan"))
                 for w in ws]),
            # counted over ALL worlds, accepted or not; the gates use the
            # accepted-only count, which is in ov_refusal_worlds.json
            "non_mass_claim_regardless_of_acceptance": sum(
                bool(v.get("claims_non_mass_structure")) for v in A),
            "accepted_and_claiming_non_mass_structure": sum(
                bool(v["accepted"] and v.get("claims_non_mass_structure"))
                for v in A),
        }
        t3[key] = {
            "n": len(ws),
            "search_found_the_law": _frac(x["exact_form"].get("search_found_the_law")
                                          for x in R if x["exact_form"].get("applicable")),
            "system_reported_the_law": _frac(
                x["exact_form"].get("system_reported_the_law")
                for x in R if x["exact_form"].get("applicable")),
            "symbolically_equivalent": _frac(
                x["exact_form"].get("symbolically_equivalent")
                for x in R if x["exact_form"].get("applicable")),
            "median_distinct_algebraic_forms": st.median(
                [s["n_distinct_algebraic_forms"] for s in S if s] or [0]),
            "worlds_claiming_form_identified": sum(
                bool(s and s["algebraic_form_identified"]) for s in S),
        }

    refusal = {}
    for b in ("G2", "G3", "G4", "G4M", "G5", "GC", "GRT", "NCAL"):
        ws = [w for w in rec if rec[w]["block"] == b]
        refusal[b] = {
            "n": len(ws),
            "accepted": sum(adj[w]["verdict"]["accepted"] for w in ws),
            "accepted_claiming_non_mass_structure": sum(
                bool(adj[w]["verdict"]["accepted"]
                     and adj[w]["verdict"].get("claims_non_mass_structure"))
                for w in ws),
            "h_main_rejected": sum(bool(adj[w].get("hmain", {}).get("h_main_rejected"))
                                   for w in ws),
            "accepted_worlds": [w for w in ws if adj[w]["verdict"]["accepted"]],
        }

    ck = ART / "ov_ckpt"
    state = {
        "checkpoint_root": str(ck.relative_to(ROOT)),
        "search_units": sum(1 for p in ck.rglob("*.json") if p.name != "_world.json"),
        "world_records": sum(1 for p in ck.rglob("_world.json")),
        "by_block": {d.name: sum(1 for p in d.rglob("*.json")
                                 if p.name != "_world.json")
                     for d in sorted(ck.iterdir()) if d.is_dir()},
        "selection_results": sum(1 for _ in (ART / "ov_sel").rglob("pysr.json")),
        "adjudication_results": sum(1 for _ in (ART / "ov_adj").rglob("pysr.json")),
    }

    runtime = {"stages": {}}
    for eng, pat in (("pysr", "/tmp/ov_search_s%d.log"),
                     ("gplearn", "/tmp/ov_gp_s%d.log")):
        mins = []
        for s in range(4):
            p = Path(pat % s)
            if not p.exists():
                continue
            m = re.findall(r"done: (\d+) run, (\d+) present, ([\d.]+) min",
                           p.read_text())
            if m:
                mins.append({"shard": s, "ran": int(m[-1][0]),
                             "present": int(m[-1][1]), "minutes": float(m[-1][2])})
        if mins:
            runtime["stages"][eng] = {
                "shards": mins, "wall_minutes": max(x["minutes"] for x in mins),
                "units": sum(x["ran"] for x in mins)}
    budget = json.loads((ART / "ov_runtime_budget.json").read_text())
    runtime["projected_hours"] = budget["projection"]["total_hours"]
    runtime["projected_pysr_s_per_run"] = budget["projection"]["pysr_wall_s_per_run"]
    if "pysr" in runtime["stages"]:
        p = runtime["stages"]["pysr"]
        runtime["actual_pysr_s_per_run"] = p["wall_minutes"] * 60 / max(1, p["units"])
    runtime["actual_total_hours"] = sum(
        v["wall_minutes"] for v in runtime["stages"].values()) / 60.0

    (ART / "ov_type2_recovery.json").write_text(json.dumps(t2, indent=1, default=str))
    (ART / "ov_exact_form_recovery.json").write_text(json.dumps(t3, indent=1, default=str))
    (ART / "ov_refusal_worlds.json").write_text(json.dumps(refusal, indent=1, default=str))
    (ART / "ov_checkpoint_state.json").write_text(json.dumps(state, indent=1))
    (ART / "ov_runtime_actual.json").write_text(json.dumps(runtime, indent=1))
    print(json.dumps({"type2": t2, "runtime": runtime}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
