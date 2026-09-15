# muru-v2-comparator-benchmark-1.0: closed record chain

**Status:** CLOSED. The benchmark is final and its 1,327-compound population is EXPOSED. No further analysis, rerun,
subset analysis or re-interpretation of this population is permitted. This note is a closure record written on
2026-09-15 (UTC). It changes no numerical result, prediction, preregistration or interpretation file.

Governing documents: `MURU_COMPARATOR_BENCHMARK_PREREGISTRATION.md` (frozen) and `MURU_COMPARATOR_BENCHMARK_RESULT.md`
(written after the result commit).

## Chain

| Step | Commit | Published ref on `origin` (verified by `git ls-remote`) | Commit time (UTC) | Parent |
|---|---|---|---|---|
| Preregistration and freeze | `c0e724e342ee37139a50999be2030bd8144b1346` | `refs/muru-freeze/muru-v2-comparator-benchmark-1.0` | 2026-09-14T23:40:31Z | `21fae1a` (feasibility audit) |
| Frozen competitor predictions | `2c291a2be28617083dab19b7dadcc617b1ace75b` | `refs/muru-predictions/muru-v2-comparator-benchmark-1.0` | 2026-09-15T01:01:00Z | `c0e724e` |
| Pre-access record | `9ed02751cc1ff4e868afbe6ab0764555e53b333d` | `refs/muru-access/muru-v2-comparator-benchmark-1.0` | 2026-09-15T01:09:04Z | `2c291a2` |
| Numerical result | `156fb8777306f88cb00bce8e85d241464e662630` | `refs/muru-result/muru-v2-comparator-benchmark-1.0` | 2026-09-15T01:10:28Z | `2c291a2` |
| Post-result interpretation | `5b1c5026c9d73b443e4eb7d87dc521cf9145df25` | branch `claude/muru-comparator-feasibility-audit-6b9895` | 2026-09-15T01:12:02Z | `156fb87` |

**Topology.** The pre-access record and the result are siblings: both are children of the execution commit `2c291a2`,
because `analysis.py` ran from the clean prediction commit, not from the access-record commit. The branch therefore did
not contain `access_record.json` until this closure. A non-fast-forward merge of `9ed0275` now brings it in unchanged
(sha256 `01e2cd46b8aca349b79e8234894719947bb5036b65bbb7555df9b51468d786b3`, identical to the blob at `9ed0275`). Nothing
was rebased, amended or force-pushed, so all five commits above keep their original identities and are ancestors of
the benchmark PR head.

## Ordering evidence

| Event | Time (UTC) | Source |
|---|---|---|
| Branch created on GitHub at `2c291a2` | 2026-09-15T01:08:21Z | GitHub repository activity API |
| Access record written | 2026-09-15T01:08:52.247Z | `access_record.json` `utc_timestamp` |
| Access record committed | 2026-09-15T01:09:04Z | commit `9ed0275` |
| Analysis started | 2026-09-15T01:09:56.978Z | `result/analysis_start_utc.txt` |
| Analysis ended, exit 0 | 2026-09-15T01:10:03Z | `result/analysis_exit.txt` |
| Result pushed | 2026-09-15T01:10:29Z | GitHub repository activity API |
| Interpretation pushed | 2026-09-15T01:12:03Z | GitHub repository activity API |

**Limit of the ordering evidence.** GitHub's activity and events APIs record branch updates only. They do not
timestamp the push of custom refs such as `refs/muru-access/...`. The ref is verified present on `origin` at `9ed0275`
today, and its commit precedes the analysis start by 53 seconds. `analysis.py` itself checks only that the freeze ref
resolves locally, that the prediction files match their committed manifest, and that `MURU_COMPARATOR_ONE_LOOK=1` is
set. It does not check the access ref. Publication of the access ref before the
analysis therefore rests on the operator procedure recorded in the result document, not on an independent server
timestamp.

## Invariants checked at closure

| Check | Result |
|---|---|
| Population key list sha256 equals access record (`dbdba9ca...52514`) | pass |
| Population CSV sha256 equals access record (`55264419...276fe`) | pass |
| `prediction_manifest.json` sha256 equals access record (`b39f6434...9c4`) | pass |
| `competitor_mu.csv` sha256 equals access record (`c51041d4...baad`) | pass |
| `analysis.py` sha256 equals access record (`c6851db9...1276`) | pass |
| `analysis.py`, population files, technical artifacts and preregistration unchanged from `c0e724e` to head | pass (only `verify_predictions.py` was added, at `2c291a2`) |
| Predictions and prediction verification unchanged from `2c291a2` to head | pass |
| Result artifacts unchanged from `156fb87` to head; four sha256 values equal those listed in the result document | pass |
| Only `MURU_COMPARATOR_BENCHMARK_RESULT.md` was added from `156fb87` to `5b1c502` | pass |
| Primary Bonferroni 98.33% ratio intervals in `analysis.json`: FIORA-OS v0.1.0 [0.588, 0.652], ICEBERG 2.1 [0.741, 0.823], GLACIER [0.864, 0.968] | match result document |
| Raw-NCE diagnostic ratios in `analysis.json`: ICEBERG 2.1 1.076 [1.029, 1.127], GLACIER 1.238 [1.181, 1.299] | match result document |

## What follows

The collision-energy interface question that this benchmark exposed is taken up by a new, separate, outcome-blind
study (`MURU_CE_INTERFACE_ADJUDICATION_*`, branch `claude/muru-ce-interface-adjudication`). That study may not use
this population or its outcomes to choose, tune, validate or justify any energy mapping.
