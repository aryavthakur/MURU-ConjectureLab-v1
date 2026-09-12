"""Tier A2: twelve additional interpretable descriptors, fixed a priori.

Chosen from the failure analysis's pointer (n_O and rotatable bonds are the
strongest non-size signals, so labile-bond and heteroatom-environment
features are the natural next representation) and from the collision-energy
literature (degrees of freedom, H-bonding, charge localisation). Fixed
before any Stage 2B candidate using them was fitted. With Tier A this is
24 features, the protocol's cap.
"""
from __future__ import annotations

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import Crippen, Descriptors, Fragments, Lipinski, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

TIER_A2: tuple[str, ...] = (
    "n_hbd",              # H-bond donors: mobile protons, charge-directed cleavage
    "n_hba",              # H-bond acceptors: protonation sites
    "frac_csp3",          # saturation: low-frequency modes, energy sink
    "mol_logp",           # Crippen logP: polarity proxy orthogonal to TPSA
    "n_amide",            # amide bonds: dominant low-energy cleavage in peptides / pesticides
    "n_ester_carboxyl",   # ester + carboxylic acid: neutral loss channels
    "n_ether",            # ether oxygens: charge-remote cleavage
    "n_hydroxyl",         # aliphatic + aromatic OH: water loss
    "n_amine",            # primary + secondary + tertiary amines: preferred protonation
    "n_aromatic_atoms",   # aromatic atom count: delocalised, resists fragmentation
    "n_halogen_aromatic", # halogens on aromatic carbon: stable substituents
    "fraction_rotatable", # rotatable bonds per heavy atom: flexibility, scale-free
)

SCALE_A2 = {"n_hbd": 2.0, "n_hba": 4.0, "frac_csp3": 0.4, "mol_logp": 3.0, "n_amide": 1.0,
            "n_ester_carboxyl": 1.0, "n_ether": 1.0, "n_hydroxyl": 1.0, "n_amine": 1.0,
            "n_aromatic_atoms": 6.0, "n_halogen_aromatic": 1.0, "fraction_rotatable": 0.2}


def tier_a2_descriptors(smiles: str) -> dict[str, float]:
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return {}
    heavy = max(m.GetNumHeavyAtoms(), 1)
    arom_hal = sum(1 for a in m.GetAtoms() if a.GetSymbol() in ("F", "Cl", "Br", "I")
                   and any(n.GetIsAromatic() for n in a.GetNeighbors()))
    d = {
        "n_hbd": float(Lipinski.NumHDonors(m)),
        "n_hba": float(Lipinski.NumHAcceptors(m)),
        "frac_csp3": float(rdMolDescriptors.CalcFractionCSP3(m)),
        "mol_logp": float(Crippen.MolLogP(m)),
        "n_amide": float(Fragments.fr_amide(m)),
        "n_ester_carboxyl": float(Fragments.fr_ester(m) + Fragments.fr_COO(m)),
        "n_ether": float(Fragments.fr_ether(m)),
        "n_hydroxyl": float(Fragments.fr_Al_OH(m) + Fragments.fr_Ar_OH(m)),
        "n_amine": float(Fragments.fr_NH2(m) + Fragments.fr_NH1(m) + Fragments.fr_NH0(m)),
        "n_aromatic_atoms": float(sum(a.GetIsAromatic() for a in m.GetAtoms())),
        "n_halogen_aromatic": float(arom_hal),
        "fraction_rotatable": float(rdMolDescriptors.CalcNumRotatableBonds(m) / heavy),
    }
    if not all(np.isfinite(v) for v in d.values()):
        return {}
    return d
