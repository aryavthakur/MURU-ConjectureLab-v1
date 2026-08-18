# MURU v2 E2: Predeclaration of Operational Choices

**Status:** Written before any V2C world is generated or any search executed.
This document exists because `MURU_V2_G2_PARETO_STUDY_DESIGN.md` section 2.8
specifies E2a's population as "5 truth families x 3 coefficient regimes x 3
noise levels x 12 replicates = 540 worlds" without stating the regimes'
numeric values, and the A-E first-loss taxonomy in the execution goal is a
finer partition than the design doc's own four-way `SUCCESS /
NEVER_ON_FRONT / LOST_IN_RETENTION / LOST_IN_CROSS_SEED` split. Both gaps are
closed here, mechanically, before any result exists to bias the closure.

Scope: **E2a only** (fresh V2C worlds, decision-admissible). E2b (Held-out
replay) is out of scope for this run by the execution goal's own instruction
("Use ONLY E2's fresh development worlds... no Held-out/Challenge evidence
used for decisions"). No E4 ablation is run or licensed here.

---

## 1. Provenance of the frozen source this run executes against

Worktree `exp/v2-e2-pareto-observability`, forked from
`claude/muru-v2-e0-provenance-a827a6` (commit `2868b6b`), which is itself
downstream of the v1-closed production lineage (`3056c9a`) and already
carries both `v2_design_reference/` (the committed E2 design, remediation
plan, causal decision tree, V1 G2 decomposition, root-cause ranking) and the
full frozen `src/muru/paper_benchmark` + `src/muru/discovery` production
source RC5 executed Held-out against. Nothing under `src/muru/paper_benchmark`
or `src/muru/discovery` is edited by this experiment; E2 adds new modules
under `src/muru/v2_calibration/e2_*.py` only, mirroring the discipline
`e0_worlds.py` already established: reused frozen functions are imported, not
copied, wherever the schema (a compounds/trajectories DataFrame pair) allows
it, and any function that IS transcribed line-for-line is checked against the
original by an executable identity test before use.

Execution environment: an existing venv independently verified to match this
worktree's `requirements.lock.txt` exactly on every scientifically relevant
package (`pysr==1.5.10`, `scikit-learn==1.9.0`, `scipy==1.18.0`,
`sympy==1.14.0`, plus `numpy`/`pandas` version-identical), with Julia /
SymbolicRegression.jl already precompiled against that same PySR version.
Rebuilding a fresh venv from the lock file would reproduce the identical
pinned versions at the cost of a Julia precompilation cycle this run does not
need to pay twice; the reuse is disclosed here rather than silent, and the
full `pip freeze` diff against the lock file is captured in the run manifest.

## 2. E2a coefficient regimes (3 levels)

The frozen generative law draws `coefficient = rng.uniform(0.25, 0.55)` for
every one of the four descriptor-bearing families
(`mass_affine_descriptor`, `mass_saturating_descriptor`, `mass_interaction`,
`mass_exponential_descriptor`; see `generator.py::_law`). E2a fixes this draw
to a controlled value instead of leaving it random, which is the study's
entire independent-variable-free-except-persistence discipline applied to
world *construction*: the three levels are the frozen support's own two
endpoints and midpoint, introducing no new magnitude and requiring no
external rationale under the difficulty guard.

| Regime | `coefficient` |
|---|---|
| low | 0.25 |
| mid | 0.40 |
| high | 0.55 |

`mass_power` (the negative-control family) has no `coefficient` term in its
law (`scale * mass**exponent`; see `_law`'s `mass_only` branch, where
`coefficient` is drawn but never used, exactly as in the real generator). Its
`exponent = rng.uniform(0.45, 0.75)` draw is therefore **unaffected by
regime**: `mass_power` worlds are generated identically across all three
"regime" labels, differing only in each replicate's own random draw. This is
disclosed rather than hidden; the regime factor is a no-op for this one
family by construction of its own truth law, not by a new choice made here.

## 3. E2a noise levels (3 levels)

`generator.py::_response_matrix` already keys `noise_sd` off the case
`kind` string, with values `{0.0, 0.0295, 0.06}` for the three explicit
`scalar_*` kinds and a default of `0.02` for every other kind (which is what
all four descriptor families and `mass_power` actually receive in the real
benchmark). E2a reuses exactly the three values that already appear as
literal noise levels anywhere in the frozen generator's own `noise_sd`
dictionary and are not specific to one excluded family:

| Level | `noise_sd` |
|---|---|
| noiseless | 0.0 |
| default | 0.02 |
| strong | 0.06 |

`0.0295` (`scalar_moderate`) is excluded because it is specific to a kind
outside the five G2 families and is redundant with `default=0.02`'s role as
the mid-point; using `{0.0, 0.02, 0.06}` also matches E1's own noise-level
list exactly (`MURU_V2_A1_STUDY_DESIGN.md`), so E2a's noise axis is not a
fresh invention relative to the rest of the v2 plan.

## 4. World identity and namespace

Per `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` section 2.2:

```
world_id     = "V2C|E2|<cell_id>|r<replicate:03d>"
cell_id      = "<family>|c_<regime_label>|n_<noise_label>"
seed payload = "muru-v2-calibration|" + "|".join(parts)
```

`generator.derive_seed` prefixes `"paper-benchmark-v1|"`; every E2a world
content seed is derived under `"muru-v2-calibration|"` instead, so no V2C
world's construction seed can collide with any benchmark case's. Verified by
a disjointness assertion in the preflight step, not by inspection alone.

**Deterministic enumeration**, fixed before any world is built (this fixes
`world_ordinal`, used only for the search-seed band arithmetic below, and has
no scientific effect on any world's content):

```
families = [mass_affine_descriptor, mass_power, mass_saturating_descriptor,
            mass_interaction, mass_exponential_descriptor]   # generator._law's own order
regimes  = [low, mid, high]      # coefficient 0.25 / 0.40 / 0.55
noises   = [noiseless, default, strong]   # noise_sd 0.0 / 0.02 / 0.06
replicate in 0..11

world_ordinal = ((family_idx*3 + regime_idx)*3 + noise_idx)*12 + replicate
```

540 worlds, `world_ordinal` in `[0, 540)`, bijective with `(family, regime,
noise, replicate)`.

## 5. Search seed band (new, disjoint)

PySR's `random_state` needs a bounded, signed-32-bit-safe integer, matching
every existing frozen precedent (`calibration_contract.PB_SEED_BASE`,
`seed_band_registry.FALSV2_SEED_BASE`, the reserved
`a3_5_case_search_reserved` band). A new band is declared, checked by the
same `seed_band_registry.find_overlaps` machinery the repository already
uses (executed, not just asserted by arithmetic on paper):

```
E2A_SEED_BASE     = 2_104_500_000
E2A_SEED_CAPACITY = 1_000_000
e2a_seed(world_ordinal, k) = E2A_SEED_BASE + world_ordinal*30 + k
    world_ordinal in [0, 540), k in [0, 30)   -- max offset 16,199
```

Placed in the 9,988,600-integer void between `a3_5_case_search_reserved`'s
end (`2,100,011,399`) and `a3_1_a3_2_structural_null_calibration`'s start
(`2,110,000,000`), leaving guards of 4,488,601 and 4,500,000 integers on
each side -- both exceeding the new band's own 1,000,000 capacity, mirroring
`falsification_calibration_v2`'s own stated placement discipline. Verified
computationally against every `DECLARED_BANDS` entry: zero new unacknowledged
overlaps (the sole overlap found is the pre-existing acknowledged
`objval_plan2` x `rc3_engineering_smoke` pair already on record). Max seed
`2,105,499,999 < 2,147,483,647` (signed 32-bit max).

## 6. The A-E first-loss taxonomy, mapped onto real pipeline stages

The execution goal asks for a finer partition than the design doc's own
four-way split. It is realized here as a strict refinement -- every A-E case
maps onto exactly one design-doc class, and the union of C and D below is the
design doc's `LOST_IN_CROSS_SEED`:

| Design doc class | A-E refinement |
|---|---|
| `NEVER_ON_FRONT` | **A** |
| `LOST_IN_RETENTION` | **B** |
| `LOST_IN_CROSS_SEED` | **C** (aggregation) or **D** (classifier/equivalence) |
| `SUCCESS` | **E** |

For one world (case), over its 30 seeds, using only functions already frozen
in `src/muru/paper_benchmark`:

- `correct_on_front(seed)`: **true** iff any row of that seed's full,
  persisted Pareto front is `g2_correct` under the truth-blind-at-search-time,
  truth-joined-downstream classifier (`g2_contract.evaluate_g2_event` ==
  `SUCCESS`, i.e. `classify_support(...) == MATCH` **and**
  `classify_family_match(...) == MATCH` against this world's own known truth
  support/family).
- `retained_correct(seed)`: **true** iff that seed's `argmax(score)`-retained
  row (`rc5_selection.select_row_label`, byte-identical to the production
  path) is itself `g2_correct`.
- **A -- `NEVER_ON_FRONT`**: `correct_on_front(seed)` is false for all 30
  seeds. No retention or aggregation stage is even reached.
- **B -- `LOST_IN_RETENTION`**: `correct_on_front(seed)` is true for >=1 seed,
  but `retained_correct(seed)` is false for all 30 seeds -- a correct row
  existed somewhere on some front and `argmax(score)` never kept it.
- Otherwise >=1 seed's retained candidate is itself correct. Run
  `rc5_selection.group_and_select` over the 30 seeds' retained candidates
  (identical to production: `identity_contract.template_key` grouping,
  largest-class-wins, lowest-ordinal tie-break) to get the case's winning
  class and representative candidate.
  - **E -- `SUCCESS`**: the representative is itself `g2_correct`.
  - Otherwise the representative is not classified correct. Distinguish by a
    secondary, classifier-independent ground-truth check --
    `discovery.equivalence.algebraically_equivalent` between the
    representative's parsed expression and this world's own known truth
    expression (up to a positive multiplicative constant, the same tolerance
    the frozen recovery hierarchy already uses):
    - **D -- classifier/equivalence loses it**: the representative *is*
      algebraically equivalent to the planted truth, but the truth-blind
      classifier (structural support/family pattern matching) does not
      recognize it as correct. The classifier, not the search or the voting
      relation, is where this case is lost.
    - **C -- lost in cross-seed aggregation**: the representative is not
      algebraically equivalent to the truth either -- a genuinely incorrect
      class won the cross-seed vote over the seed(s) that did retain a
      correct candidate.

This is mechanical and exhaustive: every one of the 540 E2a cases receives
exactly one of A/B/C/D/E, in that decision order, with no case left
unclassified and no case double-counted (the five conditions are checked in
strict sequence and each terminates the classification).

## 7. What this predeclaration does not decide

No retention policy is chosen here. No grammar, budget, or objective change
is proposed here. `P_retain_given_front`, `P_win_given_retain`, the
score/complexity/r2 gaps, and the A-E counts are measurements this run
produces, not quantities fixed in advance -- only the *rule that computes
them* is fixed here, before they are seen.
