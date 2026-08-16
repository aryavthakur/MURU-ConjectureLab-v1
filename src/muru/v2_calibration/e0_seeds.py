"""E0 seed namespace, mechanically disjoint from the benchmark's.

`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 2.2 and
`MURU_V2_A1_STUDY_DESIGN.md` section 5 bind both strings:

    world_id     = "V2C|<experiment>|<cell_id>|r<replicate:03d>"
    seed payload = "muru-v2-calibration|" + "|".join(parts)

`generator.derive_seed` prefixes `"paper-benchmark-v1|"`.  The prefixes differ,
so no v2 world can collide with a benchmark case's seed stream.

The seed parts deliberately carry the **replicate only, never the cell**: the
design requires all nine cells to share covariates, `mu_inf`, `phi_p`, `g` and
the noise draws, which is true iff the seed stream does not see the cell.
:func:`e0_seed` therefore has no cell argument at all, so the property is
enforced by the signature rather than by discipline.
"""
from __future__ import annotations

import hashlib

from muru.paper_benchmark.generator import derive_seed as benchmark_derive_seed

__all__ = [
    "V2_SEED_PREFIX",
    "BENCHMARK_SEED_PREFIX",
    "WORLD_ID_PREFIX",
    "EXPERIMENT",
    "derive_v2_seed",
    "e0_seed",
    "e0_world_id",
    "assert_namespace_disjoint",
]

V2_SEED_PREFIX = "muru-v2-calibration|"
BENCHMARK_SEED_PREFIX = "paper-benchmark-v1|"
WORLD_ID_PREFIX = "V2C|"
EXPERIMENT = "E0"


def derive_v2_seed(*parts: str) -> int:
    """The v2 twin of `generator.derive_seed`, differing only in its prefix."""
    payload = V2_SEED_PREFIX + "|".join(parts)
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def e0_seed(replicate: int, stage: str) -> int:
    """The seed for one E0 replicate's `stage` draw, identical in every cell."""
    return derive_v2_seed(EXPERIMENT, f"r{replicate:03d}", stage)


def e0_world_id(cell_id: str, replicate: int) -> str:
    """`V2C|E0|<cell_id>|r<replicate:03d>`, the design's world identifier."""
    return f"{WORLD_ID_PREFIX}{EXPERIMENT}|{cell_id}|r{replicate:03d}"


def assert_namespace_disjoint() -> dict[str, object]:
    """Fail closed unless the v2 namespace cannot reach the benchmark's.

    Three independent checks, all static:

    1. the two seed payload prefixes are distinct, and neither is a prefix of
       the other (so no payload can be read under both conventions);
    2. no `V2C|` world id resolves through `registry.resolve_case_id`;
    3. on a shared parts tuple the two derivations disagree, which is the
       observable consequence of (1).
    """
    from muru.paper_benchmark.registry import resolve_case_id

    if V2_SEED_PREFIX == BENCHMARK_SEED_PREFIX:
        raise AssertionError("v2 and benchmark seed prefixes are identical")
    if V2_SEED_PREFIX.startswith(BENCHMARK_SEED_PREFIX) or BENCHMARK_SEED_PREFIX.startswith(V2_SEED_PREFIX):
        raise AssertionError("one seed prefix is a prefix of the other")

    probes = [e0_world_id("c_gen_1e4__ceil_1e4", 0), e0_world_id("c_gen_none__ceil_open", 59)]
    for world_id in probes:
        try:
            resolve_case_id(world_id)
        except Exception:
            continue
        raise AssertionError(f"v2 world id resolved as a benchmark case: {world_id}")

    parts = (EXPERIMENT, "r000", "compounds")
    if derive_v2_seed(*parts) == benchmark_derive_seed(*parts):
        raise AssertionError("v2 and benchmark seeds collide on a shared parts tuple")

    return {
        "v2_seed_prefix": V2_SEED_PREFIX,
        "benchmark_seed_prefix": BENCHMARK_SEED_PREFIX,
        "world_id_prefix": WORLD_ID_PREFIX,
        "probe_world_ids": probes,
        "v2_seed_on_shared_parts": derive_v2_seed(*parts),
        "benchmark_seed_on_shared_parts": benchmark_derive_seed(*parts),
        "disjoint": True,
    }
