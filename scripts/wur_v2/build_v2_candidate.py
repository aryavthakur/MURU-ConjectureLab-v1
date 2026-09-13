"""Fit and serialize the v2 candidate and comparators on all 1,325 compounds; verify reload parity."""
import json, os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "4"
from pathlib import Path
import numpy as np
from muru.wur_v2 import runner as RU, candidate as CA, engine as EN, models as MO, ledger as LG
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "artifacts/wur_v2/candidate"; OUT.mkdir(parents=True, exist_ok=True)
d = RU.load_data()
models = CA.fit_all(d)
for name, m in models.items():
    (OUT / f"{name}.json").write_text(CA.canonical_json(m) + "\n")
# reload parity against in-memory engine predictions on training compounds
keys = list(d.cov.index)
ts = EN.trainset(d, keys, "scaffold_group", 0)
jm = models[CA.CANDIDATE_ID]
jr = MO.JointRidge("MORGAN", "_")
m, stats, bw = jr.fit(ts, (jm["cfg"]["alpha"], jm["cfg"]["block_weight"]))
lg_engine = jr.predict((m, stats, bw), ts, ts.keys)
re = json.loads((OUT / f"{CA.CANDIDATE_ID}.json").read_text())
lg_json = CA.predict_log_g(re, d.cov.loc[ts.keys, "smiles"], d.cov.loc[ts.keys, "precursor_mz"])
parity = float(np.max(np.abs(lg_engine - lg_json)))
manifest = {name: {"sha256": CA.sha256_of(json.loads((OUT / f"{name}.json").read_text())), "cfg": m_.get("cfg"), "n_training": m_["n_training"]} for name, m_ in models.items()}
manifest["reload_parity_max_abs_logg"] = parity
(OUT / "candidate_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
print(json.dumps(manifest, indent=1))
assert parity < 1e-9
