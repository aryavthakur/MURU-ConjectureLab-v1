"""v2 identity normalization and structural grouping (protocol section 2).

Identity unit: the connectivity key (InChIKey first block) of the parent
structure. The first block encodes the constitution without stereochemistry
or isotopes, so stereoisomers and E/Z isomers share one identity and are
never split across folds. Parent: the largest organic fragment, neutralized
where a neutral form exists (a permanent cation such as a quaternary
ammonium keeps its charge). No current exposed SMILES carries a salt, so
the parent step is a no-op on the exposed data and exists for external
sources.

Primary structural group: the Bemis-Murcko scaffold of the stereo-stripped
parent (v1 kept stereochemistry in the scaffold string, so two steroid
scaffolds straddled folds; review finding LK-1). An acyclic parent is its
own group. Strict sensitivity grouping: connected components of the
Morgan-count Tanimoto graph at similarity >= 0.55 over the union of scaffold
groups (single linkage), which puts close acyclic homologues and near-
identical scaffolds together.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import inchi, rdFingerprintGenerator
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")
STRICT_SIMILARITY = 0.55


def parent_mol(smiles: str):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    m = rdMolStandardize.LargestFragmentChooser(preferOrganic=True).choose(m)
    try:
        m = rdMolStandardize.Uncharger().uncharge(m)
    except Exception:
        pass
    return m


def parent_connectivity_key(smiles: str) -> str | None:
    m = parent_mol(smiles)
    if m is None:
        return None
    k = inchi.MolToInchiKey(m)
    return k.split("-")[0] if k else None


def stereo_free_smiles(smiles: str) -> str | None:
    m = parent_mol(smiles)
    if m is None:
        return None
    Chem.RemoveStereochemistry(m)
    return Chem.MolToSmiles(m)


def scaffold_group_v2(smiles: str, connectivity_key: str) -> str:
    m = parent_mol(smiles)
    if m is None:
        return f"__UNPARSED__{connectivity_key}"
    Chem.RemoveStereochemistry(m)
    sc = MurckoScaffold.GetScaffoldForMol(m)
    s = Chem.MolToSmiles(sc) if sc is not None else ""
    return s if s else f"__ACYCLIC__{connectivity_key}"


def strict_clusters(smiles: pd.Series, scaffold: pd.Series, threshold: float = STRICT_SIMILARITY) -> pd.Series:
    """Single-linkage components over Morgan-count Tanimoto >= threshold, merged with scaffold groups."""
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = [gen.GetCountFingerprint(Chem.MolFromSmiles(s)) for s in smiles]
    n = len(fps)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for i in range(n):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:])
        for j, s in enumerate(sims):
            if s >= threshold:
                union(i, i + 1 + j)
    first_by_scaffold: dict[str, int] = {}
    for i, g in enumerate(scaffold):
        if g in first_by_scaffold:
            union(i, first_by_scaffold[g])
        else:
            first_by_scaffold[g] = i
    roots = [find(i) for i in range(n)]
    labels = pd.factorize(pd.Series(roots))[0]
    return pd.Series([f"SC{l:04d}" for l in labels], index=smiles.index)
