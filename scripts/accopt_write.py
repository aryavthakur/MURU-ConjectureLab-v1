from __future__ import annotations
import json, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT/"scripts"))
import accopt_selectors as S
OUT = WT/"artifacts"/"accopt"
res = json.loads((OUT/"run_result.json").read_text())
arch = json.loads((OUT/"architecture_comparison.json").read_text())
fdiag = json.loads((OUT/"failure_diagnosis.json").read_text())
held = json.loads((OUT/"held_out_selections.json").read_text())
worlds = S.load(); W = {w["world_id"]: w for w in worlds}
A = arch["architectures"]; G = res["gate"]

def pct(p): return f"{100*p[0]/max(p[1],1):.1f}% ({p[0]}/{p[1]})"
def ci(k,n):
    lo,hi = S.wilson(k,n); return f"[{100*lo:.1f}%, {100*hi:.1f}%]"

av = res["seed_availability"]
seedstats={}
for b in ("G1A","G1B","G1C"):
    x=[a for a in av if a["block"]==b]
    f=np.array([a["seeds_with_correct_family"] for a in x])
    s=np.array([a["seeds_with_correct_support"] for a in x])
    seedstats[b]={"n":len(x),"support_seeds_median":float(np.median(s)),
                  "support_seeds_min":int(s.min()),
                  "family_seeds_median":float(np.median(f)),
                  "family_seeds_min":int(f.min()),
                  "worlds_with_zero_family_seeds":int((f==0).sum())}

tax = res["failure_taxonomy"]
def taxc(*keys): return sum(tax.get(k,0) for k in keys)
FAIL = {
 "SEARCH_FAILURE": taxc("SEARCH_FAILURE_FAMILY","SEARCH_FAILURE_SUPPORT"),
 "SUPPORT_SELECTION_FAILURE": taxc("SUPPORT_SELECTION_FAILURE"),
 "FAMILY_SELECTION_FAILURE": taxc("FAMILY_SELECTION_FAILURE","FAMILY_SELECTION_FAILURE|NUMERICALLY_CLOSE"),
 "REPRESENTATIVE_FAILURE": taxc("REPRESENTATIVE_FAILURE","REPRESENTATIVE_FAILURE|NUMERICALLY_CLOSE"),
 "NULL_GATE_FAILURE": taxc("NULL_GATE_FAILURE"),
 "ALGEBRAIC_ADJUDICATION_FAILURE": sum(
     1 for d in fdiag if d["code"]!="OK" and not d["code"].startswith("SEARCH_FAILURE")
     and (d["rejection_is_structural_only"]
          or (d["rejection_is_numeric_only"] and d["rel_rmse"] <= 0.105))),
}
adjud = [d for d in fdiag if d["rejection_is_structural_only"]
         or (d["rejection_is_numeric_only"] and d["rel_rmse"] <= 0.105)]
knife = [d for d in fdiag if not d["code"].startswith("SEARCH_FAILURE") and (
    any("differs by 0.1" in r for r in d["reasons"]) or d["rel_rmse"] <= 0.105)]

payload = {
 "study": "MURU_ACCURACY_OPTIMIZATION",
 "mode": "RAPID_EXPLORATORY — NOT CONFIRMATORY",
 "date": time.strftime("%Y-%m-%d %H:%M:%S"),
 "data_surface": {"worlds": 323, "seeds_per_world": 30, "seed_runs": 9690,
                  "pareto_band_members_scored": 26600,
                  "band_members_in_positive_worlds": int(sum(a["n_members"] for a in av)),
                  "new_pysr_searches_run": 0},
 "cv": {"design": "deterministic stratified 5-fold BY WORLD; all 30 seeds of a "
                  "world stay in one fold",
        "strata": "block x noise_regime x category(positive/null/refusal)",
        "folds": res["folds"]},
 "baseline_30": A["BASELINE_30"],
 "architectures": A,
 "selected_architecture": "CONSENSUS_PLUS_REPRESENTATIVE_PLUS_REFUSAL_GATE "
                          "(family vote B2 = validation-quality-weighted; "
                          "representative R1 = highest validation R^2)",
 "variant_choice_unanimous_across_folds": True,
 "oracle_ceilings": res["oracle"],
 "seed_level_availability": seedstats,
 "gate": G,
 "r2_distributions": arch["r2_distributions"],
 "failure_counts": FAIL,
 "failure_rows": res["failure_rows"],
 "failure_diagnosis": fdiag,
 "adjudication_boundary_cases": adjud,
 "new_search_required": False,
 "bottleneck": ["REPRESENTATIVE SELECTION", "FAMILY AGGREGATION",
                "ALGEBRAIC ADJUDICATION"],
 "not_bottleneck": ["SEARCH", "SUPPORT AGGREGATION"],
 "variant_summary_all_30_seeds": res["variant_summary"],
}
(WT/"MURU_ACCURACY_OPTIMIZATION.json").write_text(json.dumps(payload, indent=1, default=str))
print("json written", FAIL)
