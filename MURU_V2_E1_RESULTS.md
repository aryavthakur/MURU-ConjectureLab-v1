# MURU v2 Experiment E1: Joint Evaluability and Detector Power -- Results

**Status: E1 COMPLETE.** 11,475/11,475 preregistered fit units executed exactly
once. No PySR import. No v1 Held-out or Challenge case in any decision
statistic. Protocol frozen before execution at commit `de930c4`
(`MURU_V2_E1_PROTOCOL.md`), itself binding `v2_design/MURU_V2_A1_STUDY_DESIGN.md`
Sec 3, `v2_design/MURU_V2_REMEDIATION_EXPERIMENT_PLAN.md` Sec E1, and
`v2_design/MURU_V2_CAUSAL_DECISION_TREE.md` Sec A.1 to E0's measured outcome.

**Headline result: NO PAIR ADMISSIBLE.** Of the full `C0..C4 x P0..P3` grid
(390 `(criterion, rule)` combinations, each scored on 153 cells x 75
replicates), **zero pairs satisfy the frozen admissibility criteria at
`alpha = 1.0`**, and **zero pairs reach joint `power >= 0.80` for M1, M2 and
M3 simultaneously at `alpha = 2.0`** either. This is decision-tree outcome
**H3** (`MURU_V2_CAUSAL_DECISION_TREE.md` Sec A.1, branch (d)): evaluability
and detection power trade off with no admissible point at any tested
amplitude. **No constant in `adequacy.py` is licensed to change on this
evidence.**

---

## 1. Run provenance

| Field | Value |
|---|---|
| Fit units | 11,475 (153 cells x 75 replicates) |
| Distinct generated worlds | 3,825 (51 `(D, alpha, noise)` cells x 75 replicates; `MU_CEIL` is fitter-side only) |
| Compound-level records | 1,032,750 (11,475 x 3 detectors x 30 test compounds) |
| `CALIBRATE` / `CONFIRM` | 826,200 / 206,550 compound rows (9,180 / 2,295 worlds; exact 60/15 per cell, verified) |
| Wall clock (8-way parallel) | 3,730 s (62.2 min) |
| PySR imported | False |
| Seed namespace | `muru-v2-calibration|E1|...` |
| Source hashes | identical to E0's own six frozen files (re-verified in this worktree; see `MURU_V2_E1_PROTOCOL.md` header) |
| Run errors | 0 |

## 2. Pre-execution / completeness manifest

| Check | Result |
|---|---|
| 11,475 fit units generated and fit | PASS |
| 153/153 design cells present, 75 replicates each | PASS |
| Exact 60/15 `CALIBRATE`/`CONFIRM` split, every cell | PASS |
| 0 duplicate world ids | PASS |
| `world_id` namespace disjoint from v1 (`V2C|E1|...`) | PASS |
| 0 Held-out/Challenge rows in any decision statistic | PASS |
| 0 PySR imports | PASS |

## 3. Control-arm reproduction (PE1-1)

`(C0, P0)` -- the frozen v1 rule -- at `alpha = 1.0`, `noise = 0.02`, pooled
over `MU_CEIL`:

| Detector | power | evaluable/case pop. n |
|---|---|---|
| M1 | **0.0000** | 180 |
| M2 | **0.0000** | 180 |
| M3 | **0.0000** | 180 |

Matches v1's own 0/48 positive-control finding (RC2) exactly. **PE1-1
confirmed.** False-M0-rejection rate on the null population (`alpha=0`, all
noise/`MU_CEIL` levels, `n=540`): **0.0056** [Wilson 0.0019, 0.0162] --- low,
consistent with E0.

## 4. Operating-characteristic table: boundary criteria (C0-C4), win rule held at frozen `P0`

CALIBRATE, `alpha=1.0`, `noise=0.02`, pooled over `MU_CEIL` (n=180 per
detector population; n=540 for the null population):

| Criterion | params | FRR | FRR Wilson hi | indeterminate_rate | indet. Wilson hi | power M1 | power M2 | power M3 |
|---|---|---|---|---|---|---|---|---|
| C0 | (control) | 0.0056 | 0.0162 | **0.5370** | 0.5787 | 0.0 | 0.0 | 0.0 |
| C1 | delta=0.001 | 0.0056 | 0.0162 | 0.5333 | 0.5750 | 0.0 | 0.0 | 0.0 |
| C1 | delta=0.003 | 0.0056 | 0.0162 | 0.5167 | 0.5585 | 0.0 | 0.0 | 0.0 |
| C1 | delta=0.01 | 0.0056 | 0.0162 | 0.3833 | 0.4250 | 0.0 | 0.0 | 0.0 |
| C1 | delta=0.03 | 0.0056 | 0.0162 | 0.0556 | 0.0782 | 0.0 | 0.0 | 0.0 |
| C1 | delta=0.1 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| C2 | delta=0.25 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| C2 | delta=0.5 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| C2 | delta=1 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| C2 | delta=2 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| C2 | delta=4 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| C3 | rho=0.05 | 0.0056 | 0.0162 | 0.3556 | 0.3968 | 0.0 | 0.0 | 0.0 |
| C3 | rho=0.1 | 0.0056 | 0.0162 | 0.2389 | 0.2766 | 0.0 | 0.0 | 0.0 |
| C3 | rho=0.25 | 0.0056 | 0.0162 | 0.0000 | 0.0071 | 0.0 | 0.0 | 0.0 |
| **C4** | **(0 params)** | **0.0056** | **0.0162** | **0.0000** | **0.0071** | **0.0** | **0.0** | **0.0** |

**Reading this table.** Every criterion moves `indeterminate_rate` from
53.7% (frozen `C0`) down to 0.0% (`C2` at any tested `delta`, `C3` at
`rho=0.25`, and `C4`) while `FRR` stays flat at 0.0056 regardless of
criterion. **`C4` achieves the design's stated goal exactly**: zero
indeterminate cases, zero added magnitude parameters, no measurable change
to false rejection. This is RC1 resolved, cleanly, exactly as `H1(a)` (branch
A.1(a) of the decision tree) predicted. **But `power` is 0.0000 for every
detector under every one of the 15 criteria.** Fixing evaluability did not
move power at all. RC1 and RC2 are independent defects; C4 (or any other
criterion) removes RC1 without touching RC2.

## 5. Operating-characteristic table: win rules (P0-P3), boundary criterion held at `C4`

CALIBRATE, `noise=0.02`, pooled over `MU_CEIL`. `power(a=1)`/`power(a=2)` are
`alpha=1.0`/`alpha=2.0` power for that detector; full table (26 rule
instances) in `artifacts/e1/e1_analysis.json`. Selected rows spanning the
permissiveness range:

| Rule | params | FRR | power M1(a=1) | power M2(a=1) | power M3(a=1) | power M1(a=2) | power M2(a=2) | power M3(a=2) |
|---|---|---|---|---|---|---|---|---|
| P0 | (control) | 0.0056 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1111 |
| P1 | ratio=0.90,w=15 | 0.0611 | 0.0 | 0.0 | 0.05 | 0.0 | 0.0 | 0.5389 |
| P1 | ratio=0.95,w=15 | 0.1111 | 0.0 | 0.15 | 0.05 | 0.0667 | 0.7667 | - |
| **P1** | **ratio=0.98,w=15 (loosest tested)** | **0.1500** | **0.0167** | **0.0333** | **0.2000** | **0.1333** | **0.0833** | **0.8333** |
| P2 | q=0.05 (loosest tested) | 0.0056 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1111 |
| P3 | m=0.05,f=0.5 (loosest tested) | 0.0611 | 0.0 | 0.0 | 0.05 | 0.0 | 0.0 | 0.5444 |

**Reading this table.** Loosening the win rule does move power for **M3**
(up to 0.8333 at `alpha=2.0` under the loosest tested `P1`), at the cost of
`FRR` rising to 0.15 -- 3x over the 0.05 ceiling. For **M1 and M2**, no win
rule in the tested grid, at any looseness, reaches power above **0.1333**
(M1) or **0.0833** (M2), even at `alpha = 2.0` (double the v1-planted
amplitude) and even paired with the most permissive boundary criterion.
Loosening the criterion axis (Sec 4) does not move M1/M2 power either.
**Neither axis of the design's `C x P` grid reaches useful M1/M2 power.**

## 6. `alpha_star_D`: the headline sensitivity measurement

Smallest `alpha` (of `{0.25, 0.5, 1.0, 2.0}`) at which `power_D >= 0.80` with
Wilson lower `>= 0.70`, `noise = 0.02`, pooled over `MU_CEIL`:

| Criterion (rule = frozen `P0`) | `alpha_star_M1` | `alpha_star_M2` | `alpha_star_M3` |
|---|---|---|---|
| C0 through C4, all params | **undefined (> 2.0)** | **undefined (> 2.0)** | **undefined (> 2.0)** |

**`alpha_star_D` is undefined within the tested ladder (up to 2x the v1
amplitude) for every criterion under the frozen win rule.** Scanning the
full `C x P` grid (390 pairs) for the single best case: the maximum
minimum-of-three-detectors power reached at `alpha=1.0` anywhere in the grid
is `{M1: 0.0167, M2: 0.0333, M3: 0.20}` (`C1(delta=0.03)` x
`P1(ratio=0.98,w=15)`) -- nowhere close to 0.80 for any detector. **PE1-3
(alpha_star_M3 exceeds 1.0) is confirmed and understated: alpha_star_M3
exceeds 2.0 under every criterion at the frozen win rule, and only the
single loosest-tested, FRR-violating win rule brings it near 2.0.**

## 7. H2 sub-check: is any pair admissible if the power criterion is moved to `alpha=2.0`?

Explicitly checked, independently, by both the primary analysis and the
hostile audit: **0 of 390 pairs** reach `power_D >= 0.80` (Wilson lower
`>=0.70`) for **all three** of M1, M2, M3 simultaneously at `alpha=2.0`. The
closest any single detector gets is M3 at 0.8333 (one pair, at FRR=0.15,
itself inadmissible); M1 and M2 never exceed 0.1333/0.0833 at any alpha in
the tested ladder. **H2 (admissible only at larger `alpha`) is ruled out**:
this is not a case of "the right amplitude wasn't tested", because two of
the three required detectors show no meaningful amplitude-response at all.

## 8. Monotonicity, misattribution

`power_D` monotonicity in `alpha` (within `MU_CEIL`-pooled, `noise=0.02`)
holds for 375/390 pairs; the 15 violations are all small-sample artifacts at
`alpha=0.5` (rates like 3/180 vs 0/180, inside one Wilson-interval width of
each other) under the loosest, already-inadmissible `P1(ratio=0.98,*)`
rules -- disclosed, not a validity concern for any pair that matters to the
selection (no admissible pair exists to select). Misattribution across the
full grid ranges 0.0 to 0.3315 (median 0.0222); it is not the binding
constraint anywhere (`power` fails all 390 pairs; `misattribution` fails 187
of 390, always co-occurring with a `power` failure already present).

## 9. `MU_CEIL`-stratified diagnostics (mandatory reporting, protocol Sec 1)

Case-level `BOUNDARY_LIMITED` rate under the frozen `(C0, P0)` rule,
`alpha=1.0`, `noise=0.02`, by `D` and `MU_CEIL` level (case status pools all
three detector contrasts, so a D=M1 world's case status can be blocked by
M2/M3's contrast even when M1's own is clean -- see Sec 10):

| D | c1e4 (v1) | c1e3 | copen |
|---|---|---|---|
| M1 | 0.9500 | 0.9500 | 0.8667 |
| M2 | 0.7167 | 0.7500 | 0.5500 |
| M3 | 0.0333 | 0.0333 | 0.0333 |

`MU_CEIL` visibly moves the case-level boundary rate for M1/M2-planted
worlds (opening the ceiling helps) and is flat for M3-planted worlds. This
is a case-level, cross-detector statistic, not the per-detector power
statistic Sec 4-6 report; see Sec 10 for why they diverge.

## 10. Diagnostic observation, not a further decision input

Recorded as a motivating observation for the next experiment, in the same
spirit as `MURU_V2_A1_STUDY_DESIGN.md` Sec 1.1's own disclosed observation --
**not** part of the frozen decision chain above, which stands on Sec 3-8
alone.

Per-compound instrumentation shows the **M1 detector's own fitted contrast
never once touches a parameter bound** across the entire `alpha=1.0,
noise=0.02` population (`boundary_contact` rate exactly 0.0 for M1-detector
fits on M1-planted worlds, every `MU_CEIL` level). M1's power failure is
therefore mechanically unrelated to RC1 in the most direct sense available:
there is no boundary event for any criterion to resolve. A targeted probe
(one compound, the largest-descriptor test compound in one `alpha=1.0`
world) found the **fitted** `log_shape` parameter recovers only a small
fraction of the **true, injected** horizontal-shape multiplier (fitted
`s_exp = 1.032` against a true `shape_val = 1.249` for that compound) even
though the objective at the fitted point is far better than at the true
generative parameters. This is consistent with a specific, checkable
mechanism: `rc5_estimate.fit_case_phi` fits the shared profile `Phi` from
the **120 training compounds**, every one of which -- by this design's own
construction, mirroring the frozen generator's own `m1_horizontal` /
`m2_high_energy` / `m3_low_energy` branches -- carries its own
compound-specific planted deviation (via each compound's own `descriptor`
value). `Phi` is therefore fit against data that already contains a spread
of per-compound shape deviations pooled together, and the isotonic profile
absorbs much of that spread into its own shape before any test compound's
M1/M2/M3 alternative fit ever runs. If confirmed by a dedicated experiment,
this would mean the practical-win contrast's low power is not a threshold
problem at all, but a consequence of the shared-profile estimation step
structurally attenuating the very signal the alternative models are fit to
detect -- and it would apply to the real Held-out F13/F14 cases too, not
just these calibration worlds, since the mechanism (`fit_case_phi` on
training compounds that share the case's own generative kind) is identical.
This is a hypothesis this run's evidence is consistent with, not a
result E1 tested directly; it is the natural first target for the next
experiment (Sec 12).

## 11. `CONFIRM` split: not opened

No pair was selected on `CALIBRATE`. Per `MURU_V2_CAUSAL_DECISION_TREE.md`
Sec A.1 branch (e) and `MURU_V2_A1_STUDY_DESIGN.md` Sec 3.7's internal
replication discipline, `CONFIRM` (2,295 worlds, 206,550 compound rows) was
**not read for any statistic in this document** and remains sealed for
whatever the next experiment turns out to be. Verified by the hostile audit
(`e1_hostile_audit.py` operates only on `CALIBRATE` rows throughout; the
`CONFIRM` split identifiers are recorded in `artifacts/e1/worlds_full.parquet`
but no `CONFIRM` row was aggregated, filtered, or scored anywhere in
`e1_analyze.py` or `e1_hostile_audit.py`).

## 12. Hostile audit

Independent reimplementation (`scripts/e1_hostile_audit.py`, imports neither
`e1_rules.py` nor `e1_analyze.py` -- the primary analyzer -- reimplements
every criterion, rule, metric and the selection rule fresh, in a
dict/loop-based style rather than the primary's vectorised-pandas style):

| Check | Result |
|---|---|
| 11,475 worlds analyzed | PASS |
| 0 duplicate worlds | PASS |
| 153/153 cells present, 75 replicates each | PASS |
| Exact 60/15 CALIBRATE/CONFIRM split per cell | PASS |
| `world_id` namespace disjoint from v1 | PASS |
| 0 Held-out/Challenge rows | PASS |
| 0 PySR | PASS |
| 0 run errors | PASS |
| Protocol frozen before implementation (git history) | PASS |
| Control pair (C0,P0) independently reproduced | PASS |
| Admissible-pair count independently matches (0 == 0) | PASS |
| Selection is the lexicographic minimum, independently verified | PASS |
| No pair reaches joint power at alpha=2.0 either, independently confirmed | PASS |

**ALL 13 CHECKS PASS.** Full detail: `artifacts/e1/e1_hostile_audit.json`.

## 13. Scope discipline

- Exactly the preregistered 11,475 fit units (153 cells x 75 replicates); no
  v1 Held-out or Challenge case in any decision statistic.
- E1 was run exactly once; this document reports that one run.
- No PySR import at any point (confirmed live and from the run manifest's
  `pysr_imported` flag).
- No threshold in this document's admissibility/selection was chosen after
  seeing the data: `MURU_V2_E1_PROTOCOL.md` Sec 6-7 fixed every criterion,
  rule, and the lexicographic order before any world was generated (commit
  `de930c4`, predates `6ea0a83`'s implementation and every subsequent
  execution commit).
- `zero v1 scientific files modified`: `git diff 3056c9a -- src/ tests/` is
  empty other than new files this experiment added under `scripts/e1_*`.
- `CONFIRM` split untouched (Sec 11).

## 14. What the next experiment may now assume

Per `MURU_V2_CAUSAL_DECISION_TREE.md` Sec A.1 branch (d):

1. **No constant in `adequacy.py` may be edited on this evidence.** Neither
   the boundary criterion, nor the practical-win ratio/win-count/evaluability
   floor, is licensed to change.
2. **RC1 (the boundary defect) and RC2 (zero detector power) are
   independent.** `C4` (and several other criteria) fully resolves RC1 --
   `indeterminate_rate` reaches exactly 0.0 with zero added magnitude
   parameters -- while leaving RC2 completely untouched (power stays 0.0000
   for every detector). A future v2 change that adopts a boundary criterion
   for RC1 alone (e.g. `C4`, on other grounds) does not need to wait for RC2
   to resolve, and does not solve RC2 by being adopted.
3. **The practical-win LOEO contrast itself is the suspect object**, not its
   thresholds, exactly as the decision tree specifies: "The LOEO
   practical-win contrast over 30 compounds is the object under suspicion,
   not its thresholds."
4. **Sec 10's diagnostic observation is a live, checkable hypothesis**
   (shared-profile `Phi` absorbing per-compound deviations from the training
   population) that the next experiment should test directly, not assume.
5. `alpha_star_D` is reported, per design Sec 3.11's difficulty-reduction
   guard, as **undefined within `[0.25, 2.0]`** for M1 and M2 under every
   criterion and every tested win rule; this is the measured sensitivity
   floor and stands regardless of what the next experiment does. Any future
   change to the F13-F16 planted amplitudes requires an external, stated
   chemical rationale (guard Sec 3.11(b)), not calibration to this number.
