"""ION_ENV SMARTS audit pinned on reference molecules (chemistry checked by hand)."""
import pytest
from muru.wur_v2.ion_env import describe

CASES = {
    "CCN(CC)CC(=O)Nc1c(C)cccc1C": {"n_aliph_amine": 1, "n_amide_n": 1, "prox_basic_labile": 0.25},        # lidocaine
    "CN(C)C(=N)NC(=N)N": {"n_amidine_guanidine": 2, "n_aliph_amine": 0},                                   # metformin
    "CN1C2CCC1CC(C2)OC(=O)C(CO)c1ccccc1": {"n_aliph_amine": 1, "n_ester": 1, "prox_basic_labile": 0.2},   # atropine
    "Cc1cc(NS(=O)(=O)c2ccc(N)cc2)no1": {"n_aniline_n": 1, "n_sulfonyl_phosphoryl": 1, "n_pyridine_like": 1},
    "NC(=O)N1c2ccccc2C=Cc2ccccc21": {"n_amide_n": 2, "n_aliph_amine": 0},                                  # carbamazepine
    "C[N+](C)(C)CCO": {"n_permanent_cation": 1},                                                           # choline
    "O=[N+]([O-])c1ccccc1": {"n_permanent_cation": 0, "aromatic_system_fraction": pytest.approx(6 / 9)},   # nitro is not a cation
    "CC(C)Cc1ccc(C(C)C(=O)O)cc1": {"n_carboxylic_acid": 1, "n_ester": 0},                                  # ibuprofen
    "CC(=O)c1ccccc1": {"n_ketone_aldehyde": 1},
    "c1ccc2[nH]ccc2c1": {"n_pyrrole_like": 1, "n_pyridine_like": 0, "aromatic_system_fraction": 1.0},      # indole, fused system
    "CN1CCC[C@H]1c1cccnc1": {"n_aliph_amine": 1, "n_pyridine_like": 1, "prox_basic_labile": 0.0},        # nicotine, no labile bond
}


@pytest.mark.parametrize("smiles,expected", list(CASES.items()))
def test_reference_molecules(smiles, expected):
    d = describe(smiles)
    for k, v in expected.items():
        assert d[k] == v, (smiles, k, d[k], v)
