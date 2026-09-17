#!/usr/bin/env python3
"""Design A numerical separation diagnostics for the three candidate CE inputs K1, K2, K3.

IDENTIFIABILITY DIAGNOSTIC ONLY. Nothing here excludes a compound, and nothing here may be used to
choose the population. The population is fixed by 10_build_population.py before this script runs.

Frozen semantics (exactly as preregistered):
  K1 = float(NCE)
  K2 = float(NCE) * theoretical_mh / 500.0     IEEE-754 binary64, no rounding
  K3 = math.floor(K2) as a float               floor toward negative infinity; K2 > 0 throughout

CE encoding distance uses the checkpoints' own fixed sinusoid, 64 dimensions, 32 sin and 32 cos of
c / 10000^(2i/64) for i = 0..31, documented in MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md
section 6. The implementation is checked at import against the distances quoted there.

Usage:  /opt/miniconda3/bin/python3 scripts/ce_interface_adjudication/design_a/20_separation_diagnostics.py
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
POP_DIR = REPO / "artifacts/ce_interface_adjudication/design_a/population"
OUT_DIR = REPO / "artifacts/ce_interface_adjudication/design_a/diagnostics"
IN_COMPOUNDS = POP_DIR / "design_a_compounds.csv"
IN_RECORDS = POP_DIR / "design_a_records.csv"

NCE_CELLS = (30.0, 60.0)
CE_PE_DIM = 64
CE_PE_SCALAR = 10000.0
_I = np.arange(CE_PE_DIM // 2)
_DENOM = CE_PE_SCALAR ** (2.0 * _I / CE_PE_DIM)

# Mass window definitions for the "K1 and K2 are intrinsically hard to separate" region.
# K1 == K2 exactly at theoretical [M+H]+ = 500, for every NCE.
MASS_WINDOWS = {
    "within_5pct_of_500_(475.0_to_525.0)": (475.0, 525.0),
    "within_10pct_of_500_(450.0_to_550.0)": (450.0, 550.0),
    "within_20pct_of_500_(400.0_to_600.0)": (400.0, 600.0),
}
NULL_REGION = (450.0, 550.0)
ABS_K1K2_THRESHOLDS = (1.0, 2.0, 5.0)


def ce_embed(c):
    """64-dim fixed sinusoid CE encoding: 32 sin then 32 cos of c / 10000**(2i/64)."""
    a = np.asarray(c, dtype=float)[..., None] / _DENOM
    return np.concatenate([np.sin(a), np.cos(a)], axis=-1)


def ce_distance(a, b):
    return np.linalg.norm(ce_embed(a) - ce_embed(b), axis=-1)


def _self_check():
    """Reproduce the distances quoted in Phase 0 section 6."""
    quoted = {(20.0, 12.0): 4.38, (20.0, 60.0): 5.76, (0.5, 0.0): 0.75, (1.0, 0.0): 1.47,
              (5.0, 0.0): 4.12, (40.0, 0.0): 5.76, (300.0, 0.0): 6.73}
    out = {}
    for (x, y), want in quoted.items():
        got = float(ce_distance(x, y))
        out[f"d({x:g},{y:g})"] = {"computed": got, "quoted_in_phase0_section6": want,
                                  "agrees_to_2dp": abs(round(got, 2) - want) < 1e-9}
        if abs(round(got, 2) - want) >= 1e-9:
            raise SystemExit(f"CE embedding self-check FAILED for d({x},{y}): {got} vs quoted {want}")
    return out


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dist(a) -> dict:
    a = pd.Series(a).dropna().astype(float)
    if not len(a):
        return {}
    q = a.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    return {
        "n": int(len(a)), "min": float(a.min()), "q05": float(q.loc[0.05]), "q25": float(q.loc[0.25]),
        "median": float(q.loc[0.5]), "q75": float(q.loc[0.75]), "q95": float(q.loc[0.95]),
        "max": float(a.max()), "mean": float(a.mean()),
        "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
    }


README = """# Design A separation diagnostics (K1, K2, K3)

Evidence convention, as used by the other documents in this study: **VERIFIED** = read in code or data,
or recomputed here; **INFERRED** = reasoned from verified facts, not directly observed.

## What this is, and what it is not

VERIFIED: these numbers are computed from `../population/design_a_compounds.csv` only. They are an
identifiability diagnostic. **No compound is excluded by anything in this directory, and nothing here
may be used to change the population.** The population was frozen by `10_build_population.py` before
this script ran.

## Frozen semantics

VERIFIED, implemented exactly as stated:

- `K1 = float(NCE)`
- `K2 = float(NCE) * theoretical_mh / 500.0` in IEEE-754 binary64, no rounding
- `K3 = math.floor(K2)` as a float (floor toward negative infinity; `K2 > 0` for every cell here)

`theoretical_mh` is the theoretical [M+H]+ of the frozen representative structure, not the deposited
`PRECURSOR_M/Z`.

## CE encoding distance

VERIFIED: the 64-dimension fixed sinusoid of Phase 0 provenance section 6, 32 sin and 32 cos of
`c / 10000^(2i/64)` for `i = 0..31`, implemented from that definition and checked against the
distances the same section quotes: `d(20,12) = 4.38`, `d(20,60) = 5.76`, and the difference-only
reference points 0.5 -> 0.75, 1 -> 1.47, 5 -> 4.12, 40 -> 5.76, 300 -> 6.73. All reproduce to two
decimal places; the check is an assertion inside the script, so the numbers below cannot be produced
if it fails. VERIFIED consequence of that same section: the encoding has no normalisation, clipping or
bucketing, so this distance is the whole of what the three candidate inputs look like to the frozen
checkpoints at the input layer.

## Leverage

{LEVERAGE}

## The interpretation a null result requires

INFERRED, and a preregistration author must state it before the study runs: a null or unresolved
adjudication outcome on this population is **not** evidence that the three interfaces are the same.
Separation on the energy axis is bounded by the mass composition of the 33 compounds, and this
population was drawn from the one public source that satisfies the identity exclusions, not designed
for energy-axis leverage. Where `|K1 - K2|` is small, or where the encoding distance between two
candidates is small relative to what the models resolve, a null outcome is what lack of leverage
predicts, and it is indistinguishable at this size from a genuine absence of an interface difference.
The high-mass and null-mass strata of the Design B acquisition exist precisely to remove that
ambiguity.

## Files

| File | Contents |
| --- | --- |
| `k_separation_per_compound.csv` | one row per (compound, NCE cell): K1, K2, K3, absolute separations, encoding distances, mass-window flags |
| `k_separation_summary.json` | full distributions per cell and pooled, mass-window counts, threshold counts, embedding-distance distributions, the embedding self-check, and a sha256 manifest |
| `README.md` | this file |
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    selfcheck = _self_check()

    comp = pd.read_csv(IN_COMPOUNDS)
    rows = []
    for _, c in comp.iterrows():
        mh = float(c["theoretical_mh"])
        for nce in NCE_CELLS:
            k1 = float(nce)
            k2 = float(nce) * mh / 500.0
            k3 = float(math.floor(k2))
            rows.append(
                {
                    "compound_id": c["compound_id"],
                    "scaffold_group": c["scaffold_group"],
                    "formula": c["formula"],
                    "theoretical_mh": mh,
                    "nce": nce,
                    "K1": k1,
                    "K2": k2,
                    "K3": k3,
                    "abs_K1_K2": abs(k1 - k2),
                    "abs_K2_K3": abs(k2 - k3),
                    "abs_K1_K3": abs(k1 - k3),
                    "d_K1_K2": float(ce_distance(k1, k2)),
                    "d_K2_K3": float(ce_distance(k2, k3)),
                    "d_K1_K3": float(ce_distance(k1, k3)),
                    "in_null_region_450_550": bool(NULL_REGION[0] <= mh <= NULL_REGION[1]),
                }
            )
    per = pd.DataFrame(rows).sort_values(["compound_id", "nce"], kind="mergesort").reset_index(drop=True)
    for name, (lo, hi) in MASS_WINDOWS.items():
        per[f"mass_{name}"] = (per["theoretical_mh"] >= lo) & (per["theoretical_mh"] <= hi)

    quantities = ["abs_K1_K2", "abs_K2_K3", "abs_K1_K3", "d_K1_K2", "d_K2_K3", "d_K1_K3"]
    summary = {
        "study": "MURU CE interface adjudication, Design A, separation diagnostics",
        "generated_by": "scripts/ce_interface_adjudication/design_a/20_separation_diagnostics.py",
        "status": "IDENTIFIABILITY DIAGNOSTIC ONLY. Never used to exclude a compound.",
        "frozen_semantics": {
            "K1": "float(NCE)",
            "K2": "float(NCE) * theoretical_mh / 500.0, IEEE-754 binary64, no rounding",
            "K3": "math.floor(K2) as a float, floor toward negative infinity; K2 > 0 throughout",
            "theoretical_mh_source": "design_a_compounds.csv, theoretical [M+H]+ of the representative structure",
        },
        "ce_encoding": {
            "dimensions": CE_PE_DIM,
            "definition": "32 sin and 32 cos of c / 10000^(2i/64), i = 0..31 (Phase 0 provenance section 6)",
            "self_check_against_phase0_section6": selfcheck,
        },
        "population": {
            "compounds": int(comp.shape[0]),
            "scaffold_groups": int(comp["scaffold_group"].nunique()),
            "nce_cells": list(NCE_CELLS),
            "theoretical_mh": dist(comp["theoretical_mh"]),
        },
        "distributions": {},
        "mass_windows_around_mz_500": {},
        "abs_K1_K2_threshold_counts": {},
    }

    for cell in list(NCE_CELLS) + ["pooled"]:
        sub = per if cell == "pooled" else per[per["nce"] == cell]
        key = "pooled" if cell == "pooled" else f"nce_{cell:g}"
        summary["distributions"][key] = {q: dist(sub[q]) for q in quantities}

    n_comp = int(comp.shape[0])
    for name, (lo, hi) in MASS_WINDOWS.items():
        sel = comp[(comp["theoretical_mh"] >= lo) & (comp["theoretical_mh"] <= hi)]
        summary["mass_windows_around_mz_500"][name] = {
            "window_da": [lo, hi],
            "n_compounds": int(len(sel)),
            "fraction_of_population": float(len(sel) / n_comp) if n_comp else None,
            "compound_ids": sorted(sel["compound_id"].tolist()),
            "theoretical_mh": sorted(round(float(v), 4) for v in sel["theoretical_mh"]),
        }
    summary["null_region_450_to_550"] = summary["mass_windows_around_mz_500"][
        "within_10pct_of_500_(450.0_to_550.0)"
    ]

    for cell in list(NCE_CELLS) + ["pooled", "any_cell_compounds"]:
        if cell == "any_cell_compounds":
            g = per.groupby("compound_id")["abs_K1_K2"].min()
            summary["abs_K1_K2_threshold_counts"]["compounds_with_any_cell_below"] = {
                f"below_{t:g}": int((g < t).sum()) for t in ABS_K1K2_THRESHOLDS
            }
            continue
        sub = per if cell == "pooled" else per[per["nce"] == cell]
        key = "pooled_cells" if cell == "pooled" else f"nce_{cell:g}_cells"
        summary["abs_K1_K2_threshold_counts"][key] = {
            f"below_{t:g}": int((sub["abs_K1_K2"] < t).sum()) for t in ABS_K1K2_THRESHOLDS
        }
        summary["abs_K1_K2_threshold_counts"][key]["n_cells"] = int(len(sub))

    # K2 vs K3: how often does the floor actually change the value at all
    summary["K2_vs_K3"] = {
        "cells_where_K2_equals_K3_exactly": int((per["abs_K2_K3"] == 0.0).sum()),
        "cells_total": int(len(per)),
        "note": "K2 - K3 is the fractional part of K2; it is bounded in [0,1) by construction.",
    }

    p_csv = OUT_DIR / "k_separation_per_compound.csv"
    p_json = OUT_DIR / "k_separation_summary.json"
    p_readme = OUT_DIR / "README.md"
    per.to_csv(p_csv, index=False)

    pooled = summary["distributions"]["pooled"]
    nullreg = summary["null_region_450_to_550"]
    leverage = (
        "VERIFIED, from `k_separation_summary.json`:\n\n"
        f"- Pooled over the {len(per)} (compound, cell) pairs, `|K1 - K2|` has median "
        f"{pooled['abs_K1_K2']['median']:.2f}, q05 {pooled['abs_K1_K2']['q05']:.2f}, q95 "
        f"{pooled['abs_K1_K2']['q95']:.2f}, range {pooled['abs_K1_K2']['min']:.2f} to "
        f"{pooled['abs_K1_K2']['max']:.2f}.\n"
        f"- In the encoding the models actually see, `d(K1, K2)` has median "
        f"{pooled['d_K1_K2']['median']:.2f}, q05 {pooled['d_K1_K2']['q05']:.2f}, q95 "
        f"{pooled['d_K1_K2']['q95']:.2f}, against the difference-only reference points quoted above "
        f"(a difference of 1 gives 1.47, of 5 gives 4.12, of 40 gives 5.76) and a random-phase "
        f"expectation of 8.0.\n"
        f"- `d(K2, K3)` has median {pooled['d_K2_K3']['median']:.2f} and max "
        f"{pooled['d_K2_K3']['max']:.2f}: K2 and K3 differ only by the fractional part of K2, so the "
        f"K2-against-K3 contrast is the weakest of the three by construction, bounded above by "
        f"d(1, 0) = 1.47.\n"
        f"- `d(K1, K3)` has median {pooled['d_K1_K3']['median']:.2f}, q05 "
        f"{pooled['d_K1_K3']['q05']:.2f}, q95 {pooled['d_K1_K3']['q95']:.2f}.\n"
        f"- Compounds in the 450 to 550 null region, where K1 and K2 are intrinsically hard to "
        f"separate: {nullreg['n_compounds']} of {n_comp}. Within 5 percent of m/z 500: "
        f"{summary['mass_windows_around_mz_500']['within_5pct_of_500_(475.0_to_525.0)']['n_compounds']}. "
        f"Within 20 percent: "
        f"{summary['mass_windows_around_mz_500']['within_20pct_of_500_(400.0_to_600.0)']['n_compounds']}.\n"
        f"- Cells with `|K1 - K2|` below 1: "
        f"{summary['abs_K1_K2_threshold_counts']['pooled_cells']['below_1']} of {len(per)}; below 2: "
        f"{summary['abs_K1_K2_threshold_counts']['pooled_cells']['below_2']}; below 5: "
        f"{summary['abs_K1_K2_threshold_counts']['pooled_cells']['below_5']}.\n"
        f"- The NCE 60 cell carries more separation than the NCE 30 cell throughout, because "
        f"`K1 - K2 = NCE x (1 - mh/500)` scales linearly in NCE: median `|K1 - K2|` is "
        f"{summary['distributions']['nce_30']['abs_K1_K2']['median']:.2f} at NCE 30 against "
        f"{summary['distributions']['nce_60']['abs_K1_K2']['median']:.2f} at NCE 60.\n"
    )
    p_readme.write_text(README.replace("{LEVERAGE}", leverage))

    summary["manifest_sha256"] = {
        "inputs_read": {str(p.relative_to(REPO)): sha256_of(p) for p in [IN_COMPOUNDS, IN_RECORDS]},
        "outputs_written": {str(p.relative_to(REPO)): sha256_of(p) for p in [p_csv, p_readme]},
        "script": str(HERE.relative_to(REPO)),
        "script_sha256": sha256_of(HERE),
    }
    p_json.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")

    print("Design A separation diagnostics")
    print(f"  compounds {n_comp}  cells {len(per)}  (NCE {', '.join(f'{c:g}' for c in NCE_CELLS)})")
    print(f"  CE embedding self-check against Phase 0 section 6: PASS "
          f"(d(20,12)={selfcheck['d(20,12)']['computed']:.4f}, d(20,60)={selfcheck['d(20,60)']['computed']:.4f})")
    for key in ["nce_30", "nce_60", "pooled"]:
        b = summary["distributions"][key]
        print(f"  {key:7s} |K1-K2| med {b['abs_K1_K2']['median']:7.3f} [{b['abs_K1_K2']['min']:.3f}, {b['abs_K1_K2']['max']:.3f}]"
              f"   |K2-K3| med {b['abs_K2_K3']['median']:.3f}"
              f"   |K1-K3| med {b['abs_K1_K3']['median']:7.3f}")
        print(f"  {'':7s} d(K1,K2) med {b['d_K1_K2']['median']:6.3f}   d(K2,K3) med {b['d_K2_K3']['median']:6.3f}"
              f"   d(K1,K3) med {b['d_K1_K3']['median']:6.3f}")
    print(f"  compounds with theoretical [M+H]+ in 450-550 (null region): {nullreg['n_compounds']} of {n_comp}"
          f"  -> {nullreg['compound_ids']}")
    for name in MASS_WINDOWS:
        print(f"  mass window {name}: {summary['mass_windows_around_mz_500'][name]['n_compounds']}")
    print(f"  |K1-K2| below 1 / 2 / 5 (cells): "
          f"{summary['abs_K1_K2_threshold_counts']['pooled_cells']['below_1']} / "
          f"{summary['abs_K1_K2_threshold_counts']['pooled_cells']['below_2']} / "
          f"{summary['abs_K1_K2_threshold_counts']['pooled_cells']['below_5']} of {len(per)}")
    print(f"  wrote {p_csv.name}, {p_json.name}, {p_readme.name} in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
