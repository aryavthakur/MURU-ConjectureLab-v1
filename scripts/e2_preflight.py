#!/usr/bin/env python
"""E2a preflight. Every assertion the execution goal requires BEFORE launch:

  - 100% planned cases present (540 worlds, exact family x regime x noise x
    replicate grid);
  - exact planned seeds/case (30, from the new disjoint band);
  - 0 duplicate case/seed IDs (world_ids AND the full 16,200-seed population);
  - grammar/search budget/operators/objective exactly match the frozen E2
    design (SEARCH_SETTINGS, unchanged from the Held-out run);
  - manifest and source hashes frozen (git blob hashes of every frozen file
    this run imports, plus a clean-diff check against HEAD).

Writes `results/e2/manifest.json`. Raises (nonzero exit) on any failure --
this script is the gate, not a report.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.paper_benchmark import seed_band_registry as sbr  # noqa: E402
from muru.paper_benchmark.calibration_contract import SEARCH_SETTINGS  # noqa: E402
from muru.paper_benchmark.rc5_adapter import assert_grammar_settings  # noqa: E402
from muru.v2_calibration import e2_worlds as e2w  # noqa: E402

E2A_SEED_BASE = 2_104_500_000
E2A_SEED_CAPACITY = 1_000_000
SEEDS_PER_WORLD = 30

#: Every file this run imports from `src/muru/paper_benchmark` and
#: `src/muru/discovery`, i.e. everything the search/scoring/aggregation path
#: touches. Frozen: this run edits none of them.
FROZEN_SOURCE_FILES = [
    "src/muru/paper_benchmark/generator.py",
    "src/muru/paper_benchmark/registry.py",
    "src/muru/paper_benchmark/truth.py",
    "src/muru/paper_benchmark/calibration_contract.py",
    "src/muru/paper_benchmark/rc5_adapter.py",
    "src/muru/paper_benchmark/rc5_estimate.py",
    "src/muru/paper_benchmark/rc5_selection.py",
    "src/muru/paper_benchmark/rc5_case_scoring.py",
    "src/muru/paper_benchmark/rc3_calibration_runner.py",
    "src/muru/paper_benchmark/g2_contract.py",
    "src/muru/paper_benchmark/identity_contract.py",
    "src/muru/paper_benchmark/structural_acceptance.py",
    "src/muru/paper_benchmark/seed_band_registry.py",
    "src/muru/discovery/grammar.py",
    "src/muru/discovery/engine.py",
    "src/muru/discovery/equivalence.py",
    "src/muru/discovery/estimate.py",
]


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def check_population() -> dict:
    worlds = list(e2w.iter_worlds())
    assert len(worlds) == 540, f"expected 540 worlds, got {len(worlds)}"
    ids = [e2w.world_id(*w) for w in worlds]
    assert len(ids) == len(set(ids)) == 540, "duplicate world_id in the E2a population"
    ordinals = [e2w.world_ordinal(*w) for w in worlds]
    assert sorted(ordinals) == list(range(540)), "world_ordinal is not a bijection onto [0, 540)"
    per_family = {}
    for family, regime, noise, replicate in worlds:
        per_family.setdefault(family, 0)
        per_family[family] += 1
    assert all(v == 108 for v in per_family.values()), f"uneven per-family world counts: {per_family}"
    return {"n_worlds": 540, "n_unique_world_ids": len(set(ids)), "per_family_counts": per_family}


def check_seeds() -> dict:
    all_seeds = []
    for family, regime, noise, replicate in e2w.iter_worlds():
        ordinal = e2w.world_ordinal(family, regime, noise, replicate)
        world_seeds = [E2A_SEED_BASE + ordinal * SEEDS_PER_WORLD + k for k in range(SEEDS_PER_WORLD)]
        assert len(world_seeds) == SEEDS_PER_WORLD
        assert len(set(world_seeds)) == SEEDS_PER_WORLD, "duplicate seed within one world"
        all_seeds.extend(world_seeds)
    assert len(all_seeds) == 540 * 30 == 16200
    assert len(set(all_seeds)) == 16200, "duplicate seed across the E2a population"
    assert min(all_seeds) >= E2A_SEED_BASE
    assert max(all_seeds) < E2A_SEED_BASE + E2A_SEED_CAPACITY
    assert max(all_seeds) <= sbr.SIGNED_32BIT_MAX

    new_band = sbr.SeedBand(
        name="v2_e2a_fresh_world_search", min_seed=E2A_SEED_BASE,
        max_seed=E2A_SEED_BASE + E2A_SEED_CAPACITY - 1,
        source="v2_design_reference/MURU_V2_E2_PREDECLARATION.md section 5",
        derivation="E2A_SEED_BASE=2_104_500_000; capacity 1_000_000; seed=BASE+world_ordinal*30+k",
    )
    bands = sbr.DECLARED_BANDS + (new_band,)
    bad = sbr.unacknowledged_overlaps(bands)
    assert not bad, f"unacknowledged seed-band collision(s): {bad}"

    e2w.assert_seed_namespace_disjoint()

    return {
        "n_seeds_total": len(all_seeds), "n_unique_seeds": len(set(all_seeds)),
        "seed_base": E2A_SEED_BASE, "seed_capacity": E2A_SEED_CAPACITY,
        "seed_min": min(all_seeds), "seed_max": max(all_seeds),
        "signed_32bit_max": sbr.SIGNED_32BIT_MAX,
    }


def check_search_config() -> dict:
    grammar_report = assert_grammar_settings()
    expected = dict(
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sqrt", "log", "square", "cube", "inv"],
        excluded_unary=["exp", "sin", "cos", "tan"],
        maxsize=20, niterations=40, populations=15, population_size=33,
        parsimony=0.0032, adaptive_parsimony_scaling=20.0, deterministic=True,
        seeds_per_world=30,
    )
    for key, value in expected.items():
        actual = SEARCH_SETTINGS[key]
        assert actual == value, f"SEARCH_SETTINGS[{key!r}] = {actual!r}, expected {value!r} (frozen E2 config)"
    assert SEARCH_SETTINGS["engine"] == "PySR"
    assert SEARCH_SETTINGS["engine_version"] == "1.5.10"
    return {"search_settings": SEARCH_SETTINGS, "grammar_assertion": grammar_report}


def check_frozen_source() -> dict:
    diff = _run(["git", "diff", "--name-only", "HEAD", "--"] + FROZEN_SOURCE_FILES)
    assert diff == "", f"frozen source files locally modified relative to HEAD: {diff}"
    hashes = {}
    for relpath in FROZEN_SOURCE_FILES:
        blob = _run(["git", "rev-parse", f"HEAD:{relpath}"])
        hashes[relpath] = blob
    head = _run(["git", "rev-parse", "HEAD"])
    branch = _run(["git", "branch", "--show-current"])
    return {"head_commit": head, "branch": branch, "frozen_file_git_blob_hashes": hashes}


def main() -> None:
    out_dir = REPO_ROOT / "results" / "e2"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "population": check_population(),
        "seeds": check_seeds(),
        "search_config": check_search_config(),
        "source_provenance": check_frozen_source(),
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(f"PREFLIGHT PASS -- manifest written to {manifest_path}")
    print(json.dumps({k: ("..." if k == "source_provenance" else v) for k, v in report.items()}, indent=2, default=str))


if __name__ == "__main__":
    main()
