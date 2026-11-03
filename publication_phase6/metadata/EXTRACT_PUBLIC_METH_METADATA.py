#!/usr/bin/env python3
"""Download and inspect only Thermo .meth members listed in the public raw ZIP records.

Unredacted method payloads are written only to a temporary directory. The output CSV
contains filenames, member hashes, public ZIP lineage, and non-identifying method
class/term summaries; machine serials, hostnames, and filesystem paths are excluded.
"""
import csv,hashlib,importlib.util,json,re,shutil
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('phase6_extract',Path(__file__).with_name('RAW_METADATA_EXTRACTION.py'))
mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
record=json.loads((ROOT/'publication_phase6/metadata/zenodo_raw_record_13785391.json').read_text())
urls={f['key']:f['links']['self'] for f in record['files']}
members=pd.read_csv(ROOT/'publication_phase6/metadata/PUBLIC_RAW_ZIP_MEMBERS.csv')
members=members[members.extension.eq('.meth')]
cache=Path('/tmp/muru_phase6_meth_all');cache.mkdir(exist_ok=True)
out=[]
for _,row in members.iterrows():
 p=cache/(row.zip_key+'__'+Path(row.member).name)
 if not p.exists():
  rec={'name':row.member,'offset':int(row.local_header_offset),'compressed':int(row.compressed_bytes),'uncompressed':int(row.uncompressed_bytes),'method':int(row.compression_method),'crc32':int(row.crc32,16)}
  mod.extract_member_range(urls[row.zip_key],rec,p)
 b=p.read_bytes(); txt=b.decode('utf-8','ignore')
 instruments=sorted(set(re.findall(r'<Instrument\s+value="([^"]+)"',txt)))
 methodtypes=sorted(set(re.findall(r'<Type\s+type="Enum&lt;MethodType&gt;"\s+value="([^"]+)"',txt)))
 stored=sorted(set(re.findall(r'<StoredTypeVersion\s+value="([^"]+)"',txt)))
 # Count only explicit energy terms; no binary values are interpreted as settings.
 keywords={k:len(re.findall(pat,txt,re.I)) for k,pat in {
  'id_x':r'\bID-X\b','orbitrap':r'\bOrbitrap\b','q_exactive':r'Q\s*Exactive',
  'normalized_collision_energy_phrase':r'normalized\s+collision\s+energy',
  'nce_standalone':r'(?<![A-Za-z])NCE(?![A-Za-z])','collision_energy_phrase':r'collision\s+energy',
  'hcd_standalone':r'(?<![A-Za-z])HCD(?![A-Za-z])'}.items()}
 out.append({'raw_zip':row.zip_key,'zenodo_record_doi':record.get('doi'),'member':row.member,'member_sha256':hashlib.sha256(b).hexdigest(),'member_crc32_verified':'yes','file_format':'OLE Compound File; Thermo .meth','instrument_field_values':'|'.join(instruments),'method_type_values':'|'.join(methodtypes),'stored_type_versions':'|'.join(stored),'explicit_ID_X_term_count':keywords['id_x'],'explicit_Orbitrap_term_count':keywords['orbitrap'],'explicit_Q_Exactive_term_count':keywords['q_exactive'],'normalized_collision_energy_phrase_count':keywords['normalized_collision_energy_phrase'],'standalone_NCE_count':keywords['nce_standalone'],'collision_energy_phrase_count':keywords['collision_energy_phrase'],'standalone_HCD_count':keywords['hcd_standalone'],'interpretation':'Raw archive method member inspected; fields summarized only. No claim of linkage to evaluated mzML run.'})
 print(f"{row.zip_key}: {len(out)}/{len(members)} .meth files",flush=True)
p=ROOT/'publication_phase6/metadata/PUBLIC_METH_FILE_METADATA.csv'
with p.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
shutil.rmtree(cache)
print(f'WROTE {len(out)} method summaries; unredacted .meth payloads removed from temporary cache after extraction')
