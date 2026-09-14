"""Run inside the ms-pred image: read a PredSpecDB HDF5 exactly as written by the native predictor and dump every
spectrum's stored arrays (float32 masses and intensities as written, fragment masks) to JSON. No transform."""
import json
import sys

import numpy as np
from rdkit import Chem

from ms_pred import common

db = common.PredSpecDB(sys.argv[1], mode="r")
out = []
for name in sorted(db.get_all_names()):
    entries, has_remark = db.read_from_name(name)
    flat = []
    if has_remark:
        for r, d in entries.items():
            flat += [(r, c, s) for c, s in d.items()]
    else:
        flat = [(None, c, s) for c, s in entries.items()]
    for remark, ckey, spec in flat:
        smi = spec.root_canonical_smiles
        natoms = Chem.MolFromSmiles(smi).GetNumAtoms() if smi else None
        frags = np.asarray(spec.frags, dtype=bool) if spec.frags is not None else None
        is_root = ([bool(f[:natoms].all()) for f in frags] if frags is not None and natoms else None)
        out.append({
            "name": name, "remark": remark, "collision_key": ckey, "stored_collision_energy": spec.collision_energy,
            "root_canonical_smiles": smi, "adduct": spec.adduct, "natoms": natoms,
            "masses_float32": [float(x) for x in np.asarray(spec.masses, dtype=np.float32)],
            "intens_float32": [float(x) for x in np.asarray(spec.intens, dtype=np.float32)],
            "is_root_fragment": is_root,
            "frag_popcount": [int(f[:natoms].sum()) for f in frags] if frags is not None and natoms else None,
        })
json.dump(out, open(sys.argv[2], "w"))
print(f"dumped {len(out)} spectra")
