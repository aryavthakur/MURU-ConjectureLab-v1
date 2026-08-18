"""E2 rescue v2: exact early-locking of the frozen E4a routing gate.

This module NEVER changes the frozen gate itself. It only asks: given the
current partial E2a attribution counts and the number of worlds still
outstanding, can the gate's eventual verdict already be determined for
certain, no matter how the outstanding worlds resolve?

Authority for the gate being locked here:
    v2_design_reference/MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md
    section 4 ("Execution trigger (results-blind, mechanical)"), itself an
    executable restatement of
    v2_design_reference/MURU_V2_CAUSAL_DECISION_TREE.md section B.1, and
    v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md section 2.9.

The gate is a two-part sequential predicate:

  GATE 1 (falsification hook): needs E2b's direct measurement (Held-out
      replay, a *separate*, not-yet-run study, out of E2a's scope by the
      E2 predeclaration's own "Scope" paragraph). E2a completion, however
      complete, CANNOT resolve Gate 1. Reported as PENDING_E2B always.

  GATE 2 (retention-dominance over the E2a case counts), in this EXACT
      order (ties broken by falling through, matching the prereg verbatim):

        1. B > A  AND  B > C+D                    -> EXECUTE (RC3 confirmed)
        2. elif P_retain_given_front near 1
           wherever P_front is high (exoneration)  -> WITHDRAWN (RC3 withdrawn)
        3. elif A > B  AND  A > C+D                -> RC4 (E3-gated next)
        4. elif C+D > A  AND  C+D > B              -> RC7 (E4f licensed)
        5. else (tie / no strict plurality)        -> DIAGNOSTIC_ONLY

      Branch 2's condition is NOT a function of the four scalar case counts
      alone -- "near 1" and "wherever P_front is high" are never given a
      numeric epsilon or per-stratum threshold anywhere in the frozen
      source (grepped clean across the preregistration, its PROTOCOL.json,
      and the causal decision tree). See ROUTING_LOCK_THEORY.md section 3
      for the full derivation of what this means for locking: branches 3,
      4 and 5 can *never* be exactly locked from counts alone, because
      branch 2 is checked before all three of them and could always
      preempt. Only branch 1 (EXECUTE) is checked *before* the
      non-mechanical branch 2, so it is the only branch this module can
      lock with full rigor without a ratified numeric operationalization
      of branch 2.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LockState(str, Enum):
    UNLOCKED = "UNLOCKED"
    LOCKED_EXECUTE_E4A = "LOCKED_EXECUTE_E4A"          # Gate 2 branch 1, exact, unconditional on branch 2
    LOCKED_RC4 = "LOCKED_RC4"                          # only reachable if exoneration is ratified and ruled out
    LOCKED_RC7 = "LOCKED_RC7"                          # only reachable if exoneration is ratified and ruled out
    LOCKED_DIAGNOSTIC_ONLY = "LOCKED_DIAGNOSTIC_ONLY"  # only reachable if exoneration is ratified and ruled out
    FULL_RUN_REQUIRED = "FULL_RUN_REQUIRED"


@dataclass(frozen=True)
class ExonerationRatification:
    """A NOT-YET-RATIFIED numeric operationalization of Gate 2 branch 2.

    This dataclass exists so the parametrized inequalities below are
    mechanically expressible, NOT to silently decide the ambiguity. Until
    an operator explicitly constructs one of these (after a documented
    ratification decision -- see ROUTING_LOCK_THEORY.md section 3.4), no
    caller of `evaluate_gate2` may pass one, and branches 3/4/5 can only
    ever report FULL_RUN_REQUIRED.

    near_one_floor: the minimum P_retain_given_front, in the high-P_front
        stratum, that counts as "near 1".
    high_front_floor: the minimum per-stratum P_front that counts as
        "P_front is high" (defines which strata are even in scope for the
        exoneration check).
    """

    near_one_floor: float
    high_front_floor: float
    ratified_by: str
    ratified_on: str


@dataclass(frozen=True)
class Gate2Lock:
    state: LockState
    # Deliberately NOT included: A_n, B_n, C_n, D_n, or any per-branch
    # margin -- see module docstring and ROUTING_LOCK_THEORY.md section 5
    # ("operator-facing surface"). n_classified/r are completion-progress
    # counts, not outcome counts, and are safe to expose.
    n_classified: int
    r_remaining: int
    note: str


def _would_lock_bucket(x_n: int, y_n: int, z_n: int, r: int) -> bool:
    """Exact test: does X necessarily become the *unique* strict plurality
    of {X, Y, Z} over 540 cases, for every possible assignment of the r
    still-outstanding cases to X, Y, Z (or to a bucket outside the
    competition, e.g. E)?

    Derivation (ROUTING_LOCK_THEORY.md section 2 has the full proof):
    the worst case against X's plurality is r_X = 0 (nothing outstanding
    resolves to X) and, independently for each rival, r_rival = r
    (everything outstanding resolves to that one rival) -- because a
    rival's final count depends only on how much of r is assigned to IT,
    and assigning it all of r is what maximizes it. X's own final count is
    minimized at X_n (r_X = 0), which simultaneously is the worst case for
    both rival comparisons since X_final does not change with how the
    rivals split r between themselves. Hence:

        LOCK(X)  <=>  X_n > Y_n + r   AND   X_n > Z_n + r

    This is tight (necessary and sufficient), not merely sufficient: if
    X_n <= Y_n + r, the adversary can realize Y_final = Y_n + r >= X_n =
    X_final by routing all r outstanding cases to Y, which breaks X's
    plurality claim.
    """
    return (x_n > y_n + r) and (x_n > z_n + r)


def _bucket_can_ever_win(x_n: int, y_n: int, z_n: int, r: int) -> bool:
    """Exact test: does SOME assignment of the r outstanding cases exist
    under which X becomes the unique strict plurality? The most-favorable
    assignment to X is r_X = r, r_Y = r_Z = 0 (see `_would_lock_bucket`'s
    docstring for why this extreme, not some interior split, is always the
    binding case). Used only to prove the negative -- that NO bucket can
    ever win -- which is what licenses LOCKED_DIAGNOSTIC_ONLY.
    """
    x_final = x_n + r
    return (x_final > y_n) and (x_final > z_n)


def evaluate_gate2(
    a_n: int,
    b_n: int,
    c_n: int,
    d_n: int,
    r_remaining: int,
    exoneration: ExonerationRatification | None = None,
) -> Gate2Lock:
    """Evaluate the exact routing lock over Gate 2 given partial counts.

    `a_n, b_n, c_n, d_n` are the case counts already resolved to stages
    A/B/C/D (E is irrelevant to the competition and is not passed).
    `r_remaining` is the number of the 540 E2a cases with no stage yet
    (includes any quarantined-but-unresolved world, e.g. the poison world
    -- see PART_X notes -- since its eventual stage is exactly as unknown
    as any other outstanding world's, and must be treated as adversarially
    unknown, never assumed).

    Returns a `Gate2Lock` whose `state` is one of the five `LockState`
    values. Callers displaying this to an operator MUST show only
    `state`, `n_classified`, `r_remaining`, and `note` -- never the raw
    a_n/b_n/c_n/d_n arguments themselves (see `evaluate_gate2_opaque`).
    """
    if a_n < 0 or b_n < 0 or c_n < 0 or d_n < 0 or r_remaining < 0:
        raise ValueError("counts and remaining worlds must be non-negative")
    n_classified = a_n + b_n + c_n + d_n  # E cases also count toward n_classified but not toward this predicate's buckets
    cd_n = c_n + d_n

    # Branch 1 first, exactly as the frozen predicate orders it. This is
    # the ONE branch checkable before the non-mechanical branch 2, so it
    # needs no ratification.
    if _would_lock_bucket(b_n, a_n, cd_n, r_remaining):
        return Gate2Lock(
            state=LockState.LOCKED_EXECUTE_E4A,
            n_classified=n_classified,
            r_remaining=r_remaining,
            note=(
                "Gate 2 branch 1 (B strict plurality of {A,B,C+D}) is mathematically "
                "guaranteed regardless of the remaining worlds' outcomes. This locks "
                "Gate 2 only. Gate 1 (E2b falsification hook) is a separate, "
                "out-of-scope precondition for actually running E4a -- see PENDING_E2B."
            ),
        )

    # Branches 3/4/5 are each individually decidable by count arithmetic,
    # but ALL of them sit behind branch 2 in the frozen if/elif chain, and
    # branch 2's condition ("P_retain_given_front near 1 wherever P_front
    # is high") is not a function of a_n/b_n/c_n/d_n and has no ratified
    # numeric threshold in the frozen source. Locking any of 3/4/5 without
    # first ruling out branch 2 would silently substitute a count-only
    # approximation for the frozen gate -- exactly what this task forbids.
    if exoneration is None:
        return Gate2Lock(
            state=LockState.FULL_RUN_REQUIRED,
            n_classified=n_classified,
            r_remaining=r_remaining,
            note=(
                "Gate 2 branch 1 cannot be guaranteed from the current counts. "
                "Branches 3/4/5 are structurally unreachable as an EXACT lock without "
                "first ruling out branch 2 (the P_retain_given_front exoneration "
                "check), which has no ratified numeric threshold. FULL_RUN_REQUIRED "
                "for the routing component until either (a) B's plurality locks, or "
                "(b) all 540 E2a cases are classified and an analyst evaluates branch "
                "2 directly against complete, stratified data."
            ),
        )

    # A ratified operationalization was supplied. Even then, branch 2 is a
    # *stratified* (per family x regime x noise cell) statement about
    # P_front and P_retain_given_front, not reducible to the four pooled
    # scalars this function receives -- so this module still cannot decide
    # branch 2 itself. What it CAN do, once ratified thresholds exist, is
    # lock branches 3/4/5 IF AND ONLY IF the pooled counts make branch 2
    # structurally impossible regardless of the (unseen) per-stratum
    # detail -- see ROUTING_LOCK_THEORY.md section 3.4. This function
    # deliberately does not attempt that reduction; it is left
    # FULL_RUN_REQUIRED with the ratification acknowledged, pending the
    # dedicated per-stratum monitor described there.
    if _would_lock_bucket(a_n, b_n, cd_n, r_remaining) or \
       _would_lock_bucket(cd_n, a_n, b_n, r_remaining) or \
       not any(_bucket_can_ever_win(x_n, y_n, z_n, r_remaining) for x_n, y_n, z_n in (
           (a_n, b_n, cd_n), (b_n, a_n, cd_n), (cd_n, a_n, b_n),
       )):
        return Gate2Lock(
            state=LockState.FULL_RUN_REQUIRED,
            n_classified=n_classified,
            r_remaining=r_remaining,
            note=(
                f"Ratified exoneration threshold on file (by {exoneration.ratified_by}, "
                f"{exoneration.ratified_on}), but this pooled-counts monitor does not "
                "attempt the per-stratum reduction needed to rule branch 2 in or out "
                "early -- see ROUTING_LOCK_THEORY.md section 3.4. FULL_RUN_REQUIRED."
            ),
        )

    return Gate2Lock(
        state=LockState.FULL_RUN_REQUIRED,
        n_classified=n_classified,
        r_remaining=r_remaining,
        note="No lock condition met yet.",
    )


def evaluate_gate2_opaque(
    a_n: int, b_n: int, c_n: int, d_n: int, r_remaining: int,
    exoneration: ExonerationRatification | None = None,
) -> str:
    """Operator-facing entry point. Returns ONLY the state string -- never
    the counts. This is the one function a rolling-report tool should ever
    call while E2 is incomplete."""
    return evaluate_gate2(a_n, b_n, c_n, d_n, r_remaining, exoneration).state.value
