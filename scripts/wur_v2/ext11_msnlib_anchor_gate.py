"""MSnLib anchors-first gate: allowlisted headers of anchor wells, section 2 rules, guarded anchor decode, adapter gate."""
import json, time
from pathlib import Path
import numpy as np, pandas as pd
from muru.io.wur_provenance import canonical_key_hash
from muru.wur_v2 import external_mzml as X, external_msnlib as L, external_multims2 as MM
from muru.wur_v2.external_guard import AccessGuard
ROOT = Path(__file__).resolve().parents[2]; OUT = L.OUT
FREEZE = ROOT / "MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md"
wells = pd.read_csv(OUT / "anchor_wells.csv")
wells = wells[[ (L.DL / f).exists() for f in wells.fn ]]
headers = {}
for fn in sorted(wells.fn.unique()):
    headers[fn] = L.fixed_rung_scans(pd.DataFrame(X.scan_headers(L.DL / fn)))
matched = L.match_compounds(wells, headers)
elig = L.eligible(matched)
matched = matched[matched.key.isin(elig) & matched.window_ok]
pop = wells[wells.key.isin(elig)].drop_duplicates("key")
v2 = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv").set_index("group_key")
pop = pop.assign(scaffold_group=v2.loc[pop.key, "scaffold_group"].to_numpy())
summary = {"anchor_keys_in_census": int(wells.key.nunique()), "wells_downloaded": int(wells.unique_sample_id.nunique()),
           "anchors_with_both_fixed_rungs": len(elig), "anchor_keys_sha256": canonical_key_hash(sorted(elig)),
           "n_matched_scans": int(len(matched)), "rung_scan_counts": matched.energy.value_counts().to_dict()}
(OUT / "anchor_headers_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps(summary, indent=1))
allowed = set(zip(matched.file, matched.spectrum_id))
guard = AccessGuard("ANCHOR_CALIBRATION", OUT / "anchor_calibration_access.json", FREEZE, allowed)
mu, info = L.measured_mu(matched, pop, guard)
mu.to_csv(OUT / "anchor_mu.csv", index=False)
model = MM.load_models()["CANDIDATE"]
res = L.fit_and_gate(mu, model)
out = {"access": guard.record, "decode_info": info, "header_summary": summary,
       **{f: res[f] for f in ("A0", "A1", "A2") if f in res}, "qualified": res["qualified"]}
if res["qualified"]:
    out["adapter"] = res["adapter"]; res["cells"].to_csv(OUT / "anchor_cells.csv", index=False)
    fam = res["adapter"]["family"]
    if fam != "A0":
        rng = np.random.default_rng(20261012); groups = pop.set_index("key").scaffold_group; ug = groups.unique()
        by_g = {g: mu[mu.key.isin(groups.index[groups == g])] for g in ug}; boots = []
        for b in range(2000):
            sub = pd.concat([by_g[g] for g in rng.choice(ug, size=len(ug), replace=True)], ignore_index=True)
            rb = L.fit_and_gate(sub, model)
            boots.append(rb.get(fam, {}).get("params", {}))
        out["adapter_bootstrap"] = {k: np.percentile([b[k] for b in boots if k in b], [2.5, 97.5]).tolist() for k in res["adapter"] if k != "family"}
# model-free diagnostic: best rank agreement with exposed rungs
W = mu.pivot(index="key", columns="energy", values="mu")
long = pd.read_csv(ROOT / "artifacts/wur_v2/data/long_aligned.csv").pivot(index="group_key", columns="ce_numeric", values="mu").loc[W.index]
from scipy.stats import spearmanr
out["spearman_vs_exposed_rungs"] = {f"NCE{int(e)}_vs_LCSB{int(r)}": float(spearmanr(W[e], long[r], nan_policy="omit").statistic) for e in W.columns for r in long.columns}
(OUT / "anchor_calibration.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(json.dumps({k: v for k, v in out.items() if k not in ("access",)}, indent=1, default=float))
