#!/usr/bin/env python3
"""Verify and list the nested NIH 7z member without extracting spectra.

The outer ZIP member is stored (not compressed). This script range-downloads that
member to the system temporary directory, checks its declared size and ZIP CRC32,
asks bsdtar to list names only, summarizes suffixes, then deletes the temporary file.
It does not extract .mzML payloads or inspect acquisition values in the nested data.
"""
from __future__ import annotations
import csv, json, shutil, struct, subprocess, tempfile, urllib.request, zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RECORD=json.loads((ROOT/'publication_phase6/metadata/zenodo_raw_record_13785391.json').read_text())
FILE=next(f for f in RECORD['files'] if f['key']=='20230404_pluskal_nih_positive.zip')
MEMBER='20230404_pluskal_nih_positive/nih_positive_mzml.7z'
REC=next(r for r in csv.DictReader((ROOT/'publication_phase6/metadata/PUBLIC_RAW_ZIP_MEMBERS.csv').open()) if r['member']==MEMBER)
URL=FILE['links'].get('self') or FILE['links'].get('content')
SIZE=int(REC['compressed_bytes']); EXPECTED_CRC=int(REC['crc32'],16); OFFSET=int(REC['local_header_offset'])
def get(a:int,b:int)->bytes:
    req=urllib.request.Request(URL,headers={'Range':f'bytes={a}-{b}','User-Agent':'MURU-Phase6-Evidence-Audit/1.0'})
    with urllib.request.urlopen(req,timeout=180) as response:
        data=response.read(); content=response.headers.get('Content-Range','')
        if response.status!=206 or not content.startswith(f'bytes {a}-'):
            raise RuntimeError(f'Range response invalid for {a}-{b}: status {response.status}, {content}')
        return data
header=get(OFFSET,OFFSET+29)
if header[:4]!=b'PK\x03\x04': raise RuntimeError('ZIP local header signature missing')
name_len,extra_len=struct.unpack_from('<HH',header,26); DATA_OFFSET=OFFSET+30+name_len+extra_len
with tempfile.TemporaryDirectory(prefix='muru_phase6_nih_') as tmp:
    path=Path(tmp)/'nih_positive_mzml.7z'; path.touch(); path.open('r+b').truncate(SIZE); chunk=16*1024*1024
    jobs=[(a,min(a+chunk,SIZE)) for a in range(0,SIZE,chunk)]
    with path.open('r+b',buffering=0) as output:
        def fetch(pair):
            a,b=pair; data=get(DATA_OFFSET+a,DATA_OFFSET+b-1)
            if len(data)!=b-a: raise RuntimeError(f'Wrong range length at {a}')
            output.seek(a); output.write(data)
        with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(fetch,jobs))
    crc=0; n=0
    with path.open('rb') as source:
        while block:=source.read(8*1024*1024): crc=zlib.crc32(block,crc); n+=len(block)
    if n!=SIZE or crc&0xffffffff!=EXPECTED_CRC: raise RuntimeError(f'Outer ZIP member integrity failed: size={n}, CRC={crc&0xffffffff:08x}')
    result=subprocess.run(['bsdtar','-tf',str(path)],check=True,capture_output=True,text=True)
    names=result.stdout.splitlines()
    suffixes={}
    for name in names:
        suffix=Path(name.rstrip('/')).suffix.lower() or '<none>'; suffixes[suffix]=suffixes.get(suffix,0)+1
    print(f'PASS outer member size={n}, CRC32={crc&0xffffffff:08x}')
    print(f'listed names={len(names)}, extensions={dict(sorted(suffixes.items()))}')
    print(f'method-like names={sum(suffixes.get(x,0) for x in (".meth",".method",".mth",".msmethod",".rawmethod"))}')
