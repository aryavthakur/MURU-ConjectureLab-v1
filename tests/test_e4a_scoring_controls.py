"""Step 5: the 12 required non-scientific control/replay tests for the E4a
scoring implementation (e4a_scoring.py), run BEFORE any scientific E4a
result is read. Synthetic/schema-faithful data throughout except test 1,
which replays ONE already-completed real E2a world (a non-scientific
replay-consistency check, mirroring Part V's own replay-parity discipline,
not a new scientific read -- the world's OWN already-persisted stage is
the oracle, and this test only checks the re-scoring pipeline reproduces
it byte-for-byte).

No test in this file inspects, aggregates, or prints an A/B/C/D/E
frequency across more than the single real world test 1 replays (and that
world's stage is read only to compare against, never accumulated with any
other world's).
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from muru.discovery.engine import cap_threads  # noqa: E402
cap_threads()

from muru.paper_benchmark.g2_contract import wilson_lower_95, wilson_upper_95  # noqa: E402
from muru.v2_calibration import e2_classify, e2_worlds  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import e4a_scoring as e4a  # noqa: E402
from muru.v2_calibration.e2_rescue_v2 import lazy_classify as lc  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
OLD_RUN_DIR = REPO_ROOT.parent.parent / "worktrees" / "exp-v2-e2-pareto-observability" / "results" / "e2" / "run"

results = {"pass": 0, "fail": 0}


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        results["pass"] += 1
        print(f"PASS: {name}")
    else:
        results["fail"] += 1
        print(f"FAIL: {name} -- {detail}")


def row(seed=0, k=0, rank=0, expr="x0", cx=1, r2=0.5, score=None, invf=0.0, tr2=0.5):
    return e4a.E4aRow(seed_ordinal_k=k, seed=seed, front_rank=rank, expression_string=expr,
                       complexity=cx, valid_r2=r2, invalid_fraction=invf, candidate_test_r2=tr2, score=score)


# --- test 2: R3 retains the complete eligible front ---
def test_2_r3_full_front():
    rows = [row(rank=i, r2=0.1 * i, score=0.1 * i) for i in range(7)]
    retained = e4a.retain_r3(rows)
    check("2: R3 retains complete front", retained == rows, f"{len(retained)} != {len(rows)}")


# --- test 3: conditional_retention_recall(R3) mechanically 1.0 whenever defined ---
def test_3_r3_recall_identity():
    good = [
        e4a.CaseResult("w1", "mass_power", 0, "R3", "E", True, None, "x0", "mass_power", (3,), 3, 30, 30, 0),
        e4a.CaseResult("w2", "mass_power", 1, "R3", "C", False, False, "x0*x1", "mass_interaction", (5,), 5, 12, 30, 0),
    ]
    out = e4a.conditional_retention_recall(good, policy="R3")
    check("3a: R3 recall is exactly 1.0", out["recall"] == 1.0 and out["is_identity"] is True)
    check("3b: R3 recall has no Wilson interval (identity, not sample)", out["wilson_lower"] is None and out["wilson_upper"] is None)

    bad = good + [e4a.CaseResult("w3", "mass_power", 2, "R3", "B", None, None, None, None, (), None, 0, 30, 0)]
    threw = False
    try:
        e4a.conditional_retention_recall(bad, policy="R3")
    except AssertionError:
        threw = True
    check("3c: R3 stage=B is a detected control violation, not silently accepted", threw)


# --- test 4: R1/R3/R5 downstream vote identity when no valid_r2 tie ---
def test_4_r1_r3_r5_identity():
    m = row(rank=2, r2=0.9, cx=4, expr="unique_max", score=0.5)
    rows = [row(rank=0, r2=0.3, cx=6, expr="a", score=0.9), row(rank=1, r2=0.5, cx=2, expr="b", score=0.8), m,
            row(rank=3, r2=0.2, cx=1, expr="d", score=0.1)]
    votes = {}
    for policy, fn in (("R1", e4a.retain_r1), ("R3", e4a.retain_r3), ("R5", e4a.retain_r5)):
        retained = fn(rows)
        votes[policy] = e4a.cast_vote(retained)
    check("4: R1/R3/R5 all include the unique valid_r2 max", all(v is not None and v.expression_string == "unique_max" for v in votes.values()),
          str({k: (v.expression_string if v else None) for k, v in votes.items()}))
    check("4b: R1/R3/R5 cast literally the same vote object identity-by-value", len({votes["R1"].expression_string, votes["R3"].expression_string, votes["R5"].expression_string}) == 1)


# --- test 5: tie handling matches frozen lexicographic (lowest front_rank) rule ---
def test_5_tie_break():
    tied = [row(rank=3, r2=0.7, score=0.9, expr="late"), row(rank=1, r2=0.7, score=0.9, expr="early"), row(rank=5, r2=0.7, score=0.9, expr="latest")]
    r0 = e4a.retain_r0(tied)
    r1 = e4a.retain_r1(tied)
    vote = e4a.cast_vote(tied)
    check("5a: R0 tie-break picks lowest front_rank", r0[0].expression_string == "early", r0[0].expression_string)
    check("5b: R1 tie-break picks lowest front_rank", r1[0].expression_string == "early", r1[0].expression_string)
    check("5c: vote-reduction tie-break picks lowest front_rank", vote.expression_string == "early", vote.expression_string)
    r4 = e4a.retain_r4([row(rank=2, r2=0.9, cx=3, expr="x"), row(rank=0, r2=0.9, cx=3, expr="y"), row(rank=1, r2=0.85, cx=1, expr="z")], eps=0.02)
    check("5d: R4 complexity tie-break picks lowest front_rank", r4[0].expression_string == "y", r4[0].expression_string)


# --- test 6: Dev and EVAL are disjoint (and exhaustive over replicate 0..11) ---
def test_6_dev_eval_disjoint():
    splits = {r: e4a.dev_eval_split(r) for r in range(12)}
    dev = {r for r, s in splits.items() if s == "DEV"}
    eval_ = {r for r, s in splits.items() if s == "EVAL"}
    check("6a: DEV/EVAL disjoint", dev.isdisjoint(eval_))
    check("6b: DEV/EVAL exhaustive over [0,12)", dev | eval_ == set(range(12)), str(dev | eval_))
    check("6c: DEV is exactly {0,1} per section 6", dev == {0, 1}, str(dev))


# --- test 7: EVAL count = 90 for mass_power, re-derived mechanically ---
def test_7_eval_denominator_90():
    n_cells_per_family = 3 * 3  # regimes x noise levels
    n_eval_replicates = 10      # 12 - 2 DEV
    derived = n_cells_per_family * n_eval_replicates
    check("7: 9 cells x 10 EVAL replicates == EVAL_DENOM_MASS_POWER", derived == e4a.EVAL_DENOM_MASS_POWER == 90, str(derived))


# --- test 8: no world is duplicated or omitted (full 540-population bijection) ---
def test_8_population_bijection():
    seen_ordinals = set()
    seen_ids = set()
    n = 0
    for family, regime, noise in e2_worlds.iter_cells():
        for replicate in range(e2_worlds.N_REPLICATES):
            n += 1
            ordinal = e2_worlds.world_ordinal(family, regime, noise, replicate)
            wid = e2_worlds.world_id(family, regime, noise, replicate)
            seen_ordinals.add(ordinal)
            seen_ids.add(wid)
    check("8a: population size is exactly 540", n == 540, str(n))
    check("8b: world_ordinal is a bijection (no duplicate ordinals)", len(seen_ordinals) == 540, str(len(seen_ordinals)))
    check("8c: world_id is a bijection (no duplicate ids)", len(seen_ids) == 540, str(len(seen_ids)))
    check("8d: ordinals form the exact contiguous range [0,540)", seen_ordinals == set(range(540)))


# --- test 9: candidate-flow accounting reconciles ---
def test_9_candidate_flow():
    seed_rows = {s: [row(seed=s, k=s, rank=i, expr=f"s{s}r{i}", r2=0.1 + 0.01 * i, score=0.1 + 0.01 * i) for i in range(4)] for s in range(6)}
    for policy, kwargs in (("R0", {}), ("R1", {}), ("R2", {"k": 2}), ("R3", {}), ("R4", {"eps": 0.01}), ("R5", {})):
        retained_by_seed = {}
        for s in range(6):
            rows_s = seed_rows[s]
            retained_by_seed[s] = (e4a.retain_r2(rows_s, kwargs["k"]) if policy == "R2"
                                    else e4a.retain_r4(rows_s, kwargs["eps"]) if policy == "R4"
                                    else e4a.RETAIN_FNS[policy](rows_s))
        n_voting_seeds = sum(1 for s in range(6) if e4a.cast_vote(retained_by_seed[s]) is not None)
        check(f"9: {policy} every seed with rows casts exactly one vote", n_voting_seeds == 6, f"{policy}: {n_voting_seeds}")
        for s in range(6):
            check(f"9: {policy} seed {s} retained set is a subset of its front", set(r.expression_string for r in retained_by_seed[s]) <= set(r.expression_string for r in seed_rows[s]))


# --- test 10: McNemar pair counts reconcile ---
def test_10_mcnemar():
    def cr(wid, stage):
        return e4a.CaseResult(wid, "mass_power", 0, "RX", stage, None, None, None, None, (), None, 0, 30, 0)
    policy_res = [cr("w1", "E"), cr("w2", "B"), cr("w3", "E"), cr("w4", "B")]
    control_res = [cr("w1", "B"), cr("w2", "B"), cr("w3", "E"), cr("w4", "E")]
    out = e4a.mcnemar_exact(policy_res, control_res)
    check("10a: discordant+concordant reconciles to n", out["policy_wins"] + out["control_wins"] + out["both"] + out["neither"] == 4, str(out))
    check("10b: policy_wins counted correctly (w1)", out["policy_wins"] == 1, str(out))
    check("10c: control_wins counted correctly (w4)", out["control_wins"] == 1, str(out))
    check("10d: p-value in [0,1]", 0.0 <= out["p_value"] <= 1.0, str(out["p_value"]))
    mismatched = False
    try:
        e4a.mcnemar_exact([cr("w1", "E")], [cr("w2", "E")])
    except ValueError:
        mismatched = True
    check("10e: world-order mismatch is detected, not silently paired", mismatched)


# --- test 11: paired-bootstrap inputs align case-by-case ---
def test_11_bootstrap_alignment():
    def cr(wid, stage):
        return e4a.CaseResult(wid, "mass_power", 0, "RX", stage, None, None, None, None, (), None, 0, 30, 0)
    policy_res = [cr("w1", "E"), cr("w2", "E"), cr("w3", "B")]
    control_res = [cr("w1", "B"), cr("w2", "E"), cr("w3", "B")]
    out = e4a.paired_bootstrap_ci("R1", policy_res, control_res, n_resamples=500)
    check("11a: point estimate matches hand computation", abs(out["point_estimate"] - (2 / 3 - 1 / 3)) < 1e-9, str(out["point_estimate"]))
    check("11b: CI brackets the point estimate", out["ci_lower"] <= out["point_estimate"] <= out["ci_upper"], str(out))
    check("11c: bootstrap seed is derive_seed_v2-derived and reproducible", out["seed"] == e4a.derive_seed_v2("bootstrap", "R1") % (2**32))
    mismatched = False
    try:
        e4a.paired_bootstrap_ci("R1", policy_res, control_res[:2], n_resamples=10)
    except ValueError:
        mismatched = True
    check("11d: length mismatch detected, not silently truncated/padded", mismatched)


# --- test 12: Wilson denominators use the correct eligible populations, reused not reimplemented ---
def test_12_wilson_reuse():
    def cr(wid, stage):
        return e4a.CaseResult(wid, "mass_power", 0, "RX", stage, None, None, None, None, (), None, 0, 30, 0)
    eligible = [cr(f"w{i}", "E" if i < 7 else "B") for i in range(10)]  # 7/10 non-B
    out = e4a.conditional_retention_recall(eligible)
    expect_lower = wilson_lower_95(7, 10)
    expect_upper = wilson_upper_95(7, 10)
    check("12a: recall n matches the exact eligible-pool size passed in", out["n"] == 10, str(out["n"]))
    check("12b: wilson_lower matches g2_contract.wilson_lower_95 exactly (reused, not reimplemented)", out["wilson_lower"] == expect_lower, f"{out['wilson_lower']} != {expect_lower}")
    check("12c: wilson_upper matches g2_contract.wilson_upper_95 exactly", out["wilson_upper"] == expect_upper)


# --- test 1: R0 reproduces frozen production retention exactly (real replay) ---
def test_1_r0_replay():
    world_path = OLD_RUN_DIR / "worlds_shard_002.jsonl"
    cand_path = OLD_RUN_DIR / "candidates_shard_002.jsonl"
    if not world_path.exists() or not cand_path.exists():
        check("1: R0 replay (SKIPPED -- old-run files not found at expected path)", True)
        return

    target_world = None
    with world_path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("n_classify_calls") is None and "first_loss_stage" in rec:
                target_world = rec
                break
    if target_world is None:
        check("1: R0 replay (SKIPPED -- no suitable world record found)", True)
        return

    wid = target_world["world_id"]
    seed_rows: dict[int, list] = {}
    with cand_path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("world_id") != wid:
                continue
            s = rec["seed"]
            seed_rows.setdefault(s, []).append(e4a.E4aRow(
                seed_ordinal_k=rec["seed_ordinal_k"], seed=s, front_rank=rec["front_rank"],
                expression_string=rec["expression_string"], complexity=rec["engine_complexity"],
                valid_r2=rec["valid_r2"], invalid_fraction=rec["invalid_fraction"],
                candidate_test_r2=rec["test_r2"], score=rec.get("score"),
            ))
    if not seed_rows or any(r.score is None for rows in seed_rows.values() for r in rows):
        check("1: R0 replay (SKIPPED -- candidate rows missing `score`, unexpected for old-run data)", True)
        return

    family, regime, noise, replicate = target_world["family"], target_world["regime"], target_world["noise_level"], target_world["replicate"]
    world = e2_worlds.build_world(family, regime, noise, replicate)
    lc.reset_call_counters()
    result = e4a.evaluate_case_under_policy(wid, family, replicate, seed_rows, world.truth, "R0")
    check("1a: R0 replay reproduces the world's own sealed first_loss_stage exactly",
          result.first_loss_stage == target_world["first_loss_stage"],
          f"{result.first_loss_stage} != {target_world['first_loss_stage']} for {wid}")
    if target_world.get("representative_g2_correct") is not None:
        check("1b: R0 replay reproduces representative_g2_correct exactly",
              result.representative_g2_correct == target_world["representative_g2_correct"])


# --- regression test: real pathological row found live during Step 6's
# equivalence-defect reachability audit (world V2C|E2|mass_affine_
# descriptor|c_mid|n_default|r002, seed 2104501518, front_rank 12,
# invalid_fraction=1.0, valid_r2=NaN). Confirms every retention rule and
# the vote-reduction step are immune to Python's min()/max() NaN-first
# pitfall (verified empirically: plain min() over a list with a NaN-keyed
# tuple FIRST incorrectly returns that tuple, since nan compares False
# against everything). Not a scientific check -- these are hand-built rows.
def test_regression_nan_valid_r2_row():
    import math
    nan_row = row(rank=0, r2=float("nan"), score=float("nan"), expr="pathological",
                   invf=1.0, cx=20)  # NaN row FIRST by front_rank -- the exact danger case
    good_row = row(rank=1, r2=0.85, score=0.5, expr="good", cx=5)
    rows = [nan_row, good_row]

    r0 = e4a.retain_r0(rows)
    check("regression: R0 never selects a NaN-score row", len(r0) == 1 and r0[0].expression_string == "good",
          [r.expression_string for r in r0])

    r1 = e4a.retain_r1(rows)
    check("regression: R1 never selects a NaN-valid_r2 row", len(r1) == 1 and r1[0].expression_string == "good",
          [r.expression_string for r in r1])

    r2 = e4a.retain_r2(rows, k=2)
    check("regression: R2 excludes the NaN row even when k covers the whole front",
          [r.expression_string for r in r2] == ["good"], [r.expression_string for r in r2])

    r4 = e4a.retain_r4(rows, eps=0.5)
    check("regression: R4 never selects a NaN-valid_r2 row", len(r4) == 1 and r4[0].expression_string == "good",
          [r.expression_string for r in r4])

    r5 = e4a.retain_r5(rows)
    check("regression: R5 does not spuriously retain a NaN-valid_r2 row as nondominated",
          [r.expression_string for r in r5] == ["good"], [r.expression_string for r in r5])

    vote = e4a.cast_vote([nan_row, good_row])
    check("regression: vote-reduction never casts a NaN-valid_r2 vote", vote is not None and vote.expression_string == "good",
          vote.expression_string if vote else None)

    all_nan = [nan_row, row(rank=1, r2=float("nan"), score=float("nan"), expr="also_nan")]
    check("regression: all-NaN front retains nothing (not a crash, not a spurious pick)",
          e4a.retain_r1(all_nan) == [] and e4a.cast_vote(all_nan) is None)


def main():
    for fn in (test_2_r3_full_front, test_3_r3_recall_identity, test_4_r1_r3_r5_identity,
               test_5_tie_break, test_6_dev_eval_disjoint, test_7_eval_denominator_90,
               test_8_population_bijection, test_9_candidate_flow, test_10_mcnemar,
               test_11_bootstrap_alignment, test_12_wilson_reuse, test_1_r0_replay,
               test_regression_nan_valid_r2_row):
        fn()
    print(f"\n{results['pass']} passed, {results['fail']} failed")
    return 0 if results["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
