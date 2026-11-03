#!/usr/bin/env python3
from pathlib import Path
import re, subprocess
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'publication_phase6'/'external_review'
def setup(doc,title):
 sec=doc.sections[0]; sec.top_margin=Inches(.55); sec.bottom_margin=Inches(.55); sec.left_margin=Inches(.65); sec.right_margin=Inches(.65)
 n=doc.styles['Normal']; n.font.name='Times New Roman'; n.font.size=Pt(10); n._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman'); n.paragraph_format.line_spacing=1; n.paragraph_format.space_after=Pt(3)
 for name,size in [('Heading 1',12),('Heading 2',10.5)]:
  st=doc.styles[name]; st.font.name='Times New Roman'; st.font.size=Pt(size); st.font.bold=True; st.font.color.rgb=None; st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(title); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(15)
def add_md(doc,path):
 lines=path.read_text().splitlines(); i=0
 while i<len(lines):
  line=lines[i]
  if not line.strip(): i+=1; continue
  if line.startswith('# '): i+=1; continue
  if line.startswith('## '): doc.add_heading(line[3:],level=1); i+=1; continue
  if line.startswith('### '): doc.add_heading(line[4:],level=2); i+=1; continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].startswith('|'):
    vals=[x.strip() for x in lines[i].strip('|').split('|')]
    if not all(re.fullmatch(r':?-{3,}:?',x) for x in vals): rows.append(vals)
    i+=1
   t=doc.add_table(rows=0,cols=max(map(len,rows))); t.style='Table Grid'
   for ri,row in enumerate(rows):
    cells=t.add_row().cells
    for j,c in enumerate(cells):
     c.text=row[j] if j<len(row) else ''
     for p in c.paragraphs:
      for run in p.runs: run.font.name='Times New Roman'; run.font.size=Pt(8); run.bold=ri==0
   continue
  if line.startswith('- '): doc.add_paragraph(re.sub(r'[*`]','',line[2:]),style='List Bullet'); i+=1; continue
  if re.match(r'^\d+\. ',line): doc.add_paragraph(re.sub(r'[*`]','',re.sub(r'^\d+\. ','',line)),style='List Number'); i+=1; continue
  p=doc.add_paragraph(re.sub(r'[*`]','',line)); i+=1
for src_name,stem,title in [
 ('UPDATED_RESEARCH_SUMMARY_SOURCE.md','UPDATED_RESEARCH_SUMMARY','MURU-WUR-v2: Technical Summary for External Review'),
 ('UPDATED_ANALYTICAL_CHEMISTRY_PACKET_SOURCE.md','UPDATED_ANALYTICAL_CHEMISTRY_PACKET','MURU-WUR-v2: Analytical Chemistry Review Packet'),
 ('STATISTICAL_REVIEW_PACKET_SOURCE.md','STATISTICAL_REVIEW_PACKET','MURU-WUR-v2: Statistical Review Packet'),
 ('REPRODUCIBILITY_REVIEW_PACKET_SOURCE.md','REPRODUCIBILITY_REVIEW_PACKET','MURU-WUR-v2: Reproducibility Review Packet')]:
 d=Document(); setup(d,title); add_md(d,OUT/src_name); docx=OUT/(stem+'.docx'); pdf=OUT/(stem+'.pdf'); d.save(docx)
 p=subprocess.run(['/opt/homebrew/bin/soffice','--headless','--convert-to','pdf','--outdir',str(OUT),str(docx)],capture_output=True,text=True)
 if p.returncode: raise SystemExit(p.stderr)
 print(stem,pdf.stat().st_size)
