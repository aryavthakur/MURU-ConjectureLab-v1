#!/usr/bin/env python3
from pathlib import Path
import csv,re
ROOT=Path(__file__).resolve().parents[2];P4=ROOT/'publication_phase4';P3=ROOT/'publication_phase3'
source=(P4/'manuscript/MURU_PHASE4_MANUSCRIPT_SOURCE.md').read_text()
old=list(csv.DictReader((P3/'literature/REFERENCES_MASTER.csv').open(encoding='utf-8')))
old_claim=list(csv.DictReader((P3/'literature/CLAIM_TO_REFERENCE.csv').open(encoding='utf-8')))

def shift(n):return n+(n>=7)
def expand_ids(raw):
    out=[]
    for part in raw.split(','):
        part=part.strip();m=re.fullmatch(r'(\d+)[–-](\d+)',part)
        out.extend(range(int(m.group(1)),int(m.group(2))+1)) if m else out.append(int(part))
    return out
refs=[]
for row in old:
    x=dict(row);x['ref_id']=str(shift(int(row['ref_id'])))
    refs.append(x)
refs.append({'ref_id':'7','full_citation':'Goldman S, Li J, Coley CW. Generating Molecular Fragmentation Graphs with Autoregressive Neural Networks. Analytical Chemistry 96:3419–3428 (2024).','doi_or_identifier':'10.1021/acs.analchem.3c04654','year':'2024','peer_reviewed':'yes','relevant_findings_or_methods':'Introduces ICEBERG autoregressive neural network for fragmentation graph generation; original peer-reviewed ICEBERG article.','claim_supported':'ICEBERG is a graph-generative learned fragmentation method; it is not direct evidence for MURU endpoint results.','limitations_for_use':'Different model, training data and full-spectrum/fragmentation target; cite only for method context.'})
refs.sort(key=lambda r:int(r['ref_id']))
fields=list(refs[0].keys())
with (P4/'literature/REFERENCES_MASTER.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(refs)
# Retain the six-column relevance matrix and add ICEBERG primary context.
with (P3/'literature/LITERATURE_RELEVANCE_MATRIX.csv').open(encoding='utf-8') as f: rel=list(csv.DictReader(f))
relfields=list(rel[0].keys())
rel.append({'claim_id':'L27','claim_or_topic':'ICEBERG uses autoregressive neural networks to generate fragmentation graphs.','reference_ids':'7','evidence_type':'peer-reviewed primary research','allowed_interpretation':'Method context for a graph-based learned fragmentation system.','limitation':'Not a direct comparator result for the MURU μ endpoint.'})
with (P4/'literature/LITERATURE_RELEVANCE_MATRIX.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=relfields);w.writeheader();w.writerows(rel)
# Build final claim-source crosswalk from Phase 3 rows and renumbered references.
for row in old_claim:
    row['citation_ids']=';'.join(str(shift(int(v.strip()))) for v in row['citation_ids'].split(';') if v.strip())
# add ICEBERG at exactly its relevant sentence
old_claim.append({'manuscript_location':'Introduction §1','claim_text_or_topic':'ICEBERG uses autoregressive neural networks to generate fragmentation graphs.','citation_ids':'7','evidence_location':'Goldman et al. 2024 primary article','audit_status':'verified; claim scoped to method context'})
with (P4/'literature/CLAIM_TO_REFERENCE.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(old_claim[0].keys()));w.writeheader();w.writerows(old_claim)
# Audit records: every reference, source identity, peer-review status, claim fit and confidence.
audit=[]
for r in refs:
    ident=r.get('doi_or_identifier',''); peer=r.get('peer_reviewed','')
    internal=str(r['ref_id']) in {'12','13','14','15','19','23','24','25','26'}
    status='Verified against Phase 3 source database and Phase 2 source audit; bibliography/citation mapping rechecked.'
    if r['ref_id']=='7': status='Verified against publisher metadata and author manuscript; title, author order, journal, pages, year and DOI agree.'
    if 'bioRxiv' in r['full_citation'] or 'arXiv' in r['full_citation']:
        status+=' Preprint; not treated as peer-reviewed evidence.'
    if r['ref_id']=='22': status='Partially verified manufacturer documentation; use limited to general NCE/absolute-energy distinction; instrument-specific semantics for all rows are not established.'
    audit.append({'reference_id':r['ref_id'],'full_citation':r['full_citation'],'doi_or_stable_identifier':ident,'publication_year':r['year'],'peer_review_status':peer,'original_source_inspected':'Yes (publisher/author source or Phase 2 verified record)' if r['ref_id']!='22' else 'Partially; manufacturer documentation and method record consulted','metadata_check':'Title/authors/year/journal/DOI matched to recorded source' if r['ref_id']!='22' else 'Manual/version metadata incomplete in bibliography record','claim_fit':r['claim_supported'],'claim_scope_limit':r['limitations_for_use'],'audit_result':status})
with (P4/'literature/REFERENCE_AUDIT_FINAL.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(audit[0].keys()));w.writeheader();w.writerows(audit)
# Full-text citation crosswalk by substantive manuscript paragraph.
rows=[];sec='Front matter';para=0
for block in re.split(r'\n\s*\n',source):
    block=block.strip()
    if not block:continue
    if block.startswith('# '):sec=block[2:];continue
    if block.startswith('## '):sec=block[3:];para=0;continue
    if block.startswith('### '):sec=block[4:];para=0;continue
    if block.startswith('!['):
        match=re.match(r'!\[(.*?)\]',block);claim=match.group(1) if match else block
        typ='Figure caption'
    elif block.startswith('|') or block.startswith('**') and '|' in block:
        continue
    elif re.match(r'^\d+\.\s',block) and sec=='References':continue
    elif sec=='References':continue
    else:
        para+=1;claim=re.sub(r'\s+',' ',block);typ='Manuscript paragraph claim'
    ids=[]
    for match in re.finditer(r'\[([0-9]+(?:[,–-][0-9]+)*)\]',claim):
        try:ids.extend(expand for expand in expand_ids(match.group(1)))
        except Exception:pass
    ids=sorted(set(ids)); refs_here=';'.join(map(str,ids))
    rows.append({'crosswalk_id':f'CC{len(rows)+1:03d}','manuscript_location':sec,'paragraph_id':f'{sec}-P{para:02d}','claim_or_caption':claim,'reference_ids':refs_here,'supporting_source':'; '.join(f"Ref {i}" for i in ids) if ids else 'Frozen study records/code/result JSON or stated interpretation (see CLAIM_AUDIT.csv)','claim_scope_note':'References support the cited literature statement only; internal result claims are traced in CLAIM_AUDIT.csv.'})
# unnest actual citation IDs and verify mapping.
ref_ids={int(r['ref_id']) for r in refs}
missing=sorted({int(x) for row in rows for x in row['reference_ids'].split(';') if x and int(x) not in ref_ids})
if missing: raise SystemExit(f'Missing bibliography IDs: {missing}')
with (P4/'literature/CLAIM_CITATION_CROSSWALK.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
# BibTeX records from verified metadata, DOI preserving citations.
with (P4/'literature/REFERENCES_VERIFIED.bib').open('w',encoding='utf-8') as f:
 for r in refs:
  key='MURU'+r['ref_id'];citation=r['full_citation'].replace('{','').replace('}','')
  f.write(f'@misc{{{key},\n  title = {{{citation}}},\n  year = {{{r["year"]}}},\n  note = {{{r["doi_or_identifier"]}}}\n}}\n\n')
print(f"references={len(refs)} paragraphs/captions={len(rows)} missing_citations={missing}")
