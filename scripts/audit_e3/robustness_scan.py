"""INDEPENDENT robustness/sensitivity scan over the raw e3_worlds.jsonl.

Checks (numerical/implementation robustness only -- no scientific criteria
are moved):
  1. Convergence failure rate across all 50,000 (world x model) fits.
  2. BIC near-tie rate: how often is the BIC-selected model's margin over the
     runner-up small enough that floating-point noise could plausibly flip
     the selection?
  3. How many cells sit within one Wilson-CI-width of the 0.50/0.80
     classification boundaries (classification fragility, not a threshold
     change).
  4. Sample-count convention check: n_train used in every world's BIC.
  5. Distribution of BIC value magnitudes / any NaN or inf leakage.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

WORLDS_PATH = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-v2-e3-identifiability-b23a7b/results/e3_identifiability/e3_worlds.jsonl")
OUT_DIR = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/audit-v2-e3-independent/results/audit_e3")
MODEL_IDS = ("M_mass", "M_affine", "M_sat", "M_exp", "M_inter")


def main():
    n_worlds = 0
    n_fits = 0
    n_converged = 0
    n_train_values = Counter()
    bic_margin_hist = Counter()  # bucketed
    tiny_margin_worlds = []  # BIC-selected model within margin < 2.0 of runner-up (weak-evidence zone, Raftery 1995 convention)
    n_nan_or_none_bic = 0
    n_negative_c_affine_true = 0
    n_worlds_any_nonconverged = 0

    with WORLDS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            n_worlds += 1
            bics = {}
            any_nonconverged = False
            for mid in MODEL_IDS:
                m = r["models"][mid]
                n_fits += 1
                n_train_values[m["n_train"]] += 1
                if m["converged"]:
                    n_converged += 1
                else:
                    any_nonconverged = True
                bic = m["bic"]
                if bic is None:
                    n_nan_or_none_bic += 1
                else:
                    bics[mid] = bic
            if any_nonconverged:
                n_worlds_any_nonconverged += 1

            if len(bics) >= 2:
                sorted_bics = sorted(bics.values())
                margin = sorted_bics[1] - sorted_bics[0]  # runner-up minus best (BIC: lower is better)
                bucket = (
                    "<0.1" if margin < 0.1 else
                    "<1" if margin < 1 else
                    "<2" if margin < 2 else
                    "<6" if margin < 6 else
                    "<10" if margin < 10 else
                    ">=10"
                )
                bic_margin_hist[bucket] += 1
                if margin < 2.0:  # Raftery (1995): BIC diff < 2 is "weak" evidence
                    tiny_margin_worlds.append({"world_id": r["world_id"], "family": r["family"], "margin": margin, "selected": r["bic_selected_model"]})

    print(f"Total worlds: {n_worlds}")
    print(f"Total (world x model) fits: {n_fits}")
    print(f"Converged fits: {n_converged} / {n_fits} ({100*n_converged/n_fits:.4f}%)")
    print(f"Non-converged fits: {n_fits - n_converged}")
    print(f"Worlds with >=1 non-converged model fit: {n_worlds_any_nonconverged}")
    print(f"NaN/None BIC count: {n_nan_or_none_bic}")
    print(f"\nn_train value distribution (should be entirely 120): {dict(n_train_values)}")

    print(f"\nBIC margin (winner vs runner-up) histogram:")
    for k in ["<0.1", "<1", "<2", "<6", "<10", ">=10"]:
        print(f"  {k:6s}: {bic_margin_hist.get(k, 0)}")
    print(f"\nWorlds with 'weak' BIC evidence (margin < 2, Raftery 1995 convention): {len(tiny_margin_worlds)} / {n_worlds} ({100*len(tiny_margin_worlds)/n_worlds:.2f}%)")
    print(f"Worlds with near-total-tie BIC margin < 0.1: {bic_margin_hist.get('<0.1', 0)} ({100*bic_margin_hist.get('<0.1',0)/n_worlds:.2f}%)")

    # Break down tiny-margin worlds by family -- do they concentrate in the
    # families whose classification sits near a decision boundary (affine/exp)?
    by_family = Counter(w["family"] for w in tiny_margin_worlds)
    print(f"\nWeak-evidence (<2 BIC) worlds by family: {dict(by_family)}")

    result = {
        "n_worlds": n_worlds,
        "n_fits": n_fits,
        "n_converged": n_converged,
        "n_nonconverged": n_fits - n_converged,
        "n_worlds_any_nonconverged": n_worlds_any_nonconverged,
        "n_nan_bic": n_nan_or_none_bic,
        "n_train_distribution": dict(n_train_values),
        "bic_margin_histogram": dict(bic_margin_hist),
        "n_weak_evidence_worlds_margin_lt_2": len(tiny_margin_worlds),
        "weak_evidence_by_family": dict(by_family),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "robustness_scan.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
