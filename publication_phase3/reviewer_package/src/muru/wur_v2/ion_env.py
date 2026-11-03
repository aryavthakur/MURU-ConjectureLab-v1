"""ION_ENV: a small, audited ion-environment / local-chemistry block (protocol section 9, Experiment 7).

Fixed from protonation and charge-directed fragmentation chemistry before any
fit. Counts distinguish basic-site types that Tier A lumps into n_N (aliphatic
amine, aniline, amide, pyridine-type and pyrrole-type aromatic N,
amidine/guanidine), carbonyl classes that Tier A lumps into n_O (ester, acid,
ketone/aldehyde; amide is counted through its N), sulfonyl/phosphoryl groups,
permanent cations, the proximity of the most basic site to the nearest labile
bond, and the share of heavy atoms in the largest aromatic system (a
charge-retaining substructure). Pruning rules are applied on structures only
(`prune`), never on outcomes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

SMARTS = {
    "n_aliph_amine": "[NX3;!a;!$(N-a);!$(N-[#6,#16,#15]=[#8,#16,#7]);!$(N-[#7,#8]);!$(N-C#N);!$(N-[SX4](=O)=O)]",
    "n_aniline_n": "[NX3;!a;$(N-a);!$(N-[#6,#16,#15]=[#8,#16,#7]);!$(N-[#7,#8]);!$(N-[SX4](=O)=O)]",
    "n_amide_n": "[NX3;!a;$(N-[#6]=[#8,#16])]",
    "n_pyridine_like": "[nX2]",
    "n_pyrrole_like": "[nX3]",
    "n_amidine_guanidine": "[CX3;!a](=[NX2;!a])[NX3;!a]",
    "n_ester": "[#6][CX3](=O)[OX2][#6]",
    "n_carboxylic_acid": "[CX3](=O)[OX2H1]",
    "n_ketone_aldehyde": "[CX3;$([CX3](=O)([#6])[#6]),$([CX3H1](=O)[#6])]=O",
    "n_sulfonyl_phosphoryl": "[$([SX4](=O)=O),$([PX4]=O)]",
    "n_permanent_cation": "[N+,P+,S+;!$([N+]-[O-]);!$([N+]=O);!$([N+]~[O-])]",
}
# basic sites in decreasing gas-phase basicity (priority), and labile bond atoms
BASIC_PRIORITY = ("n_amidine_guanidine_n", "n_aliph_amine", "n_pyridine_like", "n_aniline_n")
BASIC_SMARTS = {"n_amidine_guanidine_n": "[NX2,NX3;!a;$(N~[CX3](~[NX2,NX3])~[NX2,NX3]),$([NX2;!a]=[CX3;!a]-[NX3;!a])]",
                "n_aliph_amine": SMARTS["n_aliph_amine"], "n_pyridine_like": SMARTS["n_pyridine_like"],
                "n_aniline_n": SMARTS["n_aniline_n"]}
LABILE_SMARTS = ("[OX2;$(O([#6])[CX3]=O)]",           # ester / lactone single-bonded O
                 "[NX3;$(N-[CX3]=O)]",                 # amide / carbamate / urea N
                 "[OX2;!a;$(O([CX4])[CX4,CX3;!$(C=O)])]",  # aliphatic ether / glycosidic O
                 "[NX3;$(N-[SX4](=O)=O)]",             # sulfonamide N
                 "[OX2;$(O([#6])-[PX4]=O)]")           # phosphate / phosphonate ester O
# which atom of a match is counted, so one functional group counts once however many
# ways the pattern can map onto it (a guanidine carbon matches once per N assignment)
ANCHOR = {"n_amidine_guanidine": 0, "n_ester": 1, "n_carboxylic_acid": 0, "n_ketone_aldehyde": 0,
          "n_sulfonyl_phosphoryl": 0}
FEATURES = tuple(SMARTS) + ("prox_basic_labile", "aromatic_system_fraction")
_PAT = {k: Chem.MolFromSmarts(v) for k, v in SMARTS.items()}
_BASIC = {k: Chem.MolFromSmarts(v) for k, v in BASIC_SMARTS.items()}
_LABILE = [Chem.MolFromSmarts(s) for s in LABILE_SMARTS]


def _largest_aromatic_system(m) -> int:
    ri = m.GetRingInfo()
    rings = [set(r) for r in ri.AtomRings() if all(m.GetAtomWithIdx(i).GetIsAromatic() for i in r)]
    best, seen = 0, [False] * len(rings)
    for i in range(len(rings)):
        if seen[i]:
            continue
        comp, stack = set(rings[i]), [i]
        seen[i] = True
        while stack:
            j = stack.pop()
            for k in range(len(rings)):
                if not seen[k] and len(rings[j] & rings[k]) >= 2:
                    seen[k] = True
                    comp |= rings[k]
                    stack.append(k)
        best = max(best, len(comp))
    return best


def describe(smiles: str) -> dict[str, float]:
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return {}
    out = {k: float(len({t[ANCHOR.get(k, 0)] for t in m.GetSubstructMatches(p)})) for k, p in _PAT.items()}
    heavy = max(m.GetNumHeavyAtoms(), 1)
    basic_atoms = []
    for name in BASIC_PRIORITY:
        hits = [t[0] for t in m.GetSubstructMatches(_BASIC[name])]
        if hits:
            basic_atoms = hits
            break
    labile = sorted({t[0] for p in _LABILE for t in m.GetSubstructMatches(p)})
    if basic_atoms and labile:
        D = Chem.GetDistanceMatrix(m)
        dist = min(D[b, l] for b in basic_atoms for l in labile if b != l) if any(b != l for b in basic_atoms for l in labile) else 0.0
        out["prox_basic_labile"] = float(1.0 / (1.0 + dist))
    else:
        out["prox_basic_labile"] = 0.0
    out["aromatic_system_fraction"] = float(_largest_aromatic_system(m) / heavy)
    return out


def table(smiles: pd.Series) -> pd.DataFrame:
    return pd.DataFrame([describe(s) for s in smiles], index=smiles.index)[list(FEATURES)]


def prune(block: pd.DataFrame, tier_a: pd.DataFrame, max_constant: float = 0.97, max_r2: float = 0.90) -> tuple[list[str], dict]:
    """Structure-only pruning: near-constant, exact duplicate, or R^2 > max_r2 on Tier A plus the rest of the block."""
    report, keep = {}, []
    for c in block.columns:
        top = block[c].value_counts(normalize=True).iloc[0]
        if top > max_constant:
            report[c] = f"dropped: modal value share {top:.3f} > {max_constant}"
            continue
        dup = [k for k in keep if np.allclose(block[c].to_numpy(), block[k].to_numpy())]
        dup += [k for k in tier_a.columns if np.allclose(block[c].to_numpy(), tier_a[k].to_numpy())]
        if dup:
            report[c] = f"dropped: exact duplicate of {dup}"
            continue
        keep.append(c)
    changed = True
    while changed:
        changed = False
        for c in list(keep):
            others = [k for k in keep if k != c]
            X = np.column_stack([np.ones(len(block)), tier_a.to_numpy(float), block[others].to_numpy(float)])
            y = block[c].to_numpy(float)
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            r2 = 1 - ((y - X @ beta) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-12)
            report.setdefault(c, "")
            if r2 > max_r2:
                keep.remove(c)
                report[c] = f"dropped: in-sample R2 {r2:.3f} on Tier A + block"
                changed = True
                break
            report[c] = f"kept: modal share {block[c].value_counts(normalize=True).iloc[0]:.3f}, R2 on Tier A + block {r2:.3f}"
    return keep, report
