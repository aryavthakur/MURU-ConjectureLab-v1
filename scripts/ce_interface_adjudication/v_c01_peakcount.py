"""TASK V: header-only PK$NUM_PEAK census for the C01 primary-tier records.

Fetches each MassBank record from the public repo and KEEPS ONLY header fields
(ACCESSION, RECORD_TITLE, COLLISION_ENERGY, PRECURSOR_TYPE, MASS_RANGE_M/Z, PK$NUM_PEAK, PK$SPLASH).
Every peak line is discarded in memory and never written. PK$NUM_PEAK is a record header count,
not peak data.
"""
from __future__ import annotations

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

WT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
REC = WT / "artifacts/ce_interface_adjudication/screen/c01_eawag_eq/c01_record_metadata.csv.gz"

cand = pd.read_csv("/tmp/v_c01_cand.csv")
devpop_sg = set(pd.read_csv(WT / "artifacts/wur_v2/data/compounds.csv",
                            usecols=["scaffold_group"])["scaffold_group"].dropna())
key_clean = ~(cand["in_msg15"] | cand["in_registry"] | cand["in_pr7"] | cand["in_comparator"])
prim = key_clean & ~(cand["sg"].isin(devpop_sg) | cand["sg_in_pr7"] | cand["sg_in_comparator"])
prim_keys = set(cand.loc[prim, "key"]) - {"PHXHZCIAPNNPTQ"}          # drop the tautomer leak
cons = key_clean & ~(cand["sg_in_registry"] | cand["sg_in_pr7"] | cand["sg_in_comparator"])
cons_keys = set(cand.loc[cons, "key"]) - {"PHXHZCIAPNNPTQ"}
print("primary keys", len(prim_keys), "conservative keys", len(cons_keys))

rec = pd.read_csv(REC)
tgt = rec[(rec["parent_key"].isin(prim_keys)) & (rec["precursor_type"] == "[M+H]+")
          & (rec["ion_mode"] == "POSITIVE")].copy()
print("primary-tier [M+H]+ records to fetch:", len(tgt))

KEEP = re.compile(r"^(ACCESSION|RECORD_TITLE|PK\$NUM_PEAK|PK\$SPLASH):|"
                  r"^AC\$MASS_SPECTROMETRY: (COLLISION_ENERGY|MASS_RANGE_M/Z)|"
                  r"^MS\$FOCUSED_ION: (PRECURSOR_TYPE|PRECURSOR_M/Z|BASE_PEAK)")


def fetch(fn: str):
    p = subprocess.run(["gh", "api", f"repos/MassBank/MassBank-data/contents/Eawag/{fn}?ref=dev",
                        "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return {"file": fn, "error": p.stderr.strip()[:120]}
    d = {"file": fn}
    for line in p.stdout.splitlines():          # peak lines are matched by nothing and dropped here
        if KEEP.match(line):
            k, _, v = line.partition(": ")
            d[k.strip()] = v.strip()
    del p                                        # nothing containing peaks survives this function
    return d


with ThreadPoolExecutor(max_workers=8) as ex:
    rows = list(ex.map(fetch, list(tgt["file"])))

df = pd.DataFrame(rows)
df.to_csv("/tmp/v_c01_peakcounts.csv", index=False)
print("errors:", int(df.get("error", pd.Series(dtype=object)).notna().sum()) if "error" in df else 0)
df["num_peak"] = pd.to_numeric(df.get("PK$NUM_PEAK"), errors="coerce")
df["nce"] = pd.to_numeric(df.get("AC$MASS_SPECTROMETRY").astype(str).str.extract(r"^(\d+)")[0]
                          if "AC$MASS_SPECTROMETRY" in df else None, errors="coerce")
# COLLISION_ENERGY lands under the AC$MASS_SPECTROMETRY key only if the partition collapsed; redo properly
ce_col = [c for c in df.columns if "COLLISION" in c]
print("columns:", list(df.columns))
m = tgt[["file", "parent_key", "nce", "name"]].merge(df[["file", "num_peak"]], on="file", how="left")
out = {
    "records_fetched": int(len(df)),
    "records_with_num_peak": int(m["num_peak"].notna().sum()),
    "num_peak_describe": {k: float(v) for k, v in m["num_peak"].describe().items()},
    "num_peak_le_1": int((m["num_peak"] <= 1).sum()),
    "num_peak_le_2": int((m["num_peak"] <= 2).sum()),
    "num_peak_le_3": int((m["num_peak"] <= 3).sum()),
    "num_peak_ge_5": int((m["num_peak"] >= 5).sum()),
    "by_nce": m.groupby("nce")["num_peak"].agg(["count", "median", "mean",
                                                lambda s: int((s <= 1).sum()),
                                                lambda s: int((s <= 2).sum())]).rename(
        columns={"<lambda_0>": "n_le_1", "<lambda_1>": "n_le_2"}).round(2).to_dict("index"),
}
# per-compound usable rungs (>=3 peaks) inside 15-90
u = m[(m["nce"] >= 15) & (m["nce"] <= 90)]
per = u.groupby("parent_key")["num_peak"].agg(n_rungs="count",
                                              n_rungs_ge3peaks=lambda s: int((s >= 3).sum()),
                                              n_rungs_ge5peaks=lambda s: int((s >= 5).sum()))
out["per_compound_rungs_15_90"] = {
    "n_compounds": int(len(per)),
    "median_rungs": float(per["n_rungs"].median()),
    "median_rungs_ge3peaks": float(per["n_rungs_ge3peaks"].median()),
    "median_rungs_ge5peaks": float(per["n_rungs_ge5peaks"].median()),
    "compounds_with_0_rungs_ge3peaks": int((per["n_rungs_ge3peaks"] == 0).sum()),
    "compounds_with_lt3_rungs_ge3peaks": int((per["n_rungs_ge3peaks"] < 3).sum()),
}
# conservative tier subset
cm = m[m["parent_key"].isin(cons_keys)]
cu = cm[(cm["nce"] >= 15) & (cm["nce"] <= 90)]
cper = cu.groupby("parent_key")["num_peak"].agg(n_rungs="count",
                                                n_ge3=lambda s: int((s >= 3).sum()))
out["conservative_tier"] = {
    "n_compounds": int(len(cper)), "records": int(len(cm)),
    "num_peak_le_1": int((cm["num_peak"] <= 1).sum()),
    "median_rungs_ge3peaks_15_90": float(cper["n_ge3"].median()),
    "compounds_with_lt3_rungs_ge3peaks": int((cper["n_ge3"] < 3).sum()),
}
print(json.dumps(out, indent=1, default=str))
Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-v2-stability-study-6537d5/c50bb7b0-c2aa-4e0b-bd11-bc34c1ea3cbc/scratchpad/vscreen/v_c01_peakcounts.json").write_text(
    json.dumps(out, indent=1, default=str))
