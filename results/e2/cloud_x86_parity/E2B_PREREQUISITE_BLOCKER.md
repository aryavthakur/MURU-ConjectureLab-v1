# E2b prerequisite: sealed held-out evidence is absent from this repository

Recorded while executing the new-host protocol. **Independent of the parity failure**, and it would
block E2b even if parity had passed.

## Frozen E2b specification (recovered, not invented)

From `v2_design_reference/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json` and
`v2_design_reference/MURU_V2_G2_PARETO_STUDY_DESIGN.md` §2.3 / §2.5:

| Element | Frozen value |
|---|---|
| Replay population | the 144 Held-out G2 cases |
| Case count / searches / seeds | 144 / 4,320 / `SEEDS_PER_CASE = 30` |
| Seeds | the v1 seeds |
| Environment | `PYSR_CONFIG`, `GRAMMAR_VERSION`, `deterministic=True`, `parallelism="serial"` unchanged |
| **Identity criterion** | replayed retention must reproduce the **sealed `selection_count` and cross-seed representative for all 144 cases**, replaying `group_and_select` exactly as the decomposition did |
| Failure consequence | any case that fails to reproduce is **quarantined and reported, not silently dropped** |
| Historical-consistency criterion | falsification hook — if E2b materially contradicts the decomposition's 69/57 retention-versus-generation split, **all E4 ablations are suspended** |
| Admissibility | `DECISION_INADMISSIBLE`; may only corroborate or contradict a conclusion already reached on E2a |

## The blocker

The identity criterion compares against **sealed per-case `selection_count` and `representative`
values**. Those are not in this repository.

Verified exhaustively:

- No file in the working tree contains a per-case `selection_count` or `representative` for the
  held-out population. Every JSON reachable from the full git history under any `held_out`/`heldout`
  path was opened and checked: **0 of 9 contain either field.**
- `results/held_out` has never existed in any commit on any branch.
- `.gitignore` ignores `artifacts/*` (with narrow un-ignores) and explicitly ignores
  `artifacts/p3_ckpt/` as "regenerable scratch — thousands of per-seed files".
- `v2_design_reference/MURU_V1_FAILURE_DECOMPOSITION.json` records the location directly:
  `sealed_evidence_root = "/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-heldout-a3-6/results/held_out"` — a **local macOS worktree**, covering 240 cases / 7,200 searches.

`results/restored/heldout_*.json` carry only aggregate endpoint results (G2 denominator 144,
4 successes, 103 failures, 37 unevaluable). Aggregates cannot satisfy a per-case identity criterion.

## Why this cannot be worked around

The sealed `selection_count`/`representative` values **are** the v1 official result. They are not
derivable from anything present without re-running v1 — which is the very thing E2b exists to check,
so deriving them would be circular.

Running the 4,320 searches without them would not be E2b. It would be a new prospective computation
on held-out data with no admissible comparison — precisely what the decision-inadmissibility rule
forbids outside the preregistered falsification hook.

## Consequence for E4a

`MURU_V2_E4A_EXECUTION_GATE_CHECK.md` already records Gate 1 (E2b) as `WAITING` — never executed
anywhere in the repository. That remains true and is now known to be **unsatisfiable on this host**
until the sealed held-out evidence is pushed from the local macOS worktree
`muru-heldout-a3-6`, in the same way the E2a result data was recovered in `ee7026d`.

## Required recovery

1. On the local macOS host, locate `.claude/worktrees/muru-heldout-a3-6/results/held_out`.
2. Verify it against whatever manifest sealed it.
3. Commit and push it into the repository under a provenance-labelled path — it is the authoritative
   sealed v1 result and must not live only in a worktree.
4. Re-check that per-case `selection_count` and `representative` are present for all 144 G2 cases.

Note this is the **second** instance of authoritative scientific record existing only on the local
machine. The first (295 of 530 E2a worlds) was found and repaired in `ee7026d`. A repository-wide
audit for other artifacts referenced by absolute local paths is warranted.
