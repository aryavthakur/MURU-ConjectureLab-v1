"""External step 3: THE ONE LOOK at MultiMS2 validation (and secondary) spectra under the VALIDATION guard."""
import json, subprocess
from pathlib import Path
import pandas as pd
from muru.wur_v2 import external_multims2 as E
from muru.wur_v2.external_guard import AccessGuard
ROOT = Path(__file__).resolve().parents[2]; OUT = E.OUT
FREEZE = ROOT / "MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md"
if (OUT / "validation_result.json").exists():
    raise SystemExit("validation_result.json exists: MultiMS2 validation was already accessed once")
cal = json.loads((OUT / "anchor_calibration.json").read_text())
if not cal.get("qualified"):
    raise SystemExit("anchor calibration did not qualify MultiMS2; validation spectra must not be decoded")
if "PART II" not in FREEZE.read_text():
    raise SystemExit("freeze document lacks Part II (fitted adapter); not authorized")
P = json.loads((OUT / "populations.json").read_text())
allowed = {tuple(x) for x in P["allowed_spectra"]["VALIDATION"]} | {tuple(x) for x in P["allowed_spectra"]["SECONDARY"]}
guard = AccessGuard("VALIDATION", OUT / "validation_access.json", FREEZE, allowed)          # first-access record written here
models = E.load_models()
adapter = cal["adapter"]
res = {"access": guard.record, "adapter": adapter}
for name in ("VALIDATION", "SECONDARY"):
    pop = pd.DataFrame(P["populations"][name]); sp = pd.DataFrame(P["spectra"][name])
    mu, info = E.measured_mu(sp, pop, guard)
    mu.to_csv(OUT / f"measured_mu_{name}.csv", index=False)
    scored = E.score_population(mu, pop, adapter, models)
    scored["decode_info"] = info
    if name == "VALIDATION":
        lo, hi = adapter["k_bootstrap_2.5_97.5"]
        scored["adapter_sensitivity"] = {}
        for label, k in (("k_lower", lo), ("k_upper", hi)):
            s2 = E.score_population(mu, pop, {**adapter, "k": k}, models, boot=False)
            scored["adapter_sensitivity"][label] = {"k": k, "P1_candidate": s2["models"]["CANDIDATE"]["P1"], "P1_ta": s2["models"]["TA_RIDGE"]["P1"],
                                                    "ratio": s2["models"]["CANDIDATE"]["P1"] / s2["models"]["TA_RIDGE"]["P1"], "n_scored": s2["n_scored"]}
        res["decision"] = E.decide(scored)
    res[name] = scored
res["git_head_at_end"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
(OUT / "validation_result.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
print(json.dumps(res["decision"], indent=1, default=float))
