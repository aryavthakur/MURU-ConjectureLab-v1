"""FINAL ACCURACY SPRINT — development replay with the frozen architecture.

Descriptive only. Runs the frozen architecture over the whole existing
development surface, with the gate fitted on that same surface (in-sample), and
reports it beside the honest held-out cross-validated numbers.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT / "scripts"))
import accopt_selectors as S
import sprint_arch as A
import sprint_run as R
import sprint_gate as G

OUT = WT / "artifacts" / "sprint"
ARCH = "A_CURRENT_FINAL"
GATE = "CURRENT_GATE"


def main():
    worlds = A.load_worlds()
    W = {w["world_id"]: w for w in worlds}
    preps = {w["world_id"]: A.prep(w) for w in worlds}
    all_ids = sorted(W)
    sel = R.run_selection(preps, W, all_ids, ARCH)
    rows = [{"world_id": w, "category": S.category(W[w]["block"]),
             "gate": sel[w]["gate"]} for w in all_ids]
    g = A.fit_gate1(rows) if GATE == "CURRENT_GATE" else A.fit_gate2(rows)
    g["form"] = GATE
    held = {}
    for w in all_ids:
        r = dict(sel[w])
        r["report"] = A.apply_gate(g, r["gate"])
        held[w] = r
    res = {"architecture": ARCH, "gate": GATE, "gate_params": g,
           "in_sample_replay": G.evaluate(held, W)}
    cv = json.loads((OUT / "gate_comparison.json").read_text())
    res["held_out_cv"] = cv["gates"][GATE]
    (OUT / "development_replay.json").write_text(json.dumps(res, indent=1, default=str))
    e = res["in_sample_replay"]
    print("REPLAY (in-sample, descriptive):")
    print(f"  support ungated   {e['all']['t_support']}/{e['all']['n']}")
    print(f"  support e2e       {e['all']['t_support_gated']}/{e['all']['n']}")
    print(f"  family            {e['all']['t_family']}/{e['all']['n']}")
    print(f"  G1B family        {e['G1B']['t_family']}/{e['G1B']['n']}")
    print(f"  G1C family        {e['G1C']['t_family']}/{e['G1C']['n']}")
    print(f"  null FPR          {e['false_positive_rate']:.4f}")
    print(f"  balanced accuracy {e['balanced_accuracy']:.4f}")
    print(f"  ROC AUC           {e['roc_auc']:.4f}")
    print("  gate params", {k: g[k] for k in ('t1', 't2')})


if __name__ == "__main__":
    main()
