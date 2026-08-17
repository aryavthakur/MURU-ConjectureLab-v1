#!/usr/bin/env python
"""Run one shard of E2a worlds: full front capture, truth-joined scoring,
cross-seed aggregation, A-E classification. Checkpointed at the world level
-- a world's records are appended to the shard's output files only after all
30 of its seeds and its cross-seed aggregation have completed, so a crash
mid-world leaves no partial world in the resumable checkpoint.

Usage:
    e2_run_shard.py --shard-index I --n-shards N --out-dir DIR [--seeds-per-world 30]

Each of the 540 worlds (e2_worlds.iter_worlds(), in its fixed deterministic
order) is assigned to shard `world_ordinal % n_shards`, so shards are
interleaved across the family/regime/noise grid rather than contiguous
blocks -- a single slow shard is not systematically the hardest cell.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_aggregate as e2a  # noqa: E402
from muru.v2_calibration import e2_classify  # noqa: E402
from muru.v2_calibration import e2_scoring as e2sc  # noqa: E402
from muru.v2_calibration import e2_search as e2s  # noqa: E402
from muru.v2_calibration import e2_worlds as e2w  # noqa: E402


def _asdict_row(front: e2s.FrontRow, scored: e2sc.ScoredRow, world: e2w.WorldContent, seed: int, k: int) -> dict:
    return {
        "world_id": world.world_id,
        "cell_id": world.cell_id,
        "family": world.truth.family,
        "regime": world.truth.regime,
        "noise_level": world.truth.noise_level,
        "replicate": world.replicate,
        "split": None,
        "seed_ordinal_k": k,
        "seed": seed,
        "front_rank": front.front_rank,
        "engine_complexity": front.engine_complexity,
        "grammar_complexity": front.grammar_complexity,
        "expression_string": front.expression_string,
        "canonical_expression": front.canonical_expression,
        "parse_ok": front.parse_ok,
        "canonicalization_status": front.canonicalization_status,
        "train_r2": front.train_r2,
        "valid_r2": front.valid_r2,
        "test_r2": front.test_r2,
        "loss": front.loss,
        "score": front.score,
        "invalid_fraction": front.invalid_fraction,
        "effective_support": list(front.effective_support) if front.effective_support else front.effective_support,
        "template_key": front.template_key_repr,
        "coefficient_estimates": list(front.coefficient_estimates) if front.coefficient_estimates else front.coefficient_estimates,
        "retained_by_argmax_score": front.retained_by_argmax_score,
        "admissibility": front.admissibility,
        "discovered_family": scored.discovered_family,
        "truth_family": scored.truth_family,
        "truth_support": sorted(scored.truth_support),
        "coefficient_regime": scored.coefficient_regime,
        "support_status_vs_truth": scored.support_status_vs_truth,
        "family_status_vs_truth": scored.family_status_vs_truth,
        "g2_correct": scored.g2_correct,
        "g2_event": scored.g2_event,
        "truth_equivalent": scored.truth_equivalent,
    }


def _world_outcome_row(outcome: e2a.WorldOutcome, world: e2w.WorldContent, wall_seconds: float) -> dict:
    cross = outcome.cross_seed
    return {
        "world_id": outcome.world_id,
        "cell_id": outcome.cell_id,
        "family": outcome.family,
        "regime": outcome.regime,
        "noise_level": outcome.noise_level,
        "replicate": outcome.replicate,
        "coefficient": world.truth.coefficient,
        "noise_sd": world.truth.noise_sd,
        "first_loss_stage": outcome.first_loss_stage,
        "n_seeds_completed_with_front": outcome.n_seeds_completed_with_front,
        "n_seeds_execution_failure": outcome.n_seeds_execution_failure,
        "n_seeds_no_candidate": outcome.n_seeds_no_candidate,
        "n_seeds_correct_on_front": outcome.n_seeds_correct_on_front,
        "n_seeds_retained_correct": outcome.n_seeds_retained_correct,
        "selection_count": cross.selection_count,
        "selection_denominator": cross.selection_denominator,
        "stability_gate_passed": cross.stability_gate_passed,
        "voting_seeds": cross.voting_seeds,
        "n_equivalence_classes": len(cross.classes),
        "representative_expression": cross.representative.expression_string if cross.representative else None,
        "representative_seed_ordinal": cross.representative.k if cross.representative else None,
        "representative_g2_correct": outcome.representative_g2_correct,
        "representative_truth_equivalent": outcome.representative_truth_equivalent,
        "seed_outcomes": [dataclasses.asdict(s) for s in outcome.seed_outcomes],
        "wall_seconds": wall_seconds,
    }


def _already_done(worlds_path: Path) -> set[str]:
    done = set()
    if worlds_path.exists():
        with worlds_path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    done.add(json.loads(line)["world_id"])
                except Exception:
                    continue
    return done


def _run_all_worlds(shard_index: int, n_shards: int, my_worlds: list, done: set[str],
                     log_path: Path, errors_path: Path, candidates_path: Path, worlds_path: Path,
                     seeds_per_world: int, seed_base: int) -> None:
    with log_path.open("a") as log:
        log.write(f"shard {shard_index}/{n_shards}: {len(my_worlds)} worlds assigned, "
                   f"{sum(1 for a in my_worlds if e2w.world_id(*a) in done)} already done\n")
        log.flush()

        for family, regime, noise, replicate in my_worlds:
            wid = e2w.world_id(family, regime, noise, replicate)
            if wid in done:
                continue
            t_world = time.monotonic()
            try:
                world = e2w.build_world(family, regime, noise, replicate)
                world_design = e2s.build_world_design(world.compounds, world.trajectories, world.world_id)

                seed_results: list[e2s.SeedFrontResult] = []
                scored_by_seed: dict[int, list[e2sc.ScoredRow]] = {}
                candidate_rows: list[dict] = []

                for k in range(seeds_per_world):
                    seed_val = seed_base + world.world_ordinal * seeds_per_world + k
                    sr = e2s.run_seed_search(world_design, k=k, seed=seed_val)
                    seed_results.append(sr)
                    scored_rows = [e2sc.score_row(fr, world.truth) for fr in sr.rows]
                    scored_by_seed[sr.seed] = scored_rows
                    for fr, sc in zip(sr.rows, scored_rows):
                        candidate_rows.append(_asdict_row(fr, sc, world, seed_val, k))

                outcome = e2a.evaluate_world(world, seed_results, scored_by_seed)
                wall = time.monotonic() - t_world

                with candidates_path.open("a") as cf:
                    for row in candidate_rows:
                        cf.write(json.dumps(row) + "\n")
                with worlds_path.open("a") as wf:
                    wf.write(json.dumps(_world_outcome_row(outcome, world, wall)) + "\n")

                log.write(
                    f"{wid}: stage={outcome.first_loss_stage} "
                    f"front={outcome.n_seeds_correct_on_front}/{outcome.n_seeds_completed_with_front} "
                    f"failures={outcome.n_seeds_execution_failure} wall={wall:.1f}s "
                    f"classify_cache={e2_classify.cache_size()}\n"
                )
                log.flush()
            except Exception as error:
                with errors_path.open("a") as ef:
                    ef.write(json.dumps({
                        "world_id": wid, "error": f"{type(error).__name__}: {error}",
                        "traceback": traceback.format_exc(),
                    }) + "\n")
                log.write(f"{wid}: WORLD-LEVEL EXECUTION FAILURE: {error}\n")
                log.flush()


def run_shard(shard_index: int, n_shards: int, out_dir: Path, seeds_per_world: int, seed_base: int,
              only_worlds: Optional[set[str]] = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = out_dir / f"candidates_shard_{shard_index:03d}.jsonl"
    worlds_path = out_dir / f"worlds_shard_{shard_index:03d}.jsonl"
    log_path = out_dir / f"log_shard_{shard_index:03d}.txt"
    errors_path = out_dir / f"errors_shard_{shard_index:03d}.jsonl"

    done = _already_done(worlds_path)
    all_worlds = list(e2w.iter_worlds())
    my_worlds = [
        args for args in all_worlds
        if e2w.world_ordinal(*args) % n_shards == shard_index
    ]
    # Execution-recovery-only restriction (see E2_EXECUTION_DEVIATION.md): when
    # set, run exactly this world-ID subset regardless of shard assignment --
    # used only for the rescue replay gate, which must rerun a specific,
    # pre-existing set of world IDs and nothing else. Does not change world
    # ordinal assignment, seed derivation, or per-world computation; a world
    # not in `only_worlds` is simply skipped, same as an already-done world.
    if only_worlds is not None:
        my_worlds = [args for args in my_worlds if e2w.world_id(*args) in only_worlds]

    try:
        _run_all_worlds(shard_index, n_shards, my_worlds, done, log_path, errors_path,
                         candidates_path, worlds_path, seeds_per_world, seed_base)
    finally:
        # Execution-safety only (see E2_EXECUTION_DEVIATION.md,
        # throughput-investigation section): without this, a shard process
        # that finishes all its assigned worlds cleanly never actually
        # exits -- e2_classify's persistent worker forks after PySR/Julia
        # is already loaded in this process, and something in that
        # inherited runtime state defeats multiprocessing's own
        # SIGTERM-then-wait atexit cleanup, hanging the parent forever.
        # e2_classify.shutdown() SIGKILLs it directly, which always works.
        e2_classify.shutdown()

    with log_path.open("a") as log:
        log.write(f"shard {shard_index} COMPLETE\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--n-shards", type=int, required=True)
    parser.add_argument("--out-dir", type=str, required=True)
    parser.add_argument("--seeds-per-world", type=int, default=30)
    parser.add_argument("--seed-base", type=int, default=2_104_500_000)
    parser.add_argument(
        "--only-worlds-file", type=str, default=None,
        help="Execution-recovery-only (see E2_EXECUTION_DEVIATION.md): path to a "
             "JSON list of world IDs. When given, run exactly these world IDs "
             "(intersected with this shard's normal ordinal assignment) instead "
             "of this shard's full assignment. Used only for the rescue replay "
             "gate.",
    )
    args = parser.parse_args()
    only_worlds = None
    if args.only_worlds_file:
        only_worlds = set(json.loads(Path(args.only_worlds_file).read_text()))
    run_shard(args.shard_index, args.n_shards, Path(args.out_dir), args.seeds_per_world, args.seed_base,
              only_worlds=only_worlds)


if __name__ == "__main__":
    main()
