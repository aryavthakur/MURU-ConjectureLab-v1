"""Extract the 561 required anchor wells' mzML members from the nine authenticated
local Zenodo archives (already-exposed calibration data -- re-decoding them for
parser preflight creates no new outcome exposure). Same deliberate tie-break as
the validation-population extraction (prefer production/no-resubmission-suffix
member)."""
from __future__ import annotations
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
DL = REPO / "data/external/msnlib_mzml"
MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
ZENODO_DIR = Path("/Users/aryav/muru-msnlib/zenodo")

ZIPS = ["20220601_mzml_mce_bioactive_positive.zip", "20230404_mzml_pluskal_nih_positive.zip",
        "20231123_mzml_mce_scaffold_positive.zip", "20231124_mzml_otavapep_positive.zip",
        "mzml_20240405_pluskal_enammol_MSn_positive.zip", "mzml_20240408_pluskal_mcedrug_MSn_positive.zip",
        "mzml_20240502_pluskal_enamdisc_MSn_positive.zip", "mzml_20241113_pluskal_mcediv_20k_MSn_positive.zip",
        "mzml_20241120_pluskal_targetmolnphts_MSn_positive.zip"]


def main():
    anchor_manifest = json.loads((MD / "anchor_file_manifest.json").read_text())
    required_wells = set(e["unique_sample_id"] for e in anchor_manifest["avail_massive"]) | \
                     set(e["unique_sample_id"] for e in anchor_manifest["avail_zenodo"])
    print(f"required anchor wells: {len(required_wells)}")

    already_on_disk = {p.stem for p in DL.glob("*.mzML")}

    member_index = []
    for z in ZIPS:
        zf = zipfile.ZipFile(ZENODO_DIR / z)
        for info in zf.infolist():
            if not info.filename.lower().endswith(".mzml"):
                continue
            fn = info.filename.rsplit("/", 1)[-1]
            m = re.search(r"(pluskal_.*?_id)(?=_|\.)", fn)
            if m and m.group(1) in required_wells:
                member_index.append({"usid": m.group(1), "zip": z, "member": info.filename, "fn": fn})
        zf.close()

    midx = pd.DataFrame(member_index)
    covered = set(midx.usid)
    missing = required_wells - covered
    print(f"covered: {len(covered)}, missing: {len(missing)}")

    fn_base = midx.fn
    midx["run_date"] = fn_base.str.extract(r"^(\d{8})_")[0]
    midx["variant"] = fn_base.str.extract(r"^\d{8}_(.*?)\d?pluskal_")[0].fillna("")
    midx["pref"] = midx.variant.eq("100AGC_60000Res_")
    midx["has_suffix"] = fn_base.str.contains(r"_\d{10,}(?:_MSn_positive)?\.mzML$", regex=True)

    n_extracted, n_present = 0, 0
    for usid, g in midx.groupby("usid"):
        local_name = None
        for r in g.itertuples(index=False):
            if Path(r.fn).stem in already_on_disk:
                local_name = r.fn
                break
        if local_name is not None:
            n_present += 1
            continue
        r = g.sort_values(["pref", "run_date", "has_suffix", "fn"], ascending=[False, False, True, True]).iloc[0]
        zf = zipfile.ZipFile(ZENODO_DIR / r.zip)
        data = zf.read(r.member)
        zf.close()
        if not (data[:200].lstrip().startswith(b"<?xml") and b"mzML" in data[:2000]):
            raise ValueError(f"{r.member}: not well-formed mzML")
        (DL / r.fn).write_bytes(data)
        n_extracted += 1

    print(f"newly extracted: {n_extracted}, already present: {n_present}, total: {n_extracted + n_present} of {len(required_wells)}")
    if missing:
        print("MISSING anchor wells:", sorted(missing))


if __name__ == "__main__":
    main()
