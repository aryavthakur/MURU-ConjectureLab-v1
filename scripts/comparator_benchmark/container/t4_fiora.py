"""T4 inside the FIORA image: structure / parser / featurization acceptance only. No model forward pass.

Loads the frozen FIORA-OS v0.1.0 inference script (minimally patched v0.1.2 release) as a module and calls its own
build_metabolites (SMILES -> Metabolite, structure graph, graph attributes, setup covariate encoding, single-break
fragmentation tree) one molecule at a time, with the checkpoint's own params JSON. The model is never instantiated.
"""
import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

import pandas as pd

code_root, csv_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, code_root)
spec = spec_from_loader("fiora_predict", SourceFileLoader("fiora_predict", f"{code_root}/scripts/fiora-predict"))
FP = module_from_spec(spec)
spec.loader.exec_module(FP)
params = json.load(open(f"{code_root}/models/fiora_OS_v0.1.0_params.json"))

df = pd.read_csv(csv_path)
results = []
for i in range(len(df)):
    row = df.iloc[[i]].copy()
    rec = {"Name": row.Name.iloc[0], "ok": False}
    try:
        with redirect_stdout(io.StringIO()):
            built, invalid = FP.build_metabolites(row, params)
        if len(invalid) or len(built) != 1:
            raise ValueError("SMILES rejected by build_metabolites")
        m = built["Metabolite"].iloc[0]
        n_edges = len(m.edges_as_tuples) if hasattr(m, "edges_as_tuples") else None
        assert m.fragmentation_tree is not None, "no fragmentation tree"
        rec.update(ok=True, n_edges=n_edges, precursor_mode=m.metadata.get("precursor_mode"),
                   n_fragments_edge_map=len(m.fragmentation_tree.edge_map))
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-1500:]
    results.append(rec)
json.dump(results, open(out_path, "w"))
print("fiora accepted", sum(r["ok"] for r in results), "of", len(results))
