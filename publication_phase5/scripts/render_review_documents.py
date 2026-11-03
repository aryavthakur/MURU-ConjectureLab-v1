from pathlib import Path
import re, subprocess
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parents[1]; E=R/'external_review'
def setup(d,title):
 sec=d.sections[0]; sec.top_margin=Inches(.7); sec.bottom_margin=Inches(.7); sec.left_margin=Inches(.8); sec.right_margin=Inches(.8)
 n=d.styles['Normal']; n.font.name='Times New Roman'; n.font.size=Pt(11); n._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman'); n.paragraph_format.line_spacing=1.0; n.paragraph_format.space_after=Pt(5)
 p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; rr=p.add_run(title); rr.bold=True; rr.font.size=Pt(15); rr.font.name='Times New Roman'
def add_md(d,path):
 lines=path.read_text().splitlines(); i=0
 while i<len(lines):
  line=lines[i]
  if not line.strip(): i+=1; continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].startswith('|'):
    vals=[v.strip() for v in lines[i].strip('|').split('|')]
    if not all(re.fullmatch(r':?-{3,}:?',v) for v in vals): rows.append(vals)
    i+=1
   t=d.add_table(rows=0,cols=max(map(len,rows))); t.style='Table Grid'
   for ix,row in enumerate(rows):
    cells=t.add_row().cells
    for j,c in enumerate(cells):
     c.text=row[j] if j<len(row) else ''
     for p in c.paragraphs:
      for run in p.runs: run.font.name='Times New Roman'; run.font.size=Pt(8); run.bold=ix==0
   continue
  if line.startswith('# '): i+=1; continue
  if line.startswith('## '): d.add_heading(line[3:],level=1); i+=1; continue
  if line.startswith('### '): d.add_heading(line[4:],level=2); i+=1; continue
  if line.startswith('- ') or line.startswith('* '): d.add_paragraph(line[2:],style='List Bullet'); i+=1; continue
  if re.match(r'^\d+\. ',line): d.add_paragraph(re.sub(r'^\d+\. ','',line),style='List Number'); i+=1; continue
  d.add_paragraph(re.sub(r'[*`]','',line)); i+=1

def render(src,stem,title):
 d=Document(); setup(d,title); add_md(d,src); out=E/(stem+'.docx'); d.save(out)
 subprocess.run(['/opt/homebrew/bin/soffice','--headless','--convert-to','pdf','--outdir',str(E),str(out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 print(out.name, (E/(stem+'.pdf')).stat().st_size)
render(E/'RESEARCH_SUMMARY_SOURCE.md','RESEARCH_SUMMARY','MURU-WUR-v2: Technical Summary for External Review')
render(E/'ANALYTICAL_CHEMISTRY_REVIEW_PACKET_SOURCE.md','ANALYTICAL_CHEMISTRY_REVIEW_PACKET','MURU-WUR-v2: Analytical Chemistry Review Packet')
render(E/'STATISTICAL_REVIEW_PACKET_SOURCE.md','STATISTICAL_REVIEW_PACKET','MURU-WUR-v2: Statistical Review Packet')
# reproducibility review packet: standalone synthesis of README, source notes, and final audit
p=E/'REPRODUCIBILITY_REVIEW_PACKET_SOURCE.md'
p.write_text('# Reproducibility review packet\n\n## Purpose and scope\nThis packet supports review of statistical reconstruction from permitted frozen outputs. It does not claim raw mzML reprocessing, model retraining, or independent experimental replication.\n\n## Instructions\n'+(E/'repro/README.md').read_text()+'\n\n## Source notes\n'+(E/'repro/SOURCE_NOTES.md').read_text()+'\n\n## Phase 5 fresh-extraction findings\n'+(R/'verification/FINAL_REPRODUCIBILITY_REPORT.md').read_text())
render(p,'REPRODUCIBILITY_REVIEW_PACKET','MURU-WUR-v2: Reproducibility Review Packet')
# feedback form
f=Document(); setup(f,'MURU-WUR-v2 External Scientific Review Feedback Form')
for label in ['Reviewer name (optional):','Professional role / relevant expertise:','Institution or affiliation (optional):','Review date:','Materials and versions examined:','Overall assessment:']:
 p=f.add_paragraph(); r=p.add_run(label); r.bold=True; f.add_paragraph('________________________________________________________________________________')
for label in ['Scientific concerns','Methodological concerns','Data interpretation concerns','Requested clarifications','Recommended manuscript revisions','Severity (critical / major / moderate / minor / editorial)','Evidence and source supporting each concern','Follow-up questions']:
 f.add_heading(label,level=2)
 for _ in range(3): f.add_paragraph('________________________________________________________________________________')
f.add_paragraph('This form records independent human feedback if completed by a reviewer. Its preparation does not imply that a review has occurred.')
f.save(E/'REVIEWER_FEEDBACK_FORM.docx')
subprocess.run(['/opt/homebrew/bin/soffice','--headless','--convert-to','pdf','--outdir',str(E),str(E/'REVIEWER_FEEDBACK_FORM.docx')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print('REVIEWER_FEEDBACK_FORM.pdf', (E/'REVIEWER_FEEDBACK_FORM.pdf').stat().st_size)
