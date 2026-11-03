#!/usr/bin/env python3
"""Build and validate Phase 6 internal and external-review ZIPs."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import csv, hashlib
ROOT=Path(__file__).resolve().parents[2]
P6=ROOT/'publication_phase6'; REL=P6/'release'
FULL=REL/'PHASE6_COMPLETE_PACKAGE.zip'; EXT=REL/'EXTERNAL_REVIEW_PACKAGE.zip'
MANIFEST=REL/'FINAL_FILE_MANIFEST.csv'; SUMS=REL/'FINAL_SHA256SUMS.txt'
EXTERNAL_FILES=[
 'external_review/EXTERNAL_REVIEW_PACKAGE_README.md',
 'manuscript/MURU_PHASE6_MANUSCRIPT_FINAL.pdf',
 'supplement/MURU_PHASE6_SUPPORTING_INFORMATION.pdf',
 'external_review/UPDATED_RESEARCH_SUMMARY.pdf',
 'external_review/UPDATED_ANALYTICAL_CHEMISTRY_PACKET.pdf',
 'external_review/STATISTICAL_REVIEW_PACKET.pdf',
 'external_review/REPRODUCIBILITY_REVIEW_PACKET.pdf',
 'external_review/REVIEWER_QUESTIONS.md',
 'external_review/EXTERNAL_REVIEW_INSTRUCTIONS.md',
 'external_review/REVIEWER_FEEDBACK_FORM.pdf',
 'external_review/HUMAN_REVIEW_STATUS.md',
 'energy/FINAL_COLLISION_ENERGY_ADJUDICATION.md',
 'metadata/EXTRACTION_VALIDATION_REPORT.md',
 'metadata/MASSIVE_LINKAGE_FINDINGS.md',
]
README='''# MURU Phase 6 external scientific review package\n\n**Status: PREPARED, NOT CLEARED TO SEND.** Owner approval for a named recipient, exact attachment scope, and sharing purpose is required before transmission. No expert has been contacted and no review has occurred.\n\nThis package contains the internal manuscript and Supporting Information, aggregate technical summaries, review questions, and feedback form. It excludes WUR records, model weights, compound-level errors, raw or converted spectra, native method payloads, and private correspondence. MassIVE metadata summaries refer to public MSV000094528; the underlying RAW payload was streamed for one checksum test and not retained.\n\nProject-authored materials have no separate external-sharing license declared. Do not forward, upload, or treat this package as public-safe until owner approval and remaining rights checks are complete.\n'''
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def build_external():
 with ZipFile(EXT,'w',ZIP_DEFLATED,compresslevel=7) as z:
  z.writestr('README_EXTERNAL_REVIEW.md',README)
  for rel in EXTERNAL_FILES:
   q=P6/rel
   if not q.is_file(): raise FileNotFoundError(q)
   z.write(q,Path(rel).as_posix())
def write_manifest():
 rows=[]
 for q in sorted(P6.rglob('*')):
  if not q.is_file(): continue
  rel=q.relative_to(P6).as_posix()
  if rel in {'release/FINAL_FILE_MANIFEST.csv','release/FINAL_SHA256SUMS.txt','release/PHASE6_COMPLETE_PACKAGE.zip'}: continue
  if '__pycache__' in q.parts or 'render' in q.parts or q.suffix.lower() in {'.pyc','.raw','.mzml','.meth','.7z'}: continue
  rows.append((rel,q.stat().st_size,sha(q)))
 with MANIFEST.open('w',newline='') as f:
  w=csv.writer(f,lineterminator='\n'); w.writerow(['relative_path','bytes','sha256']); w.writerows(rows)
def build_full():
 with ZipFile(FULL,'w',ZIP_DEFLATED,compresslevel=7) as z:
  for q in sorted(P6.rglob('*')):
   if not q.is_file(): continue
   rel=q.relative_to(P6)
   if q==FULL or q==SUMS: continue
   if '__pycache__' in rel.parts or 'render' in rel.parts or q.suffix.lower() in {'.pyc','.raw','.mzml','.meth','.7z'}: continue
   z.write(q,Path('publication_phase6')/rel)
def validate(p):
 with ZipFile(p) as z:
  names=z.namelist()
  assert all(not n.lower().endswith(('.raw','.mzml','.meth','.7z')) for n in names),p
  assert all(i.file_size < 100_000_000 for i in z.infolist()),p
  bad=z.testzip()
  if bad: raise RuntimeError(f'{p.name}: corrupt member {bad}')
  return len(names)
REL.mkdir(parents=True,exist_ok=True)
build_external(); write_manifest(); build_full()
for p in [EXT,FULL]: print(f'PASS {p.name}: {validate(p)} members, {p.stat().st_size} bytes')
with SUMS.open('w') as f:
 for p in [EXT,FULL]: f.write(f'{sha(p)}  release/{p.name}\n')
 for rel in ['manuscript/MURU_PHASE6_MANUSCRIPT_FINAL.pdf','manuscript/MURU_PHASE6_MANUSCRIPT_FINAL.docx','supplement/MURU_PHASE6_SUPPORTING_INFORMATION.pdf']:
  p=P6/rel; f.write(f'{sha(p)}  {rel}\n')
print(SUMS.read_text(),end='')
