"""S1 screen C01 (MassBank Eawag EQ post-2023.11 HCD NCE ladders), step 1: git tree table.

Metadata only. Reads commit and tree objects of a blobless partial clone of MassBank-data
(git clone --bare --filter=blob:none, registered by task D2); no blob (record content, which includes PK$PEAK) is
ever read. For every Eawag/MSBNK-Eawag-EQ*.txt path present at any of the listed refs it writes the blob SHA per ref,
the first ref where the path appears, and the UCHEM compound id and spectrum index parsed from the file name.

Output: artifacts/ce_interface_adjudication/screen/c01_eawag_eq/eawag_eq_tree_blobs.csv
"""
import argparse
import re
import subprocess
from pathlib import Path

import pandas as pd

REFS = ["2023.09", "2023.11", "2024.06", "2024.11", "2025.05.1", "2025.10", "2026.03", "dev"]
NAME = re.compile(r"^MSBNK-Eawag-EQ(\d+)(_\d+)?\.txt$")


def ls_tree(repo, ref):
    out = subprocess.run(["git", "-C", repo, "ls-tree", ref, "Eawag/"], capture_output=True, text=True, check=True).stdout
    rows = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        _, typ, sha = meta.split()
        fn = path.split("/")[-1]
        if typ == "blob" and NAME.match(fn):
            rows[fn] = sha
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    commits = {}
    per = {}
    for r in REFS:
        commits[r] = subprocess.run(["git", "-C", a.repo, "rev-parse", r + "^{commit}"], capture_output=True, text=True,
                                    check=True).stdout.strip()
        per[r] = ls_tree(a.repo, r)
    files = sorted(set().union(*[set(v) for v in per.values()]))
    recs = []
    for fn in files:
        digits = NAME.match(fn).group(1)
        d = {"file": fn, "n_digits": len(digits), "uchem_id": int(digits[:-2]), "spec_idx": int(digits[-2:]),
             "suffix": NAME.match(fn).group(2) or ""}
        for r in REFS:
            d["blob_" + r] = per[r].get(fn)
        d["first_ref"] = next((r for r in REFS if per[r].get(fn)), None)
        d["last_ref"] = [r for r in REFS if per[r].get(fn)][-1]
        recs.append(d)
    df = pd.DataFrame(recs)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print("commits", commits)
    print("files", len(df))
    print(df.groupby(["first_ref", "n_digits"]).size())
    print("present at dev", df["blob_dev"].notna().sum(), "removed before dev", df["blob_dev"].isna().sum())


if __name__ == "__main__":
    main()
