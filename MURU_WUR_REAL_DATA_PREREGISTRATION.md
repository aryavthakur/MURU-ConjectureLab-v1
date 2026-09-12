# MURU WUR real-data preregistration

**Identifier:** `wur-real-data-1.0`
**Status:** FROZEN
**Supersedes:** `wfsr-external-1.0`
**Design:** `docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md`
**Frozen:** before any Stage 1 `mu` was computed. See section 9.

## 1. What this document does

MURU has never run on real spectra. v1 closed with all three endpoints
failing, v2 diagnosed those failures, and the final synthetic holdout
returned strong generalization evidence, but every one of those results is a
synthetic world. This document governs the first real-data program.

It fixes, before any real value is seen: the partition rules, the Stage 1
bridge rule and every remaining degree of freedom in it, the Stage 2
adequacy fractions, the inherited thresholds, and the sealed-part floor.

A change to any numeric threshold here voids the study that used it, and
must be reported as a voided study rather than an amendment to a running
one.

## 2. What is superseded, and the drift record

`wfsr-external-1.0` froze a GNPS2 census of 909 qualifying trajectories in
551 scaffold groups, naming GNPS2 as the primary route and the WUR download
form as fallback. This program uses the Zenodo deposit instead. Both facts
are drift, recorded here, and neither is evidence about MURU.

| Quantity | `wfsr-external-1.0` | WFSR subset of this release |
|---|---|---|
| Qualifying trajectories | 909 | 947 |
| Scaffold groups | 551 | 568 |
| Route | GNPS2 primary | Zenodo deposit |

The old analysis-population floor of 400 trajectories and 200 scaffold
groups was written for an unsplit 909-trajectory population and does not
apply to a split one. It is replaced in section 6.

## 3. The realized population

The design session projected 971 positive and 222 negative qualifying
trajectories. The executed Stage 0 census differs, and the realized figures
are the ones that govern.

| Quantity | POS | NEG |
|---|---|---|
| Qualifying trajectories | 1,010 | 241 |
| Scaffold groups | 610 | 178 |
| From WFSR food safety | 947 | 220 |
| Also in LCSB development | 165 | 10 |
| Also in the LCSB seal | 41 | 1 |

Design-session figures, retained for the record and not used: 971 POS in 581
groups, 222 NEG in 160 groups.

Source: Zenodo record 20552933, WUR Mass Spectral Library v1.0, DOI
`10.5281/zenodo.20552933`, CC-BY 4.0, 203,752,342 bytes, sha256
`96fe2b1a6c5bcb441ee980b602e58f1b296af09b4eb9b99d56b92d44c03333d2`.
Retrieved once, by the project human, on 2026-09-11. Those bytes are the
frozen release. Re-downloading for a cleaner copy is prohibited; a changed
release is a drift record plus an amendment, never a silent substitution.
The `.db` files are authoritative over the `.msp` files, because only the
`.db` records the activation type.

### 3.1 Population-definition audit

The qualifying rule calls a connectivity key complete when the union of its
accepted rows covers the ladder. Before any `mu` existed, three questions
were asked about whether that union does load-bearing work:

| Question | POS | NEG |
|---|---|---|
| Qualifying keys carrying more than one inferred adduct | 0 | 0 |
| Ladders complete only when adducts are mixed | 0 | 0 |
| Ladders complete only when source deposits are unioned | 0 | 0 |

All zero. The union is inert and the modal-adduct selection is never
exercised. Recorded in `artifacts/wur_population_audit.json`.

## 4. Partition rules

Every rule is identity-based and runs before any `mu` exists. The unit is
the Bemis-Murcko scaffold group, and a scaffold group is never split across
sides.

| Rule | Statement |
|---|---|
| D1 | The unit is the scaffold group of the lexicographically first deposited SMILES per connectivity key |
| D2 | A group containing any compound in the LCSB development corpus goes to WUR-DEV. Those compounds are already exposed |
| D3 | A group containing any compound in the LCSB sealed confirmation set goes to WUR-SEALED. D3 beats D2 where they conflict |
| D4 | Remaining free groups split 50/50 at seed `20260911` |
| D5 | Negative mode is not split. All negative-mode trajectories go to WUR-DEV, and no negative-mode external claim is made |
| D6 | A row with `side == "WUR-DEV"` whose scaffold group is a positive-mode WUR-SEALED group is EXCLUDED. D6 overrides D5 |

D6 exists because D5 routes negative-mode trajectories to WUR-DEV without
consulting the scaffold-group logic D2 to D4 use, so a negative-mode
compound could sit in development while its scaffold group is sealed on the
positive side. D6 is scoped to development exposure only: it never relabels
a WUR-SEALED row, so the sealed key list and the sealed-part floor are
untouched. It is applied as a filter over the D1 to D5 result and does not
re-run the partition. It is a provable no-op on the positive side, because
D1 to D4 never split a scaffold group.

### 4.1 Realized partition, before and after D6

| Side | POS before | POS after | NEG before | NEG after |
|---|---|---|---|---|
| WUR-DEV | 606 | 606 | 241 | 209 |
| WUR-SEALED | 404 | 404 | 0 | 0 |
| EXCLUDED | 0 | 0 | 0 | 32 |
| Total | 1,010 | 1,010 | 241 | 241 |

D6 moves 32 negative-mode trajectories in 21 scaffold groups. Of those, 19
carry a connectivity key that is itself in the sealed list; the remaining 13
are scaffold-group neighbours of a sealed compound. The narrower key-level
count is recorded here so both readings are on the record; the group-level
rule is the one frozen.

Scaffold groups, POS: 335 WUR-DEV, 275 WUR-SEALED.

Artifacts: `artifacts/wur_retrieval_manifest.json`,
`artifacts/wur_identity_census.json`,
`artifacts/wur_population_audit.json`, `artifacts/wur_split_manifest.json`,
`artifacts/wur_dev_neg_keys.json`, and `artifacts/wur_sealed_partition.json`
holding connectivity keys only, tracked in git the way
`confirmation_set_sealed.json` is, so its hash is checkable.

## 5. Stage 1: the cross-instrument bridge gate

**Question.** Does the same compound produce the same fragmentation
trajectory on the IQ-X as on the Q Exactive at matching NCE labels? If not,
pooling the two corpora is invalid and every later result must be reported
per corpus.

### 5.1 Population B

Constructed operationally, never as arithmetic on expected counts:

    population B = (POS WUR-DEV connectivity keys)
                 INTERSECT (LCSB development connectivity keys)
                 MINUS (WUR sealed keys)
                 MINUS (LCSB sealed keys)

The realized size is asserted and reported. It is expected to be 124. If it
is not, the realized population is reported and used; the expected figure is
never forced. Disjointness from both seals is asserted, not assumed.

**Floor.** The gate requires at least **30** compounds in population B. Below
that a Spearman correlation judged against a 0.80 threshold carries little
information, and the gate cannot distinguish agreement from small-sample
noise; a realized population below 30 yields outcome `NO_POOL` with the
reason recorded, and no map is fitted. This floor is stated in erratum E-1
rather than in the original freeze, and it was set with the realized size
already known to be 124, so it is a guard against a degenerate re-run and
carries no evidential weight for this run. It is not a power calculation and
is not binding here.

### 5.2 Endpoint

`features.mu` on both sides, at the base preprocessing cell of
`configs/preprocessing.yaml`: `relative_cutoff = 0.0`,
`include_precursor = true`, `intensity_transform = "raw"`,
`precursor_match_ppm = 10.0`.

On the WUR side, `mu` is computed only for spectra that the Stage 0 identity
gates already accepted. The accepted-row table is the single definition of
an accepted spectrum, shared by the Stage 0 trajectory builder and the
Stage 1 `mu` builder, so a rejected UVPD, off-ladder, wrong-polarity or
wrong-adduct spectrum cannot re-enter at the `mu` step. Each spectrum uses
its own declared `PrecursorMass`, the WUR analogue of MassBank's
`MS$FOCUSED_ION: PRECURSOR_M/Z`. Peaks are sorted by m/z before use.

**Duplicate resolution.** Where more than one accepted spectrum exists at
the same `(connectivity_key, energy)`, the value is the **median** of the
per-spectrum `mu`. Chosen before any real `mu` existed. The contributing
spectrum ids, source libraries and `n_spectra` are preserved for every cell.

**Defects.** A blob length mismatch, a nonfinite value, a negative
intensity, a non-positive total intensity, or an unusable declared precursor
is an explicit census entry naming the spectrum and the reason. Nothing is
silently dropped. A population-B defect halts the run.

On the LCSB side, the corpus is asserted to be the base cell, by checking
its `mu` against the base-cell rows of `trajectories.parquet`, and asserted
to carry at most one `mu` per `(connectivity_key, energy)` after the
corpus's own intended aggregation. Compounds with five rather than six
energies are reported through the per-energy `n`.

### 5.3 The rule

Per energy, over population B, with `delta_i = mu_WUR,i - mu_LCSB,i` over
compounds carrying a value on both sides at that energy:

- median `|delta|` <= **0.05**, about 1.7 times the 0.0295 inter-mixture
  repeatability SD measured in `REPEATABILITY.md`; and
- Spearman rank correlation of `mu_WUR` against `mu_LCSB` >= **0.80**.

`scipy.stats.spearmanr` with its default average-rank tie handling;
`numpy.median` for both medians. An energy with fewer than 3 pairs has no
defined correlation and cannot pass. The correlation is likewise undefined
when either vector is constant, in which case `spearmanr` returns `nan`; that
energy also cannot pass. Both cases are recorded as a null correlation in the
artifact rather than as a number.

Both conditions must hold on at least **5 of the 6** energies.

| Outcome | Condition | Consequence |
|---|---|---|
| `POOL` | The rule passes | WUR-DEV and LCSB development are analysed as one population |
| `POOL_AFTER_ENERGY_ALIGNMENT` | The rule fails only through a consistent offset, and the re-applied rule then passes | One monotone energy map, fitted on population B alone, is carried into Stage 2 |
| `NO_POOL` | Anything else | WUR is its own population. LCSB stays separate. Stage 2 runs twice and reports both |

`NO_POOL` is a valid scientific outcome, not a failure to be repaired.

### 5.4 The alignment branch, fully specified

The branch is entered only when **all four** conditions hold, each read off
the raw pre-alignment statistics before any map is fitted:

1. the rule in 5.3 failed;
2. the median signed delta is strictly positive at every one of the six
   energies, or strictly negative at every one of them. An exactly zero
   median signed delta at any energy satisfies neither, so the branch is not
   entered;
3. its magnitude is <= **0.15** at every energy;
4. the Spearman correlation is >= 0.80 at every energy.

Otherwise the outcome is `NO_POOL` and no map is fitted.

**The map.** One monotone affine transform of the nominal energy axis,

    T(E) = a + b*E,    b > 0,

applied to the LCSB nominal energy to give the WUR nominal energy at which
WUR is read. It is the only fitted object, and it has two parameters.

**Readout.** WUR `mu` at a non-rung energy is read from that compound's own
six-point ladder by PCHIP, shape-preserving piecewise cubic Hermite
interpolation, knots at the six ladder rungs exactly. There is no knot
selection, and nothing here is fitted: PCHIP is a deterministic readout rule
for a curve that has already been measured, which is why it is not in
tension with the affine map being the fit. Every WUR qualifying trajectory
has all six rungs by construction, and this is asserted.

**End behaviour.** `T(E)` is clamped to [15, 90] before interpolation. No
extrapolation ever occurs. The number of clamped (compound, energy) cells is
counted and reported.

**Objective.** Minimize

    J(a, b) = SUM over the six ladder energies of
              | median over i of ( mu_WUR,i(T(E)) - mu_LCSB,i(E) ) |

the sum of absolute per-energy median signed deltas. At each energy the
index `i` ranges over exactly the paired subset that section 5.3 defines for
that energy, namely the population-B compounds carrying a value on both
sides there. That subset is not the same at every energy, because some LCSB
compounds carry five rungs rather than six, so the objective is a sum over
six medians taken on six possibly different subsets. This targets the
consistent offset the branch exists for, rather than scatter, which no
energy map can fix.

**Constraints and optimizer.** `a` in [-30, 30], `b` in [0.5, 2.0], both
chosen a priori as generous relative to any plausible NCE-label mismatch
between two Orbitraps. `scipy.optimize.differential_evolution`, seed
`20260911`, `tol = 1e-8`, `maxiter = 1000`, `polish = True`. Deterministic
at that seed. One fit, no restarts.

**Non-uniqueness.** Clamping makes `J` constant over whole regions of
`(a, b)`, so its minimiser is not in general unique. No tie-break is
imposed. The reported map is whatever the procedure specified above returns,
which is deterministic at the frozen seed, and the fitted `a`, `b`, the
objective value and the clamped-cell count are all recorded so that a reader
can see when the fit sat in a flat region.

**Re-application.** The rule in 5.3 is applied to the aligned deltas exactly
once. Pass gives `POOL_AFTER_ENERGY_ALIGNMENT`; fail gives `NO_POOL`. There
is no second fit, no third pass, and no threshold change.

The raw pre-alignment statistics are preserved in the artifact whether or
not the branch activates, together with the fitted map and the single
post-alignment evaluation when it does.

**Artifact:** `artifacts/wur_bridge_gate.json`.

## 6. Inherited thresholds and floors

| Quantity | Value | Source |
|---|---|---|
| Ladder | NCE 15, 30, 45, 60, 75, 90 | The release and the LCSB corpus share it |
| Energy snap tolerance | 0.01 | Stage 0 |
| Adduct inference tolerance | 10 ppm | Stage 0 |
| Precursor match tolerance | 10 ppm | `configs/preprocessing.yaml` |
| Seed | `20260911` | Stage 0, reused |
| `ENERGY_SCALE` | 30.0 | `discovery.estimate` |
| `E_REF` | 45.0 | `rc5_adequacy` |
| Practical-win margin | 0.90 | `rc5_adequacy` |
| Minimum observed energies per compound | 5 | `rc5_adequacy` |
| Elbow tolerance | 0.01 | Frozen search settings |
| Complexity cap | 20 | Frozen search settings |
| Search seeds | 30 | Frozen search settings |
| Frozen selector | B2 family vote, R1 representative, `t1 = 0.595`, `t2 = 0.2` | `claude/muru-final-holdout-experiment-d75e7d`, not refitted |
| **Sealed-part floor** | **250 trajectories and 150 scaffold groups** | Set in the design session, blind to every `mu` |

The sealed part realizes 404 trajectories in 275 scaffold groups and clears
both floors.

## 7. Stage 2 adequacy, as fractions

`rc5_adequacy.run_case_adequacy` and the `adequacy.py` contract hard-code
exactly 30 test compounds, 24 evaluable and 20 practical wins. Against a
real population of unknown size those become fractions of the realized test
population:

- evaluable >= **0.80** of test compounds;
- practical wins >= **2/3** of test compounds.

**Both denominators are test compounds.** The frozen contract is
`MIN_EVALUABLE_COMPOUNDS = 24` and `MIN_PRACTICAL_WINS = 20` against
`N_TEST_COMPOUNDS_EXPECTED = 30` in `adequacy.py`, and 20/30 is exactly 2/3,
so the test-compound denominator is the one that reproduces the contract.
Taking 2/3 of evaluable instead would fire at 16 of 24, which is a looser
rule than the one the synthetic work calibrated, and it is corrected here
under erratum E-1 before any Stage 2 value exists.

The 0.90 practical-win margin, the minimum of 5 observed energies, the
`log_g` bounds and `E_REF = 45.0` are unchanged. At N = 30 the fractions
reproduce the existing contract exactly (24/30 and 20/30), and the existing
contract tests must keep passing at N = 30.

## 8. Standing constraints

- The synthetic method is not re-tuned against real data. No threshold,
  grammar, engine setting, null or selector is chosen by watching real-data
  performance.
- The LCSB sealed confirmation set is not opened. D3 exists to protect it.
- The WUR sealed partition is not opened for any `mu` or descriptor value
  before a candidate is frozen on development.
- The post-reveal prohibition on the synthetic holdout stands. This program
  adds a real-data study; it does not reopen synthetic accuracy work.
- If the implementation fails on real data, the permitted response is to
  record the failure, fix it in a separate engineering track, and re-run.
  Patching the code against observed real-data behaviour mid-run is
  prohibited.

## 9. Disclosures

**Format probe.** While establishing that mzVault peak blobs are
little-endian float64, the peak list of one spectrum was decoded:
`WUR mass spectral library_POS_v1.db`, `SpectrumId = 1`. It resolves to
Azaperol, connectivity key `LVXYAFNPMXCRJI`, scaffold group
`c1ccc(CCCCN2CCN(c3ccccn3)CC2)cc1`, assigned **WUR-DEV**. It is not in the
sealed partition and its scaffold group is not a sealed group, so no sealed
compound was accessed, no quarantine is required, and the sealed-part floor
and key hash are unaffected. The probe read a format, not a gate statistic,
and it preceded this freeze.

**Reproducibility contract.** Both Stage 0 manifests stamp a creation time,
so whole-file byte-identity across runs is impossible by construction. The
contract is instead `connectivity_keys_sha256`, defined as the SHA-256 over
the UTF-8 bytes of the sorted connectivity keys joined by a single newline,
with no trailing newline. Re-running the Stage 0 CLI after adding
environment provenance reproduced the 404-key sealed list unchanged.

**Environment provenance.** `wur_split_manifest.json`,
`wur_sealed_partition.json`, `wur_dev_neg_keys.json` and
`wur_bridge_gate.json` each record the Python, rdkit, pandas, numpy, scipy
and pyarrow versions, the git commit that produced them, `git_tree_dirty`,
and the sha256 of `wur_retrieval_manifest.json`. rdkit sets the scaffold
groups and the identity gate; pandas and numpy set the grouping and the
medians; scipy supplies Spearman and PCHIP; pyarrow is the parquet engine
reading the LCSB corpus. Each also records whether the working tree was
dirty when the artifact was written. An artifact committed alongside the
code that produced it legitimately shows `git_tree_dirty: true`, because the
artifact is written before it is committed, so the recorded commit is HEAD
at run time and is normally the parent of the commit carrying the artifact.

## 10. Permission

The old WUR download form required consent before publication. The Zenodo
deposit is CC-BY 4.0, which removes that gate. The licence is the permission
basis. Confirmation with WUR is a publication-time courtesy check, not an
analysis gate.

## 11. Non-goals

UVPD spectra, stepped-energy spectra, the FCH 15 to 55 ladder,
negative-mode external claims, raw vendor files, any claim about collision
energy as a causal quantity, and any second look at the sealed part.

## 12. Errata

An erratum is a correction issued against this document after its freeze
commit. Each one records what changed, why, and what had been computed at
the time, so that a reader can judge whether the change could have been
informed by a result. A correction issued before the relevant values exist
is not a post-hoc threshold choice, but it is also not the same as having
got it right the first time, and it is recorded rather than folded in
silently.

### E-1, 2026-09-12, results-blind

Issued after the freeze commit of this document and before any Stage 1 `mu`
was computed. No bridge-gate statistic, no Stage 2 value and no sealed-part
value existed. Prompted by an independent review of the freeze.

1. **Section 7, adequacy denominator.** The document said practical wins
   `>= 2/3` of **evaluable** compounds while also claiming that at N = 30 the
   fractions reproduce the frozen contract exactly. Those two statements are
   inconsistent: 2/3 of 24 evaluable is 16, whereas the frozen contract is 20.
   The denominator is test compounds, where 20/30 is exactly 2/3. Corrected,
   and the parenthetical corrected from (24/30 and 20/24) to (24/30 and
   20/30). This was the one live opportunity in the document to pick a
   threshold after seeing data, since both 16 and 20 had textual support.
2. **Section 5.1, population-B floor.** No minimum size was stated, so a
   degenerate population could in principle have returned `POOL`. A floor of
   30 is added, with its epistemic status stated in the section itself: it
   was set knowing the realized size is 124, so it is not blind and is not
   binding on this run.
3. **Section 5.3, undefined correlation.** Added the zero-variance case
   alongside the existing fewer-than-3-pairs case.
4. **Section 5.4, residual ambiguities.** Stated that the objective's index
   ranges over the same per-energy paired subset section 5.3 defines; stated
   that clamping makes the minimiser non-unique and that no tie-break is
   imposed beyond the frozen seed's determinism; stated that an exactly zero
   median signed delta fails branch condition 2.
5. **Constants.** `polish = True` and the minimum of 3 pairs per energy
   existed only as prose. Both now have constants, alongside the new
   population-B floor, so that every operational choice in section 5 is
   importable and a change to it is a visible diff.

No numeric threshold that had already been applied to data was changed,
because none had been applied to data. Section 9's format-probe disclosure is
unaffected.
