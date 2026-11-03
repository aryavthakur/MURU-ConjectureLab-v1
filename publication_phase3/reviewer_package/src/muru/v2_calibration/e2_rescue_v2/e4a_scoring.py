"""E2 rescue v2 / Step 4: the E4a retention-policy scoring implementation.

Builds exactly what `MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`
(`f4c1105`) specifies, plus `MURU_V2_E4A_RESULTS_BLIND_AMENDMENT_V1.md`'s
three corrections, and nothing else. Every scientific primitive is reused,
not reimplemented:

    e2_classify.classify_expression / g2_contract.classify_support,
    classify_family_match, evaluate_g2_event / discovery.equivalence.
    algebraically_equivalent           -- via lazy_classify's own thin
                                           wrappers (`_classify`,
                                           `_g2_correct`, `_truth_equivalent`),
                                           themselves a decomposition of
                                           `e2_scoring.score_row` at its own
                                           seam, not a new formula.
    rc5_selection.group_and_select      -- cross-seed grouping, held fixed
                                           across every arm (Control 3).
    identity_contract.template_key      -- R6's cross-seed recurrence check.
    structural_acceptance.STABILITY_GATE/STABILITY_DENOMINATOR (20/30)
                                        -- cross_seed_stability's gate,
                                           imported not restated.
    g2_contract.wilson_lower_95/wilson_upper_95
                                        -- every proportion interval.
    e2_worlds.derive_seed_v2            -- the frozen bootstrap seed
                                           construction (section 8).

Only genuinely new code: the R0-R6 within-seed retention rules (section 5),
the shared vote-reduction rule (section 5's boxed paragraph, tie-broken per
the amendment), the per-policy A-E recomputation (section 2, mechanically
reusing `e2_aggregate.evaluate_world`'s own decision sequence), the 9
required metrics (section 7), McNemar and the paired bootstrap (section 8),
and the Dev/Eval split (section 6). No PySR run, no Julia call, no new
search -- every function here operates on already-persisted front rows.

**Known, disclosed data-completeness gap** (found while writing this, not
assumed): Rescue-v2's `raw_search.RawFrontRow` schema (introduced by this
same rescue, `src/muru/v2_calibration/e2_rescue_v2/raw_search.py`) does not
capture PySR's native `score` column -- only `complexity`, `valid_r2`,
`invalid_fraction`, `candidate_test_r2`, and `retained_by_argmax_score`
(which already encodes *whether* a row is the argmax-by-score winner,
without the row's own score value). R0 needs only the boolean flag (already
present) and is unaffected. **R1, R3, R4, R5 need only `valid_r2`/
`complexity` and are unaffected.** **R2 and R6 rank rows *by score* and
raise `InsufficientRowData` rather than silently substituting or guessing
whenever any row in their input lacks it** -- this affects every
Rescue-v2-sourced world (as opposed to the old run's full
`e2_search.FrontRow` schema, which does carry `score`) until a disclosed,
not-yet-applied schema fix (add `score` to `RawFrontRow`, re-search
affected worlds) is separately authorized. This gap is reported here, in
`MURU_V2_E4A_PREREQUISITE_VERIFICATION.md`, and in the Step 8 gate check --
`raw_search.py` was deliberately NOT edited mid-migration to avoid an
unreviewed change to a component 4 live production shards are currently
importing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from muru.paper_benchmark.calibration_contract import SeedStatus
from muru.paper_benchmark.g2_contract import wilson_lower_95, wilson_upper_95
from muru.paper_benchmark.identity_contract import parse_candidate as identity_parse_candidate, template_key
from muru.paper_benchmark.rc5_selection import (
    RetainedCandidate,
    SeedSelection,
    group_and_select,
    parse_production_candidate,
)
from muru.paper_benchmark.structural_acceptance import STABILITY_DENOMINATOR, STABILITY_GATE

from muru.v2_calibration.e2_rescue_v2.lazy_classify import _classify, _g2_correct, _truth_equivalent
from muru.v2_calibration.e2_worlds import WorldTruth, derive_seed_v2

__all__ = [
    "E4aRow", "InsufficientRowData", "POLICIES", "DEV_REPLICATES",
    "retain_r0", "retain_r1", "retain_r2", "retain_r3", "retain_r4", "retain_r5", "retain_r6",
    "cast_vote", "evaluate_case_under_policy", "CaseResult",
    "conditional_retention_recall", "false_structure_rate_proxy", "candidate_set_size",
    "complexity_burden", "cross_seed_stability", "family_performance", "final_downstream_recovery",
    "mcnemar_exact", "paired_bootstrap_ci", "dev_eval_split",
    "EVAL_DENOM_MASS_POWER",
]

# --- Amendment v1.0.0 Correction 1 ---
EVAL_DENOM_MASS_POWER = 90  # 9 (family x regime x noise) cells x 10 EVAL replicates/cell

# --- section 6 ---
DEV_REPLICATES = frozenset({0, 1})       # V2C_RET_DEV
# V2C_RET_EVAL = replicate in {2..11}, i.e. everything not in DEV_REPLICATES

POLICIES = ("R0", "R1", "R2", "R3", "R4", "R5", "R6")


@dataclass(frozen=True)
class E4aRow:
    """One front row, source-agnostic (old-run `e2_search.FrontRow` or
    Rescue-v2 `raw_search.RawFrontRow`). `score` is Optional -- see module
    docstring's disclosed gap."""

    seed_ordinal_k: int
    seed: int
    front_rank: int
    expression_string: str
    complexity: int
    valid_r2: float
    invalid_fraction: float
    candidate_test_r2: float
    score: Optional[float]


class InsufficientRowData(Exception):
    """Raised by a policy that needs a field (currently only `score`) a
    row's source did not capture. Never silently substituted or guessed --
    see module docstring."""


# --------------------------------------------------------------------------
# section 5: within-seed retention rules
# --------------------------------------------------------------------------

def _require_score(rows: Sequence[E4aRow], policy: str) -> None:
    if any(r.score is None for r in rows):
        raise InsufficientRowData(
            f"{policy} ranks rows by `score`, which is not available for every row in this seed's "
            "front (Rescue-v2-sourced row missing the PySR-native score column -- see module docstring)"
        )


def _is_finite(x: Optional[float]) -> bool:
    return x is not None and not math.isnan(x)


def _finite_by(rows: Sequence[E4aRow], field: str) -> list[E4aRow]:
    """Excludes rows whose ranking field is NaN (or None) from RETENTION
    RANKING consideration -- found live while auditing the real corpus for
    Step 6 (see MURU_V2_E4A_EQUIVALENCE_REACHABILITY_AUDIT.md): one real
    persisted row has `valid_r2 = NaN` (invalid_fraction = 1.0, an
    everywhere-invalid candidate). Production's own `rc5_selection.
    select_row_label` is safe against this by construction --
    `equations["score"].idxmax()` is pandas' own aggregation, which skips
    NaN by default -- but plain Python `min()`/`max()` on a tuple key
    containing NaN do NOT skip it: `nan` compares False against everything
    (`<`, `>`, `==`), so if a NaN-keyed row is the FIRST element `min()`/
    `max()` examines, every later, genuinely-better row loses the `<`
    comparison against it and the NaN row is incorrectly returned (verified
    empirically: `min([(-nan,12),(-0.5,0),(-0.9,1)])` returns the NaN
    tuple). This filters NaN out BEFORE ranking, for every policy, so no
    retention or vote-reduction rule can ever select an undefined-accuracy
    row -- under any reading of "argmax", a row whose accuracy is
    literally undefined cannot be the argmax. This does not touch
    `correct_on_front`/`retained_correct`, which depend only on the
    expression's own G2 classification, never on `valid_r2`/`score`."""
    return [r for r in rows if _is_finite(getattr(r, field))]


def retain_r0(rows: Sequence[E4aRow]) -> list[E4aRow]:
    """Control. `argmax(score)`. Ties broken by lowest front_rank (first
    occurrence in front order), matching `rc5_selection.select_row_label`'s
    own `equations["score"].idxmax()` -- see the amendment's tie-break
    section."""
    if not rows:
        return []
    _require_score(rows, "R0")
    finite = _finite_by(rows, "score")
    if not finite:
        return []
    return [min(finite, key=lambda r: (-r.score, r.front_rank))]


def retain_r1(rows: Sequence[E4aRow]) -> list[E4aRow]:
    """`argmax(valid_r2)`, 0 free params."""
    finite = _finite_by(rows, "valid_r2")
    if not finite:
        return []
    return [min(finite, key=lambda r: (-r.valid_r2, r.front_rank))]


def retain_r2(rows: Sequence[E4aRow], k: int) -> list[E4aRow]:
    """Top-`k` rows by `score`. `k=1` degenerates to R0 by construction."""
    if not rows:
        return []
    _require_score(rows, "R2")
    finite = _finite_by(rows, "score")
    ranked = sorted(finite, key=lambda r: (-r.score, r.front_rank))
    return ranked[:k]


def retain_r3(rows: Sequence[E4aRow]) -> list[E4aRow]:
    """Oracle/control. Whole front. Not adoption-eligible (section 5.1).
    Unlike every other arm, R3 does NOT filter NaN rows -- it retains the
    front verbatim, by definition (a NaN-`valid_r2` row still cannot win
    the vote-reduction step, which does its own finite filtering)."""
    return list(rows)


def retain_r4(rows: Sequence[E4aRow], eps: float) -> list[E4aRow]:
    """Among rows with `valid_r2 >= max(valid_r2) - eps`, keep the
    lowest-complexity row (ties broken by lowest front_rank -- no
    complexity tie-break is stated in the frozen text either, so the same
    amendment convention applies uniformly)."""
    finite = _finite_by(rows, "valid_r2")
    if not finite:
        return []
    max_r2 = max(r.valid_r2 for r in finite)
    band = [r for r in finite if r.valid_r2 >= max_r2 - eps]
    return [min(band, key=lambda r: (r.complexity, r.front_rank))]


def _dominates(a: E4aRow, b: E4aRow) -> bool:
    """`a` dominates `b` in (valid_r2, -complexity): a.valid_r2 >= b.valid_r2
    AND a.complexity <= b.complexity, with at least one strict."""
    ge_r2 = a.valid_r2 >= b.valid_r2
    le_cx = a.complexity <= b.complexity
    strict = (a.valid_r2 > b.valid_r2) or (a.complexity < b.complexity)
    return ge_r2 and le_cx and strict


def retain_r5(rows: Sequence[E4aRow]) -> list[E4aRow]:
    """Pareto-nondominated subset in `(valid_r2, -complexity)`. A NaN-
    `valid_r2` row would otherwise survive as spuriously "nondominated"
    (every `>=` comparison against NaN is False, so nothing can be proven
    to dominate it) -- excluded up front for the same reason `_finite_by`
    exists everywhere else."""
    finite = _finite_by(rows, "valid_r2")
    return [r for r in finite if not any(_dominates(other, r) for other in finite if other is not r)]


def retain_r6(rows: Sequence[E4aRow], other_seeds_top3_keys: Sequence[frozenset]) -> list[E4aRow]:
    """Top-3 by `score`, further restricted to rows whose `template_key`
    recurs in the top-3 of at least 2 of the other 29 seeds. Constants
    frozen directly (section 5.2), not Development-tuned.
    `other_seeds_top3_keys`: one frozenset of template_keys per OTHER seed
    (29 entries for a full case), precomputed by the caller (section 5.2's
    two knobs, 3 and 2, are hard-coded here, matching the frozen text)."""
    if not rows:
        return []
    _require_score(rows, "R6")
    finite = _finite_by(rows, "score")
    top3 = sorted(finite, key=lambda r: (-r.score, r.front_rank))[:3]
    kept = []
    for r in top3:
        key = template_key(identity_parse_candidate(r.expression_string))
        recurrence = sum(1 for keys in other_seeds_top3_keys if key in keys)
        if recurrence >= 2:
            kept.append(r)
    return kept


RETAIN_FNS: dict[str, Callable[..., list[E4aRow]]] = {
    "R0": retain_r0, "R1": retain_r1, "R2": retain_r2, "R3": retain_r3,
    "R4": retain_r4, "R5": retain_r5, "R6": retain_r6,
}


# --------------------------------------------------------------------------
# section 5's boxed vote-reduction rule -- identical for every arm
# --------------------------------------------------------------------------

def cast_vote(retained_rows: Sequence[E4aRow]) -> Optional[E4aRow]:
    """`argmax(valid_r2)` among the seed's own retained set, ties broken by
    lowest front_rank (amendment's tie-break section). NaN-`valid_r2` rows
    are excluded from the vote for the same reason `_finite_by` exists
    (see its docstring) -- most policies already filter these at retention
    time, but R3 deliberately does not, so the vote step must guard here
    too."""
    finite = _finite_by(retained_rows, "valid_r2")
    if not finite:
        return None
    return min(finite, key=lambda r: (-r.valid_r2, r.front_rank))


# --------------------------------------------------------------------------
# per-case, per-policy A-E recomputation (section 2)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class CaseResult:
    world_id: str
    family: str
    replicate: int
    policy: str
    first_loss_stage: str                          # A|B|C|D|E, IDENTICAL decision sequence to evaluate_world
    representative_g2_correct: Optional[bool]
    representative_truth_equivalent: Optional[bool]
    representative_expression: Optional[str]
    representative_discovered_family: Optional[str]  # metric 2's own basis -- family only, not full g2_correct
    candidate_set_sizes_per_seed: tuple[int, ...]   # retained-row count per voting seed
    representative_complexity: Optional[int]
    selection_count: int
    selection_denominator: int
    n_classify_calls: int


def evaluate_case_under_policy(
    world_id: str, family: str, replicate: int,
    seed_rows: dict[int, Sequence[E4aRow]],
    truth: WorldTruth,
    policy: str,
    policy_kwarg: Optional[dict] = None,
) -> CaseResult:
    """Recomputes stages A-E for ONE policy against the frozen front,
    section 2's decision sequence, reusing the exact stage-A/B distinction
    lazy_classify.py already proves is policy-invariant-safe to short-
    circuit on (stage A never depends on retention). This function does
    classify MORE rows than lazy_classify's own minimal-witness order where
    a policy retains a set larger than one row (necessarily -- `retained_
    correct(seed)` for a multi-row policy means "a correct row exists
    ANYWHERE in the retained set," not just at the vote winner, so every
    retained row must be classified, not only the winner)."""
    policy_kwarg = policy_kwarg or {}
    n_calls_before = _call_count()

    ordered_seeds = sorted(seed_rows.keys())
    retained_by_seed: dict[int, list[E4aRow]] = {}
    for seed in ordered_seeds:
        rows = list(seed_rows[seed])
        if not rows:
            retained_by_seed[seed] = []
            continue
        if policy == "R2":
            retained_by_seed[seed] = retain_r2(rows, policy_kwarg["k"])
        elif policy == "R4":
            retained_by_seed[seed] = retain_r4(rows, policy_kwarg["eps"])
        elif policy == "R6":
            retained_by_seed[seed] = retain_r6(rows, policy_kwarg["other_seeds_top3_keys"][seed])
        else:
            retained_by_seed[seed] = RETAIN_FNS[policy](rows)

    # correct_on_front(seed) is policy-invariant (section 2): true iff ANY
    # row anywhere on that seed's front is g2_correct.
    correct_on_front_by_seed: dict[int, bool] = {}
    retained_correct_by_seed: dict[int, bool] = {}
    for seed in ordered_seeds:
        rows = list(seed_rows[seed])
        retained = retained_by_seed[seed]
        retained_exprs = {r.expression_string for r in retained}
        any_correct_on_front = False
        any_retained_correct = False
        for r in rows:
            classification = _classify(r.expression_string)
            g2 = _g2_correct(classification, truth)
            if g2:
                any_correct_on_front = True
                if r.expression_string in retained_exprs:
                    any_retained_correct = True
        correct_on_front_by_seed[seed] = any_correct_on_front
        retained_correct_by_seed[seed] = any_retained_correct

    n_correct_on_front = sum(correct_on_front_by_seed.values())
    n_retained_correct = sum(retained_correct_by_seed.values())

    # Vote reduction + cross-seed grouping (Control 3: identical rule/function for every arm).
    selections: list[SeedSelection] = []
    for seed in ordered_seeds:
        vote = cast_vote(retained_by_seed[seed])
        if vote is None:
            selections.append(SeedSelection(k=seed, seed=seed, status=SeedStatus.COMPLETED_NO_CANDIDATE, candidate=None))
            continue
        selections.append(SeedSelection(
            k=vote.seed_ordinal_k, seed=seed, status=SeedStatus.COMPLETED_WITH_CANDIDATES,
            candidate=RetainedCandidate(
                k=vote.seed_ordinal_k, seed=seed, expression_string=vote.expression_string,
                complexity=vote.complexity, valid_r2=vote.valid_r2,
                invalid_fraction=vote.invalid_fraction, candidate_test_r2=vote.candidate_test_r2,
            ),
        ))
    cross = group_and_select(selections)

    rep_g2: Optional[bool] = None
    rep_equiv: Optional[bool] = None
    rep_expr: Optional[str] = None
    rep_complexity: Optional[int] = None
    rep_family: Optional[str] = None
    if cross.representative is not None:
        rep_expr = cross.representative.expression_string
        rep_complexity = cross.representative.complexity
        classification = _classify(rep_expr)
        rep_family = classification.discovered_family
        rep_g2 = _g2_correct(classification, truth)
        if not rep_g2:
            rep_equiv = _truth_equivalent(rep_expr, classification, truth)

    # section 2's decision sequence, verbatim.
    if n_correct_on_front == 0:
        stage = "A"
    elif n_retained_correct == 0:
        stage = "B"
    elif rep_g2:
        stage = "E"
    elif rep_equiv:
        stage = "D"
    else:
        stage = "C"

    sizes = tuple(len(retained_by_seed[s]) for s in ordered_seeds if seed_rows[s])
    return CaseResult(
        world_id=world_id, family=family, replicate=replicate, policy=policy,
        first_loss_stage=stage, representative_g2_correct=rep_g2,
        representative_truth_equivalent=rep_equiv, representative_expression=rep_expr,
        representative_discovered_family=rep_family,
        candidate_set_sizes_per_seed=sizes, representative_complexity=rep_complexity,
        selection_count=cross.selection_count, selection_denominator=cross.selection_denominator,
        n_classify_calls=_call_count() - n_calls_before,
    )


def _call_count() -> int:
    from muru.v2_calibration.e2_rescue_v2 import lazy_classify as _lc
    return _lc.call_counters()["classify"]


# --------------------------------------------------------------------------
# section 6: Dev/Eval split
# --------------------------------------------------------------------------

def dev_eval_split(replicate: int) -> str:
    return "DEV" if replicate in DEV_REPLICATES else "EVAL"


# --------------------------------------------------------------------------
# section 7: required metrics (each takes a list[CaseResult] for ONE policy,
# already restricted to the desired split -- caller's responsibility, kept
# separate from these pure functions so DEV/EVAL scoping is never implicit)
# --------------------------------------------------------------------------

def conditional_retention_recall(results: Sequence[CaseResult], policy: Optional[str] = None) -> dict:
    """Section 3's formula. `results` must already be restricted to the
    eligible pool (stage != A) for the correct denominator.

    Amendment v1.0.0 Correction 2: when `policy == "R3"`, this is an
    IDENTITY (1.0, exactly, no sampling variation -- R3 retains the whole
    front, so every eligible-pool case's already-known correct row is
    trivially retained), not a sample proportion -- no Wilson interval is
    attached, and the empirical count is reported alongside only as a
    byte-identity CONTROL check (it must equal `n` exactly; anything else
    is an implementation defect, not a finding -- see Step 5 test 3)."""
    n = len(results)
    if n == 0:
        return {"recall": float("nan"), "n": 0, "successes": 0, "wilson_lower": float("nan"), "wilson_upper": float("nan")}
    successes = sum(1 for r in results if r.first_loss_stage != "B")
    if policy == "R3":
        if successes != n:
            raise AssertionError(
                f"R3 conditional_retention_recall control violated: {successes}/{n} -- "
                "R3 must retain every eligible-pool case's correct row by construction; "
                "this is an implementation defect (see Amendment v1.0.0 Correction 2), not a finding"
            )
        return {"recall": 1.0, "n": n, "successes": successes, "is_identity": True,
                "wilson_lower": None, "wilson_upper": None}
    return {
        "recall": successes / n, "n": n, "successes": successes, "is_identity": False,
        "wilson_lower": wilson_lower_95(successes, n), "wilson_upper": wilson_upper_95(successes, n),
    }


def false_structure_rate_proxy(mass_power_eval_results: Sequence[CaseResult]) -> dict:
    """Metric 2, verbatim: "fraction whose cross-seed representative under P
    is not mass_power" -- a FAMILY-only check (`representative_discovered_
    family != "mass_power"`), not the fuller `g2_correct` (which also
    requires support match). Applied to every case with a representative
    (stages C/D/E always have one; A/B structurally have one too whenever
    any seed cast a vote, since the cross-seed vote is computed before the
    A-E decision looks at it) -- a case with NO representative at all
    (nothing ever voted) cannot meaningfully be "not mass_power" and is
    excluded from both numerator and denominator, not counted as spurious
    by default. `mass_power_eval_results` must be exactly the mass_power-
    truth cases restricted to V2C_RET_EVAL (n should equal
    EVAL_DENOM_MASS_POWER=90 under Amendment v1.0.0 Correction 1 -- the
    caller is responsible for that restriction; this function does not
    invent or re-derive the mass_power subset itself)."""
    with_rep = [r for r in mass_power_eval_results if r.representative_expression is not None]
    n = len(with_rep)
    if n == 0:
        return {"rate": float("nan"), "n": 0, "successes": 0, "wilson_lower": float("nan"), "wilson_upper": float("nan")}
    spurious = sum(1 for r in with_rep if r.representative_discovered_family != "mass_power")
    return {
        "rate": spurious / n, "n": n, "successes": spurious,
        "wilson_lower": wilson_lower_95(spurious, n), "wilson_upper": wilson_upper_95(spurious, n),
    }


def candidate_set_size(results: Sequence[CaseResult]) -> dict:
    sizes = [s for r in results for s in r.candidate_set_sizes_per_seed]
    if not sizes:
        return {"mean": float("nan"), "median": float("nan"), "n": 0}
    sizes_sorted = sorted(sizes)
    mid = len(sizes_sorted) // 2
    median = sizes_sorted[mid] if len(sizes_sorted) % 2 else (sizes_sorted[mid - 1] + sizes_sorted[mid]) / 2
    return {"mean": sum(sizes) / len(sizes), "median": median, "n": len(sizes)}


def complexity_burden(results: Sequence[CaseResult]) -> dict:
    reps = [r.representative_complexity for r in results if r.representative_complexity is not None]
    if not reps:
        return {"mean_representative_complexity": float("nan"), "median_representative_complexity": float("nan"), "n": 0}
    reps_sorted = sorted(reps)
    mid = len(reps_sorted) // 2
    median = reps_sorted[mid] if len(reps_sorted) % 2 else (reps_sorted[mid - 1] + reps_sorted[mid]) / 2
    return {"mean_representative_complexity": sum(reps) / len(reps), "median_representative_complexity": median, "n": len(reps)}


def cross_seed_stability(results: Sequence[CaseResult]) -> dict:
    """Fraction of eligible-pool cases clearing STABILITY_GATE/STABILITY_DENOMINATOR
    (20/30), imported not restated."""
    n = len(results)
    if n == 0:
        return {"fraction_clearing_gate": float("nan"), "n": 0, "gate": f"{STABILITY_GATE}/{STABILITY_DENOMINATOR}"}
    clearing = sum(1 for r in results if r.selection_denominator > 0
                   and (r.selection_count / r.selection_denominator) >= (STABILITY_GATE / STABILITY_DENOMINATOR))
    return {"fraction_clearing_gate": clearing / n, "n": n, "gate": f"{STABILITY_GATE}/{STABILITY_DENOMINATOR}"}


def family_performance(results: Sequence[CaseResult], policy: Optional[str] = None) -> dict:
    by_family: dict[str, list[CaseResult]] = {}
    for r in results:
        by_family.setdefault(r.family, []).append(r)
    out = {}
    for fam, rs in by_family.items():
        eligible = [r for r in rs if r.first_loss_stage != "A"]
        out[fam] = {
            "conditional_retention_recall": conditional_retention_recall(eligible, policy=policy),
            "e_stage_rate": (sum(1 for r in rs if r.first_loss_stage == "E") / len(rs)) if rs else float("nan"),
            "n_cases": len(rs),
        }
    return out


def worst_family_performance(family_perf: dict) -> tuple[Optional[str], float]:
    worst_family, worst_recall = None, float("inf")
    for fam, d in family_perf.items():
        recall = d["conditional_retention_recall"]["recall"]
        if not math.isnan(recall) and recall < worst_recall:
            worst_family, worst_recall = fam, recall
    return worst_family, (worst_recall if worst_family is not None else float("nan"))


def final_downstream_recovery(results: Sequence[CaseResult]) -> dict:
    """Fraction of ELIGIBLE-POOL cases (stage != A) reaching stage E."""
    eligible = [r for r in results if r.first_loss_stage != "A"]
    n = len(eligible)
    if n == 0:
        return {"rate": float("nan"), "n": 0, "successes": 0}
    successes = sum(1 for r in eligible if r.first_loss_stage == "E")
    return {"rate": successes / n, "n": n, "successes": successes,
            "wilson_lower": wilson_lower_95(successes, n), "wilson_upper": wilson_upper_95(successes, n)}


# --------------------------------------------------------------------------
# section 8: statistical procedure
# --------------------------------------------------------------------------

def mcnemar_exact(policy_results: Sequence[CaseResult], control_results: Sequence[CaseResult]) -> dict:
    """Exact McNemar on the discordant pairs of the binary "truth survives
    retention" (not-stage-B) indicator, paired case-by-case. Both sequences
    must be the SAME cases, same order, both already restricted to the
    eligible pool on V2C_RET_EVAL."""
    if len(policy_results) != len(control_results):
        raise ValueError("paired comparison requires identically-ordered, identically-sized case sequences")
    p_win = c_win = both = neither = 0
    for p, c in zip(policy_results, control_results):
        if p.world_id != c.world_id:
            raise ValueError(f"case-order mismatch: {p.world_id} vs {c.world_id}")
        p_ok = p.first_loss_stage != "B"
        c_ok = c.first_loss_stage != "B"
        if p_ok and c_ok:
            both += 1
        elif p_ok and not c_ok:
            p_win += 1
        elif c_ok and not p_ok:
            c_win += 1
        else:
            neither += 1
    n_discordant = p_win + c_win
    if n_discordant == 0:
        p_value = 1.0
    else:
        # exact two-sided binomial test of p_win among n_discordant, p=0.5
        p_value = _exact_binomial_two_sided(p_win, n_discordant, 0.5)
    return {"policy_wins": p_win, "control_wins": c_win, "both": both, "neither": neither,
            "n_discordant": n_discordant, "p_value": p_value}


def _log_comb(n: int, k: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def _binom_pmf(k: int, n: int, p: float) -> float:
    if p in (0.0, 1.0):
        return 1.0 if (k == n * p) else 0.0
    return math.exp(_log_comb(n, k) + k * math.log(p) + (n - k) * math.log(1 - p))


def _exact_binomial_two_sided(k: int, n: int, p: float) -> float:
    obs = _binom_pmf(k, n, p)
    total = 0.0
    for i in range(n + 1):
        pi = _binom_pmf(i, n, p)
        if pi <= obs * (1 + 1e-9):
            total += pi
    return min(1.0, total)


def paired_bootstrap_ci(
    policy_id: str,
    policy_results: Sequence[CaseResult], control_results: Sequence[CaseResult],
    n_resamples: int = 10_000,
) -> dict:
    """Case-level bootstrap 95% CI on the net difference (policy recall -
    control recall), resampling cases with replacement, seeded per section
    8's frozen construction: derive_seed_v2("bootstrap", "<policy_id>")."""
    if len(policy_results) != len(control_results):
        raise ValueError("paired comparison requires identically-sized case sequences")
    n = len(policy_results)
    if n == 0:
        return {"point_estimate": float("nan"), "ci_lower": float("nan"), "ci_upper": float("nan"), "n": 0}
    p_ok = [1 if r.first_loss_stage != "B" else 0 for r in policy_results]
    c_ok = [1 if r.first_loss_stage != "B" else 0 for r in control_results]
    point = sum(p_ok) / n - sum(c_ok) / n

    seed = derive_seed_v2("bootstrap", policy_id) % (2**32)
    import numpy as np
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_resamples)
    p_arr, c_arr = np.array(p_ok), np.array(c_ok)
    for b in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        diffs[b] = p_arr[idx].mean() - c_arr[idx].mean()
    lower = float(np.percentile(diffs, 2.5))
    upper = float(np.percentile(diffs, 97.5))
    return {"point_estimate": point, "ci_lower": lower, "ci_upper": upper, "n": n, "n_resamples": n_resamples, "seed": int(seed)}
