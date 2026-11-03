"""Molecular representation: Tier A descriptors, scaffolds, fingerprints, clusters.

Tier A is the frozen, interpretable, physics-facing set. Tier B is the frozen
flexible representation used only by the flexible predictive benchmark. Neither
is expanded after performance is observed (Phase 2 instructions 6 and 7).

Nothing here reads an endpoint. Descriptor computation must be independent of
the response so that the descriptor freeze is genuinely blind.
"""
from __future__ import annotations

import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors, rdFingerprintGenerator, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina

RDLogger.DisableLog("rdApp.*")

# ---------------------------------------------------------------------------
# Tier A: frozen 2026-08-11, before any Phase 2 outcome model was fitted.
#
# Selection rule applied: retain a descriptor only if it is (a) computable for
# every compound, (b) non-degenerate, (c) mechanistically motivated, and (d) not
# rank-redundant with a descriptor already retained. Dropped candidates and the
# reason for each are recorded in DESCRIPTORS.md.
# ---------------------------------------------------------------------------
TIER_A: tuple[str, ...] = (
    "precursor_mz",          # sets E_lab and the mu denominator; the mass carrier
    "total_atom_count",      # vibrational DOF proxy (3N-6), H included
    "rotatable_bonds",       # low-frequency mode density, energy sink capacity
    "ring_count",            # rigidity; rings raise dissociation thresholds
    "aromatic_ring_count",   # stabilizing substructures
    "rdbe",                  # degree of unsaturation, bond-strength proxy
    "tpsa",                  # proton affinity / charge localization proxy
    "heteroatom_fraction",   # charge localization, scale-free (mass-orthogonal)
    "n_N",                   # preferred cleavage sites
    "n_O",
    "n_S",
    "n_halogen",
)

# Descriptors that move with precursor mass. K5's mass ablation removes this
# whole block, not just precursor_mz, because dropping the named mass variable
# alone leaves its proxies behind.
MASS_BLOCK: tuple[str, ...] = ("precursor_mz", "total_atom_count", "rdbe")


def tier_a_descriptors(smiles: str) -> dict[str, float]:
    """Tier A descriptors from a SMILES string. Missing mol -> empty dict."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return {}
    mh = Chem.AddHs(m)
    heavy = max(m.GetNumHeavyAtoms(), 1)
    return {
        "total_atom_count": float(mh.GetNumAtoms()),
        "rotatable_bonds": float(rdMolDescriptors.CalcNumRotatableBonds(m)),
        "ring_count": float(rdMolDescriptors.CalcNumRings(m)),
        "aromatic_ring_count": float(rdMolDescriptors.CalcNumAromaticRings(m)),
        "rdbe": float(rdMolDescriptors.CalcNumRings(m)
                      + sum(b.GetBondTypeAsDouble() - 1 for b in m.GetBonds())),
        "tpsa": float(rdMolDescriptors.CalcTPSA(m)),
        "n_N": float(sum(a.GetSymbol() == "N" for a in m.GetAtoms())),
        "n_O": float(sum(a.GetSymbol() == "O" for a in m.GetAtoms())),
        "n_S": float(sum(a.GetSymbol() == "S" for a in m.GetAtoms())),
        "n_halogen": float(sum(a.GetSymbol() in ("F", "Cl", "Br", "I")
                               for a in m.GetAtoms())),
        "heteroatom_fraction": float(
            sum(a.GetSymbol() not in ("C", "H") for a in m.GetAtoms()) / heavy),
    }


# ---------------------------------------------------------------------------
# Tier B: frozen flexible representation.
# ---------------------------------------------------------------------------
TIER_B_RDKIT_BLOCK: tuple[str, ...] = (
    "MolWt", "MolLogP", "MolMR", "TPSA", "LabuteASA", "BalabanJ", "BertzCT",
    "Chi0v", "Chi1v", "Chi2v", "Chi3v", "Chi4v", "HallKierAlpha",
    "Kappa1", "Kappa2", "Kappa3", "NumHAcceptors", "NumHDonors",
    "NumHeteroatoms", "NumRotatableBonds", "RingCount", "NumAromaticRings",
    "NumSaturatedRings", "NumAliphaticRings", "FractionCSP3", "HeavyAtomCount",
)
MORGAN_RADIUS = 2
MORGAN_NBITS = 2048


def _morgan_gen():
    return rdFingerprintGenerator.GetMorganGenerator(
        radius=MORGAN_RADIUS, fpSize=MORGAN_NBITS)


def morgan_bits(smiles: str) -> np.ndarray:
    """Morgan radius-2 2048-bit fingerprint as a float vector."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return np.full(MORGAN_NBITS, np.nan)
    fp = _morgan_gen().GetFingerprint(m)
    arr = np.zeros(MORGAN_NBITS, dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr.astype(float)


def rdkit_block(smiles: str) -> dict[str, float]:
    """The frozen RDKit descriptor block."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return {}
    fns = dict(Descriptors.descList)
    out = {}
    for name in TIER_B_RDKIT_BLOCK:
        try:
            v = float(fns[name](m))
        except Exception:
            v = float("nan")
        out[f"rdk_{name}"] = v
    return out


# ---------------------------------------------------------------------------
# Scaffolds
# ---------------------------------------------------------------------------
def murcko_scaffold(smiles: str) -> str:
    """Bemis-Murcko scaffold SMILES. Empty string for ringless molecules."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return ""
    sc = MurckoScaffold.GetScaffoldForMol(m)
    return Chem.MolToSmiles(sc) if sc is not None else ""


def scaffold_group(smiles: str, connectivity_key: str) -> str:
    """Scaffold grouping key, with the ringless policy applied.

    Bemis-Murcko is undefined for a molecule with no ring system. Pooling every
    acyclic compound under the empty-string scaffold would assert that they
    share a core, which is chemically false. Each ringless molecule therefore
    becomes its own group, tagged so the audit can count them.

    See MASTER_PLAN_CLARIFICATIONS.md C5.
    """
    s = murcko_scaffold(smiles)
    return s if s else f"__ACYCLIC__{connectivity_key}"


# ---------------------------------------------------------------------------
# Similarity clustering
# ---------------------------------------------------------------------------
def butina_clusters_from_fps(fps: list, similarity_threshold: float = 0.6) -> list[int]:
    """Butina clusters from pre-computed fingerprints at a SIMILARITY threshold.

    RDKit's ``Butina.ClusterData`` takes a **distance** cutoff, not a
    similarity. Passing 0.6 directly would cluster everything with Tanimoto
    distance below 0.6, i.e. similarity above 0.4 -- a far looser grouping than
    intended, which would silently make the cluster-disjoint split easier.
    The conversion is

        distance = 1 - similarity

    so a similarity threshold of 0.6 becomes a distance cutoff of 0.4.
    ``tests/test_splits.py`` pins this with synthetic bit vectors of known
    pairwise similarity.

    Returns a cluster index per input, in input order.
    """
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError(f"similarity must be in [0,1], got {similarity_threshold}")
    dist_cutoff = 1.0 - similarity_threshold

    n = len(fps)
    # Condensed lower-triangle distance matrix, as ClusterData expects.
    dists: list[float] = []
    for i in range(1, n):
        if fps[i] is None:
            dists.extend([1.0] * i)
            continue
        row = []
        for j in range(i):
            if fps[j] is None:
                row.append(1.0)
            else:
                row.append(1.0 - DataStructs.TanimotoSimilarity(fps[i], fps[j]))
        dists.extend(row)

    clusters = Butina.ClusterData(dists, n, dist_cutoff,
                                 isDistData=True, reordering=True)
    labels = [-1] * n
    for ci, members in enumerate(clusters):
        for idx in members:
            labels[idx] = ci
    return labels


def butina_clusters(smiles_list: list[str],
                    similarity_threshold: float = 0.6) -> list[int]:
    """Butina clusters for SMILES at a Tanimoto SIMILARITY threshold."""
    gen = _morgan_gen()
    fps = []
    for s in smiles_list:
        m = Chem.MolFromSmiles(s)
        fps.append(gen.GetFingerprint(m) if m is not None else None)
    return butina_clusters_from_fps(fps, similarity_threshold)
