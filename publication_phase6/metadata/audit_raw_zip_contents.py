#!/usr/bin/env python3
"""Inspect public RAW ZIP central directories without downloading the RAW payloads."""
from pathlib import Path
import csv, importlib.util, json
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('phase6_extract',Path(__file__).with_name('RAW_METADATA_EXTRACTION.py'))
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
rec=json.loads((ROOT/'publication_phase6/metadata/zenodo_raw_record_13785391.json').read_text())
out=[]
member_rows=[]
for f in rec.get('files',[]):
 key=f['key']; url=f['links'].get('self') or f['links'].get('content')
 if not url: raise RuntimeError(f'No public file URL for {key}')
 total,members=mod.parse_zip_central_directory(url)
 types={}
 for m in members:
  member_rows.append({'zip_key':key,'member':m['name'],'extension':Path(m['name']).suffix.lower() or '<none>','compressed_bytes':m['compressed'],'uncompressed_bytes':m['uncompressed'],'crc32':f"{m['crc32']:08x}",'local_header_offset':m['offset'],'compression_method':m['method']})
  ext=Path(m['name']).suffix.lower() or '<none>'
  types[ext]=types.get(ext,0)+1
 method_ext=('.meth','.method','.mth','.msmethod','.methodfile','.rawmethod')
 out.append({'zip_key':key,'record_doi':rec.get('doi'),'zenodo_file_size':f['size'],'central_directory_entries':len(members),'raw_entries':types.get('.raw',0),'method_file_entries':sum(types.get(x,0) for x in method_ext),'instrument_export_entries':sum(types.get(x,0) for x in ('.xml','.txt','.csv','.pdf','.json','.tsv')),'other_extensions':'; '.join(f'{k}:{v}' for k,v in sorted(types.items())),'inspection':'remote ZIP central directory only; no RAW or other member payload downloaded'})
 print(key, len(members), sorted(types.items()), flush=True)
p=ROOT/'publication_phase6/metadata/PUBLIC_RAW_ZIP_CONTENT_AUDIT.csv'
with p.open('w',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
q=ROOT/'publication_phase6/metadata/PUBLIC_RAW_ZIP_MEMBERS.csv'
with q.open('w',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(member_rows[0]));w.writeheader();w.writerows(member_rows)
print('wrote',p,'and',q)
