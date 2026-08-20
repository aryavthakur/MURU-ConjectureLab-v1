"""Stage 4: targeted re-derivation of the family-adjudication reasons for the
remaining failures, and the representability floor for the search failures."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
import numpy as np
for _v in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[_v]="1"
WT = Path(__file__).resolve().parents[1]
MAIN = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1")
sys.path.insert(0, str(WT/"src")); sys.path.insert(0, str(WT/"scripts"))
OUT = WT/"artifacts"/"accopt"

import accopt_selectors as S
from muru.discovery import grammar, protocol
from muru.objval import equiv, recovery as recmod, select as selmod, signature
from muru.synth.generators import load_dev_covariates

cov = load_dev_covariates()
variables = list(protocol.FEATURES)
Xreal = np.column_stack([cov[c].to_numpy(float)/protocol.SCALE[c] for c in variables])
Xsynth = np.random.default_rng(0).uniform(0.2,1.8,size=(len(Xreal),len(variables)))
Zreal = selmod.lattice(Xreal, variables); Zsynth = selmod.lattice(Xsynth, variables)
truth = {w["world_id"]: w for w in json.loads(
    (MAIN/"artifacts"/"ov_truth_manifest.json").read_text())["worlds"]}

res = json.loads((OUT/"run_result.json").read_text())
held = json.loads((OUT/"held_out_selections.json").read_text())
cache = {w["world_id"]: w for w in S.load()}

diag = []
for f in res["failure_rows"]:
    wid = f["world_id"]; w = cache[wid]
    Z = Zsynth if w["family"]=="G1A" else Zreal
    tr = truth[wid]
    params = recmod.freeze_constants(tr["family"], tr["params"], variables, Z)
    psig = recmod.planted_signature(tr["family"], params, variables, Z)
    ev,_ = recmod.planted_evaluator(tr["family"], params, variables)
    pv, pok = ev(Z)
    rep = held[wid]["rep"]
    m = w["members"][rep]
    e = grammar.parse(m["expr"], variables)
    rsig = signature.signature(e, variables, Z)
    rv, rok = signature._eval(e, variables, Z)
    sf = equiv.same_family(rsig, psig, rv, pv, pok & rok)
    # representability floor: best functional rel_rmse over every band member
    best = min((mm.get("t_rel_rmse", np.inf) for mm in w["members"]
                if mm.get("t_rel_rmse") is not None
                and np.isfinite(mm.get("t_rel_rmse", np.nan))), default=float("nan"))
    n_fam = sum(1 for mm in w["members"] if mm.get("t_family"))
    reasons = sf["reasons"]
    only_numeric = bool(reasons) and all(r.startswith("predictions disagree") for r in reasons)
    only_struct = bool(reasons) and not any(r.startswith("predictions disagree") for r in reasons)
    diag.append({"world_id": wid, "code": f["code"], "block": w["block"],
                 "reasons": reasons, "rel_rmse": sf["numeric"]["rel_rmse"],
                 "r": sf["numeric"]["r"],
                 "rejection_is_numeric_only": only_numeric,
                 "rejection_is_structural_only": only_struct,
                 "best_member_rel_rmse_vs_truth": float(best),
                 "n_family_correct_members": n_fam,
                 "n_members": len(w["members"])})
    print(f"{f['code']:45s} {wid:26s} rel_rmse={sf['numeric']['rel_rmse']:.4f} "
          f"r={sf['numeric']['r']:.5f} floor={best:.4f} nfam={n_fam}")
    for r in reasons: print("      -", r)
(OUT/"failure_diagnosis.json").write_text(json.dumps(diag, indent=1, default=str))
