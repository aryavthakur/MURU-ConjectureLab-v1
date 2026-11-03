#!/usr/bin/env python3
"""Summarize a saved MassIVE dataset_files.jsp listing against verified mzML metadata.

Inputs are the downloaded MassIVE listing HTML and the temporary JSON produced by
RAW_METADATA_EXTRACTION.py. The output contains archive-level counts and per-source
basename candidate counts, not proof of identity. Only a separate downloaded RAW
SHA-1 comparison can authenticate a particular file.
"""
from __future__ import annotations
import argparse,collections,json,re,csv
from pathlib import Path
from urllib.parse import unquote

def main():
 ap=argparse.ArgumentParser();ap.add_argument('massive_listing_html',type=Path);ap.add_argument('verified_mzml_json',type=Path);ap.add_argument('--outdir',type=Path,required=True);a=ap.parse_args()
 html=a.massive_listing_html.read_text(errors='replace')
 m=re.search(r'var dataset_files = (\{.*?\});',html,re.S)
 if not m: raise RuntimeError('MassIVE dataset_files object not found')
 ds=json.loads(m.group(1)); rows=ds['row_data']; ext=collections.Counter(Path(r['name']).suffix.lower() or '<none>' for r in rows); paths=collections.Counter(r['relative_path'].split('/')[0] for r in rows)
 raw=[r for r in rows if Path(r['name']).suffix.lower()=='.raw']; by=collections.defaultdict(list)
 def normalize(name):
  x=Path(name).name.lower().replace('enamine_','enammol_')
  if x.endswith('.raw'): x=x[:-4].replace('_id','')+'.raw'
  return x
 for r in raw: by[normalize(r['name'])].append(r)
 files=json.loads(a.verified_mzml_json.read_text()); source_files=collections.defaultdict(set)
 for f in files:
  for sf in f['mzml_metadata'].get('source_files',[]):
   if sf.get('name'): source_files[f['source_zip']].add(sf['name'])
 a.outdir.mkdir(parents=True,exist_ok=True)
 with (a.outdir/'MASSIVE_DATASET_INVENTORY.csv').open('w',newline='') as h:
  w=csv.writer(h);w.writerow(['dataset','page_status','license','listing_total_rows','rows_parsed','file_extension','count','top_level_collection_counts','source_url','accessed_utc','inspection'])
  for suffix,count in sorted(ext.items()):w.writerow(['MSV000094528','Partial Public','CC0 1.0',ds.get('total_rows'),len(rows),suffix,count,'; '.join(f'{k}:{v}' for k,v in sorted(paths.items())),'https://massive.ucsd.edu/ProteoSAFe/dataset_files.jsp?task=676a38e2dd574a15905e807d78cf1e57','2026-11-03','file listing metadata only; no dataset payloads retained'])
 with (a.outdir/'MASSIVE_SOURCE_FILE_COVERAGE.csv').open('w',newline='') as h:
  fields=['source_zip','unique_mzml_source_RAW_names','MassIVE_RAW_candidate_names_after_documented_normalization','unmatched_names','candidate_match_rule','identity_limit','raw_method_extension_in_listing']
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
  for family,names in sorted(source_files.items()):
   matched=sum(bool(by.get(normalize(n))) for n in names)
   w.writerow({'source_zip':family,'unique_mzml_source_RAW_names':len(names),'MassIVE_RAW_candidate_names_after_documented_normalization':matched,'unmatched_names':len(names)-matched,'candidate_match_rule':'case-insensitive basename; strip _id before .raw; replace enamine_ with enammol_','identity_limit':'basename candidate only; exact identity not established except separate SHA1 tests','raw_method_extension_in_listing':sum(1 for r in rows if Path(r['name']).suffix.lower() in {'.meth','.method','.mth','.msmethod','.rawmethod'})})
 print(f"PASS listing rows={len(rows)} extensions={dict(sorted(ext.items()))}; wrote counts for {len(source_files)} frozen source families")
if __name__=='__main__':main()
