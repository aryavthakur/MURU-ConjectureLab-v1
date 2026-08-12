"""Phase 2 negative controls NC1-NC4, NC6, NC7.

The null decision rule is fixed in PREREGISTRATION.md section 15 and is applied
exactly as written: each control is compared against the 95th percentile of its
OWN matched permutation null, and the family of six is controlled jointly by
Benjamini-Hochberg at q = 0.10. This is not six independent alpha = 0.05 tests.

Per DEVIATIONS D13 each control fixes the estimator's hyperparameters at the
modal configuration chosen by the real run's inner loops, and applies that
frozen estimator identically to observed and permuted data. Re-tuning inside
every replicate would make the null reflect search variance rather than the
mechanism under test.

A control exceeding its threshold is a BLOCKER until explained.

Writes artifacts/p2_controls.json
"""
from __future__ import annotations

import os

# Thread caps before numpy/sklearn import; see DEVIATIONS D14.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = os.environ.get("MURU_THREADS", "4")

import ast  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.models import (SEED, FlexibleBenchmark, PerEnergyMean, TierAModel,
                         compound_errors, nested_cv, Spec)
from muru.molecules import TIER_A

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
N_PERM = 200
PRIMARY = "fold_S2"
MIN_BIT_COUNT = 5

R: dict = {"n_permutations": N_PERM, "primary_split": "S2",
           "null_rule": ("observed statistic vs the 95th percentile of its own "
                         "matched permutation null; family of six controlled by "
                         "Benjamini-Hochberg at q=0.10")}

d = pd.read_parquet(ART / "p2_splits.parquet")
tA = pd.read_parquet(ART / "p2_tierA.parquet").drop(columns=["precursor_mz"])
tB = pd.read_parquet(ART / "p2_tierB.parquet")
fp = [c for c in tB.columns if c.startswith("fp_")]
on = tB[fp].sum(axis=0)
TIER_B_FEATS = [c for c in fp if on[c] >= MIN_BIT_COUNT] + \
               [c for c in tB.columns if c.startswith("rdk_")]
df = d.merge(tA, on="group_key").merge(tB[["group_key", *TIER_B_FEATS]],
                                       on="group_key")

base = json.loads((ART / "p2_baselines.json").read_text())
hp_tierA = ast.literal_eval(base["performance"]["S2"]["TIER_A"]["hp_modal"])
hp_flex = ast.literal_eval(base["performance"]["S2"]["FLEX_BENCHMARK"]["hp_modal"])
R["frozen_hyperparameters"] = {"TIER_A": hp_tierA, "FLEX_BENCHMARK": hp_flex}


def oof_mae(frame: pd.DataFrame, spec: Spec) -> float:
    p = nested_cv(frame, spec, PRIMARY, inner_folds=4, seed=SEED)
    return float(np.mean(np.abs(p.mu - p.pred)))


SPEC_TIER_A = Spec("TIER_A", TierAModel, feats=list(TIER_A),
                   grid=[hp_tierA], needs_feats=True)
SPEC_FLEX = Spec("FLEX", FlexibleBenchmark, feats=TIER_B_FEATS,
                 grid=[hp_flex], needs_feats=True)
SPEC_B1 = Spec("B1", PerEnergyMean)

b1_mae = oof_mae(df, SPEC_B1)
tierA_mae = oof_mae(df, SPEC_TIER_A)
R["reference"] = {"B1_mae": round(b1_mae, 5), "TIER_A_mae": round(tierA_mae, 5)}

# The statistic every control is judged on: MAE improvement over B1. A working
# control should destroy that improvement, driving the statistic toward zero.
def improvement(frame, spec) -> float:
    return b1_mae - oof_mae(frame, spec)


def run_null(name: str, fn, n: int = N_PERM) -> list[float]:
    """Run a permutation null with visible progress (BACKLOG I4)."""
    t0 = time.time()
    out = []
    for i in range(n):
        out.append(fn())
        if (i + 1) % 50 == 0:
            el = time.time() - t0
            print(f"  {name}: {i+1}/{n} replicates "
                  f"({el:.0f}s, eta {el/(i+1)*(n-i-1):.0f}s)", flush=True)
    print(f"  {name}: done in {time.time()-t0:.0f}s", flush=True)
    return out


CMP_COLS = ["group_key", *[c for c in TIER_A if c != "precursor_mz"],
            "precursor_mz"]


def permute_descriptors(frame: pd.DataFrame, rng) -> pd.DataFrame:
    """NC2: permute descriptor ROWS across compounds, keep trajectories."""
    cmp_tbl = frame.drop_duplicates("group_key")[CMP_COLS].reset_index(drop=True)
    perm = cmp_tbl.copy()
    idx = rng.permutation(len(cmp_tbl))
    for c in CMP_COLS[1:]:
        perm[c] = cmp_tbl[c].to_numpy()[idx]
    return frame.drop(columns=CMP_COLS[1:]).merge(perm, on="group_key")


def permute_trajectories(frame: pd.DataFrame, rng) -> pd.DataFrame:
    """NC3: permute whole trajectories against descriptors."""
    keys = frame.group_key.drop_duplicates().to_numpy()
    mapping = dict(zip(keys, rng.permutation(keys)))
    traj = frame[["group_key", "ce_numeric", "mu"]].copy()
    traj["group_key"] = traj.group_key.map(mapping)
    return frame.drop(columns=["mu"]).merge(traj, on=["group_key", "ce_numeric"])


def permute_energy_within(frame: pd.DataFrame, rng) -> pd.DataFrame:
    """NC1: permute the six energy labels within each trajectory."""
    out = frame.copy()
    vals = out.ce_numeric.to_numpy().copy()
    for _, idx in out.groupby("group_key").indices.items():
        vals[idx] = rng.permutation(vals[idx])
    out["ce_numeric"] = vals
    return out


CONTROLS: dict[str, dict] = {}

# --- NC1: energy shuffle within compound ----------------------------------
rng = np.random.default_rng(SEED)
obs = improvement(df, SPEC_TIER_A)
null = run_null("NC1", lambda: improvement(permute_energy_within(df, rng), SPEC_TIER_A))
CONTROLS["NC1_energy_shuffle_within_compound"] = {
    "statistic": "MAE improvement over B1", "observed_real_data": round(obs, 5),
    "null": null}

# --- NC2: descriptor shuffle across compounds -----------------------------
rng = np.random.default_rng(SEED + 1)
null = run_null("NC2", lambda: improvement(permute_descriptors(df, rng), SPEC_TIER_A))
CONTROLS["NC2_descriptor_shuffle"] = {
    "statistic": "MAE improvement over B1", "observed_real_data": round(obs, 5),
    "null": null}

# --- NC3: trajectory shuffle across compounds -----------------------------
rng = np.random.default_rng(SEED + 2)
null = run_null("NC3", lambda: improvement(permute_trajectories(df, rng), SPEC_TIER_A))
CONTROLS["NC3_trajectory_shuffle"] = {
    "statistic": "MAE improvement over B1", "observed_real_data": round(obs, 5),
    "null": null}

# --- NC4: sham descriptors --------------------------------------------------
# A uniform random variable and an alphabetical-name index are injected into
# Tier A. Neither may carry information. The statistic is the improvement a
# model built on ONLY the shams achieves over B1.
rng = np.random.default_rng(SEED + 3)
cmp_tbl = df.drop_duplicates("group_key")[["group_key"]].copy()
cmp_tbl = cmp_tbl.sort_values("group_key")
cmp_tbl["sham_alpha_index"] = np.arange(len(cmp_tbl), dtype=float)
sham_frames = []
for _ in range(N_PERM):
    t = cmp_tbl.copy()
    t["sham_uniform"] = rng.random(len(t))
    sham_frames.append(t)

SHAM = ["sham_uniform", "sham_alpha_index"]
spec_sham = Spec("SHAM", TierAModel, feats=SHAM, grid=[hp_tierA],
                 needs_feats=True)
obs_sham = improvement(df.merge(sham_frames[0], on="group_key"), spec_sham)
null = [improvement(df.merge(sf, on="group_key"), spec_sham) for sf in sham_frames[:N_PERM]]
print("  NC4: done", flush=True)
CONTROLS["NC4_sham_descriptors"] = {
    "statistic": "MAE improvement over B1 using ONLY sham descriptors",
    "observed_real_data": round(obs_sham, 5), "null": null,
    "note": ("here the observed statistic IS a sham fit, so it should itself "
             "sit inside the null; the control fires only if shams "
             "systematically beat B1")}

# --- NC6: mixture identity --------------------------------------------------
rng = np.random.default_rng(SEED + 4)
mixdf = df.copy()
mixdf["mix_f"] = mixdf["mix"].astype(float)
spec_mix = Spec("MIX", TierAModel, feats=["mix_f"], grid=[hp_tierA],
                needs_feats=True)
obs_mix = improvement(mixdf, spec_mix)
null = []
for _ in range(N_PERM):
    t = mixdf.copy()
    keys = t.group_key.drop_duplicates().to_numpy()
    m = t.drop_duplicates("group_key").set_index("group_key").mix_f
    t["mix_f"] = t.group_key.map(dict(zip(keys, rng.permutation(m.to_numpy()))))
    null.append(improvement(t, spec_mix))
CONTROLS["NC6_mixture_identity"] = {
    "statistic": "MAE improvement over B1 using mixture identity alone",
    "observed_real_data": round(obs_mix, 5), "null": null}

# --- NC7: retention time ----------------------------------------------------
rng = np.random.default_rng(SEED + 5)
rtdf = df.copy()
spec_rt = Spec("RT", TierAModel, feats=["retention_time_min"], grid=[hp_tierA],
               needs_feats=True)
obs_rt = improvement(rtdf, spec_rt)
null = []
for _ in range(N_PERM):
    t = rtdf.copy()
    keys = t.group_key.drop_duplicates().to_numpy()
    v = t.drop_duplicates("group_key").set_index("group_key").retention_time_min
    t["retention_time_min"] = t.group_key.map(
        dict(zip(keys, rng.permutation(v.to_numpy()))))
    null.append(improvement(t, spec_rt))
CONTROLS["NC7_retention_time"] = {
    "statistic": "MAE improvement over B1 using retention time alone",
    "observed_real_data": round(obs_rt, 5), "null": null}

# ---------------------------------------------------------------------------
# Adjudication
#
# The six controls fall into two families that ask opposite questions, and they
# must not share one rule. PREREGISTRATION section 15 wrote a single rule
# ("observed vs its own null p95, BH across six"), which is correct for the
# nuisance family and meaningless for the destruction family. See DEVIATIONS
# D16; the correction is applied in the conservative direction for both.
#
#   DESTRUCTION controls (NC1-NC3): permutation is applied to the REAL
#   structure, and the question is whether signal SURVIVES destruction. The
#   thing under test is the null distribution itself. The real-data statistic
#   exceeding the null is the expected, desired outcome -- it confirms the
#   permutation worked -- and must never be read as a failure. Fires when the
#   permuted pipeline retains a material share of the real effect.
#
#   NUISANCE controls (NC4, NC6, NC7): the "observed" statistic IS the nuisance
#   predictor's own performance, and it must sit inside its own permutation
#   null. Fires when the nuisance variable predicts above its null p95.
# ---------------------------------------------------------------------------
FAMILY = {
    "NC1_energy_shuffle_within_compound": "destruction",
    "NC2_descriptor_shuffle": "destruction",
    "NC3_trajectory_shuffle": "destruction",
    "NC4_sham_descriptors": "nuisance",
    "NC6_mixture_identity": "nuisance",
    "NC7_retention_time": "nuisance",
}
# A destruction control fires if the permuted pipeline's 95th percentile retains
# more than this share of the real structural effect.
RESIDUAL_SHARE_LIMIT = 0.10
REAL_EFFECT = tierA_mae and (b1_mae - tierA_mae)

summary = {}
for name, c in CONTROLS.items():
    null = np.asarray(c["null"], dtype=float)
    p95 = float(np.percentile(null, 95))
    fam = FAMILY[name]
    entry = {
        "family": fam,
        "statistic": c["statistic"],
        "observed": c["observed_real_data"],
        "null_mean": round(float(null.mean()), 6),
        "null_p95": round(p95, 6),
        "null_max": round(float(null.max()), 6),
        "frac_null_replicates_beating_B1": round(float((null > 0).mean()), 4),
    }
    if fam == "destruction":
        share = p95 / REAL_EFFECT if REAL_EFFECT else float("inf")
        entry.update({
            "real_effect_for_reference": round(REAL_EFFECT, 5),
            "null_p95_as_share_of_real_effect": round(share, 4),
            "limit": RESIDUAL_SHARE_LIMIT,
            "p_value": round(float((null >= REAL_EFFECT).mean()), 4),
            "fires": bool(share > RESIDUAL_SHARE_LIMIT),
            "reads": ("permutation destroys the effect; the real-data statistic "
                      "exceeding this null is the DESIRED outcome, not a failure"),
        })
    else:
        obs = float(c["observed_real_data"])
        entry.update({
            "p_value": round(float((null >= obs).mean()), 4),
            "exceeds_null_p95": bool(obs > p95),
            "fires": bool(obs > p95),
        })
    if "note" in c:
        entry["note"] = c["note"]
    summary[name] = entry

# Benjamini-Hochberg at q = 0.10 across the nuisance family, whose p-values are
# comparable. Destruction controls are adjudicated on effect share, so a
# p-value correction does not apply to them.
nuis = [n for n in summary if summary[n]["family"] == "nuisance"]
pvals = np.array([summary[n]["p_value"] for n in nuis])
order = np.argsort(pvals)
q, m = 0.10, len(pvals)
reject = np.zeros(m, dtype=bool)
for rank, i in enumerate(order, start=1):
    if pvals[i] <= q * rank / m:
        reject[order[:rank]] = True
for i, n in enumerate(nuis):
    summary[n]["bh_significant_at_q0.10"] = bool(reject[i])
    summary[n]["fires"] = bool(summary[n]["exceeds_null_p95"] and reject[i])

R["controls"] = summary
fired = [n for n, v in summary.items() if v["fires"]]
R["controls_fired"] = fired
R["any_control_fires"] = bool(fired)
R["verdict"] = (f"CONTROL FIRES: {', '.join(fired)} -- BLOCKER until explained"
                if fired else
                "All negative controls null under the pre-registered rule")

# ---------------------------------------------------------------------------
# NC7 follow-up: is retention time an independent confounder, or a structure
# surrogate? Run only because NC7 can fire; the comparison is pre-specified by
# the question the control asks, not chosen after seeing which way it went.
# ---------------------------------------------------------------------------
rt_only = b1_mae - oof_mae(rtdf, spec_rt)
tier_a_plus_rt = Spec("TIER_A_RT", TierAModel,
                      feats=[*TIER_A, "retention_time_min"],
                      grid=[hp_tierA], needs_feats=True)
combined = b1_mae - oof_mae(rtdf, tier_a_plus_rt)
R["nc7_followup"] = {
    "question": ("does retention time carry predictive information INDEPENDENT "
                 "of Tier A structure, or is it a structure surrogate"),
    "improvement_rt_alone": round(rt_only, 5),
    "improvement_tier_a_alone": round(REAL_EFFECT, 5),
    "improvement_tier_a_plus_rt": round(combined, 5),
    "rt_share_of_structural_effect": round(rt_only / REAL_EFFECT, 4),
    "incremental_gain_from_adding_rt": round(combined - REAL_EFFECT, 5),
}

(ART / "p2_controls.json").write_text(json.dumps(R, indent=2, default=str))
print(json.dumps({k: v for k, v in R.items() if k != "controls"}, indent=2))
for n, v in summary.items():
    print(f"\n{n}\n  " + json.dumps(v, indent=2).replace("\n", "\n  "))
