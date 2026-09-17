"""Task C (completeness critic): re-derive the C01 screen numbers the deliverables quote but the
screen artifacts do not record as a named field.

Read-only. No model, no inference, no network. Appends its results into
artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json under key C01_screen_recheck.
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
sys.path.insert(0, str(ROOT / "scripts" / "ce_interface_adjudication"))

from rdkit import DataStructs, RDLogger  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
from rdkit.ML.Cluster import Butina  # noqa: E402

RDLogger.DisableLog("rdApp.*")
import scaffold_key as SK  # noqa: E402

GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
CLETHODIM = "PHXHZCIAPNNPTQ"
SCREEN = ROOT / "artifacts" / "ce_interface_adjudication" / "screen" / "c01_eawag_eq"
OUT = ROOT / "artifacts" / "ce_interface_adjudication" / "counts" / "c_taskc_recheck.json"


def n_clusters(df, dist=0.6):
    """Same recipe as screen_c01_eawag_eq.py:424-437 (Morgan2 2048, Tanimoto distance 0.6)."""
    fps = [GEN.GetFingerprint(SK.parent_mol(x)) for x in df["smiles"]]
    dd = []
    for i in range(1, len(fps)):
        dd.extend([1 - v for v in DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])])
    return len(Butina.ClusterData(dd, len(fps), dist, isDistData=True))


def main():
    rec = pd.read_csv(SCREEN / "c01_record_metadata.csv.gz")
    cs = pd.read_csv(SCREEN / "c01_compound_screen.csv")
    g = cs[cs.ge3_nce]

    out = {}

    # 1. the full distinct NCE set, which v_screen.md reported from a truncated examples field
    out["ce_string_forms"] = {str(k): int(v) for k, v in rec.ce_form.value_counts().items()}
    out["distinct_nce_values_all_5051_records"] = {str(k): int(v) for k, v in
                                                   rec.nce.value_counts().sort_index().items()}
    out["n_distinct_nce_values"] = int(rec.nce.nunique())
    modal = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0, 120.0, 150.0, 180.0]
    out["records_on_modal_9_value_ladder"] = int(rec.nce.isin(modal).sum())
    out["records_off_modal_ladder"] = int((~rec.nce.isin(modal)).sum())

    # 2. Butina cluster counts per tier, before and after the tautomer exclusion
    tiers = {}
    for col, label in [("clean_compound_level", "compound_level"), ("clean_primary", "primary"),
                       ("clean_conservative", "conservative"), ("clean_strict_msg_scaffold", "strict")]:
        pre = g[g[col]]
        post = pre[pre.cmp_key != CLETHODIM]
        tiers[label] = {
            "n_pre_tautomer": int(len(pre)), "butina_pre_tautomer": n_clusters(pre),
            "n_post_tautomer": int(len(post)), "butina_post_tautomer": n_clusters(post),
            "scaffold_groups_post_tautomer": int(post.scaffold_group.nunique()),
            "records_post_tautomer": int(post.n_records.sum()),
            "mh_ge_500_post_tautomer": int((post.mh_calc >= 500).sum()),
        }
        tagged_post = post[post.tagged_release]
        tiers[label]["tagged_only_post_tautomer"] = {
            "n": int(len(tagged_post)), "scaffold_groups": int(tagged_post.scaffold_group.nunique())}
    out["tiers"] = tiers

    # 3. per-tier NCE rung availability (the design documents quote "median 6 rungs inside 15 to 90")
    rungs = {}
    for col, label in [("clean_primary", "primary"), ("clean_conservative", "conservative")]:
        post = g[g[col] & (g.cmp_key != CLETHODIM)]
        counts, per = {}, []
        for L in post.nce_ladder:
            vals = [float(x) for x in str(L).split(",")]
            for v in vals:
                counts[v] = counts.get(v, 0) + 1
            per.append(sum(1 for v in vals if 15 <= v <= 90))
        rungs[label] = {"n_compounds": int(len(post)),
                        "compounds_carrying_each_nce": {str(k): int(counts[k]) for k in sorted(counts)},
                        "median_rungs_in_15_90": float(np.median(per))}
    out["nce_rung_availability"] = rungs

    # 4. instrument and resolution mix on the [M+H]+ records
    mh = rec[rec.precursor_type == "[M+H]+"]
    out["mh_records"] = int(len(mh))
    out["mh_instrument_strings"] = {str(k): int(v) for k, v in mh.instrument.value_counts().items()}
    out["mh_resolution"] = {str(k): int(v) for k, v in mh.resolution.value_counts().items()}
    out["compounds_with_records_from_two_instruments"] = {
        "all_415": int((cs.n_instruments > 1).sum()),
        "ge3_nce_403": int((g.n_instruments > 1).sum()),
        "compound_level_clean": int((g[g.clean_compound_level].n_instruments > 1).sum()),
        "primary": int((g[g.clean_primary].n_instruments > 1).sum()),
        "conservative": int((g[g.clean_conservative].n_instruments > 1).sum()),
        "strict": int((g[g.clean_strict_msg_scaffold].n_instruments > 1).sum()),
    }

    blob = json.loads(OUT.read_text()) if OUT.exists() else {}
    blob["C01_screen_recheck"] = out
    OUT.write_text(json.dumps(blob, indent=1))
    print(json.dumps(out, indent=1))
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
