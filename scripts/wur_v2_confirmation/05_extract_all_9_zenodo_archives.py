"""Map the frozen 2,402 required wells (2,690 sampled compounds, 2,000 scaffold
groups) to members of the nine official positive-mode Zenodo mzML archives, and
extract ONLY the required members (no wholesale expansion). Structural validity
checked; no <binary> array decoded. Files already correctly extracted/downloaded
(the 888 MCEDIV/TARGETMOL wells, the 98 MassIVE files) are left as-is, not
re-fetched -- this is transport-only, the frozen sample is unchanged.
"""
from __future__ import annotations
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
DL = REPO / "data/external/msnlib_mzml"
DL.mkdir(parents=True, exist_ok=True)
MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
ZENODO_DIR = Path("/Users/aryav/muru-msnlib/zenodo")
PROV_DIR = Path("/Users/aryav/muru-msnlib/provenance")

ZIPS = ["20220601_mzml_mce_bioactive_positive.zip", "20230404_mzml_pluskal_nih_positive.zip",
        "20231123_mzml_mce_scaffold_positive.zip", "20231124_mzml_otavapep_positive.zip",
        "mzml_20240405_pluskal_enammol_MSn_positive.zip", "mzml_20240408_pluskal_mcedrug_MSn_positive.zip",
        "mzml_20240502_pluskal_enamdisc_MSn_positive.zip", "mzml_20241113_pluskal_mcediv_20k_MSn_positive.zip",
        "mzml_20241120_pluskal_targetmolnphts_MSn_positive.zip"]

# census-recorded, independently re-verified byte sizes (STEP 3 provenance cross-check)
CENSUS_EXPECTED_BYTES = {
    "20220601_mzml_mce_bioactive_positive.zip": 2824678246,
    "20230404_mzml_pluskal_nih_positive.zip": 1082596118,
    "20231123_mzml_mce_scaffold_positive.zip": 957253214,
    "20231124_mzml_otavapep_positive.zip": 277249971,
    "mzml_20240405_pluskal_enammol_MSn_positive.zip": 1364509390,
    "mzml_20240408_pluskal_mcedrug_MSn_positive.zip": 661569255,
    "mzml_20240502_pluskal_enamdisc_MSn_positive.zip": 2724409468,
    "mzml_20241113_pluskal_mcediv_20k_MSn_positive.zip": 3148142909,
    "mzml_20241120_pluskal_targetmolnphts_MSn_positive.zip": 555117470,
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path, kind):
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if kind == "md5_named":   # "MD5 (name) = hash"
            m = re.match(r"MD5 \((.+?)\) = ([0-9a-f]+)", line)
            if m:
                out[m.group(1)] = m.group(2)
        elif kind == "sha_named":  # "hash  name"
            parts = line.split(None, 1)
            if len(parts) == 2:
                out[parts[1].strip()] = parts[0]
        elif kind == "size_ls":
            parts = line.split()
            if len(parts) >= 9:
                out[parts[-1]] = int(parts[4])
    return out


def main():
    provided_md5 = parse_manifest(PROV_DIR / "zenodo_md5.txt", "md5_named")
    provided_sha = parse_manifest(PROV_DIR / "zenodo_sha256.txt", "sha_named")
    provided_size = parse_manifest(PROV_DIR / "zenodo_sizes.txt", "size_ls")

    zip_records = []
    for z in ZIPS:
        p = ZENODO_DIR / z
        actual_size = p.stat().st_size
        actual_md5 = md5_file(p)
        actual_sha = sha256_file(p)
        rec = {
            "zip": z, "local_path": str(p), "bytes": actual_size,
            "bytes_expected_census": CENSUS_EXPECTED_BYTES.get(z),
            "bytes_match_census": actual_size == CENSUS_EXPECTED_BYTES.get(z),
            "md5_actual": actual_md5, "md5_provided": provided_md5.get(z), "md5_match": actual_md5 == provided_md5.get(z),
            "sha256_actual": actual_sha, "sha256_provided": provided_sha.get(z), "sha256_match": actual_sha == provided_sha.get(z),
            "bytes_provided": provided_size.get(z), "bytes_match_provided": actual_size == provided_size.get(z),
        }
        assert rec["bytes_match_census"], rec
        assert rec["md5_match"], rec
        assert rec["sha256_match"], rec
        assert rec["bytes_match_provided"], rec
        zip_records.append(rec)
        print(f"{z}: bytes={actual_size} md5_ok sha256_ok census_size_ok provided_size_ok", flush=True)

    unavail = pd.read_csv(MD / "unavailable_wells.csv")   # the 888 MCEDIV/TARGETMOL wells already extracted
    massive_manifest = pd.read_csv(REPO / "MSnLib_required_mzML_downloads.csv")
    all_required_wells = set(massive_manifest.unique_sample_id) | set(unavail.unique_sample_id)
    print(f"\ntotal required wells: {len(all_required_wells)}")

    already_on_disk = {p.stem for p in DL.glob("*.mzML")}
    # map every zip's mzML members once, across all 9 zips
    member_index = []   # (usid, zip, member_name)
    for z in ZIPS:
        zf = zipfile.ZipFile(ZENODO_DIR / z)
        for info in zf.infolist():
            if not info.filename.lower().endswith(".mzml"):
                continue
            fn = info.filename.rsplit("/", 1)[-1]
            m = re.search(r"(pluskal_.*?_id)(?=_|\.)", fn)
            if m and m.group(1) in all_required_wells:
                member_index.append({"usid": m.group(1), "zip": z, "member": info.filename, "fn": fn,
                                      "compress_size": info.compress_size, "file_size": info.file_size})
        zf.close()

    midx = pd.DataFrame(member_index)
    covered = set(midx.usid)
    missing = all_required_wells - covered
    print(f"wells found across all 9 zip central directories: {len(covered)}")
    if missing:
        print(f"MISSING from all 9 zips: {len(missing)} -- {sorted(missing)[:20]}")

    dupe_wells = midx.groupby("usid").size()
    print(f"wells with >1 candidate member across the 9 zips: {(dupe_wells > 1).sum()}")

    extracted, skipped_already_present = [], []
    for usid, g in midx.groupby("usid"):
        # already-present-on-disk check: does any candidate member's basename already exist and validate?
        existing = None
        for r in g.itertuples(index=False):
            local_name = Path(r.fn).stem
            if local_name in already_on_disk:
                existing = r
                break
        if existing is not None:
            skipped_already_present.append({"unique_sample_id": usid, "local_path": str(DL / existing.fn),
                                             "source_zip": existing.zip, "status": "already_present_on_disk"})
            continue
        if len(g) == 1:
            r = g.iloc[0]
        else:
            # deliberate tie-break (same rule already used for the MassIVE duplicate-acquisition
            # case): prefer a member WITHOUT a trailing resubmission-timestamp suffix; otherwise
            # take the lexicographically last (latest timestamp) candidate.
            g = g.assign(has_suffix=g.fn.str.contains(r"_\d{10,}(?:_MSn_positive)?\.mzML$", regex=True))
            r = g.sort_values(["has_suffix", "zip", "fn"], ascending=[True, True, True]).iloc[0]
        zf = zipfile.ZipFile(ZENODO_DIR / r.zip)
        data = zf.read(r.member)
        zf.close()
        if not (data[:200].lstrip().startswith(b"<?xml") and b"mzML" in data[:2000]):
            raise ValueError(f"{r.member} in {r.zip}: not well-formed mzML")
        local_path = DL / r.fn
        local_path.write_bytes(data)
        extracted.append({"unique_sample_id": usid, "source_zip": r.zip, "member": r.member,
                           "local_path": str(local_path.relative_to(REPO)), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest(), "n_candidates_in_zips": len(g),
                           "status": "extracted_verified_mzml"})

    print(f"newly extracted: {len(extracted)}; already present, skipped: {len(skipped_already_present)}; "
          f"total covered: {len(extracted) + len(skipped_already_present)} of {len(all_required_wells)}")

    out = {
        "zip_authentication": zip_records,
        "n_required_wells": len(all_required_wells),
        "n_covered_across_9_zips_central_directory": len(covered),
        "missing_wells": sorted(missing),
        "n_wells_with_duplicate_member_candidates": int((dupe_wells > 1).sum()),
        "n_newly_extracted": len(extracted), "n_already_present_skipped": len(skipped_already_present),
        "extracted": extracted, "already_present": skipped_already_present,
    }
    outp = REPO / "artifacts/wur_v2/external_msnlib/zenodo_9archive_transport_provenance.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {outp}")


if __name__ == "__main__":
    main()
