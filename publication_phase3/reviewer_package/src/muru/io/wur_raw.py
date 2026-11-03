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
    if not path.exists():
        raise FileNotFoundError(f"WUR release file missing: {path}")
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
