"""Identity-only gates for WUR spectra, per the known defects recorded in
spec §3.2 -- gated here rather than discovered downstream."""
import pandas as pd
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


ACCEPTED_COLUMNS = [
    "source_library", "source_polarity_file", "spectrum_id", "compound_id",
    "connectivity_key", "smiles", "adduct", "energy", "precursor_mass",
    "polarity",
]


def accepted_rows(raw: pd.DataFrame, polarity: str) -> pd.DataFrame:
    """One row per spectrum that passes every Stage 0 identity gate.

    This is the single definition of "a spectrum MURU accepted from the WUR
    release". `build_qualifying_trajectories` groups it; Stage 1's mu builder
    reads peaks for exactly these rows. Neither re-implements the gates, so
    they cannot drift apart and a rejected UVPD, off-ladder, wrong-polarity
    or wrong-adduct spectrum cannot leak back in downstream.

    Gates, in order: HCD only; the compound's own Polarity field (not the
    source file name); a collision energy that parses and snaps to a ladder
    rung; a deposited SMILES that verifies against its own InChIKey; and
    exactly one adduct explaining the precursor mass.
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

    df["identity_ok"] = pd.array(
        [verify_identity(s, k) for s, k in zip(df["smiles"], df["inchikey"])],
        dtype=bool,
    )
    df = df[df["identity_ok"]].copy()
    df["connectivity_key"] = df["inchikey"].map(connectivity_key)

    df["adduct"] = [
        infer_adduct(s, m, polarity)
        for s, m in zip(df["smiles"], df["precursor_mass"])
    ]
    df = df[df["adduct"].notna()].copy()
    return df.reindex(columns=ACCEPTED_COLUMNS).reset_index(drop=True)


def build_qualifying_trajectories(raw: pd.DataFrame, polarity: str) -> pd.DataFrame:
    """Reduce accepted spectra to one row per qualifying trajectory.

    A trajectory qualifies if its accepted spectra cover the full six-point
    ladder. Duplicate and cross-library deposits of the same connectivity
    key are merged into one row here, not dropped -- this is where defect
    "62/61 duplicate combos" (spec §3.2) is resolved.

    Returns: connectivity_key, smiles (lexicographically first deposited
    SMILES for that key -- design rule D1), adduct, polarity, n_source_rows,
    source_libraries (sorted tuple).
    """
    df = accepted_rows(raw, polarity)

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
