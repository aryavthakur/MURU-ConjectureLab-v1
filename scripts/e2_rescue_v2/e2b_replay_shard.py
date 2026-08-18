#!/usr/bin/env python
"""E2b (Held-out replay) -- frozen identity check against the sealed v1 evidence.

FROZEN SPECIFICATION (recovered, not invented; see
results/e2/cloud_x86_parity/E2B_PREREQUISITE_BLOCKER.md, itself quoting
v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json and
MURU_V2_G2_PARETO_STUDY_DESIGN.md 2.3/2.5):

  Replay population   the 144 Held-out G2 cases
  Case/searches/seeds 144 / 4,320 / SEEDS_PER_CASE = 30
  Seeds               the v1 seeds
  Identity criterion  replayed retention must reproduce the sealed
                      `selection_count` AND cross-seed representative for all
                      144 cases, replaying `group_and_select` exactly as the
                      decomposition did
  Failure consequence any case that fails to reproduce is QUARANTINED AND
                      REPORTED, never silently dropped
  Admissibility       DECISION_INADMISSIBLE -- may only corroborate or
                      contradict a conclusion already reached on E2a

WHAT THIS RUNS. Exactly the frozen per-case path `rc5_runner.execute_case`
runs, up to and including `group_and_select` -- the only stage the identity
criterion is defined over:

    seeds      = case_search_seeds(case_id)
    scalars    = fit_case_scalars(compounds, trajectories)
    design     = build_case_design(compounds, scalars)
    selections = [_run_one_seed(design, backend, k, seed) ...]
    selection  = group_and_select(selections)

Nothing is reimplemented: every one of those is imported unmodified from the
frozen modules. `_run_one_seed` is private but is precisely what `execute_case`
calls per seed; calling it directly is what keeps this a replay rather than a
parallel implementation. The Gate-8 falsification phase (F1), the acceptance
gates, endpoint scoring and record emission are deliberately NOT run: they are
downstream of the identity criterion and would double the search cost (F1 is
itself a second full 30-seed re-execution) without contributing to it.

SECTION 8.2 IS PRESERVED: any one seed's EXECUTION_FAILURE poisons the whole
case, and such a case is reported UNEVALUABLE_EXECUTION_FAILURE -- never
compared as if it had produced a clean selection.

SEED PROVENANCE IS CROSS-CHECKED, NOT ASSUMED: `case_search_seeds` re-derives
the 30 seeds from the case id, and this script verifies that derivation against
the `seeds_used` recorded in the sealed v1 record. A mismatch is a hard failure
for that case (SEED_DERIVATION_MISMATCH) -- it would mean the replay is not
using "the v1 seeds" the specification requires.

HOST PROVENANCE (disclosed, not glossed): the sealed reference values were
produced on macOS/arm64 under Python 3.13.12 (see the sealed
execution_manifest.json). This replay runs on Linux/x86_64 under Python 3.13.5.
`group_and_select` carries no wall-clock cap, so this comparison does NOT
inherit the SIMPLIFY_TIMEOUT host-speed defect that caused
NEW_CLOUD_HOST_PARITY_FAILED for the E2 corpus -- but cross-host reproduction
of the PySR search itself remains an empirical question. A non-reproducing case
therefore cannot be attributed to v1 being wrong without confounding, and this
script's output must be read with that caveat attached.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402

cap_threads()

from muru.paper_benchmark.calibration_contract import SeedStatus  # noqa: E402
from muru.paper_benchmark.rc5_adapter import build_case_design  # noqa: E402
from muru.paper_benchmark.rc5_estimate import fit_case_scalars  # noqa: E402
from muru.paper_benchmark.rc5_runner import (  # noqa: E402
    PySRCaseBackend,
    _run_one_seed,
    materialize_case,
)
from muru.paper_benchmark.rc5_seeds import case_search_seeds  # noqa: E402
from muru.paper_benchmark.rc5_selection import group_and_select  # noqa: E402

SEALED_DIR = REPO_ROOT / "results/e2b_heldout"
SEALED_SUMMARY = SEALED_DIR / "G2_SELECTION_COUNT_AND_REPRESENTATIVE_144.json"
SEALED_EVIDENCE = SEALED_DIR / "sealed_evidence/held_out"


def load_sealed_cases() -> list[dict]:
    payload = json.loads(SEALED_SUMMARY.read_text())
    cases = payload["cases"]
    if len(cases) != 144:
        raise SystemExit(f"expected 144 sealed G2 cases, found {len(cases)}")
    return cases


def sealed_seeds_for(case: dict) -> list[int] | None:
    """The 30 seeds the v1 run actually used, from its own sealed record."""
    rel = case.get("source_record_relpath")
    if not rel:
        return None
    path = SEALED_EVIDENCE / rel
    if not path.exists():
        return None
    return list(json.loads(path.read_text()).get("seeds_used") or [])


def replay_one_case(case: dict) -> dict:
    case_id = case["case_id"]
    t0 = time.monotonic()

    derived_seeds = list(case_search_seeds(case_id))
    sealed_seeds = sealed_seeds_for(case)
    if sealed_seeds is not None and sealed_seeds != derived_seeds:
        return {
            "case_id": case_id,
            "verdict": "SEED_DERIVATION_MISMATCH",
            "reproduced": False,
            "quarantined": True,
            "detail": "case_search_seeds() does not reproduce the sealed run's seeds_used",
            "sealed_seeds_head": sealed_seeds[:3],
            "derived_seeds_head": derived_seeds[:3],
            "wall_seconds": time.monotonic() - t0,
        }

    content = materialize_case(case_id)
    scalars = fit_case_scalars(content.compounds, content.trajectories)
    design = build_case_design(content.compounds, scalars)
    backend = PySRCaseBackend()

    selections = [
        _run_one_seed(design, backend, k, seed)
        for k, seed in enumerate(derived_seeds)
    ]

    # A3.5 section 8.2: one seed's EXECUTION_FAILURE poisons the whole case.
    failures = [s for s in selections if s.status is SeedStatus.EXECUTION_FAILURE]
    if failures:
        return {
            "case_id": case_id,
            "verdict": "UNEVALUABLE_EXECUTION_FAILURE",
            "reproduced": False,
            "quarantined": True,
            "detail": f"{len(failures)} of 30 seeds raised EXECUTION_FAILURE",
            "first_error": failures[0].error_message,
            "wall_seconds": time.monotonic() - t0,
        }

    selection = group_and_select(selections)
    replayed_rep = (
        selection.representative.expression_string
        if selection.representative is not None else None
    )

    sealed_count = case["selection_count"]
    sealed_rep = case["cross_seed_representative_expression"]
    count_ok = selection.selection_count == sealed_count
    rep_ok = replayed_rep == sealed_rep
    reproduced = count_ok and rep_ok

    return {
        "case_id": case_id,
        "family_id": case.get("family_id"),
        "verdict": "REPRODUCED" if reproduced else "MISMATCH",
        "reproduced": reproduced,
        "quarantined": not reproduced,
        "selection_count_sealed": sealed_count,
        "selection_count_replayed": selection.selection_count,
        "selection_count_match": count_ok,
        "representative_sealed": sealed_rep,
        "representative_replayed": replayed_rep,
        "representative_match": rep_ok,
        "selection_denominator_replayed": selection.selection_denominator,
        "voting_seeds": selection.voting_seeds,
        "distinct_expression_strings": selection.distinct_expression_strings,
        "distinct_coefficient_vectors": selection.distinct_coefficient_vectors,
        "sealed_g2_event": case.get("g2_event"),
        "wall_seconds": time.monotonic() - t0,
    }


def already_done(out_path: Path) -> set[str]:
    done: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["case_id"])
            except Exception:
                continue
    return done


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shard-index", type=int, required=True)
    ap.add_argument("--n-shards", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"e2b_shard_{args.shard_index:03d}.jsonl"
    log_path = out_dir / f"e2b_log_shard_{args.shard_index:03d}.txt"
    err_path = out_dir / f"e2b_errors_shard_{args.shard_index:03d}.jsonl"

    cases = load_sealed_cases()
    mine = [c for i, c in enumerate(cases) if i % args.n_shards == args.shard_index]
    done = already_done(out_path)

    with log_path.open("a") as log:
        log.write(f"e2b shard {args.shard_index}/{args.n_shards}: "
                  f"{len(mine)} assigned, {sum(1 for c in mine if c['case_id'] in done)} already done\n")
        log.flush()
        for case in mine:
            if case["case_id"] in done:
                continue
            try:
                row = replay_one_case(case)
            except Exception as error:  # orchestration-level, never silently dropped
                with err_path.open("a") as ef:
                    ef.write(json.dumps({
                        "case_id": case["case_id"],
                        "error": f"{type(error).__name__}: {error}",
                    }) + "\n")
                log.write(f"{case['case_id']}: CASE-LEVEL EXECUTION FAILURE: {error}\n")
                log.flush()
                continue
            with out_path.open("a") as fh:
                fh.write(json.dumps(row) + "\n")
            log.write(f"{row['case_id']}: {row['verdict']} wall={row['wall_seconds']:.1f}s\n")
            log.flush()
        log.write(f"e2b shard {args.shard_index} COMPLETE\n")


if __name__ == "__main__":
    main()
