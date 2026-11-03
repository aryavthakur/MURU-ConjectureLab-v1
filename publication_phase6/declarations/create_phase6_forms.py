from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
DECL=ROOT/'publication_phase6/declarations'; EXT=ROOT/'publication_phase6/external_review'

def shade(cell,color='E9EFF5'):
 tcPr=cell._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),color); tcPr.append(sh)
def base(title,subtitle):
 d=Document(); s=d.sections[0]; s.top_margin=Inches(.7);s.bottom_margin=Inches(.7);s.left_margin=Inches(.78);s.right_margin=Inches(.78)
 for nm,size in [('Normal',10.5),('Title',18),('Heading 1',13),('Heading 2',11)]:
  st=d.styles[nm];st.font.name='Aptos' if nm=='Normal' else 'Aptos Display';st.font.size=Pt(size);st.font.color.rgb=RGBColor(27,49,71) if nm!='Normal' else RGBColor(30,37,44)
  st._element.rPr.rFonts.set(qn('w:eastAsia'),st.font.name)
  if nm=='Normal': st.paragraph_format.space_after=Pt(5)
 p=d.add_paragraph(style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run(title)
 ppr=p._p.get_or_add_pPr(); pb=OxmlElement('w:pBdr'); bottom=OxmlElement('w:bottom'); bottom.set(qn('w:val'),'nil'); pb.append(bottom); ppr.append(pb)
 p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=p.add_run(subtitle);r.italic=True;r.font.size=Pt(10);r.font.color.rgb=RGBColor(80,92,106)
 d.add_paragraph('')
 return d
def footer(d,text):
 for sec in d.sections:
  p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=p.add_run(text);r.font.size=Pt(8);r.font.color.rgb=RGBColor(100,110,120)
def table(d,headers,rows,widths=None):
 t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
 for i,h in enumerate(headers):
  c=t.rows[0].cells[i];c.text=h;shade(c,'DCE6F1')
  for r in c.paragraphs[0].runs:r.bold=True;r.font.size=Pt(9)
 for row in rows:
  cells=t.add_row().cells
  for i,x in enumerate(row):
   cells[i].text=x;cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   for p in cells[i].paragraphs:
    p.paragraph_format.space_after=Pt(2)
    for r in p.runs:r.font.size=Pt(8.5)
 if widths:
  for row in t.rows:
   for i,w in enumerate(widths):row.cells[i].width=Inches(w)
 return t

# Owner confirmation form
D=base('MURU Author and Project Declaration Confirmation','Phase 6 owner review | Internal manuscript, no journal submission')
D.add_paragraph('Purpose. Please confirm or correct the author, contribution, funding, competing-interest, ethics, data-rights, and AI-assistance statements before any external circulation. The project records support some statements but do not replace the author’s personal confirmation.')
D.add_heading('1. Author identity and affiliation',level=1)
table(D,['Draft statement','Confirm / revise'],[['Author: Aryav Thakur. No affiliation or credential is stated in the manuscript.','☐ Confirm  ☐ Revise: ______________________________'],['Author display name and affiliation for any external version: not supplied.','___________________________________________________']])
D.add_heading('2. Contributions',level=1)
table(D,['Proposed contribution statement','Confirm / revise'],[['Project ownership and computational research leadership','☐ Confirm  ☐ Revise: ______________________________'],['Study protocol, model-development records, and research decisions','☐ Confirm  ☐ Revise: ______________________________'],['Software and analysis contributions','☐ Confirm  ☐ Revise: ______________________________'],['Statistical analysis, figure/table preparation, and manuscript drafting/editing','☐ Confirm  ☐ Revise: ______________________________'],['Any contribution by another person that qualifies for authorship or acknowledgment','☐ None  ☐ Add: ____________________________________']])
D.add_paragraph('Contribution claims should reflect actual work, not repository ownership alone. Add names only after confirming each person’s role and consent.')
D.add_heading('3. Funding and acknowledgments',level=1)
table(D,['Statement for confirmation','Selection'],[['No project-specific funding or acknowledgments were identified in the accessible MURU records reviewed for Phase 6.','☐ Confirm  ☐ Revise / add: __________________________']])
D.add_heading('4. Competing interests and ethics',level=1)
table(D,['Statement for confirmation','Selection'],[['Competing interests: no verified statement is currently on record. Please provide the author’s actual declaration.','☐ None  ☐ Declare: __________________________________'],['The described work is a computational analysis of existing chemical/mass-spectrometry data; no human or animal participants were involved.','☐ Confirm  ☐ Revise: ______________________________'],['Institutional approval or exemption status, if applicable: not established by the files reviewed.','☐ Not applicable  ☐ Approval / exemption details: ______']])
D.add_page_break()
D.add_heading('5. Data, code, and permissions',level=1)
table(D,['Question','Owner response'],[['Confirm project ownership and the intended license for MURU-authored code, documents, figures, and derived outputs.','___________________________________________________'],['MSnLib mzML source record is CC BY 4.0; WUR source remains access-restricted in the reviewed records. Confirm whether any WUR-derived records or model artifacts may be shared with a named reviewer.','___________________________________________________'],['Confirm that public archive availability is not being treated as blanket permission for derivatives or model weights.','☐ Confirm  ☐ Correct: ______________________________']])
D.add_heading('6. AI assistance',level=1)
D.add_paragraph('Draft disclosure: AI tools assisted with repository inspection, metadata-extraction code, statistical and provenance checks, literature discovery, preparation of figures/tables and drafting/editing of the internal manuscript and review materials. The frozen experimental outcomes were not changed. No journal submission has occurred.')
table(D,['Owner decision','Response'],[['Confirm that this accurately describes assistance and project workflow.','☐ Confirm  ☐ Revise: ______________________________'],['Additional tools, human review, or AI-supported activities to record','___________________________________________________']])
D.add_heading('7. Final confirmation',level=1)
D.add_paragraph('I confirm the statements I have checked above for the intended external circulation. Any unchecked or revised declaration must be incorporated before circulation.')
table(D,['Name','Date','Signature / approval record'],[['Aryav Thakur','________________','________________________________________']])
footer(D,'MURU Phase 6 | Owner confirmation required before external circulation')
DECL.mkdir(parents=True,exist_ok=True); D.save(DECL/'AUTHOR_CONFIRMATION_FORM.docx')

# External reviewer feedback form
F=base('MURU Scientific Review Feedback Form','Internal manuscript review | Reviewer details remain blank until a real review is conducted')
F.add_paragraph('Thank you for considering a technical review of the MURU-WUR-v2 internal manuscript. Please assess only the materials you received. The current external MSnLib result is modest and conditional; the central open issue is the physical interpretation and transfer of collision-energy coordinates. You may leave any item blank or explain that it is outside your expertise.')
F.add_heading('Review record',level=1)
table(F,['Field','Reviewer entry'],[['Reviewer name and current affiliation','___________________________________________________'],['Relevant expertise','___________________________________________________'],['Date received / version reviewed','___________________________________________________'],['Materials examined (list versions/files)','___________________________________________________'],['Prior collaboration, intellectual overlap, or potential conflict','___________________________________________________']])
F.add_heading('Overall assessment',level=1)
table(F,['Question','Response'],[['Is the research question clear and scientifically useful?','☐ Yes  ☐ Partly  ☐ No  Notes: _______________________'],['Are the model and scalar endpoint adequately described?','☐ Yes  ☐ Partly  ☐ No  Notes: _______________________'],['Are the external results interpreted within their limits?','☐ Yes  ☐ Partly  ☐ No  Notes: _______________________'],['Can the supported calculations be independently reconstructed from the supplied materials?','☐ Yes  ☐ Partly  ☐ No  Notes: _______________________'],['Overall recommendation','☐ Ready for further review  ☐ Major revision  ☐ Further data needed  ☐ Other']])
F.add_heading('Collision-energy and analytical chemistry review',level=1)
table(F,['Issue / question','Evidence, concern, or requested change'],[['Are the source mzML collision-energy annotations and their units interpreted correctly?','\n\n'],['Does the manuscript distinguish eV from NCE and numerical adapter values clearly?','\n\n'],['Is the physical interpretation of the fixed adapter justified?','\n\n'],['Are cross-instrument transfer claims appropriately limited?','\n\n'],['Is μ a meaningful and reproducible fragmentation-extent endpoint?','\n\n']])
F.add_page_break()
F.add_heading('Statistical and model-evaluation review',level=1)
table(F,['Issue / question','Evidence, concern, or requested change'],[['Is the scaffold bootstrap described and interpreted correctly?','\n\n'],['Is the 2.93% relative RMSE reduction characterized proportionately?','\n\n'],['Is the failed 5% practical criterion clear?','\n\n'],['Are adverse novelty and tail-risk findings adequately reported?','\n\n'],['Are candidate/reference implementation differences material to interpretation?','\n\n']])
F.add_page_break()
F.add_heading('Detailed comments',level=1)
for label in ['Major scientific concerns','Major methodological concerns','Data provenance or rights concerns','Minor or editorial comments','Requested revisions and supporting evidence']:
 F.add_paragraph(label,style='Heading 2');F.add_paragraph('________________________________________________________________________________\n________________________________________________________________________________\n________________________________________________________________________________')
F.add_heading('Evidence boundaries and follow-up',level=1)
table(F,['Question','Reviewer response'],[['Which conclusions are supported by the evidence reviewed?','\n\n'],['Which statements should be narrowed, qualified, or removed?','\n\n'],['What additional file, method record, or experiment would resolve remaining uncertainty?','\n\n'],['May the project team contact you with a focused follow-up question?','☐ Yes  ☐ No  Contact route provided separately']])
footer(F,'MURU Phase 6 | This form records genuine human feedback only when completed by its reviewer')
EXT.mkdir(parents=True,exist_ok=True); F.save(EXT/'REVIEWER_FEEDBACK_FORM.docx')
print('created',DECL/'AUTHOR_CONFIRMATION_FORM.docx')
print('created',EXT/'REVIEWER_FEEDBACK_FORM.docx')
