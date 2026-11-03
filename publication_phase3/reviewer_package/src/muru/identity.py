"""Molecular identity: grouping key, RDKit cross-checks, mismatch accounting.

Grouping rule (master plan section 10.1, field guide "Scientific grouping key"):
a trajectory is one compound in one ion mode. The key is the InChIKey FIRST
BLOCK (the 14-character connectivity layer), because MS/MS cannot distinguish
stereoisomers -- grouping on the full InChIKey would split a trajectory whose
records differ only in a stereo descriptor.

Nothing here repairs a structure. When CH$SMILES and CH$LINK: INCHIKEY
disagree, both are kept, the record is flagged, and the disagreement is counted
in the mismatch table. Silent repair is the failure mode this module exists to
prevent.
"""

from __future__ import annotations

from dataclasses import dataclass

from rdkit import Chem, RDLogger
from rdkit.Chem.inchi import MolToInchiKey

RDLogger.DisableLog("rdApp.*")  # RDKit warnings are captured, not printed


@dataclass(frozen=True)
class IdentityCheck:
    """Result of cross-checking CH$SMILES against CH$LINK: INCHIKEY."""

    accession: str
    smiles_raw: str | None
    inchikey_recorded: str | None
    inchikey_from_smiles: str | None
    status: str  # MATCH | MATCH_CONNECTIVITY_ONLY | MISMATCH | SMILES_UNPARSEABLE
                 # | SMILES_ABSENT | INCHIKEY_ABSENT | INCHIKEY_GENERATION_FAILED
    note: str = ""
    n_fragments: int = 0
    has_stereo: bool = False

    @property
    def usable(self) -> bool:
        """Usable for grouping. Connectivity-only agreement IS usable: MS/MS
        does not resolve stereochemistry, and the grouping key is the
        connectivity block anyway."""
        return self.status in ("MATCH", "MATCH_CONNECTIVITY_ONLY")


def first_block(inchikey: str | None) -> str | None:
    """The 14-character connectivity layer of an InChIKey."""
    if not inchikey:
        return None
    part = inchikey.strip().split("-")[0]
    return part if len(part) == 14 else None


def check_identity(accession: str, smiles: str | None,
                   inchikey: str | None) -> IdentityCheck:
    """Regenerate an InChIKey from SMILES and compare. Never repairs."""
    if smiles is None:
        return IdentityCheck(accession, smiles, inchikey, None, "SMILES_ABSENT",
                             "CH$SMILES missing")
    if inchikey is None:
        return IdentityCheck(accession, smiles, inchikey, None, "INCHIKEY_ABSENT",
                             "CH$LINK: INCHIKEY missing")

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return IdentityCheck(accession, smiles, inchikey, None, "SMILES_UNPARSEABLE",
                             "RDKit could not sanitize CH$SMILES")

    n_frag = len(Chem.GetMolFrags(mol))
    stereo = "@" in smiles or "/" in smiles or "\\" in smiles

    try:
        generated = MolToInchiKey(mol)
    except Exception as exc:  # noqa: BLE001 - RDKit raises assorted types
        return IdentityCheck(accession, smiles, inchikey, None,
                             "INCHIKEY_GENERATION_FAILED", str(exc)[:200],
                             n_frag, stereo)
    if not generated:
        return IdentityCheck(accession, smiles, inchikey, None,
                             "INCHIKEY_GENERATION_FAILED",
                             "RDKit returned an empty InChIKey", n_frag, stereo)

    if generated == inchikey.strip():
        return IdentityCheck(accession, smiles, inchikey, generated, "MATCH", "",
                             n_frag, stereo)
    if first_block(generated) == first_block(inchikey):
        return IdentityCheck(
            accession, smiles, inchikey, generated, "MATCH_CONNECTIVITY_ONLY",
            "connectivity agrees; stereo/protonation layer differs",
            n_frag, stereo,
        )
    return IdentityCheck(accession, smiles, inchikey, generated, "MISMATCH",
                         "connectivity layer disagrees", n_frag, stereo)


def group_key(inchikey: str | None, ion_mode: str | None) -> str | None:
    """Trajectory key: connectivity block + ion mode. None if unformable.

    Positive and negative mode are NEVER pooled (master plan section 10.3).
    """
    fb = first_block(inchikey)
    if fb is None or not ion_mode:
        return None
    return f"{fb}|{ion_mode.strip().upper()}"
