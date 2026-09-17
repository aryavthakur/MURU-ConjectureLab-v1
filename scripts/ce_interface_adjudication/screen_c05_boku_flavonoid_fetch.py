"""C05 screen (CE interface adjudication, task S5): metadata-only fetch of the supplementary TABLES member of the
Metabolites 2025, 15(9), 616 supplementary zip (PMC12471768), by HTTP range reads.

Policy: only the zip end-of-central-directory, the central directory (file listing) and the one member whose name
identifies it as the supplementary tables file (Tables S1 and S2) are transferred. The figures member (S2, Figures
S1-S43) and the MZmine batch member (S1) are never transferred. No spectra file of the Zenodo 16762591 record
(in-house_MSMS_library.mgf) is ever requested.

Usage:
  python3 screen_c05_boku_flavonoid_fetch.py list      # EOCD + central directory only
  python3 screen_c05_boku_flavonoid_fetch.py tables    # plus the tables member only
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

URL = "https://pmc-oa-opendata.s3.amazonaws.com/PMC12471768.1/metabolites-15-00616-s001.zip"
W = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = W / "artifacts/ce_interface_adjudication/screen/c05_boku_flavonoid/downloads"
REG = W / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
SCRIPT = "scripts/ce_interface_adjudication/screen_c05_boku_flavonoid_fetch.py"

transfers: list[dict] = []
hasher = hashlib.sha256()


def rng(a: int, b: int) -> bytes:
    req = urllib.request.Request(URL, headers={"Range": f"bytes={a}-{b}"})
    with urllib.request.urlopen(req) as r:
        assert r.status == 206, r.status
        data = r.read()
    transfers.append({"range": [a, b], "n_bytes": len(data)})
    hasher.update(data)
    return data


def size() -> int:
    req = urllib.request.Request(URL, method="HEAD")
    with urllib.request.urlopen(req) as r:
        return int(r.headers["Content-Length"])


def central_directory(total: int):
    tail = rng(max(0, total - 65557), total - 1)
    i = tail.rfind(b"PK\x05\x06")
    assert i >= 0
    _, _, _, _, n, cd_size, cd_off, _ = struct.unpack("<IHHHHIIH", tail[i:i + 22])
    cd = rng(cd_off, cd_off + cd_size - 1)
    members, p = [], 0
    for _ in range(n):
        sig, _, _, flag, meth, _, _, crc, csz, usz, fnl, exl, cml, _, _, _, loff = struct.unpack(
            "<IHHHHHHIIIHHHHHII", cd[p:p + 46])
        assert sig == 0x02014B50
        name = cd[p + 46:p + 46 + fnl].decode("utf-8", "replace")
        members.append({"name": name, "method": meth, "crc32": crc, "compressed_size": csz,
                        "uncompressed_size": usz, "local_header_offset": loff})
        p += 46 + fnl + exl + cml
    return members


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    OUT.mkdir(parents=True, exist_ok=True)
    total = size()
    members = central_directory(total)
    listing = {"source_url": URL, "zip_size_bytes": total, "members": members}
    (OUT / "supp_zip_central_directory.json").write_text(json.dumps(listing, indent=1))
    print(json.dumps(listing, indent=1))
    fetched = []
    if mode == "tables":
        tab = [m for m in members if m["name"].endswith("Supplementary Material File S3.xlsx")]
        tab = [m for m in tab if not m["name"].lower().endswith((".mgf", ".msp", ".mzml", ".hdf5", ".pdf"))]
        assert len(tab) >= 1, "no tables member identified; stop"
        for m in tab:
            assert m["uncompressed_size"] < 50_000_000
            lh = rng(m["local_header_offset"], m["local_header_offset"] + 29)
            fnl, exl = struct.unpack("<HH", lh[26:30])
            start = m["local_header_offset"] + 30 + fnl + exl
            comp = rng(start, start + m["compressed_size"] - 1)
            data = zlib.decompress(comp, -15) if m["method"] == 8 else comp
            assert zlib.crc32(data) & 0xFFFFFFFF == m["crc32"]
            # Minimisation: the workbook is NOT persisted. Only its inner part listing, its sheet names and the one
            # sheet whose name identifies Table S1 (reference standards) are written. Table S2 (plant-extract
            # feature list) is never parsed or stored.
            import io, re, zipfile
            import pandas as pd
            zf = zipfile.ZipFile(io.BytesIO(data))
            inner = [{"name": i.filename, "size": i.file_size} for i in zf.infolist()]
            wb = zf.read("xl/workbook.xml").decode("utf-8", "replace")
            sheets = re.findall(r'<sheet [^>]*name="([^"]+)"', wb)
            (OUT / "supp_S3_xlsx_inner_listing.json").write_text(json.dumps(
                {"member": m["name"], "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                 "inner_parts": inner, "sheet_names": sheets}, indent=1))
            print("sheets", sheets)
            pick = [s for s in sheets if re.search(r"S1\b|S1$|standard", s, re.I) and not re.search(r"S2", s)]
            if len(pick) != 1:
                print("Table S1 sheet not uniquely identified by name; stop without parsing", sheets)
            else:
                t1 = pd.read_excel(io.BytesIO(data), sheet_name=pick[0], header=None, dtype=str)
                dest = OUT / "supp_S3_table_S1_raw.csv"
                t1.to_csv(dest, index=False, header=False)
                print("stored", dest, t1.shape)
                fetched.append({"member": m["name"], "sheet": pick[0], "stored_as": str(dest.relative_to(W)),
                                "workbook_size_bytes": len(data),
                                "workbook_sha256": hashlib.sha256(data).hexdigest(),
                                "stored_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                                "workbook_persisted": False})
    rec = {
        "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "task": "S5-C05",
        "name": "metabolites-15-00616-s001.zip (PMC12471768 supplementary; partial HTTP range reads: EOCD, central "
                "directory" + (", tables member only" if fetched else "") + "; figures and MZmine members never read)",
        "source_url": URL,
        "source_file_size_bytes": total,
        "n_ranges": len(transfers),
        "ranges": transfers,
        "size_bytes": sum(t["n_bytes"] for t in transfers),
        "sha256": hasher.hexdigest(),
        "sha256_definition": "sha256 over all transferred bytes in transfer order",
        "members_extracted": fetched,
        "script": SCRIPT,
    }
    with REG.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
