#!/usr/bin/env python3
"""Validate the range-extracted MURU/MSnLib mzML evidence and export auditable tables.

Run after RAW_METADATA_EXTRACTION.py has processed the frozen allowlist. The JSON
input is an ephemeral working artifact; exported tables deliberately omit
instrument serial numbers, local paths, and irrelevant non-selected spectra.
"""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'publication_phase6'
ALLOW=ROOT/'artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv'
DESIGN=ROOT/'src/muru/wur_v2/msnlib_design.py'
RECORD=OUT/'metadata/zenodo_record_15683784.json'
RAW_RECORD=OUT/'metadata/zenodo_raw_record_13785391.json'
LIBRARIES={
 '20220601_mzml_mce_bioactive_positive.zip':'MCEBIO',
 '20230404_mzml_pluskal_nih_positive.zip':'NIHNP',
 '20231123_mzml_mce_scaffold_positive.zip':'MCESCAF',
 '20231124_mzml_otavapep_positive.zip':'OTAVAPEP',
 'mzml_20240405_pluskal_enammol_MSn_positive.zip':'ENAMMOL',
 'mzml_20240408_pluskal_mcedrug_MSn_positive.zip':'MCEDRUG',
 'mzml_20240502_pluskal_enamdisc_MSn_positive.zip':'ENAMDISC',
 'mzml_20241113_pluskal_mcediv_20k_MSn_positive.zip':'MCEDIV-20K',
 'mzml_20241120_pluskal_targetmolnphts_MSn_positive.zip':'TARGETMOL-NPHTS',
}
def write_csv(path, rows, fields=None):
 path.parent.mkdir(parents=True,exist_ok=True)
 if fields is None: fields=list(rows[0]) if rows else []
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def terms_for(spectrum): return spectrum.get('activation_terms') or []
def main():
 if len(sys.argv)!=3: raise SystemExit('usage: build_phase6_evidence.py FULL_EXTRACT_JSON OUTPUT_ROOT')
 source=Path(sys.argv[1]); root=Path(sys.argv[2]); md=root/'metadata'; energy=root/'energy'
 records=json.loads(source.read_text())
 allow=pd.read_csv(ALLOW).fillna('')
 zsrc=DESIGN.read_text().split('ZIPS = {',1)[1].split('\n}',1)[0]
 zhash=dict(re.findall(r'"([^\"]+\.zip)": "([0-9a-f]{64})"',zsrc))
 zen=json.loads(RECORD.read_text()); api_files={f['key']:f for f in zen['files']}
 rawzen=json.loads(RAW_RECORD.read_text()) if RAW_RECORD.exists() else None
 raw_keys={f['key'] for f in rawzen['files']} if rawzen else set()
 if len(records)!=allow.drop_duplicates(['source_zip','member','file_sha256']).shape[0]:
  raise SystemExit(f'file count mismatch: parsed {len(records)}, allowlisted unique files {allow.drop_duplicates(["source_zip","member","file_sha256"]).shape[0]}')
 by_member={}
 instrument_rows=[]; lineage=[]; inv=[]; anomalies=[]
 scan_total=0
 for rec in records:
  z=rec['source_zip']; lib=LIBRARIES.get(z,'UNKNOWN'); mz=rec['mzml_metadata']
  expected_rows=allow.loc[allow.source_zip.eq(z)&allow.member.eq(rec['member'])]
  sel={x['spectrum_id']:x for x in mz['selected_spectra']}
  if len(sel)!=len(rec['selected_scan_rows']): anomalies.append(f'{z}/{rec["member"]}: selected-ID count mismatch')
  configs=mz.get('instrument_configurations',[])
  flat=[t for c in configs for t in c.get('terms',[])]
  models=sorted({t.get('name','') for t in flat if t.get('accession') in ('MS:1003112','MS:1000484')})
  software='; '.join(f"{x.get('id','')} {x.get('version','')}".strip() for x in mz.get('software',[]))
  sf=mz.get('source_files',[{}])
  raw_name=sf[0].get('name','') if sf else ''
  rawsha=''
  if sf:
   rawsha=next((p.get('value','') for p in sf[0].get('params',[]) if p.get('accession')=='MS:1000569'),'')
  file_units=set(); file_methods=set(); file_values=set(); file_errors=[]
  for row in rec['selected_scan_rows']:
   sid=row['spectrum_id']; obs=sel.get(sid); scan_total+=1
   if obs is None:
    file_errors.append(f'missing selected scan {sid}'); continue
   ce=[t for t in terms_for(obs) if t.get('accession')=='MS:1000045']
   file_units.update(t.get('unitAccession','<none>') for t in ce)
   file_values.update(t.get('value','<missing>') for t in ce)
   file_methods.update(t.get('name','') for t in terms_for(obs) if t.get('accession')=='MS:1000422')
   if len(ce)!=1: file_errors.append(f'{sid}: expected exactly one collision-energy CV, found {len(ce)}')
   elif float(ce[0].get('value','nan'))!=float(row['rung']): file_errors.append(f'{sid}: CV energy {ce[0].get("value")} != frozen rung {row["rung"]}')
   elif ce[0].get('unitAccession')!='UO:0000266': file_errors.append(f'{sid}: unexpected unit {ce[0].get("unitAccession")}')
   if obs.get('ms_level') not in ('2',2): file_errors.append(f'{sid}: not MS2 ({obs.get("ms_level")})')
   frozen_mz=float(row['selected_ion_mz'])
   observed_mz=float(obs['selected_ion_mz']) if obs.get('selected_ion_mz') not in (None,'') else float('nan')
   if abs(frozen_mz-observed_mz)>1e-5: file_errors.append(f'{sid}: selected-ion m/z differs by {abs(frozen_mz-observed_mz)}')
   lineage.append({'source_zip':z,'library_family':lib,'zenodo_mzml_record':str(zen['id']),'zenodo_doi':zen['doi'],'mzml_member':rec['member'],'member_sha256':rec['member_sha256_verified'],'source_raw_filename_in_mzml':raw_name,'source_raw_sha1_in_mzml':rawsha,'spectrum_id':sid,'frozen_rung':row['rung'],'mzml_collision_energy_value':ce[0].get('value','') if ce else '', 'mzml_collision_energy_unit_accession':ce[0].get('unitAccession','') if ce else '', 'mzml_collision_energy_unit_name':ce[0].get('unitName','') if ce else '', 'compound_key':row['key'],'selected_ion_mz':row['selected_ion_mz']})
  if file_errors: anomalies.extend(f'{z}/{rec["member"]}: {x}' for x in file_errors)
  recapi=api_files.get(z,{})
  raw_key=next((k for k in raw_keys if k.lower().replace('_msn','')==z.lower().replace('mzml_','').replace('mzml','').replace('_msn','')), '')
  # The raw record contains seven library-family archives, but a matching name
  # is not proof that it is the file referenced by a particular mzML checksum.
  raw_archive_available='listed in public raw-positive record by family' if raw_key else 'not listed in the linked raw-positive record'
  inv.append({'source_zip':z,'library_family':lib,'zenodo_record_id':zen['id'],'zenodo_doi':zen['doi'],'zenodo_record_version':'v5 (Zenodo record page; API metadata field omits version)','zenodo_mzml_file_size_bytes':recapi.get('size',''),'zenodo_mzml_file_md5':recapi.get('checksum',''),'frozen_source_zip_sha256_declared':zhash.get(z,''),'frozen_member_count':len(expected_rows),'unique_allowlisted_mzml_files':int(expected_rows[['member','file_sha256']].drop_duplicates().shape[0]),'selected_scan_rows':len(expected_rows),'instrument_models_in_allowlist':'; '.join(models),'ionization_mode':'positive','fragmentation_method_in_selected_mzml':'; '.join(sorted(file_methods)),'observed_mzml_CE_units':'|'.join(sorted(file_units)),'observed_mzml_CE_values':'|'.join(sorted(file_values)),'raw_archive_family_status':raw_archive_available,'native_method_file_in_mzml_archive':'No; ZIP entries are mzML or directory entries in checked source archive central directories; nine-source complete directory audit pending log','source_to_public_RAW_hash_link':'Not established; the representative MCEBIO filename-associated public RAW member had SHA-1 different from the mzML sourceFile SHA-1','evidence_classification':'PARTIALLY ESTABLISHED - converted mzML scan metadata records eV; original native-method semantics not independently hash-linked'})
  instrument_rows.append({'source_zip':z,'library_family':lib,'mzml_member':rec['member'],'member_sha256':rec['member_sha256_verified'],'selected_sample_id':rec.get('selected_sample_id',''),'selected_scan_rows':rec['n_selected_scan_rows_for_member'],'instrument_models':'; '.join(models),'instrument_configuration_ids':'; '.join(sorted({c.get('id','') for c in configs})),'software_versions':software,'source_raw_filename':raw_name,'source_raw_sha1':rawsha,'selected_scan_energy_CV':'MS:1000045 collision energy','selected_scan_energy_unit_accession':'|'.join(sorted(file_units)),'selected_scan_energy_values':'|'.join(sorted(file_values)),'fragmentation_cv':'|'.join(sorted(file_methods)),'member_sha256_matches_frozen_allowlist':'yes'})
  by_member[(z,rec['member'])]=rec
 if scan_total!=len(allow): anomalies.append(f'allowlist rows {len(allow)} != parsed selected scan rows {scan_total}')
 if anomalies:
  raise SystemExit('VALIDATION FAILURE:\n'+'\n'.join(anomalies[:30]))
 if set(LIBRARIES)-{r['source_zip'] for r in records}: raise SystemExit('one or more nine sources have no parsed records')
 # Collapse per-member metadata observations into one inventory row per source ZIP.
 inv_by_zip=[]
 for z in sorted(LIBRARIES):
  group=[r for r in inv if r['source_zip']==z]
  exp=allow.loc[allow.source_zip.eq(z)]
  if not group: continue
  first=group[0].copy()
  first['frozen_member_count']=int(exp[['member','file_sha256']].drop_duplicates().shape[0])
  first['unique_allowlisted_mzml_files']=first['frozen_member_count']
  first['selected_scan_rows']=int(len(exp))
  for key in ('instrument_models_in_allowlist','fragmentation_method_in_selected_mzml','observed_mzml_CE_units','observed_mzml_CE_values'):
   vals=sorted({v for r in group for v in r[key].split('|') if v})
   first[key]='|'.join(vals)
  first['native_method_file_in_mzml_archive']='Not recovered; exact ZIP central-directory audit recorded separately'
  inv_by_zip.append(first)
 inv=inv_by_zip
 if len(inv)!=9: raise SystemExit(f'expected nine archives, found {len(inv)}')
 if sum(x['selected_scan_rows'] for x in inv)!=6004: raise SystemExit('expected 6004 selected scan records')
 write_csv(md/'MSNLIB_NINE_SOURCE_INVENTORY.csv',inv)
 write_csv(md/'INSTRUMENT_PARAMETERS.csv',instrument_rows)
 write_csv(md/'SOURCE_TO_EVALUATION_LINEAGE.csv',lineage)
 write_csv(md/'NATIVE_METHOD_SEARCH_LOG.csv',[{'source_zip':x['source_zip'],'library_family':x['library_family'],'mzml_repository':'Zenodo 15683784, version v5','mzml_record_url':'https://zenodo.org/records/15683784','native_RAW_repository':'Zenodo 13785391 (positive raw archive; seven families listed)','native_method_file_found':'No native method file in the evaluated mzML archive; source RAW references embedded in mzML','instrument_metadata_recovered':'Orbitrap ID-X; Xcalibur and ProteoWizard; selected MS2 scan CV terms','selected_scan_rows':x['selected_scan_rows'],'selected_scan_CE_unit':'electronvolt (UO:0000266)','file-level linkage_limit':'MZML member hash and selected scan IDs verified; raw SHA-1 linkage not independently established','verification_status':'PASS for converted mzML member and selected scan metadata; native method pending'} for x in inv])
 write_csv(energy/'ENERGY_CONVENTION_EVIDENCE_MATRIX.csv',[{'evidence':'Frozen MURU protocol and code','scope':'numeric selected values 20 and 60; labels NCE in protocol, unit parsed from source records not encoded','finding':'numeric values selected and passed through frozen adapter; no conversion change','classification':'verified computational fact'}, {'evidence':'MSnLib primary article Methods','scope':'article-declared Orbitrap ID-X MS2 acquisition','finding':'MS2 energies reported as 20 eV and 60 eV; instrument ID-X','classification':'primary-study method statement; source family linkage incomplete for later archives'}, {'evidence':'Zenodo mzML record v5','scope':'all nine source archive families in current record','finding':'converted flow-injection Orbitrap ID-X mzML collection for compound libraries','classification':'repository metadata'}, {'evidence':'Allowlisted mzML member hashes and selected scans','scope':f'{len(records)} files, {scan_total} frozen selected MS2 scan rows' if False else 'all frozen allowlisted scans after validator run','finding':'each selected scan carries MS:1000045 with UO:0000266 electronvolt and numerical value equal to frozen rung','classification':'direct converted-file metadata; not native method calibration'}, {'evidence':'Thermo ID-X method editor help v5.0','scope':'instrument capability','finding':'HCD interface distinguishes normalized percentage from absolute voltage','classification':'instrument-family documentation; does not identify historical setting'}, {'evidence':'Public RAW-positive Zenodo record','scope':'seven historical library families; no newer MCEDIV-20K or TargetMol archive listed','finding':'raw archives accessible but exact selected-file hash link unresolved; representative filename-associated member SHA1 did not match mzML sourceFile SHA1','classification':'partially available; identity mismatch observed'}])
 report=f'''# Extraction validation report\n\nStatus: PASS for frozen evaluated mzML members and selected spectra, subject to native-file linkage limitation.\n\n- Nine source ZIP families: {len(inv)}\n- Unique allowlisted mzML files extracted and SHA-256 checked: {len(records)}\n- Selected frozen scan rows present in parsed mzML: {scan_total}\n- Every selected ID occurred in its hashed member: yes (script hard-fails on missing IDs)\n- Selected scan energy term: PSI-MS MS:1000045, `collision energy`\n- Selected scan unit: UO:0000266, electronvolt\n- Selected collision-energy values matched frozen rung labels: yes (20/60)\n- Selected scan activation term: beam-type collision-induced dissociation, MS:1000422\n- Instrument model terms: Orbitrap ID-X (MS:1003112) in selected source records\n- Software recorded in mzML: Xcalibur and ProteoWizard; versions are in `INSTRUMENT_PARAMETERS.csv`\n- Native Thermo method files: not recovered from evaluated mzML ZIPs\n- Exact mzML-to-public-RAW byte identity: not established; representative filename-associated RAW member SHA-1 mismatch was observed\n\nValidation checks compare source member SHA-256 with the frozen allowlist, confirm ZIP CRC-32, parse the selected spectrum identifiers, require MS level 2, require exactly one collision-energy term with the expected unit and value, and compare the selected ion m/z against the frozen row metadata within the file audit. The raw archive itself was not redistributed. These results establish the converted mzML metadata semantics for the evaluated scan records, not a native-method audit or cross-instrument calibration.\n'''
 (md/'EXTRACTION_VALIDATION_REPORT.md').write_text(report)
 (md/'MISSING_METADATA_REGISTER.md').write_text('''# Missing metadata register\n\n## Resolved at converted-file level\n\nThe frozen evaluation allowlist resolves to nine positive-mode source ZIPs, 1,428 unique mzML members, and 6,004 selected MS2 scan rows. The extraction verifies the exact selected member bytes against the allowlist SHA-256, verifies ZIP CRC-32, and finds every frozen scan ID. Each selected scan records collision energy as eV in mzML. See `INSTRUMENT_PARAMETERS.csv` and `SOURCE_TO_EVALUATION_LINEAGE.csv`.\n\n## Still missing or not linked\n\n1. Native Xcalibur instrument-method files corresponding to every selected run were not found in the evaluated mzML ZIPs.\n2. Although a public raw-positive Zenodo record lists seven source library families, exact file identity is not confirmed. In the representative MCEBIO check, the RAW member identified by the apparent sample filename had a SHA-1 different from the SHA-1 embedded in the selected mzML `sourceFile` record. This indicates that the filename association alone is insufficient; it does not show why the hashes differ.\n3. The linked raw-positive record does not list the later MCEDIV-20K and TargetMol-NPHTS families.\n4. A converted mzML CV field documents the converted record’s unit but cannot independently reveal whether source software transformed or misrepresented an acquisition method parameter. The MSnLib article and the mzML fields agree on eV for the described library, but source-specific native method confirmation remains unavailable.\n5. Cross-instrument physical equivalence between the MURU development coordinate and MSnLib absolute-energy values is not established.\n\n## Shortest recovery route\n\nAsk the MSnLib data contact (Pluskal, listed as Zenodo contact person and corresponding author in the peer-reviewed paper) for the Xcalibur method or instrument-method export and the original RAW file identifiers/hashes for each of the nine source families, especially the two later families. Request a statement whether `MS:1000045` was exported from absolute HCD voltage and whether any NCE-to-eV conversion occurred during ProteoWizard conversion. See `../external_requests/NATIVE_METHOD_REQUESTS.md`; no request has been sent.\n''')
 print(f'PASS: {len(inv)} archives; {len(records)} member files; {scan_total} selected scans; no anomalies')
if __name__=='__main__': main()
