#!/usr/bin/env python3
"""Fail-fast internal consistency checks for the Phase 4 canonical source and documents."""
from pathlib import Path
import re, sys, hashlib, subprocess, zipfile
from docx import Document
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'publication_phase4'; src=BASE/'manuscript/MURU_PHASE4_MANUSCRIPT_SOURCE.md'
text=src.read_text(encoding='utf-8')
checks=[]
def check(name, ok, detail=''):
    checks.append((name,bool(ok),detail))
# Abstract word count
abstract=re.search(r'## Abstract\n(.*?)\n\n\*\*Keywords',text,re.S).group(1)
words=re.findall(r"\b[\wμα]+(?:[-’'][\wμα]+)*\b",abstract)
check('abstract 200-250 words',200<=len(words)<=250,str(len(words)))
# Required headings
required=['## Abstract','## 1. Introduction','## 2. Materials and Methods','## 3. Results','## 4. Discussion','## 5. Conclusion','## Declarations','## References']
check('required manuscript headings',all(x in text for x in required),', '.join(x for x in required if x not in text))
# References and citations
refs=text.split('## References\n',1)[1]
ref_ids=[int(x) for x in re.findall(r'(?m)^(\d+)\. ',refs)]
check('unique reference identifiers',len(ref_ids)==len(set(ref_ids)),str(len(ref_ids)))
check('reference ids contiguous 1..N',ref_ids==list(range(1,len(ref_ids)+1)),str(ref_ids[:3])+'…'+str(ref_ids[-3:]))
body=text.split('## References\n',1)[0]
cites=[]
for m in re.finditer(r'\[([0-9]+(?:[,–-][0-9]+)*)\]',body):
    for p in m.group(1).split(','):
        q=p.strip()
        if '–' in q or '-' in q:
            a,b=map(int,re.split('[–-]',q)); cites.extend(range(a,b+1))
        else:cites.append(int(q))
check('citation ids map to bibliography',bool(cites) and max(cites)<=len(ref_ids) and min(cites)>=1,f'max={max(cites) if cites else None}; refs={len(ref_ids)}')
# Visual references and source files
for i in range(1,6):
    p=BASE/f'figures/FIGURE_{i}/figure_{i}.png'
    check(f'figure {i} output exists',p.exists(),str(p.relative_to(ROOT)))
    check(f'figure {i} cited in manuscript',f'Figure {i}' in body, '')
check('supporting information exists',(BASE/'supplement/MURU_PHASE4_SUPPORTING_INFORMATION.pdf').exists(),'')
# Placeholder and terminology guards
bad=re.findall(r'(?i)\b(TODO|TBD|PLACEHOLDER|INSERT HERE)\b',text)
check('no unexplained placeholders',not bad,repr(bad))
check('no accuracy-percent claim',not re.search(r'\b\d+(?:\.\d+)?\s*%\s*accuracy\b',text,re.I),'')
# Machine-readable expected evidence anchors
expected=['1,794','1,789','1,687','0.1296115','0.1335276','0.970672','0.952361','0.989267','0.95','2.93%','1.0083','INTERFACE_UNRESOLVED','0.860, 0.918']
check('primary results and adverse findings present',all(x in text for x in expected),', '.join(x for x in expected if x not in text))
check('failed practical criterion stated','criterion therefore failed' in text.lower() or 'criterion was not met' in text.lower(),'')
check('tail no-benefit statement present','Tail-error improvement was not demonstrated' in text or 'No tail-risk advantage was demonstrated' in text,'')
check('least-similar adverse outcome present','ratio = 1.0083' in text or 'ratio of 1.0083' in text,'')
check('energy ambiguity stated','INTERFACE_UNRESOLVED' in text and 'not a physical calibration' in text,'')
check('development interval bounded','max-T script, exact seed, serialized resamples, and selection ledger were not recovered' in text,'')
check('comparator endpoint properly scoped','not cosine similarity, full-spectrum accuracy, or structure-identification accuracy' in text,'')
# Validate generated Word outputs contain expected scientific claims and reference list.
for name in ['MURU_PHASE4_MANUSCRIPT_FINAL.docx','MURU_PHASE4_STANDARD_CITATIONS.docx','MURU_PHASE4_ONLINE_CITATIONS.docx']:
    p=BASE/'manuscript'/name
    doc=Document(p); dtext='\n'.join(x.text for x in doc.paragraphs)+'\n'+'\n'.join(c.text for t in doc.tables for row in t.rows for c in row.cells)
    check(f'{name} opens and contains primary result',p.exists() and '0.97067' in dtext and '1,789' in dtext,name)
    check(f'{name} includes all references',all(f'{i}. ' in dtext for i in range(1,len(ref_ids)+1)),name)
# Layout and variant consistency
master=BASE/'manuscript/MURU_PHASE4_MANUSCRIPT_FINAL.docx'; standard=BASE/'manuscript/MURU_PHASE4_STANDARD_CITATIONS.docx'; online=BASE/'manuscript/MURU_PHASE4_ONLINE_CITATIONS.docx'
def docx_content(path):
    d=Document(path); return ([p.text for p in d.paragraphs],[[c.text for row in t.rows for c in row.cells] for t in d.tables])
check('master and standard DOCX scientific text/tables identical',docx_content(master)==docx_content(standard),'')
for label,path in [('master',master),('standard',standard),('online',online)]:
    doc=Document(path); normal=doc.styles['Normal']
    check(f'{label} body style is Times New Roman 12 pt single spaced',normal.font.name=='Times New Roman' and normal.font.size.pt==12 and normal.paragraph_format.line_spacing==1.0,label)
    pdf=path.with_suffix('.pdf')
    check(f'{label} PDF exists',pdf.exists(),str(pdf.relative_to(ROOT)))
    pages=int(re.search(r'Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(pdf)],text=True)).group(1))
    expected_pages={'master':14,'standard':14,'online':18}[label]
    check(f'{label} PDF page count',pages==expected_pages,f'{pages} pages')
def media_hashes(path):
    with zipfile.ZipFile(path) as z:return sorted(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
check('citation variants contain identical figure media',media_hashes(master)==media_hashes(online),'')
# same source fingerprint is the single-authoring guarantee for variants
source_hash=hashlib.sha256(text.encode()).hexdigest()
(BASE/'qa/CANONICAL_SOURCE_SHA256.txt').write_text(source_hash+'  MURU_PHASE4_MANUSCRIPT_SOURCE.md\n')
failed=[x for x in checks if not x[1]]
for name,ok,detail in checks: print(('PASS' if ok else 'FAIL')+' | '+name+(' | '+detail if detail else ''))
print(f'SUMMARY: {len(checks)-len(failed)}/{len(checks)} passed; source_sha256={source_hash}')
sys.exit(bool(failed))
