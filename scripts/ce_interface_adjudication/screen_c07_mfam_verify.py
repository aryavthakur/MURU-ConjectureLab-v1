#!/usr/bin/env python3
"""S7 INDEPENDENT VERIFICATION of the C07 (mFam MassBank contribution) metadata screen.

This script does NOT read screen/c07_mfam/c07_records.csv or c07_screen_summary.json.
It re-derives everything from the raw harvested payloads:
  downloads/massbank_export_jsonld/export_metadata_jsonld.jsonl.gz   (7,872 record JSON-LD bodies)
  downloads/massbank_api/browse_mFam.json + search_mFam__*.json      (MassBank3 API counts)
  downloads/github_codesearch/*.json                                 (raw MassBank record header fragments)
and the P5 exclusion key lists in artifacts/ce_interface_adjudication/exclusion/.

Outputs land in screen/c07_mfam/verify/.
Metadata only. No spectra, no peak arrays, no model inference.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from rdkit import rdBase

ROOT = Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
SCR = ROOT / "scripts/ce_interface_adjudication"
ART = ROOT / "artifacts/ce_interface_adjudication"
C07 = ART / "screen/c07_mfam"
DL = C07 / "downloads"
OUT = C07 / "verify"
EXCL = ART / "exclusion"

sys.path.insert(0, str(SCR))
from scaffold_key import key_and_group, first_block  # noqa: E402

OUT.mkdir(parents=True, exist_ok=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_keys(name: str) -> set[str]:
    p = EXCL / name
    return {ln.strip() for ln in p.read_text().splitlines() if ln.strip()}


# ---------------------------------------------------------------- 1. raw parse
JSONLD = DL / "massbank_export_jsonld/export_metadata_jsonld.jsonl.gz"

# MassBank record title convention (Documentation/MassBankRecordFormat.md, RECORD_TITLE):
#   <CH$NAME>; <AC$INSTRUMENT_TYPE>; <MS_TYPE>; <CE: ...>; <PRECURSOR_TYPE>
TITLE_RE = re.compile(r"^(?P<name>.*?);\s*(?P<itype>[A-Z0-9\-]+);\s*(?P<mstype>MS\d+)\s*;\s*(?P<rest>.*)$")

rows = []
status_ct = Counter()
with gzip.open(JSONLD, "rt") as f:
    for line in f:
        rec = json.loads(line)
        acc = rec["accession"]
        status_ct[rec.get("status")] += 1
        ds = chem = None
        for b in rec.get("body") or []:
            if b.get("@type") == "Dataset":
                ds = b
            elif b.get("@type") == "ChemicalSubstance":
                chem = b
        title = (ds or {}).get("name")
        part = ((chem or {}).get("hasBioChemEntityPart") or [{}])[0]
        rows.append(
            dict(
                accession=acc,
                lab=acc.split("-")[-1].split("_")[0],
                title=title,
                date_published=(ds or {}).get("datePublished"),
                license=(ds or {}).get("license"),
                name=(chem or {}).get("name"),
                smiles=part.get("smiles"),
                inchi=part.get("inChI"),
                inchikey=part.get("inChIKey"),
                formula=part.get("molecularFormula"),
                mono=part.get("monoisotopicMolecularWeight"),
            )
        )

df = pd.DataFrame(rows)


def split_tail(t):
    if not isinstance(t, str):
        return None, None, None, None
    m = TITLE_RE.match(t)
    if not m:
        return None, None, None, None
    rest = m.group("rest")
    parts = [p.strip() for p in rest.split(";") if p.strip()]
    ce = None
    adduct = None
    for p in parts:
        if p.upper().startswith("CE"):
            ce = p.split(":", 1)[1].strip() if ":" in p else p[2:].strip()
        elif p.startswith("[") or p.startswith("("):
            adduct = p
    if adduct is None and parts:
        adduct = parts[-1]
    return m.group("itype"), m.group("mstype"), ce, adduct


parsed = df["title"].map(split_tail)
df["t_itype"] = [p[0] for p in parsed]
df["t_mstype"] = [p[1] for p in parsed]
df["t_ce"] = [p[2] for p in parsed]
df["t_adduct"] = [p[3] for p in parsed]

# ---------------------------------------------------------------- 2. identity
kg = [key_and_group(s) for s in df["smiles"]]
df["key"] = [k for k, _ in kg]
df["scaffold_group"] = [g for _, g in kg]
df["recorded_block"] = df["inchikey"].map(first_block)

# ---------------------------------------------------------------- 3. instrument / polarity flags
# MassBank AC$INSTRUMENT_TYPE analyzer tokens:
#   ITFT = ion trap + Fourier transform (LTQ-Orbitrap family)
#   QFT  = quadrupole + Fourier transform (Q Exactive family)
# TOF / QTOF are NOT Orbitrap.
ORBITRAP_TOKENS = ("ITFT", "QFT")
df["analyzer"] = df["t_itype"].map(lambda s: s.split("-")[-1] if isinstance(s, str) else None)
df["is_orbitrap_type"] = df["analyzer"].isin(ORBITRAP_TOKENS)
df["ionization"] = df["t_itype"].map(
    lambda s: ("APCI" if isinstance(s, str) and "APCI" in s else ("ESI" if isinstance(s, str) and "ESI" in s else None))
)
df["is_pos"] = df["t_adduct"].map(lambda a: isinstance(a, str) and a.rstrip().endswith("+"))
df["is_mh"] = df["t_adduct"].map(lambda a: isinstance(a, str) and a.replace(" ", "") == "[M+H]+")

# ---------------------------------------------------------------- 4. CE semantics
NUM_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*$")
UNIT_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(eV|V|%|NCE)\s*$", re.I)
PREFIX_RE = re.compile(r"^\s*(HCD|CID|ETD)\s+([0-9]+(?:\.[0-9]+)?)\s*(eV|V|%|NCE)?\s*$", re.I)


def ce_form(s):
    if not isinstance(s, str) or not s.strip():
        return "MISSING"
    if NUM_RE.match(s):
        return "BARE_NUMBER"
    if UNIT_RE.match(s):
        return "NUMBER_WITH_UNIT"
    if PREFIX_RE.match(s):
        return "MODE_PREFIXED"
    if "," in s or "-" in s or "/" in s:
        return "MULTI_OR_RAMP"
    return "OTHER"


def ce_single_numeric(s):
    """Return a float only when the string denotes ONE energy value (unit or not)."""
    if not isinstance(s, str):
        return None
    m = NUM_RE.match(s) or UNIT_RE.match(s)
    if m:
        return float(m.group(1))
    m = PREFIX_RE.match(s)
    if m:
        return float(m.group(2))
    return None


df["ce_form"] = df["t_ce"].map(ce_form)
df["ce_value"] = df["t_ce"].map(ce_single_numeric)

# ---------------------------------------------------------------- 5. exclusion sets
sets = {
    "msg15_all": load_keys("msg15_keys_all.txt"),
    "msg15_train": load_keys("msg15_keys_train.txt"),
    "msg15_val": load_keys("msg15_keys_val.txt"),
    "msg15_test": load_keys("msg15_keys_test.txt"),
    "msg15_parent_all": load_keys("msg15_parent_keys_all.txt"),
    "msg15_simchallenge": load_keys("msg15_simchallenge_keys_all.txt"),
    "muru_registry": load_keys("muru_exposure_registry_keys.txt"),
    "muru_registry_direct": load_keys("muru_exposure_registry_keys_direct_reason.txt"),
    "muru_exposed_union": load_keys("muru_exposed_union_keys.txt"),
    "pr7_study2": load_keys("msnlib_study2_population_keys.txt"),
    "comparator_common": load_keys("comparator_common_population_keys.txt"),
    "msnlib_9lib": load_keys("msnlib_9lib_keys.txt"),
    "multims2_reserved": load_keys("multims2_reserved_validation_secondary_keys.txt"),
}
scaf_sets = {
    "msg15_scaffolds": load_keys("msg15_scaffold_groups_all.txt"),
    "muru_registry_scaffolds": load_keys("muru_exposure_registry_scaffold_groups.txt"),
    "pr7_study2_scaffolds": load_keys("msnlib_study2_population_scaffold_groups.txt"),
    "comparator_scaffolds": load_keys("comparator_common_population_scaffold_groups.txt"),
}
for n, s in sets.items():
    df[f"in_{n}"] = df["key"].isin(s)
for n, s in scaf_sets.items():
    df[f"scaf_in_{n}"] = df["scaffold_group"].isin(s)

df.to_csv(OUT / "c07_verify_records.csv", index=False)

# ---------------------------------------------------------------- 6. compound-level tables
FLAGS = [c for c in df.columns if c.startswith("in_") or c.startswith("scaf_in_")]


def compound_table(sub: pd.DataFrame) -> pd.DataFrame:
    g = sub.groupby("key", dropna=True)
    out = g.agg(
        name=("name", "first"),
        scaffold_group=("scaffold_group", "first"),
        n_records=("accession", "size"),
        labs=("lab", lambda x: ",".join(sorted(set(x)))),
        ce_strings=("t_ce", lambda x: "|".join(sorted({v for v in x if isinstance(v, str)}))),
        itypes=("t_itype", lambda x: ",".join(sorted(set(v for v in x if isinstance(v, str))))),
    ).reset_index()
    per = sub.dropna(subset=["ce_value"]).groupby(["key", "lab"])["ce_value"].nunique()
    mx = per.groupby("key").max() if len(per) else pd.Series(dtype=int)
    out["max_ce_within_lab"] = out["key"].map(mx).fillna(0).astype(int)
    first = g[FLAGS].first().reset_index()
    out = out.merge(first, on="key", how="left")
    return out


def ladder(ct: pd.DataFrame, label: str) -> dict:
    res = {"label": label}

    def stat(d, nm):
        res[nm] = dict(
            keys=int(d["key"].nunique()),
            scaffold_groups=int(d["scaffold_group"].nunique()),
            acyclic_groups=int(d["scaffold_group"].str.startswith("__ACYCLIC__").sum()),
            groups_ge2_keys=int((d.groupby("scaffold_group")["key"].nunique() >= 2).sum()) if len(d) else 0,
        )

    stat(ct, "S0_all")
    a = ct[~ct["in_muru_registry"]]
    stat(a, "S1_not_in_muru_registry")
    b = a[~a["in_pr7_study2"]]
    stat(b, "S2_and_not_in_pr7")
    c = b[~b["in_comparator_common"]]
    stat(c, "S3_and_not_in_comparator")
    d = c[~c["in_msg15_all"] & ~c["in_msg15_parent_all"]]
    stat(d, "S4_and_not_in_msg15_key")
    e = d[
        ~d["scaf_in_muru_registry_scaffolds"]
        & ~d["scaf_in_pr7_study2_scaffolds"]
        & ~d["scaf_in_comparator_scaffolds"]
    ]
    stat(e, "S5_and_scaffold_novel_vs_muru")
    f = e[~e["scaf_in_msg15_scaffolds"]]
    stat(f, "S6_and_scaffold_novel_vs_msg15")
    res["_S4_keys"] = sorted(d["key"].tolist())
    res["_final_keys"] = sorted(f["key"].tolist())
    return res


ct_all = compound_table(df)
orb = df[df["is_orbitrap_type"] & df["is_pos"] & df["is_mh"]]
ct_orb = compound_table(orb)
ct_orb_multi = ct_orb[ct_orb["max_ce_within_lab"] >= 3].copy()

ct_all.to_csv(OUT / "c07_verify_compounds_all.csv", index=False)
ct_orb.to_csv(OUT / "c07_verify_compounds_orbitrap_pos_mh.csv", index=False)
ct_orb_multi.to_csv(OUT / "c07_verify_compounds_orbitrap_pos_mh_multi_energy.csv", index=False)

# ---------------------------------------------------------------- 7. CE semantics per lab
ce_by_lab = {}
for lab, sub in df.groupby("lab"):
    ce_by_lab[lab] = dict(
        n_records=int(len(sub)),
        itypes=dict(Counter(sub["t_itype"].dropna())),
        ce_forms=dict(Counter(sub["ce_form"])),
        ce_examples=sorted({v for v in sub["t_ce"] if isinstance(v, str)})[:14],
        n_distinct_ce_strings=int(sub["t_ce"].nunique(dropna=True)),
    )

orb_multi_ce_by_lab = {}
mset = set(ct_orb_multi["key"])
for lab, sub in orb[orb["key"].isin(mset)].groupby("lab"):
    orb_multi_ce_by_lab[lab] = dict(
        n_records=int(len(sub)),
        itypes=dict(Counter(sub["t_itype"].dropna())),
        ce_forms=dict(Counter(sub["ce_form"])),
        ce_values=sorted({float(v) for v in sub["ce_value"].dropna()}),
    )

lab_supplying = Counter()
per = orb.dropna(subset=["ce_value"]).groupby(["key", "lab"])["ce_value"].nunique()
for (k, lab), n in per.items():
    if n >= 3 and k in mset:
        lab_supplying[lab] += 1

summary = dict(
    script="scripts/ce_interface_adjudication/screen_c07_mfam_verify.py",
    rdkit=rdBase.rdkitVersion,
    inputs=dict(jsonld_sha256=sha256(JSONLD), jsonld_lines=int(len(df)), http_status=dict(status_ct)),
    n_records=int(len(df)),
    n_records_by_lab=dict(Counter(df["lab"])),
    n_labs=int(df["lab"].nunique()),
    instrument_type_records=dict(Counter(df["t_itype"].dropna())),
    ion_mode_records=dict(pos=int(df["is_pos"].sum()), neg=int((~df["is_pos"]).sum())),
    adduct_top=dict(Counter(df["t_adduct"].dropna()).most_common(12)),
    licenses=dict(Counter(df["license"].dropna())),
    date_published_range=[str(df["date_published"].min()), str(df["date_published"].max())],
    title_parse_failures=int(df["t_itype"].isna().sum()),
    key_formed=int(df["key"].notna().sum()),
    key_equals_recorded_block={str(k): int(v) for k, v in Counter(df["key"] == df["recorded_block"]).items()},
    n_distinct_keys=int(df["key"].nunique()),
    n_scaffold_groups=int(df["scaffold_group"].nunique()),
    ce_form_records=dict(Counter(df["ce_form"])),
    ce_semantics_by_lab=ce_by_lab,
    orbitrap_records=int(df["is_orbitrap_type"].sum()),
    orbitrap_pos_records=int((df["is_orbitrap_type"] & df["is_pos"]).sum()),
    orbitrap_pos_mh_records=int(len(orb)),
    orbitrap_pos_mh_keys=int(orb["key"].nunique()),
    orbitrap_pos_mh_multi_energy_keys=int(ct_orb_multi["key"].nunique()),
    orbitrap_pos_mh_max_ce_hist={str(k): int(v) for k, v in Counter(ct_orb["max_ce_within_lab"]).items()},
    labs_supplying_ge3_energies=dict(lab_supplying),
    multi_energy_ce_by_lab=orb_multi_ce_by_lab,
    ladder_all=ladder(ct_all, "all mFam compounds"),
    ladder_orbitrap_pos_mh=ladder(ct_orb, "Orbitrap + POSITIVE + [M+H]+"),
    ladder_orbitrap_pos_mh_multi=ladder(ct_orb_multi, "Orbitrap + POSITIVE + [M+H]+ + >=3 energies in one lab"),
    overlap_counts_all=dict(
        msg15_any=int(ct_all["in_msg15_all"].sum()),
        msg15_parent_any=int(ct_all["in_msg15_parent_all"].sum()),
        msg15_train=int(ct_all["in_msg15_train"].sum()),
        msg15_val=int(ct_all["in_msg15_val"].sum()),
        msg15_test=int(ct_all["in_msg15_test"].sum()),
        msg15_simchallenge=int(ct_all["in_msg15_simchallenge"].sum()),
        muru_registry=int(ct_all["in_muru_registry"].sum()),
        muru_exposed_union=int(ct_all["in_muru_exposed_union"].sum()),
        pr7_study2=int(ct_all["in_pr7_study2"].sum()),
        comparator_common=int(ct_all["in_comparator_common"].sum()),
        msnlib_9lib=int(ct_all["in_msnlib_9lib"].sum()),
        multims2_reserved=int(ct_all["in_multims2_reserved"].sum()),
    ),
    overlap_counts_orbitrap_pos_mh=dict(
        msg15_any=int(ct_orb["in_msg15_all"].sum()),
        msg15_train=int(ct_orb["in_msg15_train"].sum()),
        msg15_test=int(ct_orb["in_msg15_test"].sum()),
        muru_registry=int(ct_orb["in_muru_registry"].sum()),
        pr7_study2=int(ct_orb["in_pr7_study2"].sum()),
        comparator_common=int(ct_orb["in_comparator_common"].sum()),
    ),
    overlap_counts_multi_energy=dict(
        n=int(len(ct_orb_multi)),
        msg15_any=int(ct_orb_multi["in_msg15_all"].sum()),
        muru_registry=int(ct_orb_multi["in_muru_registry"].sum()),
        pr7_study2=int(ct_orb_multi["in_pr7_study2"].sum()),
        comparator_common=int(ct_orb_multi["in_comparator_common"].sum()),
        msnlib_9lib=int(ct_orb_multi["in_msnlib_9lib"].sum()),
    ),
)

(OUT / "c07_verify_summary.json").write_text(json.dumps(summary, indent=1, default=str))
print(json.dumps({k: v for k, v in summary.items() if k != "ce_semantics_by_lab"}, indent=1, default=str))
