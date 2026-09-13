"""Assemble the v2 development population tables from the spectrum tables."""
import json
from pathlib import Path
from muru.wur_v2 import population as P

out = P.DATA
res = P.build()
res["compounds"].to_csv(out / "compounds.csv", index=False)
res["long_aligned"].to_csv(out / "long_aligned.csv", index=False)
res["wur_aligned_all"].to_csv(out / "wur_aligned_all.csv", index=False)
res["native"].to_csv(out / "native_cells.csv", index=False)
(out / "population_manifest.json").write_text(json.dumps(res["manifest"], indent=1) + "\n")
print(json.dumps(res["manifest"], indent=1))
