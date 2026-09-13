"""Extract ONLY the 888 required MCEDIV/TARGETMOL wells' mzML members from the
two local, checksum-verified Zenodo zip archives. Does not expand the zips
wholesale. Structural validity checked (mzML root), no <binary> array decoded."""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-accuracy-sprint-594932")
DL = REPO / "data/external/msnlib_mzml"
DL.mkdir(parents=True, exist_ok=True)
MD = Path("/private/tmp/claude-502/-Users-aryav-Documents-MURU-ConjectureLab-v1--claude-worktrees-muru-accuracy-sprint-594932/9eed949c-2e07-4b3c-a3d7-d2092a65dadc/scratchpad/msnlib_metadata")
ZENODO_DIR = Path("/Users/aryav/muru-msnlib/zenodo")

ZIP_EXPECTED = {
    "mzml_20241120_pluskal_targetmolnphts_MSn_positive.zip": {
        "md5": "f8238837af88f91729a211d5651f40d1",
        "sha256": "007173324b055ac6f66a273450f10e7f095baa8b6a6710dbc4f607b868553e4f",
    },
    "mzml_20241113_pluskal_mcediv_20k_MSn_positive.zip": {
        "md5": "bb0d2e16a721b920abf7615b39a02be9",
        "sha256": "89ad88f74096a59bb64ca14979eada2e35bd9c2c6eaf98c692690eea8005ab24",
    },
}


def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    unavail = pd.read_csv(MD / "unavailable_wells.csv")
    need = set(unavail.unique_sample_id)
    print(f"required MCEDIV/TARGETMOL wells: {len(need)}")

    prov_rows = []
    for zip_name, expected in ZIP_EXPECTED.items():
        zpath = ZENODO_DIR / zip_name
        md5 = md5_file(zpath)
        sha = sha256_file(zpath)
        assert md5 == expected["md5"], (zip_name, "md5 mismatch", md5, expected["md5"])
        assert sha == expected["sha256"], (zip_name, "sha256 mismatch", sha, expected["sha256"])
        print(f"{zip_name}: MD5/SHA256 verified")
        zf = zipfile.ZipFile(zpath)
        for info in zf.infolist():
            if not info.filename.lower().endswith(".mzml"):
                continue
            fn = info.filename.rsplit("/", 1)[-1]
            import re
            m = re.search(r"(pluskal_.*?_id)(?=_|\.)", fn)
            usid = m.group(1) if m else None
            if usid not in need:
                continue
            local_path = DL / fn
            data = zf.read(info)
            if not (data[:200].lstrip().startswith(b"<?xml") and b"mzML" in data[:2000]):
                raise ValueError(f"{fn}: extracted member is not a well-formed mzML header")
            local_path.write_bytes(data)
            prov_rows.append({
                "source": "Zenodo_local_archive", "official_dataset_doi": "10.5281/zenodo.15683784",
                "zip_file": zip_name, "zip_md5": md5, "zip_sha256": sha,
                "member_name": info.filename, "unique_sample_id": usid,
                "local_path": str(local_path.relative_to(REPO)),
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "compress_size_in_zip": info.compress_size, "status": "extracted_verified_mzml",
            })
        zf.close()

    got = {r["unique_sample_id"] for r in prov_rows}
    missing = need - got
    print(f"extracted {len(prov_rows)} members covering {len(got)} of {len(need)} required wells")
    if missing:
        print("MISSING:", sorted(missing)[:20])

    out = REPO / "artifacts/wur_v2/external_msnlib/zenodo_extraction_provenance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"zip_hashes_verified": ZIP_EXPECTED, "n_required": len(need),
                                "n_extracted": len(prov_rows), "n_wells_covered": len(got),
                                "missing_wells": sorted(missing), "members": prov_rows}, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
