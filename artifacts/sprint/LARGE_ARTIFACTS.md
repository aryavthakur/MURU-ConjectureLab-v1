# Large sprint artifacts (not committed)

Two artifacts exceed a sensible git payload and are regenerable byte-for-byte
from committed code plus the read-only checkpoint store `artifacts/ov_ckpt`.

| file | bytes | sha256 | regenerate |
|---|---|---|---|
| `candidate_feature_cache.json` | 18998450 | `9de8abfe22842f3a2bad81953e508343df985a9ba9b55dd7b21b545e28964f1e` | `PYTHONPATH=src python3 scripts/sprint_features.py` |
| `headroom_members.json` | 5139328 | `5c2ca4fa2366f41a732d7a812923d4d44501b9f1143646f78439bc9863c2dbb3` | `PYTHONPATH=src python3 scripts/sprint_headroom.py` |

Both are deterministic: no RNG is seeded from time, and the constant refit uses
`scipy.optimize.least_squares` from a fixed start with fixed tolerances.
