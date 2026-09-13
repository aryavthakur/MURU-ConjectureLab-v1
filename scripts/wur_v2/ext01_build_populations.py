"""External step 1 (outcome-blind): file index, allowlisted scan headers, populations VALIDATION / ANCHOR / SECONDARY."""
import hashlib, json, time
from pathlib import Path
import pandas as pd
from muru.io.wur_provenance import canonical_key_hash
from muru.wur_v2 import external_multims2 as E
ROOT = Path(__file__).resolve().parents[2]; OUT = E.OUT; OUT.mkdir(parents=True, exist_ok=True)
t0 = time.time()
files = E.file_index()
files = files[files.collection.isin(["NEXUS", "SELLECK"]) | files.blank]
headers = E.build_headers(files)
hp = ROOT / "data/external/multims2_mzml/headers_allowlisted.parquet"
headers.to_parquet(hp)
res = E.populations(headers, files)
summ = E.summarize(res)
sp = res["spectra"]
allow, spectra_by_pop = {}, {}
for name, pop in res["populations"].items():
    s = sp.merge(pop[["key", "collection", "position"]], on=["key", "collection", "position"])
    allow[name] = sorted(set(zip(s.file, s.spectrum_id)))
    spectra_by_pop[name] = s.to_dict("records")
overlap = set(allow["ANCHOR"]) & (set(allow["VALIDATION"]) | set(allow["SECONDARY"]))
assert not overlap, f"{len(overlap)} spectra matched to both an anchor and a validation compound"
summ["files"] = {"n_mzml": int(len(files)), "n_blank": int(files.blank.sum()), "by_collection_energy": files.groupby(["collection", "energy"]).size().rename("n").reset_index().to_dict("records")}
summ["headers"] = {"n_spectra": int(len(headers)), "n_ms2": int((headers.ms_level == 2).sum()), "sha256_parquet": hashlib.sha256(hp.read_bytes()).hexdigest(),
                   "scan_window_lower_values": headers[headers.ms_level == 2].scan_window_lower_limit.value_counts().to_dict(),
                   "scan_window_upper_values": headers[headers.ms_level == 2].scan_window_upper_limit.value_counts().to_dict(),
                   "collision_energy_values": headers[headers.ms_level == 2].collision_energy.value_counts().to_dict(),
                   "allowlist": sorted(E.X.ALLOW.values())}
summ["seconds"] = time.time() - t0
payload = {"summary": summ, "populations": {n: p[["key", "collection", "position", "smiles", "mh", "scaffold_group"]].to_dict("records") for n, p in res["populations"].items()},
           "allowed_spectra": {n: [list(x) for x in v] for n, v in allow.items()}, "spectra": spectra_by_pop}
(OUT / "populations.json").write_text(json.dumps(payload, indent=1, default=float) + "\n")
res["table"].to_csv(OUT / "design_rules_table.csv", index=False)
print(json.dumps(summ, indent=1, default=float)[:4000])
