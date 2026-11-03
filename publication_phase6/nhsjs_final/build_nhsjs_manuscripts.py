#!/usr/bin/env python3
"""Build the three NHSJS manuscript versions from Phase 6 source using official templates."""
from __future__ import annotations
import re, shutil, subprocess, zipfile, hashlib, json
from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT=Path(__file__).resolve().parents[2]
P6=ROOT/'publication_phase6'; OUT=P6/'nhsjs_final'
TEMPLATES=OUT/'source_templates'
TEMPLATE_URLS={
 'standard':'https://nhsjs.com/wp-content/uploads/2026/07/NHSJS-Manuscript-Template-Standard-Citations.docx',
 'online':'https://nhsjs.com/wp-content/uploads/2026/07/NHSJS-Manuscript-Template-Online-Citations.docx',
}
SOURCE=P6/'manuscript/MURU_PHASE6_MANUSCRIPT_SOURCE.md'
TITLE='Predicting Collision-Energy-Dependent Fragmentation Extent from Molecular Structure: Development and External Evaluation of MURU-WUR-v2'
TOKEN=re.compile(r'\[(\d+(?:[,–-]\d+)*)\]|(\*\*.+?\*\*)|(\*.+?\*)|`([^`]+)`')

def ensure_templates():
 TEMPLATES.mkdir(parents=True,exist_ok=True)
 for key,url in TEMPLATE_URLS.items():
  target=TEMPLATES/f'NHSJS-Manuscript-Template-{key.title()}-Citations.docx' if key=='standard' else TEMPLATES/'NHSJS-Manuscript-Template-Online-Citations.docx'
  if not target.exists():
   subprocess.run(['curl','-fL',url,'-o',str(target)],check=True)

def parse_refs(text):
 before, refs_text=text.split('## References',1)
 refs={}
 for m in re.finditer(r'^(\d+)\.\s+(.*)$',refs_text,re.M): refs[int(m.group(1))]=m.group(2).strip()
 if sorted(refs)!=list(range(1,len(refs)+1)): raise ValueError('Reference IDs must be contiguous before remapping')
 return before,refs

def split_sections(lines):
 blocks=[]; cur=[]
 for line in lines:
  if line.startswith('### ') and cur:
   blocks.append(cur); cur=[line]
  else: cur.append(line)
 if cur: blocks.append(cur)
 return blocks

def cite_ids(raw):
 out=[]
 for part in raw.split(','):
  part=part.strip(); m=re.fullmatch(r'(\d+)[–-](\d+)',part)
  out.extend(range(int(m.group(1)),int(m.group(2))+1) if m else [int(part)])
 return out

def reorder_result_subsections(lines):
 # Put the error/tail figure before the structural-novelty figure to meet first-citation order.
 starts={}
 for i,line in enumerate(lines):
  if line.startswith('### 3.5 Structural novelty'): starts['novelty']=i
  if line.startswith('### 3.6 Error distributions and tail performance'): starts['errors']=i
 if set(starts)!={'novelty','errors'}: raise ValueError('Could not locate Results 3.5/3.6 blocks')
 a,b=starts['novelty'],starts['errors']
 if a>b: return lines
 end=len(lines)
 for i in range(b+1,len(lines)):
  if lines[i].startswith(('### ','## ')): end=i; break
 novelty=lines[a:b]; errors=lines[b:end]
 novelty[0]='### 3.6 Structural novelty'
 errors[0]='### 3.5 Error distributions and tail performance'
 return lines[:a]+errors+novelty+lines[end:]

def replace_internal_refs(refs):
 base='https://github.com/aryavthakur/MURU-ConjectureLab-v1/tree/bfa153e828e08b3c7e674ef7fe9d6818d14a2b61'
 replacements={
 16:f'A. Thakur. MURU-WUR-v2 development protocol, final candidate freeze, and final report. MURU-ConjectureLab-v1. 2026. Files: MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md; MURU_WUR_V2_FINAL_CANDIDATE_FREEZE.md; MURU_WUR_V2_FINAL_REPORT.md. {base}.',
 17:f'A. Thakur. MURU-WUR-v2 MSnLib Confirmation Study 2 protocol, freeze, and result. MURU-ConjectureLab-v1. 2026. Files: MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md; MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md; MURU_V2_MSNLIB_CONFIRMATION_V2_RESULT.md. {base}.',
 18:f'A. Thakur. MURU-WUR-v2 MSnLib Confirmation Study 2 analysis code and frozen outputs. MURU-ConjectureLab-v1. 2026. Files: scripts/wur_v2_confirmation_v2/11_external_analysis.py; artifacts/wur_v2_confirmation_v2/result/external_analysis.json; artifacts/wur_v2_confirmation_v2/result/measured_mu.csv. {base}.',
 19:f'A. Thakur. MURU-WUR-v2 exposure and data registry. MURU-ConjectureLab-v1. 2026. File: MURU_V2_EXPOSURE_AND_DATA_REGISTRY.md. {base}.',
 22:f'A. Thakur. MURU-WUR-v2 review adjudication and statistical review records. MURU-ConjectureLab-v1. 2026. File: MURU_WUR_V2_REVIEW_ADJUDICATION.md. {base}.',
 24:f'A. Thakur. MURU-WUR-v2 development split and population audit. MURU-ConjectureLab-v1. 2026. File: artifacts/p2_split_audit.json. {base}.',
 29:f'A. Thakur. MURU public comparator benchmark preregistration, record chain, and result. MURU-ConjectureLab-v1. 2026. Files: MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md; MURU_COMPARATOR_BENCHMARK_RECORD_CHAIN.md; MURU_COMPARATOR_BENCHMARK_RESULT.md. {base}.',
 30:f'A. Thakur. MURU collision-energy-interface adjudication Design A preregistration and result. MURU-ConjectureLab-v1. 2026. Files: MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_PREREGISTRATION.md; MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_RESULT.md. {base}.',
 31:f'A. Thakur. MURU-WUR-v2 reproducibility manifest and full-repository regression verification. MURU-ConjectureLab-v1. 2026. File: MURU_V2_REPRODUCIBILITY_MANIFEST.md. {base}.',
  }
 for k,v in replacements.items(): refs[k]=v
 # Apply sentence-case and NHSJS journal-style formatting to entries with clear metadata.
 refs[1]=refs[1].replace('A powerful tool for natural product', 'a powerful tool for natural product')
 refs[13]=refs[13].replace('Brungs, C.; Schmid, R.; Pluskal, T.', 'C. Brungs, R. Schmid, T. Pluskal.')
 refs[4]=refs[4].replace('CFM-ID 4.0: More accurate', 'CFM-ID 4.0: more accurate')
 refs[6]=refs[6].replace('FIORA: Local neighborhood-based', 'FIORA: local neighborhood-based')
 refs[15]=refs[15].replace('Orbitrap ID-X Method Editor Help: Activation parameters', 'Orbitrap ID-X Method Editor Help: activation parameters')
 refs[32]=refs[32].replace('GLACIER: Rethinking Mass Spectrum Prediction as an Object Detection Problem', 'GLACIER: Rethinking mass spectrum prediction as an object detection problem')
 refs[12]=refs[12].replace('Nature Methods. 22(10):2028–2031, 2025.', 'Nature Methods. Vol. 22(10), pg. 2028–2031, 2025,')
 refs[26]=refs[26].replace('Introduction to linear regression analysis, 5th ed.', '*Introduction to linear regression analysis*, 5th ed.')
 refs[27]=refs[27].replace('Creation of an Open-Access High-Resolution Tandem Mass Spectral Library of 1000 Food Toxicants. Analytical Chemistry. 97(43):23822–23830, 2025.', 'Creation of an open-access high-resolution tandem mass spectral library of 1000 food toxicants. Analytical Chemistry. Vol. 97(43), pg. 23822–23830, 2025,')
 refs[28]=refs[28].replace('https://docs.thermofisher.com/.', 'n.d. (accessed 3 November 2026). https://docs.thermofisher.com/.')
 refs[25]=refs[25].replace('https://www.rdkit.org/docs/.', '2026 (version 2026.03.5; accessed 3 November 2026). https://www.rdkit.org/docs/.')
 refs[33]=refs[33].replace('Brungs, C.; Schmid, R.; Pluskal, T.', 'C. Brungs, R. Schmid, T. Pluskal.')
 refs[34]=refs[34].replace('dataset MSV000094528. MassIVE, CC0 1.0, accessed', 'dataset MSV000094528. MassIVE, CC0 1.0, accessed')
 return refs

def source_restructure():
 text=SOURCE.read_text(encoding='utf-8')
 lines=text.splitlines()
 # Figure 3/error subsection precedes Figure 4/novelty subsection.
 lines=reorder_result_subsections(lines)
 # Move the substantive conclusion and limitations into the NHSJS Discussion section.
 start=next(i for i,l in enumerate(lines) if l=='## 5. Conclusion')
 decl=next(i for i,l in enumerate(lines) if l=='## Declarations')
 conclusion=lines[start+1:decl]
 conclusion=[('### Conclusion' if l=='## 5. Conclusion' else l) for l in lines[start:decl]]
 lines=lines[:start]+lines[decl:]
 # Reinsert Conclusion as the closing subsection of Discussion, immediately before Acknowledgments.
 ack=next(i for i,l in enumerate(lines) if l=='## Declarations')
 # Move the detailed limitations declaration into the Discussion, retaining all substantive content.
 limitation=[]
 for i,l in enumerate(lines[ack+1:],ack+1):
  if l.startswith('**Research limitations.**'):
   limitation=[l.replace('**Research limitations.**','**Study limitations.**',1)]
   del lines[i]
   break
 discussion_end=next(i for i,l in enumerate(lines) if l=='## Declarations')
 insert=discussion_end
 lines[insert:insert]=['### Study limitations','',*limitation,'',*conclusion,'']
 # Make NHSJS section names unnumbered and use required order.
 normalized=[]
 for l in lines:
  if l=='## 1. Introduction': l='## Introduction'
  elif l=='## 2. Materials and Methods': l='## Methods'
  elif l=='## 3. Results': l='## Results'
  elif l=='## 4. Discussion': l='## Discussion'
  elif l=='## Declarations': l='## Acknowledgments'
  elif l.startswith('### '): l=re.sub(r'^###\s+\d+(?:\.\d+)*\s+', '### ', l)
  normalized.append(l)
 # Remove internal status note; named author is supplied in documents, not copied into anonymous version.
 normalized=[l for l in normalized if l.strip()!='Internal research draft; not submitted to a journal.']
 # Replace data availability wording with accurate access/reproduction scope, not a promise of redistribution.
 for i,l in enumerate(normalized):
  if l.startswith('**Data availability.**'):
   normalized[i]='**Data availability.** Frozen measured-μ tables, model predictions, and source records are retained in the MURU-ConjectureLab-v1 research repository at the frozen release commit. Access and redistribution remain subject to upstream data rights; these files are not included in this formatted manuscript package. The external statistical reconstruction is based on frozen measured values and predictions and does not reprocess raw spectra. MSnLib source records and acquisition instructions are identified in the Supporting Information.'
  if l.startswith('**Acknowledgments.**'):
   normalized[i]='**Funding and acknowledgments.** No funding or acknowledgments are recorded in the verified project files; the author should confirm this before any external submission.'
  if l.startswith('**Author contributions.**'):
   normalized[i]='**Author contributions.** Aryav Thakur is the verified project owner and lead developer. The contribution statement for study design, analysis, and manuscript preparation requires the author’s confirmation before external use.'
  if l.startswith('**Competing interests.**'):
   normalized[i]='**Competing interests.** The author declares no competing interests.'
  if l.startswith('**AI-assisted research and drafting record.**'):
   normalized[i]='**AI-assisted research and drafting.** AI tools assisted with repository and literature research, analysis-code authoring and testing, figure and table generation, manuscript drafting and editing, and document production. The frozen experimental outcomes were not altered. This internal manuscript has not been submitted to a journal.'
 text='\n'.join(normalized).strip()+'\n'
 # Normalize current/legacy source numbering to first appearance after the NHSJS figure order.
 before,refs=parse_refs(text)
 refs=replace_internal_refs(refs)
 order=[]
 for m in re.finditer(r'\[(\d+(?:[,–-]\d+)*)\]',before):
  for rid in cite_ids(m.group(1)):
   if rid not in order: order.append(rid)
 if set(order)!=set(refs): raise ValueError(f'Citation/reference mismatch; used={set(order)}, refs={set(refs)}')
 mapping={old:new for new,old in enumerate(order,1)}
 def remap_citation(m):
  vals=[mapping[x] for x in cite_ids(m.group(1))]
  return '['+','.join(map(str,vals))+']'
 before=re.sub(r'\[(\d+(?:[,–-]\d+)*)\]',remap_citation,before)
 ordered=[]
 for new,old in enumerate(order,1): ordered.append(f'{new}. {refs[old]}')
 # Ensure Markdown source figure paths work in this production directory.
 for n in range(1,6):
  before=before.replace(f'../figures/FIGURE_{n}/figure_{n}.png',f'figures/figure_{n}.png')
 source=before.rstrip()+'\n\n## References\n\n'+'\n'.join(ordered)+'\n'
 return source,mapping,refs

def font_run(run,name='Times New Roman',size=12):
 run.font.name=name; run.font.size=Pt(size)
 run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),name)

def parse_cite(raw):
 ids=[]
 for part in raw.split(','):
  part=part.strip(); m=re.fullmatch(r'(\d+)[–-](\d+)',part)
  ids.extend(range(int(m.group(1)),int(m.group(2))+1) if m else [int(part)])
 return ids

def rich_add(p,text,mode,refs,allow_cite=True):
 pos=0; last_cite=False
 for m in TOKEN.finditer(text):
  preceding=text[pos:m.start()]
  iscite=m.group(1) is not None
  if iscite and allow_cite:
   # NHSJS standard citations touch the preceding word; online citations require one space.
   preceding=preceding.rstrip()
  elif last_cite and preceding:
   pass
  if preceding:
   rr=p.add_run(preceding); font_run(rr); last_cite=False
  if iscite and allow_cite:
   ids=parse_cite(m.group(1))
   if mode=='standard':
    for j,rid in enumerate(ids):
     if j:
      rr=p.add_run(','); font_run(rr); rr.font.superscript=True
     rr=p.add_run(str(rid)); font_run(rr); rr.font.superscript=True
   else:
    rr=p.add_run(' '); font_run(rr)
    for j,rid in enumerate(ids):
     if j:
      rr=p.add_run(','); font_run(rr); rr.font.superscript=True
      rr=p.add_run(' '); font_run(rr)
     citation_text=re.sub(r'[\*`]', '', refs[rid])
     rr=p.add_run('((' + citation_text + '))'); font_run(rr)
   last_cite=True
  elif m.group(2):
   rr=p.add_run(m.group(2)[2:-2]); font_run(rr); rr.bold=True; last_cite=False
  elif m.group(3):
   rr=p.add_run(m.group(3)[1:-1]); font_run(rr); rr.italic=True; last_cite=False
  elif m.group(4):
   rr=p.add_run(m.group(4)); font_run(rr); rr.font.name='Times New Roman'; last_cite=False
  pos=m.end()
 tail=text[pos:]
 if tail:
  rr=p.add_run(tail); font_run(rr)

def clean_template(template_path):
 doc=Document(template_path)
 body=doc._element.body
 for child in list(body):
  if child.tag!=qn('w:sectPr'): body.remove(child)
 # Drop template example images and external hyperlinks before adding MURU's own figures.
 for rel in list(doc.part.rels.values()):
  if rel.reltype==RT.IMAGE or (rel.is_external and rel.reltype==RT.HYPERLINK):
   doc.part.drop_rel(rel.rId)
 # Use the official template's page and typography, but explicitly retain its 1-inch letter layout.
 sec=doc.sections[0]
 sec.page_width=Inches(8.5); sec.page_height=Inches(11)
 sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1)
 for name in ['Normal','NHSJS Title','NHSJS Section','NHSJS Subsection','NHSJS Subsubsection']:
  if name in doc.styles:
   st=doc.styles[name]
   st.font.name='Times New Roman'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
 if 'Normal' in doc.styles:
  normal=doc.styles['Normal']; normal.font.size=Pt(12); normal.paragraph_format.line_spacing=1.0
 props=doc.core_properties
 props.author=''; props.last_modified_by=''; props.title=''; props.subject=''; props.keywords=''; props.comments=''; props.category=''
 return doc

def add_figure(doc,alt,image_path,mode,refs):
 m=re.match(r'Figure\s+(\d+)\.\s*(.*)',alt)
 if not m: raise ValueError(f'Unexpected figure caption: {alt[:60]}')
 fignum,caption=m.group(1),m.group(2)
 # NHSJS template: bold the figure number, vertical bar, and first sentence; then provide detail.
 sentence_match=re.match(r'(.+?\.)(?:\s+(.*))?$',caption)
 lead=sentence_match.group(1) if sentence_match else caption
 detail=sentence_match.group(2) if sentence_match else ''
 ip=doc.add_paragraph(); ip.alignment=WD_ALIGN_PARAGRAPH.CENTER; ip.paragraph_format.keep_with_next=True; ip.paragraph_format.keep_together=True
 ip.add_run().add_picture(str(image_path),width=Inches(6.5))
 cp=doc.add_paragraph(style='Normal'); cp.paragraph_format.keep_together=True; cp.paragraph_format.space_before=Pt(3); cp.paragraph_format.space_after=Pt(8)
 r=cp.add_run(f'Figure {fignum} | {lead}'); font_run(r); r.bold=True
 if detail:
  cp.add_run(' ')
  rich_add(cp,detail,mode,refs)
 # Bold panel letter markers, if present, per template.
 for p_run in cp.runs:
  pass

def add_reference_paragraph(doc,num,text,mode,refs):
 p=doc.add_paragraph(style='Normal'); p.paragraph_format.keep_together=True; p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
 n=p.add_run(f'{num}. '); font_run(n)
 rich_add(p,text,mode,refs,allow_cite=False)

def build_document(source_text,outpath,template_path,mode,named):
 before,refdict=parse_refs(source_text)
 # final source was renumbered sequentially; text citation [n] maps directly to refdict[n].
 refs=refdict
 doc=clean_template(template_path)
 # Parse into block types while handling inline paragraphs and figure placements.
 lines=before.splitlines(); i=0; seen_title=False; after_title=False
 while i<len(lines):
  line=lines[i]
  if not line.strip(): i+=1; continue
  if line.startswith('# '):
   p=doc.add_paragraph(style='NHSJS Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
   rich_add(p,line[2:].strip(),mode,refs)
   seen_title=True; after_title=True; i+=1; continue
  if line.strip()=='**Aryav Thakur**':
   if named:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(8)
    r=p.add_run('Aryav Thakur'); font_run(r); r.bold=True
   i+=1; continue
  if line == '## Acknowledgments' and not named:
   # NHSJS blind-review copy omits the acknowledgments/declarations block.
   break
  if line.startswith('## '):
   heading=line[3:].strip()
   p=doc.add_paragraph(style='NHSJS Section'); rich_add(p,heading,mode,refs,allow_cite=False)
   i+=1; continue
  if line.startswith('### '):
   heading=line[4:].strip()
   p=doc.add_paragraph(style='NHSJS Subsection'); rich_add(p,heading,mode,refs,allow_cite=False)
   i+=1; continue
  if line.startswith('!['):
   m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
   if not m: raise ValueError('Bad figure markdown')
   img=(OUT/m.group(2)).resolve()
   if not img.is_file(): raise FileNotFoundError(img)
   add_figure(doc,m.group(1),img,mode,refs); i+=1; continue
  # collect paragraph, folding Markdown source wraps without absorbing a heading or image.
  para=[line.strip()]; i+=1
  while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','![')):
   para.append(lines[i].strip()); i+=1
  text=' '.join(para)
  p=doc.add_paragraph(style='Normal')
  if text.startswith('**Keywords:**'):
   rich_add(p,text,mode,refs)
  elif re.match(r'^(?:μ\s*=|\(b̂₀, β̂\)|μ̂_i\(E\))',text):
   p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_together=True
   rich_add(p,text,mode,refs)
   for r in p.runs: r.bold=False
  else:
   rich_add(p,text,mode,refs)
  p.paragraph_format.widow_control=True
 # Add reference list, including the same full entries used in online in-text citations.
 p=doc.add_paragraph(style='NHSJS Section'); p.add_run('References')
 for num,ref in refs.items(): add_reference_paragraph(doc,num,ref,mode,refs)
 props=doc.core_properties
 if mode=='standard' and not named:
  props.author=''; props.last_modified_by=''; props.title=''; props.subject=''; props.keywords=''; props.comments=''
 else:
  props.author='Aryav Thakur'; props.last_modified_by='Aryav Thakur'; props.title=TITLE; props.subject='NHSJS-formatted internal research manuscript'; props.keywords='MURU-WUR-v2; fragmentation extent; mass spectrometry'
 outpath.parent.mkdir(parents=True,exist_ok=True); doc.save(outpath)
 return outpath

def main():
 ensure_templates()
 src,mapping,_=source_restructure()
 outsrc=OUT/'MURU_NHSJS_SOURCE.md'; outsrc.write_text(src,encoding='utf-8')
 # copy figure source assets into final folder; Markdown image links are relative to this source file.
 figdir=OUT/'figures'; figdir.mkdir(exist_ok=True)
 for n in range(1,6):
  original=P6/f'figures/FIGURE_{n}'
  for ext in ['png','svg','pdf']:
   shutil.copy2(original/f'figure_{n}.{ext}',figdir/f'figure_{n}.{ext}')
 standard_template=TEMPLATES/'NHSJS-Manuscript-Template-Standard-Citations.docx'
 online_template=TEMPLATES/'NHSJS-Manuscript-Template-Online-Citations.docx'
 named=OUT/'MURU_NHSJS_NAMED_MASTER.docx'; online=OUT/'MURU_NHSJS_ONLINE_CITATIONS.docx'; anon=OUT/'MURU_NHSJS_STANDARD_ANONYMOUS.docx'
 build_document(src,named,standard_template,'standard',True)
 build_document(src,online,online_template,'online',True)
 build_document(src,anon,standard_template,'standard',False)
 titlepath=OUT/(TITLE+'.docx'); shutil.copy2(anon,titlepath)
 # Preserve the Phase 6 supplement, prevent table-row splits, repeat table headers,
 # and shorten the final archive-listing paragraph to avoid an orphan seventh page.
 si_path=OUT/'MURU_NHSJS_SUPPORTING_INFORMATION.docx'
 shutil.copy2(P6/'supplement/MURU_PHASE6_SUPPORTING_INFORMATION.docx',si_path)
 si=Document(si_path)
 old_tail='The nested NIH nih_positive_mzml.7z member had a verified outer ZIP size of 1,040,150,902 bytes and CRC-32 8d41051a; its listing contained 535 .mzML names and one directory entry, with no method-like extension. Only the listing was inspected. These archive checks narrow the search but do not authenticate a native method or source-to-run identity beyond the single exact RAW/mzML file match. Detailed per-member summaries and hashes are retained in the Phase 6 metadata directory; binary method payloads are not distributed.'
 new_tail='The nested NIH archive listing records 535 mzML names and no method-like extensions; only the listing was inspected. It does not authenticate a native method or exact run identity beyond the single RAW/mzML hash match. Per-member hashes are retained in Phase 6; binary methods are not distributed.'
 for para in si.paragraphs:
  if para.text==old_tail:
   para.text=new_tail
   break
 for table in si.tables:
  for ri,row in enumerate(table.rows):
   trPr=row._tr.get_or_add_trPr()
   if trPr.find(qn('w:cantSplit')) is None: trPr.append(OxmlElement('w:cantSplit'))
   if ri==0 and trPr.find(qn('w:tblHeader')) is None:
    header=OxmlElement('w:tblHeader'); header.set(qn('w:val'),'true'); trPr.append(header)
 si.save(si_path)
 print('citation old->new mapping:',mapping)
 print('built:',anon,online,named,titlepath)
if __name__=='__main__': main()
