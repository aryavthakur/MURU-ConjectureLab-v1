# MURU ConjectureLab v1 — Phase 1

Data reality and measurement audit for `MURU_ConjectureLab_v1_Master_Plan.md`.

**Phase 1 only.** No modelling, no splits, no symbolic regression, no machine
learning. See `PHASE1_DECISION.md` for the verdict.

## Reading order

| Document | Question it answers |
|---|---|
| [`PHASE1_DECISION.md`](PHASE1_DECISION.md) | The verdict, the three kill criteria, and fourteen questions. **Start here.** |
| [`DATA_CENSUS.md`](DATA_CENSUS.md) | What the corpus contains, and does it reconcile with the publication |
| [`CE_AUDIT.md`](CE_AUDIT.md) | What collision energy means in this corpus |
| [`ENDPOINT_SCREEN.md`](ENDPOINT_SCREEN.md) | Which fragmentation functional to use, and why |
| [`REPEATABILITY.md`](REPEATABILITY.md) | The measurement noise floor, and the curated-vs-raw branch gap |
| [`CONFOUNDERS.md`](CONFOUNDERS.md) | What else moves with each endpoint |
| [`REFERENCE_INTEGRITY.md`](REFERENCE_INTEGRITY.md) | Whether the reference pack is what it claims to be |
| [`PROPOSED_DEVIATION_FROM_MASTER_PLAN.md`](PROPOSED_DEVIATION_FROM_MASTER_PLAN.md) | Six places the plan was changed, and why |

## Reproducing

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
```

Then, in order:

```bash
.venv/bin/python scripts/t1_00_reference_integrity.py
.venv/bin/python scripts/t1_03_manifest.py
.venv/bin/python scripts/t1_build_trajectories.py
.venv/bin/python scripts/t1_11_download_mzml.py
.venv/bin/python scripts/t1_12_raw_branch.py
.venv/bin/python scripts/t1_13_repeatability.py
.venv/bin/python scripts/t1_reports.py
.venv/bin/python scripts/t1_figures.py
.venv/bin/python scripts/t1_14_decision.py
.venv/bin/python -m pytest
```

Corpus acquisition (5,582 MassBank records, pinned commit) is a sparse git
checkout; see `scripts/t1_03_manifest.py` and `configs/dataset.yaml`.

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
└── screen.py        monotonicity, Spearman, cluster bootstrap
```

Nine modules, each with a Phase 1 consumer. No `utils/`, no base classes, no
plugin registry.

## Conventions

- **Epistemic labels.** VERIFIED (observed directly), SUPPORTED (strong evidence,
  not independently established here), ASSUMPTION (awaiting verification),
  UNKNOWN, FAILED (tested and unsupported). Used literally throughout.
- **Nothing is repaired silently.** Mismatches are logged and counted; degenerate
  inputs return NaN, never a fabricated zero.
- **Collision energy is never one field.** `ce_raw`, `ce_numeric`, `energy_type`,
  `e_lab_ev_derived` and `e_com_ev_derived` are stored separately, because the
  record declares a number with no unit.
