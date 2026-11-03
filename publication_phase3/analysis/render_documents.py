#!/usr/bin/env python3
"""Render manuscript and supporting information to editable Word and PDF."""
from __future__ import annotations
import re, subprocess
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"publication_phase3"
MAN=BASE/"manuscript"; SUP=BASE/"supplement"

def citation_map(md):
    refs={}
    inrefs=False
    for line in md.splitlines():
        if line.strip()=="## References": inrefs=True; continue
        if inrefs:
            m=re.match(r"^(\d+)\.\s+(.*)$",line)
            if m: refs[int(m.group(1))]=m.group(2).strip()
    return refs

def inline(s, mode, refs):
    # Simplify markdown emphasis while retaining visible text.
    s=s.replace("`","")
    s=re.sub(r"\*\*(.*?)\*\*",r"\1",s)
    s=re.sub(r"\*(.*?)\*",r"\1",s)
    def repl(m):
        try:
            ids=[]
            for part in m.group(1).split(','):
                ends=re.split(r"[–-]",part)
                if len(ends)==2: ids.extend(range(int(ends[0]),int(ends[1])+1))
                else: ids.append(int(ends[0]))
        except Exception: return m.group(0)
        if mode=="standard":
            sup={"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹","-":"⁻","–":"⁻"}
            if '–' in m.group(1) or '-' in m.group(1):
                return ''.join(sup.get(c,c) for c in m.group(1).replace('–','-').split(',')[0].split('-')[0])+"⁻"+''.join(sup.get(c,c) for c in m.group(1).replace('–','-').split(',')[0].split('-')[1])
            return "".join("".join(sup.get(c,c) for c in str(i)) for i in ids)
        return " "+", ".join("(("+refs.get(i,str(i))+"))" for i in ids)
    return re.sub(r"\[([0-9]+(?:[,–-][0-9]+)*)\]",repl,s)

def set_cell_shading(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)

def setup(doc):
    sec=doc.sections[0]; sec.top_margin=Inches(.8); sec.bottom_margin=Inches(.8); sec.left_margin=Inches(.85); sec.right_margin=Inches(.85)
    normal=doc.styles['Normal']; normal.font.name='Times New Roman'; normal.font.size=Pt(12)
    normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=footer.add_run(); run.font.name='Times New Roman'; run.font.size=Pt(9)
    begin=OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'),'begin')
    instr=OxmlElement('w:instrText'); instr.set(qn('xml:space'),'preserve'); instr.text=' PAGE '
    separate=OxmlElement('w:fldChar'); separate.set(qn('w:fldCharType'),'separate')
    display=OxmlElement('w:t'); display.text='1'
    end=OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'),'end')
    run._r.extend([begin,instr,separate,display,end])
    normal.paragraph_format.space_after=Pt(4); normal.paragraph_format.line_spacing=1.0
    for name,size in [('Title',16),('Heading 1',14),('Heading 2',12),('Heading 3',12)]:
        st=doc.styles[name]; st.font.name='Times New Roman'; st.font.size=Pt(size); st.font.bold=True
        st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
        st.paragraph_format.space_before=Pt(10); st.paragraph_format.space_after=Pt(4)

def add_md(doc,path,mode='standard'):
    raw=path.read_text(); refs=citation_map(raw); lines=raw.splitlines(); i=0; code=False; codebuf=[]
    while i<len(lines):
        line=lines[i]
        if line.startswith('```'):
            if code:
                p=doc.add_paragraph(); r=p.add_run('\n'.join(codebuf)); r.font.name='Courier New'; r.font.size=Pt(8); codebuf=[]; code=False
            else: code=True
            i+=1; continue
        if code: codebuf.append(line); i+=1; continue
        if not line.strip(): i+=1; continue
        if line.startswith('!['):
            m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
            if m:
                img=(path.parent/m.group(2)).resolve()
                if not img.exists(): img=(BASE/m.group(2).replace('../','')).resolve()
                if img.exists():
                    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(img),width=Inches(6.3))
                    cap=doc.add_paragraph(inline(m.group(1),mode,refs)); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    for r in cap.runs: r.italic=True; r.font.size=Pt(9)
            i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                vals=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{3,}:?',v) for v in vals): rows.append(vals)
                i+=1
            if rows:
                cols=max(map(len,rows)); t=doc.add_table(rows=0,cols=cols); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
                for ri,row in enumerate(rows):
                    cells=t.add_row().cells
                    for j in range(cols):
                        val=inline(row[j] if j<len(row) else '',mode,refs); cell=cells[j]; cell.text=val; cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                        if ri==0:
                            set_cell_shading(cell,'DCE6F1')
                            for run in cell.paragraphs[0].runs: run.bold=True
                        for p in cell.paragraphs:
                            p.paragraph_format.space_after=Pt(1); p.paragraph_format.line_spacing=1.0
                            for run in p.runs: run.font.name='Times New Roman'; run.font.size=Pt(8)
                doc.add_paragraph();
            continue
        if line.startswith('# '):
            p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(inline(line[2:],mode,refs)); i+=1; continue
        if line.startswith('## '): doc.add_heading(inline(line[3:],mode,refs),level=1); i+=1; continue
        if line.startswith('### '): doc.add_heading(inline(line[4:],mode,refs),level=2); i+=1; continue
        if line.startswith('- '):
            p=doc.add_paragraph(style='List Bullet'); p.add_run(inline(line[2:],mode,refs)); i+=1; continue
        if re.match(r'^\d+\.\s',line):
            p=doc.add_paragraph(style='List Number'); p.add_run(inline(re.sub(r'^\d+\.\s','',line),mode,refs)); i+=1; continue
        # Join wrapped markdown lines into a single paragraph.
        para=[line.strip()]; i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','- ','![')) and not re.match(r'^\d+\.\s',lines[i]):
            para.append(lines[i].strip()); i+=1
        p=doc.add_paragraph(); p.add_run(inline(' '.join(para),mode,refs));
    if codebuf:
        p=doc.add_paragraph(); p.add_run('\n'.join(codebuf))

def render(src,stem,outdir,mode='standard'):
    d=Document(); setup(d); add_md(d,src,mode)
    docx=outdir/(stem+'.docx'); d.save(docx)
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',str(outdir),str(docx)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return docx,outdir/(stem+'.pdf')

def main():
    src=MAN/'MURU_MANUSCRIPT_SOURCE.md'
    out=[]
    out.append(render(src,'MURU_MANUSCRIPT_MASTER',MAN,'standard'))
    out.append(render(src,'MURU_MANUSCRIPT_STANDARD_CITATIONS',MAN,'standard'))
    out.append(render(src,'MURU_MANUSCRIPT_ONLINE_CITATIONS',MAN,'online'))
    sinfo=SUP/'MURU_SUPPORTING_INFORMATION_SOURCE.md'
    out.append(render(sinfo,'MURU_SUPPORTING_INFORMATION',SUP,'standard'))
    for x in out: print(x[0].name,x[1].stat().st_size)
if __name__=='__main__': main()
