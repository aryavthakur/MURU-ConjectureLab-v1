"""Range-fetch ONLY the Thrift footer of a remote parquet file (no data pages) and report its schema.
Column statistics in the footer are never printed or saved in parsed form."""
import hashlib, json, struct, time, urllib.request, io, sys
from msnlib_fetch import OUT, ROOT, log_row
url, name = sys.argv[1], sys.argv[2]
UA = {"User-Agent": "MURU-outcome-blind-census/1.0"}
def rng(a, b):
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={a}-{b}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        cr = r.headers.get("Content-Range"); data = r.read(8_000_001)
    return data, cr
tail, cr = rng(0, 0)
total = int(cr.split("/")[1])
tail8, _ = rng(total - 8, total - 1)
assert tail8[4:] == b"PAR1", tail8
flen = struct.unpack("<I", tail8[:4])[0]
assert flen < 8_000_000, flen
footer, cr2 = rng(total - 8 - flen, total - 1)
assert len(footer) == flen + 8
p = OUT / name
p.write_bytes(footer)
log_row({"url": url, "file": str(p.relative_to(ROOT)), "bytes": len(footer), "sha256": hashlib.sha256(footer).hexdigest(),
         "http_status": 206, "range": f"bytes={total-8-flen}-{total-1}", "remote_total_bytes": total,
         "note": "parquet footer only (schema + row-group metadata); no data pages fetched",
         "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
import pyarrow.parquet as pq
buf = io.BytesIO(b"PAR1" + footer)  # footer-only reader: metadata parse needs only trailing bytes
md = pq.read_metadata(buf)
print("rows", md.num_rows, "row_groups", md.num_row_groups, "columns", md.num_columns, "created_by", md.created_by)
sch = md.schema.to_arrow_schema()
for f in sch: print("  ", f.name, f.type)
kv = md.metadata or {}
print("kv keys", list(kv.keys()))
