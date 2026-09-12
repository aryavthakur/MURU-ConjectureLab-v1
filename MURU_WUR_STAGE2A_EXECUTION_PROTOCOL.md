# MURU WUR Stage 2A: frozen pre-WUR MURU baseline, execution protocol

**Identifier:** `wur-stage2a-1.0`
**Status:** FROZEN before any Stage 2A outcome is computed
**Governs:** the single execution of the pre-WUR MURU method on WUR development data
**Parent:** `MURU_WUR_REAL_DATA_PREREGISTRATION.md` (`wur-real-data-1.0`, errata E-1 to E-3)
**Stage 1 lineage:** branch `claude/wur-stage1-bridge-gate`, head `50d65c0b63b4d838caedda77b551cd40a8d208c7`, outcome `POOL_AFTER_ENERGY_ALIGNMENT`

## 1. Question

How does the MURU methodology that existed before any WUR performance was
seen behave on independent real spectra? The result is historical evidence
whatever it shows. Nothing in the method is changed in response to it.

## 2. Preflight, recorded

| Check | Result |
|---|---|
| Stage 1 head | `50d65c0b63b4d838caedda77b551cd40a8d208c7`, as expected; this branch (`fable/wur-stage2-muru-development`) is forked from it |
| `main` drift | `main` (`7edc0f2`) is 2 commits past the merge base (`716cf97`): the v2 master mathematical reconciliation. It touches no WUR code, no selector, and no frozen constant used here. It is not imported into this branch |
| Sealed hash | `artifacts/wur_sealed_partition.json` recomputes to `6ef8c685493068cc59b776ea852ec9e012c1216f3d92fac5137e1ffe446c2a52` over 404 keys in 275 scaffold groups; the identity-only partition rebuilt from the frozen release reproduces the same hash |
| Gate artifact | `artifacts/wur_bridge_gate.json` is byte-identical to the Stage 1 head (git blob `e2074ab`); raw rule 4 of 6 energies pass, post-alignment 5 of 6, `a = -5.95552603907965`, `b = 0.8618030610784555`, 124 clamped cells |
| Release bytes | all 20 files match `artifacts/wur_retrieval_manifest.json` |
| Sealed outcome access | none. The only WUR peak decoding to date was Stage 1's population B (124 WUR-DEV keys) and the disclosed format probe (Azaperol, WUR-DEV). There is no code path that reads a sealed spectrum's peaks: every mu builder is fed the accepted-row table filtered to an explicit key list, and this protocol asserts that list disjoint from the sealed keys before decoding |
| Frozen method identity | `FRESH_HOLDOUT_METHOD_FREEZE.json` (B2 vote, R1 representative, `t1 = 0.595`, `t2 = 0.2`, frozen p3 grammar, PySR 1.5.10 config, SymPy only) is present on this branch; `claude/muru-final-holdout-experiment-d75e7d` is an ancestor of the Stage 1 head |
| Phase 4 gate | `PHASE3_DECISION.md` still reads `STOP BEFORE PHASE 4`. That verdict governed v1's Phase 4 on the LCSB corpus. It was superseded by the v1 closure, the v2 program, the fresh synthetic holdout and the frozen WUR preregistration, which authorizes this program. `assert_phase4_authorized` is not on any executed code path and is not invoked |

## 3. Epistemic structure

Three populations, all identity-defined before any Stage 2A mu exists:

| Population | Definition | Realized |
|---|---|---|
| WUR-DEV-HOLD | 40% (by compound count) of the free WUR-DEV positive-mode scaffold groups, drawn at seed `20260912`, groups whole; see `artifacts/wur_dev_internal_holdout.json` | 130 compounds, 94 groups, keys sha256 `3c45858224363e8ad132dbe46706311238db675e656a5a3bf5b2b6b1854edd94` |
| WUR-DEV-ANALYSIS | WUR-DEV positive mode minus HOLD | 476 compounds, 241 groups, keys sha256 `6601a696ed89bbd80370ecc67bd252ff9a2fd47265c1f78c5f04626358f22b28` |
| LCSB-DEV | `p2_dev_corpus.parquet` keys minus the LCSB sealed confirmation keys (`confirmation_set_sealed.json`) | 439 compounds expected, asserted at run time |

HOLD is reserved for one internal check of the Stage 2B candidate. No
HOLD peak is decoded in Stage 2A or during Stage 2B development. It is drawn
from groups that contain no LCSB development compound, because a group with
an LCSB copy is already exposed through that copy. Population B (124 keys)
lies entirely in groups that touch LCSB development, so it is entirely in
ANALYSIS; that is asserted.

WUR-SEALED (404 keys) is not touched. WUR negative mode is not used.

## 4. Analyses

Three analyses of the same frozen method. A is primary and is the one the
Stage 2B readiness rule compares against. B and C are secondary, run once,
and reported in full.

| Id | Population | Energy coordinate | Rungs used |
|---|---|---|---|
| **A_POOLED_ALIGNED** | WUR-DEV-ANALYSIS union LCSB-DEV, one trajectory per connectivity key | LCSB nominal NCE. WUR read at `T(E) = a + b*E` with the frozen Stage 1 map and PCHIP readout (`wur_bridge.apply_energy_map`, the Stage 1 code, unchanged) | 30, 45, 60, 75, 90. **E = 15 excluded** (erratum E-3) |
| B_WUR_NATIVE | WUR-DEV-ANALYSIS | WUR native NCE, no map | 15, 30, 45, 60, 75, 90 |
| C_LCSB_NATIVE | LCSB-DEV | LCSB native NCE | 15, 30, 45, 60, 75, 90 |

Duplicate resolution in A: a key present on both sides (population B) keeps
its **LCSB native** trajectory and its WUR copy is dropped. Reason, fixed
before any outcome: the LCSB copy needs no interpolation, and the WUR copy is
the very data the map was fitted on. Expected pooled size 476 + 439 - 124 =
791; the realized size is asserted and reported.

E = 15 is reported separately: B carries it natively, and A reports the
per-compound native WUR mu at 15 and the LCSB mu at 15 descriptively (counts,
medians, the M0 leave-one-energy-out residual at 15 inside B), never inside
a pooled fit. The map is not refitted, the optimizer is not touched, the
bridge population is not changed, and no second calibration is derived.

## 5. The frozen method, step by step

Every step is existing frozen code. Column renames and the population-size
generalisation of section 5.4 are the only glue.

### 5.1 Inputs

- WUR mu: `muru.io.wur_spectra.build_mu_table` on the accepted-row table
  (`wur_identity.accepted_rows`, polarity `+`) **filtered to
  WUR-DEV-ANALYSIS keys before any blob is read**; base preprocessing cell
  (`relative_cutoff 0.0, include_precursor true, intensity_transform raw,
  precursor_match_ppm 10.0`); duplicates at a `(key, energy)` collapse by the
  median, provenance retained. A peak defect is a census entry, never a
  silent drop; a defect in an ANALYSIS spectrum halts the run.
- LCSB mu: `p2_dev_corpus.parquet`, asserted base-cell against
  `trajectories.parquet` exactly as `scripts/build_wur_bridge_gate.py`
  does, restricted to LCSB-DEV keys.
- Descriptors: the 12 frozen Tier A variables (`protocol.FEATURES`), scaled
  by `protocol.SCALE`. LCSB from `p2_descriptors_tierA.parquet`; WUR from
  `molecules.tier_a_descriptors` on the deposited SMILES of the qualifying
  trajectory, with `precursor_mz` the median declared `PrecursorMass` over
  that key's accepted spectra. A key whose descriptors cannot be computed is
  an explicit failure entry and is excluded with its count reported.
- Scaffold group: `molecules.scaffold_group` on the same SMILES; population
  B keys take the LCSB group. Both sides use the same function.
- `group_key` in Stage 2 is the bare connectivity key.

### 5.2 Split

`muru.discovery.protocol.group_split(groups, world_id)`, the frozen
60/20/20 scaffold-group-disjoint split, with
`world_id = "WUR2A|<analysis id>|seed20260911"`. Both connectivity-key and
scaffold-group disjointness across parts are asserted with
`muru.splits.assert_group_disjoint`. Part sizes are reported.

### 5.3 Collapse and H-MAIN

`muru.discovery.estimate.fit_collapse` on every compound of the analysis
(`ENERGY_SCALE = 30`, 3 alternations, 60 isotonic knots, `log g` grid
`[-1.6, 1.6]` x 241), returning `g_hat`, its variance, inverse-variance
weights, `Phi`, residual SD and `hmain_adequacy` (400 compound bootstraps,
seed 12345). This is the frozen `protocol.build_world_data` behaviour: the
search target of every compound is estimated against a `Phi` fitted on all
compounds of the world. That is a property of the frozen method and is
recorded, not changed.

### 5.4 M0 to M3 adequacy ladder

`rc5_estimate.fit_case_phi` fits `Phi` on **training** compounds only
(`E_REF = 45`, 60 knots, 3 alternations). For every **test** compound and
each detector M1, M2, M3, `rc5_adequacy.evaluate_compound_contrast` runs the
frozen leave-one-energy-out contrast against M0 (`log g` in `[-2, 2]`,
shape in `[-ln 2, ln 2]`, 81 x 29 coarse grid, 3 refinement rounds,
unweighted SSE, boundary flags). Practical win is
`adequacy.is_practical_win`: `mae_alt <= 0.90 * mae_m0`, binary64, no
epsilon. Fewer than 5 distinct observed energies is `INSUFFICIENT_DATA`.

Population-size generalisation, from preregistration section 7 and E-1,
implemented in integer arithmetic so that N = 30 reproduces the frozen
24 and 20 exactly:

    evaluable_sufficient  iff  5 * evaluable >= 4 * N_test
    fired                 iff  evaluable_sufficient and 3 * wins >= 2 * N_test

Case status follows `adequacy.decide_case_adequacy`'s precedence unchanged:
any fired detector rejects M0; none fired with all three contrasts
evaluable-sufficient is `M0_NOT_REJECTED`; otherwise the most severe
indeterminate state present. The directional binomial tail
`adequacy.directional_null_tail(wins, evaluable)` is reported per detector
as a diagnostic. In A, a test compound with 5 rungs is at the floor with zero
slack: an LCSB compound whose missing rung is not 15 has 4 and is
`INSUFFICIENT_DATA` there. That is reported, not repaired.

### 5.5 Symbolic search

30 seeds from `protocol.seed_list(world_id)`; `engine.run_pysr` with the
frozen `PYSR_CONFIG` (PySR 1.5.10, `niterations 40, populations 15,
population_size 33, maxsize 20, parsimony 0.0032, adaptive_parsimony_scaling
20, deterministic, serial`), frozen grammar (`+ - * /`, `sqrt log square
cube inv`, nested constraints, complexity cap 20, invalid fraction cap
0.005). Train part fits, validation part scores. Every seed's whole Pareto
front is checkpointed (`discovery.checkpoint.Store`) before the next seed.

### 5.6 Frozen selection and gate

Exactly `scripts/fh_30_predict.py`'s deployed sequence: Pareto band at
`BAND_TOL = 0.01` per seed; structural signature on a 2,000-point lattice
(`objval.select.lattice`, seed 20260812) drawn over the analysis world's own
scaled descriptor domain; Type 2 family clustering (`objval.equiv.
cluster_families`); modal effective-support consensus; B2 validation-quality
weighted family vote; R1 highest-validation-R2 representative
(`sprint_arch.select_ABC(P, "A_CURRENT_FINAL")`); gate `REPORT iff
median_seed_best_r2 >= 0.595 and selection_fraction >= 0.2`
(`accopt_selectors.gate_features`). Thresholds are read from
`FRESH_HOLDOUT_METHOD_FREEZE.json`, not retyped.

### 5.7 Held-out generalisation

The representative expression, and every band member, is scored on the
**test** part, which no step above has used for fitting or selection:
weighted R2 (`engine.weighted_r2` with the collapse weights), unweighted R2,
Spearman rho between predicted and estimated `g_hat`. The representative's
test R2 is the Stage 2A generalisation number.

## 6. Endpoints

Reported for each analysis. A's values are the baseline the Stage 2B
readiness rule references.

| Id | Endpoint | Source |
|---|---|---|
| E1 | H-MAIN: collapse/free-shape LOEO RMSE ratio, 95% CI, `h_main_rejected`; residual SD | 5.3 |
| E2 | Ladder: per detector `N_test`, evaluable, wins, fractions, status counts, fired; case status; binomial tail | 5.4 |
| E3 | Gate decision REPORT / NO_REPORT; `median_seed_best_r2`; `selection_fraction`; `modal_support_freq` | 5.6 |
| E4 | Selected representative: expression, complexity, effective support and blocks, validation R2, **test R2** (weighted and unweighted), test Spearman | 5.6, 5.7 |
| E5 | Seed-level: 30 best-validation-R2 values, number of valid candidates per seed, band sizes, cluster table | 5.5, 5.6 |
| E6 | Population: realized sizes, scaffold counts, per-energy n, missingness, duplicate census, descriptor failures, split sizes | 5.1, 5.2 |
| E7 | E = 15 separate report | section 4 |
| E8 | Descriptive per-energy mu distribution and per-energy M0 LOEO absolute error on test compounds | 5.4 |

Uncertainty: 1,000 compound-level bootstrap resamples at seed `20260911`
for the evaluable fraction, win fraction and test R2 (percentile 2.5 / 97.5).
A Wilson 95% interval accompanies every fraction.

There is no truth, so family recovery, support recovery, null FPR and AUC
are not computable and are not reported. No value in this document is a
success criterion; Stage 2A has none.

## 7. Failure handling

Any exception inside an analysis is caught at the analysis boundary,
recorded verbatim with the step that raised it, and the remaining analyses
run. Nothing is retried with different settings. An engineering defect
that makes the intended frozen method impossible to execute may be fixed
under these rules: the fix is results-blind (chosen from the traceback, not
from any outcome), it is recorded in section 9 of the result document as an
engineering correction distinct from scientific redesign, it carries a
regression test, and the whole stage is re-run from scratch after it.

## 8. Reproducibility record

Each analysis writes `artifacts/wur_stage2a/<analysis>/` holding the long
mu table, covariates, split, collapse output, ladder records, per-seed
candidate checkpoints, the candidate cache, the selection record, and a
`manifest.json` with sha256 of every file, the connectivity-key hash of the
population, environment provenance (`wur_provenance.environment_provenance`)
and the code commit. `MURU_WUR_STAGE2A_BASELINE_RESULT.md` reports all
endpoints. The commit carrying the result is immutable; later generations
add files, never edit these.

## 9. Ambiguities resolved here, before computation

1. **Seeds per world.** The fresh synthetic holdout ran 6 seeds per world as
   a documented time-budget deviation. The inherited frozen setting and the
   preregistration table both say 30. Stage 2A uses 30.
2. **Which Phi feeds the search target.** The frozen discovery path fits
   `Phi` on all compounds; the frozen ladder fits it on training compounds.
   Both are kept as they are, each in its own step.
3. **Lattice domain.** The deployed fresh-holdout code drew the signature
   lattice from the LCSB development descriptor matrix. Stage 2A draws it
   from each analysis world's own descriptor matrix, which for C is that
   same matrix.
4. **Population-B duplicates.** LCSB copy kept (section 4).
5. **Adequacy denominators.** Test compounds, integer arithmetic (5.4).
6. **`group_key`.** The bare connectivity key on both sides.
7. **Descriptor `precursor_mz` for WUR.** Median declared precursor mass over
   the key's accepted spectra.
8. **HOLD.** Excluded from A and B entirely; never decoded.
