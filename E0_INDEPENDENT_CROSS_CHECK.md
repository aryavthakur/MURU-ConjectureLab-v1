# E0 independent cross-check against the parallel E0 run

Performed only after this worktree's own E0 result was fully analyzed,
hostile-audited (12/12 pass), and sealed by commit `bdbcea6`. Nothing in this
document changes that sealed result; this is a post-hoc comparison against a
second, independently-built implementation of the same experiment, run
concurrently by a different session in worktree
`muru-v2-e0-provenance-a827a6` (branch `claude/muru-v2-e0-provenance-a827a6`,
result commit `1009bcd`, "E0 result: the fitter admissible ceiling causes
RC1's boundary pathology; the generator clip causes none of it"). That
worktree's code and numeric results were not read at any point before this
worktree's own run was complete, analyzed, and sealed.

## Design fidelity

Both implementations independently:

- forked from the same v1-closed frozen source tip (`3056c9a`) and imported
  the same design commit (`befca0d`) byte-identically (their fidelity check
  and this worktree's `v2_design/DESIGN_PROVENANCE.md` cite the same source
  hashes for `MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md`,
  `MURU_V2_A1_STUDY_DESIGN.md`, `MURU_V2_CAUSAL_DECISION_TREE.md`,
  `MURU_V1_G1_FAILURE_TAXONOMY.csv`);
- built the full 3x3 = 9-cell grid over the same two factors, at the same
  three levels each (`1e4` = `1-1e-4`, `1e3` = `1-1e-3`, generator `none` /
  fitter `open` = `1.0+1e-2`);
- resolved the one undeclared design choice -- which cell the "decoupling"
  contrast reads -- the same way: control (`C_gen=1e4, MU_CEIL=1e4`) against
  the fully-relaxed opposite corner (`C_gen=none, MU_CEIL=open`), out of nine
  possible cells and no explicit instruction to pick that one;
- ran 9 x 60 = 540 worlds, 30 test compounds, 6 energies, true M0 only, 0
  PySR imports, seeds namespaced `muru-v2-calibration|`.

## Cell-level aggregates

Every one of the 9 cells' `boundary_limited_rate` (successes/60) matches
exactly between the two runs, e.g.: control `g1e4_c1e4` 42/60 = 0.700 both
runs; `g1e3_c1e3` 46/60 = 0.7667 both; `g1e4_copen` 25/60 = 0.4167 both;
decoupled `gnone_copen` 26/60 = 0.4333 both. `contact_rate`, `unresolved_rate`,
and `mu_max_at_clip_share` in the control cell also match to the digits shown
(0.030601851851851852, 0.029382716049382716, 0.013333333333333334). This
level of agreement is the expected consequence of both implementations
following the same frozen, prescribed seed-namespace formula
(`MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` Sec 2.2) against the same pinned
environment and the same unmodified frozen fitting code -- not a
coincidence, and not cross-contamination (this worktree's code was written
and its result sealed before either codebase was compared to the other).

## Effect sizes and causal category

| | This worktree | Peer worktree |
|---|---|---|
| Decoupling contrast (control minus fully-decoupled) | 0.2667 | 0.2667 |
| Frozen decision-tree row | "H_clip and H_alias both contribute" | `H_clip_and_H_alias` |
| `C_gen` main-effect magnitude | range 0.0056 (0.0% variance share) | paired delta 0.0 |
| `MU_CEIL` main-effect magnitude | range 0.3389 (99.9% variance share) | paired delta 0.2833 |
| Mechanistic reading | fitter ceiling explains ~all of it, generator clip ~none | "the fitter admissible ceiling causes RC1's boundary pathology; the generator clip causes none of it" |

Both runs land on the identical primary classification from the frozen
decision table, and both independently disclose the same mechanistic
finding using different decomposition methods (this worktree: saturated
3x3 cell-mean ANOVA-style decomposition; peer: paired single-factor delta
contrasts with McNemar tests). The peer's own hostile review additionally
ran a comparator-sensitivity sweep across all 8 non-control cells as the
"decoupled" comparator: every comparator that varies `MU_CEIL` alone lands
in the `H_clip_and_H_alias` band (delta 0.28-0.28); every comparator that
varies `C_gen` alone (holding `MU_CEIL` fixed) lands in `H_null` (delta
≈0-(-0.067)). That sweep, run only on their side, is additional
corroboration of the same pattern this worktree's variance decomposition
shows, from a different angle.

## Disagreements

None blocking. One cosmetic difference: this worktree's abort gate declared
a `mu_max_at_clip_share` check against a mismatched (case-level vs
per-test-compound) reference denominator and failed it, disclosed and
diagnosed in `MURU_V2_E0_ADMISSIBLE_RANGE_RESULTS.md` Sec 3 (corrected
recomputation: 0.483 vs reference 0.439). The peer's own abort gate (G-A/B/C,
differently constructed, using a directly-matched v1 comparator and a
dominant-bound identity check) passed all three. Both gates are validity/
corroboration checks only, per remediation plan Sec 2.3; neither affects
either run's causal decision, which in both cases depends only on
`boundary_limited_rate`.

## Conclusion

Two independent implementations, built without either reading the other's
code, converge exactly on the same 540-world numeric result, the same
frozen-decision-tree classification, and the same mechanistic finding: the
fitter's admissible ceiling (`MU_CEIL`), not the generator's response clip
(`C_gen`), is responsible for essentially all of the measured boundary
pathology in this design. No result here was modified to produce this
agreement -- this worktree's result was sealed at commit `bdbcea6` before
the peer worktree's code or output was read at all.
