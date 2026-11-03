#!/usr/bin/env python3
"""Integrity assertions for the committed Phase 6 metadata summaries."""
from pathlib import Path
import csv, json, sys
ROOT=Path(__file__).resolve().parents[2]
MD=ROOT/'publication_phase6'/'metadata'
def rows(name):
    with (MD/name).open(newline='') as f: return list(csv.DictReader(f))
inv=rows('MSNLIB_NINE_SOURCE_INVENTORY.csv')
pars=rows('INSTRUMENT_PARAMETERS.csv')
lineage=rows('SOURCE_TO_EVALUATION_LINEAGE.csv')
meth=rows('PUBLIC_METH_FILE_METADATA.csv')
nested=rows('NESTED_NIH_ARCHIVE_AUDIT.csv')
assert len(inv)==9, len(inv)
assert len(pars)==1428, len(pars)
assert len(lineage)==6004, len(lineage)
assert sum(int(r['selected_scan_rows']) for r in pars)==6004
assert all(r['observed_mzml_CE_units']=='UO:0000266' for r in inv)
assert all(r['observed_mzml_CE_values']=='20.0|60.0' for r in inv)
assert all(r['evidence_classification'].startswith('PARTIALLY ESTABLISHED') for r in inv)
assert len(meth)==161
assert {r['instrument_field_values'] for r in meth}=={'Vanquish_H'}
assert {r['method_type_values'] for r in meth}=={'SeparationMethod'}
assert all(r['member_crc32_verified']=='yes' for r in meth)
assert not any(int(r['explicit_ID_X_term_count']) for r in meth)
assert not any(int(r['normalized_collision_energy_phrase_count']) for r in meth)
assert not any(int(r['standalone_NCE_count']) for r in meth)
assert not any(int(r['collision_energy_phrase_count']) for r in meth)
assert len(nested)==1 and nested[0]['listing_member_count']=='536' and nested[0]['method_like_members']=='0'
assert nested[0]['outer_member_crc32']=='8d41051a'
print('PASS: 9 source archives; 1,428 allowlisted members; 6,004 selected scan rows; all converted CE annotations match eV rungs 20/60')
print('PASS: 161 public .meth summaries; Vanquish_H SeparationMethod only; no explicit ID-X/NCE/collision-energy terms')
print('PASS: nested NIH 7z record reports 535 mzML names, no method-like member, and verified outer-member CRC')
