# MURU v2 E2 Computational Rescue V2 Protocol

**Status:** drafted contingent on the parity and speedup gates
(`MURU_V2_E2_REPLAY_PARITY.json`, `MURU_V2_E2_SPEED_BENCHMARK.json`)
passing -- see `MURU_V2_E2_RESCUE_V2_FEASIBILITY.md` for the gate
evaluation this protocol's adoption depends on. Version **v2.0.0** of the
E2 computational-rescue lineage (v1 = the 2026-08-16 classify-hang/
shard-death rescue, `E2_EXECUTION_DEVIATION.md`, rescue authority commit
`4892c76`).

## 1. What is unchanged (the scientific contract)

The following are declared frozen and are not modified, redefined, or
reinterpreted by this protocol, anywhere:

- **The scientific hypothesis** and the five truth families / three
  regimes / three noise levels / twelve replicates E2a design
  (`v2_design_reference/MURU_V2_E2_PREDECLARATION.md`).
- **The truth oracle** -- `e2_worlds.build_world`, `WorldTruth`
  construction, and the frozen `generator.py`-derived law/coefficient/noise
  rules. Not touched by a single line in this rescue.
- **Candidate-equivalence semantics** -- `discovery.equivalence.
  algebraically_equivalent`, `g2_contract.classify_support`/
  `classify_family_match`/`evaluate_g2_event`, `identity_contract.
  template_key`, and `rc5_selection.group_and_select`/`select_row_label`.
  Every one of these is imported and called unmodified everywhere in this
  rescue's new code (`lazy_classify.py`, `classify_cache.py`); none is
  reimplemented, approximated, or given a new tolerance.
- **First-loss definitions** -- the A-E taxonomy
  (`MURU_V2_E2_PREDECLARATION.md` section 6) and `e2_aggregate.
  evaluate_world`'s own decision sequence, reproduced (not altered) by
  `lazy_classify.py` -- see `MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md`
  section 2's theorem.
- **E2b** -- untouched, unexecuted, still out of scope for E2a, still
  `DECISION_INADMISSIBLE` for any v2 design decision.
- **The frozen E4a routing rule** -- Gate 1 (E2b falsification hook) and
  Gate 2 (retention-dominance plurality)
  (`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md` section 4). This
  rescue does not alter either gate's conditions; it only asks, exactly,
  when the eventual verdict is already certain
  (`MURU_V2_E2_ROUTING_LOCK_THEORY.md`).

## 2. What changes (computation and estimation design only)

Versioned individually so a future audit can cite exactly which change
licenses which speedup, per the mission's own requirement:

| # | Change | From | To | Module |
|---|---|---|---|---|
| 1 | Candidate classification order | Exhaustive: every front row of every seed classified inline during search | Lazy: minimum witness order (Theorem, `MURU_V2_E2_LAZY_CLASSIFICATION_SPEC.md` section 2), same classifier, applied only where the stage decision needs it | `lazy_classify.py` |
| 2 | Repeated classification across restarts/worlds | In-process-only memoization (`e2_classify._CACHE`, lost on every restart) | Source-hashed persistent cache (SQLite/WAL), survives restarts, shared across shards, additionally caches the previously-uncached `algebraically_equivalent` | `classify_cache.py` |
| 3 | Descriptive census | Full 540-world exhaustive census for first-loss rate estimates | Preregistered balanced design-based sample (r=6/n=270, derived threshold: <5% overall MOE at 95% CI, worst case), reusing already-completed worlds | `balanced_sample.py`, `MURU_V2_E2_BALANCED_SAMPLE_DESIGN.md` |
| 4 | Routing census | Full 540-world exhaustive census before the gate can be evaluated | Exact early-locking where mathematically possible (Gate 2 branch 1 only, proven tight); `FULL_RUN_REQUIRED` otherwise, never approximated | `routing_lock.py` |

**Not versioned as a change, because it changes nothing scientific:**
reusing already-completed worlds' persisted records as a replay corpus
(Part V) and prioritized-but-outcome-blind scheduling (Part IX) are
operational conveniences built entirely on top of changes 1-4, not
independent changes to any computation or estimate.

## 3. Two effective sample sizes, both explicit

Per the mission's own instruction, this protocol reports **two** distinct
`N`s and does not blend them:

- **N_GATE**: the number of E2a cases the routing-lock monitor has
  classified when (if) it reaches `LOCKED_EXECUTE_E4A`, or 540 if
  `FULL_RUN_REQUIRED` persists to full completion. Governs the E4a
  licensing decision. Never sample-based.
- **N_ESTIMATION**: 270 (the frozen balanced sample, `r=6`), governs the
  descriptive first-loss proportion estimate and its reported margin of
  error. Never substituted for N_GATE's exact requirement.

## 4. Amendment discipline

This document supersedes nothing in `MURU_V2_E2_PREDECLARATION.md`,
`MURU_V2_G2_PARETO_STUDY_DESIGN.md`, `MURU_V2_CAUSAL_DECISION_TREE.md`, or
`MURU_V2_RETENTION_REMEDIATION_PREREGISTRATION.md`. Those remain the
authority for the science; this document is authority only for
*computation and estimation design*, exactly the boundary section 1 and 2
draw. If a future reader needs to know what E2a's first-loss taxonomy
means, they read the predeclaration; if they need to know why a specific
world was or was not classified via the exhaustive or lazy path, they read
this document.

## 5. One BLOCKING disambiguation this protocol cannot resolve on its own

`MURU_V2_E2_ROUTING_LOCK_THEORY.md` section 3.2-3.3: Gate 2's "exoneration"
branch ("P_retain_given_front near 1 wherever P_front is high") has no
ratified numeric threshold anywhere in the frozen source. Until a protocol
owner ratifies one (or the 540-world census completes and an analyst
evaluates it directly against full data), `routing_lock.py` can report
`LOCKED_EXECUTE_E4A` or `FULL_RUN_REQUIRED` -- never `LOCKED_RC4`,
`LOCKED_RC7`, or `LOCKED_DIAGNOSTIC_ONLY`, regardless of how lopsided the
partial counts look. This protocol adopts that restriction as its own
operating rule, not merely as a note.
