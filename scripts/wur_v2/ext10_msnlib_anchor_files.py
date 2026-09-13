"""MSnLib anchors-first step 1 (identity only): anchor wells, preferred injection per well, Zenodo zip members,
and a range-request download of exactly those mzML members (member data only for anchor wells)."""
import importlib.util, json, struct, time, urllib.request, zlib, hashlib
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "data/external/msnlib_metadata"; DL = ROOT / "data/external/msnlib_mzml"; OUT = ROOT / "artifacts/wur_v2/external_msnlib"
OUT.mkdir(parents=True, exist_ok=True); DL.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("msnlib_census", ROOT / "scripts/wur_v2/census/msnlib/msnlib_census.py")
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
census = json.loads((ROOT / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
anchor_keys = set(census["anchors"]["design"]["v2_dev_five_rung"]["keys"])
design, _ = C.load_design(); files, _ = C.load_files()
for smi in design.smiles.dropna().unique():
    C.chem(smi)
for col in ["parse_ok", "raw_key", "parent_key", "parent_charge", "mh", "m_plus", "parent_formula"]:
    design[col] = [C.chem(s).get(col) if isinstance(s, str) else None for s in design.smiles]
design["key"] = design.parent_key
for col in ("mh", "m_plus", "parent_charge"):
    design[col] = pd.to_numeric(design[col], errors="coerce")
iso = {}
for usid, g in design.groupby("unique_sample_id"):
    ions = [(r.key, r.parent_formula, np.array([r.mh - C.PROTON + s for s in C.SHIFTS_OTHER.values()]) if r.parent_charge == 0 and np.isfinite(r.mh) else np.array([r.m_plus]))
            for r in g.itertuples() if isinstance(r.key, str)]
    for r in g.itertuples():
        if not isinstance(r.key, str) or not np.isfinite(r.mh):
            iso[r.Index] = True; continue
        other = [x for x in ions if x[0] != r.key]
        iso[r.Index] = bool(any(np.any(np.abs(x[2] - r.mh) <= C.ISO_TOL) for x in other) or any(x[1] == r.parent_formula for x in other))
design["iso_conflict"] = pd.Series(iso)
an = design[design.key.isin(anchor_keys) & ~design.iso_conflict & (design.parent_charge == 0)].copy()
zf = files[(files.polarity == "positive") & (files.format == "mzML(zip member)") & files.usid.isin(set(an.unique_sample_id))].copy()
zf["pref"] = zf.variant.eq("100AGC_60000Res_").astype(int)
one = zf.sort_values(["usid", "pref", "run_date"], ascending=[True, False, False]).drop_duplicates("usid")
an = an.merge(one[["usid", "path", "fn", "bytes", "collection"]], left_on="unique_sample_id", right_on="usid", how="inner")
print("anchor keys", an.key.nunique(), "wells", an.usid.nunique(), "GB", round(one[one.usid.isin(an.usid)].bytes.sum() / 1e9, 3))
an[["key", "library", "unique_sample_id", "smiles", "mh", "fn", "path", "collection"]].to_csv(OUT / "anchor_wells.csv", index=False)

def rng(url, a, b, tries=6):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MURU-v2/1.0", "Range": f"bytes={a}-{b}"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except Exception as e:
            time.sleep(5 * (t + 1)); err = e
    raise err

def members_with_offsets(zipname):
    cd = (MD / f"zenodo_zip_central_directory_15683784_{zipname[:-4]}.bin").read_bytes()
    out, p = {}, 0
    while p < len(cd):
        method = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28]); nlen, elen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        off = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace"); extra = cd[p + 46 + nlen:p + 46 + nlen + elen]; q = 0
        while q + 4 <= len(extra):
            hid, hl = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals = extra[q + 4:q + 4 + hl]; k = 0
                if usize == 0xFFFFFFFF: usize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF: csize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if off == 0xFFFFFFFF: off = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
            q += 4 + hl
        out[name] = (off, csize, usize, method)
        p += 46 + nlen + elen + clen
    return out

from concurrent.futures import ThreadPoolExecutor
jobs = []
for zipname, g in one[one.usid.isin(an.usid)].groupby("collection"):
    mem = members_with_offsets(zipname); url = f"https://zenodo.org/api/records/15683784/files/{zipname}/content"
    for r in g.itertuples():
        name = r.path.split("!", 1)[1]
        jobs.append((zipname, url, name, mem[name]))

def fetch(job):
    zipname, url, name, (off, csize, usize, method) = job
    dest = DL / Path(name).name
    if dest.exists() and dest.stat().st_size == usize:
        return {"zip": zipname, "member": name, "bytes": usize, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "cached": True}
    lh = rng(url, off, off + 29); nlen, elen = struct.unpack("<HH", lh[26:30])
    data = rng(url, off + 30 + nlen + elen, off + 30 + nlen + elen + csize - 1)
    raw = zlib.decompress(data, -15) if method == 8 else data
    assert len(raw) == usize, (name, len(raw), usize)
    tmp = dest.with_suffix(".part"); tmp.write_bytes(raw); tmp.rename(dest)
    return {"zip": zipname, "member": name, "bytes_compressed": csize, "bytes": usize, "sha256": hashlib.sha256(raw).hexdigest()}

log = []
with ThreadPoolExecutor(max_workers=4) as ex:
    for i, rec in enumerate(ex.map(fetch, jobs)):
        log.append(rec); print(i + 1, rec["member"], flush=True)
(OUT / "anchor_download_log.json").write_text(json.dumps(log, indent=1) + "\n")
print("downloaded", len(log))
