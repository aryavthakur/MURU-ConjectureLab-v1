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
