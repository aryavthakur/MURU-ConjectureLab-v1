"""MSnLib design frame for confirmation study 2: identity, scaffold map, conflict-free wells and ZIP members.

Structure, plate-map and ZIP central-directory metadata only; nothing here reads spectra. The rules are the ones
the census and study 1 used (scripts/wur_v2_confirmation/01_build_sample_and_massive_manifest.py), gathered in
one module so every study-2 step applies the same code.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import Descriptors, inchi, rdMolDescriptors

from muru.wur_v2 import identity as ID

RDLogger.DisableLog("rdApp.*")
ROOT = Path(__file__).resolve().parents[3]
PROTON = 1.007276
ELECTRON = 0.00054858
ISO_TOL = 0.7
DEV_MH_RANGE = (70.0, 1042.6)
SHIFTS_12A = {"[M+H]+": PROTON, "[M+NH4]+": 18.033823, "[M+Na]+": 22.989218, "[M+K]+": 38.963158,
              "[M-H2O+H]+": PROTON - 18.010565, "[M+H]+13C": PROTON + 1.003355}
LIBS = ["mcebio", "mcescaf", "nihnp", "otavapep", "enamdisc", "enammol", "mcedrug", "mcediv_50k_sub", "targetmolhtsnp"]
LIB_LABEL = {"mcebio": "MCEBIO", "mcescaf": "MCESCAF", "nihnp": "NIHNP", "otavapep": "OTAVAPEP", "enamdisc": "ENAMDISC",
             "enammol": "ENAMMOL", "mcedrug": "MCEDRUG", "mcediv_50k_sub": "MCEDIV", "targetmolhtsnp": "TARGETMOL"}
ID_COLS = ["plate_id", "well_location", "unique_sample_id", "smiles", "inchikey", "split_inchikey", "compound_name",
           "monoisotopic_mass", "structure_source"]
ZIPS = {  # the nine authenticated positive-mode mzML archives (Zenodo 10.5281/zenodo.15683784)
    "20220601_mzml_mce_bioactive_positive.zip": "e9e8375159f3d516335ea4d09d77bb5f9c28c33ff1661209fedcfe983d32ee07",
    "20230404_mzml_pluskal_nih_positive.zip": "10c812cb5aba807a88b9188ebc248c6a1e2946e68d1033f6ac493edf755950eb",
    "20231123_mzml_mce_scaffold_positive.zip": "1eb31622f10bfa644a1300591187cbe76bbf69cf5682526b5ae58d953c225bdc",
    "20231124_mzml_otavapep_positive.zip": "1a2c978eb9b7bce9e98396ea901db55af82e2f08a206922fac1d68aa6b41e6ff",
    "mzml_20240405_pluskal_enammol_MSn_positive.zip": "22194df47e151d38c2ba1eb71a20faa90f794aca417d263d999e20643cebc863",
    "mzml_20240408_pluskal_mcedrug_MSn_positive.zip": "87b9264664a118c734a6bbde320a4f4bf655ab7d2c915df55ed025ba6cdd1279",
    "mzml_20240502_pluskal_enamdisc_MSn_positive.zip": "a1da7a147025130a6c839eabb7396c4a089c79b35266359fffcaae9ef3c98d47",
    "mzml_20241113_pluskal_mcediv_20k_MSn_positive.zip": "89ad88f74096a59bb64ca14979eada2e35bd9c2c6eaf98c692690eea8005ab24",
    "mzml_20241120_pluskal_targetmolnphts_MSn_positive.zip": "007173324b055ac6f66a273450f10e7f095baa8b6a6710dbc4f607b868553e4f",
}
USID_RE = re.compile(r"(pluskal_.*?_id)(?=_|\.)")
DESIGN12B_SHA256 = "8ae32fb53e27a0fb99f875f48d7ffbe127fc1668e512b65797c3ad70712cd09e"
DESIGN12B_GROUPS_SHA256 = "809f14c4d2528661be39e169aacf67b8618f736db6d1d17afd2a7914c67f07b9"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lines(items) -> str:
    return hashlib.sha256("\n".join(sorted(items)).encode()).hexdigest()


_chem: dict = {}


def chem(smi: str) -> dict:
    """Byte-for-byte the census/study-1 identity rule."""
    if smi in _chem:
        return _chem[smi]
    rec = {"parse_ok": False, "parent_key": None, "scaffold": None, "parent_charge": None, "parent_formula": None,
           "mh": float("nan"), "m_plus": float("nan")}
    m0 = Chem.MolFromSmiles(smi) if isinstance(smi, str) and smi else None
    if m0 is not None:
        rk = inchi.MolToInchiKey(m0)
        pk = ID.parent_connectivity_key(smi)
        rec.update(parse_ok=bool(rk) and pk is not None, parent_key=pk)
        if pk is not None:
            rec["scaffold"] = ID.scaffold_group_v2(smi, pk)
    m = ID.parent_mol(smi) if rec["parse_ok"] else None
    if m is not None:
        rec["parent_charge"] = int(Chem.GetFormalCharge(m))
        rec["parent_formula"] = rdMolDescriptors.CalcMolFormula(m)
        mw = float(Descriptors.ExactMolWt(m))
        rec["mh"] = mw + PROTON if rec["parent_charge"] == 0 else float("nan")
        rec["m_plus"] = mw - ELECTRON * rec["parent_charge"] if rec["parent_charge"] > 0 else float("nan")
    _chem[smi] = rec
    return rec


def load_design(merlin: Path, cache: Path) -> pd.DataFrame:
    """All MERLIN design-table rows with identity; tables verified against the census sha256 values."""
    census = json.loads((ROOT / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    tables = census["inputs"]["design_tables"]
    hashes = {}
    for lib in LIBS:
        p = merlin / f"compounds__{lib}_cleaned.tsv"
        got = sha256_file(p)
        if got != tables[LIB_LABEL[lib]]["sha256"]:
            raise RuntimeError(f"MERLIN table {p.name} sha256 {got} does not match the census")
        hashes[p.name] = got
    id_sha = sha256_file(ROOT / "src/muru/wur_v2/identity.py")
    tag = hashlib.sha256(json.dumps([hashes, id_sha, rdBase.rdkitVersion], sort_keys=True).encode()).hexdigest()[:16]
    cp = cache / f"design_identity_{tag}.pkl"
    if cp.is_file():
        return pd.read_pickle(cp)
    parts = []
    for lib in LIBS:
        p = merlin / f"compounds__{lib}_cleaned.tsv"
        cols = pd.read_csv(p, sep="\t", nrows=0).columns
        d = pd.read_csv(p, sep="\t", usecols=[c for c in ID_COLS if c in cols], dtype=str, low_memory=False)
        d["library"] = LIB_LABEL[lib]
        parts.append(d)
    design = pd.concat(parts, ignore_index=True)
    for col in ("parse_ok", "parent_key", "scaffold", "parent_charge", "parent_formula", "mh", "m_plus"):
        design[col] = [chem(s)[col] if isinstance(s, str) else None for s in design.smiles]
    design["key"] = design.parent_key
    design["mh"] = pd.to_numeric(design.mh, errors="coerce")
    design["m_plus"] = pd.to_numeric(design.m_plus, errors="coerce")
    cache.mkdir(parents=True, exist_ok=True)
    design.to_pickle(cp)
    return design


def design12b(design: pd.DataFrame) -> tuple[set, dict, list]:
    """(12b keys, key -> census scaffold group, sorted 12b group list), all verified against pinned hashes."""
    census = json.loads((ROOT / "artifacts/wur_v2/external_census/msnlib_census.json").read_text())
    keys = set(census["design_frame"]["survivors"]["step12b_keys"])
    if sha256_lines(keys) != DESIGN12B_SHA256:
        raise RuntimeError("design 12b key hash mismatch")
    key_scaf = {}
    for k, sc in design.dropna(subset=["key"]).drop_duplicates("key")[["key", "scaffold"]].itertuples(index=False):
        key_scaf[k] = sc if isinstance(sc, str) and sc else f"__UNPARSED__{k}"
    groups = sorted({key_scaf[k] for k in keys})
    if sha256_lines(groups) != DESIGN12B_GROUPS_SHA256:
        raise RuntimeError("design 12b scaffold group list hash mismatch")
    return keys, key_scaf, groups


def conflict_free_dev_wells(design: pd.DataFrame, keys: set) -> pd.DataFrame:
    """Rows (key, unique_sample_id, mh, library, plate_id, well_location) for wells of `keys` that are free of the
    census 12a isolation conflicts (another plated compound's adduct within 0.7 Da, or the same parent formula)
    and whose [M+H]+ is inside the development range. Same rule as study 1."""
    sub = design[design.key.isin(keys)].dropna(subset=["unique_sample_id"])
    wells = design[design.unique_sample_id.isin(set(sub.unique_sample_id))]
    flag = {}
    for usid, g in wells.groupby("unique_sample_id"):
        ions = []
        for r in g.itertuples(index=False):
            if not isinstance(r.key, str):
                continue
            if r.parent_charge == 0 and np.isfinite(r.mh):
                ions.append((r.key, r.parent_formula, np.array([r.mh - PROTON + s for s in SHIFTS_12A.values()])))
            elif np.isfinite(r.m_plus):
                ions.append((r.key, r.parent_formula, np.array([r.m_plus])))
        for r in g.itertuples(index=False):
            if not isinstance(r.key, str) or not np.isfinite(r.mh):
                flag[(usid, r.key)] = True
                continue
            other = [x for x in ions if x[0] != r.key]
            flag[(usid, r.key)] = bool(any(np.any(np.abs(x[2] - r.mh) <= ISO_TOL) for x in other)
                                       or any(x[1] == r.parent_formula for x in other))
    sub = sub.assign(iso_conflict=[flag.get((u, k), True) for u, k in zip(sub.unique_sample_id, sub.key)])
    ok = sub[(~sub.iso_conflict) & sub.mh.between(*DEV_MH_RANGE)]
    return ok[["key", "unique_sample_id", "mh", "library", "plate_id", "well_location"]].drop_duplicates()


def zip_members(zip_dir: Path, verify_zip_sha: bool = True) -> pd.DataFrame:
    """One chosen mzML member per well from the nine ZIP central directories (no member is read), with the
    study-1 duplicate-acquisition tie-break: production variant, latest run date, plain over resubmission-
    suffixed name, then name."""
    rows = []
    for z, want in ZIPS.items():
        if verify_zip_sha and sha256_file(zip_dir / z) != want:
            raise RuntimeError(f"{z} sha256 does not match the authenticated archive")
        with zipfile.ZipFile(zip_dir / z) as zf:
            for i in zf.infolist():
                if i.is_dir() or not i.filename.lower().endswith(".mzml"):
                    continue
                base = i.filename.rsplit("/", 1)[-1]
                m = USID_RE.search(base)
                if m:
                    rows.append({"source_zip": z, "member": i.filename, "file": base, "unique_sample_id": m.group(1)})
    df = pd.DataFrame(rows)
    df["run_date"] = df.file.str.extract(r"^(\d{8})_")[0].fillna("")
    df["variant"] = df.file.str.extract(r"^\d{8}_(.*?)\d?pluskal_")[0].fillna("")
    df["pref"] = df.variant.eq("100AGC_60000Res_")
    df["has_resubmit_suffix"] = df.file.str.contains(r"_\d{10,}(?:_MSn_positive)?\.mzML$", regex=True)
    df = df.sort_values(["unique_sample_id", "pref", "run_date", "has_resubmit_suffix", "member"],
                        ascending=[True, False, False, True, True])
    counts = df.groupby("unique_sample_id").size()
    chosen = df.drop_duplicates("unique_sample_id").copy()
    chosen["n_candidates"] = chosen.unique_sample_id.map(counts)
    return chosen[["unique_sample_id", "source_zip", "member", "file", "n_candidates"]].reset_index(drop=True)
