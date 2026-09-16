"""MURU compound key and scaffold group, reproduced standalone for dataset screening (CE interface adjudication, P5).

Source of truth (read, not imported, so this file can be copied elsewhere):
  src/muru/wur_v2/identity.py  (sha256 2ebe0de24e5ea5f781eea94984b238be8977161a836a56b5add4e277a0ca9cbd, the
  identity_py_sha256 recorded in artifacts/wur_v2_confirmation_v2/exposure_registry/registry_manifest.json)
    parent_mol               lines 33-42
    parent_connectivity_key  lines 45-50
    scaffold_group_v2        lines 61-68
  and the census/study-1/study-2 wrapper `chem()` in src/muru/wur_v2/msnlib_design.py lines 66-87 (same rule as
  scripts/wur_v2_confirmation_v2/01_build_exposure_registry.py lines 131-152), which additionally requires that
  RDKit can build an InChIKey from the RAW (un-normalized) SMILES before it accepts the parent key.

Definitions:
  compound key    = first block (14 chars) of the InChIKey of the PARENT molecule, where parent = RDKit
                    LargestFragmentChooser(preferOrganic=True), then Uncharger (exceptions ignored). Stereo and
                    isotope layers are dropped by construction of the first block.
  scaffold group  = canonical SMILES of the Bemis-Murcko scaffold (MurckoScaffold.GetScaffoldForMol) of the parent
                    after Chem.RemoveStereochemistry; an acyclic parent gives "__ACYCLIC__<key>"; an unparseable
                    SMILES gives "__UNPARSED__<key>".
  Not the generic (atom/bond-type-erased) framework, and formal charges are kept in the scaffold string (a permanent
  cation keeps [N+] in its scaffold). The stricter "charge-neutral scaffold" of census step 10b / MultiMS2 rule R7
  (src/muru/wur_v2/external_multims2.py:50-65) is a separate screening rule, not the scaffold group.

Output is RDKit-version dependent (InChI and canonical SMILES). The frozen MURU artifacts used rdkit 2026.03.5.

Usage:
  python3 scaffold_key.py --self-test            # compare against muru.wur_v2.identity and frozen population files
  python3 scaffold_key.py "SMILES" ["SMILES" ...] # print key and scaffold group (tab separated)
"""
from __future__ import annotations

import sys
from pathlib import Path

from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem import inchi
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")
FROZEN_RDKIT = "2026.03.5"


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


def scaffold_group(smiles: str, key: str) -> str:
    m = parent_mol(smiles)
    if m is None:
        return f"__UNPARSED__{key}"
    Chem.RemoveStereochemistry(m)
    sc = MurckoScaffold.GetScaffoldForMol(m)
    s = Chem.MolToSmiles(sc) if sc is not None else ""
    return s if s else f"__ACYCLIC__{key}"


def key_and_group(smiles) -> tuple[str | None, str | None]:
    """The census/registry wrapper: key only if the raw SMILES parses AND yields an InChIKey AND a parent key exists."""
    if not isinstance(smiles, str) or not smiles:
        return None, None
    m0 = Chem.MolFromSmiles(smiles)
    if m0 is None:
        return None, None
    rk = inchi.MolToInchiKey(m0)
    pk = parent_connectivity_key(smiles)
    if not rk or pk is None:
        return None, None
    return pk, scaffold_group(smiles, pk)


def first_block(inchikey) -> str | None:
    """src/muru/identity.py:47-52: first block of a RECORDED InChIKey (no structure normalization)."""
    if not isinstance(inchikey, str) or not inchikey:
        return None
    part = inchikey.strip().split("-")[0]
    return part if len(part) == 14 else None


def _self_test() -> int:
    import pandas as pd
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from muru.wur_v2 import identity as ID  # noqa: E402

    print(f"rdkit {rdBase.rdkitVersion} (frozen artifacts: {FROZEN_RDKIT})")
    fails = 0
    cp = pd.read_csv(root / "artifacts/comparator_benchmark/population/common_population.csv",
                     usecols=["key", "scaffold_group", "model_smiles"])
    vp = pd.read_csv(root / "artifacts/wur_v2_confirmation_v2/freeze/validation_population.csv",
                     usecols=["key", "scaffold_group", "smiles"]).rename(columns={"smiles": "model_smiles"})
    for label, df in (("comparator common_population.csv (model_smiles)", cp),
                      ("study-2 validation_population.csv (smiles)", vp)):
        n = len(df)
        k_ok = g_ok = mod_ok = 0
        bad = []
        for r in df.itertuples(index=False):
            k, g = key_and_group(r.model_smiles)
            k_ok += k == r.key
            g_ok += g == r.scaffold_group
            mod_ok += (ID.parent_connectivity_key(r.model_smiles) == k and ID.scaffold_group_v2(r.model_smiles, k) == g)
            if (k != r.key or g != r.scaffold_group) and len(bad) < 5:
                bad.append((r.key, k, r.scaffold_group, g))
        print(f"{label}: n={n} key_match={k_ok} group_match={g_ok} identical_to_muru_module={mod_ok}")
        for b in bad:
            print("  mismatch", b)
        fails += (n - k_ok) + (n - g_ok) + (n - mod_ok)
    for smi in ("CC(=O)Oc1ccccc1C(=O)O", "CCCCCCCC(=O)O", "C[N+](C)(C)CC(=O)[O-]", "Cl.CN1CCC[C@H]1c1cccnc1"):
        print("example", smi, *key_and_group(smi))
    print("SELF-TEST", "PASS" if fails == 0 else f"FAIL ({fails})")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        raise SystemExit(_self_test())
    for s in sys.argv[1:]:
        print(s, *key_and_group(s), sep="\t")
