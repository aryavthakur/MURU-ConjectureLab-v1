#!/usr/bin/env python3
"""Inspect only ZIP central directories of the nine frozen Zenodo mzML sources."""
from pathlib import Path
import csv, importlib.util, json, re
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('phase6_extract',Path(__file__).with_name('RAW_METADATA_EXTRACTION.py'))
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
rec=json.loads((ROOT/'publication_phase6/metadata/zenodo_record_15683784.json').read_text())
src=(ROOT/'src/muru/wur_v2/msnlib_design.py').read_text().split('ZIPS = {',1)[1].split('\n}',1)[0]
files=re.findall(r'"([^\"]+\.zip)"\s*:\s*"([0-9a-f]{64})"',src)
out=[]
for name,sha in files:
 url=f'https://zenodo.org/api/records/{rec["id"]}/files/{name}/content'
 total,members=mod.parse_zip_central_directory(url)
 ext={}
 for x in members:
  suffix=Path(x['name']).suffix.lower() or '<none>'
  ext[suffix]=ext.get(suffix,0)+1
 row={'source_zip':name,'declared_frozen_sha256':sha,'zenodo_record':rec['id'],'zip_bytes':total,'central_directory_entries':len(members),'mzml_entries':ext.get('.mzml',0),'raw_entries':ext.get('.raw',0),'native_method_like_entries':sum(ext.get(k,0) for k in ('.meth','.method','.mth','.msmethod','.raw','.thermo','.wiff','.d','.raws')),'other_extensions':'; '.join(f'{k}:{v}' for k,v in sorted(ext.items()) if k not in ('.mzml','<none>','.raw','.meth','.method','.mth','.xml','.msmethod')),'content_types_observed':'; '.join(sorted(ext)),'inspection':'remote ZIP central directory only; no raw/native-method-like suffix counted; XML and text members are reported separately, payloads not downloaded'}
 print(name,row['central_directory_entries'],row['content_types_observed'],flush=True)
 out.append(row)
p=ROOT/'publication_phase6/metadata/SOURCE_ZIP_CONTENT_AUDIT.csv'
with p.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print('wrote',p)
