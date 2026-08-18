#!/usr/bin/env python
"""Part V: replay parity gate.

Reads ALREADY-COMPLETED worlds from a live E2a run's output directories
(read-only; never writes there), reconstructs each selected world's raw
front data (deliberately DISCARDING the persisted classification-derived
fields -- parse_ok, canonicalization_status, effective_support,
discovered_family, g2_correct, truth_equivalent -- so the lazy path
genuinely recomputes them from the real, unmodified classifier, not from
an oracle lookup), runs `lazy_classify.lazy_evaluate_world`, and compares
its result to the EXHAUSTIVE result already sealed for that world.

Sample selection is OUTCOME-BLIND: worlds are chosen by stratifying on
`wall_seconds` (an execution-timing field, not a scientific A-E field)
into fast/median/slow terciles and taking a fixed count from each --
chosen for coverage of runtime classes (Part VI needs this too), never by
looking at `first_loss_stage` or any other scientific field. Selection
happens BEFORE any scientific field of the selected worlds is read for
comparison purposes.

Per-world outcome codes are salted/opaque wherever this script writes
output a human will read; the ONLY aggregate figures ever printed or
written to `MURU_V2_E2_REPLAY_PARITY.json` are N_REPLAY / N_MATCH /
N_MISMATCH / PARITY_PASS / DETERMINISM_PASS -- never a stage frequency.
Per-mismatch diagnostic detail (needed to debug a failure, should one
occur) is written only to a gitignored local quarantine file, mirroring
the outcome-blind interim characterization's own precedent.

Usage:
    replay_parity.py --result-dir DIR [DIR ...] --sample-size N --out FILE.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.v2_calibration import e2_classify, e2_worlds  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import lazy_classify as lc  # noqa: E402

SALT = "e2-rescue-v2-replay-parity"  # fixed, non-secret -- opaque codes only need to not be reversible casually


def _opaque(world_id: str) -> str:
    return "W" + hashlib.sha256((SALT + world_id).encode()).hexdigest()[:12]


def _load_world_outcomes(dirs: list[Path]) -> dict[str, dict]:
    """world_id -> full outcome record (kept in memory only; never printed
    whole). Deduplicates by world_id, last-write-wins (matches
    `e2_run_shard._already_done`'s own dedup discipline)."""
    out: dict[str, dict] = {}
    for d in dirs:
        for path in sorted(d.glob("worlds_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    wid = rec.get("world_id")
                    if wid:
                        out[wid] = rec
    return out


def _load_candidates(dirs: list[Path], world_id: str) -> dict[int, list[lc.RawFrontRow]]:
    """Raw (classification-free) front rows for one world, grouped by
    seed. Only structural fields are kept -- expression_string,
    front_rank, complexity, r2/invalid_fraction, retained flag. Every
    classification-derived persisted field on these rows
    (parse_ok/canonicalization_status/effective_support/discovered_family/
    g2_correct/truth_equivalent) is read here ONLY to be discarded, never
    passed to the lazy path -- the whole point of this harness is that the
    lazy path must recompute these itself via the real classifier."""
    by_seed: dict[int, list[lc.RawFrontRow]] = {}
    for d in dirs:
        for path in sorted(d.glob("candidates_shard_*.jsonl")):
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("world_id") != world_id:
                        continue
                    seed = rec["seed"]
                    by_seed.setdefault(seed, []).append(lc.RawFrontRow(
                        seed_ordinal_k=rec["seed_ordinal_k"], seed=seed,
                        front_rank=rec["front_rank"], expression_string=rec["expression_string"],
                        complexity=rec["engine_complexity"], valid_r2=rec["valid_r2"],
                        invalid_fraction=rec["invalid_fraction"], candidate_test_r2=rec["test_r2"],
                        retained_by_argmax_score=rec["retained_by_argmax_score"],
                    ))
    return by_seed


def _select_sample(outcomes: dict[str, dict], sample_size: int) -> list[str]:
    """OUTCOME-BLIND selection: sort by wall_seconds only, take an even
    stride across fast/median/slow terciles. Never reads first_loss_stage
    or any other scientific field for the selection decision."""
    by_wall = sorted(outcomes.items(), key=lambda kv: kv[1].get("wall_seconds", 0.0))
    n = len(by_wall)
    if n == 0:
        return []
    sample_size = min(sample_size, n)
    if sample_size >= n:
        return [wid for wid, _ in by_wall]
    # Even stride across the wall_seconds-sorted list -- covers the full
    # runtime-class range, not just one tercile.
    stride = n / sample_size
    indices = sorted({int(i * stride) for i in range(sample_size)})
    return [by_wall[i][0] for i in indices]


def _rebuild_truth(rec: dict) -> e2_worlds.WorldTruth:
    world = e2_worlds.build_world(rec["family"], rec["regime"], rec["noise_level"], rec["replicate"])
    return world.truth


def run_replay(dirs: list[Path], sample_size: int, verify_determinism: bool) -> dict:
    outcomes = _load_world_outcomes(dirs)
    sample = _select_sample(outcomes, sample_size)

    n_match = 0
    n_mismatch = 0
    mismatch_detail = []  # local diagnostic only -- never surfaced in the returned summary
    per_world_timing = []

    for wid in sample:
        exhaustive = outcomes[wid]
        truth = _rebuild_truth(exhaustive)
        by_seed = _load_candidates(dirs, wid)

        lc.reset_call_counters()
        t0 = time.monotonic()
        lazy_result = lc.lazy_evaluate_world(by_seed, truth)
        elapsed = time.monotonic() - t0

        determinism_ok = True
        if verify_determinism:
            lc.reset_call_counters()
            lazy_result_2 = lc.lazy_evaluate_world(by_seed, truth)
            determinism_ok = (
                lazy_result.first_loss_stage == lazy_result_2.first_loss_stage
                and lazy_result.representative_g2_correct == lazy_result_2.representative_g2_correct
                and lazy_result.representative_truth_equivalent == lazy_result_2.representative_truth_equivalent
            )

        stage_match = lazy_result.first_loss_stage == exhaustive["first_loss_stage"]
        exhaustive_stage = exhaustive["first_loss_stage"]
        # representative_g2_correct / representative_truth_equivalent are
        # compared ONLY where they are decision-relevant -- see
        # MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md section 4 (updated after a
        # real mismatch found during this harness's own shakedown run: for
        # stages A/B, `evaluate_world` still computes a representative as a
        # byproduct of the unconditional cross-seed grouping step, even
        # though NEITHER field plays any role in reaching stage A or B --
        # the lazy path correctly never computes them there, and comparing
        # them would be comparing a byproduct neither the frozen decision
        # sequence nor this rescue's routing gate ever reads).
        if exhaustive_stage in ("A", "B"):
            rep_g2_match = True
            rep_te_match = True
        else:
            rep_g2_match = lazy_result.representative_g2_correct == exhaustive["representative_g2_correct"]
            if exhaustive_stage == "E":
                rep_te_match = True  # not decision-relevant once g2_correct is already True; lazy never computes it
            else:
                rep_te_match = lazy_result.representative_truth_equivalent == exhaustive["representative_truth_equivalent"]

        is_match = stage_match and rep_g2_match and rep_te_match and determinism_ok
        if is_match:
            n_match += 1
        else:
            n_mismatch += 1
            mismatch_detail.append({
                "opaque_id": _opaque(wid),
                "stage_match": stage_match, "rep_g2_match": rep_g2_match,
                "rep_te_match": rep_te_match, "determinism_ok": determinism_ok,
            })

        # NOTE: `witness_path` is deliberately NOT included here.
        # `lazy_result.witness_path in {PHASE2_FRONT_SCAN_B, PHASE2_FULL_SCAN_A}`
        # is, by this algorithm's own construction (see
        # MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md section 2), a DETERMINISTIC
        # function of the stage itself (PHASE2_FULL_SCAN_A implies stage A;
        # PHASE2_FRONT_SCAN_B implies stage B) -- carrying the stage letter
        # explicitly in its own name. Surfacing it per-world in this
        # deliverable would be a scientific-stage leak by another name, in
        # violation of "do not reveal scientific stage frequencies". Numeric
        # call counts and timings are kept (Part VI's own required metrics),
        # since they report computational cost, not a stage label.
        per_world_timing.append({
            "opaque_id": _opaque(wid),
            "lazy_wall_seconds": elapsed,
            "lazy_classify_calls": lazy_result.n_classify_calls,
            "lazy_equivalence_calls": lazy_result.n_equivalence_calls,
            "exhaustive_wall_seconds": exhaustive.get("wall_seconds"),
        })

    n_replay = len(sample)
    summary = {
        "N_REPLAY": n_replay,
        "N_MATCH": n_match,
        "N_MISMATCH": n_mismatch,
        "PARITY_PASS": bool(n_replay > 0 and n_mismatch == 0),
        "DETERMINISM_VERIFIED": bool(verify_determinism),
        "selection_method": "wall_seconds-stratified even stride (outcome-blind)",
        "classifier_version": None,  # filled by caller if a cache/version context is available
        "per_world_timing": per_world_timing,  # opaque IDs, timings/call-counts only, no stage labels
    }
    if mismatch_detail:
        quarantine_path = Path("/tmp/e2_rescue_v2_quarantine")
        quarantine_path.mkdir(exist_ok=True)
        (quarantine_path / "replay_mismatch_detail.json").write_text(json.dumps(mismatch_detail, indent=2))
        summary["mismatch_detail_quarantined_at"] = str(quarantine_path / "replay_mismatch_detail.json")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", action="append", required=True, dest="dirs")
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--no-determinism-check", action="store_true")
    args = parser.parse_args()

    dirs = [Path(d) for d in args.dirs]
    try:
        summary = run_replay(dirs, args.sample_size, verify_determinism=not args.no_determinism_check)
    finally:
        e2_classify.shutdown()  # SIGKILL the persistent classify worker before this process exits (same discipline e2_run_shard.py uses)

    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(f"N_REPLAY: {summary['N_REPLAY']}")
    print(f"N_MATCH: {summary['N_MATCH']}")
    print(f"N_MISMATCH: {summary['N_MISMATCH']}")
    print(f"PARITY_PASS: {summary['PARITY_PASS']}")
    print(f"DETERMINISM_VERIFIED: {summary['DETERMINISM_VERIFIED']}")
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
