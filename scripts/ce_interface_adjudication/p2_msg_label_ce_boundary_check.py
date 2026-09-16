#!/usr/bin/env python3
"""P2 boundary check: CE values that the ms-pred MSG label file hands to the model code.

Compares the committed ms-pred labels (data/spec_datasets/msg/labels.tsv, collision_energies
strings) with MassSpecGym 1.5 `collision_energy` from the identity parquet. Metadata only.
It records (a) whether labels.tsv carries MSG values unchanged or rounded, (b) instrument and
adduct vocabularies present, (c) CE range, and (d) how many non-integer MSG CE values equal
NCE * precursor_mz / 500 for an NCE on the 5-step ladder (a pointer for P1; source attribution
is NOT decided here).

Usage: p2_msg_label_ce_boundary_check.py OUT_JSON
"""
import ast
import json
import sys

import numpy as np
import pandas as pd

LABELS = "/Users/aryav/muru-comparators/repos/ms-pred/data/spec_datasets/msg/labels.tsv"
IDENT = ("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication/"
         "artifacts/comparator_feasibility/massspecgym15_identity.parquet")


def first_ce(s):
    v = ast.literal_eval(s)
    return float(str(v[0]).split()[0])


def main(out_path):
    lab = pd.read_csv(LABELS, sep="\t")
    idt = pd.read_parquet(IDENT, columns=["identifier", "collision_energy", "instrument_type", "adduct"])
    m = lab.merge(idt, left_on="spec", right_on="identifier", how="left")
    out = {
        "labels_rows": int(len(lab)),
        "labels_matched_in_msg15": int(m["identifier"].notna().sum()),
        "labels_ionization_counts": lab["ionization"].value_counts().to_dict(),
        "labels_instrument_counts": lab["instrument"].value_counts().to_dict(),
        "labels_instrument_equals_msg_instrument_type": bool((m["instrument"] == m["instrument_type"]).all()),
    }
    lce = m["collision_energies"].map(first_ce)
    mce = m["collision_energy"].astype(float)
    out["labels_ce_equals_msg_ce_exact"] = int(np.isclose(lce, mce).sum())
    out["labels_ce_equals_round_msg_ce"] = int(np.isclose(lce, np.round(mce)).sum())
    out["labels_ce_equals_floor_msg_ce"] = int(np.isclose(lce, np.floor(mce)).sum())
    out["labels_ce_all_integer"] = bool(np.all(np.isclose(lce, np.round(lce))))
    nonint = ~np.isclose(mce, np.round(mce))
    out["msg_ce_nonint_rows"] = int(nonint.sum())
    out["msg_ce_nonint_by_instrument"] = m.loc[nonint, "instrument"].value_counts().to_dict()
    implied = mce[nonint] * 500 / m.loc[nonint, "precursor"]
    out["msg_ce_nonint_implied_nce_within_0.05_of_5_step"] = float((np.abs(implied - 5 * np.round(implied / 5)) < 0.05).mean())
    out["ce_range_labels"] = [float(lce.min()), float(lce.max())]
    out["ce_quantiles_labels"] = {str(q): float(lce.quantile(q)) for q in (0.01, 0.5, 0.99)}
    out["precursor_range_labels"] = [float(lab["precursor"].min()), float(lab["precursor"].max())]
    with open(out_path, "w") as f:
        f.write(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
