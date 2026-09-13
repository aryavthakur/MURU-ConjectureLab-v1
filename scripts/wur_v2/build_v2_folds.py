"""Freeze the v2 partitions (identity only) to artifacts/wur_v2/folds.json."""
import json
from pathlib import Path
import pandas as pd
from muru.io.wur_provenance import canonical_key_hash
from muru.wur_v2 import folds as FO
ROOT = Path(__file__).resolve().parents[2]
cov = pd.read_csv(ROOT / "artifacts/wur_v2/data/compounds.csv")
parts = FO.all_partitions(cov)
out = {"population_keys_sha256": canonical_key_hash(cov.group_key), "k": FO.K, "inner_k": FO.INNER_K,
       "seeds": {"primary": FO.PRIMARY_SEED, "sensitivity": list(FO.SENSITIVITY_SEEDS), "strict": FO.STRICT_SEED,
                 "random": FO.RANDOM_SEED, "inner_base": FO.INNER_SEED_BASE}, "partitions": {}}
c = cov.set_index("group_key")
for name, a in parts.items():
    summ = []
    for f in sorted(a.unique()):
        ks = a.index[a == f]
        sub = c.loc[ks]
        summ.append({"fold": int(f), "n": int(len(ks)), "n_scaffold_groups": int(sub.scaffold_group.nunique()),
                     "n_strict_clusters": int(sub.strict_cluster.nunique()), "n_benzene": int((sub.scaffold_group == FO.GIANT_GROUP).sum()),
                     "n_lcsb_primary": int((sub.primary_source == "LCSB").sum())})
    out["partitions"][name] = {"assignment_sha256": FO.assignment_hash(a), "folds": summ,
                               "assignment": {k: int(v) for k, v in a.items()}}
    print(name, [(s["n"], s["n_benzene"], s["n_lcsb_primary"]) for s in summ])
# distinct held-out sets across grouped partitions
sets = {frozenset(parts[p].index[parts[p] == f]) for p in ("PRIMARY", "PARTITION_S1", "PARTITION_S2") for f in range(FO.K)}
out["distinct_heldout_sets_primary_plus_sensitivity"] = len(sets)
print("distinct held-out sets", len(sets))
(ROOT / "artifacts/wur_v2/folds.json").write_text(json.dumps(out, indent=1) + "\n")
