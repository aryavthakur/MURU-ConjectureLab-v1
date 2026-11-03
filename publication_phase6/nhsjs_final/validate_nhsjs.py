#!/usr/bin/env python3
"""Check NHSJS-formatted manuscript deliverables for content and citation integrity."""
from __future__ import annotations
import re, sys, zipfile, hashlib, subprocess
from pathlib import Path
from docx import Document

ROOT=Path(__file__).resolve().parent
FILES={
 'anonymous':ROOT/'MURU_NHSJS_STANDARD_ANONYMOUS.docx',
 'online':ROOT/'MURU_NHSJS_ONLINE_CITATIONS.docx',
 'named':ROOT/'MURU_NHSJS_NAMED_MASTER.docx',
 'si':ROOT/'MURU_NHSJS_SUPPORTING_INFORMATION.docx'}
EXPECTED={1_794,1_789,1_687}

def refs_for(d):
 seen=False; out=[]
 for p in d.paragraphs:
  if p.text.strip()=='References': seen=True; continue
  if seen and re.match(r'^\d+\.\s',p.text): out.append(p.text)
 return out

def body_paras(d, anon=False):
 out=[]; past_ack=False
 for p in d.paragraphs:
  t=p.text.strip()
  if t=='References': break
  if t=='Acknowledgments':
   if anon: break
   past_ack=True
  if past_ack: continue
  if t=='Aryav Thakur': continue
  out.append(t)
 return out

def normalized_body(d, mode, anon=False):
 result=[]; past_ack=False
 for p in d.paragraphs:
  if p.text.strip()=='References': break
  if p.text.strip()=='Acknowledgments':
   if anon: break
   past_ack=True
  if past_ack or p.text.strip()=='Aryav Thakur': continue
  parts=[]
  for r in p.runs:
   if mode=='standard' and r.font.superscript and (r.text.isdigit() or r.text==','): continue
   if mode=='online' and (r.text.startswith('((') or (r.text==',' and r.font.superscript)): continue
   parts.append(r.text)
  result.append(re.sub(r'\s+',' ',' '.join(parts)).strip())
 return result

def check_docx(name,path,mode,anonymous=False):
 d=Document(path); errors=[]; rlist=refs_for(d)
 if len(rlist)!=34: errors.append(f'{name}: references={len(rlist)}, expected 34')
 if [int(re.match(r'^(\d+)',x).group(1)) for x in rlist] != list(range(1,35)):
  errors.append(f'{name}: reference identifiers not contiguous 1..34')
 for n in range(1,6):
  if f'Figure {n} |' not in '\n'.join(p.text for p in d.paragraphs): errors.append(f'{name}: missing caption Figure {n}')
 imgs=sum(1 for r in d.part.rels.values() if r.reltype.endswith('/image'))
 if imgs!=5: errors.append(f'{name}: embedded figure count={imgs}, expected 5')
 alltext='\n'.join(p.text for p in d.paragraphs)
 if any(x in alltext.lower() for x in ['97% accuracy','97 percent accuracy','universal superiority']): errors.append(f'{name}: prohibited accuracy/superiority phrase found')
 for value in ['0.1296115107','0.1335276112','0.9706719801','0.9523611880','0.9892672062','2.9328%','5%']:
  if value not in alltext: errors.append(f'{name}: expected result/limitation missing: {value}')
 if anonymous:
  if 'Aryav Thakur' in alltext or 'Acknowledgments' in alltext: errors.append('anonymous: author name or acknowledgments section present')
  props=d.core_properties
  if any([props.author,props.last_modified_by,props.title,props.subject,props.keywords,props.comments]): errors.append('anonymous: identifying core properties not blank')
 with zipfile.ZipFile(path) as z:
  names=z.namelist(); xml='\n'.join(z.read(n).decode('utf-8','ignore') for n in names if n.endswith('.xml'))
  if re.search(r'<w:ins(?:\s|>)',xml) or re.search(r'<w:del(?:\s|>)',xml): errors.append(f'{name}: tracked changes tags present')
  if 'word/comments.xml' in names: errors.append(f'{name}: comments part present')
  if anonymous:
   if '/Users/' in xml or 'aryavthakur@' in xml.lower() or 'Aryav Thakur' in xml: errors.append('anonymous: personal metadata/path detected in package XML')
   if any(n.startswith('word/header') or n.startswith('word/footer') for n in names):
    for n in names:
     if n.startswith(('word/header','word/footer')) and n.endswith('.xml'):
      txt=z.read(n).decode('utf-8','ignore')
      if 'Aryav' in txt or '/Users/' in txt: errors.append('anonymous: identifying header/footer text present')
 if mode=='standard':
  first=[]; seen=set(); inline=[]
  for p in d.paragraphs:
   if p.text.strip()=='References': break
   for i,r in enumerate(p.runs):
    if r.font.superscript and r.text.isdigit():
     k=int(r.text); inline.append(k)
     if k not in seen: first.append(k); seen.add(k)
     if i and p.runs[i-1].text.endswith(' '): errors.append(f'{name}: whitespace before superscript citation {k}')
  if first != list(range(1,35)): errors.append(f'{name}: first-use citation sequence is {first}')
  if set(inline)!=set(range(1,35)): errors.append(f'{name}: citation IDs do not map to references')
 else:
  inline=[]; superscript_commas=0; first=[]; seen=set(); missing_leading_space=0
  for p in d.paragraphs:
   if p.text.strip()=='References': break
   runs=p.runs
   for i,r in enumerate(runs):
    if r.text.startswith('((') and r.text.endswith('))'):
     citation=r.text[2:-2]; inline.append(citation)
     if citation not in seen:
      first.append(citation); seen.add(citation)
     prev=runs[i-1].text if i else ''
     if not prev.endswith(' '): missing_leading_space+=1
    if r.font.superscript and r.text==',': superscript_commas+=1
  ref_text=[]
  for s in rlist: ref_text.append(re.sub(r'^\d+\.\s*','',s))
  if not inline: errors.append(f'{name}: no complete online citations detected')
  if set(inline)!=set(ref_text): errors.append(f'{name}: online citation/reference exact-text mismatch ({len(set(inline))} cited, {len(set(ref_text))} refs)')
  if [ref_text.index(x)+1 for x in first] != list(range(1,len(ref_text)+1)): errors.append(f'{name}: first-use sequence differs from bibliography order')
  if missing_leading_space: errors.append(f'{name}: {missing_leading_space} online citations lack required leading space')
  if superscript_commas<1: errors.append(f'{name}: no superscript citation separators detected')
 return d,errors

def main():
 errors=[]
 src=(ROOT/'MURU_NHSJS_SOURCE.md').read_text()
 abstract=src.split('## Abstract',1)[1].split('## Introduction',1)[0]
 words=re.findall(r"[\w]+(?:[’'-][\w]+)*",abstract)
 if not 200<=len(words)<=250: errors.append(f'abstract word count {len(words)} outside 200-250')
 if len(re.findall(r'^!\[Figure \d+\.',src,re.M))!=5: errors.append('source figure count differs from five')
 ds={}
 for name,path in FILES.items():
  if name=='si':
   d=Document(path); ds[name]=d
   if len(d.tables)!=9: errors.append(f'SI tables={len(d.tables)}, expected actual 9')
   continue
  d,e=check_docx(name,path,'online' if name=='online' else 'standard',name=='anonymous')
  ds[name]=d; errors.extend(e)
 a=normalized_body(ds['anonymous'],'standard',anon=True)
 o=normalized_body(ds['online'],'online')
 if a!=o:
  errors.append('anonymous standard and online manuscript scientific body text differs after citation normalization/anonymization')
 # exact-title Word manuscript must remain the anonymous standard manuscript.
 exact=ROOT/'Predicting Collision-Energy-Dependent Fragmentation Extent from Molecular Structure: Development and External Evaluation of MURU-WUR-v2.docx'
 if hashlib.sha256(exact.read_bytes()).digest()!=hashlib.sha256(FILES['anonymous'].read_bytes()).digest(): errors.append('exact-title DOCX is not byte-identical to anonymous Standard manuscript')
 for n in ['MURU_NHSJS_STANDARD_ANONYMOUS.pdf','MURU_NHSJS_ONLINE_CITATIONS.pdf','MURU_NHSJS_NAMED_MASTER.pdf','MURU_NHSJS_SUPPORTING_INFORMATION.pdf']:
  p=ROOT/n
  if not p.exists(): errors.append(f'missing rendered PDF: {n}')
  else:
   info=subprocess.check_output(['pdfinfo',str(p)],text=True)
   pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
   if 'STANDARD_ANONYMOUS' in n and pages>20: errors.append(f'standard anonymous PDF exceeds 20 pages: {pages}')
   if 'Page size:       612 x 792 pts (letter)' not in info: errors.append(f'{n}: not US Letter')
 print(f'Abstract words: {len(words)}')
 print(f'References: {len(refs_for(ds["anonymous"]))}; Figures: 5; Supporting-information Word tables: {len(ds["si"].tables)}')
 print(f'Body parity after citation normalization: {"PASS" if a==o else "FAIL"}')
 print(f'Checks: {22-len(errors) if errors else 22}/{22} PASS' if not errors else '\n'.join(errors))
 if errors: raise SystemExit(1)
if __name__=='__main__': main()
