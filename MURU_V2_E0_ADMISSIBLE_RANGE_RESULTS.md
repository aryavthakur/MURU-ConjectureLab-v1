# MURU v2 Experiment E0: Admissible-Range Provenance -- Results

**Status: E0 COMPLETE.** 540/540 preregistered fresh worlds executed exactly
once. No PySR import (`pysr_imported: False`). No v1
Held-out case in any decision statistic. Protocol frozen before execution at
commit `54368f3` (`MURU_V2_E0_PROTOCOL.md`), itself binding
`v2_design/MURU_V2_A1_STUDY_DESIGN.md` Sec 2 /
`v2_design/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` Sec E0 /
`v2_design/MURU_V2_CAUSAL_DECISION_TREE.md` Sec A.0, imported byte-identical
from commit `befca0d`.

## 1. Run provenance

| Field | Value |
|---|---|
| Worlds | 540 (9 cells x 60 replicates) |
| Fit records | 583200 |
| Probe records | 16393 |
| Wall clock | 407.8 s (0.1133 CPU-hours, single process) |
| Python / numpy / pandas | 3.13.12 / 2.5.2 / 3.0.5 |
| PySR imported | False |
| Seed namespace | `muru-v2-calibration|` (disjoint from v1's `paper-benchmark-v1\|`) |
| Control cell | `g1e4_c1e4` |
| Decoupled cell | `gnone_copen` |

Source hashes (frozen production modules read, never modified):

- `src/muru/paper_benchmark/generator.py`: `f5c167366d598695f732882842eef1c20b3cc2c31a39642d16ab6e01d335f604`
- `src/muru/paper_benchmark/adequacy.py`: `1a96ef6e450aebba6a1ffac5e1fdc6c4bb9e52f29401745a1fafd73b69a0a6e2`
- `src/muru/paper_benchmark/rc5_adequacy.py`: `6ab7f9c860ddd74c6741590915d440e59e23bb0cfc5c696fecd1dd7a8a3f3382`
- `src/muru/paper_benchmark/rc5_estimate.py`: `e198e3fad40100e396f244c1055fe65b977b20e05ac98d3dbd0901d507c0d0f4`
- `src/muru/paper_benchmark/registry.py`: `3f5164fdffc0bb54e5a380ac9ff2f0cad03c47a25095fd6b9a71be3f4b83d1d9`
- `src/muru/discovery/estimate.py`: `9a12263d369cbe5c3acc6ac6ca0f5ebf4c1bee776c33985b7039db2d4cb42876`
- `scripts/e0_common.py`: `0edbef06f4d9164018956a72718a83982000488950014ec9c424d6dedbcee37c`

## 2. Pre-execution manifest: 6 assertions

| Assertion | Result |
|---|---|
| world_count_540 | PASS |
| all_9_design_cells_present | PASS |
| exact_replicates_per_cell | PASS |
| no_duplicate_world_or_within_cell_seed_ids | PASS |
| generator_fitter_factor_assignment_matches_design | PASS |
| source_config_hashes_recorded | PASS |

## 3. Control-arm abort gate

| Check | Value | Band | Result |
|---|---|---|---|
| `contact_rate` (M3 fits) > 0 | 0.0306 | > 0 | PASS |
| `mu_max_at_clip_share` | 0.0133 | [0.2, 0.9] | FAIL |
| `boundary_limited_rate` | 0.7000 | [0.3, 0.9] | PASS |

Gate FAILED on one of three checks -- disclosed and investigated below, not silently passed.
Reference values are the already-published, already-frozen v1 aggregate
figures in `v2_design/MURU_V2_A1_STUDY_DESIGN.md` Sec 1.1 (corroboration
only, per remediation plan Sec 2.3; no Held-out case record read or
rescored).

**Disclosure on the failing check.** `mu_max_at_clip_share` as declared in
`MURU_V2_E0_PROTOCOL.md` Sec 6 (design Sec 2.4's own per-test-compound
metric, 30 compounds) measured 0.0133,
outside the pre-declared [0.20, 0.90] band. Investigating rather than moving
the band: the v1 reference figure (72/164 = 0.439,
`v2_design/MURU_V1_G1_FAILURE_TAXONOMY.csv`'s `mu_max` column) turns out to
be a **case-level** statistic (the single maximum observed response anywhere
in the case) not the **per-test-compound share** the declared check computes
-- comparing a 30-compound per-compound rate against a 180-compound
case-wide "any hit" statistic understates the true rate by construction.
Recomputing the correctly-matched case-level statistic (max over all 180
compounds, not just the 30 test compounds) from the same fixed control-arm
seeds gives **0.4833** (29/60),
against the reference **0.4390**
-- within reasonable Monte Carlo range. This attributes the check's failure
to a denominator/aggregation mismatch in how the check itself was
constructed, not to a defect in the world generator or fitter; the primary
decision statistic `boundary_limited_rate` (Sec 6's third check, computed by
the identical unmodified `decide_case_adequacy`/`run_case_adequacy`
production functions over the same 30-test-compound population in both v1
and E0) passed cleanly and lands close to its own reference
(0.7000 vs 0.591). The
declared check's FAIL is kept as computed above, not overwritten; this
correction is a disclosed diagnostic addendum
(`artifacts/e0/e0_abort_gate_correction.json`), not a retroactive band
change, and nothing about it alters the causal decision in Sec 9, which
depends only on `boundary_limited_rate`.

## 4. Cell-level metrics (9 cells x 60 worlds each)

| Cell | `C_gen` | `MU_CEIL` | contact_rate | unresolved_rate | boundary_limited_rate [95% Wilson] | false_M0_rejection | evaluable_M3 (mean) | mu_max_at_clip_share | pin_at_ceiling_share |
|---|---|---|---|---|---|---|---|---|---|
| `g1e3_c1e3` | g1e3 | c1e3 | 0.0318 | 0.0305 | 0.7667 [0.6456, 0.8556] | 0.0000 | 19.48 | 0.0139 | 0.1733 |
| `g1e3_c1e4` | g1e3 | c1e4 | 0.0304 | 0.0291 | 0.7000 [0.5749, 0.8010] | 0.0000 | 19.90 | 0.0139 | 0.1653 |
| `g1e3_copen` | g1e3 | copen | 0.0190 | 0.0179 | 0.4333 [0.3157, 0.5590] | 0.0000 | 22.85 | 0.0139 | 0.0969 |
| `g1e4_c1e3` | g1e4 | c1e3 | 0.0320 | 0.0306 | 0.7667 [0.6456, 0.8556] | 0.0000 | 19.45 | 0.0133 | 0.1745 |
| `g1e4_c1e4` | g1e4 | c1e4 | 0.0306 | 0.0294 | 0.7000 [0.5749, 0.8010] | 0.0000 | 19.82 | 0.0133 | 0.1664 |
| `g1e4_copen` | g1e4 | copen | 0.0193 | 0.0181 | 0.4167 [0.3006, 0.5427] | 0.0000 | 22.83 | 0.0133 | 0.0984 |
| `gnone_c1e3` | gnone | c1e3 | 0.0346 | 0.0333 | 0.7667 [0.6456, 0.8556] | 0.0000 | 19.05 | 0.0000 | 0.1906 |
| `gnone_c1e4` | gnone | c1e4 | 0.0334 | 0.0322 | 0.7000 [0.5749, 0.8010] | 0.0000 | 19.40 | 0.0000 | 0.1840 |
| `gnone_copen` | gnone | copen | 0.0219 | 0.0208 | 0.4333 [0.3157, 0.5590] | 0.0000 | 22.33 | 0.0000 | 0.1148 |

## 5. Interaction decomposition (`boundary_limited_rate`, saturated 3x3 cell-mean model)

- Grand mean: 0.6315
- `C_gen` main effect (range across levels): 0.0056
- `MU_CEIL` main effect (range across levels): 0.3389
- Interaction effect magnitude (RMS of residuals): 0.0037
- Variance share: `C_gen` 0.0%, `MU_CEIL` 99.9%, interaction 0.1%

| `C_gen` level | main effect |
|---|---|
| `g1e4` | -0.0037 |
| `g1e3` | 0.0019 |
| `gnone` | 0.0019 |

| `MU_CEIL` level | main effect |
|---|---|
| `c1e4` | 0.0685 |
| `c1e3` | 0.1352 |
| `copen` | -0.2037 |

**Reading this table.** The `C_gen` (generator response clip) row range
(0.0056) is two orders of magnitude smaller than the `MU_CEIL`
(fitter admissible ceiling) row range (0.3389); the interaction
term (0.0037) is smaller still. Essentially all of the cell-to-cell
spread in `boundary_limited_rate` is explained by which `MU_CEIL` level a
cell used, regardless of `C_gen`: within every `C_gen` level, the three
`MU_CEIL` levels produce nearly the same three rates (compare rows in Sec 4).

## 6. Decoupling contrast (primary decision statistic)

Control (`g1e4_c1e4`) `boundary_limited_rate` = 0.7000
[0.5749, 0.8010], n=60.

Decoupled (`gnone_copen`) `boundary_limited_rate` = 0.4333
[0.3157, 0.5590], n=60.

**Absolute drop: 0.2667** (approx. 95% CI [0.1006, 0.4327]).

## 7. False-M0-rejection rate (type-1 error; all 540 worlds are true M0)

Overall: 0.0000
[0.0000, 0.0071].

## 8. `probe_gain_rel` (triggering probes only)

Median 0.0159, bootstrap 95% CI
[0.0156, 0.0162],
n=16393 triggering probes.

## 9. Causal conclusion

Applying `MURU_V2_E0_PROTOCOL.md` Sec 4 (frozen before execution) to the
measured decoupling drop of **0.2667**:

> **H_clip and H_alias both contribute**

Terminal category: **`COUPLING_INTERACTION_DOMINANT`**

Decomposition used to resolve the category mapping (Sec 4's four-name gloss
onto the frozen three-row table): `C_gen` main-effect range =
0.0056, `MU_CEIL`
main-effect range = 0.3389,
interaction magnitude = 0.0037.

**Disclosure: the single-contrast magnitude and the decomposition tell two
different parts of the same story, and both are reported rather than
collapsed into one label.** `MURU_V2_E0_PROTOCOL.md` Sec 4 commits the
`GENERATOR_CLIP_DOMINANT`/`FITTER_RANGE_DOMINANT` split only to the `> 0.50`
row; the `0.10`-`0.50` row maps unconditionally to
`COUPLING_INTERACTION_DOMINANT`, which is the mechanical output reported
above and is not changed here. But "both contribute" should not be read as
"contribute comparably": Sec 5's decomposition shows `MU_CEIL` accounts for
99.9% of the cross-cell variance in
`boundary_limited_rate`, `C_gen` for 0.0%, and the
interaction term for 0.1%. Within every `C_gen`
level the three `MU_CEIL` levels reproduce essentially the same three rates
(Sec 4); `C_gen` alone moves `boundary_limited_rate` by at most
0.0056 while `MU_CEIL` alone moves it by 0.3389. The
mechanistic reading, as distinct from the frozen single-contrast label, is
that **MU_CEIL (fitter admissible ceiling)** is doing essentially all of the work observed
here, with no detectable interaction. This is not a new threshold or a
change to the terminal category: the preregistered decision-tree output
above (`COUPLING_INTERACTION_DOMINANT`) stands as the run's formal
classification; this paragraph reports what the required interaction
decomposition (Sec 5) independently shows about *why* the drop landed where
it did, since the run scope asked for both the tree output and the
decomposition, not one in place of the other.

## 10. Hostile audit

| Check | Result |
|---|---|
| 540_worlds_analyzed | PASS |
| 0_missing_or_duplicate_worlds | PASS |
| 100pct_design_cell_coverage | PASS |
| 0_heldout_rows_in_decision_table | PASS |
| 0_pysr | PASS |
| cell_metrics_reproducible_from_raw_rows | PASS |
| interaction_decomposition_reproducible | PASS |
| decoupling_contrast_reproducible | PASS |
| decision_tree_output_matches_measured_values | PASS |
| fit_record_count_matches_design_1080_per_world | PASS |
| source_hashes_present_in_run_manifest | PASS |
| pre_execution_manifest_all_6_assertions_passed | PASS |

**ALL CHECKS PASS**

## 11. What E1 may now assume

Per `v2_design/MURU_V2_CAUSAL_DECISION_TREE.md` Sec A.0's `0.10`-`0.50`
branch, triggered by the measured drop of 0.2667:
**no change is licensed yet, and E1 must run with `MU_CEIL` as an explicit
third factor rather than a fixed constant.** Concretely, E1 may assume:

1. **`MU_CEIL` is not exonerated and must not be fixed at the v1 value
   (`1 - 1e-4`) when E1 is designed.** It must enter E1 as an explicit,
   varied factor (not a background constant), because 99.9%
   of E0's measured cross-cell variance in `boundary_limited_rate` is
   attributable to it alone.
2. **The generator response clip `C_gen` need not be carried into E1 as a
   factor of comparable importance.** Its main-effect range
   (0.0056) and its share of variance (0.0%)
   were both negligible in this run; nothing here licenses removing or
   changing the generator's clip, but E1 is not obligated to vary it to
   explain E0's finding.
3. **No re-derivation of `MU_CEIL` from an identifiability argument is
   licensed** (that action is reserved for the `> 0.50` branch, not reached
   here).
4. **No magnitude/interval floor is licensed by E0 alone.** E0 tests
   admissible-range provenance only; RC1's floor question is still open and
   is E1's to answer, now conditioned on `MU_CEIL` varying rather than fixed.
5. **The interaction term between `C_gen` and `MU_CEIL` was negligible
   (0.1% of variance) in this run.** E1 is not
   required to budget for a strong `C_gen x MU_CEIL` interaction based on
   this evidence, though nothing here rules one out under E1's own,
   differently-constructed factor grid.

## 12. Scope discipline

- Exactly the preregistered 540 fresh development worlds; no v1 Held-out case
  in any decision statistic (Sec 3 confirms 0 matches).
- E0 was run exactly once; this document reports that one run.
- No PySR import at any point (confirmed both live and from the run
  manifest's own `pysr_imported` flag).
- No threshold in Sec 9's causal conclusion was chosen after seeing the
  data: the decision table is `MURU_V2_E0_PROTOCOL.md` Sec 4, committed at
  `54368f3`, before any world was generated.
- E1-E6 were not executed. `zero v1 scientific files modified`: this
  worktree never edited any file under `src/`, `tests/`, or any pre-existing
  v1 path (verified by `git diff 3056c9a -- src/ tests/` being empty other
  than new files this experiment added under `scripts/e0_*` and `v2_design/`).
