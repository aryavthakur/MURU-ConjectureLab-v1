#!/usr/bin/env python3
"""Range-read selected mzML members from the nine frozen Zenodo ZIP sources.

This avoids downloading multi-gigabyte ZIP files. Each extracted member is checked
against the frozen allowlist SHA-256 before XML metadata are parsed. Raw spectra are
never written to the repository; use --cache-dir outside the worktree.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, struct, time, urllib.request, urllib.error, zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
RECORD = 15683784
ALLOW = REPO / "artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv"
DESIGN = REPO / "src/muru/wur_v2/msnlib_design.py"
UA = "MURU-Phase6-Evidence-Audit/1.0 (scientific metadata verification)"

def http_range(url: str, a: int, b: int, tries: int = 10) -> tuple[bytes, str | None]:
    req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}", "User-Agent": UA})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
                if r.status != 206:
                    raise RuntimeError(f"range request returned {r.status}, expected 206")
                return data, r.headers.get("Content-Range")
        except Exception as exc:
            if attempt == tries - 1: raise
            retry_after=0
            if isinstance(exc,urllib.error.HTTPError):
                try: retry_after=float(exc.headers.get('Retry-After','0'))
                except (TypeError,ValueError): retry_after=0
            # Zenodo throttles bursts of Range requests. Back off sufficiently
            # and preserve the exception for an auditable failure if it persists.
            time.sleep(max(retry_after,min(30,2 ** min(attempt,5))))
    raise RuntimeError("unreachable")

def parse_zip_central_directory(url: str) -> tuple[int, list[dict]]:
    _, cr = http_range(url, 0, 0)
    if not cr or "/" not in cr: raise RuntimeError("missing Content-Range total")
    total = int(cr.rsplit("/", 1)[1])
    tail_start = max(0, total - 70000)
    tail, _ = http_range(url, tail_start, total - 1)
    eocd = tail.rfind(b"PK\x05\x06")
    if eocd < 0: raise RuntimeError("ZIP EOCD not found in final 70 kB")
    entries = struct.unpack_from("<H", tail, eocd + 10)[0]
    cd_size = struct.unpack_from("<I", tail, eocd + 12)[0]
    cd_off = struct.unpack_from("<I", tail, eocd + 16)[0]
    if entries == 0xFFFF or cd_size == 0xFFFFFFFF or cd_off == 0xFFFFFFFF:
        loc = tail.rfind(b"PK\x06\x07")
        if loc < 0: raise RuntimeError("ZIP64 EOCD locator missing")
        zip64_off = struct.unpack_from("<Q", tail, loc + 8)[0]
        z64, _ = http_range(url, zip64_off, zip64_off + 55)
        if z64[:4] != b"PK\x06\x06": raise RuntimeError("invalid ZIP64 EOCD")
        entries = struct.unpack_from("<Q", z64, 32)[0]
        cd_size = struct.unpack_from("<Q", z64, 40)[0]
        cd_off = struct.unpack_from("<Q", z64, 48)[0]
    if cd_size > 100_000_000: raise RuntimeError(f"unexpected central directory size {cd_size}")
    cd, _ = http_range(url, cd_off, cd_off + cd_size - 1)
    members=[]; pos=0
    while pos < len(cd):
        if cd[pos:pos+4] != b"PK\x01\x02": raise RuntimeError(f"invalid central entry at {pos}")
        csize, usize = struct.unpack_from("<II", cd, pos+20)
        nlen, elen, clen = struct.unpack_from("<HHH", cd, pos+28)
        local_off = struct.unpack_from("<I", cd, pos+42)[0]
        name = cd[pos+46:pos+46+nlen].decode("utf-8", "replace")
        extra = cd[pos+46+nlen:pos+46+nlen+elen]
        q=0
        while q+4 <= len(extra):
            hid, hl = struct.unpack_from("<HH", extra, q)
            dat=extra[q+4:q+4+hl]
            if hid == 1:
                k=0
                if usize == 0xFFFFFFFF: usize=struct.unpack_from("<Q",dat,k)[0]; k+=8
                if csize == 0xFFFFFFFF: csize=struct.unpack_from("<Q",dat,k)[0]; k+=8
                if local_off == 0xFFFFFFFF: local_off=struct.unpack_from("<Q",dat,k)[0]; k+=8
            q += 4+hl
        method=struct.unpack_from("<H",cd,pos+10)[0]
        crc=struct.unpack_from("<I",cd,pos+16)[0]
        members.append({"name":name,"compressed":csize,"uncompressed":usize,"offset":local_off,"method":method,"crc32":crc})
        pos += 46+nlen+elen+clen
    if len(members) != entries: raise RuntimeError(f"central directory entries {len(members)} != EOCD {entries}")
    return total,members

def extract_member_range(url: str, rec: dict, output: Path) -> None:
    header,_=http_range(url,rec["offset"],rec["offset"]+29)
    if header[:4] != b"PK\x03\x04": raise RuntimeError("local ZIP header signature mismatch")
    nlen,elen=struct.unpack_from("<HH",header,26)
    data_off=rec["offset"]+30+nlen+elen
    comp,_=http_range(url,data_off,data_off+rec["compressed"]-1)
    if rec["method"] == 0: raw=comp
    elif rec["method"] == 8: raw=zlib.decompress(comp,-15)
    else: raise RuntimeError(f"unsupported ZIP compression method {rec['method']}")
    if len(raw) != rec["uncompressed"]: raise RuntimeError("uncompressed size mismatch")
    if zlib.crc32(raw) & 0xffffffff != rec["crc32"]: raise RuntimeError("ZIP member CRC32 mismatch")
    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(raw)

def parse_mzml(path: Path, selected_rows: list[dict]) -> dict:
    ns={"m":"http://psi.hupo.org/ms/mzml"}
    root=ET.parse(path).getroot()
    summary={"instrument_configurations":[],"software":[],"source_files":[],"activation_terms":{},"ms_levels":{},"collision_energy_values":{},"spectrum_count":0,"selected_spectra":[]}
    groups={g.get("id"):g for g in root.findall(".//m:referenceableParamGroupList/m:referenceableParamGroup",ns)}
    def cvobj(cv): return {k:cv.get(k) for k in ["accession","name","value","unitCvRef","unitAccession","unitName"] if cv.get(k) is not None}
    for x in root.findall(".//m:instrumentConfigurationList/m:instrumentConfiguration",ns):
        terms=[cvobj(v) for v in x.findall(".//m:cvParam",ns)]
        for ref in x.findall(".//m:referenceableParamGroupRef",ns):
            grp=groups.get(ref.get("ref"))
            if grp is not None: terms.extend(cvobj(v) for v in grp.findall("m:cvParam",ns))
        summary["instrument_configurations"].append({"id":x.get("id"),"terms":terms})
    for x in root.findall(".//m:softwareList/m:software",ns):
        summary["software"].append({"id":x.get("id"),"version":x.get("version"),"terms":[cvobj(v) for v in x.findall("m:cvParam",ns)]})
    for x in root.findall(".//m:sourceFileList/m:sourceFile",ns):
        summary["source_files"].append({"id":x.get("id"),"name":x.get("name"),"location":x.get("location"),"params":[cvobj(v) for v in x.findall("m:cvParam",ns)]})
    want={r["spectrum_id"] for r in selected_rows}; found=set()
    for sp in root.findall(".//m:spectrumList/m:spectrum",ns):
        summary["spectrum_count"] += 1
        level=None
        for cv in sp.findall("m:cvParam",ns):
            if cv.get("accession")=="MS:1000511":
                level=cv.get("value"); summary["ms_levels"][level]=summary["ms_levels"].get(level,0)+1
        act=sp.find(".//m:precursor/m:activation",ns)
        if act is not None:
            terms=[cvobj(v) for v in act.findall("m:cvParam",ns)]
            for item in terms:
                key=f"{item.get('accession')}|{item.get('name')}|{item.get('unitAccession')}|{item.get('unitName')}"
                summary["activation_terms"][key]=summary["activation_terms"].get(key,0)+1
                if item.get("accession")=="MS:1000045":
                    v=item.get("value","<missing>"); summary["collision_energy_values"][v]=summary["collision_energy_values"].get(v,0)+1
        sid=sp.get("id")
        if sid in want:
            found.add(sid)
            selected_ion=sp.find(".//m:precursor/m:selectedIonList/m:selectedIon/m:cvParam[@accession='MS:1000744']",ns)
            summary["selected_spectra"].append({"spectrum_id":sid,"ms_level":level,"activation_terms":terms if act is not None else [],"selected_ion_mz":selected_ion.get("value") if selected_ion is not None else None})
    if found != want:
        raise RuntimeError(f"selected allowlist spectrum IDs missing in mzML: {len(want-found)}; examples={list(want-found)[:3]}")
    return summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--cache-dir",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--record-json",type=Path,default=None); ap.add_argument("--representatives-only",action="store_true"); ap.add_argument("--workers",type=int,default=6); args=ap.parse_args()
    import pandas as pd
    import ast
    # Load the frozen archive mapping from source, rather than silently substituting another version.
    src=DESIGN.read_text(); block=src.split("ZIPS = {",1)[1].split("\n}",1)[0]
    zip_map=dict(re.findall(r'"([^\"]+\.zip)": "([0-9a-f]{64})"',block))
    recdata=json.loads(args.record_json.read_text()) if args.record_json else None
    allow=pd.read_csv(ALLOW); chosen=allow.drop_duplicates(["source_zip","member","file_sha256"])
    if args.representatives_only: chosen=chosen.groupby("source_zip",sort=True).head(1)
    full_allow=allow
    results=[]
    for zname, grp in chosen.groupby("source_zip",sort=True):
        url=f"https://zenodo.org/api/records/{RECORD}/files/{zname}/content"
        total, members=parse_zip_central_directory(url)
        central={x["name"]:x for x in members}
        rows=grp.to_dict("records")
        def process(row):
            member=row["member"]
            match=central.get(member)
            if match is None:
                matches=[x for n,x in central.items() if n.endswith("/"+member)]
                if len(matches)!=1: raise RuntimeError(f"member {member} has {len(matches)} central-directory matches in {zname}")
                match=matches[0]
            cache=args.cache_dir/zname/member
            if cache.exists():
                cached=cache.read_bytes()
                if len(cached)==match['uncompressed'] and (zlib.crc32(cached)&0xffffffff)==match['crc32']:
                    got=hashlib.sha256(cached).hexdigest()
                else:
                    extract_member_range(url,match,cache); got=hashlib.sha256(cache.read_bytes()).hexdigest()
            else:
                extract_member_range(url,match,cache); got=hashlib.sha256(cache.read_bytes()).hexdigest()
            if got!=row["file_sha256"]: raise RuntimeError(f"allowlist SHA256 mismatch for {zname}:{member}: {got}")
            rows_for_member=full_allow.loc[full_allow.source_zip.eq(zname)&full_allow.member.eq(member)].to_dict("records")
            md=parse_mzml(cache,rows_for_member)
            return {"source_zip":zname,"source_zip_sha256_frozen":zip_map[zname],"zenodo_record":RECORD,"zenodo_file_url":url,"remote_zip_bytes":total,"member":member,"allowlist_sha256":row["file_sha256"],"member_sha256_verified":got,"selected_sample_id":row["unique_sample_id"],"n_selected_scan_rows_for_member":len(rows_for_member),"selected_scan_rows":[{"spectrum_id":r["spectrum_id"],"rung":float(r["rung"]),"key":r["key"],"selected_ion_mz":float(r["selected_ion_mz"])} for r in rows_for_member],"member_compressed_bytes":match["compressed"],"member_uncompressed_bytes":match["uncompressed"],"extracted_cache_path":str(cache),"mzml_metadata":md}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures=[pool.submit(process,row) for row in rows]
            for fut in as_completed(futures):
                results.append(fut.result())
        print(f"PASS {zname} :: verified {len(rows)} selected mzML members",flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(results,indent=2))
if __name__=="__main__": main()
