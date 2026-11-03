#!/usr/bin/env python3
from pathlib import Path
import re, hashlib, csv, sys
R=Path(__file__).resolve().parents[1]; errors=[]; checks=[]
def check(ok,label):
 checks.append((label,bool(ok)))
 if not ok: errors.append(label)
s=(R/'manuscript/MURU_PHASE5_MANUSCRIPT_SOURCE.md').read_text()
abstract=s.split('## Abstract',1)[1].split('**Keywords:**',1)[0]
wc=len(re.sub(r'[*`]','',abstract).split())
check(200<=wc<=250,f'abstract words 200-250 (observed {wc})')
for h in ['## Abstract','## 1. Introduction','## 2. Materials and Methods','## 3. Results','## 4. Discussion','## 5. Conclusion','## Declarations','## References']: check(h in s,f'required heading {h}')
refs=s.split('## References',1)[1]
refnums=[int(x) for x in re.findall(r'^(\d+)\. ',refs,re.M)]
check(len(refnums)==29 and refnums==list(range(1,30)),'29 sequential bibliography entries')
cited=set()
for x in re.findall(r'\[([0-9,–-]+)\]',s.split('## References',1)[0]):
 for v in re.split('[,]',x):
  m=re.fullmatch(r'(\d+)[–-](\d+)',v.strip())
  if m:cited.update(range(int(m.group(1)),int(m.group(2))+1))
  elif v.strip().isdigit():cited.add(int(v))
check(cited.issubset(set(refnums)),'in-text citations map to references')
check(set(refnums).issubset(cited),'each bibliography entry cited in text')
for n in range(1,6):
 for ext in ['svg','pdf','png']: check((R/f'figures/FIGURE_{n}/figure_{n}.{ext}').exists(),f'figure {n} {ext} exists')
for f in ['MURU_PHASE5_MANUSCRIPT_FINAL.docx','MURU_PHASE5_MANUSCRIPT_FINAL.pdf','MURU_PHASE5_STANDARD_CITATIONS.docx','MURU_PHASE5_ONLINE_CITATIONS.docx']:
 check((R/'manuscript'/f).exists(),f'manuscript deliverable {f}')
for f in ['MURU_PHASE5_SUPPORTING_INFORMATION.docx','MURU_PHASE5_SUPPORTING_INFORMATION.pdf']:
 check((R/'supplement'/f).exists(),f'supplement deliverable {f}')
check('0.9706719800607511' in s and '0.9523611879747089' in s and '0.9892672061846276' in s,'primary metrics and CI present')
check('0.95' in s and ('failed' in s.lower() or 'did not meet' in s.lower()),'practical threshold failure visible')
check('1.0083' in s and ('Tail-risk improvement was not demonstrated' in s or 'No improvement in tail risk was demonstrated' in s),'adverse novelty and tail results present')
check('INTERFACE_UNRESOLVED' in s and 'units are unresolved' in s.lower(),'energy uncertainty disclosed')
check('TODO' not in s and 'PLACEHOLDER' not in s,'no obvious TODO/placeholders in manuscript')
check('Accuracy' not in s and '97% accuracy' not in s,'no unsupported prediction-accuracy claim')
check('No journal submission' in (R/'START_HERE.md').read_text(),'journal non-submission status stated')
check((R/'release/FINAL_DATA_RIGHTS_REPORT.md').exists(),'data rights report exists')
print(f'{sum(v for _,v in checks)}/{len(checks)} checks passed')
for label,ok in checks: print(('PASS' if ok else 'FAIL')+' '+label)
if errors: sys.exit(1)
