#!/usr/bin/env python3
"""Apply only evidence-driven collision-energy clarifications to Phase 5 source."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
PH5=ROOT/'publication_phase5'
OUT=ROOT/'publication_phase6'/'manuscript'
OUT.mkdir(parents=True,exist_ok=True)

def renumber(md):
    parts=md.split('## References',1)
    body,refs=parts[0],parts[1]
    def cite(m):
        vals=[]
        for item in re.split(r',\s*',m.group(1)):
            x=re.fullmatch(r'(\d+)[–-](\d+)',item)
            if x: vals.extend(range(int(x.group(1)),int(x.group(2))+1))
            else:
                try: vals.append(int(item))
                except ValueError: return m.group(0)
        vals=[n+(3 if n>=13 else 0) for n in vals]
        out=[]; i=0
        while i<len(vals):
            j=i
            while j+1<len(vals) and vals[j+1]==vals[j]+1: j+=1
            out.append(str(vals[i]) if i==j else f'{vals[i]}–{vals[j]}'); i=j+1
        return '['+','.join(out)+']'
    body=re.sub(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]',cite,body)
    lines=refs.splitlines(); new=[]
    for ln in lines:
        m=re.match(r'^(\d+)\.\s',ln)
        if m and int(m.group(1))>=13:
            n=int(m.group(1))+3; ln=re.sub(r'^\d+\.',f'{n}.',ln,1)
        new.append(ln)
    # Insert three verifiable primary/data/standard references after existing #12.
    inserted=[
      '13. Brungs, C.; Schmid, R.; Pluskal, T. MsnLib multi-stage fragmentation mass spectral libraries - mzml positive and negative. Version 5. Zenodo, 2025. https://doi.org/10.5281/zenodo.15683784. CC BY 4.0.',
      '14. Mayer, G.; Montecchi-Palazzi, L.; Ovelleiro, D.; et al. The HUPO proteomics standards initiative—mass spectrometry controlled vocabulary. Database (Oxford). 2013;2013:bat009. https://doi.org/10.1093/database/bat009.',
      '15. Thermo Fisher Scientific. Orbitrap ID-X Method Editor Help: Activation parameters. Official instrument documentation, accessed 3 November 2026. https://docs.thermofisher.com/r/Orbitrap-ID-X-Method-Editor-Help/2912190859v1en-US2912274187.'
    ]
    # Find the end of reference 12, insert before old #13 now renumbered #16.
    idx=next((i for i,x in enumerate(new) if x.startswith('16. ')),None)
    if idx is None: raise ValueError('could not find shifted reference 13')
    new[idx:idx]=inserted
    return body+'## References'+'\n'.join(new)

src=(PH5/'manuscript/MURU_PHASE5_MANUSCRIPT_SOURCE.md').read_text()
# Replace abstract as a whole to keep the new verified distinction clear and within the target word count.
start=src.index('## Abstract')
end=src.index('\n## 1. Introduction',start)
kwline=next(x for x in src[start:end].splitlines() if x.startswith('**Keywords:**'))
abstract='''## Abstract

**Background and objective.** Collision-induced dissociation produces energy-dependent product-ion distributions. We tested whether molecular structure improves prediction of a scalar fragmentation-extent trajectory and whether a frozen model transfers to an external chemical library. **Methods.** MURU-WUR-v2 predicts a one-scale response profile from 12 molecular descriptors and radius-2 Morgan count features. The external analysis compared a frozen candidate with a separately selected descriptor-only ridge on a replacement MSnLib population using a paired scaffold bootstrap with 10,000 whole-scaffold resamples. The scope was positive-mode HCD at two fixed measured rungs, not full-spectrum prediction. **Results.** Of 1,794 measured compounds, five were outside either model's profile support; 1,789 compounds in 1,687 scaffolds were scored. Candidate and reference pooled RMSE were 0.1296115107 and 0.1335276112 (ratio 0.9706719801; 95% interval 0.9523611880–0.9892672062), a 2.9328% relative reduction. The interval excluded one, but the prespecified 5% practical-improvement threshold was not met. The selected converted mzML records encode collision energy in electronvolts, while native-method and RAW-to-mzML provenance remain incomplete; the fixed adapter is not a physical conversion. Tail-risk improvement was not demonstrated, and the least-similar structural quartile had a ratio near 1.0083. **Conclusion.** The frozen result is modest external confirmation for this scalar endpoint under its numerical analysis conditions; it does not establish calibrated cross-instrument energy transfer or general superiority.'''
src=src[:start]+abstract+'\n\n'+kwline+src[end:]
old='''The MSnLib primary article reports 20 eV and 60 eV for its ID-X MS2 library acquisition [12]. The nine source archives used here lack the native method metadata needed to reconcile those descriptions. We therefore call them recorded numeric settings 20 and 60 and leave their physical units unresolved. The frozen map remains a numerical adapter; it is not validated energy calibration.'''
new='''The MSnLib primary article reports ID-X MS2 settings of 20 eV and 60 eV [12], and the v5 Zenodo record identifies converted flow-injection Orbitrap ID-X mzML for the nine library families used here [13]. Phase 6 verified the frozen member hashes and selected scan identifiers; the selected mzML records encode collision energy with PSI-MS term `MS:1000045` and unit `UO:0000266` (electronvolt) [14]. This establishes the converted-file annotation for those records. The native Xcalibur method files, source-specific conversion logs, and exact RAW-to-mzML checksum links were not recovered, so the original method setting and metadata-conversion history are not independently authenticated. The frozen protocol had called the numeric values NCE 20 and 60; the code selected by numeric value and did not implement an eV-to-NCE conversion. We therefore describe them as converted mzML eV annotations under a fixed numeric model adapter, not as validated physical calibration.'''
assert old in src
src=src.replace(old,new)
pattern=r"The frozen development adapter maps the LCSB nominal coordinate `E_LCSB`.*?conversion \[2,14–15,25\]\."
new_energy="The frozen development adapter maps the LCSB nominal coordinate `E_LCSB` to the WUR coordinate `T(E) = a + bE`, with `a = −5.95552603907965` and `b = 0.8618030610784555`. For external deployment the adapter applies the inverse to the numeric rung: `E_LCSB = (rung − a)/b`. The selected converted mzML scans encode the rung as collision energy (`MS:1000045`) in electronvolts (`UO:0000266`), while the original protocol labeled the same numbers NCE [13–15]. The original Xcalibur methods and verified raw-file links were not recovered. Thermo ID-X documentation distinguishes normalized percentage from absolute voltage modes [15]; it does not identify the mode used in these historical runs. The frozen adapter did not convert eV to NCE and is not a physical calibration. The A0 protocol also assumed ID-X NCE equaled IQ-X NCE; its anchor gate failed its absolute-agreement thresholds: A0 median |Δμ| at setting 20 was 0.0501 versus the 0.05 limit; A1 pooled RMSD was 0.0811 versus 0.08; A2 median |Δμ| at setting 20 was 0.0506. The frozen primary comparison remains a model-to-model comparison under A0 on the same measured endpoint, but it does not establish absolute trajectory agreement or physical cross-instrument energy transfer. The affine adapter is computational, not a physical eV-to-NCE conversion [2,15,16–18]."
src,n=re.subn(pattern,new_energy,src,count=1)
if n!=1: raise ValueError(f'2.6 energy paragraph match count {n}')
src=src.replace('Energy interpretation is a major limitation. The numeric adapter is computationally reproducible and was not fit to the MSnLib outcomes, but its physical interpretation is not validated. The MSnLib publication describes its Orbitrap ID-X MS2 settings as 20 eV and 60 eV, whereas the frozen MURU protocol labels the selected numeric values NCE 20 and 60. The evaluated archives do not contain the instrument method files needed to resolve that discrepancy.', 'Energy interpretation remains a major limitation. The selected converted mzML records encode the collision-energy values 20 and 60 with electronvolt units, consistent with the MSnLib article’s ID-X acquisition description [12–14]. The original Xcalibur methods, conversion history, and verified RAW-to-mzML checksum links were not recovered. The MURU protocol had labeled these values NCE; the frozen code selected numeric values and did not convert eV to NCE. Thus the converted-file unit annotation is established for the selected records, but native-method semantics and the physical relationship to the WUR/IQ-X energy coordinate remain unverified.')
src=src.replace('On the frozen MSnLib population and fixed deployment energy map, MURU-WUR-v2 achieved a lower pooled fragmentation-extent RMSE than the Tier A reference, with a ratio of 0.9707 (95% scaffold-bootstrap interval 0.9524–0.9893). The gain was statistically directional but smaller than the prespecified 5% practical-improvement threshold. No tail-risk advantage was demonstrated, and performance did not improve in the least-similar structural quartile. The defensible conclusion is modest external confirmation for this two-rung, positive-mode scalar endpoint, with unresolved source-specific energy units, a failed absolute-agreement anchor gate, and limited transfer to the least-similar chemistry.', 'On the frozen MSnLib population and numerical adapter, MURU-WUR-v2 achieved a lower pooled fragmentation-extent RMSE than the Tier A reference, with a ratio of 0.9707 (95% scaffold-bootstrap interval 0.9524–0.9893). The gain was statistically directional but smaller than the prespecified 5% practical-improvement threshold. No tail-risk advantage was demonstrated, and performance did not improve in the least-similar structural quartile. The selected converted mzML records annotate the settings in eV, but native-method provenance and physical transfer to the WUR/IQ-X coordinate remain unresolved; the A0 absolute-agreement gate failed.')
src=src.replace('two external recorded numeric settings whose physical units remain unresolved.', 'two external settings whose selected converted mzML records encode electronvolts, while the native-method provenance and physical cross-instrument comparability remain unresolved.')
src=src.replace('The energy interface is unresolved; the most novel quartile shows no candidate advantage;', 'The physical energy interface is unresolved despite converted-file eV annotations; the most novel quartile shows no candidate advantage;')
src=src.replace('![Figure 3. Per-rung RMSE and compound error summaries. Upper-tail measures are descriptive; AF\'s scaffold-bootstrap difference interval includes zero.](../figures/FIGURE_3/figure_3.png)', '![Figure 3. Per-rung RMSE and compound error summaries at recorded settings 20 and 60. The selected mzML records annotate these values in eV, but native method provenance and physical energy mapping remain unverified. Upper-tail measures are descriptive; AF\'s scaffold-bootstrap difference interval includes zero.](../figures/FIGURE_3/figure_3.png)')
# Add exact v5 and controlled vocabulary citations to the source evidence statement and method.
src=src.replace('The selected converted mzML scans encode the rung as collision energy (`MS:1000045`) in electronvolts (`UO:0000266`), while the original protocol labeled the same numbers NCE [13–15].', 'The selected converted mzML scans encode the rung as collision energy (`MS:1000045`) in electronvolts (`UO:0000266`), while the original protocol labeled the same numbers NCE [13–15].')
src=renumber(src)
# Citations to newly inserted references retain their new sequential numbers;
# the general renumberer shifts the legacy citations at 13 and above.
src=src.replace('used here [16]. Phase 6 verified', 'used here [13]. Phase 6 verified')
src=src.replace('(electronvolt) [17]. This establishes', '(electronvolt) [14]. This establishes')
src=src.replace('electronvolts (`UO:0000266`), while the original protocol labeled the same numbers NCE [16–18].', 'electronvolts (`UO:0000266`), while the original protocol labeled the same numbers NCE [13–15].')
src=src.replace('voltage modes [18]; it does not identify', 'voltage modes [15]; it does not identify')
src=src.replace('conversion [2,18–21].', 'conversion [2,17–18,28].')
src=src.replace('The frozen protocol labels the external MSnLib settings as HCD NCE 20 and 60, while the peer-reviewed MSnLib paper describes its library MS2 settings as 20 eV and 60 eV. The MSnLib primary article reports ID-X MS2 settings of 20 eV and 60 eV [12],', 'The frozen protocol labels the external MSnLib settings as HCD NCE 20 and 60. The MSnLib primary article reports ID-X MS2 settings of 20 eV and 60 eV [12],')
src=src.replace('acquisition description [12,16–17].', 'acquisition description [12–14,16–17].')
(OUT/'MURU_PHASE6_MANUSCRIPT_SOURCE.md').write_text(src)
# Supplement targeted statements and citation numbering, sharing added source refs from main manuscript.
sup=(PH5/'supplement/MURU_PHASE5_SUPPORTING_INFORMATION_SOURCE.md').read_text()
sup=sup.replace('Each has measurements at two recorded numeric collision-energy settings (20 and 60; unit unresolved)', 'Each has measurements at two numeric settings (20 and 60); selected converted mzML scans annotate them in electronvolts, but native methods and RAW linkage remain unverified')
sup=sup.replace('For MSnLib, the frozen protocol calls its selected numeric settings NCE 20 and 60, but the peer-reviewed MSnLib article reports its ID-X MS2 settings as 20 eV and 60 eV. The nine evaluated files lack native method records that reconcile this discrepancy. We therefore call the values recorded numeric settings 20 and 60 and do not assign physical units.', 'For the selected MSnLib scans, Phase 6 verified converted mzML collision-energy terms with electronvolt units against allowlisted source-member hashes. The article likewise reports ID-X MS2 settings of 20 eV and 60 eV. However, native method files, conversion logs, and exact RAW-to-mzML checksum links remain unavailable; the original protocol called the values NCE. We therefore state that converted mzML encodes eV while native setting and physical energy comparability remain unverified.')
sup=sup.replace('Recorded setting 20 (unit unresolved)', 'Recorded setting 20 (converted mzML eV annotation)')
sup=sup.replace('Recorded setting 60 (unit unresolved)', 'Recorded setting 60 (converted mzML eV annotation)')
sup=sup.replace('two external numeric settings with unresolved physical units', 'two external settings whose converted mzML records encode eV but whose native methods and cross-instrument comparability remain unresolved')
# Shift existing citation numbers >=13 by 3, then preserve new reference cross-references as #13-15.
def shift_cite(m):
 vals=[]
 for item in re.split(r',\s*',m.group(1)):
  x=re.fullmatch(r'(\d+)[–-](\d+)',item)
  vals.extend(range(int(x.group(1)),int(x.group(2))+1)) if x else vals.append(int(item))
 vals=[n+3 if n>=13 else n for n in vals]
 return '['+','.join(map(str,vals))+']'
sup=re.sub(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]',shift_cite,sup)
sup=sup.replace('For the selected MSnLib scans, Phase 6 verified converted mzML collision-energy terms with electronvolt units against allowlisted source-member hashes. The article likewise reports ID-X MS2 settings of 20 eV and 60 eV.', 'For the selected MSnLib scans, Phase 6 verified converted mzML collision-energy terms with electronvolt units against allowlisted source-member hashes [12–14]. The v5 repository describes the converted ID-X collection [13], and the ID-X manual distinguishes normalized and absolute settings [15].')
(OUT/'MURU_PHASE6_SUPPORTING_INFORMATION_SOURCE.md').write_text(sup)
print('wrote manuscript + SI source; abstract words',len(re.findall(r"\b[\wμ]+(?:[’'-][\w]+)*\b",abstract)))
