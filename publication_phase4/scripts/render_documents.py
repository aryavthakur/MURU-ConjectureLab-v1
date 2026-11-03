#!/usr/bin/env python3
"""Render the Phase 4 Markdown manuscript and supplement to Word and PDF."""
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
BASE=ROOT/'publication_phase4'
MAN=BASE/'manuscript'; SUP=BASE/'supplement'
SUPSRC=SUP/'MURU_PHASE4_SUPPORTING_INFORMATION_SOURCE.md'

def citation_map(md):
    refs={}; active=False
    for line in md.splitlines():
        if line.strip()=='## References': active=True; continue
        if active:
            m=re.match(r'^(\d+)\.\s+(.*)$',line)
            if m: refs[int(m.group(1))]=m.group(2).strip().replace('`','')
    return refs

def expand_ids(raw):
    out=[]
    for part in raw.split(','):
        part=part.strip(); match=re.fullmatch(r'(\d+)[–-](\d+)',part)
        if match: out.extend(range(int(match.group(1)),int(match.group(2))+1))
        else: out.append(int(part))
    return out

def sup_digits(raw):
    trans=str.maketrans('0123456789-,–','⁰¹²³⁴⁵⁶⁷⁸⁹⁻,⁻')
    return raw.translate(trans)

def inline(text,mode,refs):
    text=text.replace('`','')
    text=re.sub(r'\*\*(.*?)\*\*',r'\1',text)
    text=re.sub(r'\*(.*?)\*',r'\1',text)
    def sub(m):
        raw=m.group(1)
        try: ids=expand_ids(raw)
        except Exception: return m.group(0)
        if mode=='standard': return sup_digits(raw)
        return '§C§'.join('('+refs.get(i,str(i))+')' for i in ids)
    return re.sub(r'\[([0-9]+(?:[,–-][0-9]+)*)\]',sub,text)

def add_rich(p,text):
    parts=text.split('§C§'); p.add_run(parts[0])
    for part in parts[1:]:
        c=p.add_run(','); c.font.superscript=True
        p.add_run(' '+part)

def shade(cell,fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)

def setup(doc):
    sec=doc.sections[0]; sec.page_width=Inches(8.5); sec.page_height=Inches(11)
    sec.top_margin=Inches(.72); sec.bottom_margin=Inches(.72); sec.left_margin=Inches(.78); sec.right_margin=Inches(.78)
    normal=doc.styles['Normal']; normal.font.name='Times New Roman'; normal.font.size=Pt(12); normal.font.color.rgb=None
    normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman'); normal.paragraph_format.line_spacing=1.0; normal.paragraph_format.space_after=Pt(5)
    for name,size in [('Title',16),('Heading 1',14),('Heading 2',12)]:
        st=doc.styles[name]; st.font.name='Times New Roman'; st.font.size=Pt(size); st.font.bold=True; st.font.color.rgb=None
        st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman'); st.paragraph_format.space_before=Pt(10); st.paragraph_format.space_after=Pt(4)
        if name=='Title':
            ppr=st._element.get_or_add_pPr(); border=ppr.find(qn('w:pBdr'))
            if border is not None: ppr.remove(border)
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=footer.add_run(); r.font.name='Times New Roman'; r.font.size=Pt(9)
    for kind,val in [('begin',None),('instrText',' PAGE '),('separate',None)]:
        el=OxmlElement('w:fldChar' if kind!='instrText' else 'w:instrText')
        if kind!='instrText': el.set(qn('w:fldCharType'),kind)
        else: el.set(qn('xml:space'),'preserve'); el.text=val
        r._r.append(el)
    t=OxmlElement('w:t'); t.text='1'; r._r.append(t)
    end=OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'),'end'); r._r.append(end)

def add_md(doc,path,mode='standard'):
    raw=path.read_text(encoding='utf-8'); refs=citation_map(raw); lines=raw.splitlines(); i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1; continue
        if line.startswith('!['):
            m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
            if m:
                img=(path.parent/m.group(2)).resolve()
                if not img.exists(): img=(BASE/m.group(2).replace('../','')).resolve()
                if img.exists():
                    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next=True; p.add_run().add_picture(str(img),width=Inches(6.75))
                    cap=doc.add_paragraph(); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER; cap.paragraph_format.keep_together=True; add_rich(cap,inline(m.group(1),mode,refs))
                    for run in cap.runs: run.italic=True; run.font.size=Pt(9)
            i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                vals=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{3,}:?',v) for v in vals): rows.append(vals)
                i+=1
            cols=max(map(len,rows)); table=doc.add_table(rows=0,cols=cols); table.style='Table Grid'; table.alignment=WD_TABLE_ALIGNMENT.CENTER
            for ri,row in enumerate(rows):
                cells=table.add_row().cells
                for j,cell in enumerate(cells):
                    cell.text=inline(row[j] if j<len(row) else '',mode,refs); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    if ri==0: shade(cell,'DCE6F1')
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after=Pt(1); p.paragraph_format.line_spacing=1.0
                        for run in p.runs: run.font.name='Times New Roman'; run.font.size=Pt(8); run.bold=ri==0
            doc.add_paragraph(); continue
        if line.startswith('# '):
            p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; add_rich(p,inline(line[2:],mode,refs)); i+=1; continue
        if line.startswith('## '):
            p=doc.add_paragraph(style='Heading 1'); add_rich(p,inline(line[3:],mode,refs)); i+=1; continue
        if line.startswith('### '):
            p=doc.add_paragraph(style='Heading 2'); add_rich(p,inline(line[4:],mode,refs)); i+=1; continue
        # Wrap Markdown source lines into a single Word paragraph.
        para=[line.strip()]; i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![')):
            para.append(lines[i].strip()); i+=1
        p=doc.add_paragraph(); add_rich(p,inline(' '.join(para),mode,refs))

def render(src,stem,outdir,mode):
    doc=Document(); setup(doc); add_md(doc,src,mode)
    docx=outdir/(stem+'.docx'); doc.save(docx)
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',str(outdir),str(docx)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return docx,outdir/(stem+'.pdf')

def main():
    src=MAN/'MURU_PHASE4_MANUSCRIPT_SOURCE.md'
    outputs=[render(src,'MURU_PHASE4_MANUSCRIPT_FINAL',MAN,'standard'),render(src,'MURU_PHASE4_STANDARD_CITATIONS',MAN,'standard'),render(src,'MURU_PHASE4_ONLINE_CITATIONS',MAN,'online'),render(SUPSRC,'MURU_PHASE4_SUPPORTING_INFORMATION',SUP,'standard')]
    for d,p in outputs: print(f'{d} | {p.stat().st_size} bytes')
if __name__=='__main__': main()
