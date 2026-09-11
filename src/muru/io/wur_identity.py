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
