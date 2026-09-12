"""CLI: reserve the identity-only WUR-DEV internal holdout (Stage 2 preflight).

Runs BEFORE any Stage 2A mu is computed. Reads identity columns only: the
partition is rebuilt from the frozen release with the Stage 0 code, the
sealed key hash is asserted, and the holdout is drawn from free WUR-DEV
scaffold groups at the frozen seed. Writes artifacts/wur_dev_internal_holdout.json.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import apply_d6, partition, sealed_scaffold_groups
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.wur_stage2.holdout import reserve_internal_holdout

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
EXPECTED_SEALED_SHA = "6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52"

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    pre = partition(load_annotated_trajectories(data_dir))
    part = apply_d6(pre, sealed_scaffold_groups(pre["POS"]))
    pos = part["POS"]
    sealed = sorted(pos.loc[pos["side"] == "WUR-SEALED", "connectivity_key"])
    sha = canonical_key_hash(sealed)
    recorded = json.loads((ART / "wur_sealed_partition.json").read_text())
    assert sha == EXPECTED_SEALED_SHA == recorded["connectivity_keys_sha256"], \
        "sealed partition does not reproduce the frozen hash"
    dev = pos[pos["side"] == "WUR-DEV"].reset_index(drop=True)
    assert not (set(dev["connectivity_key"]) & set(sealed))

    out = reserve_internal_holdout(dev)
    out["purpose"] = ("Identity-only internal holdout reserved before Stage 2A. "
                      "HOLD keys are excluded from every Stage 2A and Stage 2B "
                      "computation until the single preregistered internal "
                      "check. Not a substitute for WUR-SEALED.")
    out["created_utc"] = datetime.now(timezone.utc).isoformat()
    out["sealed_partition_sha256"] = sha
    out["wur_dev_pos"] = {"n_keys": int(len(dev)),
                          "n_scaffold_groups": int(dev["scaffold_group"].nunique())}
    out["environment"] = environment_provenance(ROOT)
    (ART / "wur_dev_internal_holdout.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("n_free_groups", "n_free_keys")}
                     | {"hold": {k: out["hold"][k] for k in ("n_keys", "n_scaffold_groups", "connectivity_keys_sha256")},
                        "analysis": {k: out["analysis"][k] for k in ("n_keys", "n_scaffold_groups", "connectivity_keys_sha256")}},
                     indent=1))
