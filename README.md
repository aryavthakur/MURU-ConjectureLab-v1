# MURU ConjectureLab v1

Falsification-first study of energy-resolved MS/MS fragmentation on one
Q Exactive, against `MURU_ConjectureLab_v1_Master_Plan.md`.

**Phases 1 and 2 complete.** No symbolic regression, no PySR, no discovery
engine, no synthetic generator — those are Phase 3+ and none of it exists in
this repository.

The fixed sequence is Phase 1 → 2 → 3 → 4 → 5. Each phase authorizes **only**
the next one; see `MASTER_PLAN_CLARIFICATIONS.md` C1, which corrects a
dependency error in the master plan.

## Reading order

**Start with the two decision documents.**

| Document | Question it answers |
|---|---|
| [`PHASE1_DECISION.md`](PHASE1_DECISION.md) | Phase 1 verdict, kill criteria K1–K3, fourteen questions |
| [`PHASE2_DECISION.md`](PHASE2_DECISION.md) | Phase 2 verdict, K4A / K4B / K5 / K8, claims-ladder rung |

### Phase 1 — data reality and measurement audit

| Document | Question it answers |
|---|---|
| [`DATA_CENSUS.md`](DATA_CENSUS.md) | What the corpus contains, and does it reconcile with the publication |
| [`CE_AUDIT.md`](CE_AUDIT.md) | What collision energy means in this corpus |
| [`ENDPOINT_SCREEN.md`](ENDPOINT_SCREEN.md) | Which fragmentation functional to use, and why |
| [`REPEATABILITY.md`](REPEATABILITY.md) | The conservative inter-mixture variability estimate, and the curated-vs-raw branch gap |
| [`CONFOUNDERS.md`](CONFOUNDERS.md) | What else moves with each endpoint |
| [`REFERENCE_INTEGRITY.md`](REFERENCE_INTEGRITY.md) | Whether the reference pack is what it claims to be |
| [`PROPOSED_DEVIATION_FROM_MASTER_PLAN.md`](PROPOSED_DEVIATION_FROM_MASTER_PLAN.md) | Six places the plan was changed in Phase 1, and why |
| [`BACKLOG.md`](BACKLOG.md) | Open IMPORTANT and MINOR issues carried forward |

### Phase 2 — representation, baselines, structural generalization

| Document | Question it answers |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | Everything frozen before modelling. Committed before any governed model ran |
| [`MASTER_PLAN_CLARIFICATIONS.md`](MASTER_PLAN_CLARIFICATIONS.md) | Five governing corrections to the master plan |
| [`SPLIT_AUDIT.md`](SPLIT_AUDIT.md) | Are the scaffold and cluster splits meaningful, and does the leakage canary work |
| [`DESCRIPTORS.md`](DESCRIPTORS.md) | Tier A and Tier B, what was dropped and why, collinearity |
| [`MASS_COUPLING_AUDIT.md`](MASS_COUPLING_AUDIT.md) | Can mu's own normalization manufacture a mass association |
| [`VARIANCE_DECOMPOSITION.md`](VARIANCE_DECOMPOSITION.md) | Where the variance lives; model adequacy before model prestige |
| [`BASELINES.md`](BASELINES.md) | The full ladder under S1, S2, S3 with grouped intervals |
| [`FLEXIBLE_PREDICTIVE_BENCHMARK.md`](FLEXIBLE_PREDICTIVE_BENCHMARK.md) | How much structural information is recoverable — and why it is not a ceiling |
| [`NEGATIVE_CONTROLS_P2.md`](NEGATIVE_CONTROLS_P2.md) | Do the controls return null under the pre-registered rule |
| [`PREPROCESSING_ROBUSTNESS_P2.md`](PREPROCESSING_ROBUSTNESS_P2.md) | Raw-vs-curated subset, mixture confounding, negative mode |
| [`DEVIATIONS.md`](DEVIATIONS.md) | Phase 2 deviations D7–D13 |

## Reproducing

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
```

Phase 1, in order:

```bash
.venv/bin/python scripts/t1_00_reference_integrity.py
```

```bash
.venv/bin/python scripts/t1_03_manifest.py && .venv/bin/python scripts/t1_build_trajectories.py
```

```bash
.venv/bin/python scripts/t1_11_download_mzml.py && .venv/bin/python scripts/t1_12_raw_branch.py && .venv/bin/python scripts/t1_13_repeatability.py
```

```bash
.venv/bin/python scripts/t1_reports.py && .venv/bin/python scripts/t1_figures.py && .venv/bin/python scripts/t1_14_decision.py
```

Phase 2, in order:

```bash
.venv/bin/python scripts/t2_01_prereg_diagnostics.py && .venv/bin/python scripts/t2_02_splits.py && .venv/bin/python scripts/t2_03_descriptors.py
```

```bash
.venv/bin/python scripts/t2_04_mass_coupling.py && .venv/bin/python scripts/t2_05_baselines.py && .venv/bin/python scripts/t2_06_variance.py
```

```bash
.venv/bin/python scripts/t2_07_controls.py && .venv/bin/python scripts/t2_08_robustness.py
```

```bash
.venv/bin/python scripts/t2_09_reports.py && .venv/bin/python scripts/t2_10_decision.py
```

Tests:

```bash
.venv/bin/python -m pytest
```

`scripts/t2_05_baselines.py` is the expensive step (gradient-boosted nested
cross-validation over three splits); everything else runs in seconds to
minutes.

## Data provenance

| Source | Pin |
|---|---|
| MassBank LCSB records | release `2026.03`, commit `705afb7bccc3b2c42410a744eef73674716a60ef` |
| Raw mzML | MassIVE `MSV000091754`, campaign `20200303_ENTACT_RP_mzML`, positive mode, mixes 499/503/505 |

Per-file SHA-256 for everything acquired is in `artifacts/MANIFEST_massbank.json`
and `artifacts/MANIFEST_mzml.json`, both tracked in git. Raw inputs are treated
as immutable and are never edited.

`MSV000091754` contains **two** acquisition campaigns. The MassBank records cite
`20200303`, so the raw branch uses only that one; mixing campaigns would compare
different injections.

## Layout

```
src/muru/
├── io/massbank.py   MassBank Record Format 2.6.0 parser, raw strings retained
├── io/mzml.py       raw branch: MS2 extraction, scan matching, merging
├── io/manifest.py   SHA-256, provenance, corpus digests
├── energy.py        CE parsing with provenance; E_lab, E_com (derived)
├── spectra.py       peak-list ops and the preprocessing grid
├── features.py      mu, SY, phi, entropy, and the decomposition identity
├── identity.py      InChIKey grouping, RDKit cross-checks
├── screen.py        monotonicity, Spearman, cluster bootstrap
├── molecules.py     Tier A / Tier B, Murcko scaffolds, Butina clustering
├── splits.py        S0–S3 with disjointness enforced by assertion
└── models.py        baseline ladder, nested grouped CV, compound bootstrap
```

Twelve modules, each with a consumer. No `utils/`, no base classes, no plugin
registry.

## Conventions

- **Epistemic labels.** VERIFIED (observed directly), SUPPORTED (strong evidence,
  not independently established here), ASSUMPTION (awaiting verification),
  UNKNOWN, FAILED (tested and unsupported). Used literally throughout.
- **Nothing is repaired silently.** Mismatches are logged and counted; degenerate
  inputs return NaN, never a fabricated zero.
- **Collision energy is never one field.** `ce_raw`, `ce_numeric`, `energy_type`,
  `e_lab_ev_derived` and `e_com_ev_derived` are stored separately, because the
  record declares a number with no unit.
- **Measurement variability wording.** The Phase 1 figure (mu SD 0.0295) is the
  conservative **inter-mixture** variability estimate — an **upper bound** on
  technical repeatability, not an instrument noise floor. Negative-mode
  repeatability is **UNKNOWN**. (An earlier revision of this README called it a
  noise floor in the Phase 1 reading-order table; corrected here. The Phase 1
  reports themselves were never edited.)
- **The confirmation set is sealed.** 110 compounds, selected by scaffold group
  before any model existed, never opened in Phase 2. It is *not* unseen with
  respect to all study design — Phase 1 selected the endpoint using the full
  corpus. See `PREREGISTRATION.md` §4.1.
