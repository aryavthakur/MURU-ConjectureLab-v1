# WUR real-data program: design

**Date:** 2026-09-11
**Status:** DESIGN, not executed, not preregistered
**Author branch:** `claude/mur-mass-spectral-library-42e6d5`

## 1. Why

MURU has never run on real spectra. v1 closed with all three endpoints failing,
v2 diagnosed those failures, and the final fresh holdout returned strong
generalization evidence, but every one of those results is a synthetic world.
Phase 4, real-data discovery, was never authorized.

The WUR library supplies the missing input: about 971 positive-mode compounds
measured on an Orbitrap IQ-X across the identical NCE 15 to 90 ladder the LCSB
corpus uses, of which about 776 are compounds MURU has never seen. That is the
first opportunity to ask whether the method does anything on real data, and it
is also the sample size the master plan named as a limit (with about 118
confirmation compounds, an effect of rho = 0.2 is detected only about 55% of
the time).

## 2. Decisions already taken

| Decision | Value |
|---|---|
| Role of the library | Split once by scaffold: part development, part sealed external validation |
| Seal size | Half the free scaffold groups |
| Governance | A new preregistration that supersedes `wfsr-external-1.0` |
| First milestone | End to end, with the cross-instrument bridge gate first |

## 3. The input

| Field | Value |
|---|---|
| Source | Zenodo record 20552933, WUR Mass Spectral Library v1.0, 2026-06-05 |
| DOI | `10.5281/zenodo.20552933` |
| Licence | CC-BY 4.0 |
| Publication | Padilla-Gonzalez et al., *Anal. Chem.* 97(43), 23822-23830 (2025) |
| Bytes | 203,752,342 |
| SHA-256 | `96fe2b1a6c5bcb441ee980b602e58f1b296af09b4eb9b99d56b92d44c03333d2` |
| Contents | 10 MSP and 10 mzVault SQLite `.db` files |
| Retrieved by | The project human, through the Zenodo record, on 2026-09-11 |

This is one retrieval. Those bytes are the frozen release. Re-downloading for a
"cleaner copy" is prohibited; a changed release is a drift record plus an
amendment, never a silent substitution.

`.db` files are authoritative over `.msp` files. They agree peak for peak on
99.9% of spectra, but only the `.db` records the activation type, without which
HCD 25 and UVPD 25 are indistinguishable.

### 3.1 Qualifying population (identity only, no mu computed)

Positive mode, HCD, all six of NCE 15/30/45/60/75/90 present:

| Quantity | Positive | Negative |
|---|---|---|
| Qualifying trajectories | 971 | 222 |
| Scaffold groups | 581 | 160 |
| From WFSR food safety | 947 (568 groups) | 220 (159 groups) |
| Compounds also in LCSB | 195 | 31 |
| ... in the LCSB development corpus | 165 | 10 |
| ... in the LCSB sealed confirmation set | 41 | 1 |
| Scaffold groups touching LCSB development | 143 (398 traj) | 27 (68 traj) |
| Scaffold groups touching the LCSB seal | 33 (63 traj) | 3 (3 traj) |
| Free groups, touching neither | 438 (573 traj) | 133 (154 traj) |

Promoted adducts, positive mode: 938 `[M+H]+`, 22 `[M+NH4]+`, 8 `[M+Na]+`,
3 `[M]+`. Negative mode: 222 `[M-H]-`.

Excluded and counted, positive mode: 1,017 stepped-energy, 842 UVPD, 857
off-ladder energies, 277 incomplete ladders, 54 adducts unresolved within
10 ppm, 10 whose scan filter contradicts the library's polarity, 4 whose
deposited SMILES contradicts its own InChIKey.

### 3.2 Known defects in the source

Recorded here so the loader gates on them rather than discovering them later.

1. Precursor ion type is blank in every record. It is inferred from the SMILES
   exact mass at 10 ppm, and a record with no explained adduct is dropped.
2. UVPD "collision energy" values (25/50/100) are activation times, not
   energies. UVPD is excluded from this program entirely.
3. Energy strings are unnormalised: `15`, `15.0`, `15.0` with trailing spaces,
   `15.0000000000000000000000`, and a handful of 40.67 values.
4. Identity errors: the Gramine entries carry Methyl caffeate's structure; two
   prenyl-tryptophan entries disagree with their own SMILES; 18 positive and 27
   negative compounds have a stated formula the SMILES contradicts.
5. 16 negative-polarity scans sit inside the positive-mode library.
6. 62 positive and 61 negative compound/activation/energy combinations appear
   more than once.

### 3.3 Drift against the frozen WFSR contract

`wfsr-external-1.0` froze a GNPS2 census of 909 qualifying trajectories and 551
scaffold groups. The WFSR subset of this release gives 947 and 568. The route
also differs: the contract names GNPS2 primary and the WUR download form as
fallback, and this came from the Zenodo deposit. Both facts are recorded as
drift in the new preregistration. Neither is treated as evidence about MURU.

## 4. Stage 0: partition and seal

Runs before any mu exists. Every rule is identity-based.

| Rule | Statement |
|---|---|
| D1 | The unit is the Bemis-Murcko scaffold group from `molecules.scaffold_group`, on the lexicographically first deposited SMILES per connectivity key |
| D2 | A group containing any compound in the LCSB development corpus goes to WUR-DEV. Those compounds are already exposed |
| D3 | A group containing any compound in the LCSB sealed confirmation set goes to WUR-SEALED, and D3 beats D2 where they conflict (33 groups, 63 trajectories, positive mode) |
| D4 | Remaining free groups split 50/50 at seed `20260911` |
| D5 | Negative mode is not split. All 222 trajectories go to WUR-DEV, and no negative-mode external claim is made |

Expected positive-mode sizes, from 200 simulated draws: sealed about 288
trajectories in about 219 groups (5th percentile 261 and 200), development about
683. Combined with the LCSB development corpus, development becomes roughly
1,230 compounds against today's 549.

The old analysis-population floor of 400 trajectories and 200 scaffold groups
was written for an unsplit 909-trajectory population. The new floor is 250
trajectories and 150 scaffold groups for the sealed part, set here, blind to
every mu.

Artifacts: `artifacts/wur_retrieval_manifest.json`,
`artifacts/wur_identity_census.json`, `artifacts/wur_split_manifest.json`,
and `artifacts/wur_sealed_partition.json` holding connectivity keys only, which
is tracked in git the way `confirmation_set_sealed.json` is, so its hash is
checkable.

## 5. Stage 1: the cross-instrument bridge gate

**Question.** Does the same compound produce the same fragmentation trajectory
on the IQ-X as on the Q Exactive at matching NCE labels? If not, pooling the two
corpora is invalid and every later result must be reported per corpus.

**Population B.** The 165 compounds shared with the LCSB development corpus,
minus the 41 in the sealed set, giving 124 expected. The realised count is
reported. Sealed compounds never enter.

**Endpoint.** `features.mu` on both sides, in the base preprocessing cell of
`configs/preprocessing.yaml`, which the loader reproduces for WUR.

**Rule, frozen before any difference is computed.** Per energy, over population
B, with `delta_i = mu_WUR,i - mu_LCSB,i`:

- median `|delta|` <= 0.05, which is about 1.7 times the 0.0295 inter-mixture
  repeatability SD measured in `REPEATABILITY.md`; and
- Spearman correlation of `mu_WUR` against `mu_LCSB` >= 0.80.

Both must hold on at least 5 of the 6 energies. Outcomes:

| Outcome | Condition | Consequence |
|---|---|---|
| `POOL` | The rule passes | WUR-DEV and LCSB development are analysed as one population |
| `POOL_AFTER_ENERGY_ALIGNMENT` | The rule fails only through a consistent offset: same sign of median signed delta at every energy, magnitude <= 0.15, and rho >= 0.80 everywhere | Fit one monotone energy map on population B alone, which is already exposed, then apply the same rule once more |
| `NO_POOL` | Anything else | WUR is its own population. LCSB stays separate. Stage 2 runs twice and reports both |

The rule is applied once per branch. Thresholds do not move after deltas are
seen; a threshold change voids the gate and is reported as such.

Artifact: `artifacts/wur_bridge_gate.json`.

## 6. Stage 2: the first real-data MURU run

### 6.1 What is reused

| Component | Status |
|---|---|
| `discovery.estimate.fit_collapse`, `hmain_adequacy` | As-is. It already takes `group_key`, `ce_numeric`, `mu`, and its `ENERGY_SCALE = 30.0` matches this ladder |
| `paper_benchmark.rc5_estimate.fit_case_phi`, `estimate_case_g` | As-is for fold-local Phi and held-out g. Column renames only |
| `paper_benchmark.rc5_adequacy.fit_model`, `evaluate_compound_contrast` | As-is per compound. This is the M0 to M3 leave-one-energy-out engine |
| `splits.py`, `molecules.py`, `features.mu` | As-is. They are source-agnostic |
| Symbolic search, grammar, 30 seeds, elbow tolerance 0.01, complexity cap 20 | As-is |
| Frozen selector: B2 family vote, R1 representative, gate `t1 = 0.595`, `t2 = 0.2` | As-is, ported from `claude/muru-final-holdout-experiment-d75e7d` into `src/`. Not re-fitted |

### 6.2 What is built

1. **A WUR loader**, `src/muru/io/wur.py` plus a build script, producing a
   trajectory table with the same columns as `p2_dev_corpus.parquet`. It reads
   the `.db` files, separates HCD from UVPD, normalises energy strings, infers
   adducts, applies the identity gate, resolves duplicates, and implements the
   same preprocessing grid. No LCSB accession or slot logic applies.
2. **A population-general adequacy stage.** `rc5_adequacy.run_case_adequacy` and
   the `adequacy.py` contract hard-code exactly 30 test compounds, 24 evaluable
   and 20 practical wins. Those become fractions of the realised test
   population: evaluable >= 0.80 of test compounds, wins >= 2/3 of evaluable.
   The 0.90 practical-win margin, the minimum of 5 observed energies, the
   `log_g` bounds and `E_REF = 45.0` are unchanged. **This is the work that
   unblocks prerequisite P3 of the external protocol**, and it is far smaller
   than the blocker document implies.
3. **A real candidate cache builder**, so the frozen selector consumes real
   search output in the shape it already expects.

### 6.3 Structure

Scaffold-group 60/20/20 train/validation/test inside development, seed
`20260911`, through `splits.py`. Phi is fitted on training compounds only; g for
validation and test compounds is estimated against that frozen Phi. The existing
leakage canary tests are re-asserted on the real table.

Order: scalar collapse and `h_main` adequacy, then the M0 to M3 ladder, then
symbolic search on g, then the frozen gate. Each stage writes and hashes its
artifact before the next begins.

### 6.4 Outcomes worth naming in advance

All four are reportable results, and the preregistration fixes the decision
rules before the run so that none of them can be salvaged after the fact:

- Real trajectories do not collapse onto a shared profile at all.
- They collapse, but no descriptor structure in g survives the null.
- Structure survives on development and the gate reports it.
- The implementation fails on real data. The permitted response is to record the
  failure, fix it in a separate engineering track, and re-run. Patching the code
  against observed real-data behaviour mid-run is prohibited.

## 7. Stage 3: the sealed part

One look, after a candidate is frozen on development, scored once, with every
number reported. Out of scope for the current implementation plan.

## 8. Governance

A new document, `MURU_WUR_REAL_DATA_PREREGISTRATION.md`, frozen before Stage 1
computes any mu. It supersedes `wfsr-external-1.0`, carries the drift record of
section 3.3, and restates in one place: the partition rules, the bridge rule,
the adequacy fractions, the inherited thresholds, and the sealed-part floor.

Unchanged constraints:

- The synthetic method is not re-tuned against real data. No threshold,
  grammar, engine setting, null or selector is chosen by watching real-data
  performance.
- The LCSB sealed confirmation set is not opened. Stage 0 rule D3 exists to
  protect it.
- The post-reveal prohibition on the synthetic holdout stands. This program adds
  a real-data study; it does not reopen synthetic accuracy work.

**Permission.** The old WUR download form required consent before publication.
The Zenodo deposit is CC-BY 4.0, which appears to remove that gate, so the
preregistration records the licence as the permission basis and flags
confirmation with WUR as a publication-time check rather than an analysis gate.

## 9. Repository mechanics

- **Base branch:** fork from `claude/muru-final-holdout-experiment-d75e7d`. It is
  main plus the only copy of the frozen selector and
  `FRESH_HOLDOUT_METHOD_FREEZE.json`. Not `exec/muru-heldout-a3-6`, which is 41
  commits behind main.
- **Data location:** `data/external/wur/`, which `.gitignore` already excludes,
  with a tracked `artifacts/wur_retrieval_manifest.json` recording the hashes.
- **Tests:** the loader gets its own tests; the split gets a disjointness test in
  the style of `tests/test_splits.py`; the generalised adequacy stage keeps the
  existing contract tests passing at N = 30 and adds cases at other N.

## 10. Non-goals

UVPD spectra, stepped-energy spectra, the FCH 15 to 55 ladder, negative-mode
external claims, raw vendor files, any claim about collision energy as a causal
quantity, and any second look at the sealed part.

## 11. Risks

1. **The bridge gate fails.** Plausible: the two libraries differ in instrument,
   thresholding and curation. The consequence is smaller effective sample size,
   not an invalid program.
2. **mzVault spectra are averaged and thresholded**, LCSB records are curated
   differently. Intensity thresholding moves mu directly. The bridge gate is the
   detector for this, which is why it runs first.
3. **The real corpus may simply not collapse.** That is the scientific question,
   and a negative answer is the result.
4. **Scaffold groups are uneven.** The largest positive-mode group, plain
   benzene, holds 122 compounds, so a single group can dominate a fold. Fold
   sizes are reported, and the split is checked against the per-fold floor
   before any fitting.
