import hashlib, re, sys, time, urllib.request
from msnlib_fetch import OUT, ROOT, log_row
def preview(url, name):
    assert re.fullmatch(r"https://zenodo\.org/records/\d+/preview/[^/]+\.zip", url), url
    req = urllib.request.Request(url, headers={"User-Agent": "MURU-outcome-blind-census/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read(20_000_001); st = r.status
    assert len(data) <= 20_000_000
    p = OUT / name; p.write_bytes(data)
    log_row({"url": url, "file": str(p.relative_to(ROOT)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
             "http_status": st, "note": "Zenodo HTML zip directory preview (file names and sizes only)",
             "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
if __name__ == "__main__":
    for key in sys.argv[2:]:
        try: preview(f"https://zenodo.org/records/{sys.argv[1]}/preview/{key}", f"zenodo_zip_listing_{sys.argv[1]}_{key[:-4]}.html")
        except BaseException as e: print("ERR", key, repr(e)[:200])
