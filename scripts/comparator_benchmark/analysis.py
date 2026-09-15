"""Benchmark step 2 (NOT RUN during protocol construction): the single frozen analysis.

Refuses to run unless (a) the preregistration freeze ref exists, (b) competitor predictions were committed with a
matching prediction manifest, and (c) MURU_COMPARATOR_ONE_LOOK=1 is set. Only then does it read the PR #7 measured
mu table. Statistics reuse muru.wur_v2.metrics unchanged.

Primary: on the identical compounds of the frozen common population (minus compounds for which any surviving primary
comparator produced no finite mu at either rung, counted), P1 of MURU and of each comparator; ratio = P1_MURU /
P1_comparator (< 1 favours MURU); whole-scaffold-group bootstrap, B = 10,000, seed 20260915, the identical replicate
weight matrix for every comparator (metrics.cluster_bootstrap draws W from (seed, number of groups) only).
Decision per comparator on the Bonferroni interval at level 1 - 0.05/k (k = surviving primary comparators; 98.33%
for k = 3): upper < 1 -> MURU_SUPERIOR; lower > 1 -> COMPARATOR_SUPERIOR; else NO_DEMONSTRATED_DIFFERENCE.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import candidate as CA   # noqa: E402
from muru.wur_v2 import metrics as M      # noqa: E402

PREREG_ID = "muru-v2-comparator-benchmark-1.0"
FREEZE_REF = f"refs/muru-freeze/{PREREG_ID}"
BOOT_B, BOOT_SEED, ALPHA = 10_000, 20260915, 0.05
NCE_RUNGS = (20.0, 60.0)
A0 = (-5.95552603907965, 0.8618030610784555)
PRIMARY = [("FIORA-OS v0.1.0", "native_nce"), ("ICEBERG 2.1", "ev_primary"), ("GLACIER", "ev_primary")]
SENSITIVITY = [("ICEBERG 2.1", "raw_nce_sensitivity"), ("GLACIER", "raw_nce_sensitivity")]
PRACTICAL = 0.95   # descriptor only: ratio <= 0.95 or >= 1/0.95


def decide(ci_adj: list[float]) -> str:
    if ci_adj[1] < 1.0:
        return "MURU_SUPERIOR"
    if ci_adj[0] > 1.0:
        return "COMPARATOR_SUPERIOR"
    return "NO_DEMONSTRATED_DIFFERENCE"


def practical(ratio: float) -> str:
    if ratio <= PRACTICAL:
        return "ratio <= 0.95 (practically meaningful MURU advantage)"
    if ratio >= 1.0 / PRACTICAL:
        return "ratio >= 1/0.95 (practically meaningful comparator advantage)"
    return "0.95 < ratio < 1/0.95 (within the practical-equivalence band)"


def primary_contrasts(pred_muru: np.ndarray, preds: dict[str, np.ndarray], Y: np.ndarray, groups,
                      n: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    k = len(preds)
    level_adj = 1.0 - ALPHA / k if k > 1 else 1.0 - ALPHA
    out = {}
    for name, pc in preds.items():
        b95 = M.cluster_bootstrap(pred_muru, pc, Y, groups, n=n, seed=seed, level=0.95)
        badj = M.cluster_bootstrap(pred_muru, pc, Y, groups, n=n, seed=seed, level=level_adj)
        out[name] = {"P1_MURU": b95["P1_cand"], "P1_comparator": b95["P1_ref"], "ratio": b95["P1_ratio"],
                     "diff": b95["P1_diff"], "ratio_ci95": b95["P1_ratio_ci"], "diff_ci95": b95["P1_diff_ci"],
                     "ratio_ci_adjusted": badj["P1_ratio_ci"], "adjusted_level": level_adj, "k": k,
                     "decision": decide(badj["P1_ratio_ci"]), "practical_descriptor": practical(b95["P1_ratio"]),
                     "MRMSE_diff_ci95": b95["MRMSE_diff_ci"], "AF_diff_ci95": b95["AF_diff_ci"],
                     "n_clusters": b95["n_clusters"], "n_boot": n, "seed": seed}
    return out


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if os.environ.get("MURU_COMPARATOR_ONE_LOOK") != "1":
        raise SystemExit("refusing: set MURU_COMPARATOR_ONE_LOOK=1 only for the single frozen analysis")
    if subprocess.run(["git", "rev-parse", "--verify", FREEZE_REF], cwd=ROOT, capture_output=True).returncode != 0:
        raise SystemExit(f"refusing: {FREEZE_REF} missing")
    pred_dir = ROOT / "artifacts/comparator_benchmark/predictions"
    man = json.loads((pred_dir / "prediction_manifest.json").read_text())
    for fname, h in man["files"].items():
        assert _sha(pred_dir / fname) == h, fname
    if subprocess.run(["git", "ls-files", "--error-unmatch", str(pred_dir / "prediction_manifest.json")],
                      cwd=ROOT, capture_output=True).returncode != 0:
        raise SystemExit("refusing: predictions are not committed")

    pop = pd.read_csv(ROOT / "artifacts/comparator_benchmark/population/common_population.csv")
    frozen = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv").set_index("key")
    comp = pd.read_csv(pred_dir / "competitor_mu.csv")
    # --- the one look at outcomes starts here ---
    mu = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/result/measured_mu.csv")
    W = mu.pivot(index="key", columns="energy", values="mu").reindex(index=pop.key, columns=list(NCE_RUNGS))

    def table(model, cond):
        t = comp[(comp.model == model) & (comp.condition == cond)]
        return t.pivot(index="key", columns="nce", values="mu").reindex(index=pop.key, columns=[20, 60]).to_numpy()

    prim = {m: table(m, c) for m, c in PRIMARY}
    ok_pred = np.all([np.isfinite(v).all(1) for v in prim.values()], axis=0)
    ok_meas = np.isfinite(W.to_numpy()).all(1)
    keep = ok_pred & ok_meas
    p = frozen.loc[pop.key]
    E = (np.array(NCE_RUNGS) - A0[0]) / A0[1]
    cand = json.loads((ROOT / "artifacts/wur_v2/candidate/V2_TA_MORGAN_JOINT.json").read_text())
    pred_muru = CA.predict_mu(cand, p.smiles, p.mh, E)
    Y = W.to_numpy()[keep]
    groups = pop.scaffold_group.to_numpy()[keep]
    nov = pd.read_csv(ROOT / "artifacts/wur_v2_confirmation_v2/freeze/novelty_bins_per_compound.csv").set_index("key")
    bins = nov.loc[pop.key[keep], "novelty_bin"].to_numpy()

    res = {"prereg_id": PREREG_ID, "n_population": int(len(pop)),
           "n_excluded_prediction_failure": int((~ok_pred).sum()), "n_excluded_measurement_incomplete": int((~ok_meas).sum()),
           "n_scored": int(keep.sum()), "n_scaffold_groups_scored": int(len(set(groups)))}
    res["primary"] = primary_contrasts(pred_muru[keep], {m: v[keep] for m, v in prim.items()}, Y, groups)
    res["summaries"] = {"MURU-WUR-v2": M.summary(pred_muru[keep], Y), **{m: M.summary(v[keep], Y) for m, v in prim.items()}}
    res["secondary_per_rung"] = {"MURU-WUR-v2": M.per_rung(pred_muru[keep], Y, NCE_RUNGS),
                                 **{m: M.per_rung(v[keep], Y, NCE_RUNGS) for m, v in prim.items()}}
    res["secondary_per_rung_signed_bias"] = {
        name: {str(e): float(np.nanmean(M.errors(v, Y)[:, j])) for j, e in enumerate(NCE_RUNGS)}
        for name, v in {"MURU-WUR-v2": pred_muru[keep], **{m: x[keep] for m, x in prim.items()}}.items()}
    res["secondary_novelty"] = {}
    for b in sorted(set(bins)):
        s = bins == b
        res["secondary_novelty"][b] = {"n": int(s.sum()), "P1": {"MURU-WUR-v2": M.p1(M.errors(pred_muru[keep][s], Y[s])),
                                        **{m: M.p1(M.errors(v[keep][s], Y[s])) for m, v in prim.items()}}}
    res["sensitivity_raw_nce_descriptive_only"] = {}
    for m, c in SENSITIVITY:
        v = table(m, c)[keep]
        fin = np.isfinite(v).all(1)
        b = M.cluster_bootstrap(pred_muru[keep][fin], v[fin], Y[fin], groups[fin], n=BOOT_B, seed=BOOT_SEED, level=0.95)
        res["sensitivity_raw_nce_descriptive_only"][m] = {"n": int(fin.sum()), "P1_comparator": b["P1_ref"],
                                                          "ratio": b["P1_ratio"], "ratio_ci95": b["P1_ratio_ci"],
                                                          "note": "diagnostic only; never affects ranking, inclusion or conclusions"}
    out = ROOT / "artifacts/comparator_benchmark/result/analysis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res["primary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
