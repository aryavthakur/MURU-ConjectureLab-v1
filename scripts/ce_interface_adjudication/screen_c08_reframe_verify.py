"""S8 second pass: independent verification of the C08 GNPS REFRAME-POSITIVE-LIBRARY screen,
plus the collision-energy evidence the first pass did not have.

What this adds over screen_c08_reframe.py:
  (1) re-derives the library-membership row split and the collision_energy emptiness directly
      from the two processed GNPS CSVs (the 88,424 / 96,016 row files each bundle an unrelated
      78,806-row MONA_ML_Export block, so a naive row count is wrong);
  (2) reads the GNPS2 dataset cache `uniquemri` table for MSV000093469, which carries per-file
      scalar acquisition metadata (Top_CEs, Top_CE_Counts, MassAnalyzer, Ionization,
      classification) derived from the mzML headers, and settles how many distinct collision
      energies the underlying raw data actually contains, without downloading any spectra;
  (3) re-computes the exclusion overlaps and candidate pools from the raw key lists instead of
      trusting the precomputed boolean columns;
  (4) re-derives MURU key and scaffold group from SMILES for a random sample of records.

Metadata only. No spectra file is read or downloaded. No prediction or inference is run.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
ART = ROOT / "artifacts/ce_interface_adjudication"
SCREEN = ART / "screen/c08_reframe"
DL = SCREEN / "downloads"
EXCL = ART / "exclusion"

sys.path.insert(0, str(ROOT / "scripts/ce_interface_adjudication"))
import scaffold_key as SK  # noqa: E402


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def keyset(name: str) -> set:
    return {ln.strip() for ln in (EXCL / name).read_text().splitlines() if ln.strip()}


out: dict = {"script": "scripts/ce_interface_adjudication/screen_c08_reframe_verify.py",
             "rdkit": SK.rdBase.rdkitVersion, "frozen_rdkit": SK.FROZEN_RDKIT}

# ---------------------------------------------------------------- (1) processed CSVs
csv_checks = {}
for fn, own in (("REFRAME-POSITIVE-LIBRARY.csv", "REFRAME-POSITIVE-LIBRARY"),
                ("CMMC-REFRAME-POSITIVE-LIBRARY.csv", "CMMC-REFRAME-POSITIVE-LIBRARY")):
    p = DL / fn
    df = pd.read_csv(p, low_memory=False, dtype=str)
    nb = df["collision_energy"].fillna("").str.strip().ne("")
    own_mask = df["GNPS_library_membership"] == own
    rec = {
        "sha256": sha256(p), "bytes": p.stat().st_size,
        "total_rows": int(len(df)),
        "rows_by_membership": {k: int(v) for k, v in df.groupby(
            df["GNPS_library_membership"].fillna("(nan)")).size().items()},
        "collision_energy_nonblank_by_membership": {
            k: int(nb[df["GNPS_library_membership"].fillna("(nan)") == k].sum())
            for k in df["GNPS_library_membership"].fillna("(nan)").unique()},
        "own_rows": int(own_mask.sum()),
        "own_collision_energy_nonblank": int(nb[own_mask].sum()),
        "own_msDissociationMethod_nonblank": int(
            df.loc[own_mask, "msDissociationMethod"].fillna("").str.strip().ne("").sum()),
        "own_msManufacturer": dict(Counter(df.loc[own_mask, "msManufacturer"].fillna("(blank)"))),
        "own_msMassAnalyzer": dict(Counter(df.loc[own_mask, "msMassAnalyzer"].fillna("(blank)"))),
        "own_adducts": dict(Counter(df.loc[own_mask, "Adduct"].fillna("(blank)"))),
    }
    csv_checks[fn] = rec
out["processed_csv_verification"] = csv_checks

# ---------------------------------------------------------------- (2) raw-file CE metadata
umri = list(csv.DictReader(open(DL / "gnps2_datasetcache_uniquemri_MSV000093469.csv")))
pos = [r for r in umri if r["collection"] == "20230816_ReFrame_drug_lib_pos"]
neg = [r for r in umri if r["collection"] == "20230821_ReFrame_drug_lib_neg"]
ce = {
    "source_url": "https://datasetcache.gnps2.org/datasette/database/uniquemri.csv?dataset__exact=MSV000093469&_size=max",
    "sha256": sha256(DL / "gnps2_datasetcache_uniquemri_MSV000093469.csv"),
    "rows": len(umri),
    "note": ("the `peak/` rows carry the computed per-file summary; the duplicate `ccms_peak/` rows are blank. "
             "Top_CEs / Top_CE_Counts are the distinct collision-energy values recorded in the mzML and their "
             "scan counts, produced by the (non-public) PerScanSummarizer_Workflow consumed at "
             "GNPS_DatasetCache/tasks_compute.py:355-356."),
    "pos_files": len(pos), "neg_files": len(neg),
    "pos_Top_CEs": dict(Counter(r["Top_CEs"] for r in pos)),
    "neg_Top_CEs": dict(Counter(r["Top_CEs"] for r in neg)),
    "pos_MassAnalyzer": dict(Counter(r["MassAnalyzer"] for r in pos)),
    "pos_Ionization": dict(Counter(r["Ionization"] for r in pos)),
    "pos_classification": dict(Counter(r["classification"] for r in pos)),
    "pos_ms2_total": sum(int(r["spectra_ms2"] or 0) for r in pos),
    "pos_ms2_covered_by_top_ce": sum(int(r["Top_CE_Counts"] or 0) for r in pos),
    "pos_files_where_Top_CE_Counts_ne_spectra_ms2": [r["filepath"] for r in pos
                                                     if r["Top_CE_Counts"] != r["spectra_ms2"]],
    "pos_RT_Range_in_Min": dict(Counter(r["RT_Range_in_Min"] for r in pos)),
}
ce["single_collision_energy_for_every_positive_ms2_scan"] = bool(
    len(ce["pos_Top_CEs"]) == 1 and ce["pos_ms2_total"] == ce["pos_ms2_covered_by_top_ce"]
    and not ce["pos_files_where_Top_CE_Counts_ne_spectra_ms2"])
out["raw_file_collision_energy_metadata"] = ce

# ---------------------------------------------------------------- (3) overlaps and pools
rec = pd.read_csv(SCREEN / "c08_reframe_records_identity_overlap.csv", low_memory=False)
out["identity_csv"] = {"sha256": sha256(SCREEN / "c08_reframe_records_identity_overlap.csv"),
                       "records": int(len(rec))}

sets = {
    "msg15_all_either_route": keyset("msg15_parent_keys_all.txt") | keyset("msg15_keys_all.txt"),
    "msg15_recorded_all": keyset("msg15_keys_all.txt"),
    "msg15_train": keyset("msg15_keys_train.txt"),
    "msg15_val": keyset("msg15_keys_val.txt"),
    "msg15_test": keyset("msg15_keys_test.txt"),
    "muru_registry": keyset("muru_exposure_registry_keys.txt"),
    "muru_exposed_union": keyset("muru_exposed_union_keys.txt"),
    "pr7": keyset("msnlib_study2_population_keys.txt"),
    "comparator": keyset("comparator_common_population_keys.txt"),
    "msnlib_9lib": keyset("msnlib_9lib_keys.txt"),
}
sgsets = {
    "msg15_sg": keyset("msg15_scaffold_groups_all.txt"),
    "muru_registry_sg": keyset("muru_exposure_registry_scaffold_groups.txt"),
    "pr7_sg": keyset("msnlib_study2_population_scaffold_groups.txt"),
    "comparator_sg": keyset("comparator_common_population_scaffold_groups.txt"),
}
out["exclusion_set_sizes"] = {k: len(v) for k, v in {**sets, **sgsets}.items()}

allk = set(rec["key"].dropna())
ov = {"records": int(len(rec)), "unique_keys": len(allk),
      "unique_scaffold_groups": int(rec["scaffold_group"].nunique())}
for n, s in sets.items():
    ov["keys_in_" + n] = len(allk & s)
out["independent_overlap_all_records"] = ov

mh = rec[(rec["adduct"] == "[M+H]+") & (rec["adduct_csv"] == "[M+H]1+") & (~rec["charged_parent"].astype(bool))]
pools = {}


def pool(label, sub):
    k = set(sub["key"].dropna())
    g = set(sub["scaffold_group"].dropna())
    per_key = sub.drop_duplicates("key")
    pools[label] = {"records": int(len(sub)), "keys": len(k), "scaffold_groups": len(g),
                    "singleton_scaffold_groups": int(sum(1 for _, c in Counter(
                        per_key["scaffold_group"]).items() if c == 1))}
    return sub


pool("V1 [M+H]+ charge-neutral parent", mh)
p1b = mh[~mh["key"].isin(sets["msg15_all_either_route"])]
pool("V1b minus MassSpecGym 1.5 (all folds, either key route)", p1b)
p3 = p1b[~p1b["key"].isin(sets["muru_registry"] | sets["muru_exposed_union"] | sets["pr7"] | sets["comparator"])]
pool("V3 minus MURU registry/exposed union, PR#7, comparator", p3)
p5 = p3[~p3["scaffold_group"].isin(sgsets["muru_registry_sg"] | sgsets["pr7_sg"] | sgsets["comparator_sg"])]
pool("V5 = V3 minus MURU/PR7/comparator scaffold groups", p5)
p8 = p5[(p5["precursor_mz"].between(70.0, 1042.6))
        & (p5["precursor_err_da"].abs() <= 0.01)
        & (~p5["coinjected_ion_within_0p7_lower_bound"].astype(bool))
        & (~p5["coinjected_isomer_lower_bound"].astype(bool))]
pool("V8 = V5 with precursor-range / precursor-consistency / no-co-injected-ion filters", p8)
out["independent_pools"] = pools

# ---------------------------------------------------------------- (4) key/scaffold re-derivation
random.seed(8)
samp = rec.dropna(subset=["smiles", "key"]).sample(n=min(400, len(rec)), random_state=8)
kok = gok = 0
bad = []
for r in samp.itertuples(index=False):
    k, g = SK.key_and_group(r.smiles)
    kok += int(k == r.key)
    gok += int(g == r.scaffold_group)
    if (k != r.key or g != r.scaffold_group) and len(bad) < 5:
        bad.append({"spectrum_id": r.spectrum_id, "csv_key": r.key, "recomputed_key": k,
                    "csv_group": r.scaffold_group, "recomputed_group": g})
out["identity_recomputation_sample"] = {"n": int(len(samp)), "key_match": kok, "scaffold_group_match": gok,
                                        "mismatches": bad}

# ---------------------------------------------------------------- write
outp = SCREEN / "verify_summary.json"
outp.write_text(json.dumps(out, indent=1, sort_keys=False))
print(json.dumps(out, indent=1)[:14000])
print("\nwrote", outp)
