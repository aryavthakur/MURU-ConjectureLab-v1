"""C05 screen (task S5): fetch ONLY the SupplementaryInformation.pdf member (methods text, SI1-SI7) of the AnnoMe paper
supplementary zip (Bioinformatics Advances 2026, vbag111; PMC13192349) by HTTP range reads, to read the LC-HRMS/MS
acquisition settings (instrument, collision energy mode) of the BOKU in-house library. No spectra file is requested.
The PDF is stored under screen/c05_boku_flavonoid/downloads/ and registered in downloads_register.jsonl.
"""
import datetime as dt, hashlib, json, struct, urllib.request, zlib
from pathlib import Path
URL = "https://pmc-oa-opendata.s3.amazonaws.com/PMC13192349.1/vbag111_supplementary_data.zip"
MEMBER = "SupplementaryInformation.pdf"
W = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
OUT = W / "artifacts/ce_interface_adjudication/screen/c05_boku_flavonoid/downloads"
REG = W / "artifacts/ce_interface_adjudication/downloads_register.jsonl"
tr, h = [], hashlib.sha256()
def rng(a, b):
    with urllib.request.urlopen(urllib.request.Request(URL, headers={"Range": f"bytes={a}-{b}"})) as r:
        assert r.status == 206; d = r.read()
    tr.append({"range": [a, b], "n_bytes": len(d)}); h.update(d); return d
tot = int(urllib.request.urlopen(urllib.request.Request(URL, method="HEAD")).headers["Content-Length"])
tail = rng(max(0, tot - 65557), tot - 1); i = tail.rfind(b"PK\x05\x06")
_, _, _, _, n, cs, co, _ = struct.unpack("<IHHHHIIH", tail[i:i + 22]); cd = rng(co, co + cs - 1); p = 0; mem = []
for _ in range(n):
    f = struct.unpack("<IHHHHHHIIIHHHHHII", cd[p:p + 46]); nm = cd[p + 46:p + 46 + f[10]].decode()
    mem.append({"name": nm, "method": f[4], "crc32": f[7], "compressed_size": f[8], "uncompressed_size": f[9], "local_header_offset": f[16]})
    p += 46 + f[10] + f[11] + f[12]
m = [x for x in mem if x["name"] == MEMBER][0]
lh = rng(m["local_header_offset"], m["local_header_offset"] + 29); fnl, exl = struct.unpack("<HH", lh[26:30])
s = m["local_header_offset"] + 30 + fnl + exl; comp = rng(s, s + m["compressed_size"] - 1)
data = zlib.decompress(comp, -15) if m["method"] == 8 else comp
assert zlib.crc32(data) & 0xFFFFFFFF == m["crc32"]
dest = OUT / "annome_vbag111_SupplementaryInformation.pdf"; dest.write_bytes(data)
(OUT / "annome_supp_zip_central_directory.json").write_text(json.dumps({"source_url": URL, "zip_size_bytes": tot, "members": mem}, indent=1))
rec = {"fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "task": "S5-C05",
       "name": "vbag111_supplementary_data.zip (AnnoMe, PMC13192349; partial HTTP range reads: EOCD, central directory, SupplementaryInformation.pdf member only; SupplementaryTables.pdf never read)",
       "source_url": URL, "source_file_size_bytes": tot, "n_ranges": len(tr), "ranges": tr,
       "size_bytes": sum(t["n_bytes"] for t in tr), "sha256": h.hexdigest(),
       "sha256_definition": "sha256 over all transferred bytes in transfer order",
       "members_extracted": [{"member": MEMBER, "stored_as": str(dest.relative_to(W)), "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}],
       "script": "scripts/ce_interface_adjudication/screen_c05_boku_flavonoid_fetch_annome_si.py"}
with REG.open("a") as fh: fh.write(json.dumps(rec) + "\n")
print(json.dumps(rec, indent=1))
