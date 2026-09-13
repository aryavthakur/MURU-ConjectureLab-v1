# MURU-WUR-v2 Reproducibility Manifest (Phase 2/3)

All numbers below were produced in a **fresh, detached `git worktree`**
(`/tmp/muru_repro_rebuild`, HEAD `1be9d54eb6f1fc1d1a5b8b3602150845e581808d` —
this branch's tip after Phase 0), separate from the working tree used for
everything else in this study, so the frozen candidate/comparator files in
the real working tree were never at risk of being overwritten. No cached run
was trusted without its fingerprint verifying first.

## 1. What was rebuilt, in order

1. **Structure representations** (`scripts/wur_v2/build_v2_representations.py`,
   `PYTHONPATH=src`, no arguments, 26.6s). Computes `TIER_A`, `MORGAN`,
   `MORGAN_COUNTS`, `ATOMPAIR`, `ATOMPAIR_COUNTS`, `MACCS`, and two kernel
   matrices from the committed compound table
   (`artifacts/wur_v2/data/compounds.csv` + identity/aligned tables) using
   RDKit 2026.03.5 only — no network, no external download.

   **Finding, disclosed rather than silently fixed:** `TIER_A.parquet` and
   `MACCS.parquet` are git-tracked in this repository, but `MORGAN.parquet`
   (the representation the frozen candidate actually depends on) is not —
   it falls under the `artifacts/*` default-ignore with no explicit
   unignore rule, unlike its siblings. This is exactly the gap Phase 3 of
   the mandate asks to check for ("Untracked representation files cannot be
   the only path to reproducing the model"). It **is** reconstructible: the
   rebuild is deterministic given the committed structures, the pinned
   RDKit version, and the feature spec already embedded in the candidate
   JSON (`radius=2, fp_size=2048, counts=true, chirality=false,
   transform=log1p`). Proof: the freshly rebuilt `TIER_A.parquet` and
   `MACCS.parquet` are **numerically exact-equal** (`np.array_equal`, not
   just `allclose`) to the committed versions, and the freshly rebuilt
   `MORGAN.parquet` reproduces the frozen candidate's exact hash (below).
   No repository convention was changed to "fix" this asymmetry — it is
   reported as a minor, non-blocking packaging inconsistency for a future
   session to decide on, not something this study should alter (see the
   Phase 1 prohibition on non-scientific changes beyond what is strictly
   needed to unblock verification).

   | Representation | Shape | sha256 (first 16 hex, of the raw ndarray bytes) |
   |---|---|---|
   | TIER_A | (1325, 12) | `45bdfdd7aef2aa2b` |
   | MORGAN | (1325, 2048) | `1dd2e97e70c18d5b` |
   | MORGAN_COUNTS | (1325, 2048) | `f447b437000370d2` |
   | ATOMPAIR | (1325, 2048) | `84e400a0ae38802f` |
   | ATOMPAIR_COUNTS | (1325, 2048) | `a66f1c71a11198f7` |
   | MACCS | (1325, 167) | `13b95c01da6dde88` |
   | MINMAX_MORGAN kernel | (1325, 1325) | `60c5ff2f3ec632b2` |
   | MINMAX_ATOMPAIR kernel | (1325, 1325) | `5c42f709bd311cb3` |

   Full-file sha256 of the rebuilt `MORGAN.parquet`:
   `7230d95a31e933424613f956f696c02d1e034164cbb30966e1f1645df14c758e`.

2. **Candidate and comparators** (`scripts/wur_v2/build_v2_candidate.py`,
   9.5s, writing into the isolated worktree's own `artifacts/wur_v2/candidate/`,
   never into the real working tree):

   | Model | Rebuilt canonical-JSON sha256 | Matches frozen/manifest |
   |---|---|---|
   | `V2_TA_MORGAN_JOINT` (candidate) | `11aa801c3acc2d862d35977d3c2ee348bdce143b89f3d0cc7ff745e61dcf9e9b` | **exact match** |
   | `V2_REF_TA_RIDGE` (comparator) | `3de70e7b2294428c2ce9f69b88a4808e3397712b2f636e260645fbc46dc5bc32` | **exact match** |
   | `V2_REF_B1_MASS` | `3e8b889c9b096dec2e03b01ad900b49ad3046fb56c0795c54e39150c64c2ab56` | **exact match** |
   | `V2_REF_B0_NULL` | `b910cc0d8a16002612a010d5898cf436edd4dd0ac60612371e8fdfac7b7ff56a` | **exact match** |

   Reload parity (in-memory engine prediction vs re-serialized JSON, on the
   1,325 training compounds): `max|Δ log g| = 2.220446049250313e-15`
   (float64 noise floor).

3. **PRIMARY and STRICT candidate P1** (`scripts/wur_v2/repro_check_p1.py`,
   written for this check; not part of the frozen pipeline, does not
   overwrite anything). Ran twice: once through the repository's own
   fingerprint-gated run cache (`runner.run(..., use_cache=True)`, the
   default), and once forcing a full from-scratch grid-search refit
   (`use_cache=False`, 28.3s, bypassing every cached `.parquet`/`.json` under
   `artifacts/wur_v2/runs/`). **Both paths produced bit-identical floats.**

   The cache path is legitimate, not a shortcut that begs the question:
   `runner.inputs_fingerprint()` hashes the outcome matrix plus every
   representation file's bytes on disk, and this was independently checked
   to equal the fingerprint recorded in the committed cache's `.json`
   sidecar (`07f215e9...` on both sides) — i.e. the freshly rebuilt
   `MORGAN.parquet` (step 1) is not merely hash-equal to itself, it
   fingerprint-matches the exact representation set the original PRIMARY/
   STRICT runs were computed against. The from-scratch rerun (no cache at
   all) is the stronger proof and is what is reported below.

   | Partition | P1 candidate | P1 Tier A | ratio | AF candidate | AF Tier A |
   |---|---|---|---|---|---|
   | PRIMARY | 0.11599941847410669 | 0.13054598985817814 | 0.8885712889390591 | 0.06339622641509433 | 0.10264150943396226 |
   | STRICT | 0.12281854776057843 | 0.13268637788545154 | 0.9256304205289858 | 0.07622641509433963 | 0.10943396226415095 |

   Mandate's stated approximate figures — candidate P1 0.1159994, Tier A
   0.1305460, ratio 0.8885713, STRICT ratio 0.9256304, AF 6.3%/10.3% — all
   reproduce to at least 6 significant figures from a from-scratch, cache-
   bypassed, isolated-worktree run.

## 2. Raw-input provenance

| Input | Local path | sha256 | Source |
|---|---|---|---|
| LCSB spectra | `artifacts/wur_v2/data/lcsb_pos_spectra.parquet` | `ce11ff7c3be574ca375ec1abab46c6c2efe728d797859e877263db9899051061` | committed to this repository (derived from MassBank/LCSB records processed earlier in the WUR v1/v2 program; see `DATA_CENSUS.md`, `MURU_Reference_Pack/`) |
| WUR spectra | `artifacts/wur_v2/data/wur_pos_spectra.parquet` | `df806afdc6f81365da6f8575cd605551a0d7e558a760af76411600bfd3993dc5` | committed; WUR archive processed in WUR Stage 0/1 (see `artifacts/wur_bridge_gate.json`, `artifacts/wur_split_manifest.json`) |
| Compound identity table | `artifacts/wur_v2/data/compounds.csv` | `87d79ab7f9e02eb7c99c4ea9b7e12a87568d0b2c8c81c372b22d44bec862e34c` | committed |
| WUR identity table | `artifacts/wur_v2/data/wur_pos_identity.csv` | `ec5c3bd5204daa6e76be6cf2995ab84b3d90fede51dfef235b1c49aa33b86c36` | committed |
| MORGAN representation | not committed (see Finding above) | `7230d95a31e933424613f956f696c02d1e034164cbb30966e1f1645df14c758e` (this rebuild) | reconstructed via `PYTHONPATH=src python3 scripts/wur_v2/build_v2_representations.py`, deterministic given the inputs above + pinned RDKit |

All four raw inputs above are already committed to this git repository at
the working commit; no multi-gigabyte raw mzML is committed anywhere (by
design — see `.gitignore`), and none was needed for this reconstruction:
the candidate and comparators depend only on the already-aggregated
spectrum/identity tables and the structure-only representations, not on raw
acquisition files.

## 3. Reconstruction commands (copy-paste reproducible)

```bash
git worktree add --detach /tmp/repro <commit>
cd /tmp/repro
PYTHONPATH=src python3 scripts/wur_v2/build_v2_representations.py
PYTHONPATH=src python3 scripts/wur_v2/build_v2_candidate.py
```

## 4. Environment

Python 3.13.12, Darwin 25.1.0 arm64 (macOS, Apple Silicon). numpy 2.5.2,
scipy 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, rdkit 2026.03.5, pymzml
2.6.1. Identical environment used for Phase 1 regression testing; see
`artifacts/wur_v2_confirmation/reproducibility_manifest.json` for the
machine-readable copy of every number in this document.
