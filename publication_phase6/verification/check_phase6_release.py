#!/usr/bin/env python3
"""Integrity checks for MURU Phase 6 release files; no scientific outputs recomputed here."""
from __future__ import annotations
import csv, hashlib, re, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P6=ROOT/'publication_phase6'
def read(path): return path.read_text(encoding='utf-8')
src=read(P6/'manuscript/MURU_PHASE6_MANUSCRIPT_SOURCE.md')
abstract=src.split('## Abstract',1)[1].split('**Keywords:**',1)[0]
words=re.findall(r"\b[\w]+(?:[’'-][\w]+)*\b",abstract)
assert 200<=len(words)<=250, len(words)
assert '## 1. Introduction' in src and '## 2. Materials and Methods' in src and '## 3. Results' in src and '## 4. Discussion' in src and '## 5. Conclusion' in src
refs=src.split('## References',1)[1]
refnums=[int(x) for x in re.findall(r'^(\d+)\. ',refs,re.M)]
assert refnums==list(range(1,35)),refnums
citations=[]
for raw in re.findall(r'\[([0-9]+(?:[,–-][0-9]+)*)\]',src[:src.index('## References')]):
 for part in raw.split(','):
  m=re.fullmatch(r'(\d+)[–-](\d+)',part.strip())
  citations.extend(range(int(m.group(1)),int(m.group(2))+1) if m else [int(part)])
assert set(citations)<=set(refnums)
assert all(x in src for x in ['1,794','1,789','1,687','0.1296115107','0.1335276112','0.9706719801','0.9523611880','0.9892672062','2.9328%','0.95'])
assert '835 of 1,428' in src or '835/1,428' in src
assert 'ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3' in read(P6/'metadata/MASSIVE_RAW_LINKAGE_TESTS.csv')
assert 'tail-risk improvement was not demonstrated' in src.lower()
assert 'calibrated physical' in src.lower() or 'physical calibration' in src.lower()
assert not re.search(r'\b(?:97% accuracy|97 percent accuracy|97% prediction accuracy)\b',src,re.I)
assert not re.search(r'\b(?:TODO|TBD|PLACEHOLDER)\b',src,re.I)
assert 'INTERFACE_UNRESOLVED' in src
assert 'The 5% practical' in src or '5% practical-improvement threshold was not met' in src
# bibliography audit and citation row 34
with (P6/'literature/FINAL_CITATION_AUDIT.csv').open(newline='') as f: audit=list(csv.DictReader(f))
assert len(audit)==34,len(audit)
with (P6/'metadata/MASSIVE_RAW_LINKAGE_TESTS.csv').open(newline='') as f: link=list(csv.DictReader(f))
assert len(link)==1 and link[0]['sha1_match']=='yes' and link[0]['selected_scan_rows_in_mzml_member']=='8'
with (P6/'metadata/SOURCE_TO_EVALUATION_LINEAGE.csv').open(newline='') as f: lineage=list(csv.DictReader(f))
assert len(lineage)==6004,len(lineage)
assert sum(r['massive_filelevel_full_sha1_verified_repeated_per_scan']=='yes' for r in lineage)==8
assert len({r['mzml_member'] for r in lineage if r['massive_filelevel_full_sha1_verified_repeated_per_scan']=='yes'})==1
for n in range(1,6):
 for ext in ['png','pdf','svg']:
  assert (P6/f'figures/FIGURE_{n}/figure_{n}.{ext}').is_file()
for f in ['manuscript/MURU_PHASE6_MANUSCRIPT_FINAL.docx','manuscript/MURU_PHASE6_MANUSCRIPT_FINAL.pdf','manuscript/MURU_PHASE6_STANDARD_CITATIONS.docx','manuscript/MURU_PHASE6_ONLINE_CITATIONS.docx','supplement/MURU_PHASE6_SUPPORTING_INFORMATION.docx','supplement/MURU_PHASE6_SUPPORTING_INFORMATION.pdf']:
 assert (P6/f).stat().st_size>0,f
print(f'PASS abstract words={len(words)}; references={len(refnums)}; mapped citations={len(set(citations))}; lineage rows={len(lineage)}')
print('PASS frozen metrics/threshold/adverse-result/energy language and one-file SHA-1 link')
print('PASS five figure triplets and required Word/PDF files')
