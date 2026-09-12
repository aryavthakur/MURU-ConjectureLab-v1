# WUR Stage 0: Partition and Seal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the identity-only pipeline that reads the frozen WUR mass
spectral library release, censuses its qualifying (HCD, full six-point NCE
ladder) trajectories, and partitions them into `WUR-DEV` and `WUR-SEALED`
per rules D1–D5, before any `mu` exists.

**Architecture:** A three-layer read-only pipeline under `src/muru/io/`:
(1) `wur_raw.py` reads the ten mzVault SQLite files into a flat per-spectrum
table (no intensities); (2) `wur_identity.py` gates each row through the
known defects (stepped energy, UVPD, off-ladder energy, unresolved adduct,
identity mismatch, wrong polarity) and reduces surviving rows to one row per
qualifying trajectory, merging duplicate/cross-library deposits by
connectivity key; (3) `wur_census.py` and `wur_partition.py` annotate each
trajectory against the existing LCSB development corpus and sealed
confirmation set and apply D1–D5. Three CLI scripts under `scripts/` wire
these into the four Stage-0 artifacts. Everything reuses `molecules.py`'s
`scaffold_group` and the existing `confirmation_set_sealed.json` /
`p2_dev_corpus.parquet` as-is; nothing under `src/muru/discovery`,
`src/muru/paper_benchmark`, or any frozen constant is touched.

**Tech Stack:** Python, `sqlite3` (stdlib), `pandas`, `numpy`, `rdkit`
(already a project dependency — `molecules.py` uses it).

**Spec:** `docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md`
on branch `claude/mur-mass-spectral-library-42e6d5` (commit `07183c3`).
Section 4 ("Stage 0: partition and seal") is what this plan implements.
Task 1 below copies this file into the working branch so it travels with
the plan.

## Global Constraints

- **Runtime data already staged in this worktree** (set up during planning,
  not part of any task): `data/external/wur/` holds all 20 real release
  files, verified byte-identical to the pinned hashes below.
  `artifacts/p2_dev_corpus.parquet` is a symlink to the main checkout's copy
  (`/Users/aryav/Documents/MURU-ConjectureLab-v1/artifacts/p2_dev_corpus.parquet`)
  — this file is gitignored (`artifacts/*` with `.parquet` not
  un-ignored) and every other worktree that uses it does the same via a
  local, untracked symlink; it is not something any task needs to create,
  but if it is ever missing, recreate the symlink rather than trying to
  regenerate the file. Tasks 1, 4, and 6's "run against the real release"
  steps depend on both being present.
- **Base branch:** fork from `claude/muru-final-holdout-experiment-d75e7d`
  (main plus the only copy of the frozen selector and
  `FRESH_HOLDOUT_METHOD_FREEZE.json`) — not `main`, not
  `exec/muru-heldout-a3-6` (41 commits behind).
- **Frozen input:** Zenodo record `10.5281/zenodo.20552933`, WUR Mass
  Spectral Library v1.0, 203,752,342 bytes, whole-archive
  SHA-256 `96fe2b1a6c5bcb441ee980b602e58f1b296af09b4eb9b99d56b92d44c03333d2`.
  This is one retrieval; a different release is a drift record plus an
  amendment, never a silent substitution.
- **Data location:** `data/external/wur/` — already excluded by
  `.gitignore` (`data/external/` is its own line). Never commit the raw
  `.db`/`.msp` files.
- **Partition rules (frozen, from spec §4):** D1 unit = Bemis-Murcko
  scaffold group of the lexicographically-first deposited SMILES per
  connectivity key. D2 a group touching LCSB development → `WUR-DEV`. D3 a
  group touching the LCSB sealed confirmation set → `WUR-SEALED`, and D3
  beats D2 on conflict. D4 remaining free groups split 50/50 at seed
  `20260911`. D5 negative mode is never split — all of it goes to
  `WUR-DEV`.
- **Sealed-part floor:** ≥250 trajectories and ≥150 scaffold groups on the
  `WUR-SEALED` side. This is the acceptance bar for Stage 0, not "must
  reproduce the design session's 971/581 headline count" — a fresh,
  from-scratch reading of the raw files is expected to differ slightly from
  that earlier count, and that is fine per the drift-recording convention
  already established for the WFSR subset (spec §3.3).
- **Sealed set stays sealed:** `artifacts/confirmation_set_sealed.json` may
  only ever be read for its `connectivity_keys` list, never for any outcome
  value. Use the existing `muru.synth.generators.sealed_keys()` helper —
  don't re-open the file directly.
- **No re-tuning:** this plan adds new `src/muru/io/wur_*.py` modules only.
  It does not modify `adequacy.py`, `splits.py`, `molecules.py`,
  `discovery/`, or `paper_benchmark/`, and it computes no `mu`.
- **Out of scope:** Stage 1 (cross-instrument bridge gate), Stage 2 (the
  full mu/feature loader and MURU run), Stage 3 (the sealed-part look), and
  MSP-file parsing (the `.db` files are authoritative per spec §3, and
  Stage 0 needs no fields the `.msp` format uniquely carries).

---

## Task 1: Branch setup, spec import, and the retrieval manifest

**Files:**
- Create: `docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md`
  (copied from `claude/mur-mass-spectral-library-42e6d5`)
- Create: `src/muru/io/wur_retrieval.py` (`src/muru/io/` already exists as a
  namespace package — confirmed no `__init__.py` there, alongside
  `manifest.py`, `massbank.py`, `mzml.py`; do not add one)
- Create: `scripts/build_wur_retrieval_manifest.py`
- Test: `tests/test_wur_retrieval.py`

**Interfaces:**
- Produces: `EXPECTED_FILES: dict[str, str]` (filename → sha256),
  `sha256_of(path: Path) -> str`, `build_manifest(data_dir: Path) -> dict`

- [ ] **Step 1: Confirm the base branch and bring the spec doc in**

```bash
git log --oneline -1 FRESH_HOLDOUT_METHOD_FREEZE.json
# must show a commit -- confirms this branch descends from
# claude/muru-final-holdout-experiment-d75e7d, not main
git show claude/mur-mass-spectral-library-42e6d5:docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md \
  > docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md
git add docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md
git commit -m "docs: import WUR real-data program spec for Stage 0 implementation"
```

- [ ] **Step 2: Write the failing test for the retrieval manifest**

```python
# tests/test_wur_retrieval.py
import hashlib

import pytest

from muru.io.wur_retrieval import build_manifest, EXPECTED_FILES


def test_build_manifest_detects_missing_files(tmp_path):
    manifest = build_manifest(tmp_path)
    assert set(manifest["missing"]) == set(EXPECTED_FILES)
    assert manifest["n_files"] == 0


def test_build_manifest_detects_hash_mismatch(tmp_path, monkeypatch):
    import muru.io.wur_retrieval as mod
    monkeypatch.setattr(mod, "EXPECTED_FILES", {"fake.db": "0" * 64})
    (tmp_path / "fake.db").write_bytes(b"wrong bytes")
    manifest = mod.build_manifest(tmp_path)
    assert manifest["hash_mismatches"] == ["fake.db"]


def test_build_manifest_passes_when_bytes_match(tmp_path, monkeypatch):
    import muru.io.wur_retrieval as mod
    content = b"exact frozen bytes for this one file"
    expected_hash = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(mod, "EXPECTED_FILES", {"fake.db": expected_hash})
    (tmp_path / "fake.db").write_bytes(content)
    manifest = mod.build_manifest(tmp_path)
    assert manifest["missing"] == []
    assert manifest["hash_mismatches"] == []
    assert manifest["files"][0]["sha256"] == expected_hash


def test_expected_files_covers_ten_msp_and_ten_db():
    dbs = [n for n in EXPECTED_FILES if n.endswith(".db")]
    msps = [n for n in EXPECTED_FILES if n.endswith(".msp")]
    assert len(dbs) == 10
    assert len(msps) == 10
```

- [ ] **Step 3: Run it to verify it fails**

Run: `pytest tests/test_wur_retrieval.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_retrieval'`

- [ ] **Step 4: Implement `src/muru/io/wur_retrieval.py`**

```python
# src/muru/io/wur_retrieval.py
"""Hash verification for the frozen WUR Zenodo release.

Source: Zenodo record 20552933, WUR Mass Spectral Library v1.0, 2026-06-05.
DOI: 10.5281/zenodo.20552933. Licence: CC-BY 4.0.
Whole-archive: 203,752,342 bytes,
sha256 96fe2b1a6c5bcb441ee980b602e58f1b296af09b4eb9b99d56b92d44c03333d2.

Per-file hashes below were computed once, at retrieval, against the frozen
release. A hash mismatch here means the local copy is not that release.
"""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_FILES = {
    "ETE organic environmental pollutants mass spectral library_NEG_v1.db":
        "13cf566e7c30d9618cb167cb7ff4831cc39e9bb91329fcb14ad15881154b2d90",
    "ETE organic environmental pollutants mass spectral library_NEG_v1.msp":
        "ae4cf59f1e8ff8d60565868b16114684969319274764d5ca4452be4096db388a",
    "ETE organic environmental pollutants mass spectral library_POS_v1.db":
        "79efdfe960abb817d0ca305f99fac1f68d82891cc041a554177fcc88cea5fb68",
    "ETE organic environmental pollutants mass spectral library_POS_v1.msp":
        "f6eff56da0dee73fdb7e33b13eb2a74decdc2b80fd44e334ee1d5816e847f299",
    "FCH food small molecules mass spectral library_NEG_v1.db":
        "f803be723608928f3e63f66f71960b7af2cb26d49013be7294064b8b888ee093",
    "FCH food small molecules mass spectral library_NEG_v1.msp":
        "88a6762a5f2bf41b0bc12fb3d85ec11ec75e4e4307eea3c852f8da8b72b50e50",
    "FCH food small molecules mass spectral library_POS_v1.db":
        "dbc7ffdeeb61bb9018cc6155b62bd67624420d1c01b5d1446f6f3a283700b337",
    "FCH food small molecules mass spectral library_POS_v1.msp":
        "47e6eb23dbb1174f5272c6e08d7cb979887d06ccf9707c1eaaea440624c5d052",
    # NOTE: this filename carries the release's own stray space before
    # "_NEG" -- preserved verbatim, not a typo introduced here.
    "WFSR Polar substances mass spectral library _NEG_v1.db":
        "c54473705c2d04f78cfea22ed40b0c5009efb4c135c1f08af457c7ecec07ab6d",
    "WFSR Polar substances mass spectral library_NEG_v1.msp":
        "4bb4a44ff3547f5018d4e68ce8f992ccddff675260494b687cb0fdc577a60704",
    "WFSR Polar substances mass spectral library_POS_v1.db":
        "2ca9722cab4c68dd886f770f824c83caeaf84018bdaf1189fcca35955e7ca67a",
    "WFSR Polar substances mass spectral library_POS_v1.msp":
        "f68eabc09361ac0e60e9e410d01216c783f3f2d023b99b2d2b40fa831e4f7146",
    "WFSR food safety mass spectral library_NEG_v1.db":
        "f366abc53ae95710e46a19641386f0c79502a5169b781de6dde0fa5b79a4e3c8",
    "WFSR food safety mass spectral library_NEG_v1.msp":
        "a0b76f95d124a115c7329e1726054e8231d49818ab75990653357fc95c332d15",
    "WFSR food safety mass spectral library_POS_v1.db":
        "8417e5c95554b0ec026446bbd7135b4d0ff707c5ff25b8a1e6ec89895b93b759",
    "WFSR food safety mass spectral library_POS_v1.msp":
        "927ed3e358874916031504a180034ed689b17b1d3f7eb97e10d770c60d0c602d",
    "WUR mass spectral library_NEG_v1.db":
        "998eb80129db97dc94abf8feccbc7ab9c40c86cf0650e0fc99b3981816b03dd9",
    "WUR mass spectral library_NEG_v1.msp":
        "77341c91f1d541be11996f3e18fa328978aaa31d661d58c701215732cef7f009",
    "WUR mass spectral library_POS_v1.db":
        "dde1e0cc5fc16fb3f575821ad26d9478fbf1d415273135a3593556bc2cae910e",
    "WUR mass spectral library_POS_v1.msp":
        "cca14c5afce38c2fa0727cdaed774f89393b748ce0f30cd164e735586e33b068",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(data_dir: Path) -> dict:
    """Verify every file in EXPECTED_FILES is present under `data_dir` with
    the pinned hash. Never raises -- callers check `missing` and
    `hash_mismatches` and decide whether to fail."""
    files, mismatches, missing = [], [], []
    for name, expected_hash in sorted(EXPECTED_FILES.items()):
        path = data_dir / name
        if not path.exists():
            missing.append(name)
            continue
        actual_hash = sha256_of(path)
        if actual_hash != expected_hash:
            mismatches.append(name)
        files.append({
            "path": name,
            "sha256": actual_hash,
            "size_bytes": path.stat().st_size,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        })
    return {
        "source": "Zenodo record 20552933, WUR Mass Spectral Library v1.0",
        "doi": "10.5281/zenodo.20552933",
        "licence": "CC-BY 4.0",
        "root": "data/external/wur",
        "files": files,
        "n_files": len(files),
        "n_expected": len(EXPECTED_FILES),
        "missing": missing,
        "hash_mismatches": mismatches,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/test_wur_retrieval.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Write the CLI wrapper**

```python
# scripts/build_wur_retrieval_manifest.py
"""Verify the WUR raw files and write artifacts/wur_retrieval_manifest.json.

Usage: python scripts/build_wur_retrieval_manifest.py [data/external/wur]
"""
import json
import sys
from pathlib import Path

from muru.io.wur_retrieval import build_manifest

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    manifest = build_manifest(data_dir)
    out = ROOT / "artifacts" / "wur_retrieval_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    if manifest["missing"] or manifest["hash_mismatches"]:
        print(f"WARNING: {len(manifest['missing'])} missing, "
              f"{len(manifest['hash_mismatches'])} hash mismatches",
              file=sys.stderr)
        sys.exit(1)
    print(f"Wrote {out} ({manifest['n_files']} files verified)")
```

- [ ] **Step 7: Place the raw files and run it for real**

Retrieve the pinned release (DOI `10.5281/zenodo.20552933`) into
`data/external/wur/` if it is not already staged there, then:

```bash
PYTHONPATH=src python scripts/build_wur_retrieval_manifest.py
```

Expected: exits 0, prints `Wrote .../artifacts/wur_retrieval_manifest.json
(20 files verified)`. If it exits 1, stop here — do not proceed to Task 2
against unverified bytes.

- [ ] **Step 8: Commit**

```bash
git add src/muru/io/wur_retrieval.py \
        scripts/build_wur_retrieval_manifest.py tests/test_wur_retrieval.py \
        artifacts/wur_retrieval_manifest.json
git commit -m "wur: add retrieval manifest and hash verification for the frozen release"
```

---

## Task 2: Raw mzVault reader

**Files:**
- Create: `src/muru/io/wur_raw.py`
- Create: `tests/fixtures/wur_db.py` (`tests/fixtures/` already exists as a
  namespace package — confirmed no `__init__.py` there; do not add one.
  Tests already import from it as `from fixtures.wur_db import ...`, not
  `from tests.fixtures...` — this repo's `pytest.ini` sets only
  `pythonpath = src`, so a test under `tests/` never sees `tests` itself
  as an importable package, only `src` and its own directory)
- Test: `tests/test_wur_raw.py`

**Interfaces:**
- Consumes: nothing from Task 1 at the code level (only shares the
  `data/external/wur/` convention)
- Produces: `LIBRARY_DB_FILES: dict[tuple[str, str], str]`,
  `RAW_COLUMNS: list[str]`,
  `read_mzvault_db(path: Path, source_library: str, source_polarity_file: str) -> pd.DataFrame`,
  `read_all_libraries(data_dir: Path, polarity_file: str) -> pd.DataFrame`.
  Also: `tests/fixtures/wur_db.py` exposes
  `make_fixture_db(path: Path, compounds: list[dict]) -> None`,
  `true_inchikey(smiles: str) -> str`, `true_exact_mass(smiles: str) -> float`
  — reused by Tasks 3 and 4's tests.

The real mzVault schema (confirmed by inspecting the actual release files,
`sqlite3 <file>.db .schema`):

```sql
CREATE TABLE CompoundTable([CompoundId] INTEGER PRIMARY KEY, [Formula] TEXT,
  [Name] TEXT, ..., [SmilesDescription] TEXT, [InChiKey] TEXT);
CREATE TABLE SpectrumTable ([SpectrumId] INTEGER PRIMARY KEY,
  [CompoundId] INTEGER REFERENCES [CompoundTable]([CompoundId]), ...,
  [PrecursorMass] DOUBLE, [CollisionEnergy] TEXT, [Polarity] TEXT,
  [FragmentationMode] TEXT, ..., [PrecursorIonType] TEXT, [Accession] TEXT);
```

- [ ] **Step 1: Write the shared fixture builder**

```python
# tests/fixtures/wur_db.py
"""Shared fixture builder for WUR mzVault-schema SQLite test databases.

Builds a minimal database against the real CompoundTable/SpectrumTable
schema (confirmed against the actual release files) so tests exercise the
real query path without needing the 200MB real release on disk.
"""
import sqlite3
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, inchi

PROTON = 1.007276

SCHEMA = """
CREATE TABLE CompoundTable(
    CompoundId INTEGER PRIMARY KEY, Formula TEXT, Name TEXT,
    InChiKey TEXT, SmilesDescription TEXT
);
CREATE TABLE SpectrumTable(
    SpectrumId INTEGER PRIMARY KEY, CompoundId INTEGER, ScanFilter TEXT,
    PrecursorMass DOUBLE, CollisionEnergy TEXT, Polarity TEXT,
    FragmentationMode TEXT, PrecursorIonType TEXT
);
"""


def true_inchikey(smiles: str) -> str:
    return inchi.MolToInchiKey(Chem.MolFromSmiles(smiles))


def true_exact_mass(smiles: str) -> float:
    return Descriptors.ExactMolWt(Chem.MolFromSmiles(smiles))


def make_fixture_db(path: Path, compounds: list[dict]) -> None:
    """Write a tiny mzVault-schema SQLite file at `path`.

    Each item of `compounds` is a dict:
      smiles (required), name, inchikey (default: true_inchikey(smiles)),
      energies (default: the full six-rung ladder as strings),
      polarity (default "+"), fragmentation_mode (default "HCD"),
      precursor_mass (default: true [M+H]+ mass),
      precursor_ion_type (default "").
    """
    con = sqlite3.connect(str(path))
    con.executescript(SCHEMA)
    compound_id = 0
    spectrum_id = 0
    for spec in compounds:
        compound_id += 1
        smiles = spec["smiles"]
        inchikey = spec.get("inchikey", true_inchikey(smiles))
        con.execute(
            "INSERT INTO CompoundTable (CompoundId, Formula, Name, InChiKey, "
            "SmilesDescription) VALUES (?, ?, ?, ?, ?)",
            (compound_id, "", spec.get("name", smiles), inchikey, smiles),
        )
        precursor_mass = spec.get(
            "precursor_mass", true_exact_mass(smiles) + PROTON)
        for energy in spec.get(
                "energies", ["15.0", "30.0", "45.0", "60.0", "75.0", "90.0"]):
            spectrum_id += 1
            con.execute(
                "INSERT INTO SpectrumTable (SpectrumId, CompoundId, "
                "ScanFilter, PrecursorMass, CollisionEnergy, Polarity, "
                "FragmentationMode, PrecursorIonType) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (spectrum_id, compound_id, "", precursor_mass, energy,
                 spec.get("polarity", "+"),
                 spec.get("fragmentation_mode", "HCD"),
                 spec.get("precursor_ion_type", "")),
            )
    con.commit()
    con.close()
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_wur_raw.py
from muru.io.wur_raw import LIBRARY_DB_FILES, RAW_COLUMNS, read_mzvault_db
from fixtures.wur_db import make_fixture_db


def test_read_mzvault_db_returns_one_row_per_spectrum(tmp_path):
    db_path = tmp_path / "fixture.db"
    make_fixture_db(db_path, [
        {"smiles": "CCO", "name": "ethanol"},
        {"smiles": "c1ccccc1", "name": "benzene", "energies": ["15.0", "30.0"]},
    ])
    df = read_mzvault_db(db_path, "WUR", "POS")
    assert list(df.columns) == RAW_COLUMNS
    assert len(df) == 6 + 2
    assert set(df["source_library"]) == {"WUR"}
    assert set(df["source_polarity_file"]) == {"POS"}


def test_library_db_files_covers_five_libraries_and_two_polarities():
    libraries = {lib for lib, _ in LIBRARY_DB_FILES}
    polarities = {pf for _, pf in LIBRARY_DB_FILES}
    assert libraries == {"ETE", "FCH", "WFSR_Polar", "WFSR_food_safety", "WUR"}
    assert polarities == {"POS", "NEG"}
    assert len(LIBRARY_DB_FILES) == 10
```

- [ ] **Step 3: Run it to verify it fails**

Run: `pytest tests/test_wur_raw.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_raw'`

- [ ] **Step 4: Implement `src/muru/io/wur_raw.py`**

```python
# src/muru/io/wur_raw.py
"""Identity-only reader for the WUR release's mzVault SQLite files.

Reads CompoundTable/SpectrumTable header columns only -- no
blobMass/blobIntensity/blobAccuracy. The .db files are authoritative over
the .msp files in this release (spec §3): they agree on peaks 99.9% of the
time, but only .db records FragmentationMode, without which HCD 25 and
UVPD 25 are indistinguishable.
"""
from pathlib import Path
import sqlite3

import pandas as pd

RAW_COLUMNS = [
    "source_library", "source_polarity_file", "compound_id", "name",
    "formula", "smiles", "inchikey", "spectrum_id", "precursor_mass",
    "collision_energy_raw", "fragmentation_mode", "polarity",
    "precursor_ion_type",
]

# (library, polarity_file) -> filename stem (no extension), exactly as
# named in the frozen Zenodo release (see wur_retrieval.EXPECTED_FILES for
# the full filenames including extension and pinned hashes). The WFSR_Polar
# NEG stem carries the release's own stray space before "_NEG" -- preserved
# verbatim.
LIBRARY_DB_FILES = {
    ("ETE", "POS"): "ETE organic environmental pollutants mass spectral library_POS_v1",
    ("ETE", "NEG"): "ETE organic environmental pollutants mass spectral library_NEG_v1",
    ("FCH", "POS"): "FCH food small molecules mass spectral library_POS_v1",
    ("FCH", "NEG"): "FCH food small molecules mass spectral library_NEG_v1",
    ("WFSR_Polar", "POS"): "WFSR Polar substances mass spectral library_POS_v1",
    ("WFSR_Polar", "NEG"): "WFSR Polar substances mass spectral library _NEG_v1",
    ("WFSR_food_safety", "POS"): "WFSR food safety mass spectral library_POS_v1",
    ("WFSR_food_safety", "NEG"): "WFSR food safety mass spectral library_NEG_v1",
    ("WUR", "POS"): "WUR mass spectral library_POS_v1",
    ("WUR", "NEG"): "WUR mass spectral library_NEG_v1",
}


def read_mzvault_db(path: Path, source_library: str,
                     source_polarity_file: str) -> pd.DataFrame:
    con = sqlite3.connect(str(path))
    try:
        df = pd.read_sql_query(
            """
            SELECT
                c.CompoundId        AS compound_id,
                c.Name              AS name,
                c.Formula           AS formula,
                c.SmilesDescription AS smiles,
                c.InChiKey          AS inchikey,
                s.SpectrumId        AS spectrum_id,
                s.PrecursorMass     AS precursor_mass,
                s.CollisionEnergy   AS collision_energy_raw,
                s.FragmentationMode AS fragmentation_mode,
                s.Polarity          AS polarity,
                s.PrecursorIonType  AS precursor_ion_type
            FROM CompoundTable c
            JOIN SpectrumTable s ON s.CompoundId = c.CompoundId
            """,
            con,
        )
    finally:
        con.close()
    df.insert(0, "source_polarity_file", source_polarity_file)
    df.insert(0, "source_library", source_library)
    return df[RAW_COLUMNS]


def read_all_libraries(data_dir: Path, polarity_file: str) -> pd.DataFrame:
    """Concatenate all five libraries' `.db` file for one nominal polarity
    file ("POS" or "NEG") into one raw per-spectrum table."""
    frames = [
        read_mzvault_db(data_dir / f"{stem}.db", library, pf)
        for (library, pf), stem in LIBRARY_DB_FILES.items()
        if pf == polarity_file
    ]
    return pd.concat(frames, ignore_index=True)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/test_wur_raw.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add src/muru/io/wur_raw.py tests/fixtures/wur_db.py tests/test_wur_raw.py
git commit -m "wur: add mzVault SQLite reader and shared test fixture"
```

---

## Task 3: Identity gate primitives

**Files:**
- Create: `src/muru/io/wur_identity.py`
- Test: `tests/test_wur_identity.py`

**Interfaces:**
- Consumes: nothing (pure functions)
- Produces: `LADDER_ENERGIES: tuple[float, ...]`,
  `normalize_collision_energy(raw) -> float | None`,
  `snap_to_ladder(energy: float | None) -> float | None`,
  `connectivity_key(inchikey: str) -> str`,
  `verify_identity(smiles: str, recorded_inchikey: str) -> bool`,
  `infer_adduct(smiles: str, precursor_mass: float, polarity: str) -> str | None`.
  These are consumed by Task 4's `build_qualifying_trajectories`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wur_identity.py
import pytest
from rdkit import Chem
from rdkit.Chem import Descriptors, inchi

from muru.io.wur_identity import (
    LADDER_ENERGIES, normalize_collision_energy, snap_to_ladder,
    connectivity_key, verify_identity, infer_adduct,
)


def test_normalize_collision_energy_parses_plain_float():
    assert normalize_collision_energy("15.0") == 15.0


def test_normalize_collision_energy_parses_long_decimal():
    assert normalize_collision_energy("15.0000000000000000000000") == 15.0


def test_normalize_collision_energy_rejects_stepped_energy():
    assert normalize_collision_energy("25,38,59") is None


def test_normalize_collision_energy_rejects_garbage():
    assert normalize_collision_energy("not a number") is None


def test_normalize_collision_energy_rejects_none():
    assert normalize_collision_energy(None) is None


@pytest.mark.parametrize("rung", LADDER_ENERGIES)
def test_snap_to_ladder_matches_exact_rung(rung):
    assert snap_to_ladder(rung) == rung


def test_snap_to_ladder_rejects_off_ladder_value():
    assert snap_to_ladder(40.7) is None


def test_connectivity_key_takes_first_block():
    assert connectivity_key("LFQSCWFLJHTTHZ-UHFFFAOYSA-N") == "LFQSCWFLJHTTHZ"


def test_verify_identity_accepts_matching_smiles_and_inchikey():
    smiles = "CCO"
    real_inchikey = inchi.MolToInchiKey(Chem.MolFromSmiles(smiles))
    assert verify_identity(smiles, real_inchikey) is True


def test_verify_identity_rejects_mismatched_inchikey():
    assert verify_identity("CCO", "AAAAAAAAAAAAAA-UHFFFAOYSA-N") is False


def test_verify_identity_rejects_unparseable_smiles():
    assert verify_identity("not a smiles", "AAAAAAAAAAAAAA-UHFFFAOYSA-N") is False


def test_infer_adduct_resolves_mh_plus():
    smiles = "CCO"
    exact_mass = Descriptors.ExactMolWt(Chem.MolFromSmiles(smiles))
    precursor_mass = exact_mass + 1.007276
    assert infer_adduct(smiles, precursor_mass, "+") == "[M+H]+"


def test_infer_adduct_resolves_m_minus_h_negative():
    smiles = "CCO"
    exact_mass = Descriptors.ExactMolWt(Chem.MolFromSmiles(smiles))
    precursor_mass = exact_mass - 1.007276
    assert infer_adduct(smiles, precursor_mass, "-") == "[M-H]-"


def test_infer_adduct_returns_none_when_nothing_matches():
    assert infer_adduct("CCO", 9999.0, "+") is None
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_wur_identity.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `src/muru/io/wur_identity.py`**

```python
# src/muru/io/wur_identity.py
"""Identity-only gates for WUR spectra, per the known defects recorded in
spec §3.2 -- gated here rather than discovered downstream."""
from rdkit import Chem
from rdkit.Chem import Descriptors, inchi

LADDER_ENERGIES = (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)
ENERGY_TOL = 0.01

# Standard adduct mass shifts (Da): m/z(adduct) - exact_mass(M).
ADDUCT_SHIFTS_POS = {
    "[M+H]+": 1.007276,
    "[M+NH4]+": 18.033823,
    "[M+Na]+": 22.989218,
    "[M]+": -0.000549,
}
ADDUCT_SHIFTS_NEG = {
    "[M-H]-": -1.007276,
}
ADDUCT_PPM_TOL = 10.0


def normalize_collision_energy(raw) -> float | None:
    """Parse a raw CollisionEnergy string to a float. None for a
    stepped-energy value (contains a comma, e.g. "25,38,59") or any
    unparseable string -- defect: 1,017 stepped-energy spectra excluded."""
    if raw is None:
        return None
    text = str(raw).strip()
    if "," in text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def snap_to_ladder(energy: float | None) -> float | None:
    """The ladder rung `energy` matches within ENERGY_TOL, else None --
    defect: 857 off-ladder energies excluded."""
    if energy is None:
        return None
    for rung in LADDER_ENERGIES:
        if abs(energy - rung) <= ENERGY_TOL:
            return rung
    return None


def connectivity_key(inchikey: str) -> str:
    """The InChIKey first block -- the connectivity key `splits.py` and
    `molecules.py` use throughout the codebase."""
    return inchikey.split("-")[0]


def verify_identity(smiles: str, recorded_inchikey: str) -> bool:
    """True if the InChIKey recomputed from `smiles` shares its
    connectivity block with `recorded_inchikey` -- defect: 4 compounds
    whose deposited SMILES contradicts its own InChIKey, excluded."""
    if not smiles or not recorded_inchikey:
        return False
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    recomputed = inchi.MolToInchiKey(mol)
    if not recomputed:
        return False
    return connectivity_key(recomputed) == connectivity_key(recorded_inchikey)


def infer_adduct(smiles: str, precursor_mass: float,
                  polarity: str) -> str | None:
    """The adduct whose theoretical m/z matches `precursor_mass` within
    ADDUCT_PPM_TOL ppm. None if zero or more than one adduct matches --
    defect: precursor ion type is blank in every record (54 unresolved)."""
    if precursor_mass is None:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    exact_mass = Descriptors.ExactMolWt(mol)
    table = ADDUCT_SHIFTS_POS if polarity == "+" else ADDUCT_SHIFTS_NEG
    matches = []
    for adduct, shift in table.items():
        theoretical = exact_mass + shift
        ppm = abs(theoretical - precursor_mass) / theoretical * 1e6
        if ppm <= ADDUCT_PPM_TOL:
            matches.append(adduct)
    return matches[0] if len(matches) == 1 else None
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_wur_identity.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
git add src/muru/io/wur_identity.py tests/test_wur_identity.py
git commit -m "wur: add identity-gate primitives (energy, adduct, identity checks)"
```

---

## Task 4: Qualifying-trajectory builder and the identity census

**Files:**
- Modify: `src/muru/io/wur_identity.py` (add `build_qualifying_trajectories`)
- Create: `src/muru/io/wur_census.py`
- Create: `scripts/build_wur_identity_census.py`
- Test: `tests/test_wur_qualifying_trajectories.py`
- Test: `tests/test_wur_census.py`

**Interfaces:**
- Consumes: `muru.io.wur_raw.read_mzvault_db`, `read_all_libraries`;
  `muru.io.wur_identity.{normalize_collision_energy, snap_to_ladder,
  connectivity_key, verify_identity, infer_adduct, LADDER_ENERGIES}`;
  `muru.molecules.scaffold_group(smiles: str, connectivity_key: str) -> str`;
  `muru.synth.generators.sealed_keys() -> set[str]`
- Produces: `build_qualifying_trajectories(raw: pd.DataFrame, polarity: str) -> pd.DataFrame`
  (columns: `connectivity_key, smiles, adduct, polarity, n_source_rows,
  source_libraries`), `load_annotated_trajectories(data_dir: Path) -> dict[str, pd.DataFrame]`
  (keys `"POS"`/`"NEG"`, each adding `scaffold_group, in_lcsb_dev,
  in_lcsb_sealed`), `build_census(annotated: dict[str, pd.DataFrame]) -> dict`.
  Consumed by Task 5's `wur_partition.py`.

- [ ] **Step 1: Write the failing tests for `build_qualifying_trajectories`**

```python
# tests/test_wur_qualifying_trajectories.py
import pandas as pd

from muru.io.wur_identity import build_qualifying_trajectories
from muru.io.wur_raw import read_mzvault_db
from fixtures.wur_db import make_fixture_db, true_inchikey


def _raw(tmp_path, compounds, library="WUR", polarity_file="POS", name="fixture.db"):
    db_path = tmp_path / name
    make_fixture_db(db_path, compounds)
    return read_mzvault_db(db_path, library, polarity_file)


def test_full_ladder_hcd_compound_qualifies(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "name": "ethanol"}])
    traj = build_qualifying_trajectories(raw, "+")
    assert len(traj) == 1
    assert traj.iloc[0]["adduct"] == "[M+H]+"
    assert traj.iloc[0]["connectivity_key"] == connectivity_key_of("CCO")


def connectivity_key_of(smiles: str) -> str:
    return true_inchikey(smiles).split("-")[0]


def test_incomplete_ladder_is_excluded(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "energies": ["15.0", "30.0", "45.0"]}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_stepped_energy_row_is_dropped_but_full_ladder_still_qualifies(tmp_path):
    raw = _raw(tmp_path, [{
        "smiles": "CCO",
        "energies": ["15.0", "30.0", "45.0", "60.0", "75.0", "90.0", "25,38,59"],
    }])
    assert len(build_qualifying_trajectories(raw, "+")) == 1


def test_identity_mismatch_is_excluded(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "inchikey": "AAAAAAAAAAAAAA-UHFFFAOYSA-N"}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_unresolved_adduct_is_excluded(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "precursor_mass": 9999.0}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_wrong_polarity_row_is_excluded_from_positive_population(tmp_path):
    raw = _raw(tmp_path, [{"smiles": "CCO", "polarity": "-"}])
    assert len(build_qualifying_trajectories(raw, "+")) == 0


def test_same_compound_across_two_libraries_merges_into_one_trajectory(tmp_path):
    raw_a = _raw(tmp_path, [{"smiles": "CCO"}], library="WUR", name="a.db")
    raw_b = _raw(tmp_path, [{"smiles": "CCO"}], library="WFSR_food_safety", name="b.db")
    raw = pd.concat([raw_a, raw_b], ignore_index=True)
    traj = build_qualifying_trajectories(raw, "+")
    assert len(traj) == 1
    assert set(traj.iloc[0]["source_libraries"]) == {"WUR", "WFSR_food_safety"}
    assert traj.iloc[0]["n_source_rows"] == 12


def test_picks_lexicographically_first_smiles_across_duplicate_deposits(tmp_path):
    ik = true_inchikey("CCO")
    raw_a = _raw(tmp_path, [{"smiles": "OCC", "inchikey": ik}], library="WUR", name="a.db")
    raw_b = _raw(tmp_path, [{"smiles": "CCO", "inchikey": ik}], library="WFSR_food_safety", name="b.db")
    raw = pd.concat([raw_a, raw_b], ignore_index=True)
    traj = build_qualifying_trajectories(raw, "+")
    assert traj.iloc[0]["smiles"] == min("OCC", "CCO")
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_wur_qualifying_trajectories.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_qualifying_trajectories'`

- [ ] **Step 3: Implement `build_qualifying_trajectories`**

Append to `src/muru/io/wur_identity.py`:

```python
import pandas as pd


def build_qualifying_trajectories(raw: pd.DataFrame, polarity: str) -> pd.DataFrame:
    """Reduce raw per-spectrum rows (any number of source libraries, one
    nominal polarity) to one row per qualifying trajectory.

    A trajectory qualifies if its HCD spectra, on the compound's own
    Polarity field (not the source file name), cover the full six-point
    ladder with no stepped or off-ladder residue, its deposited SMILES
    verifies against its own InChIKey, and exactly one adduct explains its
    precursor mass. Duplicate/cross-library deposits of the same connectivity
    key are merged into one row here, not dropped -- this is where defect
    "62/61 duplicate combos" (spec §3.2) is resolved.

    Returns: connectivity_key, smiles (lexicographically first deposited
    SMILES for that key -- design rule D1), adduct, polarity, n_source_rows,
    source_libraries (sorted tuple).
    """
    df = raw[
        (raw["fragmentation_mode"] == "HCD")
        & (raw["polarity"] == polarity)
        & raw["smiles"].notna()
        & raw["inchikey"].notna()
    ].copy()

    df["energy"] = (
        df["collision_energy_raw"].map(normalize_collision_energy).map(snap_to_ladder)
    )
    df = df[df["energy"].notna()].copy()

    df["identity_ok"] = [
        verify_identity(s, k) for s, k in zip(df["smiles"], df["inchikey"])
    ]
    df = df[df["identity_ok"]].copy()
    df["connectivity_key"] = df["inchikey"].map(connectivity_key)

    df["adduct"] = [
        infer_adduct(s, m, polarity)
        for s, m in zip(df["smiles"], df["precursor_mass"])
    ]
    df = df[df["adduct"].notna()]

    columns = ["connectivity_key", "smiles", "adduct", "polarity",
               "n_source_rows", "source_libraries"]
    rows = []
    for key, grp in df.groupby("connectivity_key"):
        if set(grp["energy"]) != set(LADDER_ENERGIES):
            continue
        rows.append({
            "connectivity_key": key,
            "smiles": min(grp["smiles"]),
            "adduct": grp["adduct"].value_counts().idxmax(),
            "polarity": polarity,
            "n_source_rows": len(grp),
            "source_libraries": tuple(sorted(grp["source_library"].unique())),
        })
    return pd.DataFrame(rows, columns=columns)
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_wur_qualifying_trajectories.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Write the failing tests for census/annotation**

```python
# tests/test_wur_census.py
import pandas as pd

from muru.io.wur_census import build_census, load_annotated_trajectories


def test_build_census_reports_counts_and_lcsb_overlap():
    traj = pd.DataFrame({
        "connectivity_key": ["K0", "K1", "K2"],
        "scaffold_group": ["g0", "g0", "g1"],
        "source_libraries": [("WUR",), ("WFSR_food_safety",), ("WUR", "FCH")],
        "adduct": ["[M+H]+", "[M+H]+", "[M+Na]+"],
        "in_lcsb_dev": [True, False, False],
        "in_lcsb_sealed": [False, False, True],
    })
    census = build_census({"POS": traj, "NEG": traj.iloc[:0]})
    pos = census["polarities"]["POS"]
    assert pos["n_trajectories"] == 3
    assert pos["n_scaffold_groups"] == 2
    assert pos["n_from_wfsr_food_safety"] == 1
    assert pos["n_in_lcsb_dev"] == 1
    assert pos["n_in_lcsb_sealed"] == 1
    assert census["polarities"]["NEG"]["n_trajectories"] == 0


def test_load_annotated_trajectories_flags_lcsb_membership(tmp_path, monkeypatch):
    import muru.io.wur_census as mod
    from fixtures.wur_db import make_fixture_db, true_inchikey

    # read_all_libraries expects all 10 db files to exist; write one tiny
    # database per (library, polarity_file), empty except where noted.
    for (library, pf), stem in mod.wur_raw.LIBRARY_DB_FILES.items():
        if pf == "POS" and library == "WUR":
            make_fixture_db(tmp_path / f"{stem}.db", [{"smiles": "CCO"}])
        elif pf == "POS" and library == "ETE":
            make_fixture_db(tmp_path / f"{stem}.db", [{"smiles": "c1ccccc1"}])
        else:
            make_fixture_db(tmp_path / f"{stem}.db", [])

    dev_key = true_inchikey("CCO").split("-")[0]
    sealed_key = true_inchikey("c1ccccc1").split("-")[0]
    monkeypatch.setattr(mod, "dev_corpus_keys", lambda: {dev_key})
    monkeypatch.setattr(mod, "sealed_keys", lambda: {sealed_key})

    annotated = load_annotated_trajectories(tmp_path)
    pos = annotated["POS"]
    assert bool(pos.loc[pos["connectivity_key"] == dev_key, "in_lcsb_dev"].iloc[0])
    assert bool(pos.loc[pos["connectivity_key"] == sealed_key, "in_lcsb_sealed"].iloc[0])
    assert "scaffold_group" in pos.columns
```

- [ ] **Step 6: Run to verify failure**

Run: `pytest tests/test_wur_census.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_census'`

- [ ] **Step 7: Implement `src/muru/io/wur_census.py`**

```python
# src/muru/io/wur_census.py
"""Annotate qualifying WUR trajectories against the existing LCSB
development corpus and sealed confirmation set, and summarize the census."""
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from muru.io import wur_raw
from muru.io.wur_identity import build_qualifying_trajectories
from muru.molecules import scaffold_group
from muru.synth.generators import sealed_keys

ROOT = Path(__file__).resolve().parents[3]


def dev_corpus_keys() -> set[str]:
    dev = pd.read_parquet(ROOT / "artifacts" / "p2_dev_corpus.parquet")
    return set(dev["inchikey_first_block"])


def load_annotated_trajectories(data_dir: Path) -> dict[str, pd.DataFrame]:
    sealed = sealed_keys()
    dev_keys = dev_corpus_keys()
    out = {}
    for polarity_file, polarity_symbol in (("POS", "+"), ("NEG", "-")):
        raw = wur_raw.read_all_libraries(data_dir, polarity_file)
        traj = build_qualifying_trajectories(raw, polarity_symbol)
        if len(traj):
            traj["scaffold_group"] = [
                scaffold_group(s, k) for s, k in
                zip(traj["smiles"], traj["connectivity_key"])
            ]
            traj["in_lcsb_dev"] = traj["connectivity_key"].isin(dev_keys)
            traj["in_lcsb_sealed"] = traj["connectivity_key"].isin(sealed)
        else:
            traj["scaffold_group"] = pd.Series(dtype=str)
            traj["in_lcsb_dev"] = pd.Series(dtype=bool)
            traj["in_lcsb_sealed"] = pd.Series(dtype=bool)
        out[polarity_file] = traj
    return out


def build_census(annotated: dict[str, pd.DataFrame]) -> dict:
    census = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "polarities": {}}
    for polarity_file, traj in annotated.items():
        n = len(traj)
        n_wfsr_fs = int(
            traj["source_libraries"].apply(
                lambda ls: "WFSR_food_safety" in ls).sum()) if n else 0
        census["polarities"][polarity_file] = {
            "n_trajectories": int(n),
            "n_scaffold_groups": int(traj["scaffold_group"].nunique()) if n else 0,
            "n_from_wfsr_food_safety": n_wfsr_fs,
            "n_in_lcsb_dev": int(traj["in_lcsb_dev"].sum()) if n else 0,
            "n_in_lcsb_sealed": int(traj["in_lcsb_sealed"].sum()) if n else 0,
            "adduct_counts": traj["adduct"].value_counts().to_dict() if n else {},
        }
    return census
```

- [ ] **Step 8: Run to verify it passes**

Run: `pytest tests/test_wur_census.py -v`
Expected: PASS (2 tests)

- [ ] **Step 9: Write the CLI wrapper**

```python
# scripts/build_wur_identity_census.py
"""CLI: build artifacts/wur_identity_census.json from data/external/wur/."""
import json
import sys
from pathlib import Path

from muru.io.wur_census import build_census, load_annotated_trajectories

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    annotated = load_annotated_trajectories(data_dir)
    census = build_census(annotated)
    out = ROOT / "artifacts" / "wur_identity_census.json"
    out.write_text(json.dumps(census, indent=2) + "\n")
    print(f"Wrote {out}")
    for pf, entry in census["polarities"].items():
        print(f"  {pf}: {entry['n_trajectories']} trajectories, "
              f"{entry['n_scaffold_groups']} scaffold groups")
```

- [ ] **Step 10: Run it against the real release**

```bash
PYTHONPATH=src python scripts/build_wur_identity_census.py
```

Expected: exits 0, prints trajectory/scaffold-group counts for POS and NEG.
Record these numbers against the sealed-part floor check in Task 5/6 — they
need not match the design session's 971/581 headline (see Global
Constraints).

- [ ] **Step 11: Commit**

```bash
git add src/muru/io/wur_identity.py src/muru/io/wur_census.py \
        scripts/build_wur_identity_census.py \
        tests/test_wur_qualifying_trajectories.py tests/test_wur_census.py \
        artifacts/wur_identity_census.json
git commit -m "wur: add qualifying-trajectory builder and identity census"
```

---

## Task 5: Partition logic (D1–D5) and the sealed-part floor check

**Files:**
- Create: `src/muru/io/wur_partition.py`
- Test: `tests/test_wur_partition.py`

**Interfaces:**
- Consumes: the `scaffold_group`/`in_lcsb_dev`/`in_lcsb_sealed`-annotated
  DataFrames produced by Task 4's `load_annotated_trajectories`
- Produces: `SEED = 20260911`, `SEALED_TRAJECTORY_FLOOR = 250`,
  `SEALED_SCAFFOLD_GROUP_FLOOR = 150`,
  `assign_side_by_group(pos_traj: pd.DataFrame, seed: int = SEED) -> pd.DataFrame`
  (adds a `side` column, values `"WUR-DEV"`/`"WUR-SEALED"`),
  `check_sealed_floor(sealed_df: pd.DataFrame) -> dict`,
  `partition(annotated: dict[str, pd.DataFrame], seed: int = SEED) -> dict[str, pd.DataFrame]`.
  Consumed by Task 6's `scripts/build_wur_partition.py`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wur_partition.py
import pandas as pd

from muru.io.wur_partition import (
    SEED, assign_side_by_group, check_sealed_floor, partition,
)


def _toy_pos(n_free_groups=40):
    rows = []
    for g in range(2):
        rows.append({"connectivity_key": f"DEV{g}", "scaffold_group": f"devgrp{g}",
                     "in_lcsb_dev": True, "in_lcsb_sealed": False})
    rows.append({"connectivity_key": "BOTH0", "scaffold_group": "bothgrp",
                 "in_lcsb_dev": True, "in_lcsb_sealed": True})
    for g in range(n_free_groups):
        rows.append({"connectivity_key": f"FREE{g}", "scaffold_group": f"free{g}",
                     "in_lcsb_dev": False, "in_lcsb_sealed": False})
    return pd.DataFrame(rows)


def test_group_touching_dev_goes_to_wur_dev():
    df = assign_side_by_group(_toy_pos())
    assert (df.loc[df["scaffold_group"] == "devgrp0", "side"] == "WUR-DEV").all()


def test_group_touching_both_dev_and_sealed_goes_to_sealed_d3_beats_d2():
    df = assign_side_by_group(_toy_pos())
    assert (df.loc[df["scaffold_group"] == "bothgrp", "side"] == "WUR-SEALED").all()


def test_free_groups_split_roughly_in_half():
    df = assign_side_by_group(_toy_pos(n_free_groups=40))
    free = df[df["scaffold_group"].str.startswith("free")]
    counts = free.groupby("side")["scaffold_group"].nunique()
    assert abs(counts.get("WUR-DEV", 0) - counts.get("WUR-SEALED", 0)) <= 1


def test_free_group_split_is_deterministic_at_fixed_seed():
    df1 = assign_side_by_group(_toy_pos(), seed=SEED)
    df2 = assign_side_by_group(_toy_pos(), seed=SEED)
    pd.testing.assert_series_equal(
        df1.set_index("connectivity_key")["side"].sort_index(),
        df2.set_index("connectivity_key")["side"].sort_index(),
    )


def test_a_scaffold_group_never_splits_across_sides():
    df = assign_side_by_group(_toy_pos(n_free_groups=60))
    per_group_sides = df.groupby("scaffold_group")["side"].nunique()
    assert (per_group_sides == 1).all()


def test_check_sealed_floor_reports_pass_and_fail():
    passing = pd.DataFrame({"scaffold_group": [f"g{i}" for i in range(150)] * 2})
    result = check_sealed_floor(passing)
    assert result["n_trajectories"] == 300
    assert result["passes_trajectory_floor"] is True
    assert result["passes_scaffold_group_floor"] is True

    failing = pd.DataFrame({"scaffold_group": ["g0"] * 10})
    assert check_sealed_floor(failing)["passes_trajectory_floor"] is False


def test_negative_mode_is_entirely_wur_dev_even_if_it_touches_sealed():
    annotated = {
        "POS": _toy_pos(),
        "NEG": pd.DataFrame({
            "connectivity_key": ["N0", "N1"], "scaffold_group": ["ng0", "ng1"],
            "in_lcsb_dev": [False, False], "in_lcsb_sealed": [False, True],
        }),
    }
    result = partition(annotated)
    assert (result["NEG"]["side"] == "WUR-DEV").all()
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_wur_partition.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_partition'`

- [ ] **Step 3: Implement `src/muru/io/wur_partition.py`**

```python
# src/muru/io/wur_partition.py
"""Stage 0 partition rules D1-D5. D1 (scaffold group of the
lexicographically-first deposited SMILES) is already applied upstream, in
wur_census.load_annotated_trajectories -- this module applies D2-D5 to the
result."""
import numpy as np
import pandas as pd

SEED = 20260911
SEALED_TRAJECTORY_FLOOR = 250
SEALED_SCAFFOLD_GROUP_FLOOR = 150


def assign_side_by_group(pos_traj: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """D2-D4 on the positive-mode qualifying trajectory table. `pos_traj`
    must already carry scaffold_group/in_lcsb_dev/in_lcsb_sealed. Returns a
    copy with an added `side` column."""
    df = pos_traj.copy()
    by_group_dev = df.groupby("scaffold_group")["in_lcsb_dev"].any()
    by_group_sealed = df.groupby("scaffold_group")["in_lcsb_sealed"].any()
    touches_dev = set(by_group_dev[by_group_dev].index)
    touches_sealed = set(by_group_sealed[by_group_sealed].index)
    free_groups = sorted(set(df["scaffold_group"]) - touches_dev - touches_sealed)

    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(free_groups)
    half = len(shuffled) // 2
    free_sealed = set(shuffled[:half])

    def side_for(group: str) -> str:
        if group in touches_sealed:
            return "WUR-SEALED"                      # D3 beats D2
        if group in touches_dev:
            return "WUR-DEV"                          # D2
        return "WUR-SEALED" if group in free_sealed else "WUR-DEV"  # D4

    df["side"] = df["scaffold_group"].map(side_for)
    return df


def check_sealed_floor(sealed_df: pd.DataFrame) -> dict:
    n_traj = len(sealed_df)
    n_groups = sealed_df["scaffold_group"].nunique() if n_traj else 0
    return {
        "n_trajectories": int(n_traj),
        "n_scaffold_groups": int(n_groups),
        "trajectory_floor": SEALED_TRAJECTORY_FLOOR,
        "scaffold_group_floor": SEALED_SCAFFOLD_GROUP_FLOOR,
        "passes_trajectory_floor": n_traj >= SEALED_TRAJECTORY_FLOOR,
        "passes_scaffold_group_floor": n_groups >= SEALED_SCAFFOLD_GROUP_FLOOR,
    }


def partition(annotated: dict[str, pd.DataFrame],
              seed: int = SEED) -> dict[str, pd.DataFrame]:
    """D1 (upstream) through D5. Returns {"POS": ..., "NEG": ...}, each with
    a `side` column."""
    pos = assign_side_by_group(annotated["POS"], seed=seed)
    neg = annotated["NEG"].copy()
    neg["side"] = "WUR-DEV"                            # D5
    return {"POS": pos, "NEG": neg}
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_wur_partition.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/muru/io/wur_partition.py tests/test_wur_partition.py
git commit -m "wur: add D1-D5 partition assignment and sealed-part floor check"
```

---

## Task 6: Manifest builders, wiring script, and leakage tests

**Why the manifest builders live in `src/muru/io/wur_partition.py`, not the
script:** this repo's `pytest.ini` sets `pythonpath = src` and nothing else —
confirmed empirically in this worktree. Under that config, a test in
`tests/` cannot import anything from `scripts/` (`scripts` is never placed
on `sys.path`; only `src` is). Testable logic belongs in `src/muru/io/`;
`scripts/` holds thin, untested CLI wiring only, exactly like Tasks 1 and 4.

**Files:**
- Modify: `src/muru/io/wur_partition.py` (add `build_split_manifest`,
  `build_sealed_partition`)
- Create: `scripts/build_wur_partition.py` (thin CLI, no independently
  tested logic)
- Test: `tests/test_wur_partition_manifests.py`
- Create: `artifacts/wur_split_manifest.json` (generated, tracked)
- Create: `artifacts/wur_sealed_partition.json` (generated, tracked — same
  git-tracked-hash convention as `artifacts/confirmation_set_sealed.json`)
- Modify: `.gitignore` — add `!artifacts/wur_split_manifest.json` and
  `!artifacts/wur_sealed_partition.json`. `artifacts/*` is ignored by
  default in this repo; Task 4 hit the identical problem for
  `wur_identity_census.json` and fixed it with a two-line addition right
  after the existing `!artifacts/p3_*.json` line — follow that same
  precedent (a short comment plus the two `!` lines) rather than
  discovering this mid-task.

**Interfaces:**
- Consumes: `muru.io.wur_census.load_annotated_trajectories`;
  `muru.io.wur_partition.{partition, check_sealed_floor, SEED}` (from
  Task 5, already in `src/muru/io/wur_partition.py`)
- Produces: `muru.io.wur_partition.build_split_manifest(partitioned: dict[str, pd.DataFrame]) -> dict`,
  `muru.io.wur_partition.build_sealed_partition(pos_partitioned: pd.DataFrame) -> dict`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_wur_partition_manifests.py
import json

import pandas as pd

from muru.io.wur_partition import build_sealed_partition, build_split_manifest, partition


def _annotated():
    pos = pd.DataFrame({
        "connectivity_key": [f"K{i}" for i in range(20)],
        "scaffold_group": [f"g{i}" for i in range(20)],
        "in_lcsb_dev": [False] * 20,
        "in_lcsb_sealed": [False] * 20,
    })
    neg = pd.DataFrame({
        "connectivity_key": ["N0"], "scaffold_group": ["ng0"],
        "in_lcsb_dev": [False], "in_lcsb_sealed": [False],
    })
    return {"POS": pos, "NEG": neg}


def test_split_manifest_reports_both_sides_and_floor_check():
    manifest = build_split_manifest(partition(_annotated()))
    assert set(manifest["polarities"]["POS"]) >= {
        "WUR-DEV", "WUR-SEALED", "sealed_floor_check"}
    assert manifest["polarities"]["NEG"]["WUR-DEV"]["n_trajectories"] == 1


def test_sealed_partition_keys_disjoint_from_dev_side():
    partitioned = partition(_annotated())
    sealed = build_sealed_partition(partitioned["POS"])
    dev_keys = set(partitioned["POS"].loc[
        partitioned["POS"]["side"] == "WUR-DEV", "connectivity_key"])
    assert not (set(sealed["connectivity_keys"]) & dev_keys)


def test_sealed_partition_is_json_serializable_with_only_identifiers():
    sealed = build_sealed_partition(partition(_annotated())["POS"])
    json.dumps(sealed)  # must not raise
    assert set(sealed) == {
        "purpose", "constructed_utc", "seed", "selection_unit",
        "n_scaffold_groups", "n_compounds", "connectivity_keys", "disclosure",
    }
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_wur_partition_manifests.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_sealed_partition' from 'muru.io.wur_partition'`

- [ ] **Step 3: Implement the manifest builders in `src/muru/io/wur_partition.py`**

Add this import near the top of the existing `src/muru/io/wur_partition.py`
(alongside the `numpy`/`pandas` imports already there from Task 5):

```python
from datetime import datetime, timezone
```

Append these two functions to the end of the file:

```python
def build_split_manifest(partitioned: dict[str, pd.DataFrame]) -> dict:
    manifest = {"seed": SEED, "created_utc": datetime.now(timezone.utc).isoformat(),
                "polarities": {}}
    for polarity_file, df in partitioned.items():
        entry = {
            "n_trajectories": int(len(df)),
            "n_scaffold_groups": int(df["scaffold_group"].nunique()) if len(df) else 0,
        }
        for side in ("WUR-DEV", "WUR-SEALED"):
            sub = df[df["side"] == side]
            entry[side] = {
                "n_trajectories": int(len(sub)),
                "n_scaffold_groups": int(sub["scaffold_group"].nunique()) if len(sub) else 0,
            }
        if polarity_file == "POS":
            entry["sealed_floor_check"] = check_sealed_floor(
                df[df["side"] == "WUR-SEALED"])
        manifest["polarities"][polarity_file] = entry
    return manifest


def build_sealed_partition(pos_partitioned: pd.DataFrame) -> dict:
    sealed = pos_partitioned[pos_partitioned["side"] == "WUR-SEALED"]
    return {
        "purpose": "SEALED WUR external-validation partition. Do not open "
                   "during Stage 2 development fitting.",
        "constructed_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "selection_unit": "bemis_murcko_scaffold_group",
        "n_scaffold_groups": int(sealed["scaffold_group"].nunique()),
        "n_compounds": int(len(sealed)),
        "connectivity_keys": sorted(sealed["connectivity_key"].tolist()),
        "disclosure": "These WUR compounds are reserved for one look at a "
                      "candidate frozen on development (Stage 3). Not read "
                      "for any mu or descriptor value before that freeze.",
    }
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest tests/test_wur_partition_manifests.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write the thin CLI wrapper**

```python
# scripts/build_wur_partition.py
"""CLI: build artifacts/wur_split_manifest.json and
artifacts/wur_sealed_partition.json from data/external/wur/.

No logic lives here -- everything testable is in
muru.io.wur_partition (see that module's own tests). This script only
wires it to real files.
"""
import json
import sys
from pathlib import Path

from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import build_sealed_partition, build_split_manifest, partition

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    partitioned = partition(load_annotated_trajectories(data_dir))

    split_manifest = build_split_manifest(partitioned)
    (ROOT / "artifacts" / "wur_split_manifest.json").write_text(
        json.dumps(split_manifest, indent=2) + "\n")

    sealed_partition = build_sealed_partition(partitioned["POS"])
    (ROOT / "artifacts" / "wur_sealed_partition.json").write_text(
        json.dumps(sealed_partition, indent=2) + "\n")

    floor = split_manifest["polarities"]["POS"]["sealed_floor_check"]
    print("Wrote wur_split_manifest.json and wur_sealed_partition.json")
    print(f"  POS WUR-SEALED: {floor['n_trajectories']} trajectories, "
          f"{floor['n_scaffold_groups']} scaffold groups")
    if not (floor["passes_trajectory_floor"] and floor["passes_scaffold_group_floor"]):
        print(f"WARNING: sealed part below floor: {floor}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 6: Run the full Stage 0 test suite**
(pytest applies `pythonpath = src` from `pytest.ini` automatically here —
no `PYTHONPATH` prefix needed for `pytest` invocations, only for the direct
`python scripts/...` invocations in Steps 6 and 7 below)

```bash
pytest tests/test_wur_retrieval.py tests/test_wur_raw.py \
       tests/test_wur_identity.py tests/test_wur_qualifying_trajectories.py \
       tests/test_wur_census.py tests/test_wur_partition.py \
       tests/test_wur_partition_manifests.py -v
```

Expected: PASS, all tests (39 total across Tasks 1–6). Also re-run the
existing leakage canary to confirm nothing in `splits.py`/`molecules.py`
regressed:

```bash
pytest tests/test_splits.py -v
```

Expected: PASS, unchanged.

- [ ] **Step 7: Run against the real release and inspect the floor check**

```bash
PYTHONPATH=src python scripts/build_wur_partition.py
cat artifacts/wur_split_manifest.json
```

Expected: exits 0. If the sealed-part floor check fails (fewer than 250
trajectories or 150 scaffold groups on `WUR-SEALED`), stop and report the
actual counts — do not adjust the seed or the 50/50 ratio to force a pass;
that decision is the user's per the approved spec, not something this plan
authorizes changing unilaterally.

- [ ] **Step 8: Commit**

```bash
git add src/muru/io/wur_partition.py scripts/build_wur_partition.py \
        tests/test_wur_partition_manifests.py \
        artifacts/wur_split_manifest.json artifacts/wur_sealed_partition.json
git commit -m "wur: wire Stage 0 partition end-to-end, write split and sealed-partition manifests"
```

- [ ] **Step 9: Open the PR**

```bash
git push -u origin HEAD
gh pr create --base claude/muru-final-holdout-experiment-d75e7d \
  --title "WUR Stage 0: partition and seal" \
  --body "$(cat <<'EOF'
Implements Stage 0 of the WUR real-data program (spec §4): identity-only
census of the frozen WUR Zenodo release and D1-D5 partition into WUR-DEV /
WUR-SEALED, before any mu exists.

- Retrieval manifest verifies the 20 raw files against pinned hashes
- Qualifying-trajectory builder gates on the known defects (stepped
  energy, UVPD, off-ladder energy, unresolved adduct, identity mismatch,
  wrong polarity)
- D1-D5 partition at seed 20260911, sealed part checked against the
  250-trajectory / 150-scaffold-group floor
- No src/muru/discovery, paper_benchmark, or frozen constant touched

Spec: docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md
Out of scope (per spec): Stage 1 bridge gate, Stage 2 MURU run, Stage 3
sealed-part look.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Base the PR on `claude/muru-final-holdout-experiment-d75e7d`, not `main` —
this branch was forked from it specifically to carry the frozen selector
forward for the eventual Stage 2 work.
