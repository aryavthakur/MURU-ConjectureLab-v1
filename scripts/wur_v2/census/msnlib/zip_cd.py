"""Range-fetch only the ZIP central directory (file names, sizes; no member data) of a remote Zenodo zip."""
import hashlib, json, struct, sys, time, urllib.request
try:
    from msnlib_fetch import OUT, ROOT, log_row
except Exception:
    OUT = ROOT = log_row = None
UA = {"User-Agent": "MURU-outcome-blind-census/1.0"}
def rng(url, a, b):
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={a}-{b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read(), r.headers.get("Content-Range")
def central_directory(rec, key):
    url = f"https://zenodo.org/api/records/{rec}/files/{key}/content"
    _, cr = rng(url, 0, 0); total = int(cr.split("/")[1])
    tail, _ = rng(url, max(0, total - 70000), total - 1)
    i = tail.rfind(b"PK\x05\x06"); assert i >= 0
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    n_entries = struct.unpack("<H", tail[i + 10:i + 12])[0]
    j = tail.rfind(b"PK\x06\x06")
    if j >= 0:
        n_entries, cd_size, cd_off = struct.unpack("<QQQ", tail[j + 32:j + 56])
    assert cd_size < 30_000_000
    cd, _ = rng(url, cd_off, cd_off + cd_size - 1)
    assert len(cd) == cd_size
    name = f"zenodo_zip_central_directory_{rec}_{key[:-4]}.bin"
    (OUT / name).write_bytes(cd)
    log_row({"url": url, "file": f"data/external/msnlib_metadata/{name}", "bytes": len(cd), "sha256": hashlib.sha256(cd).hexdigest(),
             "http_status": 206, "range": f"bytes={cd_off}-{cd_off+cd_size-1} (plus a 70 kB tail read to locate it)", "remote_total_bytes": total,
             "note": "ZIP central directory only (member names and sizes); no member data fetched",
             "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    out, p = [], 0
    while p < len(cd):
        assert cd[p:p + 4] == b"PK\x01\x02"
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, elen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        fn = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + elen]
        q = 0
        while q + 4 <= len(extra):
            hid, hl = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals = extra[q + 4:q + 4 + hl]; k = 0
                if usize == 0xFFFFFFFF: usize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF: csize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
            q += 4 + hl
        out.append({"name": fn, "compressed": csize, "uncompressed": usize})
        p += 46 + nlen + elen + clen
    assert len(out) == n_entries, (len(out), n_entries)
    json.dump({"record": rec, "zip": key, "zip_bytes": total, "members": out}, open(OUT / (name[:-4] + ".json"), "w"), indent=0)
    return out
if __name__ == "__main__":
    rec = sys.argv[1]
    for key in sys.argv[2:]:
        m = central_directory(rec, key); print(key, len(m), sum(x["compressed"] for x in m) / 1e9, sum(x["uncompressed"] for x in m) / 1e9)
