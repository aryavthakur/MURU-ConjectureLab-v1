"""Phase 2 baseline ladder, K4A, K4B, and the K5 ablations.

Executes the models frozen in PREREGISTRATION.md under S1, S2 (primary) and S3,
with nested grouped cross-validation, and evaluates the pre-registered kill
criteria. S0 is run as the leakage canary only.

Writes artifacts/p2_predictions.parquet and artifacts/p2_baselines.json
"""
from __future__ import annotations

import os

# --- Execution configuration (implementation only; see DEVIATIONS D14) -------
# Thread caps must be set BEFORE numpy / sklearn import to take effect. Left
# uncapped, sklearn's OpenMP pool sizes itself to the core count and, under
# external load on an 8-core machine, spends most of its cycles in barrier
# spin-waits: a mid-run sample of the first attempt showed 22 productive stack
# frames against 234 in wait primitives. Four threads matches the four
# performance cores.
#
# Verified inert: `scripts/t2_05a_runtime_budget.py` fits the most expensive
# grid point at 1, 2 and 4 threads and the predictions are BITWISE IDENTICAL,
# so this changes cost and nothing else.
THREADS = os.environ.get("MURU_THREADS", "4")
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = THREADS

import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from muru.models import (FlexibleBenchmark, GlobalMean, MassFlex,  # noqa: E402
                         MassSimple, PerEnergyMean, Spec, TierAModel,
                         bootstrap_metric, bootstrap_paired, compound_errors,
                         grouped_r2, nested_cv)
from muru.molecules import MASS_BLOCK, TIER_A  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
CKPT = ART / "p2_ckpt"
CKPT.mkdir(exist_ok=True)
SEED = 20260811
N_BOOT = 2000
MIN_BIT_COUNT = 5          # DEVIATIONS D12, response-blind
RIDGE_GRID = [1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0]

R: dict = {}

# ---------------------------------------------------------------------------
# Assemble the development frame
# ---------------------------------------------------------------------------
d = pd.read_parquet(ART / "p2_splits.parquet")
tA = pd.read_parquet(ART / "p2_tierA.parquet")
tB = pd.read_parquet(ART / "p2_tierB.parquet")

fp_cols = [c for c in tB.columns if c.startswith("fp_")]
on = tB[fp_cols].sum(axis=0)
keep_fp = [c for c in fp_cols if on[c] >= MIN_BIT_COUNT]
rdk_cols = [c for c in tB.columns if c.startswith("rdk_")]
TIER_B_FEATS = keep_fp + rdk_cols

# precursor_mz is present in both frames and is the same record value; keep the
# split frame's copy so the join cannot introduce an _x/_y ambiguity.
tA_join = tA.drop(columns=["precursor_mz"])
df = d.merge(tA_join, on="group_key").merge(
    tB[["group_key", *TIER_B_FEATS]], on="group_key")
assert len(df) == len(d), "descriptor join changed row count"
assert "precursor_mz" in df.columns and not any(
    c.endswith(("_x", "_y")) for c in df.columns), "ambiguous join columns"

R["setup"] = {
    "development_rows": int(len(df)),
    "development_compounds": int(df.inchikey_first_block.nunique()),
    "tier_a_n": len(TIER_A),
    "tier_b_n": len(TIER_B_FEATS),
    "tier_b_fp_bits_kept": len(keep_fp),
    "tier_b_min_bit_count": MIN_BIT_COUNT,
    "primary_split": "S2",
    "n_boot": N_BOOT,
}

TIER_A_NO_MASS = [c for c in TIER_A if c not in MASS_BLOCK]
MASS_ONLY = list(MASS_BLOCK)

# Mass-carrying RDKit descriptors, for the flexible-benchmark ablation.
RDK_MASS_LIKE = [f"rdk_{n}" for n in
                 ("MolWt", "MolMR", "LabuteASA", "HeavyAtomCount",
                  "Chi0v", "Chi1v", "Chi2v", "Chi3v", "Chi4v",
                  "Kappa1", "Kappa2", "Kappa3", "BertzCT")]
TIER_B_NO_MASS = [c for c in TIER_B_FEATS if c not in RDK_MASS_LIKE]

GBM_GRID = [{"max_depth": md, "learning_rate": lr, "max_iter": mi,
             "min_samples_leaf": 20, "l2_regularization": 0.0}
            for md in (3, 6, None) for lr in (0.05, 0.1) for mi in (200, 500)]

SPECS = [
    Spec("B0_global_mean", GlobalMean),
    Spec("B1_per_energy_mean", PerEnergyMean),
    Spec("B2_MASS_SIMPLE", MassSimple),
    Spec("MASS_FLEX", MassFlex, grid=[{"alpha": a} for a in RIDGE_GRID]),
    Spec("TIER_A", TierAModel, feats=list(TIER_A),
         grid=[{"alpha": a} for a in RIDGE_GRID], needs_feats=True),
    Spec("TIER_A_no_mass", TierAModel, feats=TIER_A_NO_MASS,
         grid=[{"alpha": a} for a in RIDGE_GRID], needs_feats=True),
    Spec("TIER_A_mass_only", TierAModel, feats=MASS_ONLY,
         grid=[{"alpha": a} for a in RIDGE_GRID], needs_feats=True),
    Spec("FLEX_BENCHMARK", FlexibleBenchmark, feats=TIER_B_FEATS,
         grid=GBM_GRID, needs_feats=True),
    Spec("FLEX_BENCHMARK_no_mass", FlexibleBenchmark, feats=TIER_B_NO_MASS,
         grid=GBM_GRID, needs_feats=True),
]

# ---------------------------------------------------------------------------
# Run the ladder
# ---------------------------------------------------------------------------
def run_unit(split: str, spec: Spec, fold_col: str) -> pd.DataFrame:
    """Run one (split, model) unit, or load it from checkpoint if already done.

    Each unit is written to its own parquet as soon as it completes, so an
    interruption costs at most the unit in flight rather than the whole ladder.
    The checkpoint is keyed on split and model name only; it is deleted by hand
    if the experiment definition changes.
    """
    ck = CKPT / f"{split}__{spec.name}.parquet"
    if ck.exists():
        p = pd.read_parquet(ck)
        print(f"{split:10s} {spec.name:26s} "
              f"MAE={np.mean(np.abs(p.mu - p.pred)):.5f}  [resumed]", flush=True)
        return p
    t0 = time.time()
    p = nested_cv(df, spec, fold_col, inner_folds=4, seed=SEED)
    p["split"] = split
    p.to_parquet(ck, index=False)
    print(f"{split:10s} {spec.name:26s} "
          f"MAE={np.mean(np.abs(p.mu - p.pred)):.5f} "
          f"({time.time()-t0:.1f}s)  [{len(UNITS)} units total]", flush=True)
    return p


UNITS = ([(s, spec, f"fold_{s}") for s in ("S1", "S2", "S3") for spec in SPECS]
         + [("S0_LEAKED", spec, "fold_S0") for spec in SPECS
            if spec.name in ("B1_per_energy_mean", "MASS_FLEX", "FLEX_BENCHMARK")])

print(f"[budget] {len(UNITS)} units, threads={THREADS}, "
      f"{len(TIER_B_FEATS)} Tier B features, {len(df)} rows", flush=True)

t_start = time.time()
preds = [run_unit(*u) for u in UNITS]
print(f"[budget] all units complete in {time.time()-t_start:.1f}s", flush=True)

pred = pd.concat(preds, ignore_index=True)
keep = ["group_key", "inchikey_first_block", "scaffold_group", "cluster_group",
        "ce_numeric", "mu", "pred", "model", "split", "outer_fold", "hp", "mix"]
pred[[c for c in keep if c in pred.columns]].to_parquet(
    ART / "p2_predictions.parquet", index=False)

# ---------------------------------------------------------------------------
# Performance, with the resampling unit matched to the claim
# ---------------------------------------------------------------------------
scaf = df.drop_duplicates("inchikey_first_block").set_index(
    "inchikey_first_block").scaffold_group
clus = df.drop_duplicates("inchikey_first_block").set_index(
    "inchikey_first_block").cluster_group
UNIT = {"S1": None, "S2": scaf, "S3": clus, "S0_LEAKED": None}
UNIT_NAME = {"S1": "compound", "S2": "scaffold", "S3": "cluster",
             "S0_LEAKED": "compound"}

R["performance"] = {}
ce_cache: dict[tuple[str, str], pd.DataFrame] = {}
for split in ("S1", "S2", "S3", "S0_LEAKED"):
    R["performance"][split] = {"resampling_unit": UNIT_NAME[split]}
    for name in pred[pred.split == split].model.unique():
        p = pred[(pred.split == split) & (pred.model == name)]
        ce = compound_errors(p)
        ce_cache[(split, name)] = ce
        b_cpd = bootstrap_metric(ce, None, N_BOOT, SEED)
        b_unit = bootstrap_metric(ce, UNIT[split], N_BOOT, SEED)
        R["performance"][split][name] = {
            # Two point estimates, each paired with the interval built from the
            # same resampling unit. The compound-level mean and the
            # scaffold-level mean differ when scaffold sizes are uneven, so
            # quoting one point against the other's interval would produce a
            # CI that fails to bracket its own estimate.
            "mae": round(b_cpd["mae"], 5),
            "mae_unit": round(b_unit["mae"], 5),
            "mae_ci_compound": [round(b_cpd["mae_lo"], 5), round(b_cpd["mae_hi"], 5)],
            "mae_ci_unit": [round(b_unit["mae_lo"], 5), round(b_unit["mae_hi"], 5)],
            "rmse": round(b_cpd["rmse"], 5),
            "grouped_r2": round(grouped_r2(p), 4),
            "n_units": b_unit["n_units"],
            "hp_modal": p.hp.mode().iloc[0] if "hp" in p else None,
        }

# ---------------------------------------------------------------------------
# Paired comparisons
# ---------------------------------------------------------------------------
def paired(split, a, b, unit_level=True):
    u = UNIT[split] if unit_level else None
    return bootstrap_paired(ce_cache[(split, a)], ce_cache[(split, b)],
                            u, N_BOOT, SEED)


PAIRS = [("FLEX_BENCHMARK", "B1_per_energy_mean"),
         ("FLEX_BENCHMARK", "B2_MASS_SIMPLE"),
         ("FLEX_BENCHMARK", "MASS_FLEX"),
         ("TIER_A", "B1_per_energy_mean"),
         ("TIER_A", "B2_MASS_SIMPLE"),
         ("TIER_A", "MASS_FLEX"),
         ("MASS_FLEX", "B1_per_energy_mean"),
         ("MASS_FLEX", "B2_MASS_SIMPLE"),
         ("TIER_A_no_mass", "B1_per_energy_mean"),
         ("TIER_A_no_mass", "MASS_FLEX"),
         ("FLEX_BENCHMARK_no_mass", "B1_per_energy_mean"),
         ("FLEX_BENCHMARK_no_mass", "MASS_FLEX"),
         ("TIER_A", "TIER_A_mass_only"),
         ("FLEX_BENCHMARK", "TIER_A")]

R["paired"] = {}
for split in ("S1", "S2", "S3"):
    R["paired"][split] = {}
    for a, b in PAIRS:
        res = paired(split, a, b)
        res_c = paired(split, a, b, unit_level=False)
        R["paired"][split][f"{a}_vs_{b}"] = {
            "mae_diff": round(res["diff"], 5),
            "ci_unit": [round(res["lo"], 5), round(res["hi"], 5)],
            "ci_compound": [round(res_c["lo"], 5), round(res_c["hi"], 5)],
            "rel_reduction_pct": round(
                -100 * res["diff"] / R["performance"][split][b]["mae"], 2),
            "a_better": bool(res["diff"] < 0),
            "ci_excludes_zero_unit": bool(res["hi"] < 0 or res["lo"] > 0),
        }

# ---------------------------------------------------------------------------
# K4A / K4B on the primary split
# ---------------------------------------------------------------------------
PRIMARY = "S2"
MIN_REL_REDUCTION = 5.0     # pre-registered minimum effect size, percent


def adjudicate(structure_model: str) -> dict:
    k4a_key = f"{structure_model}_vs_B1_per_energy_mean"
    k4b_key = f"{structure_model}_vs_MASS_FLEX"
    a = R["paired"][PRIMARY][k4a_key]
    b = R["paired"][PRIMARY][k4b_key]
    k4a = bool(a["mae_diff"] < 0 and a["ci_unit"][1] < 0)
    k4b = bool(b["mae_diff"] < 0 and b["ci_unit"][1] < 0
               and b["rel_reduction_pct"] >= MIN_REL_REDUCTION)
    return {
        "K4A": {"pass": k4a, "mae_diff_vs_B1": a["mae_diff"],
                "ci_unit": a["ci_unit"], "ci_compound": a["ci_compound"],
                "rel_reduction_pct": a["rel_reduction_pct"],
                "rule": "mean MAE reduction vs B1 > 0 and upper bound of the "
                        "95% scaffold-level paired interval < 0"},
        "K4B": {"pass": k4b, "mae_diff_vs_MASS_FLEX": b["mae_diff"],
                "ci_unit": b["ci_unit"], "ci_compound": b["ci_compound"],
                "rel_reduction_pct": b["rel_reduction_pct"],
                "min_required_rel_reduction_pct": MIN_REL_REDUCTION,
                "rule": "paired interval upper bound < 0 AND relative MAE "
                        "reduction >= 5%"},
    }


R["K4_primary_split"] = PRIMARY
R["K4_flexible"] = adjudicate("FLEX_BENCHMARK")
R["K4_tier_a"] = adjudicate("TIER_A")

# ---------------------------------------------------------------------------
# K5 inputs: does structure survive removal of the mass block?
# ---------------------------------------------------------------------------
R["K5_inputs"] = {
    "mass_block_removed": list(MASS_BLOCK),
    "rdkit_mass_like_removed": RDK_MASS_LIKE,
    "tier_a_no_mass_vs_B1": R["paired"][PRIMARY]["TIER_A_no_mass_vs_B1_per_energy_mean"],
    "flex_no_mass_vs_B1": R["paired"][PRIMARY]["FLEX_BENCHMARK_no_mass_vs_B1_per_energy_mean"],
    "tier_a_no_mass_vs_MASS_FLEX": R["paired"][PRIMARY]["TIER_A_no_mass_vs_MASS_FLEX"],
    "flex_no_mass_vs_MASS_FLEX": R["paired"][PRIMARY]["FLEX_BENCHMARK_no_mass_vs_MASS_FLEX"],
    "tier_a_vs_mass_only": R["paired"][PRIMARY]["TIER_A_vs_TIER_A_mass_only"],
}

# ---------------------------------------------------------------------------
# Leakage canary verdict
# ---------------------------------------------------------------------------
R["leakage_canary"] = {
    "purpose": ("S0 splits ROWS, so the six energies of a molecule land on both "
                "sides of the wall. Diagnostic only; never scientific "
                "performance."),
    "comparison": {
        m: {"S0_leaked_mae": R["performance"]["S0_LEAKED"][m]["mae"],
            "S2_honest_mae": R["performance"]["S2"][m]["mae"],
            "inflation_pct": round(
                100 * (R["performance"]["S2"][m]["mae"]
                       - R["performance"]["S0_LEAKED"][m]["mae"])
                / R["performance"]["S2"][m]["mae"], 2)}
        for m in ("B1_per_energy_mean", "MASS_FLEX", "FLEX_BENCHMARK")},
}
fires = R["leakage_canary"]["comparison"]["FLEX_BENCHMARK"]["inflation_pct"] > 0
R["leakage_canary"]["fires"] = bool(fires)

(ART / "p2_baselines.json").write_text(json.dumps(R, indent=2, default=str))
print("\n=== K4 (primary split S2) ===")
print(json.dumps({"flexible": R["K4_flexible"], "tier_a": R["K4_tier_a"]},
                 indent=2, default=str))
print("\n=== leakage canary ===")
print(json.dumps(R["leakage_canary"], indent=2, default=str))
