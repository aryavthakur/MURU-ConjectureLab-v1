"""Structure-only molecular representations for v2 (protocol section 9).

Every representation is a deterministic function of the representative
SMILES and is computed over all compounds at once. None reads mu, a scale
label or any outcome, so computing it globally leaks nothing; frequency
filtering and standardization, where a model uses them, happen inside the
training set.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import MACCSkeys, rdFingerprintGenerator

from muru.wur_v2.models import minmax_kernel, tier_a_scaled

RDLogger.DisableLog("rdApp.*")
MORGAN_RADIUS = 2
FP_SIZE = 2048


def morgan_counts(smiles: pd.Series) -> pd.DataFrame:
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=MORGAN_RADIUS, fpSize=FP_SIZE, includeChirality=False)
    rows = [gen.GetCountFingerprintAsNumPy(Chem.MolFromSmiles(s)).astype(float) for s in smiles]
    return pd.DataFrame(np.vstack(rows), index=smiles.index, columns=[f"mg{i}" for i in range(FP_SIZE)])


def atompair_counts(smiles: pd.Series) -> pd.DataFrame:
    gen = rdFingerprintGenerator.GetAtomPairGenerator(fpSize=FP_SIZE, includeChirality=False)
    rows = [gen.GetCountFingerprintAsNumPy(Chem.MolFromSmiles(s)).astype(float) for s in smiles]
    return pd.DataFrame(np.vstack(rows), index=smiles.index, columns=[f"ap{i}" for i in range(FP_SIZE)])


def maccs_bits(smiles: pd.Series) -> pd.DataFrame:
    rows = []
    for s in smiles:
        fp = MACCSkeys.GenMACCSKeys(Chem.MolFromSmiles(s))
        rows.append(np.array([int(fp.GetBit(i)) for i in range(fp.GetNumBits())], float))
    return pd.DataFrame(np.vstack(rows), index=smiles.index, columns=[f"mk{i}" for i in range(len(rows[0]))])


def build_all(cov: pd.DataFrame) -> tuple[dict, dict]:
    """Feature blocks and precomputed MinMax kernels, indexed by group_key."""
    smi = cov["smiles"]
    mc = morgan_counts(smi)
    ac = atompair_counts(smi)
    feats = {"TIER_A": tier_a_scaled(cov), "MORGAN": np.log1p(mc), "MORGAN_COUNTS": mc,
             "ATOMPAIR": np.log1p(ac), "ATOMPAIR_COUNTS": ac, "MACCS": maccs_bits(smi)}
    kernels = {"MINMAX_MORGAN": (cov.index, minmax_kernel(mc.to_numpy(), mc.to_numpy())),
               "MINMAX_ATOMPAIR": (cov.index, minmax_kernel(ac.to_numpy(), ac.to_numpy()))}
    return feats, kernels
